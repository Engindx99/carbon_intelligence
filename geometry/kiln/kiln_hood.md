# Kiln hood (fırın başlığı)

Tesis: 5000 t/d, tek fırın. Başlık, fırının ocak ucunu ve soğutucunun üstünü örter: soğutucudan yükselen sıcak hava (ikincil hava) fırına girer, tersiyer hava kanalı da buradan kalsinatöre ayrılır ([plant_topology.md](../plant_topology.md); [cooler.md](../cooler/cooler.md): `hood_opening`, 5.98 × 4 m, soğutucunun ilk iki segmentinin üstü).

Başlık için yayınlanmış bir ölçü ya da ölçü kuralı bulunamadı (16 Kasım 2026 araştırması). Yalnız hava hızı ölçütü var: **kullanıcı kararı (16 Kasım 2026): hız ölçütüyle boyutla**. Yerleşimdeki kare (fırının çevresinde `layout.chamber_margin` payıyla, kenar 2a) bu ölçütü sağladığı için kalır; ölçü bir **model** değeridir (Estimated), yayınlanmış bir tesis ölçüsü değildir.

## Hız kontrolü

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Conta kaçağı payı (fırın havasının) | 0.2 | literatür |
| İkincil hava sıcaklığı | 1250 K | modelleme |
| Fırın havası (twin) | 26.399 kg/s | türetilmiş |
| Birincil hava (eksenel + swirl) | 2.640 kg/s | türetilmiş |
| Conta kaçağı (ortam sıcaklığında) | 5.280 kg/s | türetilmiş |
| İkincil hava (fırın havası − birincil − kaçak) | 18.480 kg/s | türetilmiş |
| CFD: segment 1 girişi (ikincil + kaçak) | 23.759 kg/s | türetilmiş |
| CFD: segment 1 girişi, karışım sıcaklığı | 1052.0 K | türetilmiş |
| CFD: segment 2 girişi (tersiyer besleme) | 54.925 kg/s | türetilmiş |
| CFD: kömür taşıma havası (twin'de yok) | 1.254 kg/s | türetilmiş |
| CFD: kömür | 2.095 kg/s | türetilmiş |
| CFD: fırın gazı çıkışı (kütle dengesi) | 29.749 kg/s | türetilmiş |
| Hız ölçütü, alt | 4 m/s | literatür |
| Hız ölçütü, üst | 10 m/s | literatür |
| Başlıktan geçen hava (ikincil + tersiyer) | 73.40 kg/s | türetilmiş |
| Hacimsel debi (1073 K) | 224.1 m³/s | türetilmiş |
| Çıkış contasının dış yarıçapı (ROTAX) | 3.55 m | türetilmiş |
| Conta çevresindeki pay | 0.25 m | modelleme |
| Başlık genişliği (2 × (conta + pay)) | 7.60 m | türetilmiş |
| Başlık yüksekliği (soğutucu tavanından contanın üstüne) | 7.20 m | türetilmiş |
| Başlık derinliği (soğutucunun başlık açıklığı) | 5.98 m | türetilmiş |
| Kesit alanı (genişlik × yükseklik) | 54.72 m² | türetilmiş |
| Hız (1073 K) | 4.09 m/s | türetilmiş |
| Hız (ikincil havanın sıcaklığında) | 4.77 m/s | türetilmiş |
| Ölçütün izin verdiği en küçük kesit | 22.41 m² | türetilmiş |
<!-- END GENERATED -->

## Dayanak

- **Hava:** ikincil hava (twin: 26.25 kg/s) ve tersiyer hava (CFD sınırı: 54.93 kg/s, 1073 K, [calciner.md](../calciner/calciner.md)). Hepsi başlıktan geçer. Hız, tersiyer havanın sıcaklığında hesaplanır; ikincil hava daha sıcaktır (1250 K'de de kontrol edildi).
- **Ölçüt:** ikincil hava çok yüksek sıcaklıkta (600–1200 °C) ve düşük hızda (4–10 m/s) gelir ve kiln yanma havasının %80–95'idir (rotary kiln yakıcı patenti; yönetmelik değil). Başlık draftı 0 ile −2 mmSS arasında tutulur (işletme kılavuzu). Yayınlanmış tesis ölçüsü ya da başlık boyutu kuralı bulunamadı.
- Başlığın şekli (kare kesit) bir yerleşim kararıdır; ölçüt yalnız kesitin alt sınırını verir (tablodaki en küçük kenar).

**Bilinmeyenler (kaynak yok):** başlığın derinliği (sayfa düzlemine dik), yakıcının giriş açısı ve derinliği, kapılar, tersiyer hava çıkışının başlıktaki yeri ve ölçüsü, refrakter.

## CFD Geometry

Yok: başlık CFD katısı yapılmadı; soğutucu katısında `hood_opening` yüzü başlığa açılan sınırdır ([cooler.md](../cooler/cooler.md)).

## Boundary Faces

TBD (katı yok).
