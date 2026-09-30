Attribute VB_Name = "plant_topology"
'==================================================================
' Plant topology  ->  one multi-body SLDPRT (+ STEP)
'
' A SCHEMATIC solid model of the whole 2500 t/d pyroprocess, written
' to show the plant's topology: which equipment there is, where it
' stands, and the gas, meal and air paths between it. It is NOT a
' CFD input and NOT a fluid volume -- the one exception to
' CLAUDE.md rule 8. Every piece of equipment is its own named body.
'
' Sizes come from the catalogue and the component documents. Where
' no source gives a number -- elevations, the tower's position, the
' kiln inlet chamber, the cooler's aspect -- it is a SCHEMATIC
' parameter, marked as such below, chosen only to lay the plant out
' legibly. geometry/plant_topology.md lists every one.
'
' BUILD STATUS: steps 1-4, the equipment bodies in place, the gas,
' meal and air paths joined up (the air path: kiln hood and tertiary
' air duct). Colours, body names and export follow.
'
' Coordinates: z up; the calciner's axis is x = 0, y = 0; the kiln
' runs along +x, falling towards the cooler; the preheater tower
' stands at x = -TOWER_X. Unlike the calciner CFD macro, the
' calciner here is turned so its twin gooseneck lies in the y-z
' plane, which puts the twin C5s either side of it and not over the
' kiln.
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
' geometry/catalog.md. C2 = C3 = C4 (catalog.md deviation). C5 is a
' twin, each the catalogue C5 scaled by 1/sqrt 2 (cyclone_C5.md).
Const C1_D  As Double = 4.32
Const C1_HB As Double = 6.79
Const C1_HC As Double = 4.65
Const C1_VD As Double = 2.4
Const C1_DD As Double = 0.4
Const C4_D  As Double = 6.3
Const C4_HB As Double = 3.46
Const C4_HC As Double = 7.3
Const C4_VD As Double = 4.63
Const C4_DD As Double = 0.81
Const C5_D  As Double = 6.5
Const C5_HB As Double = 3.53
Const C5_HC As Double = 7.43
Const C5_VD As Double = 4.74
Const C5_DD As Double = 0.83

' Calciner [m] -- calciner.bas / calciner.md. The throat diameter is
' derived there from literature flows; carried here as its result.
Const CALC_D        As Double = 5.5
Const CALC_H        As Double = 29.46      ' cone + cylinder
Const CALC_THROAT_D As Double = 2.213299
Const CALC_CONE_DEG As Double = 65#
Const GN_D_SRC      As Double = 3.5        ' published gooseneck, two legs share its area
Const GN_OUT_AT_H   As Double = 0.5        ' legs end at this fraction of CALC_H

' Calciner meal feed pipes -- calciner.bas / calciner.md: two round
' pipes (Fidaros et al. 2007), here at +-y since the calciner is
' turned. Axis from the vessel's axis up and out through the wall
' FEED_BELOW_GN_OUT under the gooseneck legs' ends, FEED_DEPTH past it.
Const D_FEED            As Double = 0.6    ' [m], Fidaros 2007
Const FEED_SLOPE_DEG    As Double = 60#    ' below the horizontal, Fidaros 2007
Const FEED_BELOW_GN_OUT As Double = 2#     ' [m], calciner.bas
Const FEED_DEPTH        As Double = 1#     ' [m], calciner.bas

' Tertiary air duct [m] -- calciner.md: a literature flow over a
' literature velocity (derived, not published).
Const TA_D As Double = 1.725

' Meal pipes fall at the calciner feed pipes' slope, Fidaros 2007.
Const MEAL_SLOPE_DEG As Double = 60#

' Kiln [m] -- kiln.md (published)
Const KILN_D     As Double = 4#
Const KILN_L     As Double = 60#
Const KILN_SLOPE As Double = 0.03

' Cooler -- cooler.md: grate area only [m2]
Const COOLER_AREA As Double = 65#

' SCHEMATIC -- no source; they only lay the plant out.
Const OUTLET_STUB_OVER_VD As Double = 1#   ' cyclone gas outlet stub above the roof, x vortex finder D
' 6.5, not 4.5: a riser leaves the stage below along the top of its
' gas outlet stub, right under the dust outlet of the stage above,
' and that stage's meal pipe has to fall past the riser's first ball
' at MEAL_SLOPE_DEG. C4 stands higher still: see Derive.
Const STAGE_GAP   As Double = 6.5         ' a cyclone's dust outlet above the top of the stage below [m]
Const TOWER_X     As Double = 10#         ' the tower column (C1-C4) at x = -this [m]
Const C1_TWIN_GAP As Double = 2#          ' between the twin C1 barrels [m]
Const KILN_AXIS_Z As Double = 10#         ' kiln inlet axis elevation [m]
Const CHAMBER_MARGIN As Double = 1#       ' kiln inlet chamber: a cube this far round the kiln [m]
Const COOLER_W    As Double = 3#          ' grate width [m]; the length follows from the area
Const COOLER_H    As Double = 4#          ' cooler casing height [m]
Const COOLER_DROP As Double = 1#          ' cooler top below the kiln shell at discharge [m]
Const R1_CLEAR    As Double = 0.5         ' R1 riser's clearance to the twin C1 barrels, in x [m]
Const EXHAUST_L   As Double = 10#         ' C1 exhaust ducts, drawn this long towards the fan [m]
Const MEAL_CLEAR  As Double = 0.5         ' tower meal pipes pass the barrel below this far out, in x [m]
Const C4_SPLIT_X  As Double = -5#         ' C4's meal splits in two for the calciner feeds at this x [m]
Const C5_MEAL_X   As Double = -2#         ' the C5 meal pipes turn towards the kiln inlet chamber at this x [m]
Const MEAL_INTO_CHAMBER As Double = 1#    ' the C5 meal pipes end this far inside the chamber [m]
Const RAW_MEAL_L  As Double = 5#          ' raw meal feed pipe into R1, drawn this long [m]
Const MEAL_MIN_GAP As Double = 0.1        ' least gap between a meal pipe and a gas duct it passes [m]

' Risers [m] -- HFC2500 (published), catalog.md. R_k carries the gas
' from C(k+1) up to C(k). Where a flow splits in two -- R4 from the
' twin C5, R1 into the twin C1 -- each branch carries half the area.
Const R1_D As Double = 3.07
Const R2_D As Double = 3.35
Const R3_D As Double = 3.45
Const R4_D As Double = 3.6

' Output
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL  As Double = 0.001   ' relative, on each body's closed-form volume
Const BOX_TOL  As Double = 0.005   ' absolute [m]
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001
Const PI As Double = 3.14159265358979

'------------------------------------------------------------------
' Module state
'------------------------------------------------------------------

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean

' (b) derived layout -- every one computed, none typed in
Dim c5Scale As Double
Dim rCalc As Double, rThroat As Double, hCone As Double
Dim zThroat As Double, zCalcRoof As Double
Dim rGn As Double, yLeg As Double, zLeg As Double
Dim x5 As Double                          ' twin C5 axes at (-x5, +-yLeg)
Dim zDust(1 To 5) As Double               ' dust outlet elevation of each stage
Dim yC1 As Double                         ' twin C1 axes at (-TOWER_X, +-yC1)
Dim aCh As Double, zCh0 As Double         ' chamber: |x|, |y| <= aCh, z from zCh0, 2 aCh tall
Dim kAlpha As Double                      ' kiln slope angle
Dim kAx As Double, kAz As Double          ' kiln inlet end, axis centre (y = 0)
Dim kBx As Double, kBz As Double          ' kiln discharge end
Dim coolL As Double, zCool0 As Double     ' cooler length along x, floor elevation

' Gas path (step 2)
Dim yRise As Double, rGnBend As Double    ' gooseneck rises at (0, +-yRise); bend radius
Dim zGnTop As Double                      ' top of the rise, where each bend starts and ends
Dim zC5Barrel As Double                   ' the drops end at the C5 barrels' bottom
Dim zRoof(1 To 5) As Double               ' each stage's roof
Dim zTop(1 To 5) As Double                ' each stage's gas outlet stub top
Dim yRiser(2 To 4) As Double              ' R2-R4 run up the +y side of the stage above, tangent
Dim zH(1 To 3) As Double                  ' R1-R3 leave the stage below along its stub top
Dim rB4 As Double, zH4 As Double          ' R4's two branches from the twin C5
Dim xR1 As Double, zR1Top As Double       ' R1 rises at (xR1, 0) to its distributor
Dim rB1 As Double, yB1 As Double          ' the two C1 branches, at y = +-yB1
Dim zExh As Double                        ' C1 exhaust axis elevation

' Meal path (step 3)
Dim mt As Double                          ' tan of the meal slope: fall per metre run
Dim zFeed As Double                       ' calciner feed pipe axes cross the wall here
Dim yFE As Double, zFE As Double          ' feed pipe outer ends, at (0, +-yFE, zFE)
Dim zFS As Double                         ' feed pipes start on the vessel axis at this z
Dim zC4Split As Double                    ' C4's meal splits at (C4_SPLIT_X, 0, this)
Dim zRawIn As Double                      ' raw meal enters R1's riser at this z

' Air path (step 4)
Dim zHood0 As Double                      ' kiln hood: x kBx .. kBx + 2 aCh, |y| <= aCh, z from this
Dim rTA As Double, yTA As Double          ' tertiary air duct, tangent to the calciner wall at +y
Dim zTA As Double, xTA As Double          ' its run's elevation; it leaves the hood's roof at x = xTA

' Sketch planes: registered by the first walk of BuildPlant, then
' built and measured while the part is still empty (MakePlane).
Const MAX_PLANES As Long = 96
Dim pl(MAX_PLANES - 1) As SldWorks.Feature
Dim plU(MAX_PLANES - 1) As Double, plV(MAX_PLANES - 1) As Double
Dim plAx(MAX_PLANES - 1) As Long, plAt(MAX_PLANES - 1) As Double
Dim nPl As Long
Dim registering As Boolean

Dim uSign As Double, vSign As Double
Dim wRef As Double
Dim wRefSet As Boolean

Dim nBodies As Long                       ' bodies the part should hold now
Dim buildLog As String
Dim phase As String


'==================================================================
' main
'==================================================================
Sub main()

    Dim why As String

    buildLog = ""
    phase = "starting up"
    nBodies = 0

    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "working out the layout"
    Derive
    phase = "checking the layout"
    PreChecks
    phase = "building the equipment"
    Build

    Restore
    WriteLog
    MsgBox "Plant topology steps 1-4 built and verified: " & nBodies & " bodies. " & _
           "Nothing is exported yet." & vbLf & vbLf & "Full log: " & LogPath() & vbLf & vbLf & _
           Left(buildLog, 700), vbInformation, "Plant topology"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    buildLog = buildLog & "ABORTED while " & phase & ": " & why & vbLf
    WriteLog
    MsgBox "Plant topology ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
           vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Plant topology"

End Sub


'==================================================================
' (b) Layout
'==================================================================
Private Sub Derive()

    Dim top As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim s As Long

    c5Scale = Sqr(0.5)

    ' Kiln inlet chamber round the kiln's inlet end, the kiln running
    ' out of its +x face and falling KILN_SLOPE towards the cooler.
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
    zCalcRoof = zThroat + CALC_THROAT_D + CALC_H

    ' Its twin gooseneck, as in calciner.bas but in the y-z plane:
    ' legs of half the published area, rising at (R + r) / 3, turning
    ' over a 1.5 D bend and ending at half the vessel height.
    rGn = Sqr(0.5 * 0.25 * GN_D_SRC * GN_D_SRC)
    yRise = (rCalc + rGn) / 3#
    rGnBend = 1.5 * 2# * rGn
    yLeg = yRise + 2# * rGnBend
    zGnTop = zCalcRoof + 1.25 * 2# * rGn
    zLeg = zThroat + CALC_THROAT_D + GN_OUT_AT_H * CALC_H

    ' Each C5 stands beside a leg, its roof where the leg ends, its
    ' barrel tangent to the leg on the tower side.
    x5 = 0.5 * C5_D * c5Scale + rGn
    zDust(5) = zLeg - (C5_HB + C5_HC) * c5Scale
    top = zLeg + OUTLET_STUB_OVER_VD * C5_VD * c5Scale

    ' The calciner's meal feed pipes, as in calciner.bas.
    zFeed = zLeg - FEED_BELOW_GN_OUT
    yFE = rCalc + FEED_DEPTH * Cos(FEED_SLOPE_DEG * PI / 180#)
    zFE = zFeed + FEED_DEPTH * Sin(FEED_SLOPE_DEG * PI / 180#)
    zFS = zFeed - rCalc * Tan(FEED_SLOPE_DEG * PI / 180#)

    ' The tower: each stage's dust outlet STAGE_GAP over the top of
    ' the stage below -- except C4's, which stands where its meal,
    ' falling at the meal slope, reaches the calciner feeds: TOWER_X
    ' along x, then yFE along y, both at MEAL_SLOPE_DEG. (PreChecks
    ' asks that this is at least STAGE_GAP over C5.)
    mt = Tan(MEAL_SLOPE_DEG * PI / 180#)
    For s = 4 To 1 Step -1
        zDust(s) = top + STAGE_GAP
        If s = 4 Then zDust(4) = zFE + (TOWER_X + yFE) * mt
        top = zDust(s) + CycHeight(s)
    Next s
    yC1 = 0.5 * C1_D + 0.5 * C1_TWIN_GAP

    ' Every stage's roof and stub top.
    For s = 1 To 5
        CycDims s, d, hb, hc, vd, dd
        zRoof(s) = zDust(s) + hc + hb
        zTop(s) = zDust(s) + CycHeight(s)
    Next s
    zC5Barrel = zRoof(5) - C5_HB * c5Scale

    ' Gas path. R4's branches sit on the twin C5 stubs; R3 and R2 on
    ' the stub of the stage below and run out in +y to rise tangent to
    ' the stage above; R1 runs out in +x, clear of the twin C1, rises
    ' to a distributor and splits into two branches tangent to them.
    rB4 = Sqr(0.5) * 0.5 * R4_D
    zH4 = zTop(5) + rB4
    For s = 2 To 4
        yRiser(s) = 0.5 * C4_D + 0.5 * RiserD(s)
    Next s
    For s = 1 To 3
        zH(s) = zTop(s + 1) + 0.5 * RiserD(s)
    Next s
    xR1 = -TOWER_X + 0.5 * C1_D + 0.5 * R1_D + R1_CLEAR
    rB1 = Sqr(0.5) * 0.5 * R1_D
    yB1 = yC1 + 0.5 * C1_D + rB1
    zR1Top = zRoof(1) - rB1
    zExh = zTop(1) + 0.5 * C1_VD

    ' Meal path. C4's meal runs out in +x to the split, then each
    ' half along y and on in +x to a feed pipe's end. Raw meal joins
    ' R1 half way up its riser.
    zC4Split = zDust(4) - (C4_SPLIT_X + TOWER_X) * mt
    zRawIn = 0.5 * (zH(1) + zR1Top)

    ' Air path. The kiln hood mirrors the inlet chamber round the
    ' kiln's discharge end. The tertiary air duct leaves the middle of
    ' its roof, rises, and runs back over the kiln to enter the
    ' calciner tangentially -- its outer side flush with the wall --
    ' with its lower edge on the top of the cone. That elevation is
    ' SCHEMATIC: calciner.bas step 6 (the TA duct) will set its own.
    zHood0 = kBz - aCh
    rTA = 0.5 * TA_D
    yTA = rCalc - rTA
    zTA = zThroat + CALC_THROAT_D + hCone + rTA
    xTA = kBx + aCh

    ' Cooler under the kiln's discharge end, running on in +x.
    coolL = COOLER_AREA / COOLER_W
    zCool0 = kBz - 0.5 * KILN_D - COOLER_DROP - COOLER_H

End Sub


' Cyclone dimensions by stage (C2 and C3 are C4).
Private Sub CycDims(ByVal s As Long, ByRef d As Double, ByRef hb As Double, ByRef hc As Double, _
                    ByRef vd As Double, ByRef dd As Double)
    Select Case s
        Case 1
            d = C1_D: hb = C1_HB: hc = C1_HC: vd = C1_VD: dd = C1_DD
        Case 2, 3, 4
            d = C4_D: hb = C4_HB: hc = C4_HC: vd = C4_VD: dd = C4_DD
        Case 5
            d = C5_D * c5Scale: hb = C5_HB * c5Scale: hc = C5_HC * c5Scale
            vd = C5_VD * c5Scale: dd = C5_DD * c5Scale
    End Select
End Sub


' Dust outlet to the top of the gas outlet stub.
Private Function CycHeight(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    CycHeight = hc + hb + OUTLET_STUB_OVER_VD * vd
End Function


Private Function RiserD(ByVal k As Long) As Double
    Select Case k
        Case 1: RiserD = R1_D
        Case 2: RiserD = R2_D
        Case 3: RiserD = R3_D
        Case 4: RiserD = R4_D
    End Select
End Function


' A tower meal route, route m: 1 = C1 +y, 2 = C1 -y, 3 = C2, 4 = C3.
' From the dust outlet out in -x past the barrel below, along y to
' the riser of the stage below, and back in +x onto its axis -- all
' at the meal slope. Its stage, pipe radius and four points.
Private Sub TowerMeal(ByVal m As Long, ByRef k As Long, ByRef rm As Double, _
                      px() As Double, py() As Double, pz() As Double)

    Dim yk As Double, off As Double

    Select Case m
        Case 1: k = 1: yk = yC1
        Case 2: k = 1: yk = -yC1
        Case 3: k = 2: yk = 0#
        Case 4: k = 3: yk = 0#
    End Select
    If k = 1 Then rm = 0.5 * C1_DD Else rm = 0.5 * C4_DD
    off = 0.5 * C4_D + rm + MEAL_CLEAR                 ' the stage below is C2-C4 alike

    px(0) = -TOWER_X: py(0) = yk: pz(0) = zDust(k)
    px(1) = -TOWER_X - off: py(1) = yk: pz(1) = pz(0) - off * mt
    px(2) = px(1): py(2) = yRiser(k + 1): pz(2) = pz(1) - Abs(py(2) - yk) * mt
    px(3) = -TOWER_X: py(3) = py(2): pz(3) = pz(2) - off * mt

End Sub


' Pre-check of one tower meal route: its first run falls past the
' first ball of the riser feeding its own stage, and it enters the
' riser of the stage below between that riser's corner and its roof.
Private Sub MealCheckTower(ByVal m As Long)

    Dim px(3) As Double, py(3) As Double, pz(3) As Double
    Dim k As Long, rm As Double, rr As Double, gap As Double, zLo As Double

    TowerMeal m, k, rm, px, py, pz
    rr = 0.5 * RiserD(k)
    gap = DistToSegment(-TOWER_X, 0#, zH(k), px(0), py(0), pz(0), px(1), py(1), pz(1)) - rr - rm
    If gap < MEAL_MIN_GAP Then
        Fail "meal route " & m & " from C" & k & " passes " & Fmt(gap) & " m from the first ball of R" & k & _
             ". Raise STAGE_GAP."
    End If
    rr = 0.5 * RiserD(k + 1)
    If k + 1 = 4 Then zLo = zH4 Else zLo = zH(k + 1)
    If pz(3) <= zLo - rr + rm Or pz(3) >= zRoof(k + 1) - rm Then
        Fail "meal route " & m & " from C" & k & " reaches the axis of R" & (k + 1) & " at z = " & Fmt(pz(3)) & _
             " m, outside the riser (z " & Fmt(zLo) & " .. " & Fmt(zRoof(k + 1)) & ")."
    End If

End Sub


' The C5 meal pipes: z where each turns at C5_MEAL_X (i = 0) and
' where it ends inside the chamber (i = 1).
Private Function C5MealZ(ByVal i As Long) As Double
    C5MealZ = zDust(5) - (C5_MEAL_X + x5) * mt
    If i = 1 Then C5MealZ = C5MealZ - (yLeg - aCh + MEAL_INTO_CHAMBER) * mt
End Function


' Raw meal pipe radius: the twin C1 outlets' area together.
Private Function RawMealR() As Double
    RawMealR = Sqr(2#) * 0.5 * C1_DD
End Function


' Distance from point Q to the segment A-B.
Private Function DistToSegment(ByVal qx As Double, ByVal qy As Double, ByVal qz As Double, _
                               ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                               ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double) As Double
    Dim dx As Double, dy As Double, dz As Double, t As Double
    dx = x1 - x0: dy = y1 - y0: dz = z1 - z0
    t = ((qx - x0) * dx + (qy - y0) * dy + (qz - z0) * dz) / (dx * dx + dy * dy + dz * dz)
    If t < 0# Then t = 0#
    If t > 1# Then t = 1#
    DistToSegment = Sqr((x0 + t * dx - qx) ^ 2 + (y0 + t * dy - qy) ^ 2 + (z0 + t * dz - qz) ^ 2)
End Function


Private Function CycVolume(ByVal s As Long) As Double
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim r As Double, rd As Double, rv As Double
    CycDims s, d, hb, hc, vd, dd
    r = 0.5 * d: rd = 0.5 * dd: rv = 0.5 * vd
    CycVolume = (PI / 3#) * hc * (r * r + r * rd + rd * rd) + PI * r * r * hb + _
                PI * rv * rv * OUTLET_STUB_OVER_VD * vd
End Function


'==================================================================
' (c) Pre-checks: nothing may run into anything else.
'==================================================================
Private Sub PreChecks()

    Dim r4 As Double, r5 As Double, zSide As Double
    Dim s As Long

    r4 = 0.5 * C4_D
    r5 = 0.5 * C5_D * c5Scale

    ' The tower column clear of the calciner and of the twin C5s
    If TOWER_X - r4 <= rCalc Then
        Fail "the tower (C2-C4, r " & Fmt(r4) & " m at x = " & Fmt(-TOWER_X) & ") runs into " & _
             "the calciner (r " & Fmt(rCalc) & " m). Raise TOWER_X."
    End If
    If Sqr((TOWER_X - x5) ^ 2 + yLeg ^ 2) <= r4 + r5 Then
        Fail "the tower column runs into the twin C5s. Raise TOWER_X."
    End If
    ' The twin C5s clear of the calciner, and above the chamber
    If Sqr(x5 * x5 + yLeg * yLeg) <= rCalc + r5 Then
        Fail "the twin C5s run into the calciner."
    End If
    If zDust(5) <= zThroat Then
        Fail "the C5 dust outlets at z = " & Fmt(zDust(5)) & " m are below the calciner's " & _
             "throat at z = " & Fmt(zThroat) & " m; the C5 meal could not fall to the kiln inlet."
    End If
    ' The cooler above ground
    If zCool0 <= 0# Then
        Fail "the cooler floor is at z = " & Fmt(zCool0) & " m, below ground. Raise KILN_AXIS_Z."
    End If
    ' The chamber has to hold the kiln's end and the throat
    If aCh <= rThroat Then Fail "the kiln inlet chamber is narrower than the calciner throat."

    ' Gas path: each riser's horizontal run passes under the dust
    ' outlet of the stage it feeds, R4's -y branch under C4's.
    For s = 1 To 3
        If zH(s) + 0.5 * RiserD(s) >= zDust(s) Then
            Fail "R" & s & " leaves the stage below at z = " & Fmt(zH(s)) & " m and runs into the " & _
                 "dust outlet of C" & s & " at z = " & Fmt(zDust(s)) & " m. Raise STAGE_GAP."
        End If
    Next s
    If zH4 + rB4 >= zDust(4) Then
        Fail "R4's branches at z = " & Fmt(zH4) & " m run into C4's dust outlet at z = " & _
             Fmt(zDust(4)) & " m. Raise STAGE_GAP."
    End If
    ' R4's branches start on the C5 stubs, clear of the gooseneck drops
    If x5 - rB4 <= rGn Then
        Fail "R4's branches on the C5 stubs run into the gooseneck drops."
    End If
    ' R1 rises clear of the twin C1, its distributor too
    If Sqr((xR1 + TOWER_X) ^ 2 + yC1 ^ 2) - 0.5 * C1_D - 0.5 * R1_D <= 0# Then
        Fail "the R1 riser at x = " & Fmt(xR1) & " m runs into the twin C1."
    End If
    If xR1 - rB1 <= -TOWER_X + 0.5 * C1_D Then
        Fail "the R1 distributor at x = " & Fmt(xR1) & " m runs into the twin C1."
    End If

    ' Meal path. C4 stands where its meal reaches the calciner feeds
    ' at the meal slope; that has to leave room for R4 under it.
    If zDust(4) < zTop(5) + STAGE_GAP Then
        Fail "C4's meal would reach the calciner feeds at " & Fmt(MEAL_SLOPE_DEG) & " deg with its dust " & _
             "outlet at z = " & Fmt(zDust(4)) & " m, less than STAGE_GAP over the C5 stubs (z = " & _
             Fmt(zTop(5) + STAGE_GAP) & " m). Lower STAGE_GAP or move the tower out."
    End If
    If C4_SPLIT_X <= -TOWER_X + 0.5 * C4_D Or C4_SPLIT_X >= -x5 + 0.5 * C5_D * c5Scale Then
        Fail "C4_SPLIT_X = " & Fmt(C4_SPLIT_X) & " m: C4's meal has to split between the tower and the twin C5s."
    End If
    If yFE - 0.5 * D_FEED <= rCalc Then Fail "the calciner feed pipes' ends lie inside the vessel."
    If zFS - 0.5 * D_FEED <= zThroat + CALC_THROAT_D + hCone Then
        Fail "the calciner feed pipes start at z = " & Fmt(zFS) & " m on the axis, down in the cone."
    End If
    ' Each tower meal pipe falls past the first ball of the riser that
    ' feeds its own stage, and enters the riser of the stage below.
    For s = 1 To 4
        MealCheckTower s
    Next s
    ' The C5 meal pipes turn inside the chamber's x range, pass the
    ' calciner, and cross the chamber's side wall below its roof
    zSide = C5MealZ(0) - (yLeg - aCh) * mt               ' where each crosses |y| = aCh
    If Abs(C5_MEAL_X) + 0.5 * C5_DD * c5Scale >= aCh Or C5_MEAL_X <= -x5 Then
        Fail "C5_MEAL_X = " & Fmt(C5_MEAL_X) & " m: the C5 meal pipes have to turn between the C5s and " & _
             "the chamber's -x face, inside the chamber's x range."
    End If
    If Sqr(C5_MEAL_X * C5_MEAL_X + aCh * aCh) <= rCalc + 0.5 * C5_DD * c5Scale Then
        Fail "the C5 meal pipes run into the calciner."
    End If
    If zSide - 0.5 * C5_DD * c5Scale <= zCh0 Or zSide + 0.5 * C5_DD * c5Scale >= zThroat Then
        Fail "the C5 meal pipes reach the chamber's side at z = " & Fmt(zSide) & " m, outside its wall z " & _
             Fmt(zCh0) & " .. " & Fmt(zThroat) & "."
    End If
    If C5MealZ(1) - 0.5 * C5_DD * c5Scale <= zCh0 Then
        Fail "the C5 meal pipes end at z = " & Fmt(C5MealZ(1)) & " m, through the chamber floor."
    End If
    ' Air path: the hood sits on the cooler and holds the kiln's end;
    ' the TA duct fits the calciner, enters above its cone, passes
    ' over the kiln and the chamber, and under the +y feed pipe.
    If Abs(zHood0 - (zCool0 + COOLER_H)) > BOX_TOL Then
        Fail "the kiln hood's floor at z = " & Fmt(zHood0) & " m is not on the cooler's roof at z = " & _
             Fmt(zCool0 + COOLER_H) & " m."
    End If
    If aCh <= 0.5 * KILN_D Then Fail "the kiln hood is narrower than the kiln."
    If rTA >= rCalc Then Fail "the tertiary air duct is wider than the calciner."
    If zTA - rTA < zThroat + CALC_THROAT_D + hCone - BOX_TOL Then
        Fail "the tertiary air duct enters the calciner below the top of its cone."
    End If
    If zTA - rTA <= zThroat Or zTA - rTA <= kAz + 0.5 * KILN_D Then
        Fail "the tertiary air duct at z = " & Fmt(zTA) & " m runs into the kiln or the inlet chamber."
    End If
    If zTA + rTA >= zFS + yTA * Tan(FEED_SLOPE_DEG * PI / 180#) - 0.5 * D_FEED Then
        Fail "the tertiary air duct runs into the +y calciner feed pipe."
    End If
    If xTA - rTA <= kBx Or xTA + rTA >= kBx + 2# * aCh Then
        Fail "the tertiary air duct does not leave from the kiln hood's roof."
    End If

    ' The raw meal pipe stays under R1's distributor
    If zRawIn + RAW_MEAL_L * Sin(MEAL_SLOPE_DEG * PI / 180#) + RawMealR() >= zR1Top - rB1 - MEAL_MIN_GAP Then
        Fail "the raw meal pipe into R1 reaches up into R1's distributor. Shorten RAW_MEAL_L."
    End If

    Note "kiln inlet chamber: |x|, |y| <= " & Fmt(aCh) & " m, z " & Fmt(zCh0) & " .. " & _
         Fmt(zCh0 + 2# * aCh) & " m"
    Note "calciner: z " & Fmt(zThroat) & " .. " & Fmt(zCalcRoof) & " m; gooseneck legs end at (0, +-" & _
         Fmt(yLeg) & ", " & Fmt(zLeg) & ")"
    Note "twin C5 at (" & Fmt(-x5) & ", +-" & Fmt(yLeg) & "), dust outlet z " & Fmt(zDust(5)) & " m"
    Note "tower at x = " & Fmt(-TOWER_X) & ": C4 / C3 / C2 / C1 dust outlets at z " & Fmt(zDust(4)) & _
         " / " & Fmt(zDust(3)) & " / " & Fmt(zDust(2)) & " / " & Fmt(zDust(1)) & " m, top " & _
         Fmt(zDust(1) + CycHeight(1)) & " m; twin C1 at y = +-" & Fmt(yC1)
    Note "kiln: (" & Fmt(kAx) & ", 0, " & Fmt(kAz) & ") -> (" & Fmt(kBx) & ", 0, " & Fmt(kBz) & ")"
    Note "gooseneck: rise (0, +-" & Fmt(yRise) & ") to z " & Fmt(zGnTop) & ", bend R " & Fmt(rGnBend) & _
         ", drop (0, +-" & Fmt(yLeg) & ") to z " & Fmt(zC5Barrel)
    Note "R4: branches D " & Fmt(2# * rB4) & " at z " & Fmt(zH4) & ", riser at (" & Fmt(-TOWER_X) & ", " & _
         Fmt(yRiser(4)) & ") to z " & Fmt(zRoof(4))
    Note "R3 / R2: along y at z " & Fmt(zH(3)) & " / " & Fmt(zH(2)) & ", risers at y " & _
         Fmt(yRiser(3)) & " / " & Fmt(yRiser(2))
    Note "R1: along x to " & Fmt(xR1) & " at z " & Fmt(zH(1)) & ", up to " & Fmt(zR1Top) & _
         ", branches D " & Fmt(2# * rB1) & " at y +-" & Fmt(yB1)
    Note "C1 exhaust: z " & Fmt(zExh) & ", x " & Fmt(-TOWER_X) & " .. " & Fmt(-TOWER_X - EXHAUST_L)
    Note "cooler: x " & Fmt(kBx) & " .. " & Fmt(kBx + coolL) & ", z " & Fmt(zCool0) & " .. " & _
         Fmt(zCool0 + COOLER_H) & " m"
    Note "calciner feed pipes: D " & Fmt(D_FEED) & ", ends (0, +-" & Fmt(yFE) & ", " & Fmt(zFE) & _
         "); C4 meal splits at (" & Fmt(C4_SPLIT_X) & ", 0, " & Fmt(zC4Split) & ")"
    Note "C5 meal: turns at x " & Fmt(C5_MEAL_X) & ", z " & Fmt(C5MealZ(0)) & ", ends at y +-" & _
         Fmt(aCh - MEAL_INTO_CHAMBER) & ", z " & Fmt(C5MealZ(1))
    Note "raw meal into R1 at z " & Fmt(zRawIn)
    Note "kiln hood: x " & Fmt(kBx) & " .. " & Fmt(kBx + 2# * aCh) & ", z " & Fmt(zHood0) & " .. " & _
         Fmt(zHood0 + 2# * aCh) & "; TA duct D " & Fmt(TA_D) & " up at (" & Fmt(xTA) & ", " & Fmt(yTA) & _
         ") to z " & Fmt(zTA) & ", along x to the calciner"

End Sub


'==================================================================
' (d) Build. Every feature makes a new body of its own (Merge off);
'     each is checked on the volume it adds and on its own box.
'
' The plant is walked TWICE by the same code. The first walk only
' registers the sketch planes each piece will need -- nothing is
' drawn -- so that every plane can be measured while the part is
' still empty (a calibration probe would merge with a body already
' there). The second walk draws. A plane cannot be forgotten: the
' walk that draws is the walk that listed them.
'==================================================================
Private Sub Build()

    Dim i As Long

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    oldVerify = swApp.GetUserPreferenceToggle(swPerformanceVerifyOnRebuild)
    oldInputDim = swApp.GetUserPreferenceToggle(swInputDimValOnCreate)
    swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, True
    swApp.SetUserPreferenceToggle swInputDimValOnCreate, False
    prefsTouched = True

    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    '--- 0. list every sketch plane, then measure each while empty ----
    nPl = 0
    registering = True
    BuildPlant
    registering = False
    phase = "measuring " & nPl & " sketch planes"
    For i = 0 To nPl - 1
        MakePlane i
    Next i

    phase = "building the plant"
    BuildPlant

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

End Sub


' The whole plant, in build order. Run once to register planes and
' once to draw.
Private Sub BuildPlant()

    Dim wx As Double, wz As Double, rk As Double
    Dim s As Long, k As Long, m As Long
    Dim sd As Double, rm As Double, rf As Double, zb As Double, yEnd As Double
    Dim px(3) As Double, py(3) As Double, pz(3) As Double
    Dim what As String

    '=== step 1: equipment ============================================

    '--- calciner: throat + cone + vessel ------------------------------
    RevolveVertical 0#, 0#, Array( _
        0#, zThroat, _
        rThroat, zThroat, _
        rThroat, zThroat + CALC_THROAT_D, _
        rCalc, zThroat + CALC_THROAT_D + hCone, _
        rCalc, zCalcRoof, _
        0#, zCalcRoof)
    CheckAdded "calciner", _
        PI * rThroat * rThroat * CALC_THROAT_D + _
        (PI / 3#) * hCone * (rCalc * rCalc + rCalc * rThroat + rThroat * rThroat) + _
        PI * rCalc * rCalc * (CALC_H - hCone), _
        -rCalc, -rCalc, zThroat, rCalc, rCalc, zCalcRoof

    '--- cyclones -----------------------------------------------------
    BuildCyclone "C5 +y", 5, -x5, yLeg
    BuildCyclone "C5 -y", 5, -x5, -yLeg
    For s = 4 To 2 Step -1
        BuildCyclone "C" & s, s, -TOWER_X, 0#
    Next s
    BuildCyclone "C1 +y", 1, -TOWER_X, yC1
    BuildCyclone "C1 -y", 1, -TOWER_X, -yC1

    '--- kiln inlet chamber ---------------------------------------------
    ExtrudeBox "kiln inlet chamber", zCh0, -aCh, aCh, -aCh, aCh, 2# * aCh

    '--- kiln: a rectangle in y = 0 revolved about its axis edge ------
    rk = 0.5 * KILN_D
    wx = Sin(kAlpha): wz = Cos(kAlpha)          ' normal to the axis, upward
    RevolveQuad 1, 0#, Array(kAx, 0#, kAz, kBx, 0#, kBz, kBx + rk * wx, 0#, kBz + rk * wz, _
                             kAx + rk * wx, 0#, kAz + rk * wz)
    CheckAdded "kiln", PI * rk * rk * KILN_L, _
        kAx - rk * wx, -rk, kBz - rk * wz, kBx + rk * wx, rk, kAz + rk * wz

    '--- cooler ---------------------------------------------------------
    ExtrudeBox "cooler", zCool0, kBx, kBx + coolL, -0.5 * COOLER_W, 0.5 * COOLER_W, COOLER_H

    '=== step 2: the gas path ===========================================

    '--- calciner -> twin C5: the twin gooseneck -----------------------
    For k = 0 To 1
        sd = 1# - 2# * k
        Link "gas: calciner -> C5 " & SideName(sd) & " over the gooseneck"
        Cylinder 0#, sd * yRise, zCalcRoof, 0#, sd * yRise, zGnTop, rGn, "gooseneck rise " & SideName(sd)
        GooseneckBend sd
        Cylinder 0#, sd * yLeg, zGnTop, 0#, sd * yLeg, zC5Barrel, rGn, "gooseneck drop " & SideName(sd)
    Next k

    '--- twin C5 -> C4: two branches meet at the foot of R4 --------------
    For k = 0 To 1
        sd = 1# - 2# * k
        Link "gas: C5 " & SideName(sd) & " -> R4 foot"
        Ball -x5, sd * yLeg, zH4, rB4, "R4 branch start " & SideName(sd)
        Cylinder -x5, sd * yLeg, zH4, -TOWER_X, sd * yLeg, zH4, rB4, "R4 branch along x " & SideName(sd)
        Ball -TOWER_X, sd * yLeg, zH4, rB4, "R4 branch corner " & SideName(sd)
        Cylinder -TOWER_X, sd * yLeg, zH4, -TOWER_X, yRiser(4), zH4, rB4, "R4 branch along y " & SideName(sd)
    Next k
    Link "gas: R4 -> C4"
    Ball -TOWER_X, yRiser(4), zH4, 0.5 * R4_D, "R4 foot"
    Cylinder -TOWER_X, yRiser(4), zH4, -TOWER_X, yRiser(4), zRoof(4), 0.5 * R4_D, "R4 riser"

    '--- C4 -> C3 and C3 -> C2: over the stub, out in +y, up the side ---
    For k = 3 To 2 Step -1
        Link "gas: C" & (k + 1) & " -> R" & k & " -> C" & k
        Ball -TOWER_X, 0#, zH(k), 0.5 * RiserD(k), "R" & k & " start"
        Cylinder -TOWER_X, 0#, zH(k), -TOWER_X, yRiser(k), zH(k), 0.5 * RiserD(k), "R" & k & " along y"
        Ball -TOWER_X, yRiser(k), zH(k), 0.5 * RiserD(k), "R" & k & " corner"
        Cylinder -TOWER_X, yRiser(k), zH(k), -TOWER_X, yRiser(k), zRoof(k), 0.5 * RiserD(k), "R" & k & " riser"
    Next k

    '--- C2 -> twin C1: out in +x, up, a distributor, two branches -----
    Link "gas: C2 -> R1 -> twin C1"
    Ball -TOWER_X, 0#, zH(1), 0.5 * R1_D, "R1 start"
    Cylinder -TOWER_X, 0#, zH(1), xR1, 0#, zH(1), 0.5 * R1_D, "R1 along x"
    Ball xR1, 0#, zH(1), 0.5 * R1_D, "R1 corner"
    Cylinder xR1, 0#, zH(1), xR1, 0#, zR1Top, 0.5 * R1_D, "R1 riser"
    Ball xR1, 0#, zR1Top, 0.5 * R1_D, "R1 head"
    Cylinder xR1, -yB1, zR1Top, xR1, yB1, zR1Top, rB1, "R1 distributor"
    For k = 0 To 1
        sd = 1# - 2# * k
        Ball xR1, sd * yB1, zR1Top, rB1, "R1 branch corner " & SideName(sd)
        Cylinder xR1, sd * yB1, zR1Top, -TOWER_X, sd * yB1, zR1Top, rB1, "R1 branch " & SideName(sd)
    Next k

    '--- twin C1 -> exhaust ----------------------------------------------
    For k = 0 To 1
        sd = 1# - 2# * k
        Link "gas: C1 " & SideName(sd) & " -> exhaust (to the fan)"
        Ball -TOWER_X, sd * yC1, zExh, 0.5 * C1_VD, "exhaust start " & SideName(sd)
        Cylinder -TOWER_X, sd * yC1, zExh, -TOWER_X - EXHAUST_L, sd * yC1, zExh, 0.5 * C1_VD, _
                 "exhaust " & SideName(sd)
    Next k

    '=== step 3: the meal path ==========================================

    '--- raw meal into R1, half way up its riser -------------------------
    Link "meal: raw meal (from the silo) -> R1"
    Cylinder xR1 + RAW_MEAL_L * Cos(MEAL_SLOPE_DEG * PI / 180#), 0#, _
             zRawIn + RAW_MEAL_L * Sin(MEAL_SLOPE_DEG * PI / 180#), _
             xR1, 0#, zRawIn, RawMealR(), "raw meal feed"

    '--- tower: C1 -> R2, C2 -> R3, C3 -> R4 ------------------------------
    For m = 1 To 4
        TowerMeal m, k, rm, px, py, pz
        what = "C" & k
        If k = 1 Then what = what & " " & SideName(py(0))
        Link "meal: " & what & " -> R" & (k + 1)
        Cylinder px(0), py(0), pz(0), px(1), py(1), pz(1), rm, what & " meal out"
        Ball px(1), py(1), pz(1), rm, what & " meal corner 1"
        Cylinder px(1), py(1), pz(1), px(2), py(2), pz(2), rm, what & " meal along y"
        Ball px(2), py(2), pz(2), rm, what & " meal corner 2"
        Cylinder px(2), py(2), pz(2), px(3), py(3), pz(3), rm, what & " meal into R" & (k + 1)
    Next m

    '--- C4 -> the calciner's two feed pipes ------------------------------
    Link "meal: C4 -> split -> calciner feed pipes +y and -y"
    rm = 0.5 * C4_DD
    rf = 0.5 * D_FEED
    Cylinder -TOWER_X, 0#, zDust(4), C4_SPLIT_X, 0#, zC4Split, rm, "C4 meal out"
    Ball C4_SPLIT_X, 0#, zC4Split, rm, "C4 meal split"
    For k = 0 To 1
        sd = 1# - 2# * k
        zb = zC4Split - yFE * mt
        Cylinder C4_SPLIT_X, 0#, zC4Split, C4_SPLIT_X, sd * yFE, zb, rf, "C4 meal branch " & SideName(sd)
        Ball C4_SPLIT_X, sd * yFE, zb, rf, "C4 meal branch corner " & SideName(sd)
        Cylinder C4_SPLIT_X, sd * yFE, zb, 0#, sd * yFE, zFE, rf, "C4 meal to feed " & SideName(sd)
        Ball 0#, sd * yFE, zFE, rf, "calciner feed end " & SideName(sd)
        Cylinder 0#, sd * yFE, zFE, 0#, 0#, zFS, rf, "calciner feed pipe " & SideName(sd)
    Next k

    '--- twin C5 -> kiln inlet chamber --------------------------------------
    rm = 0.5 * C5_DD * c5Scale
    yEnd = aCh - MEAL_INTO_CHAMBER
    For k = 0 To 1
        sd = 1# - 2# * k
        Link "meal: C5 " & SideName(sd) & " -> kiln inlet chamber"
        Cylinder -x5, sd * yLeg, zDust(5), C5_MEAL_X, sd * yLeg, C5MealZ(0), rm, "C5 meal out " & SideName(sd)
        Ball C5_MEAL_X, sd * yLeg, C5MealZ(0), rm, "C5 meal corner " & SideName(sd)
        Cylinder C5_MEAL_X, sd * yLeg, C5MealZ(0), C5_MEAL_X, sd * yEnd, C5MealZ(1), rm, _
                 "C5 meal into the chamber " & SideName(sd)
    Next k

    '=== step 4: the air path ===========================================

    '--- kiln hood over the cooler's hot end ------------------------------
    ExtrudeBox "kiln hood", zHood0, kBx, kBx + 2# * aCh, -aCh, aCh, 2# * aCh
    Link "air: cooler -> kiln hood -> kiln (secondary air)"

    '--- tertiary air: hood roof -> up -> back over the kiln -> calciner ----
    Link "air: cooler -> kiln hood -> tertiary air duct -> calciner (tangential, +y)"
    Cylinder xTA, yTA, zHood0 + 2# * aCh, xTA, yTA, zTA, rTA, "tertiary air rise"
    Ball xTA, yTA, zTA, rTA, "tertiary air corner"
    Cylinder xTA, yTA, zTA, 0#, yTA, zTA, rTA, "tertiary air duct"

End Sub


Private Function SideName(ByVal sd As Double) As String
    If sd > 0# Then SideName = "+y" Else SideName = "-y"
End Function


' A line in the log's connection list.
Private Sub Link(ByVal what As String)
    If Not registering Then Note "-- " & what
End Sub


' One cyclone as a single body: cone from its dust outlet, barrel,
' roof, and a gas outlet stub of the vortex finder's diameter. Its
' axis is vertical through (xc, yc).
Private Sub BuildCyclone(ByVal what As String, ByVal s As Long, ByVal xc As Double, ByVal yc As Double)

    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    Dim r As Double, z0 As Double, zr As Double, zt As Double

    CycDims s, d, hb, hc, vd, dd
    r = 0.5 * d
    z0 = zDust(s)
    zr = z0 + hc + hb
    zt = z0 + CycHeight(s)

    RevolveVertical xc, yc, Array( _
        0#, z0, _
        0.5 * dd, z0, _
        r, z0 + hc, _
        r, zr, _
        0.5 * vd, zr, _
        0.5 * vd, zt, _
        0#, zt)
    CheckAdded what, CycVolume(s), xc - r, yc - r, z0, xc + r, yc + r, zt

End Sub


' A closed profile given as (r, z) pairs about the vertical axis
' through (xc, yc), drawn on the plane y = yc. The profile's own
' segment on the axis is the axis of revolution.
Private Sub RevolveVertical(ByVal xc As Double, ByVal yc As Double, pts As Variant)

    Dim n As Long, i As Long, j As Long, ip As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim seg As SldWorks.SketchSegment, axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature

    ip = PlaneOf(1, yc)
    If registering Then Exit Sub
    uSign = plU(ip): vSign = plV(ip)
    n = (UBound(pts) + 1) \ 2

    Set sk = OpenSketch(ip)
    For i = 0 To n - 1
        j = (i + 1) Mod n
        G2S sk, xc + pts(2 * i), yc, pts(2 * i + 1), u0, v0
        G2S sk, xc + pts(2 * j), yc, pts(2 * j + 1), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on a revolve profile."
        If pts(2 * i) = 0# And pts(2 * j) = 0# Then Set axisSeg = seg
    Next i
    If axisSeg Is Nothing Then Fail "a vertical revolve profile has no segment on its axis."

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")
    If RevolveSketch(skFeat, axisSeg, 2# * PI, False) Is Nothing Then
        Fail "FeatureRevolve2 failed on a vertical revolve."
    End If

End Sub


' A quadrilateral given as four (x, y, z) points lying in the plane
' of axis ax (0 = x, 1 = y) at coordinate at, revolved a full turn
' about its FIRST edge: a cylinder along that edge.
Private Sub RevolveQuad(ByVal ax As Long, ByVal at As Double, pts As Variant)

    Dim i As Long, j As Long, ip As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim seg As SldWorks.SketchSegment, axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature

    ip = PlaneOf(ax, at)
    If registering Then Exit Sub
    uSign = plU(ip): vSign = plV(ip)

    Set sk = OpenSketch(ip)
    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, pts(3 * i), pts(3 * i + 1), pts(3 * i + 2), u0, v0
        G2S sk, pts(3 * j), pts(3 * j + 1), pts(3 * j + 2), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on a revolve profile."
        If i = 0 Then Set axisSeg = seg
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")
    If RevolveSketch(skFeat, axisSeg, 2# * PI, False) Is Nothing Then
        Fail "FeatureRevolve2 failed on a cylinder."
    End If

End Sub


' A straight pipe from P0 to P1, lying in a plane y = const or
' x = const: along x, y or z, or sloping in x-z or y-z. Its
' half-section, from the axis out r along the in-plane normal, is
' drawn in that plane and revolved a full turn about the axis. Its
' box: the ends, widened along each axis i by r sqrt(1 - e_i^2) for
' the axis direction e -- r across a straight pipe, 0 along it.
Private Sub Cylinder(ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                     ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double, _
                     ByVal r As Double, ByVal what As String)

    Dim ex As Double, ey As Double, ez As Double, L As Double
    Dim nx As Double, ny As Double, nz As Double
    Dim ax As Long, at As Double
    Dim wx As Double, wy As Double, wz As Double

    L = Sqr((x1 - x0) ^ 2 + (y1 - y0) ^ 2 + (z1 - z0) ^ 2)
    If L <= 0# Then Fail what & " has no length."
    ex = (x1 - x0) / L: ey = (y1 - y0) / L: ez = (z1 - z0) / L

    If Abs(y1 - y0) < 0.000000001 Then
        ax = 1: at = y0: nx = -ez * r: ny = 0#: nz = ex * r      ' in y = y0
    ElseIf Abs(x1 - x0) < 0.000000001 Then
        ax = 0: at = x0: nx = 0#: ny = -ez * r: nz = ey * r      ' in x = x0
    Else
        Fail what & ": a pipe has to lie in a plane x = const or y = const."
    End If

    RevolveQuad ax, at, Array(x0, y0, z0, x1, y1, z1, x1 + nx, y1 + ny, z1 + nz, x0 + nx, y0 + ny, z0 + nz)
    If registering Then Exit Sub

    wx = r * Sqr(Max2(0#, 1# - ex * ex))
    wy = r * Sqr(Max2(0#, 1# - ey * ey))
    wz = r * Sqr(Max2(0#, 1# - ez * ez))
    CheckAdded what, PI * r * r * L, _
        Min2(x0, x1) - wx, Min2(y0, y1) - wy, Min2(z0, z1) - wz, _
        Max2(x0, x1) + wx, Max2(y0, y1) + wy, Max2(z0, z1) + wz

End Sub


' A ball joint at C: a half disc with a vertical diameter, drawn in
' the plane y = cy and revolved about that diameter. Which side the
' half disc is drawn on does not matter -- both sides turn into the
' same ball.
Private Sub Ball(ByVal cx As Double, ByVal cy As Double, ByVal cz As Double, ByVal r As Double, _
                 ByVal what As String)

    Dim ip As Long
    Dim ua As Double, va As Double, ub As Double, vb As Double, um As Double, vm As Double
    Dim axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature

    ip = PlaneOf(1, cy)
    If registering Then Exit Sub
    uSign = plU(ip): vSign = plV(ip)

    Set sk = OpenSketch(ip)
    G2S sk, cx, cy, cz + r, ua, va
    G2S sk, cx, cy, cz - r, ub, vb
    G2S sk, cx + r, cy, cz, um, vm
    Set axisSeg = swSkMgr.CreateLine(ua, va, 0#, ub, vb, 0#)
    If axisSeg Is Nothing Then Fail "CreateLine failed on " & what & "."
    If swSkMgr.Create3PointArc(ua, va, 0#, ub, vb, 0#, um, vm, 0#) Is Nothing Then
        Fail "Create3PointArc failed on " & what & "."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")
    If RevolveSketch(skFeat, axisSeg, 2# * PI, False) Is Nothing Then
        Fail "FeatureRevolve2 failed on " & what & "."
    End If
    CheckAdded what, (4# / 3#) * PI * r * r * r, cx - r, cy - r, cz - r, cx + r, cy + r, cz + r

End Sub


' One gooseneck bend, side sd = +1 or -1: the leg's disc at
' (0, sd yRise) in the plane z = zGnTop revolved 180 deg about the
' line through (0, sd (yRise + rGnBend), zGnTop) parallel to x -- the
' calciner.bas bend, turned into the y-z plane. It leaves the rise
' going up, goes over and comes down at y = sd yLeg. Turned the wrong
' way it swings down into the calciner, and its box says so; it is
' then taken out and turned the other way.
Private Sub GooseneckBend(ByVal sd As Double)

    Dim ip As Long, k As Long, i As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim segs As Variant
    Dim axisSeg As SldWorks.SketchSegment
    Dim f As SldWorks.Feature
    Dim y0 As Double, y1 As Double
    Dim what As String

    ip = PlaneOf(2, zGnTop)
    If registering Then Exit Sub
    uSign = plU(ip): vSign = plV(ip)
    what = "gooseneck bend " & SideName(sd)

    Set sk = OpenSketch(ip)
    G2S sk, 0#, sd * yRise, zGnTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rGn) Is Nothing Then
        Fail "CreateCircleByRadius failed on the " & what & "."
    End If
    G2S sk, -1#, sd * (yRise + rGnBend), zGnTop, u0, v0
    G2S sk, 1#, sd * (yRise + rGnBend), zGnTop, u1, v1
    If swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateCenterLine failed on the " & what & "."
    End If
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    y0 = Min2(sd * (yRise - rGn), sd * (yLeg + rGn))
    y1 = Max2(sd * (yRise - rGn), sd * (yLeg + rGn))

    For k = 0 To 1
        Set sk = skFeat.GetSpecificFeature2
        segs = sk.GetSketchSegments
        Set axisSeg = Nothing
        For i = 0 To UBound(segs)
            If segs(i).ConstructionGeometry Then Set axisSeg = segs(i)
        Next i
        If axisSeg Is Nothing Then Fail "the " & what & " sketch has lost its axis."

        Set f = RevolveSketch(skFeat, axisSeg, PI, (k = 1))
        If Not f Is Nothing Then
            If HasBodyWithBox(-rGn, y0, zGnTop, rGn, y1, zGnTop + rGnBend + rGn) Then
                CheckAdded what, PI * rGn * rGn * (PI * rGnBend), -rGn, y0, zGnTop, rGn, y1, _
                           zGnTop + rGnBend + rGn
                Exit Sub
            End If
            Note what & " turned the wrong way; reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k

    Fail "the " & what & " could not be revolved over the top in either direction."

End Sub


' Revolve a closed sketch about one of its segments by angle, as a
' NEW body: merge off, so equipment that touches stays apart.
Private Function RevolveSketch(skFeat As SldWorks.Feature, axisSeg As SldWorks.SketchSegment, _
                               ByVal angle As Double, ByVal reverse As Boolean) As SldWorks.Feature

    Dim selData As SldWorks.SelectData

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set RevolveSketch = swFeat.FeatureRevolve2( _
        True, True, False, False, reverse, False, _
        0, 0, angle, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    swModel.ClearSelection2 True

End Function


' A box standing on the plane z = zb: the rectangle x0..x1, y0..y1
' extruded h up as a new body. Extruded down instead, its box says
' so, and it is taken back out and extruded the other way.
Private Sub ExtrudeBox(ByVal what As String, ByVal zb As Double, _
                       ByVal x0 As Double, ByVal x1 As Double, ByVal y0 As Double, ByVal y1 As Double, _
                       ByVal h As Double)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim qx(3) As Double, qy(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim i As Long, j As Long, k As Long, ip As Long

    ip = PlaneOf(2, zb)
    If registering Then Exit Sub
    uSign = plU(ip): vSign = plV(ip)
    qx(0) = x0: qy(0) = y0: qx(1) = x1: qy(1) = y0
    qx(2) = x1: qy(2) = y1: qx(3) = x0: qy(3) = y1

    Set sk = OpenSketch(ip)
    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, qx(i), qy(i), zb, u0, v0
        G2S sk, qx(j), qy(j), zb, u1, v1
        If swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
            Fail "CreateLine failed on the " & what & " outline."
        End If
    Next i
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            h, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            False, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            If HasBodyWithBox(x0, y0, zb, x1, y1, zb + h) Then
                CheckAdded what, (x1 - x0) * (y1 - y0) * h, x0, y0, zb, x1, y1, zb + h
                Exit Sub
            End If
            Note what & " extruded the wrong way; reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
    Next k

    Fail "the " & what & " could not be extruded up from z = " & Fmt(zb) & " m in either direction."

End Sub


'------------------------------------------------------------------
' Sketch plane registry. A plane is (axis, coordinate): axis 0 is
' x = at, 1 is y = at, 2 is z = at. The registering walk adds each
' one once; MakePlane builds and measures it; PlaneOf finds it.
'------------------------------------------------------------------
Private Function PlaneOf(ByVal ax As Long, ByVal at As Double) As Long

    Dim i As Long

    For i = 0 To nPl - 1
        If plAx(i) = ax And Abs(plAt(i) - at) < 0.000001 Then
            PlaneOf = i
            Exit Function
        End If
    Next i
    If Not registering Then
        Fail "no sketch plane was registered at " & Mid("xyz", ax + 1, 1) & " = " & Fmt(at) & _
             "; the registering walk and the drawing walk disagree."
    End If
    If nPl > UBound(plAx) Then Fail "more than " & (UBound(plAx) + 1) & " sketch planes."
    plAx(nPl) = ax: plAt(nPl) = at
    PlaneOf = nPl
    nPl = nPl + 1

End Function


Private Sub MakePlane(ByVal i As Long)

    Dim base As SldWorks.Feature
    Dim bx As Double, by As Double, bz As Double

    Select Case plAx(i)
        Case 0: Set base = FindPlaneWithNormal(1#, 0#, 0#): bx = plAt(i)
        Case 1: Set base = FindPlaneWithNormal(0#, 1#, 0#): by = plAt(i)
        Case 2: Set base = FindPlaneWithNormal(0#, 0#, 1#): bz = plAt(i)
    End Select
    If base Is Nothing Then Fail "could not find a default plane."

    If Abs(plAt(i)) < 0.000001 Then
        Set pl(i) = base
        CalibrateSketchAxes pl(i), 0#, 0#, 0#, plU(i), plV(i)
    Else
        Set pl(i) = OffsetPlane(base, bx, by, bz, plU(i), plV(i))
    End If

End Sub


Private Function Min2(ByVal a As Double, ByVal b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function

Private Function Max2(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function


Private Function OpenSketch(ByVal ip As Long) As SldWorks.Sketch
    swModel.ClearSelection2 True
    pl(ip).Select2 False, 0
    swSkMgr.InsertSketch True
    Set OpenSketch = swSkMgr.ActiveSketch
    If OpenSketch Is Nothing Then Fail "could not open a sketch on plane " & ip & "."
    wRefSet = False
End Function


'==================================================================
' (f) Verification. The part must hold exactly one more body than
'     before, the total volume must grow by the new body's closed
'     form, and one body must sit exactly in the expected box -- so
'     a body in the wrong place, the wrong size or merged into its
'     neighbour is caught at the step that made it.
'==================================================================
Private Sub CheckAdded(ByVal what As String, ByVal vAdd As Double, _
                       ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                       ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double)

    Static vBefore As Double
    Dim got As Double, total As Double

    If registering Then Exit Sub
    If nBodies = 0 Then vBefore = 0#
    nBodies = nBodies + 1
    If BodyCount() <> nBodies Then
        Fail what & ": the part holds " & BodyCount() & " bodies, expected " & nBodies & _
             ". It merged into a neighbour or split."
    End If

    total = BodiesVolume()
    got = total - vBefore
    Note what & ": " & Fmt(got) & " m3 (expected " & Fmt(vAdd) & ")"
    If Abs(got - vAdd) > VOL_TOL * vAdd Then
        Fail what & " is " & Fmt(got) & " m3 but should be " & Fmt(vAdd) & " m3."
    End If
    vBefore = total

    If Not HasBodyWithBox(x0, y0, z0, x1, y1, z1) Then
        Fail what & ": no body sits in the box (" & Fmt(x0) & ", " & Fmt(y0) & ", " & Fmt(z0) & _
             ") .. (" & Fmt(x1) & ", " & Fmt(y1) & ", " & Fmt(z1) & ")."
    End If

End Sub


' GetBodyBox may be loose round a sloping body, so it only picks the
' candidates -- a body whose loose box holds the expected one -- and
' each candidate's tight box is measured with GetExtremePoint.
Private Function HasBodyWithBox(ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                                ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double) As Boolean

    Dim bodies As Variant, b As Variant
    Dim bd As SldWorks.Body2
    Dim i As Long
    Dim t(5) As Double, px As Double, py As Double, pz As Double

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    For i = 0 To UBound(bodies)
        Set bd = bodies(i)
        b = bd.GetBodyBox
        If b(0) < x0 + BOX_TOL And b(1) < y0 + BOX_TOL And b(2) < z0 + BOX_TOL And _
           b(3) > x1 - BOX_TOL And b(4) > y1 - BOX_TOL And b(5) > z1 - BOX_TOL Then
            bd.GetExtremePoint -1#, 0#, 0#, px, py, pz: t(0) = px
            bd.GetExtremePoint 0#, -1#, 0#, px, py, pz: t(1) = py
            bd.GetExtremePoint 0#, 0#, -1#, px, py, pz: t(2) = pz
            bd.GetExtremePoint 1#, 0#, 0#, px, py, pz: t(3) = px
            bd.GetExtremePoint 0#, 1#, 0#, px, py, pz: t(4) = py
            bd.GetExtremePoint 0#, 0#, 1#, px, py, pz: t(5) = pz
            If Abs(t(0) - x0) < BOX_TOL And Abs(t(1) - y0) < BOX_TOL And Abs(t(2) - z0) < BOX_TOL And _
               Abs(t(3) - x1) < BOX_TOL And Abs(t(4) - y1) < BOX_TOL And Abs(t(5) - z1) < BOX_TOL Then
                HasBodyWithBox = True
                Exit Function
            End If
        End If
    Next i

End Function


Private Function BodyCount() As Long
    Dim bodies As Variant
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    BodyCount = UBound(bodies) + 1
End Function


Private Function BodiesVolume() As Double
    Dim bodies As Variant, mp As Variant
    Dim i As Long
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    For i = 0 To UBound(bodies)
        mp = bodies(i).GetMassProperties(1000#)
        BodiesVolume = BodiesVolume + mp(3)
    Next i
End Function


'==================================================================
' Sketch plane mapping -- copied from cyclone.bas / calciner.bas,
' where the reasons are written out in full: points are given in
' MODEL coordinates and put through the plane's own transform, the
' off-plane component is compared against the sketch's first point,
' and which way a plane's axes run -- and where the plane really is --
' is measured with a test block, never read.
'==================================================================
Private Sub G2S(sk As SldWorks.Sketch, ByVal gx As Double, ByVal gy As Double, ByVal gz As Double, _
                ByRef u As Double, ByRef v As Double)

    Dim a As Variant, s As Double, w As Double

    a = sk.ModelToSketchTransform.ArrayData
    s = a(12)
    u = ((a(0) * gx + a(1) * gy + a(2) * gz) * s + a(9)) * uSign
    v = ((a(3) * gx + a(4) * gy + a(5) * gz) * s + a(10)) * vSign
    w = (a(6) * gx + a(7) * gy + a(8) * gz) * s + a(11)

    If Not wRefSet Then
        wRef = w
        wRefSet = True
    ElseIf Abs(w - wRef) > PLANE_TOL Then
        Fail "point (" & Fmt(gx) & ", " & Fmt(gy) & ", " & Fmt(gz) & ") lies " & _
             Fmt(w - wRef) & " m off the plane of the other points in its sketch."
    End If

End Sub


Private Function OffsetPlane(base As SldWorks.Feature, _
                             ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                             ByRef us As Double, ByRef vs As Double) As SldWorks.Feature

    Dim p As SldWorks.Feature
    Dim opt As Long
    Dim k As Long
    Dim at As String

    at = "(" & Fmt(bx) & ", " & Fmt(by) & ", " & Fmt(bz) & ")"

    For k = 0 To 1
        opt = swRefPlaneReferenceConstraint_Distance
        If k = 1 Then opt = opt Or swRefPlaneReferenceConstraint_OptionFlip

        swModel.ClearSelection2 True
        base.Select2 False, 0
        Set p = swFeat.InsertRefPlane(opt, Abs(bx) + Abs(by) + Abs(bz), 0, 0#, 0, 0#)
        swModel.ClearSelection2 True
        If p Is Nothing Then Fail "InsertRefPlane failed for the offset plane through " & at & "."

        If TryCalibrateSketchAxes(p, bx, by, bz, us, vs) Then
            Note "offset plane measured through " & at
            Set OffsetPlane = p
            Exit Function
        End If

        swModel.ClearSelection2 True
        p.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    Next k

    Fail "the offset plane could not be placed through " & at & "; a test block " & _
         "dropped on it landed somewhere else both ways round."

End Function


Private Sub CalibrateSketchAxes(p As SldWorks.Feature, _
                                ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                ByRef us As Double, ByRef vs As Double)
    If Not TryCalibrateSketchAxes(p, bx, by, bz, us, vs) Then
        Fail "sketch axis calibration failed on plane " & p.Name & "."
    End If
End Sub


Private Function TryCalibrateSketchAxes(p As SldWorks.Feature, _
                                        ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                        ByRef us As Double, ByRef vs As Double) As Boolean

    Dim mx As Double, my As Double, mz As Double
    Dim i1 As Long, i2 As Long
    Dim p0(2) As Double, p1(2) As Double
    Dim k As Long

    PlaneNormal p, mx, my, mz
    If Abs(mx) > 0.9 Then
        i1 = 1: i2 = 2
    ElseIf Abs(my) > 0.9 Then
        i1 = 0: i2 = 2
    ElseIf Abs(mz) > 0.9 Then
        i1 = 0: i2 = 1
    Else
        Fail "sketch axis calibration: the plane normal is not a model axis."
    End If

    p0(0) = bx: p0(1) = by: p0(2) = bz
    p1(0) = bx: p1(1) = by: p1(2) = bz
    p0(i1) = p0(i1) + 1#: p1(i1) = p1(i1) + 2#
    p0(i2) = p0(i2) + 3#: p1(i2) = p1(i2) + 5#

    For k = 0 To 3
        us = 1#: If (k And 1) <> 0 Then us = -1#
        vs = 1#: If (k And 2) <> 0 Then vs = -1#
        If ProbeLandsWhereAsked(p, p0, p1, i1, i2, us, vs) Then
            Note "sketch axes on plane " & p.Name & ": u x " & Fmt(us) & ", v x " & Fmt(vs)
            TryCalibrateSketchAxes = True
            Exit Function
        End If
    Next k

End Function


Private Function ProbeLandsWhereAsked(p As SldWorks.Feature, p0() As Double, p1() As Double, _
                                      ByVal i1 As Long, ByVal i2 As Long, _
                                      ByVal us As Double, ByVal vs As Double) As Boolean

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim bodies As Variant, box As Variant
    Dim i3 As Long
    Dim ok As Boolean

    uSign = us: vSign = vs

    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "sketch axis calibration was asked to run with bodies already in the part."
    End If

    swModel.ClearSelection2 True
    p.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch axis calibration sketch."
    wRefSet = False

    G2S sk, p0(0), p0(1), p0(2), u0, v0
    G2S sk, p1(0), p1(1), p1(2), u1, v1
    swSkMgr.CreateLine u0, v0, 0#, u1, v0, 0#
    swSkMgr.CreateLine u1, v0, 0#, u1, v1, 0#
    swSkMgr.CreateLine u1, v1, 0#, u0, v1, 0#
    swSkMgr.CreateLine u0, v1, 0#, u0, v0, 0#
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondBlind, swEndCondBlind, 0.5, 0.01, _
        False, False, False, False, 0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True

    If f Is Nothing Then
        ok = False
    Else
        bodies = swPart.GetBodies2(swSolidBody, True)
        If IsEmpty(bodies) Then
            ok = False
        Else
            box = bodies(0).GetBodyBox
            i3 = 3 - i1 - i2
            ok = Near(box(i1), p0(i1)) And Near(box(i1 + 3), p1(i1)) And _
                 Near(box(i2), p0(i2)) And Near(box(i2 + 3), p1(i2)) And _
                 (Near(box(i3), p0(i3)) Or Near(box(i3 + 3), p0(i3)))
        End If
        swModel.ClearSelection2 True
        f.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    End If

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    swModel.EditDelete
    swModel.ClearSelection2 True

    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then Fail "a sketch axis calibration probe could not be removed."

    ProbeLandsWhereAsked = ok

End Function


Private Function Near(ByVal a As Double, ByVal b As Double) As Boolean
    Near = (Abs(a - b) < 0.001)
End Function


Private Sub PlaneNormal(p As SldWorks.Feature, ByRef mx As Double, ByRef my As Double, ByRef mz As Double)
    Dim sk As SldWorks.Sketch
    Dim a As Variant
    swModel.ClearSelection2 True
    p.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a probe sketch on a reference plane."
    a = sk.ModelToSketchTransform.ArrayData
    mx = a(6): my = a(7): mz = a(8)
    swSkMgr.InsertSketch True
    swModel.ClearSelection2 True
End Sub


' The default plane whose normal is the given direction, found by
' probing rather than by name -- plane names are localised.
Private Function FindPlaneWithNormal(ByVal vx As Double, ByVal vy As Double, ByVal vz As Double) As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim mx As Double, my As Double, mz As Double
    Set f = swModel.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then
            PlaneNormal f, mx, my, mz
            If Abs(Abs(mx * vx + my * vy + mz * vz) - 1#) < DIR_TOL Then
                Set FindPlaneWithNormal = f
                Exit Function
            End If
        End If
        Set f = f.GetNextFeature
    Loop
End Function


Private Function LastFeature(ByVal typeName As String) As SldWorks.Feature
    Dim f As SldWorks.Feature
    Set f = swModel.FeatureByPositionReverse(0)
    If f Is Nothing Then Fail "no feature was created where a " & typeName & " was expected."
    If f.GetTypeName2 <> typeName Then
        Fail "expected the last feature to be a " & typeName & ", found " & f.GetTypeName2 & "."
    End If
    Set LastFeature = f
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
    If prefsTouched Then
        swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, oldVerify
        swApp.SetUserPreferenceToggle swInputDimValOnCreate, oldInputDim
        prefsTouched = False
    End If
End Sub


' The whole log, to a file: a message box shows about 1000 characters.
Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\plant_topology_build.log"
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
    Err.Raise vbObjectError + 1, "plant_topology", msg
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


' No trailing decimal separator on whole numbers ("65", not "65,").
Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
    If Right(Fmt, 1) = "," Or Right(Fmt, 1) = "." Then Fmt = Left(Fmt, Len(Fmt) - 1)
End Function
