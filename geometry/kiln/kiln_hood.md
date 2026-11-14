# Kiln hood (fırın başlığı)

Tesis: 5000 t/d, tek fırın. Başlık, fırının ocak ucunu ve soğutucunun üstünü örter: soğutucudan yükselen sıcak hava (ikincil hava) fırına girer, tersiyer hava kanalı da buradan kalsinatöre ayrılır ([plant_topology.md](../plant_topology.md); [cooler.md](../cooler/cooler.md): `hood_opening`, 5.98 × 4 m, soğutucunun ilk iki segmentinin üstü).

Başlık için yayınlanmış bir ölçü ya da ölçü kuralı bulunamadı (16 Kasım 2026 araştırması). Yalnız hava hızı ölçütü var: **kullanıcı kararı (16 Kasım 2026): hız ölçütüyle boyutla**. Yerleşimdeki kare (fırının çevresinde `layout.chamber_margin` payıyla, kenar 2a) bu ölçütü sağladığı için kalır; ölçü bir **model** değeridir (Estimated), yayınlanmış bir tesis ölçüsü değildir.

## Hız kontrolü

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| İkincil hava debisi | 26.246 kg/s | modelleme |
| Hız ölçütü, alt | 4 m/s | literatür |
| Hız ölçütü, üst | 10 m/s | literatür |
| Başlıktan geçen hava (ikincil + tersiyer) | 81.17 kg/s | türetilmiş |
| Hacimsel debi (1073 K) | 247.8 m³/s | türetilmiş |
| Başlık kesiti (kare, kenar 2a) | 6.80 m | türetilmiş |
| Kesit alanı | 46.24 m² | türetilmiş |
| Hız (1073 K) | 5.36 m/s | türetilmiş |
| Hız (1250 K) | 6.24 m/s | türetilmiş |
| Ölçütün izin verdiği en küçük kenar | 4.98 m | türetilmiş |
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
