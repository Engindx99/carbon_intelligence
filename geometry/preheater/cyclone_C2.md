# Cyclone C2

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§2, §3, §4, §6). Referans hat: 2500 t/d.
Farin borusu: [meal_pipe_C2.md](meal_pipe_C2.md)
Tesiste iki özdeş 2500 t/d hattı var; her hatta bu siklondan bir tane, CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).
İlk CFD prototipi. Seçilme nedeni: C1'e özgü aktarım varsayımını (FLS'nin tek üst siklonundan çoklu C1'e) taşımaması.

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2, C3 ve C4 özdeş siklonlar; ölçüler C4'ünkiler. Bu kademenin katalog değerleri (D 6.10, gövde 3.67, koni 6.51, vorteks bulucu 4.35 / 3.05, toz çıkışı 0.80, giriş 1.23 × 8.71 m) [catalog.md](../catalog.md)'de duruyor; sapmanın gerekçesi orada.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Hat başına adet | 1 | yayınlanmış |
| Efektif iç çap D | 6.3 m | yayınlanmış; C4 ile özdeş |
| Silindirik gövde yüksekliği | 6.3 m | CFD kararı; C4 ile özdeş |
| Koni yüksekliği | 7.3 m | FLS oranıyla türetilmiş; C4 ile özdeş |
| Vorteks bulucu daldırması S | 3.9 m | CFD kararı; C4 ile özdeş |
| Vorteks bulucu çapı D_x | 4.63 m | FLS oranıyla türetilmiş; C4 ile özdeş |
| Toz çıkışı çapı | 0.81 m | FLS oranıyla türetilmiş; C4 ile özdeş |
| Giriş genişliği | 2.912 m | CFD kararı; C4 ile özdeş |
| Giriş yüksekliği | 3.4 m | CFD kararı; C4 ile özdeş |
| Giriş eğimi | 0 ° | CFD kararı; C4 ile özdeş |
| Volüt | var | CFD kararı; C4 ile özdeş |
| Çıkış dönüşü | 90 ° | CFD kararı; C4 ile özdeş |
| Çıkış borusu yükselişi (çatının üstünde) | 7.871 m | 1.7 D_x |
| Çıkış dirseği merkez yarıçapı | 4.630 m | 1 D_x |
| Çıkış bacağı / inişi | 4.630 m | 1 D_x |
| Toplam yükseklik (gövde + koni) | 13.600 m | türetilmiş |
| **Ekipman hacmi (gövde + koni)** | 283.25 m³ | türetilmiş |
| **Islak alan (gövde + çatı halkası + koni)** | 226.13 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Katı `geometry/macros/cyclone.bas` ile `CYCLONE_NAME = "C4"` seçilerek kurulur: C2, C4'ün CFD domeniyle özdeştir ([cyclone_C4.md](cyclone_C4.md)) — volütlü giriş, h = D gövde, daldırma 3.90 m, 90° çıkış dirseği. Tesiste çıkış borusu R1'in başıdır ([riser_R1.md](riser_R1.md)).

Eski `geometry/output/2500/C2.step` (273.1 m³) eski katalog ölçülerine (D 6.10) aittir, kullanılmamalı. Eski `geometry.cfd_boundary` config bloğu 14 Ekim 2026'da silindi; sınır seçimleri `cyclone.bas`'tadır.

## Boundary Faces

Giriş ve çıkış yüzleri: C4'teki gibi ([cyclone_C4.md](cyclone_C4.md))
Toz çıkışı diski: toz çıkışı — z = 0
Diğer bütün yüzler: duvar

## Derived Properties

C4 ile özdeş (ara kademe standardı). Ekipman hacmi, ıslak alan ve toplam yükseklik Geometrik Ölçüler'deki tabloda; CFD gövdesiyle (h = D; kullanıcı kararı, 13 Ekim 2026: twin C2–C4'te C5 gibi CFD gövdesini kullanır). Katalog gövdesiyle 194.5 m³ ve 169.9 m²'ydi.

Koni duvarının yatayla açısı: 69.4° — farinin 40°'lik yığılma açısının üstünde
Volüt giriş kesiti: 9.90 m² (3.40 × 2.912)
Vorteks bulucu kesiti: 16.84 m²
Toz çıkışı kesiti: 0.515 m²

