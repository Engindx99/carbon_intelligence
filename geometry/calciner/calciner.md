# Calciner (kalsinatör)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, §6, Ek). Referans hat: 2500 t/d.
Tip: **ILC** (in-line calciner). İkiz yakıtın %60'ını kalsinatörde yakıyor (`fuel.kiln_fraction: 0.40`).
Kaynak: önısıtıcı ve kalsinatör HFC2500 tasarımı (2005); efektif çaplar yayınlanmış.

## Geometrik Ölçüler

| Ölçü | Değer | Kaynak / türetme |
|---|---|---|
| Efektif iç çap | 5.50 m | HFC2500 (yayınlanmış) |
| Gövde boyu (koni + silindir) | 29.46 m | FLS `calciner_H/D` = 33.00 / 6.16 (türetilmiş) |
| Alt koni duvar açısı | 65° (yatayla) | Holcim StDC 2022, siklon konisi için en az 65°; kalsinatör konisine de uygulandı |
| Alt koni yüksekliği | 3.524 m | (R − r_boğaz) · tan 65° |
| Silindir boyu | 25.936 m | 29.46 − koni |
| Boğaz çapı | 2.213 m | Literatür akışı / literatür hızı, aşağıda |
| Tersiyer hava kanalı | 1.725 m, tek, teğetsel | Literatür akışı / literatür hızı, aşağıda (6. adımda kurulur) |
| Kaz boynu çapı | 3.50 m | yayınlanmış ([gooseneck.md](../preheater/gooseneck.md)) |
| Çift kaz boynu, kol başına | 2.475 m | 3.50 × √0.5: toplam kesit korunur (kullanıcı kararı, 29 Eylül 2026) |
| Farin besleme boruları | 2 × Ø0.6 m, yatayla 60° | Fidaros ve diğ. 2007 |

**Boğaz ve tersiyer kanal türetmesi.** Bunlar için yayınlanmış bir ölçü ya da oran bulunamadı: FLS kalsinatörü düz bir silindir olarak verir (arXiv 2504.02886 Tablo 8, koni 0), bakılan CFD makaleleri de bu ölçüleri yazmaz. Bu yüzden her biri, literatürdeki bir akışın literatürdeki bir hıza bölünmesiyle bulunur. İdeal gaz ve 1 atm varsayılır. **İkizin akışları kullanılmaz**: ikiz henüz hazır değil; örneğin tersiyer havayı 575 K veriyor, tesislerde bu değer ~1100 K (kullanıcı kararı, 29 Eylül 2026).

| | Fırın gazı → boğaz | Tersiyer hava |
|---|---|---|
| Kütle akışı | 110 600 kg/h = 30.72 kg/s | 49 600 + 16 200 + 33 065 kg/h = 27.46 kg/s |
| Akış kaynağı | Mikulčić ve diğ. 2012 (aynı Ø5.5 m kalsinatör) | Mikulčić ve diğ. 2012: TA + brülör birincil + ikincil havası. ILC'de yanma havasının tamamı tersiyer kanaldan girer |
| Sıcaklık | 1050 °C | 800 °C (Kahawalage ve diğ. 2017) |
| Bileşim / M | %74.4 N₂, 7.6 O₂, 5.0 H₂O, 13.0 CO₂ → 29.90 g/mol (Kahawalage 2017) | %21 O₂ / 79 N₂ → 28.85 g/mol |
| Yoğunluk | 0.2754 kg/m³ | 0.3276 kg/m³ |
| Hacimsel akış | 111.6 m³/s | 83.8 m³/s |
| Tasarım hızı | 29 m/s (CPFD 2025, boğaz ortalaması 28–30 m/s) | 35.87 m/s (Chanamai & Rodkwan 2019) |
| **Çap** | **2.213 m** | **1.725 m** |

Fidaros ve diğ. 2007 farini **iki** Ø0.6 m borudan, yatayla 60° eğimle verir; kömürü iki Ø0.2 m borudan, 30° eğimle. Farin boruları 5. adımda kuruldu, yakıt portu 7. adımda kurulacak.

## CFD Geometry

Makro: [`geometry/macros/calciner.bas`](../macros/calciner.bas). Yapım adım adım ilerler. **Şu an kurulu olanlar**: gövde (1. adım), çift kaz boynu (2–4. adımlar) ve iki farin besleme borusu (5. adım). Henüz dışa aktarım yapılmaz.

Koordinatlar: eksen **z**, fırın gazı giriş yüzü (boğazın altı) **z = 0**.

```
boğaz      Ø2.213, z = 0 .. 2.213       (THROAT_LEN_OVER_D = 1.0, modelleme parametresi)
koni       65°, z = 2.213 .. 5.737
silindir   Ø5.50, z = 5.737 .. 31.673   (düz tavan)
kaz boynu  2 × Ø2.475, x–z düzleminde ayna simetrik:
           yükseliş x = ±1.329, z = 31.673 .. 34.767
           180° dirsek, R = 3.712, tepe z = 39.717
           iniş x = ±8.754, z = 34.767 .. 16.943 (gövdenin yarı yüksekliği) → gas_outlet_1 (+x), gas_outlet_2 (−x)
farin      2 × Ø0.6, 60°, ±x'te (y = 0 düzleminde, her inişin altında), eksen gövdeden dışarı doğru yükselir:
           eksenler duvarı z = 14.943'te keser (çıkış yüzlerinin 2.0 m altı)
           uç yüzleri (±3.250, 0, 15.809) → meal_feed_1 (+x), meal_feed_2 (−x)
```

Boğazın koni altındaki boyu bir tesis ölçüsü değildir. Giriş yüzünü koninin ağzına değil, düz bir parçanın üstüne koymak için seçilmiş bir modelleme parametresidir.

**Çift kaz boynu** (kullanıcı kararı, 29 Eylül 2026). Tavandan iki kol çıkar ve her biri dışarı doğru döner.
- **Çap.** Yayınlanmış Ø3.50'lik iki boru Ø5.50'lik tavana yan yana sığmaz (7.0 > 5.5 m). Bu yüzden her kol alanın yarısını taşır: Ø2.475. Toplam kesit ve hız korunur.
- **Boru eksenleri türetilir:** x = (R + r)/3. Bu konumda iki boru arasındaki boşluk, her boru ile gövde duvarı arasındaki boşluğa eşittir: 0.183 m. Böylece tavanda kalan en ince şerit olabileceği en kalın hâlini alır.
- **Boylar modelleme parametresidir.** Yükseliş (1.25 D) ve dirsek yarıçapı (1.5 D) C1 makrosundan alınmıştır. İnişler gövdenin yanında, **gövdenin yarı yüksekliğine** kadar sarkar: z = 2.213 + 29.46/2 = 16.943, iniş boyu 17.824 m (7.2 D) (kullanıcı kararı, 29 Eylül 2026). Böylece çıkış yüzü dirsekten uzakta, düzelmiş bir akışın üstünde durur; C1'de düz borunun ucundaki çıkış yüzünde %38 geri akış ölçülmüştü.
- **Yön ölçülür, varsayılmaz.** Bir extrude yanlış yöne giderse ya gövde sayısı ya da hacim bunu söyler; bir dirsek yanlış dönerse hacim ve kutunun tepesi söyler. Bu durumda feature silinir ve diğer yön denenir.

**Farin besleme boruları** (kullanıcı kararı, 29 Eylül 2026). Gövdenin iki yanında, kaz boynuyla aynı x–z düzleminde ±x'te, her inen borunun altında dururlar. İlk kurulumda ±y'deydiler; kullanıcının isteğiyle yanlara alındılar. Boru uçları (|x| ≤ 3.51) inen boruların iç duvarından (|x| = 7.52) uzaktadır; bunu bir ön kontrol zorlar.
- **Ölçüler ve yön.** Çap ve eğim Fidaros 2007'den alınmıştır. Her boru gövde eksenine bakar ve duvardan uzaklaştıkça yükselir, böylece farin ortaya doğru düşer.
- **Yükseklik.** Boru eksenleri duvarı, kaz boynu çıkış yüzlerinin ("saçaklar") `FEED_BELOW_GN_OUT = 2.0 m` altında keser: z = 14.943. Borunun tamamı çıkış yüzlerinin altında kalır; en üst noktası z = 15.959'dur.
- **Boy.** Boru gövde ekseninden başlar; başlangıç diski gövdenin içinde kalır ve birleşimde erir. Duvardan eksen boyunca `FEED_DEPTH = 1.0 m` dışarı çıkar (C1 oluğu gibi). Uç yüzün tamamen dışarıda kalması için bu değer r·tan 60° = 0.52 m'yi aşmalıdır.
- **Nasıl kurulur.** x = 0 düzlemindeki yarım kesit dikdörtgeni, kendi eksen kenarı etrafında tam tur döndürülür. Tam turun yanlış gidebileceği bir yönü yoktur; hangi tarafa düştüğünü ±x'te bulunan uç yüzü söyler.
- **Hacim.** Gövde dışında kalan kısım boru başına πr²L − (1/cos θ)·2∫√(r²−a²)√(R²−a²) da = **0.28506 m³**. İntegral eliptiktir; makro a = r sin φ dönüşümüyle Simpson kuralıyla hesaplar ve bağımsız bir Monte Carlo sağlaması 0.2852 verdi. Bu hacim 982 m³'lük domenin ‰1'inin (0.98 m³) altında, yani toplam hacim kontrolü boruyu göremez. Bu yüzden her boru için ayrıca şunlar kontrol edilir: eklenen hacim %1 toleransla, uç yüzü beklenen tarafta bulunmalı ve alanı 0.2827 m² olmalı.

Planlanan adımlar:
1. gövde (revolve)
2. \+ iki yükseliş borusu
3. \+ iki 180° dirsek (3a: +x, 3b: −x)
4. \+ iki iniş borusu
5. \+ iki farin besleme borusu (5a: +x, 5b: −x)
6. \+ tersiyer kanal (Ø1.725, teğetsel, dil ile)
7. \+ yakıt portu
8. sınır yüzü etiketleme ve export → `geometry/output/2500/calciner.*`

## Boundary Faces

| Sınır | Durum |
|---|---|
| `kiln_gas_inlet` | z = 0 diski, 3.847 m² (1. adımdan beri var, henüz boyanmıyor) |
| `gas_outlet_1`, `gas_outlet_2` | +x ve −x'teki inişlerin aşağı bakan diskleri, z = 16.943, her biri 4.811 m². Ayrı renkler, 8. adımda boyanır; x'in işaretiyle ayırt edilir. Her biri ikiz C5'lerden birini besler ([cyclone_C5.md](../preheater/cyclone_C5.md)); bağ bu yüzler üzerinden kurulur, C5 bu domene katılmaz |
| `meal_feed_1`, `meal_feed_2` | +x ve −x'teki boruların eğik uç yüzleri, her biri 0.2827 m². Gaz için duvar, DPM için enjeksiyon yüzeyi (C1'deki gibi) |
| `tertiary_air_inlet`, `fuel_inlet` | 6–8. adımlar |

## Derived Properties

Adım hacimleri (kapalı form, makro ‰1 ile doğrular):

```
boğaz          8.516 m³
koni          43.660 m³
silindir     616.191 m³
gövde        659.851 m³   (koni + silindir)
1  domen     668.367 m³
2  + yükseliş  698.131 m³   (iki boru, toplam 29.764)
3a + dirsek    754.234 m³   (Pappus, her biri 56.103)
3b + dirsek    810.338 m³
4  + iniş      981.821 m³   (2 · 85.742)
5a + farin +x  982.106 m³   (boru başına 0.28506; ayrıca %1 ile kontrol edilir)
5b + farin −x  982.391 m³
```

Kutu: x ±9.991, y ±2.75, z 0 … 39.717 (farin boruları kutuyu değiştirmez).

Ekipman hacmi: **659.85 m³**. Önceki 700.0 m³ değeri, Ø5.50 × 29.46 boyutlarında düz bir silindirin hacmiydi. Koni aynı toplam boyun içine alındığı için hacim %5.7 düştü (kullanıcı kararı, 29 Eylül 2026). İkizin `calciner.length` değeri bu hacimden okunmaz ve değişmez.

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
