# Kiln inlet chamber (fırın giriş odası)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§5). Referans hat: 2500 t/d.
Durum: 2500 hattı için kaynak yok. Bir kaynak ya da açık bir kullanıcı kararı gerekiyor; CFD ile türetilmeyecek.

## Geometrik Ölçüler

Geometri: TBD (yayınlanmış kaynak yok; model değeri aşağıda, "Hız kontrolü" bölümünde)

## CFD Geometry

Katı yok.

## Boundary Faces

TBD.

## Derived Properties

TBD.

## Hız kontrolü (16 Kasım 2026)

Ebat için yayınlanmış bir kural bulunamadı; kullanıcı kararı: hız ölçütüyle boyutla. Yerleşimdeki kare (fırının çevresinde `layout.chamber_margin` payıyla, kenar 2a; başlıkla aynı) ölçütü sağlar, bu yüzden ölçü kalır ve bir **model** değeridir (Estimated). Ölçüt: fırın girişindeki gaz hızı yaklaşık 10 m/s'nin altında olmalı, tercihen çok altında (cemnet forumu; yönetmelik değil). Kalsinatörün yükselen kolu en az ~6 m/s ister ([MDPI](https://www.mdpi.com/2571-8797/5/2/36)).

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Fırın girişi gaz hızı üst sınırı | 10 m/s | literatür |
| Fırın gazı hacimsel debisi (1323 K) | 223.2 m³/s | türetilmiş |
| Oda kesiti (kare, kenar 2a) | 6.80 m | türetilmiş |
| Hız, oda kesitinde | 4.83 m/s | türetilmiş |
| Hız, fırın tüpünün girişinde (CFD debisi) | 12.33 m/s | türetilmiş |
| Ölçütün izin verdiği en küçük kenar | 4.72 m | türetilmiş |
| Başvuru sınırı (Holcim StDC 2022; tek şirketin standardı) | 23 m/s | literatür |
| Fırın ağzı payı (ağzın dairesi rampa ayağına ve tavana değmesin) | 0.2 m | modelleme |
| Oda yüksekliği (düz tavan; boğaz tavanda) | 6.800 m | türetilmiş |
| Boğaz çapı (kalsinatörün) | 3.130 m | türetilmiş |
| Taban rampası: ayağı, +x duvarında (zeminden) | 0.800 m | türetilmiş |
| Taban rampası: yatay uzunluk (tüm plan, dudaktan karşı üst köşeye) | 6.800 m | türetilmiş |
| Taban rampası eğimi (yataya; geometriden) | 41.4 ° | türetilmiş |
<!-- END GENERATED -->

Dikkat: CFD'nin fırın gazı debisiyle (61.44 kg/s, 1323 K) fırın tüpünün kendi giriş hızı 10 m/s'yi aşıyor (tablo); twin'in debisinde (35.9 kg/s) 7.2 m/s olur. Bu, kalsinatörün CFD gaz debisi ile fırın tüpü arasındaki bilinen debi farkıdır (twin 80 kg/s, CFD 116.4 kg/s toplam giriş), yeni bir bulgu değildir.
