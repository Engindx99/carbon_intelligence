Attribute VB_Name = "calciner"
'==================================================================
' ILC calciner CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' Builds ONE closed solid: the gas volume inside the in-line
' calciner of the 5000 t/d plant -- two identical 2500 t/d preheater
' strings on one calciner and kiln (user decision, 12 Oct 2026),
' sized from the PF5000 line, itself double-string -- the kiln riser throat, the bottom
' cone and the vertical vessel -- and, as the build grows, its
' tangential tertiary air duct, the C4 meal pipe, a fuel port and the
' gooseneck down towards C5. Nothing structural is modelled -- no
' shell, no refractory (CLAUDE.md rule 8).
'
' BUILD STATUS: complete. Throat + cone + vessel, the gooseneck (a neck
' of three straight pieces -- 45 deg up, level, 45 deg down -- over the
' roof's top, then one vertical channel in front of the vessel, dividing
' at its lower end into two arms; user decision, 15 Nov 2026), the two meal feed pipes, the
' tangential tertiary air duct and the two fuel pipes, and a vertical meal pipe into a dispersion box
' on the wall at each side (user decision, 28 Nov 2026); the boundary faces are coloured and the solid is
' exported (STEP AP214, STL, SLDPRT).
'
' Coordinates: calciner axis = z, the kiln gas inlet face (bottom of
' the throat) at z = 0.
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
'     Every one is published, derived from a named literature value,
'     or a modelling parameter that says where a CFD boundary sits.
'     Sources: geometry/calciner/calciner.md.
'------------------------------------------------------------------

Const CALCINER_NAME As String = "calciner"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const D_VESSEL                     As Double  = 6.7404       ' effective inner D [derived_from_reference, calciner/calciner.md]
Const H_VESSEL                     As Double  = 30#          ' cone + cylinder [published, calciner/calciner.md]
Const CONE_DEG                     As Double  = 65#          ' [literature, calciner/calciner.md]
Const M_KILN_GAS                   As Double  = 61.44444444  ' kg/s [literature, calciner/calciner.md]
Const T_KILN_GAS                   As Double  = 1323.15      ' K [literature, calciner/calciner.md]
Const X_N2                         As Double  = 0.744        ' [literature, calciner/calciner.md]
Const X_O2                         As Double  = 0.076        ' [literature, calciner/calciner.md]
Const X_H2O                        As Double  = 0.05         ' [literature, calciner/calciner.md]
Const X_CO2                        As Double  = 0.13         ' [literature, calciner/calciner.md]
Const U_THROAT                     As Double  = 29#          ' m/s [literature, calciner/calciner.md]
Const THROAT_LEN_OVER_D            As Double  = 1#           ' [model, calciner/calciner.md]
Const D_GOOSENECK_SRC              As Double  = 3.5          ' each leg [published, preheater/gooseneck.md]
Const GN_OUTLET_AT_VESSEL_H        As Double  = 0.788074238954 ' the arms' level runs' axis, x H_VESSEL (C5's inlet axis, plant_geometry.py) [derived]
Const GN_SLOPE_DEG                 As Double  = 45#          ' the neck's two inclined pieces, to the horizontal [model, preheater/gooseneck.md]
Const GN_PIECE_OVER_D              As Double  = 1#           ' the neck's inclined pieces, x neck D [model, preheater/gooseneck.md]
Const GN_LEVEL_OVER_D              As Double  = 0.5          ' the neck's level piece, x neck D [model, preheater/gooseneck.md]
Const GN_CHANNEL_OVER_D            As Double  = 0.85         ' the vertical channel below the neck, x neck D [model, preheater/gooseneck.md]
Const GN_ARM_DEG                   As Double  = 60#          ' each arm's angle to the vertical [model, preheater/gooseneck.md]
Const GN_ARM_RUN_OVER_D            As Double  = 0.5          ' each arm's level run, x leg D [model, preheater/gooseneck.md]
Const GN_ROOT_FWD                  As Double  = 0.184956     ' where the neck's first piece pierces the roof, in front of the axis, m (cap kept inside the vessel) [derived]
Const GN_INSIDE_VESSEL             As Double  = 47.546441    ' the neck's first piece inside the vessel, m3 (grid, plant_geometry.py) [derived]
Const GN_OVERLAP_NECK_ARM          As Double  = 5.669359     ' channel x one arm, m3 [derived]
Const GN_OVERLAP_ARMS              As Double  = 4.122321     ' arm x arm, m3 [derived]
Const GN_OVERLAP_ALL               As Double  = 0#           ' channel x both arms, m3 [derived]
Const D_TA                         As Double  = 2.4393       ' tertiary air duct [derived_from_reference, calciner/calciner.md]
Const TA_CONE_CLEARANCE            As Double  = 0.05         ' its lower edge over the cone's top [model, calciner/calciner.md]
Const TA_WALL_RELIEF               As Double  = 0.05         ' its outer wall inside the vessel's [model, calciner/calciner.md]
Const TA_STUB_LEN                  As Double  = 3#           ' its face past the vessel's tangent plane [model, calciner/calciner.md]
Const FEED_ABOVE_TA                As Double  = 1#           ' meal / fuel holes over the duct's top [model, calciner/calciner.md]
Const D_FEED                       As Double  = 0.8485       ' [literature, calciner/calciner.md]
Const FEED_SLOPE_DEG               As Double  = 60#          ' below the horizontal [literature, calciner/calciner.md]
Const FEED_DEPTH                   As Double  = 1#           ' meal and fuel pipes past the wall [model, calciner/calciner.md]
Const D_FUEL                       As Double  = 0.2828       ' [literature, calciner/calciner.md]
Const FUEL_SLOPE_DEG               As Double  = 30#          ' below the horizontal [literature, calciner/calciner.md]
Const BOX_WIDTH_OVER_D             As Double  = 2.16         ' dispersion box width, x D_FEED (the meal pipe's bore) [model, calciner/calciner.md]
Const BOX_DEPTH_OVER_D             As Double  = 1.25         ' its back face out past the wall, x D_FEED [model, calciner/calciner.md]
Const BOX_BACK_H_OVER_D            As Double  = 0#           ' its back face's height, x D_FEED [model, calciner/calciner.md]
Const BOX_SLOPE_DEG                As Double  = 60#          ' its floor ramp to the horizontal [model, calciner/calciner.md]
Const BOX_PIPE_RISE                As Double  = 1#           ' its vertical meal pipe over the box's top [model, calciner/calciner.md]
Const OVERLAP_N                    As Long    = 300          ' grid per axis, the bends' shared volume [plant_geometry.py]
Const P_ATM                        As Double  = 101325#      ' Pa, the throat's gas [plant_geometry.py]
Const R_GAS                        As Double  = 8.314462618  ' J/(mol K) [plant_geometry.py]
Const M_N2                         As Double  = 0.0280134    ' kg/mol [plant_geometry.py]
Const M_O2                         As Double  = 0.0319988    ' kg/mol [plant_geometry.py]
Const M_H2O                        As Double  = 0.01801528   ' kg/mol [plant_geometry.py]
Const M_CO2                        As Double  = 0.0440095    ' kg/mol [plant_geometry.py]
' END GENERATED

' Vessel [m] -- geometry/calciner/calciner.md, geometry/catalog.md
' PF5000 publishes a 7.2 m shell and a 30.0 m vessel; the effective
' diameter is the shell x FLS calciner_eff_over_shell = 3.08 / 3.29,
' the rule geometry/catalog.md uses for every vendor shell. (The
' 2500 t/d line's calciner was 5.50 x 29.46 m, HFC2500.)
' -> D_VESSEL, H_VESSEL: in the generated block above
'    D_VESSEL: effective inner diameter, PF5000 shell 7.2 x 3.08 / 3.29
'    H_VESSEL: cone + cylinder, PF5000 (published)

' Bottom cone wall angle above the horizontal. Holcim StDC 2022 asks
' at least 65 deg of a cyclone cone so meal slides off it rather than
' building up; the calciner cone carries the same meal and gets the
' same rule. No source gives a calciner cone angle of its own.
' -> CONE_DEG: in the generated block above

' Throat. No source publishes a throat diameter, so it is sized from
' a literature flow at a literature velocity -- never from the twin,
' which is not ready (user decision, 29 Sep 2026):
'
'   kiln gas   2 x 110 600 kg/h     Mikulcic et al. 2012, a 5.5 m
'                                   calciner of a 2500 t/d class line;
'                                   the 5000 t/d kiln makes twice it
'   at         1050 C               Kahawalage et al. 2017
'   of         74.4 N2, 7.6 O2,     Kahawalage et al. 2017, mol %
'              5.0 H2O, 13.0 CO2
'   through    29 m/s               CPFD 2025 (4000 t/d calciner),
'                                   throat mean 28-30 m/s
'
' Ideal gas at one atmosphere; the throat diameter follows in Derive.
' -> M_KILN_GAS, T_KILN_GAS, X_N2, X_O2, X_H2O, X_CO2, U_THROAT: in the generated block above
'    M_KILN_GAS: 2 x 110 600 kg/h [kg/s]
'    T_KILN_GAS: [K]
'    U_THROAT: [m/s]

' Modelling parameter -- NOT a plant dimension. The kiln riser below
' the cone is cut off this far down, in throat diameters, so the gas
' inlet face sits on a straight run rather than on the cone's lip.
' -> THROAT_LEN_OVER_D: in the generated block above

' Gooseneck (user decisions, 12 Oct and 15 Nov 2026). Each arm takes one
' string's gas to its C5: a 2500 t/d line's whole gas, so each arm is
' the published 3.50 m gooseneck of that line
' (geometry/preheater/gooseneck.md). Two 3.50 m arms do not fit side
' by side on the 6.74 m roof, so ONE neck leaves the roof's centre
' with the two arms' area, 3.50 x sqrt 2 = 4.95 m, velocity kept. It is
' three straight pipes: one rising from the roof's middle, one level,
' one dropping, each joined to the next by a mitre, so that the neck
' comes down in front of the vessel (forward = -y) and goes on as one
' vertical channel of its diameter; at the channel's lower end it
' divides into two arms, each leaving in the plane across it (x-z)
' at an angle to the vertical, a straight piece, a mitre, and a vertical
' drop to its gas outlet face. Each arm's start disc is centred on the
' channel's end.
' A mitre joint between equal pipes is made of the two pipes, each
' running on past the joint by r tan(turn / 2), then cut by the joint's
' plane (the plane through the node whose normal is the sum of the two
' directions): the mitred pipe exactly, and its volume the pipes' axis lengths.
' Modelling parameters -- NOT plant dimensions. No source gives the
' gooseneck's lengths. The rise and the bend are C1's (cyclone.bas),
' where the outlet face had to move past a bend before the backflow on
' it went away. Each arm comes down in one inclined piece and turns
' (mitre) to a level run to its outlet face, a vertical plane at +-x
' (user's sketch, 15 Nov 2026). The runs' axis is C5's inlet axis
' (plant_geometry.gooseneck: C5 stands over the tertiary air duct by
' its clearance), as a fraction of the vessel (cone + cylinder) above
' its bottom, z = zThroatTop.
' -> GN_OUTLET_AT_VESSEL_H, GN_SLOPE_DEG, GN_PIECE_OVER_D, GN_LEVEL_OVER_D: in the generated block above
' -> GN_ARM_DEG, GN_ARM_RUN_OVER_D: in the generated block above
' -> GN_INSIDE_VESSEL, GN_OVERLAP_NECK_ARM, GN_OVERLAP_ARMS, GN_OVERLAP_ALL: in the generated block above
'    GN_OUTLET_AT_VESSEL_H: the arms' level runs' axis, fraction of H_VESSEL
'    GN_SLOPE_DEG: the neck's two inclined pieces, to the horizontal [deg]
'    GN_PIECE_OVER_D, GN_LEVEL_OVER_D: the neck's inclined pieces and its level piece, x neck D
'    GN_ARM_DEG: each arm's angle to the vertical where it leaves the neck [deg]
'    GN_ARM_RUN_OVER_D: the arm's level run to its outlet face, x leg D
'    GN_INSIDE_VESSEL: the neck's first piece's part inside the vessel [m3], GN_OVERLAP_*:
'    what the neck and the arms share [m3] (grids in plant_geometry.py)

' Tertiary air (user decision, 14 Oct 2026). One duct of the derived
' bore, entering at the bottom of the cylinder tangentially, as in a
' 5000 t/d in-line calciner (Chen et al.): its lower edge on the top
' of the cone, its outer wall on the vessel's. Each is kept a hair
' clear -- a round duct whose wall touches the vessel's at a point, or
' whose bottom runs along the cone/cylinder seam, leaves the boolean
' a degenerate edge (cyclone.bas keeps its inlet off the roof for the
' same reason). It comes in along +x, the hood's side, on the -y side
' of the axis, and the domain keeps a stub of it, its face
' TA_STUB_LEN past the vessel's tangent plane x = R.
' -> D_TA, TA_CONE_CLEARANCE, TA_WALL_RELIEF, TA_STUB_LEN: in the generated block above

' Meal feed. Fidaros et al. 2007 feed the raw meal through two round
' 0.6 m pipes at 60 deg to the horizontal; here one on each side of
' the vessel, at +x and -x, in the gooseneck's x-z plane (user
' decision, 29 Sep 2026): each takes one string's C4 meal.
' That is twice the meal of Fidaros's calciner per pipe, so the area
' doubles at the same meal velocity: 0.6 x sqrt 2 = 0.8485 m. Each
' pipe points at the vessel axis and rises away from the wall, so the
' meal falls in towards the middle.
' -> D_FEED, FEED_SLOPE_DEG: in the generated block above
'    D_FEED: [m], Fidaros 2007 x sqrt 2
'    FEED_SLOPE_DEG: below the horizontal, Fidaros 2007

' Fuel. Fidaros's two 0.2 m coal pipes at 30 deg, x sqrt 2 for a
' string each, as the meal pipes; at +y and -y, 90 deg round from them.
' -> D_FUEL, FUEL_SLOPE_DEG: in the generated block above

' Modelling parameters -- NOT plant dimensions. Meal and fuel go in
' just above the tertiary air (Chen et al.: at one height, in
' different directions; US 10,974,992: the main meal inlet above the
' tertiary air inlet; user decision, 14 Oct 2026): each meal pipe's
' hole in the wall starts FEED_ABOVE_TA over the duct's top, and the
' fuel pipes' axes meet the wall where the meal pipes' do. Each pipe
' runs FEED_DEPTH out along its axis past the wall, as C1's feed
' chute does, and starts one pipe diameter inside it. Until 14 Oct the
' meal pipes hung 2 m below the gooseneck's CFD outlet faces, a place
' no plant rule gave.
' -> FEED_ABOVE_TA, FEED_DEPTH: in the generated block above

' Output
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

' Grid points per axis for the volumes the gooseneck's neck and arms
' share: computed in geometry/plant_geometry.py, handed over as the
' GN_OVERLAP_* constants (their error is well under VOL_TOL on the body).
' -> OVERLAP_N: in the generated block above (plant_geometry.py's grid)

' Verification tolerances
Const VOL_TOL  As Double = 0.001   ' relative, on every closed-form stage volume
' A feed pipe adds well under a cubic metre to a ~1870 m3 body, under
' VOL_TOL on the whole, so its stage is also checked on the volume it ADDS, to this.
Const FEED_VOL_TOL As Double = 0.01
' What a pipe adds is the difference of two ~1640 m3 volumes, each good to about
' 1e-6 of itself (SolidWorks' mass properties): the fuel pipe, 0.063 m3, read
' 1.5 and 2.9 % off on two builds of the same pipe; with the shorter gooseneck
' (24 Nov 2026, ~1536 m3) the +y one read 0.0773 (23 %, 0.0145 m3 = 0.9e-5 of the
' body). So the check has this much of the body's volume as a floor; the end face's
' area still checks the pipe, CheckStageVol the whole to VOL_TOL.
Const ADD_NOISE As Double = 0.000015
Const AREA_TOL As Double = 0.002   ' relative, on face areas
Const BOX_TOL  As Double = 0.005   ' absolute [m]; GetBodyBox may overstate curved faces
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001

' -> P_ATM, R_GAS: in the generated block above
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

' (b) derived coordinates -- every one computed, none typed in
Dim R As Double                             ' vessel radius
Dim rhoKiln As Double                       ' kiln gas density at the throat [kg/m3]
Dim qKiln As Double                         ' kiln gas volume flow [m3/s]
Dim rThroat As Double                       ' throat radius
Dim zThroatTop As Double                    ' where the throat meets the cone
Dim hCone As Double                         ' cone height
Dim zConeTop As Double                      ' where the cone meets the cylinder
Dim zRoof As Double                         ' the vessel's flat roof
Dim rGn As Double                           ' gooseneck arm radius
Dim rNeck As Double                         ' the neck's radius, two arms' area
Dim gnBeta As Double                        ' the neck's inclined pieces, to the horizontal [rad]
Dim gnPiece As Double, gnLevel As Double    ' the neck's pieces' axis lengths
Dim gnSet As Double                         ' the first piece's cap, this far behind the roof point along its axis
Dim fN(4) As Double, zN(4) As Double        ' the neck's nodes (forward = -y, z): N0 on the roof, N1, N2, N3 where the channel starts, N4 its lower end
Dim gnYoff As Double                        ' the neck's channel, and the arms, at y = -this
Dim gnChan As Double                        ' the vertical channel below the third piece, its length
Dim zSplit As Double                        ' the channel's lower end, z: the arms leave it
Dim armAng As Double, armLa As Double       ' each arm's angle to the vertical, its inclined piece (axis, to the mitre node)
Dim armRun As Double, xBend As Double       ' each arm's level run, and where the arm turns level (x = +-this)
Dim xGnLeg As Double                        ' the two gas outlet faces, x = +-this (vertical planes), y = -gnYoff
Dim zGnOut As Double                        ' the arms' level runs' axis, z (the outlet faces' centres)
Dim zGnApex As Double                       ' highest point of the neck: the level piece's top
Dim eNeck As Double, eArm As Double         ' how far a mitred pipe runs on past its joint
Dim xBoxMax As Double                       ' the arms' outlet faces, |x|
Dim yBoxMin As Double                       ' the channel's front wall (the foremost part), y
Dim vRun As Double                          ' the volume the build should have reached so far
Dim vArmRun As Double, vArmPiece As Double
Dim rTA As Double                           ' tertiary air duct radius
Dim xTA As Double, zTA As Double            ' its axis, parallel to y, through (xTA, ., zTA)
Dim yTAEnd As Double                        ' its face, the tertiary_air_inlet, at y = this (< 0)
' The meal (+-x) and fuel (+-y) pipes. Each in its own vertical plane
' through the vessel axis, along a horizontal "radial" rho out from the
' axis: it starts at rho0, one pipe diameter inside the wall, rises
' away from it at its slope (axis e = (c, s) in rho, z), meets the
' wall at zFeed and ends FEED_DEPTH past it.
Dim rFeed As Double, s1 As Double
Dim xFeedEnd As Double, zFeedEnd As Double  ' centre of the end face, the meal_feed, at x = +-xFeedEnd
Dim xFeedMax As Double                      ' |x| of the end faces' outer edges
Dim zFeed As Double                         ' where each meal and fuel pipe's axis meets the wall
Dim rFuel As Double, uc As Double, us As Double
Dim rhoFuel0 As Double, zFuelStart As Double, lFuel As Double
Dim yFuelEnd As Double, zFuelEnd As Double  ' centre of the end face, the fuel_inlet, at y = +-yFuelEnd
Dim yFuelMax As Double                      ' |y| of the end faces' outer edges
Dim outName As String                       ' file name the solid is written under

' Sketch axis directions, measured at run time by CalibrateSketchAxes.
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profiles
Dim uSignY As Double, vSignY As Double      ' the y = 0 plane, for the feed pipes
Dim uSignO As Double, vSignO As Double      ' y = -gnYoff, the arms' plane

' The dispersion boxes (user decision, 28 Nov 2026): a wedge cut flat, on the wall at +-x. Its
' section in the y = 0 plane (rho radial, z): the top level at boxZ1; the floor level at boxZ0 from
' the chord plane rho = boxRin (inside the wall's thickness, the cylinder's curve hidden) to the
' tangent plane rho = R, then a ramp at BOX_SLOPE_DEG up to the back face at boxRout (boxBackH
' under the top); boxH high at the open window in the tangent plane, boxW wide across. A vertical
' meal pipe stands on its top face at rho = boxRp, its top face the meal_feed.
Dim boxW As Double, boxBackH As Double, boxH As Double, boxTan As Double
Dim boxRin As Double, boxRout As Double, boxRp As Double
Dim boxZ0 As Double, boxZ1 As Double, boxZFoot As Double, zPipeTop As Double
Dim pipeMidZ As Double, pipeLen As Double

' The off-plane component of the first point drawn in the sketch
' now open; see G2S.
Dim wRef As Double
Dim wRefSet As Boolean

' expected volumes, all closed form
Dim vThroat As Double, vCone As Double, vCyl As Double, vVessel As Double
Dim vFeed As Double                         ' one feed pipe, the part outside the vessel
Dim vTA As Double                           ' the tertiary air stub, the part outside the vessel
Dim vFuel As Double                         ' one fuel pipe, the part outside the vessel
Dim vStage1 As Double, vStage2 As Double, vStage3a As Double, vStage3b As Double
Dim vStage4 As Double, vStage5a As Double, vStage5b As Double, vStage6 As Double
Dim vStage7a As Double, vStage7b As Double
Dim vFinal As Double

Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStlUnits As Long, oldStlQuality As Long
Dim oldStepAppear As Boolean, oldStlBinary As Boolean
Dim oldStlNoShift As Boolean, oldStlInfo As Boolean
Dim oldStlDev As Double, oldStlAngle As Double

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

    Restore
    WriteLog CALCINER_NAME & " built, verified and exported"
    ' no message box when OUT_ROOT\quiet.flag exists (a run from WSL, tools/sw_run.py):
    ' the log carries the result
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox CALCINER_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, _
               vbInformation, "Calciner"
    End If
    Exit Sub

Failed:
    ' Read the reason BEFORE Restore: the On Error statement inside
    ' it resets the Err object and the reason would be lost.
    why = Err.Description
    Restore
    WriteLog CALCINER_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox CALCINER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Calciner"
    End If

End Sub


'==================================================================
' (b) Derived coordinates
'==================================================================
Private Sub Derive()

    Dim mMol As Double

    R = 0.5 * D_VESSEL

    ' Throat: literature flow over literature velocity. Molar masses
    ' in kg/mol.
    mMol = X_N2 * M_N2 + X_O2 * M_O2 + X_H2O * M_H2O + X_CO2 * M_CO2
    rhoKiln = P_ATM * mMol / (R_GAS * T_KILN_GAS)
    qKiln = M_KILN_GAS / rhoKiln
    rThroat = Sqr(qKiln / (PI * U_THROAT))

    zThroatTop = THROAT_LEN_OVER_D * 2# * rThroat
    hCone = (R - rThroat) * Tan(CONE_DEG * PI / 180#)
    zConeTop = zThroatTop + hCone
    zRoof = zThroatTop + H_VESSEL

    ' ---- closed-form volumes, one per build stage ----
    vThroat = PI * rThroat * rThroat * zThroatTop
    vCone = (PI / 3#) * hCone * (R * R + R * rThroat + rThroat * rThroat)
    vCyl = PI * R * R * (H_VESSEL - hCone)
    vVessel = vCone + vCyl

    ' Gooseneck. One neck of both arms' area, three straight pieces and
    ' a vertical channel; two arms from its lower end.
    rGn = 0.5 * D_GOOSENECK_SRC
    rNeck = rGn * Sqr(2#)
    gnBeta = GN_SLOPE_DEG * PI / 180#
    gnPiece = GN_PIECE_OVER_D * 2# * rNeck
    gnLevel = GN_LEVEL_OVER_D * 2# * rNeck
    gnSet = rNeck
    fN(0) = GN_ROOT_FWD: zN(0) = zRoof
    fN(1) = fN(0) + gnPiece * Cos(gnBeta): zN(1) = zN(0) + gnPiece * Sin(gnBeta)
    fN(2) = fN(1) + gnLevel: zN(2) = zN(1)
    fN(3) = fN(2) + gnPiece * Cos(gnBeta): zN(3) = zN(2) - gnPiece * Sin(gnBeta)
    gnChan = GN_CHANNEL_OVER_D * 2# * rNeck
    fN(4) = fN(3): zN(4) = zN(3) - gnChan
    gnYoff = fN(3)
    zSplit = zN(4)
    zGnApex = zN(1) + rNeck
    eNeck = rNeck * Tan(gnBeta / 2#)

    armAng = GN_ARM_DEG * PI / 180#
    armRun = GN_ARM_RUN_OVER_D * 2# * rGn
    zGnOut = zThroatTop + GN_OUTLET_AT_VESSEL_H * H_VESSEL
    If zGnOut >= zSplit Then
        Fail "the arms' level runs at z = " & Fmt(zGnOut) & " m are not below the channel's end, z = " & Fmt(zSplit) & " m."
    End If
    armLa = (zSplit - zGnOut) / Cos(armAng)
    xBend = (zSplit - zGnOut) * Tan(armAng)
    xGnLeg = xBend + armRun
    eArm = rGn * Tan((PI / 2# - armAng) / 2#)    ' the mitre turns by 90 deg less the arm's angle
    xBoxMax = xGnLeg
    yBoxMin = -(gnYoff + rNeck)

    vRun = 0#
    vArmRun = PI * rGn * rGn * armRun
    vArmPiece = PI * rGn * rGn * armLa

    vStage1 = vThroat + vVessel            ' throat + cone + cylinder
    ' + the neck: three pieces, each the pipes' axis length (a mitre adds
    ' exactly that), the first from its cap, less what of it is inside the vessel
    ' (a grid, plant_geometry.py)
    vStage2 = vStage1 + PI * rNeck * rNeck * (gnSet + 2# * gnPiece + gnLevel + gnChan) - GN_INSIDE_VESSEL
    vStage3a = vStage2 + vArmRun + vArmPiece - GN_OVERLAP_NECK_ARM   ' + the +x arm
    ' Meal feed pipes. Checked here, not in PreChecks: at 90 deg the
    ' lines below divide by zero before PreChecks runs.
    If FUEL_SLOPE_DEG <= 0# Or FUEL_SLOPE_DEG >= 90# Then
        Fail "FUEL_SLOPE_DEG is " & Fmt(FUEL_SLOPE_DEG) & "; the fuel pipes have to slope " & _
             "between the horizontal and the vertical."
    End If

    ' Tertiary air: tangential at the bottom of the cylinder, its axis
    ' parallel to x on the -y side, from x = 0 (inside the vessel) out
    ' to its face. Every line of it along x leaves the vessel at
    ' sqrt(R^2 - y^2), so what the merge keeps is the stub less the
    ' vessel's half chord integrated over the disc.
    rTA = 0.5 * D_TA
    xTA = -(R - TA_WALL_RELIEF - rTA)
    zTA = zConeTop + TA_CONE_CLEARANCE + rTA
    yTAEnd = -(R + TA_STUB_LEN)
    vTA = PI * rTA * rTA * (-yTAEnd) - ChordIntegral(rTA, xTA)

    ' Meal: a vertical pipe into a dispersion box on the wall (user 28 Nov
    ' 2026). The box's bottom is FEED_ABOVE_TA over the duct's top; it stands out
    ' from the chord plane rho_in = sqrt(R^2 - (a/2)^2) by its edge a, so its four
    ' sides meet the cylinder. What it adds outside the vessel: a x (the strip
    ' between the cylinder and the outer face over the width) plus the pipe.
    rFeed = 0.5 * D_FEED
    boxW = BOX_WIDTH_OVER_D * D_FEED
    boxBackH = BOX_BACK_H_OVER_D * D_FEED
    boxTan = Tan(BOX_SLOPE_DEG * PI / 180#)
    boxRin = Sqr(R * R - 0.25 * boxW * boxW)
    boxRout = R + BOX_DEPTH_OVER_D * D_FEED
    boxRp = boxRout - 0.5 * BOX_DEPTH_OVER_D * D_FEED
    boxH = boxBackH + (boxRout - R) * boxTan
    boxZ0 = zTA + rTA + FEED_ABOVE_TA
    boxZ1 = boxZ0 + boxH
    boxZFoot = boxZ1 - boxBackH
    zFeed = boxZ0 + 0.5 * boxH              ' the fuel pipes meet the wall at the box's mid height
    zPipeTop = boxZ1 + BOX_PIPE_RISE
    pipeLen = BOX_PIPE_RISE + 0.1           ' 0.1 m into the box so the two merge on volume
    pipeMidZ = boxZ1 + 0.5 * (BOX_PIPE_RISE - 0.1)
    xFeedEnd = boxRp
    zFeedEnd = zPipeTop
    xFeedMax = boxRout
    ' what the merge keeps outside the vessel: the lead-in (rho_in .. R) at the full height over
    ' what is outside the cylinder (w R less the integral of sqrt(R^2 - y^2) over the width),
    ' the ramp and back face beyond R, the pipe on top
    s1 = 0.5 * boxW * boxRin + R * R * ArcSin(0.5 * boxW / R)
    vFeed = boxH * (boxW * R - s1) + boxW * (boxBackH * (boxRout - R) + 0.5 * boxTan * (boxRout - R) ^ 2) + _
            PI * rFeed * rFeed * BOX_PIPE_RISE

    ' Fuel pipes, at the meal pipes' height, the same way.
    rFuel = 0.5 * D_FUEL
    uc = Cos(FUEL_SLOPE_DEG * PI / 180#)
    us = Sin(FUEL_SLOPE_DEG * PI / 180#)
    rhoFuel0 = R - D_FUEL
    zFuelStart = zFeed - (R - rhoFuel0) * (us / uc)
    lFuel = (R - rhoFuel0) / uc + FEED_DEPTH
    yFuelEnd = R + FEED_DEPTH * uc
    zFuelEnd = zFeed + FEED_DEPTH * us
    yFuelMax = yFuelEnd + rFuel * us
    vFuel = PI * rFuel * rFuel * lFuel - (ChordIntegral(rFuel, 0#) - rhoFuel0 * PI * rFuel * rFuel) / uc

    vStage3b = vStage3a + vArmRun + vArmPiece - GN_OVERLAP_NECK_ARM - GN_OVERLAP_ARMS + GN_OVERLAP_ALL   ' + the -x arm
    vStage4 = vStage3b
    vStage5a = vStage4 + vFeed             ' + the +x meal feed pipe
    vStage5b = vStage5a + vFeed            ' + the -x meal feed pipe
    vStage6 = vStage5b + vTA               ' + the tertiary air duct
    vStage7a = vStage6 + vFuel             ' + the +y fuel pipe
    vStage7b = vStage7a + vFuel            ' + the -y fuel pipe
    vFinal = vStage7b                      ' the CFD domain

    outName = CALCINER_NAME

End Sub


'==================================================================
' (c) Pre-checks. A combination that cannot be built is refused; no
'     dimension is ever adjusted to make it buildable.
'==================================================================
Private Sub PreChecks()

    ' 1. the cone has to open, not close
    If rThroat >= R Then
        Fail "the throat (D " & Fmt(2# * rThroat) & " m) is not narrower than the vessel (D " & _
             Fmt(D_VESSEL) & " m); there is no cone to build."
    End If

    ' 2. a cone angle a wall can have
    If CONE_DEG <= 0# Or CONE_DEG >= 90# Then
        Fail "CONE_DEG is " & Fmt(CONE_DEG) & "; the cone wall has to lie between the " & _
             "horizontal and the vertical."
    End If

    ' 3. the cone has to fit inside the vessel height, with cylinder
    '    left above it
    If hCone >= H_VESSEL Then
        Fail "the cone is " & Fmt(hCone) & " m tall, not shorter than the whole vessel (" & _
             Fmt(H_VESSEL) & " m)."
    End If

    ' 4. the gas inlet face has to sit on a straight run below the cone
    If THROAT_LEN_OVER_D <= 0# Then
        Fail "THROAT_LEN_OVER_D is " & Fmt(THROAT_LEN_OVER_D) & ". The kiln gas inlet face " & _
             "would sit on the cone's lip."
    End If

    ' 5. the neck's first piece through the roof, whose opening is an
    '    ellipse of semi-axes r and r / sin(slope) -- more than the roof
    '    is wide, and left so: the pipe laps the roof's edge a little
    If gnBeta <= 0# Or gnBeta >= PI / 2# Then
        Fail "GN_SLOPE_DEG is " & Fmt(GN_SLOPE_DEG) & "; the neck's inclined pieces have to lie between the horizontal and the vertical."
    End If
    If rNeck >= R Then
        Fail "the gooseneck neck (D " & Fmt(2# * rNeck) & " m) is not narrower than the D " & Fmt(D_VESSEL) & " m vessel."
    End If

    ' 6. the neck's pieces: a mitre takes r tan(turn / 2) of a pipe's
    '    length at each end, so a piece between two joints has to be
    '    longer than twice that
    If GN_PIECE_OVER_D <= 0# Or GN_LEVEL_OVER_D <= 0# Then
        Fail "GN_PIECE_OVER_D and GN_LEVEL_OVER_D have to be positive."
    End If
    If gnLevel <= 2# * rNeck * Tan(gnBeta / 2#) Or gnPiece <= rNeck * Tan(gnBeta / 2#) Then
        Fail "the neck's pieces are too short for their mitres: the level piece has to exceed " & _
             Fmt(2# * rNeck * Tan(gnBeta / 2#)) & " m, the inclined ones " & Fmt(rNeck * Tan(gnBeta / 2#)) & " m."
    End If

    ' 7. the arms
    If armAng <= 0# Or armAng >= PI / 2# Then
        Fail "GN_ARM_DEG is " & Fmt(GN_ARM_DEG) & "; the arms have to leave the neck between the vertical and the horizontal."
    End If
    If armLa <= eArm Or armRun <= eArm Then
        Fail "the arms' inclined piece (" & Fmt(armLa) & " m) or level run (" & Fmt(armRun) & " m) is shorter than its mitre needs (" & Fmt(eArm) & " m)."
    End If
    If gnChan <= eNeck Then
        Fail "the neck's vertical channel (" & Fmt(gnChan) & " m) is shorter than its mitre needs (" & Fmt(eNeck) & " m)."
    End If
    If xBend - eArm <= 0# Then
        Fail "the arms turn level at x = +-" & Fmt(xBend) & " m, inside the mitre's " & Fmt(eArm) & " m of the channel."
    End If
    If gnYoff - rGn - R <= 0# Then
        Fail "the arms' plane at y = -" & Fmt(gnYoff) & " m is not clear of the vessel."
    End If
    ' 8. the tertiary air duct: clear of the cone and of the vessel's
    '    wall by its two hairs, inside the cylinder, out past the wall
    If TA_CONE_CLEARANCE <= 0# Or TA_WALL_RELIEF <= 0# Then
        Fail "TA_CONE_CLEARANCE and TA_WALL_RELIEF have to be positive: a duct touching the " & _
             "cone's seam or the vessel's wall leaves the boolean a degenerate edge."
    End If
    If 2# * rTA + TA_WALL_RELIEF >= 2# * R Then
        Fail "the tertiary air duct (D " & Fmt(D_TA) & " m) does not fit across the vessel."
    End If
    If zTA + rTA >= zRoof Then
        Fail "the tertiary air duct reaches the roof."
    End If
    If TA_STUB_LEN <= 0# Then Fail "TA_STUB_LEN is " & Fmt(TA_STUB_LEN) & "; the duct's face would be inside the vessel."

    ' 9. the meal and fuel pipes. Each end face has to lie wholly
    '    outside the vessel, or part of it merges away: its edge
    '    nearest the wall reaches in by r * sin.
    If FEED_DEPTH * uc <= rFuel * us Then
        Fail "the fuel pipes' end faces reach back into the vessel; FEED_DEPTH must exceed " & _
             Fmt(rFuel * us / uc) & " m at " & Fmt(FUEL_SLOPE_DEG) & " deg."
    End If
    If FEED_ABOVE_TA <= 0# Then
        Fail "FEED_ABOVE_TA is " & Fmt(FEED_ABOVE_TA) & "; the meal pipes' holes would run into " & _
             "the tertiary air duct."
    End If
    ' The fuel pipes meet the wall where the meal pipes do; their holes
    ' have to clear the duct too.
    If zFeed - rFuel / uc - (R - Sqr(R * R - rFuel * rFuel)) * (us / uc) <= zTA + rTA Then
        Fail "the fuel pipes' holes reach down into the tertiary air duct."
    End If
    ' The fuel pipes' start discs sit inside the vessel, over the cone.
    If zFuelStart - rFuel * uc <= zConeTop Then
        Fail "the fuel pipes start at z = " & Fmt(zFuelStart - rFuel * uc) & " m, inside the cone."
    End If
    ' The duct is on the -y side, from x = 0 out; the meal pipes are at
    ' y = 0, the fuel pipes at x = 0. Clear of it in y and z.
    If xTA + rTA >= -rFuel Then
        Fail "the tertiary air duct reaches x = " & Fmt(xTA + rTA) & " m, into the -y fuel pipe."
    End If
    If zGnOut <= zConeTop Then
        Fail "the gooseneck's level runs are at z = " & Fmt(zGnOut) & " m, below the top of " & _
             "the cone at z = " & Fmt(zConeTop) & " m."
    End If


    ' 10. the dispersion boxes: the box has to fit the vessel, its pipe stand clear
    '     of the cylinder, its bottom stay over the tertiary air duct's top and the
    '     whole of it over the cone.
    If BOX_WIDTH_OVER_D <= 0# Or BOX_DEPTH_OVER_D <= 0# Or BOX_BACK_H_OVER_D < 0# Or BOX_PIPE_RISE <= 0# Or _
       BOX_SLOPE_DEG <= 0# Or BOX_SLOPE_DEG >= 90# Then Fail "the BOX_* sizes have to be positive and the slope between 0 and 90 deg."
    If 0.5 * boxW >= R Then Fail "the dispersion box (width " & Fmt(boxW) & " m) does not fit the vessel."
    If boxRp - rFeed <= R Then Fail "the dispersion box's pipe reaches into the vessel."
    If boxZ0 <= zTA + rTA Then Fail "the dispersion box's bottom is not over the tertiary air duct's top."
    If boxZ0 <= zConeTop Then Fail "the dispersion box's bottom is not over the cone's top."
    If boxZ1 + BOX_PIPE_RISE >= zRoof Then Fail "the dispersion box's pipe top is over the roof."

    Note "kiln gas: " & Fmt(M_KILN_GAS) & " kg/s at " & Fmt(T_KILN_GAS) & " K, rho " & _
         Fmt(rhoKiln) & " kg/m3, " & Fmt(qKiln) & " m3/s"
    Note "throat D " & Fmt(2# * rThroat) & " m at " & Fmt(U_THROAT) & " m/s, " & _
         Fmt(zThroatTop) & " m long"
    Note "cone " & Fmt(CONE_DEG) & " deg, " & Fmt(hCone) & " m tall, z " & Fmt(zThroatTop) & _
         " .. " & Fmt(zConeTop) & " m"
    Note "cylinder D " & Fmt(D_VESSEL) & " m, z " & Fmt(zConeTop) & " .. " & Fmt(zRoof) & " m"
    Note "gooseneck neck: D " & Fmt(2# * rNeck) & " m, 3 straight pieces at " & Fmt(GN_SLOPE_DEG) & _
         " deg: " & Fmt(gnPiece) & " m, level " & Fmt(gnLevel) & " m, " & Fmt(gnPiece) & " m; first piece's cap " & _
         Fmt(gnSet) & " m behind the roof point (" & Fmt(GN_INSIDE_VESSEL) & " m3 inside the vessel); crown z = " & _
         Fmt(zGnApex) & " m; lower end at y = -" & Fmt(gnYoff) & " m, z = " & Fmt(zSplit) & " m"
    Note "gooseneck channel: vertical, D " & Fmt(2# * rNeck) & " m, " & Fmt(gnChan) & " m long, from z = " & _
         Fmt(zN(3)) & " m to z = " & Fmt(zN(4)) & " m, where the arms leave"
    Note "gooseneck arms: 2 arms D " & Fmt(2# * rGn) & " m leaving the channel's lower end at " & Fmt(GN_ARM_DEG) & _
         " deg, piece " & Fmt(armLa) & " m, level runs " & Fmt(armRun) & " m from x = +-" & Fmt(xBend) & _
         " m to the outlet faces at x = +-" & Fmt(xGnLeg) & " m, z = " & Fmt(zGnOut) & " m (channel x arm " & Fmt(GN_OVERLAP_NECK_ARM) & _
         " m3, arms " & Fmt(GN_OVERLAP_ARMS) & " m3, all " & Fmt(GN_OVERLAP_ALL) & " m3 shared)"
    Note "tertiary air: duct D " & Fmt(D_TA) & " m, tangential, axis at x = " & Fmt(xTA) & _
         " m, z = " & Fmt(zTA) & " m, face at y = " & Fmt(yTAEnd) & " m, " & Fmt(vTA) & _
         " m3 outside the vessel"
    Note "meal feed: 2 dispersion boxes, wedge, width " & Fmt(boxW) & " m, back face rho " & Fmt(boxRout) & " m " & _
         Fmt(boxBackH) & " m high, floor " & Fmt(BOX_SLOPE_DEG) & " deg down to the window in the tangent plane (flat lead-in from rho " & Fmt(boxRin) & _
         " m), " & Fmt(boxH) & " m high, z " & Fmt(boxZ0) & " .. " & Fmt(boxZ1) & " m; vertical pipe D " & Fmt(D_FEED) & _
         " m on its top, axis rho " & Fmt(boxRp) & " m, top face centred (+-" & Fmt(xFeedEnd) & ", 0, " & _
         Fmt(zFeedEnd) & "), " & Fmt(vFeed) & " m3 each outside the vessel"
    Note "fuel: 2 pipes D " & Fmt(D_FUEL) & " m at " & Fmt(FUEL_SLOPE_DEG) & _
         " deg, axes meet the wall at z = " & Fmt(zFeed) & " m, end faces centred (0, +-" & _
         Fmt(yFuelEnd) & ", " & Fmt(zFuelEnd) & "), " & Fmt(vFuel) & " m3 each outside the vessel"
    Note "vessel volume (cone + cylinder)   " & Fmt(vVessel) & " m3"
    Note "CFD domain volume                 " & Fmt(vFinal) & " m3"
End Sub


'==================================================================
' (d) Build
'==================================================================
Private Sub Build()

    Dim planeX0 As SldWorks.Feature       ' the x = 0 plane
    Dim planeY0 As SldWorks.Feature       ' the y = 0 plane
    Dim planeZ0 As SldWorks.Feature       ' the z = 0 plane
    Dim planeYoff As SldWorks.Feature     ' y = -gnYoff: the arms' plane
    Dim planePipeZ As SldWorks.Feature        ' z = the pipe's mid height
    Dim uPipeZ As Double, vPipeZ As Double
    Dim f As SldWorks.Feature
    Dim sg As Double, i As Long

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
    ' All probes run while the part is still empty. Once the vessel
    ' is there a probe would land inside it, merge with it, and then
    ' measure the merged body instead of itself.
    Set planeYoff = OffsetPlane(planeY0, 0#, -gnYoff, 0#, uSignO, vSignO)
    ' the boxes' planes now, while the part is empty (the calibration needs that)
    Set planePipeZ = OffsetPlane(planeZ0, 0#, 0#, pipeMidZ, uPipeZ, vPipeZ)
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX
    CalibrateSketchAxes planeY0, 0#, 0#, 0#, uSignY, vSignY

    '--- 1. throat + cone + cylinder --------------------------------
    Set f = RevolveProfile(planeX0, Array( _
        0#, 0#, _
        rThroat, 0#, _
        rThroat, zThroatTop, _
        R, zConeTop, _
        R, zRoof, _
        0#, zRoof), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the throat + cone + cylinder profile."
    CheckStage "1  throat + cone + cylinder", vStage1, -R, -R, 0#, R, R, zRoof

    '--- 2. the neck: three straight pieces, mitred -------------------
    ' Each piece is a pipe that runs on past a joint by eNeck; it is cut
    ' by the joint's plane (MitrePiece) and joined to what is there.
    ' Where two pipes meet, the plane is the one through the joint's node
    ' whose normal is the sum of their directions.
    Dim d1(2) As Double, d2(2) As Double, d3(2) As Double
    Dim m1(2) As Double, m2(2) As Double, m3(2) As Double, nd1(2) As Double, nd2(2) As Double, nd3(2) As Double
    Dim d4(2) As Double
    Dim q0(2) As Double, q1(2) As Double
    Dim cuts(11) As Double

    d1(0) = 0#: d1(1) = -Cos(gnBeta): d1(2) = Sin(gnBeta)
    d2(0) = 0#: d2(1) = -1#:          d2(2) = 0#
    d3(0) = 0#: d3(1) = -Cos(gnBeta): d3(2) = -Sin(gnBeta)
    nd1(0) = 0#: nd1(1) = -fN(1): nd1(2) = zN(1)
    d4(0) = 0#: d4(1) = 0#:           d4(2) = -1#
    nd2(0) = 0#: nd2(1) = -fN(2): nd2(2) = zN(2)
    nd3(0) = 0#: nd3(1) = -fN(3): nd3(2) = zN(3)
    BisectorOf d1, d2, m1
    BisectorOf d2, d3, m2
    BisectorOf d3, d4, m3

    vRun = vStage1
    ' the first piece, from its cap inside the vessel to joint 1 (kept:
    ' behind m1). It pierces the roof GN_ROOT_FWD in front of the axis, so
    ' its cap lies wholly inside the vessel; what is inside merges away
    q0(0) = 0#: q0(1) = -fN(0) + gnSet * Cos(gnBeta): q0(2) = zRoof - gnSet * Sin(gnBeta)
    q1(0) = 0#: q1(1) = nd1(1) + eNeck * d1(1): q1(2) = nd1(2) + eNeck * d1(2)
    PutJointCut cuts, 0, nd1, m1, -1#
    MitrePiece planeX0, uSignX, vSignX, True, q0, q1, rNeck, cuts, 1, _
               PI * rNeck * rNeck * (gnSet + gnPiece) - GN_INSIDE_VESSEL, "2.1 neck, first piece"
    ' the level piece, between the two joints (kept: beyond m1, behind m2)
    q0(0) = 0#: q0(1) = nd1(1) - eNeck * d2(1): q0(2) = nd1(2)
    q1(0) = 0#: q1(1) = nd2(1) + eNeck * d2(1): q1(2) = nd2(2)
    PutJointCut cuts, 0, nd1, m1, 1#
    PutJointCut cuts, 1, nd2, m2, -1#
    MitrePiece planeX0, uSignX, vSignX, True, q0, q1, rNeck, cuts, 2, _
               PI * rNeck * rNeck * gnLevel, "2.2 neck, level piece"
    ' the last piece, from joint 2 to joint 3 (kept: beyond m2, behind m3)
    q0(0) = 0#: q0(1) = nd2(1) - eNeck * d3(1): q0(2) = nd2(2) - eNeck * d3(2)
    q1(0) = 0#: q1(1) = nd3(1) + eNeck * d3(1): q1(2) = nd3(2) + eNeck * d3(2)
    PutJointCut cuts, 0, nd2, m2, 1#
    PutJointCut cuts, 1, nd3, m3, -1#
    MitrePiece planeX0, uSignX, vSignX, True, q0, q1, rNeck, cuts, 2, _
               PI * rNeck * rNeck * gnPiece, "2.3 neck, last piece"
    ' the vertical channel, from joint 3 down to the arms' node (kept: beyond m3)
    q0(0) = 0#: q0(1) = nd3(1): q0(2) = nd3(2) - eNeck * d4(2)
    q1(0) = 0#: q1(1) = -fN(4): q1(2) = zN(4)
    PutJointCut cuts, 0, nd3, m3, 1#
    MitrePiece planeX0, uSignX, vSignX, True, q0, q1, rNeck, cuts, 1, _
               PI * rNeck * rNeck * gnChan, "2.4 neck, vertical channel"
    CheckStageVol "2  + gooseneck neck", vStage2

    '--- 3. the two arms ----------------------------------------------
    ' In the plane y = -gnYoff across the channel's lower end. Each: the
    ' inclined piece from the channel's end (its start disc inside the channel)
    ' and the level run to the outlet face, mitred where they meet.
    Dim da(2) As Double, db(2) As Double, ma(2) As Double, nda(2) As Double
    For i = 0 To 1
        sg = 1# - 2# * i
        da(0) = sg * Sin(armAng): da(1) = 0#: da(2) = -Cos(armAng)
        db(0) = sg: db(1) = 0#: db(2) = 0#
        nda(0) = sg * xBend: nda(1) = -gnYoff: nda(2) = zGnOut
        BisectorOf da, db, ma
        q0(0) = 0#: q0(1) = -gnYoff: q0(2) = zSplit
        q1(0) = nda(0) + eArm * da(0): q1(1) = -gnYoff: q1(2) = nda(2) + eArm * da(2)
        PutJointCut cuts, 0, nda, ma, -1#
        If i = 0 Then
            MitrePiece planeYoff, uSignO, vSignO, False, q0, q1, rGn, cuts, 1, _
                       PI * rGn * rGn * armLa - GN_OVERLAP_NECK_ARM, "3 arm piece"
        Else
            MitrePiece planeYoff, uSignO, vSignO, False, q0, q1, rGn, cuts, 1, _
                       PI * rGn * rGn * armLa - GN_OVERLAP_NECK_ARM - GN_OVERLAP_ARMS + GN_OVERLAP_ALL, "3 arm piece"
        End If
        q0(0) = nda(0) - eArm * db(0): q0(1) = -gnYoff: q0(2) = nda(2) - eArm * db(2)
        q1(0) = sg * xGnLeg: q1(1) = -gnYoff: q1(2) = zGnOut
        PutJointCut cuts, 0, nda, ma, 1#
        MitrePiece planeYoff, uSignO, vSignO, False, q0, q1, rGn, cuts, 1, _
                   PI * rGn * rGn * armRun, "3 arm level run"
        If i = 0 Then
            CheckStageVol "3a + gooseneck arm, +x", vStage3a
        Else
            CheckStageVol "3b + gooseneck arm, -x", vStage3b
        End If
    Next i
    vStage4 = vStage3b

    '--- 5. the two meal feed pipes, at +x and -x ---------------------
    ' Each is a rectangle in the y = 0 plane revolved about its own
    ' axis edge. A full turn has no direction to get wrong; the end
    ' face, found at +x or -x, says which side each landed on. The
    ' drops reach further out in x, so the box does not move.
    AddMealBox planeY0, planePipeZ, uPipeZ, vPipeZ, 1#, vFeed, "5a + meal box, +x"
    CheckStageVol "5a + meal box, +x", vStage5a
    AddMealBox planeY0, planePipeZ, uPipeZ, vPipeZ, -1#, vFeed, "5b + meal box, -x"
    CheckStageVol "5b + meal box, -x", vStage5b

    AddTertiaryAir planeY0, "6  + tertiary air"
    CheckStageVol "6  + tertiary air", vStage6

    '--- 7. the two fuel pipes, at +y and -y ---------------------------
    ' As the meal pipes, in the x = 0 plane; they reach out past the
    ' vessel in y, so the box grows there.
    AddPipe planeX0, 1, 1#, rFuel, uc, us, rhoFuel0, zFuelStart, lFuel, yFuelEnd, zFuelEnd, _
            vFuel, "fuel_inlet", "7a + fuel, +y"
    CheckStageVol "7a + fuel, +y", vStage7a
    AddPipe planeX0, 1, -1#, rFuel, uc, us, rhoFuel0, zFuelStart, lFuel, yFuelEnd, zFuelEnd, _
            vFuel, "fuel_inlet", "7b + fuel, -y"
    CheckStageVol "7b + fuel, -y", vStage7b

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

End Sub


' A closed profile in the x = 0 plane, given as r, z pairs, revolved
' 360 deg about the calciner axis. Where the profile is closed by a
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
' point, with the sketch axes on it measured at the same time --
' copied from cyclone.bas. Which side of the base plane
' InsertRefPlane puts the offset on is not ours to choose and cannot
' be read back off the sketch transform, so it is measured: a test
' block is dropped on the plane and its box read back. A plane on
' the wrong side fails that test and is deleted, and the other side
' is tried.
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


' A straight pipe of radius rr from P0 to P1, both in plane pl: a
' rectangle from the axis out along n (in the plane, normal to the
' axis) revolved a full turn about its axis edge -- a full turn has no
' direction to get wrong. dv is the volume it should add, bodies the
' number of solid bodies the part should hold after it.
Private Sub RectPipe(pl As SldWorks.Feature, ByVal usg As Double, ByVal vsg As Double, _
                     ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                     ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double, _
                     ByVal nx As Double, ByVal ny As Double, ByVal nz As Double, ByVal rr As Double, _
                     ByVal dv As Double, ByVal bodies As Long, ByVal stage As String)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim axisSeg As SldWorks.SketchSegment
    Dim seg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim px(3) As Double, py(3) As Double, pz(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim i As Long, j As Long

    uSign = usg: vSign = vsg
    px(0) = x0: py(0) = y0: pz(0) = z0
    px(1) = x1: py(1) = y1: pz(1) = z1
    px(2) = x1 + rr * nx: py(2) = y1 + rr * ny: pz(2) = z1 + rr * nz
    px(3) = x0 + rr * nx: py(3) = y0 + rr * ny: pz(3) = z0 + rr * nz

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, px(i), py(i), pz(i), u0, v0
        G2S sk, px(j), py(j), pz(j), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed at stage " & stage & "."
        If i = 0 Then Set axisSeg = seg
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set f = swFeat.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        True, True, True)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "FeatureRevolve2 failed at stage " & stage & "."

    vRun = vRun + dv
    CheckPiece stage, bodies

End Sub


' The unit vector along a + b: the normal of the mitre plane between a
' pipe running along a and one running on along b.
Private Sub BisectorOf(a() As Double, b() As Double, m() As Double)
    Dim k As Long, l As Double
    For k = 0 To 2
        m(k) = a(k) + b(k)
    Next k
    l = Sqr(m(0) * m(0) + m(1) * m(1) + m(2) * m(2))
    For k = 0 To 2
        m(k) = m(k) / l
    Next k
End Sub


' Cut number c of a piece: the joint's node and the unit direction, from
' the node, towards the side of its plane the piece keeps (side x the
' plane's normal).
Private Sub PutJointCut(cuts() As Double, ByVal c As Long, node() As Double, m() As Double, ByVal side As Double)
    Dim k As Long
    For k = 0 To 2
        cuts(6 * c + k) = node(k)
        cuts(6 * c + 3 + k) = side * m(k)
    Next k
End Sub


' A straight pipe from p0 to p1 (both in plane pl) as a body of its own,
' not merged with anything: a rectangle from the axis out in the plane,
' revolved a full turn about the axis edge. inX: the plane is x = const
' (the radial direction is then in y, z), otherwise y = const.
Private Function PipeFeature(pl As SldWorks.Feature, ByVal usg As Double, ByVal vsg As Double, _
                             ByVal inX As Boolean, p0() As Double, p1() As Double, _
                             ByVal rr As Double, ByVal stage As String) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim axisSeg As SldWorks.SketchSegment
    Dim seg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim px(3) As Double, py(3) As Double, pz(3) As Double
    Dim dx As Double, dy As Double, dz As Double, l As Double
    Dim nx As Double, ny As Double, nz As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim i As Long, j As Long

    dx = p1(0) - p0(0): dy = p1(1) - p0(1): dz = p1(2) - p0(2)
    l = Sqr(dx * dx + dy * dy + dz * dz)
    dx = dx / l: dy = dy / l: dz = dz / l
    If inX Then
        nx = 0#: ny = -dz: nz = dy
    Else
        nx = -dz: ny = 0#: nz = dx
    End If

    uSign = usg: vSign = vsg
    px(0) = p0(0): py(0) = p0(1): pz(0) = p0(2)
    px(1) = p1(0): py(1) = p1(1): pz(1) = p1(2)
    px(2) = p1(0) + rr * nx: py(2) = p1(1) + rr * ny: pz(2) = p1(2) + rr * nz
    px(3) = p0(0) + rr * nx: py(3) = p0(1) + rr * ny: pz(3) = p0(2) + rr * nz

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, px(i), py(i), pz(i), u0, v0
        G2S sk, px(j), py(j), pz(j), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed at stage " & stage & "."
        If i = 0 Then Set axisSeg = seg
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set f = swFeat.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "FeatureRevolve2 failed at stage " & stage & "."
    Set PipeFeature = f

End Function


' The body a revolve feature made, read fresh from the feature.
Private Function BodyOfFeature(f As SldWorks.Feature, ByVal stage As String) As SldWorks.Body2
    Dim fc As Variant
    Dim fa As SldWorks.Face2
    fc = f.GetFaces
    If IsEmpty(fc) Then Fail "stage " & stage & ": the pipe feature has no faces."
    Set fa = fc(0)
    Set BodyOfFeature = fa.GetBody
End Function


' A pipe with mitred ends, joined to the part. The pipe runs on past
' each joint (p0, p1 are its extended ends); each of the nc cuts is a
' joint's plane (node, direction to the kept side), made as a fat pipe
' of its own whose start disc lies on the plane and whose bulk is on the
' kept side. The pipe is intersected with them (Combine, Common): a
' cylinder with its ends cut by the planes. Then all bodies are added
' together. dv is the volume the part gains.
Private Sub MitrePiece(pl As SldWorks.Feature, ByVal usg As Double, ByVal vsg As Double, _
                       ByVal inX As Boolean, p0() As Double, p1() As Double, ByVal rr As Double, _
                       cuts() As Double, ByVal nc As Long, ByVal dv As Double, ByVal stage As String)

    Dim fs() As SldWorks.Feature
    Dim tools() As Object, rest() As Object
    Dim c As Long, k As Long
    Dim big As Double, l As Double
    Dim a(2) As Double, b(2) As Double
    Dim f As SldWorks.Feature

    ReDim fs(nc)
    Set fs(0) = PipeFeature(pl, usg, vsg, inX, p0, p1, rr, stage)

    l = Sqr((p1(0) - p0(0)) ^ 2 + (p1(1) - p0(1)) ^ 2 + (p1(2) - p0(2)) ^ 2)
    big = 3# * (l + 2# * rr)
    For c = 0 To nc - 1
        For k = 0 To 2
            a(k) = cuts(6 * c + k)
            b(k) = cuts(6 * c + k) + big * cuts(6 * c + 3 + k)
        Next k
        Set fs(c + 1) = PipeFeature(pl, usg, vsg, inX, a, b, big, stage & " cutter")
    Next c

    If nc > 0 Then
        ReDim tools(nc)
        For c = 0 To nc
            Set tools(c) = BodyOfFeature(fs(c), stage)
        Next c
        Set f = swFeat.InsertCombineFeature(SWBODYINTERSECT, Nothing, tools)
        If f Is Nothing Then
            ReDim rest(nc - 1)
            For c = 1 To nc
                Set tools(c) = BodyOfFeature(fs(c), stage)
                Set rest(c - 1) = tools(c)
            Next c
            Set tools(0) = BodyOfFeature(fs(0), stage)
            Set f = swFeat.InsertCombineFeature(SWBODYINTERSECT, tools(0), rest)
        End If
        If f Is Nothing Then Fail "stage " & stage & ": the pipe could not be cut by its joint planes."
    End If

    JoinBodies stage
    vRun = vRun + dv
    CheckPiece stage, 1

End Sub


' Add every solid body of the part into one.
Private Sub JoinBodies(ByVal stage As String)
    Dim bodies As Variant
    Dim tools() As Object, rest() As Object
    Dim i As Long
    Dim f As SldWorks.Feature
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "stage " & stage & ": the part has no solid body."
    If UBound(bodies) = 0 Then Exit Sub
    ReDim tools(UBound(bodies))
    For i = 0 To UBound(bodies)
        Set tools(i) = bodies(i)
    Next i
    Set f = swFeat.InsertCombineFeature(SWBODYADD, Nothing, tools)
    If f Is Nothing Then
        ReDim rest(UBound(bodies) - 1)
        For i = 1 To UBound(bodies)
            Set rest(i - 1) = bodies(i)
        Next i
        Set f = swFeat.InsertCombineFeature(SWBODYADD, bodies(0), rest)
    End If
    If f Is Nothing Then Fail "stage " & stage & ": the bodies could not be added together."
End Sub


' The part's volume and body count as they should be after a piece of
' the gooseneck (the arms are bodies of their own until the straight
' piece joins them to the neck).
Private Sub CheckPiece(ByVal stage As String, ByVal bodies As Long)
    Dim got As Double
    got = BodiesVolume()
    Note "stage " & stage & ": " & Fmt(got) & " m3 (expected " & Fmt(vRun) & "), " & BodyCount() & " bodies"
    If BodyCount() <> bodies Then
        Fail "stage " & stage & " left " & BodyCount() & " solid bodies, expected " & bodies & ". A boolean did not merge."
    End If
    If Abs(got - vRun) > VOL_TOL * vRun Then
        Fail "stage " & stage & " volume is " & Fmt(got) & " m3 but should be " & Fmt(vRun) & _
             " m3 (" & Fmt(100# * (got - vRun) / vRun) & " %)."
    End If
End Sub


' A stage of the build with its closed-form volume and one body.
Private Sub CheckStageVol(ByVal stage As String, ByVal expected As Double)
    Dim got As Double
    Dim mp As Variant
    mp = TheBody(stage).GetMassProperties(1000#)
    got = mp(3)
    Note "stage " & stage & ": " & Fmt(got) & " m3 (expected " & Fmt(expected) & ")"
    If Abs(got - expected) > VOL_TOL * expected Then
        Fail "stage " & stage & " volume is " & Fmt(got) & " m3 but should be " & _
             Fmt(expected) & " m3 (" & Fmt(100# * (got - expected) / expected) & " %)."
    End If
    vRun = expected
End Sub


' One meal or fuel pipe. It lies in the vertical plane through the
' vessel axis along model axis ax (0 = x, the meal pipes, drawn on the
' y = 0 plane; 1 = y, the fuel pipes, on the x = 0 plane), on side +1
' or -1 of it, and is drawn in "radial" rho along that axis and z.
'
' The pipe's half-section -- a rectangle from its axis out to r along
' the section's "up" w = (-s, c) in (rho, z) -- revolved a full turn
' about the axis edge. It starts at rho0, one pipe diameter inside the
' wall, so its start disc is inside the vessel and dissolves in the
' merge, and runs out through the wall to its end face. A full turn
' has no direction to get wrong; the end face, found where it has to
' be, says which side it landed on.
'
' What it adds is a cubic metre or less of ~1890, under VOL_TOL on
' the whole body, so it is checked on its own: the volume ADDED, and
' the end face found with the pipe's area.
Private Sub AddPipe(pl As SldWorks.Feature, ByVal ax As Long, ByVal side As Double, _
                    ByVal rp As Double, ByVal c As Double, ByVal s As Double, _
                    ByVal rho0 As Double, ByVal z0 As Double, ByVal l As Double, _
                    ByVal rhoEnd As Double, ByVal zEnd As Double, ByVal expected As Double, _
                    ByVal what As String, ByVal stage As String)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim pr(3) As Double, pz(3) As Double
    Dim gx As Double, gy As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim seg As SldWorks.SketchSegment
    Dim before As Double, added As Double
    Dim face As SldWorks.Face2
    Dim i As Long, j As Long

    If ax = 0 Then
        uSign = uSignY: vSign = vSignY
    Else
        uSign = uSignX: vSign = vSignX
    End If
    before = BodiesVolume()

    pr(0) = rho0:                pz(0) = z0                 ' start, on the axis
    pr(1) = rho0 + l * c:        pz(1) = z0 + l * s         ' end, on the axis
    pr(2) = pr(1) - rp * s:      pz(2) = pz(1) + rp * c      ' end, r up
    pr(3) = pr(0) - rp * s:      pz(3) = pz(0) + rp * c      ' start, r up

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        RadialToModel ax, side * pr(i), gx, gy
        G2S sk, gx, gy, pz(i), u0, v0
        RadialToModel ax, side * pr(j), gx, gy
        G2S sk, gx, gy, pz(j), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed at stage " & stage & "."
        If i = 0 Then Set axisSeg = seg          ' start -> end, the pipe's axis
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set f = swFeat.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        True, True, True)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "FeatureRevolve2 failed at stage " & stage & "."

    added = BodiesVolume() - before
    Note "stage " & stage & ": added " & Fmt(added) & " m3 (expected " & Fmt(expected) & ")"
    If Abs(added - expected) > FEED_VOL_TOL * expected + ADD_NOISE * BodiesVolume() Then
        Fail "stage " & stage & " added " & Fmt(added) & " m3 but should add " & Fmt(expected) & _
             " m3 (" & Fmt(100# * (added - expected) / expected) & " %)."
    End If

    Set face = PipeEndFace(Nothing, ax, side, c, s, rhoEnd, zEnd)
    If face Is Nothing Then
        Fail "stage " & stage & ": no end face normal to the pipe at radial " & _
             Fmt(side * rhoEnd) & ", z " & Fmt(zEnd) & "."
    End If
    CheckArea what & " end", face.GetArea, PI * rp * rp

End Sub


Private Function ArcSin(ByVal x As Double) As Double
    ArcSin = Atn(x / Sqr(1# - x * x))
End Function


' One meal inlet at side +1 (+x) or -1 (-x): the dispersion box and its vertical pipe,
' united with the body. The box: the wedge section (rho, z) on planeY0 -- the open face's
' bottom (boxRin, boxZ0), the tangent plane (R, boxZ0), the back face's foot (boxRout, boxZFoot),
' its top (boxRout, boxZ1), the top's start (boxRin, boxZ1) -- extruded mid-plane by boxW, so there is no direction
' to get wrong. The pipe: a circle of radius rFeed at (side * boxRp, 0) on planePipe,
' extruded mid-plane by pipeLen (it starts 0.1 m inside the box so the two merge on
' volume, not on a shared face). planePipe was made while the part was empty, its sketch
' axes measured then (uPipeZ, vPipeZ). The two together add vFeed outside the vessel;
' the pipe's top face is the meal_feed, checked by its area.
Private Sub AddMealBox(planeBox As SldWorks.Feature, planePipe As SldWorks.Feature, _
                       ByVal uPipeZ As Double, ByVal vPipeZ As Double, _
                       ByVal side As Double, ByVal expected As Double, ByVal stage As String)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim cr(4) As Double, cz(4) As Double
    Dim u(4) As Double, w(4) As Double
    Dim u0 As Double, w0 As Double, gx As Double, gy As Double
    Dim nP As Long
    Dim before As Double, added As Double
    Dim face As SldWorks.Face2
    Dim i As Long, j As Long

    before = BodiesVolume()

    ' --- the wedge
    ' the floor level from the chord plane to the tangent plane, the ramp up to the back face's
    ' foot, the back face up to the top if it has one, the top back to the chord plane
    cr(0) = boxRin:  cz(0) = boxZ0
    cr(1) = R:       cz(1) = boxZ0
    cr(2) = boxRout: cz(2) = boxZFoot
    If boxBackH > 0.0001 Then
        cr(3) = boxRout: cz(3) = boxZ1
        cr(4) = boxRin:  cz(4) = boxZ1
        nP = 5
    Else
        cr(3) = boxRin:  cz(3) = boxZ1
        nP = 4
    End If
    uSign = uSignY: vSign = vSignY
    swModel.ClearSelection2 True
    planeBox.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the box sketch for stage " & stage & "."
    wRefSet = False
    For i = 0 To nP - 1
        RadialToModel 0, side * cr(i), gx, gy
        G2S sk, gx, gy, cz(i), u(i), w(i)
    Next i
    For i = 0 To nP - 1
        j = (i + 1) Mod nP
        If swSkMgr.CreateLine(u(i), w(i), 0#, u(j), w(j), 0#) Is Nothing Then _
            Fail "CreateLine (box) failed at stage " & stage & "."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")
    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondMidPlane, swEndCondBlind, _
        boxW, 0.01, _
        False, False, False, False, _
        0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "the dispersion box could not be extruded at stage " & stage & "."

    ' --- the pipe
    uSign = uPipeZ: vSign = vPipeZ
    swModel.ClearSelection2 True
    planePipe.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the pipe sketch for stage " & stage & "."
    wRefSet = False
    G2S sk, side * boxRp, 0#, pipeMidZ, u0, w0
    If swSkMgr.CreateCircleByRadius(u0, w0, 0#, rFeed) Is Nothing Then _
        Fail "CreateCircleByRadius (meal pipe) failed at stage " & stage & "."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")
    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondMidPlane, swEndCondBlind, _
        pipeLen, 0.01, _
        False, False, False, False, _
        0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "the meal pipe could not be extruded at stage " & stage & "."

    added = BodiesVolume() - before
    Note "stage " & stage & ": added " & Fmt(added) & " m3 (expected " & Fmt(expected) & ")"
    If BodyCount() <> 1 Then Fail "stage " & stage & " left " & BodyCount() & " solid bodies, expected 1."
    If Abs(added - expected) > FEED_VOL_TOL * expected + ADD_NOISE * BodiesVolume() Then
        Fail "stage " & stage & " added " & Fmt(added) & " m3 but should add " & Fmt(expected) & _
             " m3 (" & Fmt(100# * (added - expected) / expected) & " %)."
    End If

    Set face = PipeEndFace(Nothing, 0, side, 0#, 1#, boxRp, zPipeTop)
    If face Is Nothing Then
        Fail "stage " & stage & ": no meal pipe top face at radial " & Fmt(side * boxRp) & ", z " & Fmt(zPipeTop) & "."
    End If
    CheckArea "meal pipe top", face.GetArea, PI * rFeed * rFeed

End Sub


' A point at radial rho along model axis ax (0 = x, 1 = y), in model x, y.
Private Sub RadialToModel(ByVal ax As Long, ByVal rho As Double, ByRef gx As Double, ByRef gy As Double)
    If ax = 0 Then
        gx = rho: gy = 0#
    Else
        gx = 0#: gy = rho
    End If
End Sub


' A pipe's end face: the plane face normal to its axis -- side * c
' along model axis ax, s along z -- through its end centre, and on its
' side of the vessel. A plane's root point can lie anywhere on it, so
' the side is read off the face's box, not the plane: the +x and -x
' pipes' end planes both cross x = 0, and a root point there passes
' the through-the-centre test for either. Given a face, says whether
' it is that one (returns it or Nothing); given none, searches the
' body.
Private Function PipeEndFace(ByVal cand As SldWorks.Face2, ByVal ax As Long, ByVal side As Double, _
                             ByVal c As Double, ByVal s As Double, _
                             ByVal rhoEnd As Double, ByVal zEnd As Double) As SldWorks.Face2

    Dim faces As Variant
    Dim face As SldWorks.Face2
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim other As Long
    Dim i As Long, n As Long

    other = 1 - ax
    If cand Is Nothing Then
        faces = TheBody("pipe end face").GetFaces
        n = UBound(faces)
    Else
        n = 0
    End If
    For i = 0 To n
        If cand Is Nothing Then Set face = faces(i) Else Set face = cand
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(p(other)) < DIR_TOL And Abs(Abs(p(ax) * side * c + p(2) * s) - 1#) < DIR_TOL Then
                If Abs((p(3 + ax) - side * rhoEnd) * side * c + (p(5) - zEnd) * s) < 0.0001 And _
                   FaceCentre(face, ax) * side > 0# Then
                    Set PipeEndFace = face
                    Exit Function
                End If
            End If
        End If
    Next i

End Function


' The middle of a face's box along model axis ax (0 = x, 1 = y, 2 = z).
Private Function FaceCentre(face As SldWorks.Face2, ByVal ax As Long) As Double
    Dim b As Variant
    b = face.GetBox
    FaceCentre = 0.5 * (b(ax) + b(ax + 3))
End Function


' The tertiary air duct: a circle of radius rTA about (xTA, 0, zTA) on
' the y = 0 plane, extruded blind out to y = yTAEnd (< 0; the duct comes
' in from -y, parallel to the kiln: user 24 Nov 2026). Which way a blind
' extrusion goes is not ours to choose, and the vessel is symmetric in
' y, so the volume cannot tell the two apart: the face at yTAEnd says
' which way it went, and the other way is tried.
Private Sub AddTertiaryAir(planeY0 As SldWorks.Feature, ByVal stage As String)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim u0 As Double, v0 As Double
    Dim f As SldWorks.Feature
    Dim before As Double, added As Double
    Dim k As Long

    uSign = uSignY: vSign = vSignY
    before = BodiesVolume()

    swModel.ClearSelection2 True
    planeY0.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False
    G2S sk, xTA, 0#, zTA, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rTA) Is Nothing Then
        Fail "CreateCircleByRadius failed at stage " & stage & "."
    End If
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            -yTAEnd, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            added = BodiesVolume() - before
            If BodyCount() = 1 And Abs(added - vTA) <= FEED_VOL_TOL * vTA And HasPlaneFace(1, yTAEnd) Then
                Note "stage " & stage & ": added " & Fmt(added) & " m3 (expected " & Fmt(vTA) & ")"
                Exit Sub
            End If
            Note "stage " & stage & " extruded the wrong way (" & BodyCount() & " bodies, added " & _
                 Fmt(added) & " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "stage " & stage & " could not be extruded out to y = " & Fmt(yTAEnd) & " m adding " & _
         Fmt(vTA) & " m3 in either direction."

End Sub


' Integral over a pipe's section of the vessel's half chord: the disc
' of radius r centred at c across the section,
'   2 int sqrt(r^2 - (a - c)^2) sqrt(R^2 - a^2) da.
' Elliptic, so evaluated: with a = c + r sin(phi) the integrand is
' smooth and Simpson's rule on 400 panels is exact to rounding
' (geometry/plant_geometry.py chord_integral, the same).
Private Function ChordIntegral(ByVal rp As Double, ByVal cp As Double) As Double

    Const n As Long = 400
    Dim h As Double, phi As Double, a As Double, g As Double, w As Double, sum As Double
    Dim k As Long

    h = PI / n
    For k = 0 To n
        phi = -0.5 * PI + k * h
        a = cp + rp * Sin(phi)
        g = 2# * rp * rp * Cos(phi) ^ 2 * Sqr(R * R - a * a)
        If k = 0 Or k = n Then
            w = 1#
        ElseIf (k Mod 2) = 1 Then
            w = 4#
        Else
            w = 2#
        End If
        sum = sum + w * g
    Next k
    ChordIntegral = sum * h / 3#

End Function


Private Sub CheckArea(ByVal what As String, ByVal got As Double, ByVal expected As Double)
    If Abs(got - expected) > AREA_TOL * expected Then
        Fail "the " & what & " face is " & Fmt(got) & " m2 but should be " & Fmt(expected) & " m2."
    End If
End Sub


Private Function BodyCount() As Long

    Dim bodies As Variant

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    BodyCount = UBound(bodies) + 1

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
' Sketch plane mapping -- copied from cyclone.bas, where the reasons
' are written out in full. In short: every point is given in MODEL
' coordinates and put through the plane's own transform; the
' off-plane component is compared against the FIRST point of the
' same sketch, never against zero, because ModelToSketchTransform's
' translation does not run the way its name promises; and which way
' a plane's sketch axes run is measured with a test block, not read.
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


' Which way round a sketch plane's axes actually run, measured: a
' 1 m x 2 m rectangle of known model coordinates, off the origin, is
' drawn, extruded and its bounding box read back for each of the four
' sign combinations. The probe is removed before anything real is
' built.
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
            ' run; the third says where the plane itself is.
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
' on it. An empty sketch is discarded on exit.
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
' The kiln gas inlet and the roof are the two planes the profile
' was drawn to end on; both have to be there.
Private Sub Verify()

    Dim body As SldWorks.Body2
    Dim edges As Variant
    Dim edge As SldWorks.Edge
    Dim adj As Variant
    Dim i As Long

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

    If Not HasPlaneFace(2, 0#) Then Fail "no kiln gas inlet face at z = 0."
    If Not HasPlaneFace(2, zRoof) Then Fail "no roof face at z = " & Fmt(zRoof) & " m."
    If Not HasPlaneFace(1, yTAEnd) Then Fail "no tertiary air inlet face at y = " & Fmt(yTAEnd) & " m."

    Note "closed manifold solid: " & (UBound(edges) + 1) & " edges, each with two faces"
    CheckExtremes body

End Sub


' The domain's true extent from its extreme points (GetBodyBox bounds
' curved faces loosely): the arms' outer walls (or the tertiary air
' duct's face) in x, the neck's front wall and the fuel pipes in y, the
' arch's crown in z.
Private Sub CheckExtremes(body As SldWorks.Body2)
    Dim b(5) As Double, d(2) As Double, want(5) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    want(0) = -xBoxMax: want(1) = yBoxMin: want(2) = 0#
    want(3) = xBoxMax
    If yTAEnd < want(1) Then want(1) = yTAEnd                        ' the tertiary air duct's face may reach further
    want(4) = yFuelMax: want(5) = zGnApex
    For a = 0 To 5
        If Abs(b(a) - want(a)) > 0.01 Then
            Fail "the solid's " & nm(a) & " is " & Fmt(b(a)) & " m but should be " & Fmt(want(a)) & " m."
        End If
    Next a
    Note "extent: x " & Fmt(b(0)) & " .. " & Fmt(b(3)) & ", y " & Fmt(b(1)) & " .. " & Fmt(b(4)) & _
         ", z " & Fmt(b(2)) & " .. " & Fmt(b(5)) & " m"
End Sub


'==================================================================
' (g) Boundary faces.
'
' Face names are regenerated by every boolean, so the boundaries are
' found by what they ARE: a plane, its normal and a point on it, read
' analytically off the surface. Each gets its own colour; AP214
' carries face colours and Fluent Meshing makes a zone of each, to be
' named as the log lists them. Everything else is wall.
'==================================================================
Private Sub TagBoundaryFaces()

    Dim body As SldWorks.Body2
    Dim faces As Variant
    Dim face As SldWorks.Face2
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim i As Long, k As Long
    Dim n(8) As Long, a(8) As Double
    Dim names As Variant, want As Variant
    Dim e0 As Double, e1 As Double, e2 As Double

    ' 0 kiln_gas_inlet, 1 / 2 gas_outlet_1 (+x) / _2 (-x), 3 tertiary_air_inlet,
    ' 4 / 5 meal_feed_1 (+x) / _2 (-x), 6 / 7 fuel_inlet_1 (+y) / _2 (-y), 8 wall
    names = Array("kiln_gas_inlet", "gas_outlet_1", "gas_outlet_2", "tertiary_air_inlet", _
                  "meal_feed_1", "meal_feed_2", "fuel_inlet_1", "fuel_inlet_2", "wall")

    Set body = TheBody("final")
    faces = body.GetFaces

    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        k = 8
        If surf.IsPlane Then
            p = surf.PlaneParams
            e0 = p(0): e1 = p(1): e2 = p(2)
            If Abs(e0) < DIR_TOL And Abs(e1) < DIR_TOL Then
                If Abs(p(5)) < 0.0001 Then
                    k = 0
                ElseIf Not PipeEndFace(face, 0, 1#, 0#, 1#, xFeedEnd, zFeedEnd) Is Nothing Then
                    k = 4                       ' the meal pipes' top faces face up
                ElseIf Not PipeEndFace(face, 0, -1#, 0#, 1#, xFeedEnd, zFeedEnd) Is Nothing Then
                    k = 5
                End If
            ElseIf Abs(e0) < DIR_TOL And Abs(e2) < DIR_TOL And Abs(p(4) - yTAEnd) < 0.0001 Then
                k = 3
            ElseIf Abs(e1) < DIR_TOL And Abs(e2) < DIR_TOL And Abs(p(3) - xGnLeg) < 0.0001 Then
                k = 1
            ElseIf Abs(e1) < DIR_TOL And Abs(e2) < DIR_TOL And Abs(p(3) + xGnLeg) < 0.0001 Then
                k = 2
            ElseIf Not PipeEndFace(face, 1, 1#, uc, us, yFuelEnd, zFuelEnd) Is Nothing Then
                k = 6
            ElseIf Not PipeEndFace(face, 1, -1#, uc, us, yFuelEnd, zFuelEnd) Is Nothing Then
                k = 7
            End If
        End If
        PaintZone face, k
        n(k) = n(k) + 1
        a(k) = a(k) + face.GetArea
    Next i

    ' Exactly one of each. Two would mean an end cap survived a merge
    ' and blocks an opening; none, that a face merged away.
    want = Array(PI * rThroat * rThroat, PI * rGn * rGn, PI * rGn * rGn, PI * rTA * rTA, _
                 PI * rFeed * rFeed, PI * rFeed * rFeed, PI * rFuel * rFuel, PI * rFuel * rFuel)
    For k = 0 To 7
        If n(k) <> 1 Then Fail "found " & n(k) & " " & names(k) & " faces, expected 1."
        CheckArea names(k), a(k), want(k)
        Note "boundary " & names(k) & ": " & Fmt(a(k)) & " m2, colour " & ZoneColour(k)
    Next k
    Note "boundary wall: " & n(8) & " faces, " & Fmt(a(8)) & " m2"

    swModel.ClearSelection2 True

End Sub


' The colour each zone is painted, RGB 0..1. Distinct enough to tell
' apart in Fluent Meshing; the wall a neutral grey.
Private Sub ZoneRGB(ByVal k As Long, ByRef r As Double, ByRef g As Double, ByRef b As Double)
    Select Case k
    Case 0: r = 0.2: g = 0.7: b = 0.35          ' kiln_gas_inlet, green
    Case 1: r = 0.2: g = 0.45: b = 0.85         ' gas_outlet_1, blue
    Case 2: r = 0.1: g = 0.25: b = 0.55         ' gas_outlet_2, dark blue
    Case 3: r = 0.85: g = 0.25: b = 0.2         ' tertiary_air_inlet, red
    Case 4: r = 0.6: g = 0.3: b = 0.7           ' meal_feed_1, purple
    Case 5: r = 0.4: g = 0.15: b = 0.5          ' meal_feed_2, dark purple
    Case 6: r = 0.85: g = 0.55: b = 0.15        ' fuel_inlet_1, orange
    Case 7: r = 0.55: g = 0.35: b = 0.1         ' fuel_inlet_2, brown
    Case Else: r = 0.72: g = 0.72: b = 0.72     ' wall, grey
    End Select
End Sub


Private Function ZoneColour(ByVal k As Long) As String
    Dim r As Double, g As Double, b As Double
    ZoneRGB k, r, g, b
    ZoneColour = "(" & Fmt(r) & ", " & Fmt(g) & ", " & Fmt(b) & ")"
End Function


Private Sub PaintZone(face As SldWorks.Face2, ByVal k As Long)
    Dim r As Double, g As Double, b As Double
    ZoneRGB k, r, g, b
    Paint face, r, g, b
End Sub


' RGB, ambient, diffuse, specular, shininess, transparency, emission.
' Copied from cyclone.bas, where the reasons are written out: set
' through the property from a typed Double array (VBA's Array() is
' read wrongly), read back and checked, because the colours are the
' only thing carrying the boundary names into Fluent.
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
' (h) Export -- as cyclone.bas: STEP AP214 (it carries the face
'     colours), binary STL in metres not shifted into positive space,
'     and the SLDPRT.
'==================================================================
Private Sub ExportFiles()

    Dim outDir As String

    outDir = OUT_ROOT & LINE_KEY & "\"
    EnsureDir OUT_ROOT
    EnsureDir outDir

    ' Application-wide export defaults: remembered, handed back in Restore.
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

    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True

    swApp.SetUserPreferenceIntegerValue swExportStlUnits, swMETER
    swApp.SetUserPreferenceToggle swSTLBinaryFormat, True
    swApp.SetUserPreferenceToggle swSTLDontTranslateToPositive, True
    swApp.SetUserPreferenceToggle swSTLShowInfoOnSave, False
    swApp.SetUserPreferenceIntegerValue swSTLQuality, swSTLQuality_Custom
    swApp.SetUserPreferenceDoubleValue swSTLDeviation, 0.001        ' metres
    swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, 0.1     ' radians

    KeepOldSolid outDir
    SaveOne outDir & outName & ".SLDPRT"
    SaveOne outDir & outName & ".step"
    SaveOne outDir & outName & ".stl"

End Sub


' The solid this one replaces (the Y gooseneck's, the CFD results'
' geometry) is kept, once, as <name>_Y_old.<ext>.
Private Sub KeepOldSolid(ByVal outDir As String)
    Dim e As Variant
    On Error Resume Next
    For Each e In Array(".SLDPRT", ".step", ".stl")
        If Dir(outDir & outName & e) <> "" And Dir(outDir & outName & "_Y_old" & e) = "" Then
            FileCopy outDir & outName & e, outDir & outName & "_Y_old" & e
            If Err.Number = 0 Then Note "kept the earlier " & outName & e & " as " & outName & "_Y_old" & e
            Err.Clear
        End If
    Next e
End Sub


' A failed export returns without raising, so the outcome is read
' from the error code and then from the disk (cyclone.bas: SolidWorks
' 2026 writes the file and still returns False).
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
    Err.Raise vbObjectError + 1, "calciner", msg
End Sub


' The whole log, to a file: a message box shows about 1000 characters,
' and tests/test_plant_geometry.py holds the solid to
' geometry/plant_geometry.py through it. The first line is the outcome.
Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\calciner_build.log"
End Function

Private Sub WriteLog(ByVal outcome As String)
    Dim fn As Integer
    On Error Resume Next
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    fn = FreeFile
    Open LogPath() For Output As #fn
    Print #fn, outcome & vbLf & buildLog;
    Close #fn
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
End Function
