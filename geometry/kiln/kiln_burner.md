# Kiln burner (fırın yakıcısı)

Tesis: 5000 t/d, tek fırın ([plant_topology.md](../plant_topology.md)). Yakıcı fırının ocak (hood) ucundan girer, ekseni boyunca ateşler. **Tip: JETFLEX çok kanallı yakıcı** (FLSmidth/Fuller; kullanıcı kararı, 16 Kasım 2026): eksenel hava için dikdörtgen jet memeleri yakıt çevresinde eş merkezli, ayrıca girdap (swirl) havası; alev şekli ve momentumu ana olarak birincil hava basıncı ve debisiyle ayarlanır.

Bu tesisin yakıcısı için yayınlanmış bir ölçü yok. Yakıcı **prosese göre seçildi**: ısıl güç twin'in fırın yakmasından, jet momentumu JETFLEX'in yayınlanmış N/MW aralığından gelir. Sonuç bir **seçim**dir (Estimated); satıcı ölçüsü değildir.

## Çalışma noktası ve seçim

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Kiln yakıtı | 2.09494 kg/s | modelleme |
| Yakıt alt ısıl değeri | 32 MJ/kg | modelleme |
| Fırın yanma havası | 26.3993 kg/s | modelleme |
| Birincil hava payı | 0.1 | modelleme |
| Birincil hava sıcaklığı | 293.15 K | modelleme |
| Alev momentumu | 9 N/MW | literatür |
| Isıl güç | 67.04 MW | türetilmiş |
| Birincil hava debisi | 2.640 kg/s | türetilmiş |
| Jet momentumu | 603 N | türetilmiş |
| Ortalama jet hızı | 229 m/s | türetilmiş |
| Birincil hava yoğunluğu | 1.204 kg/m³ | türetilmiş |
| Jet toplam alanı | 0.0096 m² | türetilmiş |
| Jet eşdeğer çapı | 111 mm | türetilmiş |
<!-- END GENERATED -->

## Dayanak

- **Isıl güç:** twin'in referans durumunda fırın yakıtı 2.095 kg/s (toplamın %38'i, VDZ payı), LHV 32 MJ/kg → 67.04 MW ([configs/twin_cfg.yaml](../../configs/twin_cfg.yaml) `fuel`; `tests/data/twin_state_reference.json`). JETFLEX kapasite aralığı 10–250 MW içinde.
- **Birincil hava:** fırın yanma havası 29.16 kg/s, %10'u birincil (twin'in `burning.primary_air_fraction` değeri), ortam sıcaklığında (293.15 K varsayımı). Çok kanallı yakıcılar için 6–10 % aralığı anılır (Duoflex broşüründe 6–8 %; JETFLEX 2.0 oranı düşürmeye izin verir, sayı bulunamadı), yani 0.10 üst uca yakın ve twin ile tutarlı.
- **Momentum 9 N/MW (aralığın ortası):** FLSmidth, JETFLEX için birincil hava ile 7 N/MW'dan 11 N/MW'a alev momentumu verir ([FLSmidth JETFLEX](https://www.flsmidth.com/en-gb/products/pyro/jetflex-burner)). 9 N/MW × 67.04 MW = 603 N. Ortalama jet hızı momentum / debi = 207 m/s; jet toplam alanı debi / (ρ·u) ≈ 0.0117 m² (eşdeğer çap 122 mm). Bu **ortalama** bir değerdir; eksenel (yüksek hız) ve girdap (düşük hız) kanallarının payı bilinmez. Başka bir yakıcıdan örnek: eksenel hava ~350 m/s (%1.6), girdap ~160 m/s (%2.4), kömür taşıyıcı hava ~28 m/s (%2.3 ), kiln havasına oranla (patent anlatımı; kapasite yok).
- **Sınır:** JETFLEX kullanım kılavuzunda azami birincil hava basıncı 400 mbar ([Scribd kılavuz](https://www.scribd.com/document/681290457/FLSJETFLEX-20-Burner-1)); bu çalışma noktasındaki jet basıncı bunun altında kalmalıdır (hesaplanmadı).

**Bilinmeyenler (kaynak yok, çizilmez):** yakıcı borusu dış çapı, kanal sayısı ve ölçüleri, meme sayısı ve açıları, eksenel/girdap payı, yakıcının fırına giriş derinliği ve eğimi.

## CFD Geometry

Yok: yakıcı CFD katısı yapılmadı; fırın CFD'si de yok ([kiln.md](kiln.md)). Yakıcı fırın katısında bir giriş yüzü olacaksa, `kiln_hood` ucunda jet alanı (yukarıdaki tablo) bir sınır olarak verilir.

## Boundary Faces

TBD (katı yok).
