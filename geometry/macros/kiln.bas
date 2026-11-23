Attribute VB_Name = "kiln"
'==================================================================
' Rotary kiln CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' ONE closed solid: the gas volume inside the kiln tube of the 5000 t/d
' plant (a plain cylinder, effective inner diameter and length as
' published for the PF5000 line). Nothing structural is modelled: no
' shell, no refractory, no tyres, no drive (CLAUDE.md rule 8).
'
' Coordinates: the kiln axis = z, the back end (towards the kiln inlet
' chamber, where the meal enters) at z = 0, the hood end (the clinker
' leaves, the hot air enters) at z = KILN_L. The solid starts at
' z = KILN_Z0: the kiln inlet chamber's CFD solid carries the tube's
' first KILN_Z0 (its stub, user decision 22 Nov 2026), so the two
' together are KILN_L long, no more. The tube's slope (3 %, the
' feed end up) belongs to how it is installed (plant_geometry.layout
' tilts it); it is not built into the solid, so both ends stay true
' circles and the drawing can measure them.
'
' Boundary faces: kiln_back (z = KILN_Z0, the chamber's kiln_gas_inlet
' face) and kiln_hood (z = KILN_L); the
' wall is everything else. Their positions are coloured for Fluent.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA editor
' File -> Import File... and pick this .bas. Run `main`.
' Outputs geometry\output\2500\kiln.SLDPRT, .step, .stl and
' kiln_build.log (tests/test_plant_geometry.py reads the log).
'==================================================================

Option Explicit

Const KILN_NAME As String = "kiln"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const KILN_D                       As Double  = 4.8          ' effective inner diameter [published, kiln/kiln.md]
Const KILN_L                       As Double  = 60#          ' back end (z = 0) to hood end [cfd_decision, kiln/kiln.md]
Const KILN_Z0                      As Double  = 2.4          ' the solid's back face: the kiln inlet chamber's stub ends here (stub + solid = KILN_L) [derived]
Const KILN_SLOPE                   As Double  = 3#           ' %: the installed slope, not built into the solid [published, kiln/kiln.md]
Const KILN_TRANSITION_L            As Double  = 25#          ' the transition zone from the back end (model split) [model, kiln/kiln.md]
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
Dim R As Double, vKiln As Double
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profile
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
    R = 0.5 * KILN_D
    vKiln = PI * R * R * (KILN_L - KILN_Z0)
    phase = "building the solid"
    Build
    phase = "verifying the solid"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog KILN_NAME & " built, verified and exported"
    ' no message box when OUT_ROOT\quiet.flag exists (tools/sw_run.py kiln_solid.main)
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox KILN_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog KILN_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox KILN_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln"
    End If
End Sub


'==================================================================
' Build: a rectangle (r, z) revolved about the axis
'==================================================================
Private Sub Build()
    Dim planeX0 As SldWorks.Feature
    Dim f As SldWorks.Feature

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

    Set planeX0 = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX0 Is Nothing Then Fail "could not find the default plane whose normal is X."
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX

    Set f = RevolveProfile(planeX0, Array( _
        0#, KILN_Z0, _
        R, KILN_Z0, _
        R, KILN_L, _
        0#, KILN_L), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the kiln profile."

    Note "kiln: D " & Fmt(KILN_D) & " m, L " & Fmt(KILN_L) & " m (the solid from z " & Fmt(KILN_Z0) & _
         ", the chamber's stub before it: " & Fmt(KILN_L - KILN_Z0) & " m), slope " & Fmt(KILN_SLOPE) & _
         " % (installation, not built into the solid), volume " & Fmt(vKiln) & " m3"
    Note "kiln zones (model split, not in the solid): transition " & Fmt(KILN_TRANSITION_L) & _
         " m from the back end, burning " & Fmt(KILN_L - KILN_TRANSITION_L) & " m"
End Sub


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
    If Abs(vGot - vKiln) > VOL_TOL * vKiln Then
        Fail "the kiln is " & Fmt(vGot) & " m3, expected " & Fmt(vKiln) & " m3."
    End If
    Note "kiln volume " & Fmt(vGot) & " m3 (expected " & Fmt(vKiln) & ")"

    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    want(0) = -R: want(1) = -R: want(2) = KILN_Z0: want(3) = R: want(4) = R: want(5) = KILN_L
    For a = 0 To 5
        If Abs(b(a) - want(a)) > BOX_TOL Then Fail "the solid's " & nm(a) & " is " & Fmt(b(a)) & " m but should be " & Fmt(want(a)) & " m."
    Next a
    Note "extent: x " & Fmt(b(0)) & " .. " & Fmt(b(3)) & ", y " & Fmt(b(1)) & " .. " & Fmt(b(4)) & _
         ", z " & Fmt(b(2)) & " .. " & Fmt(b(5)) & " m"
End Sub


'==================================================================
' Boundary faces: the two end planes, found by what they are
'==================================================================
Private Sub TagBoundaryFaces()
    Dim faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface, p As Variant
    Dim i As Long, k As Long
    Dim n(2) As Long, a(2) As Double
    Dim names As Variant

    names = Array("kiln_back", "kiln_hood", "wall")
    faces = TheBody().GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        k = 2
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(p(0)) < DIR_TOL And Abs(p(1)) < DIR_TOL Then
                If Abs(p(5) - KILN_Z0) < 0.0001 Then
                    k = 0
                ElseIf Abs(p(5) - KILN_L) < 0.0001 Then
                    k = 1
                End If
            End If
        End If
        Select Case k
        Case 0: Paint face, 0#, 0.8, 0#
        Case 1: Paint face, 0.9, 0#, 0#
        Case Else: Paint face, 0.7, 0.7, 0.7
        End Select
        n(k) = n(k) + 1
        a(k) = a(k) + face.GetArea
    Next i

    For k = 0 To 1
        If n(k) <> 1 Then Fail "found " & n(k) & " " & names(k) & " faces, expected 1."
        If Abs(a(k) - PI * R * R) > AREA_TOL * PI * R * R Then _
            Fail names(k) & " is " & Fmt(a(k)) & " m2, expected " & Fmt(PI * R * R) & " m2."
        Note "boundary " & names(k) & ": " & Fmt(a(k)) & " m2, colour " & IIf(k = 0, "green", "red")
    Next k
    Note "boundary wall: " & n(2) & " faces, " & Fmt(a(2)) & " m2"
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

    SaveOne outDir & KILN_NAME & ".SLDPRT"
    SaveOne outDir & KILN_NAME & ".step"
    SaveOne outDir & KILN_NAME & ".stl"
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
    Err.Raise vbObjectError + 1, "kiln", msg
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\kiln_build.log"
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


