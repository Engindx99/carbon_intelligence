Attribute VB_Name = "plant_assembly"
'==================================================================
' The pyroprocess assembly, step by step (user, 23 Nov 2026: the whole
' process in one assembly, "sirayla"; option A: the CFD solids as they
' are, each in its own domain)  ->  plant_assembly.SLDASM + jpgs
'
' tower: the kiln inlet chamber, the calciner with its gooseneck, and on
' each side a string: C5, C4, C3, C2 (C2 = C3 = C4: one solid, placed
' three times) and the C1 twin with R1; then the kiln's end
' (kiln_outlet_assembly.SLDASM: the kiln, its wall and ROTAX parts, the
' burner, the flame volume, the cooler and its mechanics) out of the
' chamber's mouth. Every part's place and turn come
' from geometry/plant_geometry.py tower_placement() (the generated TWR_
' strings): the plant frame is the calciner's (z up from the ground, the
' strings at +-x, the gooseneck and the kiln towards -y); each cyclone
' turned about its axis so its CFD riser stands on the axis of the one
' below; string 2 is string 1's mirror in x = 0, from the mirrored
' solids (<part>_m.SLDPRT, mirror_parts below). The assembly's
' frame is SolidWorks' (y up): plant (x, y, z) -> (x, z, -y).
'
' Not a CFD domain: where two CFD domains overlap (the risers) or leave
' a gap (the gooseneck arm and C5's riser inlet) is listed by
' tower_placement()["joints"] and tested (tests/test_plant_geometry.py).
'
' To run: python3 tools/sw_run.py plant_assembly.tower from WSL, after
' the parts are built. Outputs geometry\output\2500\plant_assembly.SLDASM,
' plant_assembly_<view>.jpg and plant_assembly_build.log.
'==================================================================

Option Explicit

Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_PARTS                      As Double  = 13           ' the tower's components [derived]
Const TWR_1                        As String  = "kiln_inlet_chamber|kiln_inlet_chamber.SLDPRT|0|0|1|1|0|0|0|1|0|0|6.6|0;calciner|calciner.SLDPRT|1|0|0|0|0|-1|0|1|0|0|12.550030915|0;C5_1|C5_plant.SLDPRT|1|0|0|0|0|-1|0|1|0|16.781329542|23.790589231|16.936925264;C4_1|C4.SLDPRT|0.729088696|0|-0.684419223|-0.684419223|0|-0.729088696|0|1|0|23.584177627|38.322335263|16.936925264;C3_1|C4.SLDPRT|-0.729088696|0|0.684419223|0.684419223|0|0.729088696|0|1|0|16.781329542|52.422335263|16.936925264;C2_1|C4.SLDPRT|0.729088696|0|-0.684419223|-0.684419223|0|-0.729088696|0|1|0|23.584177627|66.522335263|16.936925264;C1_twin_1|C1_twin.SLDPRT|1|0|0|0|0|-1|0|1|0|23.584177627|89.477335263|10.209538903;C5_2|C5_plant_m.SLDPRT|1|0|0|0|0|-1|0|1|0|-16.781329542|23.790589231|16.936925264;C4_2|C4_m.SLDPRT|0.729088696|0|0.684419223|0.684419223|0|-0.729088696|0|1|0|-23.584177627|38.322335263|16.936925264;" ' plant_geometry.tower_placement() parts
Const TWR_2                        As String  = "C3_2|C4_m.SLDPRT|-0.729088696|0|-0.684419223|-0.684419223|0|0.729088696|0|1|0|-16.781329542|52.422335263|16.936925264;C2_2|C4_m.SLDPRT|0.729088696|0|0.684419223|0.684419223|0|-0.729088696|0|1|0|-23.584177627|66.522335263|16.936925264;C1_twin_2|C1_twin_m.SLDPRT|1|0|0|0|0|-1|0|1|0|-23.584177627|89.477335263|10.209538903;kiln_outlet|kiln_outlet_assembly.SLDASM|1|0|0|0|0.999550304|0.029986509|0|-0.029986509|0.999550304|0|10|3.4;" ' plant_geometry.tower_placement() parts
Const TWR_3                        As String  = ""           ' plant_geometry.tower_placement() parts
Const TWR_4                        As String  = ""           ' plant_geometry.tower_placement() parts
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Dim swApp As SldWorks.SldWorks
Dim mu As SldWorks.MathUtility
Dim buildLog As String
Dim phase As String


Sub tower()
    Dim why As String, outDir As String, tpl As String, all As String
    Dim asmDoc As SldWorks.ModelDoc2, asm As SldWorks.AssemblyDoc
    Dim doc As SldWorks.ModelDoc2, comp As SldWorks.Component2
    Dim recs As Variant, f As Variant, comps As Variant
    Dim e As Long, w As Long, i As Long, k As Long, n As Long
    Dim t(15) As Double, pb As Variant, bx As Variant
    Dim cx(2) As Double, want(2) As Double, dmax As Double, d As Double

    buildLog = ""
    phase = "starting up"
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    Set mu = swApp.GetMathUtility
    outDir = OUT_ROOT & LINE_KEY & "\"

    all = TWR_1 & TWR_2 & TWR_3 & TWR_4
    recs = Split(all, ";")

    phase = "opening the parts"
    For i = 0 To UBound(recs)
        If Len(recs(i)) > 0 Then
            f = Split(recs(i), "|")
            If UBound(f) <> 13 Then Fail "part record " & i & ": " & (UBound(f) + 1) & " fields, not 14."
            If Dir(outDir & f(1)) = "" Then Fail outDir & f(1) & " is not built yet."
            Set doc = swApp.OpenDoc6(outDir & f(1), IIf(UCase$(Right$(f(1), 6)) = "SLDASM", swDocASSEMBLY, swDocPART), _
                                     swOpenDocOptions_Silent, "", e, w)
            If doc Is Nothing Then Fail "could not open " & f(1) & " (error " & e & ")."
        End If
    Next i

    phase = "making the assembly"
    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateAssembly)
    Set asmDoc = swApp.NewDocument(tpl, 0, 0, 0)
    If asmDoc Is Nothing Then Fail "could not create an assembly from the default template (" & tpl & ")."
    Set asm = asmDoc
    For i = 0 To UBound(recs)
        If Len(recs(i)) > 0 Then
            f = Split(recs(i), "|")
            Set comp = asm.AddComponent5(outDir & f(1), swAddComponentConfigOptions_CurrentSelectedConfig, "", _
                                         False, "", 0#, 0#, 0#)
            If comp Is Nothing Then Fail "AddComponent5 refused " & f(1) & "."
            ' the part's axes (rows) and origin; the rows as the transform's
            ' first nine terms (the reading kiln_flame.bas's CoolerPlacement found)
            For k = 0 To 15: t(k) = 0#: Next k
            For k = 0 To 8: t(k) = Val(f(2 + k)): Next k
            t(9) = Val(f(11)): t(10) = Val(f(12)): t(11) = Val(f(13)): t(12) = 1#
            comp.Transform2 = mu.CreateTransform(t)
            asmDoc.ClearSelection2 True
            comp.Select4 False, Nothing, False
            asm.FixComponent
            asmDoc.ClearSelection2 True
            ' check: the part box's centre, carried by the same rows, is the
            ' component box's centre (the boxes are not exact: 1.5 m)
            Set doc = swApp.GetOpenDocumentByName(outDir & f(1))
            If doc.GetType = swDocASSEMBLY Then
                Dim subAsm As SldWorks.AssemblyDoc
                Set subAsm = doc
                pb = subAsm.GetBox(0)
            Else
                pb = doc.GetPartBox(True)
            End If
            bx = comp.GetBox(False, False)
            For k = 0 To 2
                cx(k) = 0.5 * (pb(k) + pb(k + 3))
            Next k
            dmax = 0#
            For k = 0 To 2
                want(k) = t(9 + k) + cx(0) * t(k) + cx(1) * t(3 + k) + cx(2) * t(6 + k)
                d = Abs(0.5 * (bx(k) + bx(k + 3)) - want(k))
                If d > dmax Then dmax = d
            Next k
            If dmax > 1.5 Then Fail f(0) & " landed " & Fmt(dmax) & " m off its place (box centre)."
            Note "placed " & f(0) & " (" & f(1) & ") at (" & Fmt(t(9)) & ", " & Fmt(t(10)) & ", " & Fmt(t(11)) & _
                 "), box centre within " & Fmt(dmax) & " m"
            n = n + 1
        End If
    Next i
    asmDoc.ForceRebuild3 False

    phase = "verifying the assembly"
    comps = asm.GetComponents(True)
    If IsEmpty(comps) Then Fail "the assembly has no components."
    If UBound(comps) + 1 <> CLng(N_PARTS) Or n <> CLng(N_PARTS) Then _
        Fail "the assembly has " & (UBound(comps) + 1) & " components, the list " & N_PARTS & "."

    phase = "saving"
    Dim vw As Variant, vn As Variant
    vn = Array("front", "right", "top", "isometric")
    k = 0
    For Each vw In Array(swFrontView, swRightView, swTopView, swIsometricView)
        asmDoc.ShowNamedView2 "", CLng(vw)
        asmDoc.ViewZoomtofit2
        asmDoc.GraphicsRedraw2
        asmDoc.Extension.SaveAs outDir & "plant_assembly_" & vn(k) & ".jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
        k = k + 1
    Next vw
    asmDoc.Extension.SaveAs outDir & "plant_assembly.SLDASM", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    If e <> 0 Then Fail "could not write plant_assembly.SLDASM (error " & e & ")."
    Note "wrote " & outDir & "plant_assembly.SLDASM"
    WriteLog "plant_assembly built, verified and saved"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "plant_assembly saved." & vbLf & vbLf & buildLog, vbInformation, "Plant assembly"
    Exit Sub

Failed:
    why = Err.Description
    WriteLog "plant_assembly ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "plant_assembly ABORTED:" & vbLf & why, vbCritical, "Plant assembly"
End Sub


' The mirrored solids string 2 is built from (tower_placement(): string 2
' is string 1's mirror in x = 0): each part mirrored about its own x = 0
' plane (IPartDoc.MirrorPart2 on the default plane whose normal is x),
' the link broken, written as <part>_m.SLDPRT. Checked by the extent:
' x min / max swapped and negated, y and z the same. Run after the parts
' are built: python3 tools/sw_run.py plant_assembly.mirror_parts.
Sub mirror_parts()
    Dim why As String, outDir As String, nm As Variant
    Dim doc As SldWorks.ModelDoc2, part As SldWorks.PartDoc, res As SldWorks.ModelDoc2
    Dim f As SldWorks.Feature, feat As SldWorks.Feature, e As Long, w As Long, k As Long
    Dim b0 As Variant, b1 As Variant, ok As Boolean, nPl As Long

    buildLog = ""
    phase = "starting up"
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    outDir = OUT_ROOT & LINE_KEY & "\"
    For Each nm In Array("C4", "C5_plant", "C1_twin")
        phase = "mirroring " & nm
        If Dir(outDir & nm & ".SLDPRT") = "" Then Fail outDir & nm & ".SLDPRT is not built yet."
        Set doc = swApp.OpenDoc6(outDir & nm & ".SLDPRT", swDocPART, swOpenDocOptions_Silent, "", e, w)
        If doc Is Nothing Then Fail "could not open " & nm & ".SLDPRT (error " & e & ")."
        Set part = doc
        b0 = part.GetPartBox(True)
        ok = False: nPl = 0
        Set f = doc.FirstFeature
        Do While Not f Is Nothing And nPl < 3
            If f.GetTypeName2 = "RefPlane" Then
                nPl = nPl + 1
                swApp.ActivateDoc3 doc.GetTitle, False, swDontRebuildActiveDoc, e
                doc.ClearSelection2 True
                f.Select2 False, 0
                Set res = Nothing
                On Error Resume Next
                Set feat = part.MirrorPart2(True, swMirrorPartOptions_ImportSolids, res)
                On Error GoTo Failed
                If Not res Is Nothing Then
                    b1 = res.GetPartBox(True)
                    If Abs(b1(0) + b0(3)) < 0.05 And Abs(b1(3) + b0(0)) < 0.05 And Abs(b1(1) - b0(1)) < 0.05 And _
                       Abs(b1(4) - b0(4)) < 0.05 And Abs(b1(2) - b0(2)) < 0.05 And Abs(b1(5) - b0(5)) < 0.05 Then
                        res.Extension.SaveAs outDir & nm & "_m.SLDPRT", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
                        If e <> 0 Then Fail "could not write " & nm & "_m.SLDPRT (error " & e & ")."
                        swApp.CloseDoc res.GetTitle
                        Note "mirrored " & nm & " about plane " & nPl & " (" & f.Name & ") -> " & nm & "_m.SLDPRT"
                        ok = True
                        Exit Do
                    End If
                    swApp.CloseDoc res.GetTitle
                End If
            End If
            Set f = f.GetNextFeature
        Loop
        swApp.CloseDoc doc.GetTitle
        If Not ok Then Fail nm & ": no default plane gave the mirror in x = 0 (MirrorPart2)."
    Next nm
    WriteLog "mirror_parts done"
    Exit Sub

Failed:
    why = Err.Description
    WriteLog "mirror_parts ABORTED while " & phase & ": " & why
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "plant_assembly", msg
End Sub


Private Sub WriteLog(ByVal outcome As String)
    Dim fn As Integer
    On Error Resume Next
    fn = FreeFile
    Open OUT_ROOT & LINE_KEY & "\plant_assembly_build.log" For Output As #fn
    Print #fn, outcome & vbLf & buildLog;
    Close #fn
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.###")
End Function
