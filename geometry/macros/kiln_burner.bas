Attribute VB_Name = "kiln_burner"
'==================================================================
' Kiln burner (JETFLEX 2.0) CFD flow volume  ->  STEP (AP214) + STL + SLDPRT
'
' The channels of the kiln burner up to its tip (geometry/kiln/
' kiln_burner.md; user, 22 Nov 2026: a geometry a CFD can take, the
' burner's channels only, to be set into a flame domain later):
'   coal    the straight solid fuel pipe (coal + its conveying air),
'           a little above the tip's centre;
'   axial   an annular plenum behind the front plate and the ring of
'           rectangular axial air slots through it (fixed nozzles);
'   swirl   an annular plenum and the ring of square swirl air holes
'           through the plate, inclined towards +theta (the swirl turns
'           anticlockwise seen from the kiln).
' Fuel lance, igniter and flame scanner are no flow path here (closed in
' the tip, part of its wall in the flame domain). Sizes: the brochure's
' tip (image ratios) scaled so the slots pass the twin's axial air at the
' JETFLEX manual's pressure (plant_geometry.kiln_burner(), the generated
' KBR_ strings and per-channel checks).
'
' Frame: the burner's axis z, the tip plane z = 0, the flow towards +z
' (into the kiln); y up; x to the right seen from the kiln (SolidWorks'
' front view looks at the tip as the kiln does).
'
' Boundary faces (coloured for Fluent): coal_inlet (dark red),
' axial_inlet (red), swirl_inlet (light red) -- the channels' upstream
' ends; coal_outlet (dark blue), axial_outlet (blue, one face per slot),
' swirl_outlet (light blue, one per hole) -- in the tip plane; wall =
' every other face (grey).
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py kiln_burner_solid.main from WSL.
' Outputs geometry\output\2500\kiln_burner.SLDPRT, .step, .stl, the
' previews kiln_burner_front.jpg / _iso.jpg and kiln_burner_build.log.
'==================================================================

Option Explicit

Const PART_NAME As String = "kiln_burner"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const N_BODIES                     As Double  = 63           ' bodies before joining [derived]
Const KBR_1                        As String  = "coal|coal|cyl|0|0.033669104|-1.047448325|0|0|1|0.104744833|1.047448325|0.036103366|-0.104744833|-0.071075729|-1.047448325|0.104744833|0.138413936|0|0.35|0.25|0.15;axial_slot_00|axial|slot|0|0.215959661|-0.07|0|0.034416871|0.010857057|2.914699851|0.000026157|-0.017988538|0.206799209|-0.07|0.017988538|0.225120112|0|0.1|0.3|0.8;axial_slot_01|axial|slot|-0.066735205|0.205389843|-0.07|0|0.034416871|0.010857057|3.228859116|0.000026157|-0.084351285|0.198482157|-0.07|-0.049119126|0.212297528|0|0.1|0.3|0.8;axial_slot_02|axial|slot|-0.126937904|0.174715036|-0.07|0|0.034416871|0.010857057|3.543018382|0.000026157|-0.144899447|0.162994177|-0.07|-0.10897636|0.186435894|0|0.1|0.3|0.8;axial_slot_03|axial|slot|-0.174715036|0.126937904|-0.07|0|0.034416871|0.010857057|3.857177647|0.000026157|-0.191263842|0.111551192|-0.07|-0.158166229|0.142324616|0|0.1|0.3|0.8;" ' plant_geometry.kiln_burner() bodies
Const KBR_2                        As String  = "axial_slot_04|axial|slot|-0.205389843|0.066735205|-0.07|0|0.034416871|0.010857057|4.171336912|0.000026157|-0.218905999|0.049188798|-0.07|-0.191873686|0.084281612|0|0.1|0.3|0.8;axial_slot_05|axial|slot|-0.215959661|0|-0.07|0|0.034416871|0.010857057|4.485496178|0.000026157|-0.225120112|-0.017988538|-0.07|-0.206799209|0.017988538|0|0.1|0.3|0.8;axial_slot_06|axial|slot|-0.205389843|-0.066735205|-0.07|0|0.034416871|0.010857057|4.799655443|0.000026157|-0.212297528|-0.084351285|-0.07|-0.198482157|-0.049119126|0|0.1|0.3|0.8;axial_slot_07|axial|slot|-0.174715036|-0.126937904|-0.07|0|0.034416871|0.010857057|5.113814708|0.000026157|-0.186435894|-0.144899447|-0.07|-0.162994177|-0.10897636|0|0.1|0.3|0.8;axial_slot_08|axial|slot|-0.126937904|-0.174715036|-0.07|0|0.034416871|0.010857057|5.427973974|0.000026157|-0.142324616|-0.191263842|-0.07|-0.111551192|-0.158166229|0|0.1|0.3|0.8;" ' plant_geometry.kiln_burner() bodies
Const KBR_3                        As String  = "axial_slot_09|axial|slot|-0.066735205|-0.205389843|-0.07|0|0.034416871|0.010857057|5.742133239|0.000026157|-0.084281612|-0.218905999|-0.07|-0.049188798|-0.191873686|0|0.1|0.3|0.8;axial_slot_10|axial|slot|0|-0.215959661|-0.07|0|0.034416871|0.010857057|6.056292504|0.000026157|-0.017988538|-0.225120112|-0.07|0.017988538|-0.206799209|0|0.1|0.3|0.8;axial_slot_11|axial|slot|0.066735205|-0.205389843|-0.07|0|0.034416871|0.010857057|6.37045177|0.000026157|0.049119126|-0.212297528|-0.07|0.084351285|-0.198482157|0|0.1|0.3|0.8;axial_slot_12|axial|slot|0.126937904|-0.174715036|-0.07|0|0.034416871|0.010857057|6.684611035|0.000026157|0.10897636|-0.186435894|-0.07|0.144899447|-0.162994177|0|0.1|0.3|0.8;axial_slot_13|axial|slot|0.174715036|-0.126937904|-0.07|0|0.034416871|0.010857057|6.9987703|0.000026157|0.158166229|-0.142324616|-0.07|0.191263842|-0.111551192|0|0.1|0.3|0.8;" ' plant_geometry.kiln_burner() bodies
Const KBR_4                        As String  = "axial_slot_14|axial|slot|0.205389843|-0.066735205|-0.07|0|0.034416871|0.010857057|7.312929566|0.000026157|0.191873686|-0.084281612|-0.07|0.218905999|-0.049188798|0|0.1|0.3|0.8;axial_slot_15|axial|slot|0.215959661|0|-0.07|0|0.034416871|0.010857057|7.627088831|0.000026157|0.206799209|-0.017988538|-0.07|0.225120112|0.017988538|0|0.1|0.3|0.8;axial_slot_16|axial|slot|0.205389843|0.066735205|-0.07|0|0.034416871|0.010857057|7.941248097|0.000026157|0.198482157|0.049119126|-0.07|0.212297528|0.084351285|0|0.1|0.3|0.8;axial_slot_17|axial|slot|0.174715036|0.126937904|-0.07|0|0.034416871|0.010857057|8.255407362|0.000026157|0.162994177|0.10897636|-0.07|0.186435894|0.144899447|0|0.1|0.3|0.8;axial_slot_18|axial|slot|0.126937904|0.174715036|-0.07|0|0.034416871|0.010857057|8.569566627|0.000026157|0.111551192|0.158166229|-0.07|0.142324616|0.191263842|0|0.1|0.3|0.8;" ' plant_geometry.kiln_burner() bodies
Const KBR_5                        As String  = "axial_slot_19|axial|slot|0.066735205|0.205389843|-0.07|0|0.034416871|0.010857057|8.883725893|0.000026157|0.049188798|0.191873686|-0.07|0.084281612|0.218905999|0|0.1|0.3|0.8;swirl_hole_00|swirl|hole|-0.014282638|0.181478129|0|-0.078459096|0.996917334|0|-0.863355736|-0.06794757|-0.5|-0.498458667|-0.039229548|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.020066473|0.176362643|-0.07|0.03179113|0.189764501|0|0.1|0.6|0.3;swirl_hole_01|swirl|hole|-0.042496229|0.177009535|0|-0.233445364|0.97236992|0|-0.842097053|-0.202169615|-0.5|-0.48618496|-0.116722682|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.048875764|0.171167705|-0.07|0.003181167|0.192285946|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_6                        As String  = "swirl_hole_02|swirl|hole|-0.069663422|0.168182379|0|-0.382683432|0.923879533|0|-0.800103145|-0.331413574|-0.5|-0.461939766|-0.191341716|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.076481571|0.161758051|-0.07|-0.025507127|0.190072674|0|0.1|0.6|0.3;swirl_hole_03|swirl|hole|-0.09511527|0.155214015|0|-0.522498565|0.852640164|0|-0.738408043|-0.45249703|-0.5|-0.426320082|-0.261249282|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.102204148|0.148365376|-0.07|-0.05356735|0.183179181|0|0.1|0.6|0.3;swirl_hole_04|swirl|hole|-0.118225065|0.138423766|0|-0.649448048|0.760405966|0|-0.658530883|-0.562438508|-0.5|-0.380202983|-0.324724024|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.12541012|0.131319453|-0.07|-0.080308568|0.171775209|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_7                        As String  = "swirl_hole_05|swirl|hole|-0.138423766|0.118225065|0|-0.760405966|0.649448048|0|-0.562438508|-0.658530883|-0.5|-0.324724024|-0.380202983|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.145528079|0.11104001|-0.07|-0.105072323|0.156141562|0|0.1|0.6|0.3;swirl_hole_06|swirl|hole|-0.155214015|0.09511527|0|-0.852640164|0.522498565|0|-0.45249703|-0.738408043|-0.5|-0.261249282|-0.426320082|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.162062653|0.088026392|-0.07|-0.127248848|0.13666319|0|0.1|0.6|0.3;swirl_hole_07|swirl|hole|-0.168182379|0.069663422|0|-0.923879533|0.382683432|0|-0.331413574|-0.800103145|-0.5|-0.191341716|-0.461939766|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.174606707|0.062845273|-0.07|-0.146292084|0.113819718|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_8                        As String  = "swirl_hole_08|swirl|hole|-0.177009535|0.042496229|0|-0.97236992|0.233445364|0|-0.202169615|-0.842097053|-0.5|-0.116722682|-0.48618496|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.182851364|0.036116695|-0.07|-0.161733123|0.088173626|0|0.1|0.6|0.3;swirl_hole_09|swirl|hole|-0.181478129|0.014282638|0|-0.996917334|0.078459096|0|-0.06794757|-0.863355736|-0.5|-0.039229548|-0.498458667|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.186593614|0.008498804|-0.07|-0.173191757|0.060356407|0|0.1|0.6|0.3;swirl_hole_10|swirl|hole|-0.181478129|-0.014282638|0|-0.996917334|-0.078459096|0|0.06794757|-0.863355736|-0.5|0.039229548|-0.498458667|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.189764501|-0.020066473|-0.07|-0.176362643|0.03179113|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_9                        As String  = "swirl_hole_11|swirl|hole|-0.177009535|-0.042496229|0|-0.97236992|-0.233445364|0|0.202169615|-0.842097053|-0.5|0.116722682|-0.48618496|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.192285946|-0.048875764|-0.07|-0.171167705|0.003181167|0|0.1|0.6|0.3;swirl_hole_12|swirl|hole|-0.168182379|-0.069663422|0|-0.923879533|-0.382683432|0|0.331413574|-0.800103145|-0.5|0.191341716|-0.461939766|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.190072674|-0.076481571|-0.07|-0.161758051|-0.025507127|0|0.1|0.6|0.3;swirl_hole_13|swirl|hole|-0.155214015|-0.09511527|0|-0.852640164|-0.522498565|0|0.45249703|-0.738408043|-0.5|0.261249282|-0.426320082|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.183179181|-0.102204148|-0.07|-0.148365376|-0.05356735|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_10                       As String  = "swirl_hole_14|swirl|hole|-0.138423766|-0.118225065|0|-0.760405966|-0.649448048|0|0.562438508|-0.658530883|-0.5|0.324724024|-0.380202983|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.171775209|-0.12541012|-0.07|-0.131319453|-0.080308568|0|0.1|0.6|0.3;swirl_hole_15|swirl|hole|-0.118225065|-0.138423766|0|-0.649448048|-0.760405966|0|0.658530883|-0.562438508|-0.5|0.380202983|-0.324724024|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.156141562|-0.145528079|-0.07|-0.11104001|-0.105072323|0|0.1|0.6|0.3;swirl_hole_16|swirl|hole|-0.09511527|-0.155214015|0|-0.522498565|-0.852640164|0|0.738408043|-0.45249703|-0.5|0.426320082|-0.261249282|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.13666319|-0.162062653|-0.07|-0.088026392|-0.127248848|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_11                       As String  = "swirl_hole_17|swirl|hole|-0.069663422|-0.168182379|0|-0.382683432|-0.923879533|0|0.800103145|-0.331413574|-0.5|0.461939766|-0.191341716|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.113819718|-0.174606707|-0.07|-0.062845273|-0.146292084|0|0.1|0.6|0.3;swirl_hole_18|swirl|hole|-0.042496229|-0.177009535|0|-0.233445364|-0.97236992|0|0.842097053|-0.202169615|-0.5|0.48618496|-0.116722682|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.088173626|-0.182851364|-0.07|-0.036116695|-0.161733123|0|0.1|0.6|0.3;swirl_hole_19|swirl|hole|-0.014282638|-0.181478129|0|-0.078459096|-0.996917334|0|0.863355736|-0.06794757|-0.5|0.498458667|-0.039229548|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.060356407|-0.186593614|-0.07|-0.008498804|-0.173191757|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_12                       As String  = "swirl_hole_20|swirl|hole|0.014282638|-0.181478129|0|0.078459096|-0.996917334|0|0.863355736|0.06794757|-0.5|0.498458667|0.039229548|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.03179113|-0.189764501|-0.07|0.020066473|-0.176362643|0|0.1|0.6|0.3;swirl_hole_21|swirl|hole|0.042496229|-0.177009535|0|0.233445364|-0.97236992|0|0.842097053|0.202169615|-0.5|0.48618496|0.116722682|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|-0.003181167|-0.192285946|-0.07|0.048875764|-0.171167705|0|0.1|0.6|0.3;swirl_hole_22|swirl|hole|0.069663422|-0.168182379|0|0.382683432|-0.923879533|0|0.800103145|0.331413574|-0.5|0.461939766|0.191341716|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.025507127|-0.190072674|-0.07|0.076481571|-0.161758051|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_13                       As String  = "swirl_hole_23|swirl|hole|0.09511527|-0.155214015|0|0.522498565|-0.852640164|0|0.738408043|0.45249703|-0.5|0.426320082|0.261249282|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.05356735|-0.183179181|-0.07|0.102204148|-0.148365376|0|0.1|0.6|0.3;swirl_hole_24|swirl|hole|0.118225065|-0.138423766|0|0.649448048|-0.760405966|0|0.658530883|0.562438508|-0.5|0.380202983|0.324724024|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.080308568|-0.171775209|-0.07|0.12541012|-0.131319453|0|0.1|0.6|0.3;swirl_hole_25|swirl|hole|0.138423766|-0.118225065|0|0.760405966|-0.649448048|0|0.562438508|0.658530883|-0.5|0.324724024|0.380202983|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.105072323|-0.156141562|-0.07|0.145528079|-0.11104001|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_14                       As String  = "swirl_hole_26|swirl|hole|0.155214015|-0.09511527|0|0.852640164|-0.522498565|0|0.45249703|0.738408043|-0.5|0.261249282|0.426320082|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.127248848|-0.13666319|-0.07|0.162062653|-0.088026392|0|0.1|0.6|0.3;swirl_hole_27|swirl|hole|0.168182379|-0.069663422|0|0.923879533|-0.382683432|0|0.331413574|0.800103145|-0.5|0.191341716|0.461939766|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.146292084|-0.113819718|-0.07|0.174606707|-0.062845273|0|0.1|0.6|0.3;swirl_hole_28|swirl|hole|0.177009535|-0.042496229|0|0.97236992|-0.233445364|0|0.202169615|0.842097053|-0.5|0.116722682|0.48618496|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.161733123|-0.088173626|-0.07|0.182851364|-0.036116695|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_15                       As String  = "swirl_hole_29|swirl|hole|0.181478129|-0.014282638|0|0.996917334|-0.078459096|0|0.06794757|0.863355736|-0.5|0.039229548|0.498458667|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.173191757|-0.060356407|-0.07|0.186593614|-0.008498804|0|0.1|0.6|0.3;swirl_hole_30|swirl|hole|0.181478129|0.014282638|0|0.996917334|0.078459096|0|-0.06794757|0.863355736|-0.5|-0.039229548|0.498458667|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.176362643|-0.03179113|-0.07|0.189764501|0.020066473|0|0.1|0.6|0.3;swirl_hole_31|swirl|hole|0.177009535|0.042496229|0|0.97236992|0.233445364|0|-0.202169615|0.842097053|-0.5|-0.116722682|0.48618496|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.171167705|-0.003181167|-0.07|0.192285946|0.048875764|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_16                       As String  = "swirl_hole_32|swirl|hole|0.168182379|0.069663422|0|0.923879533|0.382683432|0|-0.331413574|0.800103145|-0.5|-0.191341716|0.461939766|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.161758051|0.025507127|-0.07|0.190072674|0.076481571|0|0.1|0.6|0.3;swirl_hole_33|swirl|hole|0.155214015|0.09511527|0|0.852640164|0.522498565|0|-0.45249703|0.738408043|-0.5|-0.261249282|0.426320082|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.148365376|0.05356735|-0.07|0.183179181|0.102204148|0|0.1|0.6|0.3;swirl_hole_34|swirl|hole|0.138423766|0.118225065|0|0.760405966|0.649448048|0|-0.562438508|0.658530883|-0.5|-0.324724024|0.380202983|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.131319453|0.080308568|-0.07|0.171775209|0.12541012|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_17                       As String  = "swirl_hole_35|swirl|hole|0.118225065|0.138423766|0|0.649448048|0.760405966|0|-0.658530883|0.562438508|-0.5|-0.380202983|0.324724024|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.11104001|0.105072323|-0.07|0.156141562|0.145528079|0|0.1|0.6|0.3;swirl_hole_36|swirl|hole|0.09511527|0.155214015|0|0.522498565|0.852640164|0|-0.738408043|0.45249703|-0.5|-0.426320082|0.261249282|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.088026392|0.127248848|-0.07|0.13666319|0.162062653|0|0.1|0.6|0.3;swirl_hole_37|swirl|hole|0.069663422|0.168182379|0|0.382683432|0.923879533|0|-0.800103145|0.331413574|-0.5|-0.461939766|0.191341716|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.062845273|0.146292084|-0.07|0.113819718|0.174606707|0|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_18                       As String  = "swirl_hole_38|swirl|hole|0.042496229|0.177009535|0|0.233445364|0.97236992|0|-0.842097053|0.202169615|-0.5|-0.48618496|0.116722682|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.036116695|0.161733123|-0.07|0.088173626|0.182851364|0|0.1|0.6|0.3;swirl_hole_39|swirl|hole|0.014282638|0.181478129|0|0.078459096|0.996917334|0|-0.863355736|0.06794757|-0.5|-0.498458667|0.039229548|0.866025404|0.009407668|0.183384153|-0.07|0|0.000007154|0.008498804|0.173191757|-0.07|0.060356407|0.186593614|0|0.1|0.6|0.3;axial_plenum|axial|ring|0.203382734|0.229656266|-0.56|-0.06|0.017871679|-0.229656266|-0.229656266|-0.56|0.229656266|0.229656266|-0.06|0.1|0.3|0.8;swirl_plenum|swirl|ring|0.173340909|0.196288469|-0.56|-0.06|0.013323639|-0.196288469|-0.196288469|-0.56|0.196288469|0.196288469|-0.06|0.1|0.6|0.3;" ' plant_geometry.kiln_burner() bodies
Const KBR_19                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const KBR_20                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const KBR_21                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const KBR_22                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const KBR_23                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const KBR_24                       As String  = ""           ' plant_geometry.kiln_burner() bodies
Const COAL_V                       As Double  = 0.036103366  ' coal channel volume [m3] [derived]
Const COAL_N_OUT                   As Long    = 1            ' coal outlet faces in the tip plane [derived]
Const COAL_A_OUT                   As Double  = 0.034467921  ' coal outlet area [m2] [derived]
Const COAL_A_IN                    As Double  = 0.034467921  ' coal inlet area [m2] [derived]
Const COAL_BOX_0                   As Double  = -0.104745    ' coal extent (x0) [m] [derived]
Const COAL_BOX_1                   As Double  = -0.071076    ' coal extent (y0) [m] [derived]
Const COAL_BOX_2                   As Double  = -1.047448    ' coal extent (z0) [m] [derived]
Const COAL_BOX_3                   As Double  = 0.104745     ' coal extent (x1) [m] [derived]
Const COAL_BOX_4                   As Double  = 0.138414     ' coal extent (y1) [m] [derived]
Const COAL_BOX_5                   As Double  = 0#           ' coal extent (z1) [m] [derived]
Const AXIAL_V                      As Double  = 0.018320078  ' axial channel volume [m3] [derived]
Const AXIAL_N_OUT                  As Long    = 20           ' axial outlet faces in the tip plane [derived]
Const AXIAL_A_OUT                  As Double  = 0.007473319  ' axial outlet area [m2] [derived]
Const AXIAL_A_IN                   As Double  = 0.035743357  ' axial inlet area [m2] [derived]
Const AXIAL_BOX_0                  As Double  = -0.229656    ' axial extent (x0) [m] [derived]
Const AXIAL_BOX_1                  As Double  = -0.229656    ' axial extent (y0) [m] [derived]
Const AXIAL_BOX_2                  As Double  = -0.56        ' axial extent (z0) [m] [derived]
Const AXIAL_BOX_3                  As Double  = 0.229656     ' axial extent (x1) [m] [derived]
Const AXIAL_BOX_4                  As Double  = 0.229656     ' axial extent (y1) [m] [derived]
Const AXIAL_BOX_5                  As Double  = 0#           ' axial extent (z1) [m] [derived]
Const SWIRL_V                      As Double  = 0.013568909  ' swirl channel volume [m3] [derived]
Const SWIRL_N_OUT                  As Long    = 40           ' swirl outlet faces in the tip plane [derived]
Const SWIRL_A_OUT                  As Double  = 0.004087834  ' swirl outlet area [m2] [derived]
Const SWIRL_A_IN                   As Double  = 0.026647279  ' swirl inlet area [m2] [derived]
Const SWIRL_BOX_0                  As Double  = -0.196288    ' swirl extent (x0) [m] [derived]
Const SWIRL_BOX_1                  As Double  = -0.196288    ' swirl extent (y0) [m] [derived]
Const SWIRL_BOX_2                  As Double  = -0.56        ' swirl extent (z0) [m] [derived]
Const SWIRL_BOX_3                  As Double  = 0.196288     ' swirl extent (x1) [m] [derived]
Const SWIRL_BOX_4                  As Double  = 0.196288     ' swirl extent (y1) [m] [derived]
Const SWIRL_BOX_5                  As Double  = 0#           ' swirl extent (z1) [m] [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL As Double = 0.0001   ' relative, on each body's volume
Const BOX_TOL As Double = 0.00001  ' absolute [m], on each body's extent
Const AREA_TOL As Double = 0.0001  ' relative, on a boundary's area
Const FACE_TOL As Double = 0.000001
Const DIR_TOL As Double = 0.000001

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim md      As SldWorks.Modeler
Dim mu      As SldWorks.MathUtility

Dim nB As Long
Dim bName() As String, bGroup() As String, bKind() As String
Dim bP() As Double, bV() As Double, bBox() As Double, bRGB() As Double

Dim boxSwap As Boolean, boxBase As Boolean

Dim buildLog As String
Dim phase As String
Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStlUnits As Long, oldStlQuality As Long
Dim oldStepAppear As Boolean, oldStlBinary As Boolean
Dim oldStlNoShift As Boolean, oldStlInfo As Boolean
Dim oldStlDev As Double, oldStlAngle As Double


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

    phase = "reading the bodies"
    ReadBodies
    phase = "building the channels"
    Build
    phase = "verifying the channels"
    Verify
    phase = "tagging the boundary faces"
    TagBoundaryFaces
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog PART_NAME & " built, verified and exported"
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln burner"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln burner"
    End If
End Sub


'==================================================================
' The generated records: name|group|kind|params|V|box(6)|rgb(3)
'==================================================================
Private Sub ReadBodies()
    Dim all As String, recs As Variant, f As Variant
    Dim i As Long, j As Long, np As Long, k As Long

    all = KBR_1 & KBR_2 & KBR_3 & KBR_4 & KBR_5 & KBR_6 & KBR_7 & KBR_8 & KBR_9 & KBR_10 & KBR_11 & KBR_12 & _
          KBR_13 & KBR_14 & KBR_15 & KBR_16 & KBR_17 & KBR_18 & KBR_19 & KBR_20 & KBR_21 & KBR_22 & KBR_23 & KBR_24
    recs = Split(all, ";")
    nB = CLng(N_BODIES)
    ReDim bName(nB - 1): ReDim bGroup(nB - 1): ReDim bKind(nB - 1)
    ReDim bP(nB - 1, 15): ReDim bV(nB - 1): ReDim bBox(nB - 1, 5): ReDim bRGB(nB - 1, 2)

    i = 0
    For j = 0 To UBound(recs)
        If Len(recs(j)) > 0 Then
            If i >= nB Then Fail "more body records than N_BODIES (" & nB & ")."
            f = Split(recs(j), "|")
            bName(i) = f(0): bGroup(i) = f(1): bKind(i) = f(2)
            np = KindParams(bKind(i))
            If np = 0 Then Fail "body " & bName(i) & ": unknown kind " & bKind(i) & "."
            If UBound(f) <> 2 + np + 1 + 6 + 3 Then Fail "body " & bName(i) & ": " & (UBound(f) + 1) & " fields."
            For k = 0 To np - 1: bP(i, k) = Val(f(3 + k)): Next k
            bV(i) = Val(f(3 + np))
            For k = 0 To 5: bBox(i, k) = Val(f(4 + np + k)): Next k
            For k = 0 To 2: bRGB(i, k) = Val(f(10 + np + k)): Next k
            i = i + 1
        End If
    Next j
    If i <> nB Then Fail i & " body records, N_BODIES says " & nB & "."
    Note nB & " bodies read from the generated block"
End Sub


Private Function KindParams(ByVal kind As String) As Long
    Select Case kind
        Case "ring": KindParams = 4
        Case "slot": KindParams = 7
        Case "cyl": KindParams = 8
        Case "hole": KindParams = 16
    End Select
End Function


'==================================================================
' Build: each record a modeler body, checked; a channel's bodies
' joined into one; each channel a body of the part
'==================================================================
Private Sub Build()
    Dim grp As Variant, i As Long, k As Long
    Dim b As SldWorks.Body2, acc As SldWorks.Body2, res As Variant, e As Long
    Dim f As SldWorks.Feature, nParts As Long, pass As Long

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set md = swApp.GetModeler
    Set mu = swApp.GetMathUtility

    ProbeBox
    k = 0
    For Each grp In Array("coal", "axial", "swirl")
        Set acc = Nothing
        nParts = 0
        ' the plenum (ring) first: each opening then joins it, one body
        For pass = 0 To 1
        For i = 0 To nB - 1
            If bGroup(i) = grp And ((pass = 0) = (bKind(i) = "ring" Or bKind(i) = "cyl")) Then
                Set b = MakeBody(i)
                If b Is Nothing Then Fail "could not make " & bName(i) & "."
                If Not BoxIs(b, i) Then Fail bName(i) & " came out at " & BoxText(b) & ", expected " & WantText(i) & "."
                If Abs(Volume(b) - bV(i)) > VOL_TOL * bV(i) Then _
                    Fail bName(i) & " is " & Fmt(Volume(b)) & " m3, expected " & Fmt(bV(i)) & " m3."
                If acc Is Nothing Then
                    Set acc = b
                Else
                    res = acc.Operations2(SWBODYADD, b, e)
                    If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail grp & ": joining " & bName(i) & " failed (" & e & ")."
                    If UBound(res) <> 0 Then Fail grp & ": joining " & bName(i) & " left " & (UBound(res) + 1) & " bodies (it does not reach the plenum)."
                    Set acc = res(0)
                End If
                nParts = nParts + 1
            End If
        Next i
        Next pass
        If acc Is Nothing Then Fail "no body for the " & grp & " channel."
        Set f = swPart.CreateFeatureFromBody3(acc, False, 0)
        If f Is Nothing Then Fail "CreateFeatureFromBody3 failed on the " & grp & " channel."
        NameNewBody CStr(grp), k
        Note "channel " & grp & ": " & nParts & " bodies joined into one"
        k = k + 1
    Next grp
End Sub


Private Function MakeBody(ByVal i As Long) As SldWorks.Body2
    Dim outer As SldWorks.Body2, inner As SldWorks.Body2, res As Variant, e As Long
    Dim b As SldWorks.Body2, t As SldWorks.Body2, slab As SldWorks.Body2, cut As SldWorks.Body2, k As Long
    Dim ca As Double, sa As Double
    Select Case bKind(i)
        Case "ring"
            Set outer = CylBody(0#, 0#, bP(i, 2), 0#, 0#, 1#, bP(i, 1), bP(i, 3) - bP(i, 2))
            Set inner = CylBody(0#, 0#, bP(i, 2) - 0.01, 0#, 0#, 1#, bP(i, 0), bP(i, 3) - bP(i, 2) + 0.02)
            res = outer.Operations2(SWBODYCUT, inner, e)
            If e <> swBodyOperationNoError Or IsEmpty(res) Then Fail bName(i) & ": the ring's cut failed (" & e & ")."
            If UBound(res) <> 0 Then Fail bName(i) & ": the ring's cut gave " & (UBound(res) + 1) & " bodies."
            Set MakeBody = res(0)
        Case "cyl"
            Set MakeBody = CylBody(bP(i, 0), bP(i, 1), bP(i, 2), bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7))
        Case "slot"
            ' l x w at the origin (z0 .. z1), turned alpha about +z, moved to (cx, cy);
            ' the transform's row convention is not trusted: both readings, the extent decides
            Set b = BoxBody(-0.5 * bP(i, 4), 0.5 * bP(i, 4), -0.5 * bP(i, 5), 0.5 * bP(i, 5), bP(i, 2), bP(i, 3))
            ca = Cos(bP(i, 6)): sa = Sin(bP(i, 6))
            For k = 0 To 1
                Set t = b.Copy
                t.ApplyTransform Frame(ca, sa, 0#, -sa, ca, 0#, 0#, 0#, 1#, bP(i, 0), bP(i, 1), 0#, k = 1)
                If BoxIs(t, i) Then Set MakeBody = t: Exit Function
            Next k
            Fail bName(i) & ": neither reading of the turn put it at " & WantText(i) & " (last " & BoxText(t) & ")."
        Case "hole"
            ' a x a x H centred at the origin, its axes put on (e1, e2, d) at P,
            ' then cut to the slab z0 .. z1
            Set b = BoxBody(-0.5 * bP(i, 12), 0.5 * bP(i, 12), -0.5 * bP(i, 12), 0.5 * bP(i, 12), _
                            -0.5 * bP(i, 13), 0.5 * bP(i, 13))
            For k = 0 To 1
                Set t = b.Copy
                t.ApplyTransform Frame(bP(i, 3), bP(i, 4), bP(i, 5), bP(i, 6), bP(i, 7), bP(i, 8), _
                                       bP(i, 9), bP(i, 10), bP(i, 11), bP(i, 0), bP(i, 1), bP(i, 2), k = 1)
                Set slab = CylBody(0#, 0#, bP(i, 14), 0#, 0#, 1#, 2#, bP(i, 15) - bP(i, 14))
                res = t.Operations2(SWBODYINTERSECT, slab, e)
                If e = swBodyOperationNoError And Not IsEmpty(res) Then
                    If UBound(res) = 0 Then
                        Set cut = res(0)
                        If BoxIs(cut, i) Then Set MakeBody = cut: Exit Function
                    End If
                End If
            Next k
            Fail bName(i) & ": neither reading of the frame put it at " & WantText(i) & "."
    End Select
End Function


' Local x, y, z onto (ax, ay, az), (bx, by, bz), (cx, cy, cz), then moved
' by (tx, ty, tz); the rotation's rows or its columns (transposed).
Private Function Frame(ByVal ax As Double, ByVal ay As Double, ByVal az As Double, _
                       ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                       ByVal cx As Double, ByVal cy As Double, ByVal cz As Double, _
                       ByVal tx As Double, ByVal ty As Double, ByVal tz As Double, _
                       ByVal transposed As Boolean) As SldWorks.MathTransform
    Dim t(15) As Double
    If transposed Then
        t(0) = ax: t(1) = bx: t(2) = cx
        t(3) = ay: t(4) = by: t(5) = cy
        t(6) = az: t(7) = bz: t(8) = cz
    Else
        t(0) = ax: t(1) = ay: t(2) = az
        t(3) = bx: t(4) = by: t(5) = bz
        t(6) = cx: t(7) = cy: t(8) = cz
    End If
    t(9) = tx: t(10) = ty: t(11) = tz
    t(12) = 1#
    Set Frame = mu.CreateTransform(t)
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
' probed conventions (kiln_rotax.bas).
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
    Note "CreateBodyFromBox3: width along " & IIf(boxSwap, "y", "x") & ", point at the " & IIf(boxBase, "base", "middle")
End Sub


' The body the last feature made: the one not yet named. Named, painted.
Private Sub NameNewBody(ByVal nm As String, ByVal have As Long)
    Dim bodies As Variant, body As SldWorks.Body2, found As SldWorks.Body2
    Dim k As Long, n As Long
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "no body after making the " & nm & " channel."
    If UBound(bodies) + 1 <> have + 1 Then _
        Fail "after the " & nm & " channel the part has " & (UBound(bodies) + 1) & " bodies, expected " & (have + 1) & " (channels merged)."
    For k = 0 To UBound(bodies)
        Set body = bodies(k)
        If body.Name <> "coal" And body.Name <> "axial" And body.Name <> "swirl" Then Set found = body: n = n + 1
    Next k
    If n <> 1 Then Fail n & " unnamed bodies after the " & nm & " channel, expected 1."
    found.Name = nm
    If found.Name <> nm Then Fail "a body did not take the name " & nm & "."
End Sub


Private Function BodyOf(ByVal nm As String) As SldWorks.Body2
    Dim bodies As Variant, k As Long, body As SldWorks.Body2
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    For k = 0 To UBound(bodies)
        Set body = bodies(k)
        If body.Name = nm Then Set BodyOf = body: Exit Function
    Next k
    Fail "no body named " & nm & "."
End Function


'==================================================================
' Verify: three channels, each its volume and exact extent
'==================================================================
Private Sub Verify()
    Dim bodies As Variant, grp As Variant, body As SldWorks.Body2
    Dim vWant As Double, bx As Variant, x As Variant, k As Long, vSum As Double
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) <> 2 Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not 3."
    For Each grp In Array("coal", "axial", "swirl")
        Set body = BodyOf(grp)
        Select Case grp
            Case "coal": vWant = COAL_V: bx = Array(COAL_BOX_0, COAL_BOX_1, COAL_BOX_2, COAL_BOX_3, COAL_BOX_4, COAL_BOX_5)
            Case "axial": vWant = AXIAL_V: bx = Array(AXIAL_BOX_0, AXIAL_BOX_1, AXIAL_BOX_2, AXIAL_BOX_3, AXIAL_BOX_4, AXIAL_BOX_5)
            Case "swirl": vWant = SWIRL_V: bx = Array(SWIRL_BOX_0, SWIRL_BOX_1, SWIRL_BOX_2, SWIRL_BOX_3, SWIRL_BOX_4, SWIRL_BOX_5)
        End Select
        If Abs(Volume(body) - vWant) > VOL_TOL * vWant Then _
            Fail "the " & grp & " channel is " & Fmt(Volume(body)) & " m3, expected " & Fmt(vWant) & " m3."
        x = ExactBox(body)
        For k = 0 To 5
            If Abs(x(k) - bx(k)) > BOX_TOL Then Fail "the " & grp & " channel sits at " & BoxText(body) & _
                ", expected x " & Fmt(bx(0)) & " .. " & Fmt(bx(3)) & ", y " & Fmt(bx(1)) & " .. " & Fmt(bx(4)) & _
                ", z " & Fmt(bx(2)) & " .. " & Fmt(bx(5)) & "."
        Next k
        vSum = vSum + vWant
        Note "body " & grp & ": " & Fmt(vWant) & " m3, " & BoxText(body)
    Next grp
    Note "flow volume " & Fmt(vSum) & " m3 in three channels"
End Sub


Private Function Volume(b As SldWorks.Body2) As Double
    Dim mp As Variant
    mp = b.GetMassProperties(1#)
    Volume = mp(3)
End Function


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
' Boundary faces: the planes normal to the axis at the tip (outlets)
' and at each channel's upstream end (inlets); the rest is wall
'==================================================================
Private Sub TagBoundaryFaces()
    Dim grp As Variant, body As SldWorks.Body2, faces As Variant, face As SldWorks.Face2
    Dim surf As SldWorks.Surface, p As Variant, i As Long, k As Long
    Dim zIn As Double, nOut As Long, aOut As Double, nIn As Long, aIn As Double
    Dim nWall As Long, aWall As Double, a As Double
    Dim wantN As Long, wantOut As Double, wantIn As Double

    For Each grp In Array("coal", "axial", "swirl")
        Set body = BodyOf(grp)
        Select Case grp
            Case "coal": zIn = COAL_BOX_2: wantN = COAL_N_OUT: wantOut = COAL_A_OUT: wantIn = COAL_A_IN
            Case "axial": zIn = AXIAL_BOX_2: wantN = AXIAL_N_OUT: wantOut = AXIAL_A_OUT: wantIn = AXIAL_A_IN
            Case "swirl": zIn = SWIRL_BOX_2: wantN = SWIRL_N_OUT: wantOut = SWIRL_A_OUT: wantIn = SWIRL_A_IN
        End Select
        nOut = 0: aOut = 0#: nIn = 0: aIn = 0#
        faces = body.GetFaces
        For i = 0 To UBound(faces)
            Set face = faces(i)
            Set surf = face.GetSurface
            k = 0                                  ' 0 wall, 1 inlet, 2 outlet
            If surf.IsPlane Then
                p = surf.PlaneParams               ' normal, root point
                If Abs(Abs(p(2)) - 1#) < DIR_TOL Then
                    If Abs(p(5)) < FACE_TOL Then
                        k = 2
                    ElseIf Abs(p(5) - zIn) < FACE_TOL Then
                        k = 1
                    End If
                End If
            End If
            a = face.GetArea
            Select Case k
            Case 1
                nIn = nIn + 1: aIn = aIn + a
                Select Case grp
                    Case "coal": Paint face, 0.55, 0#, 0#
                    Case "axial": Paint face, 0.9, 0#, 0#
                    Case "swirl": Paint face, 1#, 0.45, 0.45
                End Select
            Case 2
                nOut = nOut + 1: aOut = aOut + a
                Select Case grp
                    Case "coal": Paint face, 0#, 0#, 0.5
                    Case "axial": Paint face, 0#, 0.4, 0.9
                    Case "swirl": Paint face, 0.45, 0.75, 1#
                End Select
            Case Else
                nWall = nWall + 1: aWall = aWall + a
                Paint face, 0.7, 0.7, 0.7
            End Select
        Next i
        CheckFace grp & "_inlet", nIn, 1, aIn, wantIn
        CheckFace grp & "_outlet", nOut, wantN, aOut, wantOut
    Next grp
    Note "boundary wall: " & nWall & " faces, " & Fmt(aWall) & " m2"
    swModel.ClearSelection2 True
End Sub


Private Sub CheckFace(ByVal what As String, ByVal n As Long, ByVal nWant As Long, ByVal a As Double, ByVal aWant As Double)
    If n <> nWant Then Fail "found " & n & " " & what & " faces, expected " & nWant & "."
    If Abs(a - aWant) > AREA_TOL * aWant Then Fail what & " is " & Fmt(a) & " m2, expected " & Fmt(aWant) & " m2."
    Note "boundary " & what & ": " & n & " faces, " & Fmt(a) & " m2"
End Sub


' Set through the property from a typed Double array, read back and
' checked (the colours carry the boundary names into Fluent).
Private Sub Paint(face As SldWorks.Face2, ByVal r As Double, ByVal g As Double, ByVal b As Double)
    Dim m(8) As Double
    Dim got As Variant
    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = 0#: m(8) = 0#
    face.MaterialPropertyValues = m
    got = face.MaterialPropertyValues
    If IsEmpty(got) Then Fail "a face reports no colour after one was set on it."
    If Abs(got(0) - r) > 0.01 Or Abs(got(1) - g) > 0.01 Or Abs(got(2) - b) > 0.01 Then _
        Fail "a face's colour came back as (" & Fmt(got(0)) & ", " & Fmt(got(1)) & ", " & Fmt(got(2)) & _
             ") after being set to (" & Fmt(r) & ", " & Fmt(g) & ", " & Fmt(b) & ")."
End Sub


'==================================================================
' Export: STEP AP214 (carries the face colours), binary STL in metres,
' the SLDPRT and two previews -- as id_fan.bas; the bodies stay apart.
'==================================================================
Private Sub ExportFiles()
    Dim outDir As String, e As Long, w As Long
    outDir = OUT_ROOT & LINE_KEY & "\"
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(outDir, vbDirectory) = "" Then MkDir outDir

    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    oldStlUnits = swApp.GetUserPreferenceIntegerValue(swExportStlUnits)
    oldStlBinary = swApp.GetUserPreferenceToggle(swSTLBinaryFormat)
    oldStlNoShift = swApp.GetUserPreferenceToggle(swSTLDontTranslateToPositive)
    oldStlInfo = swApp.GetUserPreferenceToggle(swSTLShowInfoOnSave)
    oldStlQuality = swApp.GetUserPreferenceIntegerValue(swSTLQuality)
    oldStlDev = swApp.GetUserPreferenceDoubleValue(swSTLDeviation)
    oldStlAngle = swApp.GetUserPreferenceDoubleValue(swSTLAngleTolerance)
    exportPrefsTouched = True

    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True
    swApp.SetUserPreferenceIntegerValue swExportStlUnits, swMETER
    swApp.SetUserPreferenceToggle swSTLBinaryFormat, True
    swApp.SetUserPreferenceToggle swSTLDontTranslateToPositive, True
    swApp.SetUserPreferenceToggle swSTLShowInfoOnSave, False
    swApp.SetUserPreferenceIntegerValue swSTLQuality, swSTLQuality_Custom
    swApp.SetUserPreferenceDoubleValue swSTLDeviation, 0.0001
    swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, 0.1

    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "", swFrontView
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.Extension.SaveAs outDir & PART_NAME & "_front.jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w
    swModel.ShowNamedView2 "", swIsometricView
    swModel.ViewZoomtofit2
    swModel.GraphicsRedraw2
    swModel.Extension.SaveAs outDir & PART_NAME & "_iso.jpg", swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, e, w

    SaveOne outDir & PART_NAME & ".SLDPRT"
    SaveOne outDir & PART_NAME & ".step"
    SaveOne outDir & PART_NAME & ".stl"
End Sub


Private Sub SaveOne(ByVal path As String)
    Dim errs As Long, warns As Long
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If errs <> 0 Then Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    If Dir(path) = "" Then Fail "SolidWorks reported no error but " & path & " is not on disk."
    Note "wrote " & path
End Sub


'==================================================================
' Housekeeping
'==================================================================
Private Sub Restore()
    On Error Resume Next
    If exportPrefsTouched Then
        swApp.SetUserPreferenceIntegerValue swStepAP, oldStepAP
        swApp.SetUserPreferenceToggle swStepExportAppearances, oldStepAppear
        swApp.SetUserPreferenceIntegerValue swExportStlUnits, oldStlUnits
        swApp.SetUserPreferenceToggle swSTLBinaryFormat, oldStlBinary
        swApp.SetUserPreferenceToggle swSTLDontTranslateToPositive, oldStlNoShift
        swApp.SetUserPreferenceToggle swSTLShowInfoOnSave, oldStlInfo
        swApp.SetUserPreferenceIntegerValue swSTLQuality, oldStlQuality
        swApp.SetUserPreferenceDoubleValue swSTLDeviation, oldStlDev
        swApp.SetUserPreferenceDoubleValue swSTLAngleTolerance, oldStlAngle
        exportPrefsTouched = False
    End If
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "kiln_burner", msg
End Sub


Private Sub WriteLog(ByVal outcome As String)
    Dim fn As Integer
    On Error Resume Next
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    fn = FreeFile
    Open OUT_ROOT & LINE_KEY & "\" & PART_NAME & "_build.log" For Output As #fn
    Print #fn, outcome & vbLf & buildLog;
    Close #fn
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
End Function
