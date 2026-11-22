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

Katı `geometry/macros/cyclone.bas` ile `CYCLONE_NAME = "C4"` seçilerek kurulur: C2, C4'ün CFD domeniyle özdeştir ([cyclone_C4.md](cyclone_C4.md)) — R3'ün dik riser'ı ve 45°'lik geçişi, 1.0 m yatay kanal, volütlü giriş, h = D gövde, daldırma 3.90 m, 1.70·D_x düz çıkış borusu. Tesiste çıkış borusu R1'in başıdır ([riser_R1.md](riser_R1.md)).

**Tesiste C2'nin çıkışı dönmez (kullanıcı kararı, 17 Kasım 2026).** R1, C2'nin ekseninde dik yükselir:
CFD'nin 7.871 m'lik çıkış borusu, ucunda 45°'lik bir daraltıcı (Ø4.63 → Ø3.07, 0.78 m) ve R1. İkiz
C1'ler bu yüzden C2'nin üstündedir.

Aynı gün C4'ün CFD domeninin de 90° dirseği kalktı (R2–R4 dik riser'lar; [cyclone_C4.md](cyclone_C4.md)).
C2 böylece hem girişinde (R3, kolon aralığı 5.838 m) hem çıkışında domenle birebirdir; önceki
sapma (C2'nin ΔP'si dirsekli domenin Eu'suyla taşınıyordu) kapandı. Domen henüz çözülmedi: Eu
11.54 eski domenin sonucudur. Yeni çözüm C2'nin Eu'sunu ve R1'e giren dönen akımın profilini
birlikte verecek; ikiz C1'in Y'li giriş domeninin giriş koşulu odur.
Önce (13 Ekim – 17 Kasım 2026) C2'nin CFD dirseği ve bacağı gazı kalsinatöre doğru 11.3 m taşıyor,
R1 orada bir dirsekle yükseliyordu.

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

