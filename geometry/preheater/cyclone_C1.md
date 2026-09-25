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

Giriş genişliği: 0.86 m — FLS oranı (türetilmiş). Kurulan kanal **0.83 m**; aradaki 0.03 m, teğet kenarı açan `INLET_TANGENT_RELIEF`'tir (aşağıya bakın).

Giriş yüksekliği: 2.16 m — **kullanıcı kararı**, katalog değeri değil

FLS oranı 4.97 m veriyor (a/D = 1.15); giriş bilerek kısaltıldı. Gerekçe: yayınlanmış uzun giriş, gerçek makinede 270°'lik sarmal volütle beslendiği için anlamlıdır, bu model ise volütü bilerek kurmuyor. Volüt yerine düz teğetsel kanal konunca uzun giriş gerekçesini kaybediyor — 4.97 m'de açıklığın %61'i vorteks bulucu ağzının (z = 9.28) altında kalıyor ve oradan giren gaz halkayı atlayarak kısa devre yapabiliyor; giriş hızı da ~7 m/s'ye düşüyor, oysa preheater siklonları 15–20 m/s'de çalışır.

2.16 m ise a/D = 0.50 ve a/b = 2.51: Stairmand'in klasik oranı. Açıklığın yalnızca %10'u vorteks bulucu ağzının altında kalıyor ve giriş hızı ~16 m/s'ye dönüyor. Genişlik zaten klasikti (b/D = 0.86/4.32 = 0.199; teğet payından sonra kurulan değer 0.83/4.32 = 0.192).

Ekipman hacmi değişmiyor, dolayısıyla kalma süresi ve holdup etkilenmiyor. Katalog tablosu ([catalog.md](../catalog.md)) yayınlanmış 4.97 değerini taşımaya devam eder; sapma bu dokümanda kayıtlıdır.

Giriş kesit alanı: 1.793 m² (kurulan kesit; katalog genişliğiyle 1.858 m² olurdu)

Giriş kanalı: 0.83 × 2.16 m, 3.0 m uzunluğunda, teğetsel, sabit kesitli, 5° aşağı eğimli

Giriş yönü: Cyclone gövdesine teğetsel ve düşey düzlemde 5° aşağı eğimli

Kesit değişimi: Yok — kanal boyunca sabit

Volüt geometrisi: Modellenmeyecek; basitleştirilmiş düz, teğetsel ve eğimli giriş kullanılacak

C1 Y ayrımı: TBD — `LayoutParams` alanı tanımlı, değeri yok

## CFD Geometry

Katı `geometry/output/2500/C1.step` (ayrıca `.stl` ve `.SLDPRT`), `geometry/macros/cyclone.bas` SolidWorks makrosuyla üretilir. (Eski `python -m geometry --export` komutunun dayandığı paket kaldırıldı.)

CFD domeni, tek C1 cyclone + sabit kesitli teğetsel ve eğimli farin giriş kanalının akış hacmından oluşturulur.

Koordinatlar: siklon ekseni z, toz çıkışı z = 0. Gaz +x yönünde girer; giriş y ∈ [1.30, 2.13] aralığında olduğundan girdap **yukarıdan bakıldığında saat yönündedir**.

Koni: z = 0 → 4.650 m (Φ0.40 → Φ4.32)

Silindirik gövde: z = 4.650 → 11.440 m (çatı)

Vorteks bulucu duvarı: z = 9.280 → 11.440 m, 0.08 m kalınlığında (oyulmuş), r = 1.200 → 1.280

Çıkış borusu (vorteks bulucunun içi): z = 9.280 → 17.440 m, Φ2.40

Giriş kanalı: y = 1.300 → 2.130 (dış duvar gövdeye teğet düzlemden 0.03 m içeride); ekseni (cos5°, 0, −sin5°); gövdenin teğet düzleminde (x = 0) z = 9.071 → 11.239 m; gövdedeki açıklığın en yukarı ulaştığı nokta x = −1.725, z = 11.390 m

Giriş yüzü: merkezi (−2.989, 1.715, 10.416), x = −3.083 → −2.895, z = 9.341 → 11.492 m

Hacim ayrımı:

Ekipman hacmi (gövde + koni): 124.54 m³
+ Gövdenin dışında kalan serbest kanal: 3.15 m³
+ Çatının üstündeki çıkış borusu: 27.14 m³
− Vorteks bulucu duvarı: 1.35 m³
CFD domen hacmi (`C1.step`): 153.48 m³

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi):

`outlet_extension_over_vortex_D`: 2.5 — Çıkış yüzü çatıdan 2.5 vorteks bulucu çapı (6.00 m) yukarıda, z = 17.44.

Bu, çatının üstündeki **çıkış kanalıdır**, vorteks bulucu değil — vorteks bulucu çatıdan aşağı inen 2.16 m'lik daldırma borusudur ve bu parametre ona dokunmaz. Gerçek tesiste çatının üstünde bir kanal vardır (gaz ID fana gider) ama boyu tesis yerleşimine göre belirlenir; buradaki uzunluk bir CFD seçimidir. Siklon CFD literatüründe tipik uzatma 1–5 vorteks bulucu çapıdır.

Başlangıçta 1.0'dı. İlk Fluent koşusu bunun yetmediğini gösterdi: çıkış borusundan yukarı çıkan girdabın merkezinde aşağı yönlü bir ters akım çekirdeği var ve 2.40 m'lik uzatma o çekirdek hâlâ açıkken sınırı kesiyordu — çıkış yüzünün **%40–44'ünde gaz içeri giriyordu**. Fluent orada kullanıcının verdiği backflow değerlerini dayatmak zorunda kalıyor, dayatılan durum domenin istediği durumla çatışıyor ve çözüm yakınsamak yerine kütle dengesinde ±%0.3'lük bir limit çevrimine oturuyordu. 6.00 m, çekirdeğin kapanması için belirgin biçimde daha fazla yer bırakır. Garanti değil: girdap eksenel mesafeyle yavaş söner, dolayısıyla 2.5 D'nin sonunda teğetsel hız hâlâ belirgin olabilir ve bir miktar geri akış kalabilir. Kalırsa seçenekler uzatmayı 4 D'ye çıkarmak ya da geri akışı kabul edip backflow değerlerinin (603 K) doğruluğuna güvenmek — tek girişli ve izotermal bu koşuda o değer zaten doğru.

`inlet_tangent_relief_m`: 0.03 m — Kanalın dış duvarını gövdeye teğet düzlemden içeri çeker; aşağıdaki modelleme sadeleştirmeleri listesinde gerekçesi var.

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
**artık bu payı yemiyor**: yalnızca dış duvarı kaydırdığı için iç duvar 1.30'da sabit. İki parametrenin
0.10 m'lik ortak bütçeyi paylaştığı düzen kaldırıldı.

`inlet_extension_over_D` C1 için **kullanılmaz**: kanal boyu 3.0 m yayınlanmış bir tesis ölçüsüdür, CFD uzatması değil. Gövdenin teğet düzleminden dışarı, kanal ekseni boyunca, kesit ağırlık merkezinden ölçülür — yüz 5° eğik olduğu için başka bir datumla boy ±0.22 m belirsiz kalırdı.

Modelleme sadeleştirmeleri:

- Yayınlanmış volüt modellenmiyor; giriş düz, teğet, 5° eğimli bir kanal.
- Kanalın en yüksek noktası çatının 0.05 m altında tutuluyor (`INLET_ROOF_CLEARANCE`). Kanal siklona doğru indiği için üst kenarını doğrudan çatıya dayamak, kanalı gövdenin izdüşümü üzerinde çatının üstüne çıkarır ve çatı plakasının üzerinde sivrilerek biten çıkmaz bir akışkan kaması bırakırdı. Bu boşluk çatıyı düz, açıklığı gövdede temiz bir delik olarak tutar. Tesis ölçüsü değil, modelleme seçimi.
- Kanalın dış duvarı gövdeye **teğet değil**: `INLET_TANGENT_RELIEF = 0.03` m ile içeri
  çekildi, dış duvar y = 2.130'da. Tam teğetken (0) birleşim, teğet çizgi boyunca sıfır açılı
  bir kenara kapanıyor ve akışkan orada sıfır kalınlığa iniyordu.

  Bu, modeldeki **mesh'in ulaşamadığı tek kusurdu**. Dihedral açı ölçekten bağımsızdır: hücre
  boyunu yarıya indirince aynı sliver yarı boyunda geri gelir. Ölçüldü de — 0.15 m'lik mesh'te
  o kenardaki hücrenin orthogonal quality'si 0.135 ve en-boy oranı 79'du; adaptasyonla
  inceltilince en-boy oranı **175'e çıktı**, yani incelttikçe kötüleşti. Modeldeki diğer bütün
  ince yapılar (vorteks bulucu ağzı, çatı altı şeridi) bir **genişliktir** ve genişlik yerel
  yüzey boyutlandırmasına boyun eğer; açı eğmez.

  Ayrıca bir **daralan boşluk**, çıkıntı değil: her iki yüzey de no-slip duvar, prizma
  katmanları birbirine doğru büyüyüp eziliyordu.

  Değeri şöyle okuyun: **teğet çizgiye yakın bölgede izin verilen en küçük akışkan kalınlığı.**
  Kama x²/2R ile kalınlaştığından 0.03 m, |x| < 0.359 m aralığında 30 mm'den ince akışkanı
  kesip atıyor ve içerdeki açıyı 0°'den **9.56°**'ye açıyor.

  Yalnızca **dış duvarı** kaydırıyor. Eskiden iki duvarı birden kaydırıyordu; o zaman 0.86 × 2.16
  kesiti korunuyordu ama iç duvar vorteks bulucuya yaklaşıyor ve `vortex_finder_wall_m` ile
  0.10 m'lik bir bütçeyi paylaşmak zorunda kalıyordu. Dış duvar hiçbir şeye komşu olmadığı için
  tek başına kaydırmak hiç pay yemiyor. Bedeli kesit: 0.86 → 0.83 m, 1.858 → 1.793 m² (−%3.5),
  giriş hızı 16.5 → 17.1 m/s (preheater bandı 15–20 m/s), b/D 0.199 → 0.192 (Stairmand 0.20).
  Genişlik zaten yayınlanmış bir tesis ölçüsü değil, FLS oranından türetilmiş bir değer.

- Kanalın açıklığı ile çatı arasında kalan gövde duvarı şeridi, `INLET_ROOF_CLEARANCE = 0.05`
  yüzünden 0.78 m'lik bir yay boyunca 0.10 m'nin altına, en dar yerde 0.05 m'ye iniyor.
  **Bilerek dokunulmadı**: bu bir dar yüzey şeridi, daralan boşluk değil — çatıyla arasındaki
  açı 90°, sliver üretmez, yalnızca mesher'ı orada küçük elemana zorlar ve proximity
  boyutlandırması bunu kendiliğinden yapar. Ölçülmüş bir kötü hücre kanıtı da yok. Mesh orada
  sorun gösterirse değer 0.15'e çekilir; bedeli kanalın 0.10 m inmesi ve açıklığın vorteks
  bulucu ağzının altında kalan oranının %9.6 → %14.3 çıkmasıdır.

- Farin borusu yok; toz çıkışı bir sınır yüzü.
- C1 Y ayrımı modellenmiyor: tek C1 kuruluyor.

Kontrol: `C1.step` tek parça ve kapalı bir katı olmalı, hacmi 153.48 m³ olmalı. Makro bunu ve ara adımların her birini export etmeden önce kendisi doğrular.

STEP'i dosyadan okuyarak doğrulanacak değerler: `CYLINDRICAL_SURFACE` yarıçapları
**200 / 1200 / 1280 / 2160 mm**, kanal köşeleri **y = +1300 … +2130 mm**, z = **0 … 17440 mm**.
Dış duvarın 2160 değil 2130 olması, teğet payının uygulandığının tek satırlık kanıtı.
(Diskteki STEP, 25 Eylül 03:20, pay uygulanmadan önce üretildi ve dış duvarı 2160'ta taşıyor;
kanalın +y'de olduğu orada zaten doğrulandı.)
(Bir ara makro kanalı −y'de kuruyordu — referans düzlemi orijine göre aynalanmış tarafa
koyuyor ve hiçbir doğrulama bunu göremiyordu, çünkü gövde y'de simetrik olduğundan sınırlayıcı
kutu, ayna hacmi değiştirmediğinden hacim, giriş yüzü aynı kaldığından alan kontrolü hepsi
geçiyordu. Düzlemin yeri artık üzerine bırakılan bir test bloğuyla **ölçülüyor**,
[macros/README.md](../macros/README.md).)

## Boundary Faces

Giriş kanalının uç yüzü: `meal_inlet` — merkezi (−2.989, 1.715, 10.416), normali kanal ekseni, 1.793 m² (yeşil)

Çıkış borusunun üst yüzü: `gas_outlet` — z = 17.440 m, 4.524 m² (mavi)

Toz çıkışı diski: `dust_outlet` — z = 0, 0.126 m² (turuncu)

Diğer bütün yüzler duvar (gri): `cyclone_wall`, `cone_wall`, `vortex_finder_wall`, `meal_inlet_wall`

Yüzler adla değil, geometrileriyle (düzlem mi, normali, üzerindeki nokta) bulunur; Boolean sonrası yüz adları yeniden üretildiği için ad araması kırılgandır. Etiketler yüz rengi olarak taşınır; AP214 renkleri koruduğundan Fluent Meshing bunlardan named selection üretir.

## İlk CFD Koşusu (kaba mesh, 24–25 Eylül 2026)

Bu bölüm **aşılmış bir geometriyle** (vorteks bulucu 0.05 m, çıkış uzatması 1.0 D, kanal −y'de,
teğet payı yok, giriş genişliği 0.86 m) ve kaba bir mesh'le alınmış sonuçları taşır. Aşağıdaki
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

Giriş kesit alanı: 1.793 m²

Giriş hidrolik çapı: 1.199 m

Vorteks bulucu kesiti: 4.524 m²

Toz çıkışı kesiti: 0.126 m²

Islak alan (gövde + çatı halkası + koni): 139.7 m²

Vorteks bulucunun dış yarıçapı ile kanalın iç duvarı arasındaki pay: 0.020 m (teğet payından etkilenmez — pay yalnızca dış duvarı kaydırır) — akışkan içinde bir darboğaz değil (aradaki bölge halkanın kendisi, serbest); kanalın vorteks bulucuyu kesmemesini garanti eden geometrik sınır

Not: Geometrik olarak eksik olan volüt ve C1 Y ayrımı, ilk tek-C1 CFD modeli için gerekli değildir. Bunlar daha sonraki çoklu C1/dağıtım geometrisi çalışmasında ele alınacaktır.
