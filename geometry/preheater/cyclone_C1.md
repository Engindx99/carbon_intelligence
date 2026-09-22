# Cyclone C1

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, §6, Ek). Referans hat: 2500 t/d.
Farin borusu: [meal_pipe_C1.md](meal_pipe_C1.md)
C1 iki siklondan oluşur (×2); aşağıdaki değerler her biri içindir.
C1, FLS'nin tek üst siklonundan çoklu C1'e aktarım varsayımını taşır; bu varsayım not edilerek kurulmalı.

## Geometrik Ölçüler

Adet: 2
Efektif iç çap, D: 4.32 m — HFC2500 (yayınlanmış)
Silindirik gövde yüksekliği: 6.79 m — FLS oranı (türetilmiş)
Koni yüksekliği: 4.65 m — FLS oranı (türetilmiş)
Vorteks bulucu çapı: 2.40 m — FLS oranı (türetilmiş)
Vorteks bulucu boyu (daldırma): 2.16 m — FLS oranı (türetilmiş)
Toz çıkışı çapı: 0.40 m — FLS oranı (türetilmiş)
Giriş genişliği: 0.86 m — FLS oranı (türetilmiş)
Giriş yüksekliği: 4.97 m — FLS oranı (türetilmiş)
Volüt geometrisi: TBD — 2500 hattı için kaynak yok
C1 Y ayrımı: TBD — `LayoutParams` alanı tanımlı, değeri yok

## CFD Geometry

Katı `geometry/output/2500/C1.step` (ayrıca `.stl`) export komutuyla üretilir. CFD domen hacmi, koordinatlar ve sınır parametre etkileri CFD_VIEW.pdf'te C1 için verilmemiş: TBD.

## Boundary Faces

TBD (CFD_VIEW.pdf'te C1 için verilmemiş).

## Derived Properties

Ekipman hacmi (her biri): 124.6 m³
