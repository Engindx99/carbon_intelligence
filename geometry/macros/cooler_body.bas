Attribute VB_Name = "cooler_body"
'==================================================================
' Clinker cooler MECHANICAL PARTS (envelopes)  ->  SLDPRT + STEP
'
' NOT a CFD input and not a fabrication drawing (user request, 23 Nov
' 2026: "altta fanlar olacak"; the cooler's CFD volume is cooler.bas).
' The cooler's frame as cooler.bas: x along the grate from the hot end,
' y across, z up from the grate; kiln_flame_solid.assembly places it
' with the cooler (cooler_placement()).
'
'   casing_side_<m|p>, casing_back, casing_roof_<n>   refractory casing
'   crusher_housing                 the roller crusher at the discharge end
'   grate_plates                    air distribution plates (with MFRs)
'   undergrate_side_<m|p>, partition_<nn>   compartments, one per segment
'   cylinder_<lane>_<chamber>       the cross bar lanes' hydraulic cylinders
'   fan_volute_<nn>, fan_inlet_, fan_shaft_, fan_motor_, fan_duct_
'                                   one cooling fan per segment
'   ground_slab
'
' Every body, its size, place, volume and extent come from
' geometry/plant_geometry.py cooler_body() (the generated CBD_ strings),
' built as temporary modeler bodies (a cylinder, a box), checked against
' the generated volume and exact extent. Sizes: FLSmidth Cross-Bar
' brochure, Holderbank 2000, fan laws, schematic values
' (plant_geometry.yaml cooler_body).
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py cooler_body_solid.main from WSL.
' Outputs geometry\output\2500\cooler_body.SLDPRT, .step and
' cooler_body_build.log.
'==================================================================

Option Explicit

Const PART_NAME As String = "cooler_body"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 101          ' bodies in the part [derived]
Const CBD_1                        As String  = "casing_side_m|box|0|33.9|-2.4|-2|0|3.4|46.104|0|-2.4|0|33.9|-2|3.4|0.72|0.42|0.3;casing_side_p|box|0|33.9|2|2.4|0|3.4|46.104|0|2|0|33.9|2.4|3.4|0.72|0.42|0.3;casing_back|box|-0.4|0|-2.4|2.4|-1.797121579|3.4|9.978473431|-0.4|-2.4|-1.797121579|0|2.4|3.4|0.72|0.42|0.3;casing_roof_1|box|5.98|16.541299666|-2|2|3|3.4|16.898079466|5.98|-2|3|16.541299666|2|3.4|0.72|0.42|0.3;casing_roof_2|box|19.338700334|33.9|-2|2|3|3.4|23.298079466|19.338700334|-2|3|33.9|2|3.4|0.72|0.42|0.3;casing_roof_3|box|16.541299666|19.338700334|-2|-1.398700334|3|3.4|0.672830435|16.541299666|-2|3|19.338700334|-1.398700334|3.4|0.72|0.42|0.3;casing_roof_4|box|16.541299666|19.338700334|1.398700334|2|3|3.4|0.672830435|16.541299666|1.398700334|3|19.338700334|2|3.4|0.72|0.42|0.3;casing_end|box|33.9|34.3|-2.4|2.4|-1.797121579|3.4|9.978473431|33.9|-2.4|-1.797121579|34.3|2.4|3.4|0.72|0.42|0.3;" ' plant_geometry.cooler_body() bodies
Const CBD_2                        As String  = "grate_plates|box|0|29.9|-2|2|-0.15|0|17.94|0|-2|-0.15|29.9|2|0|0.45|0.46|0.48;undergrate_side_m|box|0|33.9|-2.4|-2.3|-1.797121579|0|6.092242151|0|-2.4|-1.797121579|33.9|-2.3|0|0.62|0.64|0.66;undergrate_side_p|box|0|33.9|2.3|2.4|-1.797121579|0|6.092242151|0|2.3|-1.797121579|33.9|2.4|0|0.62|0.64|0.66;partition_01|box|2.98|3|-2.3|2.3|-1.797121579|-0.15|0.151535185|2.98|-2.3|-1.797121579|3|2.3|-0.15|0.62|0.64|0.66;partition_02|box|5.97|5.99|-2.3|2.3|-1.797121579|-0.15|0.151535185|5.97|-2.3|-1.797121579|5.99|2.3|-0.15|0.62|0.64|0.66;partition_03|box|8.96|8.98|-2.3|2.3|-1.797121579|-0.15|0.151535185|8.96|-2.3|-1.797121579|8.98|2.3|-0.15|0.62|0.64|0.66;partition_04|box|11.95|11.97|-2.3|2.3|-1.797121579|-0.15|0.151535185|11.95|-2.3|-1.797121579|11.97|2.3|-0.15|0.62|0.64|0.66;" ' plant_geometry.cooler_body() bodies
Const CBD_3                        As String  = "partition_05|box|14.94|14.96|-2.3|2.3|-1.797121579|-0.15|0.151535185|14.94|-2.3|-1.797121579|14.96|2.3|-0.15|0.62|0.64|0.66;partition_06|box|17.93|17.95|-2.3|2.3|-1.797121579|-0.15|0.151535185|17.93|-2.3|-1.797121579|17.95|2.3|-0.15|0.62|0.64|0.66;partition_07|box|20.92|20.94|-2.3|2.3|-1.797121579|-0.15|0.151535185|20.92|-2.3|-1.797121579|20.94|2.3|-0.15|0.62|0.64|0.66;partition_08|box|23.91|23.93|-2.3|2.3|-1.797121579|-0.15|0.151535185|23.91|-2.3|-1.797121579|23.93|2.3|-0.15|0.62|0.64|0.66;partition_09|box|26.9|26.92|-2.3|2.3|-1.797121579|-0.15|0.151535185|26.9|-2.3|-1.797121579|26.92|2.3|-0.15|0.62|0.64|0.66;partition_10|box|29.89|29.91|-2.3|2.3|-1.797121579|-0.15|0.151535185|29.89|-2.3|-1.797121579|29.91|2.3|-0.15|0.62|0.64|0.66;cylinder_1_03|cyl|6.675|-1.714285714|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|-1.839285714|-0.575|8.275|-1.589285714|-0.325|0.1|0.16|0.72;" ' plant_geometry.cooler_body() bodies
Const CBD_4                        As String  = "cylinder_1_08|cyl|21.625|-1.714285714|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|-1.839285714|-0.575|23.225|-1.589285714|-0.325|0.1|0.16|0.72;cylinder_2_03|cyl|6.675|-1.142857143|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|-1.267857143|-0.575|8.275|-1.017857143|-0.325|0.1|0.16|0.72;cylinder_2_08|cyl|21.625|-1.142857143|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|-1.267857143|-0.575|23.225|-1.017857143|-0.325|0.1|0.16|0.72;cylinder_3_03|cyl|6.675|-0.571428571|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|-0.696428571|-0.575|8.275|-0.446428571|-0.325|0.1|0.16|0.72;cylinder_3_08|cyl|21.625|-0.571428571|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|-0.696428571|-0.575|23.225|-0.446428571|-0.325|0.1|0.16|0.72;cylinder_4_03|cyl|6.675|0|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|-0.125|-0.575|8.275|0.125|-0.325|0.1|0.16|0.72;" ' plant_geometry.cooler_body() bodies
Const CBD_5                        As String  = "cylinder_4_08|cyl|21.625|0|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|-0.125|-0.575|23.225|0.125|-0.325|0.1|0.16|0.72;cylinder_5_03|cyl|6.675|0.571428571|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|0.446428571|-0.575|8.275|0.696428571|-0.325|0.1|0.16|0.72;cylinder_5_08|cyl|21.625|0.571428571|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|0.446428571|-0.575|23.225|0.696428571|-0.325|0.1|0.16|0.72;cylinder_6_03|cyl|6.675|1.142857143|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|1.017857143|-0.575|8.275|1.267857143|-0.325|0.1|0.16|0.72;cylinder_6_08|cyl|21.625|1.142857143|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|1.017857143|-0.575|23.225|1.267857143|-0.325|0.1|0.16|0.72;cylinder_7_03|cyl|6.675|1.714285714|-0.45|1|0|0|0.125|1.6|0.078539816|6.675|1.589285714|-0.575|8.275|1.839285714|-0.325|0.1|0.16|0.72;" ' plant_geometry.cooler_body() bodies
Const CBD_6                        As String  = "cylinder_7_08|cyl|21.625|1.714285714|-0.45|1|0|0|0.125|1.6|0.078539816|21.625|1.589285714|-0.575|23.225|1.839285714|-0.325|0.1|0.16|0.72;fan_volute_01|cyl|1.188142069|-4.265722961|-0.731398618|1|0|0|1.065722961|0.613715863|2.189807137|1.188142069|-5.331445922|-1.797121579|1.801857931|-3.2|0.334324343|0.1|0.16|0.72;fan_inlet_01|cyl|0.648985902|-4.265722961|-0.731398618|1|0|0|0.700903016|0.539156166|0.832109169|0.648985902|-4.966625977|-1.432301634|1.188142069|-3.564819945|-0.030495601|0.45|0.46|0.48;fan_shaft_01|cyl|1.801857931|-4.265722961|-0.731398618|1|0|0|0.06|0.3|0.00339292|1.801857931|-4.325722961|-0.791398618|2.101857931|-4.205722961|-0.671398618|0.45|0.46|0.48;fan_motor_01|box|2.101857931|3.327946573|-4.648875661|-3.882570261|-1.797121579|-1.030816178|0.719988636|2.101857931|-4.648875661|-1.797121579|3.327946573|-3.882570261|-1.030816178|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_7                        As String  = "fan_duct_01|box|0.87814386|2.11185614|-4.265722961|-2.4|-1.383712281|-0.15|2.839716154|0.87814386|-4.265722961|-1.383712281|2.11185614|-2.4|-0.15|0.62|0.64|0.66;fan_volute_02|cyl|4.340804847|4.229418278|-0.7677033|1|0|0|1.029418278|0.288390306|0.960095161|4.340804847|3.2|-1.797121579|4.629195153|5.258836556|0.261714978|0.1|0.16|0.72;fan_inlet_02|cyl|3.977563726|4.229418278|-0.7677033|1|0|0|0.472213457|0.363241121|0.254461217|3.977563726|3.757204821|-1.239916758|4.340804847|4.701631736|-0.295489843|0.45|0.46|0.48;fan_shaft_02|cyl|4.629195153|4.229418278|-0.7677033|1|0|0|0.06|0.3|0.00339292|4.629195153|4.169418278|-0.8277033|4.929195153|4.289418278|-0.7077033|0.45|0.46|0.48;fan_motor_02|box|4.929195153|5.849942602|3.9416847|4.517151856|-1.797121579|-1.221654423|0.304916979|4.929195153|3.9416847|-1.797121579|5.849942602|4.517151856|-1.221654423|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_8                        As String  = "fan_duct_02|box|4.069410733|4.900589267|2.4|4.229418278|-1.183292567|-0.352114034|1.263867805|4.069410733|2.4|-1.183292567|4.900589267|4.229418278|-0.352114034|0.62|0.64|0.66;fan_volute_03|cyl|7.344041763|-4.191785538|-0.805336041|1|0|0|0.991785538|0.261916474|0.8093721|7.344041763|-5.183571076|-1.797121579|7.605958237|-3.2|0.186449497|0.1|0.16|0.72;fan_inlet_03|cyl|7.004260807|-4.191785538|-0.805336041|1|0|0|0.441715243|0.339780956|0.208273339|7.004260807|-4.633500781|-1.247051283|7.344041763|-3.750070295|-0.363620798|0.45|0.46|0.48;fan_shaft_03|cyl|7.605958237|-4.191785538|-0.805336041|1|0|0|0.06|0.3|0.00339292|7.605958237|-4.251785538|-0.865336041|7.905958237|-4.131785538|-0.745336041|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_9                        As String  = "fan_motor_03|box|7.905958237|8.76502544|-4.460244039|-3.923327037|-1.797121579|-1.260204576|0.247651779|7.905958237|-4.460244039|-1.797121579|8.76502544|-3.923327037|-1.260204576|0.45|0.46|0.48;fan_duct_03|box|7.086251837|7.863748163|-4.191785538|-2.4|-1.194084203|-0.416587878|1.083135317|7.086251837|-4.191785538|-1.194084203|7.863748163|-2.4|-0.416587878|0.62|0.64|0.66;fan_volute_04|cyl|10.328664392|4.152667368|-0.84445421|1|0|0|0.952667368|0.272671217|0.777448712|10.328664392|3.2|-1.797121579|10.601335608|5.105334737|0.108213158|0.1|0.16|0.72;fan_inlet_04|cyl|9.988883436|4.152667368|-0.84445421|1|0|0|0.441715243|0.339780956|0.208273339|9.988883436|3.710952126|-1.286169453|10.328664392|4.594382611|-0.402738967|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_10                       As String  = "fan_shaft_04|cyl|10.601335608|4.152667368|-0.84445421|1|0|0|0.06|0.3|0.00339292|10.601335608|4.092667368|-0.90445421|10.901335608|4.212667368|-0.78445421|0.45|0.46|0.48;fan_motor_04|box|10.901335608|11.737662674|3.891315161|4.414019576|-1.797121579|-1.274417163|0.228501202|10.901335608|3.891315161|-1.797121579|11.737662674|4.414019576|-1.274417163|0.45|0.46|0.48;fan_duct_04|box|10.076251837|10.853748163|2.4|4.152667368|-1.233202373|-0.455706047|1.059488363|10.076251837|2.4|-1.233202373|10.853748163|4.152667368|-0.455706047|0.62|0.64|0.66;fan_volute_05|cyl|13.3125651|-4.111872621|-0.885248958|1|0|0|0.911872621|0.284869799|0.744157109|13.3125651|-5.023745242|-1.797121579|13.5974349|-3.2|0.026623663|0.1|0.16|0.72;" ' plant_geometry.cooler_body() bodies
Const CBD_11                       As String  = "fan_inlet_05|cyl|12.972784144|-4.111872621|-0.885248958|1|0|0|0.441715243|0.339780956|0.208273339|12.972784144|-4.553587864|-1.3269642|13.3125651|-3.670157378|-0.443533715|0.45|0.46|0.48;fan_shaft_05|cyl|13.5974349|-4.111872621|-0.885248958|1|0|0|0.06|0.3|0.00339292|13.5974349|-4.171872621|-0.945248958|13.8974349|-4.051872621|-0.825248958|0.45|0.46|0.48;fan_motor_05|box|13.8974349|14.709712997|-4.365709526|-3.858035716|-1.797121579|-1.289447768|0.209350626|13.8974349|-4.365709526|-1.797121579|14.709712997|-3.858035716|-1.289447768|0.45|0.46|0.48;fan_duct_05|box|13.066251837|13.843748163|-4.111872621|-2.4|-1.27399712|-0.496500795|1.034827916|13.066251837|-4.111872621|-1.27399712|13.843748163|-2.4|-0.496500795|0.62|0.64|0.66;" ' plant_geometry.cooler_body() bodies
Const CBD_12                       As String  = "fan_volute_06|cyl|16.295566409|4.069165254|-0.927956325|1|0|0|0.869165254|0.298867183|0.709304663|16.295566409|3.2|-1.797121579|16.594433591|4.938330508|-0.058791071|0.1|0.16|0.72;fan_inlet_06|cyl|15.955785453|4.069165254|-0.927956325|1|0|0|0.441715243|0.339780956|0.208273339|15.955785453|3.627450011|-1.369671567|16.295566409|4.510880497|-0.486241082|0.45|0.46|0.48;fan_shaft_06|cyl|16.594433591|4.069165254|-0.927956325|1|0|0|0.06|0.3|0.00339292|16.594433591|4.009165254|-0.987956325|16.894433591|4.129165254|-0.867956325|0.45|0.46|0.48;fan_motor_06|box|16.894433591|17.681147563|3.823317138|4.31501337|-1.797121579|-1.305425346|0.190200049|16.894433591|3.823317138|-1.797121579|17.681147563|4.31501337|-1.305425346|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_13                       As String  = "fan_duct_06|box|16.056251837|16.833748163|2.4|4.069165254|-1.316704487|-0.539208162|1.00901129|16.056251837|2.4|-1.316704487|16.833748163|4.069165254|-0.539208162|0.62|0.64|0.66;fan_volute_07|cyl|19.277423055|-4.024248021|-0.972873557|1|0|0|0.824248021|0.31515389|0.6726488|19.277423055|-4.848496042|-1.797121579|19.592576945|-3.2|-0.148625536|0.1|0.16|0.72;fan_inlet_07|cyl|18.937642099|-4.024248021|-0.972873557|1|0|0|0.441715243|0.339780956|0.208273339|18.937642099|-4.465963264|-1.4145888|19.277423055|-3.582532778|-0.531158315|0.45|0.46|0.48;fan_shaft_07|cyl|19.592576945|-4.024248021|-0.972873557|1|0|0|0.06|0.3|0.00339292|19.592576945|-4.084248021|-1.032873557|19.892576945|-3.964248021|-0.912873557|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_14                       As String  = "fan_motor_07|box|19.892576945|20.651947758|-4.2615514|-3.786944642|-1.797121579|-1.32251482|0.171049472|19.892576945|-4.2615514|-1.797121579|20.651947758|-3.786944642|-1.32251482|0.45|0.46|0.48;fan_duct_07|box|19.046251837|19.823748163|-4.024248021|-2.4|-1.36162172|-0.584125395|0.981858799|19.046251837|-4.024248021|-1.36162172|19.823748163|-2.4|-0.584125395|0.62|0.64|0.66;fan_volute_08|cyl|22.257784613|3.97673764|-1.020383938|1|0|0|0.77673764|0.334430774|0.633876732|22.257784613|3.2|-1.797121579|22.592215387|4.753475281|-0.243646298|0.1|0.16|0.72;fan_inlet_08|cyl|21.918003657|3.97673764|-1.020383938|1|0|0|0.441715243|0.339780956|0.208273339|21.918003657|3.535022398|-1.462099181|22.257784613|4.418452883|-0.578668695|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_15                       As String  = "fan_shaft_08|cyl|22.592215387|3.97673764|-1.020383938|1|0|0|0.06|0.3|0.00339292|22.592215387|3.91673764|-1.080383938|22.892215387|4.03673764|-0.960383938|0.45|0.46|0.48;fan_motor_08|box|22.892215387|23.622117901|3.748643105|4.204832176|-1.797121579|-1.340932507|0.151898895|22.892215387|3.748643105|-1.797121579|23.622117901|4.204832176|-1.340932507|0.45|0.46|0.48;fan_duct_08|box|22.036251837|22.813748163|2.4|3.97673764|-1.409132101|-0.631635775|0.953138748|22.036251837|2.4|-1.409132101|22.813748163|3.97673764|-0.631635775|0.62|0.64|0.66;fan_volute_09|cyl|25.236129372|-3.926125281|-1.070996297|1|0|0|0.726125281|0.357741257|0.592573214|25.236129372|-4.652250562|-1.797121579|25.593870628|-3.2|-0.344871016|0.1|0.16|0.72;" ' plant_geometry.cooler_body() bodies
Const CBD_16                       As String  = "fan_inlet_09|cyl|24.896348416|-3.926125281|-1.070996297|1|0|0|0.441715243|0.339780956|0.208273339|24.896348416|-4.367840524|-1.51271154|25.236129372|-3.484410038|-0.629281055|0.45|0.46|0.48;fan_shaft_09|cyl|25.593870628|-3.926125281|-1.070996297|1|0|0|0.06|0.3|0.00339292|25.593870628|-3.986125281|-1.130996297|25.893870628|-3.866125281|-1.010996297|0.45|0.46|0.48;fan_motor_09|box|25.893870628|26.591711385|-4.144200518|-3.708050045|-1.797121579|-1.360971106|0.132748318|25.893870628|-4.144200518|-1.797121579|26.591711385|-3.708050045|-1.360971106|0.45|0.46|0.48;fan_duct_09|box|25.026251837|25.803748163|-3.926125281|-2.4|-1.45974446|-0.682248135|0.92254355|25.026251837|-3.926125281|-1.45974446|25.803748163|-2.4|-0.682248135|0.62|0.64|0.66;" ' plant_geometry.cooler_body() bodies
Const CBD_17                       As String  = "fan_volute_10|cyl|28.211639082|3.87171012|-1.125411458|1|0|0|0.67171012|0.386721835|0.548166322|28.211639082|3.2|-1.797121579|28.598360918|4.543420241|-0.453701338|0.1|0.16|0.72;fan_inlet_10|cyl|27.871858126|3.87171012|-1.125411458|1|0|0|0.441715243|0.339780956|0.208273339|27.871858126|3.429994878|-1.567126701|28.211639082|4.313425363|-0.683696216|0.45|0.46|0.48;fan_shaft_10|cyl|28.598360918|3.87171012|-1.125411458|1|0|0|0.06|0.3|0.00339292|28.598360918|3.81171012|-1.185411458|28.898360918|3.93171012|-1.065411458|0.45|0.46|0.48;fan_motor_10|box|28.898360918|29.560887365|3.664670605|4.078749635|-1.797121579|-1.383042549|0.113597741|28.898360918|3.664670605|-1.797121579|29.560887365|4.078749635|-1.383042549|0.45|0.46|0.48;" ' plant_geometry.cooler_body() bodies
Const CBD_18                       As String  = "fan_duct_10|box|28.016251837|28.793748163|2.4|3.87171012|-1.514159621|-0.736663296|0.889649556|28.016251837|2.4|-1.514159621|28.793748163|3.87171012|-0.736663296|0.62|0.64|0.66;hrb_roller_1|cyl|30.4|-2.3|-0.45|0|1|0|0.45|4.6|2.926393557|29.95|-2.3|-0.9|30.85|2.3|0|0.62|0.64|0.66;hrb_shaft_1|cyl|30.4|2.3|-0.45|0|1|0|0.12|0.5|0.022619467|30.28|2.3|-0.57|30.52|2.8|-0.33|0.45|0.46|0.48;hrb_motor_1|box|30.1|30.7|2.8|4.4|-0.75|-0.15|0.576|30.1|2.8|-0.75|30.7|4.4|-0.15|0.1|0.16|0.72;hrb_roller_2|cyl|31.4|-2.3|-0.45|0|1|0|0.45|4.6|2.926393557|30.95|-2.3|-0.9|31.85|2.3|0|0.62|0.64|0.66;hrb_shaft_2|cyl|31.4|2.3|-0.45|0|1|0|0.12|0.5|0.022619467|31.28|2.3|-0.57|31.52|2.8|-0.33|0.45|0.46|0.48;hrb_motor_2|box|31.1|31.7|2.8|4.4|-0.75|-0.15|0.576|31.1|2.8|-0.75|31.7|4.4|-0.15|0.1|0.16|0.72;hrb_roller_3|cyl|32.4|-2.3|-0.45|0|1|0|0.45|4.6|2.926393557|31.95|-2.3|-0.9|32.85|2.3|0|0.62|0.64|0.66;" ' plant_geometry.cooler_body() bodies
Const CBD_19                       As String  = "hrb_shaft_3|cyl|32.4|2.3|-0.45|0|1|0|0.12|0.5|0.022619467|32.28|2.3|-0.57|32.52|2.8|-0.33|0.45|0.46|0.48;hrb_motor_3|box|32.1|32.7|2.8|4.4|-0.75|-0.15|0.576|32.1|2.8|-0.75|32.7|4.4|-0.15|0.1|0.16|0.72;hrb_roller_4|cyl|33.4|-2.3|-0.55|0|1|0|0.45|4.6|2.926393557|32.95|-2.3|-1|33.85|2.3|-0.1|0.62|0.64|0.66;hrb_shaft_4|cyl|33.4|2.3|-0.55|0|1|0|0.12|0.5|0.022619467|33.28|2.3|-0.67|33.52|2.8|-0.43|0.45|0.46|0.48;hrb_motor_4|box|33.1|33.7|2.8|4.4|-0.85|-0.25|0.576|33.1|2.8|-0.85|33.7|4.4|-0.25|0.1|0.16|0.72;ground_slab|box|-0.4|29.9|-5.831445922|5.831445922|-2.097121579|-1.797121579|106.015686861|-0.4|-5.831445922|-2.097121579|29.9|5.831445922|-1.797121579|0.78|0.77|0.74;ground_slab_end|box|33.9|34.3|-5.831445922|5.831445922|-2.097121579|-1.797121579|1.399547021|33.9|-5.831445922|-2.097121579|34.3|5.831445922|-1.797121579|0.78|0.77|0.74;" ' plant_geometry.cooler_body() bodies
Const CBD_20                       As String  = "ground_slab_m|box|29.9|33.9|-5.831445922|-2.3|-2.097121579|-1.797121579|4.237735106|29.9|-5.831445922|-2.097121579|33.9|-2.3|-1.797121579|0.78|0.77|0.74;ground_slab_p|box|29.9|33.9|2.3|5.831445922|-2.097121579|-1.797121579|4.237735106|29.9|2.3|-2.097121579|33.9|5.831445922|-1.797121579|0.78|0.77|0.74;" ' plant_geometry.cooler_body() bodies
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
Dim logName As String             ' the build log's file name (main: cooler_body_build.log)
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
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Cooler mechanical parts"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Cooler mechanical parts"
    End If
End Sub


'==================================================================
' The generated records: name|kind|params|V|box(6)|rgb(3), ";" between
'==================================================================
Private Sub ReadBodies()
    Dim all As String, recs As Variant, f As Variant
    Dim i As Long, j As Long, np As Long, k As Long

    all = CBD_1 & CBD_2 & CBD_3 & CBD_4 & CBD_5 & CBD_6 & CBD_7 & CBD_8 & CBD_9 & CBD_10 & _
          CBD_11 & CBD_12 & CBD_13 & CBD_14 & CBD_15 & CBD_16 & CBD_17 & CBD_18 & CBD_19 & CBD_20
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
    ' the enclosure (refractory casing, the undergrate's side walls) fully
    ' see-through, so the compartments, cylinders and fans show (user, 23 Nov 2026)
    If Left$(bName(i), 7) = "casing_" Or Left$(bName(i), 16) = "undergrate_side_" Then
        PaintBody found, bRGB(i, 0), bRGB(i, 1), bRGB(i, 2), 1#
    Else
        PaintBody found, bRGB(i, 0), bRGB(i, 1), bRGB(i, 2)
    End If
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
    Err.Raise vbObjectError + 1, "cooler_body", msg
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
