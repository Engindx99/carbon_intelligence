# Calciner (kalsinatör)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, §6, Ek). Tesis: **5000 t/d**, iki özdeş 2500 t/d ön ısıtıcı hattı tek kalsinatöre ve tek fırına bağlı (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).
Tip: **ILC** (in-line calciner). İkiz yakıtın %60'ını kalsinatörde yakıyor (`fuel.kiln_fraction: 0.40`).
Kaynak: Jiangsu Pengfei 5000 t/d hattı (PF5000, kendisi de çift hatlı); efektif çap FLS oranıyla türetilir. 12 Ekim 2026'ya kadar bu doküman 2500 t/d hattının kalsinatörünü anlatıyordu: HFC2500, Ø5.50 × 29.46 m, çift kol Ø2.475.

## Geometrik Ölçüler

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Gövde (shell) çapı | 7.2 m | yayınlanmış |
| Efektif iç çap | 6.7404 m | FLS oranıyla türetilmiş; 7.20 × 3.08 / 3.29 |
| Gövde boyu (koni + silindir) | 30 m | yayınlanmış |
| Alt koni duvar açısı (yatayla) | 65 ° | literatür |
| Boğaz çapı | 3.130 m | literatür akışı / literatür hızı |
| Alt koni yüksekliği | 3.871 m | türetilmiş |
| Silindir boyu | 26.129 m | türetilmiş |
| Tersiyer hava kanalı çapı | 2.4393 m | FLS oranıyla türetilmiş |
| Farin besleme borusu çapı | 0.8485 m | literatür; Fidaros 2007 × √2 |
| Yakıt borusu çapı | 0.2828 m | literatür; Fidaros 2007 × √2 |
| **Ekipman hacmi (koni + silindir)** | 1009.71 m³ | türetilmiş |
| **Duvar alanı (silindir + koni + tavan halkası)** | 635.96 m² | türetilmiş |
<!-- END GENERATED -->
- Efektif iç çap: gövde × FLS `calciner_eff_over_shell` = 3.08 / 3.29.
- Alt koni açısı: Holcim StDC 2022 siklon konisi için en az 65° ister; kalsinatör konisine de uygulandı. Koni yüksekliği (R − r_boğaz) · tan 65°, silindir gövde boyunun kalanı.
- Boğaz ve tersiyer kanal: literatür akışı / literatür hızı, aşağıda (tersiyer kanal 6. adımda kurulur; tek, teğetsel).
- Kaz boynu: iki kol, her biri yayınlanmış 2500 t/d boynunun çapında; ortak boyun iki kolun toplam kesitinde ([gooseneck.md](../preheater/gooseneck.md); kullanıcı kararı, 12 Ekim 2026).
- Farin besleme boruları: iki adet, yatayla 60°; Fidaros ve diğ. 2007 (Ø0.6) × √2: boru başına farin iki katı, hız korunur.

**Boğaz ve tersiyer kanal türetmesi.** Bunlar için yayınlanmış bir ölçü ya da oran bulunamadı: FLS kalsinatörü düz bir silindir olarak verir (arXiv 2504.02886 Tablo 8, koni 0), bakılan CFD makaleleri de bu ölçüleri yazmaz. Bu yüzden her biri, literatürdeki bir akışın literatürdeki bir hıza bölünmesiyle bulunur. İdeal gaz ve 1 atm varsayılır. **İkizin akışları kullanılmaz**: ikiz henüz hazır değil; örneğin tersiyer havayı 575 K veriyor, tesislerde bu değer ~1100 K (kullanıcı kararı, 29 Eylül 2026). Literatür akışları 2500 t/d sınıfı bir hattındır; 5000 t/d'de ikiye katlanır.

| | Fırın gazı → boğaz | Tersiyer hava |
|---|---|---|
| Kütle akışı | 2 × 110 600 kg/h = 61.44 kg/s | 2 × (49 600 + 16 200 + 33 065) kg/h = 54.92 kg/s |
| Akış kaynağı | Mikulčić ve diğ. 2012 (Ø5.5 m kalsinatör, 2500 sınıfı) × 2 | Mikulčić ve diğ. 2012: TA + brülör birincil + ikincil havası, × 2. ILC'de yanma havasının tamamı tersiyer kanaldan girer |
| Sıcaklık | 1050 °C | 800 °C (Kahawalage ve diğ. 2017) |
| Bileşim / M | %74.4 N₂, 7.6 O₂, 5.0 H₂O, 13.0 CO₂ → 29.90 g/mol (Kahawalage 2017) | %21 O₂ / 79 N₂ → 28.85 g/mol |
| Yoğunluk | 0.2753 kg/m³ | 0.3276 kg/m³ |
| Hacimsel akış | 223.2 m³/s | 167.6 m³/s |
| Tasarım hızı | 29 m/s (CPFD 2025, boğaz ortalaması 28–30 m/s) | 35.87 m/s (Chanamai & Rodkwan 2019) |
| **Çap** | **3.130 m** | **2.439 m** |

Kalsinatörden çıkan gaz (iki hat, 2 × 56 kg/s, ~1163 K): gövdede 10.0 m/s, kalma süresi ~3.0 s; boyunda ve kollarda 18.6 m/s.

Fidaros ve diğ. 2007 farini **iki** Ø0.6 m borudan, yatayla 60° eğimle verir; kömürü iki Ø0.2 m borudan, 30° eğimle. Burada her boru bir hattın C4 farinini taşır. Farin boruları 5. adımda, yakıt boruları 7. adımda kurulur.

## CFD Geometry

Makro: [`geometry/macros/calciner.bas`](../macros/calciner.bas). Yapım adım adım ilerler ve tamamdır (14 Ekim 2026): gövde, Y kaz boynu, iki farin borusu, teğetsel tersiyer hava kanalı ve iki yakıt borusu; sınır yüzleri boyanır, katı dışa aktarılır (`geometry/output/2500/calciner.{SLDPRT,step,stl}`; klasör adı makronun `LINE_KEY`'i, tesis 5000 t/d).

Koordinatlar: eksen **z**, fırın gazı giriş yüzü (boğazın altı) **z = 0**.

<!-- BEGIN GENERATED (tools/gen_geometry.py) cfd -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Adım / parça | Konum [m] | Hacim [m³] |
|---|---|---|
| Boğaz | Ø3.130, z 0 .. 3.130 | 24.085 |
| Koni | 65°, z 3.130 .. 7.001 | 77.357 |
| Silindir (düz tavan) | Ø6.7404, z 7.001 .. 33.130 | 932.354 |
| Gövde (koni + silindir) |  | **1009.711** |
| 1 domen (boğaz + gövde) |  | 1033.797 |
| 2 + boyun | Ø4.950, eksende, z 33.130 .. 39.317 | 1152.852 (+119.055) |
| 3a + dirsek +x | kol Ø3.5, başlangıç diski x = ±0.725; 180°, R 5.250, tepe z 46.317 | 1311.537 (+158.685, Pappus) |
| 3b + dirsek −x | iki dirseğin ortak hacmi 10.346 (sayısal, 80³ nokta) | 1459.876 |
| 4 + iki iniş | x = ±11.225, z 39.317 .. 18.130 → gas_outlet_1 (+x), gas_outlet_2 (−x) | 1867.565 (+2 × 203.845) |
| 5a / 5b + farin boruları ±x | Ø0.8485, 60°, eksenleri duvarı z 11.385'da keser; deliğin alt kenarı z 10.491, uç yüzleri (±3.870, 0, 12.252) | 1868.138 / 1868.711 (+0.5730 her biri) |
| 6 + tersiyer hava | Ø2.4393, teğetsel, eksen y -2.101, z 8.271; üst kenarı z 9.491, yüzü x 6.370 | 1886.798 (+18.087) |
| 7a / 7b + yakıt boruları ±y | Ø0.2828, 30°, eksenleri duvarı z 11.385'da keser; uç yüzleri (0, ±4.236, 11.885) | 1886.860 / **1886.923** (+0.0629 her biri) |
<!-- END GENERATED -->

Kollar x–z düzleminde ayna simetriktir; başlangıç diskleri boynun içinde, kendi tarafında boynun kenarına teğettir. Tersiyer hava kanalı −y tarafında, +x'ten (başlık tarafı) gelir. Farin boruları ±x'te, y = 0 düzleminde; yakıt boruları ±y'de, x = 0 düzlemindedir. Hepsinin ekseni gövdeden dışarı doğru yükselir. Boğazın boyu `THROAT_LEN_OVER_D` (modelleme parametresi).

Boğazın koni altındaki boyu bir tesis ölçüsü değildir. Giriş yüzünü koninin ağzına değil, düz bir parçanın üstüne koymak için seçilmiş bir modelleme parametresidir.

**Y kaz boynu** (kullanıcı kararı, 12 Ekim 2026). Her kol bir hattın C5'ine iner ve o hattın bütün gazını taşır; yayınlanmış 2500 t/d boynunun çapı (Ø3.50) bu yüzden her kola düşer.
- **Neden tek boyun.** İki Ø3.50 boru Ø6.74'lük tavana yan yana sığmaz (7.0 > 6.74 m). Tavandan tek bir boyun çıkar; kesiti iki kolun toplamıdır (Ø4.95), hız korunur. 2500 kalsinatöründe bunun yerine iki kol tavandan ayrı çıkıyordu, her biri alanın yarısıyla (29 Eylül 2026).
- **Ayrım.** Boynun tepesinde iki kol başlar. Her kolun başlangıç diski boynun içindedir ve kendi tarafında boynun kenarına teğettir: x = ±(r_boyun − r_kol) (tabloda). İki disk ortada üst üste biner. Disklerin örtmediği yerde (boyun kesitinin ~%24'ü, ±y'de) boynun tepesi düz bir tavandır.
- **Ortak hacim.** İki dirsek boynun hemen üstünde bir hacmi paylaşır (tabloda). Kapalı biçimi yoktur; makro bunu 80³ noktalı orta nokta kuralıyla hesaplar (`GnBendOverlap`). Bağımsız bir Monte Carlo sağlaması 10.354 ± 0.010 m³ verdi.
- **Boylar modelleme parametresidir.** Yükseliş 1.25 × boyun çapı, dirsek yarıçapı 1.5 × kol çapı (C1 makrosunun oranları). İnişler gövdenin yanında, **gövdenin yarı yüksekliğine** kadar sarkar: boğazın üstünden gövde boyunun yarısı (`GN_OUTLET_AT_VESSEL_H`; kullanıcı kararı, 29 Eylül 2026). Böylece çıkış yüzü dirsekten uzakta, düzelmiş bir akışın üstünde durur; C1'de düz borunun ucundaki çıkış yüzünde %38 geri akış ölçülmüştü.
- **Yön ölçülür, varsayılmaz.** Bir extrude yanlış yöne giderse ya gövde sayısı ya da hacim bunu söyler; bir dirsek yanlış dönerse hacim ve kutunun tepesi söyler. Bu durumda feature silinir ve diğer yön denenir.

**Tersiyer hava kanalı** (kullanıcı kararı, 14 Ekim 2026). Chen ve diğ.'nin 5000 t/d in-line kalsinatöründeki gibi tersiyer hava gövdenin en alt bölgesine teğetsel girer ve fırın gazıyla karışır.
- **Yer.** Kanalın alt kenarı koninin tepesinde, dış duvarı gövde duvarıyla aynı hizada; her ikisi de 5 cm içeride (`TA_CONE_CLEARANCE`, `TA_WALL_RELIEF`). Yuvarlak bir kanal gövde duvarına tek noktada teğet olursa ya da alt kenarı koni–silindir dikişinin üstünden giderse, birleştirme bozuk bir kenar bırakır; `cyclone.bas` giriş kanalını tavandan aynı nedenle 5 cm aşağıda tutar.
- **Domende** yalnız bir uç parçası var: x = 0'dan (gövdenin içinde) gövdenin x = R teğet düzleminin `TA_STUB_LEN` ötesine kadar. Uç yüzü `tertiary_air_inlet`. Kanalın geri kalanı (başlığa kadar) çizimde şematiktir.
- **Hacim.** Gövde dışında kalan kısım πr²·x_uç − 2∫√(r²−(y−y_c)²)√(R²−y²) dy; makro ve `plant_geometry.py` aynı Simpson kuralıyla hesaplar. Yanlış yöne (−x) giden bir extrude aynı hacmi verir, bu yüzden yön x = +x_uç'taki yüzle anlaşılır.

**Farin besleme boruları** (kullanıcı kararları, 29 Eylül ve 14 Ekim 2026). Gövdenin iki yanında, kaz boynuyla aynı x–z düzleminde ±x'te dururlar; uçları kaz boynu inişlerinden uzaktır, bunu bir ön kontrol zorlar.
- **Yükseklik.** Farin tersiyer havanın hemen üstünden verilir (Chen ve diğ.: farin ve kömür aynı kotta, farklı yönlerden; US 10,974,992: ana farin girişi tersiyer hava girişinin üstünde). Her borunun duvardaki deliği kanalın üst kenarının `FEED_ABOVE_TA` üstünden başlar. 14 Ekim 2026'ya kadar borular kaz boynunun CFD çıkış yüzlerinin 2 m altındaydı; bu hiçbir tesis kuralından gelmiyordu.
- **Ölçüler ve yön.** Eğim Fidaros 2007'den; çap onun Ø0.6'sı × √2 (her boru bir 2500 hattının farinini taşır). Her boru gövde eksenine bakar ve duvardan uzaklaştıkça yükselir, böylece farin ortaya doğru düşer.
- **Boy.** Boru, duvarın bir boru çapı içinden başlar; başlangıç diski gövdenin içinde kalır ve birleşimde erir. (Eskiden eksenden başlıyordu; alçalan borunun başlangıcı o zaman koninin içine düşerdi.) Duvardan eksen boyunca `FEED_DEPTH` dışarı çıkar (C1 oluğu gibi). Uç yüzün tamamen dışarıda kalması için bu değer r·tan 60° = 0.73 m'yi aşmalıdır.
- **Nasıl kurulur.** y = 0 düzlemindeki yarım kesit dikdörtgeni, kendi eksen kenarı etrafında tam tur döndürülür. Tam turun yanlış gidebileceği bir yönü yoktur; hangi tarafa düştüğünü ±x'te bulunan uç yüzü söyler.
- **Hacim.** Gövde dışında kalan kısım boru başına πr²L − (1/cos θ)·(2∫√(r²−a²)√(R²−a²) da − ρ₀πr²), ρ₀ borunun başladığı yatay uzaklık (değeri CFD tablosunda). İntegral eliptiktir; makro a = r sin φ dönüşümüyle Simpson kuralıyla hesaplar. Bu hacim ~1887 m³'lük domenin ‰1'inin altında, yani toplam hacim kontrolü boruyu göremez. Bu yüzden her boru için ayrıca şunlar kontrol edilir: eklenen hacim %1 toleransla, uç yüzü beklenen tarafta bulunmalı ve alanı borunun kesiti olmalı.

**Yakıt boruları** (kullanıcı kararı, 14 Ekim 2026). Fidaros 2007'nin iki Ø0.2 m kömür borusu, 30° eğimle; her biri bir hattın yakıtını taşıdığı için çap × √2 (farin borularıyla aynı kural). Farin borularıyla aynı kotta (eksenleri duvarı aynı yerde keser), onlara 90° açıyla ±y'de. Farin boruları gibi kurulur ve kontrol edilir.

Yapım adımları:
1. gövde (revolve)
2. \+ boyun
3. \+ iki 180° dirsek (3a: +x, 3b: −x)
4. \+ iki iniş borusu
5. \+ iki farin besleme borusu (5a: +x, 5b: −x)
6. \+ tersiyer hava kanalı (teğetsel, −y tarafında, +x'ten)
7. \+ iki yakıt borusu (7a: +y, 7b: −y)
8. sınır yüzlerinin boyanması ve dışa aktarma → `geometry/output/2500/calciner.*`

`calciner_build.log` her çalıştırmada yazılır; `tests/test_plant_geometry.py` ölçüleri, adım hacimlerini ve sınır yüzü alanlarını oradan `plant_geometry.py` ile karşılaştırır.

## Gaz-yalnız CFD ve farin kalma süresi (14 Ekim 2026)

İlk koşu **tepkimesiz**dir (kullanıcı kararı): domene yalnız iki gaz girer. Yakıtın yanması ve kalsinasyonun CO₂'i yoktur; bunun etkisi sonuçta ayrıca düzeltilir.

**Mesh:** Ansys Meshing tet. Named selection'ları ve boyutları `tools/calciner_named_selections.py`'nin ürettiği Mechanical betiği koyar: yüzleri merkez ve alanlarından bulur, çünkü Workbench STEP'in renklerini düşürür.
- Boyutlar: genel 220 mm, yakıt boruları 40 mm, farin boruları 80 mm.
- Inflation yok. Denendi: hücre sayısını Student düğüm sınırına taşıdı ve çarpıklığı 0.98'e çıkardı.
- 797 952 tet → **159 973 poly hücre**, 894 661 düğüm. `improve-quality` sonrası en küçük orthogonal quality **0.199**.
- En kötü hücreler boynun tepesinde (x ±2.46, z 39.27), kol disklerinin boyna teğet olduğu yerde. Gerekirse kökten çözümü tersiyer kanaldaki gibi 5 cm'lik bir paydır.
- Fluent'te ölçülen hacim 1884.73 m³ (SolidWorks 1886.92). Sınır yüzlerinin alanları ve merkezleri kaynaktakilerle tutar.

**Kurulum:**
- Türbülans: SST k-ω + eğrilik düzeltmesi. Enerji açık.
- Gaz: tür taşınımı (N₂, O₂, H₂O, CO₂; tepkime kapalı). CO₂ karışmanın izleyicisidir: fırın gazı payı = Y_CO₂ / 0.1914.
- Özellikler: incompressible-ideal-gas; cp karışım kuralıyla (NASA polinomları); μ 4.6·10⁻⁵ kg/(m·s) ve k 0.076 W/(m·K), sabit.
- Yerçekimi −z.
- Girişler `plant_geometry.calciner_boundaries`'ten:
  - fırın gazı 61.44 kg/s, 1323.15 K;
  - tersiyer hava 54.925 kg/s, 1073.15 K, hava bileşimi;
  - ikisinde de %5 türbülans yoğunluğu ve yüzün kendi hidrolik çapı.
- Farin ve yakıt boruları adyabatik duvar.
- Çözücü: steady Coupled, PRESTO!, ikinci derece. ~1000 iterasyonda salınmadan oturdu.

**Çıkışlar eşit akışlı (kullanıcı kararı, 14 Ekim 2026).**
- İki çıkış da 0 Pa iken teğetsel tersiyer havanın girdabı gazı **%56 / %44** böldü.
- Bu bir sınır koşulu yapaylığıdır. Tesiste her kolun arkasında C5–C1 ve fan vardır; hat başına birkaç kPa'lık, akışın karesiyle artan bir direnç. Bu direnç, kalsinatörün içindeki birkaç on Pa'lık farkların yaratacağı dengesizliği ortadan kaldırır.
- Bu yüzden iki çıkışa da hedef kütle akışı verildi: her birine toplamın yarısı, 58.18 kg/s.

| Büyüklük | Değer |
|---|---|
| Bölünmeyi tutan basınç farkı (çıkış 1 − çıkış 2) | +23.7 − (−22.0) = **45.7 Pa** |
| Toplam basınç kaybı (girişler → çıkışlar, kütle ağırlıklı) | **181 Pa** |
| Fırın gazı girişi, statik, çıkışlara göre | −15.6 Pa |
| Tersiyer hava girişi, statik, çıkışlara göre | +199.8 Pa |
| Çıkış sıcaklıkları (1 / 2) | 1197 / 1222 K; karışım 1209 K |
| Fırın gazı payı (1 / 2); tam karışmış 0.528 | 0.481 / 0.575 |
| v_max | 52 m/s |

- 45.7 Pa, hatların direnci yanında küçüktür; eşit bölünme varsayımı tutarlıdır.
- Basınç enerjisinin çoğunu tersiyer hava jeti getirir (kanalda 35.9 m/s, dinamik basınç ~211 Pa). Jet gövdeyi pompalar, bu yüzden fırın gazı girişi çıkıştan aşağıdadır.
- Karışma çıkışlarda tamamlanmaz. Hat 1 (+x, tersiyer kanalın ucu tarafı) daha çok tersiyer hava alır ve 24 K daha soğuktur. Yanmasız bir sonuçtur: gerçekte yakıt bu havada yanar.

**Farin kalma süresi: tek yönlü DPM, donmuş gaz alanında.**
- Enjeksiyon: her farin borusunun ağzında, duvarın 0.35 m içinde, boru kesitinde 24 noktalık bir disk. Hız borunun ekseni boyunca, aşağı ve içe doğru 3.5 m/s.
  - Ağızdan enjekte edilir, borunun uç yüzünden değil: C1'de uç yüzden enjekte edilen farin ölü borunun içinde asılı kalmıştı.
- Tane boyu: C1'in 7 boyu sınıfı (3.8–172 µm, kütle payları 10/10/20/20/20/15/5 %). Parçacık yoğunluğu 2700 kg/m³.
- Türbülanslı saçılma: DRW, 10 deneme. Duvardan yansıma 0.8 / 0.8; boru duvarları 1.0, çünkü Fluent bu yüzlerde katsayı sormuyor.
- Toplam 3360 parsel. Gövdedeki kalma süresi, parselin boyna (z = 34 m'deki düzlem) ilk varışıdır.
- **Bütün parseller iki çıkıştan çıkar; boğazdan fırına düşen farin yoktur.**

| Tane boyu | Kütle payı | Ortalama [s] | %10 | Medyan | %90 | En uzun | Hat 1'e giden pay |
|---|---|---|---|---|---|---|---|
| 4–30 µm | %60 | 2.25–2.34 | 1.4 | 2.3–2.5 | 2.8–3.0 | 3.4 | 0.51–0.58 |
| 53 µm | %20 | 2.24 | 1.5 | 2.10 | 3.13 | 3.4 | 0.42 |
| 94 µm | %15 | 2.56 | 2.3 | 2.55 | 2.81 | 2.9 | 0.23 |
| 172 µm | %5 | 6.99 | 3.0 | 4.83 | 14.7 | 36 | 0.77 |
| **Hepsi, kütle ağırlıklı** | | **2.55** | 1.48 | 2.43 | 3.03 | | 0.478 |

- 94 µm'ye kadar farin gazla gider. Ortalamaları gazın düz akış süresine eşittir: 1009.7 m³ / 392.9 m³/s = 2.57 s. 4 µm'lik sınıf gazın kendi kalma süresi dağılımını verir: çekirdekteki hızlı akış yüzünden %10'u 1.4 s'de geçer.
- 172 µm'lik iri sınıf gövdede döner: ortalama 7 s, en uzun 36 s.
- Girdap iri taneleri hatlara farklı dağıtır. Toplamda %47.8 / %52.2.
- Kaz boynu dahil, çıkışlara kadar ortalama 5.1 s; boyun ~2.6 s ekler.

**Twin'e sonuç:**
- CFD twin'in **modelini** doğrular, sayısını değil.
  - Twin farini gazla düz akışta taşır, eksi kendi ağırlığının yarattığı kayma (`physics.suspension_transport`).
  - CFD'de kütlenin %95'i (≤ 94 µm) gazın düz akış süresinde geçer: 2.2–2.6 s, gazın süresi 2.57 s. Kayma yalnız %5'lik 172 µm sınıfında belirgindir.
  - Bu yüzden taşınım modeli değişmez.
- Süreler doğrudan karşılaştırılamaz, çünkü akışlar ve domen farklıdır:
  - Twin'in kalsinatör bölgesi gövde + kaz boynu + C5'tir (2395 m³). Referans durumda bölgenin tamamı 8.24 s, gövdenin payı ~3.5 s. Twin hızı girişteki en soğuk gazın yoğunluğuyla hesaplar; bu süre bilerek bir üst sınırdır.
  - Twin'in kalsinatöre giren gazı ~80 kg/s'dir; CFD'de literatür akışlarıyla 116.4 kg/s girer.
  - CFD'de yakıttan ve kalsinasyondan gelen CO₂ da yoktur; bu, gaz hacmini ~%20–25 eksik bırakır.
- CFD'deki gövde süresi (2.55 s) 2–5 s bandındadır.
- Kalsinatörün gaz-yalnız basınç kaybı 181 Pa'dır. Euler sayısı olarak (10.07, gövdenin yüzeysel hızıyla) twin'in diagnostics raporuna girer (D15, `configs/twin_cfg.yaml` → `pressure`). Fiziğe geri beslenmez.

### Twin akışlarıyla, CO₂ ve ısı kaynaklı (15 Ekim 2026)

Kullanıcı kararı: ikinci koşu twin'in referans durumunun akışlarıyla yapılır. Böylece sonuç twin'le birebir karşılaştırılabilir. Değerler `C:\Users\engin\calciner\twin\twin_bc.py` ile twin'in durumundan türetilir.

**Girişler ve kaynaklar:**
- Fırın gazı 35.91 kg/s, 1332.7 K, twin'in bileşimiyle (CO₂ kütlece %31.8). Tersiyer hava 44.18 kg/s, 1253.4 K.
- Gövde, twin'in eşit hacimli hücrelerinin ikişerli gruplarına denk gelen dört yükseklik bandına bölündü:

  | Bant | z [m] | Hacim, CFD / twin [m³] |
  |---|---|---|
  | 1 | 3.13–11.55 | 239.3 / 239.5 |
  | 2 | 11.55–18.26 | 239.2 / 239.5 |
  | 3 | 18.26–24.97 | 239.3 / 239.5 |
  | 4 | 24.97–33.13 | 290.8 / 291.2 |

  Bölme Fluent'te silindir cell register'larıyla ve `sep-cell-zone-mark` ile yapıldı.
- Her banda kendi kaynakları, birim hacim başına sabit:
  - **Kalsinasyon:** twin'in hücre başına gaz kütlesi artışı (CO₂ + bağlı su). Gövdede 23.42 kg/s; en çok altta.
  - **Yakıt:** twin yakıtı girişte bir anda yakar. Burada gövdeye düzgün dağıtıldı, twin'in yakıt ısısını dağıttığı gibi: +3.17 kg/s yakıt, −8.60 O₂, +10.64 CO₂, +1.13 H₂O (kg/s).
  - **Enerji:** twin'in hücre başına gaz entalpisi artışı, toplam +10.85 MW. En alt bantta eksidir (−3.47 MW), çünkü gaz orada soğuk farine ısı verir.
- Fluent tür kaynaklarını 298.15 K'de sayar ([Ansys forum](https://innovationspace.ansys.com/forum/?p=296723)). Twin'in duyulur entalpileri de aynı kuralla sayar; bu yüzden enerji kaynağı doğrudan H_çıkış − H_giriş'tir. Doğrulama: boyundaki gaz **1132.4 K**, twin'in gövde sonu sıcaklığı 1132 K.
- Kaz boynundaki kalsinasyon (2.23 kg/s) bu domende yoktur.
- Çıkışlar eşit akışlı, her biri 53.35 kg/s. Kütle dengesi kapanır: 80.10 + 26.60 = 106.69 kg/s.

**Gaz sonucu** (920 iterasyon, steady, salınım yok):

| Büyüklük | Twin akışları | Literatür akışları |
|---|---|---|
| Toplam basınç kaybı | **149 Pa** (D15'in öngörüsü 151 Pa) | 181 Pa |
| Bölünmeyi tutan fark (çıkış 1 − 2) | 36.8 Pa | 45.7 Pa |
| Statik basınç, çıkışlara göre (fırın gazı / tersiyer hava) | +40.3 / +134.3 Pa | −15.6 / +199.8 Pa |
| Çıkış sıcaklıkları (1 / 2) | 1130.5 / 1134.6 K | 1197 / 1222 K |
| CO₂ kütle kesri (1 / 2) | 0.421 / 0.432 | 0.094 / 0.111 |
| v_max | 42.5 m/s | 52 m/s |

- Euler ölçeklemesi tutar: D15 twin'in akışlarında 151 Pa öngördü, CFD 149 Pa verdi.
- Twin akışlarında iki hattın gazı neredeyse aynıdır (4 K).

**Farin kalma süresi** (aynı DPM kurulumu):

| Tane boyu | Gövde, ortalama [s] | %10 | %90 | Hat 1'e giden pay |
|---|---|---|---|---|
| 4–30 µm | 2.94–3.00 | 2.3–2.5 | 3.5–3.6 | 0.40–0.52 |
| 53 µm | 2.78 | 2.05 | 3.62 | 0.38 |
| 94 µm | 3.09 | 2.90 | 3.29 | **0.03** |
| 172 µm | 3.77 | 3.50 | 4.00 | **0.02** |
| **Hepsi, kütle ağırlıklı** | **2.98** | 2.31 | 3.61 | **0.35** |

- Fırına düşen farin yoktur. İri parsellerin %2.5'i (kütlenin ~%0.5'i) −y'deki yakıt borusunun ölü cebinde takılır; gerçekte oradan yakıt jeti çıkar. Bu parseller istatistiğin dışındadır.
  - Bu yakıt yüzlerinin parçacık koşulu "escape" kalmıştı, çünkü yüzler önce giriş olarak tanımlanmıştı. Burada "reflect" yapıldı.
- Literatür akışlarındaki uzun kuyruk (172 µm, 36 s'ye kadar) burada yoktur. Dağılım dardır: %90'ı 3.6 s içinde geçer.

**Twin'le karşılaştırma:**

| | Süre |
|---|---|
| CFD, gazın gövdenin tamamındaki düz akış süresi (gaz kütlesi 339.0 kg / bant bant kütle akışı) | **3.56 s** |
| Twin, gövdenin tamamındaki transit (8.24 s × gövde payı 0.4216) | **3.48 s** (−%2) |
| CFD, farinin besleme ağzından (z 10.8 m) boyna kalma süresi | **2.98 s** |

- **Twin'in gaz taşınımı doğru:** gövde için %2 içinde tutar.
- **Farinin süresinde twin %17 uzundur.** Neden: twin farini gövdenin dibinden verir, gerçek besleme ise tersiyer kanalın 1 m üstündedir (z 10.8 m). Farin gövdenin alt ~%27'sini görmez.
- **İki hattın farin yükü eşit değildir.** Girdap iri taneleri neredeyse tamamen hat 2'ye (−x) taşır. Toplamda farinin **%35'i hat 1'e, %65'i hat 2'ye** gider. Twin iki özdeş hat varsayar (her biri yarı yük). Bu, C5'lerin yükünü ve hatların ısı dengesini etkiler. Bu sonuç tek yönlü bir hesaptır: yüklemenin gazı etkilemesi yok.

**Bölünme borudan bağımsız** (boru başına DPM, 15 Ekim 2026; her boyu sınıfı her boru için ayrı enjeksiyon, `twin\pipes\pipe_matrix.py`). Değerler, her borunun farininin hat 1'e giden payı:

| Tane boyu | +x borusu | −x borusu |
|---|---|---|
| 4–8 µm | 0.46–0.50 | 0.40–0.42 |
| 16 µm | 0.52 | 0.51 |
| 30 µm | 0.41 | 0.39 |
| 53 µm | 0.29 | 0.43 |
| 94 µm | 0.03 | 0.03 |
| 172 µm | 0.00 | 0.00 |
| **Toplam** | **0.345** | **0.350** |

- Gövde iki borunun farinini tamamen karıştırır; ardından girdap iri taneleri −x koluna gönderir. Dengesizlik besleme düzeninden değil, girdap ile Y kaz boynunun yöneliminden gelir. C4 farin borularındaki bir bölücü klape onu düzeltemez.
- Hat 2'nin C4'ünün fazladan getirdiği farin de aynı oranla dağılır. Bu yüzden döngüde büyüme olmaz.
- **Twin'e etkisi:** iki C5'in yüklemesi ve tane boyu dağılımı farklıdır. Ağırlıklı η 0.0085 düşer; twin'de C5 0.90 → 0.89 ([cyclone_C5.md](../preheater/cyclone_C5.md)).

**Literatür:** çift hatlı, tek kalsinatörlü (Y kaz boynu) tesislerde kalsinatör çıkışındaki farin dengesizliğini ölçen bir kaynak bulunamadı (15 Ekim 2026). Bulunanlar dolaylı:
- hat dengesi için gaz tarafında bölücü damperler ([UGESL](https://ugesl.com/products/industry/splitter-damper-for-cement-plants));
- dengesizliği yakalamak için hatlar arasında sıcaklık ve fark basıncı izlemesi ([Endress+Hauser](https://www.us.endress.com/en/industry-expertise/mining-minerals-metals/preheater-optimization));
- farinin kalsinatör seviyeleri arasında bölünmesi ([FLSmidth](https://www.flsmidth-cement.com/products/flsmidth-low-nox-calciner)).

Tesis verisi bulunursa, iki C5'in alt akış sıcaklıkları ya da çıkış gazı sıcaklıkları bu bölünmeyi sınamanın yolu olur.

Dosyalar (repo dışında, `C:\Users\engin\calciner`):
- `calciner.msh`, `calciner.wbpj`, `calciner_poly.cas.h5`
- `calc_setup.cas.h5`, `calc_settings.set`
- `calc_steady.*` ve `steady.out`: iki çıkış 0 Pa
- `calc_split.*` ve `split.out`: eşit akış
- `calc_dpm.cas.h5`: DPM, `neckp` düzlemi
- `make_inj.py` ve `d004…d172.inj`: enjeksiyonlar, `plant_geometry`'den
- `rt_stats.py`, `gas_outlet_1/2.dpm`, `neckp.dpm`, `dpm_summary.txt`
- Twin akışları:
  - `twin\twin_bc.py`, `cal.pkl` ve `sp.pkl` (twin'in durumu), `twin_bc.pkl`
  - `calc_twin.*` ve `twin.out`
  - `calc_twin_dpm.cas.h5`
  - `twin\dpm\*.dpm` ve `rt_stats.py`

## Boundary Faces

Her sınır yüzü düzlemi, normali ve üstündeki bir noktayla bulunur ve kendi rengine boyanır. AP214 STEP renkleri taşır; Fluent Meshing her renkten bir bölge yapar, bölgeler log'daki renk listesine göre adlandırılır. Kalan her yüz duvardır. Her sınırdan tam bir tane bulunmalı ve alanı kendi kesiti olmalı; makro bunu kontrol eder.

| Sınır | Renk (RGB) | Ne |
|---|---|---|
| `kiln_gas_inlet` | yeşil (0.2, 0.7, 0.35) | boğazın altındaki z = 0 diski |
| `gas_outlet_1`, `gas_outlet_2` | mavi (0.2, 0.45, 0.85), koyu mavi (0.1, 0.25, 0.55) | +x ve −x'teki inişlerin aşağı bakan diskleri, her biri bir kol kesiti. Her biri bir hattın C5'ini besler ([cyclone_C5.md](../preheater/cyclone_C5.md)); bağ bu yüzler üzerinden kurulur, C5 bu domene katılmaz |
| `tertiary_air_inlet` | kırmızı (0.85, 0.25, 0.2) | tersiyer kanal parçasının x = x_uç'taki yüzü |
| `meal_feed_1`, `meal_feed_2` | mor (0.6, 0.3, 0.7), koyu mor (0.4, 0.15, 0.5) | +x ve −x'teki farin borularının eğik uç yüzleri. Gaz için duvar, DPM için enjeksiyon yüzeyi (C1'deki gibi) |
| `fuel_inlet_1`, `fuel_inlet_2` | turuncu (0.85, 0.55, 0.15), kahverengi (0.55, 0.35, 0.1) | +y ve −y'deki yakıt borularının eğik uç yüzleri; taşıma havası ve yakıt |
| `wall` | gri (0.72, 0.72, 0.72) | geri kalan her yüz |

## Derived Properties

Adım hacimleri CFD Geometry'deki tabloda (kapalı form; dirseklerin ortak hacmi ve boruların gövde dışındaki hacmi sayısal integral; makro gövdeyi ‰1, küçük parçaların eklediği hacmi %1 ile doğrular).

Kutu: x ±(iniş + kol yarıçapı), y ±(yakıt borusu ucu), z 0 … dirseklerin tepesi; değerleri makro log'unda.

Ekipman hacmi Geometrik Ölçüler'deki tabloda (2500 kalsinatörü 659.85 m³). Twin'in kalsinatör bölgesi gövdenin farin girişinden tavana kadar olan kısmını, tesisin kaz boynunu ve iki C5'i tek bir kanal olarak çözer (`calciner.zone_segments`, [fluid_volumes.md](../fluid_volumes.md)). Farin girişinin altında yalnız fırın gazı ve tersiyer hava karışır; farin de yakıt da yoktur. Bu kısmın duvarı gövde segmentine eklenir. Bu düzenleme 15 Ekim 2026'dan beri böyle (`plant_geometry.calciner_above_feed`; twin akışlarıyla yapılan CFD koşusu, yukarıda).

## Twin'in çalışma düzeyi (15 Ekim 2026)

Twin'in kalsinatörü ILC bandının altında çalışıyor. Tablo, yerel CO₂ basıncına geçişten (commit 4672add) sonraki durumu gösteriyor.

| | Twin | ILC tipik |
|---|---|---|
| Fırına giren farinin kalsinasyonu | %83.3 | %90–95 |
| Gaz çıkış sıcaklığı | 1102 K | 1123–1173 K |
| Çıkışta p_CO₂ | 0.330 atm | — |
| Kalsinatörün yakıt payı | %60 | %55–60 |

**Sınırlayan denge, kinetik değil.**
- Gaz, çıkışın yerel basıncındaki denge sıcaklığına (T_eq 1103 K) iniyor ve kalsinasyon orada duruyor.
- Bu yüzden kalma süresi kalsinasyonu değiştirmiyor (farin girişi düzeltmesi: −5 g/s).
- Önceden model sabit 0.25 atm kullanıyordu; bu, düzlüğü 1087.7 K'de tutuyordu ve kalsinasyonu %85.5 gösteriyordu.
- Artık her hücre kendi çıkış gazının CO₂'sine karşı hesaplanıyor: fırın gazı + tersiyer hava + yanmış yakıt + o hücreye kadar salınan CO₂ (`CalcinationModel.cell_back_pressure`). p ilk hücrede 0.22, çıkışta 0.33.
- Fırının ters akımlı bölgeleri hâlâ sabit 0.25 atm'de.

**Enerji bütçesi** (tanılama D16, MW):

| Giren | | Çıkan | |
|---|---|---|---|
| fırın gazı (1325 K) | 42.6 | kalsinasyon | 101.2 |
| tersiyer hava (1237 K) | 45.2 | dehidroksilasyon | 0.04 |
| yakıt (3.17 kg/s) | 101.6 | duvar kaybı | 1.6 |
| farin (C4'ten) | 67.3 | gaz çıkışı | 97.5 |
| | | farin çıkışı | 56.4 |

- **%90 için gereken:** en az 9.1 MW ek reaksiyon ısısı, yaklaşık 0.28 kg/s kalsinatör yakıtı.
  - Bu bir alt sınır. Çıkışın denge sıcaklığının üstüne, gerçek kalsinatörlerdeki 20–70 K'lik paya çıkması ayrıca ısı ister: kabaca 30 K başına 6 MW (gaz 109 kg/s, farin 70 kg/s).
- **Girişler:** aşağıdaki VDZ karşılaştırmasında. Önceki "fırın gazı tipik 1373–1473 K" ifadesi yanlıştı. Bandın üst ucu, FLS'nin ayarlanmış 1441 K'siydi; kaynaklı değerler VDZ 1351 K ve CEJ 2019 1373 K.

### VDZ referans tesisine karşı (15 Ekim 2026)

**Referans:** CEMCAP D3.2 rev 2'deki VDZ BAT tesisi (Tablo 3.1, 3.5, 3.7, 3.8, 3.9):
- 3000 t/d, farin/klinker 1.6;
- beş kademeli ön ısıtıcı, ILC ve tersiyer kanal.

**Yöntem:**
- VDZ akışlarının entalpisi twin'in kendi gaz özellikleriyle hesaplandı (298.15 K'den duyulur).
- Twin'in klinkeri bağlı suyu çıkarılarak alındı: 56.90 kg/s.
- Betik repo dışında, oturum scratchpad'inde: `vdz_compare.py`.

| kJ/kg klinker | Twin | VDZ | Fark | MW |
|---|---|---|---|---|
| Fırın yakıtı | 1190 | 1149 | +41 | +2.3 |
| Kalsinatör yakıtı | 1785 | 1877 | −92 | −5.2 |
| Toplam (ısı tüketimi) | 2975 | 3026 | −51 | −2.9 |
| Fırın gazı (0.643 / 0.491 kg/kg; 1325 / 1351 K) | 749 | 606 | +143 | +8.2 |
| Tersiyer hava (0.776 / 0.750 kg/kg; 1237 / 1359 K) | 795 | 876 | −81 | −4.6 |
| **Kalsinatöre gaz tarafından giren** | **3329** | **3359** | **−30** | **−1.7** |
| Kalsinatör gaz çıkışı (1.915 / 1.812 kg/kg; 1102 / 1133 K) | 1713 | 1712 | +1 | +0.1 |

| | Twin | VDZ |
|---|---|---|
| Kalsinatör çıkışında y_CO₂ | 0.330 | 0.332 |
| Çıkışın T_eq'ten farkı | −1 K | +30 K |
| Kalsinatöre giren farinin kalsinasyonu | %9.2 (yalnız C5 tozu) | %18 |
| Fırına giren farinin kalsinasyonu | %83.3 | %95 |
| Egzoz | 1.931 kg/kg, 574 K | 1.892 kg/kg, 587 K |
| Fırının yakıt payı | 0.40 | 0.38 |

**Sonuç: kalsinatöre giren ısı VDZ'ninkiyle neredeyse aynı (−1.7 MW).**
- Twin'in fırın gazı daha soğuk ama daha fazla; tersiyer havası daha az ısı taşıyor. İkisi birbirini büyük ölçüde götürüyor.
- Fark talep tarafında: VDZ'de farin kalsinatöre %18 kalsine giriyor, twin'de %9.2.
  - Twin'in %9.2'si tamamen C5 tozu; ön ısıtıcıda kalsinasyon modeli yok (`apply_preheater` yalnız kurutma yapıyor).
  - VDZ'nin %18'i C5 tozu olabilir (alt kademe η ≈ 0.8 bunu verir) ya da C4 borusunda gerçek bir ön kalsinasyon. Belge ayırmıyor.
  - Bu ayrım kalsinatörün ne kadar iş yaptığını belirliyor: %9'luk fark ~0.11 kg CaCO₃/kg klinker, yani ~200 kJ/kg (~11 MW).

**Bulunan iki tutarsızlık:**
- **Bağlı su klinkerde kalıyor.**
  - Twin'in klinkeri 58.73 kg/s, bunun 1.83 kg/s'si bağlı su.
  - Dehidroksilasyon 0.04 kg/s salıyor; kil suyu 400–600 °C'de ön ısıtıcıda çıkmalı (zur Strassen ~110 kJ/kg klinker).
  - Bu yüzden twin'in "2882 kJ/kg"ı gerçek klinkere bölününce 2975.
- **Yakıt eski bir klinker potansiyeline göre kurulmuş.** `fuel.Fuel_rate_total` 5.29, 3100 kJ/kg'ı 54.63 kg/s'lik o günkü D11 klinker potansiyeline uygulayarak bulunmuş. Bugünkü gerçek klinker (bağlı su hariç) 56.90 kg/s.

### Bağlı su düzeltildikten sonra (15 Ekim 2026, commit 2c95c26, b0baa52)

**Ne değişti:**
- Kil suyu artık ön ısıtıcıda çıkıyor: 1.52 kg/s ön ısıtıcıda, 0.35 kg/s kalsinatörde.
- Kinetik Cheng ve diğ. 2021'den, entalpi oksit yolundan (3.84 MJ/kg su).
- Klinkerde bağlı su kalmadı: klinker 56.90 kg/s, ısı tüketimi 2975 kJ/kg.

**Etkisi:**
- Reaksiyon ısısı (~7 MW) ön ısıtıcıdan çekiliyor; C4 farini 1018 K'den 981 K'ye soğuyor.
- Kalsinatörün CO₂'si 24.99'dan 22.28 kg/s'ye, fırına giren farinin kalsinasyonu %83.3'ten %74.3'e düşüyor.
- Fırın daha fazla kalsinasyon yapıyor; yanma bölgesinin yatak tepe sıcaklığı 1931 K'den 1755 K'ye iniyor.
- Fırın gazı 1301 K, egzoz 562 K.
- Bu, fiziksel olarak doğru bir kayıp. VDZ ile fark büyüdü (%74'e karşı %95). Yakıt tutarlılığı ve VDZ'nin %18'inin anlamı açık kararlar olarak duruyor.

**Yakınsama:** bu durumda twin 2-döngüye girdi. Yanma bölgesinde kalsinasyon endotermi sönümleniyor, ona bağlı belit ekzotermi sönümlenmiyordu. Reaksiyon ısısının tamamı aynı ağırlıkla sönümlenince twin 115 taramada yakınsıyor; sabit nokta sönümleme ağırlığından bağımsız.

### Yakıt tutarlılığı ve fırın payı (15 Ekim 2026, commit 7e1be55)

**Defter** (kJ/kg gerçek klinker, twin'e karşı VDZ, bağlı su düzeltmesinden sonra):
- Kalsinatöre gaz tarafından giren ısıda tersiyer hava −184 ile fırın gazı +178 birbirini götürüyor; kalsinatör yakıtı −92.
- Twin'in fırını daha fazla hava fazlasıyla çalışıyor: fırın girişinde O₂ %2.8, VDZ'de %1.5.

**Hipotezler** (scratchpad koşuları):

| | Kalsinasyon | Yakınsama | Yatak tepe sıcaklığı |
|---|---|---|---|
| Başlangıç | %74.3 | evet | 1755 K |
| H1: fırın havası O₂ %1.5'e göre | ~%77 | hayır | 1902 K |
| H2: 3100 kJ/kg gerçek klinkerde | %85.2 | evet | 2030 K |
| H3: H1 + H2 | %84.1 | evet | 2037 K |
| **H4: H2 + VDZ'nin fırın payı 0.380** | **%87.2** | evet | 2033 K |

**Seçilen H4** (kullanıcı kararı):
- `Fuel_rate_total` 5.513 kg/s: 3100 kJ/kg × 56.90 kg/s gerçek klinker.
- `kiln_fraction` 0.380, VDZ'den.
- Sonuç: kalsinatör çıkışı 1102 K; fırın gazı 1343 K (VDZ 1351); egzoz 572 K.

**Açık kalan:** yanma bölgesindeki yatak 2033 K'ye ısınıyor (gerçek tesiste ~1723 K). Önceki 1755 K, fırının fazladan kalsinasyon yapmasının yan etkisiydi. %90'a 3.9 MW kalıyor.

## Kaynaklar

| Anahtar | Kaynak |
|---|---|
| CEMCAP D3.2 | CEMCAP framework for comparative techno-economic analysis of CO2 capture from cement plants, D3.2 rev 2 (VDZ BAT reference plant), 2018 — <https://zenodo.org/records/1257112> |
| Cheng 2021 | Cheng S., Jiu S., Li H., Kinetics of dehydroxylation and decarburization of coal series kaolinite during calcination, Materials 14 (2021) 1493 — <https://doi.org/10.3390/ma14061493> |
| Robie & Hemingway 1995 | Thermodynamic properties of minerals and related substances at 298.15 K and 1 bar, USGS Bull. 2131 |
| Mikulčić 2012 | Mikulčić H. ve diğ., CFD analysis of a cement calciner for a cleaner cement production, Chem. Eng. Trans. 29 (2012) 1513–1518 — <https://www.aidic.it/cet/12/29/253.pdf> |
| Kahawalage 2017 | Kahawalage A.C., Melaaen M.C., Tokheim L.-A., Numerical modelling of the calcination process in a cement kiln system, SIMS 58 (2017) — <https://ep.liu.se/ecp/138/011/ecp17138011.pdf> |
| CPFD 2025 | CPFD modeling of an industrial oxy-fuel cement calciner, Energies 18 (2025) 6419 — <https://doi.org/10.3390/en18246419> |
| Chanamai 2019 | Chanamai P., Rodkwan S., Numerical simulation of gas-solid flow in a cement precalciner using AMR, JCST 9(2) (2019) 107–122, Tablo 1 |
| Fidaros 2007 | Fidaros D.K. ve diğ., Powder Technol. 171 (2007) 81–95 |
| Holcim StDC 2022 | Holcim Standard Design Criteria, Mechanical Equipment, March 2022 |
| FLS | arXiv 2504.02886, Tablo 8 |
| PF5000 | Jiangsu Pengfei, 5000 t/d hattı — <https://jspengfei.en.made-in-china.com/product/BewmtGNcXDha/China-5000t-D-Cement-Production-Line.html> (değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı) |
