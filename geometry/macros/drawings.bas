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
Const C1_L_VORTEX                  As Double  = 3.45         ' vortex finder immersion [cfd_decision, preheater/cyclone_C1.md]
Const C1_D_VORTEX                  As Double  = 2.4          ' vortex finder / outlet pipe bore [derived_from_reference, preheater/cyclone_C1.md]
Const C1_D_DUST                    As Double  = 0.4          ' dust outlet D [derived_from_reference, preheater/cyclone_C1.md]
Const C1_W_INLET                   As Double  = 0.86         ' inlet width [derived_from_reference, preheater/cyclone_C1.md]
Const C1_H_INLET                   As Double  = 3#           ' inlet height, normal to the duct [cfd_decision, preheater/cyclone_C1.md]
Const C1_INLET_SLOPE_DEG           As Double  = 0#           ' inlet duct slope [cfd_decision, preheater/cyclone_C1.md]
Const C1_VORTEX_WALL               As Double  = 0.08         ' vortex finder wall [model, preheater/cyclone_C1.md]
Const C1_HEIGHT                    As Double  = 11.44        ' barrel + cone [derived]
Const C1_OUT_RISE                  As Double  = 3#           ' outlet pipe rise over the roof [derived]
Const C1_OUT_R                     As Double  = 3.6          ' outlet bend centreline R [derived]
Const C1_OUT_RUN                   As Double  = 3#           ' outlet drop leg [derived]
Const C1_LEG_X                     As Double  = 7.2          ' barrel axis to drop leg axis [derived]
Const C1_TOP                       As Double  = 19.24        ' dust outlet to the top of the bend [derived]
Const C1_Y_INNER                   As Double  = 2.21         ' inlet duct inner wall, y [derived]
Const C1_Y_OUTER                   As Double  = 3.07         ' inlet duct outer wall, y [derived]
Const C1_FACE_TOP_X                As Double  = -3#          ' inlet face, upper edge x [derived]
Const C1_FACE_TOP_Z                As Double  = 11.44        ' inlet face, upper edge z [derived]
Const C1_FACE_BOT_X                As Double  = -3#          ' inlet face, lower edge x [derived]
Const C1_FACE_BOT_Z                As Double  = 8.44         ' inlet face, lower edge z [derived]
Const C1_REACH                     As Double  = 0#           ' inlet opening's upstream end on the barrel, -x (0: a volute) [derived]
Const C1_TAB_1                     As String  = "per_string~Number per string~2~-~published~Verified;D_barrel~Barrel inner diameter D~4320~mm~published~Verified;H_barrel~Barrel height~6790~mm~FLS ratio~Estimated;H_cone~Cone height~4650~mm~FLS ratio~Estimated;height~Barrel + cone height~11440~mm~derived~Estimated;L_vortex~Vortex finder immersion S~3450~mm~CFD decision~Estimated;D_vortex~Vortex finder / outlet pipe bore Dx~2400~mm~FLS ratio~Estimated;vortex_wall~Vortex finder wall~80~mm~model parameter~Estimated;D_dust~Dust outlet diameter~400~mm~FLS ratio~Estimated;W_inlet~Inlet width b (volute duct)~860~mm~FLS ratio~Estimated;H_inlet~Inlet height a (volute duct)~3000~mm~CFD decision~Estimated;" ' parameter table rows
Const C1_TAB_2                     As String  = "inlet_slope~Inlet duct slope~0~deg~CFD decision~Estimated;inlet_duct_length~Volute duct length (from tangent plane)~3000~mm~model parameter~Estimated;tongue~Tongue (cut-water)~50~mm~model parameter~Estimated;overlap~Scroll's inner arc inside the barrel~100~mm~model parameter~Estimated;volute~Volute~yes~-~CFD decision~Estimated;outlet_turn~Outlet bend angle~180~deg~CFD decision~Estimated;outlet_rise~Outlet pipe rise over the roof~3000~mm~derived~Estimated;outlet_bend_R~Outlet bend centreline radius~3600~mm~derived~Estimated;outlet_run~Outlet drop leg~3000~mm~derived~Estimated;leg_x~Barrel axis to drop leg axis~7200~mm~derived~Estimated;" ' parameter table rows
Const C1_TAB_3                     As String  = "top~Dust outlet to top of the bend~19240~mm~derived~Estimated;volume~Volume (barrel + cone)~124.54~m3~derived~Estimated;wet_area~Wetted area (barrel, roof ring, cone)~139.70~m2~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;u_split~C1 Y split (riser to 2 cyclones)~-~~no source~Unknown;" ' parameter table rows
Const C1_TAB_4                     As String  = ""           ' parameter table rows
Const C1_TAB_5                     As String  = ""           ' parameter table rows
Const C1_TAB_6                     As String  = ""           ' parameter table rows
Const C1_TAB_7                     As String  = ""           ' parameter table rows
Const C1_TAB_8                     As String  = ""           ' parameter table rows
Const TW_R1_D                      As Double  = 3.07         ' R1 bore [published, preheater/riser_R1.md]
Const TW_GAP                       As Double  = 1#           ' the branches' walls apart [model, preheater/riser_R1.md]
Const TW_S                         As Double  = 8.450818     ' C1 axis to axis [derived]
Const TW_BRANCH_HALF               As Double  = 1.585409     ' each branch from R1's axis, x [derived]
Const TW_BRANCH_D                  As Double  = 2.170818     ' branch bore [derived]
Const TW_Y_BRANCH                  As Double  = -6.670818    ' branches and R1 in front of the C1 axes, y [derived]
Const TW_Z_BRANCH                  As Double  = 0.269182     ' the branches' floor [derived]
Const TW_Z_SPLIT                   As Double  = -1.765818    ' R1's top: the Y starts [derived]
Const TW_R1_STUB_L                 As Double  = 0.5          ' R1 straight under its Y [derived]
Const TW_Z_CUT                     As Double  = 6.777195     ' section A-A: clear of the feed chutes and the bends [derived]
Const TW_C1_R                      As Double  = 2.16         ' barrel radius [derived]
Const TW_C1_FAR                    As Double  = 2.226723     ' each C1's outer side from its axis: the barrel, or the volute's scroll end [derived]
Const TW_Y_MIN                     As Double  = -8.516034    ' the feed chutes' far side, y (the C1_riser solid's -x) [derived]
Const TW_Y_MAX                     As Double  = 8.4          ' the outlet legs' far side, y [derived]
Const TW_TOP                       As Double  = 19.24        ' the outlet bends' crown [derived]
Const C1_twin_TAB_1                As String  = "R1_D~R1 bore~3070~mm~published~Verified;branch_D~Branch bore (half R1's area)~2171~mm~derived~Estimated;twin_gap~Branches' walls apart~1000~mm~model parameter~Estimated;spacing~C1 axis to axis~8451~mm~derived~Estimated;barrel_gap~Barrel wall to wall~4131~mm~derived~Estimated;branch_pitch~Branch axis to axis (Y)~3171~mm~derived~Estimated;y_branch~R1 / branches in front of the C1 axes~6671~mm~derived~Estimated;y_rise~Y height (R1 top to the branches' floor)~2035~mm~derived~Estimated;r1_stub~R1 straight under its Y~500~mm~derived~Schematic;D_barrel~Barrel inner diameter D~4320~mm~published~Verified;height~Barrel + cone height~11440~mm~derived~Estimated;" ' parameter table rows
Const C1_twin_TAB_2                As String  = "D_vortex~Vortex finder / outlet pipe bore Dx~2400~mm~FLS ratio~Estimated;top~Dust outlets to the top of the bends~19240~mm~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;" ' parameter table rows
Const C1_twin_TAB_3                As String  = ""           ' parameter table rows
Const C1_twin_TAB_4                As String  = ""           ' parameter table rows
Const C1_twin_TAB_5                As String  = ""           ' parameter table rows
Const C1_twin_TAB_6                As String  = ""           ' parameter table rows
Const C1_twin_TAB_7                As String  = ""           ' parameter table rows
Const C1_twin_TAB_8                As String  = ""           ' parameter table rows
Const C4_D_BARREL                  As Double  = 6.3          ' barrel inner D [derived]
Const C4_H_BARREL                  As Double  = 6.3          ' barrel height [derived]
Const C4_H_CONE                    As Double  = 7.3          ' cone height [derived]
Const C4_L_VORTEX                  As Double  = 3.9          ' vortex finder immersion [derived]
Const C4_D_VORTEX                  As Double  = 4.63         ' vortex finder / outlet pipe bore [derived]
Const C4_D_DUST                    As Double  = 0.81         ' dust outlet D [derived]
Const C4_W_INLET                   As Double  = 2.912        ' volute duct width [derived]
Const C4_H_INLET                   As Double  = 3.4          ' volute duct height [derived]
Const C4_VORTEX_WALL               As Double  = 0.08         ' vortex finder wall (not scaled) [model, preheater/cyclone_C1.md]
Const C4_TONGUE                    As Double  = 0.05         ' volute tongue (not scaled) [model, preheater/cyclone_C4.md]
Const C4_L_DUCT                    As Double  = 3#           ' volute duct length (not scaled) [model, preheater/cyclone_C4.md]
Const C4_HEIGHT                    As Double  = 13.6         ' barrel + cone [derived]
Const C4_OUT_RISE                  As Double  = 7.871        ' outlet pipe rise over the roof [derived]
Const C4_OUT_R                     As Double  = 4.63         ' outlet bend centreline R [derived]
Const C4_OUT_RUN                   As Double  = 4.63         ' outlet run after the bend [derived]
Const C4_EXIT_X                    As Double  = 9.26         ' barrel axis to the gas outlet face [derived]
Const C4_Z_LEG                     As Double  = 26.101       ' the outlet run's axis, z [derived]
Const C4_TOP                       As Double  = 28.416       ' top of the outlet pipe [derived]
Const C4_TAB_1                     As String  = "per_string~Number per string~1~-~published~Verified;D_barrel~Barrel inner diameter D~6300~mm~published~Verified;H_barrel~Barrel height~6300~mm~CFD decision~Estimated;H_cone~Cone height~7300~mm~FLS ratio~Estimated;height~Barrel + cone height~13600~mm~derived~Estimated;L_vortex~Vortex finder immersion S~3900~mm~CFD decision~Estimated;D_vortex~Vortex finder / outlet pipe bore Dx~4630~mm~FLS ratio~Estimated;vortex_wall~Vortex finder wall~80~mm~model parameter~Estimated;D_dust~Dust outlet diameter~810~mm~FLS ratio~Estimated;W_inlet~Inlet width b (volute duct)~2912~mm~CFD decision~Estimated;H_inlet~Inlet height a (volute duct)~3400~mm~CFD decision~Estimated;" ' parameter table rows
Const C4_TAB_2                     As String  = "inlet_duct_length~Volute duct length (from tangent plane)~3000~mm~model parameter~Estimated;tongue~Tongue (cut-water)~50~mm~model parameter~Estimated;overlap~Scroll's inner arc inside the barrel~100~mm~model parameter~Estimated;volute~Volute~yes~-~CFD decision~Estimated;outlet_turn~Outlet bend angle~90~deg~CFD decision~Estimated;outlet_rise~Outlet pipe rise over the roof~7871~mm~derived~Estimated;outlet_bend_R~Outlet bend centreline radius~4630~mm~derived~Estimated;outlet_run~Outlet run after the bend~4630~mm~derived~Estimated;outlet_axis~Roof to the outlet run's axis~12501~mm~derived~Estimated;exit_x~Barrel axis to the gas outlet face~9260~mm~derived~Estimated;" ' parameter table rows
Const C4_TAB_3                     As String  = "top~Dust outlet to the top of the outlet pipe~28416~mm~derived~Estimated;volume~Volume (barrel + cone)~283.25~m3~derived~Estimated;wet_area~Wetted area (barrel, roof ring, cone)~226.13~m2~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;" ' parameter table rows
Const C4_TAB_4                     As String  = ""           ' parameter table rows
Const C4_TAB_5                     As String  = ""           ' parameter table rows
Const C4_TAB_6                     As String  = ""           ' parameter table rows
Const C4_TAB_7                     As String  = ""           ' parameter table rows
Const C4_TAB_8                     As String  = ""           ' parameter table rows
Const C5_D_BARREL                  As Double  = 6.5          ' barrel inner D [derived]
Const C5_H_BARREL                  As Double  = 6.5          ' barrel height [derived]
Const C5_H_CONE                    As Double  = 7.531746     ' cone height [derived]
Const C5_L_VORTEX                  As Double  = 4.02381      ' vortex finder immersion [derived]
Const C5_D_VORTEX                  As Double  = 4.776984     ' vortex finder / outlet pipe bore [derived]
Const C5_D_DUST                    As Double  = 0.835714     ' dust outlet D [derived]
Const C5_W_INLET                   As Double  = 3.004444     ' volute duct width [derived]
Const C5_H_INLET                   As Double  = 3.507937     ' volute duct height [derived]
Const C5_VORTEX_WALL               As Double  = 0.08         ' vortex finder wall (not scaled) [model, preheater/cyclone_C1.md]
Const C5_TONGUE                    As Double  = 0.05         ' volute tongue (not scaled) [model, preheater/cyclone_C4.md]
Const C5_L_DUCT                    As Double  = 3#           ' volute duct length (not scaled) [model, preheater/cyclone_C4.md]
Const C5_HEIGHT                    As Double  = 14.031746    ' barrel + cone [derived]
Const C5_OUT_RISE                  As Double  = 8.120873     ' outlet pipe rise over the roof [derived]
Const C5_OUT_R                     As Double  = 4.776984     ' outlet bend centreline R [derived]
Const C5_OUT_RUN                   As Double  = 4.776984     ' outlet run after the bend [derived]
Const C5_EXIT_X                    As Double  = 9.553968     ' barrel axis to the gas outlet face [derived]
Const C5_Z_LEG                     As Double  = 26.929603    ' the outlet run's axis, z [derived]
Const C5_TOP                       As Double  = 29.318095    ' top of the outlet pipe [derived]
Const C5_TAB_1                     As String  = "per_string~Number per string~1~-~published~Verified;D_barrel~Barrel inner diameter D~6500~mm~published~Verified;H_barrel~Barrel height~6500~mm~derived~Estimated;H_cone~Cone height~7532~mm~derived~Estimated;height~Barrel + cone height~14032~mm~derived~Estimated;L_vortex~Vortex finder immersion S~4024~mm~derived~Estimated;D_vortex~Vortex finder / outlet pipe bore Dx~4777~mm~derived~Estimated;vortex_wall~Vortex finder wall~80~mm~model parameter~Estimated;D_dust~Dust outlet diameter~836~mm~derived~Estimated;W_inlet~Inlet width b (volute duct)~3004~mm~derived~Estimated;H_inlet~Inlet height a (volute duct)~3508~mm~derived~Estimated;" ' parameter table rows
Const C5_TAB_2                     As String  = "inlet_duct_length~Volute duct length (from tangent plane)~3000~mm~model parameter~Estimated;tongue~Tongue (cut-water)~50~mm~model parameter~Estimated;overlap~Scroll's inner arc inside the barrel~100~mm~model parameter~Estimated;volute~Volute~yes~-~derived~Estimated;outlet_turn~Outlet bend angle~90~deg~derived~Estimated;outlet_rise~Outlet pipe rise over the roof~8121~mm~derived~Estimated;outlet_bend_R~Outlet bend centreline radius~4777~mm~derived~Estimated;outlet_run~Outlet run after the bend~4777~mm~derived~Estimated;outlet_axis~Roof to the outlet run's axis~12898~mm~derived~Estimated;exit_x~Barrel axis to the gas outlet face~9554~mm~derived~Estimated;" ' parameter table rows
Const C5_TAB_3                     As String  = "top~Dust outlet to the top of the outlet pipe~29318~mm~derived~Estimated;volume~Volume (barrel + cone)~311.09~m3~derived~Estimated;wet_area~Wetted area (barrel, roof ring, cone)~240.71~m2~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;" ' parameter table rows
Const C5_TAB_4                     As String  = ""           ' parameter table rows
Const C5_TAB_5                     As String  = ""           ' parameter table rows
Const C5_TAB_6                     As String  = ""           ' parameter table rows
Const C5_TAB_7                     As String  = ""           ' parameter table rows
Const C5_TAB_8                     As String  = ""           ' parameter table rows
Const CAL_D_THROAT                 As Double  = 3.130077     ' throat (kiln gas inlet) D [derived]
Const CAL_L_THROAT                 As Double  = 3.130077     ' throat length [derived]
Const CAL_H_CONE                   As Double  = 3.871181     ' cone height [derived]
Const CAL_D_VESSEL                 As Double  = 6.7404       ' vessel inner D [derived]
Const CAL_H_VESSEL                 As Double  = 30#          ' cone + cylinder [derived]
Const CAL_H_CYL                    As Double  = 26.128819    ' cylinder height [derived]
Const CAL_Z_CONE                   As Double  = 7.001258     ' the cone's top, z [derived]
Const CAL_Z_ROOF                   As Double  = 33.130077    ' the roof, z [derived]
Const CAL_D_NECK                   As Double  = 4.949747     ' gooseneck neck D [derived]
Const CAL_PIECE                    As Double  = 4.949747     ' the neck's inclined pieces [derived]
Const CAL_LEVEL                    As Double  = 4.949747     ' the neck's level piece [derived]
Const CAL_Z_BEND                   As Double  = 36.630077    ' the level piece's axis, z [derived]
Const CAL_D_LEG                    As Double  = 3.5          ' gooseneck arm D [derived]
Const CAL_X_LEG                    As Double  = 10.78133     ' the arms' outlet faces, x [derived]
Const CAL_Z_END                    As Double  = 23.522304    ' the arms' level runs' axis, z [derived]
Const CAL_WIDTH                    As Double  = 21.562659    ' overall width over the arms' outlet faces, x [derived]
Const CAL_Z_SPLIT                  As Double  = 25.705456    ' the channel's lower end, where the arms leave, z [derived]
Const CAL_X_BEND                   As Double  = 3.78133      ' where an arm turns level, x [derived]
Const CAL_Y_OFF                    As Double  = 12.134703    ' the channel and the arms, in front of the axis [derived]
Const CAL_TOP                      As Double  = 39.104951    ' the neck's crown, z [derived]
Const CAL_Y_FRONT                  As Double  = 14.609577    ' the channel's far side, forward of the axis [derived]
Const CAL_TA_D                     As Double  = 2.4393       ' tertiary air duct D [derived]
Const CAL_TA_Y                     As Double  = -2.10055     ' its axis, y [derived]
Const CAL_TA_Z                     As Double  = 8.270908     ' its axis, z [derived]
Const CAL_TA_X                     As Double  = 6.3702       ' its face, x [derived]
Const CAL_FEED_D                   As Double  = 0.8485       ' meal pipe D [derived]
Const CAL_FEED_X                   As Double  = 3.8702       ' meal pipe end face centre, x [derived]
Const CAL_FEED_Z                   As Double  = 12.251519    ' meal pipe end face centre, z [derived]
Const CAL_FUEL_D                   As Double  = 0.2828       ' fuel pipe D [derived]
Const CAL_FUEL_Y                   As Double  = 4.236225     ' fuel pipe end face centre, y [derived]
Const CAL_FUEL_Z                   As Double  = 11.885494    ' fuel pipe end face centre, z [derived]
Const CAL_BOX_Y                    As Double  = 4.306925     ' the fuel pipes' far side, y [derived]
Const calciner_TAB_1               As String  = "D_throat~Throat (kiln gas inlet) diameter~3130~mm~derived~Estimated;L_throat~Throat length~3130~mm~derived~Estimated;H_cone~Cone height~3871~mm~derived~Estimated;D_vessel~Vessel inner diameter D~6740~mm~FLS ratio~Estimated;H_cylinder~Cylinder height~26129~mm~derived~Estimated;H_vessel~Vessel height (cone + cylinder)~30000~mm~published~Verified;D_neck~Gooseneck neck diameter (both arms' area)~4950~mm~derived~Estimated;neck_slope~Neck slope~45~deg~model parameter~Estimated;neck_piece~Neck's inclined pieces (2): length~4950~mm~derived~Estimated;neck_level~Neck's level piece: length~4950~mm~derived~Estimated;channel~Vertical channel below the neck: length~7425~mm~derived~Estimated;" ' parameter table rows
Const calciner_TAB_2               As String  = "D_leg~Gooseneck arm bore~3500~mm~published~Verified;arm_angle~Arm angle to the vertical~60~deg~model parameter~Estimated;arm_run~Arms' level run to the outlet face: length~7000~mm~derived~Estimated;y_off~Channel and arms in front of the vessel axis~12135~mm~derived~Estimated;x_leg~Barrel axis to an arm's outlet face~10781~mm~derived~Schematic;leg_end_z~Throat foot to the arms' level runs' axis (C5's inlet axis)~23522~mm~derived~Schematic;width~Overall width over the arms' outlet faces~21563~mm~derived~Schematic;top~Throat foot to the neck's crown~39105~mm~derived~Estimated;D_TA~Tertiary air duct diameter~2439~mm~FLS ratio~Estimated;" ' parameter table rows
Const calciner_TAB_3               As String  = "ta_y~Tertiary air duct axis off the vessel axis (tangential)~-2101~mm~derived~Estimated;ta_z~Tertiary air duct axis height~8271~mm~derived~Estimated;ta_x~Vessel axis to the duct's face~6370~mm~derived~Estimated;D_feed~Meal pipe diameter (two)~849~mm~literature~Estimated;feed_slope~Meal pipes' slope to the horizontal~60~deg~literature~Estimated;D_fuel~Fuel pipe diameter (two)~283~mm~literature~Estimated;fuel_slope~Fuel pipes' slope to the horizontal~30~deg~literature~Estimated;volume~Volume (cone + cylinder)~1009.71~m3~derived~Estimated;wet_area~Wetted area (cylinder, cone, roof ring)~635.96~m2~derived~Estimated;u_wall~Shell / refractory thickness~-~~no source~Unknown;" ' parameter table rows
Const calciner_TAB_4               As String  = "u_material~Material~-~~no source~Unknown;u_flange~Flanges / nozzles / manholes~-~~no source~Unknown;u_support~Supports / hangers~-~~no source~Unknown;u_burner~Burner / fuel inlet fittings~-~~no source~Unknown;" ' parameter table rows
Const calciner_TAB_5               As String  = ""           ' parameter table rows
Const calciner_TAB_6               As String  = ""           ' parameter table rows
Const calciner_TAB_7               As String  = ""           ' parameter table rows
Const calciner_TAB_8               As String  = ""           ' parameter table rows
Const KIL_D                        As Double  = 4.8          ' kiln inner D [derived]
Const KIL_L                        As Double  = 74#          ' kiln length, back end to hood end [derived]
Const kiln_TAB_1                   As String  = "D_kiln~Kiln inner diameter (effective)~4800~mm~published~Verified;L_kiln~Kiln length~74000~mm~published~Verified;slope~Slope (installed, not built into the solid)~3~%~published~Verified;transition_L~Transition zone from the back end (model split)~30830~mm~model parameter~Estimated;burning_L~Burning zone (model split)~43170~mm~derived~Estimated;volume~Volume (tube)~1339.07~m3~derived~Verified;wall_area~Wetted area (tube)~1115.89~m2~derived~Verified;u_wall~Shell / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;u_tyre~Tyres / support rollers~-~~no source~Unknown;u_drive~Drive / girth gear~-~~no source~Unknown;" ' parameter table rows
Const kiln_TAB_2                   As String  = "u_seal~Inlet and outlet seals~-~~no source~Unknown;" ' parameter table rows
Const kiln_TAB_3                   As String  = ""           ' parameter table rows
Const kiln_TAB_4                   As String  = ""           ' parameter table rows
Const kiln_TAB_5                   As String  = ""           ' parameter table rows
Const kiln_TAB_6                   As String  = ""           ' parameter table rows
Const kiln_TAB_7                   As String  = ""           ' parameter table rows
Const kiln_TAB_8                   As String  = ""           ' parameter table rows
Const COO_L                        As Double  = 29.9         ' grate length, hot end x = 0 to the cold end [derived]
Const COO_W                        As Double  = 4#           ' grate width [derived]
Const COO_H                        As Double  = 3#           ' grate to roof [derived]
Const COO_SEG_L                    As Double  = 2.99         ' one segment's length [derived]
Const COO_HOOD_L                   As Double  = 5.98         ' the hood opening's length from x = 0 [derived]
Const COO_SEGMENTS                 As Double  = 10#          ' undergrate air segments [derived]
Const cooler_TAB_1                 As String  = "grate_area~Grate area (PF5000)~119.60~m2~published~Verified;w_cool~Grate width~4000~mm~literature~Estimated;L_cool~Grate length (area / width)~29900~mm~derived~Estimated;H_cool~Height, grate to roof~3000~mm~literature~Estimated;segments~Undergrate air segments (FLS)~10~-~literature~Estimated;segment~One segment: length~2990~mm~derived~Estimated;hood_segments~Segments under the hood's opening (hot end)~2~-~literature~Estimated;hood~Hood opening: length from the hot end~5980~mm~derived~Estimated;volume~Volume (box, bed included)~358.80~m3~derived~Estimated;wall_area~Wall area (sides, ends, roof but the hood)~299.08~m2~derived~Estimated;" ' parameter table rows
Const cooler_TAB_2                 As String  = "u_vent~Vent outlet (cold end): place and size~-~~no source~Unknown;u_plate~Grate plates / compartment walls~-~~no source~Unknown;u_crusher~Clinker crusher~-~~no source~Unknown;u_chute~Clinker chute from the kiln~-~~no source~Unknown;u_wall~Casing / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;" ' parameter table rows
Const cooler_TAB_3                 As String  = ""           ' parameter table rows
Const cooler_TAB_4                 As String  = ""           ' parameter table rows
Const cooler_TAB_5                 As String  = ""           ' parameter table rows
Const cooler_TAB_6                 As String  = ""           ' parameter table rows
Const cooler_TAB_7                 As String  = ""           ' parameter table rows
Const cooler_TAB_8                 As String  = ""           ' parameter table rows
Const KIC_A                        As Double  = 6.8          ' plan: the square's side [derived]
Const KIC_H                        As Double  = 6.8          ' floor level to the flat roof [derived]
Const KIC_D_THROAT                 As Double  = 3.130077     ' the roof's throat (outlet) [derived]
Const KIC_D_MOUTH                  As Double  = 4.8          ' the kiln's mouth on the +x wall [published, kiln/kiln.md]
Const KIC_H_LIP                    As Double  = 0.8          ' the ramp's foot on the +x wall [derived]
Const KIC_RAMP_DEG                 As Double  = 41.423666    ' the floor ramp's slope, foot to the far top corner [derived]
Const kiln_inlet_chamber_TAB_1     As String  = "a_plan~Plan: side of the square (D + 2 margin)~6800~mm~derived~Estimated;H~Height: floor level to the flat roof (= the plan's side)~6800~mm~derived~Estimated;h_wall~Kiln's wall: ramp's foot to the roof (H - h_lip)~6000~mm~derived~Estimated;D_throat~Throat (outlet to the calciner) diameter~3130~mm~derived~Estimated;D_mouth~Kiln mouth diameter (the kiln's effective D)~4800~mm~published~Verified;margin~Margin round the kiln (plan = D + 2 margin)~1000~mm~model parameter~Estimated;clear~Mouth clearance to the ramp's foot~200~mm~model parameter~Estimated;h_lip~Ramp's foot on the kiln's wall, over the floor level~800~mm~derived~Estimated;" ' parameter table rows
Const kiln_inlet_chamber_TAB_2     As String  = "ramp_deg~Floor ramp's slope (foot to the far top corner)~41.4~deg~derived~Estimated;volume~Volume (to the roof)~138.72~m3~derived~Estimated;u_ports~Burner, door and inspection ports~-~~no source~Unknown;u_bypass~Gas bypass take-off~-~~no source~Unknown;u_meal~Meal entry (injected in the solver)~-~~no source~Unknown;u_shell~Casing / refractory thickness~-~~no source~Unknown;u_material~Material~-~~no source~Unknown;" ' parameter table rows
Const kiln_inlet_chamber_TAB_3     As String  = ""           ' parameter table rows
Const kiln_inlet_chamber_TAB_4     As String  = ""           ' parameter table rows
Const kiln_inlet_chamber_TAB_5     As String  = ""           ' parameter table rows
Const kiln_inlet_chamber_TAB_6     As String  = ""           ' parameter table rows
Const kiln_inlet_chamber_TAB_7     As String  = ""           ' parameter table rows
Const kiln_inlet_chamber_TAB_8     As String  = ""           ' parameter table rows
Const IDF_R1                       As Double  = 0.917989     ' the eye's circle (y = b1) [derived]
Const IDF_R2                       As Double  = 1.311413     ' the tip's circle (y = b2) [derived]
Const IDF_B1                       As Double  = 0.458994     ' the eye's plane y [derived]
Const IDF_B2                       As Double  = 0.51395      ' the outlet width b2: the rim ring's top y [derived]
Const IDF_R_MRF                    As Double  = 1.409769     ' the rotating zone's rim [derived]
Const IDF_VOL_B                    As Double  = 1.54185      ' the volute's width, y = 0 .. B [derived]
Const IDF_E_TOP_X                  As Double  = 0.935149     ' the outlet face's outer edge (along y), x [derived]
Const IDF_E_TOP_Z                  As Double  = 4.426034     ' the outlet face's outer edge, z [derived]
Const IDF_E_LOW_X                  As Double  = -0.412402    ' the outlet face's lower edge (along y), x [derived]
Const IDF_E_LOW_Z                  As Double  = 3.078483     ' the outlet face's lower edge, z [derived]
Const IDF_DIS_DX                   As Double  = -0.707106781 ' the discharge's direction, x [derived]
Const IDF_DIS_DZ                   As Double  = 0.707106781  ' the discharge's direction, z [derived]
Const IDF_X_MIN                    As Double  = -2.116387    ' the fan's x min (the volute) [derived]
Const IDF_Z_MIN                    As Double  = -2.672116    ' the fan's z min (the volute) [derived]
Const IDF_Z_MAX                    As Double  = 4.426034     ' the fan's z max (the outlet's outer edge) [derived]
Const IDF_Y_BOX                    As Double  = 1.59185      ' the inlet box's floor, y [derived]
Const IDF_BOX_H                    As Double  = 2.625448     ' the inlet box's height (z), x from -BOX_H/2 [derived]
Const IDF_BOX_DEPTH                As Double  = 1.764653     ' the inlet box's depth (y) [derived]
Const IDF_BOX_REACH                As Double  = 2.386771     ' the box's inlet face, x [derived]
Const IDF_V_ROTOR                  As Double  = 2.914511     ' the bladed rotor's volume: tells today's solid from an older one [m3] [derived]
Const id_fan_TAB_1                 As String  = "D2~Impeller diameter D2 (tip speed / pi n)~2623~mm~derived~Estimated;D1~Eye diameter D1 (0.70 D2)~1836~mm~derived~Estimated;b1~Blade height at the eye b1 (c_m1 = c0)~459~mm~derived~Estimated;b2~Outlet width b2 (Euler, Wiesner slip, continuity)~514~mm~derived~Estimated;z~Blades z = 8.5 sin(beta2) / (1 - D1/D2)~20~-~derived~Estimated;beta1~Blade inlet angle beta1 (from the tangent)~24.1~deg~derived~Estimated;beta2~Blade outlet angle~45~deg~literature~Estimated;blade_t~Blade thickness~12~mm~model parameter~Estimated;blade_arc_R~Blade: single circular arc, radius~4912~mm~derived~Estimated;B~Volute width B (3 b2)~1542~mm~derived~Estimated;" ' parameter table rows
Const id_fan_TAB_2                 As String  = "r3~Tongue circle r3 (r2 + 0.075 D2)~1508~mm~derived~Estimated;nose_R~Tongue nose radius~197~mm~derived~Estimated;spiral_deg~Log spiral angle (outlet at 30 m/s)~8.4~deg~derived~Estimated;r_end~Spiral end radius~3832~mm~derived~Estimated;h_stub~Outlet height (spiral end cos(alpha) - 2 nose R)~1906~mm~derived~Estimated;l_stub~Straight discharge length~1906~mm~derived~Estimated;gamma~Discharge angle up from the horizontal~45~deg~model parameter~Estimated;r_mrf~Rotating (MRF) zone radius~1410~mm~derived~Estimated;D_cone~Inlet cone mouth diameter~2387~mm~derived~Estimated;L_cone~Inlet cone length (eye to the box, through the plate)~1133~mm~derived~Estimated;" ' parameter table rows
Const id_fan_TAB_3                 As String  = "H_box~Inlet box height (z)~2625~mm~derived~Estimated;depth_box~Inlet box depth (y): face area 1.75 x eye~1765~mm~derived~Estimated;reach_box~Inlet box face from the axis (x)~2387~mm~derived~Estimated;q~Volume flow at the inlet (one string)~88.15~m3/s~derived~Estimated;dp~Total pressure rise~8000~Pa~model parameter~Estimated;speed~Speed~1000~rpm~literature~Estimated;u_out~Outlet velocity~30~m/s~derived~Estimated;V_rotor~Volume: rotating zone (bladed)~2.91~m3~derived~Estimated;V_volute~Volume: volute + discharge~28.51~m3~derived~Estimated;V_inlet~Volume: inlet cone + box~21.13~m3~derived~Estimated;u_casing~Casing / plate thickness~-~~no source~Unknown;" ' parameter table rows
Const id_fan_TAB_4                 As String  = "u_shaft~Shaft, hub boss, bearings~-~~no source~Unknown;u_damper~Inlet damper / IGV (VFD assumed)~-~~no source~Unknown;u_gaps~Seal gap cone-shroud, disc cavities~-~~no source~Unknown;u_material~Material, wear liners~-~~no source~Unknown;" ' parameter table rows
Const id_fan_TAB_5                 As String  = ""           ' parameter table rows
Const id_fan_TAB_6                 As String  = ""           ' parameter table rows
Const id_fan_TAB_7                 As String  = ""           ' parameter table rows
Const id_fan_TAB_8                 As String  = ""           ' parameter table rows
' END GENERATED

' Sheet [m on paper]: A1 landscape, ISO 5457 frame
Const PAPER_W  As Double = 0.841
Const PAPER_H  As Double = 0.594
' (the sheet's scale and the detail's: C1 1:50 / 1:20, C1_twin 1:100 / 1:50;
' set per run in Build)
Const FR_X0 As Double = 0.02, FR_X1 As Double = 0.831, FR_Y0 As Double = 0.01, FR_Y1 As Double = 0.584
Const COL_X0 As Double = 0.651          ' the right-hand column: notes, legend, table, title block
Const TEXT_H As Double = 0.0025
Const VIEW_LETTER_H As Double = 0.0035     ' ISO 128-3 view letters, 1.4 x TEXT_H
Const CAP_H  As Double = 0.0018

' Where the views go on the sheet [m]: the top view's centre; A-A is
' placed by its alignment over it, the left view right of A-A.
Const TOP_X  As Double = 0.2
Const TOP_Y  As Double = 0.105
Const SEC_Y  As Double = 0.38
Const LEFT_X As Double = 0.44
Const DET_X  As Double = 0.57
Const DET_Y  As Double = 0.45
' C1_twin: the front view's centre; the plan (A-A) under it, the side
' view right of it, detail C right of the plan
Const TW_FRONT_X As Double = 0.17
Const TW_FRONT_Y As Double = 0.4
Const TW_PLAN_Y  As Double = 0.155
Const TW_SIDE_X  As Double = 0.38
Const TW_DET_X   As Double = 0.55
Const TW_DET_Y   As Double = 0.2
' calciner (1:200): the plan at the bottom, A-A over it, the front view
' right of A-A, the left view right of that, detail B under the left view
Const CAL_TOP_X   As Double = 0.17
Const CAL_TOP_Y   As Double = 0.1
Const CAL_SEC_Y   As Double = 0.36
Const CAL_FRONT_X As Double = 0.33
Const CAL_LEFT_X  As Double = 0.47
Const CAL_DET_X   As Double = 0.57
Const CAL_DET_Y   As Double = 0.18

' kiln (1:200): the side view, the end view (1:50) under it
Const KIL_SIDE_X  As Double = 0.3
Const KIL_SIDE_Y  As Double = 0.4
Const KIL_END_X   As Double = 0.2
Const KIL_END_Y   As Double = 0.27

' cooler (1:100): side view, plan under it, floor view under that, the end
' view (1:50) at the bottom left
Const COO_X       As Double = 0.33
Const COO_SIDE_Y  As Double = 0.5
Const COO_PLAN_Y  As Double = 0.4
Const COO_FLOOR_Y As Double = 0.3
Const COO_END_X   As Double = 0.14
Const COO_END_Y   As Double = 0.13

' kiln inlet chamber (1:50, first angle): the side view (x right, z up), the plan
' under it, the view from the kiln's wall (+x) to the left of the side view
Const KIC_SIDE_X  As Double = 0.36
Const KIC_SIDE_Y  As Double = 0.42
Const KIC_PLAN_Y  As Double = 0.2
Const KIC_END_X   As Double = 0.14
Const KIC_END_Y   As Double = 0.42
Const KIC_STUB    As Double = 0.001     ' the throat disc over the roof (kiln_inlet_chamber.bas, STUB_T)

' ID fan (1:50, first angle): the front view from the drive side (-y: x
' right, z up), the plan under it, the view from +x (the inlet box's face)
' left of the front; the rotating zone alone at 1:20, from the inlet side
' (+y) and from +x, right of the front.
Const IDF_FRONT_X As Double = 0.25
Const IDF_FRONT_Y As Double = 0.4
Const IDF_PLAN_Y  As Double = 0.18
Const IDF_SIDE_X  As Double = 0.09
Const IDF_ROT_X   As Double = 0.43
Const IDF_ROT_Y   As Double = 0.4
Const IDF_ROTS_X  As Double = 0.57

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

Dim equip As String              ' "C1", "C1_twin", "C4", "C5", "calciner", "kiln", "cooler", "kiln_inlet_chamber" or "id_fan": what this run draws
' a volute cyclone's values (C4 / C5), loaded by LoadVolute
Dim vD As Double, vHb As Double, vHc As Double, vLv As Double, vDv As Double, vDd As Double
Dim vW As Double, vH As Double, vWall As Double, vTongue As Double, vLduct As Double
Dim vHeight As Double, vRise As Double, vBendR As Double, vRun As Double, vExitX As Double
Dim vZleg As Double, vTopZ As Double
Dim scaleD As Double, detailD As Double
Dim detX As Double, detY As Double
Dim partPath As String
Dim swPart As SldWorks.ModelDoc2
Dim partStamp As Date, partLen As Long
Dim vTop As SldWorks.View, vSec As SldWorks.View, vLeft As SldWorks.View, vDet As SldWorks.View
Dim vFront As SldWorks.View, vPlan As SldWorks.View, vSide As SldWorks.View, vDetC As SldWorks.View

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
    Build "C1"
End Sub


Sub c1_twin()
    Build "C1_twin"
End Sub


Sub c4()
    Build "C4"
End Sub


Sub c5()
    Build "C5"
End Sub


Sub calciner()
    Build "calciner"
End Sub


Sub kiln()
    Build "kiln"
End Sub


Sub cooler()
    Build "cooler"
End Sub


Sub kiln_inlet_chamber()
    Build "kiln_inlet_chamber"
End Sub


Sub id_fan()
    Build "id_fan"
End Sub


Private Sub Build(ByVal which As String)

    Dim why As String, frameWas As Long, sepWas As Boolean, sepChrWas As String

    equip = which
    buildLog = ""
    phase = "starting up"
    nDims = 0: nDimsOk = 0: nRows = 0: skPerM = 0#
    Set vTop = Nothing: Set vSec = Nothing: Set vLeft = Nothing: Set vDet = Nothing
    Set vFront = Nothing: Set vPlan = Nothing: Set vSide = Nothing: Set vDetC = Nothing
    If equip = "C1" Then
        scaleD = 50#: detailD = 20#: detX = DET_X: detY = DET_Y
    ElseIf equip = "C1_twin" Then
        scaleD = 100#: detailD = 50#: detX = TW_DET_X: detY = TW_DET_Y
    ElseIf equip = "calciner" Then
        scaleD = 200#: detailD = 50#: detX = CAL_DET_X: detY = CAL_DET_Y
    ElseIf equip = "kiln" Then
        scaleD = 200#: detailD = 50#: detX = 0.63: detY = DET_Y
    ElseIf equip = "cooler" Then
        scaleD = 100#: detailD = 50#: detX = 0.63: detY = DET_Y
    ElseIf equip = "id_fan" Then
        scaleD = 50#: detailD = 20#: detX = 0.63: detY = DET_Y
    ElseIf equip = "kiln_inlet_chamber" Then
        scaleD = 50#: detailD = 50#: detX = 0.63: detY = DET_Y
    Else
        scaleD = 100#: detailD = 20#: detX = 0.63: detY = DET_Y
        LoadVolute
    End If
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."
    Set swMath = swApp.GetMathUtility
    ' A minimized SolidWorks draws no view: no hidden lines, no tangent
    ' edges, and a dimension to such an edge finds nothing (16 Nov, runs
    ' from WSL with the window minimized: C1 12/13). Restored for the run.
    frameWas = swApp.FrameState
    If frameWas = swWindowMinimized Then
        swApp.FrameState = swWindowNormal
        Note "SolidWorks was minimized: restored for the run"
    End If
    ' A decimal point in the dimensions, as in the table and the notes:
    ' the system's separator is a comma on a Turkish Windows (KIC's ramp
    ' printed 41,4 against the table's 41.4, 16 Nov). A system option, so
    ' set for the run and put back.
    sepWas = swApp.GetUserPreferenceToggle(swUseSystemSeparatorForDims)
    sepChrWas = swApp.GetUserPreferenceStringValue(swSeparatorCharacterForDims)
    swApp.SetUserPreferenceToggle swUseSystemSeparatorForDims, False
    swApp.SetUserPreferenceStringValue swSeparatorCharacterForDims, "."

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

    buildLog = "drawings " & equip & " built: " & nDimsOk & " of " & nDims & " dimensions verified" & vbLf & buildLog
    WriteLog
    RestoreSession frameWas, sepWas, sepChrWas
    Tell "Drawing " & equip & " built: " & nDimsOk & " of " & nDims & " dimensions verified." & vbLf & _
           "Full log: " & LogPath(), vbInformation, "Equipment drawings"
    Exit Sub

Failed:
    why = Err.Description
    buildLog = "drawings " & equip & " ABORTED while " & phase & ": " & why & vbLf & buildLog
    WriteLog
    If Not swApp Is Nothing Then RestoreSession frameWas, sepWas, sepChrWas
    Tell "Drawing " & equip & " ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
           vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "Equipment drawings"
End Sub

' The window state and dimension separator Build changed, put back.
Private Sub RestoreSession(ByVal frameWas As Long, ByVal sepWas As Boolean, ByVal sepChrWas As String)
    On Error Resume Next
    swApp.SetUserPreferenceToggle swUseSystemSeparatorForDims, sepWas
    If sepChrWas <> "" Then swApp.SetUserPreferenceStringValue swSeparatorCharacterForDims, sepChrWas
    If frameWas = swWindowMinimized Then swApp.FrameState = swWindowMinimized
End Sub

' The closing message box, left out when OUT_ROOT\quiet.flag exists: a run
' started from WSL (tools/sw_run.py) must not wait on a click; the log
' carries the same text.
Private Sub Tell(ByVal msg As String, ByVal style As Long, ByVal caption As String)
    If Dir(OUT_ROOT & "quiet.flag") <> "" Then Exit Sub
    MsgBox msg, style, caption
End Sub



'==================================================================
' The parameter table (generated): rows ';', fields '~'
'==================================================================
' A volute cyclone's values for this run, from its generated Consts
' (C4's; C5's are C4's scaled, but for the finder's wall, the tongue and
' the duct's length).
Private Sub LoadVolute()
    Select Case equip
    Case "C4"
        vD = C4_D_BARREL: vHb = C4_H_BARREL: vHc = C4_H_CONE: vLv = C4_L_VORTEX: vDv = C4_D_VORTEX
        vDd = C4_D_DUST: vW = C4_W_INLET: vH = C4_H_INLET: vWall = C4_VORTEX_WALL: vTongue = C4_TONGUE
        vLduct = C4_L_DUCT: vHeight = C4_HEIGHT: vRise = C4_OUT_RISE: vBendR = C4_OUT_R: vRun = C4_OUT_RUN
        vExitX = C4_EXIT_X: vZleg = C4_Z_LEG: vTopZ = C4_TOP
    Case "C5"
        vD = C5_D_BARREL: vHb = C5_H_BARREL: vHc = C5_H_CONE: vLv = C5_L_VORTEX: vDv = C5_D_VORTEX
        vDd = C5_D_DUST: vW = C5_W_INLET: vH = C5_H_INLET: vWall = C5_VORTEX_WALL: vTongue = C5_TONGUE
        vLduct = C5_L_DUCT: vHeight = C5_HEIGHT: vRise = C5_OUT_RISE: vBendR = C5_OUT_R: vRun = C5_OUT_RUN
        vExitX = C5_EXIT_X: vZleg = C5_Z_LEG: vTopZ = C5_TOP
    End Select
End Sub


Private Sub ParseTable()
    Dim all As String, rows As Variant, f As Variant
    Dim i As Long
    If equip = "C1" Then
        all = C1_TAB_1 & C1_TAB_2 & C1_TAB_3 & C1_TAB_4 & C1_TAB_5 & C1_TAB_6 & C1_TAB_7 & C1_TAB_8
    ElseIf equip = "C4" Then
        all = C4_TAB_1 & C4_TAB_2 & C4_TAB_3 & C4_TAB_4 & C4_TAB_5 & C4_TAB_6 & C4_TAB_7 & C4_TAB_8
    ElseIf equip = "C5" Then
        all = C5_TAB_1 & C5_TAB_2 & C5_TAB_3 & C5_TAB_4 & C5_TAB_5 & C5_TAB_6 & C5_TAB_7 & C5_TAB_8
    ElseIf equip = "calciner" Then
        all = calciner_TAB_1 & calciner_TAB_2 & calciner_TAB_3 & calciner_TAB_4 & calciner_TAB_5 & _
              calciner_TAB_6 & calciner_TAB_7 & calciner_TAB_8
    ElseIf equip = "cooler" Then
        all = cooler_TAB_1 & cooler_TAB_2 & cooler_TAB_3 & cooler_TAB_4 & cooler_TAB_5 & cooler_TAB_6 & cooler_TAB_7 & cooler_TAB_8
    ElseIf equip = "id_fan" Then
        all = id_fan_TAB_1 & id_fan_TAB_2 & id_fan_TAB_3 & id_fan_TAB_4 & id_fan_TAB_5 & id_fan_TAB_6 & id_fan_TAB_7 & id_fan_TAB_8
    ElseIf equip = "kiln_inlet_chamber" Then
        all = kiln_inlet_chamber_TAB_1 & kiln_inlet_chamber_TAB_2 & kiln_inlet_chamber_TAB_3 & kiln_inlet_chamber_TAB_4 & _
              kiln_inlet_chamber_TAB_5 & kiln_inlet_chamber_TAB_6 & kiln_inlet_chamber_TAB_7 & kiln_inlet_chamber_TAB_8
    ElseIf equip = "kiln" Then
        all = kiln_TAB_1 & kiln_TAB_2 & kiln_TAB_3 & kiln_TAB_4 & kiln_TAB_5 & kiln_TAB_6 & kiln_TAB_7 & kiln_TAB_8
    Else
        all = C1_twin_TAB_1 & C1_twin_TAB_2 & C1_twin_TAB_3 & C1_twin_TAB_4 & C1_twin_TAB_5 & C1_twin_TAB_6 & _
              C1_twin_TAB_7 & C1_twin_TAB_8
    End If
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
    partPath = OUT_ROOT & LINE_KEY & "\" & equip & ".SLDPRT"
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
' The twin's solid, c1_twin.bas' own: its true extent (GetExtremePoint;
' GetBodyBox bounds curved faces loosely), 1 cm.
Private Sub CheckTwinBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = -(0.5 * TW_S + TW_C1_FAR): want(3) = 0.5 * TW_S + TW_C1_FAR
    want(1) = TW_Y_MIN: want(4) = TW_Y_MAX
    want(2) = TW_Z_SPLIT - TW_R1_STUB_L: want(5) = TW_TOP
    For i = 0 To 5
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's twin has " & Num(want(i), 3) & _
                 " -- rebuild it with c1_twin.bas."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


' A volute cyclone's solid (C4, C5; cyclone.bas): its true extent, 1 cm.
' The volute's spiral is a spline through sample points and bulges a
' little past the tongue's radius (C4: 0.125 m, C5: 0.129 m on -y, seen
' in their STL), so y min is bounded, not matched.
Private Sub CheckVoluteBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant, rT As Double
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    rT = 0.5 * vD + vTongue
    want(0) = -vLduct: If vLduct < 0.5 * vD Then want(0) = -0.5 * vD
    want(3) = vExitX
    want(1) = -rT: want(4) = rT + vW
    want(2) = 0#: want(5) = vTopZ
    For i = 0 To 5
        If i = 1 Then
            If box(1) > want(1) + 0.01 Or box(1) < want(1) - 0.2 Then
                Fail partPath & ": y min is " & Num(box(1), 3) & " m, today's " & equip & " scroll ends at " & Num(want(1), 3) & _
                     " (a spline may bulge 0.2 m past it) -- rebuild it with cyclone.bas."
            End If
        ElseIf Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's " & equip & " has " & Num(want(i), 3) & _
                 " -- rebuild it with cyclone.bas (CYCLONE_NAME = " & equip & ", VOLUTE_ON)."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


' The body's true extent from its extreme points.
Private Function ExactBox(body As SldWorks.Body2) As Variant
    Dim b(5) As Double, d(2) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed along axis " & a & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    ExactBox = b
End Function


' The calciner's solid (calciner.bas): its true extent, 1 cm.
Private Sub CheckCalcinerBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = -0.5 * CAL_WIDTH: want(3) = 0.5 * CAL_WIDTH
    want(1) = -CAL_Y_FRONT: want(4) = CAL_BOX_Y
    want(2) = 0#: want(5) = CAL_TOP
    For i = 0 To 5
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's calciner has " & Num(want(i), 3) & _
                 " -- rebuild it with calciner.bas."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


Private Sub CheckKilnBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = -0.5 * KIL_D: want(3) = 0.5 * KIL_D
    want(1) = -0.5 * KIL_D: want(4) = 0.5 * KIL_D
    want(2) = 0#: want(5) = KIL_L
    For i = 0 To 5
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's kiln has " & Num(want(i), 3) & _
                 " -- rebuild it with kiln.bas."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


Private Sub CheckCoolerBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = 0#: want(3) = COO_L
    want(1) = -0.5 * COO_W: want(4) = 0.5 * COO_W
    want(2) = 0#: want(5) = COO_H
    For i = 0 To 5
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's cooler has " & Num(want(i), 3) & _
                 " -- rebuild it with cooler.bas."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


Private Sub CheckKicBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = -0.5 * KIC_A: want(3) = 0.5 * KIC_A
    want(1) = -0.5 * KIC_A: want(4) = 0.5 * KIC_A
    want(2) = KIC_H_LIP: want(5) = KIC_H + KIC_STUB
    For i = 0 To 5
        If Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's chamber has " & Num(want(i), 3) & _
                 " -- rebuild it with kiln_inlet_chamber.bas."
        End If
    Next i
    Note "part box: x " & Num(box(0), 3) & " .. " & Num(box(3), 3) & ", y " & Num(box(1), 3) & " .. " & Num(box(4), 3) & _
         ", z " & Num(box(2), 3) & " .. " & Num(box(5), 3) & " m (as the source)"
End Sub


' The fan's three bodies (id_fan.bas: rotor, volute, inlet), as the source:
' their joint true extent at the outlet face (-x), the hub's plane (y = 0),
' the box's top (+y) and the outlet's top (+z), 1 cm; and the bladed rotor's
' volume, which tells today's blades (a millimetre off the eye's and the
' tip's circles) from an older build.
Private Sub CheckIdFanBox(doc As SldWorks.ModelDoc2)
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant, mp As Variant
    Dim lo(2) As Double, hi(2) As Double, i As Long, k As Long, nRot As Long
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 2 Then Fail partPath & " has " & (UBound(bodies) + 1) & _
        " bodies, not 3 (rotor, volute, inlet) -- rebuild it with id_fan.bas."
    For k = 0 To 2: lo(k) = 1E+30: hi(k) = -1E+30: Next k
    For i = 0 To 2
        Set b = bodies(i)
        box = ExactBox(b)
        For k = 0 To 2
            If box(k) < lo(k) Then lo(k) = box(k)
            If box(k + 3) > hi(k) Then hi(k) = box(k + 3)
        Next k
        If IdfKind(b) = "rotor" Then
            nRot = nRot + 1
            mp = b.GetMassProperties(1#)
            If Abs(mp(3) - IDF_V_ROTOR) > 0.00008 * IDF_V_ROTOR Then Fail partPath & ": the rotor is " & Num(mp(3), 6) & _
                " m3, today's has " & Num(IDF_V_ROTOR, 6) & " -- rebuild it with id_fan.bas."
        End If
    Next i
    If nRot <> 1 Then Fail partPath & ": found " & nRot & " rotor bodies, expected 1."
    If Abs(lo(0) - IDF_X_MIN) > 0.01 Or Abs(lo(1)) > 0.01 Or Abs(hi(1) - (IDF_Y_BOX + IDF_BOX_DEPTH)) > 0.01 Or _
       Abs(lo(2) - IDF_Z_MIN) > 0.01 Or Abs(hi(2) - IDF_Z_MAX) > 0.01 Then
        Fail partPath & ": x min " & Num(lo(0), 3) & ", y " & Num(lo(1), 3) & " .. " & Num(hi(1), 3) & ", z " & Num(lo(2), 3) & _
             " .. " & Num(hi(2), 3) & " m; today's fan has " & Num(IDF_X_MIN, 3) & ", 0 .. " & Num(IDF_Y_BOX + IDF_BOX_DEPTH, 3) & _
             ", " & Num(IDF_Z_MIN, 3) & " .. " & Num(IDF_Z_MAX, 3) & " -- rebuild it with id_fan.bas."
    End If
    Note "part box: x " & Num(lo(0), 3) & " .. " & Num(hi(0), 3) & ", y " & Num(lo(1), 3) & " .. " & Num(hi(1), 3) & _
         ", z " & Num(lo(2), 3) & " .. " & Num(hi(2), 3) & " m, 3 bodies (as the source)"
End Sub


' Which of the fan's bodies this is, by where it lies (as id_fan.bas).
Private Function IdfKind(ByVal body As Object) As String
    Dim bx As Variant
    bx = body.GetBodyBox
    If bx(4) > IDF_VOL_B + 0.5 * (IDF_Y_BOX - IDF_VOL_B) Then
        IdfKind = "inlet"
    ElseIf bx(0) < -(IDF_R_MRF + 0.04) Then
        IdfKind = "volute"
    Else
        IdfKind = "rotor"
    End If
End Function


' Shows only the fan's `kind` body in view v (IView.Bodies, a multibody part).
Private Sub ShowOnlyBody(v As SldWorks.View, ByVal kind As String)
    Dim pd As SldWorks.PartDoc, bodies As Variant, i As Long, n As Long
    Dim sel(0) As Object
    Set pd = swPart
    bodies = pd.GetBodies2(swSolidBody, True)
    For i = 0 To UBound(bodies)
        If IdfKind(bodies(i)) = kind Then
            Set sel(0) = bodies(i)
            n = n + 1
        End If
    Next i
    If n <> 1 Then Fail "found " & n & " " & kind & " bodies in the part, expected 1."
    v.Bodies = sel
    swModel.ForceRebuild3 False
    Note v.Name & ": shows the " & kind & " body only"
End Sub


Private Sub CheckPartBox(doc As SldWorks.ModelDoc2)
    If equip = "id_fan" Then
        CheckIdFanBox doc
        Exit Sub
    ElseIf equip = "kiln_inlet_chamber" Then
        CheckKicBox doc
        Exit Sub
    ElseIf equip = "cooler" Then
        CheckCoolerBox doc
        Exit Sub
    ElseIf equip = "kiln" Then
        CheckKilnBox doc
        Exit Sub
    ElseIf equip = "C1_twin" Then
        CheckTwinBox doc
        Exit Sub
    ElseIf equip = "calciner" Then
        CheckCalcinerBox doc
        Exit Sub
    ElseIf equip <> "C1" Then
        CheckVoluteBox doc
        Exit Sub
    End If
    ' C1 (since 16 Nov 2026 a volute): the duct's face furthest out at
    ' -x, the drop leg at +x, the duct's outer wall at +y, the scroll's
    ' end at -y; true extremes (GetExtremePoint), the spline's as on C4.
    Dim pd As SldWorks.PartDoc
    Dim bodies As Variant, b As SldWorks.Body2, box As Variant
    Dim want(5) As Double, i As Long, nm As Variant
    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    Set pd = doc
    bodies = pd.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail partPath & " has no solid body."
    If UBound(bodies) <> 0 Then Fail partPath & " has " & (UBound(bodies) + 1) & " bodies, not 1."
    Set b = bodies(0)
    box = ExactBox(b)
    want(0) = C1_FACE_BOT_X
    want(1) = -C1_Y_INNER                     ' the scroll closes on r = R + tongue
    want(2) = 0#
    want(3) = C1_LEG_X + 0.5 * C1_D_VORTEX
    want(4) = C1_Y_OUTER
    want(5) = C1_TOP
    For i = 0 To 5
        If i = 1 Then
            If box(1) > want(1) + 0.01 Or box(1) < want(1) - 0.2 Then
                Fail partPath & ": y min is " & Num(box(1), 3) & " m, today's C1 scroll ends at " & Num(want(1), 3) & _
                     " (a spline may bulge 0.2 m past it) -- rebuild it with cyclone.bas (gas_only)."
            End If
        ElseIf Abs(box(i) - want(i)) > 0.01 Then
            Fail partPath & ": " & nm(i) & " is " & Num(box(i), 3) & " m, today's C1 domain has " & Num(want(i), 3) & _
                 " -- rebuild it with cyclone.bas (gas_only: C1 without its riser)."
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
    ok = swDraw.SetupSheet5(sh.GetName, swDwgPaperA1size, swDwgTemplateNone, 1#, scaleD, _
                            True, "", PAPER_W, PAPER_H, "Default", True)
    If Not ok Then Note "WARNING: SetupSheet5 returned False."
    If Not ok Then sh.SetProperties2 swDwgPaperA1size, swDwgTemplateNone, 1#, scaleD, True, PAPER_W, PAPER_H, True
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
    Note "sheet: A1, 1:" & Fmt(scaleD) & ", first angle, ISO"
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
    If equip = "C1" Then
        MakeViewsC1
    ElseIf equip = "C1_twin" Then
        MakeViewsTwin
    ElseIf equip = "calciner" Then
        MakeViewsCalciner
    ElseIf equip = "kiln" Then
        MakeViewsKiln
    ElseIf equip = "cooler" Then
        MakeViewsCooler
    ElseIf equip = "id_fan" Then
        MakeViewsIdFan
    ElseIf equip = "kiln_inlet_chamber" Then
        MakeViewsKic
    Else
        MakeViewsVolute
    End If
End Sub


' A volute cyclone (C4, C5), laid out as C1's sheet at 1:100: the top view
' (x right, y up; the volute's duct on its +y side), A-A over it, cut
' along y = 0 through the axis, the left view right of A-A, detail B of
' the vortex finder's mouth, on the -x side (the volute is on +x).
Private Sub MakeViewsVolute()
    Dim R As Double, rx As Double, xa As Double, xb As Double
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim tries As Long, nSeen As Long, nFit As Long
    R = 0.5 * vD: rx = 0.5 * vDv

    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, TOP_X, TOP_Y, "top")
    HiddenLinesVisible vTop
    LogMap vTop, "top", scaleD

    ' A-A: along y = 0 through the whole cyclone and its outlet; the
    ' direction it is drawn in sets which way SolidWorks looks (found by
    ' trying: it must show x right, z up)
    xa = -(R + 1#): xb = vExitX + 1#
    For tries = 0 To 1
        If tries = 0 Then
            ToSheet vTop, xb, 0#, vHeight, ax, ay
            ToSheet vTop, xa, 0#, vHeight, qx, qy
        Else
            ToSheet vTop, xa, 0#, vHeight, ax, ay
            ToSheet vTop, xb, 0#, vHeight, qx, qy
        End If
        Set vSec = SectionFrom(vTop, ax, ay, qx, qy, "A", 0.5 * (ax + qx), SEC_Y)
        If Maps(vSec, 1, 0, 0, 0, 0, 1) Then Exit For
        Note "section A-A, line drawn " & IIf(tries = 0, "right to left", "left to right") & " looks wrong: " & MapText(vSec)
        If tries = 1 Then Fail "section A-A shows x right, z up in neither direction: " & MapText(vSec)
        DeleteView vSec
    Next tries
    If FindEdge(vSec, "vline", -rx, 0#, vHeight - 0.5 * vLv, -rx, 0#, nSeen, nFit) Is Nothing _
       Or foundDist > SEL_TOL Then Fail "section A-A is not cut: no vortex finder bore among its " & nSeen & " edges."
    Note "views: top " & vTop.Name & ", A-A " & vSec.Name
    LogMap vSec, "A-A", scaleD

    swDraw.EditSheet
    Set vLeft = OrientedView(0, -1, 0, 0, 0, 1, LEFT_X, SEC_Y, "left")
    AlignHeight vLeft, vSec
    HiddenLinesVisible vLeft

    Set vDet = DetailFrom(vSec, -(R - 0.35), vHeight - vLv + 0.3, 1.25, "B")
    Note "views: left " & vLeft.Name & ", detail B " & vDet.Name
    LogMap vLeft, "left", scaleD: LogMap vDet, "detail B", detailD
End Sub


' The calciner at 1:200: the plan (x right, y up) at the bottom, A-A over
' it (y = 0: the vessel, the throat, the neck and both legs, the meal
' pipes), the left view right of A-A (the fuel pipes, the tertiary air
' duct's face) and detail B of the meal and tertiary air inlets.
Private Sub MakeViewsCalciner()
    Dim R As Double, xa As Double, xb As Double
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim tries As Long, nSeen As Long, nFit As Long
    R = 0.5 * CAL_D_VESSEL

    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, CAL_TOP_X, CAL_TOP_Y, "top")
    HiddenLinesVisible vTop
    LogMap vTop, "top", scaleD

    xa = -(0.5 * CAL_WIDTH + 1#): xb = 0.5 * CAL_WIDTH + 1#
    For tries = 0 To 1
        If tries = 0 Then
            ToSheet vTop, xb, 0#, CAL_Z_ROOF, ax, ay
            ToSheet vTop, xa, 0#, CAL_Z_ROOF, qx, qy
        Else
            ToSheet vTop, xa, 0#, CAL_Z_ROOF, ax, ay
            ToSheet vTop, xb, 0#, CAL_Z_ROOF, qx, qy
        End If
        Set vSec = SectionFrom(vTop, ax, ay, qx, qy, "A", 0.5 * (ax + qx), CAL_SEC_Y)
        If Maps(vSec, 1, 0, 0, 0, 0, 1) Then Exit For
        Note "section A-A, line drawn " & IIf(tries = 0, "right to left", "left to right") & " looks wrong: " & MapText(vSec)
        If tries = 1 Then Fail "section A-A shows x right, z up in neither direction: " & MapText(vSec)
        DeleteView vSec
    Next tries
    ' SectionFrom leaves the section on the sheet's scale, and this sheet's
    ' label then went without its scale (C1, C4, C5 show it): set it as
    ' every OrientedView does; the same 1:scaleD, so nothing moves.
    vSec.ScaleDecimal = 1# / scaleD
    swModel.ForceRebuild3 False
    Note "section A-A scale set to 1:" & Fmt(scaleD)
    If FindEdge(vSec, "vline", -R, 0#, 20#, -R, 0#, nSeen, nFit) Is Nothing _
       Or foundDist > SEL_TOL Then Fail "section A-A is not cut: no vessel wall among its " & nSeen & " edges."
    Note "views: top " & vTop.Name & ", A-A " & vSec.Name
    LogMap vSec, "A-A", scaleD

    ' the front view, seen from -y: the channel and the Y's arms stand in
    ' front of the vessel (y = -CAL_Y_OFF), which A-A (y = 0, looking at
    ' the half behind it) does not show
    swDraw.EditSheet
    Set vFront = OrientedView(1, 0, 0, 0, 0, 1, CAL_FRONT_X, CAL_SEC_Y, "front")
    AlignHeight vFront, vSec
    LogMap vFront, "front", scaleD

    swDraw.EditSheet
    Set vLeft = OrientedView(0, -1, 0, 0, 0, 1, CAL_LEFT_X, CAL_SEC_Y, "left")
    AlignHeight vLeft, vSec
    HiddenLinesVisible vLeft

    Set vDet = DetailFrom(vSec, 4.2, 10.4, 3.2, "B")
    Note "views: front " & vFront.Name & ", left " & vLeft.Name & ", detail B " & vDet.Name
    LogMap vLeft, "left", scaleD: LogMap vDet, "detail B", detailD
End Sub


' The kiln (1:200): the side view, the tube's axis along the sheet (sheet
' right = model z, the back end at the left, up = model x), and the end view
' at 1:50 under it (x right, y up, looking along the axis: the true circle).
' The end view's scale is set through scaleD for its own creation only.
Private Sub MakeViewsKiln()
    Set vFront = OrientedView(0, 0, 1, 1, 0, 0, KIL_SIDE_X, KIL_SIDE_Y, "side")
    LogMap vFront, "side", scaleD

    swDraw.EditSheet
    scaleD = detailD
    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, KIL_END_X, KIL_END_Y, "end")
    LogMap vTop, "end", scaleD
    scaleD = 200#
    Note "views: side " & vFront.Name & ", end " & vTop.Name
End Sub


' The cooler (1:100), a box: the side view on top (x right, z up), the plan
' under it (the roof: x right, y up), the floor seen from below under that
' (x right, y down: the floor's strip lines), and the end view from the hot
' end at 1:50 (y to the left of the box's x = 0 face seen from -x: z up).
' The end view's scale is set through scaleD for its own creation only.
Private Sub MakeViewsCooler()
    Set vFront = OrientedView(1, 0, 0, 0, 0, 1, COO_X, COO_SIDE_Y, "side")
    LogMap vFront, "side", scaleD
    swDraw.EditSheet
    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, COO_X, COO_PLAN_Y, "plan")
    HiddenLinesVisible vTop
    LogMap vTop, "plan", scaleD
    swDraw.EditSheet
    Set vLeft = OrientedView(1, 0, 0, 0, -1, 0, COO_X, COO_FLOOR_Y, "floor")
    LogMap vLeft, "floor", scaleD
    swDraw.EditSheet
    scaleD = detailD
    Set vSide = OrientedView(0, -1, 0, 0, 0, 1, COO_END_X, COO_END_Y, "end")
    LogMap vSide, "end", scaleD
    scaleD = 100#
    Note "views: side " & vFront.Name & ", plan " & vTop.Name & ", floor " & vLeft.Name & ", end " & vSide.Name
End Sub


' The kiln inlet chamber (1:50), first-angle projection: the side view (x
' right, z up: the ramp in profile), the plan under it (the roof: x right,
' y up; hidden lines on show the mouth and the ramp), and to the LEFT of the
' side view the view from the +x wall, the kiln's wall (y right, z up: the
' mouth is a true circle).
Private Sub MakeViewsKic()
    Set vFront = OrientedView(1, 0, 0, 0, 0, 1, KIC_SIDE_X, KIC_SIDE_Y, "side")
    LogMap vFront, "side", scaleD
    swDraw.EditSheet
    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, KIC_SIDE_X, KIC_PLAN_Y, "plan")
    HiddenLinesVisible vTop
    LogMap vTop, "plan", scaleD
    swDraw.EditSheet
    Set vSide = OrientedView(0, 1, 0, 0, 0, 1, KIC_END_X, KIC_END_Y, "end")
    LogMap vSide, "end", scaleD
    Note "views: side " & vFront.Name & ", plan " & vTop.Name & ", end (from +x) " & vSide.Name
End Sub


'' The ID fan (1:50), first-angle projection: the front view from the drive
' side (-y: x right, z up; the volute's spiral, the discharge to -x, the
' hub), the plan under it (x right, y up: the widths), the view from +x left
' of it (the inlet box's face); right of the front, the rotating zone alone
' at 1:20, seen from the inlet side (+y: -x right, z up; the eye, the shroud
' and the blades where they meet it) and from +x (y right, z up: b1, b2).
Private Sub MakeViewsIdFan()
    Set vFront = OrientedView(1, 0, 0, 0, 0, 1, IDF_FRONT_X, IDF_FRONT_Y, "front")
    LogMap vFront, "front (from -y)", scaleD
    swDraw.EditSheet
    Set vTop = OrientedView(1, 0, 0, 0, 1, 0, IDF_FRONT_X, IDF_PLAN_Y, "plan")
    LogMap vTop, "plan", scaleD
    swDraw.EditSheet
    Set vSide = OrientedView(0, 1, 0, 0, 0, 1, IDF_SIDE_X, IDF_FRONT_Y, "side")
    LogMap vSide, "side (from +x)", scaleD
    swDraw.EditSheet
    scaleD = detailD
    Set vLeft = OrientedView(-1, 0, 0, 0, 0, 1, IDF_ROT_X, IDF_ROT_Y, "rotor")
    ShowOnlyBody vLeft, "rotor"
    PlaceOutlineAt vLeft, IDF_ROT_X, IDF_ROT_Y
    LogMap vLeft, "rotor (from +y)", scaleD
    swDraw.EditSheet
    Set vDet = OrientedView(0, 1, 0, 0, 0, 1, IDF_ROTS_X, IDF_ROT_Y, "rotor side")
    ShowOnlyBody vDet, "rotor"
    PlaceOutlineAt vDet, IDF_ROTS_X, IDF_ROT_Y
    LogMap vDet, "rotor side (from +x)", scaleD
    scaleD = 50#
    Note "views: front " & vFront.Name & ", plan " & vTop.Name & ", side " & vSide.Name & ", rotor " & vLeft.Name & _
         ", rotor side " & vDet.Name
End Sub


Private Sub MakeViewsC1()

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
    Set vSec = SectionFrom(vTop, qx, qy, ax, ay, "A", 0.5 * (qx + ax), SEC_Y)
    If Not Maps(vSec, 1, 0, 0, 0, 0, 1) Then Fail "section A-A does not show x right, z up: " & MapText(vSec)
    ' Cut, not just projected (run 5): the vortex finder's bore, inside
    ' the barrel below the roof, shows only in a cut.
    Dim nSeen As Long, nFit As Long
    If FindEdge(vSec, "vline", -rx, 0#, C1_HEIGHT - 0.5 * C1_L_VORTEX, -rx, 0#, nSeen, nFit) Is Nothing _
       Or foundDist > SEL_TOL Then Fail "section A-A is not cut: no vortex finder bore among its " & nSeen & " edges."
    Note "views: top " & vTop.Name & ", A-A " & vSec.Name
    LogMap vTop, "top", scaleD: LogMap vSec, "A-A", scaleD

    ' Left view, right of A-A (first angle: seen from the left), from the
    ' part's named views like the top view -- selecting A-A by name to
    ' unfold it failed in run 3. Its height is lined up with A-A's.
    swDraw.EditSheet
    Set vLeft = OrientedView(0, -1, 0, 0, 0, 1, LEFT_X, SEC_Y, "left")
    AlignHeight vLeft, vSec
    HiddenLinesVisible vLeft

    ' Detail B: the vortex finder's mouth, from A-A, on the -x side (on
    ' +x the cut runs through the volute's scroll, as on C4).
    Set vDet = DetailFrom(vSec, -(R - 0.35), C1_HEIGHT - C1_L_VORTEX + 0.3, 1.25, "B")
    Note "views: left " & vLeft.Name & ", detail B " & vDet.Name
    LogMap vLeft, "left", scaleD: LogMap vDet, "detail B", detailD

End Sub


' The twin C1 (c1_twin.bas' solid): front view (x right, z up, R1 in
' front of the C1 axes), section A-A under it (a cut at TW_Z_CUT: the two
' barrels and the two branches, seen from above), the left view right of
' it (-y right) and detail C of R1's Y.
Private Sub MakeViewsTwin()
    Dim S2 As Double, R As Double
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim tries As Long, nSeen As Long, nFit As Long
    S2 = 0.5 * TW_S: R = TW_C1_R

    Set vFront = OrientedView(1, 0, 0, 0, 0, 1, TW_FRONT_X, TW_FRONT_Y, "front")
    HiddenLinesVisible vFront
    LogMap vFront, "front", scaleD

    ' A-A: a cutting line along x at z = TW_Z_CUT in the front view; the
    ' direction it is drawn in sets which way SolidWorks looks, found
    ' by trying (the wrong try is deleted)
    For tries = 0 To 1
        If tries = 0 Then
            ToSheet vFront, S2 + R + 1.5, 0#, TW_Z_CUT, ax, ay
            ToSheet vFront, -(S2 + R + 1.5), 0#, TW_Z_CUT, qx, qy
        Else
            ToSheet vFront, -(S2 + R + 1.5), 0#, TW_Z_CUT, ax, ay
            ToSheet vFront, S2 + R + 1.5, 0#, TW_Z_CUT, qx, qy
        End If
        Set vPlan = SectionFrom(vFront, ax, ay, qx, qy, "A", TW_FRONT_X, TW_PLAN_Y)
        If Maps(vPlan, 1, 0, 0, 0, 1, 0) Then Exit For
        Note "section A-A, line drawn " & IIf(tries = 0, "right to left", "left to right") & " looks wrong: " & MapText(vPlan)
        If tries = 1 Then Fail "section A-A shows x right, y up in neither direction: " & MapText(vPlan)
        DeleteView vPlan
    Next tries
    If FindEdge(vPlan, "circle", S2 + R, 0#, TW_Z_CUT, R, TW_Z_CUT, nSeen, nFit) Is Nothing _
       Or foundDist > SEL_TOL Then Fail "section A-A is not cut: no barrel circle among its " & nSeen & " edges."
    Note "views: front " & vFront.Name & ", A-A " & vPlan.Name
    LogMap vPlan, "A-A", scaleD

    swDraw.EditSheet
    Set vSide = OrientedView(0, -1, 0, 0, 0, 1, TW_SIDE_X, TW_FRONT_Y, "side")
    AlignHeight vSide, vFront
    HiddenLinesVisible vSide
    LogMap vSide, "side", scaleD

    ' detail C: R1's Y, from the front view
    ' (centred 0.75 m over R1's top, 3.0 m round: the Y's far corner is 2.96 m
    ' off it, the dust outlets' cones 3.1 m)
    Set vDetC = DetailFrom(vFront, 0#, TW_Z_SPLIT + 0.75, 3#, "C")
    Note "views: side " & vSide.Name & ", detail C " & vDetC.Name
    LogMap vDetC, "detail C", detailD
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
            v.ScaleDecimal = 1# / scaleD
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


' Moves a view so the centre of what it shows is at (px, py): a view showing
' one body of a multibody part keeps its Position on the whole part's box
' (the id_fan run: the rotor views landed 31 and 71 mm off), so the outline
' is read and the view moved by the difference.
Private Sub PlaceOutlineAt(v As SldWorks.View, ByVal px As Double, ByVal py As Double)
    Dim ol As Variant, p As Variant
    swModel.ForceRebuild3 False
    ol = v.GetOutline
    p = v.Position
    PlaceAt v, p(0) + px - 0.5 * (ol(0) + ol(2)), p(1) + py - 0.5 * (ol(1) + ol(3))
    ol = v.GetOutline
    Note v.Name & ": outline centre at (" & Num(500# * (ol(0) + ol(2)), 1) & ", " & Num(500# * (ol(1) + ol(3)), 1) & ") mm"
End Sub


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
        s = s & Mid("xyz", i + 1, 1) & "->(" & Num((a - ox) * scaleD, 2) & "," & Num((b - oy) * scaleD, 2) & ") "
    Next i
    MapText = s
End Function


Private Function SectionFrom(parent As SldWorks.View, ByVal ax As Double, ByVal ay As Double, _
                             ByVal qx As Double, ByVal qy As Double, ByVal label As String, _
                             ByVal px As Double, ByVal py As Double) As SldWorks.View
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
    Set v = swDraw.CreateSectionViewAt5(px, py, 0#, label, 0, Nothing, 0#)
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
    Set v = swDraw.CreateDetailViewAt4(detX, detY, 0#, swDetViewSTANDARD, 1#, detailD, label, _
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
    ' tangent edges shown, not left to the session's default: C1's outlet
    ' pipe meets its bend in a tangent edge that outlet_rise is measured to
    ' (16 Nov: a session that hid them lost the dimension and the sheets'
    ' hidden lines); both read back into the log
    v.SetDisplayTangentEdges2 swTangentEdgesVisible
    If Err.Number <> 0 Then Note "WARNING: " & v.Name & ": could not show tangent edges (" & Err.Description & ")."
    Err.Clear
    Note v.Name & ": display mode " & v.GetDisplayMode2 & ", tangent edges " & v.GetDisplayTangentEdges2
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
    ' (a direction along the view's own line of sight projects to a point, and
    ' noise must not pass for a direction: both unit vectors must keep most of
    ' their length, 1 m / scale on the sheet)
    Maps = (ax > 0.9 * Sqr(ax * ax + ay * ay)) And (qy > 0.9 * Sqr(qx * qx + qy * qy)) _
           And (Sqr(ax * ax + ay * ay) > 0.5 / scaleD) And (Sqr(qx * qx + qy * qy) > 0.5 / scaleD)
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
    If equip = "C1" Then
        DimensionC1
    ElseIf equip = "C1_twin" Then
        DimensionTwin
    ElseIf equip = "calciner" Then
        DimensionCalciner
    ElseIf equip = "kiln" Then
        DimensionKiln
    ElseIf equip = "cooler" Then
        DimensionCooler
    ElseIf equip = "id_fan" Then
        DimensionIdFan
    ElseIf equip = "kiln_inlet_chamber" Then
        DimensionKic
    Else
        DimensionVolute
    End If
End Sub


' A volute cyclone's reference dimensions, each between edges the solid
' has (C1's scheme). A circle seen edge-on is measured whole, so the
' barrel's diameter is read at the cone's top, a full circle (the roof
' circle is cut by the volute); between two circles SolidWorks measures
' centre to centre, here along z or x. The spiral is a spline and is not
' dimensioned.
Private Sub DimensionVolute()
    Dim R As Double, rx As Double, rd As Double, t As Double
    Dim zr As Double, hc As Double, zv As Double, rT As Double, rS As Double, ym As Double
    R = 0.5 * vD: rx = 0.5 * vDv: rd = 0.5 * vDd: t = vWall
    zr = vHeight: hc = vHc: zv = zr - vLv
    rT = R + vTongue: rS = rT + vW: ym = 0.5 * (rT + rS)

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    ' left view: the circular edges seen edge-on (y < 0 half, clear of the volute)
    DimEdges "D_barrel", vD, vLeft, _
        "circle", 0, -R, hc, R, hc, _
        "", 0, 0, 0, 0, 0, _
        0, -0.35 * R, hc + 0.9
    DimEdges "D_dust", vDd, vLeft, _
        "circle", 0, -rd, 0, rd, 0, _
        "", 0, 0, 0, 0, 0, _
        0, -rd - 0.6, -0.9
    DimEdges "H_cone", vHc, vLeft, _
        "circle", 0, -rd, 0, rd, 0, _
        "circle", 0, -R, hc, R, hc, _
        0, -R - 1#, 0.5 * hc
    DimEdges "H_barrel", vHb, vLeft, _
        "circle", 0, -R, hc, R, hc, _
        "circle", 0, -R, zr, R, zr, _
        0, -R - 1#, 0.5 * (hc + zr)
    DimEdges "height", vHeight, vLeft, _
        "circle", 0, -rd, 0, rd, 0, _
        "circle", 0, -R, zr, R, zr, _
        0, -R - 2.4, 0.5 * zr
    ' the outlet run's axis above the roof: the roof ring's circle and the
    ' bend's end circle (face-on from -x), centre to centre
    DimEdges "outlet_axis", vRise + vBendR, vLeft, _
        "circle", 0, 0, zr, R, zr, _
        "circle", vBendR, 0, vZleg, rx, vZleg, _
        0, -R - 3.8, zr + 0.5 * (vRise + vBendR), "v"

    ' the volute's duct end face, seen face-on from -x: its height
    DimEdges "H_inlet", vH, vLeft, _
        "hline", -vLduct, ym, zr, 0, zr, _
        "hline", -vLduct, ym, zr - vH, 0, zr - vH, _
        0, rS + 1.4, zr - 0.5 * vH

    ' A-A (the plane y = 0), on the -x side (the volute is on +x)
    DimEdges "D_vortex", vDv, vSec, _
        "vline", -rx, 0, zr + 1.5, -rx, 0, _
        "vline", rx, 0, zr + 1.5, rx, 0, _
        -1#, 0, zr + 2.2
    DimEdges "L_vortex", vLv, vSec, _
        "hline", -0.5 * (rx + t + R), 0, zr, 0, zr, _
        "hline", -(rx + 0.5 * t), 0, zv, 0, zv, _
        -R - 1.8, 0, zr - 0.5 * vLv

    ' top view: the duct's two straight sides, true width
    DimEdges "W_inlet", vW, vTop, _
        "hline", -0.5 * vLduct, rT, zr, 0, zr, _
        "hline", -0.5 * vLduct, rS, zr, 0, zr, _
        -vLduct + 0.9, ym, zr
    ' the gas outlet face's distance from the barrel axis: the pipe's circle
    ' over the roof and the exit face (edge-on), centre to centre
    DimEdges "exit_x", vExitX, vTop, _
        "circle", 0, 0, zr, rx + t, zr, _
        "circle", vExitX, 0, vZleg, rx, vZleg, _
        0.5 * vExitX, -rx - 1.4, vZleg, "h"

    ' detail B: the vortex finder's wall at its mouth
    DimEdges "vortex_wall", vWall, vDet, _
        "hline", -(rx + 0.5 * t), 0, zv, 0, zv, _
        "", 0, 0, 0, 0, 0, _
        -(rx + 0.5 * t), 0, zv - 0.25

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The cooler's reference dimensions, each between edges the box has: the
' length and the hood opening in the plan (roof edges x = 0, x = hood end,
' x = L), the segment in the floor view (floor strip lines, seen from below),
' the width and the height from the near end face in the end view. Which of
' the two end faces is the near one is found, not assumed.
Private Sub DimensionCooler()
    Dim hw As Double, xe As Double, nSeen As Long, nFit As Long
    hw = 0.5 * COO_W

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    xe = 0#
    If FindEdge(vSide, "line", 0#, 0#, COO_H, 0, 0, nSeen, nFit) Is Nothing Or foundDist > SEL_TOL Then xe = COO_L
    Note "end view: the near end face is at x = " & Num(xe, 3) & " m"

    DimEdges "L_cool", COO_L, vTop, _
        "line", 0, 0, COO_H, 0, 0, _
        "line", COO_L, 0, COO_H, 0, 0, _
        0.5 * COO_L, -hw - 2.4, COO_H
    DimEdges "hood", COO_HOOD_L, vTop, _
        "line", 0, 0, COO_H, 0, 0, _
        "line", COO_HOOD_L, 0, COO_H, 0, 0, _
        0.5 * COO_HOOD_L, hw + 1.6, COO_H
    DimEdges "segment", COO_SEG_L, vLeft, _
        "line", 0, 0, 0, 0, 0, _
        "line", COO_SEG_L, 0, 0, 0, 0, _
        0.5 * COO_SEG_L, hw + 1.6, 0
    DimEdges "w_cool", COO_W, vSide, _
        "line", xe, 0, COO_H, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        xe, 0, COO_H + 2.4
    DimEdges "H_cool", COO_H, vSide, _
        "line", xe, -hw, 0.5 * COO_H, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        xe, -hw - 3#, 0.5 * COO_H

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The ID fan's reference dimensions, each between edges the solid has: the
' outlet face's outer edge (plan: B) and its near edge (front: the height,
' the face is normal to the discharge, 45 deg up);
' the inlet box face's edges (side view: height, depth); on the rotor alone
' the eye's and the tip's circles (D1, D2) and the axial offsets of the
' rim's top circle from the hub's (b2: circle centres on the axis, the
' horizontal distance in the side view). b1 is listed only: the shroud rises
' from the eye (b1) to the tip (b2 > b1), so the eye's circle is hidden
' behind the rim in every outside view (the id_fan run: MISSING).
Private Sub DimensionIdFan()
    Dim xm As Double, zm As Double, c45 As Double
    xm = 0.5 * (IDF_E_TOP_X + IDF_E_LOW_X): zm = 0.5 * (IDF_E_TOP_Z + IDF_E_LOW_Z)
    c45 = 0.70710678

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    DimEdges "B", IDF_VOL_B, vTop, _
        "line", IDF_E_TOP_X, 0.5 * IDF_VOL_B, IDF_E_TOP_Z, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        IDF_X_MIN - 0.8, 0.5 * IDF_VOL_B, IDF_E_TOP_Z
    ' (the gas-out arrow runs from the face's middle: the text slides 0.5 m
    ' along the face towards its outer edge, its 0.84 m inside the 1.9 m;
    ' 16 Nov sheet check)
    DimEdges "h_stub", Sqr((IDF_E_TOP_X - IDF_E_LOW_X) ^ 2 + (IDF_E_TOP_Z - IDF_E_LOW_Z) ^ 2), vFront, _
        "line", xm, 0, zm, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        xm + 1.2 * IDF_DIS_DX + 0.5 * (IDF_E_TOP_X - IDF_E_LOW_X) / Sqr((IDF_E_TOP_X - IDF_E_LOW_X) ^ 2 + (IDF_E_TOP_Z - IDF_E_LOW_Z) ^ 2), 0, _
        zm + 1.2 * IDF_DIS_DZ + 0.5 * (IDF_E_TOP_Z - IDF_E_LOW_Z) / Sqr((IDF_E_TOP_X - IDF_E_LOW_X) ^ 2 + (IDF_E_TOP_Z - IDF_E_LOW_Z) ^ 2)
    DimEdges "H_box", IDF_BOX_H, vSide, _
        "line", IDF_BOX_REACH, IDF_Y_BOX + IDF_BOX_DEPTH, 0, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        IDF_BOX_REACH, IDF_Y_BOX + IDF_BOX_DEPTH + 1.2, 0
    DimEdges "depth_box", IDF_BOX_DEPTH, vSide, _
        "line", IDF_BOX_REACH, IDF_Y_BOX + 0.5 * IDF_BOX_DEPTH, 0.5 * IDF_BOX_H, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        IDF_BOX_REACH, IDF_Y_BOX + 0.5 * IDF_BOX_DEPTH, 0.5 * IDF_BOX_H + 1.2
    DimEdges "D2", 2# * IDF_R2, vLeft, _
        "circle", c45 * IDF_R2, IDF_B2, c45 * IDF_R2, IDF_R2, 0, _
        "", 0, 0, 0, 0, 0, _
        -(IDF_R_MRF + 0.3), IDF_B2, IDF_R_MRF + 0.3
    DimEdges "D1", 2# * IDF_R1, vLeft, _
        "circle", c45 * IDF_R1, IDF_B1, -c45 * IDF_R1, IDF_R1, 0, _
        "", 0, 0, 0, 0, 0, _
        -(IDF_R_MRF + 0.3), IDF_B1, -(IDF_R_MRF + 0.3)
    DimEdges "b2", IDF_B2, vDet, _
        "circle", 0, 0, IDF_R_MRF, IDF_R_MRF, 0, _
        "circle", 0, IDF_B2, IDF_R_MRF, IDF_R_MRF, 0, _
        0, 0.5 * IDF_B2, IDF_R_MRF + 0.25, "h"

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The kiln inlet chamber's reference dimensions, each between edges the solid
' has: the plan's side (the roof edge in the side view, the +x wall's top edge
' in the plan), the kiln's wall from the ramp's foot to the roof (a vertical
' edge in the side view), the throat's outlet circle (plan, a true circle at
' the disc's top), the kiln mouth's circle (view from +x, a true circle) and
' the ramp's slope (between the ramp's edge and the roof's, side view). The
' near side wall (y = -a or +a) is found, not assumed.
Private Sub DimensionKic()
    Dim a As Double, ys As Double, zr As Double
    a = 0.5 * KIC_A
    zr = KIC_H

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    ys = -a
    If FindEdge(vFront, "line", 0#, ys, zr, 0, 0, 0, 0) Is Nothing Or foundDist > SEL_TOL Then ys = a
    Note "side view: the near wall is at y = " & Num(ys, 3) & " m"

    ' (text off the middle, where the gas-out arrow rises; 16 Nov sheet check)
    DimEdges "a_plan", KIC_A, vFront, _
        "line", 0, ys, zr, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        -0.3 * a, ys, zr + 1.8
    DimEdges "a_plan", KIC_A, vTop, _
        "line", a, 0, zr, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        a + 1.8, 0, zr
    DimEdges "h_wall", KIC_H - KIC_H_LIP, vFront, _
        "line", a, ys, 0.5 * (KIC_H + KIC_H_LIP), 0, 0, _
        "", 0, 0, 0, 0, 0, _
        a + 1.8, ys, KIC_H_LIP + 1#                 ' text low on the line: the kiln-gas arrow crosses it higher up (16 Nov sheet check)
    DimEdges "ramp_deg", KIC_RAMP_DEG, vFront, _
        "line", 0, ys, 0.5 * (zr + KIC_H_LIP), 0, 0, _
        "line", 0, ys, zr, 0, 0, _
        -1#, ys, zr - 0.9
    DimEdges "D_throat", KIC_D_THROAT, vTop, _
        "circle", 0, 0, zr + KIC_STUB, 0.5 * KIC_D_THROAT, zr + KIC_STUB, _
        "", 0, 0, 0, 0, 0, _
        0.5 * KIC_D_THROAT + 1.2, 0.5 * KIC_D_THROAT + 0.8, zr + KIC_STUB
    DimEdges "D_mouth", KIC_D_MOUTH, vSide, _
        "circle", a, 0, 0.5 * KIC_A, 0.5 * KIC_D_MOUTH, 0.5 * KIC_A, _
        "", 0, 0, 0, 0, 0, _
        0.5 * KIC_D_MOUTH + 1.4, 0.5 * KIC_D_MOUTH + 0.6, 0.5 * KIC_A

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The kiln's two reference dimensions, each between edges the solid has:
' the diameter from the end face's circle (end view, a true circle), the
' length between the two end faces seen edge-on (side view, circle to
' circle: the dimension is along the axis). The slope and the zone split
' have no edge in the solid: the table only.
Private Sub DimensionKiln()
    Dim R As Double
    R = 0.5 * KIL_D

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    ' the hood end's circle: in the end view it hides the back end's behind it
    DimEdges "D_kiln", KIL_D, vTop, _
        "circle", 0, 0, KIL_L, R, KIL_L, _
        "", 0, 0, 0, 0, 0, _
        R + 2.2, R + 1#, 0
    DimEdges "L_kiln", KIL_L, vFront, _
        "circle", 0, 0, 0, R, 0, _
        "circle", 0, 0, KIL_L, R, KIL_L, _
        -R - 3.2, 0, 0.5 * KIL_L

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The calciner's reference dimensions, each between edges the solid has.
' Left view (seen from -x, +y to the left): the throat, cone and cylinder
' by their circular edges seen edge-on, the legs' open ends, the neck, the
' fuel pipe's end face; A-A: the width over the legs; plan: the tertiary
' air duct's face and the meal pipe's end face (circles) and the duct's
' place, centre to centre against the roof circle.
Private Sub DimensionCalciner()
    Dim R As Double, rt As Double, rl As Double, rta As Double
    Dim zt As Double, zc As Double, zr As Double, xl As Double, ze As Double
    R = 0.5 * CAL_D_VESSEL: rt = 0.5 * CAL_D_THROAT: rl = 0.5 * CAL_D_LEG
    rta = 0.5 * CAL_TA_D
    zt = CAL_L_THROAT: zc = CAL_Z_CONE: zr = CAL_Z_ROOF: xl = CAL_X_LEG: ze = CAL_Z_END

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    ' left view. The roof circle is cut away at its front by the neck's
    ' first piece (it pierces the roof there), so its back is picked.
    ' (text right of the extension line, not on it; 16 Nov sheet check)
    DimEdges "D_throat", CAL_D_THROAT, vLeft, _
        "circle", 0, -rt, 0, rt, 0, _
        "", 0, 0, 0, 0, 0, _
        0, -rt - 2.2, -2.4
    DimEdges "L_throat", CAL_L_THROAT, vLeft, _
        "circle", 0, -rt, 0, rt, 0, _
        "circle", 0, -rt, zt, rt, zt, _
        0, -R - 2.2, 0.5 * zt
    DimEdges "H_cone", CAL_H_CONE, vLeft, _
        "circle", 0, -rt, zt, rt, zt, _
        "circle", 0, -R, zc, R, zc, _
        0, -R - 2.2, 0.5 * (zt + zc)
    DimEdges "H_cylinder", CAL_H_CYL, vLeft, _
        "circle", 0, -R, zc, R, zc, _
        "circle", 0, R, zr, R, zr, _
        0, -R - 4.4, 0.5 * (zc + zr)
    DimEdges "H_vessel", CAL_H_VESSEL, vLeft, _
        "circle", 0, -rt, zt, rt, zt, _
        "circle", 0, R, zr, R, zr, _
        0, -R - 6.6, 0.5 * (zt + zr)
    DimEdges "D_vessel", CAL_D_VESSEL, vLeft, _
        "circle", 0, -R, zc, R, zc, _
        "", 0, 0, 0, 0, 0, _
        0, R + 3.2, zc
    ' an arm's outlet face, seen square on from -x: the near one, at x = -xl
    DimEdges "D_leg", CAL_D_LEG, vLeft, _
        "circle", -xl, -CAL_Y_OFF - rl, ze, rl, ze, _
        "", 0, 0, 0, 0, 0, _
        -xl, -CAL_Y_OFF - rl - 2.4, ze - 1.4
    ' (the 283 mm face is 1.4 mm on the sheet, the text 2.9 m: placed 2.5 m out
    ' along the pipe's axis (cos 30, sin 30), past the air arrow, and 2.0 m to
    ' the side so it stands outside the extension lines; 16 Nov sheet check)
    DimEdges "D_fuel", CAL_FUEL_D, vLeft, _
        "circle", 0, CAL_FUEL_Y, CAL_FUEL_Z, 0.5 * CAL_FUEL_D, CAL_FUEL_Z, _
        "", 0, 0, 0, 0, 0, _
        0, CAL_FUEL_Y + 2.5 * Sqr(3#) * 0.5 - 2# * 0.5, CAL_FUEL_Z + 2.5 * 0.5 + 2# * Sqr(3#) * 0.5

    ' plan: the tertiary air duct and the meal pipe
    ' (text 3.1 m long at 1:200, centred on its point: wholly under the duct
    ' and its air arrow, clear of section A-A's arrow; 16 Nov sheet check)
    DimEdges "D_TA", CAL_TA_D, vTop, _
        "circle", CAL_TA_X, CAL_TA_Y, CAL_TA_Z + rta, rta, CAL_TA_Z, _
        "", 0, 0, 0, 0, 0, _
        CAL_TA_X + 0.8, CAL_TA_Y - 3#, CAL_TA_Z
    DimEdges "ta_x", CAL_TA_X, vTop, _
        "circle", 0, R, zr, R, zr, _
        "circle", CAL_TA_X, CAL_TA_Y, CAL_TA_Z + rta, rta, CAL_TA_Z, _
        0.5 * CAL_TA_X, CAL_BOX_Y + 1.6, zr, "h"
    ' the meal pipe's end face is edge-on from the front (its normal lies
    ' in the x-z plane): a straight edge of the pipe's diameter. (In plan it
    ' is a tilted ellipse, which SolidWorks dimensioned as a radius.)
    ' Dimensioned in detail B (1:50; user decision, 16 Nov 2026), which
    ' shows the pipe's entry and had no dimension. The cut through the axis
    ' leaves the end face as a straight edge of the pipe's diameter, not a
    ' circle (run of 16 Nov: 5 edges, none a circle); its middle is the end
    ' face's centre. SolidWorks sets the dimension line parallel to that
    ' edge, offset by the text point's distance along the pipe's axis
    ' (cos 60, sin 60): 2.3 m of it put the line outside the detail's
    ' circle (run of 16 Nov), so the text sits 0.6 m out along the axis.
    DimEdges "D_feed", CAL_FEED_D, vDet, _
        "line", CAL_FEED_X, 0, CAL_FEED_Z, 0, 0, _
        "", 0, 0, 0, 0, 0, _
        CAL_FEED_X + 0.6 * 0.5, 0, CAL_FEED_Z + 0.6 * Sqr(3#) * 0.5

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


' The twin's reference dimensions, each between circles the solid has:
' R1's floor and its Y's two ends in the front view, the barrels' and
' branches' sections in A-A. Between two circles SolidWorks measures
' centre to centre; the text's place (outside both, beside them) makes
' it vertical or horizontal. Each is read back and checked.
Private Sub DimensionTwin()
    Dim S2 As Double, R As Double, b As Double, rb As Double, rr As Double
    Dim zc As Double, yb As Double, zf As Double, zt As Double, zb As Double
    S2 = 0.5 * TW_S: R = TW_C1_R: b = TW_BRANCH_HALF: rb = 0.5 * TW_BRANCH_D: rr = 0.5 * TW_R1_D
    zc = TW_Z_CUT: yb = TW_Y_BRANCH
    zf = TW_Z_SPLIT - TW_R1_STUB_L: zt = TW_Z_SPLIT: zb = TW_Z_BRANCH

    swDraw.EditSheet
    If swApp.GetApplySelectionFilter Then
        swApp.SetApplySelectionFilter False
        Note "selection: a selection filter was on; turned off for this run"
    End If
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.ClearSelection2 True

    ' front view
    DimEdges "R1_D", TW_R1_D, vFront, _
        "circle", rr, yb, zf, rr, zf, _
        "", 0, 0, 0, 0, 0, _
        0, yb, zf - 1.6
    ' the Y's height in detail C (1:50; user decision, 16 Nov 2026): in the
    ' front view it crowded the meal-out labels; the text inside the
    ' detail's circle (centre x 0, z TW_Z_SPLIT + 0.75, radius 3.0 m)
    DimEdges "y_rise", zb - zt, vDetC, _
        "circle", -rr, yb, zt, rr, zt, _
        "circle", b + rb, yb, zb, rb, zb, _
        2.8, yb, 0.5 * (zt + zb)

    ' A-A (from above: x right, y up)
    DimEdges "D_barrel", C1_D_BARREL, vPlan, _
        "circle", -S2 - R, 0, zc, R, zc, _
        "", 0, 0, 0, 0, 0, _
        -S2, -R - 1.4, zc
    DimEdges "spacing", TW_S, vPlan, _
        "circle", S2 + R, 0, zc, R, zc, _
        "circle", -S2 - R, 0, zc, R, zc, _
        0, R + 1.4, zc
    DimEdges "branch_D", TW_BRANCH_D, vPlan, _
        "circle", b + rb, yb, zc, rb, zc, _
        "", 0, 0, 0, 0, 0, _
        b + rb + 1.8, yb - rb - 1.2, zc
    DimEdges "branch_pitch", 2# * b, vPlan, _
        "circle", b + rb, yb, zc, rb, zc, _
        "circle", -b - rb, yb, zc, rb, zc, _
        0, yb - rb - 1.6, zc
    DimEdges "y_branch", -yb, vPlan, _
        "circle", S2 + R, 0, zc, R, zc, _
        "circle", b + rb, yb, zc, rb, zc, _
        S2 + R + 1.6, 0.5 * yb, zc, "v"

    Note "dimensions: " & nDimsOk & " of " & nDims & " verified"
End Sub


Private Sub DimensionC1()

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

    ' Left view (looking +x): the circular edges seen edge-on, picked on
    ' the y < 0 half. The barrel's diameter is read at the cone's top, a
    ' full circle: the roof circle is cut by the volute (as on C4).
    DimEdges "D_barrel", C1_D_BARREL, vLeft, _
        "circle", 0, -R, hc, R, hc, _
        "", 0, 0, 0, 0, 0, _
        0, -0.35 * R, hc + 0.9
    DimEdges "D_dust", C1_D_DUST, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "", 0, 0, 0, 0, 0, _
        0, -rd - 0.6, -0.9
    DimEdges "H_cone", C1_H_CONE, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "circle", 0, -R, hc, R, hc, _
        0, -R - 1#, 0.5 * hc
    DimEdges "H_barrel", C1_H_BARREL, vLeft, _
        "circle", 0, -R, hc, R, hc, _
        "circle", 0, -R, zr, R, zr, _
        0, -R - 1#, 0.5 * (hc + zr)
    DimEdges "height", C1_HEIGHT, vLeft, _
        "circle", 0, -0.5 * rd, 0, rd, 0, _
        "circle", 0, -R, zr, R, zr, _
        0, -R - 2.2, 0.5 * zr
    DimEdges "outlet_rise", C1_OUT_RISE, vLeft, _
        "circle", 0, -R, zr, R, zr, _
        "circle", 0, -0.5 * rx, zr + C1_OUT_RISE, rx, zr + C1_OUT_RISE, _
        0, -R - 1#, zr + 0.5 * C1_OUT_RISE
    ' the volute's duct end face, seen face-on from -x: its height
    DimEdges "H_inlet", C1_H_INLET, vLeft, _
        "hline", C1_FACE_BOT_X, ym, zr, 0, zr, _
        "hline", C1_FACE_BOT_X, ym, zr - C1_H_INLET, 0, zr - C1_H_INLET, _
        0, yo + 1.4, zr - 0.5 * C1_H_INLET

    ' Section A-A (the plane y = 0): the cut face's straight edges; the
    ' finder's on the -x side, clear of the scroll the cut runs through
    ' on +x.
    DimEdges "D_vortex", C1_D_VORTEX, vSec, _
        "vline", -rx, 0, zr + 1.5, -rx, 0, _
        "vline", rx, 0, zr + 1.5, rx, 0, _
        0, 0, zr + 2.2
    DimEdges "L_vortex", C1_L_VORTEX, vSec, _
        "hline", -0.5 * (rx + t + R), 0, zr, 0, zr, _
        "hline", -(rx + 0.5 * t), 0, zv, 0, zv, _
        -R - 1.8, 0, zv + 0.55            ' under the gas arrow at the duct's mid-height
    DimEdges "leg_x", C1_LEG_X, vSec, _
        "vline", -rx, 0, zr + 1#, -rx, 0, _
        "vline", C1_LEG_X - rx, 0, zr + 1#, C1_LEG_X - rx, 0, _
        0.5 * C1_LEG_X, 0, zr - 2.5

    ' Top view: the volute duct's two straight sides, true width. (The
    ' duct is level since 16 Nov 2026: its 0 deg slope is listed only.)
    DimEdges "W_inlet", C1_W_INLET, vTop, _
        "hline", 0.5 * C1_FACE_BOT_X, yi, zr, 0, zr, _
        "hline", 0.5 * C1_FACE_BOT_X, yo, zr, 0, zr, _
        C1_FACE_BOT_X + 0.9, ym, zr

    ' Detail B: the vortex finder's wall at its mouth.
    DimEdges "vortex_wall", C1_VORTEX_WALL, vDet, _
        "hline", -(rx + 0.5 * t), 0, zv, 0, zv, _
        "", 0, 0, 0, 0, 0, _
        -(rx + 0.5 * t), 0, zv - 0.25

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
        ByVal tx As Double, ByVal ty As Double, ByVal tz As Double, Optional ByVal orient As String = "")

    Dim st As String
    Dim dd As SldWorks.DisplayDimension
    Dim got As Double, isAngle As Boolean
    Dim sx As Double, sy As Double

    nDims = nDims + 1
    st = StatusOf(key)
    If st <> "Verified" And st <> "Estimated" Then Fail key & " is " & st & ": it may not be dimensioned."
    isAngle = (key = "inlet_slope" Or key = "ramp_deg")

    swModel.ClearSelection2 True
    If Not PickEdge(v, k1, x1, y1, z1, p11, p12, False, key & " edge 1") Then Exit Sub
    If k2 <> "" Then
        If Not PickEdge(v, k2, x2, y2, z2, p21, p22, True, key & " edge 2") Then Exit Sub
    End If

    ToSheet v, tx, ty, tz, sx, sy
    ' Between two circles' centres the plain dimension is the slant
    ' distance whichever side its text is on (run 1 of the twin: 7058
    ' for the 6843 asked), so orient "v" / "h" asks for the vertical /
    ' horizontal one.
    Select Case orient
    Case "v": Set dd = swModel.AddVerticalDimension2(sx, sy, 0#)
    Case "h": Set dd = swModel.AddHorizontalDimension2(sx, sy, 0#)
    Case Else: Set dd = swModel.AddDimension2(sx, sy, 0#)
    End Select
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

    ' an angle that is not whole shows 0.1 deg, as the table prints it
    ' (16 Nov sheet check: KIC's ramp printed 41 deg, the table 41.4237)
    If isAngle And Abs(want - CLng(want)) > 0.000000001 Then dd.SetPrecision3 1, -1, -1, -1

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
        If kind = "circle" Then ListCircles v
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
        ListCircles v
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


' Diagnostic: every circle or arc edge of view v (centre, axis, radius, ends).
Private Sub ListCircles(v As SldWorks.View)
    Dim ents As Variant, i As Long, ed As SldWorks.Edge, crv As SldWorks.Curve
    Dim cp As Variant, n As Long
    ents = v.GetVisibleEntities2(Nothing, 1)
    If IsEmpty(ents) Then Exit Sub
    For i = 0 To UBound(ents)
        Set ed = ents(i)
        Set crv = ed.GetCurve
        If crv.IsCircle Then
            cp = crv.CircleParams
            n = n + 1
            If n <= 40 Then
                Note "  circle " & n & " of " & v.Name & ": centre (" & Num(cp(0), 3) & ", " & Num(cp(1), 3) & ", " & Num(cp(2), 3) & _
                     ") axis (" & Num(cp(3), 2) & ", " & Num(cp(4), 2) & ", " & Num(cp(5), 2) & ") r " & Num(cp(6), 3)
            End If
        End If
    Next i
End Sub


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
    phase = "drawing the frame"
    DrawFrame
    phase = "drawing the title block"
    DrawTitle
    phase = "drawing the parameter table"
    DrawTable
    phase = "drawing the notes"
    DrawNotes
    phase = "drawing the flow arrows"
    DrawFlows
    phase = "drawing the centre lines"
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
    Cell COL_X0, 0.055, "Created by", "drawings.bas"
    Cell 0.711, 0.055, "Approved by", "-"
    Cell 0.771, 0.055, "Document type", "Engineering drawing"
    Cell COL_X0, 0.046, "Legal owner", "Karbon Zekasi"
    Cell 0.711, 0.046, "Technical reference", "plant_geometry.yaml"
    Cell 0.771, 0.046, "Document status", "draft, for approval"
    LabelPH COL_X0 + 0.0015, 0.0362, "Title, supplementary title", CAP_H
    LabelPH COL_X0 + 0.0015, 0.0335, TitleText(), 0.005
    LabelPH COL_X0 + 0.0015, 0.0255, "Inner (fluid) geometry, dimensioned - not a fabrication drawing", TEXT_H
    ' CI-<area>-<equipment>-001; the calciner is its own area, CA (16 Nov
    ' sheet review, item 9: it was numbered in the preheater's, PH)
    Cell 0.771, 0.037, "Identification number", "CI-" & AreaCode() & "-" & equip & "-001"
    CellS 0.771, 0.028, "Rev.", "A"
    CellS 0.781, 0.028, "Date of issue", Format(Date, "yyyy-mm-dd")
    CellS 0.806, 0.028, "Lang.", "EN"
    CellS 0.816, 0.028, "Sheet", "1/1"
    Cell COL_X0, 0.019, "Scale", "1:" & Fmt(scaleD) & IIf(equip = "id_fan", " (rotor 1:" & Fmt(detailD) & ")", IIf(equip = "kiln_inlet_chamber", "", IIf(equip = "kiln" Or equip = "cooler", " (end view 1:", " (" & IIf(equip = "C1_twin", "C", "B") & " 1:") & Fmt(detailD) & ")"))
    Cell 0.711, 0.019, "Unit", "mm"
    Cell 0.771, 0.019, "Projection", ""
    ProjectionSymbol 0.79, 0.0125
End Sub


' The process area in the document number: PH preheater (the cyclones,
' the twin C1, the ID fan), CA calciner, RK rotary kiln, CL clinker cooler.
Private Function AreaCode() As String
    Select Case equip
    Case "calciner": AreaCode = "CA"
    Case "kiln", "kiln_inlet_chamber": AreaCode = "RK"
    Case "cooler": AreaCode = "CL"
    Case Else: AreaCode = "PH"
    End Select
End Function


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


Private Function TitleText() As String
    Select Case equip
    Case "C1": TitleText = "PREHEATER CYCLONE C1"
    Case "C1_twin": TitleText = "TWIN CYCLONE C1 + RISER R1"
    Case "C4": TitleText = "CYCLONE C2 / C3 / C4 (SAME)"
    Case "C5": TitleText = "CYCLONE C5 (C4 x 6.50/6.30)"
    Case "calciner": TitleText = "ILC CALCINER, GOOSENECK AND Y"
    Case "kiln": TitleText = "ROTARY KILN TUBE"
    Case "cooler": TitleText = "GRATE COOLER (FLUID BOX)"
    Case "kiln_inlet_chamber": TitleText = "KILN INLET CHAMBER"
    Case "id_fan": TitleText = "PREHEATER ID FAN (1 PER STRING)"
    End Select
End Function


Private Sub DrawNotes()
    Dim y As Double
    y = 0.062 + 0.0045 * (nRows + 1) + 0.05
    UseLayer L_TEXT
    LabelPH COL_X0, y + 0.038, "NOTES", 0.0035
    LabelPH COL_X0, y + 0.032, "1. Inner (fluid) volume of the CFD model; not a fabrication drawing.", TEXT_H
    LabelPH COL_X0, y + 0.027, "   Shell, refractory, material, flanges, supports: Unknown (no source).", TEXT_H
    LabelPH COL_X0, y + 0.022, "2. 1234 = Verified (published).  1234 E = Estimated: FLS ratio,", TEXT_H
    LabelPH COL_X0, y + 0.017, "   literature, CFD decision, model parameter or derived from them.", TEXT_H
    If equip = "C1" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: z = 0 at the dust outlet, gas enters towards +x (cyclone.bas).", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. " & equip & ": 2 per string; values are for one.  All dimensions mm.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Source: geometry/plant_geometry.yaml, geometry/preheater/cyclone_C1.md", TEXT_H
    ElseIf equip = "cooler" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: x along the grate, x = 0 at the hot end (under the hood); z up from the grate.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. The clinker bed is a cell zone in the box, not a body; the vent outlet has no source.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Floor: " & Num(COO_SEGMENTS, 0) & " air segments (FLS); hood opening over the first two.  Dimensions mm.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/cooler/cooler.md", TEXT_H
    ElseIf equip = "id_fan" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: y along the axis (hub y = 0, gas in towards -y), x across, z up; turns +x to +z.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. Three CFD zones: rotor (MRF, blades cut hub to shroud), volute, inlet box + cone.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Rotor views: the rotating zone alone, 1:20. One fan per string.  Dimensions mm.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/fan/id_fan.md", TEXT_H
    ElseIf equip = "kiln_inlet_chamber" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: x from the calciner axis, the kiln's mouth on the +x wall; z up from the floor level.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. Flat roof at z = H with the calciner's throat; floor: one ramp, the kiln's wall to the far corner.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Meal enters in the solver (no inlet in the solid).  Dimensions mm; first-angle projection.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/kiln/kiln_inlet_chamber.md", TEXT_H
    ElseIf equip = "kiln" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: axis z; z = 0 at the back end (kiln inlet chamber), hood end at z = L.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. The slope (table) is installed, not built into the solid.  Dimensions mm.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Transition / burning split: a model parameter, table only.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/kiln/kiln.md", TEXT_H
    ElseIf equip = "calciner" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: z = 0 at the throat's foot (kiln gas inlet); tertiary air along -x, tangential.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. One calciner for both strings; the arms end in vertical faces at z = " & Num(CAL_Z_END, 2) & " (CFD outlets, to C5).", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Meal pipes +-x at 60 deg, fuel pipes +-y at 30 deg.  Dimensions mm.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/calciner/calciner.md", TEXT_H
    ElseIf equip <> "C1_twin" Then
        LabelPH COL_X0, y + 0.012, "3. Frame: z = 0 at the dust outlet; the volute's duct on the +y side, gas into it along +x.", TEXT_H
        If equip = "C4" Then
            LabelPH COL_X0, y + 0.007, "4. C2 and C3 are this cyclone (same geometry); 1 per string.  Dimensions mm.", TEXT_H
        Else
            LabelPH COL_X0, y + 0.007, "4. C4 x 6.50/6.30; finder wall, tongue, duct length unscaled; 1 per string.  Dimensions mm.", TEXT_H
        End If
        LabelPH COL_X0, y + 0.002, "5. Source: geometry/plant_geometry.yaml, geometry/preheater/cyclone_" & equip & ".md", TEXT_H
    Else
        LabelPH COL_X0, y + 0.012, "3. Frame: z = 0 at the C1 dust outlets, x across the pair, y along the inlet ducts.", TEXT_H
        LabelPH COL_X0, y + 0.007, "4. C1 B is C1 A mirrored (ducts face each other); 1 pair per string.  Dimensions mm.", TEXT_H
        LabelPH COL_X0, y + 0.002, "5. Spacing and Y follow from the branch gap (a model choice, no source): all E.", TEXT_H
        LabelPH COL_X0, y - 0.003, "6. Source: geometry/plant_geometry.yaml, geometry/preheater/riser_R1.md", TEXT_H
    End If
End Sub


' Flow arrows on the sheet at model points of A-A: gas in, gas out,
' meal out.
Private Sub DrawFlows()
    If equip = "C1" Then
        DrawFlowsC1
    ElseIf equip = "C1_twin" Then
        DrawFlowsTwin
    ElseIf equip = "calciner" Then
        DrawFlowsCalciner
    ElseIf equip = "kiln" Then
        DrawFlowsKiln
    ElseIf equip = "cooler" Then
        DrawFlowsCooler
    ElseIf equip = "id_fan" Then
        DrawFlowsIdFan
    ElseIf equip = "kiln_inlet_chamber" Then
        DrawFlowsKic
    Else
        DrawFlowsVolute
    End If
End Sub


' A volute cyclone's flows: gas and meal into the volute's duct (top
' view), the gas out of the pipe's end and the meal out of the dust outlet
' (A-A), and which way it swirls.
Private Sub DrawFlowsVolute()
    Dim R As Double, rT As Double, ym As Double
    R = 0.5 * vD: rT = R + vTongue: ym = rT + 0.5 * vW
    UseLayer L_FLOW
    ArrowM3 vTop, -vLduct - 2.4, ym, vHeight, -vLduct - 0.3, ym, vHeight
    ArrowM3 vSec, vExitX + 0.3, 0#, vZleg, vExitX + 2.1, 0#, vZleg
    ArrowM3 vSec, 0#, 0#, -0.2, 0#, 0#, -1.4
    UseLayer L_TEXT
    LabelM3 vTop, -vLduct - 4.6, ym + 0.8, vHeight, "Gas + meal in"
    LabelM3 vSec, vExitX + 0.3, 0#, vZleg + 1#, "Gas out"
    LabelM3 vSec, 0.4, 0#, -0.8, "Meal out (to the stage below)"
    LabelM3 vTop, -R, -R - 1.2, vHeight, "Swirl clockwise seen from above"
End Sub


' The calciner's flows: the kiln gas up the throat, the gas out of the
' two legs, the meal in along each pipe (A-A), the tertiary air along -x
' (plan) and the fuel along its pipe (left view).
' The cooler's flows (side view): the air up through each floor segment, out
' of the hood opening, and the clinker along the grate (a bed zone, not in the solid).
Private Sub DrawFlowsCooler()
    Dim i As Long, cx As Double
    UseLayer L_FLOW
    For i = 0 To CLng(COO_SEGMENTS) - 1
        cx = (i + 0.5) * COO_SEG_L
        ArrowM3 vFront, cx, 0#, -2.2, cx, 0#, -0.3
    Next i
    ArrowM3 vFront, 0.5 * COO_HOOD_L, 0#, COO_H + 0.3, 0.5 * COO_HOOD_L, 0#, COO_H + 2.2
    ArrowM3 vFront, 9#, 0#, 0.4, 19#, 0#, 0.4
    UseLayer L_TEXT
    LabelM3 vFront, 0.4 * COO_L, 0#, -3.2, "Cooling air in (one per segment)"
    LabelM3 vFront, COO_HOOD_L + 0.6, 0#, COO_H + 1.2, "Hood opening (to the kiln and the tertiary air)"
    LabelM3 vFront, 20#, 0#, 0.7, "Clinker travel (bed zone)"
    ' ISO 128-3: the floor view (under the plan: in first angle it would
    ' stand over the side view) looks from below, arrow A, right of the box
    ' so it is not read as one of the air arrows; the end view (1:50, lower
    ' left) looks from the hot end along +x, arrow B
    ViewArrow vFront, COO_L + 1.5, 0#, -2.5, COO_L + 1.5, 0#, -0.3, "A"
    ViewArrow vFront, -5#, 0#, 0.5 * COO_H, -0.5, 0#, 0.5 * COO_H, "B"
    ViewTitle vLeft, "A", "above", 0.004, VIEW_LETTER_H
    ViewTitle vSide, "B (1:" & Fmt(detailD) & ")", "above", 0.055, VIEW_LETTER_H
    ViewTitle vFront, "SIDE VIEW", "right", 0.03, TEXT_H
    ViewTitle vTop, "PLAN - roof (from above)", "right", 0.03, TEXT_H
End Sub


' The fan's flows: the gas into the inlet box's face along -x (plan), out of
' the discharge, up at the discharge angle (front), and which way it turns.
Private Sub DrawFlowsIdFan()
    Dim xm As Double, zm As Double, ym As Double
    xm = 0.5 * (IDF_E_TOP_X + IDF_E_LOW_X): zm = 0.5 * (IDF_E_TOP_Z + IDF_E_LOW_Z)
    ym = IDF_Y_BOX + 0.5 * IDF_BOX_DEPTH
    UseLayer L_FLOW
    ArrowM3 vTop, IDF_BOX_REACH + 2.4, ym, 0#, IDF_BOX_REACH + 0.3, ym, 0#
    ArrowM3 vFront, xm + 0.3 * IDF_DIS_DX, 0#, zm + 0.3 * IDF_DIS_DZ, xm + 2.1 * IDF_DIS_DX, 0#, zm + 2.1 * IDF_DIS_DZ
    UseLayer L_TEXT
    LabelM3 vTop, IDF_BOX_REACH + 0.3, ym + 0.5, 0#, "Gas in (from C1)"
    LabelM3 vFront, xm + 2.3 * IDF_DIS_DX - 0.6, 0#, zm + 2.3 * IDF_DIS_DZ + 0.3, "Gas out"
    LabelM3 vFront, IDF_X_MIN, 0#, IDF_Z_MIN - 1.2, "Turns counter-clockwise seen from here"
    ' view captions under each view's lowest, leftmost point
    Dim sx As Double, sy As Double
    ToSheet vFront, IDF_X_MIN, 0#, IDF_Z_MIN - 0.3, sx, sy
    LabelPH sx, sy - 0.012, "FRONT VIEW - from the drive side (-y)", TEXT_H
    ToSheet vTop, IDF_X_MIN, 0#, 0#, sx, sy
    LabelPH sx, sy - 0.01, "PLAN - from above", TEXT_H
    ToSheet vSide, 0#, 0#, IDF_Z_MIN - 0.3, sx, sy
    LabelPH sx, sy - 0.012, "FROM +X - inlet box face", TEXT_H
    ToSheet vLeft, IDF_R_MRF, 0#, -IDF_R_MRF, sx, sy
    LabelPH sx, sy - 0.012, "ROTOR ZONE (MRF) from the inlet side, 1:20", TEXT_H
    ToSheet vDet, 0#, 0#, -IDF_R_MRF, sx, sy
    LabelPH sx - 0.01, sy - 0.022, "ROTOR, FROM +X", TEXT_H
End Sub


' The chamber's flows: the kiln gas in through the +x wall's mouth (side and
' end views) and up out of the throat; the meal slides down the ramp and out
' through the mouth into the kiln (the meal itself enters in the solver).
Private Sub DrawFlowsKic()
    Dim a As Double, zc As Double
    a = 0.5 * KIC_A: zc = 0.5 * KIC_A
    UseLayer L_FLOW
    ArrowM3 vFront, a + 3.2, 0#, zc + 0.6, a + 0.4, 0#, zc + 0.6
    ArrowM3 vFront, 0#, 0#, KIC_H + KIC_STUB + 0.3, 0#, 0#, KIC_H + KIC_STUB + 2.2
    ArrowM3 vFront, 1.2, 0#, KIC_H_LIP + 1.6, a - 0.2, 0#, KIC_H_LIP + 0.15
    UseLayer L_TEXT
    ' (right of h_wall's dimension line at a + 1.8, not across it; 16 Nov sheet check)
    LabelM3 vFront, a + 2.3, 0#, zc + 1.2, "Kiln gas in (from the kiln)"
    LabelM3 vFront, 0.5, 0#, KIC_H + KIC_STUB + 2.6, "Gas out (to the calciner throat)"
    ' View captions: each one's left edge under the view's left edge; the
    ' side and end views (one row) share one baseline.
    Dim sxS As Double, sxE As Double, sxP As Double, syRow As Double, syPlan As Double, t As Double
    ToSheet vFront, -a, 0#, KIC_H_LIP, sxS, syRow
    ToSheet vSide, -a, 0#, KIC_H_LIP, sxE, t
    ToSheet vTop, -a, -a, KIC_H, sxP, syPlan
    LabelPH sxE, syRow - 0.012, "END VIEW - from the kiln (mouth in the +x wall)", TEXT_H
    LabelPH sxS, syRow - 0.012, "SIDE VIEW - meal slides down the ramp into the kiln", TEXT_H
    LabelPH sxP, syPlan - 0.012, "PLAN - throat (outlet) in the roof", TEXT_H
End Sub


' The kiln's flows (side view): the gas from the hood to the back end,
' the meal from the back end to the hood, along the axis, either side of it.
Private Sub DrawFlowsKiln()
    UseLayer L_FLOW
    ArrowM3 vFront, 1#, 0#, KIL_L - 4#, 1#, 0#, KIL_L - 14#
    ArrowM3 vFront, -1#, 0#, 4#, -1#, 0#, 14#
    UseLayer L_TEXT
    LabelM3 vFront, 1.6, 0#, KIL_L - 30#, "Gas (hood to back end)"
    LabelM3 vFront, -2.4, 0#, 17#, "Meal (back end to hood)"
    LabelM3 vFront, 0.5 * KIL_D + 1.2, 0#, 0#, "Back end (kiln inlet chamber)"
    LabelM3 vFront, 0.5 * KIL_D + 1.2, 0#, KIL_L - 14#, "Hood end"
    ' ISO 128-3: the end view (1:50, under the side view, not in its
    ' projected place) looks from the hood end along -z: arrow A
    ViewArrow vFront, 0.5 * KIL_D + 1.5, 0#, KIL_L + 6#, 0.5 * KIL_D + 1.5, 0#, KIL_L + 1#, "A"
    ViewTitle vTop, "A (1:" & Fmt(detailD) & ")", "above", 0.004, VIEW_LETTER_H
    ViewTitle vFront, "SIDE VIEW - back end left, hood end right", "below", 0.022, TEXT_H
End Sub


Private Sub DrawFlowsCalciner()
    Dim xl As Double, ze As Double, k As Double, sg As Double, i As Long
    Dim fx As Double, fz As Double
    xl = CAL_X_LEG: ze = CAL_Z_END
    k = Sqr(3#) * 0.5
    UseLayer L_FLOW
    ArrowM3 vSec, 0#, 0#, -2.6, 0#, 0#, -0.3
    For i = 0 To 1
        sg = 1# - 2# * i
        ' the meal pipe's axis rises outward at 60 deg: in towards the vessel
        fx = CAL_FEED_X: fz = CAL_FEED_Z
        ArrowM3 vSec, sg * (fx + 1.9 * 0.5), 0#, fz + 1.9 * k, sg * (fx + 0.4 * 0.5), 0#, fz + 0.4 * k
        ' the gas out of each arm's level run, beyond its outlet face (front view)
        ArrowM3 vFront, sg * (xl - 2.6), -CAL_Y_OFF, ze, sg * (xl + 2.4), -CAL_Y_OFF, ze
    Next i
    ' down the channel (front view)
    ArrowM3 vFront, 0#, -CAL_Y_OFF, CAL_Z_ROOF - 0.5, 0#, -CAL_Y_OFF, CAL_Z_SPLIT + 1.2
    ArrowM3 vTop, CAL_TA_X + 3#, CAL_TA_Y, CAL_TA_Z, CAL_TA_X + 0.3, CAL_TA_Y, CAL_TA_Z
    ArrowM3 vLeft, 0#, CAL_FUEL_Y + 1.9 * k, CAL_FUEL_Z + 1.9 * 0.5, 0#, CAL_FUEL_Y + 0.4 * k, CAL_FUEL_Z + 0.4 * 0.5
    UseLayer L_TEXT
    LabelM3 vSec, 0.5, 0#, -2.4, "Kiln gas in"
    LabelM3 vFront, xl + 2.6, -CAL_Y_OFF, ze - 0.4, "Gas out (to C5)"
    LabelM3 vFront, -xl - 11.4, -CAL_Y_OFF, ze - 0.4, "Gas out (to C5)"
    LabelM3 vSec, CAL_FEED_X + 1.5, 0#, CAL_FEED_Z + 2.8, "Meal in"
    LabelM3 vSec, -CAL_FEED_X - 3.2, 0#, CAL_FEED_Z + 2.8, "Meal in"
    ' (16 Nov sheet check: the label, 4.0 m long, sat across section A-A's
    ' arrow; now over the duct, outside the vessel, ending before the face's
    ' dimension. "Fuel in" (2.0 m) crossed the pipe and its dimension: now
    ' under the pipe's end, running in towards it. Run 2: the label crossed
    ' the duct face's extension line (the 6370 dimension): now over the
    ' arrow, right of that line, between section A-A's line and the 2439
    ' dimension's extension line)
    LabelM3 vTop, CAL_TA_X + 0.2, CAL_TA_Y + 2#, CAL_TA_Z, "Tertiary air in"
    LabelM3 vLeft, 0#, CAL_FUEL_Y + 3#, CAL_FUEL_Z - 0.4, "Fuel in"
    ' SolidWorks leaves the scale off this section's label even with the
    ' section's scale set (C1, C4, C5 print it): the second line by hand,
    ' under "KESIT A-A" (centred on the axis, its top 20-24 mm under the
    ' throat's foot on the 16 Nov sheet)
    Dim scx As Double, scy As Double
    ToSheet vSec, 0#, 0#, 0#, scx, scy
    ' the label's own word (O-umlaut L C-cedilla E K) spelled with ChrW: the macro file stays ASCII
    ' As SolidWorks writes it on C4 (read from the PDF, 16 Nov): 13.23 pt,
    ' "... 1 : 100", centred under "KESIT A-A", top 12.8 pt under its top.
    ' CharHeight 0.0045 printed 17.01 pt, so 0.0035 is 13.23 pt; x and y put
    ' the 87 pt line's centre on the label's (481.9 pt) and its top at 986.9 pt.
    LabelPH scx - 0.0154, scy - 0.0249, ChrW(214) & "L" & ChrW(199) & "EK 1 : " & Fmt(scaleD), 0.0035
    Note "section A-A label: scale line 1:" & Fmt(scaleD) & " written by hand"
End Sub


' The twin's flows: gas and meal in at R1's floor, the meal out of the
' two dust outlets, the gas out at the outlet legs' ends (seen in the
' left view), and which way each C1 swirls.
Private Sub DrawFlowsTwin()
    Dim S2 As Double
    S2 = 0.5 * TW_S
    UseLayer L_FLOW
    ' (the arrow stops above R1_D's dimension line, 1.6 m under R1's floor)
    ArrowM3 vFront, 0#, 0#, TW_Z_SPLIT - TW_R1_STUB_L - 1#, 0#, 0#, TW_Z_SPLIT - TW_R1_STUB_L - 0.15
    ' (beside the dust outlets' axes, not on them: detail C's letter sits on
    ' the right one's axis just outside the circle; 16 Nov sheet check)
    ArrowM3 vFront, S2 + 0.45, 0#, -0.2, S2 + 0.45, 0#, -1.4
    ArrowM3 vFront, -S2 - 0.45, 0#, -0.2, -S2 - 0.45, 0#, -1.4
    ArrowM3 vSide, 0#, C1_LEG_X, C1_HEIGHT - 0.2, 0#, C1_LEG_X, C1_HEIGHT - 1.6
    UseLayer L_TEXT
    LabelM3 vFront, 2.1, 0#, TW_Z_SPLIT - TW_R1_STUB_L - 1.5, "Gas in (R1, from C2)"
    LabelM3 vFront, S2 + 0.85, 0#, -1#, "Meal out"
    LabelM3 vFront, -S2 - 3.05, 0#, -1#, "Meal out"
    ' (in the left view +y is leftwards: the text runs on from here to the right, past the arrow)
    LabelM3 vSide, 0#, C1_LEG_X - 0.6, C1_HEIGHT - 1#, "Gas out (to fan)"
    LabelM3 vPlan, -S2 - TW_C1_R, 6#, TW_Z_CUT, "C1 A swirl clockwise, C1 B anticlockwise (seen from above)"
End Sub


Private Sub DrawFlowsC1()
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
    ' SolidWorks puts A-A's label under the section, against the plan's
    ' 860 dimension: read as the plan's label (16 Nov sheet check). Beside
    ' the cone instead, in the empty field right of it.
    MoveViewLabel vSec, "A-A", R + 0.6, 0.55 * C1_H_CONE
End Sub


' Move the label SolidWorks gave view v (the note holding `tag`, e.g.
' "A-A") to model point (x, z) of v, its upper left corner. The view's
' own notes are searched, then the sheet's; what is found is logged.
Private Sub MoveViewLabel(v As SldWorks.View, ByVal tag As String, ByVal x As Double, ByVal z As Double)
    Dim pass As Long, owner As SldWorks.View, nt As Object, txt As String, seen As String
    Dim linked As String, isLabel As Boolean
    Dim sx As Double, sy As Double, pos As Variant
    ToSheet v, x, 0#, z, sx, sy
    For pass = 0 To 1
        If pass = 0 Then Set owner = v Else Set owner = swDraw.GetFirstView
        Set nt = owner.GetFirstNote
        Do While Not nt Is Nothing
            txt = nt.GetText
            linked = ""
            On Error Resume Next
            linked = CallByName(nt, "PropertyLinkedText", VbGet)
            On Error GoTo 0
            seen = seen & " [" & Replace(txt, vbLf, "/") & " | " & Replace(linked, vbLf, "/") & "]"
            ' the view's label: its lines are linked fields, so GetText reads
            ' them blank; the linked text is "<VLNAME> <VLLABEL>/<VLSCALE>
            ' <VLSCALEV>" (C1 runs, 16 Nov)
            isLabel = InStr(1, txt, tag, vbTextCompare) > 0
            If Not isLabel And pass = 0 Then isLabel = InStr(1, linked, "<VLLABEL>", vbTextCompare) > 0
            If isLabel Then
                pos = nt.GetAnnotation.GetPosition
                nt.GetAnnotation.SetPosition2 sx, sy, 0#
                Note "view label '" & Replace(txt, vbLf, " / ") & "' (linked '" & Replace(linked, vbLf, " / ") & "') of " & v.Name & " moved from (" & _
                     Num(1000 * pos(0), 1) & ", " & Num(1000 * pos(1), 1) & ") to (" & _
                     Num(1000 * sx, 1) & ", " & Num(1000 * sy, 1) & ") mm"
                Exit Sub
            End If
            Set nt = nt.GetNext
        Loop
    Next pass
    Note "WARNING: no note holding '" & tag & "' on " & v.Name & " or the sheet; notes seen:" & Left(seen, 300)
End Sub


' Centre lines (ISO 128 04.1) of the axes of revolution in A-A and the
' left view: the cyclone's, up the outlet pipe to its bend, and the
' drop leg's; each runs 0.6 m past the solid.
Private Sub DrawAxes()
    If equip = "C1" Then
        DrawAxesC1
    ElseIf equip = "C1_twin" Then
        DrawAxesTwin
    ElseIf equip = "calciner" Then
        DrawAxesCalciner
    ElseIf equip = "kiln" Then
        DrawAxesKiln
    ElseIf equip = "cooler" Then
        DrawAxesCooler
    ElseIf equip = "id_fan" Then
        DrawAxesIdFan
    ElseIf equip = "kiln_inlet_chamber" Then
        DrawAxesKic
    Else
        DrawAxesVolute
    End If
End Sub


' A volute cyclone's centre lines: its axis up its outlet pipe and the
' run's axis in A-A, the axis in the left view, the cross in the top view.
Private Sub DrawAxesVolute()
    Dim R As Double
    R = 0.5 * vD
    UseLayer L_AXIS
    AxisM vSec, 0#, 0#, -0.6, 0#, 0#, vZleg
    AxisM vSec, vBendR - 0.6, 0#, vZleg, vExitX + 0.6, 0#, vZleg
    AxisM vLeft, 0#, 0#, -0.6, 0#, 0#, vTopZ
    AxisM vTop, -R - 0.6, 0#, vHeight, vExitX + 0.6, 0#, vHeight
    AxisM vTop, 0#, -R - 0.6, vHeight, 0#, R + 0.6, vHeight
End Sub


' The cooler's centre lines: the grate's axis (y = 0) in the plan and floor
' views, the box's mid-plane in the end view.
Private Sub DrawAxesCooler()
    UseLayer L_AXIS
    AxisM vTop, -1#, 0#, COO_H, COO_L + 1#, 0#, COO_H
    AxisM vLeft, -1#, 0#, 0#, COO_L + 1#, 0#, 0#
    AxisM vSide, COO_L * 0#, 0#, -0.6, COO_L * 0#, 0#, COO_H + 0.6
End Sub


' The fan's centre lines: the axis's cross in the front and rotor views, the
' axis along y in the plan and the two side views.
Private Sub DrawAxesIdFan()
    UseLayer L_AXIS
    AxisM vFront, -IDF_R_MRF - 0.6, 0#, 0#, IDF_R_MRF + 0.6, 0#, 0#
    AxisM vFront, 0#, 0#, -IDF_R_MRF - 0.6, 0#, 0#, IDF_R_MRF + 0.6
    AxisM vTop, 0#, -0.6, 0#, 0#, IDF_Y_BOX + IDF_BOX_DEPTH + 0.6, 0#
    AxisM vSide, 0#, -0.6, 0#, 0#, IDF_Y_BOX + IDF_BOX_DEPTH + 0.6, 0#
    AxisM vLeft, -IDF_R_MRF - 0.3, 0#, 0#, IDF_R_MRF + 0.3, 0#, 0#
    AxisM vLeft, 0#, 0#, -IDF_R_MRF - 0.3, 0#, 0#, IDF_R_MRF + 0.3
    AxisM vDet, 0#, -0.3, 0#, 0#, IDF_B1 + 0.3, 0#
End Sub


' The chamber's centre lines: the throat's axis in the side view and the
' cross in the plan, the kiln's axis in the side view and the mouth's cross in
' the view from +x.
Private Sub DrawAxesKic()
    Dim a As Double, zc As Double
    a = 0.5 * KIC_A: zc = 0.5 * KIC_A
    UseLayer L_AXIS
    AxisM vFront, 0#, 0#, KIC_H_LIP - 0.6, 0#, 0#, KIC_H + KIC_STUB + 0.6
    AxisM vFront, -a - 0.6, 0#, zc, a + 1#, 0#, zc
    AxisM vTop, -a - 0.6, 0#, KIC_H, a + 0.6, 0#, KIC_H
    AxisM vTop, 0#, -a - 0.6, KIC_H, 0#, a + 0.6, KIC_H
    AxisM vSide, a, -0.5 * KIC_D_MOUTH - 0.6, zc, a, 0.5 * KIC_D_MOUTH + 0.6, zc
    AxisM vSide, a, 0#, zc - 0.5 * KIC_D_MOUTH - 0.6, a, 0#, zc + 0.5 * KIC_D_MOUTH + 0.6
End Sub


' The kiln's centre lines: the axis in the side view, the cross in the end view.
Private Sub DrawAxesKiln()
    Dim R As Double
    R = 0.5 * KIL_D
    UseLayer L_AXIS
    AxisM vFront, 0#, 0#, -2#, 0#, 0#, KIL_L + 2#
    AxisM vTop, -R - 0.6, 0#, 0#, R + 0.6, 0#, 0#
    AxisM vTop, 0#, -R - 0.6, 0#, 0#, R + 0.6, 0#
End Sub


' The calciner's centre lines: the vessel's axis up to the neck's top and
' each leg's in A-A, the axis in the left view, the crosses in the plan,
' the tertiary air duct's axis in the plan.
Private Sub DrawAxesCalciner()
    Dim R As Double
    R = 0.5 * CAL_D_VESSEL
    UseLayer L_AXIS
    AxisM vSec, 0#, 0#, -0.6, 0#, 0#, CAL_Z_BEND + 0.6
    ' front view: the vessel's axis and the channel's (the same line), each arm's from the
    ' channel's lower end to where it turns level, then level beyond the outlet face
    AxisM vFront, 0#, 0#, -0.6, 0#, 0#, CAL_TOP + 0.6
    AxisM vFront, 0#, -CAL_Y_OFF, CAL_Z_SPLIT, CAL_X_BEND, -CAL_Y_OFF, CAL_Z_END
    AxisM vFront, CAL_X_BEND, -CAL_Y_OFF, CAL_Z_END, CAL_X_LEG + 0.6, -CAL_Y_OFF, CAL_Z_END
    AxisM vFront, 0#, -CAL_Y_OFF, CAL_Z_SPLIT, -CAL_X_BEND, -CAL_Y_OFF, CAL_Z_END
    AxisM vFront, -CAL_X_BEND, -CAL_Y_OFF, CAL_Z_END, -CAL_X_LEG - 0.6, -CAL_Y_OFF, CAL_Z_END
    AxisM vLeft, 0#, 0#, -0.6, 0#, 0#, CAL_TOP + 0.6
    AxisM vLeft, -CAL_Y_OFF, 0#, CAL_Z_SPLIT - 0.6, -CAL_Y_OFF, 0#, CAL_Z_ROOF + 0.6
    AxisM vTop, -R - 0.6, 0#, CAL_Z_ROOF, R + 0.6, 0#, CAL_Z_ROOF
    AxisM vTop, 0#, -R - 0.6, CAL_Z_ROOF, 0#, R + 0.6, CAL_Z_ROOF
    AxisM vTop, 0#, 0#, CAL_Z_ROOF, 0#, -CAL_Y_OFF - 0.6, CAL_Z_ROOF
    AxisM vTop, R - 0.6, CAL_TA_Y, CAL_TA_Z, CAL_TA_X + 0.6, CAL_TA_Y, CAL_TA_Z
End Sub


' The twin's centre lines (ISO 128 04.1): each C1's axis up its outlet
' pipe and R1's axis in the front view; in A-A a cross through each
' barrel's and each branch's centre; the C1 axes and the outlet legs'
' in the left view.
Private Sub DrawAxesTwin()
    Dim S2 As Double, b As Double, yb As Double, i As Long, sg As Double
    S2 = 0.5 * TW_S: b = TW_BRANCH_HALF: yb = TW_Y_BRANCH
    UseLayer L_AXIS
    AxisM vFront, S2, 0#, -0.6, S2, 0#, TW_TOP
    AxisM vFront, -S2, 0#, -0.6, -S2, 0#, TW_TOP
    AxisM vFront, 0#, 0#, TW_Z_SPLIT - TW_R1_STUB_L - 0.6, 0#, 0#, TW_Z_SPLIT + 0.6
    For i = 0 To 1
        sg = 1# - 2# * i
        AxisM vPlan, sg * S2 - TW_C1_R - 0.5, 0#, TW_Z_CUT, sg * S2 + TW_C1_R + 0.5, 0#, TW_Z_CUT
        AxisM vPlan, sg * S2, -TW_C1_R - 0.5, TW_Z_CUT, sg * S2, TW_C1_R + 0.5, TW_Z_CUT
        AxisM vPlan, sg * b - 0.5 * TW_BRANCH_D - 0.4, yb, TW_Z_CUT, sg * b + 0.5 * TW_BRANCH_D + 0.4, yb, TW_Z_CUT
        AxisM vPlan, sg * b, yb - 0.5 * TW_BRANCH_D - 0.4, TW_Z_CUT, sg * b, yb + 0.5 * TW_BRANCH_D + 0.4, TW_Z_CUT
    Next i
    AxisM vSide, 0#, 0#, -0.6, 0#, 0#, TW_TOP
    AxisM vSide, 0#, C1_LEG_X, C1_HEIGHT - 0.6, 0#, C1_LEG_X, TW_TOP - 0.5 * C1_D_VORTEX
End Sub


Private Sub DrawAxesC1()
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
    ' a line along the view's own direction projects to a point: left out and logged
    If Sqr((qx - ax) ^ 2 + (qy - ay) ^ 2) < 0.0002 Then
        Note "centre line left out: it projects to a point in view " & v.Name & " (model (" & Num(xa, 2) & ", " & Num(ya, 2) & ", " & Num(za, 2) & _
             ") to (" & Num(xb, 2) & ", " & Num(yb, 2) & ", " & Num(zb, 2) & "))"
        Exit Sub
    End If
    LineP ax, ay, qx, qy
End Sub


Private Sub ArrowM(v As SldWorks.View, ByVal xa As Double, ByVal za As Double, ByVal xb As Double, ByVal zb As Double)
    ArrowM3 v, xa, 0#, za, xb, 0#, zb
End Sub


' An arrow between two model points, in whichever view (its transform
' drops the depth).
Private Sub ArrowM3(v As SldWorks.View, ByVal xa As Double, ByVal ya As Double, ByVal za As Double, _
                    ByVal xb As Double, ByVal yb As Double, ByVal zb As Double, Optional ByVal headK As Double = 1#)
    Dim ax As Double, ay As Double, qx As Double, qy As Double
    Dim ux As Double, uy As Double, n As Double
    Const AL As Double = 0.004, AW As Double = 0.0014
    ToSheet v, xa, ya, za, ax, ay
    ToSheet v, xb, yb, zb, qx, qy
    LineP ax, ay, qx, qy
    ux = qx - ax: uy = qy - ay: n = Sqr(ux * ux + uy * uy): ux = ux / n: uy = uy / n
    LineP qx, qy, qx - headK * (AL * ux + AW * uy), qy - headK * (AL * uy - AW * ux)
    LineP qx, qy, qx - headK * (AL * ux - AW * uy), qy - headK * (AL * uy + AW * ux)
    If headK > 1# Then LineP qx - headK * (AL * ux + AW * uy), qy - headK * (AL * uy - AW * ux), _
                             qx - headK * (AL * ux - AW * uy), qy - headK * (AL * uy + AW * ux)
End Sub


Private Sub LabelM3(v As SldWorks.View, ByVal x As Double, ByVal y As Double, ByVal z As Double, ByVal txt As String)
    Dim sx As Double, sy As Double
    ToSheet v, x, y, z, sx, sy
    LabelPH sx, sy, txt, TEXT_H
End Sub


Private Sub LabelM(v As SldWorks.View, ByVal x As Double, ByVal z As Double, ByVal txt As String)
    Dim sx As Double, sy As Double
    If v Is vTop Then ToSheet v, x, z, 0#, sx, sy Else ToSheet v, x, 0#, z, sx, sy
    LabelPH sx, sy, txt, TEXT_H
End Sub


' ISO 128-3, a view not in its projected place: on the reference view an
' arrow in the direction of viewing, from model point a to b, and its
' letter beyond the arrow's tail; the view itself carries the letter
' (ViewTitle). The letter is larger than the dimension text.
Private Sub ViewArrow(v As SldWorks.View, ByVal xa As Double, ByVal ya As Double, ByVal za As Double, _
                      ByVal xb As Double, ByVal yb As Double, ByVal zb As Double, ByVal letter As String)
    Dim ax As Double, ay As Double, qx As Double, qy As Double, ux As Double, uy As Double, n As Double
    UseLayer L_TEXT
    ' a larger, closed head: not to be read as a flow arrow (the cooler's
    ' air arrows run beside arrow A)
    ArrowM3 v, xa, ya, za, xb, yb, zb, 1.5
    ToSheet v, xa, ya, za, ax, ay
    ToSheet v, xb, yb, zb, qx, qy
    ux = ax - qx: uy = ay - qy: n = Sqr(ux * ux + uy * uy): ux = ux / n: uy = uy / n
    ' the note's position is its upper left corner: centre the letter on the tail's extension
    LabelPH ax + 0.004 * ux - 0.5 * VIEW_LETTER_H, ay + 0.004 * uy + 0.5 * VIEW_LETTER_H, letter, VIEW_LETTER_H
    Note "view arrow " & letter & " on " & v.Name
End Sub


' A view's caption, placed by the view's outline on the sheet: "above"
' (left-aligned, the letter of a view out of its projected place), "below"
' (left-aligned, the KIC / ID fan captions) or "right" (at mid height).
' gap is the clear space to the outline [m on paper].
Private Sub ViewTitle(v As SldWorks.View, ByVal txt As String, ByVal side As String, _
                      ByVal gap As Double, ByVal h As Double)
    Dim ol As Variant, px As Double, py As Double
    ' no rebuild here: the views are placed, and a rebuild would close the
    ' sheet sketch the flows and arrows are drawn in
    ol = v.GetOutline
    Select Case side
    Case "above": px = ol(0): py = ol(3) + gap + h
    Case "below": px = ol(0): py = ol(1) - gap
    Case "right": px = ol(2) + gap: py = 0.5 * (ol(1) + ol(3)) + 0.5 * h
    Case Else: Fail "ViewTitle: no side '" & side & "'."
    End Select
    UseLayer L_TEXT
    LabelPH px, py, txt, h
    Note "view label " & txt & " on " & v.Name & " (" & side & ")"
End Sub


'------------------------------------------------------------------
' Sheet sketch primitives [m on paper]
'------------------------------------------------------------------
Private Sub LineP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    If swSkMgr.CreateLine(skPerM * a, skPerM * b, 0#, skPerM * c, skPerM * d, 0#) Is Nothing Then
        Fail "CreateLine failed from (" & Format(1000# * a, "0.0") & ", " & Format(1000# * b, "0.0") & _
             ") to (" & Format(1000# * c, "0.0") & ", " & Format(1000# * d, "0.0") & ") mm on the sheet."
    End If
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

    ' Checked where it matters, on the paper: for each candidate factor a
    ' probe line is drawn at the paper point (0.75 .. 0.80, 0.56) m, the
    ' frame's top right corner, empty of views on every sheet (the id_fan
    ' run: the old fixed probe at (0.5, 0.4) m fell inside its rotor view
    ' and nothing was picked), and picked there. The sheet's own scale is
    ' tried first after the transform's (the id_fan run's transform read
    ' 20, its last view's 1:20, on a 1:50 sheet).
    Dim k As Variant, hit As Double, kk As Double
    swModel.ViewZoomtofit2
    For Each k In Array(skPerM, scaleD, 100#, 50#, 200#)
        kk = k
        swSkMgr.DisplayWhenAdded = True              ' only what is drawn can be picked
        Set seg = swSkMgr.CreateLine(0.75 * kk, 0.56 * kk, 0#, 0.8 * kk, 0.56 * kk, 0#)
        swSkMgr.DisplayWhenAdded = False
        swModel.GraphicsRedraw2
        swModel.ClearSelection2 True
        If Not seg Is Nothing Then
            If swModel.Extension.SelectByID2("", "SKETCHSEGMENT", 0.775, 0.56, 0#, False, 0, Nothing, 0) Then hit = kk
            swModel.ClearSelection2 True
            seg.Select4 False, Nothing
            swModel.EditDelete
            swModel.ClearSelection2 True
        End If
        If hit > 0 Then Exit For
    Next k
    If hit > 0 Then
        Note "sheet sketch: a probe line is picked on the paper at " & Num(hit, 4) & " sketch units per metre"
        skPerM = hit
    Else
        Note "WARNING: the probe line was not picked on the paper; using the sheet's scale 1:" & Fmt(scaleD) & _
             " (the transform read " & Num(skPerM, 4) & ")"
        skPerM = scaleD
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
    If Dir(DRAW_ROOT & equip, vbDirectory) = "" Then MkDir DRAW_ROOT & equip
    drw = OUT_ROOT & LINE_KEY & "\drawings\" & equip & ".SLDDRW"
    pdf = DRAW_ROOT & equip & "\" & equip & ".pdf"
    dxf = DRAW_ROOT & equip & "\" & equip & ".dxf"
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
    LogPath = OUT_ROOT & LINE_KEY & "\drawings_" & equip & "_build.log"
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
