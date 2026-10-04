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

## Boundary Faces

TBD (CFD_VIEW.pdf'te C4 için verilmemiş).

## Derived Properties

Ekipman hacmi: 194.5 m³ (katalog ölçüleriyle); CFD gövdesi (h = 6.30 m) 283.2 m³
