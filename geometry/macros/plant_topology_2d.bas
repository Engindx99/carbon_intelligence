Attribute VB_Name = "plant_topology_2d"
'==================================================================
' Plant topology, 2D  ->  one SolidWorks drawing (SLDDRW + PDF)
'
' A SCHEMATIC, REAL-SCALE 2D drawing of the 2500 t/d pyroprocess,
' written to show the plant's topology: which equipment there is,
' where it stands, and the gas, meal and air paths between it. It is
' NOT a CFD input -- the one exception to CLAUDE.md rule 8.
'
' The plant drawn is TWO IDENTICAL 2500 t/d STRINGS, 5000 t/d in all
' (user decision, 12 Oct 2026): 12 cyclones (each string C5, C4, C3,
' C2 and a twin C1), one ILC calciner whose twin gooseneck feeds the
' two strings' C5s, one kiln, a grate cooler and the kiln hood with
' its tertiary air duct. Each string is the 2500 line itself, so its
' cyclones are the CFD sizes and its risers the published ones. The
' calciner (Y gooseneck), tertiary air duct, kiln and cooler are the
' 5000 t/d line's (PF5000).
'
' It is drawn on an A1 sheet at 1:250, on layers that carry the
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
' the CFD sizes, which every string uses as they are: C1 (cyclone_C1.md),
' C2 = C3 = C4 (cyclone_C4.md, catalog.md deviation), C5 the CFD C4
' x 6.50 / 6.30 (cyclone_C5.md).
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
Const C5_HB As Double = 6.5
Const C5_HC As Double = 7.5317
Const C5_VD As Double = 4.777
Const C5_DD As Double = 0.8357
Const C5_HIN As Double = 3.5079     ' its volute inlet's height; a gooseneck leg runs into it

' Risers [m] -- HFC2500 (published), catalog.md; R_k carries the gas
' from C(k+1) up to C(k). Each string has its own; R1 splits into
' the twin C1, each branch half its area.
Const R1_D As Double = 3.07
Const R2_D As Double = 3.35
Const R3_D As Double = 3.45
Const R4_D As Double = 3.6

' Calciner [m] -- calciner.bas / calciner.md, the 5000 t/d plant's (PF5000)
Const CALC_D        As Double = 6.7404
Const CALC_H        As Double = 30#        ' cone + cylinder
Const CALC_THROAT_D As Double = 3.130088
Const CALC_CONE_DEG As Double = 65#
Const GN_D_SRC      As Double = 3.5        ' a Y gooseneck leg, one 2500 t/d string's published neck; the neck has both legs' area
Const GN_OUT_AT_H   As Double = 0.5        ' legs end at this fraction of CALC_H
Const FEED_BELOW_GN_OUT As Double = 2#     ' meal feed through the wall this far below the legs' ends
Const TA_D          As Double = 2.4393     ' tertiary air duct, derived in calciner.md

' Meal pipes end at the slope of the calciner feed pipes, Fidaros 2007
' (calciner.md): a chute at 60 deg meets an upright riser wall at
' 30 deg, sliding in along it.
Const MEAL_SLOPE_DEG As Double = 60#

' Kiln [m] -- kiln.md (PF5000); cooler -- cooler.md, grate area [m2] (PF5000)
Const KILN_D      As Double = 4.8
Const KILN_L      As Double = 74#
Const KILN_SLOPE  As Double = 0.03
Const COOLER_AREA As Double = 119.6

' SCHEMATIC -- no source; they only lay the plant out.
Const STUB_OVER_VD   As Double = 0.5      ' cyclone gas outlet stub above the roof, x vortex finder D. Was 1.0; halved
                                          ' (user decision, 12 Oct 2026): the tower came out 128 m, the risers
                                          ' (~19.5 m) already match FLS Table 7's 19.4-21.4 m, so the stub was the slack
Const STAGE_GAP      As Double = 4#       ' a cyclone's dust outlet above the top of the stage below [m]
Const ZIG_DX         As Double = 11#      ' a string's outer column (C4, C2) outboard of its inner one (C5, C3) [m]
Const C1_TWIN_GAP    As Double = 4#       ' between the twin C1 barrels; R1 rises in it [m]
Const C5_OVER_TA     As Double = 1.75     ' the C5 dust outlets at least this far over the tertiary air duct [m]
Const GN_TO_C5_GAP   As Double = 1#       ' a gooseneck drop to its C5 barrel; its inlet run spans it [m]
Const EXHAUST_L      As Double = 10#      ' C1 exhaust drawn this far past the string, towards the ID fan [m]
Const RAW_L          As Double = 6#       ' raw meal line drawn from this far outboard [m]
Const MEAL_JOIN_DEG  As Double = 50#      ' the outer C1's meal pipe falls at this slope to join the inner one's [deg]
Const MEAL_ENTRY_UP  As Double = 1.5      ' meal enters a riser's upright this far over the top of its run [m]
Const KILN_AXIS_Z    As Double = 10#      ' kiln inlet axis elevation [m]
Const CHAMBER_MARGIN As Double = 1#       ' kiln inlet chamber and hood: a square this far round the kiln [m]
Const COOLER_W       As Double = 4#       ' grate width [m], the FLS reference cooler's; the length follows from the area
Const COOLER_H       As Double = 4#       ' cooler casing height [m]
Const COOLER_DROP    As Double = 1#       ' cooler top below the kiln shell at discharge [m]
Const MEAL_INTO_CHAMBER As Double = 1#    ' C5 meal lands this far in from the chamber's side [m]
Const MIN_SEG        As Double = 0.05     ' a wall piece beside an opening shorter than this is left out [m]
Const CLINKER_OUT_Z  As Double = 3.5      ' clinker transport drawn this far below ground [m]
Const VENT_IN        As Double = 3#       ' cooler vent this far in from the cooler's end [m]
Const VENT_UP        As Double = 4#       ' vent arrow drawn this far over the cooler roof [m]
Const CLINKER_ON_GRATE As Double = 1#     ' clinker line this far over the cooler floor [m]
Const TA_ARROW_LONG  As Double = 1.15     ' tertiary air arrow this many times the rise from the cooler's mid-height to the hood roof; it runs on up into its duct [-]
Const C4_MEAL_DROP   As Double = 3#       ' C4 meal falls straight this far before turning towards the calciner. Its
                                          ' straight run on, behind C5 and the gooseneck, is flatter than meal flows:
                                          ' a 2D projection, as the C5 meal's [m]
Const CROSS_GAP      As Double = 0.5      ' a meal pipe is broken this far either side of a duct it passes behind [m]
Const MEAL_BEND      As Double = 1#       ' a bend piece this long after a C4 / C5 meal's straight drop, halving its turn [m]
Const C1_MEAL_DROP   As Double = 1#       ' the outer C1's meal falls straight this far before its bend [m]
Const C5_MEAL_DROP   As Double = 0.5      ' C5 meal falls straight this far, ending over the tertiary air duct. Its
                                          ' straight run on to the chamber roof is flatter than meal flows (~35 deg):
                                          ' a 2D projection -- the two strings' C5s stand beside the chamber across the kiln
                                          ' axis, not along it, so the real pipe is shorter and steeper [m]
Const FEED_LOWER     As Double = 3#       ' C4 meal drawn into the calciner this far below calciner.bas's feed [m]
Const KILN_FLOW_OFF  As Double = 1#       ' kiln gas and material lines this far either side of the kiln axis [m]
Const PRIMARY_AIR_L  As Double = 2#       ' primary air: a short arrow this long into the hood's front wall [m]
Const SEC_AIR_DX     As Double = 1.5      ' secondary air rises from the cooler this far in from the kiln's end [m]

' Sheet [m on paper]: A1 landscape at 1:300
Const SHEET_SCALE As Double = 300#
Const PAPER_W     As Double = 0.841
Const PAPER_H     As Double = 0.594
Const X0          As Double = 0.2         ' where model x = 0 falls on the sheet
Const RULER_X     As Double = 0.04        ' the elevation ruler, inside the frame
Const Y0          As Double = 0.06        ' where model z = 0 falls on the sheet
Const TEXT_H      As Double = 0.0035      ' text height
Const ARROW_L     As Double = 0.004       ' arrow head length
Const CAP_H       As Double = 0.002       ' caption text height in the title block
' Frame, ISO 5457 for A1: 20 mm left, 10 mm elsewhere; 12 x 8 zones
Const FR_X0 As Double = 0.02, FR_X1 As Double = 0.831, FR_Y0 As Double = 0.01, FR_Y1 As Double = 0.584
' The right-hand column: legend, notes, equipment list, revisions, title block
Const COL_X0 As Double = 0.651
Const LEVEL_X As Double = 33#             ' model x of the elevation marks, right of the right string [m]

' Layers: name, colour (RGB), line weight
Const L_EQUIP As String = "EKIPMAN"
Const L_GAS   As String = "GAZ"
Const L_MEAL  As String = "FARIN"
Const L_AIR   As String = "HAVA"
Const L_TEXT  As String = "YAZI"
Const L_FRAME As String = "CERCEVE"
Const L_AXIS  As String = "EKSEN"
Const L_DIM   As String = "OLCU"
Const LAYER_N As Long = 8

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
Dim kBranch As Double                     ' R1's branch to one twin C1, half its area: 1/sqrt 2 of its D
Dim aCh As Double, zCh0 As Double         ' chamber: |x| <= aCh, z from zCh0, 2 aCh tall; the hood the same square
Dim rampTan As Double                     ' slope of the chamber's floor, a ramp from the kiln's lower lip to its far top corner
Dim rCalc As Double, rThroat As Double, hCone As Double
Dim zThroat As Double, zConeTop As Double, zCalcRoof As Double
Dim rGn As Double, rNeck As Double, xGnStart As Double, rGnBend As Double
Dim xLeg As Double, zGnTop As Double, zLeg As Double
Dim zFeed As Double                       ' C4 meal reaches the calciner wall here
Dim kAlpha As Double
Dim kAx As Double, kAz As Double, kBx As Double, kBz As Double
Dim coolL As Double, zCool0 As Double, zHood0 As Double
Dim rTA As Double, zTA As Double
Dim zDust(1 To 5) As Double, zRoof(1 To 5) As Double, zTop(1 To 5) As Double
Dim zIn(1 To 5) As Double                 ' gas inlet centre, its top at the roof
Dim xInner As Double                      ' |x| of a string's inner column (C5, C3)
' Outlines a meal pipe passes behind, so it can be broken there: every
' duct's edges, closed by unseen edges across its open ends, and C5's
' section, closed likewise. Each is a closed outline, so every
' crossing toggles a pipe in / out.
Dim deXa(1 To 800) As Double, deZa(1 To 800) As Double, deXb(1 To 800) As Double, deZb(1 To 800) As Double
Dim nDE As Long
Dim ductJoinStart As Boolean, ductJoinEnd As Boolean   ' the next Duct runs on from / into another outline

' drawing state
Dim curLayer As String
Dim layerNames(LAYER_N - 1) As String
Dim nLine(LAYER_N - 1) As Long, nArc(LAYER_N - 1) As Long, nNotes As Long
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
    MsgBox "Plant topology 2D built and verified: two 2500 t/d strings, 12 cyclones, A1 at 1:" & Fmt(SHEET_SCALE) & _
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

    kBranch = Sqr(0.5)

    ' Kiln inlet chamber round the kiln's inlet end: a square, the kiln
    ' plus a margin (schematic, kiln_inlet_chamber.md has no size)
    aCh = 0.5 * KILN_D + CHAMBER_MARGIN
    zCh0 = KILN_AXIS_Z - aCh
    kAlpha = Atn(KILN_SLOPE)

    ' The calciner stands on the chamber.
    rCalc = 0.5 * CALC_D
    rThroat = 0.5 * CALC_THROAT_D
    hCone = (rCalc - rThroat) * Tan(CALC_CONE_DEG * PI / 180#)
    zThroat = zCh0 + 2# * aCh
    zConeTop = zThroat + CALC_THROAT_D + hCone
    zCalcRoof = zThroat + CALC_THROAT_D + CALC_H

    ' Its Y gooseneck exactly as calciner.bas builds it: one neck of
    ' both legs' area on the axis, 1.25 neck D up; at its top each
    ' leg's disc inside it, touching its rim on its own side, then a
    ' 1.5 leg D bend outward and down beside the C5s.
    rGn = 0.5 * GN_D_SRC
    rNeck = rGn * Sqr(2#)
    xGnStart = rNeck - rGn
    rGnBend = 1.5 * 2# * rGn
    xLeg = xGnStart + 2# * rGnBend
    zGnTop = zCalcRoof + 1.25 * 2# * rNeck
    zLeg = zThroat + CALC_THROAT_D + GN_OUT_AT_H * CALC_H
    zFeed = zLeg - FEED_BELOW_GN_OUT - FEED_LOWER

    ' The tertiary air duct from the hood to the calciner, its lower
    ' edge on the top of the cone (schematic -- calciner.bas step 6
    ' will set its own).
    rTA = 0.5 * TA_D
    zTA = zConeTop + rTA

    ' Each string: C5 GN_TO_C5_GAP outboard of its leg, its roof where
    ' the leg ends -- unless that hangs it into the tertiary air duct:
    ' the full-size C5 is 14 m tall, so it then stands C5_OVER_TA over
    ' the duct and the leg ends higher. The leg turns into the C5 at
    ' its inlet. Each stage's dust outlet STAGE_GAP over the top of the
    ' stage below.
    CycDims 5, d, hb, hc, vd, dd
    xInner = xLeg + rGn + GN_TO_C5_GAP + 0.5 * d
    zDust(5) = Max2(zLeg - (hb + hc), zTA + rTA + C5_OVER_TA)

    ' The kiln runs out of the chamber's +x side, falling KILN_SLOPE
    ' towards the cooler. The chamber has no flat floor for meal to lie
    ' on: a ramp rises from the kiln's lower lip to the chamber's far
    ' top corner, so meal and spillage slide into the kiln.
    kAx = aCh: kAz = KILN_AXIS_Z
    rampTan = (zCh0 + 2# * aCh - kAz + 0.5 * KILN_D / Cos(kAlpha)) / (2# * aCh)
    kBx = kAx + KILN_L * Cos(kAlpha)
    kBz = kAz - KILN_L * Sin(kAlpha)

    top = zDust(5) + CycHeight(5)
    For s = 4 To 1 Step -1
        zDust(s) = top + STAGE_GAP
        top = zDust(s) + CycHeight(s)
    Next s
    For s = 1 To 5
        CycDims s, d, hb, hc, vd, dd
        zRoof(s) = zDust(s) + hc + hb
        zTop(s) = zDust(s) + CycHeight(s)
        ' Every cyclone takes its gas at the roof, as its CFD solid does
        ' (C1's slot, the C2-C5 volute run down from the roof): the
        ' riser's or gooseneck leg's top wall flush with it.
        If s = 5 Then
            zIn(s) = zRoof(s) - rGn
        ElseIf s = 1 Then
            zIn(s) = zRoof(s) - kBranch * 0.5 * RiserD(1)
        Else
            zIn(s) = zRoof(s) - 0.5 * RiserD(s)
        End If
    Next s

    ' Cooler under the kiln's discharge, running on in +x; the hood,
    ' a mirror of the chamber, on it round the kiln's end.
    coolL = COOLER_AREA / COOLER_W
    zCool0 = kBz - 0.5 * KILN_D - COOLER_DROP - COOLER_H
    zHood0 = kBz - aCh

End Sub


' Cyclone dimensions by stage, the same in both strings (C2 and C3
' are C4).
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


' Riser diameter, the same in both strings.
Private Function RiserD(ByVal k As Long) As Double
    Select Case k
        Case 1: RiserD = R1_D
        Case 2: RiserD = R2_D
        Case 3: RiserD = R3_D
        Case 4: RiserD = R4_D
    End Select
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
    If rNeck >= rCalc Then Fail "the gooseneck neck is wider than the calciner roof."
    ' Each leg's run fits the C5 inlet it enters
    If 2# * rGn > C5_HIN Then Fail "the gooseneck legs (D " & Fmt(2# * rGn) & _
        ") are taller than the C5 inlet (" & Fmt(C5_HIN) & ") they enter."
    ' The C4 meal reaches the calciner's cylinder, over the cone
    If zFeed <= zConeTop Then Fail "the C4 meal would reach the calciner below its cylinder. Lower FEED_LOWER."
    ' The tertiary air duct runs under the C5s and over the chamber and kiln
    If zTA + rTA >= zDust(5) Then Fail "the tertiary air duct runs into the C5s."
    ' and under the C5 meal's straight drop
    If zDust(5) - C5_MEAL_DROP <= zTA + rTA + 0.3 Then Fail "the C5 meal's straight drop ends in the tertiary air duct."
    If zTA - rTA <= zThroat Or zTA - rTA <= kAz + 0.5 * KILN_D Then
        Fail "the tertiary air duct runs into the kiln or the inlet chamber."
    End If
    ' The cooler above ground, the hood on it
    If zCool0 <= 0# Then Fail "the cooler floor is at z = " & Fmt(zCool0) & " m, below ground. Raise KILN_AXIS_Z."
    If Abs(zHood0 - (zCool0 + COOLER_H)) > 0.001 Then Fail "the kiln hood does not sit on the cooler."
    If aCh <= rThroat Then Fail "the kiln inlet chamber is narrower than the calciner throat."
    ' its ramp no flatter than meal's angle of repose, ~40 deg
    If Atn(rampTan) * 180# / PI < 39# Then
        Fail "the kiln inlet chamber's ramp is " & Fmt(Atn(rampTan) * 180# / PI) & " deg, too flat for meal to slide."
    End If
    ' The kiln's gas and material lines inside its shell
    If KILN_FLOW_OFF >= 0.5 * KILN_D Then Fail "KILN_FLOW_OFF puts the kiln's flow lines outside its shell."
    ' The plant fits the sheet, left of the legend
    If X0 + (-xm - 0.5 * ZIG_DX - EXHAUST_L) / SHEET_SCALE < RULER_X + 0.01 Or _
       X0 + (kBx + coolL) / SHEET_SCALE > COL_X0 - 0.01 Or Y0 + (zTop(1) + 13#) / SHEET_SCALE > FR_Y1 - 0.005 Then
        Fail "the plant does not fit the A1 sheet at 1:" & Fmt(SHEET_SCALE) & "."
    End If

    Note "kiln inlet chamber: |x| <= " & Fmt(aCh) & " m, z " & Fmt(zCh0) & " .. " & Fmt(zCh0 + 2# * aCh)
    Note "calciner: z " & Fmt(zThroat) & " .. " & Fmt(zCalcRoof) & "; gooseneck neck D " & Fmt(2# * rNeck) & ", legs from x +-" & Fmt(xGnStart) & _
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
    nDE = 0: ductJoinStart = False: ductJoinEnd = False

    DrawPlant
    phase = "drawing the centre lines, elevations and grid"
    DrawAxes
    DrawLevels
    DrawGrid
    phase = "drawing the frame, legend and tables"
    DrawFrame
    DrawLegend
    DrawEquipmentList
    DrawRevisions
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
    layerNames(3) = L_AIR: layerNames(4) = L_TEXT: layerNames(5) = L_FRAME
    layerNames(6) = L_AXIS: layerNames(7) = L_DIM

    Set lm = swModel.GetLayerManager
    If lm Is Nothing Then Fail "the drawing has no layer manager."
    AddOneLayer lm, L_EQUIP, "equipment outlines", RGB(0, 0, 0), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_GAS, "hot gas and air", RGB(210, 0, 0), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_MEAL, "meal path", RGB(200, 150, 0), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_AIR, "cold air", RGB(30, 90, 220), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_TEXT, "labels, legend, tables", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_FRAME, "frame, title block, table borders", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THICK2
    AddOneLayer lm, L_AXIS, "centre lines, grid lines", RGB(0, 0, 0), swLineCENTER, swLW_THIN
    AddOneLayer lm, L_DIM, "dimensions, elevation marks, grid bubbles", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THIN
    Note "layers: " & L_EQUIP & " (black, normal), " & L_GAS & " (red), " & L_MEAL & " (yellow), " & _
         L_AIR & " (blue), " & L_TEXT & " (black, thin), " & L_FRAME & " (black, thick), " & _
         L_AXIS & " (black, centre line), " & L_DIM & " (black, thin)"

End Sub


' One layer, checked by reading it back -- AddLayer's return value is
' not relied on.
Private Sub AddOneLayer(lm As Object, ByVal name As String, ByVal desc As String, ByVal colour As Long, _
                        ByVal style As Long, ByVal weight As Long)
    Dim ret As Variant
    ret = lm.AddLayer(name, desc, colour, style, weight)
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
    For i = 0 To LAYER_N - 1
        If layerNames(i) = name Then LayerIndex = i
    Next i
End Function


Private Sub DrawPlant()

    Dim k As Long, s As Long, up As Long
    Dim sd As Double, xi As Double, xo As Double, xm As Double, xw As Double, xs0 As Double
    Dim r1 As Double, dc1 As Double, c1in As Double, c1out As Double
    Dim r As Double, rb As Double, zh As Double, zx As Double, xe As Double
    Dim wl As Double, wr As Double, ls As Double
    Dim zJoin As Double, xc As Double, zc As Double, kOff As Double, bA As Double
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
    ' calciner throat in its roof; its floor a ramp from the kiln's
    ' lower lip up to the roof
    LineM aCh, kAz - kSh, -aCh, zTopCh
    Seg aCh, kAz + kSh, aCh, zTopCh
    Seg aCh, zTopCh, rThroat, zTopCh
    Seg -rThroat, zTopCh, -aCh, zTopCh
    ' calciner: no floor (the throat), the tertiary air port in its +x
    ' wall over the cone, the two gooseneck rises in its roof
    PolyM Array(rThroat, zThroat, rThroat, zThroat + CALC_THROAT_D, rCalc, zConeTop)
    Seg rCalc, zConeTop + TA_D, rCalc, zCalcRoof
    Seg rCalc, zCalcRoof, rNeck, zCalcRoof
    Seg -rNeck, zCalcRoof, -rCalc, zCalcRoof
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
        CycloneOutline 5, col(5)
        For s = 4 To 2 Step -1
            Cyclone s, col(s), Sgn(xm - col(s)), 0.5 * RiserD(s)
        Next s
        Cyclone 1, xm - sd * dc1, sd, kBranch * 0.5 * RiserD(1)
        Cyclone 1, xm + sd * dc1, -sd, kBranch * 0.5 * RiserD(1)
    Next k

    '=== gas ==============================================================
    phase = "drawing the gas path"
    UseLayer L_GAS
    ' Through the kiln, above its axis, from the burner end to the inlet
    ' (the material runs the other way below it)
    kOff = KILN_FLOW_OFF / Cos(kAlpha)
    ' (it turns up to the calciner axis 1 m over the chamber's ramp)
    zx = Max2(kAz + kOff, kAz - kSh + aCh * rampTan + 1#)
    PathL "gas: kiln (burner end -> inlet)", Array(kBx, kBz + kOff, kAx, kAz + kOff, 0#, zx)
    PathL "gas: inlet chamber -> calciner", Array(0#, zx, 0#, zCalcRoof - 2#)
    ' The tertiary air rises straight out of the cooler through the hood,
    ' marked as the secondary air is, into its duct on the hood's top;
    ' hot, so on the gas layer as the secondary air. Drawn before the
    ' meal pipes, which are broken where they pass behind it
    zc = zCool0 + 0.5 * COOLER_H + TA_ARROW_LONG * (zHood0 + 2# * aCh - zCool0 - 0.5 * COOLER_H)
    If zc >= zTA - rTA Then Fail "the tertiary air arrow runs up past its duct's turn. Lower TA_ARROW_LONG."
    PathOut "gas: cooler -> hood (tertiary air)", Array(kBx + aCh, zCool0 + 0.5 * COOLER_H, kBx + aCh, zc)
    Duct "gas: hood -> tertiary air duct -> calciner", Array(kBx + aCh, zHood0 + 2# * aCh, _
         kBx + aCh, zTA, rCalc, zTA), TA_D, False

    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        c1in = xm - sd * dc1: c1out = xm + sd * dc1

        '--- the Y gooseneck, as calciner.bas: the neck (once), then each
        '    leg's bend, drop, and across into the C5 at its inlet ------
        If k = 0 Then
            ductJoinEnd = True                        ' the neck runs into the bends
            Duct "gas: calciner -> gooseneck neck", Array(0#, zCalcRoof, 0#, zGnTop), 2# * rNeck, False
        End If
        YBend sd
        ductJoinStart = True                          ' the drop runs on from the bend
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
        rb = kBranch * r
        zh = zTop(2) + r
        RunOverStub 2, xo, xm, r, xn
        ductJoinEnd = True                            ' R1 runs up into its split
        Duct "gas: C2 " & side & " -> R1", Array(xn, zh, xm, zh, xm, zIn(1) - rb), 2# * r, False
        wl = Min2(c1in, c1out) + r1: wr = Max2(c1in, c1out) - r1
        DuctEdge wl, zIn(1) + rb, wr, zIn(1) + rb
        DuctEdge wl, zIn(1) - rb, xm - r, zIn(1) - rb
        DuctEdge xm + r, zIn(1) - rb, wr, zIn(1) - rb
        UnseenEdge wl, zIn(1) - rb, wl, zIn(1) + rb   ' the branches open into the C1 barrels
        UnseenEdge wr, zIn(1) - rb, wr, zIn(1) + rb
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
        ' the inner C1's pipe instead: as C4's, straight down, a bend piece
        ' along the bisector of its turn, then at MEAL_JOIN_DEG.
        bA = 0.5 * (90# + MEAL_JOIN_DEG) * PI / 180#
        xe = c1out - sd * MEAL_BEND * Cos(bA)
        zc = zDust(1) - C1_MEAL_DROP - MEAL_BEND * Sin(bA)
        zJoin = zc - Abs(c1in - xe) * Tan(MEAL_JOIN_DEG * PI / 180#)
        If zJoin <= MealIntoRiser("meal: C1 " & side & " -> R2", c1in, zDust(1), xm, zEnt(3), 2) Then
            Fail "the outer C1's meal would join the inner one's below its turn. Lower MEAL_JOIN_DEG."
        End If
        PathM "meal: C1 " & side & " (second) -> the first C1's meal pipe", Array(c1out, zDust(1), _
              c1out, zDust(1) - C1_MEAL_DROP, xe, zc, c1in, zJoin)
        MealIntoRiser "meal: C2 " & side & " -> R3", col(2), zDust(2), xm, zEnt(4), 3
        MealIntoRiser "meal: C3 " & side & " -> R4", col(3), zDust(3), xm, zEnt(5), 4
        ' C4: straight down, a bend piece, then straight into the calciner,
        ' behind C5 and the gooseneck (broken there)
        C4MealBend sd, xe, zc
        PathM "meal: C4 " & side & " -> calciner", Array(col(4), zDust(4), col(4), zDust(4) - C4_MEAL_DROP, _
              xe, zc, sd * rCalc, zFeed)
        ' C5: as C4 -- straight down, a bend piece, straight to the
        ' chamber roof
        BendEnd xi, zDust(5) - C5_MEAL_DROP, sd * (aCh - MEAL_INTO_CHAMBER), zCh0 + 2# * aCh, xe, zc
        PathM "meal: C5 " & side & " -> kiln inlet chamber", Array(xi, zDust(5), xi, zDust(5) - C5_MEAL_DROP, _
              xe, zc, sd * (aCh - MEAL_INTO_CHAMBER), zCh0 + 2# * aCh)
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
    PathL "meal: inlet chamber -> kiln -> grate cooler (clinker)", Array(kAx, kAz - kOff, _
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
    ' The cooler's excess air, still hot, out of its roof near its end
    PathOut "gas: grate cooler -> cooler vent", Array(kBx + coolL - VENT_IN, zCool0 + 0.5 * COOLER_H, _
          kBx + coolL - VENT_IN, zCool0 + COOLER_H + VENT_UP)

    '=== ground and labels ==================================================
    phase = "labelling"
    UseLayer L_TEXT
    DrawRuler
    LabelM -aCh, zCh0 - 1#, "KIC kiln inlet chamber", 0#
    LabelM -3.5, zGnTop + rGnBend + rGn + 3#, "CAL ILC calciner", 0#
    LabelM -(xGnStart + rGnBend) - 0.5, zGnTop + rGnBend + rGn + 1.2, "GN", 0#
    LabelM xGnStart + rGnBend - 0.5, zGnTop + rGnBend + rGn + 1.2, "GN", 0#
    LabelM 20#, kAz + 3.5, "KLN rotary kiln D" & Num(KILN_D, 3) & " x " & Num(KILN_L, 0) & " m", 0#
    LabelM kBx + 0.3 * coolL, zCool0 + 0.75 * COOLER_H, "CLR grate cooler", 0#
    LabelM kBx + coolL - VENT_IN - 0.3 * TEXT_H * 14 * SHEET_SCALE, zCool0 + COOLER_H + VENT_UP + 1.1, _
           "to cooler vent", 0#
    LabelM kBx + coolL - 1.5 - 0.6 * TEXT_H * 20 * SHEET_SCALE, -CLINKER_OUT_Z + 2#, "to clinker transport", 0#
    LabelM kBx + 2# * aCh + 1#, zHood0 + 2# * aCh, "HD kiln hood", 0#
    LabelM kBx + 2# * aCh + 0.5, kBz + kOff - 0.3, "primary air", 0#
    ' inside the kiln, between its gas and its clinker: the kiln gas
    ' there is the secondary air the burner has fired
    LabelM kBx - 8#, kBz + 0.75, "secondary air", 0#
    ' under the duct: over it, it ran into the C5 dust outlet's elevation mark
    LabelM 42#, zTA - rTA - 0.8, "TAD tertiary air D" & Num(TA_D, 3), 0#
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
    DuctEdge xf, zTop(s), xf, zTop(s) + 2# * r
    DuctEdge xf, zTop(s) + 2# * r, xn, zTop(s) + 2# * r
    UnseenEdge xf, zTop(s), xn, zTop(s)           ' the open stub top under it
    ductJoinStart = True                          ' the riser's duct runs on from here
End Sub


' The end of the C4 meal's bend piece on side sd: MEAL_BEND along
' the bisector of its turn from straight down to the line on to the
' calciner feed.
Private Sub C4MealBend(ByVal sd As Double, ByRef xb As Double, ByRef zb As Double)
    BendEnd sd * (xInner + ZIG_DX), zDust(4) - C4_MEAL_DROP, sd * rCalc, zFeed, xb, zb
End Sub


' The end of a meal pipe's bend piece: from the foot (xs, zx) of its
' straight drop, MEAL_BEND along the bisector of the turn from straight
' down to the line on to its target (xt, zt).
Private Sub BendEnd(ByVal xs As Double, ByVal zx As Double, ByVal xt As Double, ByVal zt As Double, _
                    ByRef xb As Double, ByRef zb As Double)
    Dim ux As Double, uz As Double, L As Double
    ux = xt - xs: uz = zt - zx
    L = Sqr(ux * ux + uz * uz)
    ux = ux / L: uz = uz / L - 1#
    L = Sqr(ux * ux + uz * uz)
    xb = xs + MEAL_BEND * ux / L
    zb = zx + MEAL_BEND * uz / L
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
    PathM what, Array(xs, zs, xs, zb, xw, ze)
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
' from 0 to the first 10 m over the tower top, with a tick and its
' elevation every 10 m.
Private Sub DrawRuler()
    Dim k As Long, nk As Long
    Dim xr As Double, y As Double
    xr = (RULER_X - X0) * SHEET_SCALE
    nk = Int(zTop(1) / 10#) + 1
    LineM xr, 0#, kBx + coolL + 1.4, 0#
    LineM xr, 0#, xr, 10# * nk
    For k = 0 To nk
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


' A duct's edge: drawn, and kept so a meal pipe crossing it later can
' be broken there.
Private Sub DuctEdge(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    LineM xa, za, xb, zb
    If nDE >= UBound(deXa) Then Fail "too many duct edges for the crossing check."
    nDE = nDE + 1
    deXa(nDE) = xa: deZa(nDE) = za: deXb(nDE) = xb: deZb(nDE) = zb
End Sub


' An unseen edge closing an outline across an opening: kept for the
' crossing check, not drawn.
Private Sub UnseenEdge(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    If nDE >= UBound(deXa) Then Fail "too many duct edges for the crossing check."
    nDE = nDE + 1
    deXa(nDE) = xa: deZa(nDE) = za: deXb(nDE) = xb: deZb(nDE) = zb
End Sub


' A cyclone's section, closed, for the crossing check only (the C4
' meal passes behind C5).
Private Sub CycloneOutline(ByVal s As Long, ByVal xc As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim px(9) As Double, pz(9) As Double
    Dim i As Long
    CycDims s, d, hb, hc, vd, dd
    px(0) = xc + 0.5 * dd: pz(0) = zDust(s)
    px(1) = xc + 0.5 * d:  pz(1) = zDust(s) + hc
    px(2) = xc + 0.5 * d:  pz(2) = zRoof(s)
    px(3) = xc + 0.5 * vd: pz(3) = zRoof(s)
    px(4) = xc + 0.5 * vd: pz(4) = zTop(s)
    For i = 0 To 4
        px(9 - i) = 2# * xc - px(i): pz(9 - i) = pz(i)
    Next i
    For i = 0 To 9
        UnseenEdge px(i), pz(i), px((i + 1) Mod 10), pz((i + 1) Mod 10)
    Next i
End Sub


' A meal pipe along its axis, broken where it passes behind a duct: on
' each run, every duct edge it crosses toggles it in / out of a duct;
' the parts inside, and CROSS_GAP either side, are not drawn. An edge
' it only ends on (a pipe entering a riser) does not count. The arrow
' rides on the longest part drawn.
Private Sub PathM(ByVal what As String, pts As Variant)
    Dim n As Long, i As Long, j As Long, m As Long, q As Long, nb As Long
    Dim xa As Double, za As Double, dx As Double, dz As Double, L As Double
    Dim ex As Double, ez As Double, den As Double, t As Double, u As Double, tg As Double
    Dim t0 As Double, t1 As Double, bl As Double, bx As Double, bz As Double, bdx As Double, bdz As Double
    Dim ts() As Double
    Dim inDuct As Boolean, skip As Boolean
    n = (UBound(pts) + 1) \ 2
    If n < 2 Then Fail what & " has fewer than two points."
    bl = -1#
    For i = 0 To n - 2
        xa = pts(2 * i): za = pts(2 * i + 1)
        dx = pts(2 * i + 2) - xa: dz = pts(2 * i + 3) - za
        L = Sqr(dx * dx + dz * dz)
        If L <= 0# Then Fail what & ": two points coincide."
        ReDim ts(0 To nDE)
        m = 0
        For j = 1 To nDE
            ex = deXb(j) - deXa(j): ez = deZb(j) - deZa(j)
            den = dx * ez - dz * ex
            If Abs(den) > 1E-12 Then
                t = ((deXa(j) - xa) * ez - (deZa(j) - za) * ex) / den
                u = ((deXa(j) - xa) * dz - (deZa(j) - za) * dx) / den
                If t > 0.000001 And t < 0.999999 And u >= -0.000000001 And u <= 1.000000001 Then
                    ts(m) = t: m = m + 1
                End If
            End If
        Next j
        For j = 1 To m - 1                    ' sort the crossings along the run
            t = ts(j): q = j - 1
            Do While q >= 0
                If ts(q) <= t Then Exit Do
                ts(q + 1) = ts(q): q = q - 1
            Loop
            ts(q + 1) = t
        Next j
        nb = nb + m \ 2
        tg = CROSS_GAP / L
        ' each crossing toggles in / out of a duct; the state carries on
        ' to the next run. Draw the outside parts.
        t0 = 0#
        For j = 0 To m
            If j < m Then t1 = ts(j) - tg Else t1 = 1#
            ' (a sliver shorter than CROSS_GAP running into a duct is left
            ' out, unless it is where the pipe starts)
            skip = (j < m And (t1 - t0) * L < CROSS_GAP And Not (i = 0 And t0 = 0#))
            If Not inDuct And t1 > t0 + 0.000001 And Not skip Then
                LineM xa + t0 * dx, za + t0 * dz, xa + t1 * dx, za + t1 * dz
                If (t1 - t0) * L > bl Then
                    bl = (t1 - t0) * L
                    bx = xa + 0.5 * (t0 + t1) * dx: bz = za + 0.5 * (t0 + t1) * dz
                    bdx = dx / L: bdz = dz / L
                End If
            End If
            If j < m Then
                inDuct = Not inDuct
                If Not inDuct Then t0 = ts(j) + tg
            End If
        Next j
    Next i
    If inDuct Then Fail what & " ends behind a duct."
    If bl > 0# Then ArrowAt bx, bz, bdx, bdz
    Note "-- " & what & IIf(nb > 0, " (broken behind " & nb & " duct crossings)", "")
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
    Dim e0x(1) As Double, e0z(1) As Double, e1x(1) As Double, e1z(1) As Double

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
            DuctEdge ex(j), ez(j), ex(j + 1), ez(j + 1)
        Next j
        e0x(sg) = ex(0): e0z(sg) = ez(0)
        e1x(sg) = ex(n - 1): e1z(sg) = ez(n - 1)
    Next sg
    If capStart Then
        DuctEdge e0x(0), e0z(0), e0x(1), e0z(1)
    ElseIf Not ductJoinStart Then
        UnseenEdge e0x(0), e0z(0), e0x(1), e0z(1)
    End If
    If Not ductJoinEnd Then UnseenEdge e1x(0), e1z(0), e1x(1), e1z(1)
    ductJoinStart = False: ductJoinEnd = False
    ArrowOnLongest pts
    Note "-- " & what & " (D " & Fmt(w) & ")"

End Sub


' One leg's bend of the Y gooseneck on side sd, at its true width,
' about (sd (xGnStart + rGnBend), zGnTop): its inner wall a half circle
' from the neck's wall over to the drop; its outer wall from where it
' crosses the other leg's, on the axis -- the Y's crotch -- over to
' the drop.
Private Sub YBend(ByVal sd As Double)
    Dim cx As Double, ro As Double, zc As Double
    Dim a As Double, b As Double, c As Double, d As Double, m As Double, q As Double
    Dim i As Long
    cx = sd * (xGnStart + rGnBend)
    ro = rGnBend + rGn
    zc = zGnTop + Sqr(ro * ro - cx * cx)
    i = LayerIndex(curLayer)
    P cx - rGnBend + rGn, zGnTop, a, b
    P cx + rGnBend - rGn, zGnTop, c, d
    P cx, zGnTop + rGnBend - rGn, m, q
    If swSkMgr.Create3PointArc(a, b, 0#, c, d, 0#, m, q, 0#) Is Nothing Then
        Fail "Create3PointArc failed on the gooseneck bend's inner wall."
    End If
    nArc(i) = nArc(i) + 1
    Track a, b: Track c, d: Track m, q
    P 0#, zc, a, b
    P cx + sd * ro, zGnTop, c, d
    P cx, zGnTop + ro, m, q
    If swSkMgr.Create3PointArc(a, b, 0#, c, d, 0#, m, q, 0#) Is Nothing Then
        Fail "Create3PointArc failed on the gooseneck bend's outer wall."
    End If
    nArc(i) = nArc(i) + 1
    Track a, b: Track c, d: Track m, q
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
    LabelPH px, py, txt, TEXT_H
End Sub


' A note of text height h, its top left at (px, py) on the sheet.
Private Sub LabelPH(ByVal px As Double, ByVal py As Double, ByVal txt As String, ByVal h As Double)
    Dim nt As Object, an As Object, tf As Object
    On Error Resume Next
    swModel.ClearSelection2 True
    Set nt = swModel.InsertNote(txt)
    If Not nt Is Nothing Then
        Set an = nt.GetAnnotation
        an.SetPosition2 px, py, 0#
        Set tf = an.GetTextFormat(0)
        tf.CharHeight = h
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
    y = y - 0.012
    UseLayer L_MEAL: LineP x, y, x + 0.006, y: LineP x + 0.014, y, x + 0.02, y
    UseLayer L_GAS:  LineP x + 0.0085, y - 0.003, x + 0.0085, y + 0.003
    LineP x + 0.0115, y - 0.003, x + 0.0115, y + 0.003
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "meal pipe broken where it passes behind a duct"

    y = y - 0.02
    LabelP x, y, "NOTES"
    LabelP x, y - 0.006, "1. Elevations above ground, m; diameters internal, m."
    LabelP x, y - 0.012, "2. 5000 t/d: two identical 2500 t/d strings on one calciner and"
    LabelP x, y - 0.018, "   kiln; cyclones at the CFD sizes; see the equipment list."
    LabelP x, y - 0.024, "3. Schematic: kiln inlet chamber size has no source; meal pipes"
    LabelP x, y - 0.030, "   in 2D projection - C4, C5 pipes and the ramp are steeper in 3D."
    LabelP x, y - 0.036, "4. Not a CFD input; one string is solved, the other is its copy."

    ' 10 m scale bar
    y = y - 0.057
    LineP x, y, x + 10# / SHEET_SCALE, y
    For k = 0 To 2
        LineP x + k * 5# / SHEET_SCALE, y - 0.0015, x + k * 5# / SHEET_SCALE, y + 0.0015
    Next k
    LabelP x - 0.001, y - 0.003, "0"
    LabelP x + 10# / SHEET_SCALE - 0.002, y - 0.003, "10 m"

End Sub


Private Sub DrawTitle()

    ' ISO 7200 title block, 180 mm wide in the frame's bottom right
    Dim bx0 As Double, bx1 As Double
    bx0 = COL_X0: bx1 = FR_X1
    UseLayer L_FRAME
    RectP bx0, FR_Y0, bx1, 0.055
    UseLayer L_TEXT
    LineP bx0, 0.046, bx1, 0.046
    LineP bx0, 0.037, bx1, 0.037
    LineP bx0, 0.019, bx1, 0.019
    LineP 0.771, 0.028, bx1, 0.028
    LineP 0.711, 0.037, 0.711, 0.055
    LineP 0.771, FR_Y0, 0.771, 0.055
    LineP 0.711, FR_Y0, 0.711, 0.019
    LineP 0.781, 0.019, 0.781, 0.028
    LineP 0.806, 0.019, 0.806, 0.028
    LineP 0.816, 0.019, 0.816, 0.028

    Cell bx0, 0.055, "Created by", ""
    Cell 0.711, 0.055, "Approved by", ""
    Cell 0.771, 0.055, "Document type", "Process layout"
    Cell bx0, 0.046, "Responsible department", ""
    Cell 0.711, 0.046, "Technical reference", "plant_topology_2d.bas"
    Cell 0.771, 0.046, "Document status", "draft, schematic"
    LabelPH bx0 + 0.0015, 0.0362, "Title, supplementary title", CAP_H
    LabelP bx0 + 0.0015, 0.0335, "PYROPROCESS TOPOLOGY"
    LabelPH bx0 + 0.0015, 0.0283, "5000 t/d: two identical " & LINE_KEY & " t/d 5-stage preheater strings,", 0.0025
    LabelPH bx0 + 0.0015, 0.0248, "ILC calciner, rotary kiln, grate cooler - elevation", 0.0025
    Cell 0.771, 0.037, "Identification number", ""
    CellS 0.771, 0.028, "Rev.", ""
    CellS 0.781, 0.028, "Date of issue", Format(Date, "yyyy-mm-dd")
    CellS 0.806, 0.028, "Lang.", "EN"
    CellS 0.816, 0.028, "Sheet", "1/1"
    Cell bx0, 0.019, "Scale", "1:" & Num(SHEET_SCALE, 0) & " (A1)"
    Cell 0.711, 0.019, "Unit", "m"
    Cell 0.771, 0.019, "Source", "plant_topology.md"

End Sub


' A title block cell: its caption small at the top, its value under it.
Private Sub Cell(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.0015, yTop - 0.0008, cap, CAP_H
    If v <> "" Then LabelP x + 0.0015, yTop - 0.0038, v
End Sub


' A narrow cell: caption and value both small.
Private Sub CellS(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.001, yTop - 0.0008, cap, CAP_H * 0.85
    If v <> "" Then LabelPH x + 0.001, yTop - 0.004, v, 0.0025
End Sub


' The revision table over the title block: a header and two empty rows.
Private Sub DrawRevisions()
    UseLayer L_FRAME
    RectP COL_X0, 0.058, FR_X1, 0.076
    UseLayer L_TEXT
    LineP COL_X0, 0.07, FR_X1, 0.07
    LineP COL_X0, 0.064, FR_X1, 0.064
    LineP 0.666, 0.058, 0.666, 0.076
    LineP 0.771, 0.058, 0.771, 0.076
    LineP 0.801, 0.058, 0.801, 0.076
    LabelPH COL_X0 + 0.0015, 0.0745, "Rev.", 0.0025
    LabelPH 0.666 + 0.0015, 0.0745, "Description", 0.0025
    LabelPH 0.771 + 0.0015, 0.0745, "Date", 0.0025
    LabelPH 0.801 + 0.0015, 0.0745, "By", 0.0025
End Sub


' The equipment list: tag, equipment, quantity (both strings), size,
' basis -- the sizes from the same constants the drawing uses.
Private Sub DrawEquipmentList()
    Dim tg As Variant, eq As Variant, qt As Variant, sz As Variant, bs As Variant
    Dim yT As Double, y As Double
    Dim i As Long, n As Long
    Const RH As Double = 0.006

    tg = Array("Tag", "C1", "C2-C4", "C5", "R1", "R2", "R3", "R4", "CAL", "GN", "TAD", "KIC", "KLN", "HD", "CLR")
    eq = Array("Equipment", "twin top cyclone", "cyclone", "cyclone", "riser", "riser", "riser", "riser", _
               "ILC calciner", "Y gooseneck", "tertiary air duct", "kiln inlet chamber", "rotary kiln", _
               "kiln hood", "grate cooler")
    qt = Array("Qty", "4", "6", "2", "2", "2", "2", "2", "1", "1", "1", "1", "1", "1", "1")
    sz = Array("Size [m]", "D" & Num(2# * CycR(1), 3), "D" & Num(2# * CycR(4), 3) & ", barrel h = D", _
               "D" & Num(2# * CycR(5), 3), "D" & Num(RiserD(1), 3), "D" & Num(RiserD(2), 3), _
               "D" & Num(RiserD(3), 3), "D" & Num(RiserD(4), 3), _
               "D" & Num(CALC_D, 3) & ", H " & Num(CALC_H, 2), "neck D" & Num(2# * rNeck, 2) & ", legs D" & Num(2# * rGn, 2), "D" & Num(TA_D, 3), _
               Num(2# * aCh, 1) & " x " & Num(2# * aCh, 1) & ", ramp", _
               "D" & Num(KILN_D, 1) & " x " & Num(KILN_L, 0) & ", " & Num(100# * KILN_SLOPE, 0) & " %", _
               Num(2# * aCh, 1) & " x " & Num(2# * aCh, 1), _
               Num(COOLER_AREA, 0) & " m2, " & Num(COOLER_W, 1) & " x " & Num(coolL, 1))
    bs = Array("Basis", "CFD C1", "CFD C4", _
               "CFD C4 x 6.50/6.30", "published", "published", _
               "published", "published", "PF5000, calciner.bas", _
               "D3.5 per leg, calciner.bas", "derived, calciner.md", "schematic (no source)", "PF5000, kiln.md", _
               "schematic (no source)", "PF5000, cooler.md")
    n = UBound(tg) + 1

    yT = 0.27
    UseLayer L_TEXT
    LabelP COL_X0, yT + 0.008, "EQUIPMENT LIST"
    UseLayer L_FRAME
    RectP COL_X0, yT - n * RH, FR_X1, yT
    UseLayer L_TEXT
    For i = 1 To n - 1
        LineP COL_X0, yT - i * RH, FR_X1, yT - i * RH
    Next i
    LineP 0.669, yT - n * RH, 0.669, yT
    LineP 0.716, yT - n * RH, 0.716, yT
    LineP 0.728, yT - n * RH, 0.728, yT
    LineP 0.771, yT - n * RH, 0.771, yT
    For i = 0 To n - 1
        y = yT - i * RH - 0.0018
        LabelPH COL_X0 + 0.0015, y, CStr(tg(i)), 0.0025
        LabelPH 0.669 + 0.0015, y, CStr(eq(i)), 0.0025
        LabelPH 0.716 + 0.0015, y, CStr(qt(i)), 0.0025
        LabelPH 0.728 + 0.0015, y, CStr(sz(i)), 0.0025
        LabelPH 0.771 + 0.0015, y, CStr(bs(i)), 0.0025
    Next i
End Sub


' The frame, ISO 5457 for A1: its border, and 12 x 8 zones marked on
' it -- 1..12 along the top and bottom, A..H down the sides.
Private Sub DrawFrame()
    Dim i As Long
    Dim x As Double, y As Double, w As Double, h As Double
    UseLayer L_FRAME
    RectP FR_X0, FR_Y0, FR_X1, FR_Y1
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
        x = FR_X0 + (i - 0.5) * w - 0.3 * TEXT_H * Len(CStr(i))
        LabelP x, FR_Y1 + 0.0075, CStr(i)
        LabelP x, FR_Y0 - 0.0025, CStr(i)
    Next i
    For i = 1 To 8
        y = FR_Y1 - (i - 0.5) * h + 0.5 * TEXT_H
        LabelP FR_X0 - 0.013, y, Chr(64 + i)
        LabelP FR_X1 + 0.0025, y, Chr(64 + i)
    Next i
End Sub


' Centre lines (ISO 128 chain lines): each cyclone's axis, the kiln's
' axis, and the calciner's over its roof (below it the kiln gas line
' runs on the axis).
Private Sub DrawAxes()
    Dim k As Long, s As Long
    Dim sd As Double, xi As Double, xo As Double, xm As Double, dc1 As Double
    Dim col(2 To 5) As Double
    UseLayer L_AXIS
    dc1 = CycR(1) + 0.5 * C1_TWIN_GAP
    For k = 0 To 1
        sd = 1# - 2# * k
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        For s = 2 To 5
            LineM col(s), zDust(s) - 1#, col(s), zTop(s) + 1#
        Next s
        LineM xm - sd * dc1, zDust(1) - 1#, xm - sd * dc1, zTop(1) + 1#
        LineM xm + sd * dc1, zDust(1) - 1#, xm + sd * dc1, zTop(1) + 1#
    Next k
    LineM kAx - Cos(kAlpha), kAz + Sin(kAlpha), kBx + Cos(kAlpha), kBz - Sin(kAlpha)
    LineM 0#, zCalcRoof, 0#, zCalcRoof + 2#
End Sub


' Elevation marks: the dust outlets, the calciner roof and the tower
' top in a column right of the right string; the kiln axis left of the
' inlet chamber.
Private Sub DrawLevels()
    Dim s As Long
    UseLayer L_DIM
    For s = 5 To 1 Step -1
        LevelMark LEVEL_X, zDust(s), "+" & Num(zDust(s), 2) & " C" & s & " dust outlet"
    Next s
    ' Its text under the line when the C4 dust outlet's mark sits just
    ' over it, where the two texts would run into each other
    LevelMark LEVEL_X, zCalcRoof, "+" & Num(zCalcRoof, 2) & " calciner roof", _
              (zDust(4) >= zCalcRoof And zDust(4) - zCalcRoof < 2.5)
    LevelMark LEVEL_X, zTop(1), "+" & Num(zTop(1), 2) & " tower top"
    LevelMark -13#, kAz, "+" & Num(kAz, 2) & " kiln axis"
End Sub


' An elevation mark at (x, z): a short level line, a triangle with its
' tip on it, its text over (or, below, under the line).
Private Sub LevelMark(ByVal x As Double, ByVal z As Double, ByVal txt As String, _
                      Optional ByVal below As Boolean = False)
    Dim px As Double, py As Double
    P x, z, px, py
    LineP px, py, px + 0.008, py
    LineP px + 0.0025, py, px + 0.001, py + 0.0026
    LineP px + 0.0025, py, px + 0.004, py + 0.0026
    LineP px + 0.001, py + 0.0026, px + 0.004, py + 0.0026
    If below Then
        LabelP px + 0.0055, py - 0.001, txt
    Else
        LabelP px + 0.0055, py + 0.0045, txt
    End If
End Sub


' The column grid over the tower: grid lines 1..5 (outer L, inner L,
' calciner, inner R, outer R) with their bubbles, and the spacings
' between them dimensioned.
Private Sub DrawGrid()
    Dim gx(4) As Double
    Dim i As Long
    Dim zg As Double
    gx(0) = -(xInner + ZIG_DX): gx(1) = -xInner: gx(2) = 0#: gx(3) = xInner: gx(4) = xInner + ZIG_DX
    zg = zTop(1)
    UseLayer L_AXIS
    For i = 0 To 4
        LineM gx(i), zg + 5#, gx(i), zg + 10.5
    Next i
    UseLayer L_DIM
    For i = 0 To 4
        CircleM gx(i), zg + 11.75, 1.25
        LabelM gx(i) - 0.3 * TEXT_H * SHEET_SCALE, zg + 11.75 + 0.5 * TEXT_H * SHEET_SCALE, CStr(i + 1), 0#
    Next i
    For i = 0 To 3
        DimH gx(i), gx(i + 1), zg + 6.5, Num(gx(i + 1) - gx(i), 3), 0.5 * (gx(i) + gx(i + 1))
    Next i
    DimH gx(0), gx(4), zg + 8.5, Num(gx(4) - gx(0), 3), 0.5 * (gx(0) + gx(1))
End Sub


' A horizontal dimension from xa to xb at z: its line, oblique ticks at
' both ends, its value centred over xt.
Private Sub DimH(ByVal xa As Double, ByVal xb As Double, ByVal z As Double, ByVal txt As String, _
                 ByVal xt As Double)
    LineM xa, z, xb, z
    LineM xa - 0.5, z - 0.5, xa + 0.5, z + 0.5
    LineM xb - 0.5, z - 0.5, xb + 0.5, z + 0.5
    LabelM xt - 0.3 * TEXT_H * Len(txt) * SHEET_SCALE, z + 0.3 + TEXT_H * SHEET_SCALE, txt, 0#
End Sub


' A circle about model (x, z), radius r.
Private Sub CircleM(ByVal x As Double, ByVal z As Double, ByVal r As Double)
    Dim px As Double, py As Double
    Dim i As Long
    P x, z, px, py
    If swSkMgr.CreateCircleByRadius(px, py, 0#, r / SHEET_SCALE) Is Nothing Then
        Fail "CreateCircleByRadius failed on layer " & curLayer & "."
    End If
    i = LayerIndex(curLayer)
    nArc(i) = nArc(i) + 1
    Track px - r / SHEET_SCALE, py - r / SHEET_SCALE: Track px + r / SHEET_SCALE, py + r / SHEET_SCALE
End Sub


' A rectangle on the sheet.
Private Sub RectP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    LineP a, b, c, b
    LineP c, b, c, d
    LineP c, d, a, d
    LineP a, d, a, b
End Sub


'==================================================================
' (f) Verification: the sheet must hold, layer by layer, every line
'     and arc drawn, and its lines must span exactly what was drawn.
'==================================================================
Private Sub VerifySheet()

    Dim v As Object, ssk As Object
    Dim segs As Variant
    Dim i As Long, li As Long
    Dim gotL(LAYER_N - 1) As Long, gotA(LAYER_N - 1) As Long
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

    For li = 0 To LAYER_N - 1
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
    For i = 0 To LAYER_N - 1
        LayerSummary = LayerSummary & layerNames(i) & " " & nLine(i)
        If nArc(i) > 0 Then LayerSummary = LayerSummary & " + " & nArc(i) & " arcs"
        If i < LAYER_N - 1 Then LayerSummary = LayerSummary & ", "
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
