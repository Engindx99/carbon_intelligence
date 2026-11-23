Attribute VB_Name = "kiln_burner_body"
'==================================================================
' Kiln burner (JETFLEX 2.0), THE WHOLE BURNER as simple envelopes
'   ->  SLDPRT + STEP
'
' NOT a CFD input and not a fabrication drawing (user request, 22 Nov
' 2026: a solid and a sheet of the whole burner; the CFD input is the
' channel solid kiln_burner.bas). Frame as kiln_burner.bas: the tip plane
' z = 0, the burner back along -z, y up, x to the right seen from the
' kiln.
'
'   tip_ring, castable          the castable round the burner pipe
'   burner_pipe                 steel pipe; its bore = the channels' axial plenum
'   flange, head, bellows       mounting flange, air connection head, expansion joint
'   coal_inlet(_flange)         solid fuel inlet pipe at the back
'   air_inlet_1, air_inlet_2    the head's two air inlets (+x side)
'   beam, hanger_1, hanger_2    the carriage beam over the head
'
' Every body, its size, place, volume and extent come from
' geometry/plant_geometry.py kiln_burner_body() (the generated KBB_
' strings): ratios of the tip's D measured on the Fuller brochure's side
' view, scaled by kiln_burner()'s D_tip. The builder is kiln_rotax.bas's.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py kiln_burner_body_solid.main, then
' kiln_burner_body_solid.assembly (needs kiln_burner.SLDPRT). Outputs
' geometry\output\2500\kiln_burner_body.SLDPRT, .step,
' kiln_burner_body_build.log; kiln_burner_assembly.SLDASM + jpgs.
'==================================================================

Option Explicit

Const PART_NAME As String = "kiln_burner_body"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 13           ' bodies in the part [derived]
Const KBB_1                        As String  = "tip_ring|ring|0.239656266|0.314077459|-0.697251959|0|0.090268706|-0.314077459|-0.314077459|-0.697251959|0.314077459|0.314077459|0|0.72|0.66|0.56;castable|ring|0.239656266|0.304655135|-6.545374241|-0.697251959|0.650009272|-0.304655135|-0.304655135|-6.545374241|0.304655135|0.304655135|-0.697251959|0.72|0.66|0.56;burner_pipe|ring|0.229656266|0.239656266|-6.696131421|0|0.098727012|-0.239656266|-0.239656266|-6.696131421|0.239656266|0.239656266|0|0.45|0.46|0.48;flange|cyl|0|0|-6.758946913|0|0|1|0.348625979|0.062815492|0.023984802|-0.348625979|-0.348625979|-6.758946913|0.348625979|0.348625979|-6.696131421|0.45|0.46|0.48;head|cyl|0|0|-8.015256748|0|0|1|0.279528938|1.256309835|0.308389926|-0.279528938|-0.279528938|-8.015256748|0.279528938|0.279528938|-6.758946913|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_2                        As String  = "bellows|cyl|0|0|-8.191140125|0|0|1|0.298373586|0.175883377|0.049192106|-0.298373586|-0.298373586|-8.191140125|0.298373586|0.298373586|-8.015256748|0.45|0.46|0.48;coal_inlet|cyl|0|0.033669104|-9.503983903|0|0|1|0.11620866|1.312843778|0.055698039|-0.11620866|-0.082539556|-9.503983903|0.11620866|0.149877763|-8.191140125|0.1|0.16|0.72;coal_inlet_flange|cyl|0|0.033669104|-9.566799395|0|0|1|0.157038729|0.062815492|0.004866651|-0.157038729|-0.123369626|-9.566799395|0.157038729|0.190707833|-9.503983903|0.1|0.16|0.72;air_inlet_1|cyl|0.279528938|0|-7.324286339|1|0|0|0.157038729|0.502523934|0.038933206|0.279528938|-0.157038729|-7.481325068|0.782052872|0.157038729|-7.16724761|0.1|0.16|0.72;air_inlet_2|cyl|0.279528938|0|-7.839373371|1|0|0|0.113067885|0.502523934|0.020182974|0.279528938|-0.113067885|-7.952441256|0.782052872|0.113067885|-7.726305486|0.1|0.16|0.72;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_3                        As String  = "beam|box|-0.125630984|0.125630984|0.653281114|0.948513926|-10.465060927|-6.696131421|0.279582119|-0.125630984|0.653281114|-10.465060927|0.125630984|0.948513926|-6.696131421|0.45|0.46|0.48;hanger_1|box|-0.125630984|0.125630984|0.279528938|0.653281114|-7.035335077|-6.758946913|0.025955531|-0.125630984|0.279528938|-7.035335077|0.125630984|0.653281114|-6.758946913|0.45|0.46|0.48;hanger_2|box|-0.125630984|0.125630984|0.279528938|0.653281114|-8.096916888|-7.682334642|0.038933297|-0.125630984|0.279528938|-8.096916888|0.125630984|0.653281114|-7.682334642|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_4                        As String  = ""           ' plant_geometry.kiln_burner_body() bodies
Const KBB_5                        As String  = ""           ' plant_geometry.kiln_burner_body() bodies
Const KBB_6                        As String  = ""           ' plant_geometry.kiln_burner_body() bodies
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL As Double = 0.001   ' relative, on each body's volume
Const BOX_TOL As Double = 0.001   ' absolute [m], on each body's extent

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim md      As SldWorks.Modeler
Dim mu      As SldWorks.MathUtility

Dim nB As Long
Dim bName() As String, bKind() As String
Dim bP() As Double, bV() As Double, bBox() As Double, bRGB() As Double

' CreateBodyFromBox3's conventions, probed: width along y (not x)?
' the given point the base's centre (not the box's)?
Dim boxSwap As Boolean, boxBase As Boolean

Dim buildLog As String
Dim phase As String
Dim logName As String             ' the build log's file name (main: kiln_burner_body_build.log)
Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStepAppear As Boolean


'==================================================================
' main
'==================================================================
Sub main()
    Dim why As String

    buildLog = ""
    logName = PART_NAME & "_build.log"
    phase = "starting up"
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "reading the bodies"
    ReadBodies
    phase = "building the bodies"
    Build
    phase = "verifying the bodies"
    Verify
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog PART_NAME & " built, verified and exported"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln burner (whole)"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln burner (whole)"
    End If
End Sub


'==================================================================
' assembly: the whole burner -- its channels (kiln_burner.SLDPRT, the CFD
' flow volume) inside this envelope (kiln_burner_body.SLDPRT), both at
' the origin of the burner's frame and fixed  ->  kiln_burner_assembly.SLDASM.
' Run after both parts are built (python3 tools/sw_run.py
' kiln_burner_body_solid.assembly).
' The parts stay separate files, so rebuilding either updates it.
'==================================================================
Sub assembly()
    Dim why As String, outDir As String, tpl As String
    Dim asmDoc As SldWorks.ModelDoc2, asm As SldWorks.AssemblyDoc
    Dim doc As SldWorks.ModelDoc2, comp As SldWorks.Component2
    Dim parts As Variant, p As Variant, comps As Variant, t As Variant
    Dim e As Long, w As Long, k As Long, j As Long

    buildLog = ""
    logName = "kiln_burner_assembly_build.log"
    phase = "starting up"
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    outDir = OUT_ROOT & LINE_KEY & "\"
    parts = Array("kiln_burner.SLDPRT", PART_NAME & ".SLDPRT")

    phase = "opening the parts"
    For Each p In parts
        If Dir(outDir & p) = "" Then Fail outDir & p & " is not built yet."
        Set doc = swApp.OpenDoc6(outDir & p, swDocPART, swOpenDocOptions_Silent, "", e, w)
        If doc Is Nothing Then Fail "could not open " & p & " (error " & e & ")."
    Next p

    phase = "making the assembly"
    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateAssembly)
    Set asmDoc = swApp.NewDocument(tpl, 0, 0, 0)
    If asmDoc Is Nothing Then Fail "could not create an assembly from the default template (" & tpl & ")."
    Set asm = asmDoc
    For Each p In parts
        Set comp = asm.AddComponent5(outDir & p, swAddComponentConfigOptions_CurrentSelectedConfig, "", _
                                     False, "", 0#, 0#, 0#)
        If comp Is Nothing Then Fail "AddComponent5 refused " & p & "."
        ' AddComponent5 puts the part's box centre at the point, not its
        ' origin: the identity puts the part's origin on the assembly's
        Set mu = swApp.GetMathUtility
        comp.Transform2 = mu.CreateTransform(Identity())
        asmDoc.ClearSelection2 True
        comp.Select4 False, Nothing, False
        asm.FixComponent
        asmDoc.ClearSelection2 True
    Next p
    asmDoc.ForceRebuild3 False

    phase = "verifying the assembly"
    comps = asm.GetComponents(True)
    If IsEmpty(comps) Then Fail "the assembly has no components."
    If UBound(comps) <> 1 Then Fail "the assembly has " & (UBound(comps) + 1) & " components, not 2."
    For k = 0 To 1
        Set comp = comps(k)
        t = comp.Transform2.ArrayData
        For j = 0 To 11
            If Abs(t(j) - IIf(j = 0 Or j = 4 Or j = 8, 1#, 0#)) > 0.000001 Then _
                Fail comp.Name2 & " is not at the burner frame's origin (transform term " & j & " = " & Fmt(t(j)) & ")."
        Next j
        ' (IsFixed is not a VBA Boolean: Not on it is always true; compare)
        If CBool(comp.IsFixed) Then
            Note "component " & comp.Name2 & ": at the origin, fixed"
        Else
            Note "component " & comp.Name2 & ": at the origin but not fixed (FixComponent did not take)"
        End If
    Next k

    phase = "saving"
    ' preview images to check it by (the side view looks along -x: z right, y up)
    ' (by the standard view ids: the names alone did not turn the view)
    Dim vw As Variant, vn As Variant
    vn = Array("left", "right", "isometric", "top")
    k = 0
    For Each vw In Array(swLeftView, swRightView, swIsometricView, swTopView)
        asmDoc.ShowNamedView2 "", CLng(vw)
        asmDoc.ViewZoomtofit2
        asmDoc.GraphicsRedraw2
        asmDoc.Extension.SaveAs outDir & "kiln_burner_assembly_" & vn(k) & ".jpg", _
            swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
        k = k + 1
    Next vw
    asmDoc.ShowNamedView2 "", swIsometricView
    asmDoc.ViewZoomtofit2
    asmDoc.Extension.SaveAs outDir & "kiln_burner_assembly.SLDASM", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    If e <> 0 Then Fail "could not write kiln_burner_assembly.SLDASM (error " & e & ")."
    Note "wrote " & outDir & "kiln_burner_assembly.SLDASM"
    WriteLog "kiln_burner_assembly built, verified and saved"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_burner_assembly saved." & vbLf & vbLf & buildLog, vbInformation, "Kiln burner assembly"
    Exit Sub

Failed:
    why = Err.Description
    WriteLog "kiln_burner_assembly ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_burner_assembly ABORTED:" & vbLf & why, vbCritical, "Kiln burner assembly"
End Sub


Private Function Identity() As Variant
    Dim t(15) As Double
    t(0) = 1#: t(4) = 1#: t(8) = 1#: t(12) = 1#
    Identity = t
End Function


'==================================================================
' The generated records: name|kind|params|V|box(6)|rgb(3), ";" between
'==================================================================
Private Sub ReadBodies()
    Dim all As String, recs As Variant, f As Variant
    Dim i As Long, j As Long, np As Long, k As Long

    all = KBB_1 & KBB_2 & KBB_3 & KBB_4 & KBB_5 & KBB_6
    recs = Split(all, ";")
    nB = CLng(N_BODIES)
    ReDim bName(nB - 1): ReDim bKind(nB - 1)
    ReDim bP(nB - 1, 7): ReDim bV(nB - 1): ReDim bBox(nB - 1, 5): ReDim bRGB(nB - 1, 2)

    i = 0
    For j = 0 To UBound(recs)
        If Len(recs(j)) > 0 Then
            If i >= nB Then Fail "more body records than N_BODIES (" & nB & ")."
            f = Split(recs(j), "|")
            bName(i) = f(0): bKind(i) = f(1)
            Select Case bKind(i)
                Case "ring": np = 4
                Case "box", "rbox": np = 6
                Case "cyl": np = 8
                Case Else: Fail "body " & bName(i) & ": unknown kind " & bKind(i) & "."
            End Select
            If UBound(f) <> 1 + np + 1 + 6 + 3 Then Fail "body " & bName(i) & ": " & (UBound(f) + 1) & " fields."
            For k = 0 To np - 1: bP(i, k) = Val(f(2 + k)): Next k
            bV(i) = Val(f(2 + np))
            For k = 0 To 5: bBox(i, k) = Val(f(3 + np + k)): Next k
            For k = 0 To 2: bRGB(i, k) = Val(f(9 + np + k)): Next k
            i = i + 1
        End If
    Next j
    If i <> nB Then Fail i & " body records, N_BODIES says " & nB & "."
    Note nB & " bodies read from the generated block"
End Sub


'==================================================================
' Build: each body a temporary modeler body, then a body of the part
'==================================================================
Private Sub Build()
    Dim i As Long, b As SldWorks.Body2, f As SldWorks.Feature

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set md = swApp.GetModeler
    Set mu = swApp.GetMathUtility

    ProbeBox
    For i = 0 To nB - 1
        Set b = MakeBody(i)
        If b Is Nothing Then Fail "could not make " & bName(i) & "."
        If Not BoxIs(b, i) Then Fail bName(i) & " came out at " & BoxText(b) & ", expected " & WantText(i) & "."
        Set f = swPart.CreateFeatureFromBody3(b, False, 0)
        If f Is Nothing Then Fail "CreateFeatureFromBody3 failed on " & bName(i) & "."
        NameNewBody i
    Next i
    Note "built " & nB & " bodies"
End Sub


Private Function MakeBody(ByVal i As Long) As SldWorks.Body2
    Dim outer As SldWorks.Body2, inner As SldWorks.Body2, res As Variant, e As Long
    Dim b As SldWorks.Body2, t As SldWorks.Body2, k As Long
    Select Case bKind(i)
        Case "ring"
            Set outer = CylBody(0#, 0#, bP(i, 2), 0#, 0#, 1#, bP(i, 1), bP(i, 3) - bP(i, 2))
            Set inner = CylBody(0#, 0#, bP(i, 2) - 0.01, 0#, 0#, 1#, bP(i, 0), bP(i, 3) - bP(i, 2) + 0.02)
            res = outer.Operations2(SWBODYCUT, inner, e)
            If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail bName(i) & ": the ring's cut failed (" & e & ")."
            If UBound(res) <> 0 Then Fail bName(i) & ": the ring's cut gave " & (UBound(res) + 1) & " bodies."
            Set MakeBody = res(0)
        Case "box"
            Set MakeBody = BoxBody(bP(i, 0), bP(i, 1), bP(i, 2), bP(i, 3), bP(i, 4), bP(i, 5))
        Case "rbox"
            ' on the +y axis, then turned theta about +z; the transform's
            ' row convention is not trusted: both readings, the extent decides
            Set b = BoxBody(-0.5 * bP(i, 2), 0.5 * bP(i, 2), bP(i, 0), bP(i, 1), bP(i, 3), bP(i, 4))
            For k = 0 To 1
                Set t = b.Copy
                t.ApplyTransform TurnZ(bP(i, 5), k = 1)
                If BoxIs(t, i) Then Set MakeBody = t: Exit Function
            Next k
            Fail bName(i) & ": neither reading of the turn put it at " & WantText(i) & " (last " & BoxText(t) & ")."
        Case "cyl"
            Set MakeBody = CylBody(bP(i, 0), bP(i, 1), bP(i, 2), bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7))
    End Select
End Function


Private Function CylBody(ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                         ByVal ax As Double, ByVal ay As Double, ByVal az As Double, _
                         ByVal r As Double, ByVal h As Double) As SldWorks.Body2
    Dim p(7) As Double
    p(0) = bx: p(1) = by: p(2) = bz: p(3) = ax: p(4) = ay: p(5) = az: p(6) = r: p(7) = h
    Set CylBody = md.CreateBodyFromCyl(p)
    If CylBody Is Nothing Then Fail "CreateBodyFromCyl failed."
End Function


' An axis-aligned box x0..x1, y0..y1, z0..z1 (height along z), by the
' probed conventions.
Private Function BoxBody(ByVal x0 As Double, ByVal x1 As Double, ByVal y0 As Double, ByVal y1 As Double, _
                         ByVal z0 As Double, ByVal z1 As Double) As SldWorks.Body2
    Dim d(8) As Double
    d(0) = 0.5 * (x0 + x1): d(1) = 0.5 * (y0 + y1)
    d(2) = IIf(boxBase, z0, 0.5 * (z0 + z1))
    d(3) = 0#: d(4) = 0#: d(5) = 1#
    If boxSwap Then
        d(6) = y1 - y0: d(7) = x1 - x0
    Else
        d(6) = x1 - x0: d(7) = y1 - y0
    End If
    d(8) = z1 - z0
    Set BoxBody = md.CreateBodyFromBox3(d)
    If BoxBody Is Nothing Then Fail "CreateBodyFromBox3 failed."
End Function


Private Sub ProbeBox()
    Dim d(8) As Double, b As SldWorks.Body2, x As Variant
    Dim dx As Double, dy As Double, dz As Double
    d(0) = 10#: d(1) = 20#: d(2) = 30#: d(3) = 0#: d(4) = 0#: d(5) = 1#
    d(6) = 1#: d(7) = 2#: d(8) = 3#
    Set b = md.CreateBodyFromBox3(d)
    If b Is Nothing Then Fail "CreateBodyFromBox3 failed on the probe box."
    x = ExactBox(b)
    dx = x(3) - x(0): dy = x(4) - x(1): dz = x(5) - x(2)
    If Near(dx, 1#) And Near(dy, 2#) Then
        boxSwap = False
    ElseIf Near(dx, 2#) And Near(dy, 1#) Then
        boxSwap = True
    Else
        Fail "the probe box is " & Fmt(dx) & " x " & Fmt(dy) & " x " & Fmt(dz) & ", not 1 x 2 x 3 in any order."
    End If
    If Not Near(dz, 3#) Then Fail "the probe box's height came out " & Fmt(dz) & ", not 3."
    If Near(x(2), 30#) Then
        boxBase = True
    ElseIf Near(x(2), 28.5) Then
        boxBase = False
    Else
        Fail "the probe box runs z " & Fmt(x(2)) & " .. " & Fmt(x(5)) & " from a point at z 30."
    End If
    If Not Near(0.5 * (x(0) + x(3)), 10#) Or Not Near(0.5 * (x(1) + x(4)), 20#) Then _
        Fail "the probe box is not centred on its point in x, y: " & BoxText(b) & "."
    Note "CreateBodyFromBox3: width along " & IIf(boxSwap, "y", "x") & ", point at the " & IIf(boxBase, "base", "middle")
End Sub


' A turn of th about +z (+y towards -x), in one of the two row readings.
Private Function TurnZ(ByVal th As Double, ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double, c As Double, s As Double
    c = Cos(th): s = Sin(th)
    t(0) = c: t(4) = c: t(8) = 1#
    If transposed Then
        t(1) = -s: t(3) = s
    Else
        t(1) = s: t(3) = -s
    End If
    t(12) = 1#
    Set TurnZ = mu.CreateTransform(t)
End Function


' The body the last feature made: the one not yet named. Named, painted.
Private Sub NameNewBody(ByVal i As Long)
    Dim bodies As Variant, body As SldWorks.Body2, found As SldWorks.Body2
    Dim k As Long, n As Long
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "no body after making " & bName(i) & "."
    If UBound(bodies) + 1 <> i + 1 Then _
        Fail "after " & bName(i) & " the part has " & (UBound(bodies) + 1) & " bodies, expected " & (i + 1) & " (a body merged)."
    For k = 0 To UBound(bodies)
        Set body = bodies(k)
        If Not IsTaken(body.Name, i) Then Set found = body: n = n + 1
    Next k
    If n <> 1 Then Fail n & " unnamed bodies after " & bName(i) & ", expected 1."
    found.Name = bName(i)
    If found.Name <> bName(i) Then Fail "a body did not take the name " & bName(i) & "."
    PaintBody found, bRGB(i, 0), bRGB(i, 1), bRGB(i, 2)
End Sub


Private Function IsTaken(ByVal nm As String, ByVal upTo As Long) As Boolean
    Dim j As Long
    For j = 0 To upTo - 1
        If nm = bName(j) Then IsTaken = True: Exit Function
    Next j
End Function


'==================================================================
' Verify: each body once, its volume and its exact extent
'==================================================================
Private Sub Verify()
    Dim bodies As Variant, body As SldWorks.Body2, mp As Variant
    Dim i As Long, k As Long, hit As Long, vSum As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) + 1 <> nB Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not " & nB & "."
    For i = 0 To nB - 1
        hit = 0
        For k = 0 To UBound(bodies)
            Set body = bodies(k)
            If body.Name = bName(i) Then
                hit = hit + 1
                mp = body.GetMassProperties(1#)
                If Abs(mp(3) - bV(i)) > VOL_TOL * bV(i) Then _
                    Fail bName(i) & " is " & Fmt(mp(3)) & " m3, expected " & Fmt(bV(i)) & " m3."
                If Not BoxIs(body, i) Then Fail bName(i) & " sits at " & BoxText(body) & ", expected " & WantText(i) & "."
                vSum = vSum + mp(3)
            End If
        Next k
        If hit <> 1 Then Fail hit & " bodies named " & bName(i) & ", expected 1."
        Note "body " & bName(i) & " (" & bKind(i) & "): " & Fmt(bV(i)) & " m3, " & WantText(i)
    Next i
    Note nB & " bodies, each its volume and extent; " & Fmt(vSum) & " m3 in all"
End Sub


Private Function BoxIs(b As SldWorks.Body2, ByVal i As Long) As Boolean
    Dim x As Variant, k As Long
    x = ExactBox(b)
    For k = 0 To 5
        If Abs(x(k) - bBox(i, k)) > BOX_TOL Then Exit Function
    Next k
    BoxIs = True
End Function


Private Function ExactBox(b As SldWorks.Body2) As Variant
    Dim out(5) As Double, d(2) As Double, a As Long, sd As Long
    Dim px As Double, py As Double, pz As Double
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not b.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed."
            If sd < 0 Then out(a) = Choose(a + 1, px, py, pz) Else out(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    ExactBox = out
End Function


Private Function BoxText(b As SldWorks.Body2) As String
    Dim x As Variant
    x = ExactBox(b)
    BoxText = "x " & Fmt(x(0)) & " .. " & Fmt(x(3)) & ", y " & Fmt(x(1)) & " .. " & Fmt(x(4)) & _
              ", z " & Fmt(x(2)) & " .. " & Fmt(x(5))
End Function


Private Function WantText(ByVal i As Long) As String
    WantText = "x " & Fmt(bBox(i, 0)) & " .. " & Fmt(bBox(i, 3)) & ", y " & Fmt(bBox(i, 1)) & " .. " & _
               Fmt(bBox(i, 4)) & ", z " & Fmt(bBox(i, 2)) & " .. " & Fmt(bBox(i, 5))
End Function


Private Function Near(ByVal a As Double, ByVal b As Double) As Boolean
    Near = (Abs(a - b) < 0.001)
End Function


'==================================================================
' Export: SLDPRT and STEP AP214 (the body colours)
'==================================================================
Private Sub ExportFiles()
    Dim outDir As String
    outDir = OUT_ROOT & LINE_KEY & "\"
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(outDir, vbDirectory) = "" Then MkDir outDir

    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    exportPrefsTouched = True
    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True

    swModel.ForceRebuild3 False
    swModel.ViewZoomtofit2
    SaveOne outDir & PART_NAME & ".SLDPRT"
    SaveOne outDir & PART_NAME & ".step"
End Sub


Private Sub SaveOne(ByVal path As String)
    Dim errs As Long, warns As Long
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If errs <> 0 Then Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    If Dir(path) = "" Then Fail "SolidWorks reported no error but " & path & " is not on disk."
    Note "wrote " & path
End Sub


Private Sub PaintBody(body As SldWorks.Body2, ByVal r As Double, ByVal g As Double, ByVal b As Double)
    Dim faces As Variant, face As SldWorks.Face2
    Dim m(8) As Double, k As Long
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = 0#: m(8) = 0#
    faces = body.GetFaces
    If IsEmpty(faces) Then Fail "a body has no faces to paint."
    For k = 0 To UBound(faces)
        Set face = faces(k)
        face.MaterialPropertyValues = m
    Next k
End Sub


'==================================================================
' Housekeeping
'==================================================================
Private Sub Restore()
    On Error Resume Next
    If exportPrefsTouched Then
        swApp.SetUserPreferenceIntegerValue swStepAP, oldStepAP
        swApp.SetUserPreferenceToggle swStepExportAppearances, oldStepAppear
        exportPrefsTouched = False
    End If
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "kiln_burner_body", msg
End Sub


Private Function LogPath() As String
    If logName = "" Then logName = PART_NAME & "_build.log"
    LogPath = OUT_ROOT & LINE_KEY & "\" & logName
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
