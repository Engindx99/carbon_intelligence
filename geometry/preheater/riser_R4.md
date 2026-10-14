# Riser R4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C5 → C4 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R4, C5'in CFD çıkış borusunun kendisidir: çatının üstündeki yükseliş, 90° dirsek ve C4'nin gövdesine giden yatay bacak, hepsi vorteks bulucu çapında (kullanıcı kararı, 14 Ekim 2026; [plant_topology.md](../plant_topology.md)). Bacağın boyu yerleşimden gelir (`layout.column_offset`). Girişe 45°'lik daralma ihmal edilir, boru tam çapta sayılır. Yayınlanmış HFC2500 riser'ı (Ø3.60 m, [catalog.md](../catalog.md)) ve FLS'nin `h_tot`'u (19.87 m) bu tesisin değildir; twin 13–14 Ekim 2026 arasında onlarla, düz silindir olarak çalıştı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Çap (C5'in vorteks bulucusu D_x) | 4.777 m | türetilmiş |
| C5 çıkış borusu yükselişi | 8.121 m | türetilmiş |
| 90° dirsek, merkez yayı | 7.504 m | türetilmiş |
| Bacak, C4 gövdesine | 7.073 m | türetilmiş |
| Toplam boy | 22.698 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 406.80 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 340.63 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Ayrı katı yok: R4, C5'in CFD domeninin çıkış borusudur ([cyclone_C4.md](cyclone_C4.md)); domen bacağın 1.0 D_x'inde, gaz çıkış yüzünde biter.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına bir riser). Twin'in ön ısıtıcı kademesi bunları kullanır ([fluid_volumes.md](../fluid_volumes.md)).
