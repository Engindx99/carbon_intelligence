# Cyclone C1

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, §6, Ek). Referans hat: 2500 t/d.

Farin borusu: [meal_pipe_C1.md](meal_pipe_C1.md)

C1 iki siklondan oluşur (×2); aşağıdaki değerler her biri içindir.

Tesiste iki özdeş 2500 t/d hattı var; her hatta bir ikiz C1, toplam 4 C1, hepsi CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)). Tesis debisindeki değerler aşağıda, "Tesis debisinde" bölümünde.

C1, FLS'nin tek üst siklonundan çoklu C1'e aktarım varsayımını taşır; bu varsayım not edilerek kurulmalı.

## Geometrik Ölçüler

Yayınlanmış olan yalnız çap D'dir (HFC2500); gövde, koni, vorteks bulucu, toz çıkışı ve giriş genişliği D'den FLS oranlarıyla türetilir ([catalog.md](../catalog.md)).

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Hat başına adet | 2 | yayınlanmış |
| Efektif iç çap D | 4.32 m | yayınlanmış |
| Silindirik gövde yüksekliği | 6.79 m | FLS oranıyla türetilmiş |
| Koni yüksekliği | 4.65 m | FLS oranıyla türetilmiş |
| Vorteks bulucu daldırması S | 3.45 m | CFD kararı |
| D_x / D (= riser çapı / D) | 0.5 | CFD kararı |
| Vorteks bulucu çapı D_x (= riser çapı) | 2.1600 m | 0.5 D |
| Toz çıkışı çapı | 0.4 m | FLS oranıyla türetilmiş |
| Giriş genişliği | 0.86 m | FLS oranıyla türetilmiş |
| Giriş yüksekliği | 3 m | CFD kararı |
| Giriş eğimi | 0 ° | CFD kararı |
| Volüt | var | CFD kararı |
| Çıkış dönüşü | 180 ° | CFD kararı |
| Çıkış borusu yükselişi (çatının üstünde) | 2.700 m | 1.25 D_x |
| Çıkış dirseği merkez yarıçapı | 3.240 m | 1.5 D_x |
| Çıkış bacağı / inişi | 2.700 m | 1.25 D_x |
| Toplam yükseklik (gövde + koni) | 11.440 m | türetilmiş |
| **Ekipman hacmi (gövde + koni)** | 124.54 m³ | türetilmiş |
| **Islak alan (gövde + çatı halkası + koni)** | 140.56 m² | türetilmiş |
<!-- END GENERATED -->

### Farin Girişi

**Volütlü giriş, 0.86 × 3.00 m, daldırma S 3.45 m (kullanıcı kararı, 16 Kasım 2026).** Giriş ve daldırma CFD kararıdır, katalog değeri değil; ölçüler yukarıdaki tabloda.

Giriş tipi: Volüt (C4 ve C5 ile aynı yapı, `cyclone.bas` VOLUTE_ON): gövdenin dışında, çatıyla aynı hizada yatay bir kanal ve onun döndüğü yarım tur Arşimet sarmalı (r 3.07 → 2.21 m). Kanalın iç duvarı gövdenin teğet çizgisinin 0.05 m dışında (dil).

Giriş kesiti: Dikdörtgen, 0.86 × 3.00 m, kesit alanı 2.58 m²; kanal teğet düzleminden 3.0 m geriye, eğimsiz.

Gerekçe:
- Eski giriş (0.86 × 2.16 m'lik düz yarık, 5° aşağı eğimli, S 2.16 m) 17.9 kg/s için boyutlanmıştı (giriş hızı ~16.5 m/s).
- Tesisin debisi C1 başına 28.76 kg/s (ID fanın debisi, iki C1'e bölünmüş; ~603 K). Bu debide yarık 24.9 m/s ile çalışıyordu ve kanalın iç duvarı vorteks bulucunun dış duvarına yalnız 20 mm kalıyordu: jet doğrudan vorteks bulucuya çarpıyordu.
- a 3.00 m, giriş hızını 17.9 m/s'ye, preheater siklonlarının 15–20 m/s bandının ortasına getirir. Katalogdaki 4.97 m (a/D 1.15) 10.8 m/s verir ve S'yi 5.7 m'ye zorlar.
- Volüt jeti gövdenin dışından sokar, vorteks bulucuya çarpmasını önler. Yayınlanmış makine de volütlüdür (FLS'nin uzun girişi 270°'lik sarmalla anlamlıdır).
- S/a 1.15: Hoffmann & Stein'ın 1.1–1.2 aralığı; C4'te aynı kural uygulandı. Vorteks bulucu ağzı (z 7.99) volütün tabanının (z 8.44) 0.45 m altında, koninin 3.34 m üstünde; ağız altında açıklık kalmıyor.

Yüklü Muschelknautz ile karşılaştırma (tesis debisi, betik `c1_inlet_options.py`, çekirdek `C:\Users\engin\c4\mm\mm_loaded.py`). Gaz-yalnız ΔP mevcut yarık için CFD'nin Euler sayısıyla (6.35), diğerleri MM oranıyla ölçeklendi; volütün α'sı C4'ün CFD'sinden (0.91):

| Seçenek | v_in | Gaz ΔP | Yüklü ΔP | x₅₀ | η alt–üst |
|---|---|---|---|---|---|
| Eski yarık, a 2.16, S 2.16 | 24.9 m/s | 1223 Pa | 591 Pa | 20.2 µm | %97.0–98.7 |
| Yarık, a 3.00, S 3.45 | 17.9 | 764 | 391 | 27.5 | %95.9–97.9 |
| Yarık, a 4.97 (katalog), S 5.72 | 10.8 | 388 | 221 | 50.7 | %92.7–94.9 |
| **Volüt, a 3.00, S 3.45** | **17.9** | **810** | **495** | **24.7** | **%96.3–98.3** |

Bu oranlar MM'den gelir; volütlü C1'in kendi Euler sayısını yeni CFD verecek. O gelene kadar twin `c1_euler` 8.12 kullanır (6.35 × MM oranı 0.662 × alan oranının karesi 1.929; `configs/twin_cfg.yaml`).

Ekipman hacmi (gövde + koni) değişmiyor, kalma süresi ve holdup etkilenmiyor. Katalog tablosu ([catalog.md](../catalog.md)) yayınlanmış 4.97 ve 2.16 değerlerini taşımaya devam eder; sapma burada kayıtlıdır.

C1 Y ayrımı: ikiz C1 ve R1'in Y'si [riser_R1.md](riser_R1.md)'de ve `C1_twin` katısında.

## CFD Geometry

### Güncel geometri: volüt (16 Kasım 2026)

İki katı, ikisi de `geometry/macros/cyclone.bas` ile (build logu `geometry/output/2500/C1_cyclone_build.log`):
- **`C1_riser`** (`main`): CFD domeni, riser koluyla birlikte ([riser_R1.md](riser_R1.md)). **265.10 m³**, kapalı tek katı (51 kenar). Sınır yüzleri: gaz girişi riser tabanı 3.701 m², `gas_outlet` 4.524 m², `dust_outlet` 0.126 m², `meal_feed` 0.36 m² (gaz için duvar).
- **`C1`** (`gas_only`): riser'sız C1, teknik resmin katısı. **219.59 m³** (29 kenar); giriş yüzü kanalın ucu, 2.58 m².

Ölçüler (C1 koordinatları; siklon ekseni z, toz çıkışı z = 0, gaz +x yönünde girer):
- Volüt kanalı: y 2.21 … 3.07, z 8.44 … 11.44 (çatıyla aynı hizada); uç yüzü x = −3.00. Sarmal +x tarafında gövdeyi sarar, −y'de r 2.21'de kapanır; sarmalın gövde dışındaki alanı 3.716 m². Karşı taraftaki uç −y'de 2.227 m'ye kadar uzanır.
- Vorteks bulucu: z 7.99 … 11.44, iç Ø2.40, duvar 0.08 m.
- Çıkış: çatının 3.00 m üstüne yükseliş, 180° dirsek (R 3.60 m) +x'e, aşağı inen bacak x = 7.20; `gas_outlet` z = 11.44.
- Girdap yukarıdan bakıldığında saat yönünde.

Hacim aşamaları (log): gövde + koni 124.541; + volüt 143.428; − vorteks bulucu duvarı 141.277; + çatı üstü boru 154.850; + kaz boynu 206.014; + iniş 219.586 m³. Riser'lı domende sonra + riser dirseği 232.207; + riser 259.965; + geçiş (loft) 264.729; + farin oluğu 265.099 m³.

**Bu bölümün geri kalanı ve aşağıdaki CFD koşuları (500.8 Pa, Eu 6.35, MM kalibrasyonu, DPM) eski yarık geometrisine aittir:** 0.86 × 2.16 m, 5° aşağı eğimli kanal, S 2.16 m. Tarihçe olarak tutuluyor. Volütlü C1'in CFD'si henüz yapılmadı.

### Eski geometri: düz yarık (Eylül – 16 Kasım 2026)

Katı `geometry/output/2500/C1.step` (ayrıca `.stl` ve `.SLDPRT`), `geometry/macros/cyclone.bas` SolidWorks makrosuyla üretilir. (Eski `python -m geometry --export` komutunun dayandığı paket kaldırıldı.)

CFD domeni, tek C1 cyclone + sabit kesitli teğetsel ve eğimli farin giriş kanalının akış hacmından oluşturulur.

Koordinatlar: siklon ekseni z, toz çıkışı z = 0. Gaz +x yönünde girer; giriş y ∈ [1.30, 2.16] aralığında olduğundan girdap **yukarıdan bakıldığında saat yönündedir**.

Koni: z = 0 → 4.650 m (Φ0.40 → Φ4.32)

Silindirik gövde: z = 4.650 → 11.440 m (çatı)

Vorteks bulucu duvarı: z = 9.280 → 11.440 m, 0.08 m kalınlığında (oyulmuş), r = 1.200 → 1.280

Çıkış borusu (vorteks bulucunun içi): z = 9.280 → 17.440 m, Φ2.40

Çıkış dirseği: z = 17.440'ta başlayıp −x yönüne (giriş kanalının tarafına) dönen kavisli 90° dirsek, merkez çizgisi yarıçapı 3.60 m (1.5 D); ekseni (−3.60, 0, 17.44)'ten geçen y'ye paralel doğru. Bittiği yer x = −3.60 düzlemi, kesit merkezi z = 21.04

Yatay çıkış kanalı: x = −3.60 → −8.40 m, ekseni z = 21.04, Φ2.40; en yüksek nokta z = 22.24

**Çıkış kaz boynu (29 Eylül 2026, riser'lı domen ve bundan sonraki bütün domenler):** C1 en üst siklon; tesiste gaz çatıdan çıkıp ters U biçiminde aşağı döner ve fana giden kanala bağlanır (kullanıcı kararı). Makro artık 90° dirsek + yatay kanal yerine **180°'lik dirsek** (aynı R 3.60 m) ve **aşağı inen, yükselişle eşit boyda düz boru** kurar (bacakları eşit bir U; 4.8 m'lik ilk hali fazla sarkıyordu). Çatı üstündeki düz yükseliş de kaz boynu tesisteki gibi çatıya yakın dursun diye yarıya indirildi: 6.00 → **3.00 m** (1.25 D), dirsek z = 14.44'te başlar, ekseni (+3.60, 0, 14.44). Dönüş **+x** yönüne, riser'ın ters tarafına; −x'te aşağı inen bacak riser dirseğine yaklaşırdı. İnen borunun ekseni x = 7.20; `gas_outlet` z = 11.44'te (çatı düzlemi, ama x = 6.0–8.4'te gövdenin dışında) aşağı bakan Φ2.40 disk. Hacim: çatı üstü boru 13.57 m³ (27.14 yerine), dirsek A·π·3.60 = 51.16 m³, inen boru 13.57 m³ (yerine geçtikleri dirsek 25.58 + yatay kanal 21.71). Yukarıdaki 90° dirsek ve yatay kanal, doğrulanmış gaz-yalnız domenin (`C1.step`, 200.94 m³) geometrisi; aşağıdaki URANS, mesh ve RSM sonuçları ona aittir. Makroda `RISER_ON = False` artık o domeni değil, kaz boyunlu gaz-yalnız domeni (≈204.8 m³) kurar; eski makro commit 1249eb9'da.

Giriş kanalı: y = 1.300 → 2.160 (dış duvar gövdeye teğet); ekseni (cos5°, 0, −sin5°); teğet düzlemine varmadan **x = −0.462'de** biter (dil, aşağıya bakın); gövdenin teğet düzleminde (x = 0) izdüşümü z = 9.071 → 11.239 m; gövdedeki açıklığın en yukarı ulaştığı nokta x = −1.725, z = 11.390 m

Giriş yüzü: merkezi (−2.989, 1.730, 10.416), x = −3.083 → −2.895, z = 9.341 → 11.492 m

Hacim ayrımı:

Ekipman hacmi (gövde + koni): 124.54 m³
+ Gövdenin dışında kalan serbest kanal: 3.31 m³
+ Çatının üstündeki çıkış borusu: 27.14 m³
+ Çıkış dirseği (Pappus, A · π/2 · 3.60): 25.58 m³
+ Yatay çıkış kanalı: 21.71 m³
− Vorteks bulucu duvarı: 1.35 m³
CFD domen hacmi (`C1.step`): 200.94 m³ (dirsekten önce 153.65 m³)

CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

CFD sınır varsayımları (config `geometry.cfd_boundary`; tesis ölçüsü değil, kaynakları yok, modelleme seçimi):

`outlet_extension_over_vortex_D`: 2.5 — Çıkış borusu çatıdan 2.5 vorteks bulucu çapı (6.00 m) düz yükselir, z = 17.44. Dirsek eklenene kadar çıkış yüzü buradaydı.

Bu, çatının üstündeki **çıkış kanalıdır**, vorteks bulucu değil — vorteks bulucu çatıdan aşağı inen 2.16 m'lik daldırma borusudur ve bu parametre ona dokunmaz. Gerçek tesiste çatının üstünde bir kanal vardır (gaz ID fana gider) ama boyu tesis yerleşimine göre belirlenir; buradaki uzunluk bir CFD seçimidir. Siklon CFD literatüründe tipik uzatma 1–5 vorteks bulucu çapıdır.

Başlangıçta 1.0'dı. İlk Fluent koşusu bunun yetmediğini gösterdi: çıkış borusundan yukarı çıkan girdabın merkezinde aşağı yönlü bir ters akım çekirdeği var ve 2.40 m'lik uzatma o çekirdek hâlâ açıkken sınırı kesiyordu — çıkış yüzünün **%40–44'ünde gaz içeri giriyordu**. Fluent orada kullanıcının verdiği backflow değerlerini dayatmak zorunda kalıyor, dayatılan durum domenin istediği durumla çatışıyor ve çözüm yakınsamak yerine kütle dengesinde ±%0.3'lük bir limit çevrimine oturuyordu. 6.00 m, çekirdeğin kapanması için belirgin biçimde daha fazla yer bırakır. Garanti değil: girdap eksenel mesafeyle yavaş söner, dolayısıyla 2.5 D'nin sonunda teğetsel hız hâlâ belirgin olabilir ve bir miktar geri akış kalabilir. Kalırsa seçenekler uzatmayı 4 D'ye çıkarmak ya da geri akışı kabul edip backflow değerlerinin (603 K) doğruluğuna güvenmek — tek girişli ve izotermal bu koşuda o değer zaten doğru.

Kaldı. Tet → poly dönüşümünden sonra çekirdek daha az yayıldı, girdap güçlendi (v_max 26 → 34 m/s) ve ters akım çekirdeği 6.00 m'nin sonuna yine ulaştı: k-ω SST steady koşusunda (26 Eylül 2026) çıkış yüzünün **%38'inde** (salınım içinde %33–42) geri akış ölçüldü. Kütle dengesizliği, ΔP ve geri akış oranı aynı 18 iterasyonluk periyotla birlikte salınıyordu (korelasyon ~0.8). Bu yüzden 4 D'ye uzatmak yerine çıkışa bir dirsek eklendi (kullanıcı kararı): girdap düz boruda çok yavaş söner, dirsek onu ve ters akım çekirdeğini kırar, tesiste de gaz C1'den fana giden bir kanala döner.

`outlet_bend_r_over_vortex_D`: 1.5 — Dirseğin merkez çizgisi yarıçapı, 3.60 m. Olağan uzun yarıçaplı dirsek; 0.5'in altında dirseğin iç duvarı kendi içinden geçer, makro reddeder. Dönüş yönü (−x, giriş kanalıyla aynı taraf; kullanıcı kararı) keyfi: tek siklon için aşağı akış kanalını yerleştiren bir kaynak yok.

`outlet_run_over_vortex_D`: 2.0 — Dirsekten sonraki yatay düz kanal, 4.80 m. Çıkış yüzü bunun ucunda, x = −8.40 m; hâlâ dönen akışın içinde durmasın diye dirseğin hemen ucunda değil.

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

Güncel (volüt, 16 Kasım 2026):
- `C1_riser`: gaz girişi riser tabanı (z 0.269, daire 3.701 m², yeşil), `meal_feed` oluğun ucu (0.36 m², mor, gaz için duvar), `gas_outlet` iniş bacağının ucu (z 11.44, x 7.20, aşağı bakan Ø2.40 disk, 4.524 m², mavi), `dust_outlet` (0.126 m², turuncu). Volütün kanal ucu riser geçişiyle birleşir, ayrı bir yüz olarak kalmaz.
- `C1` (riser'sız): giriş yüzü volüt kanalının ucu (x = −3.00, merkezi (−3.00, 2.64, 9.94), 2.58 m², yeşil); diğerleri aynı. Volütün x = 0'daki iki dil yüzü duvardır.

Eski yarık geometrisi (tarihçe):

Giriş kanalının uç yüzü: `meal_inlet` — merkezi (−2.989, 1.730, 10.416), normali kanal ekseni, 1.858 m² (yeşil)

Yatay çıkış kanalının uç yüzü: `gas_outlet` — x = −8.400 m, merkezi (−8.40, 0, 21.04), normali −x, 4.524 m² (mavi)

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
tet→poly yolu Student lisansının hücre bütçesinin %80'ini harcıyor).
**Bu plan aşıldı; ne olduğu aşağıdaki "İkinci CFD Koşusu" bölümünde.** Özellikle BOI
yarıçapı 1.6 m ve çekirdek eleman boyu 0.06 m artık geçerli değil — ölçüm ikisini de
değiştirdi.

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

## İkinci CFD Koşusu (dilli geometri + prizma katmanları, 25 Eylül 2026)

Geometri güncel: dil uygulanmış (kanal x = −0.462'de biter), vorteks bulucu cidarı 0.08 m,
çıkış uzatması 2.5 D, kanal +y'de. Mesh **Ansys Meshing**, tet, global 150 mm, 8 prizma
katmanı (ilk 5 mm, büyüme 1.2), **307 bin eleman**, min orthogonal quality 0.1076. Poly'ye
çevrilmedi — bu, ilk koşuyla arasındaki farklardan biri ve sonucu etkiliyor (aşağıda).

Akışkan: sabit ρ = 0.585 kg/m³, μ = 3.0e−05 Pa·s. Bu, ilk koşudaki
`incompressible-ideal-gas` + Sutherland'ın 603 K ve 101325 Pa'daki değerlerine birebir eşit
(ρ = 0.5855, μ = 3.03e−05), yani malzeme bir fark kaynağı değil.

Sınır koşulları ilk koşuyla aynı: `inlet_farine` mass-flow-inlet 17.9 kg/s, `outlet_gas`
pressure-outlet 0 Pa, **`outlet_farine` wall**. Tek fark türbülans şiddeti %5 (ilk koşu %3.5).
Model RSM Linear Pressure-Strain + Scalable Wall Functions, SIMPLE, PRESTO!, ikinci mertebe.

**Yakınsama.** 500 iterasyon, ΔP son 200 iterasyonda **287.16 Pa**, bant ±0.3 (%0.1), eğim
0.0005 Pa/iter. Kütle dengesizliği ±0.005 kg/s (%0.03). İlk koşudaki ±%0.28–0.50'lik limit
çevrimi **kayboldu** — çıkış uzatmasının 1.0 D'den 2.5 D'ye çıkarılması amacına ulaştı.

| Büyüklük | ilk koşu (45 bin poly) | bu koşu (307 bin tet) |
|---|---|---|
| ΔP, giriş statik basıncı | 611 Pa | **254.4 Pa** |
| ΔP, toplam basınç farkı | ölçülmedi | 287.2 Pa |
| Euler ΔP/q | 7.71 | **3.21** |
| v_max | 36.83 m/s | **26.06 m/s** |
| kütle dengesizliği | %0.005 | %0.03 |
| çıkışta geri akış | %40–44 alan | limit çevrimi yok |

Enerji bütçesi kapanıyor, çözümde aritmetik hata yok: P_t,giriş = 254.1 + 79.2 = 333.3 Pa,
P_t,çıkış = 333.3 − 287.2 = 46.1 Pa; çıkıştaki 46.4 Pa kinetik enerji v_rms = 12.6 m/s
demek, eksenel bileşen 17.9/(0.585 × 4.524) = 6.8 m/s, kalan teğetsel ≈ 10.6 m/s.

### Teğetsel hız profili — asıl tanı

z = 8.0 m'de (gövdenin ortası), y = 0 doğrusu boyunca. Bu doğruda teğetsel yön x > 0 için
+y, x < 0 için −y.

| x [m] | \|v_t\| [m/s] |
|---|---|
| −2.16 (duvar) | ~1 |
| −2.10 | 15 |
| −1.10 | **18** (tepe) |
| −0.50 | 8 |
| **+0.35** | **0** |
| +0.95 | 17 |
| +2.05 | 17 |
| +2.16 (duvar) | ~1 |

Üç bulgu:

1. **Girdap ekseni kaymış.** Sıfır geçişi x = 0'da değil **x = +0.35**'te. Gerçek siklonlarda
   girdap salınır (precessing vortex core); kararlı RANS bunu sabit bir kayma olarak gösterir.
2. **Çekirdek 3–4 kat şişmiş.** |v_t| merkezden dışa doğru **r ≈ 1.0 m**'ye kadar doğrusal
   yükseliyor, yani 1 m yarıçaplı bir zorlanmış girdap (katı cisim dönmesi). Gerçek siklonda
   çekirdek yarıçapı D_e/2'nin %20–30'u, burada **0.25–0.35 m** olmalı.
3. **Girdap güçlenmiyor.** Tepe 18 m/s, giriş hızı 16.5 m/s, oran **1.1**; siklonlarda
   1.5–2.5 olur. Giriş açısal momentumu Γ = 16.46 × 1.73 = 28.5 m²/s; kayıpsız serbest
   girdap r = 1.1'de 26 m/s, r = 0.35'te 81 m/s verirdi. Momentum gövdeye giriyor ama merkeze
   **yoğunlaşamıyor**.

Duvar tarafı buna karşılık temiz: profil duvarda tek hücrede sıfıra iniyor, prizma katmanları
çalışıyor.

### İki koşu neden doğrudan karşılaştırılamaz

Dört fark var, ikisi lehte ikisi aleyhte, ve tek skalerle ayrıştırılamazlar:

| fark | yön |
|---|---|
| hücre tipi: 45 bin **poly** → 307 bin **ham tet** (dönüştürülmedi) | aleyhte, poly daha az difüzyon üretir |
| çekirdek çözünürlüğü: global 150 mm, **değişmedi** | aleyhte, mesh çalışmasının tamamı duvara gitti |
| duvar işlemi: prizmasız y+ ≈ 700–1000 → prizmalı **y+ ≈ 34** | lehte, ilki duvar fonksiyonunun geçerlilik bandının dışındaydı ve sürtünmeyi eksik hesaplıyordu |
| çıkış uzatması 1.0 D → 2.5 D, %40–44 geri akış kayboldu | lehte, geri akış Fluent'e sınırda değer dayattırıyor ve kaybı yapay şişiriyordu |

611 Pa ile 254 Pa arasındaki farkın bir kısmı gerçek düzelme, bir kısmı gerileme.
**İkisi de doğrulanmış değer değil.** Ayrıca ilk koşunun kaydı ΔP'yi *giriş statik basıncı*
olarak tanımlıyor; bu koşuda önce toplam basınç farkı ölçüldü (287.2) ve karşılaştırma için
statik basınç ayrıca okundu (254.4). Sonraki koşularda **her ikisi de** kaydedilecek.

### Sonuç

Geometri tarafı bitti: teğet kama yok, duvar profili temiz, hacim doğru, limit çevrimi yok.
Kalan sorun tek başına **çekirdek çözünürlüğü** ve o bir mesher işi.

Çekirdeği 0.30 m yarıçapa oturtmak için doğrusal yükselişi 8–10 hücreyle örmek gerek →
eleman boyu **~0.04 m**. BOI hacmi (r = 0.8 m, z = 2.135 → 12.44) **20.72 m³**:

| | hücre |
|---|---|
| tet @ 0.04 m | 2.75 milyon — yalnızca çekirdek, Student tavanının üstünde |
| hex @ 0.04 m | **324 bin** — dış bölge ve prizmalarla toplam ~500 bin |

Bu, tet yolunu kapatan ilk ölçülmüş argüman: daha önce "limit bağlamıyor" doğruydu (45 bin →
307 bin), ama sorunun nerede olduğu belli olunca tetle ödenemiyor. Sıradaki mesh
**Fluent Meshing, poly-hexcore, BOI ile çekirdekte 0.04 m**.

## Üçüncü CFD Koşusu (dirsekli çıkış, URANS, 26–27 Eylül 2026)

Geometri: çıkışa −x yönünde 90° dirsek + 2 D düz kanal eklendi, domen 200.94 m³. Mesh:
- Ansys Meshing tet, global 0.15 m, 5 prizma katmanı (ilk 5 mm, büyüme 1.2)
- Fluent'te poly'ye çevrildi + `improve-quality` → **150.6 bin hücre**, min orthogonal quality 0.22
- Fluent'in ölçtüğü hacim 200.47 m³, analitik değer 200.94

Model:
- k-ω SST + Curvature Correction, Scalable WF, y+ ≈ 35–40
- SIMPLE, PRESTO!, ikinci mertebe, Bounded Second Order Implicit
- Çıkışta backflow yönü **From Neighboring Cell**; "Normal to Boundary" geri giren akışın dönmesini siliyordu
- ρ = 0.585 kg/m³, μ = 3.0e−05 Pa·s, 603 K

Yöntem literatürden alındı (endüstriyel preheater siklonu için DTU / Mirzaei ve ark. 2023: SST-CC + URANS).

**Neden transient.** Steady çözüm 18.8 iterasyonluk bir salınıma oturdu ve oturmadı. Salınım çıkış geometrisinden (düz boru / dirsek) ve türbülans modelinden (SST / RSM) bağımsızdı: girdap çekirdeğinin kendi salınımı. Steady ΔP 490.2 ± 11.6 Pa.

**Zaman adımı.**
- Oturma: Δt 0.005 s, sonra 0.02 s.
- Δt testi: 0.02 s ile 0.01 s arasında ortalama ΔP farkı ~%0.1, salınım periyodu 0.35 / 0.33 s. **Δt = 0.02 s kabul.** Adım başına 20 iterasyon, residual düşüşü ≥ 2 mertebe.

**Ortalama penceresi:** 585–913. adımlar, 6.6 s = 1 gaz geçiş süresi = 19 periyot.

| Büyüklük | Zaman ortalaması | Anlık salınım (std) |
|---|---|---|
| **Statik ΔP (giriş statik basıncı)** | **503.8 Pa** (standart hata 0.08) | ±12.3 |
| Toplam basınç farkı (dirsek + kanal dahil) | 525.9 Pa | ±7.3 |
| Euler ΔP/q | 6.35 | |
| v_max | 34.70 m/s | ±0.2 |
| Kütle dengesizliği | 3e−4 kg/s (%0.002) | |
| Çıkışta geri akış | ~%30 alan | |
| Salınım | 0.338 ± 0.006 s → **2.96 Hz** | |

- Pencerenin iki yarısı arasındaki fark **%0.01**.
- URANS, steady'den %2.8 yüksek. Mesh çalışması bu yüzden URANS ile yapılacak.
- Shepherd-Lapple (409 Pa) CFD'nin %23 altında.

**Zaman ortalamalı profiller (z = 8 m, y = 0).** Rankine girdabı:

| | +x | −x |
|---|---|---|
| Teğetsel tepe | 26.2 m/s, r = 1.11 m | 27.8 m/s, r = 1.20 m |
| Çekirdek açısal hızı | 22.6 1/s | 22.1 1/s |
| Dış bölge üssü n (v_t·rⁿ = sabit) | 0.52 | 0.65 |
| Eksenel hızın sıfır olduğu yarıçap | 1.17 m | 1.12 m |

- Teğetsel tepe / giriş hızı = 1.6–1.7.
- Eksenel profil "M" biçimli: çekirdekte +3.8 / +4.1 m/s, merkezde +2.5 m/s'lik çukur, duvar yanında −2 m/s.
- Sıfır eksenel hız yüzeyi vorteks bulucu yarıçapında (1.20 m). Literatürle uyumlu.
- Eksen z = 8'de merkezde (v_t = 0 noktası x = −0.03). Konide ortalama alanda bile hafif kıvrık: tek teğetsel girişin asimetrisi.

**Düzeltmeler:**
- İkinci koşu bölümündeki "çekirdek 0.25–0.35 m olmalı" hedefinin kaynağı yoktu. Ölçülen tepe yarıçapı vorteks bulucu yarıçapına yakın (0.92–1.0 r_x). Kaba mesh ve eddy-viscosity modeli çekirdeği yayma eğiliminde; mesh çalışması ve RSM kontrolü bunun ne kadarının sayısal olduğunu gösterecek.
- Aynı bölümdeki "8 prizma katmanı" ifadesi mesh'te 5 katman olarak ölçüldü.

**Çıkış geri akışı için ölçüt.** Keyfi bir "%5 geri akış" sınırı kullanılmıyor. Ölçüt ΔP'nin çıkışa duyarlılığı: düz 2.5 D çıkıştan dirsekli çıkışa geçince steady ΔP 483.4 → 479.1 Pa değişti (−%0.9). Geri akışın kaynağı, çıkış borusunun merkezinde dirseğe kadar uzanan ters akış çekirdeği.

Yedek: `c1_gas_files\dp0\FLU\Fluent\urans_B\` (case, 913. adımın data dosyası, rapor dosyaları, profiller).

## Duvar Isı Kaybı (T1, 27 Eylül 2026)

Siklonun sıcaklık alanı gaz-yalnız ve adiabatik koşuda anlamsız (her yer 603 K). Literatüre göre gaz ile farin arasındaki ısı alışverişinin neredeyse tamamı siklondan önceki riser'da oluyor; siklon esas olarak bir ayırıcı. Bu yüzden ilk termal adım yalnızca kabuk kaybı.

**Kurulum:**
- Malzeme: ideal gaz + Sutherland; cp 1150 (twin'in `Cp_g` değeri), k 0.045.
- Dış duvar (gövde, koni, çatı, giriş kanalı; Fluent'te 147.05 m²): **Mixed** koşul.
  - Dış h = 3.92 W/m²K: twin'in Churchill-Chu dikey formülü, L = 11.44 m.
  - T_amb 300 K, emisivite 0.85.
  - Twin'in preheater katmanları ([physics/shell.py](../../physics/shell.py)) eşdeğer tek katmana çevrildi: 0.21 m, k = 0.227 W/mK, R = 0.924 m²K/W.
- Vorteks bulucu, çıkış borusu, dirsek ve toz çıkışı adiabatik. Vorteks bulucu iki yüzünden de gazla temas ediyor; çıkış hattı CFD uzatması, ekipman değil.
- Yüzeyler Fluent'te hücre bölgesiyle ayrıldı: silindir r = 1.30, z = 9.0–17.6 ve kutu x −9…1.3, z 17.5–22.5.
- Akış t = 12.685 s'deki anlık alanda donduruldu, yalnızca enerji çözüldü (27 iterasyonda yakınsadı).

**Sonuç:**

| Büyüklük | CFD | Twin kabuk modeli (iç film yok) |
|---|---|---|
| Kayıp | **41.80 kW** | 41.1 kW (139.1 m²) |
| Ortalama akı | **284 W/m²** | 296 W/m² |
| Gaz sıcaklık düşüşü (kütle ağırlıklı, entalpiden) | **2.05 K** | 2.09 K |

**Enerji dengesi:** net 453 W, giriş entalpisinin (6.28 MW) %0.007'si. Bunun ~323 W'ı dondurulmuş alanın kendi kütle dengesizliğinden (9.3e−4 kg/s) geliyor.

**Yorum:** CFD akısı %4 düşük. Fark, gaz tarafındaki film direncinden geliyor: ~0.04 m²K/W, yani h_iç ≈ 26 W/m²K. Duvar direncinin (0.92) yanında küçük. Twin'in kabuk yaklaşımı C1 için doğrulanmış oluyor. Duvar kaybı C1'de gazı yalnızca ~2 K soğutuyor. Termal olarak önemli olan gaz-farin alışverişi ve farin yükü (plandaki T2 ve T3 adımları).

Not: Çıkış raporundaki alan ağırlıklı t_out 1.75 K düşüş gösteriyor. Çıkıştaki geri akış bölgesi alan ortalamasını bozduğu için sıcaklık kütle ağırlıklı ya da entalpiden okunmalı.

## Mesh Bağımsızlığı, Seviye 1 (27 Eylül 2026)

**İnceltme:** Fluent region adaption, silindir r = 1.3 m, z = 3.0–9.8 m (çekirdek, teğetsel tepe ve sıfır eksenel hız yüzeyi). İnceltme **steady modda** yapıldı: transient + BSOI'de adaption, zaman terimlerini yeni hücrelere taşırken Fluent'i çökertti (`Add_Continuity_Time_Sources` segfault).

**Mesh:**
- 8 923 hücre inceltildi → **277 145 hücre** (+126 567)
- Çekirdekte hücre boyu ~0.16 → ~0.065 m
- `improve-quality` sonrası min orthogonal quality 0.174

**Koşu:** URANS, aynı ayarlar.
- Oturma: Δt 0.02 s ile 3.3 s.
- Sonra Δt 0.01 s ile 2.55 s. Çekirdekte Courant ~5.

| Büyüklük | Seviye 0 (150.6 bin) | Seviye 1 (277 bin) | Fark |
|---|---|---|---|
| Statik ΔP | 503.8 Pa | tepe 522 → son periyot **509.9**, periyot başına ~1 Pa düşüyor | **+%1.2 … +%3.6** |
| Toplam basınç farkı | 525.9 Pa | 526.4 Pa (son periyot) | ~%0 |
| v_max | 34.7 m/s | 38.1 m/s | +%10 |
| Salınım periyodu | 0.338 s (Δt 0.02) | 0.32 s (Δt 0.02) / 0.30 s (Δt 0.01) | |

**Karar (kullanıcı):** ΔP'nin iki seviye arasındaki farkı, sürüklenme bandının tamamında literatürün %5 kriterinin içinde. Mesh bağımsızlığı ΔP için kabul edildi. Twin'e verilecek değer **504–510 Pa** (gaz-yalnız, 17.9 kg/s, 603 K). Sürüklenmenin sonu beklenmedi.

Çekirdekteki tepe hız mesh bağımsız değil (+%10). ΔP bütünleşik bir büyüklük olduğu için çözünürlüğe daha az duyarlı; tepe hız ise çekirdeğin ne kadar inceltildiğine bağlı. Twin'e ΔP aktarıldığı için belirleyici olan ΔP.

## Türbülans Modeli Kontrolü, RSM (D, 27 Eylül 2026)

**Kurulum:** Seviye 1 mesh (277 145 hücre), SST-CC çözümünden (adım 1498, t = 21.84 s) RSM'e geçildi.
- Linear Pressure-Strain, Scalable wall functions
- Diğer ayarlar URANS ile aynı: BSOI, PRESTO!, ikinci mertebe
- Δt 0.01 s, adım başına en fazla 20 iterasyon, ~26 s/adım
- Koşu adım 1499–2008 arası: 510 adım, 5.1 s akış süresi. Domenin kalma süresi ~6.6 s (201 m³ / 30.6 m³/s), yani ~0.8 kalma süresi.

**Kararlılık ve gerçekçilik** (adım 2000, `.dat.h5`):
- Residual sıçraması yok.
- Negatif normal gerilme yok.
- Schwarz eşitsizliği 64 hücrede bozuluyor (%0.02).
- k medyanı 3.1 m²/s², μt/μ medyanı 800.

Pseudo-time + RSM denemesinde durum çok farklıydı: hücrelerin %25'i ihlaldeydi, μt/μ medyanı 31 000'di. Bu çözümün türbülans alanı fiziksel.

| Büyüklük | SST-CC seviye 1 | RSM, 1709–2008 arası periyot ortalamaları (0.34 s) | Son periyot, SST'ye göre |
|---|---|---|---|
| Statik ΔP | ~510 Pa | 500.5 → 496.6 → 488.1 → 481.6 → **480.5** | **−%6** |
| Toplam basınç farkı | 526.4 Pa | 518.4 → 512.3 → 505.2 → 500.0 → **499.0** | −%5 |
| v_max | 38.1 m/s | 35.96 → 35.81 → 35.45 → 35.16 → **35.07** | −%8 |

- Geçişte ΔP önce +%6 yükseldi (adım 1508'de 535 Pa), sonra sürekli düştü.
- Periyottan periyoda düşüş 4.5 → 3.8 → 2.7 → 1.1 Pa: yavaşlıyor ama durmadı.
- Üstel fit anlamlı bir asimptot vermedi.
- RSM girdabı SST'den daha zayıf tahmin ediyor.

**Sonuç (kullanıcı kararı):** RSM yakınsatılmadı. Plato için 3–5 kalma süresi, yani 10+ saat daha gerekirdi.
- Kayıt: **RSM, SST-CC'nin en az %6 altında ve hâlâ düşüyor.**
- Twin değeri SST-CC ile **504–510 Pa** kalıyor. C1'in statik ΔP belirsizlik bandı 480–510 Pa.
- Ara kademe CFD'si de SST-CC ile çözülecek. Böylece model yanlılığı Euler ölçeklemesinde sadeleşir.
- İki model arasındaki farkı, modelden bağımsız Muschelknautz tahmini (adım E) değerlendirecek.

## Muschelknautz Karşılaştırması (E, 28 Eylül 2026)

**Yöntem:** Muschelknautz yöntemi (MM), Hoffmann & Stein, *Gas Cyclones and Swirl Tubes*, 2. baskı, Böl. 6.
- Giriş daralma katsayısı α, yarık giriş için.
- Duvarda teğetsel hız, v_θw = v_in·R_in/(α·R).
- Duvar sürtünmesiyle kontrol yüzeyindeki (CS: vorteks bulucu yarıçapında, onun altındaki silindir) teğetsel hız v_θCS.
- ΔP = Δp_gövde (duvar sürtünmesi) + Δp_x (çekirdek ve vorteks bulucu).
- f = 0.005: temiz gaz, düz duvar. CFD duvarları da pürüzsüz.

**Girdiler:**
- Bu dokümandaki CFD ölçüleri: giriş 0.86 × 2.16 m, vorteks bulucu iç Φ2.40, dış Φ2.56.
- Gaz: 17.9 kg/s, ρ 0.5855 kg/m³, Q 30.57 m³/s.
- Hızlar: v_in 16.46 m/s, v_x 6.76 m/s, ½ρv_in² = 79.3 Pa.
- Sürtünme alanı A_R = 156.4 m²: çatı 9.5, gövde 92.2, koni 37.4, vorteks bulucu dışı 17.4.

| | MM | CFD SST-CC (seviye 0, ortalama alan) | CFD RSM (seviye 1) |
|---|---|---|---|
| α | 0.622 | – | – |
| v_θ, duvar (giriş seviyesi) | 21.2 m/s | 15.0 m/s (r > 2.0 m ortalaması) | 14.4 m/s |
| v_θCS (r = 1.2 m) | **28.0 m/s** | **26.9 m/s** | 26.7 m/s |
| Statik ΔP | **642 Pa** (gövde 120 + vorteks bulucu 522) | 503.8 Pa (seviye 1: ~510) | 480.5 Pa, düşüyor |
| Euler sayısı | 8.10 | 6.35 (6.43) | 6.06 |

MM'nin f'ye duyarlılığı ters yönde: pürüzlü duvar girdabı zayıflattığı için ΔP düşer.
- f 0.0065 → 602 Pa
- f 0.008 → 569 Pa

**Bulgular:**
- **Girdap gücü uyuşuyor.** Kontrol yüzeyindeki teğetsel hızda MM ile CFD arasındaki fark %4. CS boyunca CFD değeri z'ye neredeyse bağlı değil (26.4–27.0 m/s); MM'nin sabit v_θCS varsayımına uyuyor.
- **ΔP'de MM, SST'nin %27 üstünde.** Fark vorteks bulucu kaybı (Δp_x) bağıntısından geliyor. MM'ye CFD'nin kendi v_θCS değeri (26.9) verilince Δp_x tek başına 492 Pa, toplam 605 Pa. Yani CFD ile tam aynı girdapla bile MM'nin çekirdek/çıkış kaybı CFD'nin toplam ΔP'sine yaklaşık eşit.
- **Duvardaki hızı MM daha yüksek veriyor** (21 m/s'ye karşı 15). CFD değeri duvar sınır tabakasına kadar uzanan bir halkanın ortalaması, bu yüzden düşük kalıyor. z = 8 m'de r = 2.1 m'deki değer 19.2 m/s.
- **Cebirsel bağıntılar CFD'nin iki yanına düşüyor:**

| Bağıntı | Eu | ΔP |
|---|---|---|
| Casal–Martinez | 4.51 | 357 Pa |
| Shepherd–Lapple | 5.16 | 409 Pa |
| CFD SST-CC | 6.35–6.43 | 504–510 Pa |
| Dirgo | 7.03 | 558 Pa |
| MM | 8.10 | 642 Pa |

  CFD, bağıntıların %40'lık yayılımının ortasında. RSM (480 Pa) de bu aralıkta; D'deki SST ile RSM farkını bağıntılar ayırt edemiyor.

**Sonuç:**
- C1 için kalibrasyon: CFD/MM = 504/642 = **0.785**.
- Twin'e giden değer değişmedi: 504–510 Pa.
- MM kalibre edilmiş haliyle köprü olarak kullanılabilir. Faktörün geometriden geometriye taşınıp taşınmadığını ara kademe CFD'si gösterecek: C1'in ab/De² değeri 0.32, ara kademeninki 0.56. Taşınmıyorsa ara kademe CFD'sinin kendi Euler sayısı kullanılır.

**Ara kademe ve C5 için MM ön tahmini** (f 0.005, aynı 0.08 m vorteks bulucu duvarı):

| | ab/De² | Eu_MM | Gövde / vorteks bulucu payı |
|---|---|---|---|
| C4 (= C2 = C3) | 0.559 | 8.66 | 0.31 / 8.35 |
| C5 | 0.555 | 8.69 | 0.32 / 8.38 |

- C5'in Euler sayısı C4'ünkinden %0.4 farklı. MM, C5'in ara kademe CFD'sinden Euler sayısıyla ölçeklenmesini destekliyor.
- Uyarı: C4 ve C5'in girişi (9.44 m) gövdeden (3.46 m) uzun ve koniye iniyor. MM'nin varsayımı girişin gövde içinde kalması. Bu geometride MM'nin mutlak değeri C1'dekinden daha az güvenilir; asıl sayıyı ara kademe CFD'si verecek.

## Farin Yüklemesi (T2, 28 Eylül 2026) — ilk deneme ve riser kararı

**Kurulum:** Seviye 0 mesh (150,578 hücre), URANS SST-CC, Δt 0.02 s, gaz-yalnız çözümden (t = 13.085 s) başlangıç. Farin `inlet_gas` yüzünden:
- 13.89 kg/s (c0 0.78), 542 K, gaz 638 K. Bu, 80/20 riser/siklon ısı paylaşımı varsayımıyla (farin 300 K, gaz 776 K, denge 603 K) seçilmişti.
- Rosin–Rammler 2–300 µm, d̄ 40.9 µm, n 0.904 (90 µm elekte %13, 200 µm elekte %1.5 kalıntı; d50 ≈ 27 µm), 2700 kg/m³, cp 850.
- DRW dağılımı; `wall_dust` escape, diğer duvarlar reflect.

**Sonuç: iki yönlü bağlantı her denemede ıraksadı.**
- Düz DPM: tam debide ve %25 debide, linearize kaynaklar ve 0.5 gevşetmeyle bile. Patlama çatı–giriş köşesinde (z 11.16–11.43, ince prizma hücreleri); konsantrasyon 5–9 kg/m³.
- DDPM: 3.47 kg/s'de 6. adımda (t 13.905 s). "Temperature limited to 1 K" bütün hücrelerde, AMG ıraksaması, kayan nokta hatası.

**Tek yönlü DPM testi (15 adım, 0.3 s):** İzleme temiz — 29,610 parsel, **0 aborted**, 0 escaped. *Degenerate subtet* uyarıları zararsız. Yani çöküş izlemeden değil, iki yönlü bağlantıdan. Farinin dağılımı:
- Kütlenin %55'i duvarda kayıyor; tamamı gövdenin üst kısmında (z 8.5–11.5 m, r ≈ 2.15 m) duvar şeridinde.
- Yerel yük oranı (farin/gaz kütlesi) medyanda 0.64, hacmi 1–5·10⁻⁵ m³ olan duvar prizmalarında **20–107** (10–60 kg/m³). En kötüleri çatı köşesi ve giriş hizasındaki duvar.

Bu şerit fiziksel (Muschelknautz'un şerit modeli de bunu varsayıyor). Sayısal sorun, gaz kütlesinin 100 katı farinin, her adımda bir kez hesaplanan açık kaynaklarla çok küçük prizma hücrelerine yüklenmesi.

**DTU tezinden (Mirzaei 2023, Ek A ve D):**
- Fluent DDPM'in varsayılan gaz–partikül enerji bağlantısı ("Eulerian yaklaşım") **100 µm'den ince partiküllerde enerji dengesini bozuyor** (±%100). Çözüm, 2022R2'de eklenen `/define/models/dpm/interaction/ddpm-energy-coupling-via-source-term? yes`. Bizim d50 27 µm; DDPM çöküşündeki bütün hücrelerde birden 1 K'ye inen sıcaklık bu hatanın izi olabilir.
- Kararlılık: node-based averaging, implicit tracking, Wen–Yu drag, parsel hacmi en küçük hücrenin yarısından küçük, duvar geri sekme 0.8, URF basınç 0.7 / momentum 0.3. Zaman adımı Courant 200–300 (bizim 0.02 s bunun altında).
- Domen **riser + siklon**; farin riser'a bir besleme borusundan verilir, gaz–farin ısı alışverişi büyük ölçüde riser'da olur.

**Karar (kullanıcı):** C1 riser bağlantısıyla birlikte kurulur ([riser_R1.md](riser_R1.md)).
- Riser ve dirsek yuvarlak, Ø2.171 m (yayınlanmış R1 alanının C1 başına yarısı, ~8.7 m/s), dirsek yarıçapı 1.0 D; 1.5 m'lik yuvarlak→dikdörtgen geçişle mevcut 0.86 × 2.16 m kanala bağlanır. Kanal ve siklon doğrulanmış domenle aynı. Kare giriş elendi (1.36 m'lik kenar vorteks bulucuya çarpar).
- Farin riser duvarından giren, yatayla 60° eğimli bir oluktan ("distribution box") ham farin sıcaklığında (300 K) verilir; gaz riser tabanından 776 K'de girer.
- CAD incelemesi (29 Eylül 2026, analizden önce): yatay stub 60° eğimli oluğa döndü (farin duvar şeridi olarak değil, gaz akımına düşerek girsin). Besleme altındaki riser 2.5 → 4.5 m (~2 D) uzadı. Domen ≈ 250.2 m³ oldu ve mesh yeniden kurulacak. Kaz boynu çıkışındaki %26–30 geri akış için CAD değişmedi. Yüklü koşuda geri akış sıcaklığı t_out'a eşitlenir ve enerji dengesi geri akış terimiyle birlikte raporlanır.
- Riser/siklon ısı paylaşımı artık varsayım değil, sonuç. C1'in gaz-yalnız ΔP'si kanal–gövde düzlemi ile çıkış arasında yeniden ölçülür ve 504–510 Pa ile karşılaştırılır.
- Önce DTU ayarlarıyla mevcut C1'de kısa bir DDPM denemesi, çöküşün sebebini riser'dan ayırmak için.

**Riser domeninde DDPM (30 Eylül 2026) — sonuç: terk edildi.** Riser domeninde (191,208 poly hücre) gaz-yalnız referans: C1 statik ΔP **500.8 Pa** (doğrulanmış 503.8'e göre −%0.6); riser'daki düşüş 64.3 Pa, bunun ~59 Pa'sı hızlanma. DDPM'de öğrenilenler:
- İlk iterasyondaki ıraksamanın sebebi Granular ve Packing Limit "Enhanced Numerics" seçenekleriydi (DTU kurulumunda yoklar). İkisi kapatılınca kararlı.
- Oluğun uç yüzünden verilen farinin %99'u **oluğun kapalı ucundaki durgun gazda asılı kaldı**. İnce taneler ~2.5 cm'de duruyor, mm/s ile çöküyor. DDPM oluktaki yoğun granüler kaymayı temsil edemiyor.
- Oluk ağzından riser'a verilen farin yoğun bir **perde** oluşturdu: yerel yük 30–60 kg/kg, etkin yoğunluk ~10 kg/m³. Perde duvar boyunca düşüp gazı aşağı çekti (w +8 → −2 m/s). 6.95 kg/s'de ~1 s sonra kenarlarından ısınarak dönmeye başladı; 13.89 kg/s'de soğuk perde olarak kaldı. Tesiste bunu saçma plakası önler.
- **Fluent'in Rosin–Rammler'i [d_min, d_max] aralığını doğrusal böler:** 2–300 µm ve 10 çapla kütlenin %39'u 2 µm sınıfında toplanıyor. Kütle dilimli bir dosya enjeksiyonu gerekir.
- Rejime varmak 400–500 adım ister, yani 5–8 saat. Tam yükte basınç alanı sorunlu kaldı (dpt testere dişi, p_in 650 → ~150 Pa).

**Karar (kullanıcı, CLAUDE.md madde 9):** yüklü durum CFD ile değil, aşağıdaki gibi analitik olarak hesaplanır. Tek yönlü DPM de gereksiz: yüksek yüklemede sınır yükleme baskın ve iç girdabın kademeli verimi toplam η'yi ancak birkaç puan değiştiriyor.

## Yüklü Durum (Ekim 2026)

**Yöntem:**
- Sıcaklıklar ve enerji dengesi riser'da ısıl denge varsayımından. Farinin ısıl zaman sabiti 0.01–0.08 s, beslemeden siklona varış ~1 s. DDPM'de perdeden kopan taneler de hemen 750+ K'e çıkıyordu.
- ΔP ve η Muschelknautz yöntemiyle (MM), yüklemeyle birlikte. Hoffmann & Stein (2007) Böl. 6'daki denklemler, Svensen ve diğ. 2025'te (arXiv 2504.02886, denk. 77–82) yazıldığı biçimde:
  - giriş daralması α(c₀);
  - yüklü sürtünme f = 0.005·(1 + 3√c₀);
  - v_θ(r);
  - sınır yükleme c₀L = 0.025·(x₅₀/x_med)·(10c₀)^k, c₀ ≥ 0.1 için k = 0.15;
  - kesme çapı x₅₀.
- ΔP terimleri (gövde sürtünmesi + vorteks bulucu) E adımındaki gibi. Yüklü siklon ΔP'si CFD'ye kalibre edilir: ΔP = 504 Pa × MM_yüklü / MM_temiz.
- İç girdabın kademeli verimi 1/(1 + (x₅₀/x)^β), β = 5. Girişte ayrılmayan farinin besleme dağılımına sahip olduğu varsayılıyor; bu bir üst sınır, alt sınır 0.
- Kontrol: aynı betik temiz gaz durumunda E adımını yeniden üretiyor (α 0.622, v_θCS 27.97 m/s, 642.1 Pa).

**Girdiler:**
- Gaz 17.9 kg/s, riser tabanında 776 K. Farin 13.89 kg/s, 300 K; c₀ = 0.776.
- 603 K'de ρ 0.5855 kg/m³, μ 3.03·10⁻⁵ Pa·s. Q = 30.57 m³/s, v_in 16.46 m/s, v_x 6.76 m/s.
- RR d̄ 40.9 µm, n 0.904; x_med 27.3 µm. ρ_p 2700 kg/m³.
- H_CS = 6.91 m: vorteks bulucu ağzından koni yarıçapının R_x'e indiği yere kadar.

| Büyüklük | Temiz gaz (MM) | Yüklü (MM) |
|---|---|---|
| α | 0.622 | 0.795 |
| f | 0.0050 | 0.0182 |
| v_θ duvar / v_θCS | 21.2 / 28.0 m/s | 16.6 / 14.7 m/s |
| Δp gövde + vorteks bulucu | 120 + 522 = 642 Pa | 115 + 202 = 317 Pa |
| x₅₀ | 12.8 µm | 24.4 µm |
| c₀L | – | 0.030 kg/kg |

Yükleme girdabı yarıya indiriyor: duvar sürtünmesi 3.6 kat, girişteki daralma da azalıyor. Bu yüzden ΔP düşüyor ve kesme çapı büyüyor. Yüklü siklonlardaki bu ΔP düşüşü literatürde bilinen bir olgu.

**Sonuç (C1 başına):**

| Büyüklük | Değer |
|---|---|
| Gaz ve farin çıkış sıcaklığı | **602.5 K** (denge) |
| Isı alışverişi | 3.5715 MW (gaz = farin, residual 3·10⁻¹⁶) |
| Siklon statik ΔP | **249 Pa** (gaz-yalnız 504 × 0.494) |
| Riser ΔP | **190 Pa**: gaz 64.3 + farini riser hızına çıkarma 42.4 + kanal hızına çıkarma 61.3 + askıdaki farinin ağırlığı 22.4 (0.454 kg/m³, 5.0 m yükseliş) |
| Toplam, riser tabanı → C1 çıkışı | **439 Pa** (gaz-yalnız 568) |
| η | **%96.1–98.3** (alt: yalnız sınır yükleme; üst: + iç girdap) |
| Egzozla taşınan toz | 0.24–0.55 kg/s |

Taşınan toz da 602.5 K'de çıkar; ayırma enerji dengesini değiştirmez. Varsayımlar: adyabatik duvar, sabit cp, C1'de reaksiyon ve nem yok.

**Duyarlılık:**

| Durum | Siklon ΔP | x₅₀ | η |
|---|---|---|---|
| Temel | 249 Pa | 24.4 µm | %96.1–98.3 |
| f_air 0.0065 | 241 Pa | 28.1 µm | %95.5–97.8 |
| H_CS = 9.28 m (Svensen'in h_i tanımı) | 249 Pa | 21.1 µm | %96.6–98.7 |
| β = 3 | 249 Pa | 24.4 µm | %96.1–98.3 |
| c₀ −%20 | 264 Pa | 23.2 µm | %95.5–98.1 |
| c₀ +%20 | 237 Pa | 25.5 µm | %96.5–98.4 |

**Literatürle karşılaştırma:**
- **η:** üst kademe siklonları için %91–95 tercih edilen aralık (US 10,598,434 B2). Svensen ve diğ.'nin ayarlanmış tesis modeli C1 için %95.1 veriyor. MM'nin alt sınırı (%96.1) bu bandın 1 puan üstünde. Fark beklenen yönde: sınır yükleme bağıntısı yüksek c₀'da iyimser; Svensen de c₀L'ye bir ayar katsayısı f_c koyuyor.
- **ΔP:** üst kademe için tipik 5–20 mbar (500–2000 Pa), aynı patent. Bizim 439 Pa, bandın hemen altında. Sebebi düşük gaz debisi: 17.9 kg/s, 2500 t/d hattında C1 başına ~28 kg/s'ye karşılık geliyor. ΔP ∝ ṁ² olduğundan o debide ≈ 1.07 kPa olur.

**Twin'e giden değerler** (17.9 kg/s gaz, 13.89 kg/s farin):
- çıkış sıcaklığı 602.5 K;
- toplam ΔP 439 Pa (siklon 249 + riser 190);
- η %96 (MM alt sınırı; literatür bandının üst ucuna yakın; kullanıcı kararı, 4 Ekim 2026: twin bu değeri kullanır, literatürün %95'i değil);
- toz kaybı ~0.54 kg/s.

Farklı debilerde ΔP ∝ ṁ_g² ölçeklenir.

**Twin entegrasyonu (4 Ekim 2026):**
- η, `configs/twin_cfg.yaml` → `preheater.c1_separation_efficiency: 0.96` ile Stage 5'e (twin'de C1, index N−1) uygulanır.
- Kaçan toz filtreden beslemeye döner (kullanıcı kararı). C1'den geçen katıya D = (1−η)/η × alt akış eklenir. C2'ye ve kalsinere giden kütle değişmez; twin'e etkisi yalnız ısıl: tozun C1 katı çıkışı ile besleme sıcaklığı arasındaki entalpisi (`state.Q_dust_loss_preheater`), defterde "C1 dust (returned)" satırı.
- İlk koşu (27.78 kg/s besleme): D 1.10 kg/s (iki C1 için; burada C1 başına 0.54), kayıp 0.52 MW ≈ 31 kJ/kg klinker. Bu kaybı twin'in C1 katı çıkış sıcaklığı (855 K) belirliyor; o sıcaklık bu dokümandaki 602.5 K'nin çok üstünde, çünkü twin'in ön ısıtıcı egzozu hâlâ çok sıcak (1264 K). Egzoz düzeldikçe bu kayıp da küçülür.
- ΔP twin'e girmedi: twin'de basınç/fan ağı yok.

### Tesis debisinde (12 Ekim 2026)

> **Not (16 Kasım 2026):** bu bölüm eski yarık geometrisine aittir. Volütlü C1 için yüklü MM (28.76 kg/s): ΔP 495 Pa, η %96.3–98.3 (yukarıda, "Farin Girişi"). Twin hâlâ η 0.97 kullanıyor; yeni alt sınır 0.963. Değerin değişip değişmeyeceği yeni CFD'den sonra karara bağlanacak.

CFD 17.9 kg/s'de (sektör tipik değeri) çözüldü. Tesisin her hattı 2500 t/d'dir ve hattın gazını ikiz C1'ler paylaşır: **C1 başına ~28 kg/s**. Ölçüler aynı kalır; değerler o debiye taşınır. Betik: `C:\Users\engin\c4\mm\c1_plant.py` (repo dışı). Betik, CFD noktasında yukarıdaki sayıları birebir veriyor: 249 Pa, %96.1.
- **Gaz-yalnız ΔP:** CFD'nin Euler sayısı (6.35) × giriş dinamik basıncı. Giriş hızı 25.7 m/s, ΔP **1.23 kPa**. Literatürün üst kademe bandı 0.5–2 kPa.
- **Yüklü durum:** MM, yarık α'sı ile, cyclone_C1.md'deki gibi. Farin kule döngüsünden gelir (C2–C4 η 0.93, C5 η 0.90, kalsinatörde %90 kalsinasyon): hattın C1'lerine 49.9 kg/s, C1 başına c₀ 0.89.

| C1 başına gaz | v_in | Gaz-yalnız ΔP | Yüklü ΔP | x₅₀ | η (alt – üst) |
|---|---|---|---|---|---|
| 24 kg/s | 22.1 m/s | 905 Pa | 412 Pa | 22.7 µm | %97.2–98.7 |
| **28 kg/s** | **25.7 m/s** | **1232 Pa** | **586 Pa** | **20.2 µm** | **%97.1–98.8** |
| 32 kg/s | 29.4 m/s | 1609 Pa | 793 Pa | 18.3 µm | %97.1–98.9 |

- Yüksek hız girdabı güçlendirir, x₅₀ küçülür; c₀ düşse de η'nın alt ucu ~1 puan artar.
- **Twin değeri:** **η %97**, yüklü MM'nin alt ucu; 4 Ekim 2026'daki seçim kuralının aynısı. `configs/twin_cfg.yaml` → `preheater.c1_separation_efficiency`. Hattın egzozuyla giden toz ~1.44 kg/s.

### Tek yönlü DPM kontrolü (4 Ekim 2026)

**Amaç:** MM'nin iç girdap hesabını CFD ile kontrol etmek. Kullanıcı isteğiyle eklendi; iki yönlü bağlaşım kullanılmadı.

**Kurulum:**
- Doğrulanmış gaz-yalnız alan donduruldu (`c1_riser\c1r_dpm1w.cas.h5`, 603 K). Sabit izleme yapıldı; gaz alanı değişmiyor.
- Enjeksiyon dosyası `feed_1389.inj`: 7 boyut sınıfı, oluk ağzında 24 nokta, 13.89 kg/s, 300 K.
- DRW, 10 deneme → 1680 yörünge. Max 20,000 adım, step length factor 5.
- Duvar sınır koşulu: reflect, e_n = e_t = 0.8 (DTU). `dust_outlet` trap, gaz çıkışı ve riser tabanı escape.
- **Mesh'ten sızma:** ilk denemede taneler giriş açıklığının çatı altındaki köşesinde, mesh'in en kötü hücrelerinde, "degenerate subtet" uyarılarıyla domen dışına kaçtı (düz çizgiler). Fluent'in önerdiği iki ayar sorunu giderdi: `high-resolution-tracking/check-subtet-validity? yes` ve `use-quad-face-centroid? yes`.

**Sonuç (temiz gaz, yükleme etkisi yok):**

| Sınıf | Gaz çıkışından kaçan | Toz çıkışı | Takip bitmedi | MM temiz gaz, kaçan (x₅₀ 12.8 µm, β 5) |
|---|---|---|---|---|
| 3.8 µm | %60 | %0 | %40 | %99.8 |
| 7.9 µm | %75 | %0 | %25 | %92 |
| 15.7 µm | %46 | %18 | %36 | %27 |
| 30 µm | %11 | %21 | %68 | %1.4 |
| 53–172 µm | %0 | %0 | %100 | ~%0 |
| Toplam | **%25.0** (3.48 kg/s) | %7.8 | %67.2 | %24.5 |

- **53 µm ve üstü taneler gövdenin üstünde, giriş hizasında, çatının altında dönen bir toz halkasında kalıyor.** Bu, literatürde bilinen çatı altı halkası. Tek yönlü modelde bu taneleri aşağı indiren şey (halkadaki farinin ağırlığı, kayan şerit) yok. Bu taneler duvarda, yani ayrılmış bölgede; "takip bitmedi" kütlesinin büyük kısmı ayrılmış sayılır.
- **İnce tanelerin bir kısmı adım sınırına takıldı:** 3.8 µm'de %40. 100,000 adımlı ilk koşuda (sızıntı vardı) bu oran %9'du ve %91'i kaçmıştı. Yani bu tanelerin çoğu sonunda kaçıyor.
- **Temiz gaz η:**
  - takip edilemeyen bütün taneler ayrılmış sayılırsa %75;
  - takip edilemeyen ince taneler (≤ 15.7 µm) kaçmış sayılırsa %61;
  - en iyi tahmin %71–75.
  - MM'nin temiz gaz tahmini %75.5. Toplamda uyuşuyor.
- **Kademeli verim eğrisi CFD'de MM'ninkinden daha yayvan.** 15.7 µm'de kaçan pay %46 (MM %27), 30 µm'de %11 (MM %1.4). Bu, türbülanslı dağılımın ve vorteks bulucuya kısa devre yapan akışın etkisi. Yüklü η'ye etkisi küçük: iç girdaba giren pay ~%4 ve bant %96–98'de kalıyor.
- **Kalma süresi:** kaçan taneler medyan 4.4 s (%10–90: 3.7–6.5 s), toz çıkışına varanlar medyan 10.1 s (8.2–12.5 s). Gaz-yalnız çözümde gazın siklondaki ortalama kalma süresi 6.6 s.
- **Riser:** bütün boyutlar taşınıyor, riser tabanından geri düşen farin yok (temiz gazda). Farinin aldığı ısı 3.577 MW; analitik değer 3.5715 MW.

**Çatı halkasının sebebi (görselleştirme koşuları, 4 Ekim 2026):**
- **Koşu:** gaz alanı dondurulmuş, parçacıklar zamanda ilerletildi (unsteady izleme, Δt 0.02 s; 0.2 s'lik farin darbesi, 10 s). Video `c1_riser\anim2.mp4`.
- **İri taneler duvarda kalıyor.** 53–172 µm'lik taneler siklona girdikten sonra duvarda (r ≈ 2.15 m), z 8.9–10.3 arasında bir halkada kalıyor; koniye neredeyse hiç inmiyorlar.
- **Sebep gaz alanı.** Gaz-yalnız çözümde, giriş açıklığının altında duvar dibindeki (r 1.95–2.16 m) düşey hız:

  | z | Gaz düşey hızı |
  |---|---|
  | 5.0–7.5 m | −1.2 … −0.5 m/s |
  | 8.0 m | ~0 |
  | 8.5–10.0 m | **+1.3 … +3.7 m/s** |
  | 10.5–11.0 m | −1.9 … −2.1 m/s |

  Duvar boyunca yukarı akan bu tabaka, üstten inen akışla z ≈ 10.2'de karşılaşıyor. İri tanelerin düşme hızı yukarı akıştan küçük (94 µm ~0.4 m/s, 172 µm ~1.4 m/s); gaz onları bu çizgide tutuyor.
- **Sürtünme vekili denendi:** siklon duvarında e_t 0.8 → 0.3, ayrı duvar zonu `…zyon16.1`, 5.7 s.
  - Toz çıkışına inen tane 76'dan 188'e çıktı, ama inenler 15.7 ve 30 µm'liklerdi.
  - Koşu sonunda iri tanelerin %97'si hâlâ halkadaydı.
  - Teğetsel sürtünme dönmeyi keser ama aşağı yönlü bir kuvvet uygulamaz. Bu yüzden halkayı çözmüyor.
- **Gerçek tesiste** 13.89 kg/s farin bu bölgede yoğun bir şerit oluşturur (yerel yük 30+ kg/kg) ve gazın bu zayıf yukarı akışını bastırır. Bu, iki yönlü bir etkidir; tek yönlü modelde temsil edilemez.
- **Sayılara etkisi yok:** halkadaki taneler duvarda, yani ayrılmış sayılıyor. η, ΔP ve sıcaklıklar bu davranıştan bağımsız.

**Karar (kullanıcı, 4 Ekim 2026):** temiz gaz CFD'si ve tek yönlü DPM yalnız referans ve kalibrasyon olarak kalır. Gerçek 13.89 kg/s farin davranışı yüklü MM'den gelir ("Yüklü Durum"). İki yönlü DPM ya da DDPM yapılmaz (CLAUDE.md madde 9). DPM'in kalan işi, birkaç çapın yörüngesiyle ayırma mekanizmasını belgelemek.

**Tek çaplı yörüngeler (4 Ekim 2026):**
- **Koşu:** `c1_riser\c1r_traj.cas.h5`, yukarıdaki sabit izleme kurulumu (donmuş gaz alanı, reflect 0.8, `dust_outlet` trap). 8 çap (5, 10, 15, 20, 30, 50, 100, 170 µm); her çap için oluk ağzındaki aynı 24 noktadan birer iz, DRW 1 deneme, max 20,000 adım. Fluent batch modunda çalıştırıldı. İzler `plot-write-xy-plot` ile dosyaya yazıldı ve dışarıda çizildi. Resim: `c1_riser\traj\trajectories.png` (çap başına `dp005.png` … `dp170.png`).
- **Sonuç (24 izden):**

  | Çap | Egzoz | Toz çıkışı | Bitmeyen | Bitmeyenler nerede |
  |---|---|---|---|---|
  | 5 µm | 17 | 0 | 7 | gövde altı / koni üstü, duvara yakın (z 3–6 m) |
  | 10 µm | 15 | 0 | 9 | koni dibinde dönüyor (z ~1.4 m, r ~0.7 m) |
  | 15 µm | 13 | 2 | 9 | koni dibinde dönüyor |
  | 20 µm | 8 | 6 | 10 | koni dibinde dönüyor |
  | 30 µm | 1 | 10 | 13 | çoğu koni dibinde |
  | 50 µm | 0 | 0 | 24 | çoğu çatı halkasında; birkaçı sarmalla koniye iniyor |
  | 100 µm | 0 | 0 | 24 | çatı halkası (z 9–10.2 m, r 2.15 m) |
  | 170 µm | 0 | 0 | 24 | çatı halkası |

- **Mekanizma:**
  - ≤ 15 µm: taneler duvara tam çıkamıyor. İç girdabın yukarı akışına kapılıp çoğu vorteks bulucudan kaçıyor; kaçış süresi ~3–6 s.
  - 15–30 µm: kesme çapı bölgesi (MM temiz gaz x₅₀ 12.8 µm; yüklü 24.4 µm). Duvara çıkanlar sarmal çizerek koniye iniyor. Koni dibinde girdabın ucunda uzun süre dönüyorlar; bir kısmı toz çıkışına düşüyor, bir kısmı adım sınırına takılıyor. Kaçış ile ayrılma arasındaki seçim burada yapılıyor.
  - ≥ 50 µm: merkezkaç kuvveti taneleri girer girmez duvara atıyor. Duvar dibindeki +1.3…+3.7 m/s'lik yukarı akış bunların düşme hızından büyük, o yüzden çatı halkasında kalıyorlar (bkz. "Çatı halkasının sebebi"). 50 µm sınırda: birkaçı halkadan kopup koniye iniyor.
- **Riser:** her çap riser'da taşınıyor, riser tabanına düşen yok.
- **Yüklü durumla farkı:** bu izler temiz gazın güçlü girdabında (v_θCS 28 m/s) elde edildi. Yükte girdap yarıya iner (14.7 m/s), kesme çapı 12.8 → 24.4 µm'ye büyür. Farinin ~%96'sı ise sınır yükleme mekanizmasıyla girişte duvara çöker ve şerit hâlinde koniye kayar. Bu izler o şeridi göstermez; yalnız tek tek tanelerin girdaptaki yolunu gösterir.

## Derived Properties

Ekipman hacmi (her biri), toplam yükseklik ve ıslak alan: Geometrik Ölçüler'deki tabloda. Kalma süresi, holdup ve benzeri fiziksel hesaplar ekipman hacmini kullanır.

Koni duvarının yatayla açısı: 67.1° — farinin 40°'lik yığılma açısının üstünde

Giriş kesit alanı: 2.58 m² (volüt kanalı 0.86 × 3.00; eski yarık 1.858)

Giriş hidrolik çapı: 1.34 m (eski yarık 1.23)

Vorteks bulucu kesiti: 4.524 m²

Toz çıkışı kesiti: 0.126 m²

Toz çıkışı çapının gözden geçirilmesi (16 Kasım 2026, kullanıcı onayı; ölçü değişmedi):
- Oran FLS referansınınki: Svensen ve diğ. 2025 Tablo 8, Cy1 D_d/D = 0.64/6.90 = 0.093. Farin akısı referanstan düşük; kıyas [meal_pipe_C1.md](meal_pipe_C1.md)'de.
- Girdap ucu, Alexander'ın doğal girdap boyuyla: L/D = 2.3·(D_x/D)·(D²/(a·b))^(1/3) = 2.3 × 0.556 × 2.157 = 2.76, L ≈ 11.9 m. Vorteks bulucu ağzından toz çıkışına 9.28 m var; girdap toz çıkışına ulaşır, koni duvarına tutunmaz (aşınma ve yeniden kalkış riski yok). Giriş a = 3.0 m'ye büyütülse L ≈ 10.7 m, yine yeterli. (Bu hesap eski yarıkla yapıldı.) Kabul edilen volütte (a 3.00, S 3.45) vorteks bulucu ağzından toz çıkışına 7.99 m var, L ≈ 10.7 m: girdap yine toz çıkışına ulaşır.

Volüt kanalının iç duvarı (r 2.21 m) ile vorteks bulucunun dış duvarı (r 1.28 m) arasında 0.93 m var; jet gövdenin dışından girer. Eski yarıkta bu pay 0.020 m'ydi.

C1 Y ayrımı ikiz katıda (`C1_twin`, [riser_R1.md](riser_R1.md)). Volüt 16 Kasım 2026'dan beri modelde.
