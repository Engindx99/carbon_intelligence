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
' C2 and a twin C1), one ILC calciner whose gooseneck (neck, one channel, a Y) feeds the
' two strings' C5s, one kiln, a grate cooler and the kiln hood with
' its tertiary air duct. Each string is the 2500 line itself, so its
' cyclones are the CFD sizes and its risers the published ones. The
' calciner (gooseneck), tertiary air duct, kiln and cooler are the
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

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const C1_D                         As Double  = 4.32         ' barrel D [published, preheater/cyclone_C1.md]
Const C1_HB                        As Double  = 6.79         ' barrel height [derived_from_reference, preheater/cyclone_C1.md]
Const C1_HC                        As Double  = 4.65         ' cone height [derived_from_reference, preheater/cyclone_C1.md]
Const C1_VD                        As Double  = 2.16         ' vortex finder D = riser D, D / 2 [derived]
Const C1_DD                        As Double  = 0.4          ' dust outlet D [derived_from_reference, preheater/cyclone_C1.md]
Const C4_D                         As Double  = 6.3          ' barrel D [published, preheater/cyclone_C4.md]
Const C4_HB                        As Double  = 6.3          ' barrel height [cfd_decision, preheater/cyclone_C4.md]
Const C4_HC                        As Double  = 7.3          ' cone height [derived_from_reference, preheater/cyclone_C4.md]
Const C4_VD                        As Double  = 3.15         ' vortex finder D = riser D, D / 2 [derived]
Const C4_DD                        As Double  = 0.81         ' dust outlet D [derived_from_reference, preheater/cyclone_C4.md]
Const C5_D                         As Double  = 6.5          ' barrel D [published, preheater/cyclone_C5.md]
Const C5_HB                        As Double  = 6.5          ' barrel height, C4 x scale [derived]
Const C5_HC                        As Double  = 7.531746     ' cone height, C4 x scale [derived]
Const C5_VD                        As Double  = 3.25         ' vortex finder D, C4 x scale [derived]
Const C5_DD                        As Double  = 0.835714     ' dust outlet D, C4 x scale [derived]
Const C5_HIN                       As Double  = 3.507937     ' volute inlet height, C4 x scale [derived]
Const C4_VF_S                      As Double  = 3.9          ' vortex finder immersion [cfd_decision, preheater/cyclone_C4.md]
Const C4_OUT_RISE                  As Double  = 5.355        ' outlet pipe rise over the roof [derived]
Const C4_OUT_R                     As Double  = 0#           ' outlet bend centreline R (0: straight, 17 Nov 2026) [derived]
Const C4_OUT_RUN                   As Double  = 0#           ' outlet leg (0: straight) [derived]
Const C4_IN_H                      As Double  = 3.4          ' volute inlet height [cfd_decision, preheater/cyclone_C4.md]
Const C4_IN_W                      As Double  = 2.912        ' volute inlet width [cfd_decision, preheater/cyclone_C4.md]
Const C4_TONGUE                    As Double  = 0.05         ' [model, preheater/cyclone_C4.md]
Const C4_IN_L                      As Double  = 2#           ' level inlet duct, its face back from the tangent plane [derived]
Const C1_VF_S                      As Double  = 3.45         ' vortex finder immersion [cfd_decision, preheater/cyclone_C1.md]
Const R1_D                         As Double  = 3.15         ' R1 = C2's outlet pipe, D_x [derived]
Const CALC_D                       As Double  = 6.7404       ' [derived_from_reference, calciner/calciner.md]
Const CALC_H                       As Double  = 30#          ' cone + cylinder [published, calciner/calciner.md]
Const CALC_THROAT_D                As Double  = 3.130077     ' throat D [derived]
Const CALC_CONE_DEG                As Double  = 65#          ' [literature, calciner/calciner.md]
Const GN_D_SRC                     As Double  = 3.5          ' a gooseneck leg [published, preheater/gooseneck.md]
Const GN_SLOPE_DEG                 As Double  = 45#          ' the neck's inclined pieces, to the horizontal [model, preheater/gooseneck.md]
Const GN_PIECE_OVER_D              As Double  = 1#           ' the neck's inclined pieces, x neck D [model, preheater/gooseneck.md]
Const GN_LEVEL_OVER_D              As Double  = 1#           ' the neck's level piece, x neck D [model, preheater/gooseneck.md]
Const GN_CHANNEL_OVER_D            As Double  = 1.5          ' the vertical channel below the neck, x neck D [model, preheater/gooseneck.md]
Const GN_ARM_DEG                   As Double  = 60#          ' each arm's angle to the vertical [model, preheater/gooseneck.md]
Const GN_ARM_RUN_OVER_D            As Double  = 2#           ' each arm's level run, x leg D [model, preheater/gooseneck.md]
Const GN_ROOT_FWD                  As Double  = 0.184956     ' the neck's first piece pierces the roof this far in front of the axis, m [derived]
Const GN_OUT_AT_H                  As Double  = 0.679740905621 ' CFD arms' level runs' axis, x CALC_H [derived]
Const CALC_TA_Z                    As Double  = 8.270908     ' tertiary air axis over the throat's foot [derived]
Const CALC_FEED_Z                  As Double  = 11.385494    ' meal pipes' axes at the wall, over the throat's foot [derived]
Const TA_D                         As Double  = 2.4393       ' tertiary air duct [derived_from_reference, calciner/calciner.md]
Const MEAL_SLOPE_DEG               As Double  = 60#          ' [literature, calciner/calciner.md]
Const KILN_D                       As Double  = 4.8          ' [published, kiln/kiln.md]
Const KILN_L                       As Double  = 74#          ' [published, kiln/kiln.md]
Const KILN_SLOPE                   As Double  = 0.03         ' slope / 100 [published, kiln/kiln.md]
Const COOLER_AREA                  As Double  = 119.6        ' m2 [published, cooler/cooler.md]
Const COOLER_W                     As Double  = 4#           ' grate width [literature, cooler/cooler.md]
Const COOLER_H                     As Double  = 3#           ' casing height [literature, cooler/cooler.md]
Const C1_RISER_X                   As Double  = 6.727386     ' C1 riser branch axis from the C1 axis [derived]
Const C1_RISER_Z0                  As Double  = 0.212614     ' C1 CFD domain floor, over the dust outlet [derived]
Const C1_BEND_Z                    As Double  = 7.712614     ' C1 branch bend start [derived]
Const C1_BEND_R                    As Double  = 2.227386     ' C1 branch bend centreline R [derived]
Const C1_BEND_DEG                  As Double  = 90#          ' C1 branch bend [derived]
Const C1_TRANS_L                   As Double  = 1.5          ' round -> duct transition [model, preheater/riser_R1.md]
Const C1_DUCT_H                    As Double  = 3#           ' C1 inlet duct height [cfd_decision, preheater/cyclone_C1.md]
Const C1_VOL_OUT                   As Double  = 3.07         ' C1 volute duct's outer wall from the C1 axis [derived]
Const C1_VOL_FAR                   As Double  = 2.226723     ' C1 volute scroll's end, the side away from the duct [derived]
Const C1_FEED_Z                    As Double  = 4.712614     ' C1 feed chute axis at the branch wall [derived]
Const C1_FEED_L                    As Double  = 1#           ' C1 feed chute depth [model, preheater/riser_R1.md]
Const C1_FEED_W                    As Double  = 0.6          ' C1 feed chute side [literature, preheater/riser_R1.md]
Const C1_OUT_RISE                  As Double  = 2.7          ' C1 outlet pipe rise [derived]
Const C1_OUT_R                     As Double  = 3.24         ' C1 outlet 180 deg bend centreline R [derived]
Const STAGE_GAP                    As Double  = 4#           ' [schematic, plant_topology.md]
Const ZIG_DX                       As Double  = 6.802848     ' outer column outboard of the inner: the widest riser's offset [derived]
Const DUST_OVER_ROOF               As Double  = 0.5          ' C4..C2's dust outlet over the roof below [schematic, plant_topology.md]
Const RISER_SLOPE_DEG              As Double  = 45#          ' R2..R4's inclined duct climbs at this slope into the level duct [schematic, preheater/cyclone_C4.md]
Const RISER_TAPER_DEG              As Double  = 15#          ' the inclined duct's sides narrow from D to W at this angle at most [cfd_decision, preheater/cyclone_C4.md]
Const R4_RISE_V                    As Double  = 7.035957     ' R4 vertical, C5's roof to its turn [derived]
Const R3_RISE_V                    As Double  = 7.035957     ' R3 vertical, C4's roof to its turn [derived]
Const R2_RISE_V                    As Double  = 7.035957     ' R2 vertical, C3's roof to its turn [derived]
Const RISER_RUN                    As Double  = 2.95988      ' R2/R3's transition: horizontal run, riser axis to the level duct's face [derived]
Const RISER_RUN4                   As Double  = 2.95988      ' R4's transition: horizontal run [derived]
Const RISER_Y                      As Double  = 4.656        ' a riser's axis across from its cyclone's axis (depth): under the duct [derived]
Const C5_OVER_TA                   As Double  = 1.75         ' [schematic, plant_topology.md]
Const GN_TO_C5_GAP                 As Double  = 1#           ' [schematic, plant_topology.md]
Const C1_TWIN_GAP                  As Double  = 1#           ' twin C1: gap between the branches' walls [model, preheater/riser_R1.md]
Const C1_TWIN_S                    As Double  = 8.507386     ' twin C1: axis to axis [derived]
Const C1_DUCT_Y                    As Double  = 2.64         ' C1 inlet duct / branch axis from the C1 axis [derived]
Const R1_BRANCH_HALF               As Double  = 1.613693     ' R1's Y: each branch from R1's axis [derived]
Const R1_UP_MIN                    As Double  = 0.5          ' [schematic, plant_topology.md]
Const KILN_AXIS_Z                  As Double  = 10#          ' [schematic, plant_topology.md]
Const CHAMBER_MARGIN               As Double  = 1#           ' [model, kiln/kiln_inlet_chamber.md]
Const KIC_RAMP_DEG                 As Double  = 50#          ' KIC ramp, to the horizontal [model, kiln/kiln_inlet_chamber.md]
Const KIC_RAMP_FOOT                As Double  = 1.5          ' KIC ramp's level foot, toe to the kiln mouth [model, kiln/kiln_inlet_chamber.md]
Const KIC_TOP                      As Double  = 5.950031     ' KIC floor level to its top = the calciner's throat foot (the roof's highest point under the throat) [derived]
Const COOLER_DROP                  As Double  = 1#           ' [schematic, plant_topology.md]
Const HOOD_L                       As Double  = 5.98         ' kiln hood: depth along x from the kiln's end (the cooler's hood opening) [derived]
Const HOOD_H                       As Double  = 7.2          ' kiln hood: height, the cooler's roof to the seal's top + clearance [derived]
Const HOOD_TA_X                    As Double  = 4.485        ' kiln hood: the tertiary air mouth's axis from the kiln's end, x [derived]
' END GENERATED

' Cyclones [m]: D, barrel, cone, vortex finder D, dust outlet D --
' the CFD sizes, which every string uses as they are: C1 (cyclone_C1.md),
' C2 = C3 = C4 (cyclone_C4.md, catalog.md deviation), C5 the CFD C4
' x 6.50 / 6.30 (cyclone_C5.md).
' -> C1_D, C1_HB, C1_HC, C1_VD, C1_DD, C4_D: in the generated block above
' The CFD barrel, h = D, not the catalogue's 3.46 m (cyclone_C4.md,
' catalog.md deviation, user decision 4 Oct 2026).
' -> C4_HB, C4_HC, C4_VD, C4_DD, C5_D, C5_HB, C5_HC, C5_VD, C5_DD, C5_HIN: in the generated block above
'    C5_HIN: its volute inlet's height; a gooseneck leg runs into it
' C5 is the C4 CFD domain x 6.50 / 6.30 throughout (see Kc): its vortex finder, volute and outlet
' pipe -- R4 itself, as C4 / C3's are R3 / R2
' C2-C4 as the C4 CFD domain (cyclone_C4.md, cyclone.bas, S 3.90): the vortex finder 3.90 m
' down from the roof; the gas outlet pipe (D_x) 7.87 m (1.70 D_x) straight up over it, the
' domain's end; the inlet a volute 3.40 m high under the roof, a 2.912 m wide duct and a half
' turn of Archimedean spiral 0.05 m (the tongue) off the barrel, fed by a level duct 1.0 m from
' the barrel's tangent plane and, under it, a riser whose walls turn in at 45 deg (user
' decision, 17 Nov 2026). In the plant C5..C3's outlet pipes are R4..R2 themselves: straight up
' beside the next cyclone, past the CFD's 7.87 m, into its inlet. Until 17 Nov 2026 the outlet
' turned through a 90 deg bend (R 1.0 D_x) into a 4.63 m level leg, the columns 15 m apart.
' tests/test_plant_topology_cfd_lock.py holds these to cyclone.bas
' -> C4_VF_S, C4_OUT_RISE, C4_OUT_R, C4_OUT_RUN, C4_IN_H, C4_IN_W, C4_TONGUE, C4_IN_L, C1_VF_S: in the generated block above
'    C4_OUT_RISE: 1.70 D_x (1.25 until 14 Oct 2026); the CFD part of each riser
'    C4_OUT_R, C4_OUT_RUN: 0, the outlet does not turn (17 Nov 2026)
'    C4_IN_L: the level inlet duct's length from the barrel's tangent plane
'    ZIG_DX, RISER_SLOPE_DEG, RISER_TAPER_DEG, RISER_RUN, RISER_RUN4, R2_RISE_V .. R4_RISE_V, DUST_OVER_ROOF: R4..R2
'      (user decisions, 17 and 22 Nov 2026): each the outlet pipe of the cyclone below, straight up beside the one
'      above, under its level duct; a flat-faced duct climbs from it at RISER_SLOPE_DEG into the level duct, mitred
'      to it, the riser's top cut by its roof, its floor meeting the riser's front half (plant_geometry.riser_elbow).
'      RISER_RUN(4): riser axis to the duct's face (true, along the duct). The columns ZIG_DX apart (the widest
'      riser's offset, plant_geometry.riser_inlet); each C4..C2 with its dust outlet DUST_OVER_ROOF over the roof
'      below. In this view the inclined duct and the level duct are projected on the sheet (RiserOutline; they
'      run obliquely in depth): the riser's outline, the inclined roof's and floor's edges, the duct level on
'    C1_VF_S: C1's vortex finder, down from the roof (C1 CFD)

' Risers [m] -- HFC2500 (published), catalog.md; R_k carries the gas
' from C(k+1) up to C(k). Each string has its own; R1 splits into
' the twin C1, each branch half its area. R2..R4 are the C3..C5 CFD
' outlet pipes (D_x), see RiserD.
' -> R1_D: in the generated block above

' Calciner [m] -- calciner.bas / calciner.md, the 5000 t/d plant's (PF5000)
' -> CALC_D, CALC_H, CALC_THROAT_D, CALC_CONE_DEG, GN_D_SRC, GN_SLOPE_DEG, GN_PIECE_OVER_D, GN_LEVEL_OVER_D,
'    GN_CHANNEL_OVER_D, GN_ARM_DEG, GN_ARM_RUN_OVER_D, GN_OUT_AT_H, TA_D: in the generated block above;
'    CALC_TA_Z, CALC_FEED_Z: the tertiary air duct and the meal pipes where calciner.bas builds them
'    CALC_H: cone + cylinder
'    GN_D_SRC: a gooseneck arm, one 2500 t/d string's published neck; the neck and its channel have both arms' area
'    GN_SLOPE_DEG .. GN_ROOT_FWD: the neck's three pieces, its vertical channel and the Y's arms, as calciner.bas builds them
'    GN_OUT_AT_H: the arms' level runs' axis, as a fraction of CALC_H (C5's inlet axis)
'    TA_D: tertiary air duct, derived in calciner.md
Const TA_BEND_R_OVER_D As Double = 1.5     ' its turn from the hood over to the calciner: a long-radius bend, centreline R
                                           ' this many D, as the gooseneck's (schematic; it has no CFD)

' Meal pipes end at the slope of the calciner feed pipes, Fidaros 2007
' (calciner.md): a chute at 60 deg meets an upright riser wall at
' 30 deg, sliding in along it.
' -> MEAL_SLOPE_DEG: in the generated block above

' Kiln [m] -- kiln.md (PF5000); cooler -- cooler.md, grate area [m2] (PF5000)
' -> KILN_D, KILN_L, KILN_SLOPE, COOLER_AREA: in the generated block above

' SCHEMATIC -- no source; they only lay the plant out.
' -> STAGE_GAP, ZIG_DX, C5_OVER_TA, GN_TO_C5_GAP: in the generated block above
'    STAGE_GAP: C1's dust outlet at least this far over C2's stub [m]: the C1 meal reaching R2's upright from over C2 (R1's Y could set it higher). C2..C4 stand where the outlet below (as its CFD) runs into them
'    ZIG_DX: a string's outer column (C4, C2) outboard of its inner one (C5, C3) [m]: each riser's leg past the CFD outlet face, its taper and 0.5 m (14.6 m for R4); was 20
'    C5_OVER_TA: the C5 dust outlets at least this far over the tertiary air duct [m]
'    GN_TO_C5_GAP: a gooseneck arm's outlet face to its C5 barrel; the level run goes on across it [m]
' Each of the twin C1 as its CFD domain (cyclone_C1.md, riser_R1.md): heights over its dust outlet [m, deg]
' -> C1_RISER_X, C1_RISER_Z0, C1_BEND_Z, C1_BEND_R, C1_BEND_DEG, C1_TRANS_L, C1_DUCT_H, C1_VOL_OUT, C1_VOL_FAR, C1_FEED_Z, C1_FEED_L, C1_FEED_W, C1_OUT_RISE, C1_OUT_R, R1_BRANCH_HALF, R1_UP_MIN: in the generated block above
'    C1_RISER_X: its own riser branch (D = R1's half area), its axis this far from the C1 axis
'    C1_RISER_Z0: the CFD domain's floor: the branch is straight from here ...
'    C1_BEND_Z: ... up to its bend
'    C1_BEND_R: bend centreline radius (1.0 D), its walls arcs
'    C1_BEND_DEG: the bend: from straight up to the inlet duct's axis (90: the volute's duct is level)
'    C1_TRANS_L: round -> rectangular transition along the duct axis, then the duct into the barrel
'    C1_DUCT_H: inlet duct height (the volute's, 0.86 wide, flush with the roof; user decision 16 Nov 2026)
'    C1_VOL_OUT: the volute duct's outer wall from the C1 axis, on the branch's side
'    C1_VOL_FAR: the volute's scroll end, past the barrel on the side away from the branch
'    C1_FEED_Z: the meal chute's axis meets the branch wall here, on the side away from the C1
'    C1_FEED_L: ... standing out this far along its axis, at MEAL_SLOPE_DEG
'    C1_FEED_W: ... 0.6 x 0.6 square
'    C1_OUT_RISE: gas outlet pipe (D = C1_VD) straight up over the roof ...
'    C1_OUT_R: ... a 180 deg bend away from the branch, its walls arcs, and down as far as it rose
'    The twin (user decision, 13 Nov 2026): a mirror pair, each C1 turned so its branch, bend and inlet duct
'    run in depth (+y, away from the viewer), the ducts facing each other; R1 on the mirror plane in front.
'    C1_TWIN_GAP: the two branches' walls this far apart; C1_TWIN_S (axis to axis) and R1_BRANCH_HALF follow
'    C1_DUCT_Y: each branch (and its duct) this far from its C1's axis, towards R1
'    R1_BRANCH_HALF: R1's Y: the twin's branches this far either side of R1's axis [m]
'    R1_UP_MIN: R1 straight up at least this far over C2's CFD outlet pipe before its Y; the C1 stage stands that high [m]
'    R1_D: R1 is C2's outlet pipe straight up on C2's axis (user decision, 17 Nov 2026), its bore C2's D_x
'      (21 Nov 2026: D_x = riser D = D / 2; the reducer D_x -> 3.07 is gone). Before, C2's CFD bend and leg
'      turned it over to an elbow 11.3 m towards the calciner
Const ID_FAN_L       As Double = 2.5      ' "to ID fan": an arrow this long down from each C1 outlet's leg [m]
Const RM_L           As Double = 0.8      ' raw meal: a small-headed arrow along each chute's axis, from this far past its end [m]
Const MEAL_ENTRY_UP  As Double = 1.5      ' meal enters a riser this far over its foot (R2..R4: over the roof, into the CFD outlet pipe) [m]
Const MEAL_SIDE_L    As Double = 1#       ' a meal pipe's end into a wall comes this far out from it, then into it at the meal slope [m]
Const MEAL_DROP      As Double = 1.5      ' a C1..C3's meal falls straight this far out of its dust outlet before it turns [m]
Const MEAL_JOIN_DEG  As Double = 50#      ' the near C1's meal runs at this slope, behind C2's outlet pipe and R1, to join the far one's [deg]
Const C4_MEAL_DROP   As Double = 3#       ' C4 meal falls straight this far before turning towards the calciner. Its run on,
                                          ' behind C5, is flatter than meal flows: a 2D projection, as the C5 meal's [m]
Const C5_MEAL_DROP   As Double = 1#      ' C5 meal falls straight this far before turning towards the inlet chamber [m]
Const MEAL_BEND      As Double = 1#       ' a bend piece this long after a C4 / C5 meal's straight drop, halving its turn [m]
Const CROSS_GAP      As Double = 0.5      ' a meal pipe is broken this far either side of an outline it passes behind [m]
' -> KILN_AXIS_Z, CHAMBER_MARGIN, COOLER_W, COOLER_H, COOLER_DROP: in the generated block above
'    KILN_AXIS_Z: kiln inlet axis elevation [m]
'    CHAMBER_MARGIN: kiln inlet chamber and hood: a square this far round the kiln [m]
'    COOLER_W: grate width [m], the FLS reference cooler's; the length follows from the area
'    COOLER_H: cooler casing height [m]
'    COOLER_DROP: cooler top below the kiln shell at discharge [m]
Const MEAL_INTO_CHAMBER As Double = 1#    ' C5 meal lands this far in from the chamber's side [m]
Const C5_ARROW_FROM_END As Double = 5#    ' the two C5 pipes' arrows: this far back from the throat, so both stand alike [m]
Const MIN_SEG        As Double = 0.05     ' a wall piece beside an opening shorter than this is left out [m]
Const CLINKER_OUT_Z  As Double = 3.5      ' clinker transport drawn this far below ground [m]
Const VENT_IN        As Double = 3#       ' cooler vent this far in from the cooler's end [m]
Const VENT_UP        As Double = 4#       ' vent arrow drawn this far over the cooler roof [m]
Const CLINKER_ON_GRATE As Double = 1#     ' clinker line this far over the cooler floor [m]
Const TA_ARROW_LONG  As Double = 1.15     ' tertiary air arrow this many times the rise from the cooler's mid-height to the hood roof; it runs on up into its duct [-]
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
Const AXIS_OVER As Double = 0.6      ' a cyclone's centre line past its roof [m] (~2 mm at 1:300)
Const AXIS_UNDER As Double = 0.1     ' ... and past its dust outlet: under DUST_OVER_ROOF, clear of the riser turning in below [m]
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
Dim aCh As Double, zCh0 As Double         ' chamber: |x| <= aCh, z from zCh0, 2 aCh tall (the hood: HOOD_L x HOOD_H)
Dim rampTan As Double                     ' slope of the chamber's ramp, KIC_RAMP_DEG
Dim zLip As Double, xToe As Double        ' the kiln mouth's lower lip; the ramp's toe, KIC_RAMP_FOOT in from the mouth
Dim zToe As Double                        ' the toe's height: the foot falls at KILN_SLOPE to the lip
Dim zRampTop As Double                    ' the ramp's top, on the throat's left wall
Dim rCalc As Double, rThroat As Double, hCone As Double
Dim zThroat As Double, zConeTop As Double, zCalcRoof As Double
Dim rGn As Double, rNeck As Double, gnBeta As Double, gnPiece As Double, gnLevel As Double, gnChan As Double
Dim xLeg As Double, zGnTop As Double, zLeg As Double      ' the arms' outlet faces, x; the neck's crown, z; the arms' level runs' axis, z
Dim gnYoff As Double                      ' the neck's and channel's plane, in front of the vessel (y = -this)
Dim zSplit As Double, xBend As Double, armAng As Double  ' the channel's lower end, z; where an arm turns level, x; arm angle to the vertical
Dim zWall As Double                       ' where an arm's upper edge leaves the channel's wall, z (the channel's walls end here)
Dim zFeed As Double                       ' C4 meal reaches the calciner wall here
Dim kAlpha As Double
Dim kAx As Double, kAz As Double, kBx As Double, kBz As Double
Dim coolL As Double, zCool0 As Double, zHood0 As Double
Dim rTA As Double, zTA As Double
Dim zDust(1 To 5) As Double, zRoof(1 To 5) As Double, zTop(1 To 5) As Double
Dim zIn(1 To 5) As Double                 ' gas inlet centre, its top at the roof
Dim xInner As Double                      ' |x| of a string's inner column (C5, C3)
Dim dC1 As Double                         ' each twin C1 from R1's axis
Dim dR1 As Double                         ' R1's axis from C2's, towards the calciner: 0 since R1 rises on C2's axis
Dim zTower As Double                      ' the tower's top: the C1 outlet bends

' drawing state
Dim curLayer As String
Dim layerNames(LAYER_N - 1) As String
Dim nLine(LAYER_N - 1) As Long, nArc(LAYER_N - 1) As Long, nNotes As Long
Dim pxMin As Double, pxMax As Double, pyMin As Double, pyMax As Double
Dim noteWarned As Boolean
' Closed outlines a meal pipe may pass behind (every cyclone, the
' tertiary air duct): their edges, kept for PathM, not drawn
Dim bdXa(1 To 400) As Double, bdZa(1 To 400) As Double, bdXb(1 To 400) As Double, bdZb(1 To 400) As Double
Dim nBd As Long

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
    ' no message box when OUT_ROOT\quiet.flag exists (tools/sw_run.py)
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox "Plant topology 2D built and verified: two 2500 t/d strings, 12 cyclones, A1 at 1:" & Fmt(SHEET_SCALE) & _
               "." & vbLf & LayerSummary() & vbLf & vbLf & "Full log: " & LogPath(), vbInformation, "Plant topology 2D"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    buildLog = buildLog & "ABORTED while " & phase & ": " & why & vbLf
    WriteLog
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox "Plant topology 2D ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
               vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Plant topology 2D"
    End If

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
    zThroat = zCh0 + KIC_TOP                  ' the calciner sits on the chamber's roof (22 Nov 2026)
    zConeTop = zThroat + CALC_THROAT_D + hCone
    zCalcRoof = zThroat + CALC_THROAT_D + CALC_H

    ' Its gooseneck as calciner.bas builds it (seen in the x-z plane): a
    ' neck of both arms' area, three straight pieces (up, level, down)
    ' bending forward (-y), so in this view it is one upright band on the
    ' axis; then a vertical channel of the same width, hanging in front of
    ' the vessel; at its lower end each arm leaves at armAng to the
    ' vertical, down to the level run's axis (C5's inlet axis), then
    ' level across into the C5.
    rGn = 0.5 * GN_D_SRC
    rNeck = rGn * Sqr(2#)
    gnBeta = GN_SLOPE_DEG * PI / 180#
    gnPiece = GN_PIECE_OVER_D * 2# * rNeck
    gnLevel = GN_LEVEL_OVER_D * 2# * rNeck
    gnChan = GN_CHANNEL_OVER_D * 2# * rNeck
    armAng = GN_ARM_DEG * PI / 180#
    zGnTop = zCalcRoof + gnPiece * Sin(gnBeta) + rNeck          ' the level piece's top
    zSplit = zCalcRoof - gnChan                                 ' the third piece ends at the roof's height
    zLeg = zThroat + CALC_THROAT_D + GN_OUT_AT_H * CALC_H
    gnYoff = GN_ROOT_FWD + 2# * gnPiece * Cos(gnBeta) + gnLevel
    xBend = (zSplit - zLeg) * Tan(armAng)
    zWall = zSplit + rGn * Sin(armAng) - ((rNeck - rGn * Cos(armAng)) / Sin(armAng)) * Cos(armAng)
    xLeg = xBend + GN_ARM_RUN_OVER_D * 2# * rGn
    ' The C4 meal reaches the calciner where calciner.bas's meal pipes
    ' meet its wall, just over the tertiary air duct
    zFeed = zThroat + CALC_FEED_Z

    ' The tertiary air duct from the hood to the calciner, where
    ' calciner.bas builds it: its lower edge on the top of the cone
    rTA = 0.5 * TA_D
    zTA = zThroat + CALC_TA_Z

    ' Each string: C5 GN_TO_C5_GAP outboard of its outlet face. The
    ' full-size C5 is 14 m tall, so it stands C5_OVER_TA over the
    ' tertiary air duct, and the arms' level runs are at its inlet axis
    ' (the roof less a leg radius), as plant_geometry.layout.
    CycDims 5, d, hb, hc, vd, dd
    xInner = xLeg + rGn + GN_TO_C5_GAP + 0.5 * d
    zDust(5) = zTA + rTA + C5_OVER_TA

    ' The kiln runs out of the chamber's +x side, falling KILN_SLOPE
    ' towards the cooler. The chamber (user sketch, 21 Nov 2026) has no
    ' roof ledges: the throat's walls run down, the right one to the
    ' kiln's roof line, the left one to the ramp's top; the ramp falls at
    ' KIC_RAMP_DEG to a foot KIC_RAMP_FOOT long at the kiln mouth's lower
    ' lip, so meal and spillage slide into the kiln. The foot and the
    ' right wall's run to the mouth carry the kiln shell's lines in, at
    ' KILN_SLOPE (no kink at the mouth; the foot falls towards the kiln).
    kAx = aCh: kAz = KILN_AXIS_Z
    rampTan = Tan(KIC_RAMP_DEG * PI / 180#)
    zLip = kAz - 0.5 * KILN_D / Cos(kAlpha)
    xToe = aCh - KIC_RAMP_FOOT
    zToe = zLip + KIC_RAMP_FOOT * KILN_SLOPE
    zRampTop = zToe + (xToe + rThroat) * rampTan
    kBx = kAx + KILN_L * Cos(kAlpha)
    kBz = kAz - KILN_L * Sin(kAlpha)

    ' C4..C2 (user decision, 17 Nov 2026): each over the cyclone below,
    ' its dust outlet DUST_OVER_ROOF over that roof (the cyclone two
    ' below shares its column, its riser's top just under this roof),
    ' or as high as the CFD outlet pipe below and the riser's turn ask;
    ' C1 over C2's stub
    For s = 4 To 2 Step -1
        zDust(s) = zDust(s + 1) + (CycHeight(s + 1) - CfdRise(s + 1)) _
                 + Max2(Kc(s) * (C4_HC + C4_HB) + DUST_OVER_ROOF, CfdRise(s + 1) + RiserDrop(s)) _
                 - Kc(s) * (C4_HC + C4_HB)
    Next s
    zDust(1) = zDust(2) + CycHeight(2) + STAGE_GAP
    ' R1 rises straight out of C2's outlet pipe on C2's axis (user
    ' decision, 17 Nov 2026), its bore C2's D_x, R1_UP_MIN at least
    ' and splits; the twin C1 stand as high as that asks, their CFD
    ' domain over it
    zDust(1) = Max2(zDust(1), zDust(2) + CycHeight(2) + R1_UP_MIN + R1YRise() - C1_RISER_Z0)
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

    ' The twin C1 either side of R1's axis, their ducts facing each
    ' other, their branches R1_BRANCH_HALF either side of it; the
    ' tower's top over their outlet bends (turned in depth)
    dC1 = 0.5 * C1_TWIN_S
    dR1 = 0#                                   ' R1 on C2's axis (17 Nov 2026; it stood over C2's outlet leg)
    zTower = zTop(1) + C1_OUT_R + 0.5 * C1_VD

    ' Cooler under the kiln's discharge, running on in +x; the hood on
    ' it round the kiln's end (a box sized from the outlet seal, HOOD_L
    ' deep, HOOD_H tall: kiln_hood(), 23 Nov 2026).
    coolL = COOLER_AREA / COOLER_W
    zCool0 = kBz - 0.5 * KILN_D - COOLER_DROP - COOLER_H
    zHood0 = zCool0 + COOLER_H

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


' Dust outlet to the top of the CFD's gas outlet pipe: C2..C5 the C4
' CFD's 7.87 m (C5's scaled); R4..R2 run on from there.
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

' R(k)'s inclined duct (k = 2..4; plant_geometry.riser_elbow, 22 Nov
' 2026), in C(k)'s frame (the level duct along x, its face at x = -L):
' run (riser axis back from the face), its vertical depth hv, where
' its roof / floor meet the level duct's (xrm / xfm) and its width at
' the riser (w0: the riser's D, or W if wider)
Private Sub RiserDuctDims(ByVal k As Long, ByRef run As Double, ByRef hv As Double, ByRef xrm As Double, _
                          ByRef xfm As Double, ByRef w0 As Double)
    Dim al As Double, l As Double, h As Double
    If k = 4 Then run = RISER_RUN4 Else run = RISER_RUN
    al = RISER_SLOPE_DEG * PI / 180#
    l = Kc(k) * C4_IN_L: h = Kc(k) * C4_IN_H
    hv = h / Cos(al)
    xrm = -l - 0.5 * h * Tan(0.5 * al)
    xfm = -l + 0.5 * h * Tan(0.5 * al)
    w0 = Max2(2# * StubR(k + 1), Kc(k) * C4_IN_W)
End Sub

' its floor at x, z (through the face's centre line, rising at the slope)
Private Function RiserFloorZ(ByVal k As Long, ByVal x As Double) As Double
    Dim al As Double
    al = RISER_SLOPE_DEG * PI / 180#
    RiserFloorZ = zRoof(k) - 0.5 * Kc(k) * C4_IN_H + (x + Kc(k) * C4_IN_L) * Tan(al) _
                  - 0.5 * Kc(k) * C4_IN_H / Cos(al)
End Function

' its width at x: w0 to the riser's front, W from xrm on
Private Function RiserDuctW(ByVal k As Long, ByVal x As Double) As Double
    Dim run As Double, hv As Double, xrm As Double, xfm As Double, w0 As Double, x0 As Double
    RiserDuctDims k, run, hv, xrm, xfm, w0
    x0 = -(run + Kc(k) * C4_IN_L) + StubR(k + 1)
    If x <= x0 Then
        RiserDuctW = w0
    ElseIf x >= xrm Then
        RiserDuctW = Kc(k) * C4_IN_W
    Else
        RiserDuctW = w0 + (Kc(k) * C4_IN_W - w0) * (x - x0) / (xrm - x0)
    End If
End Function

' R(k) (k = 2..4): the seam's foot (the inclined floor at the riser's
' axis, where its straight part ends) under C(k)'s roof
Private Function RiserDrop(ByVal k As Long) As Double
    Dim run As Double
    If k = 4 Then run = RISER_RUN4 Else run = RISER_RUN
    RiserDrop = zRoof(k) - RiserFloorZ(k, -(run + Kc(k) * C4_IN_L))
End Function

' A point (x, y, z) of C(k)'s frame on the sheet: t from the riser's
' axis towards C(k)'s (the sheet holds both axes, ZIG_DX apart)
Private Function SheetT(ByVal k As Long, ByVal x As Double, ByVal y As Double) As Double
    Dim run As Double, xj As Double, yd As Double
    If k = 4 Then run = RISER_RUN4 Else run = RISER_RUN
    xj = run + Kc(k) * C4_IN_L: yd = Kc(k) * RISER_Y
    SheetT = ZIG_DX - (-x * xj + y * yd) / ZIG_DX
End Function

' R(k)'s outline on the sheet past the riser's straight silhouette
' (t = -/+ D/2), outer (outerSide) or inner, as n points (t, z) from
' the silhouette's top to where it meets the level duct: outer -- the
' riser's top on the inclined roof (an arc of its ellipse to the duct's
' corner over the riser's axis), then the roof's outer edge to the
' roofs' corner; inner -- the silhouette up to where the floor's inner
' edge crosses it, then that edge to the floors' corner.
Private Sub RiserOutline(ByVal k As Long, ByVal outerSide As Boolean, ByRef n As Long, ts() As Double, zs() As Double)
    Const N_ARC As Long = 6
    Dim run As Double, hv As Double, xrm As Double, xfm As Double, w0 As Double
    Dim xj As Double, yd As Double, zz As Double, r As Double, al As Double
    Dim th0 As Double, th As Double, x As Double, y As Double, i As Long, xs(3) As Double
    RiserDuctDims k, run, hv, xrm, xfm, w0
    al = RISER_SLOPE_DEG * PI / 180#
    xj = run + Kc(k) * C4_IN_L: yd = Kc(k) * RISER_Y: zz = ZIG_DX: r = StubR(k + 1)
    ReDim ts(0 To N_ARC + 8): ReDim zs(0 To N_ARC + 8)
    n = 0
    If outerSide Then
        ' the top ellipse, theta from the silhouette (cos -xj / Z,
        ' sin yd / Z) to pi / 2 (the duct's corner on the riser's side)
        th0 = PI - Atn(yd / xj)
        For i = 0 To N_ARC
            th = th0 + (0.5 * PI - th0) * i / N_ARC
            x = -xj + r * Cos(th): y = yd + r * Sin(th)
            ts(n) = SheetT(k, x, y): zs(n) = RiserFloorZ(k, x) + hv: n = n + 1
        Next i
        xs(0) = -xj + r: xs(1) = xrm
        For i = 0 To 1
            x = xs(i)
            ts(n) = SheetT(k, x, yd + 0.5 * RiserDuctW(k, x)): zs(n) = RiserFloorZ(k, x) + hv: n = n + 1
        Next i
    Else
        x = -xj + Max2(0#, r * zz - 0.5 * yd * w0) / xj
        ts(n) = SheetT(k, x, yd - 0.5 * w0): zs(n) = RiserFloorZ(k, x): n = n + 1
        xs(0) = -xj + r: xs(1) = xrm: xs(2) = -Kc(k) * C4_IN_L: xs(3) = xfm
        For i = 0 To 3
            x = xs(i)
            If x > -xj + Max2(0#, r * zz - 0.5 * yd * w0) / xj Then
                ts(n) = SheetT(k, x, yd - 0.5 * RiserDuctW(k, x)): zs(n) = RiserFloorZ(k, x): n = n + 1
            End If
        Next i
    End If
End Sub

Private Function RiserTopZ(ByVal k As Long) As Double
    RiserTopZ = zRoof(k) - RiserDrop(k)
End Function

' R(k)'s turn into C(k)'s level duct, projected on the sheet (21 Nov
' 2026). In C(k)'s own frame the duct runs along x (its face at
' x = -L_in), across y from yIn to yOut; the riser stands at (-xj, yd),
' ZIG_DX from the axis, and the sheet holds the riser and cyclone axes.
' A point (x, y) lies t = ZIG_DX - (-x xj + y yd) / ZIG_DX from the riser
' axis towards the cyclone. tOut / tIn: the duct face's top outer and
' bottom inner corners; the loft's outline runs from the riser's top
' (t = -/+ D/2) to them, the duct's top and floor level on to the barrel.
Private Sub RiserTurnT(ByVal k As Long, ByRef tOut As Double, ByRef tIn As Double)
    Dim run As Double, xj As Double, yd As Double, w As Double
    If k = 4 Then run = RISER_RUN4 Else run = RISER_RUN
    xj = run + Kc(k) * C4_IN_L
    yd = Kc(k) * RISER_Y: w = 0.5 * Kc(k) * C4_IN_W
    tOut = ZIG_DX - (xj * Kc(k) * C4_IN_L + (yd + w) * yd) / ZIG_DX
    tIn = ZIG_DX - (xj * Kc(k) * C4_IN_L + (yd - w) * yd) / ZIG_DX
End Sub


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

    ' R1 is C2's outlet pipe: the same bore
    If Abs(StubR(2) - 0.5 * RiserD(1)) > 0.000001 Then Fail "R1 (D " & Fmt(RiserD(1)) & ") is not the gas outlet of C2."
    ' R1's Y: its branches apart, its split over R1's foot and under
    ' the C1 CFD domain's floor; the two meal chutes, side by side in
    ' front of the branches, clear of each other; the barrels too
    If R1_BRANCH_HALF <= kBranch * 0.5 * RiserD(1) Then Fail "R1's branches overlap. Raise C1_TWIN_GAP."
    If Abs(dC1 - C1_DUCT_Y - R1_BRANCH_HALF) > 0.000001 Then Fail "the twin's branches are not under their ducts."
    If C1_TWIN_S - C1_D < 0.3 Then Fail "the twin C1's barrels run into each other. Raise C1_TWIN_GAP."
    If R1SplitZ() < RiserV0(1) + R1_UP_MIN - 0.001 Then Fail "R1 splits before it rises: the C1 CFD branch does not fit over C2."
    ' the twin C1 over C2's outlet pipe, R1 between them
    If zDust(1) - zTop(2) < 0.5 Then Fail "the C1s sit on C2's outlet pipe."
    If 2# * R1_BRANCH_HALF - C1_FEED_W < 0.3 Then Fail "the twin C1's meal chutes run into each other. Raise C1_TWIN_GAP."
    ' each C1's inlet duct under its roof
    If C1InletZ() + C1InletHalf() > C1_HC + C1_HB Then Fail "the C1 inlet duct runs over the C1 roof."
    ' R4..R2 (17 Nov 2026): each riser's vertical holds the CFD outlet
    ' pipe and is the length plant_geometry gives; its top under the
    ' duct's floor; in this view its inner wall and the outer wall's end
    ' outside the barrel above; the cyclone two up over its top
    For k = 4 To 2 Step -1
        If RiserTopZ(k) - zRoof(k + 1) < CfdRise(k + 1) - 0.000001 Then
            Fail "R" & k & "'s vertical (" & Fmt(RiserTopZ(k) - zRoof(k + 1)) & " m) is shorter than C" & (k + 1) & _
                 "'s CFD outlet pipe (" & Fmt(CfdRise(k + 1)) & " m)."
        End If
        If Abs(RiserTopZ(k) - zRoof(k + 1) - Choose(k - 1, R2_RISE_V, R3_RISE_V, R4_RISE_V)) > 0.000002 Then
            Fail "R" & k & "'s vertical is " & Fmt(RiserTopZ(k) - zRoof(k + 1)) & " m here but " & _
                 Fmt(Choose(k - 1, R2_RISE_V, R3_RISE_V, R4_RISE_V)) & " m in plant_geometry."
        End If
        If RiserTopZ(k) >= zRoof(k) - Kc(k) * C4_IN_H Then Fail "R" & k & "'s top is not below C" & k & "'s duct floor."
        If ZIG_DX - StubR(k + 1) <= CycR(k) Then Fail "R" & k & " runs into C" & k & "'s barrel in this view."
        ' the riser's frame and the columns' offset agree (plant_geometry.riser_inlet)
        If Abs(Sqr((IIf(k = 4, RISER_RUN4, RISER_RUN) + Kc(k) * C4_IN_L) ^ 2 + (Kc(k) * RISER_Y) ^ 2) - ZIG_DX) > 0.00001 Then
            Fail "R" & k & ": riser run, duct length and RISER_Y do not put it ZIG_DX off C" & k & "'s axis."
        End If
        ' its projected turn: the duct face between the riser's top and the barrel
        Dim tOuter As Double, tInner As Double
        RiserTurnT k, tOuter, tInner
        If tOuter <= -StubR(k + 1) Or tInner <= StubR(k + 1) Or tInner >= ZIG_DX - CycR(k) Or tOuter >= tInner Then
            Fail "R" & k & "'s turn into C" & k & " does not project between the riser and the barrel (t " & Fmt(tOuter) & " .. " & Fmt(tInner) & ")."
        End If
        If k < 4 Then
            If zDust(k - 1) - zRoof(k) < DUST_OVER_ROOF - 0.000001 Then Fail "C" & (k - 1) & " sits on R" & k & "'s top."
        End If
    Next k
    If zDust(4) - zRoof(5) < DUST_OVER_ROOF - 0.000001 Then Fail "C4 sits on C5's roof."
    ' each riser's level top under its duct's floor, so the loft's inner
    ' wall rises to it (plant_geometry.riser_inlet; 21 Nov 2026 D_x = D / 2
    ' made the riser narrower than the duct is tall: the old D_x >= H check
    ' was the bend-and-leg layout's)
    For k = 2 To 4
        If RiserDrop(k) <= Kc(k) * C4_IN_H Then Fail "R" & k & "'s top is not below C" & k & "'s inlet duct floor."
    Next k
    If CycR(5) < Kc(5) * C4_IN_L Then Fail "the gooseneck runs into C5's CFD inlet duct."
    ' The C5s clear of the calciner; the gooseneck rises clear of each other
    If xInner - r5 <= rCalc Then Fail "the C5s run into the calciner."
    If rNeck >= rCalc Then Fail "the gooseneck neck is wider than the calciner roof."
    ' Each leg's run fits the C5 inlet it enters
    If 2# * rGn > C5_HIN Then Fail "the gooseneck legs (D " & Fmt(2# * rGn) & _
        ") are taller than the C5 inlet (" & Fmt(C5_HIN) & ") they enter."
    ' the arms' level runs are at C5's inlet axis, and the Y fits above them
    If Abs(zLeg - zIn(5)) > 0.001 Then
        Fail "the gooseneck's level runs (z " & Fmt(zLeg) & ") are not at C5's inlet axis (z " & Fmt(zIn(5)) & _
             "). GN_OUT_AT_H and the layout disagree."
    End If
    If zSplit - zLeg <= rGn * Tan((PI / 2# - armAng) / 2#) Then
        Fail "the Y's arms fall " & Fmt(zSplit - zLeg) & " m, no more than their mitre needs."
    End If
    ' The C4 meal reaches the calciner's cylinder, over the cone
    If zFeed <= zTA + rTA Then Fail "the C4 meal would reach the calciner in its tertiary air duct."
    ' The tertiary air duct runs under the C5s and over the chamber and kiln
    If zTA + rTA >= zDust(5) Then Fail "the tertiary air duct runs into the C5s."
    ' and under the C5 meal's straight drop
    If zDust(5) - C5_MEAL_DROP <= zTA + rTA + 0.3 Then Fail "the C5 meal's straight drop ends in the tertiary air duct."
    ' and over the kiln and the inlet chamber
    If zTA - rTA <= zThroat Or zTA - rTA <= kAz + 0.5 * KILN_D Then
        Fail "the tertiary air duct runs into the kiln or the inlet chamber."
    End If
    ' The cooler above ground, the hood on it
    If zCool0 <= 0# Then Fail "the cooler floor is at z = " & Fmt(zCool0) & " m, below ground. Raise KILN_AXIS_Z."
    If Abs(zHood0 - (zCool0 + COOLER_H)) > 0.001 Then Fail "the kiln hood does not sit on the cooler."
    If aCh <= rThroat Then Fail "the kiln inlet chamber is narrower than the calciner throat."
    ' its ramp no flatter than meal's angle of repose, ~40 deg
    If KIC_RAMP_DEG < 39# Then
        Fail "the kiln inlet chamber's ramp is " & Fmt(KIC_RAMP_DEG) & " deg, too flat for meal to slide."
    End If
    ' its toe between the throat's left wall and the mouth, its top under the throat's foot
    If xToe <= -rThroat Or xToe > aCh Then Fail "the kiln inlet chamber's ramp foot is " & Fmt(KIC_RAMP_FOOT) & " m: its toe leaves the chamber."
    If zRampTop >= zCh0 + KIC_TOP Then
        Fail "the kiln inlet chamber's ramp reaches z = " & Fmt(zRampTop) & " m, over the throat's foot. Lengthen KIC_RAMP_FOOT or flatten KIC_RAMP_DEG."
    End If
    ' The kiln's gas and material lines inside its shell
    If KILN_FLOW_OFF >= 0.5 * KILN_D Then Fail "KILN_FLOW_OFF puts the kiln's flow lines outside its shell."
    ' The plant fits the sheet, left of the legend
    If X0 - Max2(xm + 0.5 * ZIG_DX + VoluteReach(2), xm + 0.5 * ZIG_DX - dR1 + dC1 + CycR(1)) / SHEET_SCALE _
       < RULER_X + 0.01 Or _
       X0 + (kBx + coolL) / SHEET_SCALE > COL_X0 - 0.01 Or Y0 + (zTower + 11#) / SHEET_SCALE > FR_Y1 - 0.005 Then
        Fail "the plant does not fit the A1 sheet at 1:" & Fmt(SHEET_SCALE) & "."
    End If

    Note "kiln inlet chamber: x " & Fmt(-rThroat) & " .. " & Fmt(aCh) & " m, z " & Fmt(zLip) & " .. " & Fmt(zCh0 + KIC_TOP) & _
         "; ramp " & Fmt(KIC_RAMP_DEG) & " deg, top z " & Fmt(zRampTop) & ", toe x " & Fmt(xToe)
    Note "calciner: z " & Fmt(zThroat) & " .. " & Fmt(zCalcRoof) & "; gooseneck neck D " & Fmt(2# * rNeck) & ", crown z " & Fmt(zGnTop) & ", channel down to z " & Fmt(zSplit) & _
         ", arms turn level at x +-" & Fmt(xBend) & ", outlet faces at x +-" & Fmt(xLeg) & ", C5 inlet at z " & Fmt(zIn(5))
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
    nBd = 0

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
    Dim zx As Double, zc As Double, kOff As Double, xe As Double, xn As Double
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
    zTopCh = zCh0 + KIC_TOP
    zTopHd = zHood0 + HOOD_H

    ' kiln inlet chamber (user sketch, 21 Nov 2026): no roof ledges. The
    ' throat's right wall runs down to the kiln's roof line, then along it
    ' (KILN_SLOPE) to the kiln's upper lip; its left wall down to the
    ' ramp's top, the ramp down to its toe, the foot along the kiln's
    ' floor line (KILN_SLOPE) to the kiln's lower lip
    PolyM Array(rThroat, zTopCh, rThroat, kAz + kSh + (aCh - rThroat) * KILN_SLOPE, aCh, kAz + kSh)
    PolyM Array(-rThroat, zTopCh, -rThroat, zRampTop, xToe, zToe, aCh, kAz - kSh)
    ' calciner: no floor (the throat), the tertiary air port in its +x
    ' wall over the cone (the duct's hair of clearance under it is not
    ' drawn: 0.2 mm on the sheet), the two gooseneck rises in its roof
    PolyM Array(rThroat, zThroat, rThroat, zThroat + CALC_THROAT_D, rCalc, zConeTop)
    Seg rCalc, zTA + rTA, rCalc, zCalcRoof
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
    Seg kBx, zTopHd, kBx + HOOD_TA_X - 0.5 * TA_D, zTopHd
    Seg kBx + HOOD_TA_X + 0.5 * TA_D, zTopHd, kBx + HOOD_L, zTopHd
    LineM kBx + HOOD_L, zTopHd, kBx + HOOD_L, zHood0
    ' cooler: its roof only past the hood
    PolyM Array(kBx + HOOD_L, zCool0 + COOLER_H, kBx + coolL, zCool0 + COOLER_H, kBx + coolL, zCool0, _
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
        ' the twin C1 either side of R1; their inlets come in from the
        ' front (in depth), so the barrel walls run whole
        Cyclone 1, xo - sd * (dR1 + dC1), sd, 0#
        Cyclone 1, xo - sd * (dR1 - dC1), -sd, 0#
        For s = 5 To 2 Step -1
            CycBody s, col(s)
        Next s
        CycBody 1, xo - sd * (dR1 + dC1)
        CycBody 1, xo - sd * (dR1 - dC1)
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
    zx = Max2(kAz + kOff, zToe + xToe * rampTan + 1#)
    PathL "gas: kiln (burner end -> inlet)", Array(kBx, kBz + kOff, kAx, kAz + kOff, 0#, zx)
    PathL "gas: inlet chamber -> calciner", Array(0#, zx, 0#, zCalcRoof - 2#)
    ' The tertiary air rises straight out of the cooler through the hood,
    ' marked as the secondary air is, into its duct on the hood's top;
    ' hot, so on the gas layer as the secondary air.
    zc = zCool0 + 0.5 * COOLER_H + TA_ARROW_LONG * (zHood0 + HOOD_H - zCool0 - 0.5 * COOLER_H)
    If zc >= zTA - TA_BEND_R_OVER_D * TA_D Then Fail "the tertiary air arrow runs up into its duct's bend. Lower TA_ARROW_LONG."
    PathOut "gas: cooler -> hood (tertiary air)", Array(kBx + HOOD_TA_X, zCool0 + 0.5 * COOLER_H, kBx + HOOD_TA_X, zc)
    ' up out of the hood, a long-radius bend (its walls arcs), over to the calciner
    zx = TA_BEND_R_OVER_D * TA_D
    If zHood0 + HOOD_H >= zTA - zx Then Fail "the tertiary air duct's bend does not fit over the hood."
    Duct "gas: hood -> tertiary air duct", Array(kBx + HOOD_TA_X, zHood0 + HOOD_H, kBx + HOOD_TA_X, zTA - zx), TA_D, False, True
    ArcM kBx + HOOD_TA_X - zx, zTA - zx, zx + rTA, 0#, 0.5 * PI
    ArcM kBx + HOOD_TA_X - zx, zTA - zx, zx - rTA, 0#, 0.5 * PI
    Duct "gas: tertiary air duct -> calciner", Array(kBx + HOOD_TA_X - zx, zTA, rCalc, zTA), TA_D, False
    BodyM Array(rCalc, zTA - rTA, kBx + HOOD_TA_X + rTA, zTA - rTA, kBx + HOOD_TA_X + rTA, zTA + rTA, rCalc, zTA + rTA)

    For k = 0 To 1
        sd = 1# - 2# * k
        If sd > 0# Then side = "R" Else side = "L"
        xi = sd * xInner: xo = xi + sd * ZIG_DX: xm = 0.5 * (xi + xo)
        col(5) = xi: col(4) = xo: col(3) = xi: col(2) = xo

        '--- the gooseneck, as calciner.bas (x-z view): the neck's band up to
        '    its crown and the channel's down to the Y (once; the neck
        '    bends toward the viewer, the channel hangs in front of the
        '    vessel), then each arm: down to the C5 inlet axis, level in --
        If k = 0 Then
            Duct "gas: calciner -> gooseneck neck", Array(0#, zCalcRoof, 0#, zGnTop), 2# * rNeck, False
            LineM -rNeck, zGnTop, rNeck, zGnTop
            Duct "gas: gooseneck neck -> channel", Array(0#, zCalcRoof, 0#, zWall), 2# * rNeck, False
        End If
        YArm sd, side

        '--- R4, R3, R2: C5 / C4 / C3's outlet pipe itself, straight up
        '    beside the next cyclone, turning in at its top (17 Nov 2026);
        '    each closed too, for the meal passing behind it -------------
        For s = 5 To 3 Step -1
            up = s - 1
            RiserUp s, col(s), Sgn(col(up) - col(s)), side
            RiserBody s, col(s), Sgn(col(up) - col(s))
        Next s

        '--- R1: straight up out of C2's outlet pipe on C2's axis, its
        '    same bore, a Y into the twin C1's branches; each
        '    C1 with its branch, inlet and outlet bend as its CFD domain,
        '    the two mirror images of each other --------------------------
        R1Straight xo, side
        R1Body xo
        R1Y xo - sd * dR1
        C1Unit side & " far", xo - sd * (dR1 + dC1), -sd
        C1Unit side & " near", xo - sd * (dR1 - dC1), sd

        '--- meal ---------------------------------------------------------
        phase = "drawing the meal path, string " & side
        UseLayer L_MEAL
        ' Each cyclone feeds the riser leaving the stage two below -- the
        ' outlet pipe, on the side away from its turn, low on it, where a
        ' plant feeds its meal: both C1 into R2, C2 into R3, C3 into R4
        ' (C2 / C3 hang right over that riser's top, so their pipes pass
        ' behind it, broken, and come forward low on it; 17 Nov 2026); C4 the calciner through its wall, C5 the kiln inlet
        ' chamber through its roof. Each is drawn whole where there is
        ' room, broken where it passes behind a cyclone or the tertiary
        ' air duct (PathM). The near C1's joins the far one's beside R2,
        ' behind C2's outlet pipe, R1 and R2's bend: the twin stand over
        ' C2 since R1 rises on its axis, 6.7 m behind the C2 / R2 plane,
        ' and their pipes come forward to R2 only at its upright
        ' (user decision, 17 Nov 2026; before, they had to clear R2's
        ' bend in the plane, which would put the C1s 6 m higher).
        ' Each falls straight out of its dust outlet first.
        MealInto "C1", side, xo - sd * (dR1 + dC1), zDust(1), MEAL_DROP, MEAL_SLOPE_DEG, col(3), 2, _
                 Sgn(col(3) - col(2)), xe, zc, True
        xn = xo - sd * (dR1 - dC1)
        zx = zDust(1) - MEAL_DROP - Abs(xe - xn) * Tan(MEAL_JOIN_DEG * PI / 180#)
        If zx <= zc + 0.5 Or zx >= zDust(1) - MEAL_DROP - Abs(xe - (xo - sd * (dR1 + dC1))) * Tan(MEAL_SLOPE_DEG * PI / 180#) - 0.5 Then
            Fail "the near C1's meal does not join the far one's on its run beside R2."
        End If
        PathM "meal: C1 " & side & " near -> the far C1's pipe", Array(xn, zDust(1), xn, zDust(1) - MEAL_DROP, xe, zx)
        MealInto "C2", side, col(2), zDust(2), MEAL_DROP, MEAL_SLOPE_DEG, col(4), 3, Sgn(col(4) - col(3)), xe, zc
        MealInto "C3", side, col(3), zDust(3), MEAL_DROP, MEAL_SLOPE_DEG, col(5), 4, Sgn(col(5) - col(4)), xe, zc
        BendEnd col(4), zDust(4) - C4_MEAL_DROP, sd * rCalc, zFeed, xe, zc
        PathM "meal: C4 " & side & " -> calciner", Array(col(4), zDust(4), col(4), zDust(4) - C4_MEAL_DROP, _
              xe, zc, sd * rCalc, zFeed)
        ' into the middle of the throat's cylinder, a few metres over the chamber's roof
        BendEnd xi, zDust(5) - C5_MEAL_DROP, sd * rThroat, zThroat + 0.5 * CALC_THROAT_D, xe, zc
        PathM "meal: C5 " & side & " -> calciner throat", Array(xi, zDust(5), xi, zDust(5) - C5_MEAL_DROP, _
              xe, zc, sd * rThroat, zThroat + 0.5 * CALC_THROAT_D), C5_ARROW_FROM_END
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
    PathOut "air: primary air -> main burner", Array(kBx + HOOD_L + PRIMARY_AIR_L, kBz + kOff, _
            kBx + HOOD_L, kBz + kOff)
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
    LabelM -0.3 * TEXT_H * 3 * SHEET_SCALE, zGnTop + 3#, "ILC", 0#   ' centred on the calciner axis, as CycLabel
    LabelM -xBend - 0.5, zLeg + rGn + 2#, "GN", 0#
    LabelM xBend - 0.5, zLeg + rGn + 2#, "GN", 0#
    LabelM 20#, kAz + 3.5, "KILN rotary kiln D" & Num(KILN_D, 3) & " x " & Num(KILN_L, 0) & " m", 0#
    LabelM kBx + 0.3 * coolL, zCool0 + 0.75 * COOLER_H, "COOL grate cooler", 0#
    LabelM kBx + coolL - VENT_IN - 0.3 * TEXT_H * 14 * SHEET_SCALE, zCool0 + COOLER_H + VENT_UP + 1.1, _
           "to cooler vent", 0#
    LabelM kBx + coolL - 1.5 - 0.6 * TEXT_H * 20 * SHEET_SCALE, -CLINKER_OUT_Z + 2#, "to clinker transport", 0#
    LabelM kBx + HOOD_L + 1#, zHood0 + HOOD_H, "HOOD kiln hood", 0#
    LabelM kBx + HOOD_L + 1#, kBz + kOff - 0.6, "primary air", 0#
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
        CycLabel "C1 " & side, 1, xo - sd * (dR1 + dC1), -sd
        CycLabel "C1 " & side, 1, xo - sd * (dR1 - dC1), sd
        For s = 5 To 3 Step -1
            LabelM col(s), 0.5 * (RiserV0(s - 1) + RiserBendZ(s - 1)) - 1.5, "R" & (s - 1), -0.002
        Next s
        ' R1 between its branches, under their meal chutes
        LabelM xo - sd * dR1, zDust(1) + 0.5 * (C1_RISER_Z0 + C1_FEED_Z) - 0.5, "R1", -0.002
        ' beside each C1 outlet's bend, which turns away from the viewer,
        ' on its side away from R1
        LabelM xo - sd * (dR1 + dC1 + 0.5 * C1_VD + 0.6) - IIf(sd > 0#, 0.6 * TEXT_H * 18 * SHEET_SCALE, 0#), _
               zTop(1) + C1_OUT_R + 0.6, "to ID fan (behind)", 0#
        LabelM xo - sd * (dR1 - dC1 - 0.5 * C1_VD - 0.6) - IIf(sd < 0#, 0.6 * TEXT_H * 18 * SHEET_SCALE, 0#), _
               zTop(1) + C1_OUT_R + 0.6, "to ID fan (behind)", 0#
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
    If s = 1 Then
        C1Outline xc, inSide
        Exit Sub
    End If
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


' A twin C1's section about its axis at xc, R1 on its side inSide. Its
' outline, each side: the cone, the barrel up to the volute's floor, the
' volute out to C1_VOL_OUT on the branch's side (its duct, seen end on)
' or to C1_VOL_FAR on the other (the scroll's end), up to the roof, the
' roof in to the outlet stub, the stub up. The branch rises in front of
' it (the twin is turned, user decision 13 Nov 2026), C1_DUCT_Y +- the
' branch radius from the axis, from the CFD domain's floor to its bend's
' crown: what of the outline lies behind that band is hidden (ISO 128
' 02.1), clipped segment by segment (ClipLineM).
Private Sub C1Outline(ByVal xc As Double, ByVal inSide As Double)
    Dim rb As Double, b0 As Double, b1 As Double, z0 As Double, z1 As Double
    Dim sg As Double, k As Long, i As Long, xo As Double, zv As Double
    Dim xr As Double, xs As Double, zr As Double, zt As Double, zcone As Double
    Dim u As Variant, w As Variant
    rb = kBranch * 0.5 * RiserD(1)
    b0 = C1_DUCT_Y - rb: b1 = C1_DUCT_Y + rb              ' the branch's band, from the axis
    z0 = zDust(1) + C1_RISER_Z0                           ' its floor ...
    z1 = zDust(1) + C1_BEND_Z + C1_BEND_R + rb            ' ... to its crown's top
    zcone = zDust(1) + C1_HC: zr = zRoof(1): zt = zTop(1)
    zv = zr - C1_DUCT_H                                   ' the volute's floor
    xr = 0.5 * C1_D: xs = 0.5 * C1_VD
    If zv <= zcone Then Fail "the C1 volute reaches below the barrel; C1Outline draws it on the barrel."
    If b0 >= C1_VOL_OUT Or b1 <= xr Then Fail "the C1 branch does not stand in front of the C1's volute."
    For k = 0 To 1
        sg = 1# - 2# * k
        If sg = inSide Then xo = C1_VOL_OUT Else xo = C1_VOL_FAR
        u = Array(0.5 * C1_DD, xr, xr, xo, xo, xs, xs)    ' from the axis
        w = Array(zDust(1), zcone, zv, zv, zr, zr, zt)
        For i = 0 To 5
            If sg = inSide Then
                ClipLineM xc + sg * u(i), w(i), xc + sg * u(i + 1), w(i + 1), _
                          xc + sg * b0, xc + sg * b1, z0, z1
            Else
                LineM xc + sg * u(i), w(i), xc + sg * u(i + 1), w(i + 1)
            End If
        Next i
    Next k
End Sub


' A line, the part of it inside the box (x between xa0 and xa1 in either
' order, z between zb0 and zb1) on the hidden layer: Liang-Barsky.
' Leaves the layer as L_EQUIP.
Private Sub ClipLineM(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double, _
                      ByVal xa0 As Double, ByVal xa1 As Double, ByVal zb0 As Double, ByVal zb1 As Double)
    Dim x0 As Double, x1 As Double, dx As Double, dz As Double, t0 As Double, t1 As Double
    Dim p(3) As Double, q(3) As Double, r As Double, j As Long, ln As Double
    x0 = Min2(xa0, xa1): x1 = Max2(xa0, xa1)
    dx = xb - xa: dz = zb - za
    ln = Sqr(dx * dx + dz * dz)
    p(0) = -dx: q(0) = xa - x0
    p(1) = dx: q(1) = x1 - xa
    p(2) = -dz: q(2) = za - zb0
    p(3) = dz: q(3) = zb1 - za
    t0 = 0#: t1 = 1#
    For j = 0 To 3
        If Abs(p(j)) < 0.000000001 Then
            If q(j) < 0# Then t0 = 1#: t1 = 0#           ' parallel and outside
        Else
            r = q(j) / p(j)
            If p(j) < 0# Then
                If r > t0 Then t0 = r
            Else
                If r < t1 Then t1 = r
            End If
        End If
    Next j
    UseLayer L_EQUIP
    If t1 - t0 <= 0.000001 / ln Then
        LineM xa, za, xb, zb
        Exit Sub
    End If
    If t0 * ln > 0.000001 Then LineM xa, za, xa + t0 * dx, za + t0 * dz
    UseLayer L_HID
    LineM xa + t0 * dx, za + t0 * dz, xa + t1 * dx, za + t1 * dz
    UseLayer L_EQUIP
    If (1# - t1) * ln > 0.000001 Then LineM xa + t1 * dx, za + t1 * dz, xb, zb
End Sub


' R1 straight up out of C2's outlet pipe (drawn with C2 up to zTop)
' on C2's axis xo: the same bore (21 Nov 2026, no reducer), R1's
' walls up to its Y.
Private Sub R1Straight(ByVal xo As Double, ByVal side As String)
    Dim r As Double, zf As Double
    Dim g As Double
    Dim k As Long
    r = 0.5 * RiserD(1): zf = RiserV0(1)
    For k = 0 To 1
        g = 1# - 2# * k
        DuctEdge xo + g * r, zf, xo + g * r, R1SplitZ()
    Next k
    ArrowAt xo, 0.5 * (zf + R1SplitZ()), 0#, 1#
    Note "-- gas: C2 " & side & " outlet -> R1 straight up (D " & Fmt(RiserD(1)) & _
         ", R1 " & Fmt(R1SplitZ() - zf) & " m to its Y)"
End Sub


' R1 up to its Y on C2's axis xo, closed, for the crossing check: the
' C1 meal passes behind it.
Private Sub R1Body(ByVal xo As Double)
    Dim r As Double, zf As Double
    r = 0.5 * RiserD(1): zf = RiserV0(1)
    BodyM Array(xo + r, zf, xo + r, R1SplitZ(), xo - r, R1SplitZ(), xo - r, zf)
End Sub


' R(s - 1) (s = 3..5; user decisions, 17 and 22 Nov 2026): C(s)'s
' outlet pipe (drawn with C(s) up to zTop) straight on up beside
' C(s - 1), towards dr (+1 / -1), into the inclined duct and the level
' duct (its top flush with the roof) into the barrel, projected on the
' sheet (RiserOutline): they run obliquely in depth.
Private Sub RiserUp(ByVal s As Long, ByVal xc As Double, ByVal dr As Double, ByVal side As String)
    Dim k As Long, i As Long, n As Long
    Dim a As Double, zt As Double, zu As Double, h As Double, xb As Double
    Dim ts() As Double, zs() As Double
    k = s - 1
    a = StubR(s): zt = zTop(s): zu = zRoof(k): h = Kc(k) * C4_IN_H
    xb = xc + dr * (ZIG_DX - CycR(k))
    RiserOutline k, True, n, ts, zs
    DuctEdge xc - dr * a, zt, xc + dr * ts(0), zs(0)
    For i = 0 To n - 2
        DuctEdge xc + dr * ts(i), zs(i), xc + dr * ts(i + 1), zs(i + 1)
    Next i
    DuctEdge xc + dr * ts(n - 1), zs(n - 1), xb, zu
    RiserOutline k, False, n, ts, zs
    DuctEdge xc + dr * a, zt, xc + dr * ts(0), zs(0)
    For i = 0 To n - 2
        DuctEdge xc + dr * ts(i), zs(i), xc + dr * ts(i + 1), zs(i + 1)
    Next i
    DuctEdge xc + dr * ts(n - 1), zs(n - 1), xb, zu - h
    ArrowAt xc, 0.5 * (zt + RiserTopZ(k)), 0#, 1#
    Note "-- gas: R" & k & " " & side & " (D " & Fmt(2# * a) & ") straight up " & Fmt(RiserTopZ(k) - zRoof(s)) & _
         " m from C" & s & "'s roof to the seam's foot, an inclined duct at " & Fmt(RISER_SLOPE_DEG) & " deg into C" & k
End Sub


' RiserUp's outline, closed, from the roof below, for the crossing
' check (a meal pipe behind it is drawn broken).
Private Sub RiserBody(ByVal s As Long, ByVal xc As Double, ByVal dr As Double)
    Dim k As Long, i As Long, n As Long, m As Long
    Dim a As Double, zu As Double, h As Double, xb As Double
    Dim tOu() As Double, zo() As Double, ti() As Double, zi() As Double, no As Long, ni As Long
    Dim pts() As Variant
    k = s - 1
    a = StubR(s): zu = zRoof(k): h = Kc(k) * C4_IN_H
    xb = xc + dr * (ZIG_DX - CycR(k))
    RiserOutline k, True, no, tOu, zo
    RiserOutline k, False, ni, ti, zi
    ReDim pts(0 To 2 * (no + ni + 6) - 1)
    m = 0
    pts(m) = xc - dr * a: pts(m + 1) = zRoof(s): m = m + 2
    For i = 0 To no - 1
        pts(m) = xc + dr * tOu(i): pts(m + 1) = zo(i): m = m + 2
    Next i
    pts(m) = xb: pts(m + 1) = zu: m = m + 2
    pts(m) = xb: pts(m + 1) = zu - h: m = m + 2
    For i = ni - 1 To 0 Step -1
        pts(m) = xc + dr * ti(i): pts(m + 1) = zi(i): m = m + 2
    Next i
    pts(m) = xc + dr * a: pts(m + 1) = zRoof(s): m = m + 2
    ReDim Preserve pts(0 To m - 1)
    BodyM pts
End Sub


' the foot of R(k)'s upright: the roof under the CFD outlet pipe for
' R2..R4, the top of C2's CFD outlet pipe for R1
Private Function RiserV0(ByVal k As Long) As Double
    If k = 1 Then RiserV0 = zTop(2) Else RiserV0 = zRoof(k + 1)
End Function

' the upright's top: where R(k) turns in (R2..R4)
Private Function RiserBendZ(ByVal k As Long) As Double
    RiserBendZ = RiserTopZ(k)
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
' -1, away from R1; the two of a twin mirror each other). The twin is
' turned (user decision, 13 Nov 2026): each C1's branch, bend, inlet
' duct and meal chute, and its outlet bend, lie in depth, so this front
' view sees them end on. The branch rises straight from R1's Y,
' C1_DUCT_Y from the C1 axis towards R1, to its bend's crown, where it
' runs away from the viewer into its duct: its walls up to there, the
' crown a half circle, the flow away a cross in a circle (ISO). The
' meal chute stands towards the viewer at the meal slope: its square
' end on. The outlet pipe rises to its 180 deg bend, which turns away
' too: its crown a half circle; its leg drops behind the barrel.
Private Sub C1Unit(ByVal side As String, ByVal xc As Double, ByVal g As Double)
    Dim rb As Double, xr As Double, z0 As Double, zc As Double, zf As Double, h As Double
    Dim a As Double, zo As Double, q As Double
    z0 = zDust(1)
    rb = kBranch * 0.5 * RiserD(1)
    xr = xc - g * C1_DUCT_Y

    UseLayer L_GAS
    zc = z0 + C1_BEND_Z + C1_BEND_R                  ' the bend's crown: its axis level, running in depth
    Duct "gas: R1 " & side & " branch", Array(xr, z0 + C1_RISER_Z0, xr, zc), 2# * rb, False
    ArcM xr, zc, rb, 0#, PI
    AwayMark xr, zc, 0.35 * rb

    ' the meal chute towards the viewer: its axis meets the branch wall
    ' at C1_FEED_Z and rises C1_FEED_L along it at the meal slope
    UseLayer L_EQUIP
    zf = z0 + C1_FEED_Z
    h = 0.5 * C1_FEED_W
    zo = zf + C1_FEED_L * Sin(MEAL_SLOPE_DEG * PI / 180#)
    q = h * Cos(MEAL_SLOPE_DEG * PI / 180#)          ' the square's half height, end on
    PolyM Array(xr - h, zo - q, xr + h, zo - q, xr + h, zo + q, xr - h, zo + q, xr - h, zo - q)
    UseLayer L_MEAL
    PathOut "meal: raw meal -> R1 " & side & " branch", Array(xr, zo + q + RM_L, xr, zo + q), 0.5 * ARROW_L
    UseLayer L_TEXT
    LabelMH xr + g * (rb + 0.3), zo + q + RM_L + 0.4, "FEED", IIf(g > 0#, 0#, -0.0068), CAP_H

    ' the outlet's 180 deg bend, in depth: the pipe's walls up to its
    ' crown, a half circle there, the flow away from the viewer
    UseLayer L_GAS
    a = 0.5 * C1_VD
    LineM xc - a, zTop(1), xc - a, zTop(1) + C1_OUT_R
    LineM xc + a, zTop(1), xc + a, zTop(1) + C1_OUT_R
    ArcM xc, zTop(1) + C1_OUT_R, a, 0#, PI
    AwayMark xc, zTop(1) + C1_OUT_R, 0.35 * a
    Note "-- gas: C1 " & side & " outlet bend (in depth) -> leg behind -> ID fan"
End Sub


' A flow away from the viewer (ISO): a cross in a circle at (x, z).
Private Sub AwayMark(ByVal x As Double, ByVal z As Double, ByVal r As Double)
    Dim c As Double
    c = r / Sqr(2#)
    CircleM x, z, r
    LineM x - c, z - c, x + c, z + c
    LineM x - c, z + c, x + c, z - c
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


' A meal pipe from a dust outlet at (xs, zs) into R(k) (k = 2..4, the
' outlet pipe at xr), drawn whole: drop straight down, then at deg out
' to MEAL_SIDE_L beside the wall on side sg (away from the riser's
' turn), down beside it and into it at the meal slope MEAL_ENTRY_UP
' over the roof; broken where it passes behind a riser or a cyclone.
' Returns the foot of its run beside the wall.
Private Sub MealInto(ByVal src As String, ByVal side As String, ByVal xs As Double, ByVal zs As Double, _
                     ByVal drop As Double, ByVal deg As Double, ByVal xr As Double, ByVal k As Long, _
                     ByVal sg As Double, ByRef xpOut As Double, ByRef z3Out As Double, _
                     Optional ByVal behind As Boolean = False)
    Dim xw As Double, xp As Double, z1 As Double, z2 As Double, z3 As Double, ze As Double, tn As Double
    Dim what As String
    what = "meal: " & src & " " & side & " -> R" & k
    tn = Tan(MEAL_SLOPE_DEG * PI / 180#)
    xw = xr + sg * 0.5 * RiserD(k): xp = xw + sg * MEAL_SIDE_L
    z1 = zs - drop
    z2 = z1 - Abs(xp - xs) * Tan(deg * PI / 180#)
    ze = RiserV0(k) + MEAL_ENTRY_UP: z3 = ze + MEAL_SIDE_L * tn
    If ze + MEAL_SIDE_L * tn >= RiserBendZ(k) - 0.5 Then Fail what & ": it would enter R" & k & " past its pipe."
    If z2 <= z3 + 0.001 Then Fail what & ": the dust outlet is too low to reach R" & k & " at its slope."
    ' (no bend to clear since 17 Nov 2026: where the slope passes a
    ' riser it passes behind it, drawn broken; `behind` is kept for
    ' the callers' record)
    If drop > 0# Then
        PathM what, Array(xs, zs, xs, z1, xp, z2, xp, z3, xw, ze)
    Else
        PathM what, Array(xs, zs, xp, z2, xp, z3, xw, ze)
    End If
    xpOut = xp: z3Out = z3
End Sub

' How far the segment (xa, za)-(xb, zb) stays outside the circle about
' (cx, cz) of radius ro
Private Function SegClear(ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double, _
                          ByVal cx As Double, ByVal cz As Double, ByVal ro As Double) As Double
    Dim dx As Double, dz As Double, t As Double
    dx = xb - xa: dz = zb - za
    t = Max2(0#, Min2(1#, ((cx - xa) * dx + (cz - za) * dz) / (dx * dx + dz * dz)))
    SegClear = Sqr((xa + t * dx - cx) ^ 2 + (za + t * dz - cz) ^ 2) - ro
End Function

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

' A cyclone's name centred in its barrel, the one place no path
' crosses; under its vortex finder where that is drawn.
Private Sub CycLabel(ByVal txt As String, ByVal s As Long, ByVal xc As Double, Optional ByVal outSide As Double = 0#)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    If s = 1 And outSide <> 0# Then
        ' beside the barrel on the side away from R1: its branch and
        ' meal chute stand in front of the R1 side
        LabelM xc + outSide * (0.5 * d + 0.5) - IIf(outSide < 0#, 0.6 * TEXT_H * Len(txt) * SHEET_SCALE, 0#), _
               zRoof(s) - 0.5 * hb, txt, 0#
    ElseIf s = 1 Then
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
' A closed outline a meal pipe may pass behind: its edges kept for
' PathM, not drawn.
Private Sub BodyM(pts As Variant)
    Dim n As Long, i As Long, j As Long
    n = (UBound(pts) + 1) \ 2
    For i = 0 To n - 1
        j = (i + 1) Mod n
        If nBd >= UBound(bdXa) Then Fail "too many outlines for the meal crossing check."
        nBd = nBd + 1
        bdXa(nBd) = pts(2 * i): bdZa(nBd) = pts(2 * i + 1)
        bdXb(nBd) = pts(2 * j): bdZb(nBd) = pts(2 * j + 1)
    Next i
End Sub

' A cyclone's section, closed, for the crossing check: cone, barrel,
' roof, its outlet pipe to its top
Private Sub CycBody(ByVal s As Long, ByVal xc As Double)
    Dim d As Double, hb As Double, hc As Double, vd As Double, dd As Double
    CycDims s, d, hb, hc, vd, dd
    BodyM Array(xc + 0.5 * dd, zDust(s), xc + 0.5 * d, zDust(s) + hc, xc + 0.5 * d, zRoof(s), _
                xc + 0.5 * vd, zRoof(s), xc + 0.5 * vd, zTop(s), xc - 0.5 * vd, zTop(s), _
                xc - 0.5 * vd, zRoof(s), xc - 0.5 * d, zRoof(s), xc - 0.5 * d, zDust(s) + hc, _
                xc - 0.5 * dd, zDust(s))
End Sub

' A meal pipe along its axis, broken where it passes behind an outline
' (BodyM): along the pipe every edge it crosses toggles it in / out;
' the parts inside, and CROSS_GAP either side, are not drawn. Edges it
' only starts or ends on (its dust outlet, the wall it enters) do not
' count. The arrow rides on the longest part drawn.
Private Sub PathM(ByVal what As String, pts As Variant, Optional ByVal arrowFromEnd As Double = -1#)
    Dim n As Long, i As Long, j As Long, m As Long, q As Long, nb As Long
    Dim xa As Double, za As Double, dx As Double, dz As Double, L As Double
    Dim ex As Double, ez As Double, den As Double, t As Double, u As Double, tg As Double
    Dim t0 As Double, t1 As Double, bl As Double, bx As Double, bz As Double, bdx As Double, bdz As Double
    Dim ts() As Double
    Dim inBody As Boolean
    n = (UBound(pts) + 1) \ 2
    If n < 2 Then Fail what & " has fewer than two points."
    bl = -1#
    For i = 0 To n - 2
        xa = pts(2 * i): za = pts(2 * i + 1)
        dx = pts(2 * i + 2) - xa: dz = pts(2 * i + 3) - za
        L = Sqr(dx * dx + dz * dz)
        If L <= 0# Then Fail what & ": two points coincide."
        ReDim ts(0 To nBd)
        m = 0
        For j = 1 To nBd
            ex = bdXb(j) - bdXa(j): ez = bdZb(j) - bdZa(j)
            den = dx * ez - dz * ex
            If Abs(den) > 1E-12 Then
                t = ((bdXa(j) - xa) * ez - (bdZa(j) - za) * ex) / den
                u = ((bdXa(j) - xa) * dz - (bdZa(j) - za) * dx) / den
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
        nb = nb + m
        tg = CROSS_GAP / L
        ' each crossing toggles in / out; the state carries on to the
        ' next run. Draw the outside parts.
        t0 = 0#
        For j = 0 To m
            If j < m Then t1 = ts(j) - tg Else t1 = 1#
            If Not inBody And t1 > t0 + 0.000001 Then
                LineM xa + t0 * dx, za + t0 * dz, xa + t1 * dx, za + t1 * dz
                If (t1 - t0) * L > bl Then
                    bl = (t1 - t0) * L
                    bx = xa + 0.5 * (t0 + t1) * dx: bz = za + 0.5 * (t0 + t1) * dz
                    bdx = dx / L: bdz = dz / L
                End If
            End If
            If j < m Then
                inBody = Not inBody
                If Not inBody Then t0 = ts(j) + tg
            End If
        Next j
    Next i
    If inBody Then Fail what & " ends behind an outline."
    If arrowFromEnd >= 0# Then
        ' the arrow a fixed distance back from the end on the last run, not on the longest drawn part
        dx = pts(2 * n - 2) - pts(2 * n - 4): dz = pts(2 * n - 1) - pts(2 * n - 3)
        L = Sqr(dx * dx + dz * dz)
        If arrowFromEnd > L Then Fail what & ": the arrow's distance from the end is longer than its last run."
        bdx = dx / L: bdz = dz / L
        bx = pts(2 * n - 2) - arrowFromEnd * bdx: bz = pts(2 * n - 1) - arrowFromEnd * bdz
        bl = 1#
    End If
    If bl > 0# Then ArrowAt bx, bz, bdx, bdz
    Note "-- " & what & IIf(nb > 0, " (broken behind " & nb \ 2 & " outlines)", "")
End Sub


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


' One arm of the Y on side sd, at its true width (rGn either side of its
' axis, which runs from the channel's lower end at armAng to the
' vertical, down to the level run's axis, then level into the C5): the
' upper edge leaves the channel's wall, the lower edge starts at the
' Y's crotch on the axis where the two arms' lower edges cross; the
' corner is a mitre. The channel's own lines stop at zWall.
Private Sub YArm(ByVal sd As Double, ByVal side As String)
    Dim h As Double, sg As Double, cg As Double, f As Double
    Dim zCrotch As Double, xe As Double
    Dim xu As Double, xl As Double
    h = rGn: sg = Sin(armAng): cg = Cos(armAng)
    f = 1# / (1# + sg)                     ' the mitre's factor, normals' dot product sg
    zCrotch = zSplit - h * sg - (h * cg / sg) * cg
    xe = sd * (xInner - CycR(5))
    xu = sd * (xBend + h * cg * f)         ' the upper edge's corner
    xl = sd * (xBend - h * cg * f)         ' the lower edge's corner
    DuctEdge sd * rNeck, zWall, xu, zLeg + h
    DuctEdge xu, zLeg + h, xe, zLeg + h
    DuctEdge 0#, zCrotch, xl, zLeg - h
    DuctEdge xl, zLeg - h, xe, zLeg - h
    ArrowOnLongest Array(0#, zSplit, sd * xBend, zLeg, xe, zIn(5))
    Note "-- gas: gooseneck arm " & side & " -> C5 inlet (D " & Fmt(2# * rGn) & ")"
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
    UseLayer L_GAS:  LineP x + 0.008, y - 0.003, x + 0.008, y + 0.003: LineP x + 0.012, y - 0.003, x + 0.012, y + 0.003
    UseLayer L_MEAL: LineP x, y, x + 0.005, y: LineP x + 0.015, y, x + 0.02, y
    UseLayer L_TEXT: LabelP x + 0.025, y + 0.002, "meal pipe broken where it passes behind a duct"

    y = y - 0.02
    LabelP x, y, "NOTES"
    LabelP x, y - 0.006, "1. Elevations above ground, m; diameters internal, m."
    LabelP x, y - 0.012, "2. 5000 t/d: two identical 2500 t/d strings on one calciner and"
    LabelP x, y - 0.018, "   kiln; cyclones at the CFD sizes; see the equipment list."
    LabelP x, y - 0.024, "3. Schematic: kiln inlet chamber size has no source; C4 / C5 meal"
    LabelP x, y - 0.030, "   pipes are steeper in 3D than drawn here."
    LabelP x, y - 0.036, "4. Not a CFD input; one string is solved, the other is its copy."
    LabelP x, y - 0.042, "5. Gooseneck: the neck bends toward the viewer; neck, channel and arms"
    LabelP x, y - 0.048, "   lie in front of the calciner, y = -" & Num(gnYoff, 2) & " m (arms in that plane)."

    ' 10 m scale bar
    y = y - 0.063
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

    tg = Array("Tag", "C1", "C2-C4", "C5", "R1", "R2", "R3", "R4", "ILC", "GN", "TAD", "KIC", "KILN", "HOOD", "COOL", "FEED")
    eq = Array("Equipment", "twin top cyclone", "cyclone", "cyclone", "riser", "riser", "riser", "riser", _
               "ILC calciner", "gooseneck + Y", "tertiary air duct", "kiln inlet chamber", "rotary kiln", _
               "kiln hood", "grate cooler", "raw meal inlet")
    qt = Array("Qty", "4", "6", "2", "2", "2", "2", "2", "1", "1", "1", "1", "1", "1", "1", "2")
    sz = Array("Size [m]", "D" & Num(2# * CycR(1), 3), "D" & Num(2# * CycR(4), 3) & ", barrel h = D", _
               "D" & Num(2# * CycR(5), 3), "D" & Num(RiserD(1), 3), "D" & Num(RiserD(2), 3), _
               "D" & Num(RiserD(3), 3), "D" & Num(RiserD(4), 3), _
               "D" & Num(CALC_D, 3) & ", H " & Num(CALC_H, 2), "neck D" & Num(2# * rNeck, 2) & ", arms D" & Num(2# * rGn, 2), "D" & Num(TA_D, 3), _
               Num(aCh + rThroat, 1) & " wide, ramp " & Num(KIC_RAMP_DEG, 0) & " deg", _
               "D" & Num(KILN_D, 1) & " x " & Num(KILN_L, 0) & ", " & Num(100# * KILN_SLOPE, 0) & " %", _
               Num(2# * aCh, 1) & " x " & Num(2# * aCh, 1), _
               Num(COOLER_AREA, 0) & " m2, " & Num(COOLER_W, 1) & " x " & Num(coolL, 1), "-")
    bs = Array("Basis", "CFD C1", "CFD C4", _
               "CFD C4 x 6.50/6.30", "C2 outlet, D/2", "CFD C4 outlet", _
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


' Centre lines (ISO 128 chain lines): each cyclone's axis over its body
' only, AXIS_UNDER past the dust outlet and AXIS_OVER past the roof (user, 21 Nov 2026:
' run on through the outlet pipe and the riser they made the risers
' hard to read), the kiln's axis, and the calciner's over its roof
' (below it the kiln gas line runs on the axis).
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
            LineM col(s), zDust(s) - AXIS_UNDER, col(s), zRoof(s) + AXIS_OVER
        Next s
        LineM xo - sd * (dR1 + dC1), zDust(1) - AXIS_UNDER, xo - sd * (dR1 + dC1), zRoof(1) + AXIS_OVER
        LineM xo - sd * (dR1 - dC1), zDust(1) - AXIS_UNDER, xo - sd * (dR1 - dC1), zRoof(1) + AXIS_OVER
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
