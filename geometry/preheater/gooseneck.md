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
| Tesis: kol boyu (iniş + 45° + C5 girişine yatay) | 17.570 m | türetilmiş |
| **Tesis: hacim (iki kol)** | 764.16 m³ | türetilmiş |
| **Tesis: duvar alanı (iki kol)** | 845.30 m² | türetilmiş |
<!-- END GENERATED -->

**Tesis ve CFD** (kullanıcı kararı, 14 Ekim 2026). Tesiste kollar C5 girişlerine kadar iner: iniş, 45°'lik bir parça ve C5 gövdesine yatay bir bacak (çizim, [plant_topology.md](../plant_topology.md)). Twin bu hacmi kullanır. Kalsinatör CFD'si kolları gövdenin yarı yüksekliğinde keser (`end_at_vessel_H`, bir CFD sınır seçimi); "CFD" satırları o domenindir.

## CFD Geometry

Kaz boynu, kalsinatör katısının bir parçası olarak kurulur ([calciner.md](../calciner/calciner.md), [`calciner.bas`](../macros/calciner.bas)).

CFD'de kaz boynu bir **Y**'dir (kullanıcı kararı, 12 Ekim 2026):
- **Boyun.** Tavanın ortasından **Ø4.950** tek bir boyun çıkar. Kesiti iki kolun toplamıdır (3.50 × √2), hız korunur. Gerekçe: iki Ø3.50 kol Ø6.74'lük tavana yan yana sığmaz.
- **Kollar.** Boynun tepesinde iki **Ø3.50** kol başlar. Her kolun başlangıç diski boynun içindedir ve kendi tarafında boynun kenarına teğettir (x = ±0.725). Kollar dışa dönüp iner. İki dirsek boynun hemen üstünde 10.346 m³ paylaşır.

2500 t/d kalsinatöründe (29 Eylül 2026) tavandan iki ayrı kol çıkıyordu, her biri Ø2.475 (yayınlanmış Ø3.50'nin alanının yarısı); o düzen tek hat içindi.

Boylar yayınlanmamıştır; yükseliş ve dirsek C1 makrosunun modelleme oranlarıdır:
- boyun yükselişi 1.25 × boyun çapı = 6.187 m
- 180° dirsek, R = 1.5 × kol çapı = 5.25 m
- iniş kalsinatör gövdesinin yarı yüksekliğine kadar: 21.187 m, çıkış yüzleri z = 18.130 (kullanıcı kararı, 29 Eylül 2026)

## Boundary Faces

`gas_outlet_1` (+x) ve `gas_outlet_2` (−x): inen boruların aşağı bakan diskleri, her biri 9.621 m².

## Derived Properties

CFD domeninde: boyun 119.055 m³; iki dirsek 2 × 158.685 − 10.346 = 307.024 m³; iki iniş 407.689 m³. Toplam **833.768 m³**.
