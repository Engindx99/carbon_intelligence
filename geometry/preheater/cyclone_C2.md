# Cyclone C2

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§2, §3, §4, §6). Referans hat: 2500 t/d.
Farin borusu: [meal_pipe_C2.md](meal_pipe_C2.md)
Tesiste iki özdeş 2500 t/d hattı var; her hatta bu siklondan bir tane, CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).
İlk CFD prototipi. Seçilme nedeni: C1'e özgü aktarım varsayımını (FLS'nin tek üst siklonundan çoklu C1'e) taşımaması.

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2, C3 ve C4 özdeş siklonlar; ölçüler C4'ünkiler. Bu kademenin katalog değerleri (D 6.10, gövde 3.67, koni 6.51, vorteks bulucu 4.35 / 3.05, toz çıkışı 0.80, giriş 1.23 × 8.71 m) [catalog.md](../catalog.md)'de duruyor; sapmanın gerekçesi orada.

Efektif iç çap, D: 6.30 m — C4 ile özdeş (ara kademe standardı; C4'ün yayınlanmış HFC2500 değeri; C2'nin kendi yayınlanmış çapı 6.10 m)
Silindirik gövde yüksekliği: 3.46 m — C4 ile özdeş (FLS oranı, türetilmiş); CFD'de C4 gibi 6.30 m ve volütlü giriş ([cyclone_C4.md](cyclone_C4.md))
Koni yüksekliği: 7.30 m — C4 ile özdeş (FLS oranı, türetilmiş)
Vorteks bulucu çapı: 4.63 m — C4 ile özdeş (FLS oranı, türetilmiş)
Vorteks bulucu boyu (daldırma): 3.17 m — C4 ile özdeş (FLS oranı, türetilmiş); CFD'de C4 gibi 3.90 m ([cyclone_C4.md](cyclone_C4.md))
Toz çıkışı çapı: 0.81 m — C4 ile özdeş (FLS oranı, türetilmiş)
Giriş genişliği: 1.27 m — C4 ile özdeş (FLS oranı, türetilmiş)
Giriş yüksekliği: 9.44 m — C4 ile özdeş (FLS oranı, türetilmiş)
Volüt geometrisi: TBD — 2500 hattı için kaynak yok

## CFD Geometry

Aşağıdaki koordinatlar ve hacim ayrımı (domen 273.1 m³) C2'nin **eski** katalog ölçülerine (D 6.10) aitti ve ara kademe standardıyla geçersiz oldu; kaldırıldı. Siklon makroyla C4 ölçüleriyle kurulunca doldurulacak: TBD.

Ekipman hacmi (gövde + koni): 194.5 m³ (C4 ile özdeş)

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi, kodda varsayılan değerleri yok):

`inlet_extension_over_D`: 0.6 — Giriş yüzü eksenden 0.6 D uzakta. Eski ölçülerle en az 0.401 olmalıydı (yeni ölçülerle TBD), yoksa yüz gövdenin içinde kalır; kod bunu kontrol eder. Her +1 D için hacim artışı eski ölçülerle ≈ +65 m³ idi; yeni ölçülerle TBD.
`outlet_extension_over_vortex_D`: 1.0 — Çıkış yüzü çatıdan 1 vorteks bulucu çapı yukarıda. Hacme en çok etki eden parametre: her +1 çap için ≈ +64.5 m³ eski ölçülerle; yeni vorteks bulucu çapıyla (4.63 m) ≈ +78 m³.
`vortex_finder_wall_m`: C2 için **henüz seçilmedi**. Burada uzun süre 0.012 m yazılıydı ve config bugün 0.08 tutuyor; tek skaler iki dokümanda farklı değer iddia ediyordu. C1'de ölçülen kural şu: ağzın genişliği, mesh'in oraya koyacağı yerel yüzey boyutunun 3–4 katı olmalı ([cyclone_C1.md](cyclone_C1.md)). C2 makroyla kurulduğunda değer o ölçüte göre belirlenecek. 0.012 m'de hacme etki ~%0.2 idi.

Modelleme sadeleştirmeleri:

- Yayınlanmış 270°'lik volüt modellenmiyor; giriş düz, teğet bir kanal.
- Giriş yüksekliği (9.44 m) gövdeden (3.46 m) uzun. Bu yüzden giriş kanalı koni bölgesine iniyor ve katalog ölçüleri düzeltilmeden olduğu gibi kuruluyor.
- Farin borusu yok; toz çıkışı bir sınır yüzü.

Hazır dosya: TBD. Eski `geometry/output/2500/C2.step` (273.1 m³) eski ölçülere aittir, kullanılmamalı. Katıyı kuran makro export öncesi hacmi kendisi kontrol eder ([macros/README.md](../macros/README.md)).

## Boundary Faces

Giriş kanalının uç yüzü: giriş — konum TBD (C4 ölçüleriyle yeniden kurulacak)
Çıkış borusunun üst yüzü: çıkış — konum TBD
Toz çıkışı diski: toz çıkışı — z = 0
Diğer bütün yüzler: duvar

## Derived Properties

C4 ölçüleriyle (ara kademe standardı):

Toplam yükseklik (gövde + koni): 10.76 m
Koni duvarının yatayla açısı: 69.4° — farinin 40°'lik yığılma açısının üstünde
Giriş kesiti: 11.99 m²
Giriş hidrolik çapı: 2.24 m
Vorteks bulucu kesiti: 16.84 m²
Toz çıkışı kesiti: 0.515 m²
Islak alan (gövde + çatı halkası + koni): 169.9 m²
Ekipman hacmi (gövde + koni): 194.5 m³ — kalma süresi, holdup ve benzeri fiziksel hesaplar bunu kullanır
