# Tesis topolojisi (2D şema)

Makro: [`geometry/macros/plant_topology_2d.bas`](macros/plant_topology_2d.bas). Referans hat: 2500 t/d.

**CFD girdisi değildir.** Bu, tesisin topolojisini göstermek için çizilmiş gerçek ölçekli bir 2D şemadır: hangi ekipman var, nerede duruyor, gaz, farin ve hava hangi yoldan akıyor. `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır.

Önceki 3D topoloji modeli (`plant_topology.bas`, tek hatlı, çok gövdeli) kaldırıldı. Yerine bu 2D şema geldi; 2D daha okunur ve çakışma kısıtı taşımaz (kullanıcı kararı, 5 Ekim 2026).

## Ne çizilir

Bir SolidWorks **çizim sayfası**: A1 yatay (841 × 594 mm), ölçek **1:300**. Model koordinatları (x yatay, z kot, metre) sayfaya `P(x, z) = (X0 + x/300, Y0 + z/300)` ile yerleşir. Ölçek önce 1:200, sonra 1:250 idi. Hatlar tam 2500 ölçüsüne çıkınca kule ~125 m oldu ve A1'e 1:250'de sığmadığı için 1:300'e geçildi (12 Ekim 2026). Stub yarıya inince kule 117.4 m oldu; ölçek 1:300'de kaldı.

İlk sürüm bir parça sketch'iydi. Renkler orada görünmedi, çünkü sketch'in durum rengi özel rengi bastırıyordu. Etiketler 1 m yükseklikte okunmuyordu, her köşede de nokta yığını vardı. Çizim belgesine bu yüzden geçildi (kullanıcı kararı, 5 Ekim 2026).

- **Ekipman, gerçek kesit dış hatlarıyla:** siklonlar (toz çıkışı, koni, gövde, tavan, gaz çıkış stub'ı), kalsinatör (boğaz, koni, gövde), fırın giriş odası, fırın, soğutucu, fırın başlığı.
- **Akışın geçtiği duvarlar açıktır:** fırının iki ucu (giriş odasına ve başlığa açılır), kalsinatör boğazı (giriş odasının tavanı), kaz boynu kollarının kalsinatör tavanındaki ağızları, tersiyer hava kanalının başlık tavanındaki ve kalsinatör duvarındaki ağızları, başlığın altı (soğutucuya açık), her siklonun toz çıkışı, gaz çıkış stub'ının tepesi ve girişinin geldiği taraftaki gövde duvarı. R1 C2'nin çıkış borusundan bir daraltıcıyla dik devam eder; R2–R4, C3–C5'in çıkış borusunun kendisidir. Açıklığın yanında kalan, `MIN_SEG`'ten kısa duvar parçası çizilmez. Bütün siklonlarda giriş tavandan aşağı iner; gövde duvarı yalnız kanalın yüksekliği boyunca açıktır, altında kapalı devam eder. Tek çizgili yollar (farin, egzoz, primer hava) duvarda biter.
- **Ana kanallar gerçek çapında, çift çizgiyle:** R1–R4, kaz boynu ve tersiyer hava kanalı. Kenarlar eksenin w/2 iki yanındadır; köşeler kenarların kesişiminde birleşir. Kaz boynunun Y dirsekleri ve C1'lerin iki dirseği (kol ve gaz çıkışı, CFD katısındaki gibi) yaydır; C2–C5'in çıkış dirsekleri (R2–R4) de yaydır; R1'in daraltıcısı, Y'si ve kaz boynu inişinin dönüşü 45°'lik düz parçalardır.
- **Diğer yollar tek çizgiyle, eksen boyunca:** farin hatları, C1 egzozu, ikincil hava, fırın → kalsinatör gazı.
- **Akış okları:** her yolun en uzun parçasının ortasında, akış yönünde. Çizimden çıkan ya da yalnızca bir akımı belirten yollarda ("to ID fan", "to cooler vent", "to clinker transport", primer hava, tersiyer hava oku) ok yolun ucundadır; okun ötesinde çizgi kalmaz.
- **Farin hatları tam, arkadan geçtiği yerde kırık:** her farin hattı toz çıkışından hedefine tam çizilir (kullanıcı kararı 14 Ekim 2026, uç gösteriminden geri dönüldü). Bir hat bir siklonun, R1'in (daraltıcısıyla), R2'nin dirseğinin ya da TA kanalının arkasından geçiyorsa, o dış hattın içinde ve iki yanında `CROSS_GAP` kadar çizilmez (`PathM`; bunlar kapalı dış hat olarak kaydedilir: `BodyM`, `CycBody`, `R1Body`, `OutletBody`). Lejantta bir örneği var.
- **Şematik not:** lejantta, giriş odasının ölçüsünün kaynaksız olduğu ve farin borularının 2D izdüşümü olduğu (C4 ve C5 boruları ve oda rampası 3D yerleşimde daha diktir) yazılıdır.
- **Etiketler:** not olarak, kâğıtta 3.5 mm yükseklikte. Siklon adları gövdenin içinde (oradan hiçbir yol geçmez), riser adları kanalın içinde. Sayılar yerel ayardan bağımsız olarak noktalı ve sabit ondalıklı yazılır ("2.440").
- **Kot cetveli:** solda, çerçevenin içinde, 0'dan 100 m'ye; her 10 m'de bir çentik ve kot. Zemin çizgisi cetvelden başlar.
- **Lejant ve notlar:** renkler, ok, çift ve tek çizginin anlamı, kanalın arkasından geçerken kırılan farin hattı; altında numaralı notlar (birimler, hat başına ölçek, şematik/2D izdüşüm, CFD girdisi olmadığı) ve 10 m'lik ölçek çubuğu.
- **Çerçeve (ISO 5457):** A1, sol 20 mm, diğer kenarlar 10 mm; 12 × 8 bölge, üst ve altta 1–12, yanlarda A–H.
- **Antet (ISO 7200):** 180 mm, sağ altta. Belge türü, başlık ve ek başlık, ölçek, birim, tarih, dil, sayfa, durum, teknik referans, kaynak. Çizen, onaylayan, sorumlu birim, çizim numarası ve revizyon alanları boş bırakılır (kullanıcı kararı); elle doldurulur.
- **Revizyon tablosu:** antetin üstünde, Rev / Description / Date / By başlığı ve iki boş satır.
- **Ekipman etiketleri ve listesi:** siklonlar (C1–C5, L/R) ve riser'lar (R1–R4) adlarıyla; diğerleri etiketle: ILC kalsinatör, GN kaz boynu, TAD tersiyer hava kanalı, KIC giriş odası, KILN fırın, HOOD başlık, COOL soğutucu, FEED ham farin girişi (R1'e giren kısa ok). Sağ sütundaki ekipman listesi her etiketin adını, adedini (iki hat birlikte), ölçüsünü ve dayanağını (CFD, yayınlanmış, türetilmiş, şematik) verir; ölçüler çizimin kullandığı sabitlerden yazılır.
- **Kot işaretleri:** sağ hattın sağında (x = 50) her kademenin toz çıkışı, kalsinatör tavanı ve kule tepesi; giriş odasının solunda fırın ekseni. Üçgen sembol, seviye çizgisi ve "+40.31 C4 dust outlet" biçiminde yazı.
- **Grid ve ölçüler:** kulenin üstünde beş kolon ekseni (1 dış L, 2 iç L, 3 kalsinatör, 4 iç R, 5 dış R) balonlarıyla; aralarındaki mesafeler ve toplam, eğik çizgi uçlu ölçülerle (kolon konumları yerleşim tablosunda).
- **Eksen çizgileri (ISO 128 noktalı çizgi):** her siklonun ekseni, fırın ekseni ve kalsinatörün tavan üstündeki ekseni (tavanın altında fırın gazı eksen üstünden gider).

| Katman | Renk | Kalınlık | İçerik |
|---|---|---|---|
| EKIPMAN | siyah | normal | ekipman dış hatları |
| GAZ | kırmızı (210, 0, 0) | ince | sıcak akımlar: gaz kanalları ve yolları, sekonder ve tersiyer hava, okları |
| FARIN | koyu sarı (200, 150, 0) | normal | farin hatları, okları. İnce kalınlıkta ekranda griye kaçıyordu |
| HAVA | mavi (30, 90, 220) | ince | soğuk hava: primer hava oku |
| YAZI | siyah | ince | zemin çizgisi, kot cetveli, lejant, tabloların iç çizgileri, bölge işaretleri |
| CERCEVE | siyah | kalın 2 | çerçeve, antet, revizyon tablosu ve ekipman listesinin dış çizgileri |
| EKSEN | siyah, noktalı eksen çizgisi | ince | eksen ve grid çizgileri |
| OLCU | siyah | ince | ölçüler, kot işaretleri, grid balonları |
| GIZLI | siyah, kesikli (gizli kenar) | ince | gövdenin içindeki vorteks bulucular (C1–C5, CFD'deki daldırmayla) |

İlk sürümde açık turuncu ve normal kalınlıktaki çizgiler ekranda griye kaçıyordu; PDF'te renkler zaten doğruydu. Renk koyulaştırıldı, yol katmanları kalınlaştırıldı. Gaz kırmızıya geçtikten sonra çizim uzaktan kalın göründüğü için ekipman normal, yol katmanları ince kalınlığa indirildi.

Not ve sayfa ayarı (şablon çerçevesinin kaldırılması) çağrıları başarısız olursa çizim durmaz; log'a bir uyarı düşer.

## Tesis: iki özdeş 2500 t/d hattı, 12 siklon

Görünüm gerçek bir tesisin DCS ekranından alınmıştır: kalsinatör ortada, iki hat iki yanda, fırın ve soğutucu altta sağda.

- **Siklonlar:** her hatta C5, C4, C3, C2 ve ikiz C1; toplam 12.
- **Kalsinatör:** bir ILC. Tepesindeki Y kaz boynu iki hattın C5'lerini besler.
- **Fırın, soğutucu, başlık ve tersiyer hava kanalı:** birer tane.

**Ölçek kuralı** (kullanıcı kararı, 12 Ekim 2026): her hat tek başına bir 2500 t/d hattıdır, iki hat birlikte **5000 t/d**. Hattın siklonları CFD'si çözülen ölçülerdedir. R1 yayınlanmış 2500 ölçüsündedir; R2–R4 alttaki siklonun CFD çıkış borusudur (kullanıcı kararı, 14 Ekim 2026). İkinci hat birincinin kopyasıdır; ayrı CFD gerekmez. Bu kural 5 Ekim 2026'daki "her hat gazın yarısını taşır, ölçüler × 1/√2" kuralının yerini aldı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) equipment -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ekipman | Ölçü [m] | Kaynak |
|---|---|---|
| C1 (hat başına ikiz) | D 4.32, gövde 6.79 | cyclone_C1.md (CFD) |
| C2 = C3 = C4 | D 6.30, gövde 6.30 (h = D) | cyclone_C4.md (CFD) |
| C5 | D 6.50, gövde 6.50 (CFD C4 × 1.0317) | cyclone_C5.md |
| R1 (hat başına) | Ø3.150 | C2'nin dik çıkış borusu, D_x = D/2 (riser_R1.md) |
| R2 / R3 / R4 (hat başına) | Ø3.150 / Ø3.150 / Ø3.250 | C3 / C4 / C5'in dik çıkış borusu, 45° ile üst siklona (riser_R2–R4.md) |
| Kalsinatör | Ø6.7404, 30.0 m (koni dahil), boğaz Ø3.130, koni 65° | calciner.md (PF5000) |
| Kaz boynu | üç düz parçalı boyun (45°/0°/45°), Ø4.950, aşağıda 2 kol × Ø3.50, her kol C5 girişine iner | gooseneck.md |
| Tersiyer hava kanalı | Ø2.4393 | calciner.md |
| Fırın | Ø4.8 × 60 m, %3 eğim | kiln.md (PF5000) |
| Soğutucu | ızgara 119.6 m² = 4 × 29.90 m, gövde 3 m | cooler.md (PF5000, FLS) |
<!-- END GENERATED -->

Kalsinatör, Y kaz boynu, TAD, fırın ve soğutucu 5000 t/d'nindir: PF5000'den, ya da onun ölçülerinden türetilmiş ([calciner.md](calciner/calciner.md), [kiln.md](kiln/kiln.md), [cooler.md](cooler/cooler.md); 12 Ekim 2026). Giriş odası ve başlığın ölçüsü bir hız kontrolüyle seçilmiş model değeridir (Estimated), yerleşimde fırının çevresinde bir paydır. Twin 5000 t/d beslemesiyle çalışır; hangi ekipmanı hangi akış hacmiyle hesapladığı [fluid_volumes.md](fluid_volumes.md)'dedir.

**Tek kaynak** (kullanıcı kararı, 13–14 Ekim 2026). Her ana ölçü yalnız `geometry/plant_geometry.yaml`'da, kaynağıyla (yayınlanmış, FLS oranı, literatür, CFD kararı, modelleme, şematik) bir kez yazılıdır. Türetilen her şey (hacim, alan, kot, boru boyu) `geometry/plant_geometry.py`'dedir; bu çizimin `Derive`'ındaki yerleşim, R1–R4 ve kaz boynu da orada Python'a taşındı. Kopyalar üretilir:
- `tools/gen_geometry.py`, `cyclone.bas`, `calciner.bas` ve `plant_topology_2d.bas`'ın başındaki `BEGIN GENERATED … END GENERATED` Const bloklarını ve ekipman dokümanlarındaki tabloları yazar. Bloklar elle düzenlenmez.
- Twin geometriyi `main.load_cfg` ile oradan alır; `configs/twin_cfg.yaml` geometri yazmaz ([fluid_volumes.md](fluid_volumes.md)).
- Bir ölçüyü değiştirmek: yaml → `python3 tools/gen_geometry.py` → makroyu SolidWorks'te yeniden çalıştır. Değişen ölçü bir CFD domeninin içindeyse önce CFD yeniden çözülür (aşağıda).
- `tests/test_geometry_single_source.py` blokların güncel olduğunu; `tests/test_plant_geometry.py` Python yerleşiminin son build log'unun kotlarıyla aynı olduğunu denetler.

## CFD domenleri ve serbest bölge

Çizim CFD çözümünü bozmadan geliştirilir (kullanıcı kararı, 14 Ekim 2026). Her CFD domeni çizimde donmuş bir bloktur: giriş ve çıkış yüzlerinin arasındaki hiçbir ölçü yalnız çizimde değişmez. Değişecekse önce `cyclone.bas` değişir, CFD yeniden çözülür, sonra çizim. Yüzlerin dışı serbesttir.

<!-- BEGIN GENERATED (tools/gen_geometry.py) cfd -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Blok | Domen (donmuş) | Giriş yüzü | Çıkış yüzü |
|---|---|---|---|
| C1 (×4) | gövde, VF 3.45, Ø2.227 kol, 90° R 2.227 dirsek, 1.5 m geçiş, 0° kanal, 0.6 m oluk; 2.70 m çıkış borusu, R 3.24 180° dirsek, 2.70 m iniş | kolun tabanı, toz çıkışının 0.213 m üstü | inişin ucu, çatı kotunda, eksenden 6.48 m |
| C2–C4 (×6) | Ø3.15 dik riser 3.15 m, 45° eğik kanal, 2.00 m yatay kanal, volüt, gövde, VF 3.900, 5.355 m (1.7·VD) dik çıkış borusu | riser parçasının tabanı, gövde ekseninden 6.803 m, dönüşün 3.15 m altı | çıkış borusunun ucu, eksende, çatının 5.355 m üstünde |
| C5 (×2) | C2–C4'ün 1.0317 katı (CFD'si ayrıca çözülmez) | riser parçasının tabanı, eksenden 7.019 m | çıkış borusunun ucu, eksende, çatının 5.525 m üstünde |
<!-- END GENERATED -->

**Serbest:**
- R1'in daraltıcısı ve Y'si, yani C1 kol tabanının altı.
- Çıkış yüzünden sonraki bacak ve giriş yüzüne kadar olan kanal: uzunluğu, 4.63 → 3.40 daralması.
- Kolon aralıkları (`ZIG_DX`, `R1_BRANCH_HALF`, `GN_TO_C5_GAP`).
- Kalsinatör, kaz boynu, TA, fırın, soğutucu yerleşimi.
- Farin hatlarının gösterimi, etiketler, tablolar.

**Kısıtlar:**
- Gaz kanalı bir çıkış yüzünden bir giriş yüzüne kıvrımsız gider. Kademeler arası yükseklik bu yüzden donmuştur: 7.871 + 4.63 + 2.315 m. Kule ancak CFD değişirse uzar ya da kısalır.
- Daralma ve geçişler yalnız iki yüzün arasındadır.

**Farin girişi:** C1–C3'ün farini R2–R4'e, yani C3–C5'in CFD çıkış borusuna, çatının 1.5 m üstünden girer; bu domenin içidir. CFD gaz-only olduğu ve farin yükü analitik hesaplandığı için çözümü bozmaz. İleride yüklü (DDPM) bir CFD yapılırsa giriş yeri domenin içinde modellenmelidir.

**Kilit:**
- `tests/test_plant_topology_cfd_lock.py` iki makroyu metin olarak okur. Const'lar artık aynı kaynaktan üretildiği için bu ikinci bir güvencedir. Çizimdeki her domen ölçüsünün `cyclone.bas`'taki `SelectCyclone` değerlerine 1 mm içinde eşit olduğunu doğrular; C5 için ayrıca C4 × 1.0317 olduğunu. Biri öbürü olmadan değişirse test hangi ölçünün kaydığını yazarak düşer (`python3 -m unittest tests.test_plant_topology_cfd_lock`).
- Makronun ön kontrolleri yüzleri korur: R4–R2'nin daralması alttaki siklonun çıkış yüzünden sonra başlar ve üsttekinin giriş yüzünün dışında biter; R1'in daraltıcısı C2'nin CFD çıkış borusunun ucunda başlar (C4'ün CFD dirseği C2'de yoktur); kaz boynu C5'in giriş yüzünün dışında kalır. R1'in Y'si C1 kol tabanının altında kalır.
- Çizimdeki çıkış borusu 5.79 değil, CFD'nin tam değeri 1.25 × 4.63 = 5.7875 m'ydi; kilit testi bu 2.5 mm'lik farkı yakaladı.
- **C4 / C5 çıkış borusu 1.25·VD'den 1.70·VD'ye (5.79 → 7.87 m; kullanıcı kararı 14 Ekim 2026).** 1.25'te C2 ve C3 altlarındaki CFD dirseğinin yalnız 0.9 m üstündeydi; farin hatları dirseğe yapışmadan inemiyordu. Bu donmuş bir bloktur, iş akışına göre değişti: önce çizim denendi, sonra `cyclone.bas`'ta `OUTLET_EXT_OVER_VORTEX_D` siklon başına oldu (C1 1.25, C4 ve C5 1.70), kilit testi ikisini eşitler. C4 CFD'si bu domende yeniden çözüldü (14 Ekim 2026): statik ΔP 522.8 Pa, Eu 11.54 (1.25'li domende 515.5 Pa, 11.38; +%1.4); bkz. [cyclone_C4.md](preheater/cyclone_C4.md). Kule 112.02'den 120.41 m'ye uzadı.

**İş akışı:**
1. Serbest bölgede bir değişiklik: Python prototipi → makro → kilit testi ve ön kontroller → SolidWorks → log sayıları bu dokümana → commit.
2. Donmuş bir bloğa dokunan değişiklik: önce `cyclone.bas`, CFD yeniden çözülür, sonra çizim. Kilit testi iki tarafı eşit tutar.

## Şematik parametreler (kaynaksız; yalnız yerleşim için)

İki satır ("donmuş (CFD)") CFD domenlerinin ölçüleridir ve kilit testine bağlıdır; diğer bütün satırlar serbest bölgededir. Değerler tablonun altındaki üretilen listede. Makrodaki üretilen bloktan gelenlerin (CFD satırları, `STAGE_GAP`, `ZIG_DX`, `R1_*`, `GN_*`, `C5_OVER_TA`, `KILN_AXIS_Z`, `CHAMBER_MARGIN`, `COOLER_*`) değeri `plant_geometry.yaml`'da değiştirilir; diğerleri yalnız çizimin kendi Const'larıdır.

| Parametre | Ne belirler |
|---|---|
| **donmuş (CFD):** `C4_VF_S`, `C4_OUT_RISE`, `C4_OUT_R`, `C4_OUT_RUN`, `C4_IN_H`, `C4_IN_W`, `C4_TONGUE`, `C4_IN_L`, `C1_VF_S` | C2–C4 C4'ün CFD domeninin aynısı ([cyclone_C4.md](preheater/cyclone_C4.md), `cyclone.bas`; ölçüler yukarıdaki CFD domenleri tablosunda): vorteks bulucu çatıdan aşağı (kesikli); gaz çıkış borusu çatının üstüne çıkar (1.70·VD; 14 Ekim 2026'ya kadar 1.25·VD), 90°'lik dirsek (duvarları yay) ve yatay bacak; giriş bir volüt: düz kanal ve gövdeden dil kadar dışarıda başlayan yarım tur Arşimet sarmalı. Kesitte volüt çatının altında bir bant olarak görünür; sarmal riserın karşı tarafında gövdeden ~1.5 m taşar. Çıkışın yatay yönü CFD'de riserın ters tarafınadır; çizimde bir sonraki siklona döner (siklonun çıkışını kendi ekseni etrafında döndürmek; akış aynı, kullanıcı kararı 13 Ekim 2026). C1'in vorteks bulucusu da çatıdan aşağı. C5 bunların hepsinin 6.50/6.30 ile büyütülmüş kopyasıdır (`Kc`). Volütü kaz boynunun ters tarafındadır (kullanıcı kararı 14 Ekim 2026) |
| `STAGE_GAP` | C1'in toz çıkışının C2'nin stub'ının en az bu kadar üstünde olması. R1 C2'nin ekseninde düz yükseldiğinden (17 Kasım 2026) ikiz C1'ler C2'nin üstündedir ve iki farin borusu iç kolondaki R2'nin dik kısmına geri iner (60°, yakın C1'inki 50° ile katılır): buna en az 9.41 m gerekir, 9.5 alındı. Önce 4.0'dı; R1'in Y'si C1'i zaten daha yukarı koyuyordu. C2–C4'ün kotu artık bu paydan değil, alttaki kademenin CFD çıkışından gelir: her siklonun çatısı, alttakinin CFD dirseğinin üstü hizasındadır. 14 Ekim 2026'ya kadar C3 ve C2 bu kadar dirseğin üstündeydi; bu, CFD borusuyla dirsek arasına 4.87 m düz boru sokuyordu (CFD domeni bozuluyordu), kaldırıldı ve kule 14.6 m kısaldı (kullanıcı kararı) |
| `ZIG_DX` | Hattın dış kolonunun (C4, C2) iç kolonundan (C5, C3) uzaklığı. Yatay bacağın yalnız ilk 4.63 m'si (C5'te 4.78) CFD domenidir, üstteki siklonun 3.0 m'lik giriş kanalı gövdenin içinde kalır; aradaki bacak serbesttir. Alt sınır: çıkış yüzü + 0.5 m + daralma + gövde yarıçapı, R4 için 14.6 m; ön kontrol zorlar. 20 m idi (farin borularını riserların yanından geçirmek için); farin uçlarla gösterilince kule kare gibi durduğu için 15 m'ye indi (kullanıcı kararı 14 Ekim 2026). 11 m'den 20'ye çıkmıştı |
| **donmuş (CFD):** `C1_RISER_X` … `C1_OUT_R` | Her C1, kendi CFD domeniyle aynı ([cyclone_C1.md](preheater/cyclone_C1.md), [riser_R1.md](preheater/riser_R1.md)); yükseklikler toz çıkışından: riser kolu (R1'in alanının yarısı) domen tabanından dirseğine dik; dirsek (CFD'deki gibi yuvarlak: duvarları eş merkezli iki yay); geçiş ve aşağı eğimli giriş kanalı gövdeye; kare kesitli, 60° eğimli farin oluğu kol duvarından dışarı çıkar; gaz çıkışı çatının üstünde dik boru, kolun ters tarafına 180° dirsek (yuvarlak, iki yay) ve aşağı inen bacak |
| `R1_RED_DEG`, `R1_RED_L` | R1, C2'nin çıkış borusundan C2'nin ekseninde dik devam eder (kullanıcı kararı 17 Kasım 2026): Ø4.63 → Ø3.07 konik daraltıcı, yarım açı 45° (çizimin 45°'lik parçaları), boy 0.78 m; daralma kaybı ~3 Pa. Önceki `R1_LEG_ON` (0.5 m) C2'nin CFD bacağını R1'in dirseğine uzatıyordu; o düzende R1 C2'den 11.3 m kalsinatöre doğruydu |
| `C1_TWIN_GAP` (→ `C1_TWIN_S`, `R1_BRANCH_HALF`) | İkiz C1 (kullanıcı kararı 13 Kas 2026): ayna simetrik çift, her C1 kendi CFD domeniyle aynı ama ekseni etrafında 90° döndürülmüş; kol, dirsek, giriş kanalı, farin oluğu ve çıkış dirseği derinlik yönünde (bu ön görünüşte uçtan görünür, akış ⊗ ile). Giriş kanalları birbirine bakar, ortak R1 simetri düzleminde önde yükselir. `C1_TWIN_GAP` iki kolun cidarları arası (model); C1 eksenleri arası ve Y'nin kol yarı aralığı ondan türetilir. Önceden kollar ön görünüş düzlemindeydi ve C1'ler R1'den 9.593 m uzaktaydı |
| `GN_TO_C5_GAP` | Kaz boynu inişi ile C5 gövdesi arasındaki boşluk. İniş, C5'in giriş kotunda bu boşluğu yatay geçerek gövdeye girer |
| `GN_BEND_LEG` | Kaz boynu inişinin C5'e dönerken 45° parçasının yatay boyu, kol çapı cinsinden. Kolla C5 gövdesi arasında 2.75 m olduğu için riserlardaki 1.0 sığmıyor; ön kontrol, ardından en az yarım kol yarıçapı yatay giriş kalmasını zorlar |
| `TA_BEND_R_OVER_D` | Tersiyer hava kanalının başlıktan kalsinatöre dönüşü: kaz boynundaki gibi geniş bir dirsek, eksende R 3.66 m, duvarları iki yay (kullanıcı kararı 14 Ekim 2026; önceden keskin köşeydi). Ön kontrol, dirseğin başlığın üstüne sığmasını ve tersiyer hava okunun dirsekten önce bitmesini zorlar |
| `C5_OVER_TA` | C5'lerin toz çıkışının tersiyer hava kanalının üstünden en az bu kadar yukarıda olması. Tam boy C5 (gövde + koni 14 m) kaz boynu kolunun bittiği kottan asılınca kanala iniyordu; C5 bu kadar yukarıda durur, kol daha yukarıda biter |
| `MEAL_ENTRY_UP` | Farinin riser'a, ayağının bu kadar üstünde girdiği yer: R2–R4'te çatının üstü, yani CFD çıkış borusunun içine (7.87 m'lik borunun alt kısmı) |
| `MEAL_SIDE_L` | Riser'a giren farin hattının duvarın yanında indiği dik hattın duvardan uzaklığı; hat buradan 60° ile duvara girer |
| `MEAL_DROP` | C1–C3'ün farininin toz çıkışından dik düştüğü boy; her hat siklondan önce düz çıkar, sonra 60° ile döner (kullanıcı kararı 14 Ekim 2026) |
| `MEAL_OVER_GAP` | C2 ve C3'ün farini düz inişinden sonra 60° ile altındaki CFD çıkış dirseğinin üstünden dışarı çıkar; makro, eğimli parçanın dirseğin dış duvarına (tam daire, güvenli tarafta) bundan fazla yaklaşmasına izin vermez. 1.70·VD ile C2 / C3 dirseğin 2.9 m üstündedir, açıklık 0.40 / 0.41 m. 1.25·VD'de 0.9 m'ydi; düz iniş ancak 0.5 m, eğim 40° olabiliyordu |
| `MEAL_JOIN_DEG` | Yakın C1'in farininin, düz inişinden sonra uzak C1'inkine katılırken eğimi. 17 Kasım 2026'dan beri iki C1 farini de R2'nin dirseğinin arkasından geçer (C1'ler C2/R2 düzleminin 6.7 m arkasında; aynı düzlemde temizlemek C1'leri 6 m yükseltirdi, kullanıcı kararı); önce dirsekten 5.5 m açıktı. 60°'de uzak C1'in hattına R2'ye döndüğü yerin altında varırdı |
| `C4_MEAL_DROP` / `C5_MEAL_DROP` | C4 ve C5 farininin toz çıkışından dik düştüğü boy; ardından 1 m'lik (`MEAL_BEND`) bir dönüş parçası ve hedefe düz hat. C5'inki 1.0 m'den uzun olamaz: düz iniş TA kanalının 0.3 m üstünde bitmeli (ön kontrol). Bu düz hatlar farinin aktığından yatıktır (C4 ~16°, C5 ~34°): 2D izdüşümdür, 3D'de borular diktir |
| `CROSS_GAP` | Farin hattının arkasından geçtiği dış hattın iki yanında bırakılan boşluk |
| `ID_FAN_L` | Her C1 çıkışının inen bacağından aşağı "to ID fan" okunun boyu |
| `RM_L` | Ham farin okunun her oluğun ucundan dışarı uzadığı boy; ok başı diğerlerinin yarısı (2 mm) |
| `KILN_AXIS_Z` | Fırın giriş ekseninin kotu |
| `CHAMBER_MARGIN` | Giriş odası ve başlık: fırının çevresinde bu payla bir kare. Model değeri (hız kontrolü); [kiln_inlet_chamber.md](kiln/kiln_inlet_chamber.md)'de yayınlanmış ölçü yok |
| `COOLER_W` / `COOLER_H` | Izgara genişliği ve gövde yüksekliği, FLS referans soğutucusunun (boy alandan çıkar: 29.9 m). Çizimde gövde 14 Ekim 2026'ya kadar 4.0 m'ydi; [cooler.md](cooler/cooler.md)'nin 3.0'ı tek kaynakta kaldı |
| `COOLER_DROP` | Soğutucunun tepesinin, deşarjdaki fırın kabuğunun altında kaldığı mesafe |
| `MEAL_INTO_CHAMBER` | C5 farininin giriş odası tavanına, odanın yan yüzünden bu kadar içeride indiği yer |
| `KILN_FLOW_OFF` | Fırın içindeki gaz ve malzeme çizgilerinin fırın ekseninden dik uzaklığı: gaz üstte, malzeme altta. Fırın kabuğunun (±2.4 m) içinde kalmalı; ön kontrol bunu zorlar |
| `PRIMARY_AIR_L` | Primer havayı yalnızca belirten kısa okun boyu; ok başlığın ön duvarında biter |
| `SEC_AIR_DX` | Sekonder havanın soğutucudan, fırının ucundan bu kadar içeride yükseldiği yer |
| `CLINKER_OUT_Z` | Klinkerin soğutucunun ucundan indiği klinker taşımanın zeminin altındaki derinliği |
| `VENT_IN` | Fazla soğutucu havasının soğutucunun ucundan bu kadar içeride, tavanından çıkması |
| `VENT_UP` | Vent okunun soğutucunun tavanının üstünde çizildiği boy |
| `CLINKER_ON_GRATE` | Klinker çizgisinin soğutucu tabanının üstündeki yüksekliği |
| `TA_ARROW_LONG` | Tersiyer hava okunun boyu: soğutucu ortasından başlığın tavanına olan yüksekliğin bu katı. Ok soğutucu ortasından (z 3.2) başlar ve kanalın içine, z 12.4'e kadar uzanır; ok ucu orada, çizgi okun ötesine geçmez. Kanalın dirseğine ulaşamaz; makro bunu kontrol eder |
| `SHEET_SCALE`, `X0`, `Y0` | Sayfa ölçeği ve model (0, 0)'ın sayfadaki yeri. X0, C1'lerin dışa dönen çıkış dirsekleri sayfaya sığsın diye 0.20'den kaydı |
| `RULER_X` | Kot cetvelinin sayfadaki yeri, çerçevenin içinde |
| `TEXT_H`, `ARROW_L`, `CAP_H` | Kâğıtta yazı yüksekliği, ok boyu, antetteki başlık yazısı |
| `FR_X0`…`FR_Y1`, `COL_X0` | Çerçeve ve sağ sütunun (lejant, liste, revizyon, antet) sol kenarı |
| `LEVEL_X` | Kot işaretlerinin model x'i, sağ hattın sağında, dış C1'in çıkış bacağının dışında |


Değerler (çizimin bütün sayısal Const'ları; çizim kendi Const'larını kendisi yazar, gerisi tek kaynaktan üretilir):

<!-- BEGIN GENERATED (tools/gen_geometry.py) params -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Const | Değer | Nerede yazılı |
|---|---|---|
| `C1_D` | 4.32 | plant_geometry.yaml |
| `C1_HB` | 6.79 | plant_geometry.yaml |
| `C1_HC` | 4.65 | plant_geometry.yaml |
| `C1_VD` | 2.16 | plant_geometry.yaml |
| `C1_DD` | 0.4 | plant_geometry.yaml |
| `C4_D` | 6.3 | plant_geometry.yaml |
| `C4_HB` | 6.3 | plant_geometry.yaml |
| `C4_HC` | 7.3 | plant_geometry.yaml |
| `C4_VD` | 3.15 | plant_geometry.yaml |
| `C4_DD` | 0.81 | plant_geometry.yaml |
| `C5_D` | 6.5 | plant_geometry.yaml |
| `C5_HB` | 6.5 | plant_geometry.yaml |
| `C5_HC` | 7.531746 | plant_geometry.yaml |
| `C5_VD` | 3.25 | plant_geometry.yaml |
| `C5_DD` | 0.835714 | plant_geometry.yaml |
| `C5_HIN` | 3.507937 | plant_geometry.yaml |
| `C4_VF_S` | 3.9 | plant_geometry.yaml |
| `C4_OUT_RISE` | 5.355 | plant_geometry.yaml |
| `C4_OUT_R` | 0 | plant_geometry.yaml |
| `C4_OUT_RUN` | 0 | plant_geometry.yaml |
| `C4_IN_H` | 3.4 | plant_geometry.yaml |
| `C4_IN_W` | 2.912 | plant_geometry.yaml |
| `C4_TONGUE` | 0.05 | plant_geometry.yaml |
| `C4_IN_L` | 2 | plant_geometry.yaml |
| `C1_VF_S` | 3.45 | plant_geometry.yaml |
| `R1_D` | 3.15 | plant_geometry.yaml |
| `CALC_D` | 6.7404 | plant_geometry.yaml |
| `CALC_H` | 30 | plant_geometry.yaml |
| `CALC_THROAT_D` | 3.130077 | plant_geometry.yaml |
| `CALC_CONE_DEG` | 65 | plant_geometry.yaml |
| `GN_D_SRC` | 3.5 | plant_geometry.yaml |
| `GN_SLOPE_DEG` | 45 | plant_geometry.yaml |
| `GN_PIECE_OVER_D` | 1 | plant_geometry.yaml |
| `GN_LEVEL_OVER_D` | 0.5 | plant_geometry.yaml |
| `GN_CHANNEL_OVER_D` | 0.85 | plant_geometry.yaml |
| `GN_ARM_DEG` | 60 | plant_geometry.yaml |
| `GN_ARM_RUN_OVER_D` | 0.5 | plant_geometry.yaml |
| `GN_ROOT_FWD` | 0.184956 | plant_geometry.yaml |
| `GN_OUT_AT_H` | 0.788074238954 | plant_geometry.yaml |
| `CALC_TA_Z` | 8.270908 | plant_geometry.yaml |
| `CALC_FEED_Z` | 11.385494 | plant_geometry.yaml |
| `TA_D` | 2.4393 | plant_geometry.yaml |
| `MEAL_SLOPE_DEG` | 60 | plant_geometry.yaml |
| `KILN_D` | 4.8 | plant_geometry.yaml |
| `KILN_L` | 60 | plant_geometry.yaml |
| `KILN_SLOPE` | 0.03 | plant_geometry.yaml |
| `COOLER_AREA` | 119.6 | plant_geometry.yaml |
| `COOLER_W` | 4 | plant_geometry.yaml |
| `COOLER_H` | 3 | plant_geometry.yaml |
| `C1_RISER_X` | 6.727386 | plant_geometry.yaml |
| `C1_RISER_Z0` | 0.212614 | plant_geometry.yaml |
| `C1_BEND_Z` | 7.712614 | plant_geometry.yaml |
| `C1_BEND_R` | 2.227386 | plant_geometry.yaml |
| `C1_BEND_DEG` | 90 | plant_geometry.yaml |
| `C1_TRANS_L` | 1.5 | plant_geometry.yaml |
| `C1_DUCT_H` | 3 | plant_geometry.yaml |
| `C1_VOL_OUT` | 3.07 | plant_geometry.yaml |
| `C1_VOL_FAR` | 2.226723 | plant_geometry.yaml |
| `C1_FEED_Z` | 4.712614 | plant_geometry.yaml |
| `C1_FEED_L` | 1 | plant_geometry.yaml |
| `C1_FEED_W` | 0.6 | plant_geometry.yaml |
| `C1_OUT_RISE` | 2.7 | plant_geometry.yaml |
| `C1_OUT_R` | 3.24 | plant_geometry.yaml |
| `STAGE_GAP` | 4 | plant_geometry.yaml |
| `ZIG_DX` | 6.802848 | plant_geometry.yaml |
| `DUST_OVER_ROOF` | 0.5 | plant_geometry.yaml |
| `RISER_SLOPE_DEG` | 45 | plant_geometry.yaml |
| `RISER_TAPER_DEG` | 15 | plant_geometry.yaml |
| `R4_RISE_V` | 7.035957 | plant_geometry.yaml |
| `R3_RISE_V` | 7.035957 | plant_geometry.yaml |
| `R2_RISE_V` | 7.035957 | plant_geometry.yaml |
| `RISER_RUN` | 2.95988 | plant_geometry.yaml |
| `RISER_RUN4` | 2.95988 | plant_geometry.yaml |
| `RISER_Y` | 4.656 | plant_geometry.yaml |
| `C5_OVER_TA` | 5 | plant_geometry.yaml |
| `GN_TO_C5_GAP` | 1 | plant_geometry.yaml |
| `C1_TWIN_GAP` | 1 | plant_geometry.yaml |
| `C1_TWIN_S` | 8.507386 | plant_geometry.yaml |
| `C1_DUCT_Y` | 2.64 | plant_geometry.yaml |
| `R1_BRANCH_HALF` | 1.613693 | plant_geometry.yaml |
| `R1_UP_MIN` | 0.5 | plant_geometry.yaml |
| `KILN_AXIS_Z` | 10 | plant_geometry.yaml |
| `CHAMBER_MARGIN` | 1 | plant_geometry.yaml |
| `KIC_RAMP_DEG` | 50 | plant_geometry.yaml |
| `KIC_RAMP_FOOT` | 1.5 | plant_geometry.yaml |
| `KIC_TOP` | 5.950031 | plant_geometry.yaml |
| `COOLER_DROP` | 1 | plant_geometry.yaml |
| `HOOD_L` | 5.98 | plant_geometry.yaml |
| `HOOD_H` | 7.2 | plant_geometry.yaml |
| `HOOD_TA_X` | 4.485 | plant_geometry.yaml |
| `TA_BEND_R_OVER_D` | 1.5 | çizimin kendi Const'u |
| `ID_FAN_L` | 2.5 | çizimin kendi Const'u |
| `RM_L` | 0.8 | çizimin kendi Const'u |
| `MEAL_ENTRY_UP` | 1.5 | çizimin kendi Const'u |
| `MEAL_SIDE_L` | 1 | çizimin kendi Const'u |
| `MEAL_DROP` | 1.5 | çizimin kendi Const'u |
| `MEAL_JOIN_DEG` | 50 | çizimin kendi Const'u |
| `C4_MEAL_DROP` | 3 | çizimin kendi Const'u |
| `C5_MEAL_DROP` | 1 | çizimin kendi Const'u |
| `MEAL_BEND` | 1 | çizimin kendi Const'u |
| `CROSS_GAP` | 0.5 | çizimin kendi Const'u |
| `MEAL_INTO_CHAMBER` | 1 | çizimin kendi Const'u |
| `C5_ARROW_FROM_END` | 5 | çizimin kendi Const'u |
| `MIN_SEG` | 0.05 | çizimin kendi Const'u |
| `CLINKER_OUT_Z` | 3.5 | çizimin kendi Const'u |
| `VENT_IN` | 3 | çizimin kendi Const'u |
| `VENT_UP` | 4 | çizimin kendi Const'u |
| `CLINKER_ON_GRATE` | 1 | çizimin kendi Const'u |
| `TA_ARROW_LONG` | 1.15 | çizimin kendi Const'u |
| `KILN_FLOW_OFF` | 1 | çizimin kendi Const'u |
| `PRIMARY_AIR_L` | 2 | çizimin kendi Const'u |
| `SEC_AIR_DX` | 1.5 | çizimin kendi Const'u |
| `SHEET_SCALE` | 300 | çizimin kendi Const'u |
| `PAPER_W` | 0.841 | çizimin kendi Const'u |
| `PAPER_H` | 0.594 | çizimin kendi Const'u |
| `X0` | 0.215 | çizimin kendi Const'u |
| `RULER_X` | 0.04 | çizimin kendi Const'u |
| `Y0` | 0.06 | çizimin kendi Const'u |
| `TEXT_H` | 0.0035 | çizimin kendi Const'u |
| `ARROW_L` | 0.004 | çizimin kendi Const'u |
| `CAP_H` | 0.002 | çizimin kendi Const'u |
| `FR_X0` | 0.02 | çizimin kendi Const'u |
| `COL_X0` | 0.651 | çizimin kendi Const'u |
| `LEVEL_X` | 50 | çizimin kendi Const'u |
| `AXIS_OVER` | 0.6 | çizimin kendi Const'u |
| `AXIS_UNDER` | 0.1 | çizimin kendi Const'u |
| `LAYER_N` | 9 | çizimin kendi Const'u |
| `EXT_TOL` | 0.0001 | çizimin kendi Const'u |
<!-- END GENERATED -->

## Yerleşim

Kalsinatör ekseni x = 0'dadır. Sağ hat (R) +x'te, fırının üstünde durur; sol hat (L) −x'te, onun aynasıdır.

Konumlar ve kotlar (z zeminden, x kalsinatör ekseninden, sağ hat):

<!-- BEGIN GENERATED (tools/gen_geometry.py) layout -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ne | Konum [m] |
|---|---|
| Fırın giriş odası | x = −3.400 .. 3.400, z 6.600 .. 12.550; taban rampası 50.0° |
| Kalsinatör | z 12.550 .. 45.680; kaz boynu tepesi z 51.655, kol inişi x = ±5.475, C5 giriş kotu z 39.322 |
| Tersiyer hava kanalı | eksen z 20.821 |
| İç kolon (C5, C3) | x = ±11.475 |
| Dış kolon (C4, C2) | x = ±18.278 |
| R1 | x = ±18.278 |
| İkiz C1 | x = ±14.024 ve ±22.531 |
| C5 toz çıkışı / çıkış borusu tepesi | z 27.041 / 46.597 |
| C4 toz çıkışı / çıkış borusu tepesi | z 41.572 / 60.527 |
| C3 toz çıkışı / çıkış borusu tepesi | z 55.672 / 74.627 |
| C2 toz çıkışı / çıkış borusu tepesi | z 69.772 / 88.727 |
| C1 toz çıkışı / çıkış borusu tepesi | z 92.727 / 106.867 |
| Kule tepesi (C1 çıkış dirseklerinin tepesi) | z 111.187 |
| Fırın | (3.400, 10.000) → (63.373, 8.201) |
| Soğutucu | x 63.373 .. 93.273, z 1.801 .. 4.801 |
| Fırın başlığı | x 63.373 .. 69.353, z 4.801 .. 12.001 |
<!-- END GENERATED -->

Fırın giriş odasının düz tabanı yoktur: tabanı fırının alt dudağından odanın sol üst köşesine çıkan bir rampadır. Y kaz boynunun kolları boynun içinden başlar, dirsekle döner, C5'in giriş kotuna iner ve yatay olarak C5 gövdesine girer. R4, R3 ve R2 C5, C4 ve C3'ün çıkış borusudur; R1 C2'nin çıkış borusundan, C2'nin ekseninde dik çıkar. İkiz C1'ler R1'in iki yanında, C2'nin üstünde, birbirinin aynasıdır.

## Yollar

Her hattaki yollar aynıdır; sol hat sağın aynasıdır.

**Gaz:**
- başlık (brülör ucu) → fırın boyunca, eksenin `KILN_FLOW_OFF` üstünde → giriş odası (rampanın 1 m üstünden kalsinatör eksenine döner) → kalsinatör → kaz boynu → C5. Kaz boynu `calciner.bas`'taki gibi bir Y'dir: tavanın ortasından boyun yükselir; tepesinde iki kol başlar (çaplar ekipman tablosunda), her biri 180° dirsekle dışa döner ve iner. İki kolun dış duvarları boynun 3.6 m üstünde, eksende kesişir; çatal orasıdır. İniş, C5'in girişine ulaşınca riserlar gibi iki 45°'lik adımla döner: girişin `GN_BEND_LEG` kol çapı üstünde 45° döner, 45° ile girişin seviyesine iner ve 1 m yatay olarak C5 gövdesinin yan duvarına, üst duvarı tavan hizasında girer; bu, volütlü girişin yandan görünüşüdür. Kol C5'in volüt girişinin yüksekliğine sığar; ön kontrol bunu zorlar. Kolun inişi, C5 tersiyer hava kanalının üstünde durduğu için `calciner.bas`'taki kol ucundan (kalsinatörün yarı yüksekliği) daha yukarıda biter.
- C5 → R4 → C4: R2 / R3 gibi; R4, C5'in CFD çıkış borusunun kendisidir (kullanıcı kararı 14 Ekim 2026): çatının üstünde CFD'nin dik borusu, hemen ardından CFD dirseği (C4'ün çatı kotunda) ve yatay bacakla (çıkış yüzünden sonra 0.92 m serbest) C4'e girer; bacağın alt duvarı son 1.38 m'de 45° ile volüt girişine yükselir. Eski 45°'lik daralma ve iki 45° dönüş kalktı.
- C4 → R3 → C3, C3 → R2 → C2: riser, C4 / C3'ün CFD çıkışının kendisidir (kullanıcı kararı 13 Ekim 2026, ayrı riser kalktı ve yol kısaldı). Çıkış CFD domeninin birebir aynısıdır (14 Ekim 2026): çatının üstünde CFD'nin dik borusu (siyah, siklonun parçası), hemen ardından 90° dirsek (duvarları yay) ve yatay bacak (çıkış yüzünden sonra 1.36 m serbest). CFD'nin bacağından sonrası domenin dışındadır; bacak oradan düz devam eder (bir ara orada 45° ile 1.5 m yükselip katları açıyordu; kıvrım istenmediği için kalktı, 14 Ekim 2026). Bacağın üst duvarı üst siklonun çatı hizasındadır, alt duvarı son 1.23 m'de 45° ile volüt girişine yükselir; üst siklonun kotu buradan gelir.
- C2 → R1 → ikiz C1: R1 C2'nin ekseninde dik yükselir (kullanıcı kararı 17 Kasım 2026): C2'nin CFD çıkış borusu (çatının üstünde 7.871 m) ucunda 45°'lik bir daraltıcıyla (`R1_RED_L`) Ø4.63'ten R1'in çapına daralır, R1 oradan Y'ye kadar düz çıkar (en az `R1_UP_MIN`; C1 kademesini `STAGE_GAP` belirlediği için 6.95 m). C4'ün CFD dirseği ve bacağı C2'de çizilmez; C3–C5'te durur. 13 Ekim – 17 Kasım 2026 arasında C2'nin bacağı `R1_LEG_ON` kadar uzayıp bir dirsekle yukarı dönüyordu ve R1 C2'den 11.3 m kalsinatöre doğruydu. Sonra R1 45°'lik düz parçalardan bir Y ile iki kola ayrılır: R1'in duvarları 45° ile dışa açılır, kolların iç duvarları R1 eksenindeki çataldan 45° ile yükselir; her kol Y boyunca kendi çapındadır (R1'in alanının yarısı). Kollar Y'den sonra, tam C1 CFD domeninin tabanında (`C1_RISER_Z0`) dik başlar. Oradan yukarısı her C1 için CFD domeninin aynısıdır: dik kol, 90° dirsek, geçiş ve volütün yatay giriş kanalı (bkz. `C1_RISER_X` … satırı). İkizler birbirinin aynasıdır: kollar ortada, gaz çıkış dirsekleri dışa döner. Aynalanmış akış aynı çözümdür, yalnız girdap ters yönde döner. Y CFD domeninin altında kalır; ama R1 düz olduğundan C2'nin dönen akımı Y'ye ve kollara ulaşır, aynalı ikizlerin girişine ters yönlü dönme gelir. C1 CFD'sinin düzgün giriş profili bu yüzden bir yaklaşımdır; Y'li giriş domeni gerekir ([riser_R1.md](preheater/riser_R1.md)).
- ikiz C1 → ID fan: her C1'in gaz çıkışı CFD'deki gibi çatının üstünde yükselir, kolun ters tarafına 180° döner ve çatı kotuna iner; oradan aşağı bir "to ID fan" oku

**Farin:**
- ham farin → C1 kolları: CFD'deki gibi her kolun C1'den uzak tarafındaki 60°'lik oluktan (`C1_FEED_W`, `C1_FEED_Z`); oluk kapalı uçlu çizilir, içinden küçük başlı bir ok kol duvarına iner, okun ucunda küçük "FEED" yazılıdır. Hat başına iki, toplam dört besleme
- Farin hatları tam çizilir; arkasından geçtiği siklonda ya da TA kanalında kırılır (bkz. "Farin hatları tam, arkadan geçtiği yerde kırık").
- Uzak C1 → R2, C2 → R3, C3 → R4: her siklon iki kademe altındaki riser'ı, yani C3 / C4 / C5'in CFD çıkış borusunu besler. Hat borunun dirseğin ters tarafına gelir, duvarın `MEAL_SIDE_L` yanında iner ve 60° ile boruya, çatının `MEAL_ENTRY_UP` üstünden, CFD borusunun alt kısmına girer. CFD gaz-only'dir; farin yükü analitik hesaptadır, bu yüzden giriş yeri CFD çözümünü değiştirmez.
  - Uzak C1'in hattı toz çıkışından `MEAL_DROP` düşer, 60° ile R2'nin yanına geçer ve 19.1 m iner; hiçbir şeyi kesmez.
  - C2 ve C3 kendi riser'larının tam üstündedir: hat toz çıkışından `MEAL_DROP` düşer, 60° ile dirseğin üstünden dışarı çıkar (0.40 / 0.41 m açık), sonra iner. C3'ün hattı kaz boynu inişinden 0.86 m açıktadır.
  - 60° eğim, kalsinatör besleme borularının eğimidir (Fidaros 2007). Boru dik riser duvarıyla 30° yapar, yani farin duvara yatık, neredeyse teğet kayarak girer.
  - Tesislerde farin, riser'a alttaki siklonun hemen üstünden bu şekilde verilir.
- Yakın C1 (hattın dış ucundaki) → uzak C1'in hattı: toz çıkışından `MEAL_DROP` düşer, `MEAL_JOIN_DEG` ile R1'in ve R2'nin dirseğinin arkasından geçer (kırık) ve uzak C1'in R2'nin yanında inen hattına katılır. Uzak C1'in hattı da R2'nin dirseğinin arkasından geçer: C1'ler C2/R2 düzleminin 6.7 m arkasındadır, borular R2'ye ancak dik kısmında öne döner (17 Kasım 2026). İki C1'in farini tek boruyla R2'ye girer (kullanıcı kararı 14 Ekim 2026).
- C4 → kalsinatör: `C4_MEAL_DROP` dik düşer, `MEAL_BEND`'lik dönüş parçası ve kalsinatör duvarına, `calciner.bas`'ın farin borularının duvarı kestiği kotta (`CALC_FEED_Z`, tersiyer kanalın hemen üstü; 14 Ekim 2026'ya kadar çizimde 3 m aşağıdaydı, `FEED_LOWER`) düz hat; C5'in konisinin arkasından geçer (kırık). Her hattın C4'ü kendi taraftaki besleme borusunu besler.
- C5 → giriş odasının tavanı: `C5_MEAL_DROP` dik düşer, dönüş parçası ve tavana, kenarından `MEAL_INTO_CHAMBER` içeride düz hat; kalsinatör konisinin altından geçer. Sağ hattaki TA kanalının arkasından geçer (kırık), soldaki hiçbir şeyi kesmez.
- Giriş odasında farin birikmez: düz taban yerine fırının alt dudağından odanın sol üst köşesine çıkan bir rampa var (açısı yerleşim tablosunda; Ø4.0 fırınla 39.8°'ydi). Bu, farinin yığılma açısı (~40°), yani kayabildiği sınır; makro 39°'nin altına izin vermez. İki C5'in farini rampaya düşer ve fırına kayar. Eski düz taban fırın ağzının 1 m altındaydı ve sol yarısı fırından 5 m uzak bir ölü bölgeydi
- giriş odası → fırın → ızgaralı soğutucu (klinker): fırın ağzından başlar, fırın boyunca eksenin `KILN_FLOW_OFF` altında gazın tersine akar, başlıkta soğutucuya düşer ve ızgara boyunca ilerler. Fırın içindeki iki paralel ve ters oklu çizgi karşı akışı gösterir
- ızgaralı soğutucu → klinker taşıma: klinker soğutucunun ucundan dik iner, tabanından çıkar ve zeminin `CLINKER_OUT_Z` altında, "to clinker transport" yazısının yanında bir okla biter. Sağa değil aşağı iner, çünkü sağda antet var

**Hava:**
- primer hava → ana brülör: yalnızca belirtilir; başlığın ön duvarına, fırın gazının (kırmızı) başladığı kotta dokunan kısa bir ok; çizgi okun ucunda biter
- soğutucu → başlık (sekonder hava): başlığın altında soğutucudan yükselir ve fırının ucuna, fırın gazının başladığı noktaya girer. GAZ katmanında (kırmızı) çizilir, çünkü fırının içinde fırın gazı olarak devam eden akım odur. Fırının içinde ayrı çizilmez: fırın gazı, primer ve sekonder havanın brülörde yanmış hâlidir
- Çizimde "primary air" başlığın dışında, primer hava hattının altında; "secondary air" fırının içinde, fırın gazı ile klinker çizgisinin arasında yazılıdır
- soğutucu → başlık → tersiyer hava kanalı → kalsinatör (GAZ katmanında, kırmızı; sıcak hava): tersiyer hava soğutucudan başlığın içinden dik bir okla yükselir ve başlığın tepesindeki kanala girer; kanal dik yükselir, `TA_BEND_R_OVER_D` × D yarıçaplı dirsekle yatay döner. Kanal kalsinatöre koni tepesinde, `calciner.bas`'ın kurduğu kotta (`CALC_TA_Z`) girer; CFD'de teğetseldir, çizim onu yandan gösterir.
- soğutucu → vent (fazla hava, GAZ katmanında, kırmızı; hâlâ sıcak): soğutucunun ucundan `VENT_IN` içeride tavanından dik bir okla çıkar, "to cooler vent" yazısına gider

## Doğrulama

Makronun ön kontrolleri:
- R1 ikiz C1'lerin arasına sığıyor ve C2'nin gaz çıkışından dar; `R1_RED_L` `R1_RED_DEG`'deki daraltıcının boyu; C1'ler C2'nin çıkış borusunun en az 0.5 m üstünde
- C3 ve C2'nin konisi, altlarındaki CFD dirseğinin dış duvarının en az 0.5 m üstünde; R2–R4'ün bacakları dirsekten sonra üst siklona ulaşıyor ve 3.40 m'lik girişe daralacak yer var
- R2–R4'e giden farin CFD borusunun dirseğin altında kalan kısmına giriyor, toz çıkışından ulaşabiliyor; C2 / C3'ün eğimli parçası altındaki dirsekten en az 0.3 m açık
- C5 farininin dik düşüşü TA kanalının üstünde bitiyor
- C5'ler kalsinatöre, hatlar kaz boynu kollarına değmiyor
- kaz boynu kolu C5'in volüt girişinin yüksekliğine sığıyor
- C5'ler TA kanalının en az `C5_OVER_TA` üstünde (yerleşim bunu kurar)
- C4 farini kalsinatöre koninin üstünden giriyor
- TA, C5'lerin altından, giriş odası ve fırının üstünden geçiyor
- soğutucu zeminin üstünde, başlık soğutucunun üstünde
- fırın içindeki gaz ve malzeme çizgileri fırın kabuğunun içinde

Çizimden sonra sayfa sketch'i geri okunur. Her katmanda çizilen çizgi ve yay sayısı bulunmalı. Beklenen sayılar:

| Katman | Çizgi | Yay |
|---|---|---|
| EKIPMAN | 155 | 0 |
| GAZ | 173 | 38 |
| FARIN | 91 | 0 |
| HAVA | 4 | 0 |
| YAZI | 91 | 0 |
| CERCEVE | 16 | 0 |
| EKSEN | 19 | 0 |
| OLCU | 47 | 5 |
| GIZLI | 24 | 0 |

Son doğrulanmış çalıştırma 14 Ekim 2026 (CFD kilidi; C4 / C5 çıkış borusu 1.70·VD; dört C1 dahil bütün farin hatları tam, arkadan geçtiği yerde kırık; TA dirseği; "ILC" etiketi). Sayfada 241 not vardır. GAZ'daki 2 ek çizgi lejanttaki kırık hat örneğinin kanalıdır. GIZLI'daki 24 çizgi on iki vorteks bulucunun (her hatta C2–C5 ve iki C1) duvarları. Bu sayılar okları, lejantı, tabloları ve anteti içerir. OLCU'daki 5 yay grid balonları, GAZ'daki 38 yay kaz boynunun (4), dört C1'in kol ve çıkış dirseklerinin (16), sekiz C2–C5 çıkış dirseğinin (16) ve TA dirseğinin (2) duvarlarıdır. Çizgilerin kâğıttaki kapsamı da çizildiği kapsama 0.1 mm içinde oturmalı.

1/√2 ölçekli sürüm bir Python betiğiyle de kurulmuştu; o betik, hiçbir kanal kenarının ya da farin hattının kendi kaynağı ya da hedefi olmayan bir ekipman dış hattını kesmediğini doğruladı. Bilinçli istisnalar, ekipmanın içinden geçen akış çizgileridir (fırın → giriş odası → kalsinatör, soğutucu → başlık → fırın, giriş odası → fırın → soğutucu klinker yolu). Farin hatları yalnız arkasından geçtikleri yerlerde (yakın C1 → C2'nin çıkış dirseği ve R1 dirseği, C4 → C5'in konisi, sağ C5 → TA kanalı) kesişir ve orada kırılır; bu Python'da da denetlendi (14 Ekim 2026).

Ham farin R1'e, kendi hedefine girer. Betik ayrıca etiketlerin yaklaşık metin kutularını taradı: hiçbir etiket bir çizgiyle ya da başka bir etiketle çakışmıyor.

Çıktılar `geometry/output/2500/` altında:
- çizim `plant_topology_2d.SLDDRW`
- `plant_topology_2d.pdf`
- tam log `plant_topology_2d_build.log`
