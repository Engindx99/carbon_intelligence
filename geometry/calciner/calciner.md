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

Fidaros ve diğ. 2007 farini **iki** Ø0.6 m borudan, yatayla 60° eğimle verir; kömürü iki Ø0.2 m borudan, 30° eğimle. Burada her boru bir hattın C4 farinini taşır. Farin boruları 5. adımda kuruldu, yakıt portu 7. adımda kurulacak.

## CFD Geometry

Makro: [`geometry/macros/calciner.bas`](../macros/calciner.bas). Yapım adım adım ilerler. **Şu an kurulu olanlar**: gövde (1. adım), Y kaz boynu (2–4. adımlar) ve iki farin besleme borusu (5. adım). Henüz dışa aktarım yapılmaz.

Koordinatlar: eksen **z**, fırın gazı giriş yüzü (boğazın altı) **z = 0**.

```
boğaz      Ø3.130, z = 0 .. 3.130       (THROAT_LEN_OVER_D = 1.0, modelleme parametresi)
koni       65°, z = 3.130 .. 7.001
silindir   Ø6.740, z = 7.001 .. 33.130  (düz tavan)
kaz boynu  boyun Ø4.950, eksende, z = 33.130 .. 39.317
           2 kol × Ø3.50, x–z düzleminde ayna simetrik; başlangıç diskleri x = ±0.725
           (boynun içinde, kendi tarafında boynun kenarına teğet)
           180° dirsek, R = 5.25, tepe z = 46.317
           iniş x = ±11.225, z = 39.317 .. 18.130 (gövdenin yarı yüksekliği) → gas_outlet_1 (+x), gas_outlet_2 (−x)
farin      2 × Ø0.849, 60°, ±x'te (y = 0 düzleminde, her inişin altında), eksen gövdeden dışarı doğru yükselir:
           eksenler duvarı z = 16.130'da keser (çıkış yüzlerinin 2.0 m altı)
           uç yüzleri (±3.870, 0, 16.996) → meal_feed_1 (+x), meal_feed_2 (−x)
```

Boğazın koni altındaki boyu bir tesis ölçüsü değildir. Giriş yüzünü koninin ağzına değil, düz bir parçanın üstüne koymak için seçilmiş bir modelleme parametresidir.

**Y kaz boynu** (kullanıcı kararı, 12 Ekim 2026). Her kol bir hattın C5'ine iner ve o hattın bütün gazını taşır; yayınlanmış 2500 t/d boynunun çapı (Ø3.50) bu yüzden her kola düşer.
- **Neden tek boyun.** İki Ø3.50 boru Ø6.74'lük tavana yan yana sığmaz (7.0 > 6.74 m). Tavandan tek bir boyun çıkar; kesiti iki kolun toplamıdır (Ø4.95), hız korunur. 2500 kalsinatöründe bunun yerine iki kol tavandan ayrı çıkıyordu, her biri alanın yarısıyla (29 Eylül 2026).
- **Ayrım.** Boynun tepesinde iki kol başlar. Her kolun başlangıç diski boynun içindedir ve kendi tarafında boynun kenarına teğettir: x = ±(r_boyun − r_kol) = ±0.725. İki disk ortada üst üste biner. Disklerin örtmediği yerde (boyun kesitinin ~%24'ü, ±y'de) boynun tepesi düz bir tavandır.
- **Ortak hacim.** İki dirsek boyunun hemen üstünde, z = 39.317 .. ~42.96 arasında **10.346 m³** paylaşır. Kapalı biçimi yoktur; makro bunu 80³ noktalı orta nokta kuralıyla hesaplar (`GnBendOverlap`). Bağımsız bir Monte Carlo sağlaması 10.354 ± 0.010 m³ verdi.
- **Boylar modelleme parametresidir.** Yükseliş 1.25 × boyun çapı, dirsek yarıçapı 1.5 × kol çapı (C1 makrosunun oranları). İnişler gövdenin yanında, **gövdenin yarı yüksekliğine** kadar sarkar: z = 3.130 + 30.00/2 = 18.130 (kullanıcı kararı, 29 Eylül 2026). Böylece çıkış yüzü dirsekten uzakta, düzelmiş bir akışın üstünde durur; C1'de düz borunun ucundaki çıkış yüzünde %38 geri akış ölçülmüştü.
- **Yön ölçülür, varsayılmaz.** Bir extrude yanlış yöne giderse ya gövde sayısı ya da hacim bunu söyler; bir dirsek yanlış dönerse hacim ve kutunun tepesi söyler. Bu durumda feature silinir ve diğer yön denenir.

**Farin besleme boruları** (kullanıcı kararı, 29 Eylül 2026). Gövdenin iki yanında, kaz boynuyla aynı x–z düzleminde ±x'te, her inen borunun altında dururlar. Boru uçları (|x| ≤ 4.24) inen boruların iç duvarından (|x| = 9.475) uzaktadır; bunu bir ön kontrol zorlar.
- **Ölçüler ve yön.** Eğim Fidaros 2007'den; çap onun Ø0.6'sı × √2 (her boru bir 2500 hattının farinini taşır). Her boru gövde eksenine bakar ve duvardan uzaklaştıkça yükselir, böylece farin ortaya doğru düşer.
- **Yükseklik.** Boru eksenleri duvarı, kaz boynu çıkış yüzlerinin `FEED_BELOW_GN_OUT = 2.0 m` altında keser: z = 16.130. Borunun tamamı çıkış yüzlerinin altında kalır; en üst noktası z = 17.208'dir.
- **Boy.** Boru gövde ekseninden başlar; başlangıç diski gövdenin içinde kalır ve birleşimde erir. Duvardan eksen boyunca `FEED_DEPTH = 1.0 m` dışarı çıkar (C1 oluğu gibi). Uç yüzün tamamen dışarıda kalması için bu değer r·tan 60° = 0.73 m'yi aşmalıdır.
- **Nasıl kurulur.** x = 0 düzlemindeki yarım kesit dikdörtgeni, kendi eksen kenarı etrafında tam tur döndürülür. Tam turun yanlış gidebileceği bir yönü yoktur; hangi tarafa düştüğünü ±x'te bulunan uç yüzü söyler.
- **Hacim.** Gövde dışında kalan kısım boru başına πr²L − (1/cos θ)·2∫√(r²−a²)√(R²−a²) da = **0.57301 m³**. İntegral eliptiktir; makro a = r sin φ dönüşümüyle Simpson kuralıyla hesaplar. Bu hacim ~1869 m³'lük domenin ‰1'inin altında, yani toplam hacim kontrolü boruyu göremez. Bu yüzden her boru için ayrıca şunlar kontrol edilir: eklenen hacim %1 toleransla, uç yüzü beklenen tarafta bulunmalı ve alanı 0.5654 m² olmalı.

Planlanan adımlar:
1. gövde (revolve)
2. \+ boyun
3. \+ iki 180° dirsek (3a: +x, 3b: −x)
4. \+ iki iniş borusu
5. \+ iki farin besleme borusu (5a: +x, 5b: −x)
6. \+ tersiyer kanal (Ø2.439, teğetsel, dil ile)
7. \+ yakıt portu
8. sınır yüzü etiketleme ve export → `geometry/output/2500/calciner.*` (klasör adı makronun `LINE_KEY`'i; tesis 5000 t/d)

## Boundary Faces

| Sınır | Durum |
|---|---|
| `kiln_gas_inlet` | z = 0 diski, 7.695 m² (1. adımdan beri var, henüz boyanmıyor) |
| `gas_outlet_1`, `gas_outlet_2` | +x ve −x'teki inişlerin aşağı bakan diskleri, z = 18.130, her biri 9.621 m². Ayrı renkler, 8. adımda boyanır; x'in işaretiyle ayırt edilir. Her biri bir hattın C5'ini besler ([cyclone_C5.md](../preheater/cyclone_C5.md)); bağ bu yüzler üzerinden kurulur, C5 bu domene katılmaz |
| `meal_feed_1`, `meal_feed_2` | +x ve −x'teki boruların eğik uç yüzleri, her biri 0.5654 m². Gaz için duvar, DPM için enjeksiyon yüzeyi (C1'deki gibi) |
| `tertiary_air_inlet`, `fuel_inlet` | 6–8. adımlar |

## Derived Properties

Adım hacimleri (kapalı form; dirseklerin ortak hacmi sayısal; makro ‰1 ile doğrular):

```
boğaz           24.085 m³
koni            77.357 m³
silindir       932.354 m³
gövde         1009.711 m³   (koni + silindir)
1  domen      1033.797 m³
2  + boyun    1152.852 m³   (119.055)
3a + dirsek   1311.537 m³   (Pappus, her biri 158.685)
3b + dirsek   1459.876 m³   (158.685 − ortak 10.346)
4  + iniş     1867.565 m³   (2 · 203.845)
5a + farin +x 1868.138 m³   (boru başına 0.57301; ayrıca %1 ile kontrol edilir)
5b + farin −x 1868.711 m³
```

Kutu: x ±12.975, y ±3.370, z 0 … 46.317 (farin boruları kutuyu değiştirmez).

Ekipman hacmi Geometrik Ölçüler'deki tabloda (2500 kalsinatörü 659.85 m³). Twin'in kalsinatör bölgesi bu gövdeyi, tesisin kaz boynunu ve iki C5'i tek bir kanal olarak çözer (`calciner.zone_segments`, [fluid_volumes.md](../fluid_volumes.md)).

## Kaynaklar

| Anahtar | Kaynak |
|---|---|
| Mikulčić 2012 | Mikulčić H. ve diğ., CFD analysis of a cement calciner for a cleaner cement production, Chem. Eng. Trans. 29 (2012) 1513–1518 — <https://www.aidic.it/cet/12/29/253.pdf> |
| Kahawalage 2017 | Kahawalage A.C., Melaaen M.C., Tokheim L.-A., Numerical modelling of the calcination process in a cement kiln system, SIMS 58 (2017) — <https://ep.liu.se/ecp/138/011/ecp17138011.pdf> |
| CPFD 2025 | CPFD modeling of an industrial oxy-fuel cement calciner, Energies 18 (2025) 6419 — <https://doi.org/10.3390/en18246419> |
| Chanamai 2019 | Chanamai P., Rodkwan S., Numerical simulation of gas-solid flow in a cement precalciner using AMR, JCST 9(2) (2019) 107–122, Tablo 1 |
| Fidaros 2007 | Fidaros D.K. ve diğ., Powder Technol. 171 (2007) 81–95 |
| Holcim StDC 2022 | Holcim Standard Design Criteria, Mechanical Equipment, March 2022 |
| FLS | arXiv 2504.02886, Tablo 8 |
| PF5000 | Jiangsu Pengfei, 5000 t/d hattı — <https://jspengfei.en.made-in-china.com/product/BewmtGNcXDha/China-5000t-D-Cement-Production-Line.html> (değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı) |
