Attribute VB_Name = "c1_twin"
'==================================================================
' Twin C1 over one R1: CFD fluid volume  ->  SLDPRT + STEP (AP214)
'
' The two top cyclones of a string and the riser they share (user
' decision, 13 Nov 2026; geometry/preheater/riser_R1.md). Each C1 is
' the verified C1 + riser branch solid, C1_riser.SLDPRT from
' cyclone.bas (RISER_ON), copied as it is: opened read-only, never
' changed, checked unchanged at the end. The pair:
'
'   frame   z from the C1 dust outlets (as C1_riser), x across the pair
'           (mirror plane x = 0), y the inlet ducts' direction
'   C1 A    C1_riser turned 90 deg about z (its +x, the gas into its
'           duct, to +y) and moved to x = +TWIN_S / 2: its duct and
'           branch on its -x side, facing the other; swirl clockwise
'   C1 B    C1 A's mirror in x = 0: swirl anticlockwise
'   R1      on the mirror plane, BRANCH_Y in front of the C1 axes: a
'           straight stub R1_STUB_L under its Y (as far as it rises
'           over C2's outlet leg), then a loft from its top to each
'           branch's floor -- the round ends of a pant-leg Y
'
' Nothing structural (CLAUDE.md rule 8). The spacing and the Y are
' derived (plant_geometry.c1_twin), the gap between the branches'
' walls a model choice: Estimated, no source gives them.
'
' To run: build C1_riser.SLDPRT with cyclone.bas (CYCLONE_NAME "C1",
' RISER_ON True) first; then Tools -> Macro -> New, import this file,
' run main. Outputs geometry\output\2500\C1_twin.SLDPRT, .step and
' c1_twin_build.log (tests read it).
'==================================================================
Option Explicit

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const R1_D                         As Double  = 3.15         ' R1 bore = C2's D_x [derived]
Const TWIN_GAP                     As Double  = 1#           ' the branches' walls apart [model, preheater/riser_R1.md]
Const TWIN_S                       As Double  = 8.507386     ' C1 axis to axis [derived]
Const BRANCH_HALF                  As Double  = 1.613693     ' each branch from R1's axis, x [derived]
Const BRANCH_D                     As Double  = 2.227386     ' branch bore (half R1's area) [derived]
Const BRANCH_Y                     As Double  = -6.727386    ' branches and R1 in front of the C1 axes, y [derived]
Const Z_BRANCH                     As Double  = 0.212614     ' the branches' floor (the C1_riser inlet face) [derived]
Const Z_SPLIT                      As Double  = -1.862386    ' R1's top: the Y starts [derived]
Const R1_STUB_L                    As Double  = 2.137614     ' R1 straight under its Y, from the top of C2's CFD outlet pipe [derived]
Const C1_R                         As Double  = 2.16         ' barrel radius [derived]
Const C1_Y_FAR                     As Double  = 2.226723     ' the C1_riser solid's side away from its duct (C1 frame -y): the barrel, or the volute's scroll end [derived]
Const C1_TOP                       As Double  = 18.46        ' the outlet bend's crown [derived]
Const C1_X_MAX                     As Double  = 2.654055     ' the C1_riser solid's far side (C1 frame x): its outlet leg, or (outlet_side -1) the barrel / scroll [derived]
Const C1_X_MIN                     As Double  = -8.600887    ' the C1_riser solid's near side (C1 frame x): its feed chute, or the outlet leg past it [derived]
Const OUT_Z_END                    As Double  = 11.44        ' the outlet legs' end faces [derived]
Const OUT_Y                        As Double  = -6.48        ' the outlet legs' axes, twin y (C1 frame x; outlet_side) [derived]
' END GENERATED

Const LINE_KEY As String = "2500"
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"
Const SRC_NAME As String = "C1_riser"
Const OUT_NAME As String = "C1_twin"
Const PI As Double = 3.14159265358979
Const BOX_TOL As Double = 0.002          ' a box side vs the source [m]
Const VOL_TOL As Double = 0.002          ' a volume vs the expected, relative
Const LEG_TOL As Double = 0.02           ' a Y leg vs the sheared frustum, relative: SolidWorks' loft between
                                         ' offset circles is not quite ruled (run 4: -0.8 %)
Const FACE_TOL As Double = 0.0005        ' a face found by its level [m]
Const FACE_XY_TOL As Double = 0.02       ' ... and by its box across (GetBox may be loose) [m]

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swMath  As SldWorks.MathUtility
Dim srcPath As String
Dim srcStamp As Date, srcLen As Long
Dim srcBody As SldWorks.Body2
Dim vSrc As Double
Dim oldStepAP As Long, oldStepAppear As Boolean, stepPrefsTouched As Boolean
Dim buildLog As String
Dim phase As String


Sub main()

    Dim why As String

    buildLog = ""
    phase = "starting up"
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    Set swMath = swApp.GetMathUtility

    phase = "reading the C1_riser solid"
    ReadSource
    phase = "making the part"
    NewPart
    phase = "placing the two C1"
    PlaceTwin
    phase = "adding R1 and its Y"
    AddR1
    phase = "joining the bodies"
    JoinAll
    phase = "checking the solid"
    Verify
    phase = "tagging the boundary faces"
    TagFaces
    phase = "saving"
    SaveOne OUT_ROOT & LINE_KEY & "\" & OUT_NAME & ".SLDPRT"
    SaveStep OUT_ROOT & LINE_KEY & "\" & OUT_NAME & ".step"
    RestorePrefs
    SourceUntouched

    buildLog = "c1_twin built" & vbLf & buildLog
    WriteLog
    ' no message box when OUT_ROOT\quiet.flag exists (tools/sw_run.py)
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox "C1_twin built." & vbLf & "Full log: " & LogPath(), vbInformation, "Twin C1"
    End If
    Exit Sub

Failed:
    why = Err.Description
    RestorePrefs
    buildLog = "c1_twin ABORTED while " & phase & ": " & why & vbLf & buildLog
    WriteLog
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox "C1_twin ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
               vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Twin C1"
    End If
End Sub


'==================================================================
' The source: C1_riser, read-only
'==================================================================
Private Sub ReadSource()
    Dim errs As Long, warns As Long
    Dim doc As SldWorks.ModelDoc2
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, bx As Variant
    srcPath = OUT_ROOT & LINE_KEY & "\" & SRC_NAME & ".SLDPRT"
    If Dir(srcPath) = "" Then Fail srcPath & " does not exist: build it with cyclone.bas (C1, RISER_ON) first."
    srcStamp = FileDateTime(srcPath): srcLen = FileLen(srcPath)
    Set doc = swApp.OpenDoc6(srcPath, swDocPART, swOpenDocOptions_Silent Or swOpenDocOptions_ReadOnly, "", errs, warns)
    If doc Is Nothing Then Fail "could not open " & srcPath & " (error " & errs & ")."
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail SRC_NAME & " has no solid body."
    If UBound(bodies) <> 0 Then Fail SRC_NAME & " has " & (UBound(bodies) + 1) & " bodies, not one."
    Set srcBody = bodies(0)
    bx = ExactBox(srcBody)
    Note "source: " & srcPath & " (read-only, " & srcLen & " bytes, " & Format(srcStamp, "yyyy-mm-dd hh:nn:ss") & ")"
    Note "source box: x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
         ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & " m"
    ' the solid is the source's: its extent along the duct (x) and its height
    CheckNear "source x min (feed chute)", bx(0), C1_X_MIN
    CheckNear "source x max", bx(3), C1_X_MAX
    CheckNear "source z min (dust outlet)", bx(2), 0#
    CheckNear "source z max (outlet bend crown)", bx(5), C1_TOP
    vSrc = Volume(srcBody)
    Note "source volume " & Fmt(vSrc) & " m3"
End Sub


Private Sub NewPart()
    Dim tpl As String
    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplatePart)
    If tpl = "" Then Fail "no default part template is set (Tools > Options > Default Templates)."
    Set swModel = swApp.NewDocument(tpl, 0, 0#, 0#)
    If swModel Is Nothing Then Fail "could not create a part from " & tpl & "."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
End Sub


'==================================================================
' The two C1: the source turned, moved, and mirrored
'==================================================================
' A: (x, y) -> (S/2 - y, x): the source's +x (into its duct) to +y,
' its +y side (duct, branch) to -x. B: A mirrored, (x, y) -> (y - S/2, x).
' First as temporary bodies under a MathTransform (its return value is
' not trusted -- run 2 it said False on a plain turn -- nor its row
' convention: each copy's box is checked, both readings tried); failing
' that, with SolidWorks' own features: the source as a body, Move/Copy
' Body to turn and move it, Mirror Body in the plane x = 0.
Private Sub PlaceTwin()
    Dim a As SldWorks.Body2, b As SldWorks.Body2
    Set a = Placed(0, -1, 1, 0, 0.5 * TWIN_S, "C1 A")
    If Not a Is Nothing Then Set b = Placed(0, 1, 1, 0, -0.5 * TWIN_S, "C1 B (mirror)")
    If Not a Is Nothing And Not b Is Nothing Then
        MakeFeature a, "C1 A"
        MakeFeature b, "C1 B"
        Exit Sub
    End If
    Note "temporary-body transforms did not land: placing with features"
    PlaceByFeatures
End Sub


' A copy of the source under x' = m00 x + m01 y + tx, y' = m10 x + m11 y,
' z' = z, checked where it lands; Nothing if neither reading lands.
Private Function Placed(ByVal m00 As Double, ByVal m01 As Double, ByVal m10 As Double, ByVal m11 As Double, _
                        ByVal tx As Double, ByVal what As String) As SldWorks.Body2
    Dim k As Long, b As SldWorks.Body2, ok As Boolean
    For k = 0 To 1
        Set b = srcBody.Copy
        If b Is Nothing Then Fail "could not copy the source body."
        If k = 0 Then
            ok = b.ApplyTransform(Xform(m00, m10, m01, m11, tx))
        Else
            ok = b.ApplyTransform(Xform(m00, m01, m10, m11, tx))
        End If
        If LandsRight(b, m00, m01, m10, m11, tx) Then
            Note what & ": placed" & IIf(k = 1, " (transposed matrix)", "") & " (ApplyTransform said " & ok & "); " & BoxText(b)
            If Abs(Volume(b) - vSrc) > VOL_TOL * vSrc Then Fail what & ": its volume " & Fmt(Volume(b)) & _
                " m3 is not the source's " & Fmt(vSrc) & "."
            Set Placed = b
            Exit Function
        End If
        Note what & ": transform try " & (k + 1) & " (ApplyTransform said " & ok & ") landed " & BoxText(b)
    Next k
End Function


Private Sub PlaceByFeatures()
    Dim f As SldWorks.Feature, a As SldWorks.Body2, k As Long
    Dim ang As Variant
    ' C1 A: the source, turned +90 deg about z, then moved S/2 along x
    For Each ang In Array(0.5 * PI, -0.5 * PI)
        ClearBodies
        MakeFeature srcBody.Copy, "C1 A (as the source)"
        Set a = OnlyBody()
        SelectBody a, False, 1
        Set f = swFeat.InsertMoveCopyBody2(0#, 0#, 0#, 0#, 0#, 0#, 0#, 0#, 0#, CDbl(ang), False, 1)
        If f Is Nothing Then Fail "Move/Copy Body refused the turn of C1 A."
        Set a = OnlyBody()
        SelectBody a, False, 1
        Set f = swFeat.InsertMoveCopyBody2(0.5 * TWIN_S, 0#, 0#, 0#, 0#, 0#, 0#, 0#, 0#, 0#, False, 1)
        If f Is Nothing Then Fail "Move/Copy Body refused the move of C1 A."
        Set a = OnlyBody()
        If LandsRight(a, 0, -1, 1, 0, 0.5 * TWIN_S) Then
            Note "C1 A: placed by Move/Copy Body, turned " & Fmt(CDbl(ang) * 180# / PI) & " deg; " & BoxText(a)
            Exit For
        End If
        Note "C1 A: Move/Copy Body turned " & Fmt(CDbl(ang) * 180# / PI) & " deg landed " & BoxText(a)
        Set a = Nothing
    Next ang
    If a Is Nothing Then Fail "C1 A lands neither way Move/Copy Body turns it (log)."
    If Abs(Volume(a) - vSrc) > VOL_TOL * vSrc Then Fail "C1 A's volume " & Fmt(Volume(a)) & " m3 is not the source's."

    ' C1 B: A's mirror in the plane x = 0
    swModel.ClearSelection2 True
    SelectBody a, False, 256
    If Not PlaneX0().Select2(True, 2) Then Fail "could not select the plane x = 0 to mirror in."
    Set f = swFeat.InsertMirrorFeature2(True, False, False, False, 0)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "Mirror Body refused C1 A."
    If BodyCount() <> 2 Then Fail "the mirror left " & BodyCount() & " bodies, not 2."
    For k = 0 To 1
        If LandsRight(BodyN(k), 0, 1, 1, 0, -0.5 * TWIN_S) Then
            Note "C1 B: mirrored; " & BoxText(BodyN(k))
            Exit Sub
        End If
    Next k
    Fail "C1 B (the mirror) did not land at x = -S/2: " & BoxText(BodyN(0)) & " / " & BoxText(BodyN(1))
End Sub


' The default plane with its normal along x, by probing (the names are
' localised: "Right Plane" is "Sag Duzlem" here).
Private Function PlaneX0() As SldWorks.Feature
    Dim f As SldWorks.Feature, sk As SldWorks.Sketch, a As Variant
    Set f = swModel.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.SketchManager.InsertSketch True
            Set sk = swModel.SketchManager.ActiveSketch
            If Not sk Is Nothing Then
                a = sk.ModelToSketchTransform.ArrayData
                swModel.SketchManager.InsertSketch True
                swModel.ClearSelection2 True
                ' the sketch's normal, as cyclone.bas reads it (PlaneNormal)
                If Abs(Abs(a(6)) - 1#) < 0.001 Then
                    Set PlaneX0 = f
                    Exit Function
                End If
            End If
        End If
        Set f = f.GetNextFeature
    Loop
    Fail "no default plane has its normal along x."
End Function


Private Sub SelectBody(b As SldWorks.Body2, ByVal append As Boolean, ByVal mark As Long)
    Dim sd As SldWorks.SelectData
    If Not append Then swModel.ClearSelection2 True
    Set sd = swModel.SelectionManager.CreateSelectData
    sd.Mark = mark
    If Not b.Select2(append, sd) Then Fail "could not select a body (mark " & mark & ")."
End Sub


Private Sub ClearBodies()
    Dim f As SldWorks.Feature, nxt As SldWorks.Feature
    Do While BodyCount() > 0
        Set f = swModel.FeatureByPositionReverse(0)
        If f Is Nothing Then Exit Do
        swModel.ClearSelection2 True
        f.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    Loop
End Sub


Private Function OnlyBody() As SldWorks.Body2
    If BodyCount() <> 1 Then Fail BodyCount() & " bodies where one was expected."
    Set OnlyBody = BodyN(0)
End Function


Private Function BodyN(ByVal i As Long) As SldWorks.Body2
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    Set BodyN = bodies(i)
End Function


' The MathTransform of a turn in x-y (rows r0 = (a, b), r1 = (c, d) as
' SolidWorks stores them) and a shift tx in x.
Private Function Xform(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double, _
                       ByVal tx As Double) As SldWorks.MathTransform
    Dim t(15) As Double
    t(0) = a: t(1) = b: t(2) = 0#
    t(3) = c: t(4) = d: t(5) = 0#
    t(6) = 0#: t(7) = 0#: t(8) = 1#
    t(9) = tx: t(10) = 0#: t(11) = 0#
    t(12) = 1#
    Set Xform = swMath.CreateTransform(t)
End Function


' Where the source's box corners must go: x' from its y range, y'
' from its x range, z as it was.
Private Function LandsRight(b As SldWorks.Body2, ByVal m00 As Double, ByVal m01 As Double, _
                            ByVal m10 As Double, ByVal m11 As Double, ByVal tx As Double) As Boolean
    Dim s As Variant, g As Variant
    Dim xa As Double, xb As Double, ya As Double, yb As Double
    s = ExactBox(srcBody): g = ExactBox(b)
    ' x' = m01 y + tx (m00 = 0), y' = m10 x (m11 = 0)
    xa = tx + Min2(m01 * s(1), m01 * s(4)): xb = tx + Max2(m01 * s(1), m01 * s(4))
    ya = Min2(m10 * s(0), m10 * s(3)): yb = Max2(m10 * s(0), m10 * s(3))
    LandsRight = Abs(g(0) - xa) < BOX_TOL And Abs(g(3) - xb) < BOX_TOL And _
                 Abs(g(1) - ya) < BOX_TOL And Abs(g(4) - yb) < BOX_TOL And _
                 Abs(g(2) - s(2)) < BOX_TOL And Abs(g(5) - s(5)) < BOX_TOL
End Function


Private Sub MakeFeature(b As SldWorks.Body2, ByVal what As String)
    Dim f As SldWorks.Feature
    Set f = swPart.CreateFeatureFromBody3(b, False, swCreateFeatureBodyCheck)
    If f Is Nothing Then Fail "could not make a feature of " & what & "."
End Sub


'==================================================================
' R1: its straight stub, then a loft to each branch's floor
'==================================================================
Private Sub AddR1()
    Dim md As SldWorks.Modeler
    Dim cyl As SldWorks.Body2
    Dim p(7) As Double
    Dim bx As Variant
    Dim top As SldWorks.Face2, fa As SldWorks.Face2, fb As SldWorks.Face2

    Set md = swApp.GetModeler
    p(0) = 0#: p(1) = BRANCH_Y: p(2) = Z_SPLIT - R1_STUB_L
    p(3) = 0#: p(4) = 0#: p(5) = 1#
    p(6) = 0.5 * R1_D: p(7) = R1_STUB_L
    Set cyl = md.CreateBodyFromCyl(p)
    If cyl Is Nothing Then Fail "could not make R1's stub."
    bx = ExactBox(cyl)
    If Abs(bx(2) - (Z_SPLIT - R1_STUB_L)) > BOX_TOL Or Abs(bx(5) - Z_SPLIT) > BOX_TOL Then
        Fail "R1's stub came out at z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & ", not " & _
             Fmt(Z_SPLIT - R1_STUB_L) & " .. " & Fmt(Z_SPLIT) & "."
    End If
    MakeFeature cyl, "R1's stub"
    Note "R1 stub: D " & Fmt(R1_D) & ", z " & Fmt(Z_SPLIT - R1_STUB_L) & " .. " & Fmt(Z_SPLIT) & ", y " & Fmt(BRANCH_Y)

    Set top = DiscAt(0#, BRANCH_Y, Z_SPLIT, 0.5 * R1_D, "R1's top")
    Set fa = DiscAt(BRANCH_HALF, BRANCH_Y, Z_BRANCH, 0.5 * BRANCH_D, "C1 A's branch floor")
    Set fb = DiscAt(-BRANCH_HALF, BRANCH_Y, Z_BRANCH, 0.5 * BRANCH_D, "C1 B's branch floor")
    LoftLeg top, fa, "A"
    ' the first loft is its own body, so R1's top is still there
    Set top = DiscAt(0#, BRANCH_Y, Z_SPLIT, 0.5 * R1_D, "R1's top")
    Set fb = DiscAt(-BRANCH_HALF, BRANCH_Y, Z_BRANCH, 0.5 * BRANCH_D, "C1 B's branch floor")
    LoftLeg top, fb, "B"
End Sub


' The planar, level face whose box is the disc at (x, y, z), radius r.
Private Function DiscAt(ByVal x As Double, ByVal y As Double, ByVal z As Double, ByVal r As Double, _
                        ByVal what As String) As SldWorks.Face2
    Dim bodies As Variant, faces As Variant, bx As Variant
    Dim i As Long, j As Long
    Dim fc As SldWorks.Face2, sf As SldWorks.Surface
    bodies = swPart.GetBodies2(swSolidBody, True)
    For i = 0 To UBound(bodies)
        faces = bodies(i).GetFaces
        For j = 0 To UBound(faces)
            Set fc = faces(j)
            Set sf = fc.GetSurface
            If sf.IsPlane Then
                bx = fc.GetBox
                If Abs(bx(2) - z) < FACE_TOL And Abs(bx(5) - z) < FACE_TOL And _
                   Abs(bx(0) - (x - r)) < FACE_XY_TOL And Abs(bx(3) - (x + r)) < FACE_XY_TOL And _
                   Abs(bx(1) - (y - r)) < FACE_XY_TOL And Abs(bx(4) - (y + r)) < FACE_XY_TOL Then
                    Set DiscAt = fc
                    Exit Function
                End If
            End If
        Next j
    Next i
    Fail "found no face for " & what & " (a disc r " & Fmt(r) & " at " & Fmt(x) & ", " & Fmt(y) & ", " & Fmt(z) & ")."
End Function


' A loft between two round ends, not merged (both legs start on R1's
' top); a ruled loft between parallel circles is a frustum, sheared:
' pi h / 3 (r1^2 + r1 r2 + r2^2).
Private Sub LoftLeg(f0 As SldWorks.Face2, f1 As SldWorks.Face2, ByVal leg As String)
    Dim sd As SldWorks.SelectData
    Dim ent As SldWorks.Entity
    Dim f As SldWorks.Feature
    Dim before As Long, got As Double, want As Double, r1 As Double, r2 As Double, h As Double
    before = BodyCount()
    swModel.ClearSelection2 True
    Set sd = swModel.SelectionManager.CreateSelectData
    sd.Mark = 1
    Set ent = f0: ent.Select4 False, sd
    Set ent = f1: ent.Select4 True, sd
    Set f = swFeat.InsertProtrusionBlend2(False, True, False, 1#, 0, 0, 1#, 1#, True, True, _
                                          False, 0#, 0#, 0, False, True, True, 0)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "the loft of the Y's leg " & leg & " was refused."
    If BodyCount() <> before + 1 Then Fail "the Y's leg " & leg & " did not come out as its own body."
    r1 = 0.5 * R1_D: r2 = 0.5 * BRANCH_D: h = Z_BRANCH - Z_SPLIT
    want = PI * h / 3# * (r1 * r1 + r1 * r2 + r2 * r2)
    got = Volume(LegBody(IIf(leg = "A", 1#, -1#)))
    If Abs(got - want) > LEG_TOL * want Then Fail "the Y's leg " & leg & " is " & Fmt(got) & " m3, not the frustum's " & Fmt(want) & "."
    Note "Y leg " & leg & ": " & Fmt(got) & " m3 (frustum " & Fmt(want) & ", " & Fmt(100# * (got - want) / want) & " %)"
End Sub


'==================================================================
' One body
'==================================================================
Private Sub JoinAll()
    Dim bodies As Variant, tools() As Object
    Dim i As Long
    Dim f As SldWorks.Feature
    bodies = swPart.GetBodies2(swSolidBody, True)
    If UBound(bodies) <> 4 Then Fail (UBound(bodies) + 1) & " bodies before the join, not 5 (two C1, R1, two legs)."
    ReDim tools(UBound(bodies))
    For i = 0 To UBound(bodies)
        Set tools(i) = bodies(i)
    Next i
    Set f = swFeat.InsertCombineFeature(SWBODYADD, Nothing, tools)
    If f Is Nothing Then
        ReDim tools(UBound(bodies) - 1)
        For i = 1 To UBound(bodies)
            Set tools(i - 1) = bodies(i)
        Next i
        Set f = swFeat.InsertCombineFeature(SWBODYADD, bodies(0), tools)
        If f Is Nothing Then Fail "the five bodies could not be combined."
    End If
    If BodyCount() <> 1 Then Fail "the join left " & BodyCount() & " bodies: the Y does not reach a C1."
End Sub


Private Sub Verify()
    Dim b As SldWorks.Body2, g As Variant
    Dim got As Double, lo As Double, hi As Double, vLeg As Double, vStub As Double
    Dim r1 As Double, r2 As Double, h As Double
    Set b = LastBody()
    g = ExactBox(b)
    Note "twin box: " & BoxText(b)
    ' symmetric about x = 0, the barrels its outer sides (with a volute,
    ' the scroll's end, 67 mm past the barrel on C1), the outlet legs its back, the feed chutes its front, R1's stub its floor
    CheckNear "x max (C1 A's far side)", g(3), 0.5 * TWIN_S + C1_Y_FAR
    CheckNear "x min (C1 B's far side)", g(0), -(0.5 * TWIN_S + C1_Y_FAR)
    CheckNear "y max", g(4), C1_X_MAX
    CheckNear "y min", g(1), C1_X_MIN
    CheckNear "z min (R1's stub)", g(2), Z_SPLIT - R1_STUB_L
    CheckNear "z max (the outlet bends)", g(5), C1_TOP
    r1 = 0.5 * R1_D: r2 = 0.5 * BRANCH_D: h = Z_BRANCH - Z_SPLIT
    vLeg = PI * h / 3# * (r1 * r1 + r1 * r2 + r2 * r2)
    vStub = PI * r1 * r1 * R1_STUB_L
    ' the legs overlap each other over R1's top: the whole lies between
    ' the two C1, the stub and one leg, and all of them
    lo = 2# * vSrc + vStub + (1# - LEG_TOL) * vLeg: hi = 2# * vSrc + vStub + 2# * (1# + LEG_TOL) * vLeg
    got = Volume(b)
    If got < lo * (1# - VOL_TOL) Or got > hi * (1# + VOL_TOL) Then
        Fail "the twin is " & Fmt(got) & " m3; it must lie between " & Fmt(lo) & " and " & Fmt(hi) & "."
    End If
    Note "twin volume " & Fmt(got) & " m3 (2 x " & Fmt(vSrc) & " C1_riser + R1 stub " & Fmt(vStub) & _
         " + Y " & Fmt(got - 2# * vSrc - vStub) & ")"
    Note "twin: C1 axes " & Fmt(TWIN_S) & " apart, branches " & Fmt(2# * BRANCH_HALF) & " apart (walls " & _
         Fmt(TWIN_GAP) & "), R1 " & Fmt(-BRANCH_Y) & " in front"
End Sub


' The gas faces: R1's floor in (green), the two outlet legs' ends out
' (red), as cyclone.bas colours them.
Private Sub TagFaces()
    Paint DiscAt(0#, BRANCH_Y, Z_SPLIT - R1_STUB_L, 0.5 * R1_D, "R1's floor"), 0#, 0.8, 0#
    Note "inlet_gas: R1's floor, z " & Fmt(Z_SPLIT - R1_STUB_L)
    Paint OutletEnd(1#), 0.9, 0#, 0#
    Paint OutletEnd(-1#), 0.9, 0#, 0#
    Note "outlets: the two C1 outlet legs' ends, z " & Fmt(OUT_Z_END)
End Sub


' The level face at OUT_Z_END on the +sg side.
Private Function OutletEnd(ByVal sg As Double) As SldWorks.Face2
    Dim faces As Variant, bx As Variant, j As Long
    Dim fc As SldWorks.Face2, sf As SldWorks.Surface
    faces = LastBody().GetFaces
    For j = 0 To UBound(faces)
        Set fc = faces(j)
        Set sf = fc.GetSurface
        If sf.IsPlane Then
            bx = fc.GetBox
            If Abs(bx(2) - OUT_Z_END) < FACE_TOL And Abs(bx(5) - OUT_Z_END) < FACE_TOL And _
               sg * (bx(0) + bx(3)) > 0# And Abs(0.5 * (bx(1) + bx(4)) - OUT_Y) < 0.05 Then
                Set OutletEnd = fc
                Exit Function
            End If
        End If
    Next j
    Fail "found no outlet end face on the " & IIf(sg > 0#, "+x", "-x") & " side at z " & Fmt(OUT_Z_END) & "."
End Function


Private Sub Paint(face As SldWorks.Face2, ByVal r As Double, ByVal g As Double, ByVal b As Double)
    Dim m(8) As Double
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = 0#: m(8) = 0#
    face.MaterialPropertyValues = m
End Sub


'==================================================================
' Housekeeping
'==================================================================
Private Sub SourceUntouched()
    If FileDateTime(srcPath) <> srcStamp Or FileLen(srcPath) <> srcLen Then _
        Fail srcPath & " changed while it was copied: rebuild it with cyclone.bas."
    Note "source unchanged: " & srcPath
End Sub


Private Sub SaveOne(ByVal path As String)
    Dim errs As Long, warns As Long
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If errs <> 0 Then Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    If Dir(path) = "" Then Fail "SolidWorks reported no error but " & path & " is not on disk."
    Note "wrote " & path
End Sub


' STEP AP214 with the face colours, as cyclone.bas writes it (AP203
' drops the boundary colours). Run 5 wrote a STEP with no solid in it
' (a header only, 4.5 kB): the file is read back and must hold one.
Private Sub SaveStep(ByVal path As String)
    Dim k As Long
    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    stepPrefsTouched = True
    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True
    For k = 1 To 2
        swModel.ForceRebuild3 False
        SaveOne path
        If StepHasSolid(path) Then
            Note "STEP: " & FileLen(path) & " bytes, holds the solid"
            Exit Sub
        End If
        Note "WARNING: " & path & " (" & FileLen(path) & " bytes) holds no solid; try " & k
    Next k
    Fail path & " holds no solid after two exports."
End Sub


Private Function StepHasSolid(ByVal path As String) As Boolean
    Dim fn As Integer, txt As String
    fn = FreeFile
    Open path For Binary Access Read As #fn
    txt = Space$(LOF(fn))
    Get #fn, , txt
    Close #fn
    StepHasSolid = (InStr(txt, "MANIFOLD_SOLID_BREP") > 0) And (InStr(txt, "ADVANCED_FACE") > 0)
End Function


Private Sub RestorePrefs()
    On Error Resume Next
    If stepPrefsTouched Then
        swApp.SetUserPreferenceIntegerValue swStepAP, oldStepAP
        swApp.SetUserPreferenceToggle swStepExportAppearances, oldStepAppear
        stepPrefsTouched = False
    End If
End Sub


Private Function Volume(b As SldWorks.Body2) As Double
    Dim mp As Variant
    mp = b.GetMassProperties(1#)
    Volume = mp(3)
End Function


' The Y's leg on the sg side: the body that spans the Y's height
' (z Z_SPLIT .. Z_BRANCH), its top over that side's branch. Bodies are
' not listed in the order they were made (run 3).
Private Function LegBody(ByVal sg As Double) As SldWorks.Body2
    Dim bodies As Variant, g As Variant, i As Long
    Dim b As SldWorks.Body2
    bodies = swPart.GetBodies2(swSolidBody, True)
    For i = 0 To UBound(bodies)
        Set b = bodies(i)
        g = ExactBox(b)
        If Abs(g(2) - Z_SPLIT) < BOX_TOL And Abs(g(5) - Z_BRANCH) < BOX_TOL And sg * (g(0) + g(3)) > 0# Then
            Set LegBody = b
            Exit Function
        End If
    Next i
    Fail "found no body that is the Y's leg on the " & IIf(sg > 0#, "+x", "-x") & " side."
End Function


Private Function BodyCount() As Long
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then BodyCount = 0 Else BodyCount = UBound(bodies) + 1
End Function


Private Function LastBody() As SldWorks.Body2
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no body."
    Set LastBody = bodies(UBound(bodies))
End Function


Private Function BoxText(b As SldWorks.Body2) As String
    Dim g As Variant
    g = ExactBox(b)
    BoxText = "x " & Fmt(g(0)) & " .. " & Fmt(g(3)) & ", y " & Fmt(g(1)) & " .. " & Fmt(g(4)) & _
              ", z " & Fmt(g(2)) & " .. " & Fmt(g(5)) & " m"
End Function


Private Sub CheckNear(ByVal what As String, ByVal got As Double, ByVal want As Double)
    If Abs(got - want) > BOX_TOL Then Fail what & " is " & Fmt(got) & " m, the source's " & Fmt(want) & "."
End Sub


' The body's true extent, from its extreme points (GetBodyBox bounds
' curved faces loosely; cyclone.bas's ExactBox).
Private Function ExactBox(body As SldWorks.Body2) As Variant
    Dim b(5) As Double, d(2) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    ExactBox = b
End Function


Private Function Min2(ByVal a As Double, ByVal b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function


Private Function Max2(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\c1_twin_build.log"
End Function


Private Sub WriteLog()
    Dim fn As Integer
    On Error Resume Next
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    fn = FreeFile
    Open LogPath() For Output As #fn
    Print #fn, buildLog;
    Close #fn
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "c1_twin", msg
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Replace(Format(v, "0.000"), ",", ".")
End Function
