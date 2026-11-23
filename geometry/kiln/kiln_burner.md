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
| Birincil hava payı (eksenel + girdap) | 0.1 | modelleme |
| Birincil hava sıcaklığı | 293.15 K | modelleme |
| Eksenel hava basıncı | 28500 Pa | literatür |
| Girdap hava basıncı | 16500 Pa | literatür |
| Kömür / taşıma havası yüklemesi | 1.67 | literatür |
| Alev momentumu, alt sınır | 7 N/MW | literatür |
| Alev momentumu, üst sınır | 11 N/MW | literatür |
| Kömür hızı, karşılaştırma | 33 m/s | literatür |
| Eksenel yarık sayısı | 20 | FLS oranıyla türetilmiş |
| Yarık alanı / D_uç² | 0.000947 | FLS oranıyla türetilmiş |
| Yarık boy / en | 3.17 | FLS oranıyla türetilmiş |
| Yarığın teğetten açısı | 13 ° | FLS oranıyla türetilmiş |
| Yarık halkası r / D_uç | 0.3438 | FLS oranıyla türetilmiş |
| Girdap deliği sayısı | 40 | FLS oranıyla türetilmiş |
| Delik ağzı alanı / D_uç² | 0.000259 | FLS oranıyla türetilmiş |
| Delik halkası r / D_uç | 0.2898 | FLS oranıyla türetilmiş |
| Katı yakıt borusu D / D_uç | 0.3335 | FLS oranıyla türetilmiş |
| Katı yakıt borusu kaçıklığı (yukarı) / D_uç | 0.0536 | FLS oranıyla türetilmiş |
| Girdap deliği eksen açısı | 30 ° | modelleme |
| Ön plaka kalınlığı | 0.06 m | modelleme |
| Plenum boyu | 0.5 m | modelleme |
| Kömür borusu boyu / D | 5 | modelleme |
| Plenum açıklığı | 0.004 m | modelleme |
| Kanallar arası en ince duvar | 0.003 m | modelleme |
| Isıl güç | 67.04 MW | türetilmiş |
| Birincil hava (eksenel + girdap) | 2.640 kg/s | türetilmiş |
| Eksenel hava | 1.938 kg/s | türetilmiş |
| Girdap hava | 0.702 kg/s | türetilmiş |
| Girdap payı | 0.266 | türetilmiş |
| Taşıma havası | 1.254 kg/s | türetilmiş |
| Fırına giren soğuk hava payı (birincil + taşıma) | 0.148 | türetilmiş |
| Eksenel jet hızı | 200.7 m/s | türetilmiş |
| Girdap jet hızı | 157.6 m/s | türetilmiş |
| Momentum (Σ ṁu) | 500 N | türetilmiş |
| Momentum / ısıl güç | 7.45 N/MW | türetilmiş |
| Eksenel momentum bileşeni | 485 N | türetilmiş |
| Uç dış çapı D_uç | 628 mm | türetilmiş |
| Eksenel açıklık alanı | 0.00747 m² | türetilmiş |
| Yarık boy × en | 34.4 × 10.9 mm | türetilmiş |
| Yarık halkası yarıçapı | 216.0 mm | türetilmiş |
| Girdap akış alanı (deliğe dik) | 0.00354 m² | türetilmiş |
| Girdap deliği kenarı (deliğe dik) | 9.4 mm | türetilmiş |
| Delik halkası yarıçapı | 182.0 mm | türetilmiş |
| Kömür borusu iç çapı | 209.5 mm | türetilmiş |
| Kömür borusu kaçıklığı (yukarı) | 33.7 mm | türetilmiş |
| Kömür borusu hızı | 30.2 m/s | türetilmiş |
| Eksenel plenum r | 203.4 … 229.7 mm | türetilmiş |
| Girdap plenumu r | 173.3 … 196.3 mm | türetilmiş |
| Hacim: kömür / eksenel / girdap | 0.0361 / 0.0183 / 0.0136 m³ | türetilmiş |
| Gövde: uç halkası boyu / D_uç | 1.11 | FLS oranıyla türetilmiş |
| Gövde: refrakter boyu / D_uç | 10.42 | FLS oranıyla türetilmiş |
| Gövde: refrakter çapı / D_uç | 0.97 | FLS oranıyla türetilmiş |
| Gövde: arka kafa boyu / D_uç | 2 | FLS oranıyla türetilmiş |
| Gövde: arka kafa çapı / D_uç | 0.89 | FLS oranıyla türetilmiş |
| Gövde: kömür girişi boyu / D_uç | 2.19 | FLS oranıyla türetilmiş |
| Gövde: kiriş boyu / D_uç | 6 | şematik |
| Gövde: çelik brülör borusu et kalınlığı | 0.01 m | modelleme |
| Brülör toplam boyu | 9.57 m | türetilmiş |
| Refrakter dış çapı (uç halkasının arkası) | 609 mm | türetilmiş |
| Çelik brülör borusu dış çapı | 479 mm | türetilmiş |
| Refrakter boru boyu | 6.55 m | türetilmiş |
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
