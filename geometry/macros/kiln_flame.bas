Attribute VB_Name = "kiln_flame"
'==================================================================
' The flame zone's CFD fluid volume: the kiln hood, the kiln's bore over
' the burning zone and the burner's channels  ->  SLDPRT + STEP
'
' A CFD input (user decision, 23 Nov 2026: the kiln outlet and the burner
' integrated). Kiln frame (kiln.bas): the kiln's axis z, its hood end at
' z = KILN_L, y up; the hood level, the kiln falling at its slope.
'
'   hood                      the hood's inside: a box on the cooler's roof
'                             round the kiln's end (kiln_hood())
'                             (its flat floor split into the cooler's two hood
'                             segments: secondary air in, tertiary air in)
'   tertiary_air_mouth        a stub on its roof: the tertiary air out
'   kiln_bore                 the kiln's gas bore back over the burning zone
'   void_burner_*             the burner (tip ring, castable) cut out
'   void_hopper_p, _m         the hood's bottom corners beside the cooler cut
'                             off: the hopper's walls (Fuller ABC Inlet)
'   (no clinker bed: the bore is whole; the strip of wall under the bed is
'    a region set in the CFD, plant_geometry.kiln_flame()["bed_strip"])
'   + the channels            coal, axial, swirl copied from kiln_burner.SLDPRT
'                             and placed by kiln_burner_placement()
'
' Boundary faces (KFL_FACES; every other face is wall), painted for
' Fluent: secondary_air_in, tertiary_supply_in, tertiary_air_out,
' kiln_gas_out, coal_in, axial_in, swirl_in. Each is found by a point in
' it and its normal and checked by its area.
'
' Bodies and faces from geometry/plant_geometry.py kiln_flame(); the
' builder is kiln_burner_body.bas's.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py kiln_flame_solid.main (needs
' kiln_burner.SLDPRT), then kiln_flame_solid.assembly (needs kiln_wall,
' kiln_rotax, kiln_burner, kiln_burner_body). Outputs
' geometry\output\2500\kiln_flame.SLDPRT, .step, kiln_flame_build.log;
' kiln_outlet_assembly.SLDASM + jpgs.
'==================================================================

Option Explicit

Const PART_NAME As String = "kiln_flame"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 7            ' bodies before joining [derived]
Const N_GROUPS                     As Double  = 1            ' bodies in the part [derived]
Const N_FACES                      As Double  = 7            ' boundary faces [derived]
Const KFL_1                        As String  = "hood|flame|fbox|0|0.289569723|62.982658106|0|0.029986509|0.999550304|0|0.999550304|-0.029986509|1|0|0|5.98|7.2|7.6|327.2256|-3.8|-3.398471032|59.886051265|3.8|3.977610478|66.079264946|0.85|0.35|0.1;kiln_bore|flame|cyl|0|0|25|0|0|1|2.4|35.072072|634.64926315|-2.4|-2.4|25|2.4|2.4|60.072072|0.85|0.35|0.1;void_hopper_p|flame|fbox|4.474519053|-2.082216216|63.053811684|0|0.029986509|0.999550304|0.5|0.865635955|-0.025969079|0.866025404|-0.499775152|0.014993255|7.98|4.6|3.058845727|112.28410894|2|-4.957192628|58.982946066|6.949038106|0.792760196|67.124677302|0.85|0.35|0.1;void_hopper_m|flame|fbox|-4.474519053|-2.082216216|63.053811684|0|0.029986509|0.999550304|-0.5|0.865635955|-0.025969079|-0.866025404|-0.499775152|0.014993255|7.98|4.6|3.058845727|112.28410894|-6.949038106|-4.957192628|58.982946066|-2|0.792760196|67.124677302|0.85|0.35|0.1;" ' plant_geometry.kiln_flame() bodies
Const KFL_2                        As String  = "tertiary_air_mouth|flame|cyl|0|3.931781096|64.369064363|0|0.999550304|-0.029986509|1.21965|7.3189|34.203151672|-1.21965|3.895208051|62.930494574|1.21965|11.283962859|65.588165891|0.85|0.35|0.1;void_burner_tip_ring|flame|cyl|0|0|59.75|0|0|1|0.314077459|0.698251959|0.216389195|-0.314077459|-0.314077459|59.75|0.314077459|0.314077459|60.448251959|0.85|0.35|0.1;void_burner_castable|flame|cyl|0|0|60.447251959|0|0|1|0.304655135|7.545374241|2.200126556|-0.304655135|-0.304655135|60.447251959|0.304655135|0.304655135|67.9926262|0.85|0.35|0.1;" ' plant_geometry.kiln_flame() bodies
Const KFL_3                        As String  = ""           ' plant_geometry.kiln_flame() bodies
Const KFL_4                        As String  = ""           ' plant_geometry.kiln_flame() bodies
Const KFL_GROUPS                   As String  = "flame|-1|7;" ' the part's body: name|V (-1: parts overlap)|parts
Const KFL_FACES                    As String  = "secondary_air_in|0|-3.353641201|61.596281835|0|-0.999550304|0.029986509|11.96|1|0.55|0;tertiary_supply_in|0|-3.263981539|64.584937242|0|-0.999550304|0.029986509|11.96|0.95|0.8|0.1;tertiary_air_out|0|11.247389813|64.149596102|0|0.999550304|-0.029986509|4.67326397|0.6|0.2|0.8;kiln_gas_out|0|0|25|0|0|-1|18.095573685|0.2|0.2|0.9;coal_in|0|0.033669104|60.797448325|0|0|1|0.034467921|0.55|0|0;axial_in|0|0.2165195|60.31|0|0|1|0.035743357|0.9|0|0;swirl_in|0|0.184814689|60.31|0|0|1|0.026647279|1|0.45|0.45;" ' boundaries: name|point|outward normal|area|rgb
Const KFL_R11                      As Double  = -1#          ' the burner's x axis, kiln x [derived]
Const KFL_R12                      As Double  = 0#           ' the burner's x axis, kiln y [derived]
Const KFL_R13                      As Double  = 0#           ' the burner's x axis, kiln z [derived]
Const KFL_R21                      As Double  = 0#           ' the burner's y axis, kiln x [derived]
Const KFL_R22                      As Double  = 1#           ' the burner's y axis, kiln y [derived]
Const KFL_R23                      As Double  = -0#          ' the burner's y axis, kiln z [derived]
Const KFL_R31                      As Double  = 0#           ' the burner's z axis, kiln x [derived]
Const KFL_R32                      As Double  = -0#          ' the burner's z axis, kiln y [derived]
Const KFL_R33                      As Double  = -1#          ' the burner's z axis, kiln z [derived]
Const KFL_TX                       As Double  = 0#           ' the burner's tip, kiln x [derived]
Const KFL_TY                       As Double  = 0#           ' the burner's tip, kiln y [derived]
Const KFL_TZ                       As Double  = 59.75        ' the burner's tip, kiln z [derived]
Const KFL_COAL_X0                  As Double  = -0.104745    ' the copied coal channel's extent, kiln frame [derived]
Const KFL_COAL_Y0                  As Double  = -0.071076    ' the copied coal channel's extent, kiln frame [derived]
Const KFL_COAL_Z0                  As Double  = 59.75        ' the copied coal channel's extent, kiln frame [derived]
Const KFL_COAL_X1                  As Double  = 0.104745     ' the copied coal channel's extent, kiln frame [derived]
Const KFL_COAL_Y1                  As Double  = 0.138414     ' the copied coal channel's extent, kiln frame [derived]
Const KFL_COAL_Z1                  As Double  = 60.797448    ' the copied coal channel's extent, kiln frame [derived]
Const KFL_BRN_X0                   As Double  = -0.376893    ' the placed whole burner's extent, kiln frame [derived]
Const KFL_BRN_Y0                   As Double  = -0.496242    ' the placed whole burner's extent, kiln frame [derived]
Const KFL_BRN_Z0                   As Double  = 59.75        ' the placed whole burner's extent, kiln frame [derived]
Const KFL_BRN_X1                   As Double  = 0.987145     ' the placed whole burner's extent, kiln frame [derived]
Const KFL_BRN_Y1                   As Double  = 0.948514     ' the placed whole burner's extent, kiln frame [derived]
Const KFL_BRN_Z1                   As Double  = 70.215061    ' the placed whole burner's extent, kiln frame [derived]
Const KFL_COO_R11                  As Double  = 0#           ' the cooler's x axis, kiln x [derived]
Const KFL_COO_R12                  As Double  = 0.029986509  ' the cooler's x axis, kiln y [derived]
Const KFL_COO_R13                  As Double  = 0.999550304  ' the cooler's x axis, kiln z [derived]
Const KFL_COO_R21                  As Double  = 1#           ' the cooler's y axis, kiln x [derived]
Const KFL_COO_R22                  As Double  = 0#           ' the cooler's y axis, kiln y [derived]
Const KFL_COO_R23                  As Double  = 0#           ' the cooler's y axis, kiln z [derived]
Const KFL_COO_R31                  As Double  = 0#           ' the cooler's z axis, kiln x [derived]
Const KFL_COO_R32                  As Double  = 0.999550304  ' the cooler's z axis, kiln y [derived]
Const KFL_COO_R33                  As Double  = -0.029986509 ' the cooler's z axis, kiln z [derived]
Const KFL_COO_TX                   As Double  = 0#           ' the cooler's origin, kiln x [derived]
Const KFL_COO_TY                   As Double  = -6.397122    ' the cooler's origin, kiln y [derived]
Const KFL_COO_TZ                   As Double  = 60.191914    ' the cooler's origin, kiln z [derived]
Const KFL_COO_X0                   As Double  = -2#          ' the placed cooler's extent, kiln frame [derived]
Const KFL_COO_Y0                   As Double  = -6.397122    ' the placed cooler's extent, kiln frame [derived]
Const KFL_COO_Z0                   As Double  = 59.850301    ' the placed cooler's extent, kiln frame [derived]
Const KFL_COO_X1                   As Double  = 2#           ' the placed cooler's extent, kiln frame [derived]
Const KFL_COO_Y1                   As Double  = 6.0065       ' the placed cooler's extent, kiln frame [derived]
Const KFL_COO_Z1                   As Double  = 94.076669    ' the placed cooler's extent, kiln frame [derived]
Const KFL_CBD_X0                   As Double  = -5.831446    ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_CBD_Y0                   As Double  = -8.505295    ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_CBD_Z0                   As Double  = 59.690139    ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_CBD_X1                   As Double  = 5.831446     ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_CBD_Y1                   As Double  = -1.970114    ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_CBD_Z1                   As Double  = 94.539374    ' the placed cooler_body's extent, kiln frame [derived]
Const KFL_SPLIT_AX                 As Double  = -2.5         ' the hood floor's split line, end A, x [derived]
Const KFL_SPLIT_AY                 As Double  = -3.308811    ' the hood floor's split line, end A, y [derived]
Const KFL_SPLIT_AZ                 As Double  = 63.09061     ' the hood floor's split line, end A, z [derived]
Const KFL_SPLIT_BX                 As Double  = 2.5          ' the hood floor's split line, end B, x [derived]
Const KFL_SPLIT_BY                 As Double  = -3.308811    ' the hood floor's split line, end B, y [derived]
Const KFL_SPLIT_BZ                 As Double  = 63.09061     ' the hood floor's split line, end B, z [derived]
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
Dim bName() As String, bGroup() As String, bKind() As String
Dim nG As Long, gName() As String, gV() As Double, gN() As Long
Dim bP() As Double, bV() As Double, bBox() As Double, bRGB() As Double

' CreateBodyFromBox3's conventions, probed: width along y (not x)?
' the given point the base's centre (not the box's)?
Dim boxSwap As Boolean, boxBase As Boolean

Dim buildLog As String
Dim scr As SldWorks.ModelDoc2     ' the bends' one scratch part (kept open over a build: memory)
Dim scrTitle As String
Dim scrSeen As String             ' its bodies taken so far: |name|name|
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
    phase = "splitting the hood floor"
    SplitFloor
    phase = "tagging the boundary faces"
    TagFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog PART_NAME & " built, verified and exported"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln flame zone"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln flame zone"
    End If
End Sub


'==================================================================
' assembly: the kiln's end with the burner in it -- the kiln wall and its
' ROTAX parts (kiln frame), the burner's channels and its whole body
' (placed: kiln_burner_placement(), rows KFL_R, tip KFL_T) and this flame
' zone volume, and the cooler's volume under the hood (cooler_placement():
' its hood_1 / hood_2 on the hood floor's two faces)  ->  kiln_outlet_assembly.SLDASM
' + jpgs. The parts stay
' separate files, so rebuilding any updates it.
'==================================================================
Sub assembly()
    Dim why As String, outDir As String, tpl As String
    Dim asmDoc As SldWorks.ModelDoc2, asm As SldWorks.AssemblyDoc
    Dim doc As SldWorks.ModelDoc2, comp As SldWorks.Component2
    Dim parts As Variant, placed As Variant, comps As Variant
    Dim e As Long, w As Long, k As Long, j As Long, bx As Variant, ok As Boolean

    buildLog = ""
    logName = "kiln_outlet_assembly_build.log"
    phase = "starting up"
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    Set mu = swApp.GetMathUtility
    outDir = OUT_ROOT & LINE_KEY & "\"
    parts = Array("kiln_wall.SLDPRT", "kiln_rotax.SLDPRT", "kiln_burner.SLDPRT", "kiln_burner_body.SLDPRT", PART_NAME & ".SLDPRT", _
                  "cooler.SLDPRT", "kiln.SLDPRT", "cooler_body.SLDPRT")
    placed = Array(False, False, True, True, False, True, False, True)

    phase = "opening the parts"
    For k = 0 To UBound(parts)
        If Dir(outDir & parts(k)) = "" Then Fail outDir & parts(k) & " is not built yet."
        Set doc = swApp.OpenDoc6(outDir & parts(k), swDocPART, swOpenDocOptions_Silent, "", e, w)
        If doc Is Nothing Then Fail "could not open " & parts(k) & " (error " & e & ")."
    Next k

    phase = "making the assembly"
    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateAssembly)
    Set asmDoc = swApp.NewDocument(tpl, 0, 0, 0)
    If asmDoc Is Nothing Then Fail "could not create an assembly from the default template (" & tpl & ")."
    Set asm = asmDoc
    For k = 0 To UBound(parts)
        Set comp = asm.AddComponent5(outDir & parts(k), swAddComponentConfigOptions_CurrentSelectedConfig, "", _
                                     False, "", 0#, 0#, 0#)
        If comp Is Nothing Then Fail "AddComponent5 refused " & parts(k) & "."
        ' AddComponent5 puts the part's box centre at the point: the
        ' identity (or the burner's placement) puts its origin right
        If placed(k) Then
            ' the transform's row convention is not trusted: both
            ' readings, the whole burner's extent decides
            ok = False
            For j = 0 To 1
                If parts(k) = "cooler.SLDPRT" Or parts(k) = "cooler_body.SLDPRT" Then
                    comp.Transform2 = CoolerPlacement(j = 1)
                Else
                    comp.Transform2 = Placement(j = 1)
                End If
                asmDoc.ForceRebuild3 False
                If parts(k) = "kiln_burner.SLDPRT" Then ok = True: Exit For
                bx = comp.GetBox(False, False)
                If Not IsEmpty(bx) Then
                    If parts(k) = "cooler.SLDPRT" Then
                        ' the cooler under the hood: its roof's openings on the flame volume's floor
                        If Abs(bx(0) - KFL_COO_X0) < 0.05 And Abs(bx(1) - KFL_COO_Y0) < 0.05 And Abs(bx(2) - KFL_COO_Z0) < 0.05 And _
                           Abs(bx(3) - KFL_COO_X1) < 0.05 And Abs(bx(4) - KFL_COO_Y1) < 0.05 And Abs(bx(5) - KFL_COO_Z1) < 0.05 Then ok = True: Exit For
                    ElseIf parts(k) = "cooler_body.SLDPRT" Then
                        ' the cooler's mechanical parts, placed as the cooler
                        If Abs(bx(0) - KFL_CBD_X0) < 0.1 And Abs(bx(1) - KFL_CBD_Y0) < 0.1 And Abs(bx(2) - KFL_CBD_Z0) < 0.1 And _
                           Abs(bx(3) - KFL_CBD_X1) < 0.1 And Abs(bx(4) - KFL_CBD_Y1) < 0.1 And Abs(bx(5) - KFL_CBD_Z1) < 0.1 Then ok = True: Exit For
                    ElseIf Abs(bx(2) - KFL_BRN_Z0) < 0.05 And Abs(bx(5) - KFL_BRN_Z1) < 0.05 And _
                       Abs(bx(0) - KFL_BRN_X0) < 0.05 And Abs(bx(4) - KFL_BRN_Y1) < 0.05 Then
                        ok = True: Exit For
                    End If
                End If
            Next j
            If Not ok Then Fail parts(k) & " landed at " & BoxOf(bx) & " in neither reading, not at its placement."
            Note "placed " & parts(k) & IIf(j = 1, " (transposed reading)", "")
        Else
            comp.Transform2 = mu.CreateTransform(Identity())
        End If
        asmDoc.ClearSelection2 True
        comp.Select4 False, Nothing, False
        asm.FixComponent
        asmDoc.ClearSelection2 True
    Next k
    asmDoc.ForceRebuild3 False

    phase = "verifying the assembly"
    comps = asm.GetComponents(True)
    If IsEmpty(comps) Then Fail "the assembly has no components."
    If UBound(comps) <> UBound(parts) Then Fail "the assembly has " & (UBound(comps) + 1) & " components, not " & (UBound(parts) + 1) & "."
    For k = 0 To UBound(comps)
        Set comp = comps(k)
        bx = comp.GetBox(False, False)
        Note "component " & comp.Name2 & ": " & BoxOf(bx)
    Next k

    phase = "saving"
    Dim vw As Variant, vn As Variant
    vn = Array("side", "top", "isometric", "hood")
    k = 0
    For Each vw In Array(swRightView, swTopView, swIsometricView, swBackView)
        asmDoc.ShowNamedView2 "", CLng(vw)
        asmDoc.ViewZoomtofit2
        asmDoc.GraphicsRedraw2
        asmDoc.Extension.SaveAs outDir & "kiln_outlet_assembly_" & vn(k) & ".jpg", _
            swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
        k = k + 1
    Next vw
    ' The gas (CFD) volumes are solids. (Display states were tried, 23 Nov
    ' 2026: CreateDisplayState / RenameDisplayState refused on this assembly.)
    ' Only the kiln's bore (kiln.SLDPRT, the inlet side) is hidden; the
    ' outlet's gas parts (kiln_flame, cooler) stay: their faces are painted
    ' see-through, so the burner's tip shows through them (user, 23 Nov 2026).
    Dim nGas As Long
    For k = 0 To UBound(comps)
        Set comp = comps(k)
        If Left$(comp.Name2, 5) = "kiln-" Then
            comp.Visible = swComponentHidden: nGas = nGas + 1
        End If
    Next k
    asmDoc.ShowNamedView2 "", swBackView
    asmDoc.ViewZoomtofit2
    asmDoc.GraphicsRedraw2
    asmDoc.Extension.SaveAs outDir & "kiln_outlet_assembly_from_inlet.jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    Note "view from the kiln inlet, kiln bore hidden, flame volume and cooler see-through: kiln_outlet_assembly_from_inlet.jpg"
    Note nGas & " gas volume saved hidden (kiln, the inlet side): Show it in the FeatureManager"
    asmDoc.ShowNamedView2 "", swIsometricView
    asmDoc.ViewZoomtofit2
    asmDoc.Extension.SaveAs outDir & "kiln_outlet_assembly.SLDASM", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    If e <> 0 Then Fail "could not write kiln_outlet_assembly.SLDASM (error " & e & ")."
    Note "wrote " & outDir & "kiln_outlet_assembly.SLDASM"
    WriteLog "kiln_outlet_assembly built, verified and saved"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_outlet_assembly saved." & vbLf & vbLf & buildLog, vbInformation, "Kiln outlet assembly"
    Exit Sub

Failed:
    why = Err.Description
    WriteLog "kiln_outlet_assembly ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_outlet_assembly ABORTED:" & vbLf & why, vbCritical, "Kiln outlet assembly"
End Sub


' The gas (CFD) volumes among the assembly's components.
Private Function IsGas(ByVal nm As String) As Boolean
    IsGas = (Left$(nm, 11) = "kiln_flame-" Or Left$(nm, 7) = "cooler-" Or Left$(nm, 5) = "kiln-")
End Function


' The cooler's placement (plant_geometry.cooler_placement()): its axes in
' the kiln frame (rows, or their columns), its origin, scale 1.
Private Function CoolerPlacement(ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double
    If transposed Then
        t(0) = KFL_COO_R11: t(1) = KFL_COO_R21: t(2) = KFL_COO_R31: t(3) = KFL_COO_R12: t(4) = KFL_COO_R22: t(5) = KFL_COO_R32
        t(6) = KFL_COO_R13: t(7) = KFL_COO_R23: t(8) = KFL_COO_R33
    Else
        t(0) = KFL_COO_R11: t(1) = KFL_COO_R12: t(2) = KFL_COO_R13: t(3) = KFL_COO_R21: t(4) = KFL_COO_R22: t(5) = KFL_COO_R23
        t(6) = KFL_COO_R31: t(7) = KFL_COO_R32: t(8) = KFL_COO_R33
    End If
    t(9) = KFL_COO_TX: t(10) = KFL_COO_TY: t(11) = KFL_COO_TZ: t(12) = 1#
    Set CoolerPlacement = mu.CreateTransform(t)
End Function


' The burner's placement as a component transform: rotation (its axes'
' rows, or their columns), the tip, scale 1.
Private Function Placement(ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double
    If transposed Then
        t(0) = KFL_R11: t(1) = KFL_R21: t(2) = KFL_R31: t(3) = KFL_R12: t(4) = KFL_R22: t(5) = KFL_R32
        t(6) = KFL_R13: t(7) = KFL_R23: t(8) = KFL_R33
    Else
        t(0) = KFL_R11: t(1) = KFL_R12: t(2) = KFL_R13: t(3) = KFL_R21: t(4) = KFL_R22: t(5) = KFL_R23
        t(6) = KFL_R31: t(7) = KFL_R32: t(8) = KFL_R33
    End If
    t(9) = KFL_TX: t(10) = KFL_TY: t(11) = KFL_TZ: t(12) = 1#
    Set Placement = mu.CreateTransform(t)
End Function


Private Function BoxOf(bx As Variant) As String
    If IsEmpty(bx) Then BoxOf = "(no box)": Exit Function
    BoxOf = "x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
            ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5))
End Function


' The burner's channels (kiln_burner.SLDPRT: coal, axial, swirl), copied,
' placed (both readings of the frame's rows: the coal channel's extent
' decides) and joined onto the flame body: their outlets on the tip
' plane open into it, their inlets stay its boundary faces.
Private Sub AddChannels(acc As SldWorks.Body2)
    Dim path As String, doc As SldWorks.ModelDoc2, e As Long, w As Long, wasOpen As Boolean
    Dim bodies As Variant, j As Long, k As Long, b As SldWorks.Body2, t As SldWorks.Body2
    Dim res As Variant, rd As Long, x As Variant
    path = OUT_ROOT & LINE_KEY & "\kiln_burner.SLDPRT"
    If Dir(path) = "" Then Fail "kiln_burner.SLDPRT is not built yet (kiln_burner_solid.main)."
    Set doc = swApp.GetOpenDocumentByName(path)
    wasOpen = Not doc Is Nothing
    If Not wasOpen Then Set doc = swApp.OpenDoc6(path, swDocPART, swOpenDocOptions_Silent, "", e, w)
    If doc Is Nothing Then Fail "could not open kiln_burner.SLDPRT (error " & e & ")."
    bodies = doc.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "kiln_burner.SLDPRT has no bodies."
    If UBound(bodies) <> 2 Then Fail "kiln_burner.SLDPRT has " & (UBound(bodies) + 1) & " bodies, not 3."
    ' which reading of the rows: by the coal channel
    rd = -1
    For j = 0 To 2
        Set b = bodies(j)
        If b.Name = "coal" Then
            For k = 0 To 1
                Set t = b.Copy
                t.ApplyTransform Frame(KFL_R11, KFL_R12, KFL_R13, KFL_R21, KFL_R22, KFL_R23, _
                                       KFL_R31, KFL_R32, KFL_R33, KFL_TX, KFL_TY, KFL_TZ, k = 1)
                x = ExactBox(t)
                If Near(x(0), KFL_COAL_X0) And Near(x(1), KFL_COAL_Y0) And Near(x(2), KFL_COAL_Z0) And _
                   Near(x(3), KFL_COAL_X1) And Near(x(4), KFL_COAL_Y1) And Near(x(5), KFL_COAL_Z1) Then rd = k: Exit For
            Next k
        End If
    Next j
    If rd < 0 Then Fail "the coal channel lands at its placement in neither reading of the frame."
    For j = 0 To 2
        Set b = bodies(j)
        Set t = b.Copy
        t.ApplyTransform Frame(KFL_R11, KFL_R12, KFL_R13, KFL_R21, KFL_R22, KFL_R23, _
                               KFL_R31, KFL_R32, KFL_R33, KFL_TX, KFL_TY, KFL_TZ, rd = 1)
        res = acc.Operations2(SWBODYADD, t, e)
        If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail "joining the " & b.Name & " channel failed (" & e & ")."
        If UBound(res) <> 0 Then Fail "joining the " & b.Name & " channel left " & (UBound(res) + 1) & " bodies (its outlets do not reach the flame volume)."
        Set acc = res(0)
    Next j
    If Not wasOpen Then swApp.CloseDoc doc.GetTitle
    swApp.ActivateDoc3 swModel.GetTitle, False, swDontRebuildActiveDoc, e
    Note "the burner's 3 channels joined (frame read " & IIf(rd = 1, "transposed", "by rows") & ")"
End Sub


'==================================================================
' The boundary faces: each a planar face holding its point, square to
' its normal, of its area; painted (the colours carry the names into
' Fluent). Every other face is wall.
'==================================================================
Private Sub TagFaces()
    Dim recs As Variant, f As Variant, j As Long, i As Long, nF As Long
    Dim nm() As String, P() As Double, cnt() As Long, ar() As Double
    Dim body As SldWorks.Body2, faces As Variant, face As SldWorks.Face2, surf As SldWorks.Surface
    Dim pp As Variant, q As Variant, hit As Long, k As Long, nWall As Long, aWall As Double

    recs = Split(KFL_FACES, ";")
    nF = CLng(N_FACES)
    ReDim nm(nF - 1): ReDim P(nF - 1, 9): ReDim cnt(nF - 1): ReDim ar(nF - 1)
    j = 0
    For i = 0 To UBound(recs)
        If Len(recs(i)) > 0 Then
            f = Split(recs(i), "|")
            nm(j) = f(0)
            For k = 0 To 9: P(j, k) = Val(f(1 + k)): Next k
            j = j + 1
        End If
    Next i
    If j <> nF Then Fail j & " boundary faces listed, N_FACES says " & nF & "."
    Set body = BodyNamed("flame")
    faces = body.GetFaces
    For i = 0 To UBound(faces)
        Set face = faces(i)
        Set surf = face.GetSurface
        hit = -1
        If surf.IsPlane Then
            pp = surf.PlaneParams
            For j = 0 To nF - 1
                If Abs(Abs(pp(0) * P(j, 3) + pp(1) * P(j, 4) + pp(2) * P(j, 5)) - 1#) < 0.000001 Then
                    q = face.GetClosestPointOn(P(j, 0), P(j, 1), P(j, 2))
                    If Not IsEmpty(q) Then
                        If Sqr((q(0) - P(j, 0)) ^ 2 + (q(1) - P(j, 1)) ^ 2 + (q(2) - P(j, 2)) ^ 2) < 0.0001 Then hit = j: Exit For
                    End If
                End If
            Next j
        End If
        If hit >= 0 Then
            cnt(hit) = cnt(hit) + 1: ar(hit) = ar(hit) + face.GetArea
            If nm(hit) = "secondary_air_in" Or nm(hit) = "tertiary_supply_in" Then
                Paint face, P(hit, 7), P(hit, 8), P(hit, 9), 1#
            Else
                Paint face, P(hit, 7), P(hit, 8), P(hit, 9)
            End If
        Else
            nWall = nWall + 1: aWall = aWall + face.GetArea
            Paint face, 0.7, 0.7, 0.7
        End If
    Next i
    For j = 0 To nF - 1
        If cnt(j) <> 1 Then Fail "found " & cnt(j) & " faces for " & nm(j) & ", expected 1."
        If Abs(ar(j) - P(j, 6)) > 0.001 * P(j, 6) Then Fail nm(j) & " is " & Fmt(ar(j)) & " m2, expected " & Fmt(P(j, 6)) & " m2."
        Note "boundary " & nm(j) & ": 1 face, " & Fmt(ar(j)) & " m2"
    Next j
    Note "boundary wall: " & nWall & " faces, " & Fmt(aWall) & " m2"
    swModel.ClearSelection2 True
End Sub


' The hood's flat floor (between the hopper's feet: the cooler's width) is
' the cooler's two hood segments: a split line across it at one segment
' (KFL_SPLIT_A..B, past both edges) makes them two faces, secondary_air_in
' and tertiary_supply_in (no stubs; user, 23 Nov 2026). Sketched on the
' face itself; IModelDoc2.InsertSplitLineProject wants the sketch at mark 4,
' the face at mark 1 (both marks tried, as in cooler.bas).
Private Sub SplitFloor()
    Dim body As SldWorks.Body2, faces As Variant, face As SldWorks.Face2, q As Variant
    Dim mx As Double, my As Double, mz As Double, i As Long, k As Long, n0 As Long, mk As Long
    Dim sk As SldWorks.Sketch, skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim xf As SldWorks.MathTransform, pa As SldWorks.MathPoint, pb As SldWorks.MathPoint
    Dim c(2) As Double, a As Variant, b As Variant, sd As SldWorks.SelectData, ent As SldWorks.Entity

    mx = 0.5 * (KFL_SPLIT_AX + KFL_SPLIT_BX): my = 0.5 * (KFL_SPLIT_AY + KFL_SPLIT_BY): mz = 0.5 * (KFL_SPLIT_AZ + KFL_SPLIT_BZ)
    Set body = BodyNamed("flame")
    n0 = UBound(body.GetFaces) + 1
    For k = 0 To 3
        Set face = FaceAt(BodyNamed("flame"), mx, my, mz)
        If face Is Nothing Then Fail "found no face at the hood floor's split line (" & Fmt(mx) & ", " & Fmt(my) & ", " & Fmt(mz) & ")."
        swModel.ClearSelection2 True
        Set ent = face
        ent.Select4 False, Nothing
        swModel.SketchManager.InsertSketch True
        Set sk = swModel.SketchManager.ActiveSketch
        If sk Is Nothing Then Fail "could not open a sketch on the hood's floor."
        Set xf = sk.ModelToSketchTransform
        c(0) = KFL_SPLIT_AX: c(1) = KFL_SPLIT_AY: c(2) = KFL_SPLIT_AZ
        Set pa = mu.CreatePoint(c): Set pa = pa.MultiplyTransform(xf): a = pa.ArrayData
        c(0) = KFL_SPLIT_BX: c(1) = KFL_SPLIT_BY: c(2) = KFL_SPLIT_BZ
        Set pb = mu.CreatePoint(c): Set pb = pb.MultiplyTransform(xf): b = pb.ArrayData
        If Abs(a(2)) > 0.0001 Or Abs(b(2)) > 0.0001 Then Fail "the split line's ends lie off the hood's floor (" & Fmt(a(2)) & ", " & Fmt(b(2)) & " m)."
        If swModel.SketchManager.CreateLine(a(0), a(1), 0#, b(0), b(1), 0#) Is Nothing Then Fail "CreateLine failed on the hood floor's split line."
        swModel.SketchManager.InsertSketch True
        Set skFeat = swModel.FeatureByPositionReverse(0)
        mk = IIf((k And 1) <> 0, 0, 1)
        Set face = FaceAt(BodyNamed("flame"), mx, my, mz)
        swModel.ClearSelection2 True
        skFeat.Select2 False, 4
        Set sd = swModel.SelectionManager.CreateSelectData
        sd.Mark = mk
        Set ent = face
        ent.Select4 True, sd
        On Error Resume Next
        swModel.InsertSplitLineProject ((k And 2) <> 0), False
        If Err.Number <> 0 Then Note "InsertSplitLineProject (mark " & mk & ") raised: " & Err.Description
        Err.Clear
        On Error GoTo 0
        swModel.ClearSelection2 True
        Set body = BodyNamed("flame")
        If UBound(body.GetFaces) + 1 = n0 + 1 Then
            Note "split the hood's floor at one segment: " & n0 + 1 & " faces (form " & k & ")"
            Exit Sub
        End If
        Set f = swModel.FeatureByPositionReverse(0)
        If Not f Is Nothing Then
            f.Select2 False, 0
            swModel.EditDelete
        End If
        swModel.ClearSelection2 True
    Next k
    Fail "could not split the hood's floor: InsertSplitLineProject changed nothing in any of its forms."
End Sub


' The body's planar face through the point (closest point within 0.1 mm).
Private Function FaceAt(body As SldWorks.Body2, ByVal x As Double, ByVal y As Double, ByVal z As Double) As SldWorks.Face2
    Dim faces As Variant, q As Variant, i As Long
    faces = body.GetFaces
    For i = 0 To UBound(faces)
        If faces(i).GetSurface.IsPlane Then
            q = faces(i).GetClosestPointOn(x, y, z)
            If Not IsEmpty(q) Then
                If Sqr((q(0) - x) ^ 2 + (q(1) - y) ^ 2 + (q(2) - z) ^ 2) < 0.0001 Then Set FaceAt = faces(i): Exit Function
            End If
        End If
    Next i
End Function


' Set through the property from a typed Double array, read back and checked.
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
        Fail "a face's colour did not take."
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

    all = KFL_1 & KFL_2 & KFL_3 & KFL_4
    recs = Split(all, ";")
    nB = CLng(N_BODIES)
    ReDim bName(nB - 1): ReDim bGroup(nB - 1): ReDim bKind(nB - 1)
    ReDim bP(nB - 1, 14): ReDim bV(nB - 1): ReDim bBox(nB - 1, 5): ReDim bRGB(nB - 1, 2)

    i = 0
    For j = 0 To UBound(recs)
        If Len(recs(j)) > 0 Then
            If i >= nB Then Fail "more body records than N_BODIES (" & nB & ")."
            f = Split(recs(j), "|")
            bName(i) = f(0): bGroup(i) = f(1): bKind(i) = f(2)
            Select Case bKind(i)
                Case "ring": np = 4
                Case "box": np = 6
                Case "cyl": np = 8
                Case "fbox": np = 15
                Case "tube": np = 9
                Case "tor": np = 13
                Case Else: Fail "body " & bName(i) & ": unknown kind " & bKind(i) & "."
            End Select
            If UBound(f) <> 2 + np + 1 + 6 + 3 Then Fail "body " & bName(i) & ": " & (UBound(f) + 1) & " fields."
            For k = 0 To np - 1: bP(i, k) = Val(f(3 + k)): Next k
            bV(i) = Val(f(3 + np))
            For k = 0 To 5: bBox(i, k) = Val(f(4 + np + k)): Next k
            For k = 0 To 2: bRGB(i, k) = Val(f(10 + np + k)): Next k
            i = i + 1
        End If
    Next j
    If i <> nB Then Fail i & " body records, N_BODIES says " & nB & "."

    recs = Split(KFL_GROUPS, ";")
    nG = CLng(N_GROUPS)
    ReDim gName(nG - 1): ReDim gV(nG - 1): ReDim gN(nG - 1)
    i = 0
    For j = 0 To UBound(recs)
        If Len(recs(j)) > 0 Then
            f = Split(recs(j), "|")
            gName(i) = f(0): gV(i) = Val(f(1)): gN(i) = CLng(Val(f(2)))
            i = i + 1
        End If
    Next j
    If i <> nG Then Fail i & " groups listed, N_GROUPS says " & nG & "."
    Note nB & " bodies in " & nG & " groups read from the generated block"
End Sub


'==================================================================
' Build: each body a temporary modeler body, then a body of the part
'==================================================================
Private Sub Build()
    Dim i As Long, k As Long, n As Long, e As Long, res As Variant
    Dim b As SldWorks.Body2, acc As SldWorks.Body2, f As SldWorks.Feature

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set md = swApp.GetModeler
    Set mu = swApp.GetMathUtility

    ProbeBox
    For k = 0 To nG - 1
        Set acc = Nothing: n = 0
        For i = 0 To nB - 1
            If bGroup(i) = gName(k) And Not IsVoid(i) Then
                Set b = MakeBody(i)
                If b Is Nothing Then Fail "could not make " & bName(i) & "."
                If Not BoxIs(b, i) Then Fail bName(i) & " came out at " & BoxText(b) & ", expected " & WantText(i) & "."
                If acc Is Nothing Then
                    Set acc = b
                Else
                    res = acc.Operations2(SWBODYADD, b, e)
                    If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail gName(k) & ": joining " & bName(i) & " failed (" & e & ")."
                    If UBound(res) <> 0 Then Fail gName(k) & ": joining " & bName(i) & " left " & (UBound(res) + 1) & " bodies (it does not touch the rest)."
                    Set acc = res(0)
                End If
                n = n + 1
            End If
        Next i
        ' then the bores cut out of the joined body (the inside open)
        For i = 0 To nB - 1
            If bGroup(i) = gName(k) And IsVoid(i) Then
                Set b = MakeBody(i)
                If Not BoxIs(b, i) Then Fail bName(i) & " came out at " & BoxText(b) & ", expected " & WantText(i) & "."
                res = acc.Operations2(SWBODYCUT, b, e)
                If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail gName(k) & ": cutting " & bName(i) & " failed (" & e & ")."
                If UBound(res) <> 0 Then Fail gName(k) & ": cutting " & bName(i) & " left " & (UBound(res) + 1) & " bodies."
                Set acc = res(0)
                n = n + 1
            End If
        Next i
        ' then the burner's channels, copied in from their own part
        If gName(k) = "flame" Then AddChannels acc
        If n <> gN(k) Then Fail gName(k) & ": " & n & " parts, the list says " & gN(k) & "."
        Set f = swPart.CreateFeatureFromBody3(acc, False, 0)
        If f Is Nothing Then Fail "CreateFeatureFromBody3 failed on " & gName(k) & "."
        NameNewBody k
    Next k
    CloseScratch
    ' (the bends' scratch part took the focus: back to this part)
    swApp.ActivateDoc3 swModel.GetTitle, False, swDontRebuildActiveDoc, e
    Note "built " & nG & " bodies from " & nB & " parts"
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
        Case "tube"
            ' the bore a little longer at both ends, so the cut opens them
            Set outer = CylBody(bP(i, 0), bP(i, 1), bP(i, 2), bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7))
            Set inner = CylBody(bP(i, 0) - 0.01 * bP(i, 3), bP(i, 1) - 0.01 * bP(i, 4), bP(i, 2) - 0.01 * bP(i, 5), _
                                bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 8), bP(i, 7) + 0.02)
            res = outer.Operations2(SWBODYCUT, inner, e)
            If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail bName(i) & ": the tube's cut failed (" & e & ")."
            If UBound(res) <> 0 Then Fail bName(i) & ": the tube's cut gave " & (UBound(res) + 1) & " bodies."
            Set MakeBody = res(0)
        Case "tor"
            Set MakeBody = TorBody(i)
        Case "fbox"
            ' a x b x c centred at the origin, its axes put on (e1, e2, e3) at the centre;
            ' the transform's row convention not trusted: both readings, the extent decides
            Set b = BoxBody(-0.5 * bP(i, 12), 0.5 * bP(i, 12), -0.5 * bP(i, 13), 0.5 * bP(i, 13), -0.5 * bP(i, 14), 0.5 * bP(i, 14))
            For k = 0 To 1
                Set t = b.Copy
                t.ApplyTransform Frame(bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7), bP(i, 8), _
                                       bP(i, 9), bP(i, 10), bP(i, 11), bP(i, 0), bP(i, 1), bP(i, 2), k = 1)
                If BoxIs(t, i) Then Set MakeBody = t: Exit Function
            Next k
            Fail bName(i) & ": neither reading of the frame put it at " & WantText(i) & "."
    End Select
End Function


Private Function IsVoid(ByVal i As Long) As Boolean
    IsVoid = (Left$(bName(i), 5) = "void_")
End Function


' A smooth pipe bend: an annulus (r, r_in) revolved through the angle in a
' scratch part (the modeler makes no torus), its body copied out (the
' new body: by its name, not merged with the earlier ones; deleting the
' revolve left its feature disconnected): one scratch part for all the
' bends, closed when the build ends (23 Nov 2026: a part opened and
' closed per bend, over many runs, left SolidWorks short of memory). There the bore's centreline runs round the y axis
' from (R, 0, 0), towards +z or -z (the revolve's sense, read off the
' body); then its frame puts x on u, the heading on w, about C (both
' readings of the transform's rows, the extent decides, as fbox).
Private Function TorBody(ByVal i As Long) As SldWorks.Body2
    Dim doc As SldWorks.ModelDoc2, f As SldWorks.Feature, sk As SldWorks.Feature
    Dim bodies As Variant, b As SldWorks.Body2, t As SldWorks.Body2, x As Variant
    Dim R As Double, sg As Double, sx As Double, k As Long, title As String
    Dim xx As Double, xy As Double, xz As Double
    Dim zx As Double, zy As Double, zz As Double, yx As Double, yy As Double, yz As Double
    Dim ax As SldWorks.SketchSegment, sd As SldWorks.SelectData

    R = bP(i, 9)
    If scr Is Nothing Then
        Set scr = swApp.NewPart
        If scr Is Nothing Then Fail bName(i) & ": could not open a scratch part."
        scrTitle = scr.GetTitle
    End If
    Set doc = scr
    title = scrTitle
    ' the first reference plane is the Front plane (z = 0) in any language
    Set f = doc.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then Exit Do
        Set f = f.GetNextFeature
    Loop
    If f Is Nothing Then Fail bName(i) & ": the scratch part has no reference plane."
    doc.ClearSelection2 True
    f.Select2 False, 0
    doc.SketchManager.InsertSketch True
    doc.SketchManager.AddToDB = True
    doc.SketchManager.CreateCircleByRadius R, 0#, 0#, bP(i, 10)
    doc.SketchManager.CreateCircleByRadius R, 0#, 0#, bP(i, 11)
    Set ax = doc.SketchManager.CreateCenterLine(0#, -1#, 0#, 0#, 1#, 0#)
    doc.SketchManager.AddToDB = False
    If ax Is Nothing Then CloseScratch: Fail bName(i) & ": CreateCenterLine failed."
    doc.SketchManager.InsertSketch True
    ' the sketch: the last ProfileFeature
    Set f = doc.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "ProfileFeature" Then Set sk = f
        Set f = f.GetNextFeature
    Loop
    If sk Is Nothing Then CloseScratch: Fail bName(i) & ": no sketch in the scratch part."
    doc.ClearSelection2 True
    Set sd = doc.SelectionManager.CreateSelectData
    sd.Mark = 16
    ax.Select4 False, sd
    sk.Select2 True, 0
    Set f = doc.FeatureManager.FeatureRevolve2(True, True, False, False, False, False, _
            swEndCondBlind, swEndCondBlind, bP(i, 12), 0#, False, False, 0#, 0#, _
            swThinWallOneDirection, 0#, 0#, False, True, True)
    If f Is Nothing Then CloseScratch: Fail bName(i) & ": the revolve failed."
    bodies = doc.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then CloseScratch: Fail bName(i) & ": the revolve made no body."
    Set b = Nothing
    For k = 0 To UBound(bodies)
        Set t = bodies(k)
        If InStr(scrSeen, "|" & t.Name & "|") = 0 Then
            If Not b Is Nothing Then CloseScratch: Fail bName(i) & ": the revolve made more than one new body."
            Set b = t
        End If
    Next k
    If b Is Nothing Then CloseScratch: Fail bName(i) & ": no new body after the revolve."
    scrSeen = scrSeen & "|" & b.Name & "|"
    Set b = b.Copy
    x = ExactBox(b)
    ' (the sketch's x the part's x, or -x; the revolve towards +z, or -z)
    sx = IIf(x(3) > 0.5 * R, 1#, -1#)
    sg = IIf(x(5) > -x(2), 1#, -1#)       ' (by the side it reaches further: also for a small angle)
    ' local x onto sx u, local z onto sg w, local y = z cross x
    xx = sx * bP(i, 3): xy = sx * bP(i, 4): xz = sx * bP(i, 5)
    zx = sg * bP(i, 6): zy = sg * bP(i, 7): zz = sg * bP(i, 8)
    yx = zy * xz - zz * xy: yy = zz * xx - zx * xz: yz = zx * xy - zy * xx
    For k = 0 To 1
        Set t = b.Copy
        t.ApplyTransform Frame(xx, xy, xz, yx, yy, yz, zx, zy, zz, _
                               bP(i, 0), bP(i, 1), bP(i, 2), k = 1)
        If BoxIs(t, i) Then Set TorBody = t: Exit Function
    Next k
    Fail bName(i) & ": neither reading of the frame put the bend at " & WantText(i) & " (last " & BoxText(t) & ")."
End Function


Private Sub CloseScratch()
    If scr Is Nothing Then Exit Sub
    swApp.CloseDoc scrTitle
    Set scr = Nothing
    scrTitle = ""
    scrSeen = ""
End Sub


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


' Local x, y, z onto (ax, ay, az), (bx, by, bz), (cx, cy, cz), moved by
' (tx, ty, tz); the rotation's rows or its columns (transposed).
Private Function Frame(ByVal ax As Double, ByVal ay As Double, ByVal az As Double, _
                       ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                       ByVal cx As Double, ByVal cy As Double, ByVal cz As Double, _
                       ByVal tx As Double, ByVal ty As Double, ByVal tz As Double, _
                       ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double
    If transposed Then
        t(0) = ax: t(1) = bx: t(2) = cx: t(3) = ay: t(4) = by: t(5) = cy: t(6) = az: t(7) = bz: t(8) = cz
    Else
        t(0) = ax: t(1) = ay: t(2) = az: t(3) = bx: t(4) = by: t(5) = bz: t(6) = cx: t(7) = cy: t(8) = cz
    End If
    t(9) = tx: t(10) = ty: t(11) = tz: t(12) = 1#
    Set Frame = mu.CreateTransform(t)
End Function


' The body the last feature made: the one not yet named. Named, painted.
Private Sub NameNewBody(ByVal k As Long)
    Dim bodies As Variant, body As SldWorks.Body2, found As SldWorks.Body2
    Dim j As Long, n As Long, i As Long
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "no body after making " & gName(k) & "."
    If UBound(bodies) + 1 <> k + 1 Then _
        Fail "after " & gName(k) & " the part has " & (UBound(bodies) + 1) & " bodies, expected " & (k + 1) & " (a body merged)."
    For j = 0 To UBound(bodies)
        Set body = bodies(j)
        If Not IsTaken(body.Name, k) Then Set found = body: n = n + 1
    Next j
    If n <> 1 Then Fail n & " unnamed bodies after " & gName(k) & ", expected 1."
    found.Name = gName(k)
    If found.Name <> gName(k) Then Fail "a body did not take the name " & gName(k) & "."
    For i = 0 To nB - 1
        If bGroup(i) = gName(k) Then PaintBody found, bRGB(i, 0), bRGB(i, 1), bRGB(i, 2): Exit For
    Next i
End Sub


Private Function BodyNamed(ByVal nm As String) As SldWorks.Body2
    Dim bodies As Variant, j As Long, body As SldWorks.Body2
    bodies = swPart.GetBodies2(swSolidBody, False)
    For j = 0 To UBound(bodies)
        Set body = bodies(j)
        If body.Name = nm Then Set BodyNamed = body: Exit Function
    Next j
    Fail "no body named " & nm & "."
End Function


Private Function IsTaken(ByVal nm As String, ByVal upTo As Long) As Boolean
    Dim j As Long
    For j = 0 To upTo - 1
        If nm = gName(j) Then IsTaken = True: Exit Function
    Next j
End Function


'==================================================================
' Verify: each body once, its volume and its exact extent
'==================================================================
Private Sub Verify()
    Dim bodies As Variant, body As SldWorks.Body2, mp As Variant, x As Variant
    Dim k As Long, j As Long, i As Long, hit As Long, vSum As Double
    Dim lo(2) As Double, hi(2) As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) + 1 <> nG Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not " & nG & "."
    For k = 0 To nG - 1
        hit = 0
        For j = 0 To UBound(bodies)
            Set body = bodies(j)
            If body.Name = gName(k) Then
                hit = hit + 1
                mp = body.GetMassProperties(1#)
                If gV(k) > 0# Then
                    If Abs(mp(3) - gV(k)) > VOL_TOL * gV(k) Then _
                        Fail gName(k) & " is " & Fmt(mp(3)) & " m3, expected " & Fmt(gV(k)) & " m3."
                End If
                ' the group's extent: its parts' joint one (not a cut_ part's: the voids trim it)
                lo(0) = 1E+30: lo(1) = 1E+30: lo(2) = 1E+30: hi(0) = -1E+30: hi(1) = -1E+30: hi(2) = -1E+30
                For i = 0 To nB - 1
                    If bGroup(i) = gName(k) And Not IsVoid(i) And Left$(bName(i), 4) <> "cut_" Then
                        If bBox(i, 0) < lo(0) Then lo(0) = bBox(i, 0)
                        If bBox(i, 1) < lo(1) Then lo(1) = bBox(i, 1)
                        If bBox(i, 2) < lo(2) Then lo(2) = bBox(i, 2)
                        If bBox(i, 3) > hi(0) Then hi(0) = bBox(i, 3)
                        If bBox(i, 4) > hi(1) Then hi(1) = bBox(i, 4)
                        If bBox(i, 5) > hi(2) Then hi(2) = bBox(i, 5)
                    End If
                Next i
                x = ExactBox(body)
                For i = 0 To 2
                    If Abs(x(i) - lo(i)) > BOX_TOL Or Abs(x(i + 3) - hi(i)) > BOX_TOL Then _
                        Fail gName(k) & " sits at " & BoxText(body) & ", its parts span x " & Fmt(lo(0)) & " .. " & Fmt(hi(0)) & _
                             ", y " & Fmt(lo(1)) & " .. " & Fmt(hi(1)) & ", z " & Fmt(lo(2)) & " .. " & Fmt(hi(2)) & "."
                Next i
                vSum = vSum + mp(3)
                Note "body " & gName(k) & " (" & gN(k) & " parts): " & Fmt(mp(3)) & " m3" & _
                     IIf(gV(k) > 0#, " = source", " (parts overlap: extent checked)") & ", " & BoxText(body)
            End If
        Next j
        If hit <> 1 Then Fail hit & " bodies named " & gName(k) & ", expected 1."
    Next k
    Note nG & " bodies, each its extent (and volume where its parts do not overlap); " & Fmt(vSum) & " m3 in all"
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
    Dim outDir As String, e As Long, w As Long
    outDir = OUT_ROOT & LINE_KEY & "\"
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(outDir, vbDirectory) = "" Then MkDir outDir

    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    exportPrefsTouched = True
    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True

    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "", swIsometricView
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.Extension.SaveAs outDir & PART_NAME & "_isometric.jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
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
    CloseScratch
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
