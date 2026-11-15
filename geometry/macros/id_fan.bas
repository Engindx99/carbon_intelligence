Attribute VB_Name = "id_fan"
'==================================================================
' ID fan CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' THREE closed solids, the flow path of one string's preheater ID fan
' (geometry/fan/id_fan.md): a single-inlet backward-curved centrifugal
' fan, its sizes all from geometry/plant_geometry.yaml through
' plant_geometry.id_fan():
'   rotor   the rotating (MRF) zone: the impeller's passage, a flat hub
'           (back plate) at y = 0, a straight conical shroud from the eye
'           (r1, b1) to the tip (r2, b2), a rim ring out to R_MRF; the z
'           single-arc plate blades are cut out of it, hub to shroud;
'   volute  the casing: a log spiral r = R3 exp(K theta) from the
'           tongue (its growth set by the outlet velocity), constant
'           width B (y = 0 .. B), round the rotating zone (a hole
'           R_MRF), the tongue's round nose, and a straight discharge
'           along (DIS_DX, DIS_DZ), up at the discharge angle, to the
'           outlet face normal to it;
'   inlet   the inlet box (its inlet face looks along +x) on the outside
'           of the volute's front plate (its floor at y = B1 + CONE_L,
'           past y = B), and the inlet cone from it down to the eye (y = B1).
' The bodies touch on the eye's disc (inlet | rotor) and the rim's
' cylinder (rotor | volute): the MRF interfaces. No casing plate,
' shaft, damper or bearing; leakage gaps and the disc cavities behind
' the hub and outside the shroud are not in the flow path.
'
' Coordinates: y along the fan's axis (the hub's plane y = 0, the eye
' at y = B1, the gas comes in towards -y); x horizontal, z up; the
' discharge leaves on the upper +x side heading up and to -x. The impeller turns +theta, from +x
' towards +z; the blades lean back against that.
'
' Boundary faces (coloured for Fluent): fan_inlet = the box's face at
' x = BOX_REACH (red); fan_outlet = the discharge's face, normal to
' (DIS_DX, 0, DIS_DZ) (blue); interface_eye (yellow) and interface_rim (green),
' one face on each side; blade (orange); wall = every other face (grey).
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA editor
' File -> Import File... and pick this .bas. Run `main`.
' Outputs geometry\output\2500\id_fan.SLDPRT, .step, .stl and
' id_fan_build.log (tests/test_plant_geometry.py reads the log).
'==================================================================

Option Explicit

Const FAN_NAME As String = "id_fan"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const FAN_R1                       As Double  = 0.91863      ' eye radius: the blades' leading edge, the shroud's inner rim [derived]
Const FAN_R2                       As Double  = 1.312329     ' impeller tip radius [derived]
Const FAN_B1                       As Double  = 0.459315     ' blade height at r1: hub (y = 0) to the shroud, the eye's plane [derived]
Const FAN_B2                       As Double  = 0.513935     ' blade height at r2 (the outlet width) [derived]
Const FAN_R_MRF                    As Double  = 1.410754     ' the rotating zone's rim [derived]
Const FAN_Z                        As Long    = 20           ' blade count [derived]
Const BLADE_T                      As Double  = 0.012        ' plate blade thickness [model, fan/id_fan.md]
Const BLADE_R_IN                   As Double  = 0.91963      ' the blades' inner cap: r1 + the edge clearance [derived]
Const BLADE_R_OUT                  As Double  = 1.311329     ' the blades' outer cap: r2 - the edge clearance [derived]
Const BLADE_RB                     As Double  = 4.9207       ' the blade centreline's arc radius [derived]
Const BLADE_RC                     As Double  = 4.099159     ' the arc centre's distance from the axis [derived]
Const BLADE_SENSE                  As Double  = 1#           ' +1: a point at radius r sits +phi(r) from the centre's ray (backward) [derived]
Const VOL_B                        As Double  = 1.541804     ' volute width, y = 0 (back wall, the hub's plane) to B [derived]
Const VOL_R3                       As Double  = 1.509178     ' the spiral's start radius (tongue circle) [derived]
Const VOL_K                        As Double  = 0.148493531  ' log spiral r = R3 exp(K theta), K = tan(alpha), from the outlet velocity [derived]
Const VOL_PSI0                     As Double  = 0.932814467  ' the spiral's start ray from +x towards +z [rad] [derived]
Const NOSE_R                       As Double  = 0.196849     ' the tongue's nose radius [derived]
Const DIS_DX                       As Double  = -0.707106781 ' the discharge's direction, x (-cos gamma) [derived]
Const DIS_DZ                       As Double  = 0.707106781  ' the discharge's direction, z (sin gamma) [derived]
Const VOL_S_EXIT                   As Double  = 2.471972     ' the outlet face: the plane p . (DIS_DX, 0, DIS_DZ) = this [derived]
Const CONE_R                       As Double  = 1.194219     ' the inlet cone's mouth radius (r1 at y = B1) [derived]
Const CONE_L                       As Double  = 1.132489     ' the inlet cone's length, y = B1 to the box's floor (B + the front plate) [derived]
Const BOX_H                        As Double  = 2.627283     ' the inlet box's height (z) and width behind the axis (x from -BOX_H/2) [derived]
Const BOX_DEPTH                    As Double  = 1.765886     ' the inlet box's depth along y [derived]
Const BOX_REACH                    As Double  = 2.388439     ' the box's inlet face, x [derived]
Const V_ROTOR                      As Double  = 2.997639     ' rotating zone before the blades are cut [m3] [derived]
Const V_BLADES                     As Double  = 0.077806     ' the blades' volume, hub to shroud [m3] [derived]
Const V_VOLUTE                     As Double  = 28.576001    ' volute + discharge outside the rotating zone [m3] [derived]
Const V_CONE                       As Double  = 3.993163     ' inlet cone [m3] [derived]
Const V_BOX                        As Double  = 17.175737    ' inlet box [m3] [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const SPLINE_PTS As Long = 73      ' the spiral's spline: a point every 5 deg
Const VOL_TOL  As Double = 0.001   ' relative, on the volumes
Const AREA_TOL As Double = 0.002   ' relative, on face areas
Const BOX_TOL  As Double = 0.01    ' absolute [m]
Const FACE_TOL As Double = 0.0001
Const RAD_TOL  As Double = 0.0005  ' on a cylinder's radius [m]
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001
Const PI As Double = 3.14159265358979

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean
Dim uSignY As Double, vSignY As Double      ' the plane y = 0 (the volute, the blades)
Dim uSignZ As Double, vSignZ As Double      ' the plane z = 0 (the revolve profiles)
Dim uSignB As Double, vSignB As Double      ' the plane y = yBox (the inlet box's floor)
Dim uSign As Double, vSign As Double
Dim wRef As Double
Dim wRefSet As Boolean

Dim rEnd As Double, hOut As Double, yBox As Double
Dim p0x As Double, p0z As Double            ' the spiral's start, the tongue
Dim pex As Double, pez As Double            ' the spiral's end, the discharge's outer wall
Dim ntx As Double, ntz As Double            ' the nose's far side T: the discharge's lower wall starts here
Dim e1x As Double, e1z As Double            ' the outlet face's outer corner (end of the outer wall)
Dim e2x As Double, e2z As Double            ' the outlet face's lower corner (end of the lower wall)
Dim nnx As Double, nnz As Double            ' the outward normal at the tongue, (DIS_DZ, -DIS_DX)

Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStlUnits As Long, oldStlQuality As Long
Dim oldStepAppear As Boolean, oldStlBinary As Boolean
Dim oldStlNoShift As Boolean, oldStlInfo As Boolean
Dim oldStlDev As Double, oldStlAngle As Double

Dim buildLog As String
Dim phase As String


'==================================================================
' main
'==================================================================
Sub main()

    Dim why As String

    buildLog = ""
    phase = "starting up"
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "working out the coordinates"
    Expected
    phase = "building the solids"
    Build
    phase = "verifying the solids"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog FAN_NAME & " built, verified and exported"
    MsgBox FAN_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "ID fan"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog FAN_NAME & " ABORTED while " & phase & ": " & why
    MsgBox FAN_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "ID fan"
End Sub


' The points the outline is drawn through, and what the build is held to.
Private Sub Expected()
    rEnd = VOL_R3 * Exp(2# * PI * VOL_K)
    p0x = VOL_R3 * Cos(VOL_PSI0): p0z = VOL_R3 * Sin(VOL_PSI0)
    pex = rEnd * Cos(VOL_PSI0):   pez = rEnd * Sin(VOL_PSI0)
    nnx = DIS_DZ: nnz = -DIS_DX
    ntx = p0x + 2# * NOSE_R * nnx: ntz = p0z + 2# * NOSE_R * nnz
    hOut = (pex - ntx) * nnx + (pez - ntz) * nnz
    e1x = pex + (VOL_S_EXIT - (pex * DIS_DX + pez * DIS_DZ)) * DIS_DX
    e1z = pez + (VOL_S_EXIT - (pex * DIS_DX + pez * DIS_DZ)) * DIS_DZ
    e2x = ntx + (VOL_S_EXIT - (ntx * DIS_DX + ntz * DIS_DZ)) * DIS_DX
    e2z = ntz + (VOL_S_EXIT - (ntx * DIS_DX + ntz * DIS_DZ)) * DIS_DZ
    yBox = FAN_B1 + CONE_L
    Note "impeller: D2 " & Fmt(2# * FAN_R2) & " m, D1 " & Fmt(2# * FAN_R1) & " m, b2 " & Fmt(FAN_B2) & " m, b1 " & Fmt(FAN_B1) & _
         " m, " & FAN_Z & " blades " & Fmt(BLADE_T) & " m thick (arc R " & Fmt(BLADE_RB) & " m); rotating zone to r " & Fmt(FAN_R_MRF) & " m"
    Note "volute: B " & Fmt(VOL_B) & " m, spiral r " & Fmt(VOL_R3) & " -> " & Fmt(rEnd) & " m (K " & Fmt(VOL_K) & _
         "), nose R " & Fmt(NOSE_R) & " m, outlet " & Fmt(VOL_B) & " x " & Fmt(hOut) & " m from (" & Fmt(e2x) & ", " & Fmt(e2z) & _
         ") to (" & Fmt(e1x) & ", " & Fmt(e1z) & "), discharge along (" & Fmt(DIS_DX) & ", " & Fmt(DIS_DZ) & ")"
    Note "inlet: cone r " & Fmt(FAN_R1) & " -> " & Fmt(CONE_R) & " m over " & Fmt(CONE_L) & " m, box " & Fmt(BOX_H) & " x " & _
         Fmt(BOX_DEPTH) & " m face at x " & Fmt(BOX_REACH) & ", floor y " & Fmt(yBox)
    Note "expected volumes: rotor " & Fmt(V_ROTOR - V_BLADES) & " m3 (" & Fmt(V_ROTOR) & " less blades " & Fmt(V_BLADES) & _
         "), volute " & Fmt(V_VOLUTE) & " m3, inlet " & Fmt(V_CONE + V_BOX) & " m3 (cone " & Fmt(V_CONE) & " + box " & Fmt(V_BOX) & ")"
End Sub


'==================================================================
' Build
'==================================================================
Private Sub Build()
    Dim planeY As SldWorks.Feature, planeZ As SldWorks.Feature, planeB As SldWorks.Feature

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    oldVerify = swApp.GetUserPreferenceToggle(swPerformanceVerifyOnRebuild)
    oldInputDim = swApp.GetUserPreferenceToggle(swInputDimValOnCreate)
    swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, True
    swApp.SetUserPreferenceToggle swInputDimValOnCreate, False
    prefsTouched = True

    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    ' every plane is measured on the EMPTY part (the calibration probe
    ' only works on one), then the bodies are built
    Set planeY = FindPlaneWithNormal(0#, 1#, 0#)
    If planeY Is Nothing Then Fail "could not find the default plane whose normal is Y."
    CalibrateSketchAxes planeY, 0#, 0#, 0#, uSignY, vSignY
    Set planeZ = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ Is Nothing Then Fail "could not find the default plane whose normal is Z."
    CalibrateSketchAxes planeZ, 0#, 0#, 0#, uSignZ, vSignZ
    Set planeB = OffsetPlane(planeY, 0#, yBox, 0#, uSignB, vSignB)

    ' the rotor first and alone, so the blades' through-all cut can only
    ' reach it; then the others, kept apart from it (no merge)
    BuildRotor planeZ
    CutBlades planeY
    BuildVolute planeY
    BuildCone planeZ
    BuildBox planeB
    NameBodies
End Sub


' The rotating zone: the (r, y) profile revolved round the y axis.
Private Sub BuildRotor(pl As SldWorks.Feature)
    Dim px(5) As Double, py(5) As Double, got As Double
    px(0) = 0#:        py(0) = 0#
    px(1) = FAN_R_MRF: py(1) = 0#
    px(2) = FAN_R_MRF: py(2) = FAN_B2
    px(3) = FAN_R2:    py(3) = FAN_B2
    px(4) = FAN_R1:    py(4) = FAN_B1           ' the shroud: a straight cone from the tip to the eye
    px(5) = 0#:        py(5) = FAN_B1
    RevolveOnZ pl, px, py, 6, True, "rotating zone"
    If BodyCount() <> 1 Then Fail "the rotating zone made " & BodyCount() & " bodies, not one."
    got = Volume(BodyOf("rotor"))
    If Abs(got - V_ROTOR) > VOL_TOL * V_ROTOR Then Fail "the rotating zone is " & Fmt(got) & " m3, expected " & Fmt(V_ROTOR) & " m3."
    Note "rotating zone revolved: " & Fmt(got) & " m3 (expected " & Fmt(V_ROTOR) & ")"
End Sub


' The blades: each the strip between two arcs about its centre (radius
' BLADE_RB -+ BLADE_T / 2), from BLADE_R_IN to BLADE_R_OUT (a millimetre
' inside the eye's and the tip's circles, so the straight caps never
' notch those edges into sliver faces), closed by two straight caps; all FAN_Z in one sketch on y = 0, cut through
' all both ways (only the rotor is there to cut).
Private Sub CutBlades(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim i As Long, s As Long, rr As Double, g As Double, rm As Double
    Dim ax(1, 2) As Double, az(1, 2) As Double      ' (side, r1 / rm / r2)
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double, u2 As Double, v2 As Double
    Dim got As Double, want As Double

    rm = 0.5 * (BLADE_R_IN + BLADE_R_OUT)
    uSign = uSignY: vSign = vSignY
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the blades' sketch on the y = 0 plane."
    wRefSet = False
    For i = 0 To FAN_Z - 1
        g = 2# * PI * i / FAN_Z
        For s = 0 To 1
            rr = BLADE_RB + (2 * s - 1) * 0.5 * BLADE_T
            ArcPoint g, rr, BLADE_R_IN, ax(s, 0), az(s, 0)
            ArcPoint g, rr, rm, ax(s, 1), az(s, 1)
            ArcPoint g, rr, BLADE_R_OUT, ax(s, 2), az(s, 2)
            G2S sk, ax(s, 0), 0#, az(s, 0), u0, v0
            G2S sk, ax(s, 2), 0#, az(s, 2), u1, v1
            G2S sk, ax(s, 1), 0#, az(s, 1), u2, v2
            If swSkMgr.Create3PointArc(u0, v0, 0#, u1, v1, 0#, u2, v2, 0#) Is Nothing Then _
                Fail "Create3PointArc failed on blade " & i & "."
        Next s
        For s = 0 To 2 Step 2                           ' the caps at r1 and r2
            G2S sk, ax(0, s), 0#, az(0, s), u0, v0
            G2S sk, ax(1, s), 0#, az(1, s), u1, v1
            If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on blade " & i & "'s cap."
        Next s
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureCut4( _
        False, False, False, _
        swEndCondThroughAll, swEndCondThroughAll, 0.01, 0.01, _
        False, False, False, False, 0#, 0#, _
        False, False, False, False, _
        False, True, True, True, True, False, _
        swStartSketchPlane, 0#, False, False)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "the blades could not be cut out of the rotating zone."
    If BodyCount() <> 1 Then Fail "cutting the blades left " & BodyCount() & " bodies, not one."
    got = Volume(BodyOf("rotor"))
    want = V_ROTOR - V_BLADES
    If Abs(got - want) > VOL_TOL * want Then Fail "the bladed rotating zone is " & Fmt(got) & " m3, expected " & Fmt(want) & " m3."
    Note FAN_Z & " blades cut: rotating zone " & Fmt(got) & " m3 (expected " & Fmt(want) & ")"
End Sub


' The point at radius r on the circle of radius rr about blade g's
' centre (BLADE_RC on the ray g): phi off the centre's ray by the law of
' cosines, on BLADE_SENSE's side.
Private Sub ArcPoint(ByVal g As Double, ByVal rr As Double, ByVal r As Double, ByRef x As Double, ByRef z As Double)
    Dim c As Double, a As Double
    c = (BLADE_RC * BLADE_RC + r * r - rr * rr) / (2# * BLADE_RC * r)
    If Abs(c) >= 1# Then Fail "a blade arc of radius " & Fmt(rr) & " m does not reach r = " & Fmt(r) & " m."
    a = g + BLADE_SENSE * ACos(c)
    x = r * Cos(a): z = r * Sin(a)
End Sub


Private Function ACos(ByVal c As Double) As Double
    ACos = Atn(-c / Sqr(1# - c * c)) + 0.5 * PI
End Function


' The volute's outline on y = 0, going round it:
'   P0 (the tongue)  the spiral, a spline, +theta round to
'   PE (its end)     the discharge's outer wall along d to
'   E1               across the outlet face (normal to d) to
'   E2               the lower wall back along -d to
'   T                the nose's far side; the nose, a half circle
'                    round its -d side, back to P0.
' The rotating zone's circle R_MRF is a hole. Extruded B along +y,
' a body of its own (no merge with the rotor it touches).
Private Sub BuildVolute(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim pd() As Double, th As Double, rr As Double
    Dim gx(3) As Double, gz(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double, u2 As Double, v2 As Double
    Dim i As Long, k As Long, got As Double, bx As Variant
    Dim body As SldWorks.Body2

    uSign = uSignY: vSign = vSignY
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the volute's sketch on the y = 0 plane."
    wRefSet = False

    ReDim pd(3 * SPLINE_PTS - 1)
    For k = 0 To SPLINE_PTS - 1
        If k = 0 Then
            G2S sk, p0x, 0#, p0z, u0, v0
        ElseIf k = SPLINE_PTS - 1 Then
            G2S sk, pex, 0#, pez, u0, v0
        Else
            th = 2# * PI * k / (SPLINE_PTS - 1)
            rr = VOL_R3 * Exp(VOL_K * th)
            G2S sk, rr * Cos(VOL_PSI0 + th), 0#, rr * Sin(VOL_PSI0 + th), u0, v0
        End If
        pd(3 * k) = u0: pd(3 * k + 1) = v0: pd(3 * k + 2) = 0#
    Next k
    If swSkMgr.CreateSpline2((pd), False) Is Nothing Then Fail "CreateSpline2 failed on the volute's spiral."

    gx(0) = pex: gz(0) = pez
    gx(1) = e1x: gz(1) = e1z
    gx(2) = e2x: gz(2) = e2z
    gx(3) = ntx: gz(3) = ntz
    For i = 0 To 2
        G2S sk, gx(i), 0#, gz(i), u0, v0
        G2S sk, gx(i + 1), 0#, gz(i + 1), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the discharge."
    Next i
    G2S sk, ntx, 0#, ntz, u0, v0
    G2S sk, p0x, 0#, p0z, u1, v1
    G2S sk, p0x + NOSE_R * (nnx - DIS_DX), 0#, p0z + NOSE_R * (nnz - DIS_DZ), u2, v2
    If swSkMgr.Create3PointArc(u0, v0, 0#, u1, v1, 0#, u2, v2, 0#) Is Nothing Then Fail "Create3PointArc failed on the tongue's nose."
    G2S sk, 0#, 0#, 0#, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, FAN_R_MRF) Is Nothing Then Fail "CreateCircleByRadius failed on the rotating zone's hole."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, VOL_B, 0.01, _
            False, False, False, False, 0#, 0#, _
            False, False, False, False, _
            False, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            If BodyCount() = 2 Then
                Set body = BodyOf("volute")
                bx = body.GetBodyBox
                If Abs(bx(1)) < BOX_TOL And Abs(bx(4) - VOL_B) < BOX_TOL Then
                    got = Volume(body)
                    If Abs(got - V_VOLUTE) > VOL_TOL * V_VOLUTE Then Fail "the volute is " & Fmt(got) & " m3, expected " & Fmt(V_VOLUTE) & " m3."
                    Note "volute extruded " & IIf(k = 0, "forward", "reversed") & ": " & Fmt(got) & " m3 (expected " & Fmt(V_VOLUTE) & ")"
                    Exit Sub
                End If
                Note "the volute extruded the wrong way (y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & "); reversing"
            Else
                Note "the volute left " & BodyCount() & " bodies, not two"
            End If
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k
    Fail "the volute could not be extruded from y = 0 to y = " & Fmt(VOL_B) & " m in either direction."
End Sub


' The inlet cone: from the eye (r1, y = B1) out to its mouth at the box's floor.
Private Sub BuildCone(pl As SldWorks.Feature)
    Dim px(3) As Double, py(3) As Double, got As Double
    px(0) = 0#:     py(0) = FAN_B1
    px(1) = FAN_R1: py(1) = FAN_B1
    px(2) = CONE_R: py(2) = yBox
    px(3) = 0#:     py(3) = yBox
    RevolveOnZ pl, px, py, 4, False, "inlet cone"
    If BodyCount() <> 3 Then Fail "the inlet cone left " & BodyCount() & " bodies, not three (it must not merge with the rotor)."
    got = Volume(BodyOf("inlet"))
    If Abs(got - V_CONE) > VOL_TOL * V_CONE Then Fail "the inlet cone is " & Fmt(got) & " m3, expected " & Fmt(V_CONE) & " m3."
    Note "inlet cone revolved: " & Fmt(got) & " m3 (expected " & Fmt(V_CONE) & ")"
End Sub


' The inlet box on the cone's mouth: x from -BOX_H / 2 to its face at
' BOX_REACH, z -+ BOX_H / 2, y from the floor up BOX_DEPTH; merged
' with the cone (the only body it touches).
Private Sub BuildBox(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim gx(3) As Double, gz(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim i As Long, k As Long, got As Double, want As Double, bx As Variant
    Dim body As SldWorks.Body2

    gx(0) = -0.5 * BOX_H: gz(0) = -0.5 * BOX_H
    gx(1) = BOX_REACH:    gz(1) = -0.5 * BOX_H
    gx(2) = BOX_REACH:    gz(2) = 0.5 * BOX_H
    gx(3) = -0.5 * BOX_H: gz(3) = 0.5 * BOX_H
    uSign = uSignB: vSign = vSignB
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the inlet box's sketch."
    wRefSet = False
    For i = 0 To 3
        G2S sk, gx(i), yBox, gz(i), u0, v0
        G2S sk, gx((i + 1) Mod 4), yBox, gz((i + 1) Mod 4), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the inlet box."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    want = V_CONE + V_BOX
    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, BOX_DEPTH, 0.01, _
            False, False, False, False, 0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            If BodyCount() = 3 Then
                Set body = BodyOf("inlet")
                bx = body.GetBodyBox
                got = Volume(body)
                If Abs(bx(4) - (yBox + BOX_DEPTH)) < BOX_TOL And Abs(got - want) <= VOL_TOL * want Then
                    Note "inlet box extruded " & IIf(k = 0, "forward", "reversed") & ", merged with the cone: " & Fmt(got) & _
                         " m3 (expected " & Fmt(want) & ")"
                    Exit Sub
                End If
                Note "the inlet box went the wrong way (top y " & Fmt(bx(4)) & ", " & Fmt(got) & " m3); reversing"
            Else
                Note "the inlet box left " & BodyCount() & " bodies, not three; reversing"
            End If
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k
    Fail "the inlet box could not be extruded up from y = " & Fmt(yBox) & " m onto the cone in either direction."
End Sub


' The bodies take their zone's name (Fluent reads them from the STEP);
' a SolidWorks that will not rename them leaves the default names.
Private Sub NameBodies()
    Dim nm As Variant, i As Long, body As SldWorks.Body2
    nm = Array("rotor", "volute", "inlet")
    For i = 0 To 2
        Set body = BodyOf(nm(i))
        On Error Resume Next
        body.Name = nm(i)
        If Err.Number <> 0 Then Note "body " & nm(i) & " could not be renamed (" & Err.Description & ")"
        Err.Clear
        On Error GoTo 0
    Next i
End Sub


' A closed (r, y) profile on the z = 0 plane (x = r), revolved round
' its edge on the axis.
Private Sub RevolveOnZ(pl As SldWorks.Feature, px() As Double, py() As Double, ByVal n As Long, _
                       ByVal merge As Boolean, ByVal what As String)
    Dim sk As SldWorks.Sketch
    Dim seg As SldWorks.SketchSegment, axisSeg As SldWorks.SketchSegment
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim sd As SldWorks.SelectData
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim i As Long, j As Long

    uSign = uSignZ: vSign = vSignZ
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the " & what & "'s sketch on the z = 0 plane."
    wRefSet = False
    For i = 0 To n - 1
        j = (i + 1) Mod n
        G2S sk, px(i), py(i), 0#, u0, v0
        G2S sk, px(j), py(j), 0#, u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on the " & what & "'s profile."
        If px(i) = 0# And px(j) = 0# Then Set axisSeg = seg
    Next i
    If axisSeg Is Nothing Then Fail "the " & what & "'s profile has no edge on the axis."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set sd = swModel.SelectionManager.CreateSelectData
    sd.Mark = 16
    axisSeg.Select4 False, sd
    skFeat.Select2 True, 0
    Set f = swFeat.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        merge, True, True)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the " & what & "."
End Sub


' Which body is which, by where it lies: the inlet reaches past the
' volute's front plate (y > B); the volute's spiral runs out past the
' rotating zone's rim (-x); the rotor is the rest.
Private Function KindOf(ByVal body As Object) As String
    Dim bx As Variant
    bx = body.GetBodyBox
    If bx(4) > VOL_B + 0.5 * (FAN_B1 + CONE_L - VOL_B) Then
        KindOf = "inlet"
    ElseIf bx(0) < -(FAN_R_MRF + 0.5 * (VOL_R3 - FAN_R_MRF)) Then
        KindOf = "volute"
    Else
        KindOf = "rotor"
    End If
End Function


Private Function BodyOf(ByVal kind As String) As SldWorks.Body2
    Dim bodies As Variant, i As Long, n As Long
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    For i = 0 To UBound(bodies)
        If KindOf(bodies(i)) = kind Then
            Set BodyOf = bodies(i)
            n = n + 1
        End If
    Next i
    If n <> 1 Then Fail "found " & n & " bodies that look like the " & kind & ", expected 1."
End Function


Private Function Volume(body As SldWorks.Body2) As Double
    Dim mp As Variant
    mp = body.GetMassProperties(1#)
    Volume = mp(3)
End Function


Private Function BodyCount() As Long
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then BodyCount = 0 Else BodyCount = UBound(bodies) + 1
End Function


'==================================================================
' Verify: three bodies, each closed, the right volumes and extents
'==================================================================
Private Sub Verify()
    Dim nm As Variant, want(2) As Double, i As Long, k As Long
    Dim body As SldWorks.Body2, edges As Variant, adj As Variant
    Dim got As Double, bx As Variant

    If BodyCount() <> 3 Then Fail "the part has " & BodyCount() & " bodies, expected 3 (rotor, volute, inlet)."
    nm = Array("rotor", "volute", "inlet")
    want(0) = V_ROTOR - V_BLADES: want(1) = V_VOLUTE: want(2) = V_CONE + V_BOX
    For i = 0 To 2
        Set body = BodyOf(nm(i))
        edges = body.GetEdges
        If IsEmpty(edges) Then Fail "the " & nm(i) & " has no edges."
        For k = 0 To UBound(edges)
            adj = edges(k).GetTwoAdjacentFaces2
            If IsEmpty(adj) Then Fail "an edge of the " & nm(i) & " reports no adjacent faces; it is not closed."
            If adj(0) Is Nothing Or adj(1) Is Nothing Then Fail "an edge of the " & nm(i) & " has one face; it is an open shell."
        Next k
        got = Volume(body)
        If Abs(got - want(i)) > VOL_TOL * want(i) Then Fail "the " & nm(i) & " is " & Fmt(got) & " m3, expected " & Fmt(want(i)) & " m3."
        bx = body.GetBodyBox
        Note "body " & nm(i) & ": closed, " & (UBound(edges) + 1) & " edges, " & Fmt(got) & " m3 (expected " & Fmt(want(i)) & _
             "); x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5))
    Next i

    ' where each body must end, on its exact planes
    bx = BodyOf("rotor").GetBodyBox
    If Abs(bx(1)) > BOX_TOL Or Abs(bx(4) - IIf(FAN_B2 > FAN_B1, FAN_B2, FAN_B1)) > BOX_TOL Or Abs(bx(3) - FAN_R_MRF) > BOX_TOL Then _
        Fail "the rotor's box is wrong: y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & ", x max " & Fmt(bx(3)) & "."
    bx = BodyOf("volute").GetBodyBox
    If Abs(bx(1)) > BOX_TOL Or Abs(bx(4) - VOL_B) > BOX_TOL Then _
        Fail "the volute's box is wrong: y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & "."
    bx = BodyOf("inlet").GetBodyBox
    If Abs(bx(1) - FAN_B1) > BOX_TOL Or Abs(bx(4) - (yBox + BOX_DEPTH)) > BOX_TOL Or Abs(bx(3) - BOX_REACH) > BOX_TOL Then _
        Fail "the inlet's box is wrong: y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & ", x max " & Fmt(bx(3)) & "."
    Note "solid fluid volume " & Fmt(V_ROTOR - V_BLADES + V_VOLUTE + V_CONE + V_BOX) & " m3 in three zones"
End Sub


'==================================================================
' Boundary faces: found by what they are
'==================================================================
Private Sub TagBoundaryFaces()
    Dim nm As Variant, b As Long, i As Long, k As Long
    Dim body As SldWorks.Body2, faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface
    Dim p As Variant
    Dim cnt(5) As Long, area(5) As Double, a As Double
    Dim aRimRotor As Double, aRimVolute As Double, aEyeIn As Double, aEyeRotor As Double

    nm = Array("rotor", "volute", "inlet")
    For b = 0 To 2
        Set body = BodyOf(nm(b))
        faces = body.GetFaces
        For i = 0 To UBound(faces)
            Set face = faces(i)
            Set surf = face.GetSurface
            k = 0                        ' 0 wall, 1 fan_inlet, 2 fan_outlet, 3 interface_eye, 4 interface_rim, 5 blade
            If surf.IsPlane Then
                p = surf.PlaneParams
                If nm(b) = "inlet" And Abs(Abs(p(0)) - 1#) < DIR_TOL And Abs(p(3) - BOX_REACH) < FACE_TOL Then
                    k = 1
                ElseIf nm(b) = "volute" And Abs(Abs(p(0) * DIS_DX + p(2) * DIS_DZ) - 1#) < DIR_TOL And _
                       Abs(p(3) * DIS_DX + p(5) * DIS_DZ - VOL_S_EXIT) < FACE_TOL Then
                    k = 2
                ElseIf nm(b) <> "volute" And Abs(Abs(p(1)) - 1#) < DIR_TOL And Abs(p(4) - FAN_B1) < FACE_TOL Then
                    k = 3
                ElseIf nm(b) = "rotor" And Abs(p(1)) < DIR_TOL Then
                    k = 5                ' a blade's cap: its normal lies in the x-z plane
                End If
            ElseIf surf.IsCylinder Then
                p = surf.CylinderParams  ' origin, axis, radius
                If Abs(Abs(p(4)) - 1#) < DIR_TOL And Abs(p(6) - FAN_R_MRF) < RAD_TOL And nm(b) <> "inlet" Then
                    k = 4
                ElseIf nm(b) = "rotor" And (Abs(p(6) - (BLADE_RB - 0.5 * BLADE_T)) < RAD_TOL Or _
                                            Abs(p(6) - (BLADE_RB + 0.5 * BLADE_T)) < RAD_TOL) Then
                    k = 5
                End If
            End If
            a = face.GetArea
            cnt(k) = cnt(k) + 1: area(k) = area(k) + a
            If k = 3 Then
                If nm(b) = "inlet" Then aEyeIn = aEyeIn + a Else aEyeRotor = aEyeRotor + a
            ElseIf k = 4 Then
                If nm(b) = "rotor" Then aRimRotor = aRimRotor + a Else aRimVolute = aRimVolute + a
            End If
            Select Case k
            Case 1: Paint face, 0.9, 0#, 0#
            Case 2: Paint face, 0#, 0.4, 0.9
            Case 3: Paint face, 0.95, 0.85, 0#
            Case 4: Paint face, 0#, 0.7, 0.2
            Case 5: Paint face, 1#, 0.5, 0#
            Case Else: Paint face, 0.7, 0.7, 0.7
            End Select
        Next i
    Next b

    CheckFace "fan_inlet", cnt(1), 1, area(1), BOX_H * BOX_DEPTH, "red"
    CheckFace "fan_outlet", cnt(2), 1, area(2), VOL_B * hOut, "blue"
    CheckFace "interface_eye inlet side", IIf(aEyeIn > 0#, 1, 0), 1, aEyeIn, PI * FAN_R1 * FAN_R1, "yellow"
    CheckFace "interface_eye rotor side", IIf(aEyeRotor > 0#, 1, 0), 1, aEyeRotor, PI * FAN_R1 * FAN_R1, "yellow"
    CheckFace "interface_rim rotor side", IIf(aRimRotor > 0#, 1, 0), 1, aRimRotor, 2# * PI * FAN_R_MRF * FAN_B2, "green"
    CheckFace "interface_rim volute side", IIf(aRimVolute > 0#, 1, 0), 1, aRimVolute, 2# * PI * FAN_R_MRF * VOL_B, "green"
    If cnt(5) < 2 * FAN_Z Then Fail "found " & cnt(5) & " blade faces, expected at least " & 2 * FAN_Z & "."
    Note "boundary blade: " & cnt(5) & " faces, " & Fmt(area(5)) & " m2, colour orange"
    Note "boundary wall: " & cnt(0) & " faces, " & Fmt(area(0)) & " m2"
    Note "the volute's rim face is B wide, the rotor's b2: Fluent's interface makes the rest of it wall"
    swModel.ClearSelection2 True
End Sub


Private Sub CheckFace(ByVal what As String, ByVal n As Long, ByVal nWant As Long, ByVal a As Double, ByVal aWant As Double, ByVal colour As String)
    If n <> nWant Then Fail "found " & n & " " & what & " faces, expected " & nWant & "."
    If Abs(a - aWant) > AREA_TOL * aWant Then Fail what & " is " & Fmt(a) & " m2, expected " & Fmt(aWant) & " m2."
    Note "boundary " & what & ": " & Fmt(a) & " m2, colour " & colour
End Sub

'==================================================================
' Export: STEP AP214 (carries the face colours), binary STL in metres,
' and the SLDPRT -- as calciner.bas; the three bodies stay apart.
'==================================================================
Private Sub ExportFiles()
    Dim outDir As String
    outDir = OUT_ROOT & LINE_KEY & "\"
    EnsureDir OUT_ROOT
    EnsureDir outDir

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
    swApp.SetUserPreferenceDoubleValue swSTLDeviation, 0.001
    swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, 0.1

    SaveOne outDir & FAN_NAME & ".SLDPRT"
    SaveOne outDir & FAN_NAME & ".step"
    SaveOne outDir & FAN_NAME & ".stl"
End Sub


Private Sub SaveOne(ByVal path As String)
    Dim errs As Long, warns As Long
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If errs <> 0 Then Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    If Dir(path) = "" Then Fail "SolidWorks reported no error but " & path & " is not on disk."
    Note "wrote " & path
End Sub


Private Sub EnsureDir(ByVal path As String)
    If Dir(path, vbDirectory) = "" Then MkDir path
End Sub


' Set through the property from a typed Double array, read back and
' checked (the colours carry the boundary names into Fluent).
Private Sub Paint(face As SldWorks.Face2, ByVal r As Double, ByVal g As Double, ByVal b As Double)
    Dim m(8) As Double
    Dim got As Variant
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = 0#: m(8) = 0#
    face.MaterialPropertyValues = m
    got = face.MaterialPropertyValues
    If IsEmpty(got) Then Fail "a face reports no colour after one was set on it."
    If Abs(got(0) - r) > 0.01 Or Abs(got(1) - g) > 0.01 Or Abs(got(2) - b) > 0.01 Then _
        Fail "a face's colour came back as (" & Fmt(got(0)) & ", " & Fmt(got(1)) & ", " & Fmt(got(2)) & _
             ") after being set to (" & Fmt(r) & ", " & Fmt(g) & ", " & Fmt(b) & ")."
End Sub


'==================================================================
' Housekeeping
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
    Err.Raise vbObjectError + 1, "id_fan", msg
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\id_fan_build.log"
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


'==================================================================
' Sketch helpers, as in calciner.bas (calibrated at run time)
'==================================================================

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
