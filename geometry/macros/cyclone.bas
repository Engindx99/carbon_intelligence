Attribute VB_Name = "cyclone"
'==================================================================
' Cyclone CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' Builds ONE closed solid: the gas volume inside a single preheater
' cyclone, plus its tangential meal/gas inlet duct and the outlet
' pipe above the roof, which rises, turns over through a 180 deg
' gooseneck and drops to the outlet face; with RISER_ON, also the
' round riser, its bend and the transition into the inlet duct, and
' the meal feed chute. With VOLUTE_ON the inlet is a simple volute
' outside the barrel instead of a slot through the shell, and with
' OUTLET_TURN_DEG 90 the outlet turns into a horizontal run instead
' (C4). Nothing structural is modelled -- no shell, no refractory
' (CLAUDE.md rule 8).
'
' Coordinates: cyclone axis = z, dust outlet at z = 0. Gas enters
' along +x at y in [R - inlet_w, R], so the swirl runs CLOCKWISE
' seen from above (angular momentum about z is -y*vx < 0). The
' deleted geometry/components.py said anticlockwise; that docstring
' was wrong, the geometry it built was this.
'
' SI ONLY. The SolidWorks API is always metres and radians,
' whatever the document's display units are set to.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA
' editor File -> Import File... and pick this .bas. Run `main`.
' See README.md next to this file.
'==================================================================

Option Explicit

'------------------------------------------------------------------
' (a) PARAMETERS -- the only numbers in this file.
'     Pick the cyclone with CYCLONE_NAME; its dimensions and its
'     per-cyclone modelling choices are set in SelectCyclone below.
'     The table for every stage of every line is in
'     geometry/catalog.md.
'------------------------------------------------------------------

Const CYCLONE_NAME As String = "C1"      ' "C1" or "C4"
Const LINE_KEY As String = "2500"

' Per-cyclone values, assigned in SelectCyclone. Catalogue
' dimensions [m] first, then the modelling choices that differ
' between the cyclones.
Dim D_BARREL As Double                   ' effective inner diameter
Dim H_BARREL As Double                   ' cylindrical body height
Dim H_CONE As Double                     ' cone height
Dim L_VORTEX As Double                   ' vortex finder immersion
Dim D_VORTEX As Double                   ' vortex finder diameter
Dim D_DUST As Double                     ' dust outlet diameter
Dim W_INLET As Double                    ' inlet width  (normal to the duct axis)
Dim H_INLET As Double                    ' inlet height (normal to the duct axis)
Dim INLET_SLOPE_DEG As Double            ' duct inclined this far DOWNWARD toward the cyclone
Dim VOLUTE_ON As Boolean                 ' inlet through a volute instead of a slot in the shell
Dim OUTLET_TURN_DEG As Double            ' outlet bend: 180 (gooseneck + drop) or 90 (elbow + run)
Dim RISER_ON As Boolean                  ' riser, its bend and the feed chute in front of the duct
Dim BOI_RADIUS As Double                 ' mesh sizing cylinder about the cyclone axis [m]

' Modelling parameters -- NOT plant dimensions. No source gives
' them; they say where the CFD boundary faces sit.
' configs/twin_cfg.yaml : geometry.cfd_boundary
' How far the outlet pipe rises straight above the roof before the
' bend starts, in vortex finder diameters. Until the bend was added
' this was where the outlet face sat. 1.0 was too short and the
' first Fluent run said so:
' the swirl leaving up the bore carries a reverse-flow core that
' was still open where the boundary cut it, so 40-44 % of the
' outlet face had gas coming back IN. Fluent then has to impose the
' backflow values there, the imposed state fights the state the
' domain wants, and the whole solution sat in a limit cycle of
' +/- 0.3 % on the mass balance instead of converging. 2.5 put the
' face 6.0 m above the roof, and that held only while the vortex
' was weak. Once the mesh stopped smearing the core (tet -> poly)
' the swirl got stronger, v_max 26 -> 34 m/s, its reverse-flow core
' reached the face again, and the face was 38 % backflow (k-omega
' SST, 26 Sep 2026). The mass imbalance, the pressure drop and the
' backflow fraction all swung together on one 18-iteration period,
' correlation 0.8. A straight pipe cannot fix this at any sensible
' length, because swirl decays very slowly in one.
'
' The bend below is the fix, and it is what the plant has: the gas
' leaving C1 turns into a duct to the fan. The rise was left at 2.5
' so that the bend was the only thing that changed against the run
' that measured the 38 %. With the 180 deg gooseneck it looked far
' taller than a plant's, and it was halved to 1.25 (3.0 m) so the
' gooseneck sits close over the roof as in the plant (user decision,
' 29 Sep 2026). The bend, not the rise, is what breaks the swirl.
Const OUTLET_EXT_OVER_VORTEX_D As Double = 1.25   ' straight rise above roof, x vortex D

' The outlet gooseneck: the pipe section swept through 180 deg about
' a horizontal axis, turning the flow from +z over the top and down,
' then a straight drop to the outlet face. C1 is the top cyclone and
' this is what its gas duct does in the plant -- up out of the roof,
' over, and down to the duct to the fan (user decision, 29 Sep 2026).
' The first bend had only the 90 deg and a horizontal run; either
' breaks up the swirl and its reverse-flow core, so the outlet face
' sits in flow that is going the one way. Modelling parameters, no
' plant source.
'
' Bend radius is the centreline radius, 1.5 diameters: an ordinary
' long-radius elbow. Anything under half a diameter folds the inner
' wall through itself; PreChecks refuses it.
'
' It turns to +x, away from the inlet side, where the riser now
' stands: turned to -x the drop would come down beside the riser
' bend. It clears everything by construction: the bend starts above
' the roof and the drop lands outside the barrel.
' C1: 1.5. Per cyclone, set in SelectCyclone.
Dim ELBOW_R_OVER_VORTEX_D As Double    ' bend centreline radius, x vortex D
' The drop is as long as the rise, so the gooseneck is a plain U
' with equal legs (user decision, 29 Sep 2026; 2.0 D hung too far
' down). The outlet face then lies in the roof's own plane, well
' clear of it in x; TagBoundaryFaces tells the two apart by where
' the face sits in x.
' C1: = OUTLET_EXT_OVER_VORTEX_D. Per cyclone, set in SelectCyclone;
' with the 90 deg elbow it is the length of the horizontal run.
Dim OUTLET_DOWN_OVER_VORTEX_D As Double   ' straight drop or run, x vortex D
' Vortex finder wall thickness [m]. What this carves out of the
' fluid is a slot 2.16 m deep and this wide, running the finder's
' whole 7.6 m circumference, and its lower rim is an annular face of
' the same width. At the 0.012 m this started as, that face is a
' 631:1 ribbon: a mesher spans it with one sliver element and the
' skewness there runs to 0.95 while the rest of the mesh averages
' 0.28. 0.05 m brings it to 154:1, and 0.08 m to 96:1.
'
' 0.05 m was not enough. It held at the 0.15 m cells the first mesh
' was built with, but the cyclone needs about 0.05 m cells in the
' core to resolve the vortex at all, and at that size a 50 mm rim
' is one cell wide. Refining the core in Fluent drove the minimum
' orthogonal quality to 0.015 -- Fluent's floor is 0.01 -- and both
' of the worst cells sat under this rim, at r = 1.23-1.25,
' z = 9.22, 60 mm below its face. A feature thinner than the cell
' size cannot be meshed, only worked around.
'
' Thickening it costs nothing physically. The wall's job is to keep
' the swirl in the annulus apart from the gas leaving up the bore,
' and a 12 mm plate and a 50 mm one do that identically -- the flow
' does not care how thick the plate is. It is a modelling choice
' with no source either way (configs/twin_cfg.yaml says so), and it
' takes the annulus from 0.948 to 0.910 m, 4 % narrower.
'
' The limit is the duct: its inner wall sits at
' y = R - INLET_TANGENT_RELIEF - inlet_w, so the finder's outer
' radius must stay under that. The two parameters share one budget:
'
'     VORTEX_WALL + INLET_TANGENT_RELIEF < 0.10 m
'
' and they cannot both be spent. This file spends it on the rim,
' because that is where the measurement says the mesh actually
' fails: 0.015 orthogonal quality under the rim against 0.135 at
' the tangent edge, an order of magnitude apart. The tangent edge
' is handled with a face sizing in the mesher instead, which costs
' no geometry. 0.08 m leaves a 0.020 m margin to the duct wall.
'
' 80 mm is also the more physical of the two ends of the range: a
' preheater dip tube is heat resistant steel or SiC, often
' refractory lined, and 80 mm of it is ordinary. The 12 mm this
' started at was the least physical value of the three.
Const VORTEX_WALL              As Double = 0.08
Const L_INLET                  As Double = 3#     ' duct length from the barrel tangent plane [m]

' How far the duct's highest point stays below the roof plate [m].
' The duct slopes down towards the cyclone, so it is highest at the
' upstream edge of its opening in the shell. Anchoring the top edge
' ON the roof instead would push the duct above the roof over the
' barrel's footprint and leave a wedge of fluid sitting on the roof
' plate, tapering to a dead end. This clearance is what keeps the
' roof flat and the opening a clean hole in the shell. It cannot be
' zero: at zero the duct roof, the cyclone roof and the barrel all
' meet at one degenerate point.
Const INLET_ROOF_CLEARANCE As Double = 0.05

' Superseded by INLET_TONGUE below, and kept at 0.
'
' It pulls the duct's OUTER wall in off the barrel. That opens the
' tangent junction from 0 to sqrt(2a/R) radians -- 9.56 deg at
' 0.03 m -- but it does not remove it: the offset plane still meets
' the cylinder, just at x = -0.359 instead of x = 0, and the fluid
' still closes to nothing there. Two tips instead of one, at a
' finite angle. It also costs inlet section, because the outer wall
' runs the whole length of the duct: 0.03 m takes 0.86 -> 0.83 m,
' 1.858 -> 1.793 m2, and pushes the inlet velocity 16.5 -> 17.1 m/s.
'
' INLET_TONGUE removes the junction outright and costs none of
' that, so this stays at 0. Setting both is refused by PreChecks --
' the combination is not worked out and the volume term below
' assumes the outer wall is the barrel's own tangent plane.
Const INLET_TANGENT_RELIEF As Double = 0#

' Mesh sizing cylinder -- the body of influence, written out on its
' own as <name>_boi.step. NOT fluid geometry and NOT part of the
' exported solid: a separate body the mesher reads as a sizing
' region and never meshes. Fluent Meshing only offers a body of
' influence when the CAD hands it a body, and drawing that by hand
' after every dimension change is how a mesh stops matching the
' geometry it was built for.
'
' The radius has to clear every real surface by a margin, because a
' refinement front landing on a geometric edge is exactly what
' wrecked the first refined mesh: the front was put at r = 1.25,
' which is the vortex finder's outer radius to the millimetre, and
' the minimum orthogonal quality fell to 0.015 against Fluent's
' floor of 0.01. BOI_CLEARANCE is the margin.
'
' Against the vortex finder the margin is two-sided: the cylinder
' may sit inside the bore or outside the shell, but not on either
' surface and not in the annulus between them. At 0.08 m wall and
' 0.3 m clearance that means r <= 0.90 m or r >= 1.58 m. The core
' lives inside the bore, so 0.8 m takes the inside branch with
' 0.40 m to spare.
'
' 0.8 m is what the first resolved run measured the core to need,
' not a guess. That run put a tangential velocity profile across
' the barrel at z = 8 m: the velocity rises linearly out to
' r = 1.0 m before it peaks, so the solver is turning a core that
' should be 0.25 - 0.35 m across into a 1 m solid-body wheel, and
' the peak reaches only 1.1 times the inlet velocity where a
' cyclone gives 1.5 - 2.5. The profile also crosses zero at
' x = +0.35, so the vortex axis sits off centre and the region has
' to be wide enough to hold it there. 0.8 m covers r = 1.0 m of
' core about an axis displaced 0.35 m, with the peak inside it.
'
' 1.6 m was the earlier value, chosen to reach the vortex finder
' radius. At the 0.04 m cells the core actually needs it would be
' about 1.5 million cells in the region alone, which does not fit;
' 0.8 m is about 320 000. The size the mesher is given is a mesher
' setting, not a geometry one, so tune it there.
'
' Two bodies in one geometry broke the mesher once: the watertight
' workflow merged the sizing cylinder into the fluid region and the
' cone vanished inside it. That happened with the cylinder inserted
' into the cyclone's own part. Hand the two STEP files to Import
' Geometry separately instead (Import Type: Multiple Files) and
' pick the cylinder in Add Local Sizing -> Body of Influence.
Const EXPORT_BOI      As Boolean = True

' BOI_RADIUS is per cyclone, set in SelectCyclone.
Const BOI_CLEARANCE   As Double = 0.3    ' least distance to any real surface [m]

' Where the sizing cylinder stops, above the roof. Everything above
' that is the straight outlet extension, whose only job is to hold
' the boundary condition away from the flow; resolving it costs
' cells and buys no physics.
Const BOI_ROOF_MARGIN As Double = 1#     ' [m]

' The cylinder also has to stop before it reaches the cone wall,
' for the same reason it has to clear the barrel: a refinement
' front sitting on a wall is what wrecked the first refined mesh.
' The floor is derived, not set -- it is the height where the cone
' has opened to BOI_RADIUS + BOI_CLEARANCE. Below it the cone is
' narrower than the region, so there is nothing there to size that
' the global setting cannot.

' How thick the shell is left between the duct's outer wall and
' the barrel's tangent line [m]. The cut-water.
'
' The duct's outer wall is the plane y = R and the barrel is the
' cylinder r = R: tangent at x = 0, so running the duct all the way
' there closes the union to a zero-angle edge with the fluid
' vanishing along it. That is the one defect in this model meshing
' cannot reach. A dihedral angle is scale invariant -- halve the
' cell and the same sliver returns at half the size, and it did:
' orthogonal quality 0.135 and aspect ratio 79 on the 0.15 m mesh,
' aspect ratio 175 after refinement. Refining made it worse. Every
' other thin feature here is a WIDTH and yields to a local face
' size; an angle does not.
'
' So the duct stops short of the tangent plane instead, at
'
'     xTrim = sqrt(t (2R - t))
'
' where the wedge between the plane and the cylinder is exactly t
' thick. The part of the end cap inside the barrel dissolves in the
' merge as it always did; what survives is a blunt rectangle t wide
' and one duct height tall. The tangency still exists as geometry,
' but between x = -xTrim and x = 0 it lies inside the solid shell,
' where it bounds no fluid and nothing meshes it. The worst corner
' left in the opening is the 53 deg one at x = -reach, which was
' always there.
'
' It costs almost nothing. 0.05 m removes 0.0166 m3, 0.011 % of the
' domain, and leaves the catalogue section 0.86 x 2.16 and the
' 16.5 m/s inlet velocity exactly as they were.
'
' It is also the more faithful geometry. No real cyclone closes the
' shell-to-duct joint to a knife edge; it is plate plus refractory,
' blunt, 50-100 mm. A model that sharpens it to zero is further
' from the machine, not closer.
'
' The surviving face is a ledge, not a converging gap, so it only
' has to take a few surface elements across it: 0.05 m is 2.5 at a
' 0.02 m face size and 4 at 0.0125 m.
Const INLET_TONGUE As Double = 0.05

' The volute (VOLUTE_ON), for cyclones whose published inlet is too
' wide to pass between the barrel and the vortex finder -- C4's is
' 1.27 m against 0.84 m of annulus. The plant feeds such a cyclone
' through a wrap-around scroll, so the CFD model does too, in the
' simplest form that keeps the published barrel and finder.
'
' Seen from above it is one closed outline, extruded down from the
' roof by the inlet height:
'   - a straight duct L_INLET long whose inner wall runs
'     INLET_TONGUE outside the barrel's tangent line (y = R + t) and
'     whose outer wall is W_INLET further out;
'   - from x = 0 the outer wall winds in as the Archimedean spiral
'     r = R + t + W (1 - phi / pi), phi measured clockwise from +y,
'     the way the gas turns, until it has closed onto r = R + t at
'     phi = pi;
'   - the inner side of the scroll is an arc VOLUTE_OVERLAP inside
'     the barrel, so the merge eats it and the scroll opens onto the
'     barrel all the way round, with no coincident faces;
'   - both ends close radially, which leaves the same blunt
'     INLET_TONGUE-thick cut-water at each end that the slot inlet
'     has, for the same reason: no zero-angle edge.
' The duct is horizontal and flush with the roof.
'
' The spiral is a spline through VOLUTE_SPLINE_PTS points of it. Its
' fluid area outside the barrel is closed form (the integral of
' (r^2 - R^2) / 2 over phi), and a spline through that many points of
' a smooth spiral is far inside VOL_TOL of it.
Const VOLUTE_OVERLAP    As Double = 0.1     ' scroll's inner arc inside the barrel [m]
Const VOLUTE_SPLINE_PTS As Long = 25        ' points along the half turn

' The riser in front of the inlet duct: the gas comes up a vertical
' riser, turns through a bend into the duct, and the raw meal is fed
' into the riser down a sloping chute through its wall -- the plant's
' "distribution box". Modelling choice, no plant source for any of
' the lengths (geometry/preheater/riser_R1.md).
'
' Why it is here: fed straight into the duct at 542 K, the meal made
' both two-way DPM and DDPM diverge (T2, 28 Sep 2026), and 542 K
' itself was an assumed 80/20 riser/cyclone split of the gas-meal
' heat exchange. DTU's industrial DDPM cyclone (Mirzaei 2023) feeds
' the meal into a riser for the same reason: that is where the
' exchange happens. With the riser the split is a result.
'
' Section: the published R1 is a 3.07 m round duct shared by the
' twin C1s, so each C1's riser is round with half its area: 3.70 m2,
' 2.17 m across, 8.7-10.6 m/s at 17.9 kg/s where DTU measured
' 7.5-9.3 m/s. The riser and its bend are round, as in the plant;
' the cyclone is still entered through the validated 0.86 x 2.16 m
' duct, and a loft RISER_TRANS_LEN long, along the duct axis, turns
' the round section into the duct's rectangle. A square inlet was
' ruled out: 1.36 m of it would run through the vortex finder,
' whose annulus is 0.88 m (user decisions, 28-29 Sep 2026).
'
' The bend is the round section swept about a horizontal axis
' through 90 deg plus the duct slope, from straight up into the duct
' axis, built like the outlet bend. Its centreline radius is 1.0
' riser diameter, usual for riser bends, and the transition is
' 1.5 m (24 deg half angle, still a comfortable contraction): both
' were cut from 1.5 D and 2.0 m to bring the riser 1.7 m closer to
' the cyclone (user decision, 29 Sep 2026). The 3.0 m duct is a
' published plant length and stays. Below the bend the riser runs
' straight down: RISER_ABOVE_FEED from the feed to the bend, which
' gives the coarse meal (tau_T 0.08 s at 200 um) about 11 m of
' riser, bend, transition and duct before the barrel, and
' RISER_BELOW_FEED under the feed, about 2 D, so the gas arrives
' developed and meal that falls back has riser to be caught in
' before it leaves through the gas inlet. 2.5 m was 2 D_h of the
' first, thin riser and only 1.15 D of this one.
'
' The meal comes in down a chute, as in the plant: a square pipe
' sloping FEED_SLOPE_DEG below the horizontal, whose axis meets the
' riser wall at zFeed. A horizontal stub drops the meal along the
' riser wall as a strand, and a wall strand in thin prism cells is
' what made two-way DPM diverge (T2, 28 Sep 2026). 60 deg clears
' the raw meal's 40-45 deg angle of repose; no plant source gives
' the angle or the section (user decision, 29 Sep 2026).
'
' Off, the macro builds the validated gas-only domain exactly as
' before and writes it under the old name. RISER_ON is per cyclone,
' set in SelectCyclone; the lengths below are C1's.
Const D_RISER_SRC          As Double = 3.07  ' published R1 inner diameter [m], geometry/catalog.md
Const RISER_AREA_SHARE      As Double = 0.5   ' the twin C1s share R1
Const RISER_TRANS_LEN       As Double = 1.5   ' round-to-duct loft, along the duct axis [m]
Const RISER_BEND_R_OVER_D   As Double = 1#    ' bend centreline radius, x riser diameter
Const RISER_ABOVE_FEED      As Double = 3#    ' feed (chute axis at the wall) to bend start [m]
Const RISER_BELOW_FEED      As Double = 4.5   ' riser gas inlet to feed [m]
Const FEED_W                As Double = 0.6   ' feed chute section, along y [m]
Const FEED_H                As Double = 0.6   ' feed chute section, normal to its axis in x-z [m]
Const FEED_DEPTH            As Double = 1#    ' feed chute, along its axis beyond the riser wall [m]
Const FEED_SLOPE_DEG        As Double = 60#   ' feed chute below the horizontal, rising away from the riser

' Output
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

' Verification tolerances
Const VOL_TOL  As Double = 0.001   ' relative, on every closed-form stage volume
Const AREA_TOL As Double = 0.002   ' relative, on the boundary face areas
Const BOX_TOL  As Double = 0.005   ' absolute [m]; GetBodyBox may overstate curved faces
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001

Const PI As Double = 3.14159265358979

'------------------------------------------------------------------
' Module state
'------------------------------------------------------------------

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean

Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStlUnits As Long, oldStlQuality As Long
Dim oldStepAppear As Boolean, oldStlBinary As Boolean
Dim oldStlNoShift As Boolean, oldStlInfo As Boolean
Dim oldStlDev As Double, oldStlAngle As Double

' (b) derived coordinates -- every one computed, none typed in
Dim R As Double, rDust As Double, rVortex As Double
Dim zRoof As Double, zVortexBottom As Double, zOutletTop As Double
Dim rBend As Double                         ' bend centreline radius
Dim zElbowTop As Double                     ' highest point of the gooseneck
Dim xLeg As Double                          ' axis of the drop after the gooseneck, x = this
Dim zGasOut As Double                       ' the gas outlet face, z = this, facing down
Dim xBoxMax As Double                       ' the domain's +x extreme, the drop's outer wall
Dim zBoiTop As Double                       ' top of the mesh sizing cylinder
Dim zBoiBot As Double                       ' floor of the mesh sizing cylinder
Dim yOuter As Double, yInner As Double, yMid As Double
Dim wDuct As Double                         ' built duct width = W_INLET - relief
Dim dx As Double, dz As Double          ' duct axis direction d = (dx, 0, dz)
Dim nx As Double, nz As Double          ' duct section "up"  n = (nx, 0, nz)
Dim zTopAt0 As Double, zBotAt0 As Double
Dim reach As Double                     ' |x| where the duct's inner wall meets the barrel
Dim xTrim As Double                     ' |x| where the duct stops, short of the tangent plane
Dim ceX As Double, ceY As Double, ceZ As Double   ' inlet face centre
Dim xInletNear As Double, zDuctTop As Double
Dim rRiser As Double                        ' riser radius
Dim rRiserBend As Double                    ' riser bend centreline radius
Dim gX As Double, gZ As Double              ' centre of the round end of the transition
Dim xRiserAxis As Double, zRiserTop As Double   ' riser bend axis, parallel to y
Dim xRiser As Double                        ' the straight riser's axis, x = this, y = yMid
Dim xBoxMin As Double, yBoxMax As Double    ' the domain's box once the riser is on
Dim zRiserBot As Double                     ' the riser's gas inlet face
Dim zFeed As Double                         ' where the feed chute's axis meets the riser wall
Dim fx As Double, fz As Double              ' feed chute axis e = (fx, 0, fz), up and away from the riser
Dim wx As Double, wz As Double              ' feed chute section "up" w = (wx, 0, wz)
Dim zFeedStart As Double, lFeed As Double   ' chute start on the riser axis, its length from there
Dim xFeedEnd As Double, zFeedEnd As Double  ' centre of the chute's end face, the meal_feed
Dim zRiserBendTop As Double                 ' highest point of the riser bend
Dim outName As String                       ' file name the solid is written under
Dim rTongue As Double                       ' volute: duct inner wall / spiral end radius, R + t
Dim rScroll0 As Double                      ' volute: spiral start radius, R + t + W
Dim aScroll As Double                       ' volute: spiral fluid area outside the barrel [m2]
Dim xScrollMax As Double, yScrollMin As Double   ' volute: the spiral's extremes
Dim zLegAxis As Double                      ' 90 deg outlet: axis height of the horizontal run
Dim xGasOut As Double                       ' 90 deg outlet: the gas outlet face, x = this
' The domain's box after the inlet stage, before the outlet is on.
Dim xLo2 As Double, yLo2 As Double, xHi2 As Double, yHi2 As Double

' Sketch axis directions, measured at run time by CalibrateSketchAxes.
' uSign/vSign are the pair in force for the sketch being drawn now;
' the others are what was measured for each plane.
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profiles
Dim uSignD As Double, vSignD As Double      ' the duct's own plane, for its side view
Dim uSignZ As Double, vSignZ As Double      ' z = zOutletTop, where the bend starts
Dim uSignQ As Double, vSignQ As Double      ' z = zRiserTop, where the riser meets its bend
Dim uSignF As Double, vSignF As Double      ' y = yMid - FEED_W / 2, the feed chute's side, for its side view
Dim uSignR As Double, vSignR As Double      ' z = zRoof, the volute's outline
Dim uSignL As Double, vSignL As Double      ' x = rBend, where the 90 deg elbow ends

' The off-plane component of the first point drawn in the sketch
' now open. Every later point in the same sketch has to match it;
' see G2S for why the value itself is not compared against zero.
Dim wRef As Double
Dim wRefSet As Boolean

' expected volumes, all closed form
Dim vEquip As Double, vDuctFree As Double, vPipe As Double, vWall As Double
Dim vElbow As Double, vLeg As Double
Dim vRiserBend As Double, vRiser As Double, vFeed As Double
Dim vTransLo As Double, vTransHi As Double, vTransMid As Double
Dim vStage1 As Double, vStage2 As Double, vStage3 As Double
Dim vStage4 As Double, vStage5 As Double, vStage6 As Double
Dim vStage7 As Double, vStage8 As Double, vStage9 As Double, vFinal As Double

Dim buildLog As String

' What the macro is doing right now, so that an error raised by
' SolidWorks itself -- which carries no location -- still says where
' it happened.
Dim phase As String


'==================================================================
' main
'==================================================================
Sub main()

    Dim why As String

    ' Module state survives between runs, so start from a clean log
    ' or the second run's report is the first one's as well.
    buildLog = ""
    phase = "starting up"

    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "working out the coordinates"
    Derive
    phase = "checking the dimensions can be built"
    PreChecks

    phase = "building the solid"
    Build
    phase = "verifying the solid"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles
    If EXPORT_BOI Then
        phase = "building the mesh sizing cylinder"
        BuildBoi
    End If

    Restore
    MsgBox CYCLONE_NAME & " built and exported." & vbLf & vbLf & buildLog, vbInformation, "Cyclone"
    Exit Sub

Failed:
    ' Read the reason BEFORE Restore: the On Error statement inside
    ' it resets the Err object and the reason would be lost.
    why = Err.Description
    Restore
    MsgBox CYCLONE_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Cyclone"

End Sub


'==================================================================
' (a') The cyclone being built. Catalogue dimensions come from the
'      component document named in each case; everything else is a
'      modelling choice explained where it is set.
'==================================================================
Private Sub SelectCyclone()

    Select Case CYCLONE_NAME

    Case "C1"
        ' geometry/preheater/cyclone_C1.md
        D_BARREL = 4.32
        H_BARREL = 6.79
        H_CONE = 4.65
        L_VORTEX = 2.16
        D_VORTEX = 2.4
        D_DUST = 0.4
        W_INLET = 0.86

        ' Inlet height, normal to the duct axis. NOT the catalogue value.
        '
        ' The FLS ratio gives 4.97 m, i.e. a/D = 1.15. That is genuine for a
        ' low pressure drop preheater cyclone -- but only because the real
        ' machine feeds it through a 270 deg wrap-around volute, which this
        ' model deliberately does not build. With the volute replaced by a
        ' straight tangential duct, a 4.97 m inlet lost its reason to exist:
        ' it put 61 % of the opening below the vortex finder's rim, a
        ' short-circuit path, and dropped the inlet velocity to about
        ' 7 m/s where preheater cyclones run at 15-20.
        '
        ' 2.16 m is a/D = 0.50 and a/b = 2.51, which is Stairmand's classical
        ' proportion, puts only 10 % of the opening below the rim and brings
        ' the inlet velocity back to about 16 m/s. The inlet width was
        ' already classical: b/D = 0.86 / 4.32 = 0.199.
        '
        ' Equipment volume is untouched, so the twin's residence time and
        ' hold-up are unaffected. See geometry/preheater/cyclone_C1.md.
        H_INLET = 2.16

        INLET_SLOPE_DEG = 5#
        VOLUTE_ON = False
        OUTLET_TURN_DEG = 180#
        ELBOW_R_OVER_VORTEX_D = 1.5
        OUTLET_DOWN_OVER_VORTEX_D = OUTLET_EXT_OVER_VORTEX_D
        RISER_ON = True
        BOI_RADIUS = 0.8

    Case "C4"
        ' geometry/preheater/cyclone_C4.md -- also C2 and C3, which
        ' are identical to it (user decision, 27 Sep 2026).
        D_BARREL = 6.3

        ' Barrel height, NOT the catalogue value. The FLS ratio gives
        ' 3.46 m, h/D 0.55, which with the 3.17 m immersion put the
        ' vortex finder's mouth only 0.29 m above the start of the
        ' cone. h = D (1.0, usual for preheater cyclones) lifts it to
        ' 3.13 m above; the immersion, the cone, the finder and the
        ' dust outlet stay as catalogued (user decision, 4 Oct 2026).
        H_BARREL = 6.3
        H_CONE = 7.3
        L_VORTEX = 3.17
        D_VORTEX = 4.63
        D_DUST = 0.81

        ' Inlet, NOT the catalogue 1.27 x 9.44 m. That inlet is wider
        ' than the 0.84 m annulus between barrel and finder and taller
        ' than the catalogue's 3.46 m barrel, running down the cone to
        ' r = 0.9 m, with 66 % of it below the finder's rim. The plant
        ' feeds it through a volute; so does this model (VOLUTE_ON),
        ' with the area the published inlet has at the plant's flow
        ' (user decision, 4 Oct 2026): 9.90 m2, 16.0 m/s at 56 kg/s and
        ' 1033 K.
        '
        ' 3.40 m tall: chosen when the barrel was still 3.46 m, so the
        ' volute's floor would clear the barrel-to-cone edge. It stays
        ' with the longer barrel because the height is what sets how
        ' much of the opening lies below the finder's rim -- 7 % at
        ' 3.40 against the 3.17 m immersion; taller, the short circuit
        ' grows. The width keeps the area: 9.90 / 3.40 = 2.912 m.
        H_INLET = 3.4
        W_INLET = 2.912

        INLET_SLOPE_DEG = 0#
        VOLUTE_ON = True

        ' C4's gas goes on to the R3 riser, not down to a fan, so its
        ' outlet turns through 90 deg into a horizontal run. Either
        ' bend breaks the swirl, which is what the bend is for.
        OUTLET_TURN_DEG = 90#

        ' C1's 1.5 D bend and 1.25 D drop, scaled to this 4.63 m
        ' finder, made the outlet more than half the domain (378 of
        ' 666 m3). A 1.0 D bend -- the ratio C1's riser bend uses --
        ' still breaks the swirl, and a 1.0 D run keeps the outlet
        ' face a diameter clear of it (user decision, 4 Oct 2026).
        ' The rise above the roof stays at 1.25 D: that is C1's
        ' backflow measurement.
        ELBOW_R_OVER_VORTEX_D = 1#
        OUTLET_DOWN_OVER_VORTEX_D = 1#
        RISER_ON = False

        ' C1's measured core radius scaled with the finder diameter:
        ' 0.8 x 4.63 / 2.40 = 1.54 m, rounded down to stay inside
        ' the bore with the clearance PreChecks asks for.
        BOI_RADIUS = 1.5

    Case Else
        Fail "CYCLONE_NAME is " & CYCLONE_NAME & "; this macro knows C1 and C4."

    End Select

End Sub


'==================================================================
' (b) Derived coordinates
'==================================================================
Private Sub Derive()

    Dim th As Double, thF As Double
    Dim k As Long, ph As Double, rr As Double, legLen As Double

    SelectCyclone

    R = 0.5 * D_BARREL
    rDust = 0.5 * D_DUST
    rVortex = 0.5 * D_VORTEX

    zRoof = H_CONE + H_BARREL
    zVortexBottom = zRoof - L_VORTEX
    zOutletTop = zRoof + OUTLET_EXT_OVER_VORTEX_D * D_VORTEX
    rBend = ELBOW_R_OVER_VORTEX_D * D_VORTEX
    zElbowTop = zOutletTop + rBend + rVortex
    xLeg = 2# * rBend
    zGasOut = zOutletTop - OUTLET_DOWN_OVER_VORTEX_D * D_VORTEX
    xBoxMax = xLeg + rVortex

    ' The 90 deg elbow ends facing +x, its section centred rBend up
    ' and rBend out from where it started; the straight run carries
    ' it on to the outlet face, as long as the 180 deg drop would be.
    legLen = OUTLET_DOWN_OVER_VORTEX_D * D_VORTEX
    zLegAxis = zOutletTop + rBend
    xGasOut = rBend + legLen
    If OUTLET_TURN_DEG = 90# Then xBoxMax = xGasOut

    zBoiTop = zRoof + BOI_ROOF_MARGIN

    ' Where the cone has opened to BOI_RADIUS + BOI_CLEARANCE.
    zBoiBot = H_CONE * (BOI_RADIUS + BOI_CLEARANCE - rDust) / (R - rDust)
    If zBoiBot < 0# Then zBoiBot = 0#

    ' The relief moves the outer wall only, so the inner wall -- the
    ' one that has to clear the vortex finder -- does not move with
    ' it. wDuct is the width the duct is actually built and checked
    ' against; W_INLET is the catalogue width it starts from.
    yOuter = R - INLET_TANGENT_RELIEF
    yInner = R - W_INLET
    wDuct = yOuter - yInner
    yMid = 0.5 * (yInner + yOuter)

    th = INLET_SLOPE_DEG * PI / 180#
    dx = Cos(th): dz = -Sin(th)         ' towards the cyclone, downward
    nx = Sin(th): nz = Cos(th)          ' section "up", normal to the axis

    ' How far upstream the opening in the shell reaches: the duct's
    ' inner wall meets the barrel there, and that is the duct's
    ' highest point inside the barrel's footprint.
    reach = Sqr(R * R - yInner * yInner)
    xTrim = Sqr(INLET_TONGUE * (2# * R - INLET_TONGUE))

    ' Anchor: the top of the opening sits INLET_ROOF_CLEARANCE below
    ' the roof. Everything else follows from the constant section.
    zTopAt0 = zRoof - INLET_ROOF_CLEARANCE - reach * (nx / nz)
    zBotAt0 = zTopAt0 - H_INLET / nz

    ' Inlet face centre: L_INLET back along the axis from where the
    ' duct centreline crosses the barrel's tangent plane x = 0.
    ' Measuring at the centroid is what makes the volume below exact
    ' -- the tilted end cut adds and removes equal wedges about it.
    ceX = -L_INLET * dx
    ceY = yMid
    ceZ = 0.5 * (zTopAt0 + zBotAt0) - L_INLET * dz

    xInletNear = ceX + 0.5 * H_INLET * nx      ' inlet face edge nearest the cyclone
    zDuctTop = ceZ + 0.5 * H_INLET * nz        ' highest point of the duct

    ' The volute: a horizontal duct outside the barrel, flush with the
    ' roof, and the spiral it winds into. See VOLUTE_OVERLAP.
    rTongue = R + INLET_TONGUE
    rScroll0 = rTongue + W_INLET
    If VOLUTE_ON Then
        yMid = rTongue + 0.5 * W_INLET
        ceY = yMid
        ceZ = zRoof - 0.5 * H_INLET
        zDuctTop = zRoof

        ' Fluid area between r = R and the spiral over the half turn:
        ' with r linear in phi, the integral of r^2 is closed form.
        aScroll = 0.5 * (PI * (rScroll0 ^ 3 - rTongue ^ 3) / (3# * W_INLET) - PI * R * R)

        ' The spiral's extremes in x and y, sampled finely enough that
        ' the step is far below BOX_TOL.
        xScrollMax = 0#: yScrollMin = 0#
        For k = 0 To 3600
            ph = PI * k / 3600#
            rr = rScroll0 - W_INLET * ph / PI
            If rr * Sin(ph) > xScrollMax Then xScrollMax = rr * Sin(ph)
            If rr * Cos(ph) < yScrollMin Then yScrollMin = rr * Cos(ph)
        Next k

        ' The duct runs L_INLET back from the tangent plane x = 0, but
        ' on a wide barrel the barrel itself reaches further (C4:
        ' R = 3.15 against L = 3.0).
        xLo2 = -MaxD(L_INLET, R)
        yLo2 = yScrollMin
        xHi2 = xScrollMax
        yHi2 = rScroll0
    Else
        xLo2 = ceX - 0.5 * H_INLET * nx
        yLo2 = -R
        xHi2 = R
        yHi2 = R
    End If

    ' ---- closed-form volumes, one per build stage ----
    vEquip = PI * R * R * H_BARREL _
           + (PI / 3#) * H_CONE * (R * R + R * rDust + rDust * rDust)

    ' The duct outside the barrel. Integrating the free axial length
    ' over the section gives a closed form; the part that varies
    ' along the section's own "up" axis cancels by symmetry.
    vDuctFree = H_INLET * L_INLET * wDuct - (H_INLET / nz) * Segment(R, yInner, yOuter)

    ' Less the wedge the tongue keeps out of the fluid: the part of
    ' the duct between x = -xTrim and the tangent plane that lay
    ' outside the barrel. Seen from the y axis that region runs from
    ' yOuter - INLET_TONGUE to yOuter, and the closed form is the
    ' rectangle minus the circular segment under it.
    vDuctFree = vDuctFree - (H_INLET / nz) * _
                (xTrim * INLET_TONGUE - Segment(R, yOuter - INLET_TONGUE, yOuter))

    ' The volute lies wholly outside the barrel but for its inner arc,
    ' which the merge eats: duct plus spiral, one inlet height deep.
    If VOLUTE_ON Then vDuctFree = H_INLET * (L_INLET * W_INLET + aScroll)

    vPipe = PI * rVortex * rVortex * (zOutletTop - zRoof)
    vWall = PI * ((rVortex + VORTEX_WALL) ^ 2 - rVortex * rVortex) * L_VORTEX

    ' Pappus: a section swept about an axis it does not cross sweeps
    ' its area times the path of its centroid, here an arc of radius
    ' rBend through the bend angle. Exact, not an approximation, while
    ' rBend > rVortex.
    vElbow = PI * rVortex * rVortex * (OUTLET_TURN_DEG * PI / 180# * rBend)
    If OUTLET_TURN_DEG = 90# Then
        vLeg = PI * rVortex * rVortex * legLen
    Else
        vLeg = PI * rVortex * rVortex * (zOutletTop - zGasOut)
    End If

    ' The transition runs RISER_TRANS_LEN back along the duct axis
    ' from the inlet face; its round end, centred at G, is where the
    ' bend ends. The bend's axis is rRiserBend below G along the
    ' section's "up", so its last section is that circle. Swept from
    ' straight up through 90 deg plus the slope, it passes the
    ' vertical on the way, so its top is the outer radius right above
    ' the axis.
    rRiser = Sqr(RISER_AREA_SHARE * 0.25 * D_RISER_SRC * D_RISER_SRC)
    rRiserBend = RISER_BEND_R_OVER_D * 2# * rRiser
    gX = ceX - RISER_TRANS_LEN * dx
    gZ = ceZ - RISER_TRANS_LEN * dz
    xRiserAxis = gX - rRiserBend * nx
    zRiserTop = gZ - rRiserBend * nz
    xRiser = xRiserAxis - rRiserBend
    zRiserBendTop = zRiserTop + rRiserBend + rRiser
    zFeed = zRiserTop - RISER_ABOVE_FEED
    zRiserBot = zFeed - RISER_BELOW_FEED

    ' The chute starts on the riser's axis, low enough that its axis
    ' meets the wall at zFeed, and runs FEED_DEPTH past the wall.
    ' Checked here, not in PreChecks: at 90 deg the lines below divide
    ' by zero before PreChecks runs.
    If FEED_SLOPE_DEG < 0# Or FEED_SLOPE_DEG >= 90# Then
        Fail "FEED_SLOPE_DEG is " & Fmt(FEED_SLOPE_DEG) & "; the chute has to slope between " & _
             "0 (horizontal) and 90 deg (vertical, which would run along the riser wall)."
    End If
    thF = FEED_SLOPE_DEG * PI / 180#
    fx = -Cos(thF): fz = Sin(thF)
    wx = Sin(thF): wz = Cos(thF)
    zFeedStart = zFeed - rRiser * (fz / -fx)
    lFeed = rRiser / -fx + FEED_DEPTH
    xFeedEnd = xRiser + lFeed * fx
    zFeedEnd = zFeedStart + lFeed * fz
    ' the end face's corner furthest out, the lower one
    xBoxMin = xFeedEnd - 0.5 * FEED_H * wx
    yBoxMax = R
    If yMid + rRiser > yBoxMax Then yBoxMax = yMid + rRiser

    ' Pappus again: the disc's centroid sits on the centreline.
    vRiserBend = PI * rRiser * rRiser * rRiserBend * (0.5 * PI + th)
    vRiser = PI * rRiser * rRiser * (RISER_ABOVE_FEED + RISER_BELOW_FEED)

    ' The loft from the disc to the duct's rectangle has no closed
    ' form -- it depends on how SolidWorks pairs the two outlines --
    ' so it is held between the two prisms it has to lie between, and
    ' the mean of its end areas is only reported against.
    vTransLo = RISER_TRANS_LEN * wDuct * H_INLET
    vTransHi = RISER_TRANS_LEN * PI * rRiser * rRiser
    vTransMid = 0.5 * (vTransLo + vTransHi)

    ' The chute starts on the riser's axis and runs out through the
    ' wall. A line of it at (y, w) in its section leaves the riser
    ' where the horizontal reach s cos + w sin equals sqrt(r^2 - y^2);
    ' the w part is odd across the section and cancels, as it does for
    ' the duct, so what the merge keeps is the prism less the circular
    ' segment stretched by 1 / cos. At 0 deg this is a plain stub.
    vFeed = FEED_H * (FEED_W * lFeed - Segment(rRiser, -0.5 * FEED_W, 0.5 * FEED_W) / -fx)

    vStage1 = vEquip                       ' barrel + cone
    vStage2 = vStage1 + vDuctFree          ' + inlet duct
    vStage3 = vStage2 - vWall              ' - vortex finder wall
    vStage4 = vStage3 + vPipe              ' + outlet pipe above the roof
    vStage5 = vStage4 + vElbow             ' + 180 deg gooseneck, or 90 deg elbow
    vStage6 = vStage5 + vLeg               ' + drop, or run, to the outlet face
    vStage7 = vStage6 + vRiserBend         ' + riser bend, a second body for now
    vStage8 = vStage7 + vRiser             ' + straight riser, same second body
    vStage9 = vStage8 + vTransMid          ' + loft joining the two; measured once built
    If RISER_ON Then
        vFinal = vStage9 + vFeed           ' + meal feed chute; re-based on the measured loft
        outName = CYCLONE_NAME & "_riser"
    Else
        vFinal = vStage6
        outName = CYCLONE_NAME
    End If

End Sub

' Integral of sqrt(R^2 - y^2) dy from y0 to y1.
Private Function Segment(ByVal Rr As Double, ByVal y0 As Double, ByVal y1 As Double) As Double
    Segment = SegAntider(Rr, y1) - SegAntider(Rr, y0)
End Function

Private Function SegAntider(ByVal Rr As Double, ByVal y As Double) As Double
    Dim q As Double
    q = Rr * Rr - y * y
    If q < 0# Then q = 0#
    SegAntider = 0.5 * y * Sqr(q) + 0.5 * Rr * Rr * ASin(y / Rr)
End Function

' How far the feed chute's hole in the riser wall reaches from zFeed.
' Its edges leave the wall where s cos = sqrt(r^2 - y^2) -+ (H/2) sin,
' which puts them (H/2) / cos above and below zFeed on the chute's
' mid-plane; towards the sides the wall curves in, which drops both
' edges by up to (r - sqrt(r^2 - (W/2)^2)) tan. The upper edge gains
' nothing from that, the lower one loses it, and this returns the
' larger reach, the lower one.
Private Function FeedHoleHalf() As Double
    FeedHoleHalf = 0.5 * FEED_H / -fx + _
                   (rRiser - Sqr(rRiser * rRiser - 0.25 * FEED_W * FEED_W)) * (fz / -fx)
End Function

Private Function ASin(ByVal v As Double) As Double
    If v >= 1# Then ASin = PI / 2#: Exit Function
    If v <= -1# Then ASin = -PI / 2#: Exit Function
    ASin = Atn(v / Sqr(1# - v * v))
End Function


'==================================================================
' (c) Pre-checks. The four the deleted cyclone_layout() enforced,
'     plus the two the 5 deg slope introduces. A combination that
'     cannot be built is refused; no dimension is ever adjusted to
'     make it buildable.
'==================================================================
Private Sub PreChecks()

    ' The checks common to both inlets, then the slot's or the
    ' volute's own.
    If OUTLET_TURN_DEG <> 180# And OUTLET_TURN_DEG <> 90# Then
        Fail "OUTLET_TURN_DEG is " & Fmt(OUTLET_TURN_DEG) & "; the outlet bend is built for " & _
             "180 (gooseneck and drop) or 90 (elbow and horizontal run)."
    End If
    If VOLUTE_ON Then
        VolutePreChecks
        Exit Sub
    End If

    ' 1. the inlet face must lie outside the barrel. The slope tilts
    '    the face, so it is the face's edge NEAREST the cyclone that
    '    has to clear it.
    If xInletNear > -reach Then
        Fail "the inlet face reaches x = " & Fmt(xInletNear) & " m, inside the barrel " & _
             "(the barrel reaches x = " & Fmt(-reach) & " m at the duct's inner wall). " & _
             "L_INLET must exceed " & Fmt((reach + 0.5 * H_INLET * nx) / dx) & " m."
    End If

    ' 2. the duct must not reach below the dust outlet
    If zBotAt0 <= 0# Then
        Fail "the inlet duct reaches z = " & Fmt(zBotAt0) & " m, at or below the dust outlet."
    End If

    ' 3. the vortex finder wall must fit between the finder and the barrel
    If rVortex + VORTEX_WALL >= R Then
        Fail "a vortex finder wall of " & Fmt(VORTEX_WALL) & " m does not fit between the " & _
             "finder (D " & Fmt(D_VORTEX) & " m) and the barrel (D " & Fmt(D_BARREL) & " m)."
    End If

    ' 4. the vortex finder must not reach below the dust outlet
    If L_VORTEX >= zRoof Then
        Fail "the vortex finder (" & Fmt(L_VORTEX) & " m) reaches below the dust outlet."
    End If

    ' 5. the duct's inner wall must clear the vortex finder, which it
    '    passes within a few centimetres on these dimensions
    If yInner <= rVortex + VORTEX_WALL Then
        Fail "the duct's inner wall at y = " & Fmt(yInner) & " m runs into the vortex finder " & _
             "(outer radius " & Fmt(rVortex + VORTEX_WALL) & " m). Reduce VORTEX_WALL -- " & _
             "INLET_TANGENT_RELIEF moves the outer wall only and buys no clearance here."
    End If

    ' 6. the opening must fit under the roof with its clearance intact.
    '    At zero clearance the duct's roof, the cyclone's roof and the
    '    barrel all meet at a single point, which is degenerate.
    If INLET_ROOF_CLEARANCE <= 0# And INLET_SLOPE_DEG <> 0# Then
        Fail "INLET_ROOF_CLEARANCE is " & Fmt(INLET_ROOF_CLEARANCE) & " m. With a sloped " & _
             "duct it has to be positive, or the duct roof, the cyclone roof and the " & _
             "barrel meet at one degenerate point."
    End If
    If zTopAt0 + reach * (nx / nz) > zRoof + 0.000000001 Then
        Fail "the inlet opening reaches z = " & Fmt(zTopAt0 + reach * (nx / nz)) & _
             " m, above the roof at z = " & Fmt(zRoof) & " m."
    End If

    ' NOTE deliberately absent: "the duct must stay above the cone".
    ' On C2-C5 the published inlet is taller than the barrel and the
    ' duct runs down into the cone region. That is what the
    ' catalogue describes and it is built as described.

    ' The sizing cylinder's wall is a refinement front, not a
    ' surface, and a front that coincides with real geometry makes
    ' slivers there. Keep it in open fluid on both sides: inside the
    ' vortex finder's bore or outside its shell, never on either
    ' surface or in the annulus between them.
    BoiPreChecks

    ' 8. the tongue
    If INLET_TONGUE <= 0# Then
        Fail "INLET_TONGUE is " & Fmt(INLET_TONGUE) & " m. At zero the duct's outer wall " & _
             "runs onto the barrel's tangent line and the union closes to a zero-angle " & _
             "edge, which no mesh size can resolve."
    End If
    If INLET_TANGENT_RELIEF <> 0# Then
        Fail "INLET_TONGUE and INLET_TANGENT_RELIEF are both set. The tongue's volume term " & _
             "assumes the duct's outer wall is the barrel's own tangent plane, and the two " & _
             "together have not been worked out. Use the tongue and leave the relief at 0."
    End If
    If xTrim >= reach Then
        Fail "the tongue stops the duct at x = " & Fmt(-xTrim) & " m, at or outside where " & _
             "its inner wall meets the barrel (" & Fmt(-reach) & " m); the duct would never " & _
             "break into the shell. Reduce INLET_TONGUE."
    End If

    OutletPreChecks
    RiserPreChecks

    Note "equipment volume (barrel + cone)  " & Fmt(vEquip) & " m3"
    Note "CFD domain volume                 " & Fmt(vFinal) & " m3"
    Note "duct top / bottom at x = 0        " & Fmt(zTopAt0) & " / " & Fmt(zBotAt0) & " m"
    Note "vortex finder clearance           " & Fmt(yInner - rVortex - VORTEX_WALL) & " m"
    Note "built duct width                  " & Fmt(wDuct) & " m (catalogue " & _
         Fmt(W_INLET) & " less " & Fmt(INLET_TANGENT_RELIEF) & " tangency relief)"
    Note "tongue                            " & Fmt(INLET_TONGUE) & " m thick, duct stops at x = " & _
         Fmt(-xTrim) & " m"
    OutletNote
    If RISER_ON Then
        Note "riser: D " & Fmt(2# * rRiser) & " m at x = " & Fmt(xRiser) & ", z " & Fmt(zRiserBot) & _
             " .. " & Fmt(zRiserTop) & " m, bend R " & Fmt(rRiserBend) & " m to z " & _
             Fmt(zRiserBendTop) & " m"
        Note "feed chute: " & Fmt(FEED_SLOPE_DEG) & " deg, meets the riser wall at z " & Fmt(zFeed) & _
             " m, end face centred (" & Fmt(xFeedEnd) & ", " & Fmt(yMid) & ", " & Fmt(zFeedEnd) & ")"
        Note "transition: " & Fmt(RISER_TRANS_LEN) & " m from (" & Fmt(gX) & ", " & Fmt(gZ) & _
             "), loft volume expected " & Fmt(vTransLo) & " .. " & Fmt(vTransHi) & " m3"
    End If
End Sub


' The volute's own checks (VOLUTE_ON). The slot's checks 1, 2, 5, 6
' and the tongue's are about a duct that breaks into the shell; this
' one stays outside it.
Private Sub VolutePreChecks()

    If RISER_ON Then
        Fail "RISER_ON with VOLUTE_ON: the riser's transition is built onto the slot duct's " & _
             "section, and joining it to the volute has not been worked out."
    End If
    If INLET_SLOPE_DEG <> 0# Then
        Fail "INLET_SLOPE_DEG is " & Fmt(INLET_SLOPE_DEG) & " with VOLUTE_ON; the volute is " & _
             "built as a horizontal outline extruded from the roof."
    End If
    If W_INLET <= 0# Or H_INLET <= 0# Then
        Fail "the inlet is " & Fmt(W_INLET) & " x " & Fmt(H_INLET) & " m."
    End If
    If INLET_TONGUE <= 0# Then
        Fail "INLET_TONGUE is " & Fmt(INLET_TONGUE) & " m. At zero the volute's walls run onto " & _
             "the barrel's tangent and close to a zero-angle edge."
    End If

    ' The floor must stay above the barrel-to-cone edge, or the two
    ' edges coincide in the merge.
    If zRoof - H_INLET <= H_CONE Then
        Fail "the volute reaches down to z = " & Fmt(zRoof - H_INLET) & " m, at or below the " & _
             "barrel's bottom edge at z = " & Fmt(H_CONE) & " m. Keep H_INLET under H_BARREL."
    End If

    ' The overlap arc must stay in open barrel, clear of the finder.
    If VOLUTE_OVERLAP <= 0# Then
        Fail "VOLUTE_OVERLAP is " & Fmt(VOLUTE_OVERLAP) & " m; the scroll's inner arc has to lie " & _
             "inside the barrel or its face coincides with the barrel's."
    End If
    If R - VOLUTE_OVERLAP <= rVortex + VORTEX_WALL Then
        Fail "the volute's inner arc at r = " & Fmt(R - VOLUTE_OVERLAP) & " m reaches the vortex " & _
             "finder (outer radius " & Fmt(rVortex + VORTEX_WALL) & " m)."
    End If
    If VOLUTE_SPLINE_PTS < 9 Then
        Fail "VOLUTE_SPLINE_PTS is " & VOLUTE_SPLINE_PTS & "; a half turn needs more points."
    End If

    ' The 3 vortex finder checks that hold for any inlet.
    If rVortex + VORTEX_WALL >= R Then
        Fail "a vortex finder wall of " & Fmt(VORTEX_WALL) & " m does not fit between the " & _
             "finder (D " & Fmt(D_VORTEX) & " m) and the barrel (D " & Fmt(D_BARREL) & " m)."
    End If
    If L_VORTEX >= zRoof Then
        Fail "the vortex finder (" & Fmt(L_VORTEX) & " m) reaches below the dust outlet."
    End If

    BoiPreChecks
    OutletPreChecks

    Note "equipment volume (barrel + cone)  " & Fmt(vEquip) & " m3"
    Note "CFD domain volume                 " & Fmt(vFinal) & " m3"
    Note "volute: duct " & Fmt(W_INLET) & " x " & Fmt(H_INLET) & " m, " & Fmt(L_INLET) & _
         " m long, inner wall y = " & Fmt(rTongue) & " m; spiral r " & Fmt(rScroll0) & " -> " & _
         Fmt(rTongue) & " m over 180 deg, " & Fmt(aScroll) & " m2 outside the barrel"
    Note "volute floor at z = " & Fmt(zRoof - H_INLET) & " m; " & _
         Fmt(100# * MaxD(0#, H_INLET - L_VORTEX) / H_INLET) & " % of the opening below the " & _
         "finder's rim"
    OutletNote

End Sub


Private Function MaxD(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then MaxD = a Else MaxD = b
End Function


' The sizing cylinder's checks, the same for both inlets.
Private Sub BoiPreChecks()
    If EXPORT_BOI Then
    If BOI_RADIUS > rVortex - BOI_CLEARANCE And _
       BOI_RADIUS < rVortex + VORTEX_WALL + BOI_CLEARANCE Then
        Fail "the mesh sizing cylinder at r = " & Fmt(BOI_RADIUS) & " m is too close to the " & _
             "vortex finder, whose bore is r = " & Fmt(rVortex) & " m and whose outer radius " & _
             "is " & Fmt(rVortex + VORTEX_WALL) & " m. With " & Fmt(BOI_CLEARANCE) & " m of " & _
             "clearance it has to stay under " & Fmt(rVortex - BOI_CLEARANCE) & " m or over " & _
             Fmt(rVortex + VORTEX_WALL + BOI_CLEARANCE) & " m."
    End If
    If R - BOI_RADIUS < BOI_CLEARANCE Then
        Fail "the mesh sizing cylinder at r = " & Fmt(BOI_RADIUS) & " m comes within " & _
             Fmt(R - BOI_RADIUS) & " m of the barrel wall at r = " & Fmt(R) & " m; it needs " & _
             Fmt(BOI_CLEARANCE) & " m."
    End If
    If zBoiBot >= zBoiTop Then
        Fail "the mesh sizing cylinder has no height left: its floor is at z = " & _
             Fmt(zBoiBot) & " m and its roof at z = " & Fmt(zBoiTop) & " m."
    End If
    End If
End Sub


Private Sub OutletNote()
    If OUTLET_TURN_DEG = 90# Then
        Note "outlet: rise to z = " & Fmt(zOutletTop) & " m, elbow R " & Fmt(rBend) & _
             " m over 90 deg, run along +x at z = " & Fmt(zLegAxis) & " m to the outlet face at x = " & _
             Fmt(xGasOut) & " m"
    Else
        Note "outlet: rise to z = " & Fmt(zOutletTop) & " m, bend R " & Fmt(rBend) & _
             " m over 180 deg, drop at x = " & Fmt(xLeg) & " m to the outlet face at z = " & Fmt(zGasOut) & " m"
    End If
End Sub


' 9. the outlet bend, either way round.
Private Sub OutletPreChecks()

    ' At rBend <= rVortex the inner wall of the
    '    bend passes through the axis it is swept about and the solid
    '    folds through itself; Pappus stops being the volume, too.
    If rBend <= rVortex Then
        Fail "the outlet bend radius " & Fmt(rBend) & " m is not larger than the pipe radius " & _
             Fmt(rVortex) & " m; the bend would fold through itself. ELBOW_R_OVER_VORTEX_D " & _
             "must exceed 0.5."
    End If
    If OUTLET_DOWN_OVER_VORTEX_D <= 0# Then
        Fail "OUTLET_DOWN_OVER_VORTEX_D is " & Fmt(OUTLET_DOWN_OVER_VORTEX_D) & ". The outlet face " & _
             "would sit on the end of the bend, where the flow is still turning."
    End If
    If OUTLET_EXT_OVER_VORTEX_D <= 0# Then
        Fail "OUTLET_EXT_OVER_VORTEX_D is " & Fmt(OUTLET_EXT_OVER_VORTEX_D) & ". The bend has to " & _
             "start above the roof, not on it."
    End If
    If OUTLET_TURN_DEG = 180# Then
    If xLeg - rVortex <= R Then
        Fail "the outlet drop's inner wall at x = " & Fmt(xLeg - rVortex) & " m is not clear of " & _
             "the barrel (x = " & Fmt(R) & " m). Raise ELBOW_R_OVER_VORTEX_D."
    End If
    ' The drop stands clear of the barrel in x, so it may come down
    ' past the roof; it only has to stay above the dust outlet.
    If zGasOut <= 0# Then
        Fail "the outlet drop comes down to z = " & Fmt(zGasOut) & " m, at or below the dust " & _
             "outlet."
    End If
    If VOLUTE_ON And xLeg - rVortex <= xScrollMax Then
        Fail "the outlet drop's inner wall at x = " & Fmt(xLeg - rVortex) & " m comes down onto " & _
             "the volute, which reaches x = " & Fmt(xScrollMax) & " m."
    End If
    Else
    ' The 90 deg elbow and its run stay above the rise's top, so
    ' they clear the roof, and the volute under it, by construction;
    ' what is checked is that the run's underside really is up there.
    If zLegAxis - rVortex <= zRoof Then
        Fail "the outlet run's underside at z = " & Fmt(zLegAxis - rVortex) & " m is not above " & _
             "the roof at z = " & Fmt(zRoof) & " m."
    End If
    End If

End Sub


' 10. the riser. Built outside everything else by construction;
'     these say so with the numbers.
Private Sub RiserPreChecks()

    If RISER_ON Then
    If RISER_BEND_R_OVER_D <= 0.5 Then
        Fail "RISER_BEND_R_OVER_D is " & Fmt(RISER_BEND_R_OVER_D) & ". At 0.5 or under the " & _
             "riser bend's inner wall reaches its own axis and the solid folds through itself."
    End If
    If RISER_TRANS_LEN <= 0# Then
        Fail "RISER_TRANS_LEN is " & Fmt(RISER_TRANS_LEN) & " m; the round riser needs a " & _
             "transition to reach the duct's rectangle."
    End If
    If 2# * rRiser <= wDuct Then
        Fail "the riser (D " & Fmt(2# * rRiser) & " m) is no wider than the duct (" & _
             Fmt(wDuct) & " m); the transition would be a diffuser."
    End If
    ' The circle at the transition's round end lies in a plane normal
    ' to the duct axis; its furthest reach towards +x is r along n.
    If gX + rRiser * nx >= -R Then
        Fail "the transition's round end reaches x = " & Fmt(gX + rRiser * nx) & " m, not clear " & _
             "of the barrel (x = " & Fmt(-R) & " m). Lengthen RISER_TRANS_LEN."
    End If
    If xInletNear >= -rVortex Then
        Fail "the inlet face reaches x = " & Fmt(xInletNear) & " m, into the outlet pipe " & _
             "above the roof (|x| <= " & Fmt(rVortex) & " m)."
    End If
    If zRiserBendTop >= zOutletTop Then
        Fail "the riser bend rises to z = " & Fmt(zRiserBendTop) & " m, past the start of the " & _
             "outlet bend at z = " & Fmt(zOutletTop) & " m."
    End If
    ' The chute's hole in the wall reaches at most this far above and
    ' below zFeed: its section's height, stretched by the slope, plus
    ' the rise across half its width where the wall curves back.
    If RISER_ABOVE_FEED <= FeedHoleHalf() Or RISER_BELOW_FEED <= FeedHoleHalf() Then
        Fail "the feed chute's hole in the riser wall reaches " & Fmt(FeedHoleHalf()) & _
             " m above and below the feed; it does not fit between the riser's bend and its " & _
             "inlet face."
    End If
    If FEED_W >= 2# * rRiser Then
        Fail "the feed chute (" & Fmt(FEED_W) & " m wide) does not fit on the riser (D " & _
             Fmt(2# * rRiser) & " m)."
    End If
    ' The end face has to lie wholly outside the riser, or part of the
    ' meal_feed face is inside it and merges away. Its nearest edge,
    ' the upper one, reaches in by half the section times the sine.
    If FEED_DEPTH * -fx <= 0.5 * FEED_H * wx Then
        Fail "the feed chute's end face reaches back into the riser; FEED_DEPTH must exceed " & _
             Fmt(0.5 * FEED_H * wx / -fx) & " m at " & Fmt(FEED_SLOPE_DEG) & " deg."
    End If
    ' The start face has to lie wholly inside the riser, above its
    ' inlet face, or the closed-form volume counts a piece that is not
    ' there. Across it the reach is at most half the section times the
    ' sine, and half the width across.
    If Sqr((0.5 * FEED_H * wx) ^ 2 + (0.5 * FEED_W) ^ 2) >= rRiser Then
        Fail "the feed chute's start face does not fit inside the riser."
    End If
    If zFeedStart - 0.5 * FEED_H * wz <= zRiserBot Then
        Fail "the feed chute starts at z = " & Fmt(zFeedStart - 0.5 * FEED_H * wz) & _
             " m, below the riser's inlet face at z = " & Fmt(zRiserBot) & " m."
    End If
    If zRiserBot <= 0# Then
        Fail "the riser's inlet face is at z = " & Fmt(zRiserBot) & " m, at or below the " & _
             "dust outlet."
    End If
    End If

End Sub


'==================================================================
' (d) Build
'
' Six features, ten with the riser, all merged on creation, so no
' Combine feature is needed. The part holds one solid body except
' while the riser waits for the transition loft to join it on.
'==================================================================
Private Sub Build()

    Dim planeX0 As SldWorks.Feature       ' the x = 0 plane
    Dim planeY0 As SldWorks.Feature       ' the y = 0 plane
    Dim planeDuct As SldWorks.Feature     ' y = yInner, the duct's inner wall
    Dim planeZ0 As SldWorks.Feature       ' the z = 0 plane
    Dim planeBend As SldWorks.Feature     ' z = zOutletTop: the gooseneck starts and ends here
    Dim planeRiser As SldWorks.Feature    ' z = zRiserTop, where the riser meets its bend
    Dim planeFeed As SldWorks.Feature     ' y = yMid - FEED_W / 2, the feed chute's side wall
    Dim planeRoof As SldWorks.Feature     ' z = zRoof, the volute's outline
    Dim planeLeg As SldWorks.Feature      ' x = rBend, where the 90 deg elbow ends
    Dim xMin5 As Double
    Dim f As SldWorks.Feature

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    ' Verification on rebuild is slower but it is what makes a
    ' boolean that produced non-manifold geometry fail loudly
    ' instead of being quietly accepted.
    oldVerify = swApp.GetUserPreferenceToggle(swPerformanceVerifyOnRebuild)
    oldInputDim = swApp.GetUserPreferenceToggle(swInputDimValOnCreate)
    swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, True
    swApp.SetUserPreferenceToggle swInputDimValOnCreate, False
    prefsTouched = True

    ' exact coordinates: no inferencing, no snapping, no auto relations
    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    Set planeX0 = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX0 Is Nothing Then Fail "could not find the default plane whose normal is X."
    Set planeY0 = FindPlaneWithNormal(0#, 1#, 0#)
    If planeY0 Is Nothing Then Fail "could not find the default plane whose normal is Y."
    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."

    '--- 0. measure every plane's sketch axes ------------------------
    ' All probes run while the part is still empty. Once the barrel
    ' is there a probe would land inside it, merge with it, and then
    ' measure the merged body instead of itself.
    If VOLUTE_ON Then
        Set planeRoof = OffsetPlane(planeZ0, 0#, 0#, zRoof, uSignR, vSignR)
    Else
        Set planeDuct = OffsetPlane(planeY0, 0#, yInner, 0#, uSignD, vSignD)
    End If
    Set planeBend = OffsetPlane(planeZ0, 0#, 0#, zOutletTop, uSignZ, vSignZ)
    If OUTLET_TURN_DEG = 90# Then
        Set planeLeg = OffsetPlane(planeX0, rBend, 0#, 0#, uSignL, vSignL)
    End If
    If RISER_ON Then
        Set planeRiser = OffsetPlane(planeZ0, 0#, 0#, zRiserTop, uSignQ, vSignQ)
        Set planeFeed = OffsetPlane(planeY0, 0#, yMid - 0.5 * FEED_W, 0#, uSignF, vSignF)
    End If
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX

    '--- 1. barrel + cone -------------------------------------------
    Set f = RevolveProfile(planeX0, Array( _
        0#, 0#, _
        rDust, 0#, _
        R, H_CONE, _
        R, zRoof, _
        0#, zRoof), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the barrel + cone profile."
    CheckStage "1  barrel + cone", vStage1, -R, -R, 0#, R, R, zRoof

    '--- 2. inlet duct, or volute -----------------------------------
    If VOLUTE_ON Then
        Set f = ExtrudeVolute(planeRoof)
    Else
        Set f = ExtrudeInlet(planeDuct)
    End If
    If f Is Nothing Then Fail "FeatureExtrusion3 failed on the inlet duct."
    CheckStage "2  + inlet duct", vStage2, _
               xLo2, yLo2, 0#, xHi2, yHi2, zDuctTop

    '--- 3. carve out the vortex finder wall ------------------------
    ' The tool runs past the roof into empty space on purpose: a cut
    ' tool that ends flush with a face of the target is the classic
    ' way to upset a boolean. Nothing exists above the roof yet.
    Set f = RevolveProfile(planeX0, Array( _
        rVortex, zVortexBottom, _
        rVortex + VORTEX_WALL, zVortexBottom, _
        rVortex + VORTEX_WALL, zRoof + 0.5, _
        rVortex, zRoof + 0.5), True)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the vortex finder wall."
    CheckStage "3  - vortex finder wall", vStage3, _
               xLo2, yLo2, 0#, xHi2, yHi2, zDuctTop

    '--- 4. outlet pipe above the roof ------------------------------
    Set f = RevolveProfile(planeX0, Array( _
        0#, zRoof, _
        rVortex, zRoof, _
        rVortex, zOutletTop, _
        0#, zOutletTop), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the outlet pipe."
    CheckStage "4  + outlet pipe", vStage4, _
               xLo2, yLo2, 0#, xHi2, yHi2, zOutletTop

    '--- 5. 180 deg gooseneck ---------------------------------------
    ' It goes over to +x and ends back in the plane z = zOutletTop,
    ' so it takes the box to the far wall of the drop; in -x the inlet
    ' face is still the extreme.
    xMin5 = xLo2
    If OUTLET_TURN_DEG = 90# Then
        ' The 90 deg elbow ends at x = rBend, facing +x; the run
        ' takes the box on to the outlet face.
        Set f = RevolveElbow(planeBend, 0.5 * PI)
        CheckStage "5  + outlet elbow", vStage5, _
                   xMin5, yLo2, 0#, MaxD(xHi2, rBend), yHi2, zElbowTop

        '--- 6. horizontal run to the outlet face --------------------
        Set f = ExtrudeRun(planeLeg)
        CheckStage "6  + outlet run", vStage6, _
                   xMin5, yLo2, 0#, xBoxMax, yHi2, zElbowTop
    Else
        Set f = RevolveElbow(planeBend, PI)
        CheckStage "5  + outlet gooseneck", vStage5, _
                   xMin5, yLo2, 0#, xBoxMax, yHi2, zElbowTop

        '--- 6. drop to the outlet face -----------------------------
        Set f = ExtrudeLeg(planeBend)
        CheckStage "6  + outlet drop", vStage6, _
                   xMin5, yLo2, 0#, xBoxMax, yHi2, zElbowTop
    End If

    ' The riser and its bend are built apart from the cyclone as a
    ' second body -- the transition that joins them is a loft between
    ' two faces that have to exist first -- so stages 7 and 8 are
    ' checked on the two bodies together. They reach past the inlet
    ' face in -x and past the barrel in y, which moves the box.
    If RISER_ON Then
        '--- 7. round riser bend, ending on the transition's round end
        Set f = RevolveRiserBend(planeRiser)
        CheckBodies "7  + riser bend", 2, vStage7, _
                    xRiser - rRiser, -R, 0#, xBoxMax, yBoxMax, zElbowTop

        '--- 8. round riser down to its gas inlet -------------------
        Set f = ExtrudeRiser(planeRiser)
        CheckBodies "8  + riser", 2, vStage8, _
                    xRiser - rRiser, -R, 0#, xBoxMax, yBoxMax, zElbowTop

        '--- 9. loft from the round end to the duct's rectangle ------
        Set f = LoftTransition()
        CheckBodies "9  + transition", 1, vStage9, _
                    xRiser - rRiser, -R, 0#, xBoxMax, yBoxMax, zElbowTop

        '--- 10. meal feed chute out through the riser wall ----------
        Set f = ExtrudeFeedChute(planeFeed)
        CheckStage "10 + feed chute", vFinal, _
                   xBoxMin, -R, 0#, xBoxMax, yBoxMax, zElbowTop
    End If

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

End Sub


' A closed profile in the x = 0 plane, given as r, z pairs, revolved
' 360 deg about the cyclone axis. Where the profile is closed by a
' segment lying on the axis, that same segment is used as the axis
' of revolution so there is no duplicate centreline for SolidWorks
' to choose between; profiles clear of the axis get one centreline,
' and exactly one.
Private Function RevolveProfile(planeX0 As SldWorks.Feature, pts As Variant, _
                                ByVal isCut As Boolean) As SldWorks.Feature

    Dim n As Long, i As Long, j As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim zLo As Double, zHi As Double
    Dim seg As SldWorks.SketchSegment
    Dim axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim selData As SldWorks.SelectData

    uSign = uSignX: vSign = vSignX

    n = (UBound(pts) + 1) \ 2
    zLo = pts(1): zHi = pts(1)
    For i = 0 To n - 1
        If pts(2 * i + 1) < zLo Then zLo = pts(2 * i + 1)
        If pts(2 * i + 1) > zHi Then zHi = pts(2 * i + 1)
    Next i

    swModel.ClearSelection2 True
    planeX0.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a sketch on the x = 0 plane."
    wRefSet = False

    For i = 0 To n - 1
        j = (i + 1) Mod n
        G2S sk, 0#, pts(2 * i), pts(2 * i + 1), u0, v0
        G2S sk, 0#, pts(2 * j), pts(2 * j + 1), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on the revolve profile."
        If pts(2 * i) = 0# And pts(2 * j) = 0# Then Set axisSeg = seg
    Next i

    If axisSeg Is Nothing Then
        G2S sk, 0#, 0#, zLo, u0, v0
        G2S sk, 0#, 0#, zHi, u1, v1
        Set axisSeg = swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#)
        If axisSeg Is Nothing Then Fail "CreateCenterLine failed on the revolve axis."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set RevolveProfile = swFeat.FeatureRevolve2( _
        True, True, False, isCut, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        True, True, True)

    swModel.ClearSelection2 True

End Function


' A plane parallel to a default plane, through the given model
' point, with the sketch axes on it measured at the same time. The
' point lies on the base plane's normal axis -- (0, y, 0) for the
' y = 0 plane, (0, 0, z) for z = 0 -- so its one nonzero coordinate
' is the offset.
'
' Which side of the base plane InsertRefPlane puts the offset on is
' not ours to choose, and it cannot be read back off the sketch
' transform either. That is how the first C1.step came out with its
' inlet duct mirrored to -y while every check in this file passed:
' the plane answered "yes, the point at +1.30 is on me" while
' sitting at -1.30, the duct was then extruded away from the origin
' as asked and landed at -2.16, and nothing downstream could see
' it. The barrel is symmetric in y, so the bounding box matched;
' a mirror image has the same volume, so the volume matched; the
' inlet face has the same area either way, so the area matched.
'
' So the side is not read, it is measured. The plane is built, a
' test block of known model coordinates is dropped on it and its
' bounding box read back. The box says where the plane really is
' as well as which way its axes run. A plane on the wrong side
' fails that test and is deleted, and the other side is tried.
Private Function OffsetPlane(base As SldWorks.Feature, _
                             ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                             ByRef us As Double, ByRef vs As Double) As SldWorks.Feature

    Dim pl As SldWorks.Feature
    Dim opt As Long
    Dim k As Long
    Dim at As String

    at = "(" & Fmt(bx) & ", " & Fmt(by) & ", " & Fmt(bz) & ")"

    For k = 0 To 1
        opt = swRefPlaneReferenceConstraint_Distance
        If k = 1 Then opt = opt Or swRefPlaneReferenceConstraint_OptionFlip

        swModel.ClearSelection2 True
        base.Select2 False, 0
        Set pl = swFeat.InsertRefPlane(opt, Abs(bx) + Abs(by) + Abs(bz), 0, 0#, 0, 0#)
        swModel.ClearSelection2 True
        If pl Is Nothing Then
            Fail "InsertRefPlane failed for the offset plane through " & at & "."
        End If

        If TryCalibrateSketchAxes(pl, bx, by, bz, us, vs) Then
            Note "offset plane measured through " & at
            Set OffsetPlane = pl
            Exit Function
        End If

        swModel.ClearSelection2 True
        pl.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    Next k

    Fail "the offset plane could not be placed through " & at & "; a test block " & _
         "dropped on it landed somewhere else both ways round."

End Function


' The duct.
'
' Drawn as its SIDE VIEW -- the quadrilateral the duct cuts in the
' x-z plane -- on the plane of its own inner wall, then extruded
' straight along y by the inlet width. The 5 deg slope and the
' tilted inlet face are carried by the sketch, so the extrusion
' itself is an ordinary blind one along a principal axis.
'
' The quadrilateral's downstream edge is x = -xTrim: the duct stops
' INLET_TONGUE of shell short of the barrel's tangent plane rather
' than running into it. See INLET_TONGUE for why.
'
' Its end cap does not become a wall across the opening. Below
' y = R - INLET_TONGUE the cap is inside the barrel and dissolves
' in the merge, exactly as the cap at x = 0 used to; only the strip
' above that survives, and that strip is the tongue. What the duct
' must not do is run PAST the tangent plane, where it would break
' back out through the far side of the shell -- at y = R the barrel
' reaches no further than x = 0.
Private Function ExtrudeInlet(planeDuct As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim hh As Double
    Dim qx(3) As Double, qz(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim i As Long, j As Long, k As Long
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant

    uSign = uSignD: vSign = vSignD

    hh = 0.5 * H_INLET

    qx(0) = ceX - hh * nx: qz(0) = ceZ - hh * nz      ' inlet face, bottom
    qx(1) = ceX + hh * nx: qz(1) = ceZ + hh * nz      ' inlet face, top
    ' The duct slopes down towards the cyclone, so stepping xTrim
    ' back up the axis lifts both edges by xTrim * tan(slope), and
    ' nx / nz is that tangent -- the same ratio PreChecks uses.
    qx(2) = -xTrim:        qz(2) = zTopAt0 + xTrim * (nx / nz)   ' tongue, top
    qx(3) = -xTrim:        qz(3) = zBotAt0 + xTrim * (nx / nz)   ' tongue, bottom

    swModel.ClearSelection2 True
    planeDuct.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the inlet duct sketch."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, qx(i), yInner, qz(i), u0, v0
        G2S sk, qx(j), yInner, qz(j), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
            Fail "CreateLine failed on the inlet duct side view."
        End If
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    ' Blind, one inlet width along y. The duct has to end up on the
    ' +y side, between yInner and yOuter; if the first direction put
    ' it on the other side the volume is wrong, so undo and reverse.
    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            wDuct, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody("2  + inlet duct")
            mp = body.GetMassProperties(1000#)
            If Abs(mp(3) - vStage2) <= VOL_TOL * vStage2 Then
                Set ExtrudeInlet = f
                Exit Function
            End If
            Note "inlet duct extruded the wrong way (volume " & Fmt(mp(3)) & _
                 " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the inlet duct could not be extruded to the right volume in either " & _
         "direction along y. Expected " & Fmt(vStage2) & " m3 after the merge."

End Function


' The volute (VOLUTE_ON): its outline in the roof plane, extruded
' down by the inlet height. The outline, going round it:
'
'   A (-L, rT)   inlet face, inner corner       rT = R + INLET_TONGUE
'   B (-L, rS)   inlet face, outer corner       rS = rT + W_INLET
'   C ( 0, rS)   end of the duct's outer wall, start of the spiral
'   spline       r = rS - W phi / pi, clockwise from +y over the
'                +x side, to
'   E ( 0, -rT)  end of the spiral
'   F ( 0, -rI)  radially in to the overlap arc  rI = R - VOLUTE_OVERLAP
'   arc          through (rI, 0) to
'   G ( 0, rI)
'   H ( 0, rT)   radially out: the tongue's face
'   back to A    the duct's inner wall
'
' The arc and the inner ends of the two radial lines lie inside the
' barrel and dissolve in the merge; what is left at x = 0 on either
' side is a blunt face INLET_TONGUE wide, the cut-water.
'
' Which way the extrusion goes is measured as everywhere else: up it
' would only touch the barrel along the roof's edge and leave a second
' body, so the body count, the volume and the box top all say.
Private Function ExtrudeVolute(planeRoof As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim rT As Double, rS As Double, rI As Double
    Dim gx(6) As Double, gy(6) As Double
    Dim pd() As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double, u2 As Double, v2 As Double
    Dim ph As Double, rr As Double
    Dim i As Long, k As Long, n As Long
    Dim bodies As Variant, mp As Variant, box As Variant
    Dim ok As Boolean

    uSign = uSignR: vSign = vSignR

    rT = rTongue
    rS = rScroll0
    rI = R - VOLUTE_OVERLAP

    swModel.ClearSelection2 True
    planeRoof.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the volute sketch."
    wRefSet = False

    ' The straight sides: H -> A -> B -> C, then E -> F and G -> H.
    gx(0) = 0#: gy(0) = rT              ' H
    gx(1) = -L_INLET: gy(1) = rT        ' A
    gx(2) = -L_INLET: gy(2) = rS        ' B
    gx(3) = 0#: gy(3) = rS              ' C
    For i = 0 To 2
        G2S sk, gx(i), gy(i), zRoof, u0, v0
        G2S sk, gx(i + 1), gy(i + 1), zRoof, u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
            Fail "CreateLine failed on the volute's duct."
        End If
    Next i

    ' The spiral, C to E. Its two ends are set exactly rather than
    ' through Sin / Cos, so they meet the lines on either side to the
    ' last bit and the outline closes.
    n = VOLUTE_SPLINE_PTS
    ReDim pd(3 * n - 1)
    For k = 0 To n - 1
        ph = PI * k / (n - 1)
        rr = rS - W_INLET * k / (n - 1)
        If k = 0 Then
            G2S sk, 0#, rS, zRoof, u0, v0
        ElseIf k = n - 1 Then
            G2S sk, 0#, -rT, zRoof, u0, v0
        Else
            G2S sk, rr * Sin(ph), rr * Cos(ph), zRoof, u0, v0
        End If
        pd(3 * k) = u0: pd(3 * k + 1) = v0: pd(3 * k + 2) = 0#
    Next k
    If swSkMgr.CreateSpline2((pd), False) Is Nothing Then
        Fail "CreateSpline2 failed on the volute's spiral."
    End If

    ' E -> F, radially in at the spiral's end.
    G2S sk, 0#, -rT, zRoof, u0, v0
    G2S sk, 0#, -rI, zRoof, u1, v1
    If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateLine failed on the volute's far tongue."
    End If

    ' F -> G, the overlap arc through (rI, 0).
    G2S sk, 0#, -rI, zRoof, u0, v0
    G2S sk, 0#, rI, zRoof, u1, v1
    G2S sk, rI, 0#, zRoof, u2, v2
    If swSkMgr.Create3PointArc(u0, v0, 0#, u1, v1, 0#, u2, v2, 0#) Is Nothing Then
        Fail "Create3PointArc failed on the volute's inner arc."
    End If

    ' G -> H, radially out to the duct's inner wall.
    G2S sk, 0#, rI, zRoof, u0, v0
    G2S sk, 0#, rT, zRoof, u1, v1
    If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateLine failed on the volute's near tongue."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            H_INLET, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            bodies = swPart.GetBodies2(swSolidBody, True)
            ok = False
            If Not IsEmpty(bodies) Then
                If UBound(bodies) = 0 Then
                    mp = bodies(0).GetMassProperties(1000#)
                    box = bodies(0).GetBodyBox
                    ok = Abs(mp(3) - vStage2) <= VOL_TOL * vStage2 And _
                         Abs(box(5) - zRoof) <= BOX_TOL
                End If
            End If
            If ok Then
                Set ExtrudeVolute = f
                Exit Function
            End If
            Note "volute extruded the wrong way; reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the volute could not be extruded down from the roof to the right volume in either " & _
         "direction. Expected one body of " & Fmt(vStage2) & " m3 after the merge."

End Function


' The horizontal run after the 90 deg elbow: the elbow's end section,
' a disc in the plane x = rBend centred at (rBend, 0, zLegAxis),
' extruded along +x to the gas outlet face. Extruded the other way it
' runs back through the elbow and the volume comes out short.
Private Function ExtrudeRun(planeLeg As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim u0 As Double, v0 As Double
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant
    Dim k As Long

    uSign = uSignL: vSign = vSignL

    swModel.ClearSelection2 True
    planeLeg.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the outlet run sketch."
    wRefSet = False

    G2S sk, rBend, 0#, zLegAxis, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rVortex) Is Nothing Then
        Fail "CreateCircleByRadius failed on the outlet run section."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            xGasOut - rBend, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody("6  + outlet run")
            mp = body.GetMassProperties(1000#)
            If Abs(mp(3) - vStage6) <= VOL_TOL * vStage6 And HasPlaneFace(0, xGasOut) Then
                Set ExtrudeRun = f
                Exit Function
            End If
            Note "outlet run extruded the wrong way (volume " & Fmt(mp(3)) & " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the outlet run could not be extruded out to x = " & Fmt(xGasOut) & " m in either " & _
         "direction. Expected " & Fmt(vStage6) & " m3 after the merge."

End Function


' The outlet gooseneck (OUTLET_TURN_DEG 180), or the 90 deg elbow.
'
' The pipe's section at the top of the rise -- a disc in the plane
' z = zOutletTop -- revolved 180 deg about the line through
' (rBend, 0, zOutletTop) parallel to y. That line lies in the same
' plane as the disc, which is what a revolve needs, and it clears the
' disc by rBend - rVortex, so the result is a half torus. It leaves
' the rise going up, goes over the top and comes back down into the
' same plane at x = 2 rBend, facing down.
'
' Which way a revolve turns is not ours to choose any more than which
' way an extrusion goes. Turned the wrong way the bend runs down
' through the pipe and the roof; the volume then comes out short and
' the top of the box stays at the rise. Either says so, and the
' other way is tried.
Private Function RevolveElbow(planeBend As SldWorks.Feature, ByVal ang As Double) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim segs As Variant
    Dim axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant, box As Variant
    Dim i As Long, k As Long

    uSign = uSignZ: vSign = vSignZ

    swModel.ClearSelection2 True
    planeBend.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the outlet gooseneck sketch."
    wRefSet = False

    G2S sk, 0#, 0#, zOutletTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rVortex) Is Nothing Then
        Fail "CreateCircleByRadius failed on the outlet gooseneck section."
    End If
    G2S sk, rBend, -1#, zOutletTop, u0, v0
    G2S sk, rBend, 1#, zOutletTop, u1, v1
    If swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateCenterLine failed on the outlet gooseneck axis."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        ' A segment pointer does not survive a deleted feature, so the
        ' axis is looked up again from the sketch on every attempt.
        Set sk = skFeat.GetSpecificFeature2
        segs = sk.GetSketchSegments
        Set axisSeg = Nothing
        For i = 0 To UBound(segs)
            If segs(i).ConstructionGeometry Then Set axisSeg = segs(i)
        Next i
        If axisSeg Is Nothing Then Fail "the outlet gooseneck sketch has lost its axis."

        swModel.ClearSelection2 True
        Set selData = swModel.SelectionManager.CreateSelectData
        selData.Mark = 16
        axisSeg.Select4 False, selData
        skFeat.Select2 True, 0

        Set f = swFeat.FeatureRevolve2( _
            True, True, False, False, (k = 1), False, _
            0, 0, ang, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            True, True, True)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody("5  + outlet gooseneck")
            mp = body.GetMassProperties(1000#)
            box = body.GetBodyBox
            ' Up or down is all this has to tell apart, so the box is
            ' only asked which side of the rise's top the bend went;
            ' CheckStage then holds the box to BOX_TOL.
            If Abs(mp(3) - vStage5) <= VOL_TOL * vStage5 And _
               box(5) > zOutletTop + 0.5 * rBend Then
                Set RevolveElbow = f
                Exit Function
            End If
            Note "outlet gooseneck turned the wrong way (volume " & Fmt(mp(3)) & " m3, top " & _
                 Fmt(box(5)) & " m); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the outlet gooseneck could not be revolved to the right volume in either direction. " & _
         "Expected " & Fmt(vStage5) & " m3 after the merge, top at z = " & Fmt(zElbowTop) & " m."

End Function


' The straight drop from the end of the gooseneck to the gas outlet
' face: the bend's end section, a disc in the plane z = zOutletTop
' centred at (xLeg, 0), extruded down. Extruded up instead it runs
' back into the bend and the volume comes out short.
Private Function ExtrudeLeg(planeBend As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim u0 As Double, v0 As Double
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant
    Dim k As Long

    uSign = uSignZ: vSign = vSignZ

    swModel.ClearSelection2 True
    planeBend.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the outlet drop sketch."
    wRefSet = False

    G2S sk, xLeg, 0#, zOutletTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rVortex) Is Nothing Then
        Fail "CreateCircleByRadius failed on the outlet drop section."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            zOutletTop - zGasOut, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody("6  + outlet drop")
            mp = body.GetMassProperties(1000#)
            If Abs(mp(3) - vStage6) <= VOL_TOL * vStage6 And HasPlaneFace(2, zGasOut) Then
                Set ExtrudeLeg = f
                Exit Function
            End If
            Note "outlet drop extruded the wrong way (volume " & Fmt(mp(3)) & " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the outlet drop could not be extruded down to z = " & Fmt(zGasOut) & " m in either " & _
         "direction. Expected " & Fmt(vStage6) & " m3 after the merge."

End Function


' The round riser bend.
'
' The riser's disc at the top of the straight riser -- centred on
' (xRiser, yMid) in the plane z = zRiserTop -- revolved through 90 deg
' plus the duct slope about the line through (xRiserAxis, 0,
' zRiserTop) parallel to y. It leaves the riser going up, passes the
' vertical, and ends on the circle at G, normal to the duct axis,
' where the transition will start. The same construction as the
' outlet bend.
'
' It touches nothing yet, so it is a second body either way round.
' Turned the wrong way it swings down instead of up; the riser
' body's own box says which.
Private Function RevolveRiserBend(planeRiser As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim segs As Variant
    Dim axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim box As Variant
    Dim i As Long, k As Long

    uSign = uSignQ: vSign = vSignQ

    swModel.ClearSelection2 True
    planeRiser.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the riser bend sketch."
    wRefSet = False

    G2S sk, xRiser, yMid, zRiserTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rRiser) Is Nothing Then
        Fail "CreateCircleByRadius failed on the riser bend section."
    End If
    G2S sk, xRiserAxis, yMid - 1#, zRiserTop, u0, v0
    G2S sk, xRiserAxis, yMid + 1#, zRiserTop, u1, v1
    If swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateCenterLine failed on the riser bend axis."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        Set sk = skFeat.GetSpecificFeature2
        segs = sk.GetSketchSegments
        Set axisSeg = Nothing
        For i = 0 To UBound(segs)
            If segs(i).ConstructionGeometry Then Set axisSeg = segs(i)
        Next i
        If axisSeg Is Nothing Then Fail "the riser bend sketch has lost its axis."

        swModel.ClearSelection2 True
        Set selData = swModel.SelectionManager.CreateSelectData
        selData.Mark = 16
        axisSeg.Select4 False, selData
        skFeat.Select2 True, 0

        Set f = swFeat.FeatureRevolve2( _
            True, True, False, False, (k = 1), False, _
            0, 0, 0.5 * PI + INLET_SLOPE_DEG * PI / 180#, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            True, True, True)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            box = RiserBodyBox()
            If Not IsEmpty(box) Then
                If box(5) > zRiserTop + 0.5 * rRiserBend Then
                    Set RevolveRiserBend = f
                    Exit Function
                End If
                Note "riser bend turned down (top " & Fmt(box(5)) & " m); reversing"
            End If
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the riser bend could not be revolved upwards in either direction; expected its " & _
         "top at z = " & Fmt(zRiserBendTop) & " m."

End Function


' The box of the riser's own body while it is still apart from the
' cyclone: the one lying wholly on the far side of x = -R. Empty if
' there are not exactly two bodies.
Private Function RiserBodyBox() As Variant

    Dim bodies As Variant, box As Variant
    Dim i As Long

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    If UBound(bodies) <> 1 Then Exit Function
    For i = 0 To 1
        box = bodies(i).GetBodyBox
        If box(3) < -R Then
            RiserBodyBox = box
            Exit Function
        End If
    Next i

End Function


' The straight round riser: the same disc extruded down from the
' bend to the gas inlet face. Extruded up instead it runs into the
' bend, and the overlap takes most of its volume away.
Private Function ExtrudeRiser(planeRiser As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim u0 As Double, v0 As Double
    Dim f As SldWorks.Feature
    Dim got As Double
    Dim k As Long

    uSign = uSignQ: vSign = vSignQ

    swModel.ClearSelection2 True
    planeRiser.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the riser sketch."
    wRefSet = False

    G2S sk, xRiser, yMid, zRiserTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rRiser) Is Nothing Then
        Fail "CreateCircleByRadius failed on the riser section."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            zRiserTop - zRiserBot, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            got = BodiesVolume()
            If Abs(got - vStage8) <= VOL_TOL * vStage8 And HasPlaneFace(2, zRiserBot) Then
                Set ExtrudeRiser = f
                Exit Function
            End If
            Note "riser extruded the wrong way (volume " & Fmt(got) & " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the riser could not be extruded down to z = " & Fmt(zRiserBot) & " m in either " & _
         "direction. Expected " & Fmt(vStage8) & " m3 over the two bodies."

End Function


' The transition: a loft from the bend's round end to the duct's
' rectangular end, merging the riser body into the cyclone.
'
' Both profiles are existing planar faces, found by what they are --
' normal to the duct axis, at the inlet face and RISER_TRANS_LEN
' upstream of it -- so nothing is sketched on a plane tilted with
' the duct, which the axis calibration in this file cannot measure.
'
' A loft between a circle and a rectangle has no closed-form volume,
' so this one stage is held between the two prisms of its end areas
' instead of to the per-mille; the measured value becomes the base
' the feed chute is checked on.
Private Function LoftTransition() As SldWorks.Feature

    Dim bodies As Variant, faces As Variant
    Dim fc As SldWorks.Face2
    Dim duct As SldWorks.Face2, roundEnd As SldWorks.Face2
    Dim ent As SldWorks.Entity
    Dim surf As SldWorks.Surface
    Dim selData As SldWorks.SelectData
    Dim p As Variant
    Dim f As SldWorks.Feature
    Dim b As Long, i As Long
    Dim sOff As Double, got As Double

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "no body to loft the transition on."
    For b = 0 To UBound(bodies)
        faces = bodies(b).GetFaces
        For i = 0 To UBound(faces)
            Set fc = faces(i)
            Set surf = fc.GetSurface
            If surf.IsPlane Then
                p = surf.PlaneParams
                If Abs(p(1)) < DIR_TOL And Abs(Abs(p(0) * dx + p(2) * dz) - 1#) < DIR_TOL Then
                    sOff = (p(3) - ceX) * dx + (p(5) - ceZ) * dz
                    If Abs(sOff) < 0.001 Then
                        Set duct = fc
                    ElseIf Abs(sOff + RISER_TRANS_LEN) < 0.001 Then
                        Set roundEnd = fc
                    End If
                End If
            End If
        Next i
    Next b
    If duct Is Nothing Then Fail "the transition could not find the duct's end face."
    If roundEnd Is Nothing Then Fail "the transition could not find the riser bend's end face."

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 1
    Set ent = roundEnd
    ent.Select4 False, selData
    Set ent = duct
    ent.Select4 True, selData

    Set f = swFeat.InsertProtrusionBlend2( _
        False, True, False, 1#, _
        0, 0, 1#, 1#, True, True, _
        False, 0#, 0#, 0, _
        True, True, True, 0)
    swModel.ClearSelection2 True
    If f Is Nothing Then
        Fail "InsertProtrusionBlend2 refused the loft between the riser bend's round end and " & _
             "the duct's end face."
    End If

    bodies = swPart.GetBodies2(swSolidBody, True)
    If UBound(bodies) <> 0 Then
        Fail "the transition left " & (UBound(bodies) + 1) & " bodies; the loft did not join " & _
             "the riser to the cyclone."
    End If
    got = BodiesVolume()
    If got < vStage8 + vTransLo * (1# - VOL_TOL) Or got > vStage8 + vTransHi * (1# + VOL_TOL) Then
        Fail "the transition added " & Fmt(got - vStage8) & " m3; a loft between these ends " & _
             "has to lie between " & Fmt(vTransLo) & " and " & Fmt(vTransHi) & " m3."
    End If

    Note "transition loft " & Fmt(got - vStage8) & " m3 (mean of the end prisms " & _
         Fmt(vTransMid) & ", " & Fmt(100# * (got - vStage8 - vTransMid) / vTransMid) & " %)"
    vStage9 = got
    vFinal = vStage9 + vFeed
    Set LoftTransition = f

End Function


' The meal feed chute. Drawn as its SIDE VIEW -- the rectangle it
' cuts in the x-z plane, tilted FEED_SLOPE_DEG -- on the plane of its
' own side wall y = yMid - FEED_W / 2, then extruded straight along y
' by its width, as the inlet duct is. It starts on the riser's axis,
' so its lower end lies inside the riser and dissolves in the merge.
'
' Extruded the wrong way along y it lands off the riser's middle and
' cuts a different segment out of it, but only about 0.14 m3 of 250
' different, under VOL_TOL; so the end face is found and its extent
' in y read back, which settles it.
Private Function ExtrudeFeedChute(planeFeed As SldWorks.Feature) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim qx(3) As Double, qz(3) As Double
    Dim hh As Double, y0 As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant
    Dim i As Long, j As Long, k As Long

    uSign = uSignF: vSign = vSignF

    hh = 0.5 * FEED_H
    y0 = yMid - 0.5 * FEED_W

    qx(0) = xRiser - hh * wx:   qz(0) = zFeedStart - hh * wz      ' start, lower edge
    qx(1) = xFeedEnd - hh * wx: qz(1) = zFeedEnd - hh * wz        ' end, lower edge
    qx(2) = xFeedEnd + hh * wx: qz(2) = zFeedEnd + hh * wz        ' end, upper edge
    qx(3) = xRiser + hh * wx:   qz(3) = zFeedStart + hh * wz      ' start, upper edge

    swModel.ClearSelection2 True
    planeFeed.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the feed chute sketch."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, qx(i), y0, qz(i), u0, v0
        G2S sk, qx(j), y0, qz(j), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
            Fail "CreateLine failed on the feed chute side view."
        End If
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            FEED_W, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody("10 + feed chute")
            mp = body.GetMassProperties(1000#)
            If Abs(mp(3) - vFinal) <= VOL_TOL * vFinal And Not FeedEndFace(body) Is Nothing Then
                Set ExtrudeFeedChute = f
                Exit Function
            End If
            Note "feed chute extruded the wrong way along y (volume " & Fmt(mp(3)) & _
                 " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "the feed chute could not be extruded to the right volume in either direction " & _
         "along y. Expected " & Fmt(vFinal) & " m3 and an end face centred at (" & _
         Fmt(xFeedEnd) & ", " & Fmt(yMid) & ", " & Fmt(zFeedEnd) & ")."

End Function


' The feed chute's end face: the plane face normal to the chute axis
' through its end centre, spanning the chute's own width in y.
' Nothing else in the part is normal to that axis; the position and
' the y span are what tell a chute extruded the wrong way along y.
Private Function FeedEndFace(body As SldWorks.Body2) As SldWorks.Face2

    Dim faces As Variant
    Dim surf As SldWorks.Surface
    Dim p As Variant, bx As Variant
    Dim i As Long

    faces = body.GetFaces
    For i = 0 To UBound(faces)
        Set surf = faces(i).GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(p(1)) < DIR_TOL And Abs(Abs(p(0) * fx + p(2) * fz) - 1#) < DIR_TOL Then
                If Abs((p(3) - xFeedEnd) * fx + (p(5) - zFeedEnd) * fz) < 0.0001 Then
                    bx = faces(i).GetBox
                    If Abs(bx(1) - (yMid - 0.5 * FEED_W)) < BOX_TOL And _
                       Abs(bx(4) - (yMid + 0.5 * FEED_W)) < BOX_TOL Then
                        Set FeedEndFace = faces(i)
                        Exit Function
                    End If
                End If
            End If
        End If
    Next i

End Function


' Total volume of every solid body in the part.
Private Function BodiesVolume() As Double

    Dim bodies As Variant, mp As Variant
    Dim i As Long

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    For i = 0 To UBound(bodies)
        mp = bodies(i).GetMassProperties(1000#)
        BodiesVolume = BodiesVolume + mp(3)
    Next i

End Function


' CheckStage for the stages where the riser is still a body of its
' own: the body count, the summed volume and the joint box.
Private Sub CheckBodies(ByVal stage As String, ByVal nBodies As Long, ByVal expected As Double, _
                        ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                        ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double)

    Dim bodies As Variant, box As Variant
    Dim lo(2) As Double, hi(2) As Double
    Dim got As Double
    Dim i As Long, a As Long

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "stage " & stage & " left no solid body."
    If UBound(bodies) + 1 <> nBodies Then
        Fail "stage " & stage & " left " & (UBound(bodies) + 1) & " solid bodies, expected " & _
             nBodies & "."
    End If

    got = BodiesVolume()
    Note "stage " & stage & ": " & Fmt(got) & " m3 (expected " & Fmt(expected) & ")"
    If Abs(got - expected) > VOL_TOL * expected Then
        Fail "stage " & stage & " volume is " & Fmt(got) & " m3 but should be " & _
             Fmt(expected) & " m3 (" & Fmt(100# * (got - expected) / expected) & " %)."
    End If

    For i = 0 To UBound(bodies)
        box = bodies(i).GetBodyBox
        For a = 0 To 2
            If i = 0 Or box(a) < lo(a) Then lo(a) = box(a)
            If i = 0 Or box(a + 3) > hi(a) Then hi(a) = box(a + 3)
        Next a
    Next i
    CheckExtent stage, "x min", lo(0), x0
    CheckExtent stage, "y min", lo(1), y0
    CheckExtent stage, "z min", lo(2), z0
    CheckExtent stage, "x max", hi(0), x1
    CheckExtent stage, "y max", hi(1), y1
    CheckExtent stage, "z max", hi(2), z1

End Sub


' Whether any body has a planar face normal to model axis ax
' (0 = x, 1 = y, 2 = z) lying at that coordinate.
Private Function HasPlaneFace(ByVal ax As Long, ByVal at As Double) As Boolean

    Dim bodies As Variant, faces As Variant
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim b As Long, i As Long

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    For b = 0 To UBound(bodies)
        faces = bodies(b).GetFaces
        For i = 0 To UBound(faces)
            Set surf = faces(i).GetSurface
            If surf.IsPlane Then
                p = surf.PlaneParams
                If Abs(Abs(p(ax)) - 1#) < DIR_TOL And Abs(p(3 + ax) - at) < 0.0001 Then
                    HasPlaneFace = True
                    Exit Function
                End If
            End If
        Next i
    Next b

End Function


'==================================================================
' Sketch plane mapping.
'
' A sketch plane's own (u, v) axes are not the model's X, Y, Z, and
' which way round they go differs from plane to plane. Rather than
' write that mapping out and hope, every point below is given in
' MODEL coordinates and put through the plane's own transform at
' run time.
'
' The third component is compared against the FIRST point drawn in
' the same sketch, not against zero. ModelToSketchTransform's
' translation does not run in the direction its name promises, so
' the absolute value is not a distance from the plane and testing
' it against zero silently accepts a plane mirrored about the
' origin -- which is how the first C1.step came out with its inlet
' duct at -y. Where a plane actually sits is measured instead, by
' OffsetPlane; what is checked here is the thing this comparison
' can settle on its own: that all the points of one sketch are
' coplanar, whatever plane that turns out to be.
'==================================================================
Private Sub G2S(sk As SldWorks.Sketch, ByVal gx As Double, ByVal gy As Double, ByVal gz As Double, _
                ByRef u As Double, ByRef v As Double)

    Dim a As Variant, s As Double, w As Double

    a = sk.ModelToSketchTransform.ArrayData
    s = a(12)
    u = ((a(0) * gx + a(1) * gy + a(2) * gz) * s + a(9)) * uSign
    v = ((a(3) * gx + a(4) * gy + a(5) * gz) * s + a(10)) * vSign
    w = (a(6) * gx + a(7) * gy + a(8) * gz) * s + a(11)

    If Not wRefSet Then
        wRef = w
        wRefSet = True
    ElseIf Abs(w - wRef) > PLANE_TOL Then
        Fail "point (" & Fmt(gx) & ", " & Fmt(gy) & ", " & Fmt(gz) & ") lies " & _
             Fmt(w - wRef) & " m off the plane of the other points in its sketch."
    End If

End Sub


' Which way round a sketch plane's axes actually run.
'
' ModelToSketchTransform says where a model point lands in sketch
' space, but it does not settle the question this macro needs
' answered: draw at those coordinates and where does the geometry
' come out? On the first run the barrel came out with exactly the
' right volume and exactly the wrong sign in z -- mirrored about
' the dust outlet -- and the plane-membership check in G2S cannot
' see that, because a profile in the plane x = 0 stays in that
' plane whichever way up it is drawn.
'
' So the mapping is not reasoned about, it is measured. A small
' rectangle of known model coordinates is drawn, extruded, and its
' bounding box read back; the four sign combinations are tried in
' turn and the one that puts the box where it was asked for is the
' one the rest of the macro uses on that plane. The rectangle is
' deliberately 1 m by 2 m and off the origin, so a swapped or
' shifted axis cannot pass by looking symmetric. The probe is
' removed before anything real is built.
'
' Calibration is per plane: the revolve profiles and the duct's
' side view sit on planes with different normals, and nothing says
' the two share a convention.
Private Sub CalibrateSketchAxes(pl As SldWorks.Feature, _
                                ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                ByRef us As Double, ByRef vs As Double)

    If Not TryCalibrateSketchAxes(pl, bx, by, bz, us, vs) Then
        Fail "sketch axis calibration failed on plane " & pl.Name & ": no combination of " & _
             "sketch axis signs put a test block where it was asked for. Either the sketch " & _
             "axes are not a sign flip of the model axes on this plane, or the plane is not " & _
             "where it was asked to be."
    End If

End Sub


' The same measurement, reporting failure instead of stopping the
' macro, so OffsetPlane can use a failed calibration as its signal
' that a candidate plane came out on the wrong side.
Private Function TryCalibrateSketchAxes(pl As SldWorks.Feature, _
                                        ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                        ByRef us As Double, ByRef vs As Double) As Boolean

    Dim mx As Double, my As Double, mz As Double
    Dim i1 As Long, i2 As Long
    Dim p0(2) As Double, p1(2) As Double
    Dim k As Long

    PlaneNormal pl, mx, my, mz
    If Abs(mx) > 0.9 Then
        i1 = 1: i2 = 2                 ' normal X: the plane carries Y and Z
    ElseIf Abs(my) > 0.9 Then
        i1 = 0: i2 = 2                 ' normal Y: the plane carries X and Z
    ElseIf Abs(mz) > 0.9 Then
        i1 = 0: i2 = 1                 ' normal Z: the plane carries X and Y
    Else
        Fail "sketch axis calibration: the plane normal (" & Fmt(mx) & ", " & Fmt(my) & _
             ", " & Fmt(mz) & ") is not a model axis."
    End If

    p0(0) = bx: p0(1) = by: p0(2) = bz
    p1(0) = bx: p1(1) = by: p1(2) = bz
    p0(i1) = p0(i1) + 1#: p1(i1) = p1(i1) + 2#
    p0(i2) = p0(i2) + 3#: p1(i2) = p1(i2) + 5#

    For k = 0 To 3
        us = 1#: If (k And 1) <> 0 Then us = -1#
        vs = 1#: If (k And 2) <> 0 Then vs = -1#
        If ProbeLandsWhereAsked(pl, p0, p1, i1, i2, us, vs) Then
            Note "sketch axes on plane " & pl.Name & ": u x " & Fmt(us) & ", v x " & Fmt(vs)
            TryCalibrateSketchAxes = True
            Exit Function
        End If
    Next k

    TryCalibrateSketchAxes = False

End Function


' Draw the test rectangle with the given signs, extrude it, compare
' the body box against what was asked for, then take it back out
' again. True when it landed where it was asked to.
Private Function ProbeLandsWhereAsked(pl As SldWorks.Feature, p0() As Double, p1() As Double, _
                                      ByVal i1 As Long, ByVal i2 As Long, _
                                      ByVal us As Double, ByVal vs As Double) As Boolean

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim bodies As Variant, box As Variant
    Dim i3 As Long
    Dim ok As Boolean

    uSign = us: vSign = vs

    ' The probe has to be the only body in the part, or it would
    ' merge with what is already there and then report that body's
    ' box instead of its own.
    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "sketch axis calibration was asked to run with " & (UBound(bodies) + 1) & _
             " body/bodies already in the part; it only works on an empty one."
    End If

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch axis calibration sketch."
    wRefSet = False

    G2S sk, p0(0), p0(1), p0(2), u0, v0
    G2S sk, p1(0), p1(1), p1(2), u1, v1
    swSkMgr.CreateLine u0, v0, 0#, u1, v0, 0#
    swSkMgr.CreateLine u1, v0, 0#, u1, v1, 0#
    swSkMgr.CreateLine u1, v1, 0#, u0, v1, 0#
    swSkMgr.CreateLine u0, v1, 0#, u0, v0, 0#
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondBlind, swEndCondBlind, 0.5, 0.01, _
        False, False, False, False, 0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True

    If f Is Nothing Then
        ok = False
    Else
        bodies = swPart.GetBodies2(swSolidBody, True)
        If IsEmpty(bodies) Then
            ok = False
        Else
            box = bodies(0).GetBodyBox     ' xmin ymin zmin xmax ymax zmax
            ' The two in-plane axes say which way the sketch axes
            ' run. The third says where the plane itself is: the
            ' block starts on the plane and grows one way or the
            ' other off it, so one of its two bounds on that axis
            ' has to be the plane's own coordinate. Without this
            ' line a plane mirrored about the origin passes, and
            ' everything built on it comes out mirrored too.
            i3 = 3 - i1 - i2
            ok = Near(box(i1), p0(i1)) And Near(box(i1 + 3), p1(i1)) And _
                 Near(box(i2), p0(i2)) And Near(box(i2 + 3), p1(i2)) And _
                 (Near(box(i3), p0(i3)) Or Near(box(i3 + 3), p0(i3)))
        End If
        swModel.ClearSelection2 True
        f.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    End If

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    swModel.EditDelete
    swModel.ClearSelection2 True

    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "a sketch axis calibration probe could not be removed; " & _
             (UBound(bodies) + 1) & " body/bodies are still in the part."
    End If

    ProbeLandsWhereAsked = ok

End Function


Private Function Near(ByVal a As Double, ByVal b As Double) As Boolean
    Near = (Abs(a - b) < 0.001)
End Function


' A plane's normal in model coordinates, read from a sketch opened
' on it. An empty sketch is discarded on exit, so this costs a
' feature only while it is being measured.
Private Sub PlaneNormal(pl As SldWorks.Feature, ByRef mx As Double, ByRef my As Double, ByRef mz As Double)

    Dim sk As SldWorks.Sketch
    Dim a As Variant

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a probe sketch on a reference plane."
    a = sk.ModelToSketchTransform.ArrayData
    mx = a(6): my = a(7): mz = a(8)
    swSkMgr.InsertSketch True
    swModel.ClearSelection2 True

End Sub


' The default plane whose normal is the given direction, found by
' probing rather than by name -- plane names are localised, so
' "Right Plane" does not exist on a Turkish install.
Private Function FindPlaneWithNormal(ByVal vx As Double, ByVal vy As Double, ByVal vz As Double) As SldWorks.Feature

    Dim f As SldWorks.Feature
    Dim mx As Double, my As Double, mz As Double

    Set f = swModel.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then
            PlaneNormal f, mx, my, mz
            If Abs(Abs(mx * vx + my * vy + mz * vz) - 1#) < DIR_TOL Then
                Set FindPlaneWithNormal = f
                Exit Function
            End If
        End If
        Set f = f.GetNextFeature
    Loop

End Function


Private Function LastFeature(ByVal typeName As String) As SldWorks.Feature
    Dim f As SldWorks.Feature
    Set f = swModel.FeatureByPositionReverse(0)
    If f Is Nothing Then Fail "no feature was created where a " & typeName & " was expected."
    If f.GetTypeName2 <> typeName Then
        Fail "expected the last feature to be a " & typeName & ", found " & f.GetTypeName2 & "."
    End If
    Set LastFeature = f
End Function


'==================================================================
' (f) Self-verification. Every stage has a closed-form volume and a
'     known bounding box, so the model is checked against
'     arithmetic, not against a previous run. Nothing is exported
'     until all of it passes.
'==================================================================
Private Sub CheckStage(ByVal stage As String, ByVal expected As Double, _
                       ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                       ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double)

    Dim body As SldWorks.Body2
    Dim mp As Variant, box As Variant
    Dim got As Double

    Set body = TheBody(stage)

    ' IBody2::GetMassProperties is always SI; IMassProperty follows
    ' the document's units unless told otherwise, so use this one.
    mp = body.GetMassProperties(1000#)
    got = mp(3)

    Note "stage " & stage & ": " & Fmt(got) & " m3 (expected " & Fmt(expected) & ")"

    If Abs(got - expected) > VOL_TOL * expected Then
        Fail "stage " & stage & " volume is " & Fmt(got) & " m3 but should be " & _
             Fmt(expected) & " m3 (" & Fmt(100# * (got - expected) / expected) & " %)."
    End If

    box = body.GetBodyBox
    ' GetBodyBox bounds a spline face by its control polygon, which
    ' lies outside the curve: on the volute's spiral it overstated the
    ' box by 21 mm. The body's true extreme points are exact, so the
    ' volute is held to those.
    If VOLUTE_ON Then box = ExactBox(body)
    CheckExtent stage, "x min", box(0), x0
    CheckExtent stage, "y min", box(1), y0
    CheckExtent stage, "z min", box(2), z0
    CheckExtent stage, "x max", box(3), x1
    CheckExtent stage, "y max", box(4), y1
    CheckExtent stage, "z max", box(5), z1

End Sub


' The body's bounding box from its extreme points along the six axis
' directions, in GetBodyBox's order: xmin ymin zmin xmax ymax zmax.
Private Function ExactBox(body As SldWorks.Body2) As Variant

    Dim b(5) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long
    Dim d(2) As Double

    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#
            d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then
                Fail "GetExtremePoint failed along axis " & a & "."
            End If
            If sd < 0 Then
                b(a) = Choose(a + 1, px, py, pz)
            Else
                b(a + 3) = Choose(a + 1, px, py, pz)
            End If
        Next sd
    Next a

    ExactBox = b

End Function


Private Function TheBody(ByVal stage As String) As SldWorks.Body2

    Dim bodies As Variant

    ' Body pointers do not survive a feature, so never cache one.
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "stage " & stage & " left no solid body."
    If UBound(bodies) <> 0 Then
        Fail "stage " & stage & " left " & (UBound(bodies) + 1) & " solid bodies; " & _
             "the CFD domain has to be one. A boolean did not merge."
    End If
    Set TheBody = bodies(0)

End Function


Private Sub CheckExtent(ByVal stage As String, ByVal what As String, ByVal got As Double, ByVal expected As Double)
    If Abs(got - expected) > BOX_TOL Then
        Fail "at stage " & stage & " the bounding box " & what & " is " & Fmt(got) & _
             " m but should be " & Fmt(expected) & " m."
    End If
End Sub


' Closed and manifold, checked independently of SolidWorks' own
' claim: in a closed solid every edge has exactly two adjacent
' faces. A free edge means an open shell that would leak in CFD.
Private Sub Verify()

    Dim body As SldWorks.Body2
    Dim edges As Variant
    Dim edge As SldWorks.Edge
    Dim adj As Variant
    Dim i As Long

    ' Solidity is already settled: GetBodies2 was asked for solid
    ' bodies only, and it returned exactly one.
    phase = "checking that the solid is closed"
    Set body = TheBody("final")

    edges = body.GetEdges
    If IsEmpty(edges) Then Fail "the body has no edges."

    For i = 0 To UBound(edges)
        Set edge = edges(i)
        adj = edge.GetTwoAdjacentFaces2
        If IsEmpty(adj) Then Fail "edge " & i & " reports no adjacent faces; the body is not closed."
        If adj(0) Is Nothing Or adj(1) Is Nothing Then
            Fail "edge " & i & " has only one adjacent face; the body is an open shell."
        End If
    Next i

    Note "closed manifold solid: " & (UBound(edges) + 1) & " edges, each with two faces"

End Sub


'==================================================================
' (g) Boundary faces.
'
' Face names are regenerated by every boolean, so the three
' boundaries are found by what they ARE: a plane, its normal and a
' point on it, read analytically off the surface. Each gets its own
' colour; AP214 carries face colours and Fluent Meshing makes named
' selections from them. Everything else is wall.
'==================================================================
Private Sub TagBoundaryFaces()

    Dim body As SldWorks.Body2
    Dim faces As Variant
    Dim face As SldWorks.Face2
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim i As Long
    Dim nDust As Long, nGas As Long, nInlet As Long, nFeed As Long, nDuctEnd As Long
    Dim aDust As Double, aGas As Double, aInlet As Double, aFeed As Double
    Dim e0 As Double, e1 As Double, e2 As Double, pz As Double

    Set body = TheBody("final")
    faces = body.GetFaces

    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            e0 = p(0): e1 = p(1): e2 = p(2): pz = p(5)

            If Abs(e0) < DIR_TOL And Abs(e1) < DIR_TOL Then
                If Abs(pz) < 0.0001 Then
                    Paint face, 0.85, 0.55, 0.15          ' dust_outlet
                    nDust = nDust + 1: aDust = aDust + face.GetArea
                ElseIf OUTLET_TURN_DEG = 180# And Abs(pz - zGasOut) < 0.0001 And FaceXMin(face) > R Then
                    Paint face, 0.2, 0.45, 0.85           ' gas_outlet, the drop's end
                    nGas = nGas + 1: aGas = aGas + face.GetArea
                ElseIf RISER_ON And Abs(pz - zRiserBot) < 0.0001 Then
                    ' The gas enters here now, so it takes the colour
                    ' the inlet face had and Fluent Meshing's naming
                    ' carries over unchanged.
                    Paint face, 0.2, 0.7, 0.35            ' gas inlet, riser bottom
                    nInlet = nInlet + 1: aInlet = aInlet + face.GetArea
                Else
                    Paint face, 0.72, 0.72, 0.72          ' roof, vortex finder rim
                End If
            ElseIf RISER_ON And Abs(e1) < DIR_TOL And Abs(Abs(e0 * fx + e2 * fz) - 1#) < DIR_TOL And _
                   Abs((p(3) - xFeedEnd) * fx + (pz - zFeedEnd) * fz) < 0.0001 Then
                Paint face, 0.6, 0.3, 0.7                 ' meal_feed: gas wall, DPM injection
                nFeed = nFeed + 1: aFeed = aFeed + face.GetArea
            ElseIf OUTLET_TURN_DEG = 90# And Abs(e1) < DIR_TOL And Abs(e2) < DIR_TOL And _
                   Abs(p(3) - xGasOut) < 0.0001 Then
                Paint face, 0.2, 0.45, 0.85               ' gas_outlet, the run's end
                nGas = nGas + 1: aGas = aGas + face.GetArea
            ElseIf VOLUTE_ON And Abs(e1) < DIR_TOL And Abs(e2) < DIR_TOL And _
                   Abs(p(3) - xGasOut) >= 0.0001 And Abs(p(3) + L_INLET) >= 0.0001 Then
                ' The volute's two tongue faces at x = 0 are normal to
                ' the duct axis too; they are wall.
                Paint face, 0.72, 0.72, 0.72              ' volute tongues
            ElseIf Abs(e1) < DIR_TOL And Abs(Abs(e0 * dx + e2 * dz) - 1#) < DIR_TOL Then
                ' With the riser on, this face is where the riser bend
                ' meets the duct and must have merged away.
                Paint face, 0.2, 0.7, 0.35                ' meal_inlet
                nInlet = nInlet + 1: aInlet = aInlet + face.GetArea
                nDuctEnd = nDuctEnd + 1
            Else
                Paint face, 0.72, 0.72, 0.72              ' meal_inlet_wall
            End If
        Else
            Paint face, 0.72, 0.72, 0.72                  ' barrel, cone, vortex finder
        End If
    Next i

    ' Exactly one of each. Two inlet faces would mean the duct never
    ' broke into the barrel and its end cap is still standing across
    ' the opening; none would mean it overshot.
    If nDust <> 1 Then Fail "found " & nDust & " dust outlet faces, expected 1."
    If nGas <> 1 Then Fail "found " & nGas & " gas outlet faces, expected 1."
    If RISER_ON Then
        If nDuctEnd <> 0 Then
            Fail "found " & nDuctEnd & " faces normal to the duct axis; the riser bend did not " & _
                 "merge across the duct's end and a wall still closes it."
        End If
        If nInlet <> 1 Then Fail "found " & nInlet & " riser inlet faces, expected 1."
        If nFeed <> 1 Then Fail "found " & nFeed & " feed chute end faces, expected 1."
        CheckArea "meal_feed", aFeed, FEED_W * FEED_H
    ElseIf nInlet <> 1 Then
        Fail "found " & nInlet & " faces normal to the duct axis, expected 1 (the inlet). " & _
             "Two means the duct's end cap survived the merge and blocks the opening."
    End If

    CheckArea "dust_outlet", aDust, PI * rDust * rDust
    CheckArea "gas_outlet", aGas, PI * rVortex * rVortex
    If RISER_ON Then
        CheckArea "gas inlet", aInlet, PI * rRiser * rRiser
    Else
        CheckArea "gas inlet", aInlet, wDuct * H_INLET
    End If

    Note "gas inlet " & Fmt(aInlet) & " m2 (green), gas_outlet " & Fmt(aGas) & _
         " m2 (blue), dust_outlet " & Fmt(aDust) & " m2 (orange)"
    If RISER_ON Then Note "meal_feed " & Fmt(aFeed) & " m2 (purple) -- a wall for the gas"

    swModel.ClearSelection2 True

End Sub


' The least x a face reaches. The gas outlet shares the roof's plane
' when the gooseneck's legs are equal; it is the one out past the
' barrel.
Private Function FaceXMin(face As SldWorks.Face2) As Double
    Dim b As Variant
    b = face.GetBox
    FaceXMin = b(0)
End Function


Private Sub CheckArea(ByVal what As String, ByVal got As Double, ByVal expected As Double)
    If Abs(got - expected) > AREA_TOL * expected Then
        Fail "the " & what & " face is " & Fmt(got) & " m2 but should be " & Fmt(expected) & " m2."
    End If
End Sub


' RGB, ambient, diffuse, specular, shininess, transparency, emission.
'
' Set through the property -- IFace2 has no SetMaterialPropertyValues2
' in 2026 -- and from a typed Double array. VBA's Array() builds a
' Variant of Variants, which this property accepts without complaint
' and then reads wrongly: it left the red and blue channels at zero,
' so three differently coloured boundaries came out sharing two
' colours. The colours are the only thing carrying the boundary names
' into Fluent, so they are read back and checked here rather than
' trusted. The tolerance allows the 8-bit quantisation SolidWorks
' applies on the way in.
Private Sub Paint(face As SldWorks.Face2, ByVal r As Double, ByVal g As Double, ByVal b As Double)

    Dim m(8) As Double
    Dim got As Variant

    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#        ' ambient
    m(4) = 1#        ' diffuse
    m(5) = 0.3       ' specular
    m(6) = 0.3       ' shininess
    m(7) = 0#        ' transparency
    m(8) = 0#        ' emission

    face.MaterialPropertyValues = m

    got = face.MaterialPropertyValues
    If IsEmpty(got) Then Fail "a face reports no colour after one was set on it."
    If Abs(got(0) - r) > 0.01 Or Abs(got(1) - g) > 0.01 Or Abs(got(2) - b) > 0.01 Then
        Fail "a face's colour came back as (" & Fmt(got(0)) & ", " & Fmt(got(1)) & ", " & _
             Fmt(got(2)) & ") after being set to (" & Fmt(r) & ", " & Fmt(g) & ", " & _
             Fmt(b) & "). The boundary names would not reach Fluent."
    End If

End Sub


'==================================================================
' (h) Export
'==================================================================
' The mesh sizing cylinder, built in a part of its own.
'
' It is deliberately a separate document and a separate file. Put
' in the same part it would either merge with the fluid body or
' survive as a second body, and every volume check in Verify would
' have to learn about it; exported inside C1.step it would be a
' second solid for the mesher to wrap. A plain cylinder in its own
' file is the whole of what Fluent Meshing needs.
'
' The plane axes are measured again here: calibration is per plane
' and these are a new document's planes, so nothing measured in the
' cyclone's part carries over.
Private Sub BuildBoi()

    Dim planeX0 As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant
    Dim expect As Double
    Dim cycTitle As String
    Dim errs As Long

    ' The cyclone's own document, to be brought back to the front
    ' when this one is done. Otherwise the macro ends showing a
    ' plain cylinder and it looks as though it built the wrong
    ' thing.
    cycTitle = swModel.GetTitle

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part for the sizing cylinder."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    Set planeX0 = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX0 Is Nothing Then Fail "could not find the X normal plane in the sizing cylinder part."
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX

    Set f = RevolveProfile(planeX0, Array( _
        0#, zBoiBot, _
        BOI_RADIUS, zBoiBot, _
        BOI_RADIUS, zBoiTop, _
        0#, zBoiTop), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the mesh sizing cylinder."

    Set body = TheBody("mesh sizing cylinder")
    mp = body.GetMassProperties(1000#)
    expect = PI * BOI_RADIUS * BOI_RADIUS * (zBoiTop - zBoiBot)
    If Abs(mp(3) - expect) > VOL_TOL * expect Then
        Fail "the mesh sizing cylinder came out at " & Fmt(mp(3)) & " m3, expected " & _
             Fmt(expect) & " m3."
    End If

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

    SaveOne OUT_ROOT & LINE_KEY & "\" & CYCLONE_NAME & "_boi.step"
    Note "sizing cylinder  r = " & Fmt(BOI_RADIUS) & " m, z = " & Fmt(zBoiBot) & _
         " .. " & Fmt(zBoiTop) & " m, " & Fmt(mp(3)) & " m3 -- a mesher input, not fluid"

    swApp.ActivateDoc2 cycTitle, False, errs

End Sub


Private Sub ExportFiles()

    Dim outDir As String

    outDir = OUT_ROOT & LINE_KEY & "\"
    EnsureDir OUT_ROOT
    EnsureDir outDir

    ' These are application-wide export defaults, so remember them
    ' and hand them back the way they were found.
    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    oldStlUnits = swApp.GetUserPreferenceIntegerValue(swExportStlUnits)
    oldStlBinary = swApp.GetUserPreferenceToggle(swSTLBinaryFormat)
    oldStlNoShift = swApp.GetUserPreferenceToggle(swSTLDontTranslateToPositive)
    oldStlInfo = swApp.GetUserPreferenceToggle(swSTLShowInfoOnSave)
    oldStlQuality = swApp.GetUserPreferenceIntegerValue(swSTLQuality)
    oldStlDev = swApp.GetUserPreferenceDoubleValue(swSTLDeviation)
    oldStlAngle = swApp.GetUserPreferenceDoubleValue(swSTLAngleTolerance)
    exportPrefsTouched = True

    ' STEP AP214: AP203 does not carry the face colours the boundary
    ' tagging above depends on.
    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True

    ' STL: binary, metres, and NOT shifted into positive space.
    ' Translating it would silently throw away the coordinate system
    ' the bounding box was just verified against. Deviation and
    ' angle match what geometry/export.py used for the CadQuery
    ' output, so the two are comparable.
    swApp.SetUserPreferenceIntegerValue swExportStlUnits, swMETER
    swApp.SetUserPreferenceToggle swSTLBinaryFormat, True
    swApp.SetUserPreferenceToggle swSTLDontTranslateToPositive, True
    swApp.SetUserPreferenceToggle swSTLShowInfoOnSave, False
    swApp.SetUserPreferenceIntegerValue swSTLQuality, swSTLQuality_Custom
    swApp.SetUserPreferenceDoubleValue swSTLDeviation, 0.001        ' metres
    swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, 0.1     ' radians

    SaveOne outDir & outName & ".SLDPRT"
    SaveOne outDir & outName & ".step"
    SaveOne outDir & outName & ".stl"

End Sub


' A failed export returns without raising, so the outcome is read
' from the error code and then from the disk. The return value is
' not used: SolidWorks 2026 writes the file and still returns False,
' so believing it would throw away work that actually succeeded.
Private Sub SaveOne(ByVal path As String)

    Dim errs As Long, warns As Long

    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, _
                            Nothing, errs, warns

    If errs <> 0 Then
        Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    End If
    If Dir(path) = "" Then
        Fail "SolidWorks reported no error but " & path & " is not on disk."
    End If

    Note "wrote " & path

End Sub


Private Sub EnsureDir(ByVal path As String)
    If Dir(path, vbDirectory) = "" Then MkDir path
End Sub


'==================================================================
' Housekeeping. AddToDB and the two application preferences are
' global editor state: leaving them set would break the user's next
' interactive sketch, so they are restored on the way out whether
' the build succeeded or not.
'==================================================================
Private Sub Restore()
    On Error Resume Next
    If Not swSkMgr Is Nothing Then
        swSkMgr.AddToDB = False
        swSkMgr.DisplayWhenAdded = True
    End If
    If prefsTouched Then
        swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, oldVerify
        swApp.SetUserPreferenceToggle swInputDimValOnCreate, oldInputDim
        prefsTouched = False
    End If
    If exportPrefsTouched Then
        swApp.SetUserPreferenceIntegerValue swStepAP, oldStepAP
        swApp.SetUserPreferenceToggle swStepExportAppearances, oldStepAppear
        swApp.SetUserPreferenceIntegerValue swExportStlUnits, oldStlUnits
        swApp.SetUserPreferenceToggle swSTLBinaryFormat, oldStlBinary
        swApp.SetUserPreferenceToggle swSTLDontTranslateToPositive, oldStlNoShift
        swApp.SetUserPreferenceToggle swSTLShowInfoOnSave, oldStlInfo
        swApp.SetUserPreferenceIntegerValue swSTLQuality, oldStlQuality
        swApp.SetUserPreferenceDoubleValue swSTLDeviation, oldStlDev
        swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, oldStlAngle
        exportPrefsTouched = False
    End If
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "cyclone", msg
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
End Function
