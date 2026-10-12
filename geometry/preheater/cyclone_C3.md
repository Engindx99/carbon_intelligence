# Cyclone C3

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d. Tekli siklon.
Farin borusu: [meal_pipe_C3.md](meal_pipe_C3.md)
Tesiste iki özdeş 2500 t/d hattı var; her hatta bu siklondan bir tane, CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2, C3 ve C4 özdeş siklonlar; ölçüler C4'ünkiler. Bu kademenin katalog değerleri (D 6.30, gövde 3.22, koni 7.26, vorteks bulucu 4.62 / 3.15, toz çıkışı 0.84, giriş 1.26 × 9.46 m) [catalog.md](../catalog.md)'de duruyor; sapmanın gerekçesi orada.

Efektif iç çap, D: 6.30 m — C4 ile özdeş (ara kademe standardı; C4'ün yayınlanmış HFC2500 değeri)
Silindirik gövde yüksekliği: 3.46 m — C4 ile özdeş (FLS oranı, türetilmiş); CFD'de C4 gibi 6.30 m ve volütlü giriş ([cyclone_C4.md](cyclone_C4.md))
Koni yüksekliği: 7.30 m — C4 ile özdeş (FLS oranı, türetilmiş)
Vorteks bulucu çapı: 4.63 m — C4 ile özdeş (FLS oranı, türetilmiş)
Vorteks bulucu boyu (daldırma): 3.17 m — C4 ile özdeş (FLS oranı, türetilmiş); CFD'de C4 gibi 3.90 m ([cyclone_C4.md](cyclone_C4.md))
Toz çıkışı çapı: 0.81 m — C4 ile özdeş (FLS oranı, türetilmiş)
Giriş genişliği: 1.27 m — C4 ile özdeş (FLS oranı, türetilmiş)
Giriş yüksekliği: 9.44 m — C4 ile özdeş (FLS oranı, türetilmiş)
Volüt geometrisi: TBD — 2500 hattı için kaynak yok

## CFD Geometry

Katı `geometry/output/2500/C3.step` (ayrıca `.stl`) export komutuyla üretilir; C2 ile aynı yolla kurulabilir. CFD domen hacmi, koordinatlar ve sınır parametre etkileri CFD_VIEW.pdf'te C3 için verilmemiş: TBD.

## Boundary Faces

TBD (CFD_VIEW.pdf'te C3 için verilmemiş).

## Derived Properties

Ekipman hacmi: 194.5 m³ (C4 ile özdeş; katalog ölçüleriyle 187.0 m³ idi)
