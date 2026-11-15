# P&ID (boru ve enstrümantasyon diyagramı)

Makro: [`geometry/macros/pid.bas`](../macros/pid.bas). Kaynak: [`geometry/pid/pid.yaml`](pid.yaml). Referans hat: 2500 t/d (bir hat çizilir, ikincisi özdeştir).

**CFD girdisi değildir.** Tesisi **twin'in modellediği hâliyle** gösteren, dört A1 sayfalık bir P&ID'dir; `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır. Çizim şeması [`plant_topology.md`](../plant_topology.md)'dekinden farklıdır: o gerçek ölçekli bir yerleşim şemasıdır, bu ise ekipman, hat ve enstrüman ilişkisini ölçeksiz gösterir.

## Kapsam kuralı (kullanıcı kararı, 14 Kasım 2026)

Yalnız twin'in modellediği çizilir; başka hiçbir enstrüman eklenmez. Twin'de sensör, kontrolör ya da basınç durumu yoktur. Bu yüzden enstrümanlar twin'in **kendi değişkenleridir**: girdiler (`configs/twin_cfg.yaml`), durum ve akış alanları, raporlayıcının sonuçları. Basınç, CO, NOx, fırın torku ve damper konumu twin'de olmadığından çizilmez. `bypass_ratio` kullanılmadığı, `tertiary_air_fraction` yerine geçildiği için çizilmez.

Kapsam listesi `tools/pid/scope.py`'dedir; her anahtar tam bir enstrümanla karşılanır, listede olmayan anahtar reddedilir (`tests/test_pid.py`).

## Tek kaynak

- `pid.yaml` yalnız topoloji, etiket ve yerleşim hücresini taşır. **Ölçü ve proses değeri yazılmaz.**
- Hat boyutu `plant_geometry.yaml`'a referanstır (`yaml:`, `derived:`) ya da yoktur (`absent`, çizimde "-").
- Enstrümanın değeri twin anahtarına referanstır; durumu anahtarın önekinden gelir ve eşleşmesi doğrulanır.
- Makroya giren kopyalar `python3 tools/gen_geometry.py` ile üretilir; bu dokümandaki tablolar da.

| Durum | Anlamı |
|---|---|
| Input | twin'in girdisi (`cfg:`); sahada cihaz yoktur, panelde gösterilir |
| Modelled | twin'in hesapladığı durum ya da akış (`mass:`, `state:`, `stage:`, `attr:`) |
| Report-only | yalnız raporlayıcının hesapladığı değer (`diag:`); hiçbir dengeye girmez |

Hat ölçüsü durumu çizimlerdeki gibidir: yayınlanmış → Verified, türetilmiş / literatür / model → Estimated (çizimde " E"), kaynağı olmayan → Unknown ("-").

## Numaralama

- **Hat:** `<servis harfi><sayfa no><sıra>`; G gaz, M farin, D toz dönüşü, A hava, F yakıt, K klinker. Örnek: G104, M103, A302.
- **Enstrüman (ISA 5.1):** `<harfler>-<sayfa no><sıra>`; TT/TI sıcaklık, FT/FI akış, FY oran, AT analiz, ST hız, PDI fark basıncı, JI güç.
- **Sayfa arası akım:** `OPC-nn` konektörü hattı bitirir; sonraki sayfada o sayfanın kendi numarasıyla yeniden başlar.
- **B hattı** çizilmez. Ekipman etiketleri envanterindir (`tools/drawings/inventory.py`).

## Sayfalar

<!-- BEGIN GENERATED (tools/gen_geometry.py) sheets -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| No | Kod | Başlık | Ekipman | Hat | Enstrüman |
|---|---|---|---|---|---|
| 1 | PH | PREHEATER, STRING A (STRING B IDENTICAL) | 16 | 24 | 22 |
| 2 | CA | ILC CALCINER, GOOSENECK AND TERTIARY AIR | 5 | 9 | 8 |
| 3 | KI | ROTARY KILN, INLET CHAMBER, HOOD AND BURNER | 4 | 12 | 15 |
| 4 | CO | GRATE COOLER | 1 | 6 | 10 |
<!-- END GENERATED -->

## Ekipman

<!-- BEGIN GENERATED (tools/gen_geometry.py) equipment -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Kimlik | Etiket | Sembol | Sayfa | Adet |
|---|---|---|---|---|
| FEEDA | FEED | feed_chute | PH | - |
| R1A | R1 | riser | PH | - |
| C1A | C1 | cyclone | PH | 2 |
| C2A | C2 | cyclone | PH | - |
| C3A | C3 | cyclone | PH | - |
| C4A | C4 | cyclone | PH | - |
| C5A | C5 | cyclone | PH | - |
| R2A | R2-R3 | riser | PH | - |
| R3A | R2-R3 | riser | PH | - |
| R4A | R4 | riser | PH | - |
| MP1A | MP | flap_valve | PH | - |
| MP2A | MP | flap_valve | PH | - |
| MP3A | MP | flap_valve | PH | - |
| MP4A | MP | flap_valve | PH | - |
| MP5A | MP | flap_valve | PH | - |
| IDFA | IDF | fan | PH | 1 per string |
| ILC | ILC | vessel | CA | - |
| GN | GN | gooseneck | CA | - |
| TAD | TAD | duct | CA | - |
| NOZM | NOZ | nozzle_meal | CA | 2 |
| NOZF | NOZ | nozzle_fuel | CA | 2 |
| KIC | KIC | chamber | KI | - |
| KILN | KILN | rotary_kiln | KI | - |
| HOOD | HOOD | hood | KI | - |
| BRN | BRN | burner | KI | - |
| COOL | COOL | grate_cooler | CO | - |
<!-- END GENERATED -->

## Hatlar

<!-- BEGIN GENERATED (tools/gen_geometry.py) lines -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Hat | Servis | Nereden | Nereye | Sayfa | Ölçü [m] | Durum |
|---|---|---|---|---|---|---|
| D101 | dust | C1A.dust_esc | FEEDA.dust_in | PH | - | Unknown |
| G101 | gas | OPC-01 | C5A.gas_in | PH | D 3.500 | Verified |
| G102 | gas | C5A.gas_out | R4A.gas_in | PH | D 4.777 E | Estimated |
| G103 | gas | R4A.gas_out | C4A.gas_in | PH | D 4.777 E | Estimated |
| G104 | gas | C4A.gas_out | R3A.gas_in | PH | D 4.630 E | Estimated |
| G105 | gas | R3A.gas_out | C3A.gas_in | PH | D 4.630 E | Estimated |
| G106 | gas | C3A.gas_out | R2A.gas_in | PH | D 4.630 E | Estimated |
| G107 | gas | R2A.gas_out | C2A.gas_in | PH | D 4.630 E | Estimated |
| G108 | gas | C2A.gas_out | R1A.gas_in | PH | D 4.630 E | Estimated |
| G109 | gas | R1A.gas_out | C1A.gas_in | PH | D 3.070 | Verified |
| G110 | gas | C1A.gas_out | IDFA.gas_in | PH | D 2.400 E | Estimated |
| G111 | gas | IDFA.gas_out | SNK.stack | PH | - | Unknown |
| M101 | meal_raw | SRC.raw_meal | FEEDA.in | PH | - | Unknown |
| M102 | meal_raw | FEEDA.out | R1A.meal_in | PH | D 0.600 E | Estimated |
| M103 | meal_hot | C1A.dust_out | MP1A.in | PH | D 0.600 E | Estimated |
| M104 | meal_hot | MP1A.out | R2A.meal_in | PH | D 0.600 E | Estimated |
| M105 | meal_hot | C2A.dust_out | MP2A.in | PH | D 0.849 E | Estimated |
| M106 | meal_hot | MP2A.out | R3A.meal_in | PH | D 0.849 E | Estimated |
| M107 | meal_hot | C3A.dust_out | MP3A.in | PH | D 0.849 E | Estimated |
| M108 | meal_hot | MP3A.out | R4A.meal_in | PH | D 0.849 E | Estimated |
| M109 | meal_hot | C4A.dust_out | MP4A.in | PH | D 0.849 E | Estimated |
| M110 | meal_hot | MP4A.out | OPC-02 | PH | D 0.849 E | Estimated |
| M111 | meal_hot | C5A.dust_out | MP5A.in | PH | D 0.694 E | Estimated |
| M112 | meal_hot | MP5A.out | OPC-03 | PH | D 0.694 E | Estimated |
| A201 | air_hot | OPC-05 | TAD.air_in | CA | D 2.439 E | Estimated |
| A202 | air_hot | TAD.air_out | ILC.tertiary_air_inlet | CA | D 2.439 E | Estimated |
| F201 | fuel | SRC.fuel_calciner | NOZF.fuel_in | CA | - | Unknown |
| F202 | fuel | NOZF.fuel_out | ILC.fuel_inlet | CA | D 0.283 E | Estimated |
| G201 | gas | OPC-04 | ILC.kiln_gas_inlet | CA | D 3.130 E | Estimated |
| G202 | gas | ILC.gas_outlet | GN.gas_in | CA | D 4.950 E | Estimated |
| G203 | gas | GN.gas_out | OPC-01 | CA | D 3.500 | Verified |
| M201 | meal_hot | OPC-02 | NOZM.meal_in | CA | D 0.849 E | Estimated |
| M202 | meal_hot | NOZM.meal_out | ILC.meal_feed | CA | D 0.849 E | Estimated |
| A301 | air_primary | SRC.primary_air | BRN.air_in | KI | - | Unknown |
| A302 | air_hot | OPC-06 | HOOD.sec_in | KI | - | Unknown |
| A303 | air_hot | HOOD.sec_out | KILN.air_in | KI | - | Unknown |
| A304 | air_hot | OPC-07 | HOOD.ter_in | KI | - | Unknown |
| A305 | air_hot | HOOD.ter_out | OPC-05 | KI | - | Unknown |
| F301 | fuel | SRC.fuel_kiln | BRN.fuel_in | KI | - | Unknown |
| G301 | gas | BRN.flame_out | KILN.burner_in | KI | - | Unknown |
| G302 | gas | KILN.gas_out | KIC.gas_in | KI | D 4.800 | Verified |
| G303 | gas | KIC.gas_out | OPC-04 | KI | - | Unknown |
| K301 | clinker | KILN.clinker_out | OPC-08 | KI | - | Unknown |
| M301 | meal_hot | OPC-03 | KIC.meal_in | KI | D 0.694 E | Estimated |
| M302 | meal_hot | KIC.meal_out | KILN.meal_in | KI | - | Unknown |
| A401 | air_cooler | SRC.cooler_air | COOL.grate_air | CO | - | Unknown |
| A402 | air_hot | COOL.hood_1 | OPC-06 | CO | - | Unknown |
| A403 | air_hot | COOL.hood_2 | OPC-07 | CO | - | Unknown |
| A404 | air_hot | COOL.vent_outlet | SNK.cooler_vent | CO | - | Unknown |
| K401 | clinker | OPC-08 | COOL.clinker_in | CO | - | Unknown |
| K402 | clinker | COOL.clinker_out | SNK.clinker | CO | - | Unknown |
<!-- END GENERATED -->

## Enstrümanlar

Tek "kontrol" `solver/setpoint.py`'daki ters çözümdür (`solve_fuel_rate`): serbest kireç (AT-401) ya da klinker sıcaklığı hedefine göre `Fuel_rate_total`'ı bulur. Döngü değildir; düz çalıştırmada kapalıdır ve çizimde kesikli sinyal çizgisiyle (SP-1) gösterilir. Referans değer sütunu `tests/data/twin_state_reference.json`'dandır; orada olmayan değer "-" yazılır.

<!-- BEGIN GENERATED (tools/gen_geometry.py) instruments -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Etiket | Değişken | Twin anahtarı | Durum | Referans değer (SI) | Yer |
|---|---|---|---|---|---|
| FT-101 | raw meal feed | cfg:feed.Feed_rate_kg_s | Input | - | M101 |
| TT-103 | C1 meal outlet T | stage:4.solid_outlet_temperature | Modelled | 572.8 | M103 |
| TT-105 | C2 meal outlet T | stage:3.solid_outlet_temperature | Modelled | 747.2 | M105 |
| TT-107 | C3 meal outlet T | stage:2.solid_outlet_temperature | Modelled | 879 | M107 |
| TT-109 | C4 meal outlet T | stage:1.solid_outlet_temperature | Modelled | 987.8 | M109 |
| TT-104 | C4 gas outlet T | stage:1.gas_outlet_temperature | Modelled | 980.4 | G104 |
| TT-106 | C3 gas outlet T | stage:2.gas_outlet_temperature | Modelled | 877.5 | G106 |
| TT-108 | C2 gas outlet T | stage:3.gas_outlet_temperature | Modelled | 745 | G108 |
| TT-110 | C1 gas outlet (exhaust) T | stage:4.gas_outlet_temperature | Modelled | 572.4 | G110 |
| AT-110 | stack O2 target | cfg:fuel.O2 | Input | - | G110 |
| FT-103 | preheater gas flow | mass:m_dot_g_preheater | Modelled | 112.5 | G104 |
| FT-111 | exhaust flow | mass:m_dot_exhaust | Modelled | 115.1 | G111 |
| FT-102 | C5 dust escaping to C4 | mass:m_dot_s_C5_dust | Modelled | 7.407 | G102 |
| FT-105 | C1 dust returned with the feed | attr:preheater.m_dot_dust_return | Modelled | - | D101 |
| FT-112 | C5 meal to the kiln | mass:m_dot_s_calciner_out | Modelled | 67.34 | M112 |
| TI-101 | preheater shell T (max) | state:Preheater_T_shell_max | Modelled | - | C4A |
| PDI-102 | C5 dP (Euler) | diag:gas_pressure_losses.rows[C5].dP | Report-only | - | C5A |
| PDI-103 | C4 dP (Euler) | diag:gas_pressure_losses.rows[C4].dP | Report-only | - | C4A |
| PDI-105 | C3 dP (Euler) | diag:gas_pressure_losses.rows[C3].dP | Report-only | - | C3A |
| PDI-107 | C2 dP (Euler) | diag:gas_pressure_losses.rows[C2].dP | Report-only | - | C2A |
| PDI-109 | C1 dP (Euler) | diag:gas_pressure_losses.rows[C1].dP | Report-only | - | C1A |
| JI-101 | hydraulic power of the CFD dP | diag:gas_pressure_losses.total_power_W | Report-only | - | IDFA |
| FT-201 | calciner fuel | mass:m_dot_fuel_calciner | Modelled | 3.418 | F201 |
| FT-202 | tertiary air | mass:m_dot_tertiary_air | Modelled | 50.34 | A202 |
| TT-204 | tertiary air T | state:Tg_tertiary_air | Modelled | - | A202 |
| FT-204 | meal into the calciner | mass:m_dot_s_calciner_in | Modelled | 94.59 | M202 |
| FT-203 | calciner gas flow | mass:m_dot_g_calciner | Modelled | 112.5 | G203 |
| TT-202 | calciner gas T (zone profile) | state:Tg_calciner | Modelled | - | ILC |
| TI-205 | calciner shell T (max) | state:Calciner_T_shell_max | Modelled | - | ILC |
| PDI-201 | calciner dP (Euler) | diag:gas_pressure_losses.rows[calciner].dP | Report-only | - | ILC |
| FT-301 | kiln fuel | mass:m_dot_fuel_kiln | Modelled | 2.095 | F301 |
| FY-301 | kiln share of the total fuel | cfg:fuel.kiln_fraction | Input | - | F301 |
| FT-302 | primary air | mass:m_dot_primary_air | Modelled | 2.64 | A301 |
| FY-302 | primary air share of kiln air | cfg:burning.primary_air_fraction | Input | - | A301 |
| FT-303 | secondary air | mass:m_dot_secondary_air | Modelled | 23.76 | A303 |
| TT-301 | gas T into the burning zone | state:Tg_burning_in | Modelled | - | G301 |
| TT-302 | meal T into the burning zone | state:Ts_burning_in | Modelled | - | M302 |
| ST-301 | kiln speed (clipped to rpm_min..rpm_max) | cfg:motion.rpm_default | Input | - | KILN |
| TT-303 | kiln gas T at the back end | state:Tg_transition[0] | Modelled | 1333 | G303 |
| FT-304 | kiln gas flow, burning zone out | mass:m_dot_g_burning_out | Modelled | 28.49 | G301 |
| FT-305 | kiln gas flow to the calciner | mass:m_dot_g_transition | Modelled | 31.52 | G303 |
| FT-306 | clinker from the burning zone | mass:m_dot_s_burning | Modelled | 56.9 | K301 |
| TT-304 | clinker T at the kiln outlet | state:Ts_burning[-1] | Modelled | 2027 | K301 |
| TI-307 | transition shell T (max) | state:Transition_T_shell_max | Modelled | - | KILN |
| TI-308 | burning shell T (max) | state:Burning_T_shell_max | Modelled | - | KILN |
| FT-401 | cooler air | mass:m_dot_air_cooler | Modelled | 125.2 | A401 |
| FY-401 | cooler air per kg clinker | cfg:cooler_air.cooling_air_rate_kg_per_kg_clinker | Input | - | A401 |
| ST-401 | grate speed | cfg:cooler.grate_speed_m_s | Input | - | COOL |
| TT-402 | secondary air T | state:Tg_secondary_air | Modelled | - | A402 |
| FT-402 | cooler vent air | mass:m_dot_vent_air | Modelled | 51.09 | A404 |
| TT-404 | vent air T | state:Tg_vent_air | Modelled | - | A404 |
| TT-403 | clinker T at the cooler outlet | state:Ts_cooler[-1] | Modelled | 510.3 | K402 |
| FT-403 | clinker out | mass:m_dot_clinker | Modelled | 56.9 | K402 |
| AT-401 | free lime in the clinker | diag:free_lime.free_lime_pct | Report-only | - | COOL |
| TI-405 | cooler shell T (max) | state:Cooler_T_shell_max | Modelled | - | COOL |
<!-- END GENERATED -->

## Sayfa arası bağlantılar

<!-- BEGIN GENERATED (tools/gen_geometry.py) connectors -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Kimlik | Servis | Nereden sayfa | Nereye sayfa | Açıklama |
|---|---|---|---|---|
| OPC-01 | gas | CA | PH | GOOSENECK GAS TO C5 |
| OPC-02 | meal_hot | PH | CA | C4 MEAL TO CALCINER |
| OPC-03 | meal_hot | PH | KI | C5 MEAL VIA THROAT TO KILN INLET CHAMBER |
| OPC-04 | gas | KI | CA | KILN GAS TO CALCINER THROAT |
| OPC-05 | air_hot | KI | CA | TERTIARY AIR FROM HOOD |
| OPC-06 | air_hot | CO | KI | SECONDARY AIR FROM COOLER |
| OPC-07 | air_hot | CO | KI | TERTIARY AIR FROM COOLER |
| OPC-08 | clinker | KI | CO | CLINKER TO COOLER |
<!-- END GENERATED -->

## Doğrulama

Makro her sayfada katman başına çizgi ve yay sayısını geri okur ve çizilenle karşılaştırır; tutmazsa durur. Tablo ilk doğrulanmış çalıştırmalardan alınmıştır (`tests/test_pid.py` log'la karşılaştırır). Bu sayılar okları, bayrakları, listeleri ve anteti içerir; yay sayısı daire sembollerdir (enstrüman balonları, lejant, fan).

**PH, CA, KI ve CO (14 Kasım 2026):** 16 ekipman, 24 hat, 22 enstrüman, 3 konektör; sayfada 303 not. CA: 5 ekipman, 9 hat, 8 enstrüman, 4 konektör; sayfada 176 not. KI: 4 ekipman, 12 hat, 15 enstrüman, 6 konektör; sayfada 225 not. CO: 1 ekipman, 6 hat, 10 enstrüman, 3 konektör; sayfada 169 not.

| Sayfa | Katman | Çizgi | Yay |
|---|---|---|---|
| PH | EKIPMAN | 87 | 1 |
| PH | GAZ | 57 | 0 |
| PH | FARIN | 61 | 0 |
| PH | TOZ | 8 | 0 |
| PH | HAVA | 1 | 0 |
| PH | YAKIT | 1 | 0 |
| PH | KLINKER | 1 | 0 |
| PH | SINYAL | 1 | 0 |
| PH | ENSTRUMAN | 31 | 24 |
| PH | YAZI | 101 | 0 |
| PH | CERCEVE | 20 | 0 |
| PH | GIZLI | 10 | 0 |
| CA | EKIPMAN | 42 | 0 |
| CA | GAZ | 20 | 0 |
| CA | FARIN | 9 | 0 |
| CA | TOZ | 1 | 0 |
| CA | HAVA | 1 | 0 |
| CA | YAKIT | 9 | 0 |
| CA | KLINKER | 1 | 0 |
| CA | SINYAL | 1 | 0 |
| CA | ENSTRUMAN | 10 | 10 |
| CA | YAZI | 72 | 0 |
| CA | CERCEVE | 20 | 0 |
| CA | GIZLI | 0 | 0 |
| KI | EKIPMAN | 52 | 0 |
| KI | GAZ | 31 | 0 |
| KI | FARIN | 10 | 0 |
| KI | TOZ | 1 | 0 |
| KI | HAVA | 4 | 0 |
| KI | YAKIT | 4 | 0 |
| KI | KLINKER | 4 | 0 |
| KI | SINYAL | 6 | 0 |
| KI | ENSTRUMAN | 19 | 17 |
| KI | YAZI | 82 | 0 |
| KI | CERCEVE | 20 | 0 |
| KI | GIZLI | 1 | 0 |
| CO | EKIPMAN | 33 | 0 |
| CO | GAZ | 10 | 0 |
| CO | FARIN | 1 | 0 |
| CO | TOZ | 1 | 0 |
| CO | HAVA | 4 | 0 |
| CO | YAKIT | 1 | 0 |
| CO | KLINKER | 7 | 0 |
| CO | SINYAL | 1 | 0 |
| CO | ENSTRUMAN | 14 | 12 |
| CO | YAZI | 71 | 0 |
| CO | CERCEVE | 20 | 0 |
| CO | GIZLI | 0 | 0 |

Dört sayfa da çalıştırıldı.

## Bilinmeyenler

Kaynağı olmayan hat boyutları (`absent`): ID fan kanalları, primer hava borusu, soğutucu hava kanalları, vent kanalı, klinker taşıma, fırın giriş odası ile fırın arasındaki geçiş. Brülör (G301) ve klinker (K301) hatları fırın başlığının içinden geçer; bilinçli, çünkü ikisi de başlıktan geçer. C1 tozunun besleme ile dönüşü twin'de var (`m_dot_dust_return`) ama filtre nesnesi yoktur; hat ekipmansız çizilir.
