# Tesis topolojisi (2D şema)

Makro: [`geometry/macros/plant_topology_2d.bas`](macros/plant_topology_2d.bas). Referans hat: 2500 t/d.

**CFD girdisi değildir.** Bu, tesisin topolojisini göstermek için çizilmiş gerçek ölçekli bir 2D şemadır: hangi ekipman var, nerede duruyor, gaz, farin ve hava hangi yoldan akıyor. `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır.

Önceki 3D topoloji modeli (`plant_topology.bas`, tek hatlı, çok gövdeli) kaldırıldı. Yerine bu 2D şema geldi; 2D daha okunur ve çakışma kısıtı taşımaz (kullanıcı kararı, 5 Ekim 2026).

## Ne çizilir

Bir SolidWorks **çizim sayfası**: A1 yatay (841 × 594 mm), ölçek **1:300**. Model koordinatları (x yatay, z kot, metre) sayfaya `P(x, z) = (X0 + x/300, Y0 + z/300)` ile yerleşir. Ölçek önce 1:200, sonra 1:250 idi. Hatlar tam 2500 ölçüsüne çıkınca kule ~125 m oldu ve A1'e 1:250'de sığmadığı için 1:300'e geçildi (12 Ekim 2026). Stub yarıya inince kule 117.4 m oldu; ölçek 1:300'de kaldı.

İlk sürüm bir parça sketch'iydi. Renkler orada görünmedi, çünkü sketch'in durum rengi özel rengi bastırıyordu. Etiketler 1 m yükseklikte okunmuyordu, her köşede de nokta yığını vardı. Çizim belgesine bu yüzden geçildi (kullanıcı kararı, 5 Ekim 2026).

- **Ekipman, gerçek kesit dış hatlarıyla:** siklonlar (toz çıkışı, koni, gövde, tavan, gaz çıkış stub'ı), kalsinatör (boğaz, koni, gövde), fırın giriş odası, fırın, soğutucu, fırın başlığı.
- **Akışın geçtiği duvarlar açıktır:** fırının iki ucu (giriş odasına ve başlığa açılır), kalsinatör boğazı (giriş odasının tavanı), kaz boynu kollarının kalsinatör tavanındaki ağızları, tersiyer hava kanalının başlık tavanındaki ve kalsinatör duvarındaki ağızları, başlığın altı (soğutucuya açık), her siklonun toz çıkışı, gaz çıkış stub'ının tepesi ve girişinin geldiği taraftaki gövde duvarı. Riser'lar stub'ın üstünde açık başlar; yalnız stub'ın dış duvarının üstünde kapakları vardır. Açıklığın yanında kalan, `MIN_SEG`'ten (0.05 m) kısa duvar parçası çizilmez. Bütün siklonlarda giriş tavandan aşağı iner; gövde duvarı yalnız kanalın yüksekliği boyunca açıktır, altında kapalı devam eder. Tek çizgili yollar (farin, egzoz, primer hava) duvarda biter.
- **Ana kanallar gerçek çapında, çift çizgiyle:** R1–R4, kaz boynu ve tersiyer hava kanalı. Kenarlar eksenin w/2 iki yanındadır; köşeler kenarların kesişiminde birleşir.
- **Diğer yollar tek çizgiyle, eksen boyunca:** farin hatları, C1 egzozu, ikincil hava, fırın → kalsinatör gazı.
- **Akış okları:** her yolun en uzun parçasının ortasında, akış yönünde. Çizimden çıkan ya da yalnızca bir akımı belirten yollarda ("to ID fan", "to cooler vent", "to clinker transport", primer hava, tersiyer hava oku) ok yolun ucundadır; okun ötesinde çizgi kalmaz.
- **Kesişmeler:** bir farin hattı bir gaz kanalını kestiği yerde kırılır: kanalın içinde ve kenarlarının `CROSS_GAP` (0.5 m) ötesinde çizilmez, kanalın arkasından geçtiği okunur. Makro her kanalı kapalı bir dış hat olarak kaydeder: çizilen kenarları (`DuctEdge`) ve açık uçlarını kapatan, çizilmeyen kenarları (`UnseenEdge`; stub ağzı, kanal uçları, R1'in C1'lere açılan uçları). C5'in kesiti de kapalı bir dış hat olarak kaydedilir; C4 farini onun arkasından geçer. Farin hatları bu dış hatlarla kesilir (`PathM`): her kesişme hattı içeri / dışarı çevirir ve bu durum hattın bir sonraki parçasına taşınır. Bir hattın yalnız ucunun değdiği kenar (riser duvarına giren farin) sayılmaz; bir kanala giren, `CROSS_GAP`'ten kısa ara parça çizilmez; kanalın arkasında biten bir farin hattı makroyu durdurur. Ok, çizilen en uzun parçaya konur. Lejantta bir örneği var.
- **Şematik not:** lejantta, giriş odasının ölçüsünün kaynaksız olduğu ve farin borularının 2D izdüşümü olduğu (C4 ve C5 boruları ve oda rampası 3D yerleşimde daha diktir) yazılıdır.
- **Etiketler:** not olarak, kâğıtta 3.5 mm yükseklikte. Siklon adları gövdenin içinde (oradan hiçbir yol geçmez), riser adları kanalın içinde. Sayılar yerel ayardan bağımsız olarak noktalı ve sabit ondalıklı yazılır ("2.440").
- **Kot cetveli:** solda, çerçevenin içinde, 0'dan 100 m'ye; her 10 m'de bir çentik ve kot. Zemin çizgisi cetvelden başlar.
- **Lejant ve notlar:** renkler, ok, çift ve tek çizginin, kırılmanın anlamı; altında numaralı notlar (birimler, hat başına ölçek, şematik/2D izdüşüm, CFD girdisi olmadığı) ve 10 m'lik ölçek çubuğu.
- **Çerçeve (ISO 5457):** A1, sol 20 mm, diğer kenarlar 10 mm; 12 × 8 bölge, üst ve altta 1–12, yanlarda A–H.
- **Antet (ISO 7200):** 180 mm, sağ altta. Belge türü, başlık ve ek başlık, ölçek, birim, tarih, dil, sayfa, durum, teknik referans, kaynak. Çizen, onaylayan, sorumlu birim, çizim numarası ve revizyon alanları boş bırakılır (kullanıcı kararı); elle doldurulur.
- **Revizyon tablosu:** antetin üstünde, Rev / Description / Date / By başlığı ve iki boş satır.
- **Ekipman etiketleri ve listesi:** siklonlar (C1–C5, L/R) ve riser'lar (R1–R4) adlarıyla; diğerleri etiketle: CAL kalsinatör, GN kaz boynu, TAD tersiyer hava kanalı, KIC giriş odası, KLN fırın, HD başlık, CLR soğutucu. Sağ sütundaki ekipman listesi her etiketin adını, adedini (iki hat birlikte), ölçüsünü ve dayanağını (CFD, yayınlanmış, türetilmiş, şematik) verir; ölçüler çizimin kullandığı sabitlerden yazılır.
- **Kot işaretleri:** sağ hattın sağında (x = 33) her kademenin toz çıkışı, kalsinatör tavanı ve kule tepesi; giriş odasının solunda fırın ekseni. Üçgen sembol, seviye çizgisi ve "+36.30 C4 dust outlet" biçiminde yazı.
- **Grid ve ölçüler:** kulenin üstünde beş kolon ekseni (1 dış L, 2 iç L, 3 kalsinatör, 4 iç R, 5 dış R) balonlarıyla; aralarındaki mesafeler (8.000 / 13.289 / 13.289 / 8.000) ve toplam (42.579) eğik çizgi uçlu ölçülerle.
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
| R1 / R2 / R3 / R4 (hat başına) | Ø3.07 / 3.35 / 3.45 / 3.60 | catalog.md (HFC2500) |
| Kalsinatör | Ø6.74, 30.0 m (koni dahil), boğaz Ø3.130, koni 65° | calciner.md (PF5000) |
| Kaz boynu | Y: boyun Ø4.95, 2 kol × Ø3.50, kalsinatörün yarı yüksekliğinde biter | calciner.md, gooseneck.md |
| Tersiyer hava kanalı | Ø2.439 (türetilmiş) | calciner.md |
| Fırın | Ø4.8 × 74 m, %3 eğim | kiln.md (PF5000) |
| Soğutucu | ızgara alanı 119.6 m² | cooler.md (PF5000) |

Kalsinatör, Y kaz boynu, TAD, fırın ve soğutucu 5000 t/d'nindir: PF5000'den, ya da onun ölçülerinden türetilmiş ([calciner.md](calciner/calciner.md), [kiln.md](kiln/kiln.md), [cooler.md](cooler/cooler.md); 12 Ekim 2026). Giriş odası ve başlık şematiktir, fırının çevresinde bir paydır. Twin 5000 t/d beslemesiyle çalışır; hangi ekipmanı hangi akış hacmiyle hesapladığı [fluid_volumes.md](fluid_volumes.md)'dedir.

Siklon CFD dokümanları (`cyclone_C1–C5.md`) ve `cyclone.bas` aynı ölçüleri kullanır; çizim onlardan ayrılmaz.

## Şematik parametreler (kaynaksız; yalnız yerleşim için)

| Parametre | Değer | Ne belirler |
|---|---|---|
| `STUB_OVER_VD` | 0.5 | Siklon gaz çıkış stub'ının tavan üstündeki boyu, vorteks bulucu çapı cinsinden. 1.0 idi; kule 128 m çıkınca yarıya indi (kullanıcı kararı, 12 Ekim 2026). Riser boyları (~19.5 m) zaten FLS Tablo 7'nin 19.4–21.4 m'siyle uyumluydu; şematik pay stub'daydı |
| `STAGE_GAP` | 4.0 m | Bir siklonun toz çıkışının, alttaki kademenin tepesinden yüksekliği. En geniş riser'dan (Ø3.60) büyük olmalı; ön kontrol bunu zorlar |
| `ZIG_DX` | 11.0 m | Hattın dış kolonunun (C4, C2) iç kolonundan (C5, C3) uzaklığı. Riser'lar iki kolonun ortasından çıkar; bu aralık en geniş riser (Ø3.60) ile iki yandaki siklonun yarıçapına yetmeli. Ön kontrol bunu zorlar |
| `C1_TWIN_GAP` | 4.0 m | İkiz C1 gövdeleri arasındaki boşluk. R1 (Ø3.07) bu boşluktan yükselir; ön kontrol sığmasını zorlar |
| `GN_TO_C5_GAP` | 1.0 m | Kaz boynu inişi ile C5 gövdesi arasındaki boşluk. İniş, C5'in giriş kotunda bu boşluğu yatay geçerek gövdeye girer |
| `C5_OVER_TA` | 1.75 m | C5'lerin toz çıkışının tersiyer hava kanalının üstünden en az bu kadar yukarıda olması. Tam boy C5 (gövde + koni 14 m) kaz boynu kolunun bittiği kottan asılınca kanala iniyordu; C5 bu kadar yukarıda durur, kol daha yukarıda biter |
| `MEAL_JOIN_DEG` | 50° | Dış C1'in farin borusunun, dik iniş ve dirsekten sonra iç C1'in borusuna katılırken indiği eğim. 60°'de R2'nin köşesini kesiyordu |
| `C1_MEAL_DROP` | 1.0 m | Dış C1 farininin dirsekten önceki dik inişi |
| `MEAL_ENTRY_UP` | 1.5 m | Farinin riser'ın düşey kısmına, yatay parçasının üst kenarının bu kadar üstünde girdiği yer |
| `EXHAUST_L` | 10.0 m | C1 egzozunun ID fana doğru çizilen boyu |
| `RAW_L` | 6.0 m | Ham farin hattının dışarıdan çizildiği uzaklık |
| `KILN_AXIS_Z` | 10.0 m | Fırın giriş ekseninin kotu |
| `CHAMBER_MARGIN` | 1.0 m | Giriş odası ve başlık: fırının çevresinde bu payla bir kare. Şematiktir; [kiln_inlet_chamber.md](kiln/kiln_inlet_chamber.md)'de ölçü yok |
| `COOLER_W` / `COOLER_H` | 4.0 / 4.0 m | Izgara genişliği, FLS referans soğutucusunun (boy alandan çıkar: 29.9 m), ve soğutucu gövde yüksekliği |
| `COOLER_DROP` | 1.0 m | Soğutucunun tepesinin, deşarjdaki fırın kabuğunun altında kaldığı mesafe |
| `MEAL_INTO_CHAMBER` | 1.0 m | C5 farininin giriş odası tavanına, odanın yan yüzünden bu kadar içeride indiği yer |
| `C4_MEAL_DROP` | 3.0 m | C4 farininin, kalsinatöre dönmeden önce toz çıkışından dik indiği boy |
| `MEAL_BEND` | 1.0 m | C4 ve C5 farininin dik inişinden sonra, dönüşün açıortayında giden ara dirsek parçası; dönüşü ikiye böler |
| `CROSS_GAP` | 0.5 m | Farin hattının kestiği kanalın kenarlarının ötesinde bırakılan boşluk (1:300'de 1.7 mm) |
| `C5_MEAL_DROP` | 0.5 m | C5 farininin dik inişi; TA kanalının üstünde biter |
| `FEED_LOWER` | 3.0 m | C4 farininin kalsinatöre, `calciner.bas`'ın besleme kotunun (bacak uçlarının 2 m altı) bu kadar altından girmesi. Yalnız topoloji içindir; CFD besleme boruları yerinde kalır |
| `KILN_FLOW_OFF` | 1.0 m | Fırın içindeki gaz ve malzeme çizgilerinin fırın ekseninden dik uzaklığı: gaz üstte, malzeme altta. Fırın kabuğunun (±2.4 m) içinde kalmalı; ön kontrol bunu zorlar |
| `PRIMARY_AIR_L` | 2.0 m | Primer havayı yalnızca belirten kısa okun boyu; ok başlığın ön duvarında biter |
| `SEC_AIR_DX` | 1.5 m | Sekonder havanın soğutucudan, fırının ucundan bu kadar içeride yükseldiği yer |
| `CLINKER_OUT_Z` | 3.5 m | Klinkerin soğutucunun ucundan indiği klinker taşımanın zeminin altındaki derinliği |
| `VENT_IN` | 3.0 m | Fazla soğutucu havasının soğutucunun ucundan bu kadar içeride, tavanından çıkması |
| `VENT_UP` | 4.0 m | Vent okunun soğutucunun tavanının üstünde çizildiği boy |
| `CLINKER_ON_GRATE` | 1.0 m | Klinker çizgisinin soğutucu tabanının üstündeki yüksekliği |
| `TA_ARROW_LONG` | 1.15 | Tersiyer hava okunun boyu: soğutucu ortasından başlığın tavanına olan yüksekliğin bu katı. Ok soğutucu ortasından (z 3.2) başlar ve kanalın içine, z 12.4'e kadar uzanır; ok ucu orada, çizgi okun ötesine geçmez. Kanalın dirseğine ulaşamaz; makro bunu kontrol eder |
| `SHEET_SCALE`, `X0`, `Y0` | 1:300; 0.20, 0.06 m | Sayfa ölçeği ve model (0, 0)'ın sayfadaki yeri |
| `RULER_X` | 0.04 m | Kot cetvelinin sayfadaki yeri, çerçevenin içinde |
| `TEXT_H`, `ARROW_L`, `CAP_H` | 3.5, 4, 2 mm | Kâğıtta yazı yüksekliği, ok boyu, antetteki başlık yazısı |
| `FR_X0`…`FR_Y1`, `COL_X0` | 0.020–0.831 × 0.010–0.584 m; 0.651 m | Çerçeve ve sağ sütunun (lejant, liste, revizyon, antet) sol kenarı |
| `LEVEL_X` | 33 m | Kot işaretlerinin model x'i, sağ hattın sağında |

## Yerleşim

Kalsinatör ekseni x = 0'dadır. Sağ hat (R) +x'te, fırının üstünde durur; sol hat (L) −x'te, onun aynasıdır.

```
fırın giriş odası  |x| ≤ 3.4, tavan z 13.4; düz tabanı yok: tabanı fırının alt dudağından (3.4, 7.6)
                    odanın sol üst köşesine (−3.4, 13.4) çıkan 40.5°'lik bir rampa
kalsinatör          z 13.4 .. 46.530; Y kaz boynu: boyun eksende, kollar x = ±0.725'ten başlar, R 5.25 dirsekle döner,
                    x = ±11.225'ten C5'in giriş kotuna (z 36.872) iner ve yatay C5 gövdesine girer
iç kolon (C5, C3)   x = ±17.225    C5 kendi kolundan 1.0 m dışarıda
dış kolon (C4, C2)  x = ±28.225
riser'lar           x = ±22.725    iki kolonun ortası
ikiz C1             x = ±18.565 ve ±26.885 (R1 aralarından yükselir)
toz çıkışları       C5 24.591 · C4 45.011 · C3 64.926 · C2 84.841 · C1 104.756; kule tepesi 117.396
tersiyer hava       z 21.621, Ø2.439
fırın               (3.4, 10.0) → (77.367, 7.781)
soğutucu            x 77.367 .. 107.267, z 0.381 .. 4.381
fırın başlığı       x 77.367 .. 84.167, z 4.381 .. 11.181
```

## Yollar

Her hattaki yollar aynıdır; sol hat sağın aynasıdır.

**Gaz:**
- başlık (brülör ucu) → fırın boyunca, eksenin 1.0 m üstünde → giriş odası (rampanın 1 m üstünden kalsinatör eksenine döner) → kalsinatör → kaz boynu → C5. Kaz boynu `calciner.bas`'taki gibi bir Y'dir: tavanın ortasından Ø4.95 boyun yükselir; tepesinde iki Ø3.50 kol başlar, her biri 180° dirsekle dışa döner ve iner. İki kolun dış duvarları boynun 3.6 m üstünde, eksende kesişir; çatal orasıdır. İniş, C5'in giriş kotunda dirsek yapar ve yatay olarak C5 gövdesinin yan duvarına, üst duvarı tavan hizasında girer; bu, volütlü girişin yandan görünüşüdür. Kol Ø3.50'dir ve C5'in volüt girişinin yüksekliğine (3.508 m) sığar; ön kontrol bunu zorlar. Kolun inişi, C5 tersiyer hava kanalının üstünde durduğu için `calciner.bas`'taki kol ucundan (kalsinatörün yarı yüksekliği) daha yukarıda biter.
- C5 → R4 → C4 → R3 → C3 → R2 → C2: riser, alttaki siklonun gaz çıkış stub'ının tepesinde yatay kanal olarak başlar. Kolonların ortasına gider, yükselir ve üstteki siklonun yanından girer: kanalın üst duvarı çatı hizasındadır (CFD katılarında giriş çatıdan aşağı iner: C1 yarığı, C2–C5 volütü).
- C2 → R1 → ikiz C1: R1 iki C1'in arasında yükselir. İkiye ayrılır; her kolun alanı R1'in yarısıdır (Ø2.171, CFD'deki C1 riser'ı).
- ikiz C1 → egzoz: iki stub birleşir ve hattın dışına, "to ID fan" ucuna gider

**Farin:**
- ham farin → R1: 60° ile aşağı inip R1'in yatay parçasının dış ucuna, C2'nin gaz çıkışının hemen üstüne girer
- C2 → R3, C3 → R4, iç C1 → R2: farin önce kendi kolonunda **düşey iner**, sonra **60°'lik bir parçayla** riser'ın düşey kısmına yan duvarından girer.
  - C3'ün farini R4'e, C4 farin hattının R4'ü kestiği kotun en az 1 m üstünden girer; iki farin borusu kesişmez.
  - Giriş noktası, riser'ın alttaki siklonun üstündeki yatay parçasının 1.5 m üstündedir (`MEAL_ENTRY_UP`).
  - 60° eğim, kalsinatör besleme borularının eğimidir (Fidaros 2007). Boru dik riser duvarıyla 30° yapar, yani farin duvara yatık, neredeyse teğet kayarak girer.
  - Tesislerde farin, riser'a alttaki siklonun hemen üstünden bu şekilde verilir.
- dış C1 → iç C1'in borusu: dış C1, C2'nin ve R1'in C2 stub'ı üstündeki yatay kanalının hemen üstünde durduğu için düşey inemez. Farini C4 gibi 1 m dik iner, 1 m'lik dirsekten geçer ve 50° ile iç C1'in borusuna katılır; ikiz C1'lerin farini birleşir. Hat R1'in yatay kanalının arkasından geçer ve orada kırılır.
- C4 → önce 3.0 m dik iner, 1 m'lik bir ara dirsekten geçer, sonra düz hatla kalsinatör duvarına, z 24.943'e (`calciner.bas`'ın besleme kotunun 3 m altı) iner; her hattın C4'ü kendi taraftaki besleme borusunu besler. Hat C5'in arkasından geçer ve orada kırılır (tam ölçekte kaz boynu inişinin altından geçer). Kesitte ~37°'dir: bu bir 2D izdüşümüdür. Çizimde iki hat yan yana dizildiği için yatay mesafe şişer; gerçekte C4 farin borusu C5'in yanından, başka bir derinlikte ve dik geçer. Bir ara C4'ü 9.2 m yükseltip kesitte 45° verilmişti; bu R4'ü ~23 m'ye uzatıyordu (R2, R3 ~12.6 m), kademeler yeniden `STAGE_GAP`'e indirildi.
- C5 → giriş odasının tavanı: C4 gibi dik iner (0.5 m), 1 m'lik dirsekten geçer, düz hatla odanın tavanına, kenarından 1 m içeride iner. Bu hat kesitte ~36°'dir, farinin akabileceğinden (~40–45°) yatıktır. Bu bir 2D izdüşümüdür: çizimde iki hattın C5'leri fırın ekseni boyunca sağa sola dizilir, gerçekte ise odanın iki yanında, fırın eksenine dik durur; gerçek boru daha kısa ve diktir. Kesitte 40°'yi zorlamak odayı ±4.6 m'ye, 45° ±6.8 m'ye genişletiyordu (fırın doğrultusunda kalsinatörden geniş, gerçekçi değil); oda bu yüzden şematik kaldı: fırının çevresinde 1 m pay (Ø4.8 fırınla ±3.4 m). Gerçek eğim, oda ve borunun ölçüleri bir kaynaktan gelince belirlenir. Sağdaki C5'te hat TA kanalını çapraz keser
- Giriş odasında farin birikmez: düz taban yerine fırının alt dudağından odanın sol üst köşesine çıkan bir rampa var, 40.5° (Ø4.0 fırınla 39.8°'ydi). Bu, farinin yığılma açısı (~40°), yani kayabildiği sınır; makro 39°'nin altına izin vermez. İki C5'in farini rampaya düşer ve fırına kayar. Eski düz taban fırın ağzının 1 m altındaydı ve sol yarısı fırından 5 m uzak bir ölü bölgeydi
- giriş odası → fırın → ızgaralı soğutucu (klinker): fırın ağzından başlar, fırın boyunca eksenin 1.0 m altında gazın tersine akar, başlıkta soğutucuya düşer ve ızgara boyunca ilerler. Fırın içindeki iki paralel ve ters oklu çizgi karşı akışı gösterir
- ızgaralı soğutucu → klinker taşıma: klinker soğutucunun ucundan dik iner, tabanından çıkar ve zeminin 3.5 m altında, "to clinker transport" yazısının yanında bir okla biter. Sağa değil aşağı iner, çünkü sağda antet var

**Hava:**
- primer hava → ana brülör: yalnızca belirtilir; başlığın ön duvarına, fırın gazının (kırmızı) başladığı kotta dokunan kısa bir ok; çizgi okun ucunda biter
- soğutucu → başlık (sekonder hava): başlığın altında soğutucudan yükselir ve fırının ucuna, fırın gazının başladığı noktaya girer. GAZ katmanında (kırmızı) çizilir, çünkü fırının içinde fırın gazı olarak devam eden akım odur. Fırının içinde ayrı çizilmez: fırın gazı, primer ve sekonder havanın brülörde yanmış hâlidir
- Çizimde "primary air" başlığın dışında, primer hava hattının altında; "secondary air" fırının içinde, fırın gazı ile klinker çizgisinin arasında yazılıdır
- soğutucu → başlık → tersiyer hava kanalı → kalsinatör (GAZ katmanında, kırmızı; sıcak hava): tersiyer hava soğutucudan başlığın içinden dik bir okla yükselir ve başlığın tepesindeki kanala girer. Kanal kalsinatöre koni tepesinde (z 21.621'de) girer. Bu kot şematiktir; kalsinatör CFD makrosunun 6. adımı (TA kanalı) kendi yerini belirleyecek.
- soğutucu → vent (fazla hava, GAZ katmanında, kırmızı; hâlâ sıcak): soğutucunun ucundan 3 m içeride tavanından dik bir okla çıkar, "to cooler vent" yazısına gider

## Doğrulama

Makronun ön kontrolleri:
- kolonlar arasında riser'a yer var
- C5'ler kalsinatöre, hatlar kaz boynu kollarına değmiyor
- kaz boynu kolu C5'in volüt girişinin yüksekliğine sığıyor
- C5'ler TA kanalının en az `C5_OVER_TA` üstünde (yerleşim bunu kurar)
- C4 farini, dik inişinden sonra da C5 stub'ının üstünden geçiyor ve kalsinatöre koninin üstünden giriyor
- TA, C5'lerin altından, giriş odası ve fırının üstünden geçiyor
- soğutucu zeminin üstünde, başlık soğutucunun üstünde
- fırın içindeki gaz ve malzeme çizgileri fırın kabuğunun içinde

Çizimden sonra sayfa sketch'i geri okunur. Her katmanda çizilen çizgi ve yay sayısı bulunmalı. Beklenen sayılar:

| Katman | Çizgi | Yay |
|---|---|---|
| EKIPMAN | 119 | 0 |
| GAZ | 143 | 4 |
| FARIN | 73 | 0 |
| HAVA | 4 | 0 |
| YAZI | 89 | 0 |
| CERCEVE | 16 | 0 |
| EKSEN | 19 | 0 |
| OLCU | 47 | 5 |

Sayfada 231 not vardır. Bu sayılar okları, lejantı, tabloları ve anteti içerir. OLCU'daki 5 yay grid balonlarıdır. Çizgilerin kâğıttaki kapsamı da çizildiği kapsama 0.1 mm içinde oturmalı.

1/√2 ölçekli sürüm bir Python betiğiyle de kurulmuştu; tam ölçekli sürüm (12 Ekim 2026) için bu tarama yinelenmedi, aşağıdaki kırılmalar makro log'undan ve PDF'ten. O betik, hiçbir kanal kenarının ya da farin hattının kendi kaynağı ya da hedefi olmayan bir ekipman dış hattını kesmediğini doğruladı. Bilinçli istisnalar, ekipmanın içinden geçen akış çizgileridir (fırın → giriş odası → kalsinatör, soğutucu → başlık → fırın, giriş odası → fırın → soğutucu klinker yolu). Farin hatlarının gaz kanallarıyla çaprazlaması 2D'de kaçınılmazdır; gerçekte ikisi farklı derinliktedir. Çizimde bu yerlerde farin hattı kırılır:
- dış C1 farini ile R1'in yatay kanalı
- C4 farini ile C5 (iki hatta)
- sağ C5 farini ile TA kanalı

Makro log'u kırılmaları hat hat yazar; tam ölçekli çizimde (12 Ekim 2026) dış C1 farini R1'in yatay kanalının arkasından geçer, C4 farininin kaz boynu ile kesişmesi kalktı.

Ham farin R1'e, kendi hedefine girer. Betik ayrıca etiketlerin yaklaşık metin kutularını taradı: hiçbir etiket bir çizgiyle ya da başka bir etiketle çakışmıyor.

Çıktılar `geometry/output/2500/` altında:
- çizim `plant_topology_2d.SLDDRW`
- `plant_topology_2d.pdf`
- tam log `plant_topology_2d_build.log`
