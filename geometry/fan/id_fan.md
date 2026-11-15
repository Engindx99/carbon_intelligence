# ID fan (ön ısıtıcı egzoz fanı)

Tesis: 5000 t/d, iki özdeş 2500 t/d hat tek fırında ([plant_topology.md](../plant_topology.md)). Her hattın C1 çıkışı kendi fanına gider; **hat başına bir fan** (kullanıcı kararı, 16 Kasım 2026). Kule dışı.

Bu tesisin fanı için yayınlanmış bir ölçü yok. Fan **prosese göre seçildi**: çalışma noktası twin'in egzozundan, basınç kullanıcının kararından, boyutlar fan yasalarından gelir. Sonuç bir **seçim**dir (Estimated); satıcı ölçüsü değildir.

## Çalışma noktası ve seçim

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Fan sayısı (hat başına) | 1 | CFD kararı |
| Egzoz debisi (hat başına) | 57.526 kg/s | modelleme |
| Egzoz sıcaklığı | 572.99 K | modelleme |
| Gaz mol kütlesi | 31.9 g/mol | modelleme |
| Fan girişi, atmosferin altında | 4000 Pa | modelleme |
| Toplam basınç artışı | 8000 Pa | modelleme |
| Verim | 0.8 | literatür |
| Dönme hızı | 1000 dev/dk | literatür |
| Giriş gaz yoğunluğu | 0.652 kg/m³ | türetilmiş |
| Hacimsel debi (hat başına) | 88.27 m³/s | türetilmiş |
| Hacimsel debi (hat başına) | 317785 m³/h | türetilmiş |
| Hacimsel debi (iki hat) | 635569 m³/h | türetilmiş |
| Mil gücü | 883 kW | türetilmiş |
| Motor gücü (×1.10) | 971 kW | türetilmiş |
| Uç hızı | 137.4 m/s | türetilmiş |
| Çark çapı D2 | 2.625 m | türetilmiş |
| Göz oranı D1/D2 | 0.7 | literatür |
| Göz çapı D1 | 1.837 m | türetilmiş |
| Göz hızı c0 | 33.3 m/s | türetilmiş |
| Debi katsayısı φ | 0.1187 - | türetilmiş |
| Kanat çıkış açısı β2 (teğetten) | 45 ° | literatür |
| Kanat sayısı katsayısı k | 8.5 | literatür |
| Kanat sayısı z = k sinβ2 / (1 − D1/D2) | 20 - | türetilmiş |
| Kanat kalınlığı | 0.012 m | modelleme |
| Kanat uçlarının göz/uç dairesine boşluğu | 0.001 m | modelleme |
| Hücum açısı | 3 ° | modelleme |
| Kanat giriş açısı β1 | 24.1 ° | türetilmiş |
| Çark giriş genişliği b1 | 0.459 m | türetilmiş |
| Hidrolik verim η_h | 0.88 | modelleme |
| Wiesner kayma katsayısı | 0.897 - | türetilmiş |
| Wiesner D1/D2 sınırı | 0.749 - | türetilmiş |
| Çıkış teğetsel hızı cu2 | 101.5 m/s | türetilmiş |
| Çıkış meridyen hızı cm2 | 21.7 m/s | türetilmiş |
| Çark çıkış genişliği b2 | 0.514 m | türetilmiş |
| Kanat yayı yarıçapı | 4.92 m | türetilmiş |
| Salyangoz genişlik oranı B/b2 | 3 | literatür |
| Salyangoz genişliği B | 1.542 m | türetilmiş |
| Dil boşluğu / D2 | 0.075 | literatür |
| Dil dairesi r3 | 1.509 m | türetilmiş |
| Dil burun yarıçapı / D2 | 0.075 | literatür |
| Salyangoz çıkış hızı | 30 m/s | modelleme |
| Spiral açısı (çıkış hızından) | 8.45 ° | türetilmiş |
| Spiral sonu r_end | 3.837 m | türetilmiş |
| Spiral sonu kesiti (yükseklik) | 2.327 m | türetilmiş |
| Spiral sonu kesitinde hız | 24.6 m/s | türetilmiş |
| Çıkış ağzı yüksekliği (h cosα − 2 burun) | 1.908 m | türetilmiş; alan 2.942 m² |
| Çıkış hızı (ağız) | 30.0 m/s | türetilmiş |
| Çıkış düz parçası / yükseklik | 1 | modelleme |
| Çıkış yönü (yataydan yukarı) | 45 ° | modelleme |
| MRF kenarı (dil boşluğunun payı) | 0.5 | modelleme |
| MRF bölgesi yarıçapı | 1.411 m | türetilmiş |
| Giriş konisi ağzı / D1 | 1.3 | modelleme |
| Ön yan sac (salyangoz ile kutu arası) | 0.05 m | modelleme |
| Giriş konisi boyu (gözden kutu tabanına) | 1.132 m | türetilmiş |
| Giriş konisi ağız çapı | 2.388 m | türetilmiş |
| Giriş kutusu alan oranı | 1.75 | modelleme |
| Giriş kutusu yükseklik oranı | 1.1 | modelleme |
| Giriş kutusu uzanım oranı | 0.5 | modelleme |
| Giriş kutusu yüzü (yükseklik × derinlik) | 2.627 m | türetilmiş; yükseklik, derinlik 1.766 m |
| Giriş kutusu hızı | 19.0 m/s | türetilmiş |
| Hacim: dönen bölge (kanatsız) | 2.998 m³ | türetilmiş |
| Hacim: kanatlar | 0.0778 m³ | türetilmiş |
| Hacim: dönen bölge (kanatlı) | 2.920 m³ | türetilmiş |
| Hacim: salyangoz + çıkış | 28.576 m³ | türetilmiş |
| Hacim: giriş konisi | 3.993 m³ | türetilmiş |
| Hacim: giriş kutusu | 17.176 m³ | türetilmiş |
<!-- END GENERATED -->

## Dayanak

- **Debi ve sıcaklık:** twin'in referans durumunda ön ısıtıcı egzozu 115.05 kg/s ve 572.2 K (hat başına 57.53 kg/s; `tests/data/twin_state_reference.json`). Gaz mol kütlesi (31.9 g/mol) kalsinasyon CO₂'si, yakıt ürünleri, N₂, O₂ ve nem için bir tahmindir. Fan girişi atmosferin 4 kPa altında alınır (twin'de basınç ağı yok).
- **Toplam basınç 8 kPa (kullanıcı kararı, model):** modelin kapsadığı hat basınç düşümü yaklaşık 2.2 kPa (C1 ≈ 440, C2 ve C3 ≈ 400'er, C4 ≈ 360, C5 ≈ 410 Pa yüklü; kalsinatör 149 Pa; [cyclone_C4.md](../preheater/cyclone_C4.md), [calciner.md](../calciner/calciner.md)). Fan ayrıca C1'den fana kanalı ve fan sonrası sistemi (ham değirmen, filtre, baca) yener; bunlar modelde yok. 8 kPa, aşağıdaki literatür örneklerinin (6–10 kPa) ortasıdır. World Cement'e göre basınç payı hesaplanan değerin %32 üstünde seçilir.
- **Literatür:**
  - Çin tesisi: 820 000 m³/h ve 10.2 kPa tasarım, 3350 kW motor; sonradan ölçülen 880 000 m³/h, 9.95 kPa, 3015 kW mil gücü, yani η = Q·Δp/P = 0.81 ([Howden vaka](https://files.chartindustries.com/Howden_Fans_Cement_Case_StMarys.pdf)); kapasite yazmıyor. Verim 0.80 bu ölçümden.
  - 3000 t/d, 4 kademeli eğitim örneği: 6 kPa.
  - Geri eğimli kanatlı (backward-curved) ön ısıtıcı fanı (seçilen tip), 1180 → 880 dev/dk (Holnam, [cemnet forumu](https://www.cemnet.com/Forum/thread/108246/preheater-fan-coating-problem.html)); çark çapı 2200–3500 mm ([Pengxiang kataloğu](https://directindustry.com/prod/zhejiang-pengxiang-hvac-equipment-co-ltd/product-232709-2328770.html)). 1000 dev/dk bu aralığın içinde.
  - 5000 t/d için 600 000–900 000 m³/h, 280–350 °C (satıcı blogu, kaynaksız; yalnız büyüklük sınıfı).
- **Boyut:** uç hızı u = √(2Δp / (ρ ψ)), ψ = 1.0 (model), çark çapı D = u / (π n), giriş çapı √(4Q / (π v)), v = 25 m/s (model). Motor, mil gücünün 1.10 katı.

**Tip (kullanıcı kararı, 16 Kasım 2026): tek girişli, tek genişlikli (SISW), geri eğimli kanatlı santrifüj fan.** Neden santrifüj: 8 kPa'lık basınç artışını ve 88 m³/s debiyi tek kademede eksenel fan vermez; sıcak (572 K) ve tozlu gazda ağır hizmet çarkı kullanılır; ön ısıtıcı ID fanı literatürde (Holnam, Howden vakaları, Pengxiang kataloğu) hep santrifüjtür. Neden geri eğimli: verimli ve düşük gürültülü; aynı performans için radyal uçlu kanattan daha büyük çark ister (cemnet, Holnam), ψ = 1.0 ve 2.99 m çark bu tip içindir. Radyal uçlu kanat toz birikimine daha dayanıklıdır; seçilmedi, seçilirse yalnız çark çapı değişir. Çark ölçüleri satıcı tasarımı değil, çalışma noktasından türetilmiş büyüklük sınıfıdır.

## CFD Geometry

Yok: fan CFD katısı yapılmadı; gaz hattının sınırı C1'in çıkış kanalıdır (twin C1 → "to ID fan").

## Boundary Faces

TBD (katı yok).
