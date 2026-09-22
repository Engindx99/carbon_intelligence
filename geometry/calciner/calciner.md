# Calciner (kalsinatör)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, §6, Ek). Referans hat: 2500 t/d.
Kaynak: önısıtıcı ve kalsinatör HFC2500 tasarımı (2005); efektif çaplar yayınlanmış.

## Geometrik Ölçüler

Efektif iç çap: 5.50 m — HFC2500 (yayınlanmış)
Boy: 29.46 m — CFD_VIEW.pdf'te belirtilmemiş
Giriş boğazı: TBD — 2500 hattı için kaynak yok
Tersiyer hava kanalı: kapsam dışı — Karar gereği; kalsinatör tabanı tek giriş

## CFD Geometry

Şu an Φ5.50 × 29.46 m'lik düz bir silindir.
Katı `geometry/output/2500/calciner.step` (ayrıca `.stl`) export komutuyla üretilir. CFD domen hacmi CFD_VIEW.pdf'te verilmemiş: TBD.

## Boundary Faces

Taban: giriş (tek giriş)
Tepe: çıkış

## Derived Properties

Ekipman hacmi: 700.0 m³
