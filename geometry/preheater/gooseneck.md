# Gooseneck (kaz boynu)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§5, Ek). Tesis: 5000 t/d, iki özdeş 2500 t/d hattı ([plant_topology.md](../plant_topology.md)).
Bağlantı: kalsinatör tepesi → iki hattın C5'leri; her kol bir hattın C5'ine iner ([cyclone_C5.md](cyclone_C5.md)).

## Geometrik Ölçüler

Kolun çapı yayınlanmıştır: bir 2500 t/d hattının boynu. Tesiste **her kol** bu çaptadır; her kol bir hattın bütün gazını taşır. Boylar yayınlanmamıştır.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Kol iç çapı | 3.5 m | yayınlanmış |
| Ortak boyun çapı (kol × √2) | 4.950 m | türetilmiş |
| Boyunun eğik parçaları (2 adet): boy | 4.950 m | 1 × boyun çapı; modelleme |
| Boyunun eğimi (yataya) | 45.0 ° | modelleme (kullanıcı kararı) |
| Boyunun yatay parçası: boy | 2.475 m | 0.5 × boyun çapı; modelleme |
| Düşey kanal: boy | 4.207 m | 0.85 × boyun çapı; modelleme (kullanıcı kararı) |
| Kanalın ekseni, gövde ekseninin önünde (−y) | 9.660 m | türetilmiş |
| Kemerin tepesi (boru dış kenarı) | 39.105 m | türetilmiş |
| Kanalın başladığı kot (üçüncü parçanın alt ucu) | 33.130 m | türetilmiş |
| Kolların ayrıldığı kot (kanalın alt ucu) | 28.923 m | türetilmiş |
| Kolun boyuna açısı (düşeyden) | 60.0 ° | modelleme (kullanıcı kararı) |
| Kolun eğik parçası: boy (yatay kolun eksenine kadar) | 4.301 m | C5 giriş ekseninden türetilir |
| Kolun yataya döndüğü nokta, x | 3.725 m | türetilmiş |
| Kolun yatay kısmı: boy | 1.750 m | 0.5 × kol çapı; modelleme (kullanıcı çizimi) |
| Kol çıkış yüzü (dikey düzlem), x | 5.475 m | türetilmiş |
| Boru kökünün (çatıyı deldiği nokta) gövde ekseninin önüne kayması | 0.185 m | kapak gövdenin içinde kalsın diye türetilir (5 cm pay) |
| Birinci parçanın gövde içindeki hacmi | 47.546 m³ | türetilmiş |
| Kanal ile bir kolun ortak hacmi | 5.669 m³ | türetilmiş |
| İki kolun ortak hacmi | 4.122 m³ | türetilmiş |
| CFD: kolların yatay kısmının ekseni (C5 giriş ekseni), z | 26.772 m | türetilmiş |
| CFD: hacim | 420.12 m³ | türetilmiş |
| CFD: duvar alanı | 390.91 m² | türetilmiş |
| Tesis: yatay kolun CFD çıkışından C5 namlusuna uzantısı | 2.750 m | türetilmiş |
| **Tesis: hacim (iki kol)** | 473.03 m³ | türetilmiş |
| **Tesis: duvar alanı (iki kol)** | 451.39 m² | türetilmiş |
<!-- END GENERATED -->

**Tesis ve CFD** (kullanıcı kararı, 14 Ekim 2026). Tesiste kollar C5 girişlerine kadar iner: iniş, 45°'lik bir parça ve C5 gövdesine yatay bir bacak (çizim, [plant_topology.md](../plant_topology.md)). Twin bu hacmi kullanır. Kalsinatör CFD'si kolları yatay kolların uç yüzünde, C5'in giriş ekseninde keser; "CFD" satırları o domenindir.

## CFD Geometry

CFD'de kaz boynu üç parçalı bir boyun, düşey bir kanal ve bir Y'dir (kullanıcı kararları, 12 Ekim ve 15 Kasım 2026):
- **Boyun.** Kesiti iki kolun toplamıdır (kol çapı × √2, Ø4.950), hız korunur. Gerekçe: iki kol kalsinatör tavanına yan yana sığmaz (2 × 3.50 = 7.0 > 6.74 m). Boyun üç düz parçadır, birleşimleri mitre: tavanı 45° yukarı-öne delen eğik parça, yatay parça, 45° aşağı-öne inen parça; her biri 1 × boyun çapı. İlk parçanın kapağı gövdenin içinde kalacak kadar önden çıkar (`y_off`).
- **Düşey kanal.** Boyunun inen ucundan aşağı, 1.5 × boyun çapı (7.425 m).
- **Kollar.** Kanalın alt ucunda iki kol ayrılır (kot 25.705 m). Her kol x–z düzleminde düşeyden 60° dışa gider, mitre ile yatay kola döner. Yatay kol 2 kol çapı (7.000 m) uzunluğundadır, ekseni C5'in giriş eksenindedir (z 23.522 m). Kollar ayna simetriktir.

Boylar yayınlanmamıştır; hepsi boyun ve kol çapının katı olan modelleme oranlarıdır, yalnız kol çapı yayınlanmıştır. Kollar C5'in giriş eksenine kadar iner, gövdenin yarı yüksekliğine değil (kullanıcı kararı, 15 Kasım 2026). Değerleri Geometrik Ölçüler'deki tabloda; konumları ve adım hacimleri [calciner.md](../calciner/calciner.md)'deki CFD tablosunda.

## Boundary Faces

`gas_outlet_1` (+x) ve `gas_outlet_2` (−x): yatay kolların dikey uç yüzleri (x = ±10.781 m), her biri bir kol kesiti (9.621 m²).

## Derived Properties

CFD domeninin ve tesisin hacimleri Geometrik Ölçüler'deki tabloda; parça parça hacimler [calciner.md](../calciner/calciner.md)'deki CFD tablosunda.
