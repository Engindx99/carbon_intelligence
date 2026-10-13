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
' C5 is the C4 CFD domain x 6.50 / 6.30 throughout (see Kc): its vortex finder, volute and outlet
' pipe -- R4 itself, as C4 / C3's are R3 / R2
' C2-C4 as the C4 CFD domain (cyclone_C4.md, cyclone.bas, S 3.90): the vortex finder 3.90 m
' down from the roof; the gas outlet pipe (D_x) 5.79 m (1.25 D_x) up over it, a 90 deg bend
' (centreline R 1.0 D_x, its walls arcs) and a 4.63 m (1.0 D_x) level leg, the riser going on
' from its end; the inlet a volute 3.40 m high under the roof, a 2.912 m wide duct and a half
' turn of Archimedean spiral 0.05 m (the tongue) off the barrel, fed by a straight duct 3.0 m
' from the barrel's tangent plane. In the plant C5..C3's outlet pipes are R4..R2 themselves:
' the CFD's 5.79 m, its bend, its leg level on into the next cyclone's inlet. The domain is
' frozen between its faces -- the inlet duct's end, 3.0 m from the axis, and the leg's end,
' 9.26 m from it -- and tests/test_plant_topology_cfd_lock.py holds these to cyclone.bas
Const C4_VF_S    As Double = 3.9
Const C4_OUT_RISE As Double = 5.7875   ' 1.25 D_x
Const C4_OUT_R   As Double = 4.63
Const C4_OUT_RUN As Double = 4.63
Const C4_IN_H    As Double = 3.4
Const C4_IN_W    As Double = 2.912
Const C4_TONGUE  As Double = 0.05
Const C4_IN_L    As Double = 3#       ' the inlet duct's length from the barrel's tangent plane: its face this far from the axis
Const C1_VF_S    As Double = 2.16     ' C1's vortex finder, down from the roof (C1 CFD)

' Risers [m] -- HFC2500 (published), catalog.md; R_k carries the gas
' from C(k+1) up to C(k). Each string has its own; R1 splits into
' the twin C1, each branch half its area. R2..R4 are the C3..C5 CFD
' outlet pipes (D_x), see RiserD.
Const R1_D As Double = 3.07

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
Const STAGE_GAP      As Double = 4#       ' C1's dust outlet at least this far over C2's stub [m] (R1's Y sets it higher).
                                          ' C2..C4 stand where the outlet below (as its CFD) runs into them
Const ZIG_DX         As Double = 15#      ' a string's outer column (C4, C2) outboard of its inner one (C5, C3) [m]: each
                                          ' riser's leg past the CFD outlet face, its taper and 0.5 m (14.6 m for R4); was 20
Const C5_OVER_TA     As Double = 1.75     ' the C5 dust outlets at least this far over the tertiary air duct [m]
Const GN_TO_C5_GAP   As Double = 1#       ' a gooseneck drop to its C5 barrel; its inlet run spans it [m]
Const GN_BEND_LEG    As Double = 0.5      ' the drop turns into C5 in two 45 deg steps: a 45 deg piece this many leg D across, then level [-]
' Each of the twin C1 as its CFD domain (cyclone_C1.md, riser_R1.md): heights over its dust outlet [m, deg]
Const C1_RISER_X     As Double = 6.843    ' its own riser branch (D = R1's half area), its axis this far from the C1 axis
Const C1_RISER_Z0    As Double = 0.885    ' the CFD domain's floor: the branch is straight from here ...
Const C1_BEND_Z      As Double = 8.385    ' ... up to its bend
Const C1_BEND_R      As Double = 2.171    ' bend centreline radius (1.0 D), its walls arcs
Const C1_BEND_DEG    As Double = 95#      ' the bend: from straight up to the inlet duct's 5 deg down
Const C1_TRANS_L     As Double = 1.5      ' round -> rectangular transition along the duct axis, then the duct into the barrel
Const C1_DUCT_H      As Double = 2.16     ' inlet duct height (0.86 wide, tangential)
Const C1_FEED_Z      As Double = 5.385    ' the meal chute's axis meets the branch wall here, on the side away from the C1
Const C1_FEED_L      As Double = 1#       ' ... standing out this far along its axis, at MEAL_SLOPE_DEG
Const C1_FEED_W      As Double = 0.6      ' ... 0.6 x 0.6 square
Const C1_OUT_RISE    As Double = 3#       ' gas outlet pipe (D = C1_VD) straight up over the roof ...
Const C1_OUT_R       As Double = 3.6      ' ... a 180 deg bend away from the branch, its walls arcs, and down as far as it rose
Const R1_BRANCH_HALF As Double = 2.75     ' R1's Y: the twin's branches this far either side of R1's axis [m]
Const R1_UP_MIN      As Double = 0.5      ' R1's wall on C2's side straight up at least this far over the leg before its Y; the C1 stage stands that high [m]
Const R1_LEG_ON      As Double = 0.5      ' C2's outlet leg runs on this far past the CFD's 4.63 m into R1's elbow: the
                                          ' two strings' far C1 outlet bends ~6 m apart over the calciner [m]
Const ID_FAN_L       As Double = 2.5      ' "to ID fan": an arrow this long down from each C1 outlet's leg [m]
Const RM_L           As Double = 0.8      ' raw meal: a small-headed arrow along each chute's axis, from this far past its end [m]
Const MEAL_ENTRY_UP  As Double = 1.5      ' meal enters a riser this far over its foot (R2..R4: over the roof, into the CFD outlet pipe) [m]
Const MEAL_LINK_L    As Double = 1.5      ' a meal pipe, shown by its end: straight this long either side of its source's tag [m]
Const MEAL_SIDE_L    As Double = 1#       ' a meal pipe's end into a wall comes this far out from it, then into it at the meal slope [m]
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
Const FEED_LOWER     As Double = 3#       ' C4 meal drawn into the calciner this far below calciner.bas's feed [m]
Const KILN_FLOW_OFF  As Double = 1#       ' kiln gas and material lines this far either side of the kiln axis [m]
Const PRIMARY_AIR_L  As Double = 2#       ' primary air: a short arrow this long into the hood's front wall [m]
Const SEC_AIR_DX     As Double = 1.5      ' secondary air rises from the cooler this far in from the kiln's end [m]

' Sheet [m on paper]: A1 landscape at 1:300
Const SHEET_SCALE As Double = 300#
Const PAPER_W     As Double = 0.841
Const PAPER_H     As Double = 0.594
Const X0          As Double = 0.215       ' where model x = 0 falls on the sheet
Const RULER_X     As Double = 0.04        ' the elevation ruler, inside the frame
Const Y0          As Double = 0.06        ' where model z = 0 falls on the sheet
Const TEXT_H      As Double = 0.0035      ' text height
Const ARROW_L     As Double = 0.004       ' arrow head length
Const CAP_H       As Double = 0.002       ' caption text height in the title block
' Frame, ISO 5457 for A1: 20 mm left, 10 mm elsewhere; 12 x 8 zones
Const FR_X0 As Double = 0.02, FR_X1 As Double = 0.831, FR_Y0 As Double = 0.01, FR_Y1 As Double = 0.584
' The right-hand column: legend, notes, equipment list, revisions, title block
Const COL_X0 As Double = 0.651
Const LEVEL_X As Double = 50#             ' model x of the elevation marks, right of the right string [m]

' Layers: name, colour (RGB), line weight
Const L_EQUIP As String = "EKIPMAN"
Const L_GAS   As String = "GAZ"
Const L_MEAL  As String = "FARIN"
Const L_AIR   As String = "HAVA"
Const L_TEXT  As String = "YAZI"
Const L_FRAME As String = "CERCEVE"
Const L_AXIS  As String = "EKSEN"
Const L_DIM   As String = "OLCU"
Const L_HID   As String = "GIZLI"
Const LAYER_N As Long = 9

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
Dim dC1 As Double                         ' each twin C1 from R1's axis
Dim dR1 As Double                         ' R1's axis from C2's, towards the calciner
Dim zTower As Double                      ' the tower's top: the C1 outlet bends

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
    ' its inlet.
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

    ' C4..C2: each roof flush with the top of the CFD outlet bend of
    ' the stage below (R4..R2) running into it; C1 over C2's stub
    For s = 4 To 2 Step -1
        zDust(s) = zDust(s + 1) + CycHeight(s + 1) + OutR(s + 1) + StubR(s + 1) - C4_HC - C4_HB
    Next s
    zDust(1) = zDust(2) + CycHeight(2) + STAGE_GAP
    ' R1 turns up out of C2's outlet leg, rises R1_UP_MIN over it and splits;
    ' the twin C1 stand as high as that asks, their CFD domain over it
    zDust(1) = Max2(zDust(1), zDust(2) + CycHeight(2) + C4_OUT_R + 0.5 * C4_VD + R1_UP_MIN + R1YRise() - C1_RISER_Z0)
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
            zIn(s) = zDust(1) + C1InletZ()
        Else
            zIn(s) = zRoof(s) - 0.5 * C4_IN_H          ' the volute's inlet, R2..R4's leg tapering into it
        End If
    Next s

    ' The twin C1 either side of C2's axis, their branches R1_BRANCH_HALF
    ' either side of it; the tower's top over their outlet bends
    dC1 = C1_RISER_X + R1_BRANCH_HALF
    dR1 = C4_OUT_R + C4_OUT_RUN + R1_LEG_ON + 0.5 * RiserD(1)
    zTower = zTop(1) + C1_OUT_R + 0.5 * C1_VD

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


' Dust outlet to the top of the gas outlet pipe, where its bend starts:
' each as its CFD domain (C2..C5 the C4 CFD's 5.79 m, C5's scaled; no
' straight pipe added before the bend, so the domain stays the one
' solved, user decision 14 Oct 2026).
Private Function CycHeight(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    If s = 1 Then CycHeight = hc + hb + C1_OUT_RISE Else CycHeight = hc + hb + CfdRise(s)
End Function

' C2..C5 are the C4 CFD domain, C5 scaled by 6.50 / 6.30: its scale
Private Function Kc(ByVal s As Long) As Double
    If s = 5 Then Kc = C5_D / C4_D Else Kc = 1#
End Function

Private Function CfdRise(ByVal s As Long) As Double
    CfdRise = Kc(s) * C4_OUT_RISE
End Function

Private Function OutR(ByVal s As Long) As Double
    OutR = Kc(s) * C4_OUT_R
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


' Riser diameter, the same in both strings: R2..R4 the C3..C5 outlet
' pipe (the published 3.35 / 3.45 / 3.60 are not drawn).
Private Function RiserD(ByVal k As Long) As Double
    If k = 1 Then RiserD = R1_D Else RiserD = StubR(k + 1) * 2#
End Function


'==================================================================
' (c) Pre-checks: no outline may run into another.
'==================================================================
Private Sub PreChecks()

    Dim r1 As Double, r4 As Double, r5 As Double, xm As Double
    Dim k As Long

    r1 = CycR(1): r4 = CycR(4): r5 = CycR(5)
    xm = xInner + 0.5 * ZIG_DX

    ' R1 narrows out of C2's outlet leg
    If StubR(2) < 0.5 * RiserD(1) Then Fail "R1 (D " & Fmt(RiserD(1)) & ") is wider than the gas outlet of C2."
    ' R1's Y: its branches apart, its split over R1's foot and under
    ' the C1 CFD domain's floor; the two meal chutes, facing each other
    ' between the branches, clear of each other
    If R1_BRANCH_HALF <= kBranch * 0.5 * RiserD(1) Then Fail "R1's branches overlap. Raise R1_BRANCH_HALF."
    If R1SplitZ() < RiserV0(1) + R1_UP_MIN - 0.001 Then Fail "R1 splits before it rises: the C1 CFD branch does not fit over C2."
    ' the twin C1 over C2's outlet bend
    If zDust(1) - (zTop(2) + C4_OUT_R + 0.5 * C4_VD) < 0.5 Then Fail "the C1s sit on C2's outlet bend."
    If R1_BRANCH_HALF - kBranch * 0.5 * RiserD(1) - (C1_FEED_L + RM_L) * Cos(MEAL_SLOPE_DEG * PI / 180#) < 0.3 Then
        Fail "the twin C1's meal chutes run into each other. Raise R1_BRANCH_HALF."
    End If
    ' each C1's inlet duct under its roof
    If C1InletZ() + C1InletHalf() > C1_HC + C1_HB Then Fail "the C1 inlet duct runs over the C1 roof."
    ' R4..R2, C5..C3's CFD outlet: C3 / C2's cone clear over the bend
    ' of C5 / C4 under it (its outer wall over that cyclone's axis), and
    ' the leg reaching the next cyclone past its bend, with room to taper
    ' at 45 deg onto the 3.40 m inlet
    For k = 5 To 4 Step -1
        If zDust(k - 2) - (zTop(k) + Sqr((OutR(k) + StubR(k)) ^ 2 - OutR(k) ^ 2)) < 0.5 Then
            Fail "C" & (k - 2) & " sits on the outlet bend of C" & k & "."
        End If
    Next k
    If C4_IN_H > C4_VD Then Fail "the C4 inlet is taller than its outlet pipe, which runs into it."
    ' The CFD domains' faces: R4..R2's leg runs straight past the outlet
    ' face of C5..C3 (2 R from its axis) and tapers onto the 3.40 m
    ' inlet only outside the next cyclone's inlet face (C4_IN_L from its
    ' axis); R1's elbow starts past C2's outlet face; the gooseneck
    ' meets C5 outside its inlet face
    For k = 5 To 3 Step -1
        If ZIG_DX - CycR(k - 1) - (2# * StubR(k) - C4_IN_H) < 2# * OutR(k) + 0.5 Then
            Fail "R" & (k - 1) & " tapers inside the CFD outlet leg of C" & k & ". Raise ZIG_DX."
        End If
        If CycR(k - 1) < Kc(k - 1) * C4_IN_L Then
            Fail "R" & (k - 1) & " tapers inside the CFD inlet duct of C" & (k - 1) & "."
        End If
    Next k
    If dR1 - 0.5 * RiserD(1) < 2# * C4_OUT_R - 0.001 Then Fail "R1's elbow starts inside C2's CFD outlet leg. Raise R1_LEG_ON."
    If CycR(5) < Kc(5) * C4_IN_L Then Fail "the gooseneck runs into C5's CFD inlet duct."
    ' The C5s clear of the calciner; the gooseneck rises clear of each other
    If xInner - r5 <= rCalc Then Fail "the C5s run into the calciner."
    If rNeck >= rCalc Then Fail "the gooseneck neck is wider than the calciner roof."
    ' Each leg's run fits the C5 inlet it enters
    If 2# * rGn > C5_HIN Then Fail "the gooseneck legs (D " & Fmt(2# * rGn) & _
        ") are taller than the C5 inlet (" & Fmt(C5_HIN) & ") they enter."
    ' and its 45 deg turn leaves a level run into it
    If GN_TO_C5_GAP + rGn - GN_BEND_LEG * 2# * rGn < 0.5 * rGn Then
        Fail "the gooseneck's turn into C5 does not fit GN_TO_C5_GAP. Lower GN_BEND_LEG."
    End If
    ' The C4 meal reaches the calciner's cylinder, over the cone
    If zFeed <= zConeTop Then Fail "the C4 meal would reach the calciner below its cylinder. Lower FEED_LOWER."
    ' The tertiary air duct runs under the C5s and over the chamber and kiln
    If zTA + rTA >= zDust(5) Then Fail "the tertiary air duct runs into the C5s."
    ' and under the C5 meal's straight drop
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
    If X0 - Max2(xm + 0.5 * ZIG_DX + VoluteReach(2), xm + 0.5 * ZIG_DX - dR1 + dC1 + 2# * C1_OUT_R + 0.5 * C1_VD) / SHEET_SCALE _
       < RULER_X + 0.01 Or _
       X0 + (kBx + coolL) / SHEET_SCALE > COL_X0 - 0.01 Or Y0 + (zTower + 11#) / SHEET_SCALE > FR_Y1 - 0.005 Then
        Fail "the plant does not fit the A1 sheet at 1:" & Fmt(SHEET_SCALE) & "."
    End If

    Note "kiln inlet chamber: |x| <= " & Fmt(aCh) & " m, z " & Fmt(zCh0) & " .. " & Fmt(zCh0 + 2# * aCh)
    Note "calciner: z " & Fmt(zThroat) & " .. " & Fmt(zCalcRoof) & "; gooseneck neck D " & Fmt(2# * rNeck) & ", legs from x +-" & Fmt(xGnStart) & _
         ", legs at x +-" & Fmt(xLeg) & " down to the C5 inlet at z " & Fmt(zIn(5))
    Note "strings: inner column x +-" & Fmt(xInner) & " (C5, C3), outer x +-" & Fmt(xInner + ZIG_DX) & _
         " (C4, C2), risers straight up out of C2..C5, twin C1 at x +-" & _
         Fmt(xm + 0.5 * ZIG_DX - dR1 - dC1) & " and +-" & Fmt(xm + 0.5 * ZIG_DX - dR1 + dC1) & ", each with its CFD riser branch; tower top " & Fmt(zTower)
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
    layerNames(6) = L_AXIS: layerNames(7) = L_DIM: layerNames(8) = L_HID

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
    AddOneLayer lm, L_HID, "hidden edges: vortex finders", RGB(0, 0, 0), swLineHIDDEN, swLW_THIN
    Note "layers: " & L_EQUIP & " (black, normal), " & L_GAS & " (red), " & L_MEAL & " (yellow), " & _
         L_AIR & " (blue), " & L_TEXT & " (black, thin), " & L_FRAME & " (black, thick), " & _
         L_AXIS & " (black, centre line), " & L_DIM & " (black, thin), " & L_HID & " (black, hidden)"

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
    Dim sd As Double, xi As Double, xo As Double, xm As Double
    Dim zx As Double, zc As Double, kOff As Double
    Dim kSh As Double, zTopCh As Double, zTopHd As Double
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

    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        ' each open on the side its inlet comes from: C5 the gooseneck's
        ' (towards the calciner), the others their riser's
        Cyclone 5, col(5), -sd, rGn
        Volute 5, col(5), sd
        For s = 4 To 2 Step -1
            Cyclone s, col(s), Sgn(xm - col(s)), 0.5 * C4_IN_H
            Volute s, col(s), -Sgn(xm - col(s))
        Next s
        ' the twin C1 either side of R1, their branches between them
        Cyclone 1, xo - sd * (dR1 + dC1), sd, C1InletHalf()
        Cyclone 1, xo - sd * (dR1 - dC1), -sd, C1InletHalf()
        UseLayer L_HID
        For s = 5 To 2 Step -1
            VortexFinder s, col(s)
        Next s
        VortexFinder 1, xo - sd * (dR1 + dC1)
        VortexFinder 1, xo - sd * (dR1 - dC1)
        UseLayer L_EQUIP
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
    ' hot, so on the gas layer as the secondary air.
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

        '--- the Y gooseneck, as calciner.bas: the neck (once), then each
        '    leg's bend, drop, and across into the C5 at its inlet ------
        If k = 0 Then
            Duct "gas: calciner -> gooseneck neck", Array(0#, zCalcRoof, 0#, zGnTop), 2# * rNeck, False
        End If
        YBend sd
        ' (down to just over the C5 inlet, 45 deg across down to it in two
        ' 45 deg steps, then level into it)
        Duct "gas: gooseneck drop " & side & " -> C5 inlet", Array(sd * xLeg, zGnTop, _
             sd * xLeg, zIn(5) + GN_BEND_LEG * 2# * rGn, sd * (xLeg + GN_BEND_LEG * 2# * rGn), zIn(5), _
             xi - sd * CycR(5), zIn(5)), 2# * rGn, False

        '--- R4, R3, R2: C5 / C4 / C3's CFD outlet pipe itself, straight
        '    up to the next cyclone's roof, its 90 deg bend there and the
        '    leg level into that cyclone's inlet ----------------------------
        For s = 5 To 3 Step -1
            up = s - 1
            OutletRiser s, col(s), Sgn(col(up) - col(s)), col(up) - Sgn(col(up) - col(s)) * CycR(up), side
        Next s

        '--- R1: out of C2's CFD outlet, its leg towards the calciner,
        '    an elbow straight up, a Y into the twin C1's branches; each
        '    C1 with its branch, inlet and outlet bend as its CFD domain,
        '    the two mirror images of each other --------------------------
        R1Elbow xo, sd, side
        R1Y xo - sd * dR1
        C1Unit side & " far", xo - sd * (dR1 + dC1), -sd
        C1Unit side & " near", xo - sd * (dR1 - dC1), sd

        '--- meal ---------------------------------------------------------
        phase = "drawing the meal path, string " & side
        UseLayer L_MEAL
        ' Every meal pipe is shown by its end only, its source's tag in
        ' a break (MealEnd): drawn whole, in 2D each would lie across the
        ' ducts between (a cyclone just over the outlet bend under it,
        ' the pipes running across the tower). Each cyclone feeds the
        ' riser leaving the stage two below -- the CFD outlet pipe, on
        ' the side away from its bend, low on it, where a plant feeds its
        ' meal: both C1 into R2, C2 into R3, C3 into R4; C4 the calciner
        ' through its wall, C5 the kiln inlet chamber through its roof.
        MealLink "C1", side, col(3), 2, Sgn(col(3) - col(2))
        MealLink "C2", side, col(4), 3, Sgn(col(4) - col(3))
        MealLink "C3", side, col(5), 4, Sgn(col(5) - col(4))
        MealEnd "C4", "meal: C4 " & side & " -> calciner", sd * rCalc, zFeed, sd, True
        MealEnd "C5", "meal: C5 " & side & " -> kiln inlet chamber", sd * (aCh - MEAL_INTO_CHAMBER), zCh0 + 2# * aCh, sd, False
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
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        For s = 5 To 2 Step -1
            CycLabel "C" & s & " " & side, s, col(s)
        Next s
        CycLabel "C1 " & side, 1, xo - sd * (dR1 + dC1)
        CycLabel "C1 " & side, 1, xo - sd * (dR1 - dC1)
        For s = 5 To 3 Step -1
            LabelM col(s), 0.5 * (RiserV0(s - 1) + RiserBendZ(s - 1)) - 1.5, "R" & (s - 1), -0.002
        Next s
        ' R1 between its branches, under their meal chutes
        LabelM xo - sd * dR1, zDust(1) + 0.5 * (C1_RISER_Z0 + C1_FEED_Z) - 0.5, "R1", -0.002
        ' under each C1 outlet's arrow
        LabelM xo - sd * (dR1 + dC1 + 2# * C1_OUT_R) - 0.3 * TEXT_H * 9 * SHEET_SCALE, zRoof(1) - ID_FAN_L - 0.6, "to ID fan", 0#
        LabelM xo - sd * (dR1 - dC1 - 2# * C1_OUT_R) - 0.3 * TEXT_H * 9 * SHEET_SCALE, zRoof(1) - ID_FAN_L - 0.6, "to ID fan", 0#
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


' C2's CFD gas outlet over its stub top at xo (string sd): the 90 deg
' bend towards the calciner, its walls arcs; the leg level on past the
' CFD's 4.63 m into R1's elbow. The leg's top wall runs straight into
' R1's wall on C2's side, which turns straight up; its bottom wall
' turns up at 45 deg across to R1's far wall -- a mitred elbow,
' narrowing from D_x to R1's D. R1 rises to its Y.
Private Sub R1Elbow(ByVal xo As Double, ByVal sd As Double, ByVal side As String)
    Dim zt As Double, cx As Double, a0 As Double, zl As Double, a As Double, r As Double, xr As Double
    zt = zTop(2): cx = xo - sd * C4_OUT_R
    zl = zt + C4_OUT_R: a = 0.5 * C4_VD: r = 0.5 * RiserD(1): xr = xo - sd * dR1
    If sd < 0# Then a0 = PI Else a0 = 0#
    ArcM cx, zt, C4_OUT_R + a, a0, 0.5 * PI
    ArcM cx, zt, C4_OUT_R - a, a0, 0.5 * PI
    DuctEdge cx, zl + a, xr + sd * r, zl + a
    DuctEdge cx, zl - a, xr + sd * r, zl - a
    DuctEdge xr + sd * r, zl - a, xr - sd * r, zl - a + 2# * r
    DuctEdge xr + sd * r, zl + a, xr + sd * r, R1SplitZ()
    DuctEdge xr - sd * r, zl - a + 2# * r, xr - sd * r, R1SplitZ()
    ArrowAt 0.5 * (cx + xr + sd * r), zl, -sd, 0#
    Note "-- gas: C2 " & side & " outlet -> R1 (D " & Fmt(C4_VD) & " -> " & Fmt(RiserD(1)) & ")"
End Sub


' R(s - 1) (s = 3..5): C(s)'s CFD outlet pipe (the cyclone's stub, up
' to zTop), its 90 deg bend towards dr (+1 / -1), its walls arcs, its
' and its level leg, straight on past the CFD domain's outlet face to
' the barrel wall of C(s - 1) at xw, its top flush with that roof: its
' top straight in, its bottom rising at 45 deg onto the 3.40 m inlet
' over the last stretch.
Private Sub OutletRiser(ByVal s As Long, ByVal xc As Double, ByVal dr As Double, ByVal xw As Double, _
                        ByVal side As String)
    Dim zt As Double, cx As Double, a0 As Double, zl As Double, tp As Double, a As Double
    zt = zTop(s): cx = xc + dr * OutR(s)
    zl = zt + OutR(s): a = StubR(s): tp = 2# * a - C4_IN_H
    If dr > 0# Then a0 = PI Else a0 = 0#
    ArcM cx, zt, OutR(s) + a, a0, 0.5 * PI
    ArcM cx, zt, OutR(s) - a, a0, 0.5 * PI
    Duct "gas: R" & (s - 1) & " " & side & " leg -> C" & (s - 1), Array(cx, zl, xw - dr * tp, zl), 2# * a, False
    DuctEdge xw - dr * tp, zl + a, xw, zl + a
    DuctEdge xw - dr * tp, zl - a, xw, zl - a + tp
End Sub


' the foot of R(k)'s upright: the roof under the CFD outlet pipe for
' R2..R4, the top of C2's outlet leg for R1
Private Function RiserV0(ByVal k As Long) As Double
    If k = 1 Then RiserV0 = zTop(2) + C4_OUT_R + 0.5 * C4_VD Else RiserV0 = zRoof(k + 1)
End Function

' the upright's top: where C(k + 1)'s outlet bend starts (R2..R4)
Private Function RiserBendZ(ByVal k As Long) As Double
    RiserBendZ = zTop(k + 1)
End Function


' C(s)'s volute (s = 2..5, the C4 CFD's, C5's scaled) seen from the side: a band
' C4_IN_H deep under the roof, its duct in front of the barrel from
' the riser's side, its spiral standing out on the far side (away)
' as far as VoluteReach.
Private Sub Volute(ByVal s As Long, ByVal xc As Double, ByVal away As Double)
    Dim zb As Double, xv As Double
    zb = zRoof(s) - Kc(s) * C4_IN_H: xv = VoluteReach(s)
    LineM xc - away * CycR(s), zb, xc + away * xv, zb
    LineM xc + away * xv, zb, xc + away * xv, zRoof(s)
    LineM xc + away * CycR(s), zRoof(s), xc + away * xv, zRoof(s)
End Sub

' the spiral r = R + t + W (1 - phi / pi) at its widest seen side on
Private Function VoluteReach(ByVal s As Long) As Double
    Dim i As Long, ph As Double, x As Double
    For i = 0 To 200
        ph = PI * i / 200#
        x = (CycR(s) + Kc(s) * (C4_TONGUE + C4_IN_W * (1# - ph / PI))) * Sin(ph)
        If x > VoluteReach Then VoluteReach = x
    Next i
End Function


' A cyclone's vortex finder, hidden in its barrel: its walls from the
' roof down its immersion (C1 and C2..C5 as their CFD).
Private Sub VortexFinder(ByVal s As Long, ByVal xc As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double, sv As Double
    CycDims s, d, hb, hc, vd, dd
    If s = 1 Then sv = C1_VF_S Else sv = Kc(s) * C4_VF_S
    LineM xc - 0.5 * vd, zRoof(s), xc - 0.5 * vd, zRoof(s) - sv
    LineM xc + 0.5 * vd, zRoof(s), xc + 0.5 * vd, zRoof(s) - sv
End Sub


' R1's Y into the twin C1's branches, R1_BRANCH_HALF either side of
' xo, of straight pieces: R1's walls open out at 45 deg from its top
' to the branches' outer walls; the branches' inner walls run 45 deg
' up from the crotch on R1's axis, parallel, so each branch keeps its
' own width through the Y. The branches' straight run starts where
' the inner walls turn up, at the C1 CFD domain's floor.
Private Function R1SplitZ() As Double
    R1SplitZ = zDust(1) + C1_RISER_Z0 - R1YRise()
End Function

' how far the Y rises, from R1's top to its branches' straight run
Private Function R1YRise() As Double
    Dim r As Double, rb As Double
    r = 0.5 * RiserD(1): rb = kBranch * r
    R1YRise = R1_BRANCH_HALF - rb + 2# * Sqr(2#) * rb - r
End Function

Private Sub R1Y(ByVal xo As Double)
    Dim r As Double, rb As Double, b As Double, zs As Double, zo As Double, zy As Double, zc As Double
    Dim g As Double
    Dim k As Long
    r = 0.5 * RiserD(1): rb = kBranch * r: b = R1_BRANCH_HALF
    zs = R1SplitZ()
    zo = zs - r + b + rb                           ' the outer walls' corner
    zy = zs - r + 2# * Sqr(2#) * rb                ' the crotch
    zc = zDust(1) + C1_RISER_Z0                    ' the inner walls' corner
    For k = 0 To 1
        g = 1# - 2# * k
        DuctEdge xo + g * r, zs, xo + g * (b + rb), zo
        DuctEdge xo + g * (b + rb), zo, xo + g * (b + rb), zc
        DuctEdge xo, zy, xo + g * (b - rb), zc
    Next k
End Sub


' C1's inlet as its CFD domain, over its dust outlet, x from its axis
' towards its branch negative: the bend's end and the transition's end
' on the inlet duct's axis, and that axis at the barrel wall.
Private Sub C1InletAxis(ByRef bx As Double, ByRef bz As Double, ByRef tx As Double, ByRef tz As Double, _
                        ByRef wx As Double, ByRef wz As Double)
    Dim th As Double, al As Double
    th = (180# - C1_BEND_DEG) * PI / 180#
    al = (C1_BEND_DEG - 90#) * PI / 180#
    bx = -C1_RISER_X + C1_BEND_R + C1_BEND_R * Cos(th)
    bz = C1_BEND_Z + C1_BEND_R * Sin(th)
    tx = bx + C1_TRANS_L * Cos(al): tz = bz - C1_TRANS_L * Sin(al)
    wx = -0.5 * C1_D: wz = tz - (wx - tx) * Tan(al)
End Sub

' the inlet duct's axis at the barrel wall, over the dust outlet
Private Function C1InletZ() As Double
    Dim bx As Double, bz As Double, tx As Double, tz As Double, wx As Double, wz As Double
    C1InletAxis bx, bz, tx, tz, wx, wz
    C1InletZ = wz
End Function

' half the inlet's opening in the barrel wall, the branch's width on
' a vertical through the 5 deg duct (drawn at the branch's D; the
' 2.16 m duct is 0.011 m less)
Private Function C1InletHalf() As Double
    C1InletHalf = kBranch * 0.5 * RiserD(1) / Cos((C1_BEND_DEG - 90#) * PI / 180#)
End Function


' One C1 at xc as its CFD domain, its branch on its -g side (g = +1 /
' -1; the two of a twin mirror each other): the branch straight up
' from R1's Y, its 95 deg bend, the transition and inlet duct 5 deg
' down into the barrel; the meal chute on the branch's far side with
' the raw meal's arrow; the outlet pipe's 180 deg bend away from the
' branch, its leg down, and the arrow to the ID fan. Both bends are
' round as in the CFD solid: their walls concentric arcs.
Private Sub C1Unit(ByVal side As String, ByVal xc As Double, ByVal g As Double)
    Dim bx As Double, bz As Double, tx As Double, tz As Double, wx As Double, wz As Double
    Dim a0 As Double, a1 As Double, rb As Double, xr As Double, z0 As Double, tn As Double
    Dim ux As Double, uz As Double, nx As Double, nz As Double, o As Double, t As Double
    Dim ex(1) As Double, ez(1) As Double, sx As Double, sz As Double
    Dim cx As Double, zt As Double, lx As Double
    Dim k As Long
    C1InletAxis bx, bz, tx, tz, wx, wz
    z0 = zDust(1)
    rb = kBranch * 0.5 * RiserD(1)
    xr = xc - g * C1_RISER_X
    ' the bend about (xr + g R, its start), from straight up over to
    ' the duct's 5 deg down
    If g > 0# Then
        a0 = PI: a1 = PI - C1_BEND_DEG * PI / 180#
    Else
        a0 = 0#: a1 = C1_BEND_DEG * PI / 180#
    End If
    UseLayer L_GAS
    Duct "gas: R1 " & side & " branch", Array(xr, z0 + C1_RISER_Z0, xr, z0 + C1_BEND_Z), 2# * rb, False
    ArcM xr + g * C1_BEND_R, z0 + C1_BEND_Z, C1_BEND_R + rb, a0, a1
    ArcM xr + g * C1_BEND_R, z0 + C1_BEND_Z, C1_BEND_R - rb, a0, a1
    Duct "gas: R1 " & side & " branch bend -> C1 inlet", Array(xc + g * bx, z0 + bz, xc + g * tx, z0 + tz, _
         xc + g * wx, z0 + wz), 2# * rb, False, True

    ' the meal chute, square, its axis at the meal slope out of the
    ' branch's far wall, its end closed
    UseLayer L_EQUIP
    tn = Tan(MEAL_SLOPE_DEG * PI / 180#)
    ux = -g * Cos(MEAL_SLOPE_DEG * PI / 180#): uz = Sin(MEAL_SLOPE_DEG * PI / 180#)
    nx = uz: nz = -ux
    sx = xr - g * rb: sz = z0 + C1_FEED_Z         ' its axis at the wall
    For k = 0 To 1
        o = (0.5 - k) * C1_FEED_W
        t = -o * nx / ux                          ' its side from the wall
        ex(k) = sx + C1_FEED_L * ux + o * nx: ez(k) = sz + C1_FEED_L * uz + o * nz
        LineM sx + o * nx + t * ux, sz + o * nz + t * uz, ex(k), ez(k)
    Next k
    LineM ex(0), ez(0), ex(1), ez(1)
    UseLayer L_MEAL
    PathOut "meal: raw meal -> R1 " & side & " branch", Array(sx + (C1_FEED_L + RM_L) * ux, _
            sz + (C1_FEED_L + RM_L) * uz, sx, sz), 0.5 * ARROW_L
    UseLayer L_TEXT
    LabelMH sx + (C1_FEED_L + RM_L) * ux, sz + (C1_FEED_L + RM_L) * uz + 0.9, "RM", _
            IIf(g > 0#, 0.0003, -0.0031), CAP_H

    ' the outlet: from the stub's top, 180 deg away from the branch,
    ' about (cx, the stub's top), then its leg down
    UseLayer L_GAS
    cx = xc + g * C1_OUT_R: zt = zTop(1)
    lx = xc + 2# * g * C1_OUT_R
    If g > 0# Then
        a0 = PI: a1 = 0#
    Else
        a0 = 0#: a1 = PI
    End If
    ArcM cx, zt, C1_OUT_R + 0.5 * C1_VD, a0, a1
    ArcM cx, zt, C1_OUT_R - 0.5 * C1_VD, a0, a1
    Duct "gas: C1 " & side & " outlet bend -> leg", Array(lx, zt, lx, zRoof(1)), C1_VD, False
    PathOut "gas: C1 " & side & " -> ID fan", Array(lx, zRoof(1), lx, zRoof(1) - ID_FAN_L)
End Sub


' An arc about (cx, cz), radius r, from angle a0 to a1 [rad] through
' their middle.
Private Sub ArcM(ByVal cx As Double, ByVal cz As Double, ByVal r As Double, ByVal a0 As Double, ByVal a1 As Double)
    Dim a As Double, b As Double, c As Double, d As Double, m As Double, q As Double
    Dim i As Long
    P cx + r * Cos(a0), cz + r * Sin(a0), a, b
    P cx + r * Cos(a1), cz + r * Sin(a1), c, d
    P cx + r * Cos(0.5 * (a0 + a1)), cz + r * Sin(0.5 * (a0 + a1)), m, q
    If swSkMgr.Create3PointArc(a, b, 0#, c, d, 0#, m, q, 0#) Is Nothing Then
        Fail "Create3PointArc failed on layer " & curLayer & "."
    End If
    i = LayerIndex(curLayer)
    nArc(i) = nArc(i) + 1
    Track a, b: Track c, d: Track m, q
End Sub


' The end of a meal pipe from cyclone src into R(k) (k = 2..4, the
' CFD outlet pipe at xr): on the side sg away from its bend, into the
' wall MEAL_ENTRY_UP over the roof.
Private Sub MealLink(ByVal src As String, ByVal side As String, ByVal xr As Double, ByVal k As Long, _
                     ByVal sg As Double)
    Dim ze As Double
    ze = RiserV0(k) + MEAL_ENTRY_UP
    If ze + MEAL_SIDE_L * Tan(MEAL_SLOPE_DEG * PI / 180#) >= RiserBendZ(k) - 0.5 Then
        Fail "meal " & src & " " & side & ": it would enter R" & k & " past its pipe."
    End If
    MealEnd src, "meal: " & src & " " & side & " -> R" & k, xr + sg * 0.5 * RiserD(k), ze, sg, True
End Sub

' A meal pipe shown by its end only, reaching (xt, zt): straight down,
' src's tag in a break in it, MEAL_LINK_L either side; into a wall
' (intoWall) it comes MEAL_SIDE_L out on side sg and turns into it at
' the meal slope, onto a roof it runs straight down. The arrow's tip
' on the target.
Private Sub MealEnd(ByVal src As String, ByVal what As String, ByVal xt As Double, ByVal zt As Double, _
                    ByVal sg As Double, ByVal intoWall As Boolean)
    Dim xp As Double, z3 As Double, zg As Double, gap As Double, w As Double
    If intoWall Then
        xp = xt + sg * MEAL_SIDE_L: z3 = zt + MEAL_SIDE_L * Tan(MEAL_SLOPE_DEG * PI / 180#)
    Else
        xp = xt: z3 = zt
    End If
    gap = CAP_H * SHEET_SCALE + 0.4                ' the break the tag sits in
    zg = z3 + MEAL_LINK_L                           ' the break's foot
    LineM xp, zg + gap, xp, zg + gap + MEAL_LINK_L
    If intoWall Then
        PathOut what, Array(xp, zg, xp, z3, xt, zt), 0.5 * ARROW_L
    Else
        PathOut what, Array(xp, zg, xt, zt), 0.5 * ARROW_L
    End If
    UseLayer L_TEXT
    w = 0.0013 * Len(src)
    LabelMH xp, zg + gap - 0.2, src, -0.5 * w, CAP_H
    UseLayer L_MEAL
End Sub


' A cyclone's name centred in its barrel, the one place no path
' crosses; under its vortex finder where that is drawn.
Private Sub CycLabel(ByVal txt As String, ByVal s As Long, ByVal xc As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    If s = 1 Then
        LabelM xc - 0.3 * TEXT_H * Len(txt) * SHEET_SCALE, zRoof(s) - C1_VF_S - 0.6, txt, 0#
    Else
        LabelM xc - 0.3 * TEXT_H * Len(txt) * SHEET_SCALE, zRoof(s) - Kc(s) * C4_VF_S - 0.6, txt, 0#
    End If
End Sub


' The ground line and, at the sheet's left edge, an elevation ruler
' from 0 to the first 10 m over the tower top, with a tick and its
' elevation every 10 m.
Private Sub DrawRuler()
    Dim k As Long, nk As Long
    Dim xr As Double, y As Double
    xr = (RULER_X - X0) * SHEET_SCALE
    nk = Int(zTower / 10#) + 1
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


' A duct's edge.
Private Sub DuctEdge(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    LineM xa, za, xb, zb
End Sub


' A path that leaves the drawing (or only marks a stream): one line,
' with the arrow's tip at its end, so no line runs on past the arrow;
' its head hd long on the sheet.
Private Sub PathOut(ByVal what As String, pts As Variant, Optional ByVal hd As Double = ARROW_L)
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
    ArrowAt pts(2 * n - 2) - ax * 0.5 * hd * SHEET_SCALE, pts(2 * n - 1) - az * 0.5 * hd * SHEET_SCALE, ax, az, hd
    Note "-- " & what
End Sub


' A duct at its true width w: two lines offset w / 2 either side of
' its axis, joined at each corner where the offset lines cross
' (mitre). capStart closes the duct's first end. The arrow rides on
' the axis, which is not drawn; noArrow leaves it out (R1's short
' upright, a C1 inlet after its bend: their arrows ride on the C1
' branches).
Private Sub Duct(ByVal what As String, pts As Variant, ByVal w As Double, ByVal capStart As Boolean, _
                 Optional ByVal noArrow As Boolean = False)

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
    If capStart Then DuctEdge e0x(0), e0z(0), e0x(1), e0z(1)
    If Not noArrow Then ArrowOnLongest pts
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


Private Sub ArrowAt(ByVal x As Double, ByVal z As Double, ByVal dx As Double, ByVal dz As Double, _
                    Optional ByVal hd As Double = ARROW_L)
    Dim px As Double, py As Double, tx As Double, ty As Double
    Dim k As Long, sg As Double
    P x, z, px, py
    tx = px + dx * 0.5 * hd: ty = py + dz * 0.5 * hd
    For k = 0 To 1
        sg = 1# - 2# * k
        LineP tx, ty, tx - dx * hd - sg * dz * 0.4 * hd, ty - dz * hd + sg * dx * 0.4 * hd
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


' As LabelM, text height h.
Private Sub LabelMH(ByVal x As Double, ByVal z As Double, ByVal txt As String, ByVal dx As Double, ByVal h As Double)
    Dim px As Double, py As Double
    P x, z, px, py
    LabelPH px + dx, py, txt, h
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
    Call ArrowAt((x + 0.02 - 0.25 * ARROW_L - X0) * SHEET_SCALE, (y - Y0) * SHEET_SCALE, 1#, 0#, 0.5 * ARROW_L)
    UseLayer L_TEXT: LabelPH x + 0.0083, y + 0.001, "C2", CAP_H
    LabelP x + 0.025, y + 0.002, "meal pipe shown by its end only, its source in the break"

    y = y - 0.02
    LabelP x, y, "NOTES"
    LabelP x, y - 0.006, "1. Elevations above ground, m; diameters internal, m."
    LabelP x, y - 0.012, "2. 5000 t/d: two identical 2500 t/d strings on one calciner and"
    LabelP x, y - 0.018, "   kiln; cyclones at the CFD sizes; see the equipment list."
    LabelP x, y - 0.024, "3. Schematic: kiln inlet chamber size has no source; meal pipes"
    LabelP x, y - 0.030, "   shown by their ends only, their runs lie across the ducts in 2D."
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

    tg = Array("Tag", "C1", "C2-C4", "C5", "R1", "R2", "R3", "R4", "CAL", "GN", "TAD", "KIC", "KLN", "HD", "CLR", "RM")
    eq = Array("Equipment", "twin top cyclone", "cyclone", "cyclone", "riser", "riser", "riser", "riser", _
               "ILC calciner", "Y gooseneck", "tertiary air duct", "kiln inlet chamber", "rotary kiln", _
               "kiln hood", "grate cooler", "raw meal inlet")
    qt = Array("Qty", "4", "6", "2", "2", "2", "2", "2", "1", "1", "1", "1", "1", "1", "1", "2")
    sz = Array("Size [m]", "D" & Num(2# * CycR(1), 3), "D" & Num(2# * CycR(4), 3) & ", barrel h = D", _
               "D" & Num(2# * CycR(5), 3), "D" & Num(RiserD(1), 3), "D" & Num(RiserD(2), 3), _
               "D" & Num(RiserD(3), 3), "D" & Num(RiserD(4), 3), _
               "D" & Num(CALC_D, 3) & ", H " & Num(CALC_H, 2), "neck D" & Num(2# * rNeck, 2) & ", legs D" & Num(2# * rGn, 2), "D" & Num(TA_D, 3), _
               Num(2# * aCh, 1) & " x " & Num(2# * aCh, 1) & ", ramp", _
               "D" & Num(KILN_D, 1) & " x " & Num(KILN_L, 0) & ", " & Num(100# * KILN_SLOPE, 0) & " %", _
               Num(2# * aCh, 1) & " x " & Num(2# * aCh, 1), _
               Num(COOLER_AREA, 0) & " m2, " & Num(COOLER_W, 1) & " x " & Num(coolL, 1), "-")
    bs = Array("Basis", "CFD C1", "CFD C4", _
               "CFD C4 x 6.50/6.30", "published", "CFD C4 outlet", _
               "CFD C4 outlet", "CFD C5 outlet", "PF5000, calciner.bas", _
               "D3.5 per leg, calciner.bas", "derived, calciner.md", "schematic (no source)", "PF5000, kiln.md", _
               "schematic (no source)", "PF5000, cooler.md", "into R1, schematic")
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
    Dim sd As Double, xi As Double, xo As Double, xm As Double
    Dim col(2 To 5) As Double
    UseLayer L_AXIS
    For k = 0 To 1
        sd = 1# - 2# * k
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo
        For s = 2 To 5
            LineM col(s), zDust(s) - 1#, col(s), zTop(s) + 1#
        Next s
        LineM xo - sd * (dR1 + dC1), zDust(1) - 1#, xo - sd * (dR1 + dC1), zTop(1) + 1#
        LineM xo - sd * (dR1 - dC1), zDust(1) - 1#, xo - sd * (dR1 - dC1), zTop(1) + 1#
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
    ' The C4 dust outlet's and the calciner roof's marks can sit within
    ' a text height of each other: the lower one's text then goes under
    ' its line, where the two texts would otherwise run into each other
    For s = 5 To 1 Step -1
        LevelMark LEVEL_X, zDust(s), "+" & Num(zDust(s), 2) & " C" & s & " dust outlet", _
                  (s = 4 And zCalcRoof > zDust(4) And zCalcRoof - zDust(4) < 2.5)
    Next s
    LevelMark LEVEL_X, zCalcRoof, "+" & Num(zCalcRoof, 2) & " calciner roof", _
              (zDust(4) >= zCalcRoof And zDust(4) - zCalcRoof < 2.5)
    LevelMark LEVEL_X, zTower, "+" & Num(zTower, 2) & " tower top"
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
    zg = zTower - 3#
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
