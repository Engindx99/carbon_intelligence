# Cyclone C3

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d. Tekli siklon.
Farin borusu: [meal_pipe_C3.md](meal_pipe_C3.md)
Tesiste iki özdeş 2500 t/d hattı var; her hatta bu siklondan bir tane, CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2, C3 ve C4 özdeş siklonlar; ölçüler C4'ünkiler. Bu kademenin katalog değerleri (D 6.30, gövde 3.22, koni 7.26, vorteks bulucu 4.62 / 3.15, toz çıkışı 0.84, giriş 1.26 × 9.46 m) [catalog.md](../catalog.md)'de duruyor; sapmanın gerekçesi orada.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Hat başına adet | 1 | yayınlanmış |
| Efektif iç çap D | 6.3 m | yayınlanmış; C4 ile özdeş |
| Silindirik gövde yüksekliği | 6.3 m | CFD kararı; C4 ile özdeş |
| Koni yüksekliği | 7.3 m | FLS oranıyla türetilmiş; C4 ile özdeş |
| Vorteks bulucu daldırması S | 3.9 m | CFD kararı; C4 ile özdeş |
| D_x / D (= riser çapı / D) | 0.5 | CFD kararı; C4 ile özdeş |
| Vorteks bulucu çapı D_x (= riser çapı) | 3.1500 m | 0.5 D |
| Toz çıkışı çapı | 0.81 m | FLS oranıyla türetilmiş; C4 ile özdeş |
| Giriş genişliği | 2.912 m | CFD kararı; C4 ile özdeş |
| Giriş yüksekliği | 3.4 m | CFD kararı; C4 ile özdeş |
| Giriş eğimi | 0 ° | CFD kararı; C4 ile özdeş |
| Volüt | var | CFD kararı; C4 ile özdeş |
| Çıkış dönüşü | 0 ° | CFD kararı; C4 ile özdeş |
| Çıkış borusu yükselişi (çatının üstünde) | 5.355 m | 1.7 D_x |
| Yatay giriş kanalı (teğet düzleminden) | 2.000 m | türetilmiş |
| Riserın dirsek altındaki eğik kesimi | 30 ° | şematik |
| Riser ekseni, gövde ekseninden (kolon aralığı) | 6.792 m | türetilmiş |
| Dirsek merkez yarıçapı (riser ekseninden kanal ağzına) | 2.944 m | türetilmiş |
| CFD domenindeki dik riser (dönüşün altında) | 3.150 m | türetilmiş |
| Toplam yükseklik (gövde + koni) | 13.600 m | türetilmiş |
| **Ekipman hacmi (gövde + koni)** | 283.25 m³ | türetilmiş |
| **Islak alan (gövde + çatı halkası + koni)** | 235.17 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Katı `geometry/output/2500/C3.step` (ayrıca `.stl`) export komutuyla üretilir; C2 ile aynı yolla kurulabilir. CFD domen hacmi, koordinatlar ve sınır parametre etkileri CFD_VIEW.pdf'te C3 için verilmemiş: TBD.

## Boundary Faces

TBD (CFD_VIEW.pdf'te C3 için verilmemiş).

## Derived Properties

Ekipman hacmi (gövde + koni) ve ıslak alan Geometrik Ölçüler'deki tabloda — C4 ile özdeş, CFD gövdesiyle (h = D; kullanıcı kararı, 13 Ekim 2026: twin C2–C4'te C5 gibi CFD gövdesini kullanır). Katalog gövdesiyle 194.5 m³, bu kademenin kendi katalog ölçüleriyle 187.0 m³ idi.
