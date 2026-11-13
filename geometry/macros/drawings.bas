Attribute VB_Name = "drawings"
'==================================================================
' Equipment drawings: ISO engineering drawings of the INNER (fluid)
' geometry, from the CFD solids cyclone.bas / calciner.bas built.
'
' Pilot: cyclone C1 (output\2500\C1.SLDPRT, built by cyclone.bas with
' RISER_ON = False). One A1 sheet, first-angle projection (ISO 5456-2):
'
'   top view      base view, looking -z: x right, y up
'   section A-A   the plane y = 0, looking +y: x right, z up -- the
'                 front view, aligned over the top view
'   left view     unfolded from A-A: looking +x, z up
'   detail B      the vortex finder's mouth, 1:20
'
' Dimensions are reference dimensions on the views' real edges (the
' solids carry no sketch dimensions): each is selected at the sheet
' point a model point maps to, checked against the edge it should be,
' and read back. Estimated values carry the suffix " E"; Unknown is
' never dimensioned. The sheet's parameter table lists every value
' with its source and status (tools/drawings/cyclone.py).
'
' The numbers are the one source's (geometry/plant_geometry.yaml),
' written into the generated block below by tools/gen_geometry.py.
' Nothing structural is drawn: no wall, refractory, flange, support
' or material -- no source gives one, and the table says so.
'
' Run: build C1 first (cyclone.bas with CYCLONE_NAME "C1" and, in its
' C1 case, RISER_ON = False: the gas-only domain, output\2500\C1.SLDPRT;
' CheckPartBox refuses anything else), then Tools > Macro > New,
' import this file, run main. Outputs:
'   geometry\drawings\C1\C1.pdf, C1.dxf             (committed)
'   geometry\output\2500\drawings\C1.SLDDRW         (references the part)
'   geometry\output\2500\drawings_C1_build.log      (tests read it)
'==================================================================
Option Explicit

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const C1_D_BARREL                  As Double  = 4.32         ' barrel inner D [published, preheater/cyclone_C1.md]
Const C1_H_BARREL                  As Double  = 6.79         ' barrel height [derived_from_reference, preheater/cyclone_C1.md]
Const C1_H_CONE                    As Double  = 4.65         ' cone height [derived_from_reference, preheater/cyclone_C1.md]
Const C1_L_VORTEX                  As Double  = 2.16         ' vortex finder immersion [derived_from_reference, preheater/cyclone_C1.md]
Const C1_D_VORTEX                  As Double  = 2.4          ' vortex finder / outlet pipe bore [derived_from_reference, preheater/cyclone_C1.md]
Const C1_D_DUST                    As Double  = 0.4          ' dust outlet D [derived_from_reference, preheater/cyclone_C1.md]
Const C1_W_INLET                   As Double  = 0.86         ' inlet width [derived_from_reference, preheater/cyclone_C1.md]
Const C1_H_INLET                   As Double  = 2.16         ' inlet height, normal to the duct [cfd_decision, preheater/cyclone_C1.md]
Const C1_INLET_SLOPE_DEG           As Double  = 5#           ' inlet duct slope [cfd_decision, preheater/cyclone_C1.md]
Const C1_VORTEX_WALL               As Double  = 0.08         ' vortex finder wall [model, preheater/cyclone_C1.md]
Const C1_HEIGHT                    As Double  = 11.44        ' barrel + cone [derived]
Const C1_OUT_RISE                  As Double  = 3#           ' outlet pipe rise over the roof [derived]
Const C1_OUT_R                     As Double  = 3.6          ' outlet bend centreline R [derived]
Const C1_OUT_RUN                   As Double  = 3#           ' outlet drop leg [derived]
Const C1_LEG_X                     As Double  = 7.2          ' barrel axis to drop leg axis [derived]
Const C1_TOP                       As Double  = 19.24        ' dust outlet to the top of the bend [derived]
Const C1_Y_INNER                   As Double  = 1.3          ' inlet duct inner wall, y [derived]
Const C1_Y_OUTER                   As Double  = 2.16         ' inlet duct outer wall, y [derived]
Const C1_FACE_TOP_X                As Double  = -2.894456    ' inlet face, upper edge x [derived]
Const C1_FACE_TOP_Z                As Double  = 11.492315    ' inlet face, upper edge z [derived]
Const C1_FACE_BOT_X                As Double  = -3.082712    ' inlet face, lower edge x [derived]
Const C1_FACE_BOT_Z                As Double  = 9.340534     ' inlet face, lower edge z [derived]
Const C1_REACH                     As Double  = 1.724993     ' inlet opening's upstream end on the barrel, -x [derived]
Const C1_TAB_1                     As String  = "per_string~Number per string~2~-~published~Verified;D_barrel~Barrel inner diameter D~4320~mm~published~Verified;H_barrel~Barrel height~6790~mm~FLS ratio~Estimated;H_cone~Cone height~4650~mm~FLS ratio~Estimated;height~Barrel + cone height~11440~mm~derived~Estimated;L_vortex~Vortex finder immersion S~2160~mm~FLS ratio~Estimated;D_vortex~Vortex finder / outlet pipe bore Dx~2400~mm~FLS ratio~Estimated;vortex_wall~Vortex finder wall~80~mm~model parameter~Estimated;D_dust~Dust outlet diameter~400~mm~FLS ratio~Estimated;W_inlet~Inlet width b~860~mm~FLS ratio~Estimated;H_inlet~Inlet height a (normal to the duct)~2160~mm~CFD decision~Estimated;" ' parameter table rows
Const C1_TAB_2                     As String  = "inlet_slope~Inlet duct slope~5~deg~CFD decision~Estimated;inlet_duct_length~Inlet duct length (axis, from tangent plane)~3000~mm~model parameter~Estimated;inlet_roof_clearance~Opening top below the roof~50~mm~model parameter~Estimated;tongue~Tongue (cut-water)~50~mm~model parameter~Estimated;volute~Volute~no~-~CFD decision~Estimated;outlet_turn~Outlet bend angle~180~deg~CFD decision~Estimated;outlet_rise~Outlet pipe rise over the roof~3000~mm~derived~Estimated;outlet_bend_R~Outlet bend centreline radius~3600~mm~derived~Estimated;outlet_run~Outlet drop leg~3000~mm~derived~Estimated;leg_x~Barrel axis to drop leg axis~7200~mm~derived~Estimated;" ' parameter table rows
Const C1_TAB_3                     As String  = "top~Dust outlet to top of the bend~19240~mm~derived~Estimated;volume~Volume (barrel + cone)~124.54~m3~derived~Estimated;wet_area~Wetted area (barrel, roof ring, cone)~139.70~m2~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;u_split~C1 Y split (riser to 2 cyclones)~-~~no source~Unknown;" ' parameter table rows
Const C1_TAB_4                     As String  = ""           ' parameter table rows
Const C1_TAB_5                     As String  = ""           ' parameter table rows
Const C1_TAB_6                     As String  = ""           ' parameter table rows
Const C1_TAB_7                     As String  = ""           ' parameter table rows
Const C1_TAB_8                     As String  = ""           ' parameter table rows
' END GENERATED

' Sheet [m on paper]: A1 landscape, ISO 5457 frame
Const PAPER_W  As Double = 0.841
Const PAPER_H  As Double = 0.594
Const SCALE_D  As Double = 50#          ' 1:50, the sheet's scale
Const DETAIL_D As Double = 20#          ' 1:20, detail B
Const FR_X0 As Double = 0.02, FR_X1 As Double = 0.831, FR_Y0 As Double = 0.01, FR_Y1 As Double = 0.584
Const COL_X0 As Double = 0.651          ' the right-hand column: notes, legend, table, title block
Const TEXT_H As Double = 0.0025
Const CAP_H  As Double = 0.0018

' Where the views go on the sheet [m]: the top view's centre; A-A is
' placed by its alignment over it, the left view right of A-A.
Const TOP_X  As Double = 0.2
Const TOP_Y  As Double = 0.105
Const SEC_Y  As Double = 0.38
Const LEFT_X As Double = 0.44
Const DET_X  As Double = 0.57
Const DET_Y  As Double = 0.45

Const EQUIP    As String = "C1"
Const LINE_KEY As String = "2500"
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"
Const DRAW_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\drawings\"

Const L_FRAME As String = "CERCEVE"
Const L_TEXT  As String = "YAZI"
Const L_DIM   As String = "OLCU"
Const L_FLOW  As String = "AKIS"
Const L_AXIS  As String = "EKSEN"

Const SEL_TOL As Double = 0.0005        ' a picked edge vs the one asked for [m, model]
Const DIM_TOL As Double = 0.0001        ' a dimension read back vs the source [m]
Const PI As Double = 3.14159265358979


'------------------------------------------------------------------
' Module state
'------------------------------------------------------------------
Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swDraw  As SldWorks.DrawingDoc
Dim swSkMgr As SldWorks.SketchManager
Dim swMath  As SldWorks.MathUtility

Dim partPath As String
Dim swPart As SldWorks.ModelDoc2
Dim partStamp As Date, partLen As Long
Dim vTop As SldWorks.View, vSec As SldWorks.View, vLeft As SldWorks.View, vDet As SldWorks.View

' the parameter table, parsed: key, label, value, unit, source, status
Dim tKey() As String, tLabel() As String, tVal() As String, tUnit() As String
Dim tSrc() As String, tStat() As String
Dim nRows As Long

Dim nDims As Long, nDimsOk As Long
Dim skPerM As Double             ' sheet sketch units per metre of paper (SheetFurniture)
Dim foundDist As Double          ' FindEdge: the found edge's distance to the point [m]
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
    Set swMath = swApp.GetMathUtility

    phase = "reading the parameter table"
    ParseTable
    phase = "opening the part"
    OpenPart
    phase = "making the sheet"
    NewSheet
    phase = "making the views"
    MakeViews
    phase = "dimensioning"
    DimensionAll
    phase = "drawing the frame, title block and table"
    SheetFurniture
    phase = "saving"
    SaveOutputs

    buildLog = "drawings " & EQUIP & " built: " & nDimsOk & " of " & nDims & " dimensions verified" & vbLf & buildLog
    WriteLog
    MsgBox "Drawing " & EQUIP & " built: " & nDimsOk & " of " & nDims & " dimensions verified." & vbLf & _
           "Full log: " & LogPath(), vbInformation, "Equipment drawings"
    Exit Sub

Failed:
    why = Err.Description
    buildLog = "drawings " & EQUIP & " ABORTED while " & phase & ": " & why & vbLf & buildLog
    WriteLog
    MsgBox "Drawing " & EQUIP & " ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
           vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Equipment drawings"
End Sub


'==================================================================
' The parameter table (generated): rows ';', fields '~'
'==================================================================
Private Sub ParseTable()
    Dim all As String, rows As Variant, f As Variant
    Dim i As Long
    all = C1_TAB_1 & C1_TAB_2 & C1_TAB_3 & C1_TAB_4 & C1_TAB_5 & C1_TAB_6 & C1_TAB_7 & C1_TAB_8
    rows = Split(all, ";")
    nRows = 0
    For i = 0 To UBound(rows)
        If Len(rows(i)) > 0 Then nRows = nRows + 1
    Next i
    If nRows = 0 Then Fail "the generated parameter table is empty (run tools/gen_geometry.py)."
    ReDim tKey(1 To nRows): ReDim tLabel(1 To nRows): ReDim tVal(1 To nRows)
    ReDim tUnit(1 To nRows): ReDim tSrc(1 To nRows): ReDim tStat(1 To nRows)
    nRows = 0
    For i = 0 To UBound(rows)
        If Len(rows(i)) > 0 Then
            f = Split(rows(i), "~")
            If UBound(f) <> 5 Then Fail "table row " & (nRows + 1) & " has " & (UBound(f) + 1) & " fields, not 6."
            nRows = nRows + 1
            tKey(nRows) = f(0): tLabel(nRows) = f(1): tVal(nRows) = f(2)
            tUnit(nRows) = f(3): tSrc(nRows) = f(4): tStat(nRows) = f(5)
        End If
    Next i
    Note "table: " & nRows & " rows"
End Sub


Private Function StatusOf(ByVal key As String) As String
    Dim i As Long
    For i = 1 To nRows
        If tKey(i) = key Then StatusOf = tStat(i): Exit Function
    Next i
    Fail "no table row for " & key & "."
End Function


'==================================================================
' The part and the sheet
'==================================================================
Private Sub OpenPart()
    Dim errs As Long, warns As Long
    Dim doc As SldWorks.ModelDoc2
    partPath = OUT_ROOT & LINE_KEY & "\" & EQUIP & ".SLDPRT"
    If Dir(partPath) = "" Then Fail partPath & " does not exist: build it with cyclone.bas first."
    ' The solid is a verified CFD input: opened read-only, never saved,
    ' and its file is checked unchanged at the end (PartUntouched).
    partStamp = FileDateTime(partPath): partLen = FileLen(partPath)
    Set doc = swApp.OpenDoc6(partPath, swDocPART, swOpenDocOptions_Silent Or swOpenDocOptions_ReadOnly, "", errs, warns)
    If doc Is Nothing Then Fail "could not open " & partPath & " (error " & errs & ")."
    Note "part: " & partPath & " (read-only, " & partLen & " bytes, " & Format(partStamp, "yyyy-mm-dd hh:nn:ss") & ")"
    Set swPart = doc
    CheckPartBox doc
End Sub


' The part must be today's gas-only C1 domain in the macro's frame:
' z = 0 at the dust outlet, the inlet face furthest out at -x, the drop
' leg's outer wall at +x, the bend's crown on top. An older build (the
' 90 deg elbow and run towards -x) or the riser domain is refused.
Private Sub CheckPartBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As Object, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = b.GetBodyBox
    want(0) = C1_FACE_BOT_X
    want(1) = -0.5 * C1_D_BARREL
    want(2) = 0#
    want(3) = C1_LEG_X + 0.5 * C1_D_VORTEX
    want(4) = 0.5 * C1_D_BARREL
    want(5) = C1_TOP
    For i = 0 To 5
        ' GetBodyBox may be loose by a little; never by centimetres.
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's C1 domain has " & Num(want(i), 3) & _
                 " -- rebuild it with cyclone.bas (CYCLONE_NAME ""C1"", RISER_ON = False in its C1 case)."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


Private Sub NewSheet()
    Dim tpl As String
    Dim sh As SldWorks.Sheet
    Dim ok As Boolean
    Dim props As Variant

    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateDrawing)
    If tpl = "" Then Fail "no default drawing template is set (Tools > Options > Default Templates)."
    Set swModel = swApp.NewDocument(tpl, swDwgPaperA1size, PAPER_W, PAPER_H)
    If swModel Is Nothing Then Fail "could not create a drawing from " & tpl & "."
    Set swDraw = swModel
    Set swSkMgr = swModel.SketchManager
    Note "template: " & tpl

    ' A blank A1 sheet at 1:50, first-angle projection, no sheet format
    ' (this macro draws the ISO 5457 frame and ISO 7200 title block).
    ' SetupSheet5 as plant_topology_2d.bas calls it, with the scale and
    ' the projection (FirstAngle = True); read back, not trusted.
    Set sh = swDraw.GetCurrentSheet
    ok = swDraw.SetupSheet5(sh.GetName, swDwgPaperA1size, swDwgTemplateNone, 1#, SCALE_D, _
                            True, "", PAPER_W, PAPER_H, "Default", True)
    If Not ok Then Note "WARNING: SetupSheet5 returned False."
    If Not ok Then sh.SetProperties2 swDwgPaperA1size, swDwgTemplateNone, 1#, SCALE_D, True, PAPER_W, PAPER_H, True
    props = sh.GetProperties2
    Note "sheet properties: " & Num(props(0), 0) & " " & Num(props(1), 0) & " " & Num(props(2), 3) & " " & _
         Num(props(3), 3) & " " & Num(props(4), 0) & " " & Num(props(5), 4) & " " & Num(props(6), 4)
    If props(4) = 0 Then Fail "the sheet is not first-angle projection."

    ' ISO drafting standard, mm, whole millimetres.
    With swModel.Extension
        .SetUserPreferenceInteger swDetailingDimensionStandard, swDetailingNoOptionSpecified, swDetailingStandardISO
        .SetUserPreferenceInteger swUnitSystem, swDetailingNoOptionSpecified, swUnitSystem_MMGS
        .SetUserPreferenceInteger swUnitsLinearDecimalPlaces, swDetailingNoOptionSpecified, 0
        .SetUserPreferenceInteger swUnitsAngularDecimalPlaces, swDetailingNoOptionSpecified, 0
    End With
    If swModel.Extension.GetUserPreferenceInteger(swDetailingDimensionStandard, swDetailingNoOptionSpecified) _
       <> swDetailingStandardISO Then Fail "could not set the ISO drafting standard."
    MakeLayers
    Note "sheet: A1, 1:" & Fmt(SCALE_D) & ", first angle, ISO"
End Sub


Private Sub MakeLayers()
    Dim lm As Object
    Set lm = swModel.GetLayerManager
    If lm Is Nothing Then Fail "the drawing has no layer manager."
    AddOneLayer lm, L_FRAME, "frame, title block (ISO 128 01.2, 0.7)", swLineCONTINUOUS, swLW_THICK2
    AddOneLayer lm, L_TEXT, "notes, tables (01.1, 0.25)", swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_DIM, "dimensions (01.1, 0.25)", swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_FLOW, "flow arrows (01.1, 0.35)", swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_AXIS, "axes (04.1, 0.25)", swLineCENTER, swLW_THIN
End Sub


Private Sub AddOneLayer(lm As Object, ByVal name As String, ByVal desc As String, _
                        ByVal style As Long, ByVal weight As Long)
    Dim ret As Variant
    ret = lm.AddLayer(name, desc, RGB(0, 0, 0), style, weight)
    If lm.GetLayer(name) Is Nothing Then Fail "layer " & name & " was not created (AddLayer returned " & CStr(ret) & ")."
End Sub


Private Sub UseLayer(ByVal name As String)
    Dim lm As Object
    Set lm = swModel.GetLayerManager
    lm.SetCurrentLayer name
    If UCase(lm.GetCurrentLayer) <> UCase(name) Then Fail "could not make layer " & name & " current."
End Sub


'==================================================================
' Views
'==================================================================
Private Sub MakeViews()

    Dim R As Double, rx As Double, xa As Double, xb As Double
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim ok As Boolean

    R = 0.5 * C1_D_BARREL: rx = 0.5 * C1_D_VORTEX

    ' Top view: whichever named view, at whichever quarter turn, puts
    ' model +x to the sheet's right and +y up.
    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, TOP_X, TOP_Y, "top")
    HiddenLinesVisible vTop

    ' Section A-A: a cutting line along y = 0 in the top view, drawn
    ' from right to left -- SolidWorks then looks +y (measured on the
    ' first run: left to right looks -y); A-A must show x right, z up.
    xa = -R - C1_W_INLET - 1.5: xb = C1_LEG_X + rx + 1#
    ToSheet vTop, xa, 0#, C1_HEIGHT, ax, ay
    ToSheet vTop, xb, 0#, C1_HEIGHT, qx, qy
    Set vSec = SectionFrom(vTop, qx, qy, ax, ay, "A")
    If Not Maps(vSec, 1, 0, 0, 0, 0, 1) Then Fail "section A-A does not show x right, z up: " & MapText(vSec)
    ' Cut, not just projected (run 5): the vortex finder's bore, inside
    ' the barrel below the roof, shows only in a cut.
    Dim nSeen As Long, nFit As Long
    If FindEdge(vSec, "vline", -rx, 0#, C1_HEIGHT - 0.5 * C1_L_VORTEX, -rx, 0#, nSeen, nFit) Is Nothing _
       Or foundDist > SEL_TOL Then Fail "section A-A is not cut: no vortex finder bore among its " & nSeen & " edges."
    Note "views: top " & vTop.Name & ", A-A " & vSec.Name
    LogMap vTop, "top", SCALE_D: LogMap vSec, "A-A", SCALE_D

    ' Left view, right of A-A (first angle: seen from the left), from the
    ' part's named views like the top view -- selecting A-A by name to
    ' unfold it failed in run 3. Its height is lined up with A-A's.
    swDraw.EditSheet
    Set vLeft = OrientedView(0, -1, 0, 0, 0, 1, LEFT_X, SEC_Y, "left")
    AlignHeight vLeft, vSec
    HiddenLinesVisible vLeft

    ' Detail B: the vortex finder's mouth, from A-A.
    Set vDet = DetailFrom(vSec, R - 0.35, C1_HEIGHT - C1_L_VORTEX + 0.3, 1.25, "B")
    Note "views: left " & vLeft.Name & ", detail B " & vDet.Name
    LogMap vLeft, "left", SCALE_D: LogMap vDet, "detail B", DETAIL_D

End Sub


' A model view whose sheet-right is model (rx, ry, rz) and sheet-up
' model (ux, uy, uz): tries the part's named views (their names are
' localised -- "*Top" is "*Dik Olarak" here -- so they are read from the part,
' not typed) at the four quarter turns; the first that maps right is
' kept. Every try is logged.
Private Function OrientedView(ByVal rx As Double, ByVal ry As Double, ByVal rz As Double, _
                              ByVal ux As Double, ByVal uy As Double, ByVal uz As Double, _
                              ByVal px As Double, ByVal py As Double, ByVal what As String) As SldWorks.View
    Dim names As Variant, i As Long, k As Long
    Dim v As SldWorks.View
    names = swPart.GetModelViewNames
    If IsEmpty(names) Then Fail "the part lists no named views."
    For i = 0 To UBound(names)
        Set v = swDraw.CreateDrawViewFromModelView3(partPath, names(i), px, py, 0#)
        If v Is Nothing Then
            Note what & " view: " & names(i) & " could not be placed"
        Else
            v.ScaleDecimal = 1# / SCALE_D
            For k = 0 To 3
                v.Angle = k * PI / 2#
                swModel.ForceRebuild3 False
                If Maps(v, rx, ry, rz, ux, uy, uz) Then
                    PlaceAt v, px, py
                    Note what & " view: " & names(i) & " turned " & (90 * k) & " deg"
                    Set OrientedView = v
                    Exit Function
                End If
                If k = 0 Then Note what & " view: tried " & names(i) & ": " & MapText(v)
            Next k
            DeleteView v
        End If
    Next i
    Fail "no named view shows the " & what & " view (tries in the log)."
End Function


' Moves a view's centre to (px, py) on the sheet. Position takes an
' array of Doubles; a Variant Array() is silently ignored (run 3: the
' views stayed where SolidWorks dropped them, off the sheet).
Private Sub PlaceAt(v As SldWorks.View, ByVal px As Double, ByVal py As Double)
    Dim p(1) As Double, got As Variant
    p(0) = px: p(1) = py
    v.Position = p
    swModel.ForceRebuild3 False
    got = v.Position
    If Abs(got(0) - px) > 0.001 Or Abs(got(1) - py) > 0.001 Then _
        Fail v.Name & " did not move to (" & Num(1000 * px, 1) & ", " & Num(1000 * py, 1) & ") mm: it is at (" & _
             Num(1000 * got(0), 1) & ", " & Num(1000 * got(1), 1) & ") mm."
End Sub


' Where the model axes go on the sheet, for the log: "x->(+1,0) ...".
Private Function MapText(v As SldWorks.View) As String
    Dim ox As Double, oy As Double, a As Double, b As Double, i As Long
    Dim e(2) As Double, s As String
    ToSheet v, 0, 0, 0, ox, oy
    For i = 0 To 2
        e(0) = 0: e(1) = 0: e(2) = 0: e(i) = 1
        ToSheet v, e(0), e(1), e(2), a, b
        s = s & Mid("xyz", i + 1, 1) & "->(" & Num((a - ox) * SCALE_D, 2) & "," & Num((b - oy) * SCALE_D, 2) & ") "
    Next i
    MapText = s
End Function


Private Function SectionFrom(parent As SldWorks.View, ByVal ax As Double, ByVal ay As Double, _
                             ByVal qx As Double, ByVal qy As Double, ByVal label As String) As SldWorks.View
    Dim seg As Object
    Dim v As SldWorks.View
    Dim kax As Double, kay As Double, kqx As Double, kqy As Double
    ToViewSketch parent, ax, ay, kax, kay
    ToViewSketch parent, qx, qy, kqx, kqy
    swDraw.ActivateView parent.Name
    swSkMgr.AddToDB = True
    Set seg = swSkMgr.CreateLine(kax, kay, 0#, kqx, kqy, 0#)
    swSkMgr.AddToDB = False
    If seg Is Nothing Then Fail "could not sketch the cutting line " & label & "-" & label & "."
    swModel.ClearSelection2 True
    seg.Select4 False, Nothing
    Set v = swDraw.CreateSectionViewAt5(0.5 * (ax + qx), SEC_Y, 0#, label, 0, Nothing, 0#)
    If v Is Nothing Then Fail "could not make section " & label & "-" & label & "."
    Set SectionFrom = v
End Function


Private Function DetailFrom(parent As SldWorks.View, ByVal x As Double, ByVal z As Double, _
                            ByVal r As Double, ByVal label As String) As SldWorks.View
    Dim cx As Double, cy As Double, ex As Double, ey As Double
    Dim seg As Object
    Dim v As SldWorks.View
    Dim kx As Double, ky As Double
    ToSheet parent, x, 0#, z, cx, cy
    ToSheet parent, x + r, 0#, z, ex, ey
    ToViewSketch parent, cx, cy, kx, ky
    swDraw.ActivateView parent.Name
    swSkMgr.AddToDB = True
    Set seg = swSkMgr.CreateCircleByRadius(kx, ky, 0#, Abs(ex - cx) / parent.ScaleDecimal)
    swSkMgr.AddToDB = False
    If seg Is Nothing Then Fail "could not sketch the detail circle " & label & "."
    Note "detail " & label & " circle: centre (" & Num(1000 * cx, 1) & ", " & Num(1000 * cy, 1) & _
         ") mm, radius " & Num(1000 * Abs(ex - cx), 1) & " mm on the sheet, in " & parent.Name
    swModel.ClearSelection2 True
    seg.Select4 False, Nothing
    Set v = swDraw.CreateDetailViewAt4(DET_X, DET_Y, 0#, swDetViewSTANDARD, 1#, DETAIL_D, label, _
                                       swDetCircleCIRCLE, True, False, False, 5)
    If v Is Nothing Then Fail "could not make detail " & label & "."
    Set DetailFrom = v
End Function


' A rejected try is deleted; selecting a view by its name failed in
' run 3, so its centre on the sheet is tried as well.
Private Sub DeleteView(v As SldWorks.View)
    Dim nm As String, p As Variant, ok As Boolean
    nm = v.Name
    swDraw.EditSheet
    swModel.ClearSelection2 True
    ok = swModel.Extension.SelectByID2(nm, "DRAWINGVIEW", 0, 0, 0, False, 0, Nothing, 0)
    If Not ok Then
        p = v.Position
        ok = swModel.Extension.SelectByID2("", "DRAWINGVIEW", p(0), p(1), 0, False, 0, Nothing, 0)
    End If
    If ok Then
        swModel.EditDelete
    Else
        Note "WARNING: could not select the rejected view " & nm & " to delete it."
    End If
End Sub


' Moves v up or down so model z = 0 sits at the same sheet height as
' in ref (projection alignment).
Private Sub AlignHeight(v As SldWorks.View, ref As SldWorks.View)
    Dim ax As Double, ay As Double, bx As Double, by As Double, p As Variant
    ToSheet ref, 0, 0, 0, ax, ay
    ToSheet v, 0, 0, 0, bx, by
    p = v.Position
    PlaceAt v, p(0), p(1) + (ay - by)
End Sub


Private Sub HiddenLinesVisible(v As SldWorks.View)
    On Error Resume Next
    v.SetDisplayMode3 False, swHIDDEN_GREYED, False, True
    If Err.Number <> 0 Then Note "WARNING: " & v.Name & ": could not show hidden lines (" & Err.Description & ")."
    Err.Clear
End Sub


' Model point -> sheet point through the view's own transform.
Private Sub ToSheet(v As SldWorks.View, ByVal x As Double, ByVal y As Double, ByVal z As Double, _
                    ByRef sx As Double, ByRef sy As Double)
    Dim pt As SldWorks.MathPoint
    Dim d(2) As Double
    Dim a As Variant
    d(0) = x: d(1) = y: d(2) = z
    Set pt = swMath.CreatePoint(d)
    Set pt = pt.MultiplyTransform(v.ModelToViewTransform)
    a = pt.ArrayData
    sx = a(0): sy = a(1)
End Sub


' Sheet point -> the active view's sketch: a view's sketch is measured
' from the view's centre at full size (run 5: a cutting line given in
' sheet metres landed 1/50 as long next to the top view's centre, so
' A-A was not cut and the detail circle was a dot).
Private Sub ToViewSketch(v As SldWorks.View, ByVal sx As Double, ByVal sy As Double, _
                         ByRef kx As Double, ByRef ky As Double)
    Dim p As Variant
    p = v.Position
    kx = (sx - p(0)) / v.ScaleDecimal
    ky = (sy - p(1)) / v.ScaleDecimal
End Sub


' Does model direction r go to the sheet's right and u up?
Private Function Maps(v As SldWorks.View, ByVal rx As Double, ByVal ry As Double, ByVal rz As Double, _
                      ByVal ux As Double, ByVal uy As Double, ByVal uz As Double) As Boolean
    Dim ox As Double, oy As Double, ax As Double, ay As Double, qx As Double, qy As Double
    ToSheet v, 0, 0, 0, ox, oy
    ToSheet v, rx, ry, rz, ax, ay
    ToSheet v, ux, uy, uz, qx, qy
    ax = ax - ox: ay = ay - oy: qx = qx - ox: qy = qy - oy
    Maps = (ax > 0.9 * Sqr(ax * ax + ay * ay)) And (qy > 0.9 * Sqr(qx * qx + qy * qy)) _
           And (Sqr(ax * ax + ay * ay) > 0#) And (Sqr(qx * qx + qy * qy) > 0#)
End Function


' Where a view landed and at what scale, logged; the scale is checked.
Private Sub LogMap(v As SldWorks.View, ByVal what As String, ByVal denom As Double)
    Dim ox As Double, oy As Double, a As Double, b As Double, mm As Double
    Dim ol As Variant, i As Long, e(2) As Double
    ' 1 m along whichever model axis lies in the view plane (model x is
    ' the line of sight in the left view: run 4 read 0 mm there).
    ToSheet v, 0, 0, 0, ox, oy
    For i = 0 To 2
        e(0) = 0: e(1) = 0: e(2) = 0: e(i) = 1
        ToSheet v, e(0), e(1), e(2), a, b
        If 1000# * Sqr((a - ox) ^ 2 + (b - oy) ^ 2) > mm Then mm = 1000# * Sqr((a - ox) ^ 2 + (b - oy) ^ 2)
    Next i
    ol = v.GetOutline
    Note what & ": " & v.Name & ", model origin at sheet (" & Num(1000 * ox, 1) & ", " & Num(1000 * oy, 1) & _
         ") mm, 1 m -> " & Num(mm, 3) & " mm, outline (" & Num(1000 * ol(0), 1) & ", " & Num(1000 * ol(1), 1) & _
         ") .. (" & Num(1000 * ol(2), 1) & ", " & Num(1000 * ol(3), 1) & ") mm"
    If Abs(mm - 1000# / denom) > 0.01 Then Fail what & " is drawn at 1:" & Num(1000# / mm, 2) & ", not 1:" & Fmt(denom) & "."
End Sub


'==================================================================
' Dimensions
'==================================================================
Private Sub DimensionAll()

    Dim R As Double, rx As Double, rd As Double, t As Double
    Dim zr As Double, hc As Double, zv As Double
    Dim yi As Double, yo As Double, ym As Double
    Dim dx As Double, dz As Double, th As Double, s As Double
    Dim mx As Double, mz As Double

    R = 0.5 * C1_D_BARREL: rx = 0.5 * C1_D_VORTEX: rd = 0.5 * C1_D_DUST
    t = C1_VORTEX_WALL
    zr = C1_HEIGHT: hc = C1_H_CONE: zv = zr - C1_L_VORTEX
    yi = C1_Y_INNER: yo = C1_Y_OUTER: ym = 0.5 * (yi + yo)
    th = C1_INLET_SLOPE_DEG * PI / 180#
    dx = Cos(th): dz = -Sin(th)
    swDraw.EditSheet

    ' What selection depends on, logged: the drawing must be the active
    ' document, no selection filter may be on, the sheet must be drawn.
    Dim ad As SldWorks.ModelDoc2
    Set ad = swApp.ActiveDoc
    If ad Is Nothing Then
        Note "selection: no active document"
    Else
        Note "selection: active document " & ad.GetTitle & IIf(ad Is swModel, " (the drawing)", " (NOT the drawing)")
    End If
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True
    Note "selection: view " & vSec.Name & " by name: " & _
         swModel.Extension.SelectByID2(vSec.Name, "DRAWINGVIEW", 0, 0, 0, False, 0, Nothing, 0)
    swModel.ClearSelection2 True

    ' Left view (looking +x): the circular edges seen edge-on. A circle
    ' is picked on its y < 0 half, clear of the inlet duct in front of
    ' the y > 0 half.
    DimEdges "D_barrel", C1_D_BARREL, vLeft, _
        "circle", 0, -0.85 * R, zr, R, zr, _
        "", 0, 0, 0, 0, 0, _
        0, -0.85 * R, zr + 1.2
    DimEdges "D_dust", C1_D_DUST, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "", 0, 0, 0, 0, 0, _
        0, -rd - 0.6, -0.9
    DimEdges "H_cone", C1_H_CONE, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "circle", 0, -0.7 * R, hc, R, hc, _
        0, -R - 1#, 0.5 * hc
    DimEdges "H_barrel", C1_H_BARREL, vLeft, _
        "circle", 0, -0.7 * R, hc, R, hc, _
        "circle", 0, -0.85 * R, zr, R, zr, _
        0, -R - 1#, 0.5 * (hc + zr)
    DimEdges "height", C1_HEIGHT, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "circle", 0, -0.85 * R, zr, R, zr, _
        0, -R - 2.2, 0.5 * zr
    DimEdges "outlet_rise", C1_OUT_RISE, vLeft, _
        "circle", 0, -0.85 * R, zr, R, zr, _
        "circle", 0, -0.5 * rx, zr + C1_OUT_RISE, rx, zr + C1_OUT_RISE, _
        0, -R - 1#, zr + 0.5 * C1_OUT_RISE

    ' Section A-A (the plane y = 0): the cut face's straight edges.
    DimEdges "D_vortex", C1_D_VORTEX, vSec, _
        "vline", -rx, 0, zr + 1.5, -rx, 0, _
        "vline", rx, 0, zr + 1.5, rx, 0, _
        0, 0, zr + 2.2
    DimEdges "L_vortex", C1_L_VORTEX, vSec, _
        "hline", 0.5 * (rx + t + R), 0, zr, 0, zr, _
        "hline", rx + 0.5 * t, 0, zv, 0, zv, _
        R + 1.8, 0, zr - 0.5 * C1_L_VORTEX
    DimEdges "leg_x", C1_LEG_X, vSec, _
        "vline", -rx, 0, zr + 1#, -rx, 0, _
        "vline", C1_LEG_X - rx, 0, zr + 1#, C1_LEG_X - rx, 0, _
        0.5 * C1_LEG_X, 0, zr - 2.5

    ' The inlet duct behind the cut (y = yi, its near side wall): the
    ' face's side edge is the inlet height true size; its lower edge
    ' against the roof line gives the slope.
    DimEdges "H_inlet", C1_H_INLET, vSec, _
        "line", 0.5 * (C1_FACE_TOP_X + C1_FACE_BOT_X), yi, 0.5 * (C1_FACE_TOP_Z + C1_FACE_BOT_Z), 0, 0, _
        "", 0, 0, 0, 0, 0, _
        0.5 * (C1_FACE_TOP_X + C1_FACE_BOT_X) - 1#, 0, 0.5 * (C1_FACE_TOP_Z + C1_FACE_BOT_Z)
    s = 0.5 * (-R - C1_FACE_BOT_X) / dx
    mx = C1_FACE_BOT_X + s * dx: mz = C1_FACE_BOT_Z + s * dz
    DimEdges "inlet_slope", C1_INLET_SLOPE_DEG, vSec, _
        "line", mx, yi, mz, 0, 0, _
        "hline", -0.5 * (rx + t + R), 0, zr, 0, zr, _
        mx - 0.6, 0, mz + 2#

    ' Top view: the inlet face's upper edge, true width.
    DimEdges "W_inlet", C1_W_INLET, vTop, _
        "line", C1_FACE_TOP_X, ym, C1_FACE_TOP_Z, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        C1_FACE_TOP_X - 0.8, ym, C1_FACE_TOP_Z

    ' Detail B: the vortex finder's wall at its mouth.
    DimEdges "vortex_wall", C1_VORTEX_WALL, vDet, _
        "hline", rx + 0.5 * t, 0, zv, 0, zv, _
        "", 0, 0, 0, 0, 0, _
        rx + 0.5 * t, 0, zv - 0.25

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"

End Sub


' One dimension of `key` in view v: pick one or two edges at model
' points (each with what it must be), put the dimension's text at the
' model point (tx, ty, tz), read it back, check it, log it.
'   kind "circle": a circle of radius p1 whose centre is at z = p2
'   kind "hline":  a line along x at z = p2
'   kind "vline":  a line along z at x = p1
'   kind "line":   any line through the pick point
'   kind "":       no second edge
Private Sub DimEdges(ByVal key As String, ByVal want As Double, v As SldWorks.View, _
        ByVal k1 As String, ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double, ByVal p11 As Double, ByVal p12 As Double, _
        ByVal k2 As String, ByVal x2 As Double, ByVal y2 As Double, ByVal z2 As Double, ByVal p21 As Double, ByVal p22 As Double, _
        ByVal tx As Double, ByVal ty As Double, ByVal tz As Double)

    Dim st As String
    Dim dd As SldWorks.DisplayDimension
    Dim got As Double, isAngle As Boolean
    Dim sx As Double, sy As Double

    nDims = nDims + 1
    st = StatusOf(key)
    If st <> "Verified" And st <> "Estimated" Then Fail key & " is " & st & ": it may not be dimensioned."
    isAngle = (key = "inlet_slope")

    swModel.ClearSelection2 True
    If Not PickEdge(v, k1, x1, y1, z1, p11, p12, False, key & " edge 1") Then Exit Sub
    If k2 <> "" Then
        If Not PickEdge(v, k2, x2, y2, z2, p21, p22, True, key & " edge 2") Then Exit Sub
    End If

    ToSheet v, tx, ty, tz, sx, sy
    Set dd = swModel.AddDimension2(sx, sy, 0#)
    swModel.ClearSelection2 True
    If dd Is Nothing Then
        Note "MISSING dim " & key & ": AddDimension2 made nothing"
        Exit Sub
    End If
    If st = "Estimated" Then dd.SetText swDimensionTextSuffix, " E"
    ' The overall height is H_barrel + H_cone, also dimensioned: an
    ' auxiliary dimension, in parentheses (ISO 129-1).
    If key = "height" Then
        dd.SetText swDimensionTextPrefix, "("
        dd.SetText swDimensionTextSuffix, IIf(st = "Estimated", " E)", ")")
    End If
    dd.GetAnnotation.Layer = L_DIM

    got = dd.GetDimension2(0).SystemValue
    If isAngle Then
        got = got * 180# / PI
        If got > 90# Then got = 180# - got
        If Abs(got - want) > 0.01 Then
            Note "MISMATCH dim " & key & " " & Num(got, 3) & " deg, source " & Num(want, 3)
            Exit Sub
        End If
        Note "dim " & key & " " & Num(got, 3)
    Else
        If Abs(got - want) > DIM_TOL Then
            Note "MISMATCH dim " & key & " " & Num(1000 * got, 3) & " mm, source " & Num(1000 * want, 3)
            Exit Sub
        End If
        Note "dim " & key & " " & Num(1000 * got, 3)
    End If
    nDimsOk = nDimsOk + 1
End Sub


' Select the edge under model point (x, y, z) in view v and check it
' is the one meant (see DimEdges for the kinds).
Private Function PickEdge(v As SldWorks.View, ByVal kind As String, ByVal x As Double, ByVal y As Double, _
                          ByVal z As Double, ByVal p1 As Double, ByVal p2 As Double, ByVal append As Boolean, _
                          ByVal what As String) As Boolean
    Dim ed As SldWorks.Edge, ent As SldWorks.Entity
    Dim sd As SldWorks.SelectData
    Dim nSeen As Long, nFit As Long

    ' Picking at a sheet point (SelectByID2 "EDGE") found nothing in any
    ' view in run 5; the view's own edges are searched instead, and the
    ' one asked for is selected in that view.
    Set ed = FindEdge(v, kind, x, y, z, p1, p2, nSeen, nFit)
    If ed Is Nothing Then
        Note "MISSING dim " & what & ": none of the " & nSeen & " edges of " & v.Name & " is the " & kind & _
             " asked for (" & nFit & " of that kind)"
        Exit Function
    End If
    ' Runs 6 and 7: View.SelectEntity and Entity.Select4 (view in the
    ' SelectData) both refused every edge. Each way is tried in turn and
    ' the log says which one took.
    Dim how As String, q As Variant, sx As Double, sy As Double
    Set ent = ed
    Set sd = swModel.SelectionManager.CreateSelectData
    sd.View = v
    If v.SelectEntity(ent, append) Then
        how = "SelectEntity"
    ElseIf ent.Select4(append, sd) Then
        how = "Select4"
    Else
        swDraw.ActivateView v.Name
        If ent.Select4(append, sd) Then
            how = "Select4 in the active view"
        Else
            swDraw.EditSheet
            q = ed.GetClosestPointOn(x, y, z)
            ToSheet v, q(0), q(1), q(2), sx, sy
            If swModel.Extension.SelectByID2("", "EDGE", sx, sy, 0#, append, 0, Nothing, 0) Then
                how = "SelectByID2 at (" & Num(1000 * sx, 1) & ", " & Num(1000 * sy, 1) & ") mm"
            Else
                Note "MISSING dim " & what & ": the edge was found but no way selected it in " & v.Name & _
                     " (SelectEntity, Select4, Select4 active, SelectByID2 at (" & Num(1000 * sx, 1) & ", " & _
                     Num(1000 * sy, 1) & ") mm)"
                Exit Function
            End If
        End If
    End If
    If how <> "SelectEntity" Then Note "(" & what & " selected by " & how & ")"
    If swModel.SelectionManager.GetSelectedObjectCount2(-1) <> IIf(append, 2, 1) Then
        Note "MISSING dim " & what & ": " & swModel.SelectionManager.GetSelectedObjectCount2(-1) & _
             " objects selected after picking it in " & v.Name
        Exit Function
    End If
    PickEdge = True
End Function


' The visible edge of view v that is the `kind` asked for (see
' DimEdges) nearest to the model point (x, y, z); Nothing if none is.
' nSeen: edges in the view; nFit: those of the right kind.
Private Function FindEdge(v As SldWorks.View, ByVal kind As String, ByVal x As Double, ByVal y As Double, _
                          ByVal z As Double, ByVal p1 As Double, ByVal p2 As Double, _
                          ByRef nSeen As Long, ByRef nFit As Long) As SldWorks.Edge
    Dim ents As Variant, i As Long
    Dim ed As SldWorks.Edge, crv As SldWorks.Curve
    Dim cp As Variant, lp As Variant, q As Variant
    Dim fits As Boolean, d As Double, best As Double

    nSeen = 0: nFit = 0: best = 1E+30
    ents = v.GetVisibleEntities2(Nothing, 1)          ' swViewEntityType_Edge
    If IsEmpty(ents) Then Exit Function
    nSeen = UBound(ents) + 1
    For i = 0 To UBound(ents)
        Set ed = ents(i)
        Set crv = ed.GetCurve
        fits = False
        Select Case kind
        Case "circle"
            If crv.IsCircle Then
                cp = crv.CircleParams         ' centre x y z, axis x y z, radius
                fits = Abs(cp(6) - p1) < SEL_TOL And Abs(cp(2) - p2) < SEL_TOL
            End If
        Case "hline", "vline", "line"
            If crv.IsLine Then
                lp = crv.LineParams           ' root x y z, direction x y z
                If kind = "hline" Then fits = Abs(lp(5)) < 0.001 And Abs(lp(2) - p2) < SEL_TOL
                If kind = "vline" Then fits = Abs(Abs(lp(5)) - 1#) < 0.001 And Abs(lp(0) - p1) < SEL_TOL
                If kind = "line" Then fits = DistToLine(x, y, z, lp) < SEL_TOL
            End If
        End Select
        If fits Then
            nFit = nFit + 1
            q = ed.GetClosestPointOn(x, y, z)
            d = Sqr((q(0) - x) ^ 2 + (q(1) - y) ^ 2 + (q(2) - z) ^ 2)
            If kind = "line" And d > SEL_TOL Then fits = False   ' on the line, off the segment
            If fits And d < best Then best = d: Set FindEdge = ed
        End If
    Next i
    foundDist = best
End Function


Private Function DistToLine(ByVal x As Double, ByVal y As Double, ByVal z As Double, lp As Variant) As Double
    Dim ux As Double, uy As Double, uz As Double, n As Double
    Dim wx As Double, wy As Double, wz As Double, s As Double
    ux = lp(3): uy = lp(4): uz = lp(5)
    n = Sqr(ux * ux + uy * uy + uz * uz)
    ux = ux / n: uy = uy / n: uz = uz / n
    wx = x - lp(0): wy = y - lp(1): wz = z - lp(2)
    s = wx * ux + wy * uy + wz * uz
    DistToLine = Sqr((wx - s * ux) ^ 2 + (wy - s * uy) ^ 2 + (wz - s * uz) ^ 2)
End Function


'==================================================================
' Frame, title block, table, notes, flow arrows (sheet sketch)
'==================================================================
Private Sub SheetFurniture()
    swDraw.EditSheet
    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False
    CalibrateSheetSketch
    DrawFrame
    DrawTitle
    DrawTable
    DrawNotes
    DrawFlows
    DrawAxes
    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ClearSelection2 True
End Sub


' ISO 5457 for A1: 20 mm left, 10 mm elsewhere; 12 x 8 zones.
Private Sub DrawFrame()
    Dim i As Long, x As Double, y As Double, w As Double, h As Double
    UseLayer L_FRAME
    RectP FR_X0, FR_Y0, FR_X1, FR_Y1
    LineP PAPER_W / 2, 0#, PAPER_W / 2, FR_Y0 + 0.005          ' centring marks
    LineP PAPER_W / 2, PAPER_H, PAPER_W / 2, FR_Y1 - 0.005
    LineP 0#, PAPER_H / 2, FR_X0 + 0.005, PAPER_H / 2
    LineP PAPER_W, PAPER_H / 2, FR_X1 - 0.005, PAPER_H / 2
    UseLayer L_TEXT
    w = (FR_X1 - FR_X0) / 12#: h = (FR_Y1 - FR_Y0) / 8#
    For i = 1 To 11
        x = FR_X0 + i * w
        LineP x, FR_Y1, x, FR_Y1 + 0.005
        LineP x, FR_Y0, x, FR_Y0 - 0.005
    Next i
    For i = 1 To 7
        y = FR_Y1 - i * h
        LineP FR_X0 - 0.005, y, FR_X0, y
        LineP FR_X1, y, FR_X1 + 0.005, y
    Next i
    For i = 1 To 12
        x = FR_X0 + (i - 0.5) * w - 0.001
        LabelPH x, FR_Y1 + 0.0075, CStr(i), 0.0035
        LabelPH x, FR_Y0 - 0.0015, CStr(i), 0.0035
    Next i
    For i = 1 To 8
        y = FR_Y1 - (i - 0.5) * h + 0.0017
        LabelPH FR_X0 - 0.013, y, Chr(64 + i), 0.0035
        LabelPH FR_X1 + 0.0025, y, Chr(64 + i), 0.0035
    Next i
End Sub


' ISO 7200 title block, 180 mm wide in the frame's bottom right.
Private Sub DrawTitle()
    UseLayer L_FRAME
    RectP COL_X0, FR_Y0, FR_X1, 0.055
    UseLayer L_TEXT
    LineP COL_X0, 0.046, FR_X1, 0.046
    LineP COL_X0, 0.037, FR_X1, 0.037
    LineP COL_X0, 0.019, FR_X1, 0.019
    LineP 0.771, 0.028, FR_X1, 0.028
    LineP 0.711, 0.037, 0.711, 0.055
    LineP 0.771, FR_Y0, 0.771, 0.055
    LineP 0.711, FR_Y0, 0.711, 0.019
    LineP 0.781, 0.019, 0.781, 0.028
    LineP 0.806, 0.019, 0.806, 0.028
    LineP 0.816, 0.019, 0.816, 0.028
    Cell COL_X0, 0.055, "Created qy", "drawings.bas"
    Cell 0.711, 0.055, "Approved qy", "-"
    Cell 0.771, 0.055, "Document type", "Engineering drawing"
    Cell COL_X0, 0.046, "Legal owner", "Karbon Zekasi"
    Cell 0.711, 0.046, "Technical reference", "plant_geometry.yaml"
    Cell 0.771, 0.046, "Document status", "draft, for approval"
    LabelPH COL_X0 + 0.0015, 0.0362, "Title, supplementary title", CAP_H
    LabelPH COL_X0 + 0.0015, 0.0335, "PREHEATER CYCLONE " & EQUIP, 0.005
    LabelPH COL_X0 + 0.0015, 0.0255, "Inner (fluid) geometry, dimensioned - not a fabrication drawing", TEXT_H
    Cell 0.771, 0.037, "Identification number", "CI-PH-" & EQUIP & "-001"
    CellS 0.771, 0.028, "Rev.", "A"
    CellS 0.781, 0.028, "Date of issue", Format(Date, "yyyy-mm-dd")
    CellS 0.806, 0.028, "Lang.", "EN"
    CellS 0.816, 0.028, "Sheet", "1/1"
    Cell COL_X0, 0.019, "Scale", "1:" & Fmt(SCALE_D) & " (B 1:" & Fmt(DETAIL_D) & ")"
    Cell 0.711, 0.019, "Unit", "mm"
    Cell 0.771, 0.019, "Projection", ""
    ProjectionSymbol 0.79, 0.0125
End Sub


Private Sub Cell(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.0015, yTop - 0.0008, cap, CAP_H
    If v <> "" Then LabelPH x + 0.0015, yTop - 0.004, v, TEXT_H
End Sub


Private Sub CellS(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.001, yTop - 0.0008, cap, CAP_H * 0.85
    If v <> "" Then LabelPH x + 0.001, yTop - 0.004, v, 0.0022
End Sub


' ISO 5456-2 first-angle symbol: the truncated cone's end view right
' of its side view.
Private Sub ProjectionSymbol(ByVal x As Double, ByVal y As Double)
    Dim h As Double
    h = 0.005
    UseLayer L_TEXT
    LineP x - h, y - h / 4, x, y - h / 2
    LineP x, y - h / 2, x, y + h / 2
    LineP x, y + h / 2, x - h, y + h / 4
    LineP x - h, y + h / 4, x - h, y - h / 4
    CircleP x + 0.9 * h, y, h / 2
    CircleP x + 0.9 * h, y, h / 4
End Sub


' The parameter table over the title block: value, unit, source,
' status of every row, Unknown ones with a dash.
Private Sub DrawTable()
    Const RH As Double = 0.0045
    Dim cx As Variant, cap As Variant
    Dim yT As Double, y As Double, i As Long, c As Long
    cx = Array(COL_X0, COL_X0 + 0.008, COL_X0 + 0.084, COL_X0 + 0.1, COL_X0 + 0.112, COL_X0 + 0.15, FR_X1)
    cap = Array("No", "Parameter", "Value", "Unit", "Source", "Status")
    yT = 0.062 + RH * (nRows + 1)
    UseLayer L_FRAME
    RectP COL_X0, 0.062, FR_X1, yT
    UseLayer L_TEXT
    LabelPH COL_X0, yT + 0.0065, "PARAMETERS (value - source - status)", 0.0035
    For c = 1 To 5
        LineP cx(c), 0.062, cx(c), yT
    Next c
    For c = 0 To 5
        LabelPH cx(c) + 0.001, yT - 0.001, CStr(cap(c)), 0.002
    Next c
    For i = 1 To nRows
        y = yT - RH * i
        LineP COL_X0, y, FR_X1, y
        LabelPH cx(0) + 0.001, y - 0.001, CStr(i), 0.0018
        LabelPH cx(1) + 0.001, y - 0.001, tLabel(i), 0.0018
        LabelPH cx(2) + 0.001, y - 0.001, tVal(i), 0.0018
        LabelPH cx(3) + 0.001, y - 0.001, tUnit(i), 0.0018
        LabelPH cx(4) + 0.001, y - 0.001, tSrc(i), 0.0018
        LabelPH cx(5) + 0.001, y - 0.001, tStat(i), 0.0018
    Next i
End Sub


Private Sub DrawNotes()
    Dim y As Double
    y = 0.062 + 0.0045 * (nRows + 1) + 0.05
    UseLayer L_TEXT
    LabelPH COL_X0, y + 0.038, "NOTES", 0.0035
    LabelPH COL_X0, y + 0.032, "1. Inner (fluid) volume of the CFD model; not a fabrication drawing.", TEXT_H
    LabelPH COL_X0, y + 0.027, "   Shell, refractory, material, flanges, supports: Unknown (no source).", TEXT_H
    LabelPH COL_X0, y + 0.022, "2. 1234 = Verified (published).  1234 E = Estimated: FLS ratio,", TEXT_H
    LabelPH COL_X0, y + 0.017, "   literature, CFD decision, model parameter or derived from them.", TEXT_H
    LabelPH COL_X0, y + 0.012, "3. Frame: z = 0 at the dust outlet, gas enters towards +x (cyclone.bas).", TEXT_H
    LabelPH COL_X0, y + 0.007, "4. " & EQUIP & ": 2 per string; values are for one.  All dimensions mm.", TEXT_H
    LabelPH COL_X0, y + 0.002, "5. Source: geometry/plant_geometry.yaml, geometry/preheater/cyclone_C1.md", TEXT_H
End Sub


' Flow arrows on the sheet at model points of A-A: gas in, gas out,
' meal out.
Private Sub DrawFlows()
    Dim R As Double, rx As Double
    Dim cx As Double, cz As Double
    R = 0.5 * C1_D_BARREL: rx = 0.5 * C1_D_VORTEX
    cx = 0.5 * (C1_FACE_TOP_X + C1_FACE_BOT_X): cz = 0.5 * (C1_FACE_TOP_Z + C1_FACE_BOT_Z)
    UseLayer L_FLOW
    ArrowM vSec, cx - 2#, cz + 2# * Tan(C1_INLET_SLOPE_DEG * PI / 180#), cx - 0.2, cz + 0.2 * Tan(C1_INLET_SLOPE_DEG * PI / 180#)
    ArrowM vSec, C1_LEG_X, C1_HEIGHT - 0.2, C1_LEG_X, C1_HEIGHT - 1.6
    ArrowM vSec, 0, -0.2, 0, -1.4
    UseLayer L_TEXT
    LabelM vSec, cx - 2.2, cz + 1.4, "Gas + meal in"
    LabelM vSec, C1_LEG_X + 0.4, C1_HEIGHT - 1#, "Gas out (to fan)"
    LabelM vSec, 0.4, -0.8, "Meal out (to the stage below)"
    LabelM vTop, -R, -R - 0.8, "Swirl clockwise seen from above"
End Sub


' Centre lines (ISO 128 04.1) of the axes of revolution in A-A and the
' left view: the cyclone's, up the outlet pipe to its bend, and the
' drop leg's; each runs 0.6 m past the solid.
Private Sub DrawAxes()
    Dim zr As Double, zb As Double
    zr = C1_HEIGHT: zb = C1_HEIGHT + C1_OUT_RISE
    UseLayer L_AXIS
    AxisM vSec, 0, 0, -0.6, 0, 0, zb
    AxisM vSec, C1_LEG_X, 0, zr - 0.6, C1_LEG_X, 0, zb
    AxisM vLeft, 0, 0, -0.6, 0, 0, zb
End Sub


Private Sub AxisM(v As SldWorks.View, ByVal xa As Double, ByVal ya As Double, ByVal za As Double, _
                  ByVal xb As Double, ByVal yb As Double, ByVal zb As Double)
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    ToSheet v, xa, ya, za, ax, ay
    ToSheet v, xb, yb, zb, qx, qy
    LineP ax, ay, qx, qy
End Sub


Private Sub ArrowM(v As SldWorks.View, ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim ux As Double, uy As Double, n As Double
    Const AL As Double = 0.004, AW As Double = 0.0014
    ToSheet v, xa, 0#, za, ax, ay
    ToSheet v, xb, 0#, zb, qx, qy
    LineP ax, ay, qx, qy
    ux = qx - ax: uy = qy - ay: n = Sqr(ux * ux + uy * uy): ux = ux / n: uy = uy / n
    LineP qx, qy, qx - AL * ux - AW * uy, qy - AL * uy + AW * ux
    LineP qx, qy, qx - AL * ux + AW * uy, qy - AL * uy - AW * ux
End Sub


Private Sub LabelM(v As SldWorks.View, ByVal x As Double, ByVal z As Double, ByVal txt As String)
    Dim sx As Double, sy As Double
    If v Is vTop Then ToSheet v, x, z, 0#, sx, sy Else ToSheet v, x, 0#, z, sx, sy
    LabelPH sx, sy, txt, TEXT_H
End Sub


'------------------------------------------------------------------
' Sheet sketch primitives [m on paper]
'------------------------------------------------------------------
Private Sub LineP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    If swSkMgr.CreateLine(skPerM * a, skPerM * b, 0#, skPerM * c, skPerM * d, 0#) Is Nothing Then Fail "CreateLine failed."
End Sub

Private Sub RectP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    LineP a, b, c, b: LineP c, b, c, d: LineP c, d, a, d: LineP a, d, a, b
End Sub

Private Sub CircleP(ByVal x As Double, ByVal y As Double, ByVal r As Double)
    If swSkMgr.CreateCircleByRadius(skPerM * x, skPerM * y, 0#, skPerM * r) Is Nothing Then Fail "CreateCircleByRadius failed."
End Sub

' The sheet's sketch is not in paper metres: run 9 drew every frame,
' table and arrow line at 1/100 of its size by the sheet origin (the
' status bar's sheet scale is 1:100), as a view's sketch is at the
' view's scale. A probe line's sketch transform gives the factor.
Private Sub CalibrateSheetSketch()
    Dim seg As Object, sk As Object, xf As Object
    Dim p0 As SldWorks.MathPoint, p1 As SldWorks.MathPoint
    Dim d(2) As Double, a As Variant, b As Variant
    Set seg = swSkMgr.CreateLine(0#, 0#, 0#, 0.1, 0#, 0#)
    If seg Is Nothing Then Fail "could not sketch on the sheet."
    Set sk = seg.GetSketch
    Set xf = sk.ModelToSketchTransform
    d(0) = 0: d(1) = 0: d(2) = 0
    Set p0 = swMath.CreatePoint(d): Set p0 = p0.MultiplyTransform(xf)
    d(0) = 1
    Set p1 = swMath.CreatePoint(d): Set p1 = p1.MultiplyTransform(xf)
    a = p0.ArrayData: b = p1.ArrayData
    skPerM = Sqr((b(0) - a(0)) ^ 2 + (b(1) - a(1)) ^ 2)
    Note "sheet sketch: the transform reads " & Num(skPerM, 4) & " sketch units per metre of paper"
    swModel.ClearSelection2 True
    seg.Select4 False, Nothing
    swModel.EditDelete

    ' Checked where it matters, on the paper: a probe line at sketch
    ' (20 .. 30, 20) is picked at its paper midpoint (25, 20) / factor;
    ' 1:100 and 1:50 put it 200 mm apart, inside the sheet.
    Dim k As Variant, hit As Double
    swModel.ViewZoomtofit2
    swSkMgr.DisplayWhenAdded = True              ' only what is drawn can be picked
    Set seg = swSkMgr.CreateLine(20#, 20#, 0#, 30#, 20#, 0#)
    swSkMgr.DisplayWhenAdded = False
    swModel.GraphicsRedraw2
    For Each k In Array(skPerM, 100#, 50#)
        swModel.ClearSelection2 True
        If swModel.Extension.SelectByID2("", "SKETCHSEGMENT", 25# / k, 20# / k, 0#, False, 0, Nothing, 0) Then
            hit = k: Exit For
        End If
    Next k
    swModel.ClearSelection2 True
    seg.Select4 False, Nothing
    swModel.EditDelete
    If hit > 0 Then
        Note "sheet sketch: a probe line is picked on the paper at " & Num(hit, 4) & " sketch units per metre"
        skPerM = hit
    Else
        Note "WARNING: the probe line was not picked on the paper; using the transform's factor"
    End If
    Note "sheet sketch: " & Num(skPerM, 4) & " sketch units per metre of paper"
    If skPerM < 0.001 Then Fail "the sheet sketch transform reads " & Num(skPerM, 6) & "."
End Sub


' A note of text height h, its top left at (px, py).
Private Sub LabelPH(ByVal px As Double, ByVal py As Double, ByVal txt As String, ByVal h As Double)
    Dim nt As Object, an As Object, tf As Object
    swModel.ClearSelection2 True
    Set nt = swModel.InsertNote(txt)
    If nt Is Nothing Then Fail "InsertNote failed for '" & txt & "'."
    Set an = nt.GetAnnotation
    an.SetPosition2 px, py, 0#
    Set tf = an.GetTextFormat(0)
    tf.CharHeight = h
    an.SetTextFormat 0, False, tf
    an.Layer = L_TEXT
    swModel.ClearSelection2 True
End Sub


'==================================================================
' Output and housekeeping
'==================================================================
Private Sub SaveOutputs()
    Dim errs As Long, warns As Long
    Dim drw As String, pdf As String, dxf As String
    If Dir(OUT_ROOT & LINE_KEY & "\drawings", vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY & "\drawings"
    If Dir(DRAW_ROOT, vbDirectory) = "" Then MkDir DRAW_ROOT
    If Dir(DRAW_ROOT & EQUIP, vbDirectory) = "" Then MkDir DRAW_ROOT & EQUIP
    drw = OUT_ROOT & LINE_KEY & "\drawings\" & EQUIP & ".SLDDRW"
    pdf = DRAW_ROOT & EQUIP & "\" & EQUIP & ".pdf"
    dxf = DRAW_ROOT & EQUIP & "\" & EQUIP & ".dxf"
    SaveOne drw, errs, warns
    SaveOne pdf, errs, warns
    SaveOne dxf, errs, warns
    PartUntouched
End Sub


' The CFD solid's file is as it was when opened.
Private Sub PartUntouched()
    If FileDateTime(partPath) <> partStamp Or FileLen(partPath) <> partLen Then _
        Fail partPath & " changed while drawing it: restore it from cyclone.bas."
    Note "part unchanged: " & partPath
End Sub


' SaveAs's return value is not relied on (README): the file must exist.
Private Sub SaveOne(ByVal path As String, errs As Long, warns As Long)
    On Error Resume Next
    If Dir(path) <> "" Then Kill path
    On Error GoTo 0
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If Dir(path) = "" Then Fail "could not write " & path & " (error " & errs & ")."
    Note "wrote " & path
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\drawings_" & EQUIP & "_build.log"
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
    Err.Raise vbObjectError + 1, "drawings", msg
End Sub

Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub

' A number with a decimal point whatever the locale.
Private Function Num(ByVal v As Double, ByVal dec As Long) As String
    If dec > 0 Then
        Num = Replace(Format(v, "0." & String(dec, "0")), ",", ".")
    Else
        Num = Format(v, "0")
    End If
End Function

Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
    If Right(Fmt, 1) = "," Or Right(Fmt, 1) = "." Then Fmt = Left(Fmt, Len(Fmt) - 1)
End Function
