Attribute VB_Name = "cooler"
'==================================================================
' Grate cooler CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' The gas volume of the clinker cooler of the 5000 t/d plant
' (geometry/cooler/cooler.md, cooler_cfd.md), plant_geometry.cooler_cfd():
' the casing over the grate, grate width x grate length x the height from
' the grate to the roof, as TWO bodies sharing the bed's top:
'   bed        the clinker bed, bed_h deep over the floor: a porous cell
'              zone in the solver (Ergun; the clinker moves at the grate
'              speed);
'   freeboard  the air over it, up to the roof, with the vent duct.
' The floor: the fixed inclined inlet grate (CIS) over the first segment,
' falling to the flat grate, then the flat grate. No grate plates,
' compartment walls, crusher or clinker chute (CLAUDE.md rule 8;
' cooler_cfd.md says why).
'
' Coordinates: x along the grate, x = 0 at the hot end (under the hood,
' where the clinker falls), y across (the axis at y = 0), z up from the
' flat grate plane (z = 0).
'
' Boundary faces: grate_air_1 (the inclined inlet) .. grate_air_n (flat
' strips), each the FLS reference cooler's undergrate air segment; on the
' flat roof hood_1 and hood_2 (the hood's opening, one segment each, split
' off the roof: the flame volume's flat hood floor, its secondary_air_in and
' tertiary_supply_in, lies on them), the rest wall; the
' vent duct off the roof near the middle, its end face vent_out; bed_top
' the two bodies' shared faces (an interior); the clinker outlet past the
' grate's end: the bed's end clinker_out (shared, an interior: the clinker
' leaves the porous zone there) and the roller breaker's deck hrb_deck
' under the freeboard carried on over it (user, 23 Nov 2026). Coloured for
' Fluent.
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
Const COOLER_CIS_SEGMENTS          As Double  = 1#           ' segments under the inclined inlet grate (grate_air_1) [model, cooler/cooler.md]
Const COOLER_CIS_L                 As Double  = 2.99         ' the inclined inlet's length along x [derived]
Const COOLER_CIS_RISE              As Double  = 0.635544     ' the inlet grate's height at x = 0 over the flat grate [derived]
Const COOLER_CIS_AREA              As Double  = 12.227194    ' the inclined inlet face (grate_air_1) [derived]
Const COOLER_BED_H                 As Double  = 0.409217     ' the clinker bed's depth over the floor, along z [derived]
Const COOLER_VENT_D                As Double  = 2.797401     ' the vent duct's bore: the vent air at vent_T and vent_velocity [derived]
Const COOLER_VENT_X                As Double  = 17.94        ' the vent duct's axis, x [derived]
Const COOLER_VENT_L                As Double  = 8.392202     ' the vent duct's run up off the roof to vent_out [derived]
Const COOLER_BED_V                 As Double  = 48.942299    ' the bed body's volume [derived]
Const COOLER_FB_V                  As Double  = 405.636413   ' the freeboard body's volume (the vent duct included) [derived]
Const COOLER_BED_TOP_A             As Double  = 119.867194   ' the bed's top (the two bodies' shared faces) [derived]
Const COOLER_BED_WALL_A            As Double  = 26.108016    ' the bed body's walls [derived]
Const COOLER_FB_WALL_A             As Double  = 376.13657    ' the freeboard body's walls (the duct's included) [derived]
Const COOLER_HRB_L                 As Double  = 4#           ' the HRB deck past the grate's end (the clinker outlet) [derived]
Const COOLER_CLINKER_OUT_A         As Double  = 1.636866     ' the bed's end at x = L (clinker_out) [derived]
Const COOLER_HRB_DECK_A            As Double  = 16#          ' the HRB deck's top (hrb_deck) [derived]
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
Dim nSeg As Long, nHood As Long
Dim uSignZ As Double, vSignZ As Double      ' the z = 0 plane (the floor and roof splits)
Dim uSignY As Double, vSignY As Double      ' the y = 0 plane (the side profiles)
Dim uSignR As Double, vSignR As Double      ' the roof plane z = COOLER_H (the vent)
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
    If CLng(COOLER_CIS_SEGMENTS) <> 1 Then Fail "the inclined inlet is one segment (grate_air_1) in this macro."
    If nHood <> 2 Then Fail "the hood's opening is two segments (hood_1, hood_2) in this macro."
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
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox COOLER_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Cooler"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog COOLER_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox COOLER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Cooler"
End Sub


'==================================================================
' Build: the bed, the freeboard on it, the vent duct, then the floor
' and the roof split into their zones
'==================================================================
Private Sub Build()
    Dim planeZ0 As SldWorks.Feature, planeY0 As SldWorks.Feature, planeRoof As SldWorks.Feature
    Dim px(8) As Double, pz(8) As Double

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

    ' every plane is measured while the part is still empty (the probes need it)
    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."
    Set planeY0 = FindPlaneWithNormal(0#, 1#, 0#)
    If planeY0 Is Nothing Then Fail "could not find the default plane whose normal is Y."
    CalibrateSketchAxes planeZ0, 0#, 0#, 0#, uSignZ, vSignZ
    CalibrateSketchAxes planeY0, 0#, 0#, 0#, uSignY, vSignY
    Set planeRoof = OffsetPlane(planeZ0, 0#, 0#, COOLER_H, uSignR, vSignR)

    ' the bed: the floor (the inlet grate's slope, then flat) and the same line bed_h up
    px(0) = 0#: pz(0) = COOLER_CIS_RISE
    px(1) = COOLER_CIS_L: pz(1) = 0#
    px(2) = COOLER_L: pz(2) = 0#
    px(3) = COOLER_L: pz(3) = COOLER_BED_H
    px(4) = COOLER_CIS_L: pz(4) = COOLER_BED_H
    px(5) = 0#: pz(5) = COOLER_CIS_RISE + COOLER_BED_H
    ExtrudeSide planeY0, px, pz, 6, True, "the bed"
    If BodyCount() <> 1 Then Fail "the bed left " & BodyCount() & " bodies, expected 1."
    ' the flat floor in strips at x = CIS_L + i * segment length (before the
    ' freeboard: its HRB deck is level at z = 0 too)
    SplitFace planeZ0, 0#, COOLER_CIS_L, COOLER_SEG_L, nSeg - 2, nSeg - 1, "the flat floor"

    ' the freeboard: the bed's top to the flat roof, a body of its own, on
    ' past the grate's end over the HRB deck (the clinker outlet: the bed's
    ' end clinker_out, the deck's top hrb_deck)
    px(0) = 0#: pz(0) = COOLER_CIS_RISE + COOLER_BED_H
    px(1) = COOLER_CIS_L: pz(1) = COOLER_BED_H
    px(2) = COOLER_L: pz(2) = COOLER_BED_H
    px(3) = COOLER_L: pz(3) = 0#
    px(4) = COOLER_L + COOLER_HRB_L: pz(4) = 0#
    px(5) = COOLER_L + COOLER_HRB_L: pz(5) = COOLER_H
    px(6) = 0#: pz(6) = COOLER_H
    ExtrudeSide planeY0, px, pz, 7, False, "the freeboard"
    If BodyCount() <> 2 Then Fail "the freeboard left " & BodyCount() & " bodies, expected the bed and the freeboard."
    Note "cooler: " & Fmt(COOLER_W) & " m wide, " & Fmt(COOLER_L) & " m long, " & Fmt(COOLER_H) & _
         " m high; inlet grate " & Fmt(COOLER_CIS_L) & " m, rising " & Fmt(COOLER_CIS_RISE) & _
         " m to the hot end; bed " & Fmt(COOLER_BED_H) & " m deep"

    ' the roof split across at one and two segments: hood_1, hood_2 (on the
    ' flame volume's flat hood floor, its two inlets: the volumes meet there)
    ' and the rest
    SplitFace planeRoof, COOLER_H, 0#, COOLER_SEG_L, 2, 3, "the roof", True
    AddVent planeRoof
    Note "vent: bore " & Fmt(COOLER_VENT_D) & " m at x = " & Fmt(COOLER_VENT_X) & " m, run " & Fmt(COOLER_VENT_L) & " m up"

    Note "cooler: " & nSeg & " segments of " & Fmt(COOLER_SEG_L) & " m (grate_air_1 .. " & nSeg & _
         " from the hot end), hood opening " & nHood & " segments, x 0 .. " & Fmt(COOLER_HOOD_L) & " m"
End Sub


' A side profile (x, z points, in order) on the y = 0 plane, extruded
' mid-plane across the grate's width; merge False makes it a body of its own.
Private Sub ExtrudeSide(pl As SldWorks.Feature, px() As Double, pz() As Double, ByVal n As Long, _
                        ByVal merge As Boolean, ByVal what As String)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim i As Long

    uSign = uSignY: vSign = vSignY
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch of " & what & " on the y = 0 plane."
    wRefSet = False
    For i = 0 To n - 1
        G2S sk, px(i), 0#, pz(i), u0, v0
        G2S sk, px((i + 1) Mod n), 0#, pz((i + 1) Mod n), u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then Fail "CreateLine failed on the profile of " & what & "."
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondMidPlane, swEndCondBlind, _
        COOLER_W, 0.01, _
        False, False, False, False, _
        0#, 0#, _
        False, False, False, False, _
        merge, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail what & " could not be extruded."
End Sub


' The vent duct: a circle on the roof plane at (VENT_X, 0), extruded
' VENT_L up and merged into the freeboard. Which way is up on that plane
' is not ours to choose, so the freeboard's top says which way it went.
Private Sub AddVent(pl As SldWorks.Feature)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, zlo As Double, zhi As Double
    Dim k As Long, bodies As Variant, tools(0) As Object, b As SldWorks.Body2, i As Long

    uSign = uSignR: vSign = vSignR
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the vent's sketch on the roof plane."
    wRefSet = False
    G2S sk, COOLER_VENT_X, 0#, COOLER_H, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, 0.5 * COOLER_VENT_D) Is Nothing Then Fail "CreateCircleByRadius failed on the vent."
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            COOLER_VENT_L, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True
        If Not f Is Nothing Then
            ' merged by the extrusion, or left a third body touching the roof: added here
            If BodyCount() = 3 Then
                bodies = swPart.GetBodies2(swSolidBody, True)
                For i = 0 To 2
                    Set b = bodies(i)
                    BodyZRange b, zlo, zhi
                    If Abs(zlo - COOLER_H) < BOX_TOL Then Set tools(0) = b
                Next i
                If Not tools(0) Is Nothing Then
                    swFeat.InsertCombineFeature SWBODYADD, GasBody(), tools
                    Note "vent: its body added to the freeboard"
                End If
            End If
            If BodyCount() = 2 Then
                BodyZRange GasBody(), zlo, zhi
                If Abs(zhi - (COOLER_H + COOLER_VENT_L)) < BOX_TOL Then
                    Note "vent extruded " & IIf(k = 0, "forward", "reversed") & ": the freeboard's top at z " & Fmt(zhi) & " m"
                    Exit Sub
                End If
            End If
            Note "the vent extruded the wrong way (" & BodyCount() & " bodies); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set tools(0) = Nothing
        End If
    Next k
    Fail "the vent duct could not be extruded up off the roof in either direction."
End Sub


Private Sub BodyZRange(body As SldWorks.Body2, ByRef zlo As Double, ByRef zhi As Double)
    Dim px As Double, py As Double, pz As Double
    If Not body.GetExtremePoint(0#, 0#, -1#, px, py, pz) Then Fail "GetExtremePoint failed (z min)."
    zlo = pz
    If Not body.GetExtremePoint(0#, 0#, 1#, px, py, pz) Then Fail "GetExtremePoint failed (z max)."
    zhi = pz
End Sub


' Split the planar face at height z (normal along z) by nLines lines across
' it at x = x0 + i * pitch (i = 1 .. nLines), a sketch on the z = 0 plane
' projected onto that face alone. Every way the projection can be asked
' for is tried; the one that leaves nPieces faces at that height is kept.
Private Sub SplitFace(pl As SldWorks.Feature, ByVal z As Double, ByVal x0 As Double, ByVal pitch As Double, _
                      ByVal nLines As Long, ByVal nPieces As Long, ByVal what As String, _
                      Optional ByVal onRoof As Boolean = False)
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim sd As SldWorks.SelectData, ent As SldWorks.Entity
    Dim face As SldWorks.Face2
    Dim i As Long, k As Long, hw As Double, nBodies As Long
    Dim dirOpt As Boolean, flipOpt As Boolean, mk As Long

    If nLines < 1 Then Exit Sub
    nBodies = BodyCount()
    hw = 0.5 * COOLER_W
    uSign = uSignZ: vSign = vSignZ
    If onRoof Then uSign = uSignR: vSign = vSignR
    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch that splits " & what & "."
    wRefSet = False
    For i = 1 To nLines
        G2S sk, x0 + i * pitch, -hw, 0#, u0, v0
        G2S sk, x0 + i * pitch, hw, 0#, u1, v1
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
        If BodyCount() = nBodies Then
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


' Every face of every body.
Private Function AllFaces() As Collection
    Dim bodies As Variant, i As Long, j As Long, faces As Variant, b As SldWorks.Body2
    Dim c As New Collection
    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        For i = 0 To UBound(bodies)
            Set b = bodies(i)
            faces = b.GetFaces
            If Not IsEmpty(faces) Then
                For j = 0 To UBound(faces)
                    c.Add faces(j)
                Next j
            End If
        Next i
    End If
    Set AllFaces = c
End Function


' A planar face with its normal along z lying at height z, of any body.
Private Function IsLevelAt(face As SldWorks.Face2, ByVal z As Double) As Boolean
    Dim surf As SldWorks.Surface, p As Variant
    Set surf = face.GetSurface
    If surf.IsPlane Then
        p = surf.PlaneParams
        IsLevelAt = (Abs(Abs(p(2)) - 1#) < DIR_TOL And Abs(p(5) - z) < 0.0001)
    End If
End Function


Private Function LevelFace(ByVal z As Double) As SldWorks.Face2
    Dim face As Variant, f As SldWorks.Face2
    For Each face In AllFaces()
        Set f = face
        If IsLevelAt(f, z) Then
            Set LevelFace = f
            Exit Function
        End If
    Next face
End Function


Private Function PlaneFaceCount(ByVal z As Double) As Long
    Dim face As Variant, f As SldWorks.Face2, n As Long
    For Each face In AllFaces()
        Set f = face
        If IsLevelAt(f, z) Then n = n + 1
    Next face
    PlaneFaceCount = n
End Function


Private Function BodyCount() As Long
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then BodyCount = 0 Else BodyCount = UBound(bodies) + 1
End Function


'==================================================================
' The two bodies, told apart by their tops: the freeboard reaches the
' roof, the bed does not
'==================================================================
Private Function PickBody(ByVal gas As Boolean) As SldWorks.Body2
    Dim bodies As Variant, i As Long, b As SldWorks.Body2, zlo As Double, zhi As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    For i = 0 To UBound(bodies)
        Set b = bodies(i)
        BodyZRange b, zlo, zhi
        If (zhi > COOLER_H - BOX_TOL) = gas Then
            Set PickBody = b
            Exit Function
        End If
    Next i
    Fail "found no " & IIf(gas, "freeboard", "bed") & " body."
End Function

Private Function GasBody() As SldWorks.Body2
    Set GasBody = PickBody(True)
End Function

Private Function BedBody() As SldWorks.Body2
    Set BedBody = PickBody(False)
End Function


'==================================================================
' Verify: two bodies, each closed, the right volumes and boxes
'==================================================================
Private Sub Verify()
    If BodyCount() <> 2 Then Fail "the part has " & BodyCount() & " bodies, not the bed and the freeboard."
    CheckBody BedBody(), "bed", COOLER_BED_V, 0#, COOLER_CIS_RISE + COOLER_BED_H, COOLER_L
    CheckBody GasBody(), "freeboard", COOLER_FB_V, 0#, COOLER_H + COOLER_VENT_L, COOLER_L + COOLER_HRB_L
End Sub


Private Sub CheckBody(body As SldWorks.Body2, ByVal what As String, ByVal vWant As Double, _
                      ByVal zlo As Double, ByVal zhi As Double, ByVal xhi As Double)
    Dim edges As Variant, edge As SldWorks.Edge, adj As Variant
    Dim mp As Variant, vGot As Double, i As Long
    Dim b(5) As Double, d(2) As Double, want(5) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long, nm As Variant

    edges = body.GetEdges
    If IsEmpty(edges) Then Fail "the " & what & " has no edges."
    For i = 0 To UBound(edges)
        Set edge = edges(i)
        adj = edge.GetTwoAdjacentFaces2
        If IsEmpty(adj) Then Fail "the " & what & "'s edge " & i & " reports no adjacent faces; it is not closed."
        If adj(0) Is Nothing Or adj(1) Is Nothing Then Fail "the " & what & "'s edge " & i & " has only one adjacent face; it is an open shell."
    Next i
    Note what & ": closed manifold solid, " & (UBound(edges) + 1) & " edges, each with two faces"

    mp = body.GetMassProperties(1#)
    vGot = mp(3)
    If Abs(vGot - vWant) > VOL_TOL * vWant Then Fail "the " & what & " is " & Fmt(vGot) & " m3, expected " & Fmt(vWant) & " m3."
    Note what & " volume " & Fmt(vGot) & " m3 (expected " & Fmt(vWant) & ")"

    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    want(0) = 0#: want(1) = -0.5 * COOLER_W: want(2) = zlo
    want(3) = xhi: want(4) = 0.5 * COOLER_W: want(5) = zhi
    For a = 0 To 5
        If Abs(b(a) - want(a)) > BOX_TOL Then Fail "the " & what & "'s " & nm(a) & " is " & Fmt(b(a)) & " m but should be " & Fmt(want(a)) & " m."
    Next a
    Note what & " extent: x " & Fmt(b(0)) & " .. " & Fmt(b(3)) & ", y " & Fmt(b(1)) & " .. " & Fmt(b(4)) & _
         ", z " & Fmt(b(2)) & " .. " & Fmt(b(5)) & " m"
End Sub


'==================================================================
' Boundary faces: found by what they are (a plane, where it lies, which
' body it bounds)
'==================================================================
Private Sub TagBoundaryFaces()
    Dim faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface, p As Variant, bx As Variant
    Dim i As Long, k As Long, seg As Long, cx As Double, pass As Long, body As SldWorks.Body2
    Dim nG(40) As Long, aG(40) As Double
    Dim nH(2) As Long, aH(2) As Double, nVent As Long, aVent As Double
    Dim nTop(1) As Long, aTop(1) As Double, nWall(1) As Long, aWall(1) As Double
    Dim nOut(1) As Long, aOut(1) As Double, nDeck As Long, aDeck As Double
    Dim zTop As Double, aWant As Double, wantVent As Double, horiz As Boolean, flat As Boolean

    If nSeg > 40 Then Fail "more than 40 segments."
    zTop = COOLER_CIS_RISE + COOLER_BED_H
    For pass = 0 To 1                                ' 0 the bed, 1 the freeboard
        If pass = 0 Then Set body = BedBody() Else Set body = GasBody()
        faces = body.GetFaces
        For i = 0 To UBound(faces)
            Set face = faces(i)
            Set surf = face.GetSurface
            bx = face.GetBox
            cx = 0.5 * (bx(0) + bx(3))
            k = 0                                    ' 0 wall, 1 grate, 2 hood, 3 vent_out, 4 bed_top, 5 clinker_out, 6 hrb_deck
            If surf.IsPlane Then
                p = surf.PlaneParams
                ' the bed's end at the grate's end (both bodies): clinker_out
                If Abs(Abs(p(0)) - 1#) < DIR_TOL And Abs(bx(0) - COOLER_L) < 0.001 And Abs(bx(3) - COOLER_L) < 0.001 _
                   And bx(5) < COOLER_BED_H + 0.001 Then k = 5
                flat = (Abs(p(2)) > 0.5)             ' the floor, the bed's top, the roof, the vent's end
                horiz = (Abs(Abs(p(2)) - 1#) < DIR_TOL)
                If k = 5 Then
                ElseIf flat And pass = 0 Then
                    If bx(2) < 0.001 And bx(5) < COOLER_CIS_RISE + 0.001 Then     ' on the grate (z = 0 .. the inlet's rise)
                        k = 1
                        seg = Int(cx / COOLER_SEG_L) + 1
                    ElseIf bx(2) > COOLER_BED_H - 0.001 Then
                        k = 4
                    End If
                ElseIf flat And pass = 1 Then
                    If horiz And bx(5) < 0.001 And bx(0) > COOLER_L - 0.001 Then
                        k = 6
                    ElseIf horiz And Abs(p(5) - COOLER_H) < 0.0001 And bx(3) < COOLER_SEG_L + 0.001 Then
                        k = 2: seg = 1
                    ElseIf horiz And Abs(p(5) - COOLER_H) < 0.0001 And bx(0) > COOLER_SEG_L - 0.001 And bx(3) < 2# * COOLER_SEG_L + 0.001 Then
                        k = 2: seg = 2
                    ElseIf horiz And Abs(p(5) - (COOLER_H + COOLER_VENT_L)) < 0.0001 Then
                        k = 3
                    ElseIf bx(5) < zTop + 0.001 Then
                        k = 4
                    End If
                End If
            End If
            Select Case k
            Case 1
                If seg < 1 Or seg > nSeg Then Fail "a floor face lies outside the segments (centre x " & Fmt(cx) & " m)."
                nG(seg) = nG(seg) + 1: aG(seg) = aG(seg) + face.GetArea
                If seg Mod 2 = 1 Then Paint face, 0#, 0.8, 0# Else Paint face, 0#, 0.55, 0.35
            Case 2
                nH(seg) = nH(seg) + 1: aH(seg) = aH(seg) + face.GetArea
                If seg = 1 Then Paint face, 0.9, 0#, 0#, 1# Else Paint face, 0.9, 0.45, 0#, 1#
            Case 3
                nVent = nVent + 1: aVent = aVent + face.GetArea
                Paint face, 0#, 0.3, 0.9
            Case 5
                nOut(pass) = nOut(pass) + 1: aOut(pass) = aOut(pass) + face.GetArea
                Paint face, 0.95, 0.2, 0.6
            Case 6
                nDeck = nDeck + 1: aDeck = aDeck + face.GetArea
                Paint face, 0.35, 0.35, 0.4
            Case 4
                nTop(pass) = nTop(pass) + 1: aTop(pass) = aTop(pass) + face.GetArea
                Paint face, 0.55, 0.35, 0.15
            Case Else
                nWall(pass) = nWall(pass) + 1: aWall(pass) = aWall(pass) + face.GetArea
                If pass = 0 Then Paint face, 0.5, 0.5, 0.5 Else Paint face, 0.7, 0.7, 0.7
            End Select
        Next i
    Next pass

    For seg = 1 To nSeg
        If seg = 1 Then aWant = COOLER_CIS_AREA Else aWant = COOLER_SEG_L * COOLER_W
        If nG(seg) <> 1 Then Fail "found " & nG(seg) & " grate_air_" & seg & " faces, expected 1."
        If Abs(aG(seg) - aWant) > AREA_TOL * aWant Then Fail "grate_air_" & seg & " is " & Fmt(aG(seg)) & " m2, expected " & Fmt(aWant) & " m2."
        Note "boundary grate_air_" & seg & ": " & Fmt(aG(seg)) & " m2"
    Next seg
    aWant = COOLER_SEG_L * COOLER_W
    For seg = 1 To 2
        If nH(seg) <> 1 Then Fail "found " & nH(seg) & " hood_" & seg & " faces, expected 1."
        If Abs(aH(seg) - aWant) > AREA_TOL * aWant Then Fail "hood_" & seg & " is " & Fmt(aH(seg)) & " m2, expected " & Fmt(aWant) & " m2."
        Note "boundary hood_" & seg & ": " & Fmt(aH(seg)) & " m2"
    Next seg
    wantVent = 0.25 * PI * COOLER_VENT_D ^ 2
    If nVent <> 1 Then Fail "found " & nVent & " vent_out faces, expected 1."
    If Abs(aVent - wantVent) > AREA_TOL * wantVent Then Fail "vent_out is " & Fmt(aVent) & " m2, expected " & Fmt(wantVent) & " m2."
    Note "boundary vent_out: " & Fmt(aVent) & " m2"
    For pass = 0 To 1
        If nTop(pass) <> 2 Then Fail "found " & nTop(pass) & " bed_top faces on the " & IIf(pass = 0, "bed", "freeboard") & ", expected 2."
        If Abs(aTop(pass) - COOLER_BED_TOP_A) > AREA_TOL * COOLER_BED_TOP_A Then _
            Fail "bed_top on the " & IIf(pass = 0, "bed", "freeboard") & " is " & Fmt(aTop(pass)) & " m2, expected " & Fmt(COOLER_BED_TOP_A) & " m2."
    Next pass
    Note "boundary bed_top: " & Fmt(aTop(0)) & " m2 (bed), " & Fmt(aTop(1)) & " m2 (freeboard)"
    For pass = 0 To 1
        If nOut(pass) <> 1 Then Fail "found " & nOut(pass) & " clinker_out faces on the " & IIf(pass = 0, "bed", "freeboard") & ", expected 1."
        If Abs(aOut(pass) - COOLER_CLINKER_OUT_A) > AREA_TOL * COOLER_CLINKER_OUT_A Then _
            Fail "clinker_out on the " & IIf(pass = 0, "bed", "freeboard") & " is " & Fmt(aOut(pass)) & " m2, expected " & Fmt(COOLER_CLINKER_OUT_A) & " m2."
    Next pass
    Note "boundary clinker_out: " & Fmt(aOut(0)) & " m2 (bed), " & Fmt(aOut(1)) & " m2 (freeboard)"
    If nDeck <> 1 Then Fail "found " & nDeck & " hrb_deck faces, expected 1."
    If Abs(aDeck - COOLER_HRB_DECK_A) > AREA_TOL * COOLER_HRB_DECK_A Then Fail "hrb_deck is " & Fmt(aDeck) & " m2, expected " & Fmt(COOLER_HRB_DECK_A) & " m2."
    Note "boundary hrb_deck: " & Fmt(aDeck) & " m2"
    If Abs(aWall(0) - COOLER_BED_WALL_A) > AREA_TOL * COOLER_BED_WALL_A Then Fail "the bed's wall is " & Fmt(aWall(0)) & " m2, expected " & Fmt(COOLER_BED_WALL_A) & " m2."
    Note "boundary wall (bed): " & nWall(0) & " faces, " & Fmt(aWall(0)) & " m2"
    If Abs(aWall(1) - COOLER_FB_WALL_A) > AREA_TOL * COOLER_FB_WALL_A Then Fail "the freeboard's wall is " & Fmt(aWall(1)) & " m2, expected " & Fmt(COOLER_FB_WALL_A) & " m2."
    Note "boundary wall (freeboard): " & nWall(1) & " faces, " & Fmt(aWall(1)) & " m2"
    swModel.ClearSelection2 True
End Sub


' A plane parallel to a default plane, through the given model point, its
' sketch axes measured at the same time -- copied from calciner.bas (which
' copied it from cyclone.bas). Which side of the base plane InsertRefPlane
' puts the offset on is measured with a test block; the wrong side is
' deleted and the other tried. Only on an empty part (the probe's rule).
Private Function OffsetPlane(base As SldWorks.Feature, _
                             ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                             ByRef us As Double, ByRef vs As Double) As SldWorks.Feature
    Dim pl As SldWorks.Feature
    Dim opt As Long, k As Long, at As String

    at = "(" & Fmt(bx) & ", " & Fmt(by) & ", " & Fmt(bz) & ")"
    For k = 0 To 1
        opt = swRefPlaneReferenceConstraint_Distance
        If k = 1 Then opt = opt Or swRefPlaneReferenceConstraint_OptionFlip
        swModel.ClearSelection2 True
        base.Select2 False, 0
        Set pl = swFeat.InsertRefPlane(opt, Abs(bx) + Abs(by) + Abs(bz), 0, 0#, 0, 0#)
        swModel.ClearSelection2 True
        If pl Is Nothing Then Fail "InsertRefPlane failed for the offset plane through " & at & "."
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
    Fail "the offset plane could not be placed through " & at & "; a test block dropped on it landed somewhere else both ways round."
End Function

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
Private Sub Paint(face As SldWorks.Face2, ByVal r As Double, ByVal g As Double, ByVal b As Double, _
                  Optional ByVal see As Double = 0.6)
    Dim m(8) As Double
    Dim got As Variant
    ' see-through (0.6) so the gas path can be looked along in the assembly;
    ' the faces where two gas volumes meet fully (1: user, 23 Nov 2026)
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = see: m(8) = 0#
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


