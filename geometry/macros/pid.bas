Attribute VB_Name = "pid"
'==================================================================
' P&ID of the plant as the twin models it  ->  one SolidWorks drawing
' per sheet (SLDDRW + PDF + DXF): PH preheater, CA calciner, KI rotary
' kiln, CO grate cooler. A SCHEMATIC, NOT TO SCALE, A1 sheet: ISO
' 10628 / ISA 5.1 symbols placed on a grid. NOT a CFD input -- an
' exception to CLAUDE.md rule 8.
'
' Everything it draws is data. The topology, tags and layout cells are
' geometry/pid/pid.yaml, the line sizes plant_geometry.yaml's, the
' instruments the twin's own variables (geometry/pid/pid.md). They are
' written into the generated block below by tools/gen_geometry.py:
' per sheet SH the strings PID_<SH>_1 .. 16 (records ';', fields '~'),
' PID_<SH>_NO, PID_<SH>_TITLE and PID_<SH>_HASH (the source fingerprint,
' written to pid_<SH>.stamp next to the PDF). Nothing is typed here; a size is
' printed as the generator wrote it.
'
'   E~id~tag~symbol~col~row~w~h~qty~extra~label        equipment
'   L~no~service~fromId~fromPort~toId~toPort~size~status~via   line
'   I~tag~status~at~mount~var~side~along               instrument
'   O~id~line~dir~otherSheetNo~service~label           off-page connector
'   S~id~measured~manipulated~spec                     setpoint
'
' Run: Tools > Macro > New, import this file, run preheater, calciner,
' kiln or cooler (one sheet each). Outputs:
'   geometry\drawings\pid\pid_<SH>.pdf, .dxf, .stamp (committed)
'   geometry\output\2500\pid_<SH>.SLDDRW
'   geometry\output\2500\pid_<SH>_build.log         (tests read it)
'==================================================================
Option Explicit

'------------------------------------------------------------------
' (a) PARAMETERS
'------------------------------------------------------------------
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const PID_PH_NO                    As Long    = 1            ' sheet PH number
Const PID_PH_TITLE                 As String  = "PREHEATER, STRING A (STRING B IDENTICAL)" ' sheet PH title
Const PID_PH_SCOPE                 As String  = "string A"   ' sheet PH: which string(s) it draws
Const PID_PH_HASH                  As String  = "8fb1c3643d85ffac" ' sheet PH source fingerprint
Const PID_PH_1                     As String  = "E~FEEDA~FEED~feed_chute~29~14~2~2~-~-~FEED;E~R1A~R1~riser~29~19.8~2~6~-~-~R1;E~C1A~C1~cyclone~32~18~3~6~2~-~C1;E~C2A~C2~cyclone~25~15~3~6~-~-~C2;E~C3A~C3~cyclone~18~12~3~6~-~-~C3;E~C4A~C4~cyclone~11~9~3~6~-~-~C4;E~C5A~C5~cyclone~4~6~3~6~-~-~C5;E~R2A~R2-R3~riser~22~18.3~2~3~-~-~R2;E~R3A~R2-R3~riser~15~15.3~2~3~-~-~R3;E~R4A~R4~riser~8~12.3~2~3~-~-~R4;E~MP1A~MP~flap_valve~33~16~1~1~-~-~MP;E~MP2A~MP~flap_valve~26~13~1~1~-~-~MP;E~MP3A~MP~flap_valve~19~10~1~1~-~-~MP;E~MP4A~MP~flap_valve~12~7~1~1~-~-~MP;E~MP5A~MP~flap_valve~5~4~1~1~-~-~MP;E~IDFA~IDF~fan~37~29~3~3~1 per string~-~IDF;L~G101~gas~OPC-01~-~C5A~gas_in~D 3.500~Verified~-;L~G102~gas~C5A~gas_out~R4A~gas_in~D 4.777 E~Estimated~-;" ' P&ID records
Const PID_PH_2                     As String  = "L~G103~gas~R4A~gas_out~C4A~gas_in~D 4.777 E~Estimated~-;L~G104~gas~C4A~gas_out~R3A~gas_in~D 4.630 E~Estimated~-;L~G105~gas~R3A~gas_out~C3A~gas_in~D 4.630 E~Estimated~-;L~G106~gas~C3A~gas_out~R2A~gas_in~D 4.630 E~Estimated~-;L~G107~gas~R2A~gas_out~C2A~gas_in~D 4.630 E~Estimated~-;L~G108~gas~C2A~gas_out~R1A~gas_in~D 4.630 E~Estimated~-;L~G109~gas~R1A~gas_out~C1A~gas_in~D 3.070~Verified~-;L~G110~gas~C1A~gas_out~IDFA~gas_in~D 2.400 E~Estimated~-;L~G111~gas~IDFA~gas_out~SNK~stack~-~Unknown~-;L~M101~meal_raw~SRC~raw_meal~FEEDA~in~-~Unknown~-;L~M102~meal_raw~FEEDA~out~R1A~meal_in~D 0.600 E~Estimated~-;L~M103~meal_hot~C1A~dust_out~MP1A~in~D 0.600 E~Estimated~-;" ' P&ID records
Const PID_PH_3                     As String  = "L~M104~meal_hot~MP1A~out~R2A~meal_in~D 0.600 E~Estimated~33.5,10/23,10;L~M105~meal_hot~C2A~dust_out~MP2A~in~D 0.849 E~Estimated~-;L~M106~meal_hot~MP2A~out~R3A~meal_in~D 0.849 E~Estimated~26.5,7.5/16,7.5;L~M107~meal_hot~C3A~dust_out~MP3A~in~D 0.849 E~Estimated~-;L~M108~meal_hot~MP3A~out~R4A~meal_in~D 0.849 E~Estimated~19.5,5/9,5;L~M109~meal_hot~C4A~dust_out~MP4A~in~D 0.849 E~Estimated~-;L~M110~meal_hot~MP4A~out~OPC-02~-~D 0.849 E~Estimated~-;L~M111~meal_hot~C5A~dust_out~MP5A~in~D 0.696 E~Estimated~-;L~M112~meal_hot~MP5A~out~OPC-03~-~D 0.696 E~Estimated~-;L~D101~dust~C1A~dust_esc~FEEDA~dust_in~-~Unknown~37,22.8/37,15;I~FT-101~Input~M101~P~raw meal feed~top~0;" ' P&ID records
Const PID_PH_4                     As String  = "I~TT-103~Modelled~M103~F~C1 meal outlet T~top~0;I~TT-105~Modelled~M105~F~C2 meal outlet T~top~0;I~TT-107~Modelled~M107~F~C3 meal outlet T~top~0;I~TT-109~Modelled~M109~F~C4 meal outlet T~top~0;I~TT-104~Modelled~G104~F~C4 gas outlet T~top~0;I~TT-106~Modelled~G106~F~C3 gas outlet T~top~0;I~TT-108~Modelled~G108~F~C2 gas outlet T~top~0;I~TT-110~Modelled~G110~F~C1 gas outlet (exhaust) T~top~0;I~AT-110~Input~G110~P~stack O2 target~top~0;I~FT-103~Modelled~G104~F~preheater gas flow~top~0;I~FT-111~Modelled~G111~F~exhaust flow~top~0;I~FT-102~Modelled~G102~F~C5 dust escaping to C4~top~0;I~FT-105~Modelled~D101~F~C1 dust returned with the feed~top~0;I~FT-112~Modelled~M112~F~C5 meal to the kiln~top~0;" ' P&ID records
Const PID_PH_5                     As String  = "I~TI-101~Modelled~C4A~F~preheater shell T (max)~top~0;I~PDI-102~Report-only~C5A~P~C5 dP (Euler)~top~0;I~PDI-103~Report-only~C4A~P~C4 dP (Euler)~top~0;I~PDI-105~Report-only~C3A~P~C3 dP (Euler)~top~0;I~PDI-107~Report-only~C2A~P~C2 dP (Euler)~top~0;I~PDI-109~Report-only~C1A~P~C1 dP (Euler)~top~0;I~JI-101~Report-only~IDFA~P~hydraulic power of the CFD dP~top~0;O~OPC-01~G101~in~2~gas~GOOSENECK GAS TO C5;O~OPC-02~M110~out~2~meal_hot~C4 MEAL TO CALCINER;O~OPC-03~M112~out~3~meal_hot~C5 MEAL VIA THROAT TO KILN INLET CHAMBER;" ' P&ID records
Const PID_PH_6                     As String  = ""           ' P&ID records
Const PID_PH_7                     As String  = ""           ' P&ID records
Const PID_PH_8                     As String  = ""           ' P&ID records
Const PID_PH_9                     As String  = ""           ' P&ID records
Const PID_PH_10                    As String  = ""           ' P&ID records
Const PID_PH_11                    As String  = ""           ' P&ID records
Const PID_PH_12                    As String  = ""           ' P&ID records
Const PID_PH_13                    As String  = ""           ' P&ID records
Const PID_PH_14                    As String  = ""           ' P&ID records
Const PID_PH_15                    As String  = ""           ' P&ID records
Const PID_PH_16                    As String  = ""           ' P&ID records
Const PID_CA_NO                    As Long    = 2            ' sheet CA number
Const PID_CA_TITLE                 As String  = "ILC CALCINER, GOOSENECK AND TERTIARY AIR" ' sheet CA title
Const PID_CA_SCOPE                 As String  = "one for both strings" ' sheet CA: which string(s) it draws
Const PID_CA_HASH                  As String  = "65266406a0a5916d" ' sheet CA source fingerprint
Const PID_CA_1                     As String  = "E~ILC~ILC~vessel~18~6~5~20~-~-~ILC;E~GN~GN~gooseneck~18~27~8~4~-~-~GN;E~TAD~TAD~duct~6~11~8~2~-~-~TAD;E~NOZM~NOZ~nozzle_meal~28~15~3~2~2~-~NOZ meal;E~NOZF~NOZ~nozzle_fuel~28~12~3~2~2~-~NOZ fuel;L~G201~gas~OPC-04~-~ILC~kiln_gas_inlet~D 3.130 E~Estimated~-;L~A201~air_hot~OPC-05~-~TAD~air_in~D 2.439 E~Estimated~-;L~A202~air_hot~TAD~air_out~ILC~tertiary_air_inlet~D 2.439 E~Estimated~-;L~M201~meal_hot~OPC-02~-~NOZM~meal_in~D 0.849 E~Estimated~-;L~M202~meal_hot~NOZM~meal_out~ILC~meal_feed~D 0.849 E~Estimated~-;L~F201~fuel~SRC~fuel_calciner~NOZF~fuel_in~-~Unknown~-;L~F202~fuel~NOZF~fuel_out~ILC~fuel_inlet~D 0.283 E~Estimated~-;L~G202~gas~ILC~gas_outlet~GN~gas_in~D 4.950 E~Estimated~-;" ' P&ID records
Const PID_CA_2                     As String  = "L~G203~gas~GN~gas_out~OPC-01~-~D 3.500~Verified~-;I~FT-201~Modelled~F201~F~calciner fuel~top~0;I~FT-202~Modelled~A202~F~tertiary air~top~0;I~TT-204~Modelled~A202~F~tertiary air T~top~0;I~FT-204~Modelled~M202~F~meal into the calciner~top~0;I~FT-203~Modelled~G203~F~calciner gas flow~top~0;I~TT-202~Modelled~ILC~F~calciner gas T (zone profile)~right~0.92;I~TI-205~Modelled~ILC~F~calciner shell T (max)~right~0.82;I~PDI-201~Report-only~ILC~P~calciner dP (Euler)~right~0.72;O~OPC-01~G203~out~1~gas~GOOSENECK GAS TO C5;O~OPC-02~M201~in~1~meal_hot~C4 MEAL TO CALCINER;O~OPC-04~G201~in~3~gas~KILN GAS TO CALCINER THROAT;O~OPC-05~A201~in~3~air_hot~TERTIARY AIR FROM HOOD;" ' P&ID records
Const PID_CA_3                     As String  = ""           ' P&ID records
Const PID_CA_4                     As String  = ""           ' P&ID records
Const PID_CA_5                     As String  = ""           ' P&ID records
Const PID_CA_6                     As String  = ""           ' P&ID records
Const PID_CA_7                     As String  = ""           ' P&ID records
Const PID_CA_8                     As String  = ""           ' P&ID records
Const PID_CA_9                     As String  = ""           ' P&ID records
Const PID_CA_10                    As String  = ""           ' P&ID records
Const PID_CA_11                    As String  = ""           ' P&ID records
Const PID_CA_12                    As String  = ""           ' P&ID records
Const PID_CA_13                    As String  = ""           ' P&ID records
Const PID_CA_14                    As String  = ""           ' P&ID records
Const PID_CA_15                    As String  = ""           ' P&ID records
Const PID_CA_16                    As String  = ""           ' P&ID records
Const PID_KI_NO                    As Long    = 3            ' sheet KI number
Const PID_KI_TITLE                 As String  = "ROTARY KILN, INLET CHAMBER, HOOD AND BURNER" ' sheet KI title
Const PID_KI_SCOPE                 As String  = "one for both strings" ' sheet KI: which string(s) it draws
Const PID_KI_HASH                  As String  = "b926637a643b7fe2" ' sheet KI source fingerprint
Const PID_KI_1                     As String  = "E~KIC~KIC~chamber~4~14~5~8~-~-~KIC;E~KILN~KILN~rotary_kiln~12~15~15~4~-~zones=2,split=0.4166~KILN;E~HOOD~HOOD~hood~33~11~5~12~-~-~HOOD;E~BRN~BRN~burner~39~16~2~2~-~-~BRN;L~A301~air_primary~SRC~primary_air~BRN~air_in~-~Unknown~-;L~F301~fuel~SRC~fuel_kiln~BRN~fuel_in~-~Unknown~-;L~G301~gas~BRN~flame_out~KILN~burner_in~-~Unknown~-;L~A302~air_hot~OPC-06~-~HOOD~sec_in~-~Unknown~-;L~A303~air_hot~HOOD~sec_out~KILN~air_in~-~Unknown~-;L~A304~air_hot~OPC-07~-~HOOD~ter_in~-~Unknown~-;L~A305~air_hot~HOOD~ter_out~OPC-05~-~-~Unknown~-;L~M301~meal_hot~OPC-03~-~KIC~meal_in~D 0.696 E~Estimated~-;L~M302~meal_hot~KIC~meal_out~KILN~meal_in~-~Unknown~-;L~G302~gas~KILN~gas_out~KIC~gas_in~D 4.800~Verified~-;" ' P&ID records
Const PID_KI_2                     As String  = "L~G303~gas~KIC~gas_out~OPC-04~-~D 3.130 E~Estimated~-;L~K301~clinker~KILN~clinker_out~OPC-08~-~-~Unknown~-;I~FT-301~Modelled~F301~F~kiln fuel~top~0;I~FY-301~Input~F301~P~kiln share of the total fuel~top~0;I~FT-302~Modelled~A301~F~primary air~top~0;I~FY-302~Input~A301~P~primary air share of kiln air~top~0;I~FT-303~Modelled~A303~F~secondary air~top~0;I~TT-301~Modelled~G301~F~gas T into the burning zone~top~0;I~TT-302~Modelled~M302~F~meal T into the burning zone~top~0;I~ST-301~Input~KILN~P~kiln speed (clipped to rpm_min..rpm_max)~top~0;I~TT-303~Modelled~G303~F~kiln gas T at the back end~top~0;I~FT-304~Modelled~G301~F~kiln gas flow, burning zone out~top~0;" ' P&ID records
Const PID_KI_3                     As String  = "I~FT-305~Modelled~G303~F~kiln gas flow to the calciner~top~0;I~FT-306~Modelled~K301~F~clinker from the burning zone~top~0;I~TT-304~Modelled~K301~F~clinker T at the kiln outlet~top~0;I~TI-307~Modelled~KILN~F~transition shell T (max)~top~0;I~TI-308~Modelled~KILN~F~burning shell T (max)~top~0;O~OPC-03~M301~in~1~meal_hot~C5 MEAL VIA THROAT TO KILN INLET CHAMBER;O~OPC-04~G303~out~2~gas~KILN GAS TO CALCINER THROAT;O~OPC-05~A305~out~2~air_hot~TERTIARY AIR FROM HOOD;O~OPC-06~A302~in~4~air_hot~SECONDARY AIR FROM COOLER;O~OPC-07~A304~in~4~air_hot~TERTIARY AIR FROM COOLER;O~OPC-08~K301~out~4~clinker~CLINKER TO COOLER;S~SP-1~AT-401~cfg:fuel.Fuel_rate_total~free_lime_spec (1.5 %);" ' P&ID records
Const PID_KI_4                     As String  = ""           ' P&ID records
Const PID_KI_5                     As String  = ""           ' P&ID records
Const PID_KI_6                     As String  = ""           ' P&ID records
Const PID_KI_7                     As String  = ""           ' P&ID records
Const PID_KI_8                     As String  = ""           ' P&ID records
Const PID_KI_9                     As String  = ""           ' P&ID records
Const PID_KI_10                    As String  = ""           ' P&ID records
Const PID_KI_11                    As String  = ""           ' P&ID records
Const PID_KI_12                    As String  = ""           ' P&ID records
Const PID_KI_13                    As String  = ""           ' P&ID records
Const PID_KI_14                    As String  = ""           ' P&ID records
Const PID_KI_15                    As String  = ""           ' P&ID records
Const PID_KI_16                    As String  = ""           ' P&ID records
Const PID_CO_NO                    As Long    = 4            ' sheet CO number
Const PID_CO_TITLE                 As String  = "GRATE COOLER" ' sheet CO title
Const PID_CO_SCOPE                 As String  = "one for both strings" ' sheet CO: which string(s) it draws
Const PID_CO_HASH                  As String  = "c244fa81c434375b" ' sheet CO source fingerprint
Const PID_CO_1                     As String  = "E~COOL~COOL~grate_cooler~8~10~26~8~-~seg=10,hood=2~COOL;L~A401~air_cooler~SRC~cooler_air~COOL~grate_air~-~Unknown~-;L~A402~air_hot~COOL~hood_1~OPC-06~-~-~Unknown~-;L~A403~air_hot~COOL~hood_2~OPC-07~-~-~Unknown~-;L~A404~air_hot~COOL~vent_outlet~SNK~cooler_vent~-~Unknown~-;L~K401~clinker~OPC-08~-~COOL~clinker_in~-~Unknown~-;L~K402~clinker~COOL~clinker_out~SNK~clinker~-~Unknown~-;I~FT-401~Modelled~A401~F~cooler air~top~0;I~FY-401~Input~A401~P~cooler air per kg clinker~top~0;I~ST-401~Input~COOL~P~grate speed~top~0;I~TT-402~Modelled~A402~F~secondary air T~top~0;I~FT-402~Modelled~A404~F~cooler vent air~top~0;I~TT-404~Modelled~A404~F~vent air T~top~0;" ' P&ID records
Const PID_CO_2                     As String  = "I~TT-403~Modelled~K402~F~clinker T at the cooler outlet~top~0;I~FT-403~Modelled~K402~F~clinker out~top~0;I~AT-401~Report-only~COOL~P~free lime in the clinker~right~0.6;I~TI-405~Modelled~COOL~F~cooler shell T (max)~top~0;O~OPC-06~A402~out~3~air_hot~SECONDARY AIR FROM COOLER;O~OPC-07~A403~out~3~air_hot~TERTIARY AIR FROM COOLER;O~OPC-08~K401~in~3~clinker~CLINKER TO COOLER;" ' P&ID records
Const PID_CO_3                     As String  = ""           ' P&ID records
Const PID_CO_4                     As String  = ""           ' P&ID records
Const PID_CO_5                     As String  = ""           ' P&ID records
Const PID_CO_6                     As String  = ""           ' P&ID records
Const PID_CO_7                     As String  = ""           ' P&ID records
Const PID_CO_8                     As String  = ""           ' P&ID records
Const PID_CO_9                     As String  = ""           ' P&ID records
Const PID_CO_10                    As String  = ""           ' P&ID records
Const PID_CO_11                    As String  = ""           ' P&ID records
Const PID_CO_12                    As String  = ""           ' P&ID records
Const PID_CO_13                    As String  = ""           ' P&ID records
Const PID_CO_14                    As String  = ""           ' P&ID records
Const PID_CO_15                    As String  = ""           ' P&ID records
Const PID_CO_16                    As String  = ""           ' P&ID records
' END GENERATED

' The grid (schematic layout): a cell is CELL on the sheet, the drawing
' area 41 x 32 cells (tools/pid/validate.py checks every cell in it)
Const CELL    As Double = 0.015
Const GX0     As Double = 0.03
Const GY0     As Double = 0.04
Const STUB    As Double = 0.006      ' a routed line leaves a port straight this far
Const TERM_L  As Double = 0.045      ' a terminal (source, sink, off-page connector) this far from its port
Const BUB_R   As Double = 0.005      ' instrument bubble radius
Const BUB_OFF As Double = 0.014      ' bubble centre off its line
Const LBL_H     As Double = 0.0028     ' equipment labels
Const SM      As Double = 0.002      ' line flags, instrument tags, tables
Const CHAR_W  As Double = 0.0017     ' text width per character at SM, for placing a flag (measured on the PDFs: 1.4-1.7 mm)
Const TXT_PAD As Double = 0.0008     ' clear gap kept around a placed text, so two texts do not read as one
Const STAT_H  As Double = 0.0016     ' the M / I / R letter at a bubble's lower right
Const BUB_GAP As Double = 0.014      ' least centre distance of two bubbles on one line (2 BUB_R + 4 mm)
Const OCC_MAX As Long = 600          ' boxes the placed texts, bubbles and stems take
Const ARROW_L As Double = 0.004
Const CAP_H   As Double = 0.002
Const MAXN    As Long = 80
Const PI      As Double = 3.14159265358979

' Sheet [m on paper]: A1 landscape, 1:1
Const PAPER_W As Double = 0.841
Const PAPER_H As Double = 0.594
Const FR_X0 As Double = 0.02, FR_X1 As Double = 0.831, FR_Y0 As Double = 0.01, FR_Y1 As Double = 0.584
Const COL_X0 As Double = 0.651        ' the right column: legend, lists, notes, revisions, title block

' Layers: one per service, as the topology drawing's colours
Const L_EQUIP As String = "EKIPMAN"
Const L_GAS   As String = "GAZ"
Const L_MEAL  As String = "FARIN"
Const L_DUST  As String = "TOZ"
Const L_AIR   As String = "HAVA"
Const L_FUEL  As String = "YAKIT"
Const L_CLINK As String = "KLINKER"
Const L_SIG   As String = "SINYAL"
Const L_INST  As String = "ENSTRUMAN"
Const L_TEXT  As String = "YAZI"
Const L_FRAME As String = "CERCEVE"
Const L_HID   As String = "GIZLI"
Const LAYER_N As Long = 12

Const OUT_ROOT  As String = "C:\Users\engin\carbon_intelligence\geometry\output\"
Const DRAW_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\drawings\"
Const EXT_TOL   As Double = 0.0001    ' sheet extents read back vs drawn [m on paper]

'------------------------------------------------------------------
' Module state
'------------------------------------------------------------------
Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swDraw  As SldWorks.DrawingDoc
Dim swSkMgr As SldWorks.SketchManager

Dim sheetKey As String
Dim nE As Long, nL As Long, nI As Long, nO As Long, nS As Long

Dim eId(1 To MAXN) As String, eTag(1 To MAXN) As String, eSym(1 To MAXN) As String
Dim eQty(1 To MAXN) As String, eExtra(1 To MAXN) As String, eLabel(1 To MAXN) As String
Dim eX0(1 To MAXN) As Double, eY0(1 To MAXN) As Double, eX1(1 To MAXN) As Double, eY1(1 To MAXN) As Double

Dim lNo(1 To MAXN) As String, lSvc(1 To MAXN) As String
Dim lFromId(1 To MAXN) As String, lFromPort(1 To MAXN) As String
Dim lToId(1 To MAXN) As String, lToPort(1 To MAXN) As String
Dim lSize(1 To MAXN) As String, lStat(1 To MAXN) As String, lVia(1 To MAXN) As String
Dim lNp(1 To MAXN) As Long                         ' points of a routed line
Dim lPx(1 To MAXN, 1 To 24) As Double, lPy(1 To MAXN, 1 To 24) As Double
Dim lTerm(1 To MAXN) As Long                      ' 0 none, 1 it starts at a terminal, 2 it ends at one
Dim lTx(1 To MAXN) As Double, lTy(1 To MAXN) As Double, lUx(1 To MAXN) As Double, lUy(1 To MAXN) As Double

Dim iTag(1 To MAXN) As String, iStat(1 To MAXN) As String, iAt(1 To MAXN) As String
Dim iMount(1 To MAXN) As String, iVar(1 To MAXN) As String, iSide(1 To MAXN) As String, iAlong(1 To MAXN) As Double

Dim oId(1 To MAXN) As String, oLine(1 To MAXN) As String, oDir(1 To MAXN) As String
Dim oOther(1 To MAXN) As String, oSvc(1 To MAXN) As String, oLabel(1 To MAXN) As String

Dim sId(1 To MAXN) As String, sMeas(1 To MAXN) As String, sManip(1 To MAXN) As String, sSpec(1 To MAXN) As String

Dim curLayer As String
Dim layerNames(LAYER_N - 1) As String
Dim nLine(LAYER_N - 1) As Long, nArc(LAYER_N - 1) As Long, nNotes As Long
Dim pxMin As Double, pxMax As Double, pyMin As Double, pyMax As Double
Dim noteWarned As Boolean
Dim buildLog As String
Dim phase As String
Dim yNext As Double                               ' where the next list starts, going down the right column
' What is already on the drawing field, for placing flags and connector
' labels where nothing is (16 Nov 2026 review, item 6): one box per text,
' bubble and stem. Equipment boxes and the lines are checked from their own arrays.
Dim occN As Long
Dim occX0(1 To OCC_MAX) As Double, occY0(1 To OCC_MAX) As Double, occX1(1 To OCC_MAX) As Double, occY1(1 To OCC_MAX) As Double


'==================================================================
' Entry points: one sheet each
'==================================================================
Sub preheater()
    Build "PH"
End Sub

Sub calciner()
    Build "CA"
End Sub

Sub kiln()
    Build "KI"
End Sub

Sub cooler()
    Build "CO"
End Sub


Private Sub Build(ByVal which As String)

    Dim why As String
    Dim i As Long
    Dim tpl As String
    Dim ok As Boolean
    Dim dw As Object

    sheetKey = which
    buildLog = ""
    phase = "starting up"
    nNotes = 0: noteWarned = False: occN = 0
    For i = 0 To LAYER_N - 1
        nLine(i) = 0: nArc(i) = 0
    Next i
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "reading the generated data"
    ParseData
    phase = "checking the data"
    CheckData

    phase = "making the sheet"
    tpl = swApp.GetUserPreferenceStringValue(swDefaultTemplateDrawing)
    If tpl = "" Then Fail "no default drawing template is set (Tools > Options > Default Templates)."
    Set swModel = swApp.NewDocument(tpl, swDwgPaperA1size, PAPER_W, PAPER_H)
    If swModel Is Nothing Then Fail "could not create a drawing from " & tpl & "."
    Set swDraw = swModel
    Set swSkMgr = swModel.SketchManager

    ' A blank A1 sheet; allowed to fail (the drawing is still right)
    On Error Resume Next
    Set dw = swDraw
    ok = dw.SetupSheet5(dw.GetCurrentSheet.GetName, swDwgPaperA1size, swDwgTemplateNone, 1#, 1#, _
                        True, "", PAPER_W, PAPER_H, "Default", True)
    If Err.Number <> 0 Or Not ok Then Note "WARNING: could not clear the sheet format; the template's frame stays."
    Err.Clear
    On Error GoTo Failed

    swDraw.EditSheet
    MakeLayers
    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False
    pxMin = 1E+30: pyMin = 1E+30: pxMax = -1E+30: pyMax = -1E+30

    phase = "drawing the equipment"
    DrawEquipment
    phase = "routing the lines"
    RouteLines
    DrawLines
    ' instruments before the connectors' labels and the line flags, which
    ' are placed where no bubble, stem or text is yet
    phase = "placing the instruments"
    DrawInstruments
    DrawSetpoints
    phase = "placing the connectors and the line flags"
    DrawTerminals
    DrawFlags
    phase = "drawing the frame, lists and title block"
    DrawFrame
    DrawLegend
    DrawLineList
    DrawInstrumentList
    DrawNotes
    DrawRevisions
    DrawTitle

    swSkMgr.AddToDB = False
    swSkMgr.DisplayWhenAdded = True
    swModel.ClearSelection2 True

    phase = "verifying the sheet"
    VerifySheet
    swModel.ViewZoomtofit2
    phase = "saving"
    SaveOutputs

    buildLog = "pid " & sheetKey & " built: equipment " & nE & ", lines " & nL & ", instruments " & nI & _
               ", connectors " & nO & vbLf & buildLog
    WriteLog
    Tell "P&ID sheet " & sheetKey & " built and verified." & vbLf & LayerSummary() & vbLf & vbLf & _
           "Full log: " & LogPath(), vbInformation, "P&ID"
    Exit Sub

Failed:
    why = Err.Description
    Restore
    buildLog = "pid " & sheetKey & " ABORTED while " & phase & ": " & why & vbLf & buildLog
    WriteLog
    Tell "P&ID sheet " & sheetKey & " ABORTED." & vbLf & vbLf & "while " & phase & ":" & vbLf & why & _
           vbLf & vbLf & "Full log: " & LogPath(), vbCritical, "P&ID"
End Sub

' The closing message box, left out when OUT_ROOT\quiet.flag exists: a run
' started from WSL (tools/sw_run.py) must not wait on a click; the log
' carries the same text.
Private Sub Tell(ByVal msg As String, ByVal style As Long, ByVal caption As String)
    If Dir(OUT_ROOT & "quiet.flag") <> "" Then Exit Sub
    MsgBox msg, style, caption
End Sub



'==================================================================
' (b) The generated data, read into arrays
'==================================================================
Private Function SheetNo() As Long
    Select Case sheetKey
    Case "PH": SheetNo = PID_PH_NO
    Case "CA": SheetNo = PID_CA_NO
    Case "KI": SheetNo = PID_KI_NO
    Case "CO": SheetNo = PID_CO_NO
    End Select
End Function


Private Function SheetTitle() As String
    Select Case sheetKey
    Case "PH": SheetTitle = PID_PH_TITLE
    Case "CA": SheetTitle = PID_CA_TITLE
    Case "KI": SheetTitle = PID_KI_TITLE
    Case "CO": SheetTitle = PID_CO_TITLE
    End Select
End Function


' Which string(s) the sheet draws, for the title block: string A on the
' preheater; the calciner, kiln and cooler are one for both strings (16 Nov
' sheet check: every sheet said "string A").
Private Function SheetScope() As String
    Select Case sheetKey
    Case "PH": SheetScope = PID_PH_SCOPE
    Case "CA": SheetScope = PID_CA_SCOPE
    Case "KI": SheetScope = PID_KI_SCOPE
    Case "CO": SheetScope = PID_CO_SCOPE
    End Select
End Function


Private Function SheetHash() As String
    Select Case sheetKey
    Case "PH": SheetHash = PID_PH_HASH
    Case "CA": SheetHash = PID_CA_HASH
    Case "KI": SheetHash = PID_KI_HASH
    Case "CO": SheetHash = PID_CO_HASH
    End Select
End Function


Private Function Chunks() As String
    Select Case sheetKey
    Case "PH"
        Chunks = PID_PH_1 & PID_PH_2 & PID_PH_3 & PID_PH_4 & PID_PH_5 & PID_PH_6 & PID_PH_7 & PID_PH_8 & _
                 PID_PH_9 & PID_PH_10 & PID_PH_11 & PID_PH_12 & PID_PH_13 & PID_PH_14 & PID_PH_15 & PID_PH_16
    Case "CA"
        Chunks = PID_CA_1 & PID_CA_2 & PID_CA_3 & PID_CA_4 & PID_CA_5 & PID_CA_6 & PID_CA_7 & PID_CA_8 & _
                 PID_CA_9 & PID_CA_10 & PID_CA_11 & PID_CA_12 & PID_CA_13 & PID_CA_14 & PID_CA_15 & PID_CA_16
    Case "KI"
        Chunks = PID_KI_1 & PID_KI_2 & PID_KI_3 & PID_KI_4 & PID_KI_5 & PID_KI_6 & PID_KI_7 & PID_KI_8 & _
                 PID_KI_9 & PID_KI_10 & PID_KI_11 & PID_KI_12 & PID_KI_13 & PID_KI_14 & PID_KI_15 & PID_KI_16
    Case "CO"
        Chunks = PID_CO_1 & PID_CO_2 & PID_CO_3 & PID_CO_4 & PID_CO_5 & PID_CO_6 & PID_CO_7 & PID_CO_8 & _
                 PID_CO_9 & PID_CO_10 & PID_CO_11 & PID_CO_12 & PID_CO_13 & PID_CO_14 & PID_CO_15 & PID_CO_16
    Case Else
        Fail "unknown sheet " & sheetKey & "."
    End Select
End Function


Private Sub ParseData()
    Dim rows As Variant, f As Variant
    Dim i As Long, t As String

    rows = Split(Chunks(), ";")
    nE = 0: nL = 0: nI = 0: nO = 0: nS = 0
    For i = 0 To UBound(rows)
        If Len(rows(i)) > 0 Then
            f = Split(rows(i), "~")
            t = f(0)
            Select Case t
            Case "E"
                If UBound(f) <> 10 Then Fail "equipment record " & rows(i) & " has " & (UBound(f) + 1) & " fields, not 11."
                nE = nE + 1: If nE > MAXN Then Fail "too many equipment records."
                eId(nE) = f(1): eTag(nE) = f(2): eSym(nE) = f(3)
                eX0(nE) = GX(Val(f(4))): eY0(nE) = GY(Val(f(5)))
                eX1(nE) = eX0(nE) + Val(f(6)) * CELL: eY1(nE) = eY0(nE) + Val(f(7)) * CELL
                eQty(nE) = f(8): eExtra(nE) = f(9): eLabel(nE) = f(10)
            Case "L"
                If UBound(f) <> 9 Then Fail "line record " & rows(i) & " has " & (UBound(f) + 1) & " fields, not 10."
                nL = nL + 1: If nL > MAXN Then Fail "too many line records."
                lNo(nL) = f(1): lSvc(nL) = f(2)
                lFromId(nL) = f(3): lFromPort(nL) = f(4): lToId(nL) = f(5): lToPort(nL) = f(6)
                lSize(nL) = f(7): lStat(nL) = f(8): lVia(nL) = f(9)
            Case "I"
                If UBound(f) <> 7 Then Fail "instrument record " & rows(i) & " has " & (UBound(f) + 1) & " fields, not 8."
                nI = nI + 1: If nI > MAXN Then Fail "too many instrument records."
                iTag(nI) = f(1): iStat(nI) = f(2): iAt(nI) = f(3): iMount(nI) = f(4): iVar(nI) = f(5)
                iSide(nI) = f(6): iAlong(nI) = Val(f(7))
            Case "O"
                If UBound(f) <> 6 Then Fail "connector record " & rows(i) & " has " & (UBound(f) + 1) & " fields, not 7."
                nO = nO + 1: If nO > MAXN Then Fail "too many connector records."
                oId(nO) = f(1): oLine(nO) = f(2): oDir(nO) = f(3): oOther(nO) = f(4): oSvc(nO) = f(5): oLabel(nO) = f(6)
            Case "S"
                If UBound(f) <> 4 Then Fail "setpoint record " & rows(i) & " has " & (UBound(f) + 1) & " fields, not 5."
                nS = nS + 1: If nS > MAXN Then Fail "too many setpoint records."
                sId(nS) = f(1): sMeas(nS) = f(2): sManip(nS) = f(3): sSpec(nS) = f(4)
            Case Else
                Fail "unknown record type " & t & "."
            End Select
        End If
    Next i
    If nE = 0 Or nL = 0 Then Fail "the generated data holds no equipment or no lines (run tools/gen_geometry.py)."
    Note "data: " & nE & " equipment, " & nL & " lines, " & nI & " instruments, " & nO & " connectors, " & nS & " setpoints"
End Sub


Private Sub CheckData()
    Dim i As Long, k As Long, ok As Boolean
    For i = 1 To nL
        If IsEquip(lFromId(i)) Then k = EqIndex(lFromId(i))
        If IsEquip(lToId(i)) Then k = EqIndex(lToId(i))
        If Not IsEquip(lFromId(i)) And Not IsEquip(lToId(i)) Then Fail "line " & lNo(i) & " joins two terminals."
    Next i
    For i = 1 To nI
        ok = (LineIndex(iAt(i)) > 0) Or (EqIndexOrZero(iAt(i)) > 0)
        If Not ok Then Fail "instrument " & iTag(i) & " is at " & iAt(i) & ", which is on no line or equipment of this sheet."
    Next i
    For i = 1 To nO
        If LineIndex(oLine(i)) = 0 Then Fail "connector " & oId(i) & " names line " & oLine(i) & ", not on this sheet."
    Next i
End Sub


Private Function GX(ByVal c As Double) As Double
    GX = GX0 + c * CELL
End Function

Private Function GY(ByVal r As Double) As Double
    GY = GY0 + r * CELL
End Function

Private Function IsEquip(ByVal id As String) As Boolean
    IsEquip = Not (id = "SRC" Or id = "SNK" Or Left(id, 4) = "OPC-")
End Function

Private Function EqIndexOrZero(ByVal id As String) As Long
    Dim i As Long
    For i = 1 To nE
        If eId(i) = id Then EqIndexOrZero = i: Exit Function
    Next i
End Function

Private Function EqIndex(ByVal id As String) As Long
    EqIndex = EqIndexOrZero(id)
    If EqIndex = 0 Then Fail "no equipment " & id & " on sheet " & sheetKey & "."
End Function

Private Function LineIndex(ByVal wanted As String) As Long
    Dim i As Long
    For i = 1 To nL
        If lNo(i) = wanted Then LineIndex = i: Exit Function
    Next i
End Function

' "zones=2,split=0.4166": the value of one key of an equipment's extra
Private Function ExtraVal(ByVal extra As String, ByVal key As String) As Double
    Dim parts As Variant, kv As Variant
    Dim i As Long
    parts = Split(extra, ",")
    For i = 0 To UBound(parts)
        kv = Split(parts(i), "=")
        If UBound(kv) = 1 Then
            If kv(0) = key Then ExtraVal = Val(kv(1)): Exit Function
        End If
    Next i
End Function


'==================================================================
' (c) Ports: where a line meets a symbol, and which way it leaves
'==================================================================
Private Sub PortPos(ByVal id As String, ByVal port As String, ByRef px As Double, ByRef py As Double, _
                    ByRef dx As Double, ByRef dy As Double)
    Dim i As Long
    Dim x0 As Double, y0 As Double, x1 As Double, y1 As Double, w As Double, h As Double, mx As Double, my As Double
    i = EqIndex(id)
    x0 = eX0(i): y0 = eY0(i): x1 = eX1(i): y1 = eY1(i)
    w = x1 - x0: h = y1 - y0: mx = 0.5 * (x0 + x1): my = 0.5 * (y0 + y1)
    px = 0#: py = 0#: dx = 0#: dy = 0#

    Select Case eSym(i)
    Case "cyclone"
        Select Case port
        Case "gas_in": px = x0: py = y0 + 0.8 * h: dx = -1#
        Case "gas_out": px = mx: py = y1: dy = 1#
        Case "dust_out": px = mx: py = y0: dy = -1#
        Case "dust_esc": px = x1: py = y0 + 0.8 * h: dx = 1#
        End Select
    Case "riser"
        Select Case port
        Case "gas_in": px = x0: py = my: dx = -1#
        Case "gas_out": px = x1: py = my: dx = 1#
        Case "meal_in": px = mx: py = y0: dy = -1#
        End Select
    Case "feed_chute"
        Select Case port
        Case "in": px = mx: py = y0: dy = -1#
        Case "out": px = mx: py = y1: dy = 1#
        Case "dust_in": px = x1: py = my: dx = 1#
        End Select
    Case "flap_valve"
        Select Case port
        Case "in": px = mx: py = y1: dy = 1#
        Case "out": px = mx: py = y0: dy = -1#
        End Select
    Case "fan"
        Select Case port
        Case "gas_in": px = x0: py = my: dx = -1#
        Case "gas_out": px = mx: py = y0: dy = -1#
        End Select
    Case "vessel"
        Select Case port
        Case "kiln_gas_inlet": px = mx: py = y0: dy = -1#
        Case "tertiary_air_inlet": px = x0: py = y0 + 0.3 * h: dx = -1#
        Case "meal_feed": px = x1: py = y0 + 0.5 * h: dx = 1#
        Case "fuel_inlet": px = x1: py = y0 + 0.35 * h: dx = 1#
        Case "gas_outlet": px = mx: py = y1: dy = 1#
        End Select
    Case "gooseneck"
        Select Case port
        Case "gas_in": px = x0 + 0.3125 * w: py = y0: dy = -1#
        Case "gas_out": px = x1: py = my: dx = 1#
        End Select
    Case "duct"
        Select Case port
        Case "air_in": px = x0: py = my: dx = -1#
        Case "air_out": px = x1: py = my: dx = 1#
        End Select
    Case "nozzle_meal"
        Select Case port
        Case "meal_in": px = x1: py = my: dx = 1#
        Case "meal_out": px = x0: py = my: dx = -1#
        End Select
    Case "nozzle_fuel"
        Select Case port
        Case "fuel_in": px = x1: py = my: dx = 1#
        Case "fuel_out": px = x0: py = my: dx = -1#
        End Select
    Case "chamber"
        Select Case port
        Case "gas_in": px = x1: py = y0 + 0.55 * h: dx = 1#
        Case "gas_out": px = x0: py = my: dx = -1#
        Case "meal_in": px = mx: py = y1: dy = 1#
        Case "meal_out": px = x1: py = y0 + 0.2 * h: dx = 1#
        End Select
    Case "hood"
        Select Case port
        Case "sec_in": px = x0 + 0.15 * w: py = y0: dy = -1#
        Case "ter_in": px = x0 + 0.85 * w: py = y0: dy = -1#
        Case "sec_out": px = x0: py = y0 + 0.45 * h: dx = -1#
        Case "ter_out": px = mx: py = y1: dy = 1#
        End Select
    Case "rotary_kiln"
        Select Case port
        Case "gas_out": px = x0: py = y0 + 0.7 * h: dx = -1#
        Case "meal_in": px = x0: py = y0 + 0.3 * h: dx = -1#
        Case "burner_in": px = x1: py = y0 + 0.75 * h: dx = 1#
        Case "air_in": px = x1: py = y0 + 0.4 * h: dx = 1#
        Case "clinker_out": px = x1: py = y0 + 0.1 * h: dx = 1#
        End Select
    Case "burner"
        Select Case port
        Case "air_in": px = mx: py = y1: dy = 1#
        Case "fuel_in": px = mx: py = y0: dy = -1#
        Case "flame_out": px = x0: py = my: dx = -1#
        End Select
    Case "grate_cooler"
        Select Case port
        Case "grate_air": px = mx: py = y0 - 0.5 * CELL: dy = -1#
        Case "hood_1": px = x0 + 0.05 * w: py = y1: dy = 1#
        Case "hood_2": px = x0 + 0.25 * w: py = y1: dy = 1#
        Case "vent_outlet": px = x1 - 0.1 * w: py = y1: dy = 1#
        Case "clinker_in": px = x0: py = y0 + 0.7 * h: dx = -1#
        Case "clinker_out": px = x1: py = y0 + 0.2 * h: dx = 1#
        End Select
    End Select
    If dx = 0# And dy = 0# Then Fail "equipment " & id & " (" & eSym(i) & ") has no port " & port & "."
End Sub


'==================================================================
' (d) Routing: orthogonal, port stub to port stub, through the via cells
'==================================================================
Private Sub RouteLines()
    Dim i As Long
    For i = 1 To nL
        RouteOne i
    Next i
    Note "routed " & nL & " lines"
End Sub


Private Sub AddPt(ByVal li As Long, ByVal x As Double, ByVal y As Double)
    Dim n As Long
    n = lNp(li)
    If n > 0 Then
        If Abs(lPx(li, n) - x) < 0.0000001 And Abs(lPy(li, n) - y) < 0.0000001 Then Exit Sub
    End If
    If n >= 24 Then Fail "line " & lNo(li) & " has more than 24 points."
    n = n + 1
    lNp(li) = n: lPx(li, n) = x: lPy(li, n) = y
End Sub


' Join the last point to (x, y) with at most one corner, continuing the
' last segment's direction first.
Private Sub JoinTo(ByVal li As Long, ByVal x As Double, ByVal y As Double)
    Dim n As Long, px As Double, py As Double
    Dim horiz As Boolean
    n = lNp(li)
    px = lPx(li, n): py = lPy(li, n)
    If Abs(x - px) > 0.0000001 And Abs(y - py) > 0.0000001 Then
        If n >= 2 Then
            horiz = Abs(lPy(li, n) - lPy(li, n - 1)) < 0.0000001
        Else
            horiz = True
        End If
        If horiz Then AddPt li, x, py Else AddPt li, px, y
    End If
    AddPt li, x, y
End Sub


Private Sub RouteOne(ByVal li As Long)
    Dim ax As Double, ay As Double, adx As Double, ady As Double
    Dim bx As Double, bpy As Double, bdx As Double, bdy As Double
    Dim v As Variant, c As Variant
    Dim k As Long

    lNp(li) = 0
    lTerm(li) = 0
    If Not IsEquip(lFromId(li)) Then
        PortPos lToId(li), lToPort(li), bx, bpy, bdx, bdy
        lTerm(li) = 1
        lTx(li) = bx + bdx * TERM_L: lTy(li) = bpy + bdy * TERM_L
        lUx(li) = -bdx: lUy(li) = -bdy           ' the flow runs from the terminal into the port
        AddPt li, lTx(li), lTy(li)
        AddPt li, bx, bpy
    ElseIf Not IsEquip(lToId(li)) Then
        PortPos lFromId(li), lFromPort(li), ax, ay, adx, ady
        lTerm(li) = 2
        lTx(li) = ax + adx * TERM_L: lTy(li) = ay + ady * TERM_L
        lUx(li) = adx: lUy(li) = ady
        AddPt li, ax, ay
        AddPt li, lTx(li), lTy(li)
    Else
        PortPos lFromId(li), lFromPort(li), ax, ay, adx, ady
        PortPos lToId(li), lToPort(li), bx, bpy, bdx, bdy
        AddPt li, ax, ay
        AddPt li, ax + adx * STUB, ay + ady * STUB
        If lVia(li) <> "-" Then
            v = Split(lVia(li), "/")
            For k = 0 To UBound(v)
                c = Split(v(k), ",")
                JoinTo li, GX(Val(c(0))), GY(Val(c(1)))
            Next k
        End If
        JoinTo li, bx + bdx * STUB, bpy + bdy * STUB
        JoinTo li, bx, bpy
    End If
    If lNp(li) < 2 Then Fail "line " & lNo(li) & " has no length."
End Sub


Private Function LayerOf(ByVal svc As String) As String
    Select Case svc
    Case "gas", "air_hot": LayerOf = L_GAS
    Case "meal_raw", "meal_hot": LayerOf = L_MEAL
    Case "dust": LayerOf = L_DUST
    Case "air_primary", "air_cooler": LayerOf = L_AIR
    Case "fuel": LayerOf = L_FUEL
    Case "clinker": LayerOf = L_CLINK
    Case Else: Fail "unknown service " & svc & "."
    End Select
End Function


Private Sub DrawLines()
    Dim i As Long, k As Long
    Dim dx As Double, dy As Double, d As Double, n As Long
    Dim s As Long
    For i = 1 To nL
        UseLayer LayerOf(lSvc(i))
        n = lNp(i)
        For k = 1 To n - 1
            LineP lPx(i, k), lPy(i, k), lPx(i, k + 1), lPy(i, k + 1)
        Next k
        dx = lPx(i, n) - lPx(i, n - 1): dy = lPy(i, n) - lPy(i, n - 1)
        d = Sqr(dx * dx + dy * dy)
        ArrowP lPx(i, n), lPy(i, n), dx / d, dy / d, ARROW_L
    Next i
End Sub


' The line flags (number and size), each beside its line's longest piece,
' placed last, where no text, bubble, stem, equipment box or line is.
Private Sub DrawFlags()
    Dim i As Long
    For i = 1 To nL
        FlagOn i, LongestSeg(i)
    Next i
End Sub


' A box now taken on the drawing field [m on paper].
Private Sub Occupy(ByVal x0 As Double, ByVal y0 As Double, ByVal x1 As Double, ByVal y1 As Double)
    If occN >= OCC_MAX Then Exit Sub
    occN = occN + 1
    occX0(occN) = x0: occY0(occN) = y0: occX1(occN) = x1: occY1(occN) = y1
End Sub


' True when the box lies inside the frame and meets no taken box, no
' equipment box (each kept TXT_PAD clear) and no line.
Private Function SpotFree(ByVal x0 As Double, ByVal y0 As Double, ByVal x1 As Double, ByVal y1 As Double) As Boolean
    Dim k As Long, j As Long
    SpotFree = False
    If x0 < FR_X0 + 0.003 Or x1 > FR_X1 - 0.003 Or y0 < FR_Y0 + 0.003 Or y1 > FR_Y1 - 0.003 Then Exit Function
    For k = 1 To occN
        If x1 + TXT_PAD > occX0(k) And x0 - TXT_PAD < occX1(k) And y1 + TXT_PAD > occY0(k) And y0 - TXT_PAD < occY1(k) Then Exit Function
    Next k
    For k = 1 To nE
        If x1 + TXT_PAD > eX0(k) And x0 - TXT_PAD < eX1(k) And y1 + TXT_PAD > eY0(k) And y0 - TXT_PAD < eY1(k) Then Exit Function
    Next k
    For k = 1 To nL
        For j = 1 To lNp(k) - 1
            If SegHitsBox(lPx(k, j), lPy(k, j), lPx(k, j + 1), lPy(k, j + 1), x0, y0, x1, y1) Then Exit Function
        Next j
    Next k
    SpotFree = True
End Function


' The segment a-b enters the box (Liang-Barsky clipping).
Private Function SegHitsBox(ByVal sx0 As Double, ByVal sy0 As Double, ByVal sx1 As Double, ByVal sy1 As Double, _
                            ByVal x0 As Double, ByVal y0 As Double, ByVal x1 As Double, ByVal y1 As Double) As Boolean
    Dim t0 As Double, t1 As Double, ddx As Double, ddy As Double, k As Long
    Dim p(3) As Double, q(3) As Double, r As Double
    ddx = sx1 - sx0: ddy = sy1 - sy0
    p(0) = -ddx: q(0) = sx0 - x0
    p(1) = ddx: q(1) = x1 - sx0
    p(2) = -ddy: q(2) = sy0 - y0
    p(3) = ddy: q(3) = y1 - sy0
    t0 = 0#: t1 = 1#
    For k = 0 To 3
        If Abs(p(k)) < 1E-12 Then
            If q(k) < 0# Then SegHitsBox = False: Exit Function
        Else
            r = q(k) / p(k)
            If p(k) < 0# Then
                If r > t0 Then t0 = r
            Else
                If r < t1 Then t1 = r
            End If
        End If
    Next k
    SegHitsBox = (t0 < t1)
End Function


Private Function LongestSeg(ByVal li As Long) As Long
    Dim k As Long
    Dim best As Double, d As Double
    best = -1#
    For k = 1 To lNp(li) - 1
        d = Abs(lPx(li, k + 1) - lPx(li, k)) + Abs(lPy(li, k + 1) - lPy(li, k))
        If d > best Then best = d: LongestSeg = k
    Next k
End Function


' A line's flag beside its run s: below (level run) or left (vertical run)
' of the middle first, then stepping along the run either way, then the
' other side. A run too short for the flag (a riser's gas run into its
' cyclone) gets it in two lines over the run's upstream end, inside the
' box the line leaves.
Private Sub FlagOn(ByVal li As Long, ByVal s As Long)
    Const STEP_ALONG As Double = 0.003
    Dim txt As String, tw As Double, side As Long, j As Long, off As Double
    Dim ax As Double, ay As Double, ex As Double, ey As Double
    Dim lo As Double, hi As Double, px As Double, pt As Double
    ax = lPx(li, s): ay = lPy(li, s): ex = lPx(li, s + 1): ey = lPy(li, s + 1)
    txt = lNo(li)
    If lSize(li) <> "-" Then txt = txt & " " & lSize(li)
    tw = Len(txt) * CHAR_W
    UseLayer L_TEXT
    If Abs(ey - ay) < 0.0000001 Then
        lo = IIf(ax < ex, ax, ex): hi = IIf(ax < ex, ex, ax)
        For side = 0 To 1
            pt = IIf(side = 0, ay - 0.0012, ay + 0.0012 + SM)
            For j = 0 To 16
                off = STEP_ALONG * ((j + 1) \ 2) * IIf(j Mod 2 = 1, 1#, -1#)
                px = 0.5 * (lo + hi) - 0.5 * tw + off
                If px >= lo + 0.001 And px + tw <= hi - 0.001 Then
                    If SpotFree(px, pt - SM, px + tw, pt) Then
                        LabelPH px, pt, txt, SM: Occupy px, pt - SM, px + tw, pt
                        Exit Sub
                    End If
                End If
            Next j
        Next side
        ' no clear place along the run: two lines over its upstream end
        Dim w2 As Double, x2 As Double
        w2 = IIf(Len(lNo(li)) > Len(lSize(li)), Len(lNo(li)), Len(lSize(li))) * CHAR_W
        x2 = IIf(ex >= ax, lo - 0.0015 - w2, hi + 0.0015)
        LabelPH x2, ay + 0.0012 + 2# * SM + 0.0008, lNo(li), SM
        If lSize(li) <> "-" Then LabelPH x2, ay + 0.0012 + SM, lSize(li), SM
        Occupy x2, ay + 0.0012, x2 + w2, ay + 0.0012 + 2# * SM + 0.0008
        Note "flag " & lNo(li) & ": its run is too short; written in two lines over the run's upstream end"
    Else
        lo = IIf(ay < ey, ay, ey): hi = IIf(ay < ey, ey, ay)
        For side = 0 To 1
            px = IIf(side = 0, ax - tw - 0.002, ax + 0.002)
            For j = 0 To 16
                off = STEP_ALONG * ((j + 1) \ 2) * IIf(j Mod 2 = 1, 1#, -1#)
                pt = 0.5 * (lo + hi) + 0.5 * SM + off
                If pt - SM >= lo + 0.001 And pt <= hi - 0.001 Then
                    If SpotFree(px, pt - SM, px + tw, pt) Then
                        LabelPH px, pt, txt, SM: Occupy px, pt - SM, px + tw, pt
                        Exit Sub
                    End If
                End If
            Next j
        Next side
        px = ax - tw - 0.002: pt = 0.5 * (lo + hi) + 0.5 * SM
        LabelPH px, pt, txt, SM: Occupy px, pt - SM, px + tw, pt
        Note "flag " & lNo(li) & ": no clear place beside its run; left of its middle"
    End If
End Sub


' An arrow head, its tip at (px, py), pointing along (dx, dy).
Private Sub ArrowP(ByVal px As Double, ByVal py As Double, ByVal dx As Double, ByVal dy As Double, ByVal hd As Double)
    Dim k As Long, sg As Double
    For k = 0 To 1
        sg = 1# - 2# * k
        LineP px, py, px - dx * hd - sg * dy * 0.4 * hd, py - dy * hd + sg * dx * 0.4 * hd
    Next k
End Sub


'==================================================================
' (e) Symbols (ISO 10628 / ISA 5.1, simplified), all in sheet metres
'==================================================================
Private Sub DrawEquipment()
    Dim i As Long
    For i = 1 To nE
        UseLayer L_EQUIP
        Select Case eSym(i)
        Case "cyclone": SymCyclone i
        Case "riser", "feed_chute", "duct", "nozzle_meal", "nozzle_fuel", "chamber", "hood", "gooseneck", "burner"
            RectP eX0(i), eY0(i), eX1(i), eY1(i)
        Case "flap_valve": SymValve i
        Case "fan": SymFan i
        Case "vessel": SymVessel i
        Case "rotary_kiln": SymKiln i
        Case "grate_cooler": SymCooler i
        Case Else: Fail "no symbol for " & eSym(i) & "."
        End Select
        EquipLabel i
    Next i
End Sub


Private Sub EquipLabel(ByVal i As Long)
    Dim txt As String, tw As Double
    txt = eLabel(i)
    If eQty(i) <> "-" Then txt = txt & " (" & eQty(i) & ")"
    tw = Len(txt) * 0.0017
    UseLayer L_TEXT
    Select Case eSym(i)
    Case "flap_valve"
        LabelPH eX1(i) + 0.002, 0.5 * (eY0(i) + eY1(i)) + 0.5 * LBL_H, txt, LBL_H
        Occupy eX1(i) + 0.002, 0.5 * (eY0(i) + eY1(i)) - 0.5 * LBL_H, eX1(i) + 0.002 + tw, 0.5 * (eY0(i) + eY1(i)) + 0.5 * LBL_H
    Case "fan"
        LabelPH 0.5 * (eX0(i) + eX1(i)) - 0.5 * tw, 0.5 * (eY0(i) + eY1(i)) + 0.5 * LBL_H, txt, LBL_H
    Case Else
        LabelPH eX0(i) + 0.002, eY1(i) - 0.002, txt, LBL_H
    End Select
End Sub


Private Sub SymCyclone(ByVal i As Long)
    Dim x0 As Double, y0 As Double, x1 As Double, y1 As Double, w As Double, h As Double, mx As Double, yb As Double
    x0 = eX0(i): y0 = eY0(i): x1 = eX1(i): y1 = eY1(i)
    w = x1 - x0: h = y1 - y0: mx = 0.5 * (x0 + x1): yb = y0 + 0.4 * h
    LineP x0, y1, x1, y1                          ' roof
    LineP x0, y1, x0, yb                          ' barrel
    LineP x1, y1, x1, yb
    LineP x0, yb, mx - 0.1 * w, y0                ' cone
    LineP x1, yb, mx + 0.1 * w, y0
    LineP mx - 0.1 * w, y0, mx + 0.1 * w, y0      ' dust outlet
    UseLayer L_HID                                ' the vortex finder
    LineP mx - 0.12 * w, y1, mx - 0.12 * w, y0 + 0.62 * h
    LineP mx + 0.12 * w, y1, mx + 0.12 * w, y0 + 0.62 * h
    UseLayer L_EQUIP
End Sub


Private Sub SymValve(ByVal i As Long)
    LineP eX0(i), eY1(i), eX1(i), eY1(i)
    LineP eX1(i), eY1(i), eX0(i), eY0(i)
    LineP eX0(i), eY0(i), eX1(i), eY0(i)
    LineP eX1(i), eY0(i), eX0(i), eY1(i)
End Sub


Private Sub SymFan(ByVal i As Long)
    CircleP 0.5 * (eX0(i) + eX1(i)), 0.5 * (eY0(i) + eY1(i)), 0.5 * (eX1(i) - eX0(i))
End Sub


Private Sub SymVessel(ByVal i As Long)
    Dim x0 As Double, y0 As Double, x1 As Double, y1 As Double, w As Double, h As Double, mx As Double, yb As Double
    x0 = eX0(i): y0 = eY0(i): x1 = eX1(i): y1 = eY1(i)
    w = x1 - x0: h = y1 - y0: mx = 0.5 * (x0 + x1): yb = y0 + 0.2 * h
    LineP x0, y1, x1, y1                          ' roof
    LineP x0, y1, x0, yb                          ' cylinder
    LineP x1, y1, x1, yb
    LineP x0, yb, mx - 0.15 * w, y0               ' cone to the throat, open
    LineP x1, yb, mx + 0.15 * w, y0
End Sub


Private Sub SymKiln(ByVal i As Long)
    Dim sp As Double, xs As Double
    RectP eX0(i), eY0(i), eX1(i), eY1(i)
    sp = ExtraVal(eExtra(i), "split")
    If sp > 0# Then
        xs = eX0(i) + sp * (eX1(i) - eX0(i))
        UseLayer L_HID                            ' the twin's two zones
        LineP xs, eY0(i), xs, eY1(i)
        UseLayer L_TEXT
        LabelPH eX0(i) + 0.003, eY0(i) + 0.006, "TRANSITION ZONE", SM
        LabelPH xs + 0.003, eY0(i) + 0.006, "BURNING ZONE", SM
        UseLayer L_EQUIP
    End If
End Sub


Private Sub SymCooler(ByVal i As Long)
    Dim n As Long, k As Long
    Dim xa As Double, xb As Double, yh As Double, x As Double
    RectP eX0(i), eY0(i), eX1(i), eY1(i)
    n = CLng(ExtraVal(eExtra(i), "seg"))
    If n > 0 Then
        yh = eY0(i) - 0.5 * CELL
        For k = 1 To n                            ' the undergrate air's segments
            x = eX0(i) + (k - 0.5) * (eX1(i) - eX0(i)) / n
            LineP x, eY0(i), x, yh
            If k = 1 Then xa = x
            If k = n Then xb = x
        Next k
        LineP xa, yh, xb, yh
        UseLayer L_TEXT
        LabelPH eX0(i) + 0.002, yh - 0.0012, "UNDERGRATE AIR, " & n & " SEGMENTS (HOT END LEFT)", SM
        UseLayer L_EQUIP
    End If
End Sub


' (a circle on the sheet)
Private Sub CircleP(ByVal px As Double, ByVal py As Double, ByVal r As Double)
    Dim i As Long
    If swSkMgr.CreateCircleByRadius(px, py, 0#, r) Is Nothing Then Fail "CreateCircleByRadius failed on layer " & curLayer & "."
    i = LayerIndex(curLayer)
    nArc(i) = nArc(i) + 1
    Track px - r, py - r: Track px + r, py + r
End Sub


'==================================================================
' (f) Terminals: sources, sinks and off-page connectors
'==================================================================
Private Sub DrawTerminals()
    Dim i As Long, id As String, port As String
    For i = 1 To nL
        If lTerm(i) > 0 Then
            If lTerm(i) = 1 Then
                id = lFromId(i): port = lFromPort(i)
            Else
                id = lToId(i): port = lToPort(i)
            End If
            UseLayer L_EQUIP
            If id = "SRC" Or id = "SNK" Then
                Bar i, Replace(UCase(port), "_", " ")
            Else
                Pentagon i, id
            End If
        End If
    Next i
End Sub


Private Sub Bar(ByVal li As Long, ByVal txt As String)
    Dim vx As Double, vy As Double, tw As Double, s As Double
    vx = -lUy(li): vy = lUx(li)
    LineP lTx(li) + vx * 0.005, lTy(li) + vy * 0.005, lTx(li) - vx * 0.005, lTy(li) - vy * 0.005
    tw = Len(txt) * CHAR_W
    If lTerm(li) = 2 Then s = 1# Else s = -1#     ' the label on the far side from the line
    UseLayer L_TEXT
    Dim bx0 As Double, btop As Double
    If Abs(lUx(li)) > 0.5 Then
        btop = lTy(li) + 0.5 * SM
        If s * lUx(li) > 0# Then bx0 = lTx(li) + 0.002 Else bx0 = lTx(li) - tw - 0.002
    Else
        bx0 = lTx(li) - 0.5 * tw
        If s * lUy(li) > 0# Then btop = lTy(li) + 0.002 + SM Else btop = lTy(li) - 0.002
    End If
    LabelPH bx0, btop, txt, SM
    Occupy bx0, btop - SM, bx0 + tw, btop
    UseLayer L_EQUIP
End Sub


' The off-page connector: a pentagon pointing the way the stream flows;
' under it the connector's id, the other sheet and what it carries.
Private Sub Pentagon(ByVal li As Long, ByVal id As String)
    Const PL As Double = 0.016, HW As Double = 0.004, TIP As Double = 0.004
    Dim ux As Double, uy As Double, vx As Double, vy As Double
    Dim p0x As Double, p0y As Double, p1x As Double, p1y As Double, ex As Double, ey As Double
    Dim cx As Double, cy As Double, k As Long

    ux = lUx(li): uy = lUy(li): vx = -uy: vy = ux
    If lTerm(li) = 1 Then                         ' the stream comes in: the tip meets the line
        p1x = lTx(li): p1y = lTy(li): p0x = p1x - ux * PL: p0y = p1y - uy * PL
    Else                                          ' the stream goes out: the tip points away
        p0x = lTx(li): p0y = lTy(li): p1x = p0x + ux * PL: p1y = p0y + uy * PL
    End If
    ex = p0x + ux * (PL - TIP): ey = p0y + uy * (PL - TIP)
    LineP p0x + vx * HW, p0y + vy * HW, ex + vx * HW, ey + vy * HW
    LineP ex + vx * HW, ey + vy * HW, p1x, p1y
    LineP p1x, p1y, ex - vx * HW, ey - vy * HW
    LineP ex - vx * HW, ey - vy * HW, p0x - vx * HW, p0y - vy * HW
    LineP p0x - vx * HW, p0y - vy * HW, p0x + vx * HW, p0y + vy * HW

    Occupy IIf(p0x < p1x, p0x, p1x) - HW, IIf(p0y < p1y, p0y, p1y) - HW, IIf(p0x > p1x, p0x, p1x) + HW, IIf(p0y > p1y, p0y, p1y) + HW

    ' The two-line label (connector and sheet, what goes there): over the
    ' symbol (a level connector) or right of it (an upright one) as before,
    ' unless something is there: then under it, or shifted to end at the
    ' symbol's tip, or left of it (16 Nov 2026 review, item 6).
    Dim l1 As String, w As Double, c As Long, lx As Double, lt As Double, ok As Boolean
    For k = 1 To nO
        If oId(k) = id Then
            cx = 0.5 * (p0x + p1x): cy = 0.5 * (p0y + p1y)
            l1 = id & "  SHT " & oOther(k)
            w = IIf(Len(l1) > Len(oLabel(k)), Len(l1), Len(oLabel(k))) * CHAR_W
            ok = False
            For c = 0 To 3
                If Abs(ux) > 0.5 Then
                    lx = IIf(c Mod 2 = 0, cx - 0.008, cx + 0.008 - w)
                    lt = IIf(c < 2, cy + HW + 0.0075, cy - HW - 0.0015)
                Else
                    lx = IIf(c Mod 2 = 0, cx + HW + 0.002, cx - HW - 0.002 - w)
                    lt = IIf(c < 2, cy + 0.003, cy - 0.0015 - 0.0026 - SM)
                End If
                ' a connector at the frame edge: its label slides inside the frame
                If lx < FR_X0 + 0.004 Then lx = FR_X0 + 0.004
                If lx + w > FR_X1 - 0.004 Then lx = FR_X1 - 0.004 - w
                If SpotFree(lx, lt - 0.0026 - SM, lx + w, lt) Then ok = True: Exit For
            Next c
            If Not ok Then
                lx = IIf(Abs(ux) > 0.5, cx - 0.008, cx + HW + 0.002)
                lt = IIf(Abs(ux) > 0.5, cy + HW + 0.0075, cy + 0.003)
                If lx < FR_X0 + 0.004 Then lx = FR_X0 + 0.004
                Note "connector " & id & ": no clear place for its label; over / right of the symbol"
            End If
            UseLayer L_TEXT
            LabelPH lx, lt, l1, SM
            LabelPH lx, lt - 0.0026, oLabel(k), SM
            Occupy lx, lt - 0.0026 - SM, lx + w, lt
            UseLayer L_EQUIP
        End If
    Next k
End Sub


'==================================================================
' (g) Instruments and the setpoint
'==================================================================
Private Sub DrawInstruments()
    Dim i As Long, j As Long, n As Long, k As Long
    Dim li As Long, ei As Long, s As Long
    Dim px As Double, py As Double, cx As Double, cy As Double, t As Double
    Dim horiz As Boolean

    For i = 1 To nI
        n = 0: k = 0
        For j = 1 To nI
            If iAt(j) = iAt(i) Then
                n = n + 1
                If j <= i Then k = k + 1
            End If
        Next j
        li = LineIndex(iAt(i))
        UseLayer L_INST
        If li > 0 Then
            s = LongestSeg(li)
            ' evenly along the run, but never closer than BUB_GAP (two bubbles
            ' on a short run touched, their tags ran together: TT-104 / FT-103)
            Dim segL As Double
            segL = Abs(lPx(li, s + 1) - lPx(li, s)) + Abs(lPy(li, s + 1) - lPy(li, s))
            If segL / (n + 1#) >= BUB_GAP Or segL <= 0# Then
                t = k / (n + 1#)
            Else
                t = (0.5 * segL + (k - 0.5 * (n + 1#)) * BUB_GAP) / segL
                If t < 0# Then t = 0#
                If t > 1# Then t = 1#
            End If
            px = lPx(li, s) + (lPx(li, s + 1) - lPx(li, s)) * t
            py = lPy(li, s) + (lPy(li, s + 1) - lPy(li, s)) * t
            horiz = Abs(lPy(li, s + 1) - lPy(li, s)) < 0.0000001
            If horiz Then
                cx = px: cy = py + BUB_OFF
                LineP px, py, cx, cy - BUB_R
                Occupy px - 0.0004, py, px + 0.0004, cy - BUB_R
            Else
                cx = px + BUB_OFF: cy = py
                LineP px, py, cx - BUB_R, cy
                Occupy px, py - 0.0004, cx - BUB_R, py + 0.0004
            End If
        Else
            ei = EqIndex(iAt(i))
            Select Case iSide(i)
            Case "right"                                          ' beside the equipment, iAlong up its side
                cy = eY0(ei) + iAlong(i) * (eY1(ei) - eY0(ei))
                cx = eX1(ei) + 0.012 + BUB_R
                LineP eX1(ei), cy, cx - BUB_R, cy
                Occupy eX1(ei), cy - 0.0004, cx - BUB_R, cy + 0.0004
            Case "left"
                cy = eY0(ei) + iAlong(i) * (eY1(ei) - eY0(ei))
                cx = eX0(ei) - 0.012 - BUB_R
                LineP eX0(ei), cy, cx + BUB_R, cy
                Occupy cx + BUB_R, cy - 0.0004, eX0(ei), cy + 0.0004
            Case Else                                             ' over the top, right of the gas outlet's line
                cx = 0.5 * (eX0(ei) + eX1(ei)) + 0.010 + (k - 1) * 0.014
                cy = eY1(ei) + BUB_OFF
                LineP cx, eY1(ei), cx, cy - BUB_R
                Occupy cx - 0.0004, eY1(ei), cx + 0.0004, cy - BUB_R
            End Select
        End If
        Bubble cx, cy, iTag(i), iStat(i), iMount(i)
    Next i
End Sub


' ISA 5.1: a circle, a line across it for a panel / soft value; the tag
' over it, then M modelled, I input, R report-only.
' ISA 5.1: the tag inside the bubble, its letters over the middle and its
' number under it (a panel bubble's line between them); the twin's status
' (M modelled, I input, R report-only) small at the lower right, outside.
' Nothing of the tag is outside the circle, so tags do not run into one
' another or into the line flags (16 Nov 2026 review, item 6).
Private Sub Bubble(ByVal cx As Double, ByVal cy As Double, ByVal tag As String, ByVal stat As String, ByVal mount As String)
    Dim k As Long, ltr As String, num As String
    UseLayer L_INST
    CircleP cx, cy, BUB_R
    If mount = "P" Then LineP cx - BUB_R, cy, cx + BUB_R, cy
    k = InStr(tag, "-")
    If k > 0 Then
        ltr = Left(tag, k - 1): num = Mid(tag, k + 1)
    Else
        ltr = tag: num = ""
    End If
    UseLayer L_TEXT
    LabelPH cx - 0.5 * Len(ltr) * CHAR_W, cy + 0.0005 + SM, ltr, SM
    If num <> "" Then LabelPH cx - 0.5 * Len(num) * CHAR_W, cy - 0.0005, num, SM
    LabelPH cx + 0.75 * BUB_R, cy - 0.75 * BUB_R, Left(stat, 1), STAT_H
    Occupy cx - BUB_R, cy - BUB_R - STAT_H, cx + BUB_R + CHAR_W, cy + BUB_R
End Sub


' The only "control" in the twin: an inverse solve, shown as a box and
' a dashed signal to the fuel it sets (not a loop, say so).
Private Sub DrawSetpoints()
    Dim i As Long, li As Long, s As Long
    Dim x0 As Double, y0 As Double, x1 As Double, y1 As Double, tx As Double, ty As Double, ym As Double
    For i = 1 To nS
        x0 = GX(12): y0 = GY(3): x1 = x0 + 14 * CELL: y1 = y0 + 3 * CELL
        UseLayer L_EQUIP
        RectP x0, y0, x1, y1
        UseLayer L_TEXT
        LabelPH x0 + 0.002, y1 - 0.002, sId(i) & "  INVERSE SOLVE (NOT A CONTROL LOOP)", SM
        LabelPH x0 + 0.002, y1 - 0.0075, "measures " & sMeas(i) & ", sets " & sManip(i), SM
        LabelPH x0 + 0.002, y1 - 0.0130, "spec " & sSpec(i), SM
        li = 0
        For s = 1 To nL
            If lSvc(s) = "fuel" And lTerm(s) > 0 And li = 0 Then li = s
        Next s
        If li > 0 Then
            s = LongestSeg(li)
            tx = 0.5 * (lPx(li, s) + lPx(li, s + 1))
            ty = lPy(li, s) + 0.2 * (lPy(li, s + 1) - lPy(li, s))      ' a fifth along, clear of the flag and the bubbles
            ym = 0.5 * (y0 + y1)
            UseLayer L_SIG
            LineP x1, ym, tx - 0.02, ym
            LineP tx - 0.02, ym, tx - 0.02, ty
            LineP tx - 0.02, ty, tx, ty
            ArrowP tx, ty, 1#, 0#, ARROW_L
        End If
    Next i
End Sub


'==================================================================
' (h) Sheet furniture: frame, legend, lists, notes, revisions, title block
'==================================================================
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
        x = FR_X0 + (i - 0.5) * w - 0.3 * 0.0035 * Len(CStr(i))
        LabelPH x, FR_Y1 + 0.0075, CStr(i), 0.0035
        LabelPH x, FR_Y0 - 0.0025, CStr(i), 0.0035
    Next i
    For i = 1 To 8
        y = FR_Y1 - (i - 0.5) * h + 0.5 * 0.0035
        LabelPH FR_X0 - 0.013, y, Chr(64 + i), 0.0035
        LabelPH FR_X1 + 0.0025, y, Chr(64 + i), 0.0035
    Next i
End Sub


Private Sub DrawLegend()
    Dim names As Variant, descr As Variant
    Dim i As Long, y As Double
    Const RH As Double = 0.0055
    names = Array(L_GAS, L_MEAL, L_DUST, L_AIR, L_FUEL, L_CLINK, L_SIG)
    descr = Array("gas, hot air", "raw meal, hot meal", "dust returned with the feed", "cold air", "fuel", "clinker", "setpoint signal")
    UseLayer L_TEXT
    LabelPH COL_X0, 0.58, "LEGEND", 0.0028
    For i = 0 To UBound(names)
        y = 0.57 - i * RH
        UseLayer CStr(names(i))
        LineP COL_X0, y - 0.0015, COL_X0 + 0.014, y - 0.0015
        UseLayer L_TEXT
        LabelPH COL_X0 + 0.017, y, CStr(descr(i)), SM
    Next i
    y = 0.57 - (UBound(names) + 1) * RH
    UseLayer L_INST
    CircleP COL_X0 + 0.007, y - 0.0015, 0.0025
    UseLayer L_TEXT
    LabelPH COL_X0 + 0.017, y, "instrument in the field (modelled value)", SM
    y = y - RH
    UseLayer L_INST
    CircleP COL_X0 + 0.007, y - 0.0015, 0.0025
    LineP COL_X0 + 0.0045, y - 0.0015, COL_X0 + 0.0095, y - 0.0015
    UseLayer L_TEXT
    LabelPH COL_X0 + 0.017, y, "panel / soft value (input or report-only)", SM
    y = y - RH
    LabelPH COL_X0, y, "tag inside the bubble (ISA 5.1); letter at its lower right: M modelled, I input, R report-only", SM
    yNext = y - 0.012
End Sub


Private Function EndText(ByVal id As String, ByVal port As String) As String
    If port = "-" Then EndText = id Else EndText = id & "." & port
End Function


Private Sub DrawLineList()
    Dim i As Long, n As Long
    Dim yT As Double, y As Double
    Const RH As Double = 0.0045
    Const XA As Double = 0.675, XB As Double = 0.78
    yT = yNext
    n = nL + 1
    UseLayer L_TEXT
    LabelPH COL_X0, yT + 0.0065, "LINE LIST (size from plant_geometry.yaml)", 0.0025
    UseLayer L_FRAME
    RectP COL_X0, yT - n * RH, FR_X1, yT
    UseLayer L_TEXT
    For i = 1 To n - 1
        LineP COL_X0, yT - i * RH, FR_X1, yT - i * RH
    Next i
    LineP XA, yT - n * RH, XA, yT
    LineP XB, yT - n * RH, XB, yT
    LabelPH COL_X0 + 0.0015, yT - 0.0012, "Line", SM
    LabelPH XA + 0.0015, yT - 0.0012, "From > To", SM
    LabelPH XB + 0.0015, yT - 0.0012, "Size [m]", SM
    For i = 1 To nL
        y = yT - i * RH - 0.0012
        LabelPH COL_X0 + 0.0015, y, lNo(i), SM
        LabelPH XA + 0.0015, y, EndText(lFromId(i), lFromPort(i)) & " > " & EndText(lToId(i), lToPort(i)), SM
        LabelPH XB + 0.0015, y, lSize(i), SM
    Next i
    yNext = yT - n * RH - 0.012
End Sub


Private Sub DrawInstrumentList()
    Dim i As Long, n As Long
    Dim yT As Double, y As Double
    Const RH As Double = 0.0045
    Const XA As Double = 0.682, XB As Double = 0.79
    If nI = 0 Then Exit Sub
    yT = yNext
    n = nI + 1
    UseLayer L_TEXT
    LabelPH COL_X0, yT + 0.0065, "INSTRUMENT LIST (the twin's own variables, see pid.md)", 0.0025
    UseLayer L_FRAME
    RectP COL_X0, yT - n * RH, FR_X1, yT
    UseLayer L_TEXT
    For i = 1 To n - 1
        LineP COL_X0, yT - i * RH, FR_X1, yT - i * RH
    Next i
    LineP XA, yT - n * RH, XA, yT
    LineP XB, yT - n * RH, XB, yT
    LabelPH COL_X0 + 0.0015, yT - 0.0012, "Tag", SM
    LabelPH XA + 0.0015, yT - 0.0012, "Variable", SM
    LabelPH XB + 0.0015, yT - 0.0012, "Status", SM
    For i = 1 To nI
        y = yT - i * RH - 0.0012
        LabelPH COL_X0 + 0.0015, y, iTag(i), SM
        LabelPH XA + 0.0015, y, iVar(i), SM
        LabelPH XB + 0.0015, y, iStat(i), SM
    Next i
    yNext = yT - n * RH - 0.012
End Sub


Private Sub DrawNotes()
    Dim y As Double
    If yNext < 0.09 Then Fail "the lists leave no room for the notes (" & Format(yNext, "0.000") & " m)."
    y = yNext
    UseLayer L_TEXT
    LabelPH COL_X0, y, "NOTES", 0.0025
    y = y - 0.005
    LabelPH COL_X0, y, "1. Only what the twin models is shown; nothing else is drawn.", SM
    y = y - 0.0035
    LabelPH COL_X0, y, "2. Sizes: D in m; E = estimated; - = no source gives it.", SM
    y = y - 0.0035
    LabelPH COL_X0, y, "3. Schematic, not to scale; positions are grid cells (pid.yaml).", SM
    If sheetKey = "PH" Then
        y = y - 0.0035
        LabelPH COL_X0, y, "4. String B is identical to string A; the ID fan is one per string.", SM
    End If
End Sub


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

    TCell bx0, 0.055, "Created by", ""
    TCell 0.711, 0.055, "Approved by", ""
    TCell 0.771, 0.055, "Document type", "P&ID"
    TCell bx0, 0.046, "Responsible department", ""
    TCell 0.711, 0.046, "Technical reference", "pid.bas"
    TCell 0.771, 0.046, "Document status", "draft, schematic"
    LabelPH bx0 + 0.0015, 0.0362, "Title, supplementary title", CAP_H
    LabelPH bx0 + 0.0015, 0.0335, "PYROPROCESS P&ID", 0.0028
    LabelPH bx0 + 0.0015, 0.0283, SheetTitle(), 0.002
    LabelPH bx0 + 0.0015, 0.0248, "as the twin models it, " & SheetScope(), 0.002
    TCell 0.771, 0.037, "Identification number", ""
    TCellS 0.771, 0.028, "Rev.", ""
    TCellS 0.781, 0.028, "Date of issue", Format(Date, "yyyy-mm-dd")
    TCellS 0.806, 0.028, "Lang.", "EN"
    TCellS 0.816, 0.028, "Sheet", SheetNo() & "/4"
    TCell bx0, 0.019, "Scale", "none (schematic)"
    TCell 0.711, 0.019, "Unit", "m (sizes)"
    TCell 0.771, 0.019, "Source", "pid.md"
End Sub


Private Sub TCell(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.0015, yTop - 0.0008, cap, CAP_H
    If v <> "" Then LabelPH x + 0.0015, yTop - 0.0038, v, LBL_H
End Sub


Private Sub TCellS(ByVal x As Double, ByVal yTop As Double, ByVal cap As String, ByVal v As String)
    LabelPH x + 0.001, yTop - 0.0008, cap, CAP_H * 0.85
    If v <> "" Then LabelPH x + 0.001, yTop - 0.004, v, 0.0025
End Sub


'==================================================================
' (i) Layers and drawing primitives (as plant_topology_2d.bas)
'==================================================================
Private Sub MakeLayers()
    Dim lm As Object
    layerNames(0) = L_EQUIP: layerNames(1) = L_GAS: layerNames(2) = L_MEAL: layerNames(3) = L_DUST
    layerNames(4) = L_AIR: layerNames(5) = L_FUEL: layerNames(6) = L_CLINK: layerNames(7) = L_SIG
    layerNames(8) = L_INST: layerNames(9) = L_TEXT: layerNames(10) = L_FRAME: layerNames(11) = L_HID

    Set lm = swModel.GetLayerManager
    If lm Is Nothing Then Fail "the drawing has no layer manager."
    AddOneLayer lm, L_EQUIP, "equipment symbols, terminals", RGB(0, 0, 0), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_GAS, "gas and hot air", RGB(210, 0, 0), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_MEAL, "raw meal and hot meal", RGB(200, 150, 0), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_DUST, "dust returned with the feed", RGB(200, 150, 0), swLineHIDDEN, swLW_NORMAL
    AddOneLayer lm, L_AIR, "cold air", RGB(30, 90, 220), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_FUEL, "fuel", RGB(0, 140, 60), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_CLINK, "clinker", RGB(120, 70, 20), swLineCONTINUOUS, swLW_NORMAL
    AddOneLayer lm, L_SIG, "setpoint signal", RGB(110, 110, 110), swLineHIDDEN, swLW_THIN
    AddOneLayer lm, L_INST, "instrument bubbles and leaders", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_TEXT, "labels, lists, notes", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THIN
    AddOneLayer lm, L_FRAME, "frame, title block, table borders", RGB(0, 0, 0), swLineCONTINUOUS, swLW_THICK2
    AddOneLayer lm, L_HID, "hidden edges: vortex finders, the kiln's zone split", RGB(0, 0, 0), swLineHIDDEN, swLW_THIN
    Note "layers: " & LAYER_N & " (one per service, as the topology drawing's colours)"
End Sub


Private Sub AddOneLayer(lm As Object, ByVal name As String, ByVal desc As String, ByVal colour As Long, _
                        ByVal style As Long, ByVal weight As Long)
    Dim ret As Variant
    ret = lm.AddLayer(name, desc, colour, style, weight)
    If lm.GetLayer(name) Is Nothing Then
        Fail "layer " & name & " was not created (AddLayer returned " & CStr(ret) & ")."
    End If
End Sub


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


Private Sub LineP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    Dim i As Long
    If Abs(c - a) < 0.0000001 And Abs(d - b) < 0.0000001 Then Fail "a line on layer " & curLayer & " has no length."
    If swSkMgr.CreateLine(a, b, 0#, c, d, 0#) Is Nothing Then Fail "CreateLine failed on layer " & curLayer & "."
    i = LayerIndex(curLayer)
    nLine(i) = nLine(i) + 1
    Track a, b: Track c, d
End Sub


Private Sub RectP(ByVal a As Double, ByVal b As Double, ByVal c As Double, ByVal d As Double)
    LineP a, b, c, b
    LineP c, b, c, d
    LineP c, d, a, d
    LineP a, d, a, b
End Sub


Private Sub Track(ByVal a As Double, ByVal b As Double)
    If a < pxMin Then pxMin = a
    If a > pxMax Then pxMax = a
    If b < pyMin Then pyMin = b
    If b > pyMax Then pyMax = b
End Sub


' A note of text height h, its top left at (px, py) on the sheet. Allowed
' to fail: the drawing is still right without its labels, and the log says so once.
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


'==================================================================
' (j) Verification: the sheet must hold, layer by layer, every line
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
    If Abs(a0 - pxMin) > EXT_TOL Or Abs(a1 - pxMax) > EXT_TOL Or Abs(b0 - pyMin) > EXT_TOL Then
        Fail "the sheet's lines span x " & Fmt(a0) & " .. " & Fmt(a1) & ", y from " & Fmt(b0) & _
             "; drawn to x " & Fmt(pxMin) & " .. " & Fmt(pxMax) & ", y from " & Fmt(pyMin) & "."
    End If
    Note "sheet extents: x " & Fmt(a0) & " .. " & Fmt(a1) & ", y " & Fmt(b0) & " .. " & Fmt(b1) & "; " & nNotes & " notes"
    Note "counts: equipment " & nE & ", lines " & nL & ", instruments " & nI & ", connectors " & nO
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


Private Function Min2(ByVal a As Double, ByVal b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function

Private Function Max2(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function


'==================================================================
' (k) Output and housekeeping
'==================================================================
Private Sub SaveOutputs()
    Dim errs As Long, warns As Long
    Dim drw As String, pdf As String, dxf As String
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    If Dir(DRAW_ROOT, vbDirectory) = "" Then MkDir DRAW_ROOT
    If Dir(DRAW_ROOT & "pid", vbDirectory) = "" Then MkDir DRAW_ROOT & "pid"
    drw = OUT_ROOT & LINE_KEY & "\pid_" & sheetKey & ".SLDDRW"
    pdf = DRAW_ROOT & "pid\pid_" & sheetKey & ".pdf"
    dxf = DRAW_ROOT & "pid\pid_" & sheetKey & ".dxf"
    SaveOne drw, errs, warns
    SaveOne pdf, errs, warns
    SaveOne dxf, errs, warns
    WriteStamp
End Sub


' pid_<SH>.stamp: the source fingerprint this PDF was drawn from
' (tools/pid/encode.py sheet_hash). Written only after the PDF and
' DXF exist; tests/test_pid.py fails while it differs from the source.
Private Sub WriteStamp()
    Dim stp As String
    Dim fn As Integer
    stp = DRAW_ROOT & "pid\pid_" & sheetKey & ".stamp"
    On Error Resume Next
    If Dir(stp) <> "" Then Kill stp
    On Error GoTo 0
    fn = FreeFile
    Open stp For Output As #fn
    Print #fn, SheetHash()
    Close #fn
    If Dir(stp) = "" Then Fail "could not write " & stp & "."
    Note "wrote " & stp & " (source " & SheetHash() & ")"
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


Private Sub Restore()
    On Error Resume Next
    If Not swSkMgr Is Nothing Then
        swSkMgr.AddToDB = False
        swSkMgr.DisplayWhenAdded = True
    End If
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\pid_" & sheetKey & "_build.log"
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
    Err.Raise vbObjectError + 1, "pid", msg
End Sub

Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub

' No trailing decimal separator on whole numbers ("65", not "65,").
Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
    If Right(Fmt, 1) = "," Or Right(Fmt, 1) = "." Then Fmt = Left(Fmt, Len(Fmt) - 1)
End Function
