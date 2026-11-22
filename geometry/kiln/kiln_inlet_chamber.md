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
| Oda planı (boğazın sol duvarından ağza × 2a) | 33.76 m² | türetilmiş |
| Hız, oda planında | 6.61 m/s | türetilmiş |
| Hız, fırın tüpünün girişinde (CFD debisi) | 12.33 m/s | türetilmiş |
| Ölçütün izin verdiği en küçük kenar | 4.72 m | türetilmiş |
| Başvuru sınırı (Holcim StDC 2022; tek şirketin standardı) | 23 m/s | literatür |
| Oda yüksekliği (boğazın üstü, zeminden) | 5.950 m | türetilmiş |
| Boğaz çapı (kalsinatörün; duvarları x = ±r aşağı iner) | 3.130 m | türetilmiş |
| Rampa eğimi (yataya) | 50 ° | modelleme |
| Rampa ayağı (yatay; fırının alt çizgisi, kiln.slope ile düşer) | 1.5 m | modelleme |
| Rampanın üstü, sol boğaz duvarında (zeminden) | 5.173 m | türetilmiş |
| Tavan, sağ boğaz duvarında (fırının üst çizgisi; zeminden) | 5.856 m | türetilmiş |
| Fırın borusu ucu (CFD katısı; D'ye oran) | 0.5 | modelleme |
| CFD hacmi (kesit prizması + boğaz + fırın ucu) | 158.50 m³ | türetilmiş |
<!-- END GENERATED -->

Dikkat: CFD'nin fırın gazı debisiyle (61.44 kg/s, 1323 K) fırın tüpünün kendi giriş hızı 10 m/s'yi aşıyor (tablo); twin'in debisinde (35.9 kg/s) 7.2 m/s olur. Bu, kalsinatörün CFD gaz debisi ile fırın tüpü arasındaki bilinen debi farkıdır (twin 80 kg/s, CFD 116.4 kg/s toplam giriş), yeni bir bulgu değildir.
