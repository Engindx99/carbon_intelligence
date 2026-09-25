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

Vorteks bulucu duvarı: z = 9.280 → 11.440 m, 0.08 m kalınlığında (oyulmuş), r = 1.200 → 1.280

Çıkış borusu (vorteks bulucunun içi): z = 9.280 → 17.440 m, Φ2.40

Giriş kanalı: y = 1.300 → 2.160 (dış duvar gövdeye teğet); ekseni (cos5°, 0, −sin5°); gövdenin teğet düzleminde (x = 0) z = 9.071 → 11.239 m; gövdedeki açıklığın en yukarı ulaştığı nokta x = −1.725, z = 11.390 m

Giriş yüzü: merkezi (−2.989, 1.730, 10.416), x = −3.083 → −2.895, z = 9.341 → 11.492 m

Hacim ayrımı:

Ekipman hacmi (gövde + koni): 124.54 m³
+ Gövdenin dışında kalan serbest kanal: 3.33 m³
+ Çatının üstündeki çıkış borusu: 27.14 m³
− Vorteks bulucu duvarı: 1.35 m³
CFD domen hacmi (`C1.step`): 153.66 m³

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi):

`outlet_extension_over_vortex_D`: 2.5 — Çıkış yüzü çatıdan 2.5 vorteks bulucu çapı (6.00 m) yukarıda, z = 17.44.

Bu, çatının üstündeki **çıkış kanalıdır**, vorteks bulucu değil — vorteks bulucu çatıdan aşağı inen 2.16 m'lik daldırma borusudur ve bu parametre ona dokunmaz. Gerçek tesiste çatının üstünde bir kanal vardır (gaz ID fana gider) ama boyu tesis yerleşimine göre belirlenir; buradaki uzunluk bir CFD seçimidir. Siklon CFD literatüründe tipik uzatma 1–5 vorteks bulucu çapıdır.

Başlangıçta 1.0'dı. İlk Fluent koşusu bunun yetmediğini gösterdi: çıkış borusundan yukarı çıkan girdabın merkezinde aşağı yönlü bir ters akım çekirdeği var ve 2.40 m'lik uzatma o çekirdek hâlâ açıkken sınırı kesiyordu — çıkış yüzünün **%40–44'ünde gaz içeri giriyordu**. Fluent orada kullanıcının verdiği backflow değerlerini dayatmak zorunda kalıyor, dayatılan durum domenin istediği durumla çatışıyor ve çözüm yakınsamak yerine kütle dengesinde ±%0.3'lük bir limit çevrimine oturuyordu. 6.00 m, çekirdeğin kapanması için belirgin biçimde daha fazla yer bırakır. Garanti değil: girdap eksenel mesafeyle yavaş söner, dolayısıyla 2.5 D'nin sonunda teğetsel hız hâlâ belirgin olabilir ve bir miktar geri akış kalabilir. Kalırsa seçenekler uzatmayı 4 D'ye çıkarmak ya da geri akışı kabul edip backflow değerlerinin (603 K) doğruluğuna güvenmek — tek girişli ve izotermal bu koşuda o değer zaten doğru.

`vortex_finder_wall_m`: 0.08 m — Halkadaki girdabı borudan çıkan gazdan ayıran duvar; hacme etkisi %1.08.

Başlangıçta 0.012 m'ydi, sonra 0.05, şimdi 0.08. Akış plaka kalınlığını umursamaz, mesh umursar: bu genişlik aynı zamanda vorteks bulucunun alt ağzındaki halka yüzünün genişliğidir ve o yüz 7.6 m çevre boyunca uzanır. 0.012 m'de en-boy oranı 631:1, 0.05 m'de 154:1, 0.08 m'de 96:1.

0.05 m yetmedi. 0.15 m'lik hücrelerle kurulan ilk mesh'te sorun çıkarmadı, ama siklonun girdap çekirdeğini çözebilmesi için çekirdekte ~0.05 m hücre gerekiyor ve o boyda 50 mm'lik bir ağız **tek hücre genişliğinde** kalıyor. Fluent'te çekirdek iyileştirildiğinde minimum orthogonal quality 0.015'e düştü (Fluent'in mutlak tabanı 0.01) ve en kötü iki hücrenin ikisi de bu ağzın altındaydı: r = 1.23–1.25, z = 9.22, yani halka yüzünün 60 mm altı. Hücre boyundan ince bir geometrik özellik mesh'lenemez, ancak etrafından dolaşılır.

80 mm fiziksel olarak da daha savunulabilir: preheater daldırma borusu ısıya dayanıklı çelik ya da SiC'dir, çoğu zaman refrakter kaplıdır; 80 mm olağandır. Üçü içinde en az fiziksel olan başlangıçtaki 12 mm'ydi.

Halka 0.948 → 0.910 → 0.880 m'ye daralıyor. Üst sınır kanalın iç duvarı (y = R − `INLET_TANGENT_RELIEF` − 0.86): vorteks bulucunun dış yarıçapı onun altında kalmalı. İki parametre **tek bir bütçeyi** paylaşıyor: `vortex_finder_wall_m` + `INLET_TANGENT_RELIEF` < 0.10 m. Bütçe ağza harcandı (aşağıdaki teğet kenar maddesine bakın); 0.08 m'de kanal duvarına pay 0.020 m, 0.10 m tam değerse dayanır ve ön kontrol reddeder.

`inlet_extension_over_D` C1 için **kullanılmaz**: kanal boyu 3.0 m yayınlanmış bir tesis ölçüsüdür, CFD uzatması değil. Gövdenin teğet düzleminden dışarı, kanal ekseni boyunca, kesit ağırlık merkezinden ölçülür — yüz 5° eğik olduğu için başka bir datumla boy ±0.22 m belirsiz kalırdı.

Modelleme sadeleştirmeleri:

- Yayınlanmış volüt modellenmiyor; giriş düz, teğet, 5° eğimli bir kanal.
- Kanalın en yüksek noktası çatının 0.05 m altında tutuluyor (`INLET_ROOF_CLEARANCE`). Kanal siklona doğru indiği için üst kenarını doğrudan çatıya dayamak, kanalı gövdenin izdüşümü üzerinde çatının üstüne çıkarır ve çatı plakasının üzerinde sivrilerek biten çıkmaz bir akışkan kaması bırakırdı. Bu boşluk çatıyı düz, açıklığı gövdede temiz bir delik olarak tutar. Tesis ölçüsü değil, modelleme seçimi.
- Kanalın dış duvarı gövdeye tam teğet (`INLET_TANGENT_RELIEF = 0`). Birleşim teğet çizgi boyunca sıfır açılı bir kenara kapanır. **Bilerek 0'da bırakıldı**, çünkü `vortex_finder_wall_m` ile aynı 0.10 m'lik bütçeyi paylaşıyor ve ölçüm ağzı bir mertebe önde gösterdi: vorteks bulucu ağzının altında minimum orthogonal quality **0.015**, bu teğet kenarda **0.135**. 0.135'lik bir hücre kullanılabilir, 0.015'lik değil. Bu yüzden bütçe ağza gitti ve kenar gerçek teğet geometrisi olarak bırakıldı; mesh tarafında yerel bir yüzey boyutlandırmasıyla (face sizing ≈ 0.03 m) ele alınacak — geometriden bir şey götürmez. İleride bir mesh bunun yetmediğini gösterirse buradaki 0.02, `vortex_finder_wall_m`'i 0.06'ya indirir; iki duvar birden içeri kayacağı için 0.86 × 2.16 kesiti ve giriş hızı her iki durumda da korunur.

  Ölçüm (50 mm cidarlı geometri, 0.15 m global hücre, 45 bin poly): en kötü hücre (−0.262, −2.155, 9.109), r = 2.171 m — gövdenin dışında, kanalın tabanında, tam bu kenarın üzerinde. Orthogonal quality 0.135, en-boy oranı 79.

- Farin borusu yok; toz çıkışı bir sınır yüzü.
- C1 Y ayrımı modellenmiyor: tek C1 kuruluyor.

Kontrol: `C1.step` tek parça ve kapalı bir katı olmalı, hacmi 153.66 m³ olmalı. Makro bunu ve ara adımların her birini export etmeden önce kendisi doğrular.

Diskteki `C1.step` (24 Eylül 2026, 22:28) kanalı **−y tarafında** taşır: giriş yüzünün y ağırlık merkezi +1.73 değil −1.73 m, girdap da yukarıdan bakıldığında saat yönünün tersi. Yukarıdaki koordinat tablosunun y aynası. Sebep makronun kanal düzlemini yanlış tarafa koyması ve hiçbir doğrulamanın bunu görememesiydi — gövde y'de simetrik olduğu için sınırlayıcı kutu, ayna hacmi değiştirmediği için hacim, giriş yüzü aynı kaldığı için alan kontrolü hepsi geçiyordu. Makro düzeltildi (düzlemin yeri artık üzerine bırakılan bir test bloğuyla ölçülüyor, [macros/README.md](../macros/README.md)) ama **yeniden üretilmedi**; bir sonraki üretimde geometri bu tabloya dönecek. Mevcut STEP'ten kurulan Fluent mesh'i ve çözümü geçerlidir: tek başına duran bir siklonda ayna görüntüsü birebir aynı fiziktir, yerçekimi eksenel olduğu için el yönüyle kuplaj yoktur.

## Boundary Faces

Giriş kanalının uç yüzü: `meal_inlet` — merkezi (−2.989, 1.730, 10.416), normali kanal ekseni, 1.858 m² (yeşil)

Çıkış borusunun üst yüzü: `gas_outlet` — z = 17.440 m, 4.524 m² (mavi)

Toz çıkışı diski: `dust_outlet` — z = 0, 0.126 m² (turuncu)

Diğer bütün yüzler duvar (gri): `cyclone_wall`, `cone_wall`, `vortex_finder_wall`, `meal_inlet_wall`

Yüzler adla değil, geometrileriyle (düzlem mi, normali, üzerindeki nokta) bulunur; Boolean sonrası yüz adları yeniden üretildiği için ad araması kırılgandır. Etiketler yüz rengi olarak taşınır; AP214 renkleri koruduğundan Fluent Meshing bunlardan named selection üretir.

## İlk CFD Koşusu (kaba mesh, 24–25 Eylül 2026)

Bu bölüm **aşılmış bir geometriyle** (vorteks bulucu 0.05 m, çıkış uzatması 1.0 D, kanal −y'de) ve
kaba bir mesh'le alınmış sonuçları taşır. Silinmiyor: yeni mesh'in karşılaştırma tabanı bu.

Akışkan: hava, `incompressible-ideal-gas`, Sutherland viskozitesi, işletme basıncı 101325 Pa.
Sınır koşulları: `meal_inlet` mass-flow-inlet 17.9 kg/s (sektör tipiği; twin'in kendi değeri 7.46 kg/s
ama gaz tarafı düşük), 603 K, türbülans %3.5 / D_h = 1.23 m. `gas_outlet` pressure-outlet 0 Pa.
**`dust_outlet` duvar** — farin klapesi gazı geçirmez (karar 4). Basınç şeması PRESTO!.

| Büyüklük | k-ε (Realizable) | RSM (Linear Pressure-Strain) |
|---|---|---|
| ΔP (giriş statik basıncı) | 600 Pa | **611 Pa** (±4.6, %0.75) |
| Giriş hız yüksekliği ΔP/q | 7.6 | 7.7 |
| v_max | 35.48 m/s | 36.83 m/s |
| Kütle dengesizliği (ortalama) | %0.02 | %0.005 |
| Çıkış yüzünde geri akış | — | %40–44 alan |

Giriş hızı 16.5 m/s, ρ = 0.585 kg/m³, dinamik basınç q = 79.3 Pa. Shepherd-Lapple bağıntısı
N_H = 16·a·b/D_e² = 5.2 hız yüksekliği (409 Pa) veriyor; CFD %47 üstünde, bağıntının kendi ±%50
saçılımı içinde. Domen ayrıca 3 m'lik giriş kanalını ve çatı üstü çıkış borusunu da sayıyor,
bağıntı yalnızca gövdeyi sayar.

ΔP kütle debisinin karesiyle gider: ΔP = 611 × (ṁ/17.9)². Twin'in gaz tarafı düzeldiğinde CFD'yi
yeniden koşmak gerekmez, bu formülle taşınır.

**Sonuç mesh bağımsız değil.** k-ε → RSM geçişi girdaplı akış için yapılabilecek en büyük türbülans
modeli değişikliğidir ve literatürde çekirdek çözülebildiğinde tepe hızı %20–50 artırır; burada %4
oynadı. Sebep mesh: global eleman boyu 0.15 m, hiçbir yerel kontrol yok, 230 bin tet → 45 bin poly,
girdap çekirdeği (≈1 m) boyunca **7 hücre**. Fluent içinde çekirdek adaptasyonla 673 bin hücreye
(çekirdek boyunca 20 hücre) çıkarıldı ama koşu tamamlanamadı; adaptasyon ayrıca vorteks bulucu
ağzında orthogonal quality'yi 0.015'e düşürdü ve bu, cidarın 0.08 m'ye çıkarılma gerekçesi oldu.

Yani **611 Pa ve 36.8 m/s alt sınır olarak okunmalıdır**, doğrulanmış değer olarak değil.

Sıradaki mesh hedefi (Fluent Meshing, Watertight Geometry, poly-hexcore — Ansys Meshing'in
tet→poly yolu Student lisansının hücre bütçesinin %80'ini harcıyor):

| Bölge | Hedef eleman boyu |
|---|---|
| Global | 0.10 m |
| Çekirdek (silindir r = 1.6 m, **z = 0 → 12.5**) | 0.05 m |
| Çıkış borusu uzatması (z = 12.5 → 17.44) | 0.10 m |
| Vorteks bulucu alt ağzı (halka yüzü, 80 mm) | 0.02 m |
| Teğet giriş kenarı | 0.03 m |
| Duvar inflation | ilk katman 5 mm, 8 katman, büyüme 1.2 (y+ ≈ 50) |

Çekirdek bölgesi çatının ~1 m üstünde **bilerek** bitiyor. Ondan yukarısı düz bir borudur ve
ilgilendiğimiz fizik orada değil; oraya da 0.05 m vermek 27.14 m³'e ~217 bin hücre demek olurdu,
0.10 m ise ~27 bin. Aradaki 190 bin hücre, Student lisansının bütçesinin beşte biri, hiçbir şey
kazandırmadan harcanırdı. Uzatmanın işi sınır koşulunu akıştan uzaklaştırmak, çözünürlük taşımak
değil.

## Derived Properties

Ekipman hacmi (her biri): 124.54 m³ — kalma süresi, holdup ve benzeri fiziksel hesaplar bunu kullanır

Toplam yükseklik (gövde + koni): 11.44 m

Koni duvarının yatayla açısı: 67.1° — farinin 40°'lik yığılma açısının üstünde

Giriş kesit alanı: 1.858 m²

Giriş hidrolik çapı: 1.23 m

Vorteks bulucu kesiti: 4.524 m²

Toz çıkışı kesiti: 0.126 m²

Islak alan (gövde + çatı halkası + koni): 139.7 m²

Vorteks bulucunun dış yarıçapı ile kanalın iç duvarı arasındaki pay: 0.020 m — akışkan içinde bir darboğaz değil (aradaki bölge halkanın kendisi, serbest); kanalın vorteks bulucuyu kesmemesini garanti eden geometrik sınır

Not: Geometrik olarak eksik olan volüt ve C1 Y ayrımı, ilk tek-C1 CFD modeli için gerekli değildir. Bunlar daha sonraki çoklu C1/dağıtım geometrisi çalışmasında ele alınacaktır.
