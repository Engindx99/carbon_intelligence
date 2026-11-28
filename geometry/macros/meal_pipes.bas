Attribute VB_Name = "meal_pipes"
'==================================================================
' The tower's MEAL PIPES (each pipe's bore, D)  ->  SLDPRT + STEP
'
' NOT a CFD input (user request, 24 Nov 2026: connect the meal pipes);
' plant_assembly.tower places it (the plant frame, z up). Each
' cyclone's meal pipe from its dust outlet to the riser two stages
' down (C1 -> R2, C2 -> R3, C3 -> R4), C4's to the calciner's meal pipe,
' C5's to the kiln inlet chamber's roof; both strings.
'
'   meal_<C1_in|C1_out|C2|C3|C4|C5>_<string>_<run>   one cylinder a run
'
' Every run, its size, place, volume and extent come from
' geometry/plant_geometry.py meal_routes() / meal_pipe_bodies() (the
' generated MLP_ strings), built as temporary modeler bodies, checked
' against the generated volume and exact extent. D: meal_pipes() (the
' calciner's feed pipe scaled by mass flux); routes: plant_geometry.yaml
' meal_route.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py meal_pipes_solid.main from WSL.
' Outputs geometry\output\2500\meal_pipes.SLDPRT, .step and
' meal_pipes_build.log.
'==================================================================

Option Explicit

Const PART_NAME As String = "meal_pipes"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 46           ' bodies in the part [derived]
Const MLP_1                        As String  = "meal_C1_out_1_1|cyl|18.498678979|-4.366093711|92.727335263|0|0|-1|0.299990052|2.080382092|0.588175169|18.198688927|-4.666083763|90.646953171|18.798669031|-4.066103659|92.727335263|0.93|0.55|0.13;meal_C1_out_1_2|cyl|18.53780427|-4.375287831|90.796948197|-0.486741378|0.114380205|-0.866025404|0.299990052|10.24692223|2.89705686|13.28814808|-4.673309063|81.772858209|18.799859417|-2.905221531|90.946943223|0.93|0.55|0.13;meal_C1_out_1_3|cyl|13.589328518|-3.212436883|82.072848261|0|0|-1|0.299990052|10.751015483|3.039576417|13.289338466|-3.512426935|71.321832778|13.88931857|-2.912446831|82.072848261|0.93|0.55|0.13;meal_C1_in_1_1|cyl|9.991292619|-4.366093711|92.727335263|0|0|-1|0.299990052|2.080382092|0.588175169|9.691302567|-4.666083763|90.646953171|10.291282671|-4.066103659|92.727335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_2                        As String  = "meal_C1_in_1_2|cyl|10.011899031|-4.331587249|90.796948197|-0.256355766|-0.429280469|-0.866025404|0.299990052|0.891908385|0.25216443|9.493288041|-4.985408484|89.874537852|10.301864165|-4.060644863|90.946943223|0.93|0.55|0.13;meal_C1_in_1_3|cyl|9.803859587|-4.679959636|90.174527904|0|0|-1|0.299990052|18.852695126|5.330120452|9.503869535|-4.979949688|71.321832778|10.103849639|-4.379969585|90.174527904|0.93|0.55|0.13;meal_C2_1_1|cyl|14.244985799|2.36129265|69.772335263|0|0|-1|0.42425|2.113677445|1.195177167|13.820735799|1.93704265|67.658657818|14.669235799|2.78554265|69.772335263|0.93|0.55|0.13;meal_C2_1_2|cyl|14.299287395|2.344500477|67.870782818|-0.477681353|0.14771772|-0.866025404|0.42425|11.378093726|6.433733709|8.491466492|1.924904685|57.804939605|14.672005091|4.444842337|68.082907818|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_3                        As String  = "meal_C2_1_3|cyl|8.918485784|4.008454372|58.229189605|0|0|-1|0.42425|0.738326148|0.417485911|8.494235784|3.584204372|57.490863457|9.342735784|4.432704372|58.229189605|0.93|0.55|0.13;meal_C3_1_1|cyl|11.696594052|-3.94619826|55.672335263|0|0|-1|0.42425|2.113677445|1.195177167|11.272344052|-4.37044826|53.558657818|12.120844052|-3.52194826|55.672335263|0.93|0.55|0.13;meal_C3_1_2|cyl|11.750515119|-3.964174882|53.770782818|-0.474333908|0.158137106|-0.866025404|0.42425|4.008563861|2.266639128|9.475630987|-4.383086614|50.087139682|12.124001491|-2.911360464|53.982907818|0.93|0.55|0.13;meal_C3_1_3|cyl|9.903038426|-3.348248818|50.511389682|0|0|-1|0.42425|7.120526225|4.026295679|9.478788426|-3.772498818|43.390863457|10.327288426|-2.923998818|50.511389682|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_4                        As String  = "meal_C4_1_1|cyl|8.29517001|1.945241|41.572335263|0|0|-1|0.42425|2.083773734|1.178268138|7.87092001|1.520991|39.488561529|8.71942001|2.369491|41.572335263|0.93|0.55|0.13;meal_C4_1_2|cyl|8.324287858|1.958129657|39.649821209|-0.347577299|-0.153850809|-0.924943214|0.42425|12.811231386|7.244100217|3.473596074|-0.432087574|27.638899993|8.722086436|2.377328574|39.811080889|0.93|0.55|0.13;meal_C4_1_3|cyl|3.9005125|0|27.961419353|0|0|-1|0.42425|2.183773734|1.234813056|3.4762625|-0.42425|25.777645619|4.3247625|0.42425|27.961419353|0.93|0.55|0.13;meal_C5_1_1|cyl|8.29517001|-4.857607085|27.040589231|0|0|-1|0.348756357|2.109142601|0.80593512|7.946413653|-5.206363442|24.93144663|8.643926367|-4.508850728|27.040589231|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_5                        As String  = "meal_C5_1_2|cyl|8.348860086|-4.889047706|25.13026069|-0.491925931|0.288069188|-0.821599064|0.348756357|13.570832146|5.185619137|1.369375638|-5.223020141|13.781663648|8.652500292|-0.645736674|25.32907475|0.93|0.55|0.13;meal_C5_1_3|cyl|1.726705921|-1.01114973|14.179291768|0|0|-1|0.348756357|0.209142601|0.079916534|1.377949564|-1.359906087|13.970149167|2.075462278|-0.662393373|14.179291768|0.93|0.55|0.13;meal_C1_out_2_1|cyl|-18.498678979|-4.366093711|92.727335263|0|0|-1|0.299990052|2.080382092|0.588175169|-18.798669031|-4.666083763|90.646953171|-18.198688927|-4.066103659|92.727335263|0.93|0.55|0.13;meal_C1_out_2_2|cyl|-18.53780427|-4.375287831|90.796948197|0.486741378|0.114380205|-0.866025404|0.299990052|10.24692223|2.89705686|-18.799859417|-4.673309063|81.772858209|-13.28814808|-2.905221531|90.946943223|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_6                        As String  = "meal_C1_out_2_3|cyl|-13.589328518|-3.212436883|82.072848261|0|0|-1|0.299990052|10.751015483|3.039576417|-13.88931857|-3.512426935|71.321832778|-13.289338466|-2.912446831|82.072848261|0.93|0.55|0.13;meal_C1_in_2_1|cyl|-9.991292619|-4.366093711|92.727335263|0|0|-1|0.299990052|2.080382092|0.588175169|-10.291282671|-4.666083763|90.646953171|-9.691302567|-4.066103659|92.727335263|0.93|0.55|0.13;meal_C1_in_2_2|cyl|-10.011899031|-4.331587249|90.796948197|0.256355766|-0.429280469|-0.866025404|0.299990052|0.891908385|0.25216443|-10.301864165|-4.985408484|89.874537852|-9.493288041|-4.060644863|90.946943223|0.93|0.55|0.13;meal_C1_in_2_3|cyl|-9.803859587|-4.679959636|90.174527904|0|0|-1|0.299990052|18.852695126|5.330120452|-10.103849639|-4.979949688|71.321832778|-9.503869535|-4.379969585|90.174527904|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_7                        As String  = "meal_C2_2_1|cyl|-14.244985799|2.36129265|69.772335263|0|0|-1|0.42425|2.113677445|1.195177167|-14.669235799|1.93704265|67.658657818|-13.820735799|2.78554265|69.772335263|0.93|0.55|0.13;meal_C2_2_2|cyl|-14.299287395|2.344500477|67.870782818|0.477681353|0.14771772|-0.866025404|0.42425|11.378093726|6.433733709|-14.672005091|1.924904685|57.804939605|-8.491466492|4.444842337|68.082907818|0.93|0.55|0.13;meal_C2_2_3|cyl|-8.918485784|4.008454372|58.229189605|0|0|-1|0.42425|0.738326148|0.417485911|-9.342735784|3.584204372|57.490863457|-8.494235784|4.432704372|58.229189605|0.93|0.55|0.13;meal_C3_2_1|cyl|-11.696594052|-3.94619826|55.672335263|0|0|-1|0.42425|2.113677445|1.195177167|-12.120844052|-4.37044826|53.558657818|-11.272344052|-3.52194826|55.672335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_8                        As String  = "meal_C3_2_2|cyl|-11.750515119|-3.964174882|53.770782818|0.474333908|0.158137106|-0.866025404|0.42425|4.008563861|2.266639128|-12.124001491|-4.383086614|50.087139682|-9.475630987|-2.911360464|53.982907818|0.93|0.55|0.13;meal_C3_2_3|cyl|-9.903038426|-3.348248818|50.511389682|0|0|-1|0.42425|7.120526225|4.026295679|-10.327288426|-3.772498818|43.390863457|-9.478788426|-2.923998818|50.511389682|0.93|0.55|0.13;meal_C4_2_1|cyl|-8.29517001|1.945241|41.572335263|0|0|-1|0.42425|2.083773734|1.178268138|-8.71942001|1.520991|39.488561529|-7.87092001|2.369491|41.572335263|0.93|0.55|0.13;meal_C4_2_2|cyl|-8.324287858|1.958129657|39.649821209|0.347577299|-0.153850809|-0.924943214|0.42425|12.811231386|7.244100217|-8.722086436|-0.432087574|27.638899993|-3.473596074|2.377328574|39.811080889|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_9                        As String  = "meal_C4_2_3|cyl|-3.9005125|0|27.961419353|0|0|-1|0.42425|2.183773734|1.234813056|-4.3247625|-0.42425|25.777645619|-3.4762625|0.42425|27.961419353|0.93|0.55|0.13;meal_C5_2_1|cyl|-8.29517001|-4.857607085|27.040589231|0|0|-1|0.348756357|2.109142601|0.80593512|-8.643926367|-5.206363442|24.93144663|-7.946413653|-4.508850728|27.040589231|0.93|0.55|0.13;meal_C5_2_2|cyl|-8.348860086|-4.889047706|25.13026069|0.491925931|0.288069188|-0.821599064|0.348756357|13.570832146|5.185619137|-8.652500292|-5.223020141|13.781663648|-1.369375638|-0.645736674|25.32907475|0.93|0.55|0.13;meal_C5_2_3|cyl|-1.726705921|-1.01114973|14.179291768|0|0|-1|0.348756357|0.209142601|0.079916534|-2.075462278|-1.359906087|13.970149167|-1.377949564|-0.662393373|14.179291768|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_10                       As String  = "dbox_C1_out_1|owedge|13.449717918|-3.266560094|70.122837748|0.932387221|0.36146102|1.295957024|0.889444271|1.298995029|60|0.139469141|0.866057888|12.800845707|-4.031476695|70.122837748|14.098590128|-2.501643493|71.421832778|0.55|0.55|0.6;dbox_C1_in_1|owedge|9.943470187|-4.625836426|70.122837748|-0.932387221|-0.36146102|1.295957024|0.889444271|1.298995029|60|0.139469141|0.866057888|9.294597977|-5.390753027|70.122837748|10.592342397|-3.860919825|71.421832778|0.55|0.55|0.6;dbox_C2_1|owedge|8.861508455|3.819855924|55.753807069|0.289199721|0.957268782|1.83276|1.354659467|1.837056388|60|0.294034467|2.775480174|7.788402918|2.906452475|55.753807069|9.934613992|4.733259374|57.590863457|0.55|0.55|0.6;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_11                       As String  = "dbox_C3_1|owedge|9.763405539|-3.47932674|41.653807069|0.729088696|0.684419223|1.83276|1.343659018|1.837056388|60|0.283034018|2.738442945|8.646394151|-4.607262071|41.653807069|10.880416928|-2.35139141|43.490863457|0.55|0.55|0.6;dbox_C5_1|owedge|1.643334944|-0.962328133|12.559989842|0.862928384|-0.505326235|1.506627462|1.065118923|1.510159324|60|0.193228031|1.431525386|0.803105077|-1.881500201|12.559989842|2.483564812|-0.043156065|14.070149167|0.55|0.55|0.6;dbox_C1_out_2|owedge|-13.449717918|-3.266560094|70.122837748|-0.932387221|0.36146102|1.295957024|0.889444271|1.298995029|60|0.139469141|0.866057888|-14.098590128|-4.031476695|70.122837748|-12.800845707|-2.501643493|71.421832778|0.55|0.55|0.6;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_12                       As String  = "dbox_C1_in_2|owedge|-9.943470187|-4.625836426|70.122837748|0.932387221|-0.36146102|1.295957024|0.889444271|1.298995029|60|0.139469141|0.866057888|-10.592342397|-5.390753027|70.122837748|-9.294597977|-3.860919825|71.421832778|0.55|0.55|0.6;dbox_C2_2|owedge|-8.861508455|3.819855924|55.753807069|-0.289199721|0.957268782|1.83276|1.354659467|1.837056388|60|0.294034467|2.775480174|-9.934613992|2.906452475|55.753807069|-7.788402918|4.733259374|57.590863457|0.55|0.55|0.6;dbox_C3_2|owedge|-9.763405539|-3.47932674|41.653807069|-0.729088696|0.684419223|1.83276|1.343659018|1.837056388|60|0.283034018|2.738442945|-10.880416928|-4.607262071|41.653807069|-8.646394151|-2.35139141|43.490863457|0.55|0.55|0.6;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_13                       As String  = "dbox_C5_2|owedge|-1.643334944|-0.962328133|12.559989842|-0.862928384|-0.505326235|1.506627462|1.065118923|1.510159324|60|0.193228031|1.431525386|-2.483564812|-1.881500201|12.559989842|-0.803105077|-0.043156065|14.070149167|0.55|0.55|0.6;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_14                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_15                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_16                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_17                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_18                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_19                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_20                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
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
Dim logName As String             ' the build log's file name (main: meal_pipes_build.log)
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
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Meal pipes"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Meal pipes"
    End If
End Sub


'==================================================================
' The generated records: name|kind|params|V|box(6)|rgb(3), ";" between
'==================================================================
Private Sub ReadBodies()
    Dim all As String, recs As Variant, f As Variant
    Dim i As Long, j As Long, np As Long, k As Long

    all = MLP_1 & MLP_2 & MLP_3 & MLP_4 & MLP_5 & MLP_6 & MLP_7 & MLP_8 & MLP_9 & MLP_10 & MLP_11 & MLP_12 & MLP_13 & MLP_14 & MLP_15 & MLP_16 & MLP_17 & MLP_18 & MLP_19 & MLP_20
    recs = Split(all, ";")
    nB = CLng(N_BODIES)
    ReDim bName(nB - 1): ReDim bKind(nB - 1)
    ReDim bP(nB - 1, 9): ReDim bV(nB - 1): ReDim bBox(nB - 1, 5): ReDim bRGB(nB - 1, 2)

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
                Case "owedge": np = 10
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
        Case "owedge"
            Set MakeBody = WedgeBody(i)
        Case "cyl"
            Set MakeBody = CylBody(bP(i, 0), bP(i, 1), bP(i, 2), bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7))
    End Select
End Function


' An oriented wedge (the dispersion box). p(i, 0..9): cx, cy (the floor's middle of the run, plan),
' z0 (its floor), ux, uy (the outward unit vector), w (width across), run (along u), H (height),
' slope (deg), flat (the level lead-in on the wall side, before the ramp starts). Built at the origin
' as the box run x w x H (x along u, z from 0), its lower outer part cut away by a plane through the
' floor at `flat` from its wall-side end rising outwards at slope, turned about z to u and moved to
' (cx, cy, z0). The cutter is a big box with its top face on that plane, tilted about its width axis.
' The transforms' row conventions are not trusted: the readings are tried and the one whose cutter
' rises outwards (its highest point on the outer side) and whose wedge lands in the expected extent
' is used.
Private Function WedgeBody(ByVal i As Long) As SldWorks.Body2
    Dim b As SldWorks.Body2, c As SldWorks.Body2, t As SldWorks.Body2, res As Variant, e As Long
    Dim ux As Double, uy As Double, ph As Double, th As Double
    Dim run As Double, wid As Double, hgt As Double, big As Double, flat As Double
    Dim px As Double, py As Double, pz As Double
    Dim k As Long, m As Long, cut As SldWorks.Body2, w2 As SldWorks.Body2

    ux = bP(i, 3): uy = bP(i, 4): wid = bP(i, 5): run = bP(i, 6): hgt = bP(i, 7)
    ph = bP(i, 8) * 3.14159265358979 / 180#: flat = bP(i, 9)
    th = Atn2(uy, ux)
    big = 4# * (run + hgt + wid)

    Set b = BoxBody(-0.5 * run, 0.5 * run, -0.5 * wid, 0.5 * wid, 0#, hgt)
    For k = 0 To 1
        Set c = BoxBody(-big, big, -big, big, -big, 0#)
        c.ApplyTransform RotY(ph, k = 1)
        c.ApplyTransform MoveBy(-0.5 * run + flat, 0#, 0#)
        ' it rises outwards if its highest point lies on the outer side of the bottom edge
        If c.GetExtremePoint(0#, 0#, 1#, px, py, pz) Then
            If px > -0.5 * run + flat Then
                Set t = b.Copy
                res = t.Operations2(SWBODYCUT, c, e)
                If e = swBodyOperationNoError And Not IsEmpty(res) Then
                    If UBound(res) = 0 Then Set cut = res(0)
                End If
                If Not cut Is Nothing Then Exit For
            End If
        End If
    Next k
    If cut Is Nothing Then Fail bName(i) & ": no transform reading gave a cutter rising outwards."
    For m = 0 To 1
        Set w2 = cut.Copy
        w2.ApplyTransform TurnZ(th, m = 1)
        w2.ApplyTransform MoveBy(bP(i, 0), bP(i, 1), bP(i, 2))
        If BoxIs(w2, i) Then Set WedgeBody = w2: Exit Function
    Next m
    Fail bName(i) & ": neither reading of the turn put it at " & WantText(i) & "."
End Function


Private Function Atn2(ByVal y As Double, ByVal x As Double) As Double
    If Abs(x) < 0.000001 Then
        Atn2 = IIf(y > 0#, 1.5707963267949, -1.5707963267949)
    ElseIf x > 0# Then
        Atn2 = Atn(y / x)
    ElseIf y >= 0# Then
        Atn2 = Atn(y / x) + 3.14159265358979
    Else
        Atn2 = Atn(y / x) - 3.14159265358979
    End If
End Function


' A turn about +y by th (or its transpose), and a plain move.
Private Function RotY(ByVal th As Double, ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double, c As Double, s As Double
    c = Cos(th): s = Sin(th)
    t(0) = c: t(4) = 1#: t(8) = c
    If transposed Then
        t(2) = -s: t(6) = s
    Else
        t(2) = s: t(6) = -s
    End If
    t(12) = 1#
    Set RotY = mu.CreateTransform(t)
End Function


Private Function MoveBy(ByVal dx As Double, ByVal dy As Double, ByVal dz As Double) As SldWorks.MathTransform
    Dim t(15) As Double
    t(0) = 1#: t(4) = 1#: t(8) = 1#
    t(9) = dx: t(10) = dy: t(11) = dz
    t(12) = 1#
    Set MoveBy = mu.CreateTransform(t)
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


Private Sub PaintBody(body As SldWorks.Body2, ByVal r As Double, ByVal g As Double, ByVal b As Double, _
                      Optional ByVal see As Double = 0#)
    Dim faces As Variant, face As SldWorks.Face2
    Dim m(8) As Double, k As Long
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = see: m(8) = 0#
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
    Err.Raise vbObjectError + 1, "meal_pipes", msg
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
