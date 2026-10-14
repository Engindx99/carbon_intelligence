# Tesis topolojisi (2D şema)

Makro: [`geometry/macros/plant_topology_2d.bas`](macros/plant_topology_2d.bas). Referans hat: 2500 t/d.

**CFD girdisi değildir.** Bu, tesisin topolojisini göstermek için çizilmiş gerçek ölçekli bir 2D şemadır: hangi ekipman var, nerede duruyor, gaz, farin ve hava hangi yoldan akıyor. `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır.

Önceki 3D topoloji modeli (`plant_topology.bas`, tek hatlı, çok gövdeli) kaldırıldı. Yerine bu 2D şema geldi; 2D daha okunur ve çakışma kısıtı taşımaz (kullanıcı kararı, 5 Ekim 2026).

## Ne çizilir

Bir SolidWorks **çizim sayfası**: A1 yatay (841 × 594 mm), ölçek **1:300**. Model koordinatları (x yatay, z kot, metre) sayfaya `P(x, z) = (X0 + x/300, Y0 + z/300)` ile yerleşir. Ölçek önce 1:200, sonra 1:250 idi. Hatlar tam 2500 ölçüsüne çıkınca kule ~125 m oldu ve A1'e 1:250'de sığmadığı için 1:300'e geçildi (12 Ekim 2026). Stub yarıya inince kule 117.4 m oldu; ölçek 1:300'de kaldı.

İlk sürüm bir parça sketch'iydi. Renkler orada görünmedi, çünkü sketch'in durum rengi özel rengi bastırıyordu. Etiketler 1 m yükseklikte okunmuyordu, her köşede de nokta yığını vardı. Çizim belgesine bu yüzden geçildi (kullanıcı kararı, 5 Ekim 2026).

- **Ekipman, gerçek kesit dış hatlarıyla:** siklonlar (toz çıkışı, koni, gövde, tavan, gaz çıkış stub'ı), kalsinatör (boğaz, koni, gövde), fırın giriş odası, fırın, soğutucu, fırın başlığı.
- **Akışın geçtiği duvarlar açıktır:** fırının iki ucu (giriş odasına ve başlığa açılır), kalsinatör boğazı (giriş odasının tavanı), kaz boynu kollarının kalsinatör tavanındaki ağızları, tersiyer hava kanalının başlık tavanındaki ve kalsinatör duvarındaki ağızları, başlığın altı (soğutucuya açık), her siklonun toz çıkışı, gaz çıkış stub'ının tepesi ve girişinin geldiği taraftaki gövde duvarı. R1 C2'nin çıkış bacağından bir dirsekle başlar; R2–R4, C3–C5'in çıkış borusunun kendisidir. Açıklığın yanında kalan, `MIN_SEG`'ten (0.05 m) kısa duvar parçası çizilmez. Bütün siklonlarda giriş tavandan aşağı iner; gövde duvarı yalnız kanalın yüksekliği boyunca açıktır, altında kapalı devam eder. Tek çizgili yollar (farin, egzoz, primer hava) duvarda biter.
- **Ana kanallar gerçek çapında, çift çizgiyle:** R1–R4, kaz boynu ve tersiyer hava kanalı. Kenarlar eksenin w/2 iki yanındadır; köşeler kenarların kesişiminde birleşir. Kaz boynunun Y dirsekleri ve C1'lerin iki dirseği (kol ve gaz çıkışı, CFD katısındaki gibi) yaydır; C2–C5'in çıkış dirsekleri (R2–R4) de yaydır; R1'in dirseği, Y'si ve kaz boynu inişinin dönüşü 45°'lik düz parçalardır.
- **Diğer yollar tek çizgiyle, eksen boyunca:** farin hatları, C1 egzozu, ikincil hava, fırın → kalsinatör gazı.
- **Akış okları:** her yolun en uzun parçasının ortasında, akış yönünde. Çizimden çıkan ya da yalnızca bir akımı belirten yollarda ("to ID fan", "to cooler vent", "to clinker transport", primer hava, tersiyer hava oku) ok yolun ucundadır; okun ötesinde çizgi kalmaz.
- **Farin hatları tam, arkadan geçtiği yerde kırık:** her farin hattı toz çıkışından hedefine tam çizilir (kullanıcı kararı 14 Ekim 2026, uç gösteriminden geri dönüldü). Bir hat bir siklonun, C2'nin çıkış dirseği ve R1 dirseğinin ya da TA kanalının arkasından geçiyorsa, o dış hattın içinde ve iki yanında 0.5 m (`CROSS_GAP`) çizilmez (`PathM`; bunlar kapalı dış hat olarak kaydedilir: `BodyM`, `CycBody`, `ElbowBody`). Lejantta bir örneği var.
- **Şematik not:** lejantta, giriş odasının ölçüsünün kaynaksız olduğu ve farin borularının 2D izdüşümü olduğu (C4 ve C5 boruları ve oda rampası 3D yerleşimde daha diktir) yazılıdır.
- **Etiketler:** not olarak, kâğıtta 3.5 mm yükseklikte. Siklon adları gövdenin içinde (oradan hiçbir yol geçmez), riser adları kanalın içinde. Sayılar yerel ayardan bağımsız olarak noktalı ve sabit ondalıklı yazılır ("2.440").
- **Kot cetveli:** solda, çerçevenin içinde, 0'dan 100 m'ye; her 10 m'de bir çentik ve kot. Zemin çizgisi cetvelden başlar.
- **Lejant ve notlar:** renkler, ok, çift ve tek çizginin anlamı, kanalın arkasından geçerken kırılan farin hattı; altında numaralı notlar (birimler, hat başına ölçek, şematik/2D izdüşüm, CFD girdisi olmadığı) ve 10 m'lik ölçek çubuğu.
- **Çerçeve (ISO 5457):** A1, sol 20 mm, diğer kenarlar 10 mm; 12 × 8 bölge, üst ve altta 1–12, yanlarda A–H.
- **Antet (ISO 7200):** 180 mm, sağ altta. Belge türü, başlık ve ek başlık, ölçek, birim, tarih, dil, sayfa, durum, teknik referans, kaynak. Çizen, onaylayan, sorumlu birim, çizim numarası ve revizyon alanları boş bırakılır (kullanıcı kararı); elle doldurulur.
- **Revizyon tablosu:** antetin üstünde, Rev / Description / Date / By başlığı ve iki boş satır.
- **Ekipman etiketleri ve listesi:** siklonlar (C1–C5, L/R) ve riser'lar (R1–R4) adlarıyla; diğerleri etiketle: CAL kalsinatör, GN kaz boynu, TAD tersiyer hava kanalı, KIC giriş odası, KLN fırın, HD başlık, CLR soğutucu, RM ham farin girişi (R1'e giren kısa ok). Sağ sütundaki ekipman listesi her etiketin adını, adedini (iki hat birlikte), ölçüsünü ve dayanağını (CFD, yayınlanmış, türetilmiş, şematik) verir; ölçüler çizimin kullandığı sabitlerden yazılır.
- **Kot işaretleri:** sağ hattın sağında (x = 50) her kademenin toz çıkışı, kalsinatör tavanı ve kule tepesi; giriş odasının solunda fırın ekseni. Üçgen sembol, seviye çizgisi ve "+36.30 C4 dust outlet" biçiminde yazı.
- **Grid ve ölçüler:** kulenin üstünde beş kolon ekseni (1 dış L, 2 iç L, 3 kalsinatör, 4 iç R, 5 dış R) balonlarıyla; aralarındaki mesafeler (15.000 / 17.225 / 17.225 / 15.000) ve toplam (64.450) eğik çizgi uçlu ölçülerle.
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

**Ölçek kuralı** (kullanıcı kararı, 12 Ekim 2026): her hat tek başına bir 2500 t/d hattıdır, iki hat birlikte **5000 t/d**. Hattın siklonları CFD'si çözülen ölçülerdedir, riser'ları yayınlanmış 2500 ölçüsündedir. İkinci hat birincinin kopyasıdır; ayrı CFD gerekmez. Bu kural 5 Ekim 2026'daki "her hat gazın yarısını taşır, ölçüler × 1/√2" kuralının yerini aldı.

| Ekipman | Ölçü | Kaynak |
|---|---|---|
| C1 (hat başına ikiz) | D 4.32 | cyclone_C1.md (CFD) |
| C2 = C3 = C4 | D 6.30, gövde 6.30 (h = D) | cyclone_C4.md (CFD) |
| C5 | D 6.50, gövde 6.50 (CFD C4 × 6.50/6.30) | cyclone_C5.md |
| R1 (hat başına) | Ø3.07 | catalog.md (HFC2500) |
| R2 / R3 / R4 (hat başına) | Ø4.63 / 4.63 / 4.777 | C3 / C4 / C5'in CFD çıkış borusu; yayınlanmış Ø3.35 / 3.45 / 3.60 çizilmez |
| Kalsinatör | Ø6.74, 30.0 m (koni dahil), boğaz Ø3.130, koni 65° | calciner.md (PF5000) |
| Kaz boynu | Y: boyun Ø4.95, 2 kol × Ø3.50, kalsinatörün yarı yüksekliğinde biter | calciner.md, gooseneck.md |
| Tersiyer hava kanalı | Ø2.439 (türetilmiş) | calciner.md |
| Fırın | Ø4.8 × 74 m, %3 eğim | kiln.md (PF5000) |
| Soğutucu | ızgara alanı 119.6 m² | cooler.md (PF5000) |

Kalsinatör, Y kaz boynu, TAD, fırın ve soğutucu 5000 t/d'nindir: PF5000'den, ya da onun ölçülerinden türetilmiş ([calciner.md](calciner/calciner.md), [kiln.md](kiln/kiln.md), [cooler.md](cooler/cooler.md); 12 Ekim 2026). Giriş odası ve başlık şematiktir, fırının çevresinde bir paydır. Twin 5000 t/d beslemesiyle çalışır; hangi ekipmanı hangi akış hacmiyle hesapladığı [fluid_volumes.md](fluid_volumes.md)'dedir.

Siklon CFD dokümanları (`cyclone_C1–C5.md`) ve `cyclone.bas` aynı ölçüleri kullanır; çizim onlardan ayrılmaz.

## CFD domenleri ve serbest bölge

Çizim CFD çözümünü bozmadan geliştirilir (kullanıcı kararı, 14 Ekim 2026). Her CFD domeni çizimde donmuş bir bloktur: giriş ve çıkış yüzlerinin arasındaki hiçbir ölçü yalnız çizimde değişmez. Değişecekse önce `cyclone.bas` değişir, CFD yeniden çözülür, sonra çizim. Yüzlerin dışı serbesttir.

| Blok | Domen (donmuş) | Giriş yüzü | Çıkış yüzü |
|---|---|---|---|
| C1 (×4) | gövde, VF 2.16, Ø2.171 kol, 95° R 2.171 dirsek, 1.5 m geçiş, 5° kanal, 0.6 m oluk; 3.0 m çıkış borusu, R 3.6 180° dirsek, 3.0 m iniş | kolun tabanı, toz çıkışının 0.885 m üstü | inişin ucu, çatı kotunda, eksenden 7.2 m |
| C2–C4 (×6) | gövde, VF 3.90, volüt ve 3.0 m giriş kanalı, 7.871 m (1.70·VD) çıkış borusu, R 4.63 90° dirsek, 4.63 m bacak | giriş kanalının ucu, eksenden 3.0 m (`C4_IN_L`) | bacağın ucu, eksenden 9.26 m, çatının 12.50 m üstünde |
| C5 (×2) | C2–C4'ün 6.50/6.30 = 1.0317 katı (CFD'si ayrıca çözülmez) | eksenden 3.10 m | eksenden 9.55 m |

**Serbest:**
- R1'in dirseği ve Y'si, yani C1 kol tabanının altı.
- Çıkış yüzünden sonraki bacak ve giriş yüzüne kadar olan kanal: uzunluğu, 4.63 → 3.40 daralması.
- Kolon aralıkları (`ZIG_DX`, `R1_LEG_ON`, `R1_BRANCH_HALF`, `GN_TO_C5_GAP`).
- Kalsinatör, kaz boynu, TA, fırın, soğutucu yerleşimi.
- Farin hatlarının gösterimi, etiketler, tablolar.

**Kısıtlar:**
- Gaz kanalı bir çıkış yüzünden bir giriş yüzüne kıvrımsız gider. Kademeler arası yükseklik bu yüzden donmuştur: 7.871 + 4.63 + 2.315 m. Kule ancak CFD değişirse uzar ya da kısalır.
- Daralma ve geçişler yalnız iki yüzün arasındadır.

**Farin girişi:** C1–C3'ün farini R2–R4'e, yani C3–C5'in CFD çıkış borusuna, çatının 1.5 m üstünden girer; bu domenin içidir. CFD gaz-only olduğu ve farin yükü analitik hesaplandığı için çözümü bozmaz. İleride yüklü (DDPM) bir CFD yapılırsa giriş yeri domenin içinde modellenmelidir.

**Kilit:**
- `tests/test_plant_topology_cfd_lock.py` iki makroyu metin olarak okur. Çizimdeki her domen ölçüsünün `cyclone.bas`'taki `SelectCyclone` değerlerine 1 mm içinde eşit olduğunu doğrular; C5 için ayrıca C4 × 1.0317 olduğunu. Biri öbürü olmadan değişirse test hangi ölçünün kaydığını yazarak düşer (`python3 -m unittest tests.test_plant_topology_cfd_lock`).
- Makronun ön kontrolleri yüzleri korur: R4–R2'nin daralması alttaki siklonun çıkış yüzünden sonra başlar ve üsttekinin giriş yüzünün dışında biter; R1'in dirseği C2'nin çıkış yüzünden sonra başlar; kaz boynu C5'in giriş yüzünün dışında kalır. R1'in Y'si C1 kol tabanının altında kalır.
- Çizimdeki çıkış borusu 5.79 değil, CFD'nin tam değeri 1.25 × 4.63 = 5.7875 m'ydi; kilit testi bu 2.5 mm'lik farkı yakaladı.
- **C4 / C5 çıkış borusu 1.25·VD'den 1.70·VD'ye (5.79 → 7.87 m; kullanıcı kararı 14 Ekim 2026).** 1.25'te C2 ve C3 altlarındaki CFD dirseğinin yalnız 0.9 m üstündeydi; farin hatları dirseğe yapışmadan inemiyordu. Bu donmuş bir bloktur, iş akışına göre değişti: önce çizim denendi, sonra `cyclone.bas`'ta `OUTLET_EXT_OVER_VORTEX_D` siklon başına oldu (C1 1.25, C4 ve C5 1.70), kilit testi ikisini eşitler. C4 CFD'si bu domende yeniden çözüldü (14 Ekim 2026): statik ΔP 522.8 Pa, Eu 11.54 (1.25'li domende 515.5 Pa, 11.38; +%1.4); bkz. [cyclone_C4.md](preheater/cyclone_C4.md). Kule 112.02'den 120.41 m'ye uzadı.

**İş akışı:**
1. Serbest bölgede bir değişiklik: Python prototipi → makro → kilit testi ve ön kontroller → SolidWorks → log sayıları bu dokümana → commit.
2. Donmuş bir bloğa dokunan değişiklik: önce `cyclone.bas`, CFD yeniden çözülür, sonra çizim. Kilit testi iki tarafı eşit tutar.

## Şematik parametreler (kaynaksız; yalnız yerleşim için)

İki satır ("donmuş (CFD)") CFD domenlerinin ölçüleridir ve kilit testine bağlıdır; diğer bütün satırlar serbest bölgededir.

| Parametre | Değer | Ne belirler |
|---|---|---|
| **donmuş (CFD):** `C4_VF_S`, `C4_OUT_RISE`, `C4_OUT_R`, `C4_OUT_RUN`, `C4_IN_H`, `C4_IN_W`, `C4_TONGUE`, `C4_IN_L`, `C1_VF_S` | 3.90, 7.871, 4.63, 4.63, 3.40, 2.912, 0.05, 3.0, 2.16 m | C2–C4 C4'ün CFD domeninin aynısı ([cyclone_C4.md](preheater/cyclone_C4.md), `cyclone.bas`, S 3.90): vorteks bulucu çatıdan 3.90 m aşağı (kesikli); gaz çıkış borusu (Ø4.63) çatının 7.87 m (1.70·VD; 14 Ekim 2026'ya kadar 5.79) üstüne çıkar, 90°'lik dirsek (eksende R 4.63, duvarları yay) ve 4.63 m yatay bacak; giriş 3.40 m derinliğinde bir volüt: 2.912 m genişliğinde düz kanal ve gövdeden 0.05 m (dil) dışarıda başlayan yarım tur Arşimet sarmalı. Kesitte volüt çatının altında bir bant olarak görünür; sarmal riserın karşı tarafında gövdeden ~1.5 m taşar. Çıkışın yatay yönü CFD'de riserın ters tarafınadır; çizimde bir sonraki siklona döner (siklonun çıkışını kendi ekseni etrafında döndürmek; akış aynı, kullanıcı kararı 13 Ekim 2026). C1'in vorteks bulucusu çatıdan 2.16 m aşağı. C5 bunların hepsinin 6.50/6.30 ile büyütülmüş kopyasıdır (`Kc`): vorteks bulucu Ø4.777, 4.02 m; çıkış borusu 8.12 m, dirsek R 4.777; volüt 3.508 m. Volütü kaz boynunun ters tarafındadır (kullanıcı kararı 14 Ekim 2026) |
| `STAGE_GAP` | 4.0 m | C1'in toz çıkışının C2'nin stub'ının en az bu kadar üstünde olması (R1'in Y'si C1'i zaten daha yukarı koyar). C2–C4'ün kotu artık bu paydan değil, alttaki kademenin CFD çıkışından gelir: her siklonun çatısı, alttakinin CFD dirseğinin üstü hizasındadır. 14 Ekim 2026'ya kadar C3 ve C2 bu kadar dirseğin üstündeydi; bu, CFD borusuyla dirsek arasına 4.87 m düz boru sokuyordu (CFD domeni bozuluyordu), kaldırıldı ve kule 14.6 m kısaldı (kullanıcı kararı) |
| `ZIG_DX` | 15.0 m | Hattın dış kolonunun (C4, C2) iç kolonundan (C5, C3) uzaklığı. Yatay bacağın yalnız ilk 4.63 m'si (C5'te 4.78) CFD domenidir, üstteki siklonun 3.0 m'lik giriş kanalı gövdenin içinde kalır; aradaki bacak serbesttir. Alt sınır: çıkış yüzü + 0.5 m + daralma + gövde yarıçapı, R4 için 14.6 m; ön kontrol zorlar. 20 m idi (farin borularını riserların yanından geçirmek için); farin uçlarla gösterilince kule kare gibi durduğu için 15 m'ye indi (kullanıcı kararı 14 Ekim 2026). 11 m'den 20'ye çıkmıştı |
| **donmuş (CFD):** `C1_RISER_X` … `C1_OUT_R` | CFD | Her C1, kendi CFD domeniyle aynı ([cyclone_C1.md](preheater/cyclone_C1.md), [riser_R1.md](preheater/riser_R1.md)); yükseklikler toz çıkışından: Ø2.171 riser kolu C1 ekseninden 6.843 m uzakta, 0.885'ten (domen tabanı) 8.385'e dik; 95°'lik, R 2.171 dirsek (CFD'deki gibi yuvarlak: duvarları eş merkezli iki yay); 1.5 m geçiş ve 5° aşağı eğimli 2.16 m'lik giriş kanalı gövdeye; farin oluğu 0.6 × 0.6, 60°, kol duvarını 5.385'te keser ve 1.0 m dışarı çıkar; gaz çıkışı çatının üstünde 3.0 m Ø2.40 boru, kolun ters tarafına R 3.6 m 180° dirsek (yuvarlak, iki yay) ve 3.0 m aşağı inen bacak |
| `R1_LEG_ON` | 0.5 m | C2'nin çıkış bacağının, CFD'nin 4.63 m'sinden sonra R1'in dirseğine kadar uzandığı yol. İki hattın uzak C1'lerinin çıkış dirsekleri kalsinatörün üstünde ~5.9 m arayla kalır. 1.55 m idi |
| `R1_BRANCH_HALF` | 2.75 m | R1'in Y'sinden çıkan iki kolun R1 ekseninden uzaklığı; ikiz C1'ler eksenden 9.593 m uzakta. İki farin oluğu kolların arasında birbirine bakar, ön kontrol birbirine değmemelerini zorlar |
| `GN_TO_C5_GAP` | 1.0 m | Kaz boynu inişi ile C5 gövdesi arasındaki boşluk. İniş, C5'in giriş kotunda bu boşluğu yatay geçerek gövdeye girer |
| `GN_BEND_LEG` | 0.5 | Kaz boynu inişinin C5'e dönerken 45° parçasının yatay boyu, kol çapı cinsinden. Kolla C5 gövdesi arasında 2.75 m olduğu için riserlardaki 1.0 sığmıyor; ön kontrol, ardından en az yarım kol yarıçapı yatay giriş kalmasını zorlar |
| `TA_BEND_R_OVER_D` | 1.5 | Tersiyer hava kanalının başlıktan kalsinatöre dönüşü: kaz boynundaki gibi geniş bir dirsek, eksende R 3.66 m, duvarları iki yay (kullanıcı kararı 14 Ekim 2026; önceden keskin köşeydi). Ön kontrol, dirseğin başlığın üstüne sığmasını ve tersiyer hava okunun dirsekten önce bitmesini zorlar |
| `C5_OVER_TA` | 1.75 m | C5'lerin toz çıkışının tersiyer hava kanalının üstünden en az bu kadar yukarıda olması. Tam boy C5 (gövde + koni 14 m) kaz boynu kolunun bittiği kottan asılınca kanala iniyordu; C5 bu kadar yukarıda durur, kol daha yukarıda biter |
| `MEAL_ENTRY_UP` | 1.5 m | Farinin riser'a, ayağının bu kadar üstünde girdiği yer: R2–R4'te çatının üstü, yani CFD çıkış borusunun içine (7.87 m'lik borunun alt kısmı) |

| `MEAL_SIDE_L` | 1.0 m | Riser'a giren farin hattının duvarın yanında indiği dik hattın duvardan uzaklığı; hat buradan 60° ile duvara girer |
| `MEAL_DROP` | 1.5 m | C1–C3'ün farininin toz çıkışından dik düştüğü boy; her hat siklondan önce düz çıkar, sonra 60° ile döner (kullanıcı kararı 14 Ekim 2026) |
| `MEAL_OVER_GAP` | 0.3 m | C2 ve C3'ün farini düz inişinden sonra 60° ile altındaki CFD çıkış dirseğinin üstünden dışarı çıkar; makro, eğimli parçanın dirseğin dış duvarına (tam daire, güvenli tarafta) bundan fazla yaklaşmasına izin vermez. 1.70·VD ile C2 / C3 dirseğin 2.9 m üstündedir, açıklık 0.40 / 0.41 m. 1.25·VD'de 0.9 m'ydi; düz iniş ancak 0.5 m, eğim 40° olabiliyordu |
| `MEAL_JOIN_DEG` | 50° | Yakın C1'in farininin, düz inişinden sonra uzak C1'inkine katılırken eğimi; R2'nin dirseğinden 5.5 m açık. 60°'de uzak C1'in hattına R2'ye döndüğü yerin altında varırdı |
| `C4_MEAL_DROP` / `C5_MEAL_DROP` | 3.0 / 1.0 m | C4 ve C5 farininin toz çıkışından dik düştüğü boy; ardından 1 m'lik (`MEAL_BEND`) bir dönüş parçası ve hedefe düz hat. C5'inki 1.0 m'den uzun olamaz: düz iniş TA kanalının 0.3 m üstünde bitmeli (ön kontrol). Bu düz hatlar farinin aktığından yatıktır (C4 ~16°, C5 ~34°): 2D izdüşümdür, 3D'de borular diktir |
| `CROSS_GAP` | 0.5 m | Farin hattının arkasından geçtiği dış hattın iki yanında bırakılan boşluk |
| `ID_FAN_L` | 2.5 m | Her C1 çıkışının inen bacağından aşağı "to ID fan" okunun boyu |
| `RM_L` | 0.8 m | Ham farin okunun her oluğun ucundan dışarı uzadığı boy; ok başı diğerlerinin yarısı (2 mm) |
| `KILN_AXIS_Z` | 10.0 m | Fırın giriş ekseninin kotu |
| `CHAMBER_MARGIN` | 1.0 m | Giriş odası ve başlık: fırının çevresinde bu payla bir kare. Şematiktir; [kiln_inlet_chamber.md](kiln/kiln_inlet_chamber.md)'de ölçü yok |
| `COOLER_W` / `COOLER_H` | 4.0 / 4.0 m | Izgara genişliği, FLS referans soğutucusunun (boy alandan çıkar: 29.9 m), ve soğutucu gövde yüksekliği |
| `COOLER_DROP` | 1.0 m | Soğutucunun tepesinin, deşarjdaki fırın kabuğunun altında kaldığı mesafe |
| `MEAL_INTO_CHAMBER` | 1.0 m | C5 farininin giriş odası tavanına, odanın yan yüzünden bu kadar içeride indiği yer |
| `FEED_LOWER` | 3.0 m | C4 farininin kalsinatöre, `calciner.bas`'ın besleme kotunun (bacak uçlarının 2 m altı) bu kadar altından girmesi. Yalnız topoloji içindir; CFD besleme boruları yerinde kalır |
| `KILN_FLOW_OFF` | 1.0 m | Fırın içindeki gaz ve malzeme çizgilerinin fırın ekseninden dik uzaklığı: gaz üstte, malzeme altta. Fırın kabuğunun (±2.4 m) içinde kalmalı; ön kontrol bunu zorlar |
| `PRIMARY_AIR_L` | 2.0 m | Primer havayı yalnızca belirten kısa okun boyu; ok başlığın ön duvarında biter |
| `SEC_AIR_DX` | 1.5 m | Sekonder havanın soğutucudan, fırının ucundan bu kadar içeride yükseldiği yer |
| `CLINKER_OUT_Z` | 3.5 m | Klinkerin soğutucunun ucundan indiği klinker taşımanın zeminin altındaki derinliği |
| `VENT_IN` | 3.0 m | Fazla soğutucu havasının soğutucunun ucundan bu kadar içeride, tavanından çıkması |
| `VENT_UP` | 4.0 m | Vent okunun soğutucunun tavanının üstünde çizildiği boy |
| `CLINKER_ON_GRATE` | 1.0 m | Klinker çizgisinin soğutucu tabanının üstündeki yüksekliği |
| `TA_ARROW_LONG` | 1.15 | Tersiyer hava okunun boyu: soğutucu ortasından başlığın tavanına olan yüksekliğin bu katı. Ok soğutucu ortasından (z 3.2) başlar ve kanalın içine, z 12.4'e kadar uzanır; ok ucu orada, çizgi okun ötesine geçmez. Kanalın dirseğine ulaşamaz; makro bunu kontrol eder |
| `SHEET_SCALE`, `X0`, `Y0` | 1:300; 0.215, 0.06 m | Sayfa ölçeği ve model (0, 0)'ın sayfadaki yeri. X0, C1'lerin dışa dönen çıkış dirsekleri sayfaya sığsın diye 0.20'den kaydı |
| `RULER_X` | 0.04 m | Kot cetvelinin sayfadaki yeri, çerçevenin içinde |
| `TEXT_H`, `ARROW_L`, `CAP_H` | 3.5, 4, 2 mm | Kâğıtta yazı yüksekliği, ok boyu, antetteki başlık yazısı |
| `FR_X0`…`FR_Y1`, `COL_X0` | 0.020–0.831 × 0.010–0.584 m; 0.651 m | Çerçeve ve sağ sütunun (lejant, liste, revizyon, antet) sol kenarı |
| `LEVEL_X` | 50 m | Kot işaretlerinin model x'i, sağ hattın sağında, dış C1'in çıkış bacağının dışında |

## Yerleşim

Kalsinatör ekseni x = 0'dadır. Sağ hat (R) +x'te, fırının üstünde durur; sol hat (L) −x'te, onun aynasıdır.

```
fırın giriş odası  |x| ≤ 3.4, tavan z 13.4; düz tabanı yok: tabanı fırının alt dudağından (3.4, 7.6)
                    odanın sol üst köşesine (−3.4, 13.4) çıkan 40.5°'lik bir rampa
kalsinatör          z 13.4 .. 46.530; Y kaz boynu: boyun eksende, kollar x = ±0.725'ten başlar, R 5.25 dirsekle döner,
                    x = ±11.225'ten C5'in giriş kotuna (z 36.872) iner ve yatay C5 gövdesine girer
iç kolon (C5, C3)   x = ±17.225    C5 kendi kolundan 1.0 m dışarıda
dış kolon (C4, C2)  x = ±32.225
riser'lar          R4 C5'in (x = ±17.225), R3 C4'ün (x = ±32.225), R2 C3'ün (x = ±17.225) çıkış borusu;
                    R1 x = ±20.93 (C2'nin çıkış bacağından dirsekle dik)
ikiz C1             x = ±11.34 ve ±30.52, R1'in iki yanında, birbirinin aynası; kolları x = ±18.18 ve ±23.68
toz çıkışları       C5 24.591 · C4 40.31 · C3 55.12 · C2 69.94 · C1 101.17; kule tepesi (C1 çıkış dirseklerinin tepesi) 120.41
tersiyer hava       z 21.621, Ø2.439
fırın               (3.4, 10.0) → (77.367, 7.781)
soğutucu            x 77.367 .. 107.267, z 0.381 .. 4.381
fırın başlığı       x 77.367 .. 84.167, z 4.381 .. 11.181
```

## Yollar

Her hattaki yollar aynıdır; sol hat sağın aynasıdır.

**Gaz:**
- başlık (brülör ucu) → fırın boyunca, eksenin 1.0 m üstünde → giriş odası (rampanın 1 m üstünden kalsinatör eksenine döner) → kalsinatör → kaz boynu → C5. Kaz boynu `calciner.bas`'taki gibi bir Y'dir: tavanın ortasından Ø4.95 boyun yükselir; tepesinde iki Ø3.50 kol başlar, her biri 180° dirsekle dışa döner ve iner. İki kolun dış duvarları boynun 3.6 m üstünde, eksende kesişir; çatal orasıdır. İniş, C5'in girişine ulaşınca riserlar gibi iki 45°'lik adımla döner: girişin 1.75 m (yarım kol çapı, `GN_BEND_LEG`) üstünde 45° döner, 45° ile girişin seviyesine iner ve 1 m yatay olarak C5 gövdesinin yan duvarına, üst duvarı tavan hizasında girer; bu, volütlü girişin yandan görünüşüdür. Kol Ø3.50'dir ve C5'in volüt girişinin yüksekliğine (3.508 m) sığar; ön kontrol bunu zorlar. Kolun inişi, C5 tersiyer hava kanalının üstünde durduğu için `calciner.bas`'taki kol ucundan (kalsinatörün yarı yüksekliği) daha yukarıda biter.
- C5 → R4 → C4: R2 / R3 gibi; R4, C5'in CFD çıkış borusunun kendisidir (Ø4.777, kullanıcı kararı 14 Ekim 2026): çatının üstünde 8.12 m dik boru, hemen ardından R 4.777 dirsek (C4'ün çatı kotunda) ve yatay bacakla (çıkış yüzünden sonra 0.92 m serbest) C4'e girer; bacağın alt duvarı son 1.38 m'de 45° ile 3.40 m'lik volüt girişine yükselir. Eski 45°'lik daralma ve iki 45° dönüş kalktı.
- C4 → R3 → C3, C3 → R2 → C2: riser, C4 / C3'ün CFD çıkışının kendisidir (Ø4.63; kullanıcı kararı 13 Ekim 2026, ayrı riser kalktı ve yol kısaldı). Çıkış CFD domeninin birebir aynısıdır (14 Ekim 2026): çatının üstünde 7.87 m dik boru (siyah, siklonun parçası), hemen ardından 90° dirsek (R 4.63, duvarları yay) ve yatay bacak (çıkış yüzünden sonra 1.36 m serbest). CFD'nin 4.63 m'lik bacağından sonrası domenin dışındadır; bacak oradan düz devam eder (bir ara orada 45° ile 1.5 m yükselip katları açıyordu; kıvrım istenmediği için kalktı, 14 Ekim 2026). Bacağın üst duvarı üst siklonun çatı hizasındadır, alt duvarı son 1.23 m'de 45° ile 3.40 m'lik volüt girişine yükselir; üst siklonun kotu buradan gelir.
- C2 → R1 → ikiz C1: R1 C2'nin CFD çıkışından (bacağı kalsinatöre doğru) geçer. Bacak CFD'nin 4.63 m'sinden 1.55 m (`R1_LEG_ON`) daha uzanır ve bir dirsekle yukarı döner: üst duvarı düz gidip R1'in C2 tarafındaki duvarı olarak dik yükselir, alt duvarı 45° ile R1'in öbür duvarına çıkar; dirsek Ø4.63'ten Ø3.07'ye daralır (kullanıcı kararı 13 Ekim 2026; eski daralma + 45° + 0.5 m dik kısım bacağa bağlanmıyordu). R1'in C2 tarafındaki duvarı bacağın üstünde 0.5 m dik yükselir (`R1_UP_MIN`; C1 kademesi buna göre yükselir), öbür duvarı 2.06 m. Sonra R1 45°'lik düz parçalardan bir Y ile iki kola ayrılır: R1'in duvarları 45° ile dışa açılır, kolların iç duvarları R1 eksenindeki çataldan 45° ile yükselir; her kol Y boyunca kendi çapındadır (Ø2.171, R1'in alanının yarısı). Kollar Y'den sonra, tam C1 CFD domeninin tabanında (toz çıkışının 0.885 m üstü) dik başlar. Oradan yukarısı her C1 için CFD domeninin aynısıdır: dik kol, 95° dirsek, geçiş ve 5° eğimli giriş kanalı (bkz. `C1_RISER_X` … satırı). İkizler birbirinin aynasıdır: kollar ortada, gaz çıkış dirsekleri dışa döner. Aynalanmış akış aynı çözümdür, yalnız girdap ters yönde döner. Y CFD domeninin altında kaldığı için CFD sonuçları geçerlidir; tek fark kolun tabanına gelen hız profilinin tam düzgün olmamasıdır (CFD düzgün profil verir).
- ikiz C1 → ID fan: her C1'in gaz çıkışı CFD'deki gibi çatının üstünde 3.0 m yükselir, kolun ters tarafına 180° döner ve çatı kotuna iner; oradan aşağı bir "to ID fan" oku

**Farin:**
- ham farin → C1 kolları: CFD'deki gibi her kolun C1'den uzak tarafındaki 60°'lik oluktan (0.6 × 0.6 m, toz çıkışının 5.385 m üstü); oluk kapalı uçlu çizilir, içinden küçük başlı bir ok kol duvarına iner, okun ucunda küçük "RM" yazılıdır. Hat başına iki, toplam dört besleme
- Farin hatları tam çizilir; arkasından geçtiği siklonda ya da TA kanalında kırılır (bkz. "Farin hatları tam, arkadan geçtiği yerde kırık").
- Uzak C1 → R2, C2 → R3, C3 → R4: her siklon iki kademe altındaki riser'ı, yani C3 / C4 / C5'in CFD çıkış borusunu besler. Hat borunun dirseğin ters tarafına gelir, duvarın 1 m yanında (`MEAL_SIDE_L`) iner ve 60° ile boruya, çatının 1.5 m üstünden (`MEAL_ENTRY_UP`), CFD borusunun alt kısmına girer. CFD gaz-only'dir; farin yükü analitik hesaptadır, bu yüzden giriş yeri CFD çözümünü değiştirmez.
  - Uzak C1'in hattı toz çıkışından 1.5 m düşer, 60° ile R2'nin yanına geçer ve 19.1 m iner; hiçbir şeyi kesmez.
  - C2 ve C3 kendi riser'larının tam üstündedir: hat toz çıkışından 1.5 m düşer, 60° ile dirseğin üstünden dışarı çıkar (0.40 / 0.41 m açık), sonra iner. C3'ün hattı kaz boynu inişinden 0.86 m açıktadır.
  - 60° eğim, kalsinatör besleme borularının eğimidir (Fidaros 2007). Boru dik riser duvarıyla 30° yapar, yani farin duvara yatık, neredeyse teğet kayarak girer.
  - Tesislerde farin, riser'a alttaki siklonun hemen üstünden bu şekilde verilir.
- Yakın C1 (hattın dış ucundaki, C2'nin üstündeki) → uzak C1'in hattı: toz çıkışından 1.5 m düşer, 50° ile (`MEAL_JOIN_DEG`) C2'nin çıkış dirseği ve R1 dirseğinin arkasından geçer (kırık) ve uzak C1'in R2'nin yanında inen hattına katılır; R2'nin dirseğinden 5.5 m açıktır. İki C1'in farini tek boruyla R2'ye girer (kullanıcı kararı 14 Ekim 2026).
- C4 → kalsinatör: 3 m dik düşer, 1 m'lik dönüş parçası ve kalsinatör duvarına z 26.53'te (`calciner.bas`'ın besleme kotunun 3 m altı, `FEED_LOWER`) düz hat; C5'in konisinin arkasından geçer (kırık). Her hattın C4'ü kendi taraftaki besleme borusunu besler.
- C5 → giriş odasının tavanı: 1.0 m dik düşer, dönüş parçası ve tavana, kenarından 1 m içeride (`MEAL_INTO_CHAMBER`) düz hat; kalsinatör konisinin altından geçer. Sağ hattaki TA kanalının arkasından geçer (kırık), soldaki hiçbir şeyi kesmez.
- Giriş odasında farin birikmez: düz taban yerine fırının alt dudağından odanın sol üst köşesine çıkan bir rampa var, 40.5° (Ø4.0 fırınla 39.8°'ydi). Bu, farinin yığılma açısı (~40°), yani kayabildiği sınır; makro 39°'nin altına izin vermez. İki C5'in farini rampaya düşer ve fırına kayar. Eski düz taban fırın ağzının 1 m altındaydı ve sol yarısı fırından 5 m uzak bir ölü bölgeydi
- giriş odası → fırın → ızgaralı soğutucu (klinker): fırın ağzından başlar, fırın boyunca eksenin 1.0 m altında gazın tersine akar, başlıkta soğutucuya düşer ve ızgara boyunca ilerler. Fırın içindeki iki paralel ve ters oklu çizgi karşı akışı gösterir
- ızgaralı soğutucu → klinker taşıma: klinker soğutucunun ucundan dik iner, tabanından çıkar ve zeminin 3.5 m altında, "to clinker transport" yazısının yanında bir okla biter. Sağa değil aşağı iner, çünkü sağda antet var

**Hava:**
- primer hava → ana brülör: yalnızca belirtilir; başlığın ön duvarına, fırın gazının (kırmızı) başladığı kotta dokunan kısa bir ok; çizgi okun ucunda biter
- soğutucu → başlık (sekonder hava): başlığın altında soğutucudan yükselir ve fırının ucuna, fırın gazının başladığı noktaya girer. GAZ katmanında (kırmızı) çizilir, çünkü fırının içinde fırın gazı olarak devam eden akım odur. Fırının içinde ayrı çizilmez: fırın gazı, primer ve sekonder havanın brülörde yanmış hâlidir
- Çizimde "primary air" başlığın dışında, primer hava hattının altında; "secondary air" fırının içinde, fırın gazı ile klinker çizgisinin arasında yazılıdır
- soğutucu → başlık → tersiyer hava kanalı → kalsinatör (GAZ katmanında, kırmızı; sıcak hava): tersiyer hava soğutucudan başlığın içinden dik bir okla yükselir ve başlığın tepesindeki kanala girer; kanal dik yükselir, R 3.66 m'lik dirsekle (`TA_BEND_R_OVER_D`) yatay döner. Kanal kalsinatöre koni tepesinde (z 21.621'de) girer. Bu kot şematiktir; kalsinatör CFD makrosunun 6. adımı (TA kanalı) kendi yerini belirleyecek.
- soğutucu → vent (fazla hava, GAZ katmanında, kırmızı; hâlâ sıcak): soğutucunun ucundan 3 m içeride tavanından dik bir okla çıkar, "to cooler vent" yazısına gider

## Doğrulama

Makronun ön kontrolleri:
- R1 ikiz C1'lerin arasına sığıyor ve C2'nin gaz çıkışından dar
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

Son doğrulanmış çalıştırma 14 Ekim 2026 (CFD kilidi; C4 / C5 çıkış borusu 1.70·VD; dört C1 dahil bütün farin hatları tam, arkadan geçtiği yerde kırık; TA dirseği; "CAL" etiketi). Sayfada 241 not vardır. GAZ'daki 2 ek çizgi lejanttaki kırık hat örneğinin kanalıdır. GIZLI'daki 24 çizgi on iki vorteks bulucunun (her hatta C2–C5 ve iki C1) duvarları. Bu sayılar okları, lejantı, tabloları ve anteti içerir. OLCU'daki 5 yay grid balonları, GAZ'daki 38 yay kaz boynunun (4), dört C1'in kol ve çıkış dirseklerinin (16), sekiz C2–C5 çıkış dirseğinin (16) ve TA dirseğinin (2) duvarlarıdır. Çizgilerin kâğıttaki kapsamı da çizildiği kapsama 0.1 mm içinde oturmalı.

1/√2 ölçekli sürüm bir Python betiğiyle de kurulmuştu; o betik, hiçbir kanal kenarının ya da farin hattının kendi kaynağı ya da hedefi olmayan bir ekipman dış hattını kesmediğini doğruladı. Bilinçli istisnalar, ekipmanın içinden geçen akış çizgileridir (fırın → giriş odası → kalsinatör, soğutucu → başlık → fırın, giriş odası → fırın → soğutucu klinker yolu). Farin hatları yalnız arkasından geçtikleri yerlerde (yakın C1 → C2'nin çıkış dirseği ve R1 dirseği, C4 → C5'in konisi, sağ C5 → TA kanalı) kesişir ve orada kırılır; bu Python'da da denetlendi (14 Ekim 2026).

Ham farin R1'e, kendi hedefine girer. Betik ayrıca etiketlerin yaklaşık metin kutularını taradı: hiçbir etiket bir çizgiyle ya da başka bir etiketle çakışmıyor.

Çıktılar `geometry/output/2500/` altında:
- çizim `plant_topology_2d.SLDDRW`
- `plant_topology_2d.pdf`
- tam log `plant_topology_2d_build.log`
