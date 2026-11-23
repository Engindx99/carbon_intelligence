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
Const N_BODIES                     As Double  = 53           ' bodies before joining [derived]
Const N_GROUPS                     As Double  = 15           ' bodies in the part [derived]
Const KBB_1                        As String  = "tip_ring|tip_ring|ring|0.239656266|0.314077459|-0.697251959|0|0.090268706|-0.314077459|-0.314077459|-0.697251959|0.314077459|0.314077459|0|0.72|0.66|0.56;castable|castable|ring|0.239656266|0.304655135|-6.545374241|-0.697251959|0.650009272|-0.304655135|-0.304655135|-6.545374241|0.304655135|0.304655135|-0.697251959|0.72|0.66|0.56;burner_pipe|burner_pipe|ring|0.229656266|0.239656266|-6.696131421|0|0.098727012|-0.239656266|-0.239656266|-6.696131421|0.239656266|0.239656266|0|0.45|0.46|0.48;flange|flange|tube|0|0|-6.758946913|0|0|1|0.348625979|0.062815492|0.229656266|0.013576659|-0.348625979|-0.348625979|-6.758946913|0.348625979|0.348625979|-6.696131421|0.45|0.46|0.48;fuel_lance|fuel_lance|tube|0|-0.118093125|-8.693664059|0|0|1|0.027638816|8.693664059|0.019347171|0.010640494|-0.027638816|-0.145731941|-8.693664059|0.027638816|-0.090454308|0|0.55|0.56|0.58;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_2                        As String  = "flame_scanner|flame_scanner|tube|-0.057790252|-0.095479547|-8.693664059|0|0|1|0.012249021|8.693664059|0.008574315|0.002089901|-0.070039273|-0.107728568|-8.693664059|-0.045541232|-0.083230527|0|0.55|0.56|0.58;igniter|igniter|tube|0.057790252|-0.095479547|-8.693664059|0|0|1|0.012249021|8.693664059|0.008574315|0.002089901|0.045541232|-0.107728568|-8.693664059|0.070039273|-0.083230527|0|0.55|0.56|0.58;support_ring|support|ring|0.239656266|0.376892951|-6.696131421|-6.671005225|0.006679048|-0.376892951|-0.376892951|-6.696131421|0.376892951|0.376892951|-6.671005225|0.45|0.46|0.48;support_neck|support|box|-0.157038729|0.157038729|0.30151436|0.653281114|-6.696131421|-6.671005225|0.002775993|-0.157038729|0.30151436|-6.696131421|0.157038729|0.653281114|-6.671005225|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_3                        As String  = "support_leg|support|box|-0.157038729|0.157038729|-0.471116188|-0.30151436|-6.696131421|-6.671005225|0.001338425|-0.157038729|-0.471116188|-6.696131421|0.157038729|-0.30151436|-6.671005225|0.45|0.46|0.48;support_foot|support|box|-0.219854221|0.219854221|-0.496242385|-0.471116188|-6.696131421|-6.444869454|0.002775993|-0.219854221|-0.496242385|-6.696131421|0.219854221|-0.471116188|-6.444869454|0.45|0.46|0.48;head_flange_front|head_flange_front|ring|0.279528938|0.314077459|-6.78407311|-6.758946913|0.001618843|-0.314077459|-0.314077459|-6.78407311|0.314077459|0.314077459|-6.758946913|0.45|0.46|0.48;head_flange_rear|head_flange_rear|ring|0.279528938|0.314077459|-8.015256748|-7.990130552|0.001618843|-0.314077459|-0.314077459|-8.015256748|0.314077459|0.314077459|-7.990130552|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_4                        As String  = "bellows|bellows|tube|0|0|-8.191140125|0|0|1|0.298373586|0.175883377|0.288373586|0.003242095|-0.298373586|-0.298373586|-8.191140125|0.298373586|0.298373586|-8.015256748|0.45|0.46|0.48;bellows_back|bellows|cyl|0|0|-8.191140125|0|0|1|0.293373586|0.01|0.002703908|-0.293373586|-0.293373586|-8.191140125|0.293373586|0.293373586|-8.181140125|0.45|0.46|0.48;void_bellows_fuel_lance|bellows|cyl|0|-0.118093125|-8.201140125|0|0|1|0.029638816|0.03|0.000082793|-0.029638816|-0.147731941|-8.201140125|0.029638816|-0.088454308|-8.171140125|0|0|0;void_bellows_flame_scanner|bellows|cyl|-0.057790252|-0.095479547|-8.201140125|0|0|1|0.014249021|0.03|0.000019136|-0.072039273|-0.109728568|-8.201140125|-0.043541232|-0.081230527|-8.171140125|0|0|0;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_5                        As String  = "void_bellows_igniter|bellows|cyl|0.057790252|-0.095479547|-8.201140125|0|0|1|0.014249021|0.03|0.000019136|0.043541232|-0.109728568|-8.201140125|0.072039273|-0.081230527|-8.171140125|0|0|0;void_bellows_back|bellows|cyl|0|0.033669104|-8.201140125|0|0|1|0.10620866|0.03|0.001063141|-0.10620866|-0.072539556|-8.201140125|0.10620866|0.139877763|-8.171140125|0|0|0;coal_inlet|coal|tube|0|0.033669104|-8.938644477|0|0|1|0.11620866|0.747504352|0.10620866|0.005223146|-0.11620866|-0.082539556|-8.938644477|0.11620866|0.149877763|-8.191140125|0.55|0.56|0.58;coal_bend|coal|tor|0|0.382295083|-8.938644477|0|-1|0|0|0|-1|0.348625979|0.11620866|0.10620866|0.20943951|0.000510196|-0.11620866|-0.082539556|-9.035289033|0.11620866|0.154956639|-8.938644477|0.55|0.56|0.58;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_6                        As String  = "coal_tail|coal|tube|0|0.041287418|-9.011127894|0|0.207911691|-0.978147601|0.11620866|0.505270041|0.10620866|0.003530547|-0.11620866|-0.072381804|-9.529517711|0.11620866|0.260008188|-8.986966755|0.55|0.56|0.58;coal_inlet_flange|coal|tube|0|0.146338966|-9.505356572|0|0.207911691|-0.978147601|0.157038729|0.062815492|0.10620866|0.002640593|-0.157038729|-0.00726809|-9.599449582|0.157038729|0.313006098|-9.472706384|0.55|0.56|0.58;coal_nozzle|coal|tube|-0.050319826|0.151248136|-9.388719207|-0.866025404|0.4890738|0.103955845|0.031407746|0.277958551|0.021407746|0.000461202|-0.306742865|0.123852969|-9.419956783|-0.034615953|0.314585549|-9.328586215|0.55|0.56|0.58;void_coal_nozzle|coal|cyl|-0.050319826|0.151248136|-9.388719207|-0.866025404|0.4890738|0.103955845|0.021407746|0.11620866|0.000167313|-0.16166335|0.132575393|-9.410010964|-0.039615953|0.226755491|-9.35534688|0|0|0;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_7                        As String  = "void_coal_bore|coal|cyl|0|0.041287418|-9.011127894|0|0.207911691|-0.978147601|0.10620866|0.578085533|0.02048622|-0.10620866|-0.062600328|-9.598662893|0.10620866|0.265365904|-8.989045872|0|0|0;elbow_leg|head|tube|-0.139764469|0|-7.46876197|-1|0|0|0.119349434|0.328210944|0.109349434|0.002358126|-0.467975414|-0.119349434|-7.588111404|-0.139764469|0.119349434|-7.349412536|0.55|0.56|0.58;elbow_bend|head|tor|-0.467975414|0.358048303|-7.46876197|0|-1|0|-1|0|0|0.358048303|0.119349434|0.109349434|1.570796327|0.004040875|-0.945373151|-0.119349434|-7.588111404|-0.467975414|0.358048303|-7.349412536|0.55|0.56|0.58;elbow_flange|head|tube|-0.826023717|0.358048303|-7.46876197|0|1|0|0.161121736|0.025126197|0.109349434|0.001105338|-0.987145453|0.358048303|-7.629883706|-0.66490198|0.3831745|-7.307640234|0.55|0.56|0.58;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_8                        As String  = "head|head|cyl|0|0|-8.015256748|0|0|1|0.279528938|1.256309835|0.308389926|-0.279528938|-0.279528938|-8.015256748|0.279528938|0.279528938|-6.758946913|0.45|0.46|0.48;void_head|head|cyl|0|0|-8.025256748|0|0|1|0.269528938|1.276309835|0.291284107|-0.269528938|-0.269528938|-8.025256748|0.269528938|0.269528938|-6.748946913|0|0|0;void_elbow_leg|head|cyl|-0.139764469|0|-7.46876197|-1|0|0|0.109349434|0.315647846|0.011857299|-0.455412315|-0.109349434|-7.578111404|-0.139764469|0.109349434|-7.359412536|0|0|0;air_inlet_2|head|tube|-0.139764469|0|-7.839373371|-1|0|0|0.113067885|0.328210944|0.103067885|0.002228587|-0.467975414|-0.113067885|-7.952441256|-0.139764469|0.113067885|-7.726305486|0.55|0.56|0.58;void_air_inlet_2|head|cyl|-0.139764469|0|-7.839373371|-1|0|0|0.103067885|0.315647846|0.010534148|-0.455412315|-0.103067885|-7.942441256|-0.139764469|0.103067885|-7.736305486|0|0|0;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_9                        As String  = "air_inlet_2_flange|head|tube|-0.467975414|0|-7.839373371|-1|0|0|0.146988251|0.025126197|0.103067885|0.000866922|-0.49310161|-0.146988251|-7.986361622|-0.467975414|0.146988251|-7.692385121|0.55|0.56|0.58;beam_end|beam|box|-0.125630984|0.125630984|0.653281114|0.948513926|-6.696131421|-6.671005225|0.001863881|-0.125630984|0.653281114|-6.696131421|0.125630984|0.948513926|-6.671005225|0.45|0.46|0.48;beam_web_R|beam|box|0.012563098|0.037689295|0.653281114|0.948513926|-10.465060927|-6.696131421|0.027958212|0.012563098|0.653281114|-10.465060927|0.037689295|0.948513926|-6.696131421|0.45|0.46|0.48;beam_top_R|beam|box|0.012563098|0.125630984|0.923387729|0.948513926|-10.465060927|-6.696131421|0.0107074|0.012563098|0.923387729|-10.465060927|0.125630984|0.948513926|-6.696131421|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_10                       As String  = "beam_bot_R|beam|box|0.012563098|0.125630984|0.653281114|0.678407311|-10.465060927|-6.696131421|0.0107074|0.012563098|0.653281114|-10.465060927|0.125630984|0.678407311|-6.696131421|0.45|0.46|0.48;cut_beam_brace_R|beam|fbox|0.113067885|0.80089752|-7.638363798|0|0.587785252|0.809016994|0|-0.809016994|0.587785252|1|0|0|0.811906774|0.188446475|0.025126197|0.003844332|0.100504787|0.486055905|-8.022170016|0.125630984|1.115739134|-7.254557579|0.45|0.46|0.48;void_beam_brace_R0|beam|box|0.090504787|0.135630984|0.948513926|1.7604207|-8.054317185|-7.222410411|0.030479621|0.090504787|0.948513926|-8.054317185|0.135630984|1.7604207|-7.222410411|0|0|0;void_beam_brace_R1|beam|box|0.090504787|0.135630984|-0.15862566|0.653281114|-8.054317185|-7.222410411|0.030479621|0.090504787|-0.15862566|-8.054317185|0.135630984|0.653281114|-7.222410411|0|0|0;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_11                       As String  = "beam_web_L|beam|box|-0.037689295|-0.012563098|0.653281114|0.948513926|-10.465060927|-6.696131421|0.027958212|-0.037689295|0.653281114|-10.465060927|-0.012563098|0.948513926|-6.696131421|0.45|0.46|0.48;beam_top_L|beam|box|-0.125630984|-0.012563098|0.923387729|0.948513926|-10.465060927|-6.696131421|0.0107074|-0.125630984|0.923387729|-10.465060927|-0.012563098|0.948513926|-6.696131421|0.45|0.46|0.48;beam_bot_L|beam|box|-0.125630984|-0.012563098|0.653281114|0.678407311|-10.465060927|-6.696131421|0.0107074|-0.125630984|0.653281114|-10.465060927|-0.012563098|0.678407311|-6.696131421|0.45|0.46|0.48;cut_beam_brace_L|beam|fbox|-0.113067885|0.80089752|-7.638363798|0|0.587785252|0.809016994|0|-0.809016994|0.587785252|1|0|0|0.811906774|0.188446475|0.025126197|0.003844332|-0.125630984|0.486055905|-8.022170016|-0.100504787|1.115739134|-7.254557579|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_12                       As String  = "void_beam_brace_L0|beam|box|-0.135630984|-0.090504787|0.948513926|1.7604207|-8.054317185|-7.222410411|0.030479621|-0.135630984|0.948513926|-8.054317185|-0.090504787|1.7604207|-7.222410411|0|0|0;void_beam_brace_L1|beam|box|-0.135630984|-0.090504787|-0.15862566|0.653281114|-8.054317185|-7.222410411|0.030479621|-0.135630984|-0.15862566|-8.054317185|-0.090504787|0.653281114|-7.222410411|0|0|0;beam_tail_plate_R|beam|box|0.100504787|0.125630984|0.653281114|0.948513926|-10.465060927|-10.150983468|0.002329851|0.100504787|0.653281114|-10.465060927|0.125630984|0.948513926|-10.150983468|0.45|0.46|0.48;beam_tail_plate_L|beam|box|-0.125630984|-0.100504787|0.653281114|0.948513926|-10.465060927|-10.150983468|0.002329851|-0.125630984|0.653281114|-10.465060927|-0.100504787|0.948513926|-10.150983468|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_13                       As String  = "beam_pin_R|beam|cyl|0.037689295|0.80089752|-6.784701265|1|0|0|0.037689295|0.163320279|0.00072883|0.037689295|0.763208225|-6.82239056|0.201009574|0.838586815|-6.74701197|0.45|0.46|0.48;beam_pin_L|beam|cyl|-0.037689295|0.80089752|-6.784701265|-1|0|0|0.037689295|0.163320279|0.00072883|-0.201009574|0.763208225|-6.82239056|-0.037689295|0.838586815|-6.74701197|0.45|0.46|0.48;hanger|hanger|box|-0.125630984|0.125630984|0.279528938|0.653281114|-8.096916888|-7.682334642|0.038933297|-0.125630984|0.279528938|-8.096916888|0.125630984|0.653281114|-7.682334642|0.45|0.46|0.48;" ' plant_geometry.kiln_burner_body() bodies
Const KBB_14                       As String  = ""           ' plant_geometry.kiln_burner_body() bodies
Const KBB_15                       As String  = ""           ' plant_geometry.kiln_burner_body() bodies
Const KBB_16                       As String  = ""           ' plant_geometry.kiln_burner_body() bodies
Const KBB_GROUPS                   As String  = "tip_ring|0.090268706|1;castable|0.650009272|1;burner_pipe|0.098727012|1;flange|0.013576659|1;fuel_lance|0.010640494|1;flame_scanner|0.002089901|1;igniter|0.002089901|1;support|-1|4;head_flange_front|0.001618843|1;head_flange_rear|0.001618843|1;bellows|-1|6;coal|-1|7;head|-1|9;beam|-1|17;hanger|0.038933297|1;" ' the part's bodies: name|V (-1: parts overlap)|parts
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
    ' (front: the tip seen from the kiln, to check by the brochure's p. 5)
    vn = Array("left", "right", "isometric", "top", "tip")
    k = 0
    For Each vw In Array(swLeftView, swRightView, swIsometricView, swTopView, swFrontView)
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

    all = KBB_1 & KBB_2 & KBB_3 & KBB_4 & KBB_5 & KBB_6 & KBB_7 & KBB_8 & _
          KBB_9 & KBB_10 & KBB_11 & KBB_12 & KBB_13 & KBB_14 & KBB_15 & KBB_16
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

    recs = Split(KBB_GROUPS, ";")
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
    ' a close-up of the back end to hold against the brochure's cover
    ' (the castable and the pipe hidden for it, then shown again)
    Dim e As Long, w As Long, nm As Variant
    For Each nm In Array("tip_ring", "castable", "burner_pipe")
        BodyNamed(CStr(nm)).HideBody True
    Next nm
    ' (seen from the elbow's side, -x, as the cover: the isometric turned
    ' a half turn about the vertical)
    swModel.ShowNamedView2 "", swIsometricView
    swModel.ActiveView.RotateAboutCenter 0#, 3.14159265358979 / 2#
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.Extension.SaveAs outDir & PART_NAME & "_rear.jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    For Each nm In Array("tip_ring", "castable", "burner_pipe")
        BodyNamed(CStr(nm)).HideBody False
    Next nm
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
