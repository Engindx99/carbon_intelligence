Attribute VB_Name = "calciner"
'==================================================================
' ILC calciner CFD fluid volume  ->  STEP (AP214) + STL + SLDPRT
'
' Builds ONE closed solid: the gas volume inside the in-line
' calciner of the 5000 t/d plant -- two identical 2500 t/d preheater
' strings on one calciner and kiln (user decision, 12 Oct 2026),
' sized from the PF5000 line, itself double-string -- the kiln riser throat, the bottom
' cone and the vertical vessel -- and, as the build grows, its
' tangential tertiary air duct, the C4 meal pipe, a fuel port and the
' gooseneck down towards C5. Nothing structural is modelled -- no
' shell, no refractory (CLAUDE.md rule 8).
'
' BUILD STATUS: throat + cone + vessel, the Y gooseneck and the two
' meal feed pipes. The tertiary air duct, the fuel port, and the face
' tagging with export follow; until then the macro builds and
' verifies, and exports nothing.
'
' Coordinates: calciner axis = z, the kiln gas inlet face (bottom of
' the throat) at z = 0.
'
' SI ONLY. The SolidWorks API is always metres and radians,
' whatever the document's display units are set to.
'
' To run: SolidWorks -> Tools -> Macro -> New, then in the VBA
' editor File -> Import File... and pick this .bas. Run `main`.
' See README.md next to this file.
'==================================================================

Option Explicit

'------------------------------------------------------------------
' (a) PARAMETERS -- the only numbers in this file.
'     Every one is published, derived from a named literature value,
'     or a modelling parameter that says where a CFD boundary sits.
'     Sources: geometry/calciner/calciner.md.
'------------------------------------------------------------------

Const CALCINER_NAME As String = "calciner"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const D_VESSEL                     As Double  = 6.7404       ' effective inner D [derived_from_reference, calciner/calciner.md]
Const H_VESSEL                     As Double  = 30#          ' cone + cylinder [published, calciner/calciner.md]
Const CONE_DEG                     As Double  = 65#          ' [literature, calciner/calciner.md]
Const M_KILN_GAS                   As Double  = 61.44444444  ' kg/s [literature, calciner/calciner.md]
Const T_KILN_GAS                   As Double  = 1323.15      ' K [literature, calciner/calciner.md]
Const X_N2                         As Double  = 0.744        ' [literature, calciner/calciner.md]
Const X_O2                         As Double  = 0.076        ' [literature, calciner/calciner.md]
Const X_H2O                        As Double  = 0.05         ' [literature, calciner/calciner.md]
Const X_CO2                        As Double  = 0.13         ' [literature, calciner/calciner.md]
Const U_THROAT                     As Double  = 29#          ' m/s [literature, calciner/calciner.md]
Const THROAT_LEN_OVER_D            As Double  = 1#           ' [model, calciner/calciner.md]
Const D_GOOSENECK_SRC              As Double  = 3.5          ' each leg [published, preheater/gooseneck.md]
Const GN_RISE_OVER_D               As Double  = 1.25         ' x neck D [model, preheater/gooseneck.md]
Const GN_BEND_R_OVER_D             As Double  = 1.5          ' x leg D [model, preheater/gooseneck.md]
Const GN_OUTLET_AT_VESSEL_H        As Double  = 0.5          ' x H_VESSEL [model, preheater/gooseneck.md]
Const D_FEED                       As Double  = 0.8485       ' [literature, calciner/calciner.md]
Const FEED_SLOPE_DEG               As Double  = 60#          ' below the horizontal [literature, calciner/calciner.md]
Const FEED_BELOW_GN_OUT            As Double  = 2#           ' [model, calciner/calciner.md]
Const FEED_DEPTH                   As Double  = 1#           ' [model, calciner/calciner.md]
Const OVERLAP_N                    As Long    = 80           ' grid per axis, the bends' shared volume [plant_geometry.py]
Const P_ATM                        As Double  = 101325#      ' Pa, the throat's gas [plant_geometry.py]
Const R_GAS                        As Double  = 8.314462618  ' J/(mol K) [plant_geometry.py]
Const M_N2                         As Double  = 0.0280134    ' kg/mol [plant_geometry.py]
Const M_O2                         As Double  = 0.0319988    ' kg/mol [plant_geometry.py]
Const M_H2O                        As Double  = 0.01801528   ' kg/mol [plant_geometry.py]
Const M_CO2                        As Double  = 0.0440095    ' kg/mol [plant_geometry.py]
' END GENERATED

' Vessel [m] -- geometry/calciner/calciner.md, geometry/catalog.md
' PF5000 publishes a 7.2 m shell and a 30.0 m vessel; the effective
' diameter is the shell x FLS calciner_eff_over_shell = 3.08 / 3.29,
' the rule geometry/catalog.md uses for every vendor shell. (The
' 2500 t/d line's calciner was 5.50 x 29.46 m, HFC2500.)
' -> D_VESSEL, H_VESSEL: in the generated block above
'    D_VESSEL: effective inner diameter, PF5000 shell 7.2 x 3.08 / 3.29
'    H_VESSEL: cone + cylinder, PF5000 (published)

' Bottom cone wall angle above the horizontal. Holcim StDC 2022 asks
' at least 65 deg of a cyclone cone so meal slides off it rather than
' building up; the calciner cone carries the same meal and gets the
' same rule. No source gives a calciner cone angle of its own.
' -> CONE_DEG: in the generated block above

' Throat. No source publishes a throat diameter, so it is sized from
' a literature flow at a literature velocity -- never from the twin,
' which is not ready (user decision, 29 Sep 2026):
'
'   kiln gas   2 x 110 600 kg/h     Mikulcic et al. 2012, a 5.5 m
'                                   calciner of a 2500 t/d class line;
'                                   the 5000 t/d kiln makes twice it
'   at         1050 C               Kahawalage et al. 2017
'   of         74.4 N2, 7.6 O2,     Kahawalage et al. 2017, mol %
'              5.0 H2O, 13.0 CO2
'   through    29 m/s               CPFD 2025 (4000 t/d calciner),
'                                   throat mean 28-30 m/s
'
' Ideal gas at one atmosphere; the throat diameter follows in Derive.
' -> M_KILN_GAS, T_KILN_GAS, X_N2, X_O2, X_H2O, X_CO2, U_THROAT: in the generated block above
'    M_KILN_GAS: 2 x 110 600 kg/h [kg/s]
'    T_KILN_GAS: [K]
'    U_THROAT: [m/s]

' Modelling parameter -- NOT a plant dimension. The kiln riser below
' the cone is cut off this far down, in throat diameters, so the gas
' inlet face sits on a straight run rather than on the cone's lip.
' -> THROAT_LEN_OVER_D: in the generated block above

' Y gooseneck (user decision, 12 Oct 2026). Each leg takes one
' string's gas to its C5: a 2500 t/d line's whole gas, so each leg is
' the published 3.50 m gooseneck of that line
' (geometry/preheater/gooseneck.md). Two 3.50 m legs do not fit side
' by side on the 6.74 m roof, so ONE neck rises from the roof's centre
' with the two legs' area, 3.50 x sqrt 2 = 4.95 m, velocity kept. At
' its top the two legs start, each disc inside the neck's and touching
' its rim on its own side, turn outward over a 180 deg bend and drop
' to their gas outlet faces. Where the legs' discs do not cover the
' neck's, its top is a flat ceiling.
' -> D_GOOSENECK_SRC: in the generated block above
'    D_GOOSENECK_SRC: published, one 2500 t/d line [m]: each leg

' Modelling parameters -- NOT plant dimensions. No source gives the
' gooseneck's lengths. The rise and the bend are C1's (cyclone.bas),
' where the outlet face had to move past a bend before the backflow on
' it went away. The drops hang down beside the vessel to half its
' height (user decision, 29 Sep 2026): the outlet faces sit at this
' fraction of the vessel (cone + cylinder) above its bottom, z =
' zThroatTop, far enough past the bend for the flow to straighten.
' -> GN_RISE_OVER_D, GN_BEND_R_OVER_D, GN_OUTLET_AT_VESSEL_H: in the generated block above
'    GN_RISE_OVER_D: the neck's straight rise above the roof, x neck D
'    GN_BEND_R_OVER_D: bend centreline radius, x leg D
'    GN_OUTLET_AT_VESSEL_H: outlet faces' height, fraction of H_VESSEL

' Meal feed. Fidaros et al. 2007 feed the raw meal through two round
' 0.6 m pipes at 60 deg to the horizontal; here one on each side of
' the vessel, at +x and -x, in the gooseneck's x-z plane below each
' drop (user decision, 29 Sep 2026): each takes one string's C4 meal.
' That is twice the meal of Fidaros's calciner per pipe, so the area
' doubles at the same meal velocity: 0.6 x sqrt 2 = 0.8485 m. Each
' pipe points at the vessel axis and rises away from the wall, so the
' meal falls in towards the middle.
' -> D_FEED, FEED_SLOPE_DEG: in the generated block above
'    D_FEED: [m], Fidaros 2007 x sqrt 2
'    FEED_SLOPE_DEG: below the horizontal, Fidaros 2007

' Modelling parameters -- NOT plant dimensions. Where the pipe axis
' meets the wall, this far below the gooseneck outlet faces, so the
' pipes sit a little below where the drops hang down to (user
' decision, 29 Sep 2026); and how far each pipe runs out along its
' axis past the wall, as C1's feed chute does.
' -> FEED_BELOW_GN_OUT, FEED_DEPTH: in the generated block above
'    FEED_BELOW_GN_OUT: [m]
'    FEED_DEPTH: [m]

' Output
Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

' Grid points per axis for the volume the two gooseneck bends share
' (GnBendOverlap); its error is well under VOL_TOL on the body.
' -> OVERLAP_N: in the generated block above

' Verification tolerances
Const VOL_TOL  As Double = 0.001   ' relative, on every closed-form stage volume
' A feed pipe adds well under a cubic metre to a ~1870 m3 body, under
' VOL_TOL on the whole, so its stage is also checked on the volume it ADDS, to this.
Const FEED_VOL_TOL As Double = 0.01
Const AREA_TOL As Double = 0.002   ' relative, on face areas
Const BOX_TOL  As Double = 0.005   ' absolute [m]; GetBodyBox may overstate curved faces
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001

' -> P_ATM, R_GAS: in the generated block above
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

' (b) derived coordinates -- every one computed, none typed in
Dim R As Double                             ' vessel radius
Dim rhoKiln As Double                       ' kiln gas density at the throat [kg/m3]
Dim qKiln As Double                         ' kiln gas volume flow [m3/s]
Dim rThroat As Double                       ' throat radius
Dim zThroatTop As Double                    ' where the throat meets the cone
Dim hCone As Double                         ' cone height
Dim zConeTop As Double                      ' where the cone meets the cylinder
Dim zRoof As Double                         ' the vessel's flat roof
Dim rGn As Double                           ' gooseneck leg radius
Dim rNeck As Double                         ' the neck's radius, two legs' area
Dim xGn As Double                           ' the legs' start discs, x = +-this, y = 0, inside the neck's
Dim zGnTop As Double                        ' top of the neck, where both bends start and end
Dim rGnBend As Double                       ' bend centreline radius
Dim xGnLeg As Double                        ' the drops' axes, x = +-this
Dim zGnOut As Double                        ' the two gas outlet faces, z = this, facing down
Dim zGnApex As Double                       ' highest point of the bends
Dim xBoxMax As Double                       ' the domain's |x| extreme, the drops' outer walls
Dim rFeed As Double                         ' feed pipe radius
Dim fc As Double, fs As Double              ' cos, sin of the feed slope; axis e = (+-fc, 0, fs)
Dim zFeed As Double                         ' where each feed pipe's axis meets the wall
Dim zFeedStart As Double                    ' the pipes start on the vessel axis, here
Dim lFeed As Double                         ' pipe length from its start
Dim xFeedEnd As Double, zFeedEnd As Double  ' centre of the end face, the meal_feed, at x = +-xFeedEnd
Dim xFeedMax As Double                      ' |x| of the end faces' outer edges

' Sketch axis directions, measured at run time by CalibrateSketchAxes.
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profiles
Dim uSignY As Double, vSignY As Double      ' the y = 0 plane, for the feed pipes
Dim uSignZ As Double, vSignZ As Double      ' z = zGnTop, where the gooseneck is drawn

' The off-plane component of the first point drawn in the sketch
' now open; see G2S.
Dim wRef As Double
Dim wRefSet As Boolean

' expected volumes, all closed form
Dim vThroat As Double, vCone As Double, vCyl As Double, vVessel As Double
Dim vGnPipes As Double, vGnBend As Double, vGnLegs As Double
Dim vGnOverlap As Double                    ' what the two bends share, over the neck
Dim vFeed As Double                         ' one feed pipe, the part outside the vessel
Dim vStage1 As Double, vStage2 As Double, vStage3a As Double, vStage3b As Double
Dim vStage4 As Double, vStage5a As Double
Dim vFinal As Double

Dim buildLog As String

' What the macro is doing right now, so that an error raised by
' SolidWorks itself -- which carries no location -- still says where
' it happened.
Dim phase As String


'==================================================================
' main
'==================================================================
Sub main()

    Dim why As String

    ' Module state survives between runs, so start from a clean log
    ' or the second run's report is the first one's as well.
    buildLog = ""
    phase = "starting up"

    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "working out the coordinates"
    Derive
    phase = "checking the dimensions can be built"
    PreChecks

    phase = "building the solid"
    Build
    phase = "verifying the solid"
    Verify

    Restore
    WriteLog CALCINER_NAME & " built and verified"
    MsgBox CALCINER_NAME & " built and verified. Nothing is exported until the " & _
           "boundary faces are tagged." & vbLf & vbLf & buildLog, vbInformation, "Calciner"
    Exit Sub

Failed:
    ' Read the reason BEFORE Restore: the On Error statement inside
    ' it resets the Err object and the reason would be lost.
    why = Err.Description
    Restore
    WriteLog CALCINER_NAME & " ABORTED while " & phase & ": " & why
    MsgBox CALCINER_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
           "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Calciner"

End Sub


'==================================================================
' (b) Derived coordinates
'==================================================================
Private Sub Derive()

    Dim mMol As Double

    R = 0.5 * D_VESSEL

    ' Throat: literature flow over literature velocity. Molar masses
    ' in kg/mol.
    mMol = X_N2 * M_N2 + X_O2 * M_O2 + X_H2O * M_H2O + X_CO2 * M_CO2
    rhoKiln = P_ATM * mMol / (R_GAS * T_KILN_GAS)
    qKiln = M_KILN_GAS / rhoKiln
    rThroat = Sqr(qKiln / (PI * U_THROAT))

    zThroatTop = THROAT_LEN_OVER_D * 2# * rThroat
    hCone = (R - rThroat) * Tan(CONE_DEG * PI / 180#)
    zConeTop = zThroatTop + hCone
    zRoof = zThroatTop + H_VESSEL

    ' ---- closed-form volumes, one per build stage ----
    vThroat = PI * rThroat * rThroat * zThroatTop
    vCone = (PI / 3#) * hCone * (R * R + R * rThroat + rThroat * rThroat)
    vCyl = PI * R * R * (H_VESSEL - hCone)
    vVessel = vCone + vCyl

    ' Gooseneck. One neck of both legs' area on the axis; each leg's
    ' start disc inside it, touching its rim on its own side.
    rGn = 0.5 * D_GOOSENECK_SRC
    rNeck = rGn * Sqr(2#)
    xGn = rNeck - rGn
    zGnTop = zRoof + GN_RISE_OVER_D * 2# * rNeck
    rGnBend = GN_BEND_R_OVER_D * 2# * rGn
    xGnLeg = xGn + 2# * rGnBend
    zGnOut = zThroatTop + GN_OUTLET_AT_VESSEL_H * H_VESSEL
    zGnApex = zGnTop + rGnBend + rGn
    xBoxMax = xGnLeg + rGn

    vGnPipes = PI * rNeck * rNeck * (zGnTop - zRoof)
    ' Pappus: a disc swept about an axis it does not cross sweeps its
    ' area times the path of its centroid, here half a circle of
    ' radius rGnBend. Exact while rGnBend > rGn. One bend.
    vGnBend = PI * rGn * rGn * (PI * rGnBend)
    vGnLegs = 2# * PI * rGn * rGn * (zGnTop - zGnOut)

    vStage1 = vThroat + vVessel            ' throat + cone + cylinder
    vStage2 = vStage1 + vGnPipes           ' + the neck rising from the roof
    ' The two bends start from overlapping discs, so near the neck
    ' they share a volume no closed form gives; GnBendOverlap
    ' integrates it.
    vGnOverlap = GnBendOverlap()
    vStage3a = vStage2 + vGnBend           ' + the +x bend
    ' Meal feed pipes. Checked here, not in PreChecks: at 90 deg the
    ' lines below divide by zero before PreChecks runs.
    If FEED_SLOPE_DEG <= 0# Or FEED_SLOPE_DEG >= 90# Then
        Fail "FEED_SLOPE_DEG is " & Fmt(FEED_SLOPE_DEG) & "; the feed pipes have to slope " & _
             "between the horizontal and the vertical."
    End If
    rFeed = 0.5 * D_FEED
    fc = Cos(FEED_SLOPE_DEG * PI / 180#)
    fs = Sin(FEED_SLOPE_DEG * PI / 180#)
    zFeed = zGnOut - FEED_BELOW_GN_OUT
    zFeedStart = zFeed - R * (fs / fc)
    lFeed = R / fc + FEED_DEPTH
    xFeedEnd = R + FEED_DEPTH * fc
    zFeedEnd = zFeed + FEED_DEPTH * fs
    xFeedMax = xFeedEnd + rFeed * fs

    ' A line of the pipe at (a, b) in its section -- a across, along x,
    ' b along the section's "up" -- leaves the vessel where its
    ' horizontal reach s fc - b fs equals sqrt(R^2 - a^2). The b part
    ' is odd across the section and cancels, as it does for C1's
    ' chute, so what the merge keeps is the full pipe less the vessel
    ' chord integrated over the disc and stretched by 1 / fc. That
    ' integral is elliptic; FeedChordIntegral evaluates it.
    vFeed = PI * rFeed * rFeed * lFeed - FeedChordIntegral() / fc

    vStage3b = vStage3a + vGnBend - vGnOverlap   ' + the -x bend, less what it shares with the +x one
    vStage4 = vStage3b + vGnLegs           ' + two drops to the outlet faces
    vStage5a = vStage4 + vFeed             ' + the +x meal feed pipe
    vFinal = vStage5a + vFeed              ' + the -x meal feed pipe

End Sub


'==================================================================
' (c) Pre-checks. A combination that cannot be built is refused; no
'     dimension is ever adjusted to make it buildable.
'==================================================================
Private Sub PreChecks()

    ' 1. the cone has to open, not close
    If rThroat >= R Then
        Fail "the throat (D " & Fmt(2# * rThroat) & " m) is not narrower than the vessel (D " & _
             Fmt(D_VESSEL) & " m); there is no cone to build."
    End If

    ' 2. a cone angle a wall can have
    If CONE_DEG <= 0# Or CONE_DEG >= 90# Then
        Fail "CONE_DEG is " & Fmt(CONE_DEG) & "; the cone wall has to lie between the " & _
             "horizontal and the vertical."
    End If

    ' 3. the cone has to fit inside the vessel height, with cylinder
    '    left above it
    If hCone >= H_VESSEL Then
        Fail "the cone is " & Fmt(hCone) & " m tall, not shorter than the whole vessel (" & _
             Fmt(H_VESSEL) & " m)."
    End If

    ' 4. the gas inlet face has to sit on a straight run below the cone
    If THROAT_LEN_OVER_D <= 0# Then
        Fail "THROAT_LEN_OVER_D is " & Fmt(THROAT_LEN_OVER_D) & ". The kiln gas inlet face " & _
             "would sit on the cone's lip."
    End If

    ' 5. the neck on the roof, clear of the wall
    If rNeck >= R Then
        Fail "the gooseneck neck (D " & Fmt(2# * rNeck) & " m) does not fit on the D " & _
             Fmt(D_VESSEL) & " m roof."
    End If

    ' 6. the bends. At rGnBend <= rGn the inner wall of a bend passes
    '    through the axis it is swept about and the solid folds
    '    through itself; Pappus stops being the volume, too.
    If rGnBend <= rGn Then
        Fail "the gooseneck bend radius " & Fmt(rGnBend) & " m is not larger than the leg " & _
             "radius " & Fmt(rGn) & " m. GN_BEND_R_OVER_D must exceed 0.5."
    End If

    ' 7. the rise and the drop, and the drops clear of the vessel
    If GN_RISE_OVER_D <= 0# Then
        Fail "GN_RISE_OVER_D is " & Fmt(GN_RISE_OVER_D) & ". The bends have to start above " & _
             "the roof, not on it."
    End If
    If zGnOut >= zGnTop Then
        Fail "the gooseneck outlet faces at z = " & Fmt(zGnOut) & " m are not below the ends " & _
             "of the bends at z = " & Fmt(zGnTop) & " m; they would sit where the flow is " & _
             "still turning. Lower GN_OUTLET_AT_VESSEL_H."
    End If
    If xGnLeg - rGn <= R Then
        Fail "the gooseneck drops' inner walls at |x| = " & Fmt(xGnLeg - rGn) & " m are not " & _
             "clear of the vessel (" & Fmt(R) & " m). Raise GN_BEND_R_OVER_D."
    End If
    ' 8. the feed pipes. The end face has to lie wholly outside the
    '    vessel, or part of the meal_feed face merges away: its edge
    '    nearest the wall reaches in by rFeed * sin.
    If FEED_DEPTH * fc <= rFeed * fs Then
        Fail "the feed pipes' end faces reach back into the vessel; FEED_DEPTH must exceed " & _
             Fmt(rFeed * fs / fc) & " m at " & Fmt(FEED_SLOPE_DEG) & " deg."
    End If
    ' The hole in the wall reaches rFeed / cos above and below zFeed on
    ' the pipe's mid-plane, and the lower edge drops a little more
    ' towards the sides, where the wall curves back.
    If zFeed - rFeed / fc - (R - Sqr(R * R - rFeed * rFeed)) * (fs / fc) <= zConeTop Then
        Fail "the feed pipes' holes in the wall reach down past the top of the cone at z = " & _
             Fmt(zConeTop) & " m. Lower FEED_BELOW_GN_OUT."
    End If
    ' The start disc sits on the vessel axis; it has to be clear of
    ' the cone, or the closed-form volume counts a piece that is not
    ' there.
    If zFeedStart - rFeed * fc <= zConeTop Then
        Fail "the feed pipes start at z = " & Fmt(zFeedStart - rFeed * fc) & " m on the axis, " & _
             "inside the cone (top at z = " & Fmt(zConeTop) & " m)."
    End If
    ' "A little below where the drops hang down to": the whole pipe.
    If zFeedEnd + rFeed * fc >= zGnOut Then
        Fail "the feed pipes reach up to z = " & Fmt(zFeedEnd + rFeed * fc) & " m, not below " & _
             "the gooseneck outlet faces at z = " & Fmt(zGnOut) & " m."
    End If
    ' Same plane as the drops, so clear of them in x as well.
    If xFeedMax >= xGnLeg - rGn Then
        Fail "the feed pipes reach out to |x| = " & Fmt(xFeedMax) & " m, into the gooseneck " & _
             "drops whose inner walls are at |x| = " & Fmt(xGnLeg - rGn) & " m."
    End If

    If zGnOut <= zConeTop Then
        Fail "the gooseneck drops come down to z = " & Fmt(zGnOut) & " m, below the top of " & _
             "the cone at z = " & Fmt(zConeTop) & " m."
    End If

    Note "kiln gas: " & Fmt(M_KILN_GAS) & " kg/s at " & Fmt(T_KILN_GAS) & " K, rho " & _
         Fmt(rhoKiln) & " kg/m3, " & Fmt(qKiln) & " m3/s"
    Note "throat D " & Fmt(2# * rThroat) & " m at " & Fmt(U_THROAT) & " m/s, " & _
         Fmt(zThroatTop) & " m long"
    Note "cone " & Fmt(CONE_DEG) & " deg, " & Fmt(hCone) & " m tall, z " & Fmt(zThroatTop) & _
         " .. " & Fmt(zConeTop) & " m"
    Note "cylinder D " & Fmt(D_VESSEL) & " m, z " & Fmt(zConeTop) & " .. " & Fmt(zRoof) & " m"
    Note "gooseneck: neck D " & Fmt(2# * rNeck) & " m rising to z = " & Fmt(zGnTop) & _
         " m; 2 legs D " & Fmt(2# * rGn) & " m from x = +-" & Fmt(xGn) & " m, bend R " & _
         Fmt(rGnBend) & " m over 180 deg (sharing " & Fmt(vGnOverlap) & " m3), drop at x = +-" & _
         Fmt(xGnLeg) & " m to the outlet faces at z = " & Fmt(zGnOut) & " m"
    Note "meal feed: 2 pipes D " & Fmt(D_FEED) & " m at " & Fmt(FEED_SLOPE_DEG) & _
         " deg, axes meet the wall at z = " & Fmt(zFeed) & " m, end faces centred (+-" & _
         Fmt(xFeedEnd) & ", 0, " & Fmt(zFeedEnd) & "), " & Fmt(vFeed) & " m3 each outside the vessel"
    Note "vessel volume (cone + cylinder)   " & Fmt(vVessel) & " m3"
    Note "CFD domain volume                 " & Fmt(vFinal) & " m3"
End Sub


'==================================================================
' (d) Build
'==================================================================
Private Sub Build()

    Dim planeX0 As SldWorks.Feature       ' the x = 0 plane
    Dim planeY0 As SldWorks.Feature       ' the y = 0 plane
    Dim planeZ0 As SldWorks.Feature       ' the z = 0 plane
    Dim planeGn As SldWorks.Feature       ' z = zGnTop: the whole gooseneck is drawn here
    Dim f As SldWorks.Feature

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    ' Verification on rebuild is slower but it is what makes a
    ' boolean that produced non-manifold geometry fail loudly
    ' instead of being quietly accepted.
    oldVerify = swApp.GetUserPreferenceToggle(swPerformanceVerifyOnRebuild)
    oldInputDim = swApp.GetUserPreferenceToggle(swInputDimValOnCreate)
    swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, True
    swApp.SetUserPreferenceToggle swInputDimValOnCreate, False
    prefsTouched = True

    ' exact coordinates: no inferencing, no snapping, no auto relations
    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    Set planeX0 = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX0 Is Nothing Then Fail "could not find the default plane whose normal is X."
    Set planeY0 = FindPlaneWithNormal(0#, 1#, 0#)
    If planeY0 Is Nothing Then Fail "could not find the default plane whose normal is Y."
    Set planeZ0 = FindPlaneWithNormal(0#, 0#, 1#)
    If planeZ0 Is Nothing Then Fail "could not find the default plane whose normal is Z."

    '--- 0. measure every plane's sketch axes ------------------------
    ' All probes run while the part is still empty. Once the vessel
    ' is there a probe would land inside it, merge with it, and then
    ' measure the merged body instead of itself.
    Set planeGn = OffsetPlane(planeZ0, 0#, 0#, zGnTop, uSignZ, vSignZ)
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX
    CalibrateSketchAxes planeY0, 0#, 0#, 0#, uSignY, vSignY

    '--- 1. throat + cone + cylinder --------------------------------
    Set f = RevolveProfile(planeX0, Array( _
        0#, 0#, _
        rThroat, 0#, _
        rThroat, zThroatTop, _
        R, zConeTop, _
        R, zRoof, _
        0#, zRoof), False)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on the throat + cone + cylinder profile."
    CheckStage "1  throat + cone + cylinder", vStage1, -R, -R, 0#, R, R, zRoof

    '--- 2. the neck rising from the roof ----------------------------
    ' Drawn at the top of the rise and extruded down onto the roof.
    Set f = ExtrudeCircles(planeGn, 0#, rNeck, zGnTop - zRoof, vStage2, "2  + gooseneck neck")
    CheckStage "2  + gooseneck neck", vStage2, -R, -R, 0#, R, R, zGnTop

    '--- 3. the two 180 deg bends, each turning outward --------------
    ' One feature each: a revolve takes one axis.
    Set f = RevolveGnBend(planeGn, 1#, vStage3a, "3a + gooseneck bend, +x")
    CheckStage "3a + gooseneck bend, +x", vStage3a, -R, -R, 0#, xBoxMax, R, zGnApex
    Set f = RevolveGnBend(planeGn, -1#, vStage3b, "3b + gooseneck bend, -x")
    CheckStage "3b + gooseneck bend, -x", vStage3b, -xBoxMax, -R, 0#, xBoxMax, R, zGnApex

    '--- 4. the two drops to the gas outlet faces ---------------------
    Set f = ExtrudeCircles(planeGn, xGnLeg, rGn, zGnTop - zGnOut, vStage4, "4  + gooseneck drops")
    CheckStage "4  + gooseneck drops", vStage4, -xBoxMax, -R, 0#, xBoxMax, R, zGnApex

    '--- 5. the two meal feed pipes, at +x and -x ---------------------
    ' Each is a rectangle in the y = 0 plane revolved about its own
    ' axis edge. A full turn has no direction to get wrong; the end
    ' face, found at +x or -x, says which side each landed on. The
    ' drops reach further out in x, so the box does not move.
    AddFeedPipe planeY0, 1#, "5a + meal feed, +x"
    CheckStage "5a + meal feed, +x", vStage5a, -xBoxMax, -R, 0#, xBoxMax, R, zGnApex
    AddFeedPipe planeY0, -1#, "5b + meal feed, -x"
    CheckStage "5b + meal feed, -x", vFinal, -xBoxMax, -R, 0#, xBoxMax, R, zGnApex

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ViewZoomtofit2

End Sub


' A closed profile in the x = 0 plane, given as r, z pairs, revolved
' 360 deg about the calciner axis. Where the profile is closed by a
' segment lying on the axis, that same segment is used as the axis
' of revolution so there is no duplicate centreline for SolidWorks
' to choose between; profiles clear of the axis get one centreline,
' and exactly one.
Private Function RevolveProfile(planeX0 As SldWorks.Feature, pts As Variant, _
                                ByVal isCut As Boolean) As SldWorks.Feature

    Dim n As Long, i As Long, j As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim zLo As Double, zHi As Double
    Dim seg As SldWorks.SketchSegment
    Dim axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim selData As SldWorks.SelectData

    uSign = uSignX: vSign = vSignX

    n = (UBound(pts) + 1) \ 2
    zLo = pts(1): zHi = pts(1)
    For i = 0 To n - 1
        If pts(2 * i + 1) < zLo Then zLo = pts(2 * i + 1)
        If pts(2 * i + 1) > zHi Then zHi = pts(2 * i + 1)
    Next i

    swModel.ClearSelection2 True
    planeX0.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a sketch on the x = 0 plane."
    wRefSet = False

    For i = 0 To n - 1
        j = (i + 1) Mod n
        G2S sk, 0#, pts(2 * i), pts(2 * i + 1), u0, v0
        G2S sk, 0#, pts(2 * j), pts(2 * j + 1), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on the revolve profile."
        If pts(2 * i) = 0# And pts(2 * j) = 0# Then Set axisSeg = seg
    Next i

    If axisSeg Is Nothing Then
        G2S sk, 0#, 0#, zLo, u0, v0
        G2S sk, 0#, 0#, zHi, u1, v1
        Set axisSeg = swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#)
        If axisSeg Is Nothing Then Fail "CreateCenterLine failed on the revolve axis."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set RevolveProfile = swFeat.FeatureRevolve2( _
        True, True, False, isCut, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        True, True, True)

    swModel.ClearSelection2 True

End Function


' A plane parallel to a default plane, through the given model
' point, with the sketch axes on it measured at the same time --
' copied from cyclone.bas. Which side of the base plane
' InsertRefPlane puts the offset on is not ours to choose and cannot
' be read back off the sketch transform, so it is measured: a test
' block is dropped on the plane and its box read back. A plane on
' the wrong side fails that test and is deleted, and the other side
' is tried.
Private Function OffsetPlane(base As SldWorks.Feature, _
                             ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                             ByRef us As Double, ByRef vs As Double) As SldWorks.Feature

    Dim pl As SldWorks.Feature
    Dim opt As Long
    Dim k As Long
    Dim at As String

    at = "(" & Fmt(bx) & ", " & Fmt(by) & ", " & Fmt(bz) & ")"

    For k = 0 To 1
        opt = swRefPlaneReferenceConstraint_Distance
        If k = 1 Then opt = opt Or swRefPlaneReferenceConstraint_OptionFlip

        swModel.ClearSelection2 True
        base.Select2 False, 0
        Set pl = swFeat.InsertRefPlane(opt, Abs(bx) + Abs(by) + Abs(bz), 0, 0#, 0, 0#)
        swModel.ClearSelection2 True
        If pl Is Nothing Then
            Fail "InsertRefPlane failed for the offset plane through " & at & "."
        End If

        If TryCalibrateSketchAxes(pl, bx, by, bz, us, vs) Then
            Note "offset plane measured through " & at
            Set OffsetPlane = pl
            Exit Function
        End If

        swModel.ClearSelection2 True
        pl.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    Next k

    Fail "the offset plane could not be placed through " & at & "; a test block " & _
         "dropped on it landed somewhere else both ways round."

End Function


' Discs of radius rc at (+-xc, 0) in the plane z = zGnTop -- one disc
' on the axis when xc = 0 -- extruded straight DOWN by depth: the neck
' (onto the roof) or the two drops (to the outlet faces).
'
' Which way a blind extrusion goes is not ours to choose. Up from the
' plane, the pipes would float free of the vessel -- three bodies --
' and the drops would run back into the bends and come out short; the
' body count and the volume say which, and the other way is tried.
Private Function ExtrudeCircles(planeGn As SldWorks.Feature, ByVal xc As Double, ByVal rc As Double, _
                                ByVal depth As Double, ByVal expected As Double, _
                                ByVal stage As String) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim u0 As Double, v0 As Double
    Dim f As SldWorks.Feature
    Dim got As Double
    Dim s As Long, k As Long

    uSign = uSignZ: vSign = vSignZ

    swModel.ClearSelection2 True
    planeGn.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    For s = -1 To 1 Step 2
        G2S sk, s * xc, 0#, zGnTop, u0, v0
        If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rc) Is Nothing Then
            Fail "CreateCircleByRadius failed at stage " & stage & "."
        End If
        If xc = 0# Then Exit For
    Next s

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        swModel.ClearSelection2 True
        skFeat.Select2 False, 0
        Set f = swFeat.FeatureExtrusion3( _
            True, False, (k = 1), _
            swEndCondBlind, swEndCondBlind, _
            depth, 0.01, _
            False, False, False, False, _
            0#, 0#, _
            False, False, False, False, _
            True, True, True, _
            swStartSketchPlane, 0#, False)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            got = BodiesVolume()
            If BodyCount() = 1 And Abs(got - expected) <= VOL_TOL * expected Then
                Set ExtrudeCircles = f
                Exit Function
            End If
            Note "stage " & stage & " extruded the wrong way (" & BodyCount() & " bodies, " & _
                 Fmt(got) & " m3); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "stage " & stage & " could not be extruded down to one body of " & Fmt(expected) & _
         " m3 in either direction."

End Function


' One gooseneck bend: the leg's disc at (side * xGn, 0) in the plane
' z = zGnTop, revolved 180 deg about the line through
' (side * (xGn + rGnBend), 0, zGnTop) parallel to y. That line lies
' in the disc's plane, which is what a revolve needs, and clears the
' disc by rGnBend - rGn, so the result is a half torus that leaves
' the rise going up, goes over and comes back down into the same
' plane at x = side * xGnLeg. side = +1 turns outward to +x, -1 to -x.
'
' Turned the wrong way the bend runs down through the pipe and the
' roof into the vessel; the volume then comes out short and the top
' of the box stays at the rise. Either says so, and the other way is
' tried.
Private Function RevolveGnBend(planeGn As SldWorks.Feature, ByVal side As Double, _
                               ByVal expected As Double, ByVal stage As String) As SldWorks.Feature

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim segs As Variant
    Dim axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim body As SldWorks.Body2
    Dim mp As Variant, box As Variant
    Dim reachOut As Double
    Dim i As Long, k As Long

    uSign = uSignZ: vSign = vSignZ

    swModel.ClearSelection2 True
    planeGn.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    G2S sk, side * xGn, 0#, zGnTop, u0, v0
    If swSkMgr.CreateCircleByRadius(u0, v0, 0#, rGn) Is Nothing Then
        Fail "CreateCircleByRadius failed at stage " & stage & "."
    End If
    G2S sk, side * (xGn + rGnBend), -1#, zGnTop, u0, v0
    G2S sk, side * (xGn + rGnBend), 1#, zGnTop, u1, v1
    If swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#) Is Nothing Then
        Fail "CreateCenterLine failed at stage " & stage & "."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    For k = 0 To 1
        ' A segment pointer does not survive a deleted feature, so the
        ' axis is looked up again from the sketch on every attempt.
        Set sk = skFeat.GetSpecificFeature2
        segs = sk.GetSketchSegments
        Set axisSeg = Nothing
        For i = 0 To UBound(segs)
            If segs(i).ConstructionGeometry Then Set axisSeg = segs(i)
        Next i
        If axisSeg Is Nothing Then Fail "the sketch for stage " & stage & " has lost its axis."

        swModel.ClearSelection2 True
        Set selData = swModel.SelectionManager.CreateSelectData
        selData.Mark = 16
        axisSeg.Select4 False, selData
        skFeat.Select2 True, 0

        Set f = swFeat.FeatureRevolve2( _
            True, True, False, False, (k = 1), False, _
            0, 0, PI, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            True, True, True)
        swModel.ClearSelection2 True

        If Not f Is Nothing Then
            Set body = TheBody(stage)
            mp = body.GetMassProperties(1000#)
            box = body.GetBodyBox
            ' How far the body now reaches on this bend's side of x.
            If side > 0# Then reachOut = box(3) Else reachOut = -box(0)
            If Abs(mp(3) - expected) <= VOL_TOL * expected And _
               box(5) > zGnTop + 0.5 * rGnBend And reachOut > R + rGnBend Then
                Set RevolveGnBend = f
                Exit Function
            End If
            Note "stage " & stage & " turned the wrong way (volume " & Fmt(mp(3)) & " m3, top " & _
                 Fmt(box(5)) & " m); reversing"
            swModel.ClearSelection2 True
            f.Select2 False, 0
            swModel.EditDelete
            swModel.ClearSelection2 True
            Set f = Nothing
        End If
    Next k

    Fail "stage " & stage & " could not be revolved to the right volume in either direction. " & _
         "Expected " & Fmt(expected) & " m3, top at z = " & Fmt(zGnApex) & " m."

End Function


' The volume the two gooseneck bends share. Each bend is a half torus
' over the plane z = zGnTop, about the line through
' (side * (xGn + rGnBend), ., zGnTop) parallel to y: a point is in it
' when its distance rho from that line, measured in the x-z plane,
' and its y satisfy (rho - rGnBend)^2 + y^2 <= rGn^2, z >= zGnTop.
' The +x bend never reaches x < xGn - rGn, nor the -x bend past
' -(xGn - rGn), and neither rises over rGnBend + rGn: the midpoint rule
' on that box, OVERLAP_N points a side.
Private Function GnBendOverlap() As Double
    Dim i As Long, j As Long, k As Long
    Dim hx As Double, hy As Double, hz As Double
    Dim x As Double, y As Double, z As Double
    Dim xa As Double, ra As Double, rb As Double
    Dim hit As Long
    xa = xGn + rGnBend
    hx = 2# * (rGn - xGn) / OVERLAP_N
    hy = 2# * rGn / OVERLAP_N
    hz = (rGnBend + rGn) / OVERLAP_N
    For i = 0 To OVERLAP_N - 1
        x = -(rGn - xGn) + (i + 0.5) * hx
        For k = 0 To OVERLAP_N - 1
            z = (k + 0.5) * hz
            ra = Sqr((x - xa) * (x - xa) + z * z) - rGnBend
            rb = Sqr((x + xa) * (x + xa) + z * z) - rGnBend
            For j = 0 To OVERLAP_N - 1
                y = -rGn + (j + 0.5) * hy
                If ra * ra + y * y <= rGn * rGn Then
                    If rb * rb + y * y <= rGn * rGn Then hit = hit + 1
                End If
            Next j
        Next k
    Next i
    GnBendOverlap = hit * hx * hy * hz
End Function


' One meal feed pipe, on side = +1 (+x) or -1 (-x).
'
' The pipe's half-section -- a rectangle in the plane y = 0 from its
' axis out to rFeed along the section's "up" w = (-side fs, 0, fc) --
' revolved a full turn about the axis edge. It starts on the vessel
' axis, so its start disc is inside the vessel and dissolves in the
' merge, and runs out through the wall to its end face.
'
' The volume it adds is under a cubic metre of ~1870, under VOL_TOL on the whole
' body, so it is checked on its own: the volume ADDED, the end face
' found where it has to be with the pipe's area.
Private Sub AddFeedPipe(planeY0 As SldWorks.Feature, ByVal side As Double, ByVal stage As String)

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim axisSeg As SldWorks.SketchSegment
    Dim selData As SldWorks.SelectData
    Dim px(3) As Double, pz(3) As Double
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim f As SldWorks.Feature
    Dim seg As SldWorks.SketchSegment
    Dim before As Double, added As Double
    Dim face As SldWorks.Face2
    Dim i As Long, j As Long

    uSign = uSignY: vSign = vSignY
    before = BodiesVolume()

    px(0) = 0#:                              pz(0) = zFeedStart                  ' start, on the axis
    px(1) = side * lFeed * fc:               pz(1) = zFeedStart + lFeed * fs     ' end, on the axis
    px(2) = px(1) - side * rFeed * fs:       pz(2) = pz(1) + rFeed * fc          ' end, rFeed up
    px(3) = px(0) - side * rFeed * fs:       pz(3) = pz(0) + rFeed * fc          ' start, rFeed up

    swModel.ClearSelection2 True
    planeY0.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch for stage " & stage & "."
    wRefSet = False

    For i = 0 To 3
        j = (i + 1) Mod 4
        G2S sk, px(i), 0#, pz(i), u0, v0
        G2S sk, px(j), 0#, pz(j), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed at stage " & stage & "."
        If i = 0 Then Set axisSeg = seg          ' start -> end, the pipe's axis
    Next i

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    Set f = swFeat.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 2# * PI, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        True, True, True)
    swModel.ClearSelection2 True
    If f Is Nothing Then Fail "FeatureRevolve2 failed at stage " & stage & "."

    added = BodiesVolume() - before
    Note "stage " & stage & ": added " & Fmt(added) & " m3 (expected " & Fmt(vFeed) & ")"
    If Abs(added - vFeed) > FEED_VOL_TOL * vFeed Then
        Fail "stage " & stage & " added " & Fmt(added) & " m3 but should add " & Fmt(vFeed) & _
             " m3 (" & Fmt(100# * (added - vFeed) / vFeed) & " %)."
    End If

    Set face = FeedEndFace(side)
    If face Is Nothing Then
        Fail "stage " & stage & ": no end face normal to the pipe at (" & _
             Fmt(side * xFeedEnd) & ", 0, " & Fmt(zFeedEnd) & ")."
    End If
    CheckArea "meal_feed end", face.GetArea, PI * rFeed * rFeed

End Sub


' The feed pipe's end face on the given side: the plane face normal
' to the pipe axis (side fc, 0, fs) through its end centre. Nothing
' else in the part is normal to that axis there.
Private Function FeedEndFace(ByVal side As Double) As SldWorks.Face2

    Dim faces As Variant
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim i As Long

    faces = TheBody("feed end face").GetFaces
    For i = 0 To UBound(faces)
        Set surf = faces(i).GetSurface
        If surf.IsPlane Then
            p = surf.PlaneParams
            If Abs(p(1)) < DIR_TOL And Abs(Abs(p(0) * side * fc + p(2) * fs) - 1#) < DIR_TOL Then
                If Abs((p(3) - side * xFeedEnd) * side * fc + (p(5) - zFeedEnd) * fs) < 0.0001 Then
                    Set FeedEndFace = faces(i)
                    Exit Function
                End If
            End If
        End If
    Next i

End Function


' Integral over the feed pipe's section of the vessel's half chord
' sqrt(R^2 - a^2), a across the section:
'   2 int_{-r}^{r} sqrt(r^2 - a^2) sqrt(R^2 - a^2) da.
' Elliptic, so evaluated: with a = r sin(phi) the integrand is smooth
' and periodic and Simpson's rule on 400 panels is exact to rounding.
Private Function FeedChordIntegral() As Double

    Const n As Long = 400
    Dim h As Double, phi As Double, g As Double, w As Double, sum As Double
    Dim k As Long

    h = PI / n
    For k = 0 To n
        phi = -0.5 * PI + k * h
        g = 2# * rFeed * rFeed * Cos(phi) ^ 2 * Sqr(R * R - (rFeed * Sin(phi)) ^ 2)
        If k = 0 Or k = n Then
            w = 1#
        ElseIf (k Mod 2) = 1 Then
            w = 4#
        Else
            w = 2#
        End If
        sum = sum + w * g
    Next k
    FeedChordIntegral = sum * h / 3#

End Function


Private Sub CheckArea(ByVal what As String, ByVal got As Double, ByVal expected As Double)
    If Abs(got - expected) > AREA_TOL * expected Then
        Fail "the " & what & " face is " & Fmt(got) & " m2 but should be " & Fmt(expected) & " m2."
    End If
End Sub


Private Function BodyCount() As Long

    Dim bodies As Variant

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    BodyCount = UBound(bodies) + 1

End Function


' Total volume of every solid body in the part.
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


' Whether any body has a planar face normal to model axis ax
' (0 = x, 1 = y, 2 = z) lying at that coordinate.
Private Function HasPlaneFace(ByVal ax As Long, ByVal at As Double) As Boolean

    Dim bodies As Variant, faces As Variant
    Dim surf As SldWorks.Surface
    Dim p As Variant
    Dim b As Long, i As Long

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Exit Function
    For b = 0 To UBound(bodies)
        faces = bodies(b).GetFaces
        For i = 0 To UBound(faces)
            Set surf = faces(i).GetSurface
            If surf.IsPlane Then
                p = surf.PlaneParams
                If Abs(Abs(p(ax)) - 1#) < DIR_TOL And Abs(p(3 + ax) - at) < 0.0001 Then
                    HasPlaneFace = True
                    Exit Function
                End If
            End If
        Next i
    Next b

End Function


'==================================================================
' Sketch plane mapping -- copied from cyclone.bas, where the reasons
' are written out in full. In short: every point is given in MODEL
' coordinates and put through the plane's own transform; the
' off-plane component is compared against the FIRST point of the
' same sketch, never against zero, because ModelToSketchTransform's
' translation does not run the way its name promises; and which way
' a plane's sketch axes run is measured with a test block, not read.
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


' Which way round a sketch plane's axes actually run, measured: a
' 1 m x 2 m rectangle of known model coordinates, off the origin, is
' drawn, extruded and its bounding box read back for each of the four
' sign combinations. The probe is removed before anything real is
' built.
Private Sub CalibrateSketchAxes(pl As SldWorks.Feature, _
                                ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                ByRef us As Double, ByRef vs As Double)

    If Not TryCalibrateSketchAxes(pl, bx, by, bz, us, vs) Then
        Fail "sketch axis calibration failed on plane " & pl.Name & ": no combination of " & _
             "sketch axis signs put a test block where it was asked for. Either the sketch " & _
             "axes are not a sign flip of the model axes on this plane, or the plane is not " & _
             "where it was asked to be."
    End If

End Sub


Private Function TryCalibrateSketchAxes(pl As SldWorks.Feature, _
                                        ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                        ByRef us As Double, ByRef vs As Double) As Boolean

    Dim mx As Double, my As Double, mz As Double
    Dim i1 As Long, i2 As Long
    Dim p0(2) As Double, p1(2) As Double
    Dim k As Long

    PlaneNormal pl, mx, my, mz
    If Abs(mx) > 0.9 Then
        i1 = 1: i2 = 2                 ' normal X: the plane carries Y and Z
    ElseIf Abs(my) > 0.9 Then
        i1 = 0: i2 = 2                 ' normal Y: the plane carries X and Z
    ElseIf Abs(mz) > 0.9 Then
        i1 = 0: i2 = 1                 ' normal Z: the plane carries X and Y
    Else
        Fail "sketch axis calibration: the plane normal (" & Fmt(mx) & ", " & Fmt(my) & _
             ", " & Fmt(mz) & ") is not a model axis."
    End If

    p0(0) = bx: p0(1) = by: p0(2) = bz
    p1(0) = bx: p1(1) = by: p1(2) = bz
    p0(i1) = p0(i1) + 1#: p1(i1) = p1(i1) + 2#
    p0(i2) = p0(i2) + 3#: p1(i2) = p1(i2) + 5#

    For k = 0 To 3
        us = 1#: If (k And 1) <> 0 Then us = -1#
        vs = 1#: If (k And 2) <> 0 Then vs = -1#
        If ProbeLandsWhereAsked(pl, p0, p1, i1, i2, us, vs) Then
            Note "sketch axes on plane " & pl.Name & ": u x " & Fmt(us) & ", v x " & Fmt(vs)
            TryCalibrateSketchAxes = True
            Exit Function
        End If
    Next k

    TryCalibrateSketchAxes = False

End Function


' Draw the test rectangle with the given signs, extrude it, compare
' the body box against what was asked for, then take it back out
' again. True when it landed where it was asked to.
Private Function ProbeLandsWhereAsked(pl As SldWorks.Feature, p0() As Double, p1() As Double, _
                                      ByVal i1 As Long, ByVal i2 As Long, _
                                      ByVal us As Double, ByVal vs As Double) As Boolean

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim bodies As Variant, box As Variant
    Dim i3 As Long
    Dim ok As Boolean

    uSign = us: vSign = vs

    ' The probe has to be the only body in the part, or it would
    ' merge with what is already there and then report that body's
    ' box instead of its own.
    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "sketch axis calibration was asked to run with " & (UBound(bodies) + 1) & _
             " body/bodies already in the part; it only works on an empty one."
    End If

    swModel.ClearSelection2 True
    pl.Select2 False, 0
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
            box = bodies(0).GetBodyBox     ' xmin ymin zmin xmax ymax zmax
            ' The two in-plane axes say which way the sketch axes
            ' run; the third says where the plane itself is.
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
    If Not IsEmpty(bodies) Then
        Fail "a sketch axis calibration probe could not be removed; " & _
             (UBound(bodies) + 1) & " body/bodies are still in the part."
    End If

    ProbeLandsWhereAsked = ok

End Function


Private Function Near(ByVal a As Double, ByVal b As Double) As Boolean
    Near = (Abs(a - b) < 0.001)
End Function


' A plane's normal in model coordinates, read from a sketch opened
' on it. An empty sketch is discarded on exit.
Private Sub PlaneNormal(pl As SldWorks.Feature, ByRef mx As Double, ByRef my As Double, ByRef mz As Double)

    Dim sk As SldWorks.Sketch
    Dim a As Variant

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a probe sketch on a reference plane."
    a = sk.ModelToSketchTransform.ArrayData
    mx = a(6): my = a(7): mz = a(8)
    swSkMgr.InsertSketch True
    swModel.ClearSelection2 True

End Sub


' The default plane whose normal is the given direction, found by
' probing rather than by name -- plane names are localised, so
' "Right Plane" does not exist on a Turkish install.
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
' (f) Self-verification. Every stage has a closed-form volume and a
'     known bounding box, so the model is checked against
'     arithmetic, not against a previous run. Nothing is exported
'     until all of it passes.
'==================================================================
Private Sub CheckStage(ByVal stage As String, ByVal expected As Double, _
                       ByVal x0 As Double, ByVal y0 As Double, ByVal z0 As Double, _
                       ByVal x1 As Double, ByVal y1 As Double, ByVal z1 As Double)

    Dim body As SldWorks.Body2
    Dim mp As Variant, box As Variant
    Dim got As Double

    Set body = TheBody(stage)

    ' IBody2::GetMassProperties is always SI; IMassProperty follows
    ' the document's units unless told otherwise, so use this one.
    mp = body.GetMassProperties(1000#)
    got = mp(3)

    Note "stage " & stage & ": " & Fmt(got) & " m3 (expected " & Fmt(expected) & ")"

    If Abs(got - expected) > VOL_TOL * expected Then
        Fail "stage " & stage & " volume is " & Fmt(got) & " m3 but should be " & _
             Fmt(expected) & " m3 (" & Fmt(100# * (got - expected) / expected) & " %)."
    End If

    box = body.GetBodyBox
    CheckExtent stage, "x min", box(0), x0
    CheckExtent stage, "y min", box(1), y0
    CheckExtent stage, "z min", box(2), z0
    CheckExtent stage, "x max", box(3), x1
    CheckExtent stage, "y max", box(4), y1
    CheckExtent stage, "z max", box(5), z1

End Sub


Private Function TheBody(ByVal stage As String) As SldWorks.Body2

    Dim bodies As Variant

    ' Body pointers do not survive a feature, so never cache one.
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "stage " & stage & " left no solid body."
    If UBound(bodies) <> 0 Then
        Fail "stage " & stage & " left " & (UBound(bodies) + 1) & " solid bodies; " & _
             "the CFD domain has to be one. A boolean did not merge."
    End If
    Set TheBody = bodies(0)

End Function


Private Sub CheckExtent(ByVal stage As String, ByVal what As String, ByVal got As Double, ByVal expected As Double)
    If Abs(got - expected) > BOX_TOL Then
        Fail "at stage " & stage & " the bounding box " & what & " is " & Fmt(got) & _
             " m but should be " & Fmt(expected) & " m."
    End If
End Sub


' Closed and manifold, checked independently of SolidWorks' own
' claim: in a closed solid every edge has exactly two adjacent
' faces. A free edge means an open shell that would leak in CFD.
' The kiln gas inlet and the roof are the two planes the profile
' was drawn to end on; both have to be there.
Private Sub Verify()

    Dim body As SldWorks.Body2
    Dim edges As Variant
    Dim edge As SldWorks.Edge
    Dim adj As Variant
    Dim i As Long

    phase = "checking that the solid is closed"
    Set body = TheBody("final")

    edges = body.GetEdges
    If IsEmpty(edges) Then Fail "the body has no edges."

    For i = 0 To UBound(edges)
        Set edge = edges(i)
        adj = edge.GetTwoAdjacentFaces2
        If IsEmpty(adj) Then Fail "edge " & i & " reports no adjacent faces; the body is not closed."
        If adj(0) Is Nothing Or adj(1) Is Nothing Then
            Fail "edge " & i & " has only one adjacent face; the body is an open shell."
        End If
    Next i

    If Not HasPlaneFace(2, 0#) Then Fail "no kiln gas inlet face at z = 0."
    If Not HasPlaneFace(2, zRoof) Then Fail "no roof face at z = " & Fmt(zRoof) & " m."

    Note "closed manifold solid: " & (UBound(edges) + 1) & " edges, each with two faces"

End Sub


'==================================================================
' Housekeeping. AddToDB and the two application preferences are
' global editor state: leaving them set would break the user's next
' interactive sketch, so they are restored on the way out whether
' the build succeeded or not.
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


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "calciner", msg
End Sub


' The whole log, to a file: a message box shows about 1000 characters,
' and tests/test_plant_geometry.py holds the solid to
' geometry/plant_geometry.py through it. The first line is the outcome.
Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\calciner_build.log"
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
