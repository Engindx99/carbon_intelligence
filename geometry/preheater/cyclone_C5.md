# Cyclone C5

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d.
**Hat başına bir C5** (kullanıcı kararı, 12 Ekim 2026). Tesis iki özdeş 2500 t/d hattından oluşur ([plant_topology.md](../plant_topology.md)). Kalsinatörün çift kaz boynunun her kolu bir hattın C5'ini besler. Bundan önce (29 Eylül 2026) tek hatlı bir kulede ikiz C5 vardı (katalog × 1/√2); o düzen kalktı.
Farin borusu: [meal_pipe_C5.md](meal_pipe_C5.md)

## Geometrik Ölçüler

Çap yayınlanmış değerdir: **D = 6.50 m**. **Diğer bütün ölçüler CFD'deki C4'ün ölçüleri × 6.50 / 6.30 = 1.0317** (kullanıcı kararı, 12 Ekim 2026). Gerekçe:
- Katalogdaki C5'in oranları C4'ünkilerle %1–2 içinde aynıydı.
- CFD'de çözülen C4 ise katalogdan üç noktada sapar: volüt giriş, h = D ve S/a 1.15 ([cyclone_C4.md](cyclone_C4.md)). Bu sapmalar C5'e de taşındı.
- Böylece C5, CFD'si çözülen siklonla tam geometrik benzer olur. C4'ün Euler sayısı ve volütün girdap katsayısı (α) ölçeklemesiz taşınır; C5'e ayrı CFD gerekmez.

| Ölçü | Katalog | **C5 (CFD C4 × 1.0317)** |
|---|---|---|
| Efektif iç çap, D | 6.50 m — HFC2500 (yayınlanmış) | **6.50 m** |
| Silindirik gövde yüksekliği | 3.53 m — FLS oranı | **6.50 m** (h = D) |
| Koni yüksekliği | 7.43 m — FLS oranı | **7.532 m** |
| Vorteks bulucu boyu (daldırma) | 3.25 m — FLS oranı | **4.024 m** (S/a 1.15) |
| Vorteks bulucu çapı | 4.74 m — FLS oranı | **4.777 m** |
| Toz çıkışı çapı | 0.83 m — FLS oranı | **0.836 m** |
| Giriş genişliği | 1.30 m — FLS oranı | **3.004 m** (volüt) |
| Giriş yüksekliği | 9.59 m — FLS oranı | **3.508 m** (volüt) |

Volüt giriş kesiti 10.54 m², C4'ün 9.90 m²'si × k². Katalogdaki yarık giriş gövde ile vorteks bulucu arasına sığmıyordu; C4'teki gibi basit bir volüt kurulur.

## CFD Geometry

Katı `cyclone.bas` ile `CYCLONE_NAME = "C5"` seçilerek kurulur. Modelleme seçimleri C4'ünkiyle aynı:
- volüt (`VOLUTE_ON`);
- 90° çıkış dirseği ve 1.0 D_x yatay bacak; gaz R4'e gider;
- riser yok.

Şimdilik C5 için CFD koşulmuyor; değerler aşağıda C4'ten ölçeklenir. Volüt dili (0.05 m) ve vorteks bulucu duvarı (0.08 m) makroda mutlak değerlerdir, ölçeklenmez; etkileri ihmal edilebilir. İki hattın C5'leri özdeştir; bir CFD koşulursa tek C5 çözülür, ikincisi onun kopyasıdır. Kalsinatör ile C5 ayrı domenlerdir; bağ kaz boynu kolunun çıkış yüzü üzerinden kurulur.

## Boundary Faces

TBD (katı henüz kurulmadı).

## Basınç Düşüşü ve Ayırma (12 Ekim 2026)

C4'ün CFD sonucu (Eu 11.38, S 3.90) ve yüklü Muschelknautz (MM) kalibrasyonu (α 0.913) aynen kullanılır. Betik: `C:\Users\engin\c4\mm\c5_loaded.py` (repo dışı).

Hesap tabanı, C4'teki gibi literatürden gelir:
- C5'ten hattın bütün gazı geçer: 56 kg/s.
- Kalsinatör çıkışı 1123–1193 K; ρ_g C4'ün 0.353 kg/m³ değerinden sıcaklıkla ölçeklenir. μ 4.5e-5 Pa·s.
- Katı döngüsü: C1 η 0.96–0.97, C2–C4 η 0.93, kalsinatörde %90 kalsinasyon. C5'e 33.1 kg/s katı girer; c₀ 0.59.
- Tane boyu dağılımı C1 ve C4 ile aynı (Rosin-Rammler).

| | 1123 K | 1163 K | 1193 K |
|---|---|---|---|
| Giriş hızı | 16.4 m/s | 17.0 m/s | 17.4 m/s |
| Gaz-yalnız ΔP (Eu × q_in) | 495 Pa | 512 Pa | 526 Pa |
| Yüklü ΔP | 374–414 Pa | 388–429 Pa | 398–440 Pa |
| Yüklü η (alt – üst uç) | %89.3–93.0 | %89.5–93.1 | %89.6–93.3 |

- Aralıklar, yükleme altında α'nın iki ucundan gelir: sabit 0.913 ya da yarık bağıntısıyla ölçeklenmiş 0.984.
- **Neden C4'ten düşük:** C4'te η %93'tü. C5'te yükleme daha düşük (c₀ 0.59'a karşı 0.95), sınır yükleme daha az pay ayırır. Kesme çapı da büyük (x₅₀ 49–53 µm'ye karşı ~45 µm): gaz daha sıcak ve viskoz, siklon C4'ten biraz büyük.
- **Gözenekli kalsine farin:** tane yoğunluğu 2700 yerine 2000 kg/m³ alınırsa yüklü η'nın alt ucu %87.9–88.5'e iner.
- Literatürde alt kademe bandı %73–85; MM'nin sınır yükleme bağıntısı iyimser olabilir.

**Twin değeri** (kullanıcı kararı, 12 Ekim 2026):
- **η %90**: yüklü MM'nin alt ucu, ρ_p 2700 ile; C4'teki seçimin aynısı. `configs/twin_cfg.yaml` → `preheater.c5_separation_efficiency`.
- ΔP: Eu 11.38; yüklü ~410 Pa.

C5'ten kaçan toz, C2–C4'teki gibi gazla bir üst kademeye (C4) gider.

## Derived Properties

Gövde + koni hacmi: **311.0 m³** (C4'ün CFD gövdesi 283.2 m³ × k³). İki hattın C5'leri toplam 622.1 m³.

Katalog ölçüleriyle tek C5 211.2 m³'tü; h = D gövde hacmi büyüttü. 13 Ekim 2026'dan beri twin'in ön ısıtıcısı bu hacmi kullanır.

Islak alan (gövde + çatı halkası + koni): **240.7 m²** (C4'ün 226.1 m²'si × k²).
