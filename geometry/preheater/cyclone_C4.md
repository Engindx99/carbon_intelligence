# Cyclone C4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d. Tekli siklon.
Farin borusu: [meal_pipe_C4.md](meal_pipe_C4.md)

## Geometrik Ölçüler

**Ara kademe standardı (kullanıcı kararı, 27 Eylül 2026):** C2 ve C3 bu siklonla özdeş; ölçüler aşağıdaki C4 değerleri.

Efektif iç çap, D: 6.30 m — HFC2500 (yayınlanmış)
Silindirik gövde yüksekliği: 3.46 m — FLS oranı (türetilmiş); **CFD'de 6.30 m** (aşağıda, kullanıcı kararı)
Koni yüksekliği: 7.30 m — FLS oranı (türetilmiş)
Vorteks bulucu çapı: 4.63 m — FLS oranı (türetilmiş)
Vorteks bulucu boyu (daldırma): 3.17 m — FLS oranı (türetilmiş)
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
- **Giriş 3.40 × 2.912 m = 9.90 m².** Katalog girişinin tesis debisindeki alanı: 56 kg/s ve 1033 K'de 16.0 m/s. Yükseklik, gövde henüz 3.46 m iken volüt tabanı gövde/koni kenarına denk gelmesin diye seçildi; genişlik alanı koruyor. Gövde uzadıktan sonra da korundu, çünkü yükseklik açıklığın ne kadarının vorteks bulucu ağzının altında kaldığını belirliyor: 3.17 m'lik daldırmayla %6.8. Giriş uzarsa kısa devre büyür.

**Gövde h = D = 6.30 m (kullanıcı kararı, 4 Ekim 2026; katalogdan sapma).**
- FLS oranının 3.46 m'si (h/D 0.55) 3.17 m'lik daldırmayla vorteks bulucu ağzını koninin yalnız 0.29 m üstüne koyuyordu.
- h/D 1.0 ile ağız koninin 3.13 m üstüne çıkıyor.
- Daldırma, koni, vorteks bulucu ve toz çıkışı katalogdaki gibi.
- CFD gövdesinin hacmi 283.2 m³; katalog ekipman hacmi 194.5 m³. Twin'in ön ısıtıcısı katalog hacmini kullanmıyor (yer tutucu geometri), bu yüzden twin etkilenmiyor.

**Çıkış:**
- Vorteks bulucu çatının 5.79 m (1.25 D_x) üstüne uzar; bu, C1'deki geri akış ölçümünün oranı.
- Ardından gelen 90° dirsek (merkez çizgisi yarıçapı 1.0 D_x = 4.63 m) gazı +x yönünde 4.63 m'lik (1.0 D_x) yatay bir bacağa çevirir. Gaz çıkış yüzü x = 9.26 m'de.
- C4'ün gazı R3 riser'ına gider, fana değil; bu yüzden C1'deki kaz boynu yerine 90° dirsek var. Dirsek girdabı kırar.
- C1'in oranları (1.5 D_x dirsek, 1.25 D_x bacak) Ø4.63 m'lik boruda çıkışı domenin yarısından fazlası yapıyordu (378 / 666 m³). 1.0 D_x, C1'in riser dirseğindeki oran (kullanıcı kararı, 4 Ekim 2026).
- Riser (R4) domende yok, giriş kanalında gaz düzgün profille girer.

CFD domeni ≈ 673.6 m³: siklon 283.2, volüt 96.3, çıkış 297.8, eksi vorteks bulucu duvarı 3.8 (makro log'u kesin değeri verir).

## Gaz-yalnız CFD (4–5 Ekim 2026)

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

**Twin'e giden değer (gaz-yalnız):** Eu 10.5, 56 kg/s ve 1033 K'de 477 Pa. Farklı debi ve yoğunlukta ΔP = Eu·½ρv_in². Yüklü durum ayrıca hesaplanacak.

Dosyalar (repo dışında, `C:\Users\engin\c4`):
- `c4_urans.cas.h5` / `.dat.h5`
- `c4_steady.*`
- `c4u-2-00350…00700.dat.h5` (ortalama kayıtları; `c4u-2.cas.h5` ile ve her biri için case yeniden okunarak açılmalı)
- `c4_urans_1_1.out` (adım bazında rapor)

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
