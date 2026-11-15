Attribute VB_Name = "kiln_inlet_chamber"
'==================================================================
' Kiln inlet chamber CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' ONE closed solid: the gas volume of the chamber between the rotary
' kiln's mouth and the calciner's throat (geometry/kiln/kiln_inlet_chamber.md),
' the layout's square (side 2 a, flat roof):
'   1. the x-z profile, a triangle: the floor is ONE ramp across the whole
'      plan, from the kiln mouth's lower lip up to the far top corner, the
'      +x wall and the roof; extruded across the plan;
'   2. the calciner's throat, a thin disc (STUB_T) on the roof, merged.
' The kiln mouth is a circle split on the +x wall. No refractory, no
' burner, no meal pipe: the meal is injected in the solver.
'
' Coordinates: x across from the calciner axis (x = 0), the kiln comes in
' on the +x wall (as the layout has it); y across the plan (y = 0 on the
' axis); z up from the chamber floor (z = 0).
'
' Boundary faces (coloured for Fluent): kiln_gas_inlet = the mouth's
' circle on the +x wall (red); throat_outlet = the throat's disc on the
' roof (blue); wall = every other face, the ramp included (grey).
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
Const CH_A                         As Double  = 3.4          ' half the square plan: kiln D / 2 + the layout margin [derived]
Const KILN_D                       As Double  = 4.8          ' the mouth's circle on the +x wall [published, kiln/kiln.md]
Const CH_CLEAR                     As Double  = 0.2          ' the mouth's clearance to the ramp's foot [model, kiln/kiln_inlet_chamber.md]
Const CH_R_THROAT                  As Double  = 1.565039     ' the calciner throat's radius, the outlet disc in the roof [derived]
Const CH_H_LIP                     As Double  = 0.8          ' the ramp's foot on the +x wall; the ramp rises to the far top corner, z = 2 CH_A [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const STUB_T   As Double = 0.001   ' the throat disc's thickness [m] over the roof
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
Dim uSignX As Double, vSignX As Double      ' the plane x = 0 (the mouth's split)
Dim uSignY As Double, vSignY As Double      ' the plane y = 0 (the profile)
Dim uSignS As Double, vSignS As Double      ' the plane under the outlet (the throat disc)
Dim uSign As Double, vSign As Double
Dim wRef As Double
Dim wRefSet As Boolean

Dim zRoof As Double, zTop As Double
Dim vProfile As Double, vStub As Double

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
    MsgBox CHAMBER_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln inlet chamber"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog CHAMBER_NAME & " ABORTED while " & phase & ": " & why
    MsgBox CHAMBER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln inlet chamber"
End Sub


' The volumes the build is held to: both exact.
Private Sub Expected()
    Dim a2 As Double
    zRoof = 2# * CH_A
    zTop = zRoof + STUB_T
    vProfile = 0.5 * (2# * CH_A) * (zRoof - CH_H_LIP) * (2# * CH_A)
    a2 = PI * CH_R_THROAT * CH_R_THROAT
    vStub = a2 * STUB_T
    Note "chamber: " & Fmt(2# * CH_A) & " m square, flat roof at " & Fmt(zRoof) & " m, throat D " & Fmt(2# * CH_R_THROAT) & _
         " m in it; floor ramp across the plan from " & Fmt(CH_H_LIP) & " m (the +x wall) to the far top corner"
    Note "profile volume " & Fmt(vProfile) & " m3, throat disc " & Fmt(vStub) & " m3 (exact)"
End Sub


'==================================================================
' Build
'==================================================================
Private Sub Build()
    Dim planeX As SldWorks.Feature, planeY As SldWorks.Feature, planeZ0 As SldWorks.Feature
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
    Set planeX = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX Is Nothing Then Fail "could not find the default plane whose normal is X."
    CalibrateSketchAxes planeX, 0#, 0#, 0#, uSignX, vSignX
    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."
    Set planeS = OffsetPlane(planeZ0, 0#, 0#, zRoof, uSignS, vSignS)

    ExtrudeProfile planeY
    ExtrudeStub planeS
    SplitMouth planeX
End Sub


' The x-z profile (a triangle), extruded both ways from y = 0 to the plan's sides.
Private Sub ExtrudeProfile(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim px(2) As Double, pz(2) As Double, i As Long, j As Long
    Dim bx As Variant, got As Double

    px(0) = CH_A:         pz(0) = CH_H_LIP        ' the ramp's foot on the kiln's (+x) wall, clear under the mouth
    px(1) = -CH_A:        pz(1) = zRoof           ' the ramp's top, the far top corner
    px(2) = CH_A:         pz(2) = zRoof
    uSign = uSignY: vSign = vSignY

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the profile's sketch on the y = 0 plane."
    wRefSet = False
    For i = 0 To 2
        j = (i + 1) Mod 3
        G2S sk, px(i), 0#, pz(i), u0, v0
        G2S sk, px(j), 0#, pz(j), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the profile."
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
    If f Is Nothing Then Fail "the profile could not be extruded both ways across the plan."
    If BodyCount() <> 1 Then Fail "the profile extrusion made " & BodyCount() & " bodies, not one."
    bx = TheBody().GetBodyBox
    If Abs(bx(0) + CH_A) > BOX_TOL Or Abs(bx(3) - CH_A) > BOX_TOL Or _
       Abs(bx(1) + CH_A) > BOX_TOL Or Abs(bx(4) - CH_A) > BOX_TOL Or _
       Abs(bx(2) - CH_H_LIP) > BOX_TOL Or Abs(bx(5) - zRoof) > BOX_TOL Then
        Fail "the profile's box is x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
             ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m; expected +-" & Fmt(CH_A) & " in x and y, " & Fmt(CH_H_LIP) & " .. " & Fmt(zRoof)
    End If
    got = Volume(TheBody())
    If Abs(got - vProfile) > VOL_TOL * vProfile Then Fail "the profile body is " & Fmt(got) & " m3, expected " & Fmt(vProfile) & " m3."
    Note "profile extruded: " & Fmt(got) & " m3 (expected " & Fmt(vProfile) & ")"
End Sub


' The throat's disc on the roof, STUB_T thick, merged into the body.
Private Sub ExtrudeStub(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u As Double, v As Double, k As Long, zmax As Double

    uSign = uSignS: vSign = vSignS
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the throat disc's sketch."
    wRefSet = False
    G2S sk, 0#, 0#, zRoof, u, v
    If swSkMgr.CreateCircleByRadius(u, v, 0#, CH_R_THROAT) Is Nothing Then Fail "CreateCircleByRadius failed on the throat disc."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, STUB_T, 0.01, _
            False, False, False, False, 0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            If BodyCount() = 1 Then
                zmax = MaxZ()
                If Abs(zmax - zTop) < FACE_TOL Then
                    Note "throat disc extruded " & IIf(k = 0, "forward", "reversed") & ": top at z " & Fmt(zmax) & " m"
                    Exit Sub
                End If
                Note "the throat disc extruded the wrong way (top at z " & Fmt(zmax) & "); reversing"
            Else
                Note "the throat disc left " & BodyCount() & " bodies, not one"
            End If
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k
    Fail "the throat disc could not be extruded up to z = " & Fmt(zTop) & " m in either direction."
End Sub


' The mouth: a circle on the +x wall, the wall split into the disc
' (kiln_gas_inlet) and the rest. A circle sketched on the x = 0 plane,
' projected on the wall; every way the projection can be asked for is
' tried and the one that leaves two faces on the wall is kept.
Private Sub SplitMouth(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u As Double, v As Double
    Dim sd As SldWorks.SelectData, ent As SldWorks.Entity
    Dim face As SldWorks.Face2
    Dim k As Long, dirOpt As Boolean, flipOpt As Boolean, mk As Long

    uSign = uSignX: vSign = vSignX
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the mouth's sketch on the x = 0 plane."
    wRefSet = False
    G2S sk, 0#, 0#, CH_A, u, v                      ' the kiln axis: y = 0, z = a above the floor
    If swSkMgr.CreateCircleByRadius(u, v, 0#, 0.5 * KILN_D) Is Nothing Then Fail "CreateCircleByRadius failed on the mouth."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 7
        dirOpt = ((k And 1) <> 0): flipOpt = ((k And 2) <> 0): mk = IIf((k And 4) <> 0, 0, 1)
        Set face = WallFace()
        If face Is Nothing Then Fail "found no planar face on the +x wall (x = " & Fmt(CH_A) & " m) to split."
        swModel.ClearSelection2 True
        skFeat.Select2 False, 4
        Set sd = swModel.SelectionManager.CreateSelectData
        sd.Mark = mk
        Set ent = face
        ent.Select4 True, sd
        On Error Resume Next
        swModel.InsertSplitLineProject dirOpt, flipOpt
        If Err.Number <> 0 Then Note "InsertSplitLineProject (" & dirOpt & ", " & flipOpt & ", mark " & mk & ") raised: " & Err.Description
        Err.Clear
        On Error GoTo 0
        swModel.ClearSelection2 True
        If BodyCount() = 1 Then
            If WallFaceCount() = 2 Then
                Note "split the +x wall into the mouth and the rest (projection " & dirOpt & ", " & flipOpt & ", face mark " & mk & ")"
                Exit Sub
            End If
        End If
        Set f = swModel.FeatureByPositionReverse(0)
        If Not f Is Nothing Then
            If f.GetTypeName2 = "SplitLine" Then
                Note "split of the +x wall gave " & WallFaceCount() & " faces, not 2 (projection " & dirOpt & ", " & flipOpt & ", face mark " & mk & "); undone"
                f.Select2 False, 0
                swModel.EditDelete
                swModel.ClearSelection2 True
            End If
        End If
    Next k
    Fail "could not split the +x wall into the mouth and the rest: InsertSplitLineProject changed nothing in any of its eight forms."
End Sub


' The planar face with its normal along x lying at x = +a (the first).
Private Function WallFace() As SldWorks.Face2
    Dim faces As Variant, i As Long, p As Variant
    Dim face As SldWorks.Face2, surf As SldWorks.Surface
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(Abs(p(0)) - 1#) < DIR_TOL And Abs(p(3) - CH_A) < FACE_TOL Then
                Set WallFace = face
                Exit Function
            End If
        End If
    Next i
End Function


Private Function WallFaceCount() As Long
    Dim faces As Variant, i As Long, p As Variant, n As Long
    Dim face As SldWorks.Face2, surf As SldWorks.Surface
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(Abs(p(0)) - 1#) < DIR_TOL And Abs(p(3) - CH_A) < FACE_TOL Then n = n + 1
        End If
    Next i
    WallFaceCount = n
End Function


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
    Dim bodies As Variant, i As Long, t As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    For i = 0 To UBound(bodies)
        t = t + Volume(bodies(i))
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
    vLo = (vProfile + vStub) * (1# - VOL_TOL)
    vHi = (vProfile + vStub) * (1# + VOL_TOL)
    If vGot < vLo Or vGot > vHi Then Fail "the chamber is " & Fmt(vGot) & " m3, outside " & Fmt(vLo) & " .. " & Fmt(vHi) & " m3."
    Note "chamber volume " & Fmt(vGot) & " m3 (profile " & Fmt(vProfile) & " + throat disc " & Fmt(vStub) & ")"

    bx = body.GetBodyBox
    If Abs(bx(0) + CH_A) > BOX_TOL Or Abs(bx(3) - CH_A) > BOX_TOL Or Abs(bx(1) + CH_A) > BOX_TOL Or _
       Abs(bx(4) - CH_A) > BOX_TOL Or Abs(bx(2) - CH_H_LIP) > BOX_TOL Or Abs(bx(5) - zTop) > BOX_TOL Then
        Fail "the solid's box is x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
             ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m."
    End If
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
            bx = face.GetBox
            If Abs(Abs(p(0)) - 1#) < DIR_TOL And Abs(p(3) - CH_A) < FACE_TOL Then
                If Abs(bx(4) - bx(1) - KILN_D) < BOX_TOL Then k = 1       ' the mouth's disc, not the wall round it
            ElseIf Abs(Abs(p(2)) - 1#) < DIR_TOL And Abs(p(5) - zTop) < FACE_TOL Then
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
