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

Giriş kanalı: y = 1.300 → 2.160 (dış duvar gövdeye teğet); ekseni (cos5°, 0, −sin5°); teğet düzlemine varmadan **x = −0.462'de** biter (dil, aşağıya bakın); gövdenin teğet düzleminde (x = 0) izdüşümü z = 9.071 → 11.239 m; gövdedeki açıklığın en yukarı ulaştığı nokta x = −1.725, z = 11.390 m

Giriş yüzü: merkezi (−2.989, 1.730, 10.416), x = −3.083 → −2.895, z = 9.341 → 11.492 m

Hacim ayrımı:

Ekipman hacmi (gövde + koni): 124.54 m³
+ Gövdenin dışında kalan serbest kanal: 3.31 m³
+ Çatının üstündeki çıkış borusu: 27.14 m³
− Vorteks bulucu duvarı: 1.35 m³
CFD domen hacmi (`C1.step`): 153.65 m³

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi):

`outlet_extension_over_vortex_D`: 2.5 — Çıkış yüzü çatıdan 2.5 vorteks bulucu çapı (6.00 m) yukarıda, z = 17.44.

Bu, çatının üstündeki **çıkış kanalıdır**, vorteks bulucu değil — vorteks bulucu çatıdan aşağı inen 2.16 m'lik daldırma borusudur ve bu parametre ona dokunmaz. Gerçek tesiste çatının üstünde bir kanal vardır (gaz ID fana gider) ama boyu tesis yerleşimine göre belirlenir; buradaki uzunluk bir CFD seçimidir. Siklon CFD literatüründe tipik uzatma 1–5 vorteks bulucu çapıdır.

Başlangıçta 1.0'dı. İlk Fluent koşusu bunun yetmediğini gösterdi: çıkış borusundan yukarı çıkan girdabın merkezinde aşağı yönlü bir ters akım çekirdeği var ve 2.40 m'lik uzatma o çekirdek hâlâ açıkken sınırı kesiyordu — çıkış yüzünün **%40–44'ünde gaz içeri giriyordu**. Fluent orada kullanıcının verdiği backflow değerlerini dayatmak zorunda kalıyor, dayatılan durum domenin istediği durumla çatışıyor ve çözüm yakınsamak yerine kütle dengesinde ±%0.3'lük bir limit çevrimine oturuyordu. 6.00 m, çekirdeğin kapanması için belirgin biçimde daha fazla yer bırakır. Garanti değil: girdap eksenel mesafeyle yavaş söner, dolayısıyla 2.5 D'nin sonunda teğetsel hız hâlâ belirgin olabilir ve bir miktar geri akış kalabilir. Kalırsa seçenekler uzatmayı 4 D'ye çıkarmak ya da geri akışı kabul edip backflow değerlerinin (603 K) doğruluğuna güvenmek — tek girişli ve izotermal bu koşuda o değer zaten doğru.

`inlet_tongue_m`: 0.05 m — Kanalın teğet düzlemine varmadan bittiği yerde bırakılan kabuk kalınlığı (cut-water); aşağıdaki modelleme sadeleştirmeleri listesinde gerekçesi var.

`vortex_finder_wall_m`: 0.08 m — Halkadaki girdabı borudan çıkan gazdan ayıran duvar; hacme etkisi %1.08.

Başlangıçta 0.012 m'ydi, sonra 0.05, şimdi 0.08. Akış plaka kalınlığını umursamaz, mesh umursar: bu genişlik aynı zamanda vorteks bulucunun alt ağzındaki halka yüzünün genişliğidir ve o yüz 7.6 m çevre boyunca uzanır. 0.012 m'de en-boy oranı 631:1, 0.05 m'de 154:1, 0.08 m'de 96:1.

Ağız bir **çıkıntı**, daralan boşluk değil. Prizma katmanları delik duvarından içeri, dış
duvardan dışarı, ağız yüzünden aşağı büyür — üçü de birbirinden uzağa, çakışmazlar. Tek gerçek
gereksinim, yüzey ağının ağzı birkaç elemana bölebilmesi: mesh planındaki 0.02 m yerel yüzey
boyutuyla 0.012 m ancak 0.6 eleman verir (ölçülen 0.95 skewness buradan), 0.05 m 2.5 eleman,
**0.08 m 4 eleman**.

Bir ara bu bölümde 0.015'lik orthogonal quality ölçümü "0.05 yetmedi" kanıtı olarak yazılıydı.
O ölçüm hiyerarşik adaptasyonla, hiçbir yerel boyutlandırma olmadan alındı: Fluent mevcut
hücreleri bölüyordu ve böldüğü özellikten ince hücre üretemiyordu. Yöntemin artefaktıydı,
kalınlık hakkında kanıt değildi. Değer yine de 0.08'de bırakıldı — teğet payı artık bütçeyi
paylaşmadığı için düşürmeyi gerektiren bir şey yok.

80 mm fiziksel olarak da daha savunulabilir: preheater daldırma borusu ısıya dayanıklı çelik ya da SiC'dir, çoğu zaman refrakter kaplıdır; 80 mm olağandır. Üçü içinde en az fiziksel olan başlangıçtaki 12 mm'ydi.

Halka 0.948 → 0.910 → 0.880 m'ye daralıyor. Üst sınır kanalın iç duvarı (y = R − 0.86 = 1.30): vorteks bulucunun dış yarıçapı onun altında
kalmalı, 0.08 m'de pay 0.020 m, 0.10 m tam değerse dayanır ve ön kontrol reddeder. `INLET_TANGENT_RELIEF`
kullanılmıyor (0), teğet kusuru `inlet_tongue_m` ile çözüldüğü için; iki parametrenin 0.10 m'lik
ortak bütçeyi paylaştığı düzen de böylece kalktı.

`inlet_extension_over_D` C1 için **kullanılmaz**: kanal boyu 3.0 m yayınlanmış bir tesis ölçüsüdür, CFD uzatması değil. Gövdenin teğet düzleminden dışarı, kanal ekseni boyunca, kesit ağırlık merkezinden ölçülür — yüz 5° eğik olduğu için başka bir datumla boy ±0.22 m belirsiz kalırdı.

Modelleme sadeleştirmeleri:

- Yayınlanmış volüt modellenmiyor; giriş düz, teğet, 5° eğimli bir kanal.
- Kanalın en yüksek noktası çatının 0.05 m altında tutuluyor (`INLET_ROOF_CLEARANCE`). Kanal siklona doğru indiği için üst kenarını doğrudan çatıya dayamak, kanalı gövdenin izdüşümü üzerinde çatının üstüne çıkarır ve çatı plakasının üzerinde sivrilerek biten çıkmaz bir akışkan kaması bırakırdı. Bu boşluk çatıyı düz, açıklığı gövdede temiz bir delik olarak tutar. Tesis ölçüsü değil, modelleme seçimi.
- Kanal, gövdeye teğet düzlemine **varmadan biter**: `inlet_tongue_m = 0.05` m ile x = −0.462'de.
  Uç kapağının gövdenin içinde kalan kısmı birleşmede erir, dışarıda kalan **0.05 × 2.168 m**'lik
  dikdörtgen kör bir yüz olarak ayakta kalır — gerçek makinedeki **cut-water**'ın karşılığı.

  Gerekçe: kanalın dış duvarı (y = 2.16 düzlemi) ile gövde (r = 2.16 silindiri) x = 0'da
  **teğettir**. Kanal oraya kadar sürdürülürse birleşim sıfır açılı bir kenara kapanıyor ve
  akışkan o çizgi boyunca sıfır kalınlığa iniyor. Bu, modeldeki **mesh'in ulaşamadığı tek
  kusurdu**: dihedral açı ölçekten bağımsızdır, hücreyi yarıya indirince aynı sliver yarı boyunda
  geri gelir. Ölçüldü de — 0.15 m'lik mesh'te o kenardaki hücre orthogonal quality 0.135 / en-boy
  79; adaptasyonla inceltilince en-boy **175'e çıktı**. Modeldeki diğer ince yapılar (vorteks
  bulucu ağzı, çatı altı şeridi) birer **genişliktir** ve yerel yüzey boyutlandırmasına boyun
  eğer; açı eğmez.

  Kanal erken bittiğinde teğetlik geometrik olarak hâlâ var ama x = −0.462 ile 0 arasında **katı
  kabuğun içinde** kalıyor; orada akışkan sınırlamıyor, dolayısıyla mesh'lenmiyor. Açıklıkta
  kalan en kötü köşe, zaten var olan x = −1.725'teki 53°'lik köşe.

  **Ölçüldü (25 Eylül 2026, Ansys Meshing, tet, inflation yok).** Dilin etkisi, element boyu
  dilsiz koşuyla birebir aynı tutularak ayrıştırıldı:

  | metrik | 150 mm, dilsiz | 150 mm, dilli | 200 mm, dilli |
  |---|---|---|---|
  | min orthogonal quality | 0.135 | **0.209** | 0.206 |
  | max skewness | 0.965 | **0.791** | 0.794 |
  | max en-boy oranı | 79 | **9.50** | 10.05 |

  Skewness ve orthogonal quality tek başına kanıt sayılmazdı (kabalaşma da onları düzeltir).
  Kanıt en-boy oranında: teğet kama ölçek-değişmez bir kusurdu ve inceltilince 79'dan 175'e
  *çıkıyordu*, dolayısıyla 1.33× kabalaşma onu 8× düşüremez. 79 → 9.50 geometriden gelir.
  İkinci kanıt, 200 mm ile 150 mm sütunlarının birbirinin aynı olması: mesh artık inceltmeyle
  **bozulmuyor**. Sorunun tanımı buydu.

  **Yeni en kötü hücre dilin kendisinde.** 8 katman prizma eklenmiş 307 bin elemanlı mesh'te
  (Ansys Meshing 150 mm + inflation, ilk katman 5 mm, büyüme 1.2) Fluent'in ölçtüğü minimum
  orthogonal quality **0.1076** ve yeri **(−0.482, 2.125, 10.00)** — uç kapağının hemen
  gerisi, dil yüzünün kapladığı y = 2.110–2.160 bandı. Teğet bölgede değil artık.

  Bu bir sınıf değişimi: kusur 0° dihedral açı değil, **50 mm genişliğinde bir şerit**, ve
  prizma yığını 82.5 mm ile şeritten kalın. Ölçek-bağımlı olduğu için inceltmek düzeltir,
  bozmaz. 0.10 eşiğinin üstünde kaldığı için dokunulmadı; gerekirse iki çaresi var —
  `inlet_tongue_m` 0.05 → 0.10 (şerit prizma yığınından kalın olur) ya da o yüze 0.02 m
  yerel yüzey boyutu.

  Aynı mesh'te max en-boy oranı 32.5 @ (−1.281, −0.045, 9.335), yani r = 1.282'de vorteks
  bulucunun dış duvarında bir **prizma** hücresi (5 mm × ~150 mm). Kusur değil, prizma
  katmanının tanımı.

  Fluent'in `Domain → Check` hacmi **153.5135 m³**, makronun analitik 153.646970 m³'üne göre
  %0.087 düşük. Bu faceting açığı ve büyüklüğü öngörülebilir: r = 2.16 m'lik gövde 150 mm
  kirişle ~90 parçaya bölünür, alan açığı (2π/n)²/6 = %0.081. Geometri tolerans içinde değil,
  **doğru** okunmuş.

  Kalınlık t ile durma noktası: x = √(t(2R − t)). Kesilen akışkan **0.0166 m³**, domenin
  %0.011'i. Katalog kesiti 0.86 × 2.16 ve giriş hızı 16.5 m/s **birebir korunur** — bu yüzden
  dış duvarı içeri çeken `INLET_TANGENT_RELIEF` yerine bu tercih edildi; o, açıyı 0'dan 9.56°'ye
  açıyor ama kamanın ucunu yok etmiyor (yalnızca x = −0.359'a taşıyor) ve kanal boyunca kesit
  götürüyordu (0.86 → 0.83 m, giriş hızı 17.1 m/s). Makro ikisinin birlikte kullanılmasını
  reddeder.

  Dil yüzü bir **çıkıntı**, daralan boşluk değil: 0.02 m yüzey boyutuyla 2.5, 0.0125 m ile 4
  eleman. Kanalın fiziksel boyu 3.0 → 2.54 m'ye iner; 3.0 m, teğet düzlemine ölçülen datum
  olmayı sürdürür ve giriş yüzü yerinde kalır.

- Kanalın açıklığı ile çatı arasında kalan gövde duvarı şeridi, `INLET_ROOF_CLEARANCE = 0.05`
  yüzünden 0.78 m'lik bir yay boyunca 0.10 m'nin altına, en dar yerde 0.05 m'ye iniyor.
  **Bilerek dokunulmadı**: bu bir dar yüzey şeridi, daralan boşluk değil — çatıyla arasındaki
  açı 90°, sliver üretmez, yalnızca mesher'ı orada küçük elemana zorlar ve proximity
  boyutlandırması bunu kendiliğinden yapar. Ölçülmüş bir kötü hücre kanıtı da yok. Mesh orada
  sorun gösterirse değer 0.15'e çekilir; bedeli kanalın 0.10 m inmesi ve açıklığın vorteks
  bulucu ağzının altında kalan oranının %9.6 → %14.3 çıkmasıdır.

- Farin borusu yok; toz çıkışı bir sınır yüzü.
- C1 Y ayrımı modellenmiyor: tek C1 kuruluyor.

Kontrol: `C1.step` tek parça ve kapalı bir katı olmalı, hacmi 153.65 m³ olmalı. Makro bunu ve ara adımların her birini export etmeden önce kendisi doğrular.

STEP'i dosyadan okuyarak doğrulanacak değerler: `CYLINDRICAL_SURFACE` yarıçapları
**200 / 1200 / 1280 / 2160 mm**, kanal köşeleri **y = +1300 … +2160 mm**, z = **0 … 17440 mm**,
ve kanalın uç köşelerinin x'i **−462 mm** (0 değil) — dilin uygulandığının tek satırlık kanıtı.
(Diskteki STEP 25 Eylül 14:30'da dille birlikte yeniden üretildi ve dosyadan okunarak
doğrulandı: yarıçaplar 1200/1280/2160, kanal y = 1300…2160, kanal ucu x = −462.1, dil yüzü
y = 2110 (= 2160 − 50), z = 0…17440 mm. Birim bloğu `SI_UNIT(.MILLI., .METRE.)`.)
(Bir ara makro kanalı −y'de kuruyordu — referans düzlemi orijine göre aynalanmış tarafa
koyuyor ve hiçbir doğrulama bunu göremiyordu, çünkü gövde y'de simetrik olduğundan sınırlayıcı
kutu, ayna hacmi değiştirmediğinden hacim, giriş yüzü aynı kaldığından alan kontrolü hepsi
geçiyordu. Düzlemin yeri artık üzerine bırakılan bir test bloğuyla **ölçülüyor**,
[macros/README.md](../macros/README.md).)

## Boundary Faces

Giriş kanalının uç yüzü: `meal_inlet` — merkezi (−2.989, 1.730, 10.416), normali kanal ekseni, 1.858 m² (yeşil)

Çıkış borusunun üst yüzü: `gas_outlet` — z = 17.440 m, 4.524 m² (mavi)

Toz çıkışı diski: `dust_outlet` — z = 0, 0.126 m² (turuncu)

Diğer bütün yüzler duvar (gri): `cyclone_wall`, `cone_wall`, `vortex_finder_wall`, `meal_inlet_wall`

Yüzler adla değil, geometrileriyle (düzlem mi, normali, üzerindeki nokta) bulunur; Boolean sonrası yüz adları yeniden üretildiği için ad araması kırılgandır. Etiketler yüz rengi olarak taşınır; AP214 renkleri koruduğundan Fluent Meshing bunlardan named selection üretir.

## İlk CFD Koşusu (kaba mesh, 24–25 Eylül 2026)

Bu bölüm **aşılmış bir geometriyle** (vorteks bulucu 0.05 m, çıkış uzatması 1.0 D, kanal −y'de,
kanal teğet düzlemine kadar sürüyor) ve kaba bir mesh'le alınmış sonuçları taşır. Aşağıdaki
sayılar o koşunun kendi geometrisine aittir ve güncellenmez. Silinmiyor: yeni mesh'in karşılaştırma tabanı bu.

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
| Çekirdek (`C1_boi.step`: r = 1.6 m, z = 0 → 12.44) | **0.06 m** |
| Çıkış borusu uzatması (z = 12.44 → 17.44) | 0.10 m |
| Vorteks bulucu alt ağzı (halka yüzü, 80 mm) | 0.02 m |
| Teğet giriş kenarı | 0.03 m |
| Duvar inflation | ilk katman 5 mm, 8 katman, büyüme 1.2 (y+ ≈ 50) |

Hücre bütçesi (Student lisansı 1 milyon):

| | hücre |
|---|---|
| BOI içi, 78.6 m³ @ 0.06 m | ~365.000 |
| BOI dışı, 75.0 m³ @ 0.10 m | ~75.000 |
| Duvar prizma katmanları (tahmin) | ~225.000 |
| **toplam** | **~665.000** |

0.05 m hücreyle BOI içi 629.000'e çıkıyor ve toplam ~930.000 oluyor — sınıra fazla yakın.
0.06 m'de çekirdek çapı boyunca 27 hücre var, yeterli. Hücre boyu bir mesher ayarıdır,
geometri değil; sayı düşük gelirse 0.05'e indirilebilir.

Mesh, Fluent Meshing'in **Watertight Geometry** workflow'uyla ve **poly-hexcore** ile kurulur.
Ansys Meshing'in tet → poly yolu kullanılmaz: dönüşüm hücre sayısını beşte bire düşürüyor ve
Student lisansının 1 milyonluk bütçesinin %80'i orada gidiyor.

| Görev | Ayar |
|---|---|
| Import Geometry | `C1.step`, birim m |
| Add Local Sizing | Face Size, vorteks bulucunun alt halka yüzü (80 mm) → **0.02 m** |
| Generate the Surface Mesh | min **0.02**, max **0.10**, büyüme 1.2 |
| Describe Geometry | *only fluid regions without voids* |
| Update Boundaries | `meal_inlet` mass-flow-inlet, `gas_outlet` pressure-outlet, **`dust_outlet` wall** |
| Add Boundary Layers | 8 katman, ilk katman **5 mm**, büyüme 1.2 (y+ ≈ 50, u_τ ≈ 0.8 m/s'den) |
| Generate the Volume Mesh | poly-hexcore, Max Cell Length **0.08 m** |

Beklenen ~500 bin hücre; çekirdek çapı boyunca ~12 hücre. Hedef 20'ydi, ulaşılamıyor — çünkü
`Max Cell Length` bütün iç hacme aynı boyu verir, sadece çekirdeğe değil. Çekirdeği ayrıca
inceltmek Body of Influence ister, o da geometride **ayrı bir gövde** ister.

Makro o gövdeyi üretebiliyor (`BuildBoi`, eksende r = 1.6 m, z = 0 → 12.44, ayrı `C1_boi.step`)
ama `EXPORT_BOI = False` ile **kapalı**. Sebep mesher tarafı: iki gövdeli geometride Fluent
Meshing'in watertight workflow'u silindiri ayrı bölge olarak tutmak yerine akışkan bölgeye kattı
ve koni onun içinde kayboldu. Geometri doğru, aktarım kurulmadı. Çekirdek çözünürlüğü yetersiz
çıkarsa dönülecek yer burası: `EXPORT_BOI = True`, ve `Update Regions` görevinde silindir
bölgesinin `dead` olduğundan emin olmak. BOI'li hedef 0.06 m hücre ve ~665 bin toplamdı.

## Derived Properties

Ekipman hacmi (her biri): 124.54 m³ — kalma süresi, holdup ve benzeri fiziksel hesaplar bunu kullanır

Toplam yükseklik (gövde + koni): 11.44 m

Koni duvarının yatayla açısı: 67.1° — farinin 40°'lik yığılma açısının üstünde

Giriş kesit alanı: 1.858 m²

Giriş hidrolik çapı: 1.23 m

Vorteks bulucu kesiti: 4.524 m²

Toz çıkışı kesiti: 0.126 m²

Islak alan (gövde + çatı halkası + koni): 139.7 m²

Vorteks bulucunun dış yarıçapı ile kanalın iç duvarı arasındaki pay: 0.020 m (teğet payından etkilenmez — pay yalnızca dış duvarı kaydırır) — akışkan içinde bir darboğaz değil (aradaki bölge halkanın kendisi, serbest); kanalın vorteks bulucuyu kesmemesini garanti eden geometrik sınır

Not: Geometrik olarak eksik olan volüt ve C1 Y ayrımı, ilk tek-C1 CFD modeli için gerekli değildir. Bunlar daha sonraki çoklu C1/dağıtım geometrisi çalışmasında ele alınacaktır.
