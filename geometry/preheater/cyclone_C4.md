# Cyclone C4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d. Tekli siklon.
Farin borusu: [meal_pipe_C4.md](meal_pipe_C4.md)

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2 ve C3 bu siklonla özdeş; ölçüler aşağıdaki C4 değerleri.

Efektif iç çap, D: 6.30 m — HFC2500 (yayınlanmış)
Silindirik gövde yüksekliği: 3.46 m — FLS oranı (türetilmiş); **CFD'de 6.30 m** (aşağıda, kullanıcı kararı)
Koni yüksekliği: 7.30 m — FLS oranı (türetilmiş)
Vorteks bulucu çapı: 4.63 m — FLS oranı (türetilmiş)
Vorteks bulucu boyu (daldırma): 3.17 m — FLS oranı (türetilmiş); **CFD'de 3.90 m** (aşağıda, kullanıcı kararı)
Toz çıkışı çapı: 0.81 m — FLS oranı (türetilmiş)
Giriş genişliği: 1.27 m — FLS oranı (türetilmiş)
Giriş yüksekliği: 9.44 m — FLS oranı (türetilmiş)
Volüt geometrisi: TBD — 2500 hattı için kaynak yok

## CFD Geometry

Katı `geometry/macros/cyclone.bas` ile `CYCLONE_NAME = "C4"` seçilerek üretilir: `geometry/output/2500/C4.{SLDPRT,step,stl}` ve mesh ölçü silindiri `C4_boi.step`.

**Giriş ve volüt (kullanıcı kararı, 4 Ekim 2026; katalogdan sapma):**
- Katalog girişi 1.27 × 9.44 m CFD'de olduğu gibi kurulamıyor:
  - 1.27 m genişlik, gövde ile vorteks bulucu arasındaki 0.84 m'lik halkaya sığmıyor;
  - 9.44 m yükseklik 3.46 m'lik gövdeden uzun, koninin dibine (r ≈ 0.9 m) kadar iniyor;
  - açıklığın %66'sı vorteks bulucu ağzının altında kalıyor (C1'de reddedilen kısa devre).
- Tesis böyle bir girişi volütle besler. Model de basit bir volüt kurar:
  - çatıdan aşağı ekstrüde edilen düz bir kanal (3.0 m) ve 180°'de gövdeye inen bir Arşimet sarmalı;
  - iki uçta 5 cm'lik dil (C1'deki `INLET_TONGUE` ile aynı gerekçe).
- **Giriş 3.40 × 2.912 m = 9.90 m².** Katalog girişinin tesis debisindeki alanı: 56 kg/s ve 1033 K'de 16.0 m/s. Yükseklik, gövde henüz 3.46 m iken volüt tabanı gövde/koni kenarına denk gelmesin diye seçildi; genişlik alanı koruyor. Gövde uzadıktan sonra da korundu; daldırma bu yüksekliğe göre seçildi (aşağıda).

**Gövde h = D = 6.30 m (kullanıcı kararı, 4 Ekim 2026; katalogdan sapma).**
- FLS oranının 3.46 m'si (h/D 0.55) 3.17 m'lik daldırmayla vorteks bulucu ağzını koninin yalnız 0.29 m üstüne koyuyordu.
- h/D 1.0 ile ağız koninin 3.13 m üstüne çıkıyordu; daldırma 3.90 m'ye inince 2.40 m üstünde (aşağıda).
- Koni, vorteks bulucu çapı ve toz çıkışı katalogdaki gibi.
- CFD gövdesinin hacmi 283.2 m³; katalog ekipman hacmi 194.5 m³. Twin'in ön ısıtıcısı katalog hacmini kullanmıyor (yer tutucu geometri), bu yüzden twin etkilenmiyor.

**Çıkış:**
- Vorteks bulucu çatının 5.79 m (1.25 D_x) üstüne uzar; bu, C1'deki geri akış ölçümünün oranı.
- Ardından gelen 90° dirsek (merkez çizgisi yarıçapı 1.0 D_x = 4.63 m) gazı +x yönünde 4.63 m'lik (1.0 D_x) yatay bir bacağa çevirir. Gaz çıkış yüzü x = 9.26 m'de.
- C4'ün gazı R3 riser'ına gider, fana değil; bu yüzden C1'deki kaz boynu yerine 90° dirsek var. Dirsek girdabı kırar.
- C1'in oranları (1.5 D_x dirsek, 1.25 D_x bacak) Ø4.63 m'lik boruda çıkışı domenin yarısından fazlası yapıyordu (378 / 666 m³). 1.0 D_x, C1'in riser dirseğindeki oran (kullanıcı kararı, 4 Ekim 2026).
- Riser (R4) domende yok, giriş kanalında gaz düzgün profille girer.

**Daldırma S = 3.90 m (kullanıcı kararı, 5 Ekim 2026; katalogdan sapma).**
- Katalogdaki 3.17 m, 3.40 m'lik girişe karşı S/a 0.93 veriyordu: vorteks bulucu ağzı giriş tabanının 0.23 m üstündeydi.
- S 3.17 geometrisinin CFD'si (aşağıda) giriş jetinin ağza döndüğünü gösterdi: gazın %72'si ağzın altına iniyor ama 1–2 m içinde geri dönüyor; koniye ~%10'u ulaşıyor. Temiz gaz DPM'inde 40–70 µm'lik tanelerin %80–90'ı kaçtı.
- Literatür S/a ≥ 1.1–1.2 ister (Hoffmann & Stein; US3207494). 3.90 m ile S/a 1.15: ağız giriş tabanının 0.5 m altında, koninin 2.4 m üstünde (z 9.70).
- D_x/D 0.735 büyük ama katalog değeri; alt kademe siklonlarında verim yerine düşük ΔP için seçilir, değişmedi.

CFD domeni (S 3.90) ≈ 672.7 m³: S 3.17'deki 673.6 m³ eksi uzayan vorteks bulucu duvarı 0.86 m³ (makro log'u kesin değeri verir).

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
- η **%93.5**;
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
- Ortalama alan analizi, zamana bağlı DPM ve MM henüz yapılmadı. Bakılacaklar:
  - koniye inen gaz payı (S 3.17'de ~%10);
  - z 8.5–9.5'te duvar yukarı akışı;
  - v_θCS.

Dosyalar (repo dışında, `C:\Users\engin\c4_s390`):
- `c4.msh`
- `c4s_steady.*`
- `c4s_urans.cas.h5` / `.dat.h5`
- `c4su-*.dat.h5` (otomatik kayıtlar; case `c4su-*.cas.h5` ile ve her biri için yeniden okunarak açılmalı)
- `c4s_urans.out`

## Boundary Faces

| Ad | Tip | Alan |
|---|---|---|
| `inlet_gas` | mass-flow-inlet | 9.90 m² (3.40 × 2.912) |
| `gas_outlet` | pressure-outlet | 16.82 m² (Φ4.63, x = 9.26 m) |
| `dust_outlet` | wall | 0.507 m² (Φ0.81) |
| `wall` | wall | geri kalan |

Mesh'teki named selection'lar C1'in adlarıyla gelmişti (`meal_feed` = giriş, `wall_dust` = toz çıkışı); Fluent'te yeniden adlandırıldı.

## Derived Properties

Ekipman hacmi: 194.5 m³ (katalog ölçüleriyle); CFD gövdesi (h = 6.30 m) 283.2 m³
