Attribute VB_Name = "kic_solid"
'==================================================================
' Kiln inlet chamber CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' ONE closed solid: the gas volume of the chamber between the rotary
' kiln's mouth and the calciner's throat (geometry/kiln/kiln_inlet_chamber.md),
' the section of the user's sketch (21 Nov 2026; plant_geometry.chamber_section,
' as plant_topology_2d.bas draws it), the plan 2 a across:
'   1. the x-z section, five corners, extruded across the plan: the left
'      wall x = -r (the throat's) from the ramp's top up to the roof; the
'      ramp at ramp_deg down to its toe; the foot (the kiln's bottom line,
'      falling at its slope) to the mouth's lower lip; the mouth's face,
'      square to the kiln axis, to the upper lip; the roof (the kiln's top
'      line) back to the left wall;
'   2. the calciner's throat, radius r, from its foot z = H (the roof's
'      highest point under it, at x = -r: the calciner sits on the roof,
'      user decision 22 Nov 2026) down to the roof (up to next): a wedge,
'      0 at x = -r, 2 r tan(alpha) at x = +r; its top disc is the outlet,
'      level, the calciner's own inlet face;
'   3. the kiln tube's stub, radius R and CH_STUB_L along the kiln axis,
'      revolved on the mouth's face (user decision, 22 Nov 2026: the foot
'      and roof are the tube's own lines, so a circle split on the wall
'      would touch both), merged.
' The section's foot and roof touch the stub's circle at its bottom and
' top: the mouth's face is two pieces meeting there at a point (as the
' kiln's lines carried in ask), not a sliver. No refractory, no burner, no
' meal pipe: the meal is injected in the solver.
'
' Coordinates: x across from the calciner axis (x = 0), the kiln comes in
' from +x (as the layout has it), its axis CH_A over the floor level at
' x = CH_A, falling at CH_ALPHA towards +x; y across the plan (y = 0 on
' the axis); z up from the chamber's floor level (z = 0, no face there).
'
' Boundary faces (coloured for Fluent): kiln_gas_inlet = the stub's end
' disc (red); throat_outlet = the throat's top disc (blue); wall = every
' other face, the ramp included (grey).
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA editor
' File -> Import File... and pick this .bas. Run `main`.
' Outputs geometry\output\2500\kiln_inlet_chamber.SLDPRT, .step, .stl and
' kiln_inlet_chamber_build.log (tests/test_plant_geometry.py reads the log).
'==================================================================

Option Explicit

Const CHAMBER_NAME As String = "kiln_inlet_chamber"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const CH_A                         As Double  = 3.4          ' half the plan (y), and the kiln axis over the floor level at x = a: kiln D / 2 + the layout margin [derived]
Const KILN_D                       As Double  = 4.8          ' the kiln tube's bore: the stub and its end disc (kiln_gas_inlet) [published, kiln/kiln.md]
Const CH_ALPHA                     As Double  = 0.029991005  ' the kiln's slope [rad]: the stub's axis falls at it towards +x [derived]
Const CH_H                         As Double  = 5.950031     ' the throat's top (throat_outlet), over the floor level [derived]
Const CH_R_THROAT                  As Double  = 1.565039     ' the calciner throat's radius; its walls x = +-r [derived]
Const CH_RAMP_TOP_Z                As Double  = 5.173392     ' the ramp's top on the left wall x = -r [derived]
Const CH_TOE_X                     As Double  = 1.9          ' the ramp's toe: the foot (the kiln's bottom line) starts [derived]
Const CH_TOE_Z                     As Double  = 1.04392      ' the ramp's toe [derived]
Const CH_LIP_LO_X                  As Double  = 3.328032     ' the mouth's lower lip (the end face square to the kiln axis) [derived]
Const CH_LIP_LO_Z                  As Double  = 1.001079     ' the mouth's lower lip [derived]
Const CH_LIP_UP_X                  As Double  = 3.471968     ' the mouth's upper lip [derived]
Const CH_LIP_UP_Z                  As Double  = 5.798921     ' the mouth's upper lip [derived]
Const CH_ROOF_LEFT_Z               As Double  = 5.950031     ' the roof (the kiln's top line) at the left wall x = -r [derived]
Const CH_ROOF_THROAT_Z             As Double  = 5.856129     ' the roof at the throat's right wall x = +r [derived]
Const CH_STUB_L                    As Double  = 2.4          ' the kiln tube's stub along its axis, mouth face to kiln_gas_inlet [derived]
Const CH_V_BOX                     As Double  = 114.706578   ' the section's prism, the plan across [m3] [derived]
Const CH_V_THROAT                  As Double  = 0.361282     ' the throat cylinder over the roof [m3] [derived]
Const CH_V_STUB                    As Double  = 43.429377    ' the kiln tube's stub [m3] [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL  As Double = 0.001   ' relative, on the exact volumes
Const AREA_TOL As Double = 0.002   ' relative, on face areas
Const BOX_TOL  As Double = 0.01    ' absolute [m]
Const FACE_TOL As Double = 0.0001
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001
Const PI As Double = 3.14159265358979

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean
Dim uSignY As Double, vSignY As Double      ' the plane y = 0 (the section, the stub's profile)
Dim uSignS As Double, vSignS As Double      ' the plane z = H (the throat's circle)
Dim uSign As Double, vSign As Double
Dim wRef As Double
Dim wRefSet As Boolean

Dim dX As Double, dZ As Double              ' the kiln axis's direction, out of the chamber (+x, falling)
Dim nX As Double, nZ As Double              ' square to it in the x-z plane, up
Dim axX As Double, axZ As Double            ' the axis on the mouth's face
Dim enX As Double, enZ As Double            ' the axis on the stub's end disc
Dim boxW(5) As Double                       ' the solid's box: x, y, z min then max

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

    Note "macro version 22 Nov 2026 (section, throat up to next, kiln stub)"
    phase = "working out the coordinates"
    Expected
    phase = "building the solid"
    Build
    phase = "verifying the solid"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog CHAMBER_NAME & " built, verified and exported"
    ' no message box when OUT_ROOT\quiet.flag exists (a run from WSL,
    ' tools/sw_run.py kic_solid.main): the log carries the result
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox CHAMBER_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln inlet chamber"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog CHAMBER_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox CHAMBER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln inlet chamber"
    End If
End Sub


' The axis, the box and the volumes the build is held to (the volumes are
' exact, from plant_geometry.chamber_section). The section's corners are
' checked against the kiln's lines here, so a source that no longer
' closes fails before anything is built.
Private Sub Expected()
    Dim R As Double, e As Double
    R = 0.5 * KILN_D
    dX = Cos(CH_ALPHA): dZ = -Sin(CH_ALPHA)
    nX = Sin(CH_ALPHA): nZ = Cos(CH_ALPHA)
    axX = CH_A: axZ = CH_A
    enX = axX + CH_STUB_L * dX: enZ = axZ + CH_STUB_L * dZ

    ' the lips are the mouth's face: R either side of the axis, square to it
    e = Abs(CH_LIP_LO_X - (axX - R * nX)) + Abs(CH_LIP_LO_Z - (axZ - R * nZ)) + _
        Abs(CH_LIP_UP_X - (axX + R * nX)) + Abs(CH_LIP_UP_Z - (axZ + R * nZ))
    If e > FACE_TOL Then Fail "the mouth's lips are not R either side of the kiln axis square to it (off by " & Fmt(e) & " m)."
    ' the foot and the roof are the kiln's bottom and top lines
    e = Abs((CH_TOE_Z - CH_LIP_LO_Z) * dX - (CH_TOE_X - CH_LIP_LO_X) * dZ) + _
        Abs((CH_ROOF_LEFT_Z - CH_LIP_UP_Z) * dX - (-CH_R_THROAT - CH_LIP_UP_X) * dZ)
    If e > FACE_TOL Then Fail "the foot or the roof is not along the kiln axis (off by " & Fmt(e) & " m)."
    If Not (CH_RAMP_TOP_Z < CH_ROOF_THROAT_Z And CH_TOE_X > -CH_R_THROAT And CH_TOE_X < CH_LIP_LO_X) Then
        Fail "the section does not close: the ramp's top " & Fmt(CH_RAMP_TOP_Z) & " m must be under the roof at the throat " & _
             Fmt(CH_ROOF_THROAT_Z) & " m and the toe x " & Fmt(CH_TOE_X) & " between the throat's wall and the mouth."
    End If
    If CH_ROOF_LEFT_Z > CH_H + FACE_TOL Then Fail "the roof " & Fmt(CH_ROOF_LEFT_Z) & " m is over the throat's top " & Fmt(CH_H) & " m."

    boxW(0) = -CH_R_THROAT
    boxW(1) = -CH_A
    boxW(2) = CH_LIP_LO_Z
    If enZ - R * nZ < boxW(2) Then boxW(2) = enZ - R * nZ
    boxW(3) = enX + R * nX
    boxW(4) = CH_A
    boxW(5) = CH_H

    Note "chamber: section ramp top (" & Fmt(-CH_R_THROAT) & ", " & Fmt(CH_RAMP_TOP_Z) & "), toe (" & Fmt(CH_TOE_X) & ", " & Fmt(CH_TOE_Z) & _
         "), mouth lips (" & Fmt(CH_LIP_LO_X) & ", " & Fmt(CH_LIP_LO_Z) & ") / (" & Fmt(CH_LIP_UP_X) & ", " & Fmt(CH_LIP_UP_Z) & _
         "), roof at the left wall " & Fmt(CH_ROOF_LEFT_Z) & " m; plan " & Fmt(2# * CH_A) & " m across"
    Note "throat D " & Fmt(2# * CH_R_THROAT) & " m, top at " & Fmt(CH_H) & " m; kiln stub D " & Fmt(KILN_D) & " m, " & Fmt(CH_STUB_L) & _
         " m along the axis, end disc's centre (" & Fmt(enX) & ", " & Fmt(enZ) & ")"
    Note "volumes (exact): section prism " & Fmt(CH_V_BOX) & ", throat " & Fmt(CH_V_THROAT) & ", stub " & Fmt(CH_V_STUB) & " m3"
End Sub


'==================================================================
' Build
'==================================================================
Private Sub Build()
    Dim planeY As SldWorks.Feature, planeZ0 As SldWorks.Feature
    Dim planeS As SldWorks.Feature

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
    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."
    Set planeS = OffsetPlane(planeZ0, 0#, 0#, CH_H, uSignS, vSignS)

    ExtrudeProfile planeY
    ExtrudeThroat planeS
    RevolveStub planeY
End Sub


' The x-z section (five corners), extruded both ways from y = 0 to the plan's sides.
Private Sub ExtrudeProfile(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim px(4) As Double, pz(4) As Double, i As Long, j As Long
    Dim bx As Variant, got As Double

    px(0) = -CH_R_THROAT: pz(0) = CH_RAMP_TOP_Z     ' the ramp's top on the throat's left wall
    px(1) = CH_TOE_X:     pz(1) = CH_TOE_Z          ' the toe: the foot, the kiln's bottom line, starts
    px(2) = CH_LIP_LO_X:  pz(2) = CH_LIP_LO_Z       ' the mouth's lower lip
    px(3) = CH_LIP_UP_X:  pz(3) = CH_LIP_UP_Z       ' the upper lip (the face square to the kiln axis)
    px(4) = -CH_R_THROAT: pz(4) = CH_ROOF_LEFT_Z    ' the roof, the kiln's top line, at the left wall
    uSign = uSignY: vSign = vSignY

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the section's sketch on the y = 0 plane."
    wRefSet = False
    For i = 0 To 4
        j = (i + 1) Mod 5
        G2S sk, px(i), 0#, pz(i), u0, v0
        G2S sk, px(j), 0#, pz(j), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the section."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    ' two-sided: CH_A each way from the sketch plane
    Set f = swFeat.FeatureExtrusion3( _
        False, False, False, _
        swEndCondBlind, swEndCondBlind, CH_A, CH_A, _
        False, False, False, False, 0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "the section could not be extruded both ways across the plan."
    If BodyCount() <> 1 Then Fail "the section's extrusion made " & BodyCount() & " bodies, not one."
    bx = TheBody().GetBodyBox
    If Abs(bx(0) + CH_R_THROAT) > BOX_TOL Or Abs(bx(3) - CH_LIP_UP_X) > BOX_TOL Or _
       Abs(bx(1) + CH_A) > BOX_TOL Or Abs(bx(4) - CH_A) > BOX_TOL Or _
       Abs(bx(2) - CH_LIP_LO_Z) > BOX_TOL Or Abs(bx(5) - CH_ROOF_LEFT_Z) > BOX_TOL Then
        Fail "the section's box is x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
             ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m; expected x " & Fmt(-CH_R_THROAT) & " .. " & Fmt(CH_LIP_UP_X) & _
             ", y +-" & Fmt(CH_A) & ", z " & Fmt(CH_LIP_LO_Z) & " .. " & Fmt(CH_ROOF_LEFT_Z)
    End If
    got = Volume(TheBody())
    If Abs(got - CH_V_BOX) > VOL_TOL * CH_V_BOX Then Fail "the section's prism is " & Fmt(got) & " m3, expected " & Fmt(CH_V_BOX) & " m3."
    Note "section extruded: " & Fmt(got) & " m3 (expected " & Fmt(CH_V_BOX) & ")"
End Sub


' The throat: its circle on the plane z = H, extruded down up to the next
' face (the roof), merged. Both directions are tried; the one that leaves
' one body, its top at H and the prism + throat volume is kept.
Private Sub ExtrudeThroat(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u As Double, v As Double, k As Long, zmax As Double, got As Double, want As Double, depth As Double

    want = CH_V_BOX + CH_V_THROAT
    uSign = uSignS: vSign = vSignS
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the throat's sketch on the plane z = " & Fmt(CH_H) & "."
    wRefSet = False
    G2S sk, 0#, 0#, CH_H, u, v
    If swSkMgr.CreateCircleByRadius(u, v, 0#, CH_R_THROAT) Is Nothing Then Fail "CreateCircleByRadius failed on the throat."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    ' up to next (forward, reversed); else blind into the chamber, its
    ' foot between the ramp's top and the roof (the part inside merges)
    depth = CH_H - 0.5 * (CH_RAMP_TOP_Z + CH_ROOF_THROAT_Z)
    For k = 0 To 3
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, ((k Mod 2) = 1), _
            IIf(k < 2, swEndCondUpToNext, swEndCondBlind), swEndCondBlind, depth, 0.01, _
            False, False, False, False, 0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            If BodyCount() = 1 Then
                zmax = MaxZ()
                got = Volume(TheBody())
                If Abs(zmax - CH_H) < FACE_TOL And Abs(got - want) < VOL_TOL * want Then
                    Note "throat extruded " & Choose(k + 1, "up to next", "up to next, reversed", "blind", "blind, reversed") & ": " & Fmt(got) & " m3 (expected " & Fmt(want) & ")"
                    Exit Sub
                End If
                Note "the throat's extrusion " & Choose(k + 1, "up to next", "up to next, reversed", "blind", "blind, reversed") & " gave top " & Fmt(zmax) & " m, " & Fmt(got) & " m3; undone"
            Else
                Note "the throat's extrusion left " & BodyCount() & " bodies, not one; undone"
            End If
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k
    Fail "the throat could not be extruded from z = " & Fmt(CH_H) & " m down to the roof in either direction."
End Sub


' The kiln tube's stub: the rectangle axis-to-wall, from the mouth's face
' to the end disc, sketched on y = 0 and revolved about the axis, merged.
Private Sub RevolveStub(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim seg As SldWorks.SketchSegment, axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim px(3) As Double, pz(3) As Double, i As Long, j As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim R As Double, got As Double, want As Double, k As Long

    R = 0.5 * KILN_D
    want = CH_V_BOX + CH_V_THROAT + CH_V_STUB
    px(0) = axX:          pz(0) = axZ              ' the axis on the mouth's face
    px(1) = enX:          pz(1) = enZ              ' the axis on the end disc
    px(2) = enX + R * nX: pz(2) = enZ + R * nZ
    px(3) = axX + R * nX: pz(3) = axZ + R * nZ     ' = the upper lip
    uSign = uSignY: vSign = vSignY

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the stub's sketch on the y = 0 plane."
    wRefSet = False
    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, px(i), 0#, pz(i), u0, v0
        G2S sk, px(j), 0#, pz(j), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on the stub's profile."
        If i = 0 Then Set axisSeg = seg
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    ' merged (forward, then reversed); else as its own body, combined
    For k = 0 To 2
        swModel.ClearSelection2 True
        Set selData = swModel.SelectionManager.CreateSelectData
        selData.Mark = 16
        axisSeg.Select4 False, selData
        skFeat.Select2 True, 0
        Set f = swFeat.FeatureRevolve2( _
            True, True, False, False, (k = 1), False, _
            0, 0, 2# * PI, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            (k < 2), True, True)
        swModel.ClearSelection2 True
        If f Is Nothing Then
            Note "FeatureRevolve2 (" & Choose(k + 1, "merged", "merged, reversed", "own body") & ") made nothing"
        Else
            Note "stub revolved (" & Choose(k + 1, "merged", "merged, reversed", "own body") & "): " & BodyCount() & " bodies"
            Exit For
        End If
    Next k
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the kiln tube's stub in all three forms (log)."
    If BodyCount() = 2 Then
        Dim bodies As Variant
        bodies = swPart.GetBodies2(swSolidBody, True)
        Set f = swFeat.InsertCombineFeature(15903, Nothing, bodies)     ' swBodyOperationType_e.SWBODYADD
        If f Is Nothing Then Fail "the stub revolved as its own body but could not be combined with the chamber (InsertCombineFeature add)."
        Note "stub combined with the chamber: " & BodyCount() & " bodies"
    End If
    If BodyCount() <> 1 Then Fail "the stub left " & BodyCount() & " bodies, not one."
    got = Volume(TheBody())
    If Abs(got - want) > VOL_TOL * want Then Fail "with the stub the chamber is " & Fmt(got) & " m3, expected " & Fmt(want) & " m3."
    Note "kiln tube's stub revolved on the mouth's face: " & Fmt(got) & " m3 (expected " & Fmt(want) & ")"
End Sub


Private Function MaxZ() As Double
    Dim bodies As Variant, i As Long, bx As Variant, m As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    m = -1E+30
    For i = 0 To UBound(bodies)
        bx = bodies(i).GetBodyBox
        If bx(5) > m Then m = bx(5)
    Next i
    MaxZ = m
End Function


Private Function BodiesVolume() As Double
    Dim bodies As Variant, i As Long, t As Double, b As SldWorks.Body2
    bodies = swPart.GetBodies2(swSolidBody, True)
    For i = 0 To UBound(bodies)
        Set b = bodies(i)                ' a Body2 variable: a Variant element is a ByRef type mismatch
        t = t + Volume(b)
    Next i
    BodiesVolume = t
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


Private Function TheBody() As SldWorks.Body2
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) <> 0 Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not one."
    Set TheBody = bodies(0)
End Function


'==================================================================
' Verify: one body, closed, the right volume and box
'==================================================================
Private Sub Verify()
    Dim body As SldWorks.Body2
    Dim edges As Variant, edge As SldWorks.Edge, adj As Variant
    Dim vGot As Double, vLo As Double, vHi As Double, i As Long
    Dim bx As Variant

    Set body = TheBody()
    edges = body.GetEdges
    If IsEmpty(edges) Then Fail "the body has no edges."
    For i = 0 To UBound(edges)
        Set edge = edges(i)
        adj = edge.GetTwoAdjacentFaces2
        If IsEmpty(adj) Then Fail "edge " & i & " reports no adjacent faces; the body is not closed."
        If adj(0) Is Nothing Or adj(1) Is Nothing Then Fail "edge " & i & " has only one adjacent face; the body is an open shell."
    Next i
    Note "closed manifold solid: " & (UBound(edges) + 1) & " edges, each with two faces"

    vGot = Volume(body)
    vLo = (CH_V_BOX + CH_V_THROAT + CH_V_STUB) * (1# - VOL_TOL)
    vHi = (CH_V_BOX + CH_V_THROAT + CH_V_STUB) * (1# + VOL_TOL)
    If vGot < vLo Or vGot > vHi Then Fail "the chamber is " & Fmt(vGot) & " m3, outside " & Fmt(vLo) & " .. " & Fmt(vHi) & " m3."
    Note "chamber volume " & Fmt(vGot) & " m3 (section prism " & Fmt(CH_V_BOX) & " + throat " & Fmt(CH_V_THROAT) & _
         " + kiln stub " & Fmt(CH_V_STUB) & ")"

    ' GetBodyBox may be loose on curved faces: the stub's end is held to
    ' BOX_TOL, every other side to the section's corners
    bx = body.GetBodyBox
    For i = 0 To 5
        If Abs(bx(i) - boxW(i)) > BOX_TOL Then
            Fail "the solid's box is x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
                 ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m; expected x " & Fmt(boxW(0)) & " .. " & Fmt(boxW(3)) & _
                 ", y " & Fmt(boxW(1)) & " .. " & Fmt(boxW(4)) & ", z " & Fmt(boxW(2)) & " .. " & Fmt(boxW(5)) & "."
        End If
    Next i
    Note "extent: x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
         ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m"
End Sub


'==================================================================
' Boundary faces: found by what they are
'==================================================================
Private Sub TagBoundaryFaces()
    Dim faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface, p As Variant, bx As Variant
    Dim i As Long, k As Long
    Dim nIn As Long, aIn As Double, nOut As Long, aOut As Double, nWall As Long, aWall As Double
    Dim wantIn As Double, wantOut As Double

    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        k = 0                                   ' 0 wall, 1 kiln mouth, 2 throat outlet
        If surf.IsPlane Then
            p = surf.PlaneParams
            ' the stub's end disc: normal along the kiln axis, through the
            ' axis's end point (the mouth's face pieces share the normal
            ' but lie CH_STUB_L back)
            If Abs(Abs(p(0) * dX + p(2) * dZ) - 1#) < DIR_TOL And _
               Abs((p(3) - enX) * dX + (p(5) - enZ) * dZ) < FACE_TOL Then
                k = 1
            ElseIf Abs(Abs(p(2)) - 1#) < DIR_TOL And Abs(p(5) - CH_H) < FACE_TOL Then
                k = 2
            End If
        End If
        Select Case k
        Case 1
            nIn = nIn + 1: aIn = aIn + face.GetArea
            Paint face, 0.9, 0#, 0#
        Case 2
            nOut = nOut + 1: aOut = aOut + face.GetArea
            Paint face, 0#, 0.4, 0.9
        Case Else
            nWall = nWall + 1: aWall = aWall + face.GetArea
            Paint face, 0.7, 0.7, 0.7
        End Select
    Next i

    wantIn = PI * 0.25 * KILN_D * KILN_D
    wantOut = PI * CH_R_THROAT * CH_R_THROAT
    If nIn <> 1 Then Fail "found " & nIn & " kiln_gas_inlet faces, expected 1."
    If Abs(aIn - wantIn) > AREA_TOL * wantIn Then Fail "kiln_gas_inlet is " & Fmt(aIn) & " m2, expected " & Fmt(wantIn) & " m2."
    Note "boundary kiln_gas_inlet: " & Fmt(aIn) & " m2, colour red"
    If nOut <> 1 Then Fail "found " & nOut & " throat_outlet faces, expected 1."
    If Abs(aOut - wantOut) > AREA_TOL * wantOut Then Fail "throat_outlet is " & Fmt(aOut) & " m2, expected " & Fmt(wantOut) & " m2."
    Note "boundary throat_outlet: " & Fmt(aOut) & " m2, colour blue"
    Note "boundary wall: " & nWall & " faces, " & Fmt(aWall) & " m2"
    swModel.ClearSelection2 True
End Sub

'==================================================================
' Export: STEP AP214 (carries the face colours), binary STL in metres,
' and the SLDPRT -- as calciner.bas.
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

    SaveOne outDir & CHAMBER_NAME & ".SLDPRT"
    SaveOne outDir & CHAMBER_NAME & ".step"
    SaveOne outDir & CHAMBER_NAME & ".stl"
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
    Err.Raise vbObjectError + 1, "kiln_inlet_chamber", msg
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\kiln_inlet_chamber_build.log"
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
