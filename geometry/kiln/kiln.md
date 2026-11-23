# Kiln (fırın)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, Ek). Tesis: 5000 t/d, iki özdeş 2500 t/d ön ısıtıcı hattı tek fırına bağlı (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)). Kule dışı.
Kaynak: Jiangsu Pengfei 5000 t/d hattı (PF5000; değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı).

## Geometrik Ölçüler

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Efektif iç çap | 4.8 m | yayınlanmış |
| Boy | 60 m | CFD kararı |
| Eğim | 3 % | yayınlanmış |
| Geçiş bölgesi (arka uç) | 25 m | modelleme |
| Yanma bölgesi | 35.00 m | türetilmiş |
| Sac kabuk kalınlığı | 0.030 m | literatür |
| Tuğla (astar) kalınlığı | 0.220 m | literatür |
| Tuğla soğuk yüzü A (ISO 5417) | 0.103 m | literatür |
| Tuğla boyu L, bir halka (ISO 5417) | 0.198 m | literatür |
| Giriş tayrı, L'nin oranı (ROTAX-2) | 0.33 | FLS oranıyla türetilmiş |
| Çıkış tayrı, L'nin oranı (ROTAX-2) | 0.85 | FLS oranıyla türetilmiş |
| Tayr açıklığı | 31.20 m | türetilmiş |
| Tayr genişliği | 0.90 m | FLS oranıyla türetilmiş |
| Tayr kalınlığı (radyal) | 0.45 m | FLS oranıyla türetilmiş |
| Tayr ile sac arası (teğet askı) | 0.35 m | FLS oranıyla türetilmiş |
| Tayr dış çapı | 6.90 m | türetilmiş |
| Tayr altı sac kalınlığı | 0.090 m | literatür |
| Makara çapı / tayr çapı | 0.324 | literatür |
| Makara açısı (düşeyden) | 30.0 ° | literatür |
| Makara çapı | 2.24 m | türetilmiş |
| **Ekipman hacmi** | 1085.73 m³ | türetilmiş |
| **Duvar alanı** | 904.78 m² | türetilmiş |
<!-- END GENERATED -->

Dönme hızı, min: 0.6 rpm
Dönme hızı, max: 4.0 rpm

2500 fırınıyla aynı kural (kullanıcı kararı, 12 Ekim 2026): yayınlanmış gövde çapı efektif çap olarak alınır, eğim yayınlanmış %4 yerine %3'tür.

12 Ekim 2026'ya kadar bu doküman 2500 t/d hattının fırınını anlatıyordu: Jiangsu Pengfei 2500, Ø4.0 × 60 m, %3, 0.39–4.10 rpm.

Twin bu ölçüleri `geometry/plant_geometry.yaml`'dan okur (`main.load_cfg`; 14 Ekim 2026'ya kadar `configs/twin_cfg.yaml`'daydı). Tüp iki bölgeye bölünür: geçiş ve yanma (tabloda).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (π/4 · D² · L ve π · D · L).
