# Cyclone C2

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§2, §3, §4, §6). Referans hat: 2500 t/d.
Farin borusu: [meal_pipe_C2.md](meal_pipe_C2.md)
İlk CFD prototipi. Seçilme nedeni: C1'e özgü aktarım varsayımını (FLS'nin tek üst siklonundan çoklu C1'e) taşımaması.

## Geometrik Ölçüler

Efektif iç çap, D: 6.10 m — HFC2500 (yayınlanmış)
Silindirik gövde yüksekliği: 3.67 m — FLS oranı (türetilmiş)
Koni yüksekliği: 6.51 m — FLS oranı (türetilmiş)
Vorteks bulucu çapı: 4.35 m — FLS oranı (türetilmiş)
Vorteks bulucu boyu (daldırma): 3.05 m — FLS oranı (türetilmiş)
Toz çıkışı çapı: 0.80 m — FLS oranı (türetilmiş)
Giriş genişliği: 1.23 m — FLS oranı (türetilmiş)
Giriş yüksekliği: 8.71 m — FLS oranı (türetilmiş)
Volüt geometrisi: TBD — 2500 hattı için kaynak yok

## CFD Geometry

Koordinatlar: siklon ekseni z, toz çıkışı z = 0. Değerler `components.cyclone_layout` çıktısıdır.

Koni: z = 0 → 6.511 m (Φ0.80 → Φ6.10)
Silindirik gövde: z = 6.511 → 10.179 m (çatı)
Giriş kanalı: x = −3.660 → 0, y = 1.825 → 3.050, z = 1.469 → 10.179 m. Gövdeye teğet; gaz +x yönünde girer.
Vorteks bulucu duvarı: z = 7.129 → 10.179 m, 0.012 m kalınlığında (oyulmuş)
Çıkış borusu (vorteks bulucunun içi): z = 7.129 → 14.526 m, Φ4.35

Hacim ayrımı:

Ekipman hacmi (gövde + koni; `properties.cyclone_properties().body_volume`): 180.1 m³
+ Giriş kanalının gövde ve koninin dışında kalan kısmı: 29.0 m³
+ Çatının üstündeki çıkış borusu: 64.5 m³
− Vorteks bulucu duvarı: 0.5 m³
CFD domen hacmi (`C2.step`): 273.1 m³

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi, kodda varsayılan değerleri yok):

`inlet_extension_over_D`: 0.6 — Giriş yüzü eksenden 0.6 D uzakta. En az 0.401 olmalı, yoksa yüz gövdenin içinde kalır; kod bunu kontrol eder. Her +1 D için hacim ≈ +65 m³.
`outlet_extension_over_vortex_D`: 1.0 — Çıkış yüzü çatıdan 1 vorteks bulucu çapı yukarıda. Hacme en çok etki eden parametre: her +1 çap için ≈ +64.5 m³.
`vortex_finder_wall_m`: 0.012 m — İnce bir ayırıcı duvar; hacme etkisi yaklaşık %0.2.

Modelleme sadeleştirmeleri:

- Yayınlanmış 270°'lik volüt modellenmiyor; giriş düz, teğet bir kanal.
- Yayınlanmış giriş yüksekliği (8.71 m) gövdeden (3.67 m) uzun. Bu yüzden giriş kanalı koni bölgesine iniyor ve katalog ölçüleri düzeltilmeden olduğu gibi kuruluyor.
- Farin borusu yok; toz çıkışı bir sınır yüzü.

Hazır dosya: tek parça, kapalı katı `geometry/output/2500/C2.step` (ayrıca `.stl`).
Kontrol: `C2.step` tek parça ve kapalı bir katı olmalı, hacmi 273.1 m³ olmalı. Bunu sabitleyen test, dayandığı `geometry/` paketiyle birlikte kaldırıldı; kontrolü artık katıyı kuran makro export öncesi kendisi yapar ([macros/README.md](../macros/README.md)).

## Boundary Faces

Giriş kanalının uç yüzü: giriş — x = −3.660 m
Çıkış borusunun üst yüzü: çıkış — z = 14.526 m
Toz çıkışı diski: toz çıkışı — z = 0
Diğer bütün yüzler: duvar

## Derived Properties

Toplam yükseklik (gövde + koni): 10.18 m
Koni duvarının yatayla açısı: 67.9° — farinin 40°'lik yığılma açısının üstünde
Giriş kesiti: 10.67 m²
Giriş hidrolik çapı: 2.15 m
Vorteks bulucu kesiti: 14.84 m²
Toz çıkışı kesiti: 0.509 m²
Islak alan (gövde + çatı halkası + koni): 160.9 m²
Ekipman hacmi (gövde + koni): 180.1 m³ — kalma süresi, holdup ve benzeri fiziksel hesaplar bunu kullanır
