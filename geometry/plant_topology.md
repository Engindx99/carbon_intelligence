# Tesis topolojisi (2D şema)

Makro: [`geometry/macros/plant_topology_2d.bas`](macros/plant_topology_2d.bas). Referans hat: 2500 t/d.

**CFD girdisi değildir.** Bu, tesisin topolojisini göstermek için çizilmiş gerçek ölçekli bir 2D şemadır: hangi ekipman var, nerede duruyor, gaz, farin ve hava hangi yoldan akıyor. `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır.

Önceki 3D topoloji modeli (`plant_topology.bas`, tek hatlı, çok gövdeli) kaldırıldı. Yerine bu 2D şema geldi; 2D daha okunur ve çakışma kısıtı taşımaz (kullanıcı kararı, 5 Ekim 2026).

## Ne çizilir

Bir SolidWorks **çizim sayfası**: A1 yatay (841 × 594 mm), ölçek **1:200**. Model koordinatları (x yatay, z kot, metre) sayfaya `P(x, z) = (X0 + x/200, Y0 + z/200)` ile yerleşir.

İlk sürüm bir parça sketch'iydi. Renkler orada görünmedi, çünkü sketch'in durum rengi özel rengi bastırıyordu. Etiketler 1 m yükseklikte okunmuyordu, her köşede de nokta yığını vardı. Çizim belgesine bu yüzden geçildi (kullanıcı kararı, 5 Ekim 2026).

- **Ekipman, gerçek kesit dış hatlarıyla:** siklonlar (toz çıkışı, koni, gövde, tavan, gaz çıkış stub'ı), kalsinatör (boğaz, koni, gövde), fırın giriş odası, fırın, soğutucu, fırın başlığı.
- **Akışın geçtiği duvarlar açıktır:** fırının iki ucu (giriş odasına ve başlığa açılır), kalsinatör boğazı (giriş odasının tavanı), kaz boynu kollarının kalsinatör tavanındaki ağızları, tersiyer hava kanalının başlık tavanındaki ve kalsinatör duvarındaki ağızları, başlığın altı (soğutucuya açık), her siklonun toz çıkışı, gaz çıkış stub'ının tepesi ve girişinin geldiği taraftaki gövde duvarı. Riser'lar stub'ın üstünde açık başlar; yalnız stub'ın dış duvarının üstünde kapakları vardır. Açıklığın yanında kalan, `MIN_SEG`'ten (0.05 m) kısa duvar parçası çizilmez. C5'e giren kanal gövde yüksekliği kadar olduğundan o taraftaki gövde duvarı tümüyle açıktır; C2–C4'ün gövdesi (h = D) kanaldan uzun, duvar kanalın altında kapalı devam eder. Tek çizgili yollar (farin, egzoz, primer hava) duvarda biter.
- **Ana kanallar gerçek çapında, çift çizgiyle:** R1–R4, kaz boynu ve tersiyer hava kanalı. Kenarlar eksenin w/2 iki yanındadır; köşeler kenarların kesişiminde birleşir.
- **Diğer yollar tek çizgiyle, eksen boyunca:** farin hatları, C1 egzozu, ikincil hava, fırın → kalsinatör gazı.
- **Akış okları:** her yolun en uzun parçasının ortasında, akış yönünde. Çizimden çıkan ya da yalnızca bir akımı belirten yollarda ("to ID fan", "to cooler vent", "to clinker transport", primer hava, tersiyer hava oku) ok yolun ucundadır; okun ötesinde çizgi kalmaz.
- **Etiketler:** not olarak, kâğıtta 3.5 mm yükseklikte. Siklon adları gövdenin içinde (oradan hiçbir yol geçmez), riser adları kanalın içinde. Sayılar yerel ayardan bağımsız olarak noktalı ve sabit ondalıklı yazılır ("2.440").
- **Kot cetveli:** solda, 0'dan 90 m'ye; her 10 m'de bir çentik ve kot. Zemin çizgisi cetvelden başlar.
- **Lejant:** renkler, ok, çift ve tek çizginin anlamı, hat başına çaplar ve 10 m'lik ölçek çubuğu.
- **Antet:** başlık, ölçek, tarih ve "şematik, CFD girdisi değil" notu.

| Katman | Renk | Kalınlık | İçerik |
|---|---|---|---|
| EKIPMAN | siyah | normal | ekipman dış hatları |
| GAZ | kırmızı (210, 0, 0) | ince | sıcak akımlar: gaz kanalları ve yolları, sekonder ve tersiyer hava, okları |
| FARIN | koyu sarı (200, 150, 0) | ince | farin hatları, okları |
| HAVA | mavi (30, 90, 220) | ince | soğuk hava: primer hava oku |
| YAZI | siyah | ince | zemin çizgisi, kot cetveli, lejant çizgileri, antet |

İlk sürümde açık turuncu ve normal kalınlıktaki çizgiler ekranda griye kaçıyordu; PDF'te renkler zaten doğruydu. Renk koyulaştırıldı, yol katmanları kalınlaştırıldı. Gaz kırmızıya geçtikten sonra çizim uzaktan kalın göründüğü için ekipman normal, yol katmanları ince kalınlığa indirildi.

Not ve sayfa ayarı (şablon çerçevesinin kaldırılması) çağrıları başarısız olursa çizim durmaz; log'a bir uyarı düşer.

## Tesis: iki hatlı ön ısıtıcı, 12 siklon

Görünüm gerçek bir tesisin DCS ekranından alınmıştır: kalsinatör ortada, iki hat iki yanda, fırın ve soğutucu altta sağda.

- **Siklonlar:** her hatta C5, C4, C3, C2 ve ikiz C1; toplam 12.
- **Kalsinatör:** bir ILC. Tepesindeki Y kaz boynu iki hattın C5'lerini besler.
- **Fırın, soğutucu, başlık ve tersiyer hava kanalı:** birer tane.

**Ölçek kuralı:** her hat gazın yarısını taşır. Bu yüzden hattın siklonları ve riser'ları katalogdaki 2500 ölçüsünün **1/√2** ile benzer ölçeklenmiş hâlidir; ikiz C5 kuralının aynısıdır (kullanıcı kararı, 5 Ekim 2026).

| Ekipman | Ölçü | Kaynak |
|---|---|---|
| C1 (hat başına ikiz) | D 3.055 (4.32 × 1/√2) | catalog.md |
| C2 = C3 = C4 | D 4.455 (6.30 × 1/√2), gövde 4.455 (h = D, CFD) | catalog.md (C2/C3/C4 sapması) |
| C5 | D 4.596 (6.50 × 1/√2) | cyclone_C5.md |
| R1 / R2 / R3 / R4 (hat başına) | Ø2.171 / 2.369 / 2.440 / 2.546 | catalog.md (HFC2500) × 1/√2 |
| Kalsinatör | Ø5.50, 29.46 m (koni dahil), boğaz Ø2.213, koni 65° | calciner.md |
| Kaz boynu | 2 kol × Ø2.475, kalsinatörün yarı yüksekliğinde biter | calciner.md, gooseneck.md |
| Tersiyer hava kanalı | Ø1.725 (türetilmiş) | calciner.md |
| Fırın | Ø4.0 × 60 m, %3 eğim | kiln.md |
| Soğutucu | ızgara alanı 65 m² | cooler.md |

**Bu yalnız topolojidir.** CFD dokümanları (`cyclone_C1–C4.md`, `cyclone.bas`) ve preheater CFD stratejisi tek hatlı ölçülerle kalır.

## Şematik parametreler (kaynaksız; yalnız yerleşim için)

| Parametre | Değer | Ne belirler |
|---|---|---|
| `STUB_OVER_VD` | 1.0 | Siklon gaz çıkış stub'ının tavan üstündeki boyu, vorteks bulucu çapı cinsinden |
| `STAGE_GAP` | 3.0 m | Bir siklonun toz çıkışının, alttaki kademenin tepesinden yüksekliği |
| `ZIG_DX` | 8.0 m | Hattın dış kolonunun (C4, C2) iç kolonundan (C5, C3) uzaklığı. Riser'lar iki kolonun ortasından çıkar; bu aralık en geniş riser (Ø2.546) ile iki yandaki siklonun yarıçapına yetmeli. Ön kontrol bunu zorlar |
| `C1_TWIN_GAP` | 3.0 m | İkiz C1 gövdeleri arasındaki boşluk. R1 (Ø2.171) bu boşluktan yükselir; ön kontrol sığmasını zorlar |
| `GN_TO_C5_GAP` | 1.0 m | Kaz boynu inişi ile C5 gövdesi arasındaki boşluk. İniş, C5'in giriş kotunda bu boşluğu yatay geçerek gövdeye girer |
| `MEAL_JOIN_DEG` | 50° | Dış C1'in farin borusunun, iç C1'in borusuna katılırken indiği eğim. 60°'de R2'nin köşesini kesiyordu |
| `MEAL_ENTRY_UP` | 1.5 m | Farinin riser'ın düşey kısmına, yatay parçasının üst kenarının bu kadar üstünde girdiği yer |
| `EXHAUST_L` | 10.0 m | C1 egzozunun ID fana doğru çizilen boyu |
| `RAW_L` | 6.0 m | Ham farin hattının dışarıdan çizildiği uzaklık |
| `KILN_AXIS_Z` | 10.0 m | Fırın giriş ekseninin kotu |
| `CHAMBER_MARGIN` | 1.0 m | Giriş odası ve başlık: fırının çevresinde bu payla bir kare |
| `COOLER_W` / `COOLER_H` | 3.0 / 4.0 m | Izgara genişliği (boy alandan çıkar: 21.67 m) ve soğutucu gövde yüksekliği |
| `COOLER_DROP` | 1.0 m | Soğutucunun tepesinin, deşarjdaki fırın kabuğunun altında kaldığı mesafe |
| `MEAL_INTO_CHAMBER` | 1.0 m | C5 farininin giriş odası tavanına, odanın yan yüzünden bu kadar içeride indiği yer |
| `C4_MEAL_DROP` | 3.0 m | C4 farininin, kalsinatöre dönmeden önce toz çıkışından dik indiği boy |
| `C4_MEAL_OVER` | 1.2 m | Dik inişin, farinin C5 stub'ını geçtiği kotun bu kadar üstünde bitmesi. C4 (ve üstündeki kademeler) buna yetecek kadar yükselir: `STAGE_GAP`'e göre 1.5 m daha yüksek |
| `FEED_LOWER` | 3.0 m | C4 farininin kalsinatöre, `calciner.bas`'ın besleme kotunun (bacak uçlarının 2 m altı) bu kadar altından girmesi. Yalnız topoloji içindir; CFD besleme boruları yerinde kalır |
| `KILN_FLOW_OFF` | 1.0 m | Fırın içindeki gaz ve malzeme çizgilerinin fırın ekseninden dik uzaklığı: gaz üstte, malzeme altta. Fırın kabuğunun (±2.0 m) içinde kalmalı; ön kontrol bunu zorlar |
| `PRIMARY_AIR_L` | 2.0 m | Primer havayı yalnızca belirten kısa okun boyu; ok başlığın ön duvarında biter |
| `SEC_AIR_DX` | 1.5 m | Sekonder havanın soğutucudan, fırının ucundan bu kadar içeride yükseldiği yer |
| `CLINKER_OUT_Z` | 3.5 m | Klinkerin soğutucunun ucundan indiği klinker taşımanın zeminin altındaki derinliği |
| `VENT_IN` | 3.0 m | Fazla soğutucu havasının soğutucunun ucundan bu kadar içeride, tavanından çıkması |
| `VENT_UP` | 4.0 m | Vent okunun soğutucunun tavanının üstünde çizildiği boy |
| `CLINKER_ON_GRATE` | 1.0 m | Klinker çizgisinin soğutucu tabanının üstündeki yüksekliği |
| `TA_ARROW_LONG` | 1.15 | Tersiyer hava okunun boyu: soğutucu ortasından başlığın tavanına olan yüksekliğin bu katı. Ok soğutucu ortasından (z 3.2) başlar ve kanalın içine, z 12.4'e kadar uzanır; ok ucu orada, çizgi okun ötesine geçmez. Kanalın dirseğine ulaşamaz; makro bunu kontrol eder |
| `SHEET_SCALE`, `X0`, `Y0` | 1:200; 0.20, 0.06 m | Sayfa ölçeği ve model (0, 0)'ın sayfadaki yeri |
| `RULER_X` | 0.03 m | Kot cetvelinin sayfadaki yeri |
| `TEXT_H`, `ARROW_L` | 3.5, 4 mm | Kâğıtta yazı yüksekliği ve ok boyu |

## Yerleşim

Kalsinatör ekseni x = 0'dadır. Sağ hat (R) +x'te, fırının üstünde durur; sol hat (L) −x'te, onun aynasıdır.

```
fırın giriş odası  |x| ≤ 3.0, z 7.0 .. 13.0
kalsinatör          z 13.0 .. 44.673; kaz boynu x = ±1.329'dan yükselir, R 3.712 dirsekle döner,
                    x = ±8.754'ten C5'in giriş kotuna (z 28.695) iner ve yatay C5 gövdesine girer
iç kolon (C5, C3)   x = ±13.289    C5 kendi kolundan 1.0 m dışarıda
dış kolon (C4, C2)  x = ±21.289
riser'lar           x = ±17.289    iki kolonun ortası
ikiz C1             x = ±14.262 ve ±20.317 (R1 aralarından yükselir)
toz çıkışları       C5 22.193 · C4 37.795 · C3 53.686 · C2 69.576 · C1 85.467; kule tepesi 95.253
fırın               (3.0, 10.0) → (62.973, 8.201)
soğutucu            x 62.973 .. 84.640, z 1.201 .. 5.201
fırın başlığı       x 62.973 .. 68.973, z 5.201 .. 11.201
```

## Yollar

Her hattaki yollar aynıdır; sol hat sağın aynasıdır.

**Gaz:**
- başlık (brülör ucu) → fırın boyunca, eksenin 1.0 m üstünde → giriş odası → kalsinatör → kaz boynu → C5. Kaz boynu `calciner.bas`'taki gibidir: iki kol, her biri yükseliş, 180° dirsek ve iniş. İniş, C5'in giriş kotunda (gövde ortası) dirsek yapar ve yatay olarak C5 gövdesinin yan duvarına girer; bu, teğetsel girişin yandan görünüşüdür. Giriş kanalı Ø2.475'tir ve C5 gövdesinin yüksekliğine (2.496 m) sığar; ön kontrol bunu zorlar.
- C5 → R4 → C4 → R3 → C3 → R2 → C2: riser, alttaki siklonun gaz çıkış stub'ının tepesinde yatay kanal olarak başlar. Kolonların ortasına gider, yükselir ve üstteki siklonun yanından girer: C1–C4'te kanalın üst duvarı çatı hizasında (CFD katılarında giriş çatıdan aşağı iner: C1 yarığı, C4 volütü), C5'te gövde ortasında (katalog girişi gövdeden uzun).
- C2 → R1 → ikiz C1: R1 iki C1'in arasında yükselir. İkiye ayrılır; her kolun alanı R1'in yarısıdır (Ø1.535).
- ikiz C1 → egzoz: iki stub birleşir ve hattın dışına, "to ID fan" ucuna gider

**Farin:**
- ham farin → R1: 60° ile aşağı inip R1'in yatay parçasının dış ucuna, C2'nin gaz çıkışının hemen üstüne girer
- C2 → R3, C3 → R4, iç C1 → R2: farin önce kendi kolonunda **düşey iner**, sonra **60°'lik bir parçayla** riser'ın düşey kısmına yan duvarından girer.
  - Giriş noktası, riser'ın alttaki siklonun üstündeki yatay parçasının 1.5 m üstündedir (`MEAL_ENTRY_UP`).
  - 60° eğim, kalsinatör besleme borularının eğimidir (Fidaros 2007). Boru dik riser duvarıyla 30° yapar, yani farin duvara yatık, neredeyse teğet kayarak girer.
  - Tesislerde farin, riser'a alttaki siklonun hemen üstünden bu şekilde verilir.
- dış C1 → iç C1'in borusu: dış C1, C2'nin üstünde durduğu için düşey inemez. Farini 50° ile iç C1'in borusuna katılır; ikiz C1'lerin farini birleşir.
- C4 → önce 3.0 m dik iner, sonra C5 stub'ının üstünden kalsinatör duvarına, z 24.943'e (`calciner.bas`'ın besleme kotunun 3 m altı): her hattın C4'ü kendi taraftaki besleme borusunu besler
- C5 → giriş odasının tavanı
- giriş odası → fırın → ızgaralı soğutucu (klinker): giriş odasından başlar, fırın boyunca eksenin 1.0 m altında gazın tersine akar, başlıkta soğutucuya düşer ve ızgara boyunca ilerler. Fırın içindeki iki paralel ve ters oklu çizgi karşı akışı gösterir
- ızgaralı soğutucu → klinker taşıma: klinker soğutucunun ucundan dik iner, tabanından çıkar ve zeminin 3.5 m altında, "to clinker transport" yazısının yanında bir okla biter. Sağa değil aşağı iner, çünkü sağda antet var

**Hava:**
- primer hava → ana brülör: yalnızca belirtilir; başlığın ön duvarına, fırın gazının (kırmızı) başladığı kotta dokunan kısa bir ok; çizgi okun ucunda biter
- soğutucu → başlık (sekonder hava): başlığın altında soğutucudan yükselir ve fırının ucuna, fırın gazının başladığı noktaya girer. GAZ katmanında (kırmızı) çizilir, çünkü fırının içinde fırın gazı olarak devam eden akım odur. Fırının içinde ayrı çizilmez: fırın gazı, primer ve sekonder havanın brülörde yanmış hâlidir
- Çizimde "primary air" başlığın dışında, primer hava hattının altında; "secondary air" fırının içinde, fırın gazı ile klinker çizgisinin arasında yazılıdır
- soğutucu → başlık → tersiyer hava kanalı → kalsinatör (GAZ katmanında, kırmızı; sıcak hava): tersiyer hava soğutucudan başlığın içinden dik bir okla yükselir ve başlığın tepesindeki kanala girer. Kanal kalsinatöre koni tepesinde (z 19.600'da) girer. Bu kot şematiktir; kalsinatör CFD makrosunun 6. adımı (TA kanalı) kendi yerini belirleyecek.
- soğutucu → vent (fazla hava, GAZ katmanında, kırmızı; hâlâ sıcak): soğutucunun ucundan 3 m içeride tavanından dik bir okla çıkar, "to cooler vent" yazısına gider

## Doğrulama

Makronun ön kontrolleri:
- kolonlar arasında riser'a yer var
- C5'ler kalsinatöre, hatlar kaz boynu kollarına değmiyor
- kaz boynu kolunun giriş kanalı C5 gövdesinin yüksekliğine sığıyor
- C4 farini, dik inişinden sonra da C5 stub'ının üstünden geçiyor ve kalsinatöre koninin üstünden giriyor
- TA, C5'lerin altından, giriş odası ve fırının üstünden geçiyor
- soğutucu zeminin üstünde, başlık soğutucunun üstünde
- fırın içindeki gaz ve malzeme çizgileri fırın kabuğunun içinde

Çizimden sonra sayfa sketch'i geri okunur. Her katmanda çizilen çizgi ve yay sayısı bulunmalı. Beklenen sayılar:

| Katman | Sayı |
|---|---|
| EKIPMAN | 120 çizgi |
| GAZ | 145 çizgi + 4 yay |
| FARIN | 61 çizgi |
| HAVA | 4 çizgi |
| YAZI | 21 çizgi |

Bu sayılar okları, lejant ve anteti içerir. Çizgilerin kâğıttaki kapsamı da çizildiği kapsama 0.1 mm içinde oturmalı.

Aynı çizim bir Python betiğiyle de kuruldu. Betik, hiçbir kanal kenarının ya da farin hattının kendi kaynağı ya da hedefi olmayan bir ekipman dış hattını kesmediğini doğruladı. Bilinçli istisnalar, ekipmanın içinden geçen akış çizgileridir (fırın → giriş odası → kalsinatör, soğutucu → başlık → fırın, giriş odası → fırın → soğutucu klinker yolu). Farin hatlarının gaz kanallarıyla çaprazlaması dört yerde kalır ve 2D'de kaçınılmazdır; gerçekte ikisi farklı derinliktedir:
- dış C1 farini ile R1'in yatay parçası
- C4 farini ile R4 ve kaz boynu inişi
- sağ C5 farini ile TA kanalı

Ham farin R1'e, kendi hedefine girer. Betik ayrıca etiketlerin yaklaşık metin kutularını taradı: hiçbir etiket bir çizgiyle ya da başka bir etiketle çakışmıyor.

Çıktılar `geometry/output/2500/` altında:
- çizim `plant_topology_2d.SLDDRW`
- `plant_topology_2d.pdf`
- tam log `plant_topology_2d_build.log`
