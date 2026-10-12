Attribute VB_Name = "plant_topology_2d"
'==================================================================
' Plant topology, 2D  ->  one SolidWorks drawing (SLDDRW + PDF)
'
' A SCHEMATIC, REAL-SCALE 2D drawing of the 2500 t/d pyroprocess,
' written to show the plant's topology: which equipment there is,
' where it stands, and the gas, meal and air paths between it. It is
' NOT a CFD input -- the one exception to CLAUDE.md rule 8.
'
' The plant drawn is a TWO-STRING preheater, 12 cyclones (each
' string C5, C4, C3, C2 and a twin C1), one ILC calciner whose twin
' gooseneck feeds both C5s, one kiln, a grate cooler and the kiln
' hood with its tertiary air duct. Each string carries half the gas,
' so its cyclones and risers are the catalogue 2500 sizes scaled by
' 1/sqrt 2, as the twin C5 already is. This is the topology only: the
' cyclone CFD documents and cyclone.bas stay single-string.
'
' It is drawn on an A1 sheet at 1:200, on layers that carry the
' colours: equipment outlines black, gas red, meal yellow, air
' blue. Equipment is its true section; the main ducts (risers,
' gooseneck, tertiary air) are drawn at their true diameter as two
' lines; the other paths as one line along their axis. Arrows show
' which way each path flows. A legend and a title block sit on the
' right. Where no source gives a number -- elevations, column
' spacing -- it is a SCHEMATIC parameter, marked as such below and
' listed in geometry/plant_topology.md.
'
' Model coordinates: x across, z up, metres. They go onto the sheet
' as P(x, z) = (X0 + x / SHEET_SCALE, Y0 + z / SHEET_SCALE).
'
' SI ONLY. To run: Tools -> Macro -> New, File -> Import File...,
' pick this .bas, run `main`. See README.md next to this file.
'==================================================================

Option Explicit

'------------------------------------------------------------------
' (a) PARAMETERS
'------------------------------------------------------------------

Const LINE_KEY As String = "2500"

' Cyclones [m]: D, barrel, cone, vortex finder D, dust outlet D --
' geometry/catalog.md, C2 = C3 = C4 (catalog.md deviation). Each is
' drawn at the string scale, 1/sqrt 2: two strings share the gas, as
' the twin C5s do (cyclone_C5.md).
Const C1_D  As Double = 4.32
Const C1_HB As Double = 6.79
Const C1_HC As Double = 4.65
Const C1_VD As Double = 2.4
Const C1_DD As Double = 0.4
Const C4_D  As Double = 6.3
' The CFD barrel, h = D, not the catalogue's 3.46 m (cyclone_C4.md,
' catalog.md deviation, user decision 4 Oct 2026).
Const C4_HB As Double = 6.3
Const C4_HC As Double = 7.3
Const C4_VD As Double = 4.63
Const C4_DD As Double = 0.81
Const C5_D  As Double = 6.5
Const C5_HB As Double = 3.53
Const C5_HC As Double = 7.43
Const C5_VD As Double = 4.74
Const C5_DD As Double = 0.83

' Risers [m] -- HFC2500 (published), catalog.md; R_k carries the gas
' from C(k+1) up to C(k). Drawn per string at the string scale; R1
' splits into the twin C1, each branch half its area.
Const R1_D As Double = 3.07
Const R2_D As Double = 3.35
Const R3_D As Double = 3.45
Const R4_D As Double = 3.6

' Calciner [m] -- calciner.bas / calciner.md
Const CALC_D        As Double = 5.5
Const CALC_H        As Double = 29.46      ' cone + cylinder
Const CALC_THROAT_D As Double = 2.213299
Const CALC_CONE_DEG As Double = 65#
Const GN_D_SRC      As Double = 3.5        ' published gooseneck, two legs share its area
Const GN_OUT_AT_H   As Double = 0.5        ' legs end at this fraction of CALC_H
Const FEED_BELOW_GN_OUT As Double = 2#     ' meal feed through the wall this far below the legs' ends
Const TA_D          As Double = 1.725      ' tertiary air duct, derived in calciner.md

' Meal pipes end at the slope of the calciner feed pipes, Fidaros 2007
' (calciner.md): a chute at 60 deg meets an upright riser wall at
' 30 deg, sliding in along it.
Const MEAL_SLOPE_DEG As Double = 60#

' Kiln [m] -- kiln.md (published); cooler -- cooler.md, grate area [m2]
Const KILN_D      As Double = 4#
Const KILN_L      As Double = 60#
Const KILN_SLOPE  As Double = 0.03
Const COOLER_AREA As Double = 65#

' SCHEMATIC -- no source; they only lay the plant out.
Const STUB_OVER_VD   As Double = 1#       ' cyclone gas outlet stub above the roof, x vortex finder D
Const STAGE_GAP      As Double = 3#       ' a cyclone's dust outlet above the top of the stage below [m]
Const ZIG_DX         As Double = 8#       ' a string's outer column (C4, C2) outboard of its inner one (C5, C3) [m]
Const C1_TWIN_GAP    As Double = 3#       ' between the twin C1 barrels; R1 rises in it [m]
Const GN_TO_C5_GAP   As Double = 1#       ' a gooseneck drop to its C5 barrel; its inlet run spans it [m]
Const EXHAUST_L      As Double = 10#      ' C1 exhaust drawn this far past the string, towards the ID fan [m]
Const RAW_L          As Double = 6#       ' raw meal line drawn from this far outboard [m]
Const MEAL_JOIN_DEG  As Double = 50#      ' the outer C1's meal pipe falls at this slope to join the inner one's [deg]
Const MEAL_ENTRY_UP  As Double = 1.5      ' meal enters a riser's upright this far over the top of its run [m]
Const KILN_AXIS_Z    As Double = 10#      ' kiln inlet axis elevation [m]
Const CHAMBER_MARGIN As Double = 1#       ' kiln inlet chamber and hood: a square this far round the kiln [m]
Const COOLER_W       As Double = 3#       ' grate width [m]; the length follows from the area
Const COOLER_H       As Double = 4#       ' cooler casing height [m]
Const COOLER_DROP    As Double = 1#       ' cooler top below the kiln shell at discharge [m]
Const MEAL_INTO_CHAMBER As Double = 1#    ' C5 meal lands this far in from the chamber's side [m]
Const MIN_SEG        As Double = 0.05     ' a wall piece beside an opening shorter than this is left out [m]
Const CLINKER_OUT_Z  As Double = 3.5      ' clinker transport drawn this far below ground [m]
Const VENT_IN        As Double = 3#       ' cooler vent this far in from the cooler's end [m]
Const VENT_UP        As Double = 4#       ' vent arrow drawn this far over the cooler roof [m]
Const CLINKER_ON_GRATE As Double = 1#     ' clinker line this far over the cooler floor [m]
Const TA_ARROW_LONG  As Double = 1.15     ' tertiary air arrow this many times the rise from the cooler's mid-height to the hood roof; it runs on up into its duct [-]
Const C4_MEAL_DROP   As Double = 3#       ' C4 meal falls straight this far before turning towards the calciner [m]
Const C4_MEAL_OVER   As Double = 1.2      ' ... and ends this far over where it crosses the C5 stub; C4 stands as high as that needs [m]
Const FEED_LOWER     As Double = 3#       ' C4 meal drawn into the calciner this far below calciner.bas's feed [m]
Const KILN_FLOW_OFF  As Double = 1#       ' kiln gas and material lines this far either side of the kiln axis [m]
Const PRIMARY_AIR_L  As Double = 2#       ' primary air: a short arrow this long into the hood's front wall [m]
Const SEC_AIR_DX     As Double = 1.5      ' secondary air rises from the cooler this far in from the kiln's end [m]

' Sheet [m on paper]: A1 landscape at 1:200
Const SHEET_SCALE As Double = 200#
Const PAPER_W     As Double = 0.841
Const PAPER_H     As Double = 0.594
Const X0          As Double = 0.2         ' where model x = 0 falls on the sheet
Const RULER_X     As Double = 0.03        ' the elevation ruler
Const Y0          As Double = 0.06        ' where model z = 0 falls on the sheet
Const TEXT_H      As Double = 0.0035      ' text height
Const ARROW_L     As Double = 0.004       ' arrow head length

' Layers: name, colour (RGB), line weight
Const L_EQUIP As String = "EKIPMAN"
Const L_GAS   As String = "GAZ"
Const L_MEAL  As String = "FARIN"
Const L_AIR   As String = "HAVA"
Const L_TEXT  As String = "YAZI"

' Output
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const EXT_TOL As Double = 0.0001   ' sheet extents read back vs drawn [m on paper]
Const PI As Double = 3.14159265358979


'------------------------------------------------------------------
' Module state
'------------------------------------------------------------------

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swDraw  As SldWorks.DrawingDoc
Dim swSkMgr As SldWorks.SketchManager

' (b) derived layout -- every one computed, none typed in
Dim sScale As Double                      ' string scale, 1/sqrt 2
Dim aCh As Double, zCh0 As Double         ' chamber: |x| <= aCh, z from zCh0, 2 aCh tall
Dim rCalc As Double, rThroat As Double, hCone As Double
Dim zThroat As Double, zConeTop As Double, zCalcRoof As Double
Dim rGn As Double, xRise As Double, rGnBend As Double
Dim xLeg As Double, zGnTop As Double, zLeg As Double
Dim zFeed As Double                       ' C4 meal reaches the calciner wall here
Dim kAlpha As Double
Dim kAx As Double, kAz As Double, kBx As Double, kBz As Double
Dim coolL As Double, zCool0 As Double, zHood0 As Double
Dim rTA As Double, zTA As Double
Dim zDust(1 To 5) As Double, zRoof(1 To 5) As Double, zTop(1 To 5) As Double
Dim zIn(1 To 5) As Double                 ' gas inlet centre: at the roof for C1-C4, mid-barrel for C5
Dim zC5Bar As Double                      ' the C5 barrels' bottom; a leg's inlet run fits above it
Dim xInner As Double                      ' |x| of a string's inner column (C5, C3)

' drawing state
Dim curLayer As String
Dim layerNames(4) As String
Dim nLine(4) As Long, nArc(4) As Long, nNotes As Long
Dim pxMin As Double, pxMax As Double, pyMin As Double, pyMax As Double
Dim noteWarned As Boolean

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

    phase = "working out the layout"
    Derive
    phase = "checking the layout"
    PreChecks
    phase = "drawing"
    Build

    Restore
    WriteLog
    MsgBox "Plant topology 2D built and verified: two strings, 12 cyclones, A1 at 1:" & Fmt(SHEET_SCALE) & _
           "." & vbLf & LayerSummary() & vbLf & vbLf & "Full log: " & LogPath(), vbInformation, "Plant topology 2D"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    buildLog = buildLog & "ABORTED while " & phase & ": " & why & vbLf
    WriteLog
    MsgBox "Plant topology 2D ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
           vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Plant topology 2D"

End Sub


'==================================================================
' (b) Layout
'==================================================================
Private Sub Derive()

    Dim top As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim s As Long

    sScale = Sqr(0.5)

    ' Kiln inlet chamber round the kiln's inlet end; the kiln runs
    ' out of its +x side, falling KILN_SLOPE towards the cooler.
    aCh = 0.5 * KILN_D + CHAMBER_MARGIN
    zCh0 = KILN_AXIS_Z - aCh
    kAlpha = Atn(KILN_SLOPE)
    kAx = aCh: kAz = KILN_AXIS_Z
    kBx = kAx + KILN_L * Cos(kAlpha)
    kBz = kAz - KILN_L * Sin(kAlpha)

    ' The calciner stands on the chamber.
    rCalc = 0.5 * CALC_D
    rThroat = 0.5 * CALC_THROAT_D
    hCone = (rCalc - rThroat) * Tan(CALC_CONE_DEG * PI / 180#)
    zThroat = zCh0 + 2# * aCh
    zConeTop = zThroat + CALC_THROAT_D + hCone
    zCalcRoof = zThroat + CALC_THROAT_D + CALC_H

    ' Its twin gooseneck exactly as calciner.bas builds it: legs of
    ' half the published area rising at (R + r) / 3 off the axis,
    ' 1.25 D up, over a 1.5 D bend, and down beside the C5s.
    rGn = Sqr(0.5 * 0.25 * GN_D_SRC * GN_D_SRC)
    xRise = (rCalc + rGn) / 3#
    rGnBend = 1.5 * 2# * rGn
    xLeg = xRise + 2# * rGnBend
    zGnTop = zCalcRoof + 1.25 * 2# * rGn
    zLeg = zThroat + CALC_THROAT_D + GN_OUT_AT_H * CALC_H
    zFeed = zLeg - FEED_BELOW_GN_OUT - FEED_LOWER

    ' Each string: C5 GN_TO_C5_GAP outboard of its leg, its roof where
    ' the leg ends; the leg turns into the C5 barrel at its inlet. Each
    ' stage's dust outlet STAGE_GAP over the top of the stage below.
    CycDims 5, d, hb, hc, vd, dd
    xInner = xLeg + rGn + GN_TO_C5_GAP + 0.5 * d
    zDust(5) = zLeg - (hb + hc)
    top = zLeg + STUB_OVER_VD * vd
    For s = 4 To 1 Step -1
        zDust(s) = top + STAGE_GAP
        ' C4 high enough for its meal's straight drop to end over the
        ' C5 stub, where the meal crosses it (zTop(5) + 0.3)
        If s = 4 Then zDust(4) = Max2(zDust(4), top + 0.3 + C4_MEAL_OVER + C4_MEAL_DROP)
        top = zDust(s) + CycHeight(s)
    Next s
    For s = 1 To 5
        CycDims s, d, hb, hc, vd, dd
        zRoof(s) = zDust(s) + hc + hb
        zTop(s) = zDust(s) + CycHeight(s)
        ' C1 to C4 take their gas at the roof, as their CFD solids do
        ' (C1's slot and C4's volute run down from the roof): the
        ' riser's top wall flush with it. C5's catalogue inlet is
        ' taller than its barrel; it stays at mid-barrel.
        If s = 5 Then
            zIn(s) = zRoof(s) - 0.5 * hb
        ElseIf s = 1 Then
            zIn(s) = zRoof(s) - sScale * 0.5 * RiserD(1)
        Else
            zIn(s) = zRoof(s) - 0.5 * RiserD(s)
        End If
    Next s
    CycDims 5, d, hb, hc, vd, dd
    zC5Bar = zRoof(5) - hb

    ' Cooler under the kiln's discharge, running on in +x; the hood,
    ' a mirror of the chamber, on it round the kiln's end; the
    ' tertiary air duct from the hood to the calciner, its lower edge
    ' on the top of the cone (schematic -- calciner.bas step 6 will
    ' set its own).
    coolL = COOLER_AREA / COOLER_W
    zCool0 = kBz - 0.5 * KILN_D - COOLER_DROP - COOLER_H
    zHood0 = kBz - aCh
    rTA = 0.5 * TA_D
    zTA = zConeTop + rTA

End Sub


' Cyclone dimensions by stage, per string (C2 and C3 are C4; C5 is
' the twin's own size).
Private Sub CycDims(ByVal s As Long, ByRef d As Double, ByRef hb As Double, ByRef hc As Double, _
                    ByRef vd As Double, ByRef dd As Double)
    Select Case s
        Case 1
            d = C1_D: hb = C1_HB: hc = C1_HC: vd = C1_VD: dd = C1_DD
        Case 2, 3, 4
            d = C4_D: hb = C4_HB: hc = C4_HC: vd = C4_VD: dd = C4_DD
        Case 5
            d = C5_D: hb = C5_HB: hc = C5_HC: vd = C5_VD: dd = C5_DD
    End Select
    d = d * sScale: hb = hb * sScale: hc = hc * sScale: vd = vd * sScale: dd = dd * sScale
End Sub


' Dust outlet to the top of the gas outlet stub.
Private Function CycHeight(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    CycHeight = hc + hb + STUB_OVER_VD * vd
End Function


Private Function CycR(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    CycR = 0.5 * d
End Function


Private Function StubR(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    StubR = 0.5 * vd
End Function


' Riser diameter per string.
Private Function RiserD(ByVal k As Long) As Double
    Select Case k
        Case 1: RiserD = R1_D
        Case 2: RiserD = R2_D
        Case 3: RiserD = R3_D
        Case 4: RiserD = R4_D
    End Select
    RiserD = RiserD * sScale
End Function


'==================================================================
' (c) Pre-checks: no outline may run into another.
'==================================================================
Private Sub PreChecks()

    Dim r1 As Double, r4 As Double, r5 As Double, xm As Double
    Dim k As Long

    r1 = CycR(1): r4 = CycR(4): r5 = CycR(5)
    xm = xInner + 0.5 * ZIG_DX

    ' The risers rise between a string's two columns at their true
    ' width, clear of both
    For k = 1 To 4
        If 0.5 * ZIG_DX <= Max2(r4, r5) + 0.5 * RiserD(k) Then
            Fail "ZIG_DX = " & Fmt(ZIG_DX) & " m leaves no room for R" & k & " (D " & Fmt(RiserD(k)) & _
                 ") between a string's two columns."
        End If
    Next k
    ' R1 rises between the twin C1
    If C1_TWIN_GAP <= RiserD(1) Then
        Fail "C1_TWIN_GAP = " & Fmt(C1_TWIN_GAP) & " m is narrower than R1 (D " & Fmt(RiserD(1)) & ")."
    End If
    ' A riser's run along a stub top passes under the dust outlet of
    ' the stage above, which stands in the other column
    For k = 1 To 4
        If zTop(k + 1) + RiserD(k) >= zDust(k) Then
            Fail "R" & k & " along the top of C" & (k + 1) & " reaches up to the dust outlet of C" & k & _
                 ". Raise STAGE_GAP."
        End If
    Next k
    ' The C5s clear of the calciner; the gooseneck rises clear of each other
    If xInner - r5 <= rCalc Then Fail "the C5s run into the calciner."
    If xRise - rGn <= 0# Then Fail "the two gooseneck rises overlap."
    ' Each leg's inlet run fits the C5 barrel's height
    If 2# * rGn >= zRoof(5) - zC5Bar Then Fail "the gooseneck legs (D " & Fmt(2# * rGn) & _
        ") are taller than the C5 barrel they enter."
    ' The C4 meal passes over the C5 stub
    If zDust(4) - C4_MEAL_DROP <= zTop(5) + 0.3 Then
        Fail "C4's meal, after its straight drop, is not above the C5 stub; it could not pass over it."
    End If
    ' and on into the calciner's cylinder, over the cone
    If zFeed <= zConeTop Then Fail "the C4 meal would reach the calciner below its cylinder. Lower FEED_LOWER."
    ' The tertiary air duct runs under the C5s and over the chamber and kiln
    If zTA + rTA >= zDust(5) Then Fail "the tertiary air duct runs into the C5s."
    If zTA - rTA <= zThroat Or zTA - rTA <= kAz + 0.5 * KILN_D Then
        Fail "the tertiary air duct runs into the kiln or the inlet chamber."
    End If
    ' The cooler above ground, the hood on it
    If zCool0 <= 0# Then Fail "the cooler floor is at z = " & Fmt(zCool0) & " m, below ground. Raise KILN_AXIS_Z."
    If Abs(zHood0 - (zCool0 + COOLER_H)) > 0.001 Then Fail "the kiln hood does not sit on the cooler."
    If aCh <= rThroat Then Fail "the kiln inlet chamber is narrower than the calciner throat."
    ' The kiln's gas and material lines inside its shell
    If KILN_FLOW_OFF >= 0.5 * KILN_D Then Fail "KILN_FLOW_OFF puts the kiln's flow lines outside its shell."
    ' The plant fits the sheet, left of the legend
    If X0 + (-xm - 0.5 * ZIG_DX - EXHAUST_L) / SHEET_SCALE < RULER_X + 0.01 Or _
       X0 + (kBx + coolL) / SHEET_SCALE > 0.63 Or Y0 + (zTop(1) + 4#) / SHEET_SCALE > PAPER_H - 0.02 Then
        Fail "the plant does not fit the A1 sheet at 1:" & Fmt(SHEET_SCALE) & "."
    End If

    Note "kiln inlet chamber: |x| <= " & Fmt(aCh) & " m, z " & Fmt(zCh0) & " .. " & Fmt(zCh0 + 2# * aCh)
    Note "calciner: z " & Fmt(zThroat) & " .. " & Fmt(zCalcRoof) & "; gooseneck rises at x +-" & Fmt(xRise) & _
         ", legs at x +-" & Fmt(xLeg) & " down to the C5 inlet at z " & Fmt(zIn(5))
    Note "strings: inner column x +-" & Fmt(xInner) & " (C5, C3), outer x +-" & Fmt(xInner + ZIG_DX) & _
         " (C4, C2), risers at x +-" & Fmt(xm) & ", twin C1 at x +-" & Fmt(xm - r1 - 0.5 * C1_TWIN_GAP) & _
         " and +-" & Fmt(xm + r1 + 0.5 * C1_TWIN_GAP)
    Note "dust outlets C5 / C4 / C3 / C2 / C1 at z " & Fmt(zDust(5)) & " / " & Fmt(zDust(4)) & " / " & _
         Fmt(zDust(3)) & " / " & Fmt(zDust(2)) & " / " & Fmt(zDust(1)) & "; top " & Fmt(zTop(1))
    Note "kiln: (" & Fmt(kAx) & ", " & Fmt(kAz) & ") -> (" & Fmt(kBx) & ", " & Fmt(kBz) & "); cooler x " & _
         Fmt(kBx) & " .. " & Fmt(kBx + coolL) & ", z " & Fmt(zCool0) & " .. " & Fmt(zCool0 + COOLER_H)
    Note "tertiary air at z " & Fmt(zTA) & ", D " & Fmt(TA_D)

End Sub


'==================================================================
' (d) Build: a drawing, its layers, everything on the sheet.
'==================================================================
Private Sub Build()

    Dim tpl As String
    Dim ok As Boolean
    Dim dw As Object

    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateDrawing)
    If tpl = "" Then Fail "no default drawing template is set (Tools > Options > Default Templates)."
    Set swModel = swApp.NewDocument(tpl, swDwgPaperA1size, PAPER_W, PAPER_H)
    If swModel Is Nothing Then Fail "could not create a drawing from " & tpl & "."
    Set swDraw = swModel
    Set swSkMgr = swModel.SketchManager

    ' A blank A1 sheet: no sheet format, so the template's own title
    ' block cannot sit under the drawing. Allowed to fail -- the
    ' drawing is still right, only the template's frame shows.
    On Error Resume Next
    Set dw = swDraw
    ok = dw.SetupSheet5(dw.GetCurrentSheet.GetName, swDwgPaperA1size, swDwgTemplateNone, 1#, 1#, _
                        True, "", PAPER_W, PAPER_H, "Default", True)
    If Err.Number <> 0 Or Not ok Then Note "WARNING: could not clear the sheet format; the template's frame stays."
    Err.Clear
    On Error GoTo 0

    swDraw.EditSheet
    MakeLayers

    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False
    pxMin = 1E+30: pyMin = 1E+30: pxMax = -1E+30: pyMax = -1E+30

    DrawPlant
    phase = "drawing the legend and title"
    DrawLegend
    DrawTitle

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ClearSelection2 True

    phase = "verifying the sheet"
    VerifySheet
    swModel.ViewZoomtofit2
    SaveOutputs

End Sub


Private Sub MakeLayers()

    Dim lm As Object

    layerNames(0) = L_EQUIP: layerNames(1) = L_GAS: layerNames(2) = L_MEAL
    layerNames(3) = L_AIR: layerNames(4) = L_TEXT

    Set lm = swModel.GetLayerManager
    If lm Is Nothing Then Fail "the drawing has no layer manager."
    AddOneLayer lm, L_EQUIP, "equipment outlines", RGB(0, 0, 0), swLW_NORMAL
    AddOneLayer lm, L_GAS, "hot gas and air", RGB(210, 0, 0), swLW_THIN
    AddOneLayer lm, L_MEAL, "meal path", RGB(200, 150, 0), swLW_THIN
    AddOneLayer lm, L_AIR, "cold air", RGB(30, 90, 220), swLW_THIN
    AddOneLayer lm, L_TEXT, "labels, legend, title", RGB(0, 0, 0), swLW_THIN
    Note "layers: " & L_EQUIP & " (black, normal), " & L_GAS & " (red), " & L_MEAL & " (yellow), " & _
         L_AIR & " (blue), " & L_TEXT & " (black, thin)"

End Sub


' One layer, checked by reading it back -- AddLayer's return value is
' not relied on.
Private Sub AddOneLayer(lm As Object, ByVal name As String, ByVal desc As String, ByVal colour As Long, _
                        ByVal weight As Long)
    Dim ret As Variant
    ret = lm.AddLayer(name, desc, colour, swLineCONTINUOUS, weight)
    If lm.GetLayer(name) Is Nothing Then
        Fail "layer " & name & " was not created (AddLayer returned " & CStr(ret) & ")."
    End If
End Sub


' Make a layer current, checked by reading the current layer back --
' SetCurrentLayer's return value is not relied on.
Private Sub UseLayer(ByVal name As String)
    Dim lm As Object
    Dim ret As Variant
    Set lm = swModel.GetLayerManager
    ret = lm.SetCurrentLayer(name)
    If UCase(lm.GetCurrentLayer) <> UCase(name) Then
        Fail "could not make layer " & name & " current (SetCurrentLayer returned " & CStr(ret) & _
             ", current layer is '" & lm.GetCurrentLayer & "')."
    End If
    curLayer = name
End Sub


Private Function LayerIndex(ByVal name As String) As Long
    Dim i As Long
    LayerIndex = -1
    For i = 0 To 4
        If layerNames(i) = name Then LayerIndex = i
    Next i
End Function


Private Sub DrawPlant()

    Dim k As Long, s As Long, up As Long
    Dim sd As Double, xi As Double, xo As Double, xm As Double, xw As Double, xs0 As Double
    Dim r1 As Double, dc1 As Double, c1in As Double, c1out As Double
    Dim r As Double, rb As Double, zh As Double, zx As Double, xe As Double
    Dim wl As Double, wr As Double, ls As Double
    Dim zJoin As Double, xc As Double, zc As Double, kOff As Double
    Dim kSh As Double, zTopCh As Double, zTopHd As Double, xn As Double
    Dim zEnt(2 To 5) As Double                ' top edge of the run of the riser leaving stage s
    Dim col(2 To 5) As Double
    Dim side As String

    '=== equipment ======================================================
    ' Every wall a flow passes through is left open: the kiln's ends,
    ' the calciner throat, the gooseneck and tertiary air ports, the
    ' hood over the cooler, each cyclone's inlet, gas outlet and dust
    ' outlet. Single-line paths (meal, exhaust) end on a wall as drawn.
    phase = "drawing the equipment"
    UseLayer L_EQUIP
    kSh = 0.5 * KILN_D / Cos(kAlpha)           ' kiln shell above / below its axis, on a vertical
    zTopCh = zCh0 + 2# * aCh
    zTopHd = zHood0 + 2# * aCh

    ' kiln inlet chamber: open to the kiln on its +x wall, to the
    ' calciner throat in its roof
    LineM -aCh, zCh0, aCh, zCh0
    Seg aCh, zCh0, aCh, kAz - kSh
    Seg aCh, kAz + kSh, aCh, zTopCh
    Seg aCh, zTopCh, rThroat, zTopCh
    Seg -rThroat, zTopCh, -aCh, zTopCh
    LineM -aCh, zTopCh, -aCh, zCh0
    ' calciner: no floor (the throat), the tertiary air port in its +x
    ' wall over the cone, the two gooseneck rises in its roof
    PolyM Array(rThroat, zThroat, rThroat, zThroat + CALC_THROAT_D, rCalc, zConeTop)
    Seg rCalc, zConeTop + TA_D, rCalc, zCalcRoof
    Seg rCalc, zCalcRoof, xRise + rGn, zCalcRoof
    Seg xRise - rGn, zCalcRoof, -(xRise - rGn), zCalcRoof
    Seg -(xRise + rGn), zCalcRoof, -rCalc, zCalcRoof
    PolyM Array(-rCalc, zCalcRoof, -rCalc, zConeTop, -rThroat, zThroat + CALC_THROAT_D, -rThroat, zThroat)
    ' kiln: its shell only, both ends open
    LineM kAx, kAz + kSh, kBx, kBz + kSh
    LineM kAx, kAz - kSh, kBx, kBz - kSh
    ' hood: open to the kiln on its -x wall, to the tertiary air duct
    ' in its roof, and to the cooler under it
    Seg kBx, zHood0, kBx, kBz - kSh
    Seg kBx, kBz + kSh, kBx, zTopHd
    Seg kBx, zTopHd, kBx + aCh - 0.5 * TA_D, zTopHd
    Seg kBx + aCh + 0.5 * TA_D, zTopHd, kBx + 2# * aCh, zTopHd
    LineM kBx + 2# * aCh, zTopHd, kBx + 2# * aCh, zHood0
    ' cooler: its roof only past the hood
    PolyM Array(kBx + 2# * aCh, zCool0 + COOLER_H, kBx + coolL, zCool0 + COOLER_H, kBx + coolL, zCool0, _
                kBx, zCool0, kBx, zCool0 + COOLER_H)

    r1 = CycR(1)
    dc1 = r1 + 0.5 * C1_TWIN_GAP
    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        ' each open on the side its inlet comes from: C5 the gooseneck's
        ' (towards the calciner), the others their riser's (towards xm)
        Cyclone 5, col(5), -sd, rGn
        For s = 4 To 2 Step -1
            Cyclone s, col(s), Sgn(xm - col(s)), 0.5 * RiserD(s)
        Next s
        Cyclone 1, xm - sd * dc1, sd, sScale * 0.5 * RiserD(1)
        Cyclone 1, xm + sd * dc1, -sd, sScale * 0.5 * RiserD(1)
    Next k

    '=== gas ==============================================================
    phase = "drawing the gas path"
    UseLayer L_GAS
    ' Through the kiln, above its axis, from the burner end to the inlet
    ' (the material runs the other way below it)
    kOff = KILN_FLOW_OFF / Cos(kAlpha)
    PathL "gas: kiln (burner end -> inlet)", Array(kBx, kBz + kOff, kAx, kAz + kOff, 0#, kAz + kOff)
    PathL "gas: inlet chamber -> calciner", Array(0#, kAz + kOff, 0#, zCalcRoof - 2#)

    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        c1in = xm - sd * dc1: c1out = xm + sd * dc1

        '--- the gooseneck leg, as calciner.bas: rise, bend, drop, then
        '    across into the C5 barrel at its inlet (the tangential inlet
        '    seen from the side) --------------------------------------
        Duct "gas: calciner -> gooseneck rise " & side, Array(sd * xRise, zCalcRoof, sd * xRise, zGnTop), _
             2# * rGn, False
        DuctBend sd * (xRise + rGnBend), zGnTop, rGnBend, rGn
        Duct "gas: gooseneck drop " & side & " -> C5 inlet", Array(sd * xLeg, zGnTop, sd * xLeg, zIn(5), _
             xi - sd * CycR(5), zIn(5)), 2# * rGn, False

        '--- R4..R2: along the stub top, across, up, into the side above -
        For s = 5 To 3 Step -1
            up = s - 1
            r = 0.5 * RiserD(up)
            zh = zTop(s) + r
            xs0 = col(s) - Sgn(xm - col(s)) * StubR(s)
            xw = col(up) - Sgn(col(up) - xm) * CycR(up)
            RunOverStub s, col(s), xm, r, xn
            Duct "gas: C" & s & " " & side & " -> R" & up & " -> C" & up, _
                 Array(xn, zh, xm, zh, xm, zIn(up), xw, zIn(up)), 2# * r, False
            zEnt(s) = zTop(s) + 2# * r
        Next s

        '--- R1: along the C2 stub, across, up between the twin C1, split -
        r = 0.5 * RiserD(1)
        rb = sScale * r
        zh = zTop(2) + r
        RunOverStub 2, xo, xm, r, xn
        Duct "gas: C2 " & side & " -> R1", Array(xn, zh, xm, zh, xm, zIn(1) - rb), 2# * r, False
        wl = Min2(c1in, c1out) + r1: wr = Max2(c1in, c1out) - r1
        LineM wl, zIn(1) + rb, wr, zIn(1) + rb
        LineM wl, zIn(1) - rb, xm - r, zIn(1) - rb
        LineM xm + r, zIn(1) - rb, wr, zIn(1) - rb
        Note "-- gas: R1 " & side & " -> twin C1 (split, branches D " & Fmt(2# * rb) & ")"

        '--- both C1 out, joined, towards the ID fan ---------------------
        zx = zTop(1) + 2#
        xe = xm + sd * (0.5 * ZIG_DX + EXHAUST_L)
        PathOut "gas: C1 " & side & " -> exhaust -> ID fan", Array(c1in, zTop(1), c1in, zx, xe, zx)
        PathL "gas: C1 " & side & " (second) -> exhaust", Array(c1out, zTop(1), c1out, zx)

        '--- meal ---------------------------------------------------------
        phase = "drawing the meal path, string " & side
        UseLayer L_MEAL
        ' Each falls straight down its own column, then at the meal slope
        ' through the near wall of the upright of the riser leaving the
        ' stage two below, just over that riser's run -- where a plant
        ' feeds its meal. The outer C1 sits over C2, so its meal joins
        ' the inner C1's pipe instead.
        zJoin = zDust(1) - Abs(c1out - c1in) * Tan(MEAL_JOIN_DEG * PI / 180#)
        If zJoin <= MealIntoRiser("meal: C1 " & side & " -> R2", c1in, zDust(1), xm, zEnt(3), 2) Then
            Fail "the outer C1's meal would join the inner one's below its turn. Lower MEAL_JOIN_DEG."
        End If
        PathL "meal: C1 " & side & " (second) -> the first C1's meal pipe", Array(c1out, zDust(1), c1in, zJoin)
        MealIntoRiser "meal: C2 " & side & " -> R3", col(2), zDust(2), xm, zEnt(4), 3
        MealIntoRiser "meal: C3 " & side & " -> R4", col(3), zDust(3), xm, zEnt(5), 4
        PathL "meal: C4 " & side & " -> calciner", Array(col(4), zDust(4), col(4), zDust(4) - C4_MEAL_DROP, _
              xi - sd * (StubR(5) + 0.3), zTop(5) + 0.3, sd * rCalc, zFeed)
        PathL "meal: C5 " & side & " -> kiln inlet chamber", Array(xi, zDust(5), _
              sd * (aCh - MEAL_INTO_CHAMBER), zCh0 + 2# * aCh)
        ' raw meal at the meal slope into the outer end of R1's run,
        ' just over C2's gas outlet
        xc = xo - Sgn(xm - xo) * StubR(2)
        zc = zTop(2) + 0.75 * RiserD(1)
        PathL "meal: raw meal -> R1 " & side, Array(xc + sd * RAW_L * Cos(MEAL_SLOPE_DEG * PI / 180#), _
              zc + RAW_L * Sin(MEAL_SLOPE_DEG * PI / 180#), xc, zc)
        UseLayer L_GAS
    Next k

    ' The material from the inlet chamber through the kiln below its
    ' axis, down into the cooler and along its grate (clinker)
    UseLayer L_MEAL
    PathL "meal: inlet chamber -> kiln -> grate cooler (clinker)", Array( _
          aCh - MEAL_INTO_CHAMBER, kAz - kOff + (kAx - aCh + MEAL_INTO_CHAMBER) * Tan(kAlpha), _
          kBx, kBz - kOff, kBx + 1#, zCool0 + CLINKER_ON_GRATE, kBx + coolL - 1#, zCool0 + CLINKER_ON_GRATE)
    ' and out of the cooler's end, down to the clinker transport below
    ' ground
    PathOut "meal: grate cooler -> clinker transport", Array(kBx + coolL - 1#, zCool0 + CLINKER_ON_GRATE, _
            kBx + coolL - 1#, -CLINKER_OUT_Z)

    '=== air ==============================================================
    phase = "drawing the air path"
    UseLayer L_AIR
    ' Primary air only marked: a short arrow whose tip touches the hood's
    ' front wall, level with where the kiln gas starts. The secondary
    ' air rises from the cooler under the hood into the kiln on the gas
    ' layer: it is the stream that runs on through the kiln as its gas.
    PathOut "air: primary air -> main burner", Array(kBx + 2# * aCh + PRIMARY_AIR_L, kBz + kOff, _
            kBx + 2# * aCh, kBz + kOff)
    UseLayer L_GAS
    PathL "gas: cooler -> hood (secondary air) -> kiln", Array(kBx + SEC_AIR_DX, zCool0 + 0.5 * COOLER_H, _
          kBx + SEC_AIR_DX, kBz + kOff, kBx, kBz + kOff)
    ' The tertiary air rises straight out of the cooler through the hood,
    ' marked as the secondary air is, into its duct on the hood's top;
    ' hot, so on the gas layer as the secondary air
    zc = zCool0 + 0.5 * COOLER_H + TA_ARROW_LONG * (zHood0 + 2# * aCh - zCool0 - 0.5 * COOLER_H)
    If zc >= zTA - rTA Then Fail "the tertiary air arrow runs up past its duct's turn. Lower TA_ARROW_LONG."
    PathOut "gas: cooler -> hood (tertiary air)", Array(kBx + aCh, zCool0 + 0.5 * COOLER_H, kBx + aCh, zc)
    Duct "gas: hood -> tertiary air duct -> calciner", Array(kBx + aCh, zHood0 + 2# * aCh, _
         kBx + aCh, zTA, rCalc, zTA), TA_D, False
    ' The cooler's excess air, still hot, out of its roof near its end
    PathOut "gas: grate cooler -> cooler vent", Array(kBx + coolL - VENT_IN, zCool0 + 0.5 * COOLER_H, _
          kBx + coolL - VENT_IN, zCool0 + COOLER_H + VENT_UP)

    '=== ground and labels ==================================================
    phase = "labelling"
    UseLayer L_TEXT
    DrawRuler
    LabelM -aCh, zCh0 - 1#, "kiln inlet chamber", 0#
    LabelM -3.5, zGnTop + rGnBend + rGn + 3#, "ILC calciner", 0#
    LabelM 20#, kAz + 3.5, "rotary kiln D" & Num(KILN_D, 3) & " x " & Num(KILN_L, 0) & " m", 0#
    LabelM kBx + 0.55 * coolL + 0.5, zCool0 + 0.75 * COOLER_H, "grate cooler", 0#
    LabelM kBx + coolL - VENT_IN - 0.3 * TEXT_H * 14 * SHEET_SCALE, zCool0 + COOLER_H + VENT_UP + 1.1, _
           "to cooler vent", 0#
    LabelM kBx + coolL - 1.5 - 0.6 * TEXT_H * 20 * SHEET_SCALE, -CLINKER_OUT_Z + 2#, "to clinker transport", 0#
    LabelM kBx + 2# * aCh + 1#, zHood0 + 2# * aCh, "kiln hood", 0#
    LabelM kBx + 2# * aCh + 0.5, kBz + kOff - 0.3, "primary air", 0#
    ' inside the kiln, between its gas and its clinker: the kiln gas
    ' there is the secondary air the burner has fired
    LabelM kBx - 8#, kBz + 0.85, "secondary air", 0#
    LabelM 30#, zTA + rTA + 2#, "tertiary air D" & Num(TA_D, 3), 0#
    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        If sd > 0# Then ls = 0# Else ls = -0.01
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        For s = 5 To 2 Step -1
            CycLabel "C" & s & " " & side, s, col(s)
        Next s
        CycLabel "C1 " & side, 1, xm - sd * dc1
        CycLabel "C1 " & side, 1, xm + sd * dc1
        For s = 5 To 3 Step -1
            LabelM xm, 0.5 * (zTop(s) + 0.5 * RiserD(s - 1) + zIn(s - 1)) - 1.5, "R" & (s - 1), -0.002
        Next s
        LabelM xm, 0.5 * (zTop(2) + 0.5 * RiserD(1) + zIn(1)) + 2.5, "R1", -0.002
        LabelM xm + sd * (0.5 * ZIG_DX + EXHAUST_L), zTop(1) + 3.6, "to ID fan", IIf(sd > 0#, 0#, 0.002)
        LabelM xo - Sgn(xm - xo) * StubR(2) + sd * RAW_L * Cos(MEAL_SLOPE_DEG * PI / 180#), _
               zTop(2) + 0.75 * RiserD(1) + RAW_L * Sin(MEAL_SLOPE_DEG * PI / 180#) + 1.6, "raw meal", ls
    Next k

End Sub


' One cyclone's section about the vertical axis at xc: cone, barrel,
' roof, gas outlet stub. Open where the flows pass: the dust outlet at
' the bottom, the stub's top, and the barrel wall on side inSide (+1 /
' -1) over its inlet, hIn either side of the inlet's centre.
Private Sub Cyclone(ByVal s As Long, ByVal xc As Double, ByVal inSide As Double, ByVal hIn As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim k As Long
    Dim sg As Double, zb As Double, xb As Double
    CycDims s, d, hb, hc, vd, dd
    zb = zDust(s) + hc
    For k = 0 To 1
        sg = 1# - 2# * k
        xb = xc + sg * 0.5 * d
        LineM xc + sg * 0.5 * dd, zDust(s), xb, zb
        If sg = inSide Then
            Seg xb, zb, xb, Max2(zb, zIn(s) - hIn)
            Seg xb, Min2(zRoof(s), zIn(s) + hIn), xb, zRoof(s)
        Else
            LineM xb, zb, xb, zRoof(s)
        End If
        PolyM Array(xb, zRoof(s), xc + sg * 0.5 * vd, zRoof(s), xc + sg * 0.5 * vd, zTop(s))
    Next k
End Sub


' A riser's start over a gas outlet stub: its end cap over the stub's
' far wall and its top wall over the open stub. Returns in xn the
' stub's near wall, where the riser's duct carries on towards xm.
Private Sub RunOverStub(ByVal s As Long, ByVal xc As Double, ByVal xm As Double, ByVal r As Double, _
                        ByRef xn As Double)
    Dim xf As Double
    xf = xc - Sgn(xm - xc) * StubR(s)
    xn = xc + Sgn(xm - xc) * StubR(s)
    LineM xf, zTop(s), xf, zTop(s) + 2# * r
    LineM xf, zTop(s) + 2# * r, xn, zTop(s) + 2# * r
End Sub


' A meal pipe from a dust outlet at (xs, zs) into riser R(k), whose
' upright stands at xm and whose run's top edge is at zRunTop: down
' its own column, then at MEAL_SLOPE_DEG through the upright's near
' wall MEAL_ENTRY_UP over the run. Returns where it turns.
Private Function MealIntoRiser(ByVal what As String, ByVal xs As Double, ByVal zs As Double, _
                               ByVal xm As Double, ByVal zRunTop As Double, ByVal k As Long) As Double
    Dim xw As Double, ze As Double, zb As Double
    xw = xm - Sgn(xm - xs) * 0.5 * RiserD(k)
    ze = zRunTop + MEAL_ENTRY_UP
    zb = ze + Abs(xs - xw) * Tan(MEAL_SLOPE_DEG * PI / 180#)
    If zb >= zs Then Fail what & ": the dust outlet is too low to reach the riser at the meal slope."
    PathL what, Array(xs, zs, xs, zb, xw, ze)
    MealIntoRiser = zb
End Function


' A cyclone's name centred in its barrel, the one place no path
' crosses.
Private Sub CycLabel(ByVal txt As String, ByVal s As Long, ByVal xc As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    LabelM xc - 0.3 * TEXT_H * Len(txt) * SHEET_SCALE, zRoof(s) - 0.25 * hb, txt, 0#
End Sub


' The ground line and, at the sheet's left edge, an elevation ruler
' 0 .. 90 m with a tick and its elevation every 10 m.
Private Sub DrawRuler()
    Dim k As Long
    Dim xr As Double, y As Double
    xr = (RULER_X - X0) * SHEET_SCALE
    LineM xr, 0#, kBx + coolL + 1.4, 0#
    LineM xr, 0#, xr, 90#
    For k = 0 To 9
        y = Y0 + 10# * k / SHEET_SCALE
        LineP RULER_X, y, RULER_X + 0.003, y
        If k = 0 Then
            LabelP RULER_X - 0.016, y + 0.00175, "+-0.00"
        Else
            LabelP RULER_X - 0.016, y + 0.00175, "+" & Num(10# * k, 2)
        End If
    Next k
End Sub


'------------------------------------------------------------------
' Drawing primitives. Model points are (x, z) pairs in metres; P puts
' them on the sheet. Every line goes on the current layer.
'------------------------------------------------------------------
Private Sub P(ByVal x As Double, ByVal z As Double, ByRef px As Double, ByRef py As Double)
    px = X0 + x / SHEET_SCALE
    py = Y0 + z / SHEET_SCALE
End Sub


' A line between two model points.
Private Sub LineM(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    Dim a As Double, b As Double, c As Double, d As Double
    P xa, za, a, b
    P xb, zb, c, d
    LineP a, b, c, d
End Sub


' A line between two sheet points.
Private Sub LineP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    Dim i As Long
    If Abs(c - a) < 0.0000001 And Abs(d - b) < 0.0000001 Then Fail "a line on layer " & curLayer & " has no length."
    If swSkMgr.CreateLine(a, b, 0#, c, d, 0#) Is Nothing Then Fail "CreateLine failed on layer " & curLayer & "."
    i = LayerIndex(curLayer)
    nLine(i) = nLine(i) + 1
    Track a, b: Track c, d
End Sub


' An open polyline.
Private Sub PolyM(pts As Variant)
    Dim n As Long, i As Long
    n = (UBound(pts) + 1) \ 2
    For i = 0 To n - 2
        LineM pts(2 * i), pts(2 * i + 1), pts(2 * i + 2), pts(2 * i + 3)
    Next i
End Sub


' A wall piece left beside an opening: drawn only if longer than
' MIN_SEG, so an opening that spans the wall leaves no sliver.
Private Sub Seg(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    If Sqr((xb - xa) ^ 2 + (zb - za) ^ 2) >= MIN_SEG Then LineM xa, za, xb, zb
End Sub


' A path along its axis, one line, with an arrow on its longest run.
Private Sub PathL(ByVal what As String, pts As Variant)
    Dim n As Long, i As Long
    n = (UBound(pts) + 1) \ 2
    If n < 2 Then Fail what & " has fewer than two points."
    For i = 0 To n - 2
        LineM pts(2 * i), pts(2 * i + 1), pts(2 * i + 2), pts(2 * i + 3)
    Next i
    ArrowOnLongest pts
    Note "-- " & what
End Sub


' A path that leaves the drawing (or only marks a stream): one line,
' with the arrow's tip at its end, so no line runs on past the arrow.
Private Sub PathOut(ByVal what As String, pts As Variant)
    Dim n As Long, i As Long
    Dim L As Double, ax As Double, az As Double
    n = (UBound(pts) + 1) \ 2
    If n < 2 Then Fail what & " has fewer than two points."
    For i = 0 To n - 2
        LineM pts(2 * i), pts(2 * i + 1), pts(2 * i + 2), pts(2 * i + 3)
    Next i
    ax = pts(2 * n - 2) - pts(2 * n - 4): az = pts(2 * n - 1) - pts(2 * n - 3)
    L = Sqr(ax * ax + az * az)
    ax = ax / L: az = az / L
    ArrowAt pts(2 * n - 2) - ax * 0.5 * ARROW_L * SHEET_SCALE, pts(2 * n - 1) - az * 0.5 * ARROW_L * SHEET_SCALE, ax, az
    Note "-- " & what
End Sub


' A duct at its true width w: two lines offset w / 2 either side of
' its axis, joined at each corner where the offset lines cross
' (mitre). capStart closes the duct's first end. The arrow rides on
' the axis, which is not drawn.
Private Sub Duct(ByVal what As String, pts As Variant, ByVal w As Double, ByVal capStart As Boolean)

    Dim n As Long, i As Long, j As Long, sg As Long
    Dim h As Double, L As Double, f As Double, ax As Double, az As Double
    Dim nx() As Double, nz() As Double
    Dim ex() As Double, ez() As Double
    Dim e0x(1) As Double, e0z(1) As Double

    n = (UBound(pts) + 1) \ 2
    If n < 2 Then Fail what & " has fewer than two points."
    h = 0.5 * w
    ReDim nx(n - 2): ReDim nz(n - 2)
    ReDim ex(n - 1): ReDim ez(n - 1)
    For i = 0 To n - 2
        ax = pts(2 * i + 2) - pts(2 * i): az = pts(2 * i + 3) - pts(2 * i + 1)
        L = Sqr(ax * ax + az * az)
        If L <= 0# Then Fail what & ": two points coincide."
        nx(i) = -az / L: nz(i) = ax / L
    Next i
    For sg = 0 To 1
        For j = 0 To n - 1
            If j = 0 Then
                ax = nx(0): az = nz(0): f = 1#
            ElseIf j = n - 1 Then
                ax = nx(n - 2): az = nz(n - 2): f = 1#
            Else
                ax = nx(j - 1) + nx(j): az = nz(j - 1) + nz(j)
                f = 1# / (1# + nx(j - 1) * nx(j) + nz(j - 1) * nz(j))
            End If
            ex(j) = pts(2 * j) + (1 - 2 * sg) * h * ax * f
            ez(j) = pts(2 * j + 1) + (1 - 2 * sg) * h * az * f
        Next j
        For j = 0 To n - 2
            LineM ex(j), ez(j), ex(j + 1), ez(j + 1)
        Next j
        e0x(sg) = ex(0): e0z(sg) = ez(0)
    Next sg
    If capStart Then LineM e0x(0), e0z(0), e0x(1), e0z(1)
    ArrowOnLongest pts
    Note "-- " & what & " (D " & Fmt(w) & ")"

End Sub


' A gooseneck bend at its true width: two half circles about (cx, cz),
' radii R + h and R - h, over the top.
Private Sub DuctBend(ByVal cx As Double, ByVal cz As Double, ByVal R As Double, ByVal h As Double)
    Dim k As Long
    Dim rr As Double, a As Double, b As Double, c As Double, d As Double, m As Double, q As Double
    Dim i As Long
    For k = 0 To 1
        rr = R + h * (1 - 2 * k)
        P cx - rr, cz, a, b
        P cx + rr, cz, c, d
        P cx, cz + rr, m, q
        If swSkMgr.Create3PointArc(a, b, 0#, c, d, 0#, m, q, 0#) Is Nothing Then
            Fail "Create3PointArc failed on the gooseneck bend."
        End If
        i = LayerIndex(curLayer)
        nArc(i) = nArc(i) + 1
        Track a, b: Track c, d: Track m, q
    Next k
End Sub


' An open V arrow head at the middle of the longest run of a path,
' pointing along it, ARROW_L long on the sheet.
Private Sub ArrowOnLongest(pts As Variant)
    Dim n As Long, i As Long, best As Long
    Dim L As Double, bl As Double, ax As Double, az As Double
    n = (UBound(pts) + 1) \ 2
    bl = -1#
    For i = 0 To n - 2
        L = Sqr((pts(2 * i + 2) - pts(2 * i)) ^ 2 + (pts(2 * i + 3) - pts(2 * i + 1)) ^ 2)
        If L > bl + 0.000000001 Then best = i: bl = L
    Next i
    ax = (pts(2 * best + 2) - pts(2 * best)) / bl
    az = (pts(2 * best + 3) - pts(2 * best + 1)) / bl
    ArrowAt 0.5 * (pts(2 * best) + pts(2 * best + 2)), 0.5 * (pts(2 * best + 1) + pts(2 * best + 3)), ax, az
End Sub


Private Sub ArrowAt(ByVal x As Double, ByVal z As Double, ByVal dx As Double, ByVal dz As Double)
    Dim px As Double, py As Double, tx As Double, ty As Double
    Dim k As Long, sg As Double
    P x, z, px, py
    tx = px + dx * 0.5 * ARROW_L: ty = py + dz * 0.5 * ARROW_L
    For k = 0 To 1
        sg = 1# - 2# * k
        LineP tx, ty, tx - dx * ARROW_L - sg * dz * 0.4 * ARROW_L, ty - dz * ARROW_L + sg * dx * 0.4 * ARROW_L
    Next k
End Sub


' A note at model point (x, z), shifted dx on the sheet; text
' TEXT_H high on the text layer. Allowed to fail: the drawing is
' still right without its labels, and the log says so once.
Private Sub LabelM(ByVal x As Double, ByVal z As Double, ByVal txt As String, ByVal dx As Double)
    Dim px As Double, py As Double
    P x, z, px, py
    LabelP px + dx, py, txt
End Sub


Private Sub LabelP(ByVal px As Double, ByVal py As Double, ByVal txt As String)
    Dim nt As Object, an As Object, tf As Object
    On Error Resume Next
    swModel.ClearSelection2 True
    Set nt = swModel.InsertNote(txt)
    If Not nt Is Nothing Then
        Set an = nt.GetAnnotation
        an.SetPosition2 px, py, 0#
        Set tf = an.GetTextFormat(0)
        tf.CharHeight = TEXT_H
        an.SetTextFormat 0, False, tf
        an.Layer = L_TEXT
    End If
    If (Err.Number <> 0 Or nt Is Nothing) And Not noteWarned Then
        Note "WARNING: could not place a note (" & Err.Description & "); labels are missing or unformatted."
        noteWarned = True
    End If
    If Err.Number = 0 And Not nt Is Nothing Then nNotes = nNotes + 1
    Err.Clear
    swModel.ClearSelection2 True
End Sub


Private Sub Track(ByVal a As Double, ByVal b As Double)
    If a < pxMin Then pxMin = a
    If a > pxMax Then pxMax = a
    If b < pyMin Then pyMin = b
    If b > pyMax Then pyMax = b
End Sub


'------------------------------------------------------------------
' Legend and title block, in sheet coordinates on the right.
'------------------------------------------------------------------
Private Sub DrawLegend()

    Dim x As Double, y As Double
    Dim k As Long

    x = 0.66: y = 0.53
    UseLayer L_TEXT
    LabelP x, y + 0.012, "LEGEND"

    UseLayer L_GAS:  LineP x, y, x + 0.02, y
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "hot gas and air (secondary, tertiary)"
    y = y - 0.012
    UseLayer L_MEAL: LineP x, y, x + 0.02, y
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "meal / clinker"
    y = y - 0.012
    UseLayer L_AIR:  LineP x, y, x + 0.02, y
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "cold air (primary)"
    y = y - 0.012
    UseLayer L_GAS:  LineP x, y, x + 0.02, y
    Call ArrowAt((x + 0.01 - X0) * SHEET_SCALE, (y - Y0) * SHEET_SCALE, 1#, 0#)
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "flow direction"
    y = y - 0.014
    UseLayer L_GAS:  LineP x, y + 0.002, x + 0.02, y + 0.002: LineP x, y - 0.002, x + 0.02, y - 0.002
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.004, "duct at its true diameter (risers, gooseneck, TA)"
    y = y - 0.012
    UseLayer L_TEXT: LineP x, y, x + 0.02, y
    LabelP x + 0.025, y + 0.002, "single line: path axis (meal, clinker, kiln gas, exhaust, air)"

    y = y - 0.02
    LabelP x, y, "Per string (catalogue 2500 x 1/sqrt 2):"
    LabelP x, y - 0.006, "C1 D" & Num(2# * CycR(1), 3) & " (twin), C2-C4 D" & Num(2# * CycR(4), 3) & _
                         ", C5 D" & Num(2# * CycR(5), 3)
    LabelP x, y - 0.012, "R1 / R2 / R3 / R4 D" & Num(RiserD(1), 3) & " / " & Num(RiserD(2), 3) & _
                         " / " & Num(RiserD(3), 3) & " / " & Num(RiserD(4), 3)
    LabelP x, y - 0.018, "calciner D" & Num(CALC_D, 3) & ", gooseneck legs D" & Num(2# * rGn, 3) & _
                         ", tertiary air D" & Num(TA_D, 3)
    LabelP x, y - 0.024, "elevations above ground, m; diameters are internal, m"

    ' 10 m scale bar
    y = y - 0.045
    LineP x, y, x + 10# / SHEET_SCALE, y
    For k = 0 To 2
        LineP x + k * 5# / SHEET_SCALE, y - 0.0015, x + k * 5# / SHEET_SCALE, y + 0.0015
    Next k
    LabelP x - 0.001, y - 0.003, "0"
    LabelP x + 10# / SHEET_SCALE - 0.002, y - 0.003, "10 m"

End Sub


Private Sub DrawTitle()

    Dim tx0 As Double, ty0 As Double, tx1 As Double, ty1 As Double

    tx0 = 0.64: ty0 = 0.03: tx1 = 0.83: ty1 = 0.115
    UseLayer L_TEXT
    LineP tx0, ty0, tx1, ty0
    LineP tx1, ty0, tx1, ty1
    LineP tx1, ty1, tx0, ty1
    LineP tx0, ty1, tx0, ty0
    LabelP tx0 + 0.004, ty1 - 0.004, "PYROPROCESS TOPOLOGY, " & LINE_KEY & " t/d reference line"
    LabelP tx0 + 0.004, ty1 - 0.016, "two-string preheater, 12 cyclones; ILC calciner; rotary kiln; grate cooler"
    LabelP tx0 + 0.004, ty1 - 0.028, "scale 1:" & Num(SHEET_SCALE, 0) & " on A1    " & Format(Date, "yyyy-mm-dd")
    LabelP tx0 + 0.004, ty1 - 0.040, "SCHEMATIC - shows the topology; not a CFD input"
    LabelP tx0 + 0.004, ty1 - 0.052, "drawn by geometry/macros/plant_topology_2d.bas"
    LabelP tx0 + 0.004, ty1 - 0.064, "sources: geometry/plant_topology.md"

End Sub


'==================================================================
' (f) Verification: the sheet must hold, layer by layer, every line
'     and arc drawn, and its lines must span exactly what was drawn.
'==================================================================
Private Sub VerifySheet()

    Dim v As Object, ssk As Object
    Dim segs As Variant
    Dim i As Long, li As Long
    Dim gotL(4) As Long, gotA(4) As Long
    Dim a0 As Double, a1 As Double, b0 As Double, b1 As Double
    Dim ln As SldWorks.SketchLine
    Dim pt As SldWorks.SketchPoint
    Dim t As Long

    Set v = swDraw.GetFirstView               ' the sheet itself
    If v Is Nothing Then Fail "could not read the sheet back."
    Set ssk = v.GetSketch
    If ssk Is Nothing Then Fail "the sheet has no sketch."
    segs = ssk.GetSketchSegments
    If IsEmpty(segs) Then Fail "the sheet holds no lines."

    a0 = 1E+30: b0 = 1E+30: a1 = -1E+30: b1 = -1E+30
    For i = 0 To UBound(segs)
        li = LayerIndex(segs(i).Layer)
        If li >= 0 Then
            t = segs(i).GetType
            If t = swSketchLINE Then
                gotL(li) = gotL(li) + 1
                Set ln = segs(i)
                Set pt = ln.GetStartPoint2
                a0 = Min2(a0, pt.X): a1 = Max2(a1, pt.X): b0 = Min2(b0, pt.Y): b1 = Max2(b1, pt.Y)
                Set pt = ln.GetEndPoint2
                a0 = Min2(a0, pt.X): a1 = Max2(a1, pt.X): b0 = Min2(b0, pt.Y): b1 = Max2(b1, pt.Y)
            ElseIf t = swSketchARC Then
                gotA(li) = gotA(li) + 1
            End If
        End If
    Next i

    For li = 0 To 4
        Note "layer " & layerNames(li) & ": " & gotL(li) & " lines (drawn " & nLine(li) & "), " & _
             gotA(li) & " arcs (drawn " & nArc(li) & ")"
        If gotL(li) <> nLine(li) Or gotA(li) <> nArc(li) Then
            Fail "layer " & layerNames(li) & " holds " & gotL(li) & " lines and " & gotA(li) & " arcs; drawn " & _
                 nLine(li) & " and " & nArc(li) & "."
        End If
    Next li
    ' the arcs' tops are tracked but not read back: compare lines only
    If Abs(a0 - pxMin) > EXT_TOL Or Abs(a1 - pxMax) > EXT_TOL Or Abs(b0 - pyMin) > EXT_TOL Then
        Fail "the sheet's lines span x " & Fmt(a0) & " .. " & Fmt(a1) & ", y from " & Fmt(b0) & _
             "; drawn to x " & Fmt(pxMin) & " .. " & Fmt(pxMax) & ", y from " & Fmt(pyMin) & "."
    End If
    Note "sheet extents: x " & Fmt(a0) & " .. " & Fmt(a1) & ", y " & Fmt(b0) & " .. " & Fmt(b1) & "; " & nNotes & " notes"

End Sub


Private Function LayerSummary() As String
    Dim i As Long
    For i = 0 To 4
        LayerSummary = LayerSummary & layerNames(i) & " " & nLine(i)
        If nArc(i) > 0 Then LayerSummary = LayerSummary & " + " & nArc(i) & " arcs"
        If i < 4 Then LayerSummary = LayerSummary & ", "
    Next i
    LayerSummary = LayerSummary & "; " & nNotes & " notes"
End Function


Private Sub SaveOutputs()
    Dim errs As Long, warns As Long
    Dim base As String
    On Error Resume Next
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    base = OUT_ROOT & LINE_KEY & "\plant_topology_2d"
    If swModel.Extension.SaveAs(base & ".SLDDRW", 0, 1, Nothing, errs, warns) Then
        Note "saved " & base & ".SLDDRW"
    Else
        Note "WARNING: could not save " & base & ".SLDDRW (error " & errs & "); the drawing is open, unsaved."
    End If
    If swModel.Extension.SaveAs(base & ".pdf", 0, 1, Nothing, errs, warns) Then
        Note "exported " & base & ".pdf"
    Else
        Note "WARNING: could not export " & base & ".pdf (error " & errs & ")."
    End If
    Err.Clear
End Sub


Private Function Min2(ByVal a As Double, ByVal b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function

Private Function Max2(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function


'==================================================================
' Housekeeping
'==================================================================
Private Sub Restore()
    On Error Resume Next
    If Not swSkMgr Is Nothing Then
        swSkMgr.AddToDB = False
        swSkMgr.DisplayWhenAdded = True
    End If
End Sub


' The whole log, to a file: a message box shows about 1000 characters.
Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\plant_topology_2d_build.log"
End Function

Private Sub WriteLog()
    Dim fn As Integer
    On Error Resume Next
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    fn = FreeFile
    Open LogPath() For Output As #fn
    Print #fn, buildLog;
    Close #fn
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "plant_topology_2d", msg
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


' A number for the sheet: a decimal point whatever the locale, and a
' fixed count of decimals ("2.440").
Private Function Num(ByVal v As Double, ByVal dec As Long) As String
    If dec > 0 Then
        Num = Replace(Format(v, "0." & String(dec, "0")), ",", ".")
    Else
        Num = Format(v, "0")
    End If
End Function


' No trailing decimal separator on whole numbers ("65", not "65,").
Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
    If Right(Fmt, 1) = "," Or Right(Fmt, 1) = "." Then Fmt = Left(Fmt, Len(Fmt) - 1)
End Function
