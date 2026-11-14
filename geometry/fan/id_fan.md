# ID fan (ön ısıtıcı egzoz fanı)

Tesis: 5000 t/d, iki özdeş 2500 t/d hat tek fırında ([plant_topology.md](../plant_topology.md)). Her hattın C1 çıkışı kendi fanına gider; **hat başına bir fan** (kullanıcı kararı, 16 Kasım 2026). Kule dışı.

Bu tesisin fanı için yayınlanmış bir ölçü yok. Fan **prosese göre seçildi**: çalışma noktası twin'in egzozundan, basınç kullanıcının kararından, boyutlar fan yasalarından gelir. Sonuç bir **seçim**dir (Estimated); satıcı ölçüsü değildir.

## Çalışma noktası ve seçim

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Fan sayısı (hat başına) | 1 | CFD kararı |
| Egzoz debisi (hat başına) | 57.526 kg/s | modelleme |
| Egzoz sıcaklığı | 572.19 K | modelleme |
| Gaz mol kütlesi | 31.9 g/mol | modelleme |
| Fan girişi, atmosferin altında | 4000 Pa | modelleme |
| Toplam basınç artışı | 8000 Pa | modelleme |
| Verim | 0.8 | literatür |
| Dönme hızı | 1000 dev/dk | literatür |
| Giriş gaz yoğunluğu | 0.653 kg/m³ | türetilmiş |
| Hacimsel debi (hat başına) | 88.15 m³/s | türetilmiş |
| Hacimsel debi (hat başına) | 317341 m³/h | türetilmiş |
| Hacimsel debi (iki hat) | 634682 m³/h | türetilmiş |
| Mil gücü | 882 kW | türetilmiş |
| Motor gücü (×1.10) | 970 kW | türetilmiş |
| Uç hızı | 156.6 m/s | türetilmiş |
| Çark çapı | 2.99 m | türetilmiş |
| Giriş çapı | 2.12 m | türetilmiş |
<!-- END GENERATED -->

## Dayanak

- **Debi ve sıcaklık:** twin'in referans durumunda ön ısıtıcı egzozu 115.05 kg/s ve 572.2 K (hat başına 57.53 kg/s; `tests/data/twin_state_reference.json`). Gaz mol kütlesi (31.9 g/mol) kalsinasyon CO₂'si, yakıt ürünleri, N₂, O₂ ve nem için bir tahmindir. Fan girişi atmosferin 4 kPa altında alınır (twin'de basınç ağı yok).
- **Toplam basınç 8 kPa (kullanıcı kararı, model):** modelin kapsadığı hat basınç düşümü yaklaşık 2.2 kPa (C1 ≈ 440, C2 ve C3 ≈ 400'er, C4 ≈ 360, C5 ≈ 410 Pa yüklü; kalsinatör 149 Pa; [cyclone_C4.md](../preheater/cyclone_C4.md), [calciner.md](../calciner/calciner.md)). Fan ayrıca C1'den fana kanalı ve fan sonrası sistemi (ham değirmen, filtre, baca) yener; bunlar modelde yok. 8 kPa, aşağıdaki literatür örneklerinin (6–10 kPa) ortasıdır. World Cement'e göre basınç payı hesaplanan değerin %32 üstünde seçilir.
- **Literatür:**
  - Çin tesisi: 820 000 m³/h ve 10.2 kPa tasarım, 3350 kW motor; sonradan ölçülen 880 000 m³/h, 9.95 kPa, 3015 kW mil gücü, yani η = Q·Δp/P = 0.81 ([Howden vaka](https://files.chartindustries.com/Howden_Fans_Cement_Case_StMarys.pdf)); kapasite yazmıyor. Verim 0.80 bu ölçümden.
  - 3000 t/d, 4 kademeli eğitim örneği: 6 kPa.
  - Geri eğimli kanatlı (backward-curved) ön ısıtıcı fanı, 1180 → 880 dev/dk (Holnam, [cemnet forumu](https://www.cemnet.com/Forum/thread/108246/preheater-fan-coating-problem.html)); çark çapı 2200–3500 mm ([Pengxiang kataloğu](https://directindustry.com/prod/zhejiang-pengxiang-hvac-equipment-co-ltd/product-232709-2328770.html)). 1000 dev/dk bu aralığın içinde.
  - 5000 t/d için 600 000–900 000 m³/h, 280–350 °C (satıcı blogu, kaynaksız; yalnız büyüklük sınıfı).
- **Boyut:** uç hızı u = √(2Δp / (ρ ψ)), ψ = 1.0 (model), çark çapı D = u / (π n), giriş çapı √(4Q / (π v)), v = 25 m/s (model). Motor, mil gücünün 1.10 katı.

Tip: tek girişli, tek genişlikli, geri eğimli (veya radyal uçlu) santrifüj fan; tozlu sıcak gaz için kullanılır. Çark ölçüleri satıcı tasarımı değil, çalışma noktasından türetilmiş büyüklük sınıfıdır.

## CFD Geometry

Yok: fan CFD katısı yapılmadı; gaz hattının sınırı C1'in çıkış kanalıdır (twin C1 → "to ID fan").

## Boundary Faces

TBD (katı yok).
