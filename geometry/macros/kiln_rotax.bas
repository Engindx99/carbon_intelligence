Attribute VB_Name = "kiln_rotax"
'==================================================================
' Rotary kiln MECHANICAL PARTS after FLS ROTAX-2  ->  SLDPRT + STEP
'
' NOT a CFD input and not a fabrication drawing (user request, 22 Nov
' 2026: the kiln's own dimensions stay, only the ROTAX-2 parts are
' added, as simple envelopes). The kiln's frame as kiln_wall.bas: axis
' z (back end 0, hood end L), y up, x across; the slope is not built in,
' the piers reach the sloped ground. Overlay on kiln_wall.SLDPRT (same
' origin) for the whole kiln.
'
'   tyre_<st>, tyre_section_<st>    tyre ring, thick shell plate under it
'   bracket_<st>_<ii>               tangential suspension brackets
'   roller_<st>_<L|R>, shaft_, bearing_<st>_<L|R>_<back|hood>
'   frame_<st>, pier_<st>           roller station frame, concrete pier
'   gearbox_<L|R>, motor_<L|R>      friction drive at the inlet station
'   htd, htd_stand                  hydraulic thrust device
'   inlet_seal, outlet_seal, outlet_chute_<n>, nose_ring_fan
'   shell_fan_<n>, walkway
' (<st> = inlet / outlet: the support near the back end / the hood end)
'
' Every body, its size, place, volume and extent come from
' geometry/plant_geometry.py kiln_rotax() (the generated KRX_ strings):
' this macro builds each one as a temporary body of SolidWorks' modeler
' (a cylinder, a box, a ring = cylinder minus cylinder), makes it a body
' of the part, names and colours it, and checks its volume and exact
' extent against the generated ones. Sizes are FLS ROTAX-2 image ratios,
' literature and schematic values (plant_geometry.yaml kiln_rotax).
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py kiln_rotax_solid.main from WSL.
' Outputs geometry\output\2500\kiln_rotax.SLDPRT, .step and
' kiln_rotax_build.log.
'==================================================================

Option Explicit

Const PART_NAME As String = "kiln_rotax"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 75           ' bodies in the part [derived]
Const KRX_1                        As String  = "tyre_inlet|ring|3|3.45|23.97|24.87|8.206625409|-3.45|-3.45|23.97|3.45|3.45|24.87|0.1|0.16|0.72;tyre_section_inlet|ring|2.65|2.71|22.62|26.22|3.637210311|-2.71|-2.71|22.62|2.71|2.71|26.22|0.62|0.64|0.66;bracket_inlet_00|rbox|2.71|3|0.3|23.47|25.37|0.196349541|0.1653|-0.732388758|2.628664562|23.47|-0.381576981|2.97161939|25.37|0.62|0.64|0.66;bracket_inlet_01|rbox|2.71|3|0.3|23.47|25.37|0.589048623|0.1653|-1.791431141|2.169947114|23.47|-1.38087489|2.577744372|25.37|0.62|0.64|0.66;bracket_inlet_02|rbox|2.71|3|0.3|23.47|25.37|0.981747704|0.1653|-2.577744372|1.38087489|23.47|-2.169947114|1.791431141|25.37|0.62|0.64|0.66;bracket_inlet_03|rbox|2.71|3|0.3|23.47|25.37|1.374446786|0.1653|-2.97161939|0.381576981|23.47|-2.628664562|0.732388758|25.37|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_2                        As String  = "bracket_inlet_04|rbox|2.71|3|0.3|23.47|25.37|1.767145868|0.1653|-2.97161939|-0.732388758|23.47|-2.628664562|-0.381576981|25.37|0.62|0.64|0.66;bracket_inlet_05|rbox|2.71|3|0.3|23.47|25.37|2.159844949|0.1653|-2.577744372|-1.791431141|23.47|-2.169947114|-1.38087489|25.37|0.62|0.64|0.66;bracket_inlet_06|rbox|2.71|3|0.3|23.47|25.37|2.552544031|0.1653|-1.791431141|-2.577744372|23.47|-1.38087489|-2.169947114|25.37|0.62|0.64|0.66;bracket_inlet_07|rbox|2.71|3|0.3|23.47|25.37|2.945243113|0.1653|-0.732388758|-2.97161939|23.47|-0.381576981|-2.628664562|25.37|0.62|0.64|0.66;bracket_inlet_08|rbox|2.71|3|0.3|23.47|25.37|3.337942194|0.1653|0.381576981|-2.97161939|23.47|0.732388758|-2.628664562|25.37|0.62|0.64|0.66;bracket_inlet_09|rbox|2.71|3|0.3|23.47|25.37|3.730641276|0.1653|1.38087489|-2.577744372|23.47|1.791431141|-2.169947114|25.37|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_3                        As String  = "bracket_inlet_10|rbox|2.71|3|0.3|23.47|25.37|4.123340358|0.1653|2.169947114|-1.791431141|23.47|2.577744372|-1.38087489|25.37|0.62|0.64|0.66;bracket_inlet_11|rbox|2.71|3|0.3|23.47|25.37|4.51603944|0.1653|2.628664562|-0.732388758|23.47|2.97161939|-0.381576981|25.37|0.62|0.64|0.66;bracket_inlet_12|rbox|2.71|3|0.3|23.47|25.37|4.908738521|0.1653|2.628664562|0.381576981|23.47|2.97161939|0.732388758|25.37|0.62|0.64|0.66;bracket_inlet_13|rbox|2.71|3|0.3|23.47|25.37|5.301437603|0.1653|2.169947114|1.38087489|23.47|2.577744372|1.791431141|25.37|0.62|0.64|0.66;bracket_inlet_14|rbox|2.71|3|0.3|23.47|25.37|5.694136685|0.1653|1.38087489|2.169947114|23.47|1.791431141|2.577744372|25.37|0.62|0.64|0.66;bracket_inlet_15|rbox|2.71|3|0.3|23.47|25.37|6.086835766|0.1653|0.381576981|2.628664562|23.47|0.732388758|2.97161939|25.37|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_4                        As String  = "roller_inlet_L|cyl|-2.2839|-3.955830839|23.87|0|0|1|1.1178|1.1|4.317881988|-3.4017|-5.073630839|23.87|-1.1661|-2.838030839|24.97|0.1|0.16|0.72;shaft_inlet_L|cyl|-2.2839|-3.955830839|23.17|0|0|1|0.3|2.5|0.706858347|-2.5839|-4.255830839|23.17|-1.9839|-3.655830839|25.67|0.45|0.46|0.48;bearing_inlet_L_back|box|-2.7839|-1.7839|-4.455830839|-3.455830839|23.17|23.87|0.7|-2.7839|-4.455830839|23.17|-1.7839|-3.455830839|23.87|0.45|0.46|0.48;bearing_inlet_L_hood|box|-2.7839|-1.7839|-4.455830839|-3.455830839|24.97|25.67|0.7|-2.7839|-4.455830839|24.97|-1.7839|-3.455830839|25.67|0.45|0.46|0.48;gearbox_L|cyl|-2.2839|-3.955830839|21.37|0|0|1|0.8|1.4|2.814867018|-3.0839|-4.755830839|21.37|-1.4839|-3.155830839|22.77|0.1|0.16|0.72;motor_L|box|-2.8839|-1.6839|-4.555830839|-3.355830839|18.97|20.97|2.88|-2.8839|-4.555830839|18.97|-1.6839|-3.355830839|20.97|0.45|0.46|0.48;" ' plant_geometry.kiln_rotax() bodies
Const KRX_5                        As String  = "roller_inlet_R|cyl|2.2839|-3.955830839|23.87|0|0|1|1.1178|1.1|4.317881988|1.1661|-5.073630839|23.87|3.4017|-2.838030839|24.97|0.1|0.16|0.72;shaft_inlet_R|cyl|2.2839|-3.955830839|23.17|0|0|1|0.3|2.5|0.706858347|1.9839|-4.255830839|23.17|2.5839|-3.655830839|25.67|0.45|0.46|0.48;bearing_inlet_R_back|box|1.7839|2.7839|-4.455830839|-3.455830839|23.17|23.87|0.7|1.7839|-4.455830839|23.17|2.7839|-3.455830839|23.87|0.45|0.46|0.48;bearing_inlet_R_hood|box|1.7839|2.7839|-4.455830839|-3.455830839|24.97|25.67|0.7|1.7839|-4.455830839|24.97|2.7839|-3.455830839|25.67|0.45|0.46|0.48;gearbox_R|cyl|2.2839|-3.955830839|21.37|0|0|1|0.8|1.4|2.814867018|1.4839|-4.755830839|21.37|3.0839|-3.155830839|22.77|0.1|0.16|0.72;motor_R|box|1.6839|2.8839|-4.555830839|-3.355830839|18.97|20.97|2.88|1.6839|-4.555830839|18.97|2.8839|-3.355830839|20.97|0.45|0.46|0.48;" ' plant_geometry.kiln_rotax() bodies
Const KRX_6                        As String  = "frame_inlet|box|-2.7839|2.7839|-5.055830839|-4.455830839|23.17|25.67|8.3517|-2.7839|-5.055830839|23.17|2.7839|-4.455830839|25.67|0.45|0.46|0.48;pier_inlet|box|-4.5|4.5|-9.267729448|-5.055830839|18.57|27.42|335.477724146|-4.5|-9.267729448|18.57|4.5|-5.055830839|27.42|0.78|0.77|0.74;tyre_outlet|ring|3|3.45|62.45|63.35|8.206625409|-3.45|-3.45|62.45|3.45|3.45|63.35|0.1|0.16|0.72;tyre_section_outlet|ring|2.65|2.71|61.1|64.7|3.637210311|-2.71|-2.71|61.1|2.71|2.71|64.7|0.62|0.64|0.66;bracket_outlet_00|rbox|2.71|3|0.3|61.95|63.85|0.196349541|0.1653|-0.732388758|2.628664562|61.95|-0.381576981|2.97161939|63.85|0.62|0.64|0.66;bracket_outlet_01|rbox|2.71|3|0.3|61.95|63.85|0.589048623|0.1653|-1.791431141|2.169947114|61.95|-1.38087489|2.577744372|63.85|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_7                        As String  = "bracket_outlet_02|rbox|2.71|3|0.3|61.95|63.85|0.981747704|0.1653|-2.577744372|1.38087489|61.95|-2.169947114|1.791431141|63.85|0.62|0.64|0.66;bracket_outlet_03|rbox|2.71|3|0.3|61.95|63.85|1.374446786|0.1653|-2.97161939|0.381576981|61.95|-2.628664562|0.732388758|63.85|0.62|0.64|0.66;bracket_outlet_04|rbox|2.71|3|0.3|61.95|63.85|1.767145868|0.1653|-2.97161939|-0.732388758|61.95|-2.628664562|-0.381576981|63.85|0.62|0.64|0.66;bracket_outlet_05|rbox|2.71|3|0.3|61.95|63.85|2.159844949|0.1653|-2.577744372|-1.791431141|61.95|-2.169947114|-1.38087489|63.85|0.62|0.64|0.66;bracket_outlet_06|rbox|2.71|3|0.3|61.95|63.85|2.552544031|0.1653|-1.791431141|-2.577744372|61.95|-1.38087489|-2.169947114|63.85|0.62|0.64|0.66;bracket_outlet_07|rbox|2.71|3|0.3|61.95|63.85|2.945243113|0.1653|-0.732388758|-2.97161939|61.95|-0.381576981|-2.628664562|63.85|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_8                        As String  = "bracket_outlet_08|rbox|2.71|3|0.3|61.95|63.85|3.337942194|0.1653|0.381576981|-2.97161939|61.95|0.732388758|-2.628664562|63.85|0.62|0.64|0.66;bracket_outlet_09|rbox|2.71|3|0.3|61.95|63.85|3.730641276|0.1653|1.38087489|-2.577744372|61.95|1.791431141|-2.169947114|63.85|0.62|0.64|0.66;bracket_outlet_10|rbox|2.71|3|0.3|61.95|63.85|4.123340358|0.1653|2.169947114|-1.791431141|61.95|2.577744372|-1.38087489|63.85|0.62|0.64|0.66;bracket_outlet_11|rbox|2.71|3|0.3|61.95|63.85|4.51603944|0.1653|2.628664562|-0.732388758|61.95|2.97161939|-0.381576981|63.85|0.62|0.64|0.66;bracket_outlet_12|rbox|2.71|3|0.3|61.95|63.85|4.908738521|0.1653|2.628664562|0.381576981|61.95|2.97161939|0.732388758|63.85|0.62|0.64|0.66;bracket_outlet_13|rbox|2.71|3|0.3|61.95|63.85|5.301437603|0.1653|2.169947114|1.38087489|61.95|2.577744372|1.791431141|63.85|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_9                        As String  = "bracket_outlet_14|rbox|2.71|3|0.3|61.95|63.85|5.694136685|0.1653|1.38087489|2.169947114|61.95|1.791431141|2.577744372|63.85|0.62|0.64|0.66;bracket_outlet_15|rbox|2.71|3|0.3|61.95|63.85|6.086835766|0.1653|0.381576981|2.628664562|61.95|0.732388758|2.97161939|63.85|0.62|0.64|0.66;roller_outlet_L|cyl|-2.2839|-3.955830839|62.35|0|0|1|1.1178|1.1|4.317881988|-3.4017|-5.073630839|62.35|-1.1661|-2.838030839|63.45|0.1|0.16|0.72;shaft_outlet_L|cyl|-2.2839|-3.955830839|61.65|0|0|1|0.3|2.5|0.706858347|-2.5839|-4.255830839|61.65|-1.9839|-3.655830839|64.15|0.45|0.46|0.48;bearing_outlet_L_back|box|-2.7839|-1.7839|-4.455830839|-3.455830839|61.65|62.35|0.7|-2.7839|-4.455830839|61.65|-1.7839|-3.455830839|62.35|0.45|0.46|0.48;bearing_outlet_L_hood|box|-2.7839|-1.7839|-4.455830839|-3.455830839|63.45|64.15|0.7|-2.7839|-4.455830839|63.45|-1.7839|-3.455830839|64.15|0.45|0.46|0.48;" ' plant_geometry.kiln_rotax() bodies
Const KRX_10                       As String  = "roller_outlet_R|cyl|2.2839|-3.955830839|62.35|0|0|1|1.1178|1.1|4.317881988|1.1661|-5.073630839|62.35|3.4017|-2.838030839|63.45|0.1|0.16|0.72;shaft_outlet_R|cyl|2.2839|-3.955830839|61.65|0|0|1|0.3|2.5|0.706858347|1.9839|-4.255830839|61.65|2.5839|-3.655830839|64.15|0.45|0.46|0.48;bearing_outlet_R_back|box|1.7839|2.7839|-4.455830839|-3.455830839|61.65|62.35|0.7|1.7839|-4.455830839|61.65|2.7839|-3.455830839|62.35|0.45|0.46|0.48;bearing_outlet_R_hood|box|1.7839|2.7839|-4.455830839|-3.455830839|63.45|64.15|0.7|1.7839|-4.455830839|63.45|2.7839|-3.455830839|64.15|0.45|0.46|0.48;frame_outlet|box|-2.7839|2.7839|-5.055830839|-4.455830839|61.65|64.15|8.3517|-2.7839|-5.055830839|61.65|2.7839|-4.455830839|64.15|0.45|0.46|0.48;pier_outlet|box|-4.5|4.5|-8.113848577|-5.055830839|59.9|74|388.062450933|-4.5|-8.113848577|59.9|4.5|-5.055830839|74|0.78|0.77|0.74;" ' plant_geometry.kiln_rotax() bodies
Const KRX_11                       As String  = "htd|cyl|0|-3.4|25.57|0|1|0|0.7|0.35|0.53878314|-0.7|-3.4|24.87|0.7|-3.05|26.27|0.1|0.16|0.72;htd_stand|box|-0.35|0.35|-4.455830839|-3.4|25.22|25.92|0.517357111|-0.35|-4.455830839|25.22|0.35|-3.4|25.92|0.45|0.46|0.48;inlet_seal|ring|2.65|3.3|-0.45|0.45|10.935098629|-3.3|-3.3|-0.45|3.3|3.3|0.45|0.1|0.16|0.72;outlet_seal|ring|2.65|3.55|72.7|74|22.789113109|-3.55|-3.55|72.7|3.55|3.55|74|0.1|0.16|0.72;outlet_chute_1|cyl|-1.325|-5.055830839|73.35|0|1|0|0.25|1.762371412|0.346040818|-1.575|-5.055830839|73.1|-1.075|-3.293459427|73.6|0.1|0.16|0.72;outlet_chute_2|cyl|1.325|-5.055830839|73.35|0|1|0|0.25|1.762371412|0.346040818|1.075|-5.055830839|73.1|1.575|-3.293459427|73.6|0.1|0.16|0.72;nose_ring_fan|cyl|-4.265001533|-4.430830839|73.35|0.693496184|0.720460299|0|0.625|1.6|1.963495408|-4.715289219|-4.864265955|72.725|-2.705119951|-2.844659246|73.975|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_12                       As String  = "nose_ring_fan_stand|box|-4.483751533|-4.046251533|-5.055830839|-4.220267828|73.13125|73.56875|0.159931983|-4.483751533|-5.055830839|73.13125|-4.046251533|-4.220267828|73.56875|0.45|0.46|0.48;walkway|box|-4.5|-2.5|-6.255830839|-5.055830839|27.42|59.9|77.952|-4.5|-6.255830839|27.42|-2.5|-5.055830839|59.9|0.45|0.46|0.48;shell_fan_1|cyl|-2.816067839|-4.430830839|47.9|0.536393874|0.843967779|0|0.625|1.6|1.963495408|-3.343547701|-4.766077011|47.275|-1.430357778|-2.745236222|48.525|0.62|0.64|0.66;shell_fan_1_stand|box|-3.034817839|-2.597317839|-5.055830839|-4.291801646|47.68125|48.11875|0.146239963|-3.034817839|-5.055830839|47.68125|-2.597317839|-4.291801646|48.11875|0.45|0.46|0.48;shell_fan_2|cyl|-2.816067839|-4.430830839|51.9|0.536393874|0.843967779|0|0.625|1.6|1.963495408|-3.343547701|-4.766077011|51.275|-1.430357778|-2.745236222|52.525|0.62|0.64|0.66;" ' plant_geometry.kiln_rotax() bodies
Const KRX_13                       As String  = "shell_fan_2_stand|box|-3.034817839|-2.597317839|-5.055830839|-4.291801646|51.68125|52.11875|0.146239963|-3.034817839|-5.055830839|51.68125|-2.597317839|-4.291801646|52.11875|0.45|0.46|0.48;shell_fan_3|cyl|-2.816067839|-4.430830839|55.9|0.536393874|0.843967779|0|0.625|1.6|1.963495408|-3.343547701|-4.766077011|55.275|-1.430357778|-2.745236222|56.525|0.62|0.64|0.66;shell_fan_3_stand|box|-3.034817839|-2.597317839|-5.055830839|-4.291801646|55.68125|56.11875|0.146239963|-3.034817839|-5.055830839|55.68125|-2.597317839|-4.291801646|56.11875|0.45|0.46|0.48;" ' plant_geometry.kiln_rotax() bodies
Const KRX_14                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_15                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_16                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_17                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_18                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_19                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
Const KRX_20                       As String  = ""           ' plant_geometry.kiln_rotax() bodies
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
Dim logName As String             ' the build log's file name (main: kiln_rotax_build.log)
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
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln ROTAX-2 parts"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln ROTAX-2 parts"
    End If
End Sub


'==================================================================
' assembly: the whole kiln -- the wall (kiln_wall.SLDPRT: brick and
' shell) and these parts (kiln_rotax.SLDPRT), both at the origin of the
' kiln's frame and fixed  ->  kiln_assembly.SLDASM. Run after both
' parts are built (python3 tools/sw_run.py kiln_rotax_solid.assembly).
' The parts stay separate files, so rebuilding either updates it.
'==================================================================
Sub assembly()
    Dim why As String, outDir As String, tpl As String
    Dim asmDoc As SldWorks.ModelDoc2, asm As SldWorks.AssemblyDoc
    Dim doc As SldWorks.ModelDoc2, comp As SldWorks.Component2
    Dim parts As Variant, p As Variant, comps As Variant, t As Variant
    Dim e As Long, w As Long, k As Long, j As Long

    buildLog = ""
    logName = "kiln_assembly_build.log"
    phase = "starting up"
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    outDir = OUT_ROOT & LINE_KEY & "\"
    parts = Array("kiln_wall.SLDPRT", PART_NAME & ".SLDPRT")

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
                Fail comp.Name2 & " is not at the kiln frame's origin (transform term " & j & " = " & Fmt(t(j)) & ")."
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
        asmDoc.Extension.SaveAs outDir & "kiln_assembly_" & vn(k) & ".jpg", _
            swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
        k = k + 1
    Next vw
    asmDoc.ShowNamedView2 "", swIsometricView
    asmDoc.ViewZoomtofit2
    asmDoc.Extension.SaveAs outDir & "kiln_assembly.SLDASM", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    If e <> 0 Then Fail "could not write kiln_assembly.SLDASM (error " & e & ")."
    Note "wrote " & outDir & "kiln_assembly.SLDASM"
    WriteLog "kiln_assembly built, verified and saved"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_assembly saved." & vbLf & vbLf & buildLog, vbInformation, "Kiln assembly"
    Exit Sub

Failed:
    why = Err.Description
    WriteLog "kiln_assembly ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then MsgBox "kiln_assembly ABORTED:" & vbLf & why, vbCritical, "Kiln assembly"
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

    all = KRX_1 & KRX_2 & KRX_3 & KRX_4 & KRX_5 & KRX_6 & KRX_7 & KRX_8 & KRX_9 & KRX_10 & _
          KRX_11 & KRX_12 & KRX_13 & KRX_14 & KRX_15 & KRX_16 & KRX_17 & KRX_18 & KRX_19 & KRX_20
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
        If Left(bName(i), 8) <> "bracket_" Or Right(bName(i), 3) = "_00" Then _
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
    Err.Raise vbObjectError + 1, "kiln_rotax", msg
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
