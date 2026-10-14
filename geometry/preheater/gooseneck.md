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
| Boyun yükselişi | 6.187 m | 1.25 × boyun çapı; modelleme |
| 180° dirsek merkez yarıçapı | 5.250 m | 1.5 × kol çapı; modelleme |
| İki dirseğin ortak hacmi | 10.346 m³ | türetilmiş |
| CFD: iniş (gövdenin yarı yüksekliğine) | 21.187 m | türetilmiş |
| CFD: hacim | 833.77 m³ | türetilmiş |
| CFD: duvar alanı | 924.85 m² | türetilmiş |
| Tesis: kol boyu (iniş + 45° + C5 girişine yatay) | 17.520 m | türetilmiş |
| **Tesis: hacim (iki kol)** | 763.20 m³ | türetilmiş |
| **Tesis: duvar alanı (iki kol)** | 844.20 m² | türetilmiş |
<!-- END GENERATED -->

**Tesis ve CFD** (kullanıcı kararı, 14 Ekim 2026). Tesiste kollar C5 girişlerine kadar iner: iniş, 45°'lik bir parça ve C5 gövdesine yatay bir bacak (çizim, [plant_topology.md](../plant_topology.md)). Twin bu hacmi kullanır. Kalsinatör CFD'si kolları gövdenin yarı yüksekliğinde keser (`end_at_vessel_H`, bir CFD sınır seçimi); "CFD" satırları o domenindir.

## CFD Geometry

Kaz boynu, kalsinatör katısının bir parçası olarak kurulur ([calciner.md](../calciner/calciner.md), [`calciner.bas`](../macros/calciner.bas)).

CFD'de kaz boynu bir **Y**'dir (kullanıcı kararı, 12 Ekim 2026):
- **Boyun.** Tavanın ortasından tek bir boyun çıkar. Kesiti iki kolun toplamıdır (kol çapı × √2), hız korunur. Gerekçe: iki kol kalsinatör tavanına yan yana sığmaz (karar günü: 2 × 3.50 = 7.0 > 6.74 m).
- **Kollar.** Boynun tepesinde iki kol başlar. Her kolun başlangıç diski boynun içindedir ve kendi tarafında boynun kenarına teğettir. Kollar dışa dönüp iner. İki dirsek boynun hemen üstünde bir hacmi paylaşır.

2500 t/d kalsinatöründe (29 Eylül 2026) tavandan iki ayrı kol çıkıyordu, her biri Ø2.475 (yayınlanmış Ø3.50'nin alanının yarısı); o düzen tek hat içindi.

Boylar yayınlanmamıştır; yükseliş ve dirsek C1 makrosunun modelleme oranlarıdır, iniş kalsinatör gövdesinin yarı yüksekliğine kadardır (kullanıcı kararı, 29 Eylül 2026). Değerleri Geometrik Ölçüler'deki tabloda; konumları ve adım hacimleri [calciner.md](../calciner/calciner.md)'deki CFD tablosunda.

## Boundary Faces

`gas_outlet_1` (+x) ve `gas_outlet_2` (−x): inen boruların aşağı bakan diskleri, her biri bir kol kesiti.

## Derived Properties

CFD domeninin ve tesisin hacimleri Geometrik Ölçüler'deki tabloda; parça parça hacimler [calciner.md](../calciner/calciner.md)'deki CFD tablosunda.
