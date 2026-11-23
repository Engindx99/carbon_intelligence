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
Const N_BODIES                     As Double  = 40           ' bodies in the part [derived]
Const MLP_1                        As String  = "meal_C1_out_1_1|cyl|12.54886319|-4.782145361|92.727335263|0|0|-1|0.299990052|1.580382092|0.446812875|12.248873138|-5.082135413|91.146953171|12.848853242|-4.482155309|92.727335263|0.93|0.55|0.13;meal_C1_out_1_2|cyl|12.58901369|-4.780340489|91.296948197|-0.499495579|-0.022453655|-0.866025404|0.299990052|3.521541038|0.995626237|10.570133198|-5.159326377|88.097209171|12.848900002|-4.480426069|91.446943223|0.93|0.55|0.13;meal_C1_out_1_3|cyl|10.87017001|-4.857607085|88.397199223|0|0|-1|0.299990052|15.973195245|4.516015036|10.570179958|-5.157597137|72.424003978|11.170160062|-4.557617033|88.397199223|0.93|0.55|0.13;meal_C1_out_1_4|cyl|10.910361056|-4.857607085|72.573999004|-0.5|0|-0.866025404|0.299990052|2.680362196|0.757804296|9.310380952|-5.157597137|70.102742225|11.170160062|-4.557617033|72.72399403|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_2                        As String  = "meal_C1_in_1_1|cyl|4.041476829|-4.782145361|92.727335263|0|0|-1|0.299990052|1.580382092|0.446812875|3.741486778|-5.082135413|91.146953171|4.341466881|-4.482155309|92.727335263|0.93|0.55|0.13;meal_C1_in_1_2|cyl|4.00132633|-4.780340489|91.296948197|0.499495579|-0.022453655|-0.866025404|0.299990052|3.521541038|0.995626237|3.741440017|-5.159326377|88.097209171|6.020206822|-4.480426069|91.446943223|0.93|0.55|0.13;meal_C1_in_1_3|cyl|5.72017001|-4.857607085|88.397199223|0|0|-1|0.299990052|15.973195245|4.516015036|5.420179958|-5.157597137|72.424003978|6.020160062|-4.557617033|88.397199223|0.93|0.55|0.13;meal_C1_in_1_4|cyl|5.679978964|-4.857607085|72.573999004|0.5|0|-0.866025404|0.299990052|2.680362196|0.757804296|5.420179958|-5.157597137|70.102742225|7.279959068|-4.557617033|72.72399403|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_3                        As String  = "meal_C2_1_1|cyl|8.29517001|1.945241|69.772335263|0|0|-1|0.42425|0.413677445|0.23391357|7.87092001|1.520991|69.358657818|8.71942001|2.369491|69.772335263|0.93|0.55|0.13;meal_C2_1_2|cyl|8.29517001|1.888402277|69.570782818|0|0.5|-0.866025404|0.42425|5.37735489|3.040620885|7.87092001|1.520991|64.701731878|8.71942001|4.944491|69.782907818|0.93|0.55|0.13;meal_C2_1_3|cyl|8.29517001|4.520241|65.125981878|0|0|-1|0.42425|6.835273253|3.864999621|7.87092001|4.095991|58.290708626|8.71942001|4.944491|65.125981878|0.93|0.55|0.13;meal_C2_1_4|cyl|8.29517001|4.577079722|58.502833626|0|-0.5|-0.866025404|0.42425|2.962177445|1.674960792|7.87092001|2.728579722|55.725387708|8.71942001|4.944491|58.714958626|0.93|0.55|0.13;meal_C3_1_1|cyl|8.29517001|-4.857607085|55.672335263|0|0|-1|0.42425|0.413677445|0.23391357|7.87092001|-5.281857085|55.258657818|8.71942001|-4.433357085|55.672335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_4                        As String  = "meal_C3_1_2|cyl|8.29517001|-4.800768363|55.470782818|0|-0.5|-0.866025404|0.42425|5.47735489|3.097165803|7.87092001|-7.906857085|50.515129338|8.71942001|-4.433357085|55.682907818|0.93|0.55|0.13;meal_C3_1_3|cyl|8.29517001|-7.482607085|50.939379338|0|0|-1|0.42425|6.748670712|3.816030286|7.87092001|-7.906857085|44.190708626|8.71942001|-7.058357085|50.939379338|0.93|0.55|0.13;meal_C3_1_4|cyl|8.29517001|-7.539445808|44.402833626|0|0.5|-0.866025404|0.42425|2.962177445|1.674960792|7.87092001|-7.906857085|41.625387708|8.71942001|-5.690945808|44.614958626|0.93|0.55|0.13;meal_C4_1_1|cyl|8.29517001|1.945241|41.572335263|0|0|-1|0.42425|1.565541487|0.885234142|7.87092001|1.520991|40.006793775|8.71942001|2.369491|41.572335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_5                        As String  = "meal_C4_1_2|cyl|8.313276369|1.953200654|40.134821183|-0.276257985|-0.12144452|-0.953379648|0.42425|16.50731947|9.334050174|3.345257868|-0.472632633|24.269051342|8.721016051|2.37431045|40.262848591|0.93|0.55|0.13;meal_C5_1_1|cyl|8.29517001|-4.857607085|27.040589231|0|0|-1|0.348756357|1.10666849|0.42287468|7.946413653|-5.206363442|25.933920741|8.643926367|-4.508850728|27.040589231|0.93|0.55|0.13;meal_C5_1_2|cyl|8.346659384|-4.887758987|26.129007973|-0.482704634|0.282669246|-0.828911536|0.348756357|14.842388009|5.671499763|0.876734949|-5.222292167|13.630894105|8.652094347|-0.357739182|26.324095205|0.93|0.55|0.13;meal_C1_out_2_1|cyl|-12.54886319|-4.782145361|92.727335263|0|0|-1|0.299990052|1.580382092|0.446812875|-12.848853242|-5.082135413|91.146953171|-12.248873138|-4.482155309|92.727335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_6                        As String  = "meal_C1_out_2_2|cyl|-12.58901369|-4.780340489|91.296948197|0.499495579|-0.022453655|-0.866025404|0.299990052|3.521541038|0.995626237|-12.848900002|-5.159326377|88.097209171|-10.570133198|-4.480426069|91.446943223|0.93|0.55|0.13;meal_C1_out_2_3|cyl|-10.87017001|-4.857607085|88.397199223|0|0|-1|0.299990052|15.973195245|4.516015036|-11.170160062|-5.157597137|72.424003978|-10.570179958|-4.557617033|88.397199223|0.93|0.55|0.13;meal_C1_out_2_4|cyl|-10.910361056|-4.857607085|72.573999004|0.5|0|-0.866025404|0.299990052|2.680362196|0.757804296|-11.170160062|-5.157597137|70.102742225|-9.310380952|-4.557617033|72.72399403|0.93|0.55|0.13;meal_C1_in_2_1|cyl|-4.041476829|-4.782145361|92.727335263|0|0|-1|0.299990052|1.580382092|0.446812875|-4.341466881|-5.082135413|91.146953171|-3.741486778|-4.482155309|92.727335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_7                        As String  = "meal_C1_in_2_2|cyl|-4.00132633|-4.780340489|91.296948197|-0.499495579|-0.022453655|-0.866025404|0.299990052|3.521541038|0.995626237|-6.020206822|-5.159326377|88.097209171|-3.741440017|-4.480426069|91.446943223|0.93|0.55|0.13;meal_C1_in_2_3|cyl|-5.72017001|-4.857607085|88.397199223|0|0|-1|0.299990052|15.973195245|4.516015036|-6.020160062|-5.157597137|72.424003978|-5.420179958|-4.557617033|88.397199223|0.93|0.55|0.13;meal_C1_in_2_4|cyl|-5.679978964|-4.857607085|72.573999004|-0.5|0|-0.866025404|0.299990052|2.680362196|0.757804296|-7.279959068|-5.157597137|70.102742225|-5.420179958|-4.557617033|72.72399403|0.93|0.55|0.13;meal_C2_2_1|cyl|-8.29517001|1.945241|69.772335263|0|0|-1|0.42425|0.413677445|0.23391357|-8.71942001|1.520991|69.358657818|-7.87092001|2.369491|69.772335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_8                        As String  = "meal_C2_2_2|cyl|-8.29517001|1.888402277|69.570782818|0|0.5|-0.866025404|0.42425|5.37735489|3.040620885|-8.71942001|1.520991|64.701731878|-7.87092001|4.944491|69.782907818|0.93|0.55|0.13;meal_C2_2_3|cyl|-8.29517001|4.520241|65.125981878|0|0|-1|0.42425|6.835273253|3.864999621|-8.71942001|4.095991|58.290708626|-7.87092001|4.944491|65.125981878|0.93|0.55|0.13;meal_C2_2_4|cyl|-8.29517001|4.577079722|58.502833626|0|-0.5|-0.866025404|0.42425|2.962177445|1.674960792|-8.71942001|2.728579722|55.725387708|-7.87092001|4.944491|58.714958626|0.93|0.55|0.13;meal_C3_2_1|cyl|-8.29517001|-4.857607085|55.672335263|0|0|-1|0.42425|0.413677445|0.23391357|-8.71942001|-5.281857085|55.258657818|-7.87092001|-4.433357085|55.672335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_9                        As String  = "meal_C3_2_2|cyl|-8.29517001|-4.800768363|55.470782818|0|-0.5|-0.866025404|0.42425|5.47735489|3.097165803|-8.71942001|-7.906857085|50.515129338|-7.87092001|-4.433357085|55.682907818|0.93|0.55|0.13;meal_C3_2_3|cyl|-8.29517001|-7.482607085|50.939379338|0|0|-1|0.42425|6.748670712|3.816030286|-8.71942001|-7.906857085|44.190708626|-7.87092001|-7.058357085|50.939379338|0.93|0.55|0.13;meal_C3_2_4|cyl|-8.29517001|-7.539445808|44.402833626|0|0.5|-0.866025404|0.42425|2.962177445|1.674960792|-8.71942001|-7.906857085|41.625387708|-7.87092001|-5.690945808|44.614958626|0.93|0.55|0.13;meal_C4_2_1|cyl|-8.29517001|1.945241|41.572335263|0|0|-1|0.42425|1.565541487|0.885234142|-8.71942001|1.520991|40.006793775|-7.87092001|2.369491|41.572335263|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_10                       As String  = "meal_C4_2_2|cyl|-8.313276369|1.953200654|40.134821183|0.276257985|-0.12144452|-0.953379648|0.42425|16.50731947|9.334050174|-8.721016051|-0.472632633|24.269051342|-3.345257868|2.37431045|40.262848591|0.93|0.55|0.13;meal_C5_2_1|cyl|-8.29517001|-4.857607085|27.040589231|0|0|-1|0.348756357|1.10666849|0.42287468|-8.643926367|-5.206363442|25.933920741|-7.946413653|-4.508850728|27.040589231|0.93|0.55|0.13;meal_C5_2_2|cyl|-8.346659384|-4.887758987|26.129007973|0.482704634|0.282669246|-0.828911536|0.348756357|14.842388009|5.671499763|-8.652094347|-5.222292167|13.630894105|-0.876734949|-0.357739182|26.324095205|0.93|0.55|0.13;" ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_11                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
Const MLP_12                       As String  = ""           ' plant_geometry.meal_pipe_bodies() bodies
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

    all = MLP_1 & MLP_2 & MLP_3 & MLP_4 & MLP_5 & MLP_6 & MLP_7 & MLP_8 & MLP_9 & MLP_10 & MLP_11 & MLP_12
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
