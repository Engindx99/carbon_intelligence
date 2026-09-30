# Tesis topolojisi (şematik katı model)

Makro: [`geometry/macros/plant_topology.bas`](macros/plant_topology.bas). Referans hat: 2500 t/d.

**CFD'ye girdi değildir.** Bu model tesisin topolojisini göstermek için yazılmış şematik bir katı modeldir: hangi ekipman var, nerede duruyor ve gaz, farin ve hava hangi yoldan akıyor. `CLAUDE.md`'nin 8. kuralında istisna olarak kayıtlıdır (kullanıcı kararı, 29 Eylül 2026). Akışkan hacmi, sınır yüzü ve STL yoktur.

Tek bir SLDPRT içinde her ekipman ayrı bir gövdedir; gövdeler birleştirilmez. Her gövde, eklendiği adımda üç şeyle doğrulanır:
- gövde sayısı tam olarak bir artmalı
- toplam hacim, yeni gövdenin kapalı form hacmi kadar büyümeli (‰1)
- beklenen kutuya oturan bir gövde bulunmalı

Tam log `geometry/output/2500/plant_topology_build.log` dosyasına yazılır.

## Ölçüler

| Ekipman | Ölçü | Kaynak |
|---|---|---|
| İkiz C1 | D 4.32, gövde 6.79, koni 4.65 | catalog.md |
| C2 = C3 = C4 | D 6.30, gövde 3.46, koni 7.30 | catalog.md (C2/C3 sapması) |
| İkiz C5 | D 4.596 (katalog C5 × 1/√2) | cyclone_C5.md |
| Kalsinatör | Ø5.50, 29.46 m (koni dahil), boğaz Ø2.213, koni 65° | calciner.md |
| Kaz boynu | 2 × Ø2.475; kollar gövdenin yarı yüksekliğinde biter | calciner.md, gooseneck.md |
| Kalsinatör farin besleme boruları | 2 × Ø0.60, yatayla 60° | calciner.md (Fidaros 2007) |
| Tersiyer hava kanalı | Ø1.725 (türetilmiş: literatür akışı / literatür hızı) | calciner.md |
| Fırın | Ø4.0 × 60 m, %3 eğim | kiln.md |
| Soğutucu | ızgara alanı 65 m² | cooler.md |

Siklonlar gövde + koni + tavan + vorteks bulucu çapında bir gaz çıkış stub'ı olarak çizilir. Volüt ve vorteks bulucu daldırması yoktur.

## Şematik parametreler (kaynaksız; yalnız yerleşim için)

| Parametre | Değer | Ne belirler |
|---|---|---|
| `OUTLET_STUB_OVER_VD` | 1.0 | Siklon gaz çıkış stub'ının tavan üstündeki boyu, vorteks bulucu çapı cinsinden |
| `STAGE_GAP` | 6.5 m | Bir siklonun toz çıkışının, alttaki kademenin tepesinden yüksekliği. Önce 3.0 → 4.5 (riser'ın yatay parçası üstteki toz çıkışının altına sığsın diye), sonra 4.5 → 6.5: toz çıkışından 60° ile inen farin borusu, hemen altındaki riser başlangıç küresinin yanından geçebilsin diye. C4 bu kuralla değil, farin kuralıyla konur (aşağıda) |
| `TOWER_X` | 10.0 m | Kule sütunu (C1–C4) x = −10'da |
| `C1_TWIN_GAP` | 2.0 m | İkiz C1 gövdeleri arasındaki boşluk |
| `KILN_AXIS_Z` | 10.0 m | Fırın giriş ekseninin kotu |
| `CHAMBER_MARGIN` | 1.0 m | Fırın giriş odası: fırının çevresinde bu kadar pay bırakan bir küp |
| `COOLER_W` / `COOLER_H` | 3.0 / 4.0 m | Izgara genişliği (boy alandan çıkar: 21.67 m) ve soğutucu gövde yüksekliği |
| `COOLER_DROP` | 1.0 m | Soğutucunun tepesinin, deşarjdaki fırın kabuğunun altında kaldığı mesafe |
| `R1_CLEAR` | 0.5 m | R1 riser'ının ikiz C1 gövdelerine x'teki boşluğu |
| `EXHAUST_L` | 10.0 m | C1 egzoz kanallarının fana doğru çizilen boyu |
| `MEAL_CLEAR` | 0.5 m | Kule farin borusunun, alttaki siklon gövdesinin yanından x'te geçtiği pay |
| `C4_SPLIT_X` | −5.0 m | C4 farininin kalsinatörün iki beslemesine ayrıldığı x |
| `C5_MEAL_X` | −2.0 m | C5 farin borularının giriş odasına döndüğü x |
| `MEAL_INTO_CHAMBER` | 1.0 m | C5 farin borularının giriş odasının içinde bittiği derinlik |
| `RAW_MEAL_L` | 5.0 m | Ham farin borusunun R1'e doğru çizilen boyu |

## Yerleşim

Eksenler: z yukarı; kalsinatör ekseni x = 0, y = 0. Fırın +x yönünde uzanır ve soğutucuya doğru iner; kule x = −10'da durur.

Kalsinatör, CFD makrosundakinden 90° döndürülmüştür: çift kaz boynu y–z düzlemindedir. Böylece ikiz C5'ler kalsinatörün iki yanına düşer, fırının üstüne değil.

```
fırın giriş odası  |x|, |y| ≤ 3.0, z 7.0 .. 13.0
kalsinatör          z 13.0 .. 44.673; kaz boynu kolları (0, ±8.754, 29.943)'te biter
ikiz C5             (−3.536, ±8.754); tavan = kol ucu z 29.943, toz çıkışı z 22.193
C4 / C3 / C2        x = −10, toz çıkışları z 51.759 / 73.649 / 95.539
ikiz C1             (−10, ±3.16), toz çıkışı z 117.429, tepe z 131.269
fırın               (3.0, 0, 10.0) → (62.973, 0, 8.201)
soğutucu            x 62.973 .. 84.640, |y| ≤ 1.5, z 1.201 .. 5.201
fırın başlığı       x 62.973 .. 68.973, |y| ≤ 3.0, z 5.201 .. 11.201
```

Her C5'in gövdesi, kaz boynu koluna kule tarafında teğettir.

**C4'ün kotu türetilir.** C4'ün farini kalsinatörün iki besleme borusuna 60° ile iner: önce TOWER_X boyunca x'te, sonra besleme ucunun y'si (3.25) boyunca. Bu yüzden C4'ün toz çıkışı z = 28.809 + (10 + 3.25) · tan 60° = 51.759'dadır. Bu, STAGE_GAP'in vereceği 39.795'ten 14 m yukarıdadır; ön kontrol, bu kotun C5 stub'larının en az STAGE_GAP üstünde kalmasını zorlar. R4 riser'ı bu yüzden 28 m boyundadır.

## Gaz yolu (2. adım)

fırın → giriş odası → kalsinatör → çift kaz boynu → ikiz C5 → R4 → C4 → R3 → C3 → R2 → C2 → R1 → ikiz C1 → egzoz

**Kurallar:**
- Borular eksene paralel düz parçalardır. Köşelerde borunun çapında bir küre eklem vardır; boru uçları küre merkezinde biter.
- Kaz boynu, CFD'deki gibi 180°'lik torus dirsekle döner.
- **Siklona giriş şematiktir:** besleyen dikey boru gövdeye teğet durur ve tavan kotunda biter. Bu, teğetsel girişin şematik karşılığıdır.
- Fırın ile giriş odası ve oda ile boğaz arasında temas vardır; ayrı gövde gerekmez.

**Çaplar:**
- R1–R4 HFC2500'den, yayınlanmış: 3.07 / 3.35 / 3.45 / 3.60.
- Bölünen akışlar alan bölümüyle: R4'ün C5 kolları Ø2.546, R1'in C1 kolları Ø2.171 (riser_R1.md ile aynı).
- C1 egzozu vorteks bulucu çapında: Ø2.40.

| Bağlantı | Güzergâh |
|---|---|
| kalsinatör → C5 ±y | yükseliş (0, ±1.329), z 44.673 → 47.767; dirsek R 3.712, tepe 52.717; iniş (0, ±8.754) → z 27.447 (C5 gövdesinin altı) |
| C5 ±y → R4 ayağı | Ø2.546, z 34.568: stub üstünden x boyunca −3.536 → −10, sonra y boyunca → 4.950. −y kolu C4'ün altından geçer (15.9 m boşluk) |
| R4 → C4 | (−10, 4.950)'de Ø3.60 ayak küresi; riser z 34.568 → 62.519, C4'e teğet |
| C4 → R3 → C3 | stub üstünde, y 0 → 4.875, z 68.874; riser → 84.409 |
| C3 → R2 → C2 | stub üstünde, y 0 → 4.825, z 90.714; riser → 106.299 |
| C2 → R1 → ikiz C1 | x −10 → −5.805, z 112.464; riser → 127.784; dağıtıcı Ø2.171, y ±6.405; kollar x boyunca → −10, C1'lere yandan teğet |
| C1 ±y → egzoz | Ø2.40, z 132.469, x −10 → −20 |

Ön kontroller şu dar noktaları zorlar:
- her yatay riser parçası, beslediği kademenin toz çıkışının altından geçmeli
- R4 kolları kaz boynu inişlerinden uzak olmalı
- R1 riser'ı ve dağıtıcısı ikiz C1'den uzak olmalı

## Farin yolu (3. adım)

ham farin → R1 · C1 → R2 · C2 → R3 · C3 → R4 · C4 → kalsinatörün iki besleme borusu · ikiz C5 → fırın giriş odası

Her siklonun farini, bir alttaki kademeye giden gazın riser'ına düşer; gaz onu bir üstteki siklona taşır (ters akım). C4'ün farini kalsinatöre, C5'inki fırına gider.

**Kurallar:**
- Farin boruları düz parçalardır, her biri x–z ya da y–z düzleminde **60°** eğimle iner. Bu, kalsinatör besleme borularının eğimidir (Fidaros 2007). Köşelerde boru çapında küre vardır. Yatay farin borusu yoktur.
- Çaplar:
  - Her siklonun borusu kendi toz çıkışı çapındadır: C1 Ø0.40, C2–C4 Ø0.81, C5 Ø0.587.
  - C4'ün iki kolu ve kalsinatör besleme boruları Ø0.60'tır.
  - Ham farin borusu Ø0.566'dır, yani iki C1 çıkışının toplam alanı.
- Borular hedefin içinde biter: riser'a girenler riser ekseninde, C5 boruları giriş odasının 1 m içinde.
- **Kalsinatör besleme boruları** `calciner.bas`'taki gibidir, yalnız ±y'ye döndürülmüştür. Gövde ekseninde z 23.180'den başlar, duvarı z 27.943'te keser, ucu (0, ±3.25, 28.809)'dadır. C4 kolları bu uçtaki küreye bağlanır.

| Bağlantı | Güzergâh |
|---|---|
| ham farin → R1 | +x tarafından 5 m, 60°; R1 riser'ının ortasında (z 120.124) eksende biter |
| C1 ±y → R2 | toz çıkışından −x'e x = −13.85'e; y boyunca 4.825'e; +x ile R2 eksenine. +y z 101.208'de girer; −y z 90.262'de, R2'nin dirsek küresine |
| C2 → R3 | −x'e x = −14.055'e; y boyunca 4.875'e; +x ile R3 eksenine, z 73.048 |
| C3 → R4 | aynı desen, y 4.950; R4 eksenine z 51.028'de |
| C4 → kalsinatör | y = 0'da +x yönünde x = −5'e, z 43.099 (ayırıcı küre); x = −5'te ±y'ye 3.25'e, z 37.470; +x ile besleme ucuna, z 28.809 |
| C5 ±y → giriş odası | x boyunca −3.536 → −2, z 19.534; x = −2'de y ±8.754 → ±2. Odanın yan yüzüne z 9.568'de girer, z 7.836'da biter |

Kule farin boruları −x tarafında, alttaki siklonun gövdesinin dışından (R 3.15 + r + 0.5) iner. Böylece gaz yolunun +y tarafındaki riser'larından uzak kalırlar.

**Ön kontroller:**
- her kule borusu, kendi kademesini besleyen riser'ın başlangıç küresinden en az 0.1 m uzakta
- her kule borusu hedef riser'ın kot aralığına giriyor (dirsek küresi dahil)
- C4, C5 stub'larının en az STAGE_GAP üstünde
- C5 boruları odanın yan duvarına z 7..13 aralığında giriyor ve kalsinatörden uzak
- ham farin borusu R1 dağıtıcısının altında

Python ile yapılan çakışma taramasında, 0.15 m'den yakın hiçbir ilgisiz gövde çifti çıkmadı.

## Hava yolu (4. adım)

- soğutucu → fırın başlığı → fırın (ikincil hava). Gövdeler birbirine değdiği için ayrı kanal gerekmez.
- soğutucu → fırın başlığı → tersiyer kanal → kalsinatör (tersiyer hava)

**Fırın başlığı** giriş odasının aynasıdır: fırının deşarj ucunun çevresinde `CHAMBER_MARGIN` payı bırakan 6 m'lik bir küp.
- Soğutucunun sıcak ucuna oturur; tabanı soğutucunun tavanındadır (z 5.201), çünkü `COOLER_DROP` = `CHAMBER_MARGIN`. Bunu bir ön kontrol zorlar.
- y'de soğutucudan taşar (±3.0'a karşı ±1.5); şematik olduğu için kabul.

**Tersiyer hava kanalı**, Ø1.725 (calciner.md'de türetilmiş):

| Parça | Güzergâh |
|---|---|
| kalkış | başlığın tavanının ortasından, (65.973, 1.8875), düşey z 11.201 → 19.600 |
| köşe | küre |
| kanal | fırının üstünden −x yönünde, x 65.973 → 0, y 1.8875, z 19.600 |

- **Teğetsel giriş.** Kanal ekseni kalsinatör ekseninden R − r = 1.8875 uzaktadır, dış kenarı duvarla aynı hizadadır. Kanal kalsinatörün eksen düzleminde biter; duvarın içinde kalan kısmı (x < 2.0) gövdede gizlenir. +y tarafı seçildi, dönüş yönünü bu belirler.
- **Giriş kotu şematiktir.** Kanalın alt kenarı koninin tepesindedir (z 18.737). Kalsinatör CFD makrosunun 6. adımı (TA kanalı) kendi yerini belirleyecek; farklı çıkarsa topoloji ona uyar.

**Ön kontroller:**
- başlık soğutucunun tavanında ve fırın ucunu sarıyor
- TA koni tepesinin altına inmiyor
- TA fırının ve giriş odasının üstünden geçiyor (≥ 5.7 m)
- TA, +y besleme borusunun altında kalıyor (6 m)
- TA başlığın tavanından kalkıyor

## Gövde hacimleri (kapalı form)

Tam log `geometry/output/2500/plant_topology_build.log` dosyasındadır; her bağlantı `--` ile başlayan bir satırla listelenir.

```
kalsinatör           668.367 m³
C5 (her biri)        104.226 m³
C4 = C3 = C2         272.669 m³
C1 (her biri)        135.399 m³
fırın giriş odası    216.000 m³
fırın                753.982 m³
soğutucu             260.000 m³
                     11 gövde
```

2. adım: gaz yolu **38 gövde** ekler (silindirler, küreler, 2 torus), toplam **49 gövde**; gaz yolunun hacmi 1672.960 m³. Örnekler: kaz boynu yükselişi 14.882, dirseği 56.104, inişi 97.749; riser'lar R4 284.509, R3 145.224, R2 137.368, R1 113.400 m³.

3. adım: farin yolu **39 gövde** ekler (22 boru, 15 küre, 2 kalsinatör besleme borusu), toplam **88 gövde**; farin yolunun hacmi 63.713 m³. Örnekler: kalsinatör besleme borusu 1.838, ham farin borusu 1.257 m³.

4. adım: hava yolu **4 gövde** ekler (başlık 216.000, TA yükselişi 19.629, köşe 2.688, kanal 154.182), toplam **92 gövde**; 392.499 m³.

Eğik gövdelerin kutusu `GetBodyBox` ile değil, `GetExtremePoint` ile ölçülen sıkı kutuyla kontrol edilir. `GetBodyBox` eğik gövdelerde gevşek kutu verebilir.

## Adımlar

1. **Ekipman gövdeleri yerlerinde (tamam).**
2. **Gaz yolu (tamam).**
3. **Farin yolu (tamam).**
4. **Hava yolu: fırın başlığı ve tersiyer hava kanalı (tamam).**
5. Renkler (gaz turuncu, farin sarı, hava mavi, fırın gri), gövde adları, bağlantı raporu ve STEP export.
