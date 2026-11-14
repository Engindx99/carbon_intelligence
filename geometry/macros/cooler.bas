Attribute VB_Name = "cooler"
'==================================================================
' Grate cooler CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' ONE closed solid: the gas volume above the grate of the clinker
' cooler of the 5000 t/d plant, the simplest sufficient one
' (geometry/cooler/cooler.md): a box, grate width x grate length x the
' height from the grate to the roof. No grate plates, compartment walls,
' crusher or clinker chute, and the clinker bed is a cell zone in the box
' (set in the solver), not a body (CLAUDE.md rule 8).
'
' Coordinates: x along the grate, x = 0 at the hot end (under the hood,
' where the clinker falls), y across (the axis at y = 0), z up from the
' grate plane (z = 0).
'
' Boundary faces: the floor is split into COOLER_SEGMENTS strips
' (grate_air_1 .. n from the hot end, each the FLS reference cooler's
' undergrate air segment); the roof is split once, at the end of the hood's
' opening (hood_opening, x = 0 .. COOLER_HOOD_L); the rest is wall. The
' vent outlet has no source and is not made. Coloured for Fluent.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA editor
' File -> Import File... and pick this .bas. Run `main`.
' Outputs geometry\output\2500\cooler.SLDPRT, .step, .stl and
' cooler_build.log (tests/test_plant_geometry.py reads the log).
'==================================================================

Option Explicit

Const COOLER_NAME As String = "cooler"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const COOLER_W                     As Double  = 4#           ' grate width [literature, cooler/cooler.md]
Const COOLER_H                     As Double  = 3#           ' grate to roof [literature, cooler/cooler.md]
Const COOLER_SEGMENTS              As Double  = 10#          ' undergrate air segments (FLS) [literature, cooler/cooler.md]
Const COOLER_HOOD_SEGMENTS         As Double  = 2#           ' segments from the hot end under the hood's opening [literature, cooler/cooler.md]
Const COOLER_L                     As Double  = 29.9         ' grate area / width, hot end x = 0 to the cold end [derived]
Const COOLER_SEG_L                 As Double  = 2.99         ' one segment's length [derived]
Const COOLER_HOOD_L                As Double  = 5.98         ' the hood opening's length from x = 0 [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL  As Double = 0.001   ' relative, on the volume
Const AREA_TOL As Double = 0.002   ' relative, on face areas
Const BOX_TOL  As Double = 0.01    ' absolute [m]
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001
Const PI As Double = 3.14159265358979

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean
Dim vBox As Double, nSeg As Long, nHood As Long
Dim uSignZ As Double, vSignZ As Double      ' the z = 0 plane, for the box's sketches
Dim zFloor As Double
Dim uSign As Double, vSign As Double
Dim wRef As Double
Dim wRefSet As Boolean

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
    nSeg = CLng(COOLER_SEGMENTS): nHood = CLng(COOLER_HOOD_SEGMENTS)
    vBox = COOLER_L * COOLER_W * COOLER_H
    phase = "building the solid"
    Build
    phase = "verifying the solid"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog COOLER_NAME & " built, verified and exported"
    MsgBox COOLER_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Cooler"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog COOLER_NAME & " ABORTED while " & phase & ": " & why
    MsgBox COOLER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Cooler"
End Sub


'==================================================================
' Build: the box, then the floor and the roof split into their zones
'==================================================================
Private Sub Build()
    Dim planeZ0 As SldWorks.Feature

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

    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."
    CalibrateSketchAxes planeZ0, 0#, 0#, 0#, uSignZ, vSignZ

    ExtrudeBox planeZ0
    Note "cooler: " & Fmt(COOLER_W) & " m wide, " & Fmt(COOLER_L) & " m long, " & Fmt(COOLER_H) & _
         " m high, volume " & Fmt(vBox) & " m3 (no bed, plates, walls or chute)"

    ' the floor in nSeg strips, at x = i * segment length
    SplitFace planeZ0, 0#, COOLER_SEG_L, nSeg - 1, nSeg, "the floor"
    ' the roof once, where the hood's opening ends
    SplitFace planeZ0, COOLER_H, COOLER_HOOD_L, 1, 2, "the roof"
    Note "cooler: " & nSeg & " segments of " & Fmt(COOLER_SEG_L) & " m (grate_air_1 .. " & nSeg & _
         " from the hot end), hood opening " & nHood & " segments, x 0 .. " & Fmt(COOLER_HOOD_L) & " m"
End Sub


' The rectangle on the z = 0 plane, extruded up to COOLER_H.
Private Sub ExtrudeBox(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim hw As Double, k As Long, i As Long
    Dim px(3) As Double, py(3) As Double
    Dim zlo As Double, zhi As Double

    hw = 0.5 * COOLER_W
    px(0) = 0#: py(0) = -hw
    px(1) = COOLER_L: py(1) = -hw
    px(2) = COOLER_L: py(2) = hw
    px(3) = 0#: py(3) = hw
    uSign = uSignZ: vSign = vSignZ

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the box's sketch on the z = 0 plane."
    wRefSet = False
    For i = 0 To 3
        G2S sk, px(i), py(i), 0#, u0, v0
        G2S sk, px((i + 1) Mod 4), py((i + 1) Mod 4), 0#, u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the box's rectangle."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, COOLER_H, 0.01, _
            False, False, False, False, 0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            If BodyCount() = 1 Then
                ZRange zlo, zhi
                If Abs(zlo) < BOX_TOL And Abs(zhi - COOLER_H) < BOX_TOL Then
                    Note "box extruded " & IIf(k = 0, "forward", "reversed") & ": z " & Fmt(zlo) & " .. " & Fmt(zhi) & " m"
                    Exit Sub
                End If
            End If
            Note "the box extruded the wrong way (z " & Fmt(zlo) & " .. " & Fmt(zhi) & "); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k
    Fail "the box could not be extruded to z = " & Fmt(COOLER_H) & " m in either direction."
End Sub


Private Sub ZRange(ByRef zlo As Double, ByRef zhi As Double)
    Dim body As SldWorks.Body2
    Dim px As Double, py As Double, pz As Double
    Set body = TheBody()
    If Not body.GetExtremePoint(0#, 0#, -1#, px, py, pz) Then Fail "GetExtremePoint failed (z min)."
    zlo = pz
    If Not body.GetExtremePoint(0#, 0#, 1#, px, py, pz) Then Fail "GetExtremePoint failed (z max)."
    zhi = pz
End Sub


' Split the planar face at height z (normal along z) by nLines lines across
' it at x = i * pitch (i = 1 .. nLines), a sketch on the z = 0 plane
' projected onto that face alone. Every way the projection can be asked
' for is tried; the one that leaves nPieces faces at that height is kept.
Private Sub SplitFace(pl As SldWorks.Feature, ByVal z As Double, ByVal pitch As Double, _
                      ByVal nLines As Long, ByVal nPieces As Long, ByVal what As String)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim sd As SldWorks.SelectData, ent As SldWorks.Entity
    Dim face As SldWorks.Face2
    Dim i As Long, k As Long, hw As Double
    Dim dirOpt As Boolean, flipOpt As Boolean, mk As Long

    hw = 0.5 * COOLER_W
    uSign = uSignZ: vSign = vSignZ
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch that splits " & what & "."
    wRefSet = False
    For i = 1 To nLines
        G2S sk, i * pitch, -hw, 0#, u0, v0
        G2S sk, i * pitch, hw, 0#, u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the lines that split " & what & "."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    ' IModelDoc2.InsertSplitLineProject(IsDirectional, FlipDir): the sketch
    ' selected with mark 4, the face with mark 1 (SolidWorks API help); a Sub,
    ' so the outcome is read from the faces. Both face marks are tried.
    For k = 0 To 7
        dirOpt = ((k And 1) <> 0): flipOpt = ((k And 2) <> 0): mk = IIf((k And 4) <> 0, 0, 1)
        Set face = LevelFace(z)
        If face Is Nothing Then Fail "found no planar face at z = " & Fmt(z) & " m to split (" & what & ")."
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
            If PlaneFaceCount(z) = nPieces Then
                Note "split " & what & " into " & nPieces & " faces (projection " & dirOpt & ", " & flipOpt & ", face mark " & mk & ")"
                Exit Sub
            End If
        End If
        Set f = swModel.FeatureByPositionReverse(0)
        If Not f Is Nothing Then
            If f.GetTypeName2 = "SplitLine" Then
                Note "split of " & what & " gave " & PlaneFaceCount(z) & " faces, not " & nPieces & " (projection " & dirOpt & ", " & flipOpt & ", face mark " & mk & "); undone"
                f.Select2 False, 0
                swModel.EditDelete
                swModel.ClearSelection2 True
            End If
        End If
    Next k
    Fail "could not split " & what & " into " & nPieces & " faces: InsertSplitLineProject changed nothing in any of its eight forms."
End Sub


' The planar face with its normal along z lying at height z (the first).
Private Function LevelFace(ByVal z As Double) As SldWorks.Face2
    Dim faces As Variant, i As Long, p As Variant
    Dim face As SldWorks.Face2, surf As SldWorks.Surface
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(Abs(p(2)) - 1#) < DIR_TOL And Abs(p(5) - z) < 0.0001 Then
                Set LevelFace = face
                Exit Function
            End If
        End If
    Next i
End Function


Private Function PlaneFaceCount(ByVal z As Double) As Long
    Dim faces As Variant, i As Long, p As Variant, n As Long
    Dim face As SldWorks.Face2, surf As SldWorks.Surface
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(Abs(p(2)) - 1#) < DIR_TOL And Abs(p(5) - z) < 0.0001 Then n = n + 1
        End If
    Next i
    PlaneFaceCount = n
End Function


Private Function BodyCount() As Long
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then BodyCount = 0 Else BodyCount = UBound(bodies) + 1
End Function


'==================================================================
' Verify: one body, closed, the right volume and box
'==================================================================
Private Function TheBody() As SldWorks.Body2
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) <> 0 Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not one."
    Set TheBody = bodies(0)
End Function


Private Sub Verify()
    Dim body As SldWorks.Body2
    Dim edges As Variant, edge As SldWorks.Edge, adj As Variant
    Dim mp As Variant, vGot As Double, i As Long
    Dim b(5) As Double, d(2) As Double, want(5) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long, nm As Variant

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

    mp = body.GetMassProperties(1#)
    vGot = mp(3)
    If Abs(vGot - vBox) > VOL_TOL * vBox Then Fail "the cooler is " & Fmt(vGot) & " m3, expected " & Fmt(vBox) & " m3."
    Note "cooler volume " & Fmt(vGot) & " m3 (expected " & Fmt(vBox) & ")"

    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    want(0) = 0#: want(1) = -0.5 * COOLER_W: want(2) = 0#
    want(3) = COOLER_L: want(4) = 0.5 * COOLER_W: want(5) = COOLER_H
    For a = 0 To 5
        If Abs(b(a) - want(a)) > BOX_TOL Then Fail "the solid's " & nm(a) & " is " & Fmt(b(a)) & " m but should be " & Fmt(want(a)) & " m."
    Next a
    Note "extent: x " & Fmt(b(0)) & " .. " & Fmt(b(3)) & ", y " & Fmt(b(1)) & " .. " & Fmt(b(4)) & _
         ", z " & Fmt(b(2)) & " .. " & Fmt(b(5)) & " m"
End Sub


'==================================================================
' Boundary faces: found by what they are (a level plane and where it lies)
'==================================================================
Private Sub TagBoundaryFaces()
    Dim faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface, p As Variant, bx As Variant
    Dim i As Long, k As Long, seg As Long, cx As Double
    Dim nG(40) As Long, aG(40) As Double
    Dim nHoodF As Long, aHood As Double, nWall As Long, aWall As Double
    Dim wantSeg As Double, wantHood As Double, wantWall As Double

    If nSeg > 40 Then Fail "more than 40 segments."
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        k = 0                                   ' 0 wall, 1 grate, 2 hood opening
        If surf.IsPlane Then
            p = surf.PlaneParams
            bx = face.GetBox
            cx = 0.5 * (bx(0) + bx(3))
            If Abs(Abs(p(2)) - 1#) < DIR_TOL Then
                If Abs(p(5)) < 0.0001 Then
                    k = 1
                    seg = Int(cx / COOLER_SEG_L) + 1
                ElseIf Abs(p(5) - COOLER_H) < 0.0001 And bx(3) < COOLER_HOOD_L + 0.001 Then
                    k = 2
                End If
            End If
        End If
        Select Case k
        Case 1
            If seg < 1 Or seg > nSeg Then Fail "a floor face lies outside the segments (centre x " & Fmt(cx) & " m)."
            nG(seg) = nG(seg) + 1: aG(seg) = aG(seg) + face.GetArea
            If seg Mod 2 = 1 Then Paint face, 0#, 0.8, 0# Else Paint face, 0#, 0.55, 0.35
        Case 2
            nHoodF = nHoodF + 1: aHood = aHood + face.GetArea
            Paint face, 0.9, 0#, 0#
        Case Else
            nWall = nWall + 1: aWall = aWall + face.GetArea
            Paint face, 0.7, 0.7, 0.7
        End Select
    Next i

    wantSeg = COOLER_SEG_L * COOLER_W
    wantHood = COOLER_HOOD_L * COOLER_W
    wantWall = 2# * COOLER_L * COOLER_H + 2# * COOLER_W * COOLER_H + COOLER_W * (COOLER_L - COOLER_HOOD_L)
    For seg = 1 To nSeg
        If nG(seg) <> 1 Then Fail "found " & nG(seg) & " grate_air_" & seg & " faces, expected 1."
        If Abs(aG(seg) - wantSeg) > AREA_TOL * wantSeg Then Fail "grate_air_" & seg & " is " & Fmt(aG(seg)) & " m2, expected " & Fmt(wantSeg) & " m2."
        Note "boundary grate_air_" & seg & ": " & Fmt(aG(seg)) & " m2"
    Next seg
    If nHoodF <> 1 Then Fail "found " & nHoodF & " hood_opening faces, expected 1."
    If Abs(aHood - wantHood) > AREA_TOL * wantHood Then Fail "hood_opening is " & Fmt(aHood) & " m2, expected " & Fmt(wantHood) & " m2."
    Note "boundary hood_opening: " & Fmt(aHood) & " m2, colour red"
    If Abs(aWall - wantWall) > AREA_TOL * wantWall Then Fail "the wall is " & Fmt(aWall) & " m2, expected " & Fmt(wantWall) & " m2."
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

    SaveOne outDir & COOLER_NAME & ".SLDPRT"
    SaveOne outDir & COOLER_NAME & ".step"
    SaveOne outDir & COOLER_NAME & ".stl"
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
    Err.Raise vbObjectError + 1, "cooler", msg
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\cooler_build.log"
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


