Attribute VB_Name = "cyclone"
'==================================================================
' Cyclone CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' Builds ONE closed solid: the gas volume inside a single preheater
' cyclone, plus its tangential meal/gas inlet duct and the outlet
' pipe above the roof. Nothing structural is modelled -- no shell,
' no refractory, no volute (CLAUDE.md rule 8).
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
'     Swap the eight catalogue dimensions to build another cyclone;
'     the table for every stage of every line is in
'     geometry/catalog.md.
'------------------------------------------------------------------

Const CYCLONE_NAME As String = "C1"
Const LINE_KEY As String = "2500"

' Catalogue dimensions [m] -- geometry/preheater/cyclone_C1.md
Const D_BARREL       As Double = 4.32    ' effective inner diameter
Const H_BARREL       As Double = 6.79    ' cylindrical body height
Const H_CONE         As Double = 4.65    ' cone height
Const L_VORTEX       As Double = 2.16    ' vortex finder immersion
Const D_VORTEX       As Double = 2.4     ' vortex finder diameter
Const D_DUST         As Double = 0.4     ' dust outlet diameter
Const W_INLET        As Double = 0.86    ' inlet width  (normal to the duct axis)

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
Const H_INLET        As Double = 2.16

' Modelling parameters -- NOT plant dimensions. No source gives
' them; they say where the CFD boundary faces sit.
' configs/twin_cfg.yaml : geometry.cfd_boundary
' How far above the roof the outlet face sits, in vortex finder
' diameters. 1.0 was too short and the first Fluent run said so:
' the swirl leaving up the bore carries a reverse-flow core that
' was still open where the boundary cut it, so 40-44 % of the
' outlet face had gas coming back IN. Fluent then has to impose the
' backflow values there, the imposed state fights the state the
' domain wants, and the whole solution sat in a limit cycle of
' +/- 0.3 % on the mass balance instead of converging. 2.5 puts the
' face 6.0 m above the roof, well past where the core closes.
Const OUTLET_EXT_OVER_VORTEX_D As Double = 2.5    ' outlet face above roof, x vortex D
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
Const INLET_SLOPE_DEG          As Double = 5#     ' duct inclined this far DOWNWARD toward the cyclone

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

' Mesh aid, NOT physics. 0.0 keeps the duct's outer wall exactly
' tangent to the barrel, which is the real geometry and what
' cyclone_C1.md describes; the union then closes to a zero-angle
' knife edge along the tangent line and Fluent Meshing makes sliver
' cells there. A small positive value shifts BOTH duct walls inward
' so that edge has a finite included angle -- the published section
' 0.86 x 4.97 and hence the inlet velocity are preserved exactly.
' It stays at 0 deliberately. It shares the 0.10 m budget above
' with VORTEX_WALL, and the measurements put the rim an order of
' magnitude ahead of this edge as a mesh problem: 0.015 orthogonal
' quality against 0.135. A 0.135 cell is usable; a 0.015 one is
' not. So the budget goes to the rim and this edge is left as the
' real tangent geometry, to be handled with a local face sizing.
' If a future mesh proves that insufficient, 0.02 here forces
' VORTEX_WALL down to 0.06 -- section 0.86 x 2.16 and hence the
' inlet velocity survive either way. Record it in cyclone_C1.md if
' you use it.
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
' floor of 0.01. BOI_CLEARANCE is the margin and PreChecks enforces
' it on both sides.
'
' 1.6 m covers the forced vortex core and the tangential velocity
' peak, which sits near the vortex finder radius. At 0.06 m cells
' that is about 27 cells across the core and roughly 365 000 cells
' inside the region -- the size the mesher is given is a mesher
' setting, not a geometry one, so tune it there.
Const BOI_RADIUS      As Double = 1.6    ' about the cyclone axis [m]
Const BOI_CLEARANCE   As Double = 0.3    ' least distance to any real surface [m]

' Where the sizing cylinder stops, above the roof. Everything above
' that is the straight outlet extension, whose only job is to hold
' the boundary condition away from the flow; resolving it costs
' cells and buys no physics.
Const BOI_ROOF_MARGIN As Double = 1#     ' [m]

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
Dim zBoiTop As Double                       ' top of the mesh sizing cylinder
Dim yOuter As Double, yInner As Double, yMid As Double
Dim dx As Double, dz As Double          ' duct axis direction d = (dx, 0, dz)
Dim nx As Double, nz As Double          ' duct section "up"  n = (nx, 0, nz)
Dim zTopAt0 As Double, zBotAt0 As Double
Dim reach As Double                     ' |x| where the duct's inner wall meets the barrel
Dim ceX As Double, ceY As Double, ceZ As Double   ' inlet face centre
Dim xInletNear As Double, zDuctTop As Double

' Sketch axis directions, measured at run time by CalibrateSketchAxes.
' uSign/vSign are the pair in force for the sketch being drawn now;
' the others are what was measured for each plane.
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profiles
Dim uSignD As Double, vSignD As Double      ' the duct's own plane, for its side view

' The off-plane component of the first point drawn in the sketch
' now open. Every later point in the same sketch has to match it;
' see G2S for why the value itself is not compared against zero.
Dim wRef As Double
Dim wRefSet As Boolean

' expected volumes, all closed form
Dim vEquip As Double, vDuctFree As Double, vPipe As Double, vWall As Double
Dim vStage1 As Double, vStage2 As Double, vStage3 As Double, vFinal As Double

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
    phase = "building the mesh sizing cylinder"
    BuildBoi

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
' (b) Derived coordinates
'==================================================================
Private Sub Derive()

    Dim th As Double

    R = 0.5 * D_BARREL
    rDust = 0.5 * D_DUST
    rVortex = 0.5 * D_VORTEX

    zRoof = H_CONE + H_BARREL
    zVortexBottom = zRoof - L_VORTEX
    zOutletTop = zRoof + OUTLET_EXT_OVER_VORTEX_D * D_VORTEX
    zBoiTop = zRoof + BOI_ROOF_MARGIN

    yOuter = R - INLET_TANGENT_RELIEF
    yInner = yOuter - W_INLET
    yMid = 0.5 * (yInner + yOuter)

    th = INLET_SLOPE_DEG * PI / 180#
    dx = Cos(th): dz = -Sin(th)         ' towards the cyclone, downward
    nx = Sin(th): nz = Cos(th)          ' section "up", normal to the axis

    ' How far upstream the opening in the shell reaches: the duct's
    ' inner wall meets the barrel there, and that is the duct's
    ' highest point inside the barrel's footprint.
    reach = Sqr(R * R - yInner * yInner)

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

    ' ---- closed-form volumes, one per build stage ----
    vEquip = PI * R * R * H_BARREL _
           + (PI / 3#) * H_CONE * (R * R + R * rDust + rDust * rDust)

    ' The duct outside the barrel. Integrating the free axial length
    ' over the section gives a closed form; the part that varies
    ' along the section's own "up" axis cancels by symmetry.
    vDuctFree = H_INLET * L_INLET * W_INLET - (H_INLET / nz) * Segment(R, yInner, yOuter)

    vPipe = PI * rVortex * rVortex * (zOutletTop - zRoof)
    vWall = PI * ((rVortex + VORTEX_WALL) ^ 2 - rVortex * rVortex) * L_VORTEX

    vStage1 = vEquip                       ' barrel + cone
    vStage2 = vStage1 + vDuctFree          ' + inlet duct
    vStage3 = vStage2 - vWall              ' - vortex finder wall
    vFinal = vStage3 + vPipe               ' + outlet pipe above the roof

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
             "(outer radius " & Fmt(rVortex + VORTEX_WALL) & " m). Reduce INLET_TANGENT_RELIEF."
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
    ' slivers there. Keep it in open fluid on both sides.
    If BOI_RADIUS - (rVortex + VORTEX_WALL) < BOI_CLEARANCE Then
        Fail "the mesh sizing cylinder at r = " & Fmt(BOI_RADIUS) & " m comes within " & _
             Fmt(BOI_RADIUS - rVortex - VORTEX_WALL) & " m of the vortex finder's outer " & _
             "radius " & Fmt(rVortex + VORTEX_WALL) & " m; it needs " & Fmt(BOI_CLEARANCE) & " m."
    End If
    If R - BOI_RADIUS < BOI_CLEARANCE Then
        Fail "the mesh sizing cylinder at r = " & Fmt(BOI_RADIUS) & " m comes within " & _
             Fmt(R - BOI_RADIUS) & " m of the barrel wall at r = " & Fmt(R) & " m; it needs " & _
             Fmt(BOI_CLEARANCE) & " m."
    End If

    Note "equipment volume (barrel + cone)  " & Fmt(vEquip) & " m3"
    Note "CFD domain volume                 " & Fmt(vFinal) & " m3"
    Note "duct top / bottom at x = 0        " & Fmt(zTopAt0) & " / " & Fmt(zBotAt0) & " m"
    Note "vortex finder clearance           " & Fmt(yInner - rVortex - VORTEX_WALL) & " m"
    If INLET_TANGENT_RELIEF = 0# Then
        Note "NOTE tangency relief is 0: the duct's outer wall is exactly"
        Note "     tangent to the barrel and the union closes to a zero-angle"
        Note "     edge. If Fluent Meshing makes slivers there, set"
        Note "     INLET_TANGENT_RELIEF to 0.02 and rebuild."
    End If

End Sub


'==================================================================
' (d) Build
'
' Four features, all merged on creation, so the part never holds
' more than one solid body and no Combine feature is needed.
'==================================================================
Private Sub Build()

    Dim planeX0 As SldWorks.Feature       ' the x = 0 plane
    Dim planeY0 As SldWorks.Feature       ' the y = 0 plane
    Dim planeDuct As SldWorks.Feature     ' y = yInner, the duct's inner wall
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

    '--- 0. measure both planes' sketch axes -------------------------
    ' Both probes run while the part is still empty. Once the barrel
    ' is there a probe would land inside it, merge with it, and then
    ' measure the merged body instead of itself.
    Set planeDuct = OffsetPlane(planeY0, yInner, uSignD, vSignD)
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

    '--- 2. inlet duct ----------------------------------------------
    Set f = ExtrudeInlet(planeDuct)
    If f Is Nothing Then Fail "FeatureExtrusion3 failed on the inlet duct."
    CheckStage "2  + inlet duct", vStage2, _
               ceX - 0.5 * H_INLET * nx, -R, 0#, R, R, zDuctTop

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
               ceX - 0.5 * H_INLET * nx, -R, 0#, R, R, zDuctTop

    '--- 4. outlet pipe above the roof ------------------------------
    Set f = RevolveProfile(planeX0, Array( _
        0#, zRoof, _
        rVortex, zRoof, _
        rVortex, zOutletTop, _
        0#, zOutletTop), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the outlet pipe."
    CheckStage "4  + outlet pipe", vFinal, _
               ceX - 0.5 * H_INLET * nx, -R, 0#, R, R, zOutletTop

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


' A plane parallel to y = 0 at the given y, with the sketch axes on
' it measured at the same time.
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
Private Function OffsetPlane(base As SldWorks.Feature, ByVal atY As Double, _
                             ByRef us As Double, ByRef vs As Double) As SldWorks.Feature

    Dim pl As SldWorks.Feature
    Dim opt As Long
    Dim k As Long

    For k = 0 To 1
        opt = swRefPlaneReferenceConstraint_Distance
        If k = 1 Then opt = opt Or swRefPlaneReferenceConstraint_OptionFlip

        swModel.ClearSelection2 True
        base.Select2 False, 0
        Set pl = swFeat.InsertRefPlane(opt, Abs(atY), 0, 0#, 0, 0#)
        swModel.ClearSelection2 True
        If pl Is Nothing Then
            Fail "InsertRefPlane failed for the duct plane at y = " & Fmt(atY) & " m."
        End If

        If TryCalibrateSketchAxes(pl, 0#, atY, 0#, us, vs) Then
            Note "duct plane measured at y = " & Fmt(atY) & " m"
            Set OffsetPlane = pl
            Exit Function
        End If

        swModel.ClearSelection2 True
        pl.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    Next k

    Fail "the duct plane could not be placed at y = " & Fmt(atY) & " m; a test block " & _
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
' The quadrilateral's downstream edge is the barrel's tangent plane
' x = 0, which is where the duct has to end. Short of it the duct's
' end cap survives the merge as a wall across the opening; past it
' the duct breaks back out through the far side of the shell,
' because at y = R the barrel reaches no further than x = 0. The
' deleted builder ran its box from x0 to 0.0 for the same reason.
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
    qx(2) = 0#:            qz(2) = zTopAt0            ' tangent plane, top
    qx(3) = 0#:            qz(3) = zBotAt0            ' tangent plane, bottom

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
            W_INLET, 0.01, _
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
    CheckExtent stage, "x min", box(0), x0
    CheckExtent stage, "y min", box(1), y0
    CheckExtent stage, "z min", box(2), z0
    CheckExtent stage, "x max", box(3), x1
    CheckExtent stage, "y max", box(4), y1
    CheckExtent stage, "z max", box(5), z1

End Sub


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
    Dim nDust As Long, nGas As Long, nInlet As Long
    Dim aDust As Double, aGas As Double, aInlet As Double
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
                ElseIf Abs(pz - zOutletTop) < 0.0001 Then
                    Paint face, 0.2, 0.45, 0.85           ' gas_outlet
                    nGas = nGas + 1: aGas = aGas + face.GetArea
                Else
                    Paint face, 0.72, 0.72, 0.72          ' roof, vortex finder rim
                End If
            ElseIf Abs(e1) < DIR_TOL And Abs(Abs(e0 * dx + e2 * dz) - 1#) < DIR_TOL Then
                Paint face, 0.2, 0.7, 0.35                ' meal_inlet
                nInlet = nInlet + 1: aInlet = aInlet + face.GetArea
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
    If nInlet <> 1 Then
        Fail "found " & nInlet & " faces normal to the duct axis, expected 1 (the inlet). " & _
             "Two means the duct's end cap survived the merge and blocks the opening."
    End If

    CheckArea "dust_outlet", aDust, PI * rDust * rDust
    CheckArea "gas_outlet", aGas, PI * rVortex * rVortex
    CheckArea "meal_inlet", aInlet, W_INLET * H_INLET

    Note "meal_inlet " & Fmt(aInlet) & " m2 (green), gas_outlet " & Fmt(aGas) & _
         " m2 (blue), dust_outlet " & Fmt(aDust) & " m2 (orange)"

    swModel.ClearSelection2 True

End Sub


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
        0#, 0#, _
        BOI_RADIUS, 0#, _
        BOI_RADIUS, zBoiTop, _
        0#, zBoiTop), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the mesh sizing cylinder."

    Set body = TheBody("mesh sizing cylinder")
    mp = body.GetMassProperties(1000#)
    expect = PI * BOI_RADIUS * BOI_RADIUS * zBoiTop
    If Abs(mp(3) - expect) > VOL_TOL * expect Then
        Fail "the mesh sizing cylinder came out at " & Fmt(mp(3)) & " m3, expected " & _
             Fmt(expect) & " m3."
    End If

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

    SaveOne OUT_ROOT & LINE_KEY & "\" & CYCLONE_NAME & "_boi.step"
    Note "sizing cylinder  r = " & Fmt(BOI_RADIUS) & " m, z = 0 .. " & Fmt(zBoiTop) & _
         " m, " & Fmt(mp(3)) & " m3 -- a mesher input, not fluid"

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

    SaveOne outDir & CYCLONE_NAME & ".SLDPRT"
    SaveOne outDir & CYCLONE_NAME & ".step"
    SaveOne outDir & CYCLONE_NAME & ".stl"

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
