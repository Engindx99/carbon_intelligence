# Riser R3

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C4 → C3 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R3, C4'ün çıkış borusunun dik devamıdır (kullanıcı kararı, 17 Kasım 2026): C4'ün ekseninde, vorteks bulucu çapında dik yükselir; üstü düzdür, oradan düz yüzeyli (ruled) bir geçişle C3'ün volüt kanalına girer. Geçişin dış duvarı 45° ile kanalın üst kenarına, iç duvarı daha dik kanal tabanına iner; kanal volütün 1.0 m önünde yataydır. Riser ekseni C3'ün ekseninden kolon aralığı kadar uzaktadır (`layout.column_offset`, en geniş riser'a, R4'e göre). İlk 1.70·D_x'i C4'ün CFD çıkış borusudur. Yayınlanmış HFC2500 riser'ı (Ø3.45 m, [catalog.md](../catalog.md)) ve FLS'nin `h_tot`'u (20.37 m) bu tesisin değildir; twin 13–14 Ekim 2026 arasında onlarla, düz silindir olarak çalıştı. 14 Ekim – 17 Kasım 2026 arasında R3, C4'ün CFD çıkış borusu, 90° dirseği ve C3'ün gövdesine giden yatay bacağıydı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Çap (C4'in vorteks bulucusu D_x) | 3.150 m | türetilmiş |
| Dik riser, C4'in çatısından dönüşe (ilk 5.355 m CFD çıkış borusu) | 9.791 m | türetilmiş |
| Riserın dirsek altındaki eğik kesimi | 30 ° | şematik |
| Dirsek, merkez çizgisi boyu (Ø → C3 girişi) | 3.560 m | türetilmiş |
| Yatay kanal, C3'ün volütüne | 2.000 m | türetilmiş |
| Riser ekseni, C3'ün ekseninden | 6.792 m | türetilmiş |
| Toplam boy | 15.351 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 136.99 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 172.67 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Ayrı katı yok. R3'ün CFD'deki karşılığı C4 domeninin girişidir ([cyclone_C4.md](cyclone_C4.md)): dik riser'ın 1.0·D'si, geçiş ve yatay kanal; R3 onunla birebirdir (aynı çap, aynı kolon aralığı). Dik kısmın kalanı ve C4'ün çıkış borusu ile birleşimi domende yok.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına bir riser). Twin'in ön ısıtıcı kademesi bunları kullanır ([fluid_volumes.md](../fluid_volumes.md)).
