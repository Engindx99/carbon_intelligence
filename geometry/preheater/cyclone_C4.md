# Cyclone C4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d. Tekli siklon.
Farin borusu: [meal_pipe_C4.md](meal_pipe_C4.md)
Tesiste iki özdeş 2500 t/d hattı var; her hatta bu siklondan bir tane, CFD ölçüsünde (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)).

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2 ve C3 bu siklonla özdeş; ölçüler aşağıdaki C4 değerleri.

Yayınlanmış olan yalnız çap D'dir (HFC2500); koni, vorteks bulucu ve toz çıkışı D'den FLS oranlarıyla türetilir. CFD'de katalogdan üç sapma var, hepsi kullanıcı kararı ve aşağıda gerekçeli: gövde h = D (katalog 3.46 m), daldırma 3.90 m (katalog 3.17 m) ve volütlü giriş (katalog 1.27 × 9.44 m). Katalog değerleri [catalog.md](../catalog.md)'de.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Hat başına adet | 1 | yayınlanmış |
| Efektif iç çap D | 6.3 m | yayınlanmış |
| Silindirik gövde yüksekliği | 6.3 m | CFD kararı |
| Koni yüksekliği | 7.3 m | FLS oranıyla türetilmiş |
| Vorteks bulucu daldırması S | 3.9 m | CFD kararı |
| D_x / D (= riser çapı / D) | 0.5 | CFD kararı |
| Vorteks bulucu çapı D_x (= riser çapı) | 3.1500 m | 0.5 D |
| Toz çıkışı çapı | 0.81 m | FLS oranıyla türetilmiş |
| Giriş genişliği | 2.912 m | CFD kararı |
| Giriş yüksekliği | 3.4 m | CFD kararı |
| Giriş eğimi | 0 ° | CFD kararı |
| Volüt | var | CFD kararı |
| Çıkış dönüşü | 0 ° | CFD kararı |
| Çıkış borusu yükselişi (çatının üstünde) | 5.355 m | 1.7 D_x |
| Yatay giriş kanalı (teğet düzleminden) | 2.000 m | türetilmiş |
| Riser duvarlarının kanala eğimi | 45 ° | şematik |
| Riser ekseni, gövde ekseninden (kolon aralığı) | 6.090 m | türetilmiş |
| Eğik geçiş, yatay boyu (riser ekseninden kanal ağzına) | 1.925 m | türetilmiş |
| CFD domenindeki dik riser (dönüşün altında) | 3.150 m | türetilmiş |
| Toplam yükseklik (gövde + koni) | 13.600 m | türetilmiş |
| **Ekipman hacmi (gövde + koni)** | 283.25 m³ | türetilmiş |
| **Islak alan (gövde + çatı halkası + koni)** | 235.17 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Katı `geometry/macros/cyclone.bas` ile `CYCLONE_NAME = "C4"` seçilerek üretilir: `geometry/output/2500/C4.{SLDPRT,step,stl}` ve mesh ölçü silindiri `C4_boi.step`.

**Giriş ve volüt (kullanıcı kararı, 4 Ekim 2026; katalogdan sapma):**
- Katalog girişi 1.27 × 9.44 m CFD'de olduğu gibi kurulamıyor:
  - 1.27 m genişlik, gövde ile vorteks bulucu arasındaki 0.84 m'lik halkaya sığmıyor;
  - 9.44 m yükseklik 3.46 m'lik gövdeden uzun, koninin dibine (r ≈ 0.9 m) kadar iniyor;
  - açıklığın %66'sı vorteks bulucu ağzının altında kalıyor (C1'de reddedilen kısa devre).
- Tesis böyle bir girişi volütle besler. Model de basit bir volüt kurar:
  - çatıdan aşağı ekstrüde edilen düz bir kanal (3.0 m; 17 Kasım 2026'dan beri 1.0 m, aşağıda) ve 180°'de gövdeye inen bir Arşimet sarmalı;
  - iki uçta 5 cm'lik dil (C1'deki `INLET_TONGUE` ile aynı gerekçe).
- **Giriş 3.40 × 2.912 m = 9.90 m².** Katalog girişinin tesis debisindeki alanı: 56 kg/s ve 1033 K'de 16.0 m/s. Yükseklik, gövde henüz 3.46 m iken volüt tabanı gövde/koni kenarına denk gelmesin diye seçildi; genişlik alanı koruyor. Gövde uzadıktan sonra da korundu; daldırma bu yüksekliğe göre seçildi (aşağıda).

**Gövde h = D = 6.30 m (kullanıcı kararı, 4 Ekim 2026; katalogdan sapma).**
- FLS oranının 3.46 m'si (h/D 0.55) 3.17 m'lik daldırmayla vorteks bulucu ağzını koninin yalnız 0.29 m üstüne koyuyordu.
- h/D 1.0 ile ağız koninin 3.13 m üstüne çıkıyordu; daldırma 3.90 m'ye inince 2.40 m üstünde (aşağıda).
- Koni, vorteks bulucu çapı ve toz çıkışı katalogdaki gibi.
- CFD gövdesinin hacmi yukarıdaki tabloda; katalog ölçüleriyle 194.5 m³'tü. 13 Ekim 2026'dan beri twin'in ön ısıtıcısı CFD gövdesinin hacmini ve ıslak alanını kullanır (aşağıda, Derived Properties).

**Riser girişi ve düz çıkış (kullanıcı kararı, 17 Kasım 2026).** R2–R4 artık alttaki siklonun çıkış borusunun dik devamıdır: alttaki siklonun ekseninden kolon aralığı kadar (5.838 m) uzakta dik yükselir, üstü düzdür, oradan düz yüzeyli (ruled) bir geçişle üst siklonun kanalına girer. Geçişin dış duvarı 45° ile kanalın üst kenarına, iç duvarı daha dik (81.8°) kanal tabanına gider; kanal volütün 1.0 m önünde yataydır (siklona ulaşınca kısa bir mesafe eğim sıfır). C4'ün CFD domeni bunu taşır:
- **Giriş:** R4'ün dik riser'ının 1.0·D (4.63 m) boyu, geçiş ve 1.0 m'lik yatay kanal. Gaz giriş yüzü riser'ın tabanında, Ø4.63, z 4.13 m; riser ekseni (x −3.523, y 4.656), kanalın ortasının altında.
- **Çıkış:** vorteks bulucu çatının 1.70·D_x (7.871 m) üstüne düz uzanır ve orada biter (z 21.47 m). Dirsek yok: tesiste C3–C5'in çıkış borusu bir üstteki riser'dır ve dik yükselir; C2'ninki R1'dir, o da dik (17 Kasım 2026).
- Riser'ın çapı burada C4'ün D_x'i (4.63 m). Tesiste R4, C5'in D_x'i (4.777 m) ile biraz geniştir; kolon aralığı en geniş riser'a (R4) göre seçildiği için R2 / R3 domenle birebir, R4 ise %3 geniş.
- Riser'ın dik kısmı tesiste 9.26 m (R4 9.19 m); domen yalnız 1.0·D'sini taşır. Giriş profili (düzgün, dönmesiz) bu uzunlukta gelişmiş bir boru profili değildir; geçişin ayrılma bölgesini sürecek olan geçişin kendisidir, onun için 1.0·D yeterli sayıldı (ölçülmedi).
- Katı `geometry/output/2500/C4.{SLDPRT,step,stl}`: **603.50 m³** (geçiş, ölçülen: 37.94 m³; `plant_geometry._ruled_loft` 38.24 m³ verir).
- Bu domen henüz çözülmedi: aşağıdaki Eu 11.54, η 0.96 eski domenin (yatay 3.0 m kanal, 90° dirsek) sonuçlarıdır ve yeni çözüme kadar taşınır.

Önce (4 Ekim – 17 Kasım 2026) giriş 3.0 m'lik yatay bir kanaldı (riser domende yoktu, gaz kanalda düzgün profille giriyordu). Çıkışta 90° dirsek (merkez çizgisi yarıçapı 1.0·D_x) gazı +x yönünde 4.63 m'lik yatay bir bacağa çeviriyordu, gaz çıkış yüzü x = 9.26 m'deydi.

**Daldırma S = 3.90 m (kullanıcı kararı, 5 Ekim 2026; katalogdan sapma).**
- Katalogdaki 3.17 m, 3.40 m'lik girişe karşı S/a 0.93 veriyordu: vorteks bulucu ağzı giriş tabanının 0.23 m üstündeydi.
- S 3.17 geometrisinin CFD'si (aşağıda) giriş jetinin ağza döndüğünü gösterdi: gazın %72'si ağzın altına iniyor ama 1–2 m içinde geri dönüyor; koniye ~%10'u ulaşıyor. Temiz gaz DPM'inde 40–70 µm'lik tanelerin %80–90'ı kaçtı.
- Literatür S/a ≥ 1.1–1.2 ister (Hoffmann & Stein; US3207494). 3.90 m ile S/a 1.15: ağız giriş tabanının 0.5 m altında, koninin 2.4 m üstünde (z 9.70).
- D_x/D 0.735 büyük ama katalog değeri; alt kademe siklonlarında verim yerine düşük ΔP için seçilir, değişmedi.

CFD domeni (S 3.90) ≈ 672.7 m³: S 3.17'deki 673.6 m³ eksi uzayan vorteks bulucu duvarı 0.86 m³ (makro log'u kesin değeri verir).

**Çıkış borusu 1.70·D_x (14 Ekim 2026):** çatının üstündeki düz boru 1.25·D_x'ten (5.79 m) 1.70·D_x'e (7.87 m) uzadı. İki hatlı tesis çiziminde C2 / C3 altlarındaki CFD dirseğinin yalnız 0.9 m üstündeydi; farin boruları sığmıyordu (kullanıcı kararı, [plant_topology.md](../plant_topology.md)). Domen 707.81 m³ (+35.08 m³, yalnız borunun uzaması). Çözümü aşağıda, "Gaz-yalnız CFD, çıkış borusu 1.70·D_x".

## Gaz-yalnız CFD (4–5 Ekim 2026, S 3.17 geometrisi)

**Mesh:**
- Ansys Meshing tet; Fluent'te poly'ye çevrildi ve `improve-quality` uygulandı.
- 906 bin tet → **320 692 poly hücre**, min orthogonal quality 0.20 (volüt dili).
- 1 025 202 düğüm: Student lisansının ~1.05M sınırının hemen altında, daha fazla inceltilemez.
- Fluent'te ölçülen hacim 673.0 m³.

**Kurulum:**
- Gaz: 56 kg/s, 1033 K (literatür). ρ 0.353 kg/m³ ve μ 4.2·10⁻⁵ Pa·s sabit.
- Model: SST + eğrilik düzeltmesi.
- Giriş: kütle debisi, yüze dik, %5 türbülans, D_h 3.14 m (4A/P).
- Çıkış: 0 Pa, geri akış yönü "From Neighboring Cell". Toz çıkışı duvar.
- Çözüm C1'deki gibi: PRESTO!, ikinci derece. Steady (Coupled, 350 iterasyon) başlangıç, ardından URANS (SIMPLE, BSOI, Δt 0.03 s, adım başına 20 iterasyon).
- Girdap ~7 s akış süresinde oturdu. Ortalama 7.0–21.2 s penceresinden, 34 periyot.

| Büyüklük | Değer |
|---|---|
| Statik ΔP (giriş − çıkış) | **477.1 Pa** (SE 0.3; yarılar 476.3 / 477.9) |
| Toplam basınç düşümü | 475.9 Pa |
| Euler sayısı ΔP / (½ρv_in²) | **10.53** (v_in 16.02 m/s, ½ρv_in² 45.3 Pa) |
| Steady çözüm | 435.2 Pa (URANS'ın %9.6 altında; C1'de fark %2.8) |
| Girdap salınımı | 2.39 Hz (0.42 s) |
| v_θ: duvar / CS / tepe | 24–25 / **31.7** / 38–41 m/s (tepe r ≈ 1.5 m'de) |
| Çıkışta geri akış | alanın ~%25'i |

- v_θ değerleri 7–21 s'deki 9 kaydın ortalaması.
- CS değeri vorteks bulucu yarıçapında, ağız ile koninin R_x'e indiği yer (z 5.1–10.2 m) arasında. z'ye neredeyse bağlı değil: 30.3–32.8 m/s.
- Gövde duvarının hemen yanında +5–6 m/s'lik yukarı akış var (z = 9 m). C1'deki çatı halkasını oluşturan katmanın benzeri.

**Muschelknautz ile karşılaştırma** (C1 dokümanındaki E adımının betiği; C1 sayılarını birebir veriyor):
- Volütte gaz gövdeye girmeden döner. Bu yüzden R_in, giriş kanalının merkez çizgisi yarıçapı alındı (R + dil + b/2 = 4.656 m) ve daralma α = 1.
  - Yarık bağıntısının α'sı (0.775) bu R_in ile girdabı abartıyor: 36 m/s, 604 Pa.
- Sürtünme alanı 272.6 m², f 0.005. Volüt duvarları dahil değil.

| | MM | CFD |
|---|---|---|
| v_θ duvar | 23.7 m/s | 24–25 m/s |
| v_θCS | 28.8 m/s | 31.7 m/s |
| ΔP | 416 Pa (gövde 30 + vorteks bulucu 386) | 477 Pa |
| Euler | 9.19 | 10.53 |

- **CFD/MM = 1.146.** C1'in 0.785'i taşınmıyor; C1 dokümanında öngörüldüğü gibi C2, C3 ve C5 bu CFD'nin Euler sayısıyla ölçeklenir.
- **Sapma girdap tahmininde.** CFD'nin v_θCS değeriyle MM'nin vorteks bulucu terimi 446 Pa; gövdeyle toplam 476 Pa, CFD ile aynı. C1'de aynı kontrol %20 fazla vermişti. Sapma, volüt için bilinmeyen α'dan geliyor; CFD'nin girdabına karşılık gelen α ≈ 0.92.

**Twin'e giden değer (gaz-yalnız):** Eu 10.5, 56 kg/s ve 1033 K'de 477 Pa. Farklı debi ve yoğunlukta ΔP = Eu·½ρv_in². Yüklü durum aşağıda.

Dosyalar (repo dışında, `C:\Users\engin\c4`):
- `c4_urans.cas.h5` / `.dat.h5`
- `c4_steady.*`
- `c4u-2-00350…00700.dat.h5` (ortalama kayıtları; `c4u-2.cas.h5` ile ve her biri için case yeniden okunarak açılmalı)
- `c4_urans_1_1.out` (adım bazında rapor)

## Yüklü Durum (5 Ekim 2026, S 3.17 geometrisi)

**Yöntem:** C1'deki gibi analitik (bkz. [cyclone_C1.md](cyclone_C1.md), "Yüklü Durum"). Yüklü Muschelknautz, Hoffmann & Stein Böl. 6 ve Svensen ve diğ. 2025 denk. 77–82:
- α(c₀);
- f = 0.005·(1 + 3√c₀);
- c₀L = 0.025·(x₅₀/x_med)·(10c₀)^0.15;
- x₅₀;
- iç girdap için β = 5.

Betik C1'in yüklü sonuçlarını birebir veriyor: α 0.795, v_θCS 14.7 m/s, 249 Pa, c₀L 0.030, η %96.1.
- **ΔP kalibrasyonu:** CFD'ye kalibre edilir, ΔP = 477 Pa × MM_yüklü / MM_temiz.
- **Volüt için α:** bağıntısı yok; temiz gaz α'sı CFD'nin v_θCS'sine (31.7 m/s) kalibre edildi, **α = 0.898**. Yüklemenin α'yı nasıl değiştirdiği de bilinmiyor. İki uç hesaplandı:
  - α sabit: yükleme yalnız sürtünmeyle etki eder;
  - α yarık bağıntısının oranıyla ölçeklenir: 0.99'a çıkar.
- H_CS 5.35 m: vorteks bulucu ağzından koni yarıçapının R_x'e indiği yere (z 5.08 m) kadar. Sürtünme alanı 272.6 m².

**Girdiler (literatür tabanı, iki hattın toplamı):**
- Gaz 56 kg/s, 1033 K (twin'in C4 bandı 1023–1043 K'nin ortası). ρ 0.353 kg/m³, μ 4.2·10⁻⁵ Pa·s.
- Farin beslemesi 1.55 kg/kg klinker × 28.94 kg/s = 44.9 kg/s. RR d̄ 40.9 µm, n 0.904, ρ_p 2700 kg/m³ (C1 ile aynı).
- **C4'e giren katı, kütle dengesiyle:** C3'ün alt akışı artı C5'ten gazla kaçan toz.
  - C1'den kaçan toz beslemeye döner (twin kararı).
  - C2–C4 aynı η'yi taşır.
  - C5'e kalsinatörün ürünü gelir. Kütle oranı 1 − 0.35·0.90 = 0.685 (LOI %35, kalsinasyon %90).
  - C5'in η'si yayınlanmamış: %80–90 tarandı.
- Sonuç: **C4'e ~53 kg/s katı** (C3'ten 48, C5 tozu 3–7), **c₀ ≈ 0.95**.
- İki hatlı tesiste her hat gazın da farinin de yarısını taşır; c₀ ve aşağıdaki sonuçlar siklon başına aynıdır.

| Büyüklük | Gaz-yalnız | Yüklü (η_C5 %85) |
|---|---|---|
| α | 0.898 | 0.898 / 0.993 |
| f | 0.005 | 0.020 |
| v_θ duvar / CS | 26.4 / 31.7 m/s | 26.4–23.9 / 23.6–22.1 m/s |
| Siklon ΔP | 477 Pa | **337–385 Pa** |
| x₅₀ | 34 µm | 46–49 µm |
| c₀L | – | 0.059–0.064 kg/kg |
| η | – | **%93.4–95.8** (alt: yalnız sınır yükleme; üst: + iç girdap) |

- **C5 η'sine duyarlılık küçük:** %80 → %90 arasında c₀ 0.99 → 0.92, η ±0.2 puan, ΔP ±2 Pa.
- **x₅₀ C1'den büyük** (C1 yüklü: 24 µm). Sıcak gazın viskozitesi daha yüksek, kontrol yüzeyi kısa.
- **Literatür uyumu:** η alt kademe siklonlarının literatür aralığında. Yüklemeyle ΔP'nin düşmesi C1'deki gibi.

**Riser R4'te farinin ek basınç kaybı** (hat başına; gaz 28 kg/s, farin 26.7 kg/s, Ø2.546 m, v 15.6 m/s):
- farini riser hızına çıkarma 81 Pa;
- askıdaki farinin ağırlığı 40 Pa (0.34 kg/m³; [plant_topology.md](../plant_topology.md)'deki şematik ~12 m'lik yükseliş);
- kanal hızına çıkarma 3 Pa;
- **toplam ≈ 124 Pa**.

Gazın riser'daki kendi kaybı (dirsekler, sürtünme) CFD domeninde yok ve hesaplanmadı.

**Twin'e giden değerler** (C1'deki gibi η'nin alt ucu):
- η **%93.5** (14 Ekim 2026'da 0.96'ya çıktı: sınır yükleme + DPM iç girdabı, aşağıda);
- siklon ΔP **~360 Pa** (337–385);
- R4'te farin kaynaklı ek kayıp ~124 Pa.

Farklı debilerde ΔP ∝ ṁ_g² ölçeklenir. Varsayımlar: sıcaklık literatürden sabit, adyabatik duvar, C4'te reaksiyon yok.

Betikler repo dışında: `C:\Users\engin\c4\mm\` (`mm_loaded.py`, `c4_loaded.py`).

## Gaz-yalnız CFD, S 3.90 geometrisi (12 Ekim 2026)

**Mesh:** S 3.17 ile aynı tarif (Ansys Meshing tet, global 150 mm, başka ayar yok).
- 925 bin tet → **328 119 poly hücre**.
- Min orthogonal quality **0.29**.
- 1 046 200 düğüm: Student sınırının hemen altında.
- Fluent'te ölçülen hacim 672.16 m³ (S 3.17'den 0.86 m³ az; beklenen).

**Kurulum:** S 3.17 case'inin ayarları (`/file/write-settings` → `/file/read-settings`); yüz alanları aynı (9.90 / 16.82 / 0.507 m²).
- Steady Coupled 350 iterasyon: **484.1 Pa** (S 3.17: 435.2).
- URANS: 20 adım Δt 0.01 s, ardından 0.03 s.
- Girdap ~5 s'de oturdu. Ortalama 5.0–19.7 s penceresinden, 491 adım, 36 periyot.

| Büyüklük | S 3.17 | **S 3.90** |
|---|---|---|
| Statik ΔP (giriş − çıkış) | 477.1 Pa | **515.5 Pa** (SE 0.5; yarılar 514.1 / 516.8) |
| Toplam basınç düşümü | 475.9 Pa | 506.4 Pa |
| Euler sayısı | 10.53 | **11.38** |
| Girdap salınımı | 2.39 Hz | 2.44 Hz |
| v_max | 60.8 m/s | 58.7 m/s |

- ΔP %8 arttı. Uzayan vorteks bulucu girdabı ağzın altına indiriyor; vorteks bulucu kaybı büyüyor.

**Ortalama alan** (9 otomatik kayıt, t 7.1–19.1 s; her kayıttan önce case yeniden okundu):

| | S 3.17 | S 3.90 |
|---|---|---|
| Koniye inen gaz (z 6.5) | %9.9 | %12.1 |
| Duvar yanı w, ağzın ~1 m altı | +6.0 m/s (en çok +10) | +7.0 m/s (en çok +16.7) |
| v_θCS / duvar v_θ | 31.7 / 25.4 m/s | 31.1 / 26.6 m/s |

- Gaz yapısı daldırmayla değişmedi, yalnız ağızla birlikte aşağı kaydı.
- Ana aşağı akış barel duvarında değil, vorteks bulucu hizasında (r 2.2–2.6 m) halka jeti olarak iniyor. Jetle duvar arasında, duvar boyunca yukarı dönen bir girdap var.
- Olası neden geniş vorteks bulucu. Gövde ile vorteks bulucu dış duvarı arasındaki halka yalnız 0.75 m, volüt akımı 2.9 m genişliğinde; akım vorteks bulucu duvarına yapışıyor.
- **Vorteks bulucu katalogdaki gibi kalır** (kullanıcı kararı, 12 Ekim 2026). MM'ye göre D_x/D'yi 0.60'a indirmek yüklü ΔP'yi %60 artırır, yüklü η'yı ~2 puan iyileştirir. Alt ve ara kademelerde geniş vorteks bulucu düşük ΔP için bilerek seçilir.
- SST-CC'nin eksenel alan zayıflığı ayrıca payı olabilir; RSM kontrolü yapılmadı.

**Temiz gaz DPM, zamana bağlı** (URANS ile eşzamanlı, 19.7–28.7 s, DRW kapalı; S 3.17 ile aynı kurulum):
- İlk 1.26 s'de her adımda 288 parsel (12 çap × 24 nokta), her çaptan 1032 parsel.
- Toz çıkışı "trap", duvar sekmesi 0.8.

| d (µm) | S 3.17: kaçan / toz / domende | **S 3.90: kaçan / toz / domende** |
|---|---|---|
| 2–10 | %84–87 / 0 / %13–16 | %76–84 / 0 / %16–24 |
| 15 | %80 / %3 / %17 | %73 / %12 / %16 |
| 20–25 | %81–83 / %5–9 / %8–14 | %66–72 / %18–20 / %10–14 |
| 30 | %86 / %7 / %7 | %54 / %36 / %10 |
| 40 | %69 / 0 / %31 | %20 / **%76** / %4 |
| 50–70 | %9–65 / 0 / %35–91 (çatı halkası) | %6 / **%94** / ~%1 |
| 100 | 0 / 0 / %100 (halka) | %2 / %91 / %8 |
| 170 | 0 / 0 / %100 (halka) | 0 / %65 / %35 |

| Beslemeyle ağırlıklı | S 3.17 | **S 3.90** |
|---|---|---|
| Kaçan | %60.8 | **%44.5** |
| 9 s'de toz çıkışına inen | %1.7 | **%41.3** |
| Temiz gaz η (domende kalan tutulmuş sayılırsa) | %39 | **%56** |

- **Daldırma kısa devreyi çözdü.** Gaz yapısı az değişse de giriş akımı artık doğrudan vorteks bulucuya girmiyor.
- 40–100 µm'lik tanelerin %76–94'ü ~4 s'de toz çıkışına iniyor. S 3.17'deki çatı halkası kayboldu.
- Kesme çapı CFD'de ~30 µm (30 µm'de %54 kaçış). MM'nin temiz gaz x₅₀'si 37.7 µm, iç girdap verimi %40. CFD, MM'den biraz iyi ayırıyor; C1'deki uyuma benzer (CFD %71–75, MM %75.5).

**Yüklü MM, S 3.90:**
- α, CFD'nin v_θCS'sine (31.1 m/s) yeniden kalibre edildi: 0.913. H_CS 4.62 m. c₀ 0.95.
- Siklon ΔP **368–415 Pa** (515.5 × MM oranı).
- x₅₀ 51–54 µm, c₀L 0.065–0.070.
- η **%92.7–95.2**.

**Twin'e giden değerler (S 3.90, kullanıcı kararı 12 Ekim 2026: η bizim çözümümüzden):**
- **η %93**: yüklü MM'nin alt ucu (yalnız sınır yükleme), C1'deki gibi.
  - Literatürdeki ara kademe bandı (%80–90; KHD, JCPE 2025) bunun altında. Fark not edildi, değer değiştirilmedi.
  - MM'nin sınır yükleme bağıntısı yüksek c₀'da iyimser olabilir.
- **Gaz-yalnız ΔP:** Eu 11.38, yani 56 kg/s ve 1033 K'de 515.5 Pa.
- **Yüklü siklon ΔP:** ~390 Pa (368–415). Farklı debilerde ΔP ∝ ṁ_g².
- **R4'te farin kaynaklı ek kayıp:** ~124 Pa (S 3.17 bölümündeki hesap; geometriden bağımsız).
- İki hatlı tesiste siklon başına aynı: c₀ ve giriş hızı korunur.
- Bu değerler S 3.17'nin "Twin'e giden değerler"inin yerine geçer.

**Twin entegrasyonu (12 Ekim 2026):**
- **Ayar:** `configs/twin_cfg.yaml` → `preheater.c2_c4_separation_efficiency: 0.93`. C2, C3 ve C4 (twin Stage 4–2) için aynı değer. C5 `c5_separation_efficiency` ile ayrıca verilebilir, şimdilik 1.0.
- **Kaçan toz:** E = (1 − η)·(kademeden çıkan katı). Gazla bir üst kademeye gider ve oradaki katıya kendi sıcaklığıyla karışır.
  - Bu bir iç döngüdür: tesisten kütle çıkmaz, kalsinatöre giden katı değişmez (26.391 kg/s).
  - Etkisi ısı tarafında: sıcak alt kademenin tozu üst kademenin katısını ısıtır, yani ısı yukarı taşınır.
  - C1'in tozu eskisi gibi filtreyle beslemeye döner.
- **Kütle çözümü:** kademe akışları doğrusal bir sistemle çözülür (`heat_transfer.circulating_solid_flows`). Bütün η = 1 olunca model eskisiyle bit bit aynıdır.
- **Twin sonucu** (`run_twin`, nodes_per_stage 20):
  - C4 / C3 / C2'nin gazla yukarı taşıdığı toz 1.99 / 2.14 / 2.15 kg/s.
  - C1'in filtreye kaçırdığı toz 1.10'dan 1.19 kg/s'ye, toz ısı kaybı 0.52'den 0.57 MW'a çıktı.
  - Bütün enerji, kütle ve CO₂ dengeleri kapanıyor.

Dosyalar (repo dışında, `C:\Users\engin\c4_s390`):
- `c4.msh`
- `c4s_steady.*`
- `c4s_urans.cas.h5` / `.dat.h5`
- `c4su-*.dat.h5` (otomatik kayıtlar; case `c4su-*.cas.h5` ile ve her biri için yeniden okunarak açılmalı)
- `c4s_urans.out`
- `dpm\`: `c4s_dpm_unst_end.*`, `unst\*.dpm` (örnek dosyaları)

## Gaz-yalnız CFD, çıkış borusu 1.70·D_x (14 Ekim 2026)

Geometri S 3.90 ile aynı, yalnız çıkış borusu çatının üstünde 7.871 m (1.70·D_x; önce 5.79 m). `cyclone.bas`'ta `OUTLET_EXT_OVER_VORTEX_D` artık siklon başına (C1 1.25, C4 / C5 1.70).

**Mesh:** Ansys Meshing tet, global **155 mm** (150 mm Student düğüm sınırını aşardı), başka ayar yok.
- 900 054 tet → **317 085 poly hücre**, 1 014 835 düğüm.
- Min orthogonal quality **0.37**.
- Fluent'te ölçülen hacim 707.16 m³ (SolidWorks 707.81). Yüz alanları 9.90 / 16.82 / 0.507 m².

**Kurulum:** S 3.90 case'inin ayarları (`c4_settings.set`), aynı akış: Steady Coupled 350 iterasyon, sonra URANS 20 adım Δt 0.01 s ve 650 adım Δt 0.03 s, adım başına 20 iterasyon.
- Steady: **486.8 Pa** (S 3.90 / 1.25·D_x: 484.1).
- Koşu 14.7 s'de WSL bağlantısı koptuğu için durdu; 14.6 s'lik otomatik kayıttan devam ettirildi (devamın ilk adımları kopan koşuyla aynı).
- Girdap ~5 s'de oturdu. Ortalama 5.0–19.7 s penceresinden, 491 adım, 36 periyot; SE 10 bloğun ortalamalarından.

| Büyüklük | S 3.90, 1.25·D_x | **S 3.90, 1.70·D_x** |
|---|---|---|
| Statik ΔP (giriş − çıkış) | 515.5 Pa | **522.8 Pa** (SE 1.5; yarılar 521.2 / 524.3) |
| Toplam basınç düşümü | 506.4 Pa | 511.3 Pa |
| Euler sayısı | 11.38 | **11.54** |
| Girdap salınımı | 2.44 Hz | 2.44 Hz |
| v_max | 58.7 m/s | 61.3 m/s |

- ΔP %1.4 arttı (+7.3 Pa). Beklenen yönde ve küçük: 2.08 m'lik ek düz boru girdabın dirsekten önce biraz daha sönmesine izin verir, borudaki sürtünme kaybı birkaç Pa. Mesh 150 → 155 mm değişti; farkın bir kısmı mesh olabilir.
- Girdap frekansı aynı; siklonun iç akışı değişmedi.
- Ortalama alan, DPM ve yüklü MM bu domende yeniden yapılmadı. Çıkış borusu ayırma bölgesinin dışında olduğu için S 3.90 sonuçları (koniye inen gaz, v_θCS, η) geçerli sayılır.

**Twin'e giden değerler (S 3.90 bölümündekilerin yerine yalnız ΔP):**
- **Gaz-yalnız ΔP:** Eu 11.54, yani 56 kg/s ve 1033 K'de 522.8 Pa.
- **Yüklü siklon ΔP:** aynı MM oranıyla ~395 Pa (373–421).
- C5 C4'ün geometrik benzeri olduğu için Eu 11.54 C5'e de geçer.

**η: sınır yükleme + DPM iç girdabı (kullanıcı kararı, 14 Ekim 2026):**
- %93, iç girdabın hiç toz tutmadığı varsayılan alt sınırdı. Sınır yüklemenin bıraktığı katı, c₀L/c₀ = 0.065–0.070 / 0.95 = 0.068–0.074, neredeyse seyreltiktir. Tek yönlü temiz gaz DPM'i (S 3.90) tam bu durumu çözer.
- DPM'in beslemeyle ağırlıklı sonucu: %44.5 kaçan, %41.3 toz çıkışına inen, %14.2 domende kalan. Domende kalanlar oranla paylaşılınca iç girdap verimi 41.3 / 85.8 = **%48** (sınırlar %41 ve %56).
- η = 1 − (c₀L/c₀)(1 − 0.48) = **0.962–0.965 → twin'e 0.96** (sınırlar 0.957–0.970). MM'nin kendi iç girdap verimiyle (%40) bulunan üst değer %95.2'ydi; DPM onu destekliyor.
- Literatürdeki ara kademe bandı (%80–90) bunun altında; fark not edildi. DPM 1.25·D_x domeninde yapıldı; çıkış borusu ayırma bölgesinin dışında olduğu için 1.70·D_x'e geçer.
- C5 (0.90) şimdilik değişmedi (kullanıcı kararı).

Dosyalar (repo dışında, `C:\Users\engin\c4_rise170`):
- `c4.msh`, `c4_settings.set`, `run.jou`, `restart.jou`
- `c4r_steady.*`, `c4r_urans.cas.h5` / `.dat.h5` (19.7 s)
- `c4ru-1-00050…00500.dat.h5` (case `c4ru-1.cas.h5`), `c4ru2-2-00550…00650.dat.h5` (case `c4ru2-2.cas.h5`); her biri için case yeniden okunmalı
- `c4r_urans.out` (adım ≤ 500) ve `c4r_urans2.out` (501–670)

## Boundary Faces

| Ad | Tip | Alan |
|---|---|---|
| `inlet_gas` | mass-flow-inlet | 16.84 m² (Φ4.63, riser tabanı, z = 4.13 m) |
| `gas_outlet` | pressure-outlet | 16.84 m² (Φ4.63, z = 21.47 m) |
| `dust_outlet` | wall | 0.515 m² (Φ0.81) |
| `wall` | wall | geri kalan |

17 Kasım 2026 domeninin yüzleri; önceki domende giriş volüt kanalının ucuydu (9.90 m², 3.40 × 2.912), çıkış x = 9.26 m'de. Mesh'teki named selection'lar C1'in adlarıyla gelmişti (`meal_feed` = giriş, `wall_dust` = toz çıkışı); Fluent'te yeniden adlandırıldı.

## Derived Properties

Ekipman hacmi (gövde + koni) ve ıslak alan Geometrik Ölçüler'deki tabloda — CFD gövdesiyle (h = D; kullanıcı kararı, 13 Ekim 2026: twin C2–C4'te C5 gibi CFD gövdesini kullanır). Katalog ölçüleriyle (gövde 3.46 m) 194.5 m³ ve 169.9 m²'ydi.
