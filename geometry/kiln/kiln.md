# Kiln (fırın)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, Ek). Tesis: 5000 t/d, iki özdeş 2500 t/d ön ısıtıcı hattı tek fırına bağlı (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)). Kule dışı.
Kaynak: Jiangsu Pengfei 5000 t/d hattı (PF5000; değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı).

## Geometrik Ölçüler

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Efektif iç çap | 4.8 m | yayınlanmış |
| Boy | 74 m | yayınlanmış |
| Eğim | 3 % | yayınlanmış |
| Geçiş bölgesi (arka uç) | 30.83 m | modelleme |
| Yanma bölgesi | 43.17 m | türetilmiş |
| **Ekipman hacmi** | 1339.07 m³ | türetilmiş |
| **Duvar alanı** | 1115.89 m² | türetilmiş |
<!-- END GENERATED -->

Dönme hızı, min: 0.6 rpm
Dönme hızı, max: 4.0 rpm

2500 fırınıyla aynı kural (kullanıcı kararı, 12 Ekim 2026): yayınlanmış gövde çapı efektif çap olarak alınır, eğim yayınlanmış %4 yerine %3'tür.

12 Ekim 2026'ya kadar bu doküman 2500 t/d hattının fırınını anlatıyordu: Jiangsu Pengfei 2500, Ø4.0 × 60 m, %3, 0.39–4.10 rpm.

Twin bu ölçüleri `geometry/plant_geometry.yaml`'dan okur (`main.load_cfg`; 14 Ekim 2026'ya kadar `configs/twin_cfg.yaml`'daydı). Tüp iki bölgeye bölünür: geçiş ve yanma (tabloda).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (π/4 · D² · L ve π · D · L).
