# Riser R2

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C3 → C2 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R2, C3'in CFD çıkış borusunun kendisidir: çatının üstündeki yükseliş, 90° dirsek ve C2'nin gövdesine giden yatay bacak, hepsi vorteks bulucu çapında (kullanıcı kararı, 14 Ekim 2026; [plant_topology.md](../plant_topology.md)). Bacağın boyu yerleşimden gelir (`layout.column_offset`). Girişe 45°'lik daralma ihmal edilir, boru tam çapta sayılır. Yayınlanmış HFC2500 riser'ı (Ø3.35 m, [catalog.md](../catalog.md)) ve FLS'nin `h_tot`'u (19.38 m) bu tesisin değildir; twin 13–14 Ekim 2026 arasında onlarla, düz silindir olarak çalıştı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Çap (C3'in vorteks bulucusu D_x) | 4.630 m | türetilmiş |
| C3 çıkış borusu yükselişi | 7.871 m | türetilmiş |
| 90° dirsek, merkez yayı | 7.273 m | türetilmiş |
| Bacak, C2 gövdesine | 7.220 m | türetilmiş |
| Toplam boy | 22.364 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 376.53 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 325.29 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Ayrı katı yok: R2, C3'in CFD domeninin çıkış borusudur ([cyclone_C4.md](cyclone_C4.md)); domen bacağın 1.0 D_x'inde, gaz çıkış yüzünde biter.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına bir riser). Twin'in ön ısıtıcı kademesi bunları kullanır ([fluid_volumes.md](../fluid_volumes.md)).
