# Cyclone C5

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d.
**Hat başına bir C5** (kullanıcı kararı, 12 Ekim 2026). Tesis iki özdeş 2500 t/d hattından oluşur ([plant_topology.md](../plant_topology.md)). Kalsinatörün çift kaz boynunun her kolu bir hattın C5'ini besler. Bundan önce (29 Eylül 2026) tek hatlı bir kulede ikiz C5 vardı (katalog × 1/√2); o düzen kalktı.
Farin borusu: [meal_pipe_C5.md](meal_pipe_C5.md)

## Geometrik Ölçüler

Çap yayınlanmış değerdir: **D = 6.50 m**. **Diğer bütün ölçüler CFD'deki C4'ün ölçüleri × 6.50 / 6.30 = 1.0317** (kullanıcı kararı, 12 Ekim 2026). Gerekçe:
- Katalogdaki C5'in oranları C4'ünkilerle %1–2 içinde aynıydı.
- CFD'de çözülen C4 ise katalogdan üç noktada sapar: volüt giriş, h = D ve S/a 1.15 ([cyclone_C4.md](cyclone_C4.md)). Bu sapmalar C5'e de taşındı.
- Böylece C5, CFD'si çözülen siklonla tam geometrik benzer olur. C4'ün Euler sayısı ve volütün girdap katsayısı (α) ölçeklemesiz taşınır; C5'e ayrı CFD gerekmez.

Katalog C5'i (FLS oranları; [catalog.md](../catalog.md)): gövde 3.53, koni 7.43, daldırma 3.25, vorteks bulucu 4.74, toz çıkışı 0.83, giriş 1.30 × 9.59 m.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Hat başına adet | 1 | yayınlanmış |
| Efektif iç çap D | 6.5 m | yayınlanmış |
| Silindirik gövde yüksekliği | 6.5000 m | C4 × 1.031746 |
| Koni yüksekliği | 7.5317 m | C4 × 1.031746 |
| Vorteks bulucu daldırması S | 4.0238 m | C4 × 1.031746 |
| Vorteks bulucu çapı D_x | 4.7770 m | C4 × 1.031746 |
| Toz çıkışı çapı | 0.8357 m | C4 × 1.031746 |
| Giriş genişliği | 3.0044 m | C4 × 1.031746 |
| Giriş yüksekliği | 3.5079 m | C4 × 1.031746 |
| Giriş eğimi | 0 ° | CFD kararı; C4 ile özdeş |
| Volüt | var | CFD kararı; C4 ile özdeş |
| Çıkış dönüşü | 90 ° | CFD kararı; C4 ile özdeş |
| Çıkış borusu yükselişi (çatının üstünde) | 8.121 m | 1.7 D_x |
| Çıkış dirseği merkez yarıçapı | 4.777 m | 1 D_x |
| Çıkış bacağı / inişi | 4.777 m | 1 D_x |
| Toplam yükseklik (gövde + koni) | 14.032 m | türetilmiş |
| **Ekipman hacmi (gövde + koni)** | 311.09 m³ | türetilmiş |
| **Islak alan (gövde + çatı halkası + koni)** | 240.71 m² | türetilmiş |
<!-- END GENERATED -->

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

C4'ün CFD sonucu (Eu 11.38, S 3.90; 14 Ekim 2026'da 1.70·D_x çıkışla 11.54 oldu, ΔP'ler %1.4 artar) ve yüklü Muschelknautz (MM) kalibrasyonu (α 0.913) aynen kullanılır. Betik: `C:\Users\engin\c4\mm\c5_loaded.py` (repo dışı).

Hesap tabanı, C4'teki gibi literatürden gelir:
- C5'ten hattın bütün gazı geçer: 56 kg/s.
- Kalsinatör çıkışı 1123–1193 K; ρ_g C4'ün 0.353 kg/m³ değerinden sıcaklıkla ölçeklenir. μ 4.5e-5 Pa·s.
- Katı döngüsü (o günün twin değerleri; C2–C4 14 Ekim 2026'da 0.96'ya çıktı, [cyclone_C4.md](cyclone_C4.md)): C1 η 0.96–0.97, C2–C4 η 0.93, kalsinatörde %90 kalsinasyon. C5'e 33.1 kg/s katı girer; c₀ 0.59.
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

Gövde + koni hacmi ve ıslak alan Geometrik Ölçüler'deki tabloda (C4'ün CFD gövdesi × k³ ve × k²); iki hattın C5'leri bunun iki katı.

Katalog ölçüleriyle tek C5 211.2 m³'tü; h = D gövde hacmi büyüttü. Twin bu hacmi kalsinatör bölgesinde kullanır (`calciner.zone_segments`, [fluid_volumes.md](../fluid_volumes.md)).
