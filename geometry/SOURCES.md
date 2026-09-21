# Geometri kataloğu: kaynak tablosu

Bu dosya `geometry/catalog.py` içine girecek her ölçünün nereden geldiğini gösterir. Kataloğa burada olmayan bir değer girmez.

## Temel kural

Her alan şu durumlardan birindedir:

| Durum | Anlamı |
|---|---|
| `published` | Kaynakta doğrudan yazan değerdir. `ref` alanı kaynağı gösterir. |
| `derived_from_reference` | Hattın yayınlanmış bir ölçüsü ile FLS referans kulesinin boyutsuz bir oranı çarpılarak bulunur. `ref` hem hattın kaynağını hem de oranın adını taşır. Yalnızca aşağıdaki oran tablolarında adı geçen oranlar kullanılır. |
| `model_assumption` | Kaynakta yazar, ama ölçülmüş bir değer değil, kaynağın kendi modelleme varsayımıdır. Yalnızca FLS'nin giriş genişliği `w_in = 0.4 r_c` ve buna bağlı giriş yüksekliği için kullanılır. |
| yok (`None`) | Kaynakta bulunamamıştır. Değer uydurulmaz, alan boş kalır. |

Bir değer, durumundan ayrı olarak **varsayım notları** (`assumptions`) da taşıyabilir. Bu notlar değerin dayandığı aktarım ya da model varsayımlarını açıkça yazar: çift C1'e aktarım ve `w_in` model varsayımı. Riser eşlemesi artık bir varsayım değildir; FLS Tablo 7'de açıkça yazılıdır (aşağıda uyarı 3). Rapor bunları değerin yanında gösterir.

Kapasite, debi, hız, alan ya da kalma süresi üzerinden hiçbir ölçü hesaplanmaz. Örneğin HFC'nin yayınladığı "6.9 m/s × 3.19 s" çarpımından kalsinatör boyu **türetilmez**.

Bütün uzunluklar metredir. Akışkan hacmi, **refrakterin iç yüzeyi** yani efektif iç çap üzerine kurulur. Satıcıların verdiği Φ ise çelik gövdenin iç çapıdır (壳体内径).

## Kaynaklar

Hepsi 2026-09-21'de kontrol edildi.

| ID | Kaynak | İçerik | Doğrulama |
|---|---|---|---|
| **PF1500** | Jiangsu Pengfei, 1500 t/d hattı. <http://www.cementplant-engineering.com/products/cement-production-line/77.html> | Fırın Φ3.5×54 m, %4, 0.4–3.96 rpm. C1 2-Φ4300, C2 Φ5600, C3 Φ5600, C4 Φ5900, C5 Φ5900 mm. Tek dizi, beş kademe, CDC tipi. Kalsinatör (分解炉) Φ6300 mm, yüksekliği yazılmamış. Soğutucu ızgarasının etkin alanı 61.8 m² | Sayfanın ham metni okundu |
| **PF2500** | Jiangsu Pengfei hattı. Sayfa başlığı "3000tpd", ama fırın sistemi 2500 t/d. <https://www.cementmachinery.com/Cement_Machinery/products/Production_line_EP_EPC/Cement_Production_Line/2020/0331/2670.html> | Fırın Φ4.0×60 m, %4, 0.39–4.10 rpm. C1 2-Φ4600, C2 Φ6500, C3 Φ6500, C4 Φ6800, C5 Φ6800 mm. Kalsinatör Φ5050×30000 mm (2500 t/d). Soğutucu LBT2500, 65 m² | Sayfadan alıntı yapıldı |
| **HFC2500** | Hefei Enstitüsü, "HFC2500t/d预热器分解炉系统装备的设计", 2005. <https://m.ccement.com/news/content/700825.html> | Beş kademe. C1 çift siklon, diğer kademeler tekli. Kademe başına gövde iç çapı **ve efektif iç çap** (有效内径). C2–C5 çıkış kanalları, kalsinatör ve kaz boynu (鹅颈管) | Ham metindeki tablo okundu |
| **PF5000** | Jiangsu Pengfei, 5000 t/d hattı. <https://jspengfei.en.made-in-china.com/product/BewmtGNcXDha/China-5000t-D-Cement-Production-Line.html> | Fırın Φ4.8×74 m, %4, 0.6–4.0 rpm. C1 4-Φ5.0, C2 2-Φ6.9, C3 2-Φ6.9, C4 2-Φ7.2, C5 2-Φ7.2 m (çift dizi). Kalsinatör Φ7.2×30.0 m. Soğutucu LBT36352, 119.6 m² | Sayfadan alıntı yapıldı |
| **FLS** | Svensen et al., FLSmidth referans senaryosu, arXiv 2504.02886, Tablo 8 (aynı siklon verisi arXiv 2409.10916, Tablo II'de de var). <https://arxiv.org/abs/2504.02886> | Tek dizi, beş kademe. Siklon, riser, kalsinatör, fırın ve soğutucu için iç yarıçap (r_c) ve refrakter yarıçapı (r_r) | PDF metni çıkarıldı |

Kaynak doğrulandı ama kataloğa **girmeyen** değerler:
- **Tersiyer hava kanalı çapları:** 2500 hattı için AGICO'nun bir tesisinde 2.2 m, 1500'e büyütülmüş bir tesiste Φ1577 mm efektif. İkisi de tek bir tesisin değeri ve yalnızca özetleyici bir araçla okundu; ham metinleri doğrulanmadı.
- **3000–3200 t/d siklon seti:** kaynak sayfası artık 404 veriyor.
- **İki tesisin kaz boynu ölçüleri:** başka tesislere ve başka kalsinatör tasarımlarına ait; gerekçe "Kaz boynu: bulundu, hiçbir hatta atanmadı" bölümünde.

## FLS referans oranları

Bu oranlar yalnızca `derived_from_reference` alanlarında kullanılır. D, efektif iç çaptır (2·r_c).

| Oran (FLS Tablo 8) | Cy1 | Cy2 | Cy3 | Cy4 | Cy5 |
|---|---|---|---|---|---|
| `eff_over_shell` = r_c/r_r | 0.961 | 0.950 | 0.942 | 0.939 | 0.947 |
| `barrel_h/D` = (h_t−h_c)/D | 1.572 | 0.601 | 0.510 | 0.548 | 0.544 |
| `cone_h/D` = h_c/D | 1.077 | 1.067 | 1.152 | 1.158 | 1.143 |
| `vortex_len/D` = h_x/D | 0.500 | 0.500 | 0.500 | 0.503 | 0.500 |
| `vortex_D/D` = r_x/r_c | 0.557 | 0.713 | 0.734 | 0.735 | 0.729 |
| `dust_D/D` = r_d/r_c | 0.093 | 0.132 | 0.133 | 0.128 | 0.127 |
| `inlet_w/D` = w_in/D | 0.200 | 0.201 | 0.200 | 0.201 | 0.201 |
| `inlet_h/D` = (A_in/w_in)/D | 1.150 | 1.428 | 1.501 | 1.498 | 1.475 |

| Riser oranı | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| `riser_D/D_src` = D_riser / D(çıktığı siklon, C(k+1)) | 0.718 | 0.725 | 0.726 | 0.720 |

Riserin boyu, uç konisi ve uç çapı için oran **tanımlanmamıştır**. Bunlar yalnızca FLS hattında, yayınlanmış değer olarak bulunur. Diğer hatlarda `None` kalır.

Kalsinatör ve fırın oranları:
- Kalsinatör: `calciner_eff_over_shell` = 3.08/3.29 = **0.936**, `calciner_H/D` = 33.00/6.16 = **5.357**.
- Fırın: `kiln_eff_over_shell` = 1.98/2.18 = **0.908**.

**Oranlar için uyarılar:**
1. **Cy1 tek, büyük bir üst siklondur.** Holderbank da FLS'nin tek üst siklonlu tesisler kurduğunu not eder. Satıcı hatlarında ise C1 çift siklondur. Cy1 oranlarını çift C1'e uygulamak bir **aktarım varsayımıdır**.
2. **`w_in = 0.4 r_c` makalenin kendi modelleme varsayımıdır, ölçülmüş bir değer değildir.** Buradan çıkan `inlet_h` değeri Cy2–Cy5'te gövde yüksekliğinin yaklaşık 2.5 katıdır, yani giriş koni bölgesine uzanır. HFC'nin "270° eğik volüt, kısaltılmış C2–C4 gövdesi" tarifiyle tutarlı olsa da açık bir varsayım olarak işaretlenir.
3. **Riser eşlemesi kaynakta yazılıdır** (arXiv 2504.02886 v1, Tablo 7, s. 13; 2026-09-21'de PDF metninden doğrulandı). Tablo 7 bağlantıları "To\From" matrisiyle verir. R1 satırı gazını Cy2'nin çıkışından alır (`Ax,cy2/Ain,r1`), Cy1 satırı R1'den beslenir (`Aout,r1/Ain,cy1`); R2–R4 de aynı düzendedir. Yani R_k gazı Cy(k+1)'in çıkışından Cy(k)'ye taşır. Önceki sürümde bu bir çıkarım olarak işaretliydi. Artık FLS riser değerleri Tablo 7'ye atıf yapar. `riser_D/D_src` oranının dayandığı eşleme de doğrudan kaynaktadır; bu yüzden oranla doldurulan riser çapları (1500, 5000) eşleme varsayımı taşımaz. Hiçbir sayısal değer değişmedi.
4. **R5 (61 m, r = 1.13 m) makalede adlandırılmamıştır.** Tablo 7'ye göre gazını soğutucudan alır ve kalsinatöre verir. Metin şöyle der: "Ay2,co connects to the tertiary pipe" ve "Py2 = Pin,r5" (bölüm 3.10, denklem 90b). Buradan R5'in tersiyer hava borusu olduğu **çıkarılabilir**, ama makale bunu açıkça söylemez. Tersiyer kanal kapsam dışı olduğu için (Kararlar, 3) R5 kullanılmaz.
5. **Riser oranı, kanalın çıktığı siklonun çapına göre alınır.** Beslediği siklona göre alınsaydı, satıcı hatlarındaki çift C1 R1'i olması gerekenden küçük gösterirdi, çünkü R1 ayrılmadan önce gazın tamamını taşır. FLS oranı (≈0.72), HFC2500'ün yayınlanmış oranından (0.50–0.55) belirgin biçimde büyüktür. Oranla doldurulan riserler bu yüzden daha düşük gaz hızına göre tasarlanmış bir kuleyi temsil eder.

## Hat tabloları

Kısaltmalar: **P** = `published`, **R** = `derived_from_reference`, **—** = yok.

### 2500 t/d (varsayılan `reference_line`)

Önhısıtıcı ve kalsinatör **HFC2500**'den gelir, çünkü efektif iç çapları yayınlayan tek kaynak odur. Fırın ve soğutucu **PF2500**'den gelir. Karşılaştırma: PF2500'ün gövde çapları (C1 2-Φ4.6, C2–C3 Φ6.5, C4–C5 Φ6.8) HFC'nin gövde çaplarından en fazla %2 farklıdır. Kataloğa HFC seti girer.

| Alan | Değer [m] | Durum | ref |
|---|---|---|---|
| Fırın gövde Φ × L | 4.0 × 60 | P | PF2500 |
| Fırın efektif Φ | 3.633 | R | PF2500 × `kiln_eff_over_shell` |
| Fırın eğimi / hızı | %4 / 0.39–4.10 rpm | P | PF2500 |
| Soğutucu ızgara alanı | 65 m² | P | PF2500 |

| Siklon | adet | gövde Φ (P) | efektif D (P) | gövde h (R) | koni h (R) | vorteks L (R) | vorteks D (R) | toz çıkışı D (R) | giriş w × h (R) |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 2 | 4.70 | 4.32 | 6.79 | 4.65 | 2.16 | 2.40 | 0.40 | 0.86 × 4.97 |
| C2 | 1 | 6.60 | 6.10 | 3.67 | 6.51 | 3.05 | 4.35 | 0.80 | 1.23 × 8.71 |
| C3 | 1 | 6.80 | 6.30 | 3.22 | 7.26 | 3.15 | 4.62 | 0.84 | 1.26 × 9.46 |
| C4 | 1 | 6.80 | 6.30 | 3.46 | 7.30 | 3.17 | 4.63 | 0.81 | 1.27 × 9.44 |
| C5 | 1 | 7.00 | 6.50 | 3.53 | 7.43 | 3.25 | 4.74 | 0.83 | 1.30 × 9.59 |

| Kanal | gövde Φ (P) | efektif D (P) | boy L | üst koni L | uç D |
|---|---|---|---|---|---|
| C2 çıkışı → C1 (R1) | 3.45 | 3.07 | — | — | — |
| C3 çıkışı → C2 (R2) | 3.85 | 3.35 | — | — | — |
| C4 çıkışı → C3 (R3) | 3.95 | 3.45 | — | — | — |
| C5 çıkışı → C4 (R4) | 4.10 | 3.60 | — | — | — |
| Kalsinatör | 6.00 | 5.50 | H = 29.46 (R, `calciner_H/D`) | — | — |
| Kaz boynu (kalsinatör → C5) | 4.00 | 3.50 | — | — | — |

Siklon satırlarındaki R değerleri FLS oranlarından gelir ve bu oranlar iki varsayım taşır:
- C1 değerleri, FLS'nin tek üst siklonundan (Cy1) çift C1'e yapılan bir **aktarım varsayımına** dayanır.
- Giriş w × h, FLS'nin `w_in` **model varsayımına** dayanır.

### 1500 t/d

Tek kaynak **PF1500**'dür. Yalnızca gövde çapları yayınlanmış; bu yüzden bütün efektif çaplar R durumundadır.

| Alan | Değer [m] | Durum | ref |
|---|---|---|---|
| Fırın gövde Φ × L | 3.5 × 54 | P | PF1500 |
| Fırın efektif Φ | 3.179 | R | `kiln_eff_over_shell` |
| Fırın eğimi / hızı | %4 / 0.4–3.96 rpm | P | PF1500 |
| Soğutucu ızgara alanı | 61.8 m² | P | PF1500 |
| Kalsinatör gövde Φ | 6.30 | P | PF1500 |
| Kalsinatör efektif D / H | 5.898 / 31.60 | R / R | `calciner_eff_over_shell`, `calciner_H/D` |

| Siklon | adet | gövde Φ (P) | efektif D (R) | gövde h | koni h | vorteks L | vorteks D | toz çıkışı D | giriş w × h |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 2 | 4.30 | 4.132 | 6.50 | 4.45 | 2.07 | 2.30 | 0.38 | 0.83 × 4.75 |
| C2 | 1 | 5.60 | 5.319 | 3.20 | 5.68 | 2.66 | 3.79 | 0.70 | 1.07 × 7.59 |
| C3 | 1 | 5.60 | 5.272 | 2.69 | 6.08 | 2.64 | 3.87 | 0.70 | 1.05 × 7.91 |
| C4 | 1 | 5.90 | 5.537 | 3.04 | 6.41 | 2.78 | 4.07 | 0.71 | 1.11 × 8.30 |
| C5 | 1 | 5.90 | 5.584 | 3.04 | 6.38 | 2.79 | 4.07 | 0.71 | 1.12 × 8.24 |

Kanalların hiçbir ölçüsü yayınlanmamış. Yalnızca efektif çap **R** olarak doldurulur (`riser_D/D_src`); boy, uç konisi ve uç çapı `None` kalır.

| Kanal | efektif D (R) | boy L | üst koni L | uç D |
|---|---|---|---|---|
| C2 çıkışı → C1 (R1) | 3.82 | — | — | — |
| C3 çıkışı → C2 (R2) | 3.82 | — | — | — |
| C4 çıkışı → C3 (R3) | 4.02 | — | — | — |
| C5 çıkışı → C4 (R4) | 4.02 | — | — | — |

Kaz boynu için kaynak yok.

### 5000 t/d

Tek kaynak **PF5000**'dir. **Çift dizidir**: C1 dört siklon, C2–C5 ikişer siklondur.

| Alan | Değer [m] | Durum | ref |
|---|---|---|---|
| Fırın gövde Φ × L | 4.8 × 74 | P | PF5000 |
| Fırın efektif Φ | 4.360 | R | `kiln_eff_over_shell` |
| Fırın eğimi / hızı | %4 / 0.6–4.0 rpm | P | PF5000 |
| Soğutucu ızgara alanı | 119.6 m² | P | PF5000 |
| Kalsinatör gövde Φ × H | 7.2 × 30.0 | P | PF5000 |
| Kalsinatör efektif D | 6.740 | R | `calciner_eff_over_shell` |

| Siklon | adet | gövde Φ (P) | efektif D (R) | gövde h | koni h | vorteks L | vorteks D | toz çıkışı D | giriş w × h |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 4 | 5.0 | 4.805 | 7.56 | 5.17 | 2.40 | 2.67 | 0.45 | 0.96 × 5.53 |
| C2 | 2 | 6.9 | 6.554 | 3.94 | 7.00 | 3.28 | 4.67 | 0.86 | 1.32 × 9.36 |
| C3 | 2 | 6.9 | 6.496 | 3.32 | 7.49 | 3.25 | 4.77 | 0.86 | 1.30 × 9.75 |
| C4 | 2 | 7.2 | 6.757 | 3.71 | 7.83 | 3.40 | 4.97 | 0.87 | 1.36 × 10.12 |
| C5 | 2 | 7.2 | 6.815 | 3.71 | 7.79 | 3.41 | 4.97 | 0.87 | 1.37 × 10.05 |

Kanallarda yalnızca efektif çap **R** olarak doldurulur ve dizi başına verilir. Boy, uç konisi ve uç çapı `None` kalır.

| Kanal | efektif D (R) | boy L | üst koni L | uç D |
|---|---|---|---|---|
| C2 çıkışı → C1 (R1) | 4.71 | — | — | — |
| C3 çıkışı → C2 (R2) | 4.71 | — | — | — |
| C4 çıkışı → C3 (R3) | 4.91 | — | — | — |
| C5 çıkışı → C4 (R4) | 4.91 | — | — | — |

Kaz boynu için kaynak yok.

### FLS referans kulesi (bağımsız hat)

Değerler FLS Tablo 8'den **P** olarak alınır ve efektif iç ölçüdür. Aritmetik dönüşümler (D = 2·r_c, gövde h = h_t − h_c) yayınlanmış değer sayılır.
- **Siklonlar:** yukarıdaki oran tablosunun ham değerleri. Giriş alanı A_in **P**'dir. Giriş genişliği w_in ve giriş yüksekliği A_in/w_in ise **`model_assumption`**'dır.
- **Riserler R1–R4:** D = 4.90 / 4.90 / 5.10 / 5.10 m, L = 21.38 / 19.38 / 20.37 / 19.87 m. Üst koni ve uç çapı da tabloda yayınlanmış. Hangi riserin hangi iki siklonu bağladığı Tablo 7'de yazılıdır (uyarı 3).
- **Kalsinatör:** Φ6.16 × 33.0 m.
- **Fırın:** Φ3.96 × 51 m (efektif), 4 rpm.
- **Soğutucu:** 36 × 4 m.

Kapasite yayınlanmamış. Makale yalnızca besleme debisini veriyor: 85.7 kg/s farin. Kaz boynu yoktur: Tablo 7 kalsinatör çıkışını doğrudan Cy5'e bağlar. R5 muhtemelen tersiyer borudur (uyarı 4) ve kullanılmaz.

## Açık belirsizlikler

### FLS riser geometrisi: metin ile denklemler çelişiyor

Riser **hacmi hesaplanmaz**. Kaynak netleşene kadar iki okumadan hiçbiri doğru kabul edilmez (kullanıcı kararı, 2026-09-21).

**Metin** (arXiv 2504.02886, bölüm 3.5.2):

> "The risers are cylinders with angled pipes on top. The angled pipes are modeled as truncated cones, where the height of the cones equals the pipe length and the top areas equal the cross-sectional area of the pipes' end."

**Denklemler (32)–(34)** kesit hacmini silindir + üst koni (h_cu, r_u) + alt koni (h_cl, r_l) olarak kurar. Makale ayrıca "h_cl is zero for the risers" der.

**Tablo 8'in riser satırları** ise şöyledir:

| | h_tot | h_cl | h_cu | r_c | r_l | r_u |
|---|---|---|---|---|---|---|
| R1 | 21.38 | 4.83 | 0 | 2.45 | 2.45 | 1.72 |
| R2 | 19.38 | 4.18 | 0 | 2.45 | 2.45 | 1.90 |
| R3 | 20.37 | 4.18 | 0 | 2.55 | 2.45 | 1.90 |
| R4 | 19.87 | 4.37 | 0 | 2.55 | 2.45 | 1.99 |

Çelişkiler:
1. Metin risers için h_cl = 0 der, tablo ise h_cl > 0 verir.
2. Metinde "üstte koni" vardır, ama tabloda üst koninin boyu h_cu = 0'dır.
3. Tabloyu denklemlere olduğu gibi koyunca üst koni hiç oluşmaz. Alt koni de R1 ve R2'de r_l = r_c olduğu için düz silindirdir; R3 ve R4'te ise r_c'den r_l'ye hafifçe daralan bir koni olur. Hiçbir riserde r_u kullanılmaz, yani metnin anlattığı "uca doğru daralan koni" ortaya çıkmaz.

İki okumanın hacim farkı (yalnızca bu belge için hesaplandı, kodda kullanılmıyor):

| | Silindir D × h_tot [m³] | Metin okuması: silindir (h_tot − h_cl) + koni D → 2r_u, boyu h_cl [m³] | Fark |
|---|---|---|---|
| R1 | 403.2 | 378.7 | −6.1 % |
| R2 | 365.5 | 349.1 | −4.5 % |
| R3 | 416.1 | 396.2 | −4.8 % |
| R4 | 405.9 | 387.7 | −4.5 % |

Silindir sütunu, 3. maddedeki alt koniyi hesaba katmaz (R3 ve R4).

**Katalogdaki durum:**
- FLS riserlerinin `length` (h_tot), `end_cone_len` (h_cl) ve `end_D` (2 r_u) değerleri tablodan **yayınlanmış** olarak tutulur, ama hiçbir hesapta kullanılmaz.
- `geometry/properties.py` riserler için yalnızca kesit özelliklerini verir (`duct_section`).
- Riser katısı ve kule montajı bu belirsizlik çözülmeden FLS riserlerini kullanamaz.

**Kalsinatör makalesindeki tanım (2026-09-21'de kontrol edildi).** Aynı grubun kalsinatör makalesi (arXiv 2405.03208; ADCHEM 2024 / IFAC-PapersOnLine sürümü de aynı ifadeyi taşır), bölüm 2:

> "The calciner has a total height of htot and is a cylinder with radius rc between the heights hcl and hcu. The cone sections have the smaller radii, rl and ru for the lower and upper cone, respectively."

Bu tanıma göre h_cl ve h_cu koni boyu değil, **silindirin başladığı ve bittiği eksenel konumlardır**. Denklem (33b, 33c) ile tutarlıdır. Ama çelişkiyi çözmez:
- Tablo 8'de riserler için h_cu = 0'dır. Bu tanımla silindir 0 yüksekliğinde biter, yani anlamsızdır. Ayrıca denklem (34a) h_cu'ya böldüğü için sıfıra bölme ortaya çıkar.
- Kalsinatör satırında h_cl = 33 ve h_cu = 0'dır. Sütunlar yer değiştirmiş olsaydı (h_cl = 0, h_cu = 33) kalsinatör düz bir silindir olur ve "h_cl is zero for the risers" ifadesi de tutardı. **Bunu destekleyen hiçbir kaynak yoktur.** Yalnızca gözlemdir ve benimsenmez.
- Kalsinatör makalesi h_cl ve h_cu için sayısal değer vermez. Verdiği tek ölçü şudur: "a 33 m high calciner with an inner radius of 3.08 m and refractory and shell thicknesses of 0.21 m and 0.01 m". Bu, Tablo 8'deki r_c = 3.08, r_r = 3.29, r_w = 3.30 değerleriyle tutarlıdır.

Kontrol edilen ama bir şey vermeyen kaynaklar:
- arXiv 2504.02886'nın yalnızca v1 sürümü vardır; düzeltme yayınlanmamıştır.
- Siklon (2409.10916), fırın (2405.03200), soğutucu (2409.09076) ve PI kontrol (2605.03489) makalelerinde riser geometrisi yoktur.
- Svensen'in doktora tezi bulunamadı.
- Herkese açık bir kaynak kodu bulunamadı.

**Çözüm yolu:** Sütun anlamlarının yazarlardan (DTU Compute / FLSmidth Cement) doğrulanması. Doğrulama gelene kadar bu bölüm geçerlidir: riser şekli ve hacmi hesaplanmaz, iki okumadan hiçbiri benimsenmez.

### Kaz boynu: bulundu, hiçbir hatta atanmadı

Kaz boynunun (kalsinatör çıkışından C5'e giden kanal) boyutlarını doğrudan veren iki kaynak bulundu. İkisinin de ham sayfa metni 2026-09-21'de okundu. İkisi de **başka tesislerin genişletme sırasında eklenmiş parçalarıdır**, bu yüzden kataloğa girmez.

| Kaynak | Tesis | Yayınlanan değer | Neden atanmadı |
|---|---|---|---|
| [RSP预分解窑生产线改造设计](https://m.ccement.com/news/content/700902.html) | 1000 t/d kapasiteli RSP hattı 1500 t/d'ye büyütülürken eklenmiş ("系统产量按1500t/d设计"; fiilen ortalama 1400, en fazla 1600 t/d) | "鹅颈管的尺寸为φ3.1m×31m" | PF1500 hattının kalsinatörü CDC tipi ve Φ6.3; bu değer RSP kalsinatörlü başka bir tesisin genişletme parçası. Çapın gövde mi efektif mi olduğu yazılmıyor; 31 m'nin tüm borunun ekseni mi yoksa düz bir parça mı olduğu da belirsiz. |
| [预分解窑烧成系统的技改 (Pengfei, 2017)](http://www.pengfei.com.cn/pengfei/News/Technical_News/2017/0329/2676.html) | Tianjin enstitüsü tasarımı 5000 t/d hat (çift dizi, DD kalsinatör, Ф4.8×72 m fırın), fiilen 5900 t/d | "鹅颈管主体截面是5.4×4.4m长方形，总高度18m" | PF5000 hattından farklı bir tesis ve farklı bir kalsinatör. Kesit dikdörtgen; boyu tesisin çelik taşıyıcı kirişlerine göre belirlenmiş ("由于框架梁的限制"). Özgün tasarımda kaz boynu yok, kalsinatör C5'e yatay bir kanalla bağlanıyor ("原分解炉出风口与C5旋风筒通过平管道相联"). |

Riser (bağlantı kanalı) boyları hiçbir hat için metin olarak yayınlanmış bulunamadı. Yalnızca hacim ya da gaz kalma süresi veren kaynaklar kurallar gereği dışarıda bırakıldı: Guigang 2500 t/d'nin yalnızca hacim veren kaydı ve Pengfei'nin 1.0 s kalma süresi.

## Kararlar (kullanıcı onayladı, 2026-09-21)

1. **Kaz boynunun uzunluğu:** hiçbir kaynakta yok, bu yüzden `None`. Sayı uydurulmaz. Kule oluşturucu bu alanı zorunlu sayar ve eksik olduğunda açık bir hata verir.
2. **1500 ve 5000 hatlarının kanal çapları:** `riser_D/D_src` oranıyla, **R** olarak. Riser boyu, uç konisi ve uç çapı, kaynağı olmadığı için `None` kalır; türetilmez.
3. **Tersiyer kanal:** yok. Kalsinatörün tabanı tek bir giriş sınır yüzüdür; fırın gazı ve tersiyer hava orada birlikte girer. Doğrulanmış bir kaynak bulununca eklenir.
4. **Farin boruları kule hacmine alınmıyor.** Gerekçe Holderbank'tan (s. 65): farin klapesi, farinin kullanmadığı kesiti kapatarak gazın bu yoldan kaçmasını önler. Siklonun toz çıkışı böylece bir sınır yüzü olur.
5. **Yerleşim parametreleri ekipman ölçüsü değildir.** Siklon eksenleri arasındaki yatay ofset, kanal dirsekleri ve çift C1 için Y ayrımı katalogda yer almaz. Bunlar `LayoutParams` içinde ayrı tutulur ve hiçbir solver ya da optimizasyonla hesaplanmaz.
6. **CFD sınır parametreleri tesis geometrisi değildir.** Giriş ve çıkış uzatmaları ile vorteks bulucu duvar kalınlığı `CfdBoundaryParams` içinde tutulur. Değerleri config'te açıkça verilir; kodda varsayılan değerleri yoktur.
7. **Çift dizi (5000) ilk kule oluşturucusunda kurulmaz.** 5000 hattı katalogda durur. Kule oluşturucu yalnızca zorunlu verisi tam olan topolojileri kurar; eksik veriyi tahmin etmez, eksik alanları adlarıyla sayarak hata verir.
