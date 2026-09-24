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

### Farin Girişi

Giriş tipi: Teğetsel

Giriş kesiti: Dikdörtgen, sabit kesit

Giriş genişliği: 0.86 m — FLS oranı (türetilmiş)

Giriş yüksekliği: 2.16 m — **kullanıcı kararı**, katalog değeri değil

FLS oranı 4.97 m veriyor (a/D = 1.15); giriş bilerek kısaltıldı. Gerekçe: yayınlanmış uzun giriş, gerçek makinede 270°'lik sarmal volütle beslendiği için anlamlıdır, bu model ise volütü bilerek kurmuyor. Volüt yerine düz teğetsel kanal konunca uzun giriş gerekçesini kaybediyor — 4.97 m'de açıklığın %61'i vorteks bulucu ağzının (z = 9.28) altında kalıyor ve oradan giren gaz halkayı atlayarak kısa devre yapabiliyor; giriş hızı da ~7 m/s'ye düşüyor, oysa preheater siklonları 15–20 m/s'de çalışır.

2.16 m ise a/D = 0.50 ve a/b = 2.51: Stairmand'in klasik oranı. Açıklığın yalnızca %10'u vorteks bulucu ağzının altında kalıyor ve giriş hızı ~16 m/s'ye dönüyor. Genişlik zaten klasikti (b/D = 0.86/4.32 = 0.199).

Ekipman hacmi değişmiyor, dolayısıyla kalma süresi ve holdup etkilenmiyor. Katalog tablosu ([catalog.md](../catalog.md)) yayınlanmış 4.97 değerini taşımaya devam eder; sapma bu dokümanda kayıtlıdır.

Giriş kesit alanı: 1.858 m²

Giriş kanalı: 0.86 × 2.16 m, 3.0 m uzunluğunda, teğetsel, sabit kesitli, 5° aşağı eğimli

Giriş yönü: Cyclone gövdesine teğetsel ve düşey düzlemde 5° aşağı eğimli

Kesit değişimi: Yok — kanal boyunca sabit

Volüt geometrisi: Modellenmeyecek; basitleştirilmiş düz, teğetsel ve eğimli giriş kullanılacak

C1 Y ayrımı: TBD — `LayoutParams` alanı tanımlı, değeri yok

## CFD Geometry

Katı `geometry/output/2500/C1.step` (ayrıca `.stl` ve `.SLDPRT`), `geometry/macros/cyclone.bas` SolidWorks makrosuyla üretilir. (Eski `python -m geometry --export` komutunun dayandığı paket kaldırıldı.)

CFD domeni, tek C1 cyclone + sabit kesitli teğetsel ve eğimli farin giriş kanalının akış hacmından oluşturulur.

Koordinatlar: siklon ekseni z, toz çıkışı z = 0. Gaz +x yönünde girer; giriş y ∈ [1.30, 2.16] aralığında olduğundan girdap **yukarıdan bakıldığında saat yönündedir**.

Koni: z = 0 → 4.650 m (Φ0.40 → Φ4.32)

Silindirik gövde: z = 4.650 → 11.440 m (çatı)

Vorteks bulucu duvarı: z = 9.280 → 11.440 m, 0.05 m kalınlığında (oyulmuş), r = 1.200 → 1.250

Çıkış borusu (vorteks bulucunun içi): z = 9.280 → 13.840 m, Φ2.40

Giriş kanalı: y = 1.300 → 2.160 (dış duvar gövdeye teğet); ekseni (cos5°, 0, −sin5°); gövdenin teğet düzleminde (x = 0) z = 9.071 → 11.239 m; gövdedeki açıklığın en yukarı ulaştığı nokta x = −1.725, z = 11.390 m

Giriş yüzü: merkezi (−2.989, 1.730, 10.416), x = −3.083 → −2.895, z = 9.341 → 11.492 m

Hacim ayrımı:

Ekipman hacmi (gövde + koni): 124.54 m³
+ Gövdenin dışında kalan serbest kanal: 3.33 m³
+ Çatının üstündeki çıkış borusu: 10.86 m³
− Vorteks bulucu duvarı: 0.83 m³
CFD domen hacmi (`C1.step`): 137.89 m³

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi):

`outlet_extension_over_vortex_D`: 1.0 — Çıkış yüzü çatıdan 1 vorteks bulucu çapı (2.40 m) yukarıda.

`vortex_finder_wall_m`: 0.05 m — Halkadaki girdabı borudan çıkan gazdan ayıran duvar; hacme etkisi %0.60.

Başlangıçta 0.012 m'ydi. Akış plaka kalınlığını umursamaz, mesh umursar: bu genişlik aynı zamanda vorteks bulucunun alt ağzındaki halka yüzünün genişliğidir ve o yüz 7.6 m çevre boyunca uzanır. 0.012 m'de en-boy oranı 631:1 çıkıyor, mesher tek sliver elemanla kapatıyor ve skewness orada 0.95'e tırmanıyor (mesh ortalaması 0.28). 0.05 m'de oran 154:1. Halka 0.948 → 0.910 m'ye daralıyor, %4. Üst sınır kanalın iç duvarı (y = 1.30): vorteks bulucunun dış yarıçapı onun altında kalmalı, 0.05 m'de pay 0.050 m, 0.10 m tam değerse dayanır ve ön kontrol reddeder.

`inlet_extension_over_D` C1 için **kullanılmaz**: kanal boyu 3.0 m yayınlanmış bir tesis ölçüsüdür, CFD uzatması değil. Gövdenin teğet düzleminden dışarı, kanal ekseni boyunca, kesit ağırlık merkezinden ölçülür — yüz 5° eğik olduğu için başka bir datumla boy ±0.22 m belirsiz kalırdı.

Modelleme sadeleştirmeleri:

- Yayınlanmış volüt modellenmiyor; giriş düz, teğet, 5° eğimli bir kanal.
- Kanalın en yüksek noktası çatının 0.05 m altında tutuluyor (`INLET_ROOF_CLEARANCE`). Kanal siklona doğru indiği için üst kenarını doğrudan çatıya dayamak, kanalı gövdenin izdüşümü üzerinde çatının üstüne çıkarır ve çatı plakasının üzerinde sivrilerek biten çıkmaz bir akışkan kaması bırakırdı. Bu boşluk çatıyı düz, açıklığı gövdede temiz bir delik olarak tutar. Tesis ölçüsü değil, modelleme seçimi.
- Kanalın dış duvarı gövdeye tam teğet (`INLET_TANGENT_RELIEF = 0`). Birleşim teğet çizgi boyunca sıfır açılı bir kenara kapanır; mesh orada zorlanırsa makronun parametresi 0.02 m'ye çekilir, iki duvar birden içeri kayacağı için 0.86 × 2.16 kesiti korunur. Henüz kullanılmadı. Ölçüm: 50 mm'lik vorteks bulucu cidarıyla üretilen mesh'te en kötü hücre artık vorteks bulucu ağzında değil, (−0.262, −2.155, 9.109)'da — r = 2.171 m, yani gövdenin dışında, kanalın tabanında, tam bu teğet kenarın üzerinde. Minimum orthogonal quality 0.135 (Fluent'in pratik alt sınırı 0.1), maksimum en-boy oranı 79. Kabul edilebilir; k-ε çözümü bu mesh'le kütle dengesi %0.10 ve ΔP 603 Pa verdi.
- Farin borusu yok; toz çıkışı bir sınır yüzü.
- C1 Y ayrımı modellenmiyor: tek C1 kuruluyor.

Kontrol: `C1.step` tek parça ve kapalı bir katı olmalı, hacmi 137.89 m³ olmalı. Makro bunu ve ara adımların her birini export etmeden önce kendisi doğrular.

Diskteki `C1.step` (24 Eylül 2026, 22:28) kanalı **−y tarafında** taşır: giriş yüzünün y ağırlık merkezi +1.73 değil −1.73 m, girdap da yukarıdan bakıldığında saat yönünün tersi. Yukarıdaki koordinat tablosunun y aynası. Sebep makronun kanal düzlemini yanlış tarafa koyması ve hiçbir doğrulamanın bunu görememesiydi — gövde y'de simetrik olduğu için sınırlayıcı kutu, ayna hacmi değiştirmediği için hacim, giriş yüzü aynı kaldığı için alan kontrolü hepsi geçiyordu. Makro düzeltildi (düzlemin yeri artık üzerine bırakılan bir test bloğuyla ölçülüyor, [macros/README.md](../macros/README.md)) ama **yeniden üretilmedi**; bir sonraki üretimde geometri bu tabloya dönecek. Mevcut STEP'ten kurulan Fluent mesh'i ve çözümü geçerlidir: tek başına duran bir siklonda ayna görüntüsü birebir aynı fiziktir, yerçekimi eksenel olduğu için el yönüyle kuplaj yoktur.

## Boundary Faces

Giriş kanalının uç yüzü: `meal_inlet` — merkezi (−2.989, 1.730, 10.416), normali kanal ekseni, 1.858 m² (yeşil)

Çıkış borusunun üst yüzü: `gas_outlet` — z = 13.840 m, 4.524 m² (mavi)

Toz çıkışı diski: `dust_outlet` — z = 0, 0.126 m² (turuncu)

Diğer bütün yüzler duvar (gri): `cyclone_wall`, `cone_wall`, `vortex_finder_wall`, `meal_inlet_wall`

Yüzler adla değil, geometrileriyle (düzlem mi, normali, üzerindeki nokta) bulunur; Boolean sonrası yüz adları yeniden üretildiği için ad araması kırılgandır. Etiketler yüz rengi olarak taşınır; AP214 renkleri koruduğundan Fluent Meshing bunlardan named selection üretir.

## Derived Properties

Ekipman hacmi (her biri): 124.54 m³ — kalma süresi, holdup ve benzeri fiziksel hesaplar bunu kullanır

Toplam yükseklik (gövde + koni): 11.44 m

Koni duvarının yatayla açısı: 67.1° — farinin 40°'lik yığılma açısının üstünde

Giriş kesit alanı: 1.858 m²

Giriş hidrolik çapı: 1.23 m

Vorteks bulucu kesiti: 4.524 m²

Toz çıkışı kesiti: 0.126 m²

Islak alan (gövde + çatı halkası + koni): 139.7 m²

Vorteks bulucunun dış yarıçapı ile kanalın iç duvarı arasındaki pay: 0.050 m — akışkan içinde bir darboğaz değil (aradaki bölge halkanın kendisi, serbest); kanalın vorteks bulucuyu kesmemesini garanti eden geometrik sınır

Not: Geometrik olarak eksik olan volüt ve C1 Y ayrımı, ilk tek-C1 CFD modeli için gerekli değildir. Bunlar daha sonraki çoklu C1/dağıtım geometrisi çalışmasında ele alınacaktır.
