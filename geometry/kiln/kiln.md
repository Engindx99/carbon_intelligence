# Kiln (fırın)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, Ek). Tesis: 5000 t/d, iki özdeş 2500 t/d ön ısıtıcı hattı tek fırına bağlı (kullanıcı kararı, 12 Ekim 2026; [plant_topology.md](../plant_topology.md)). Kule dışı.
Kaynak: Jiangsu Pengfei 5000 t/d hattı (PF5000; değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı).

## Geometrik Ölçüler

Efektif iç çap: 4.8 m
Boy: 74 m
Eğim: 3 %
Dönme hızı, min: 0.6 rpm
Dönme hızı, max: 4.0 rpm

2500 fırınıyla aynı kural (kullanıcı kararı, 12 Ekim 2026): yayınlanmış gövde çapı efektif çap olarak alınır, eğim yayınlanmış %4 yerine %3'tür.

12 Ekim 2026'ya kadar bu doküman 2500 t/d hattının fırınını anlatıyordu: Jiangsu Pengfei 2500, Ø4.0 × 60 m, %3, 0.39–4.10 rpm.

Twin (`configs/twin_cfg.yaml`, `kiln:`) bu ölçüleri henüz okumaz; twin'in 5000 t/d'ye taşınması ayrı bir adımdır.
