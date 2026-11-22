# Riser R2

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C3 → C2 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R2, C3'ün çıkış borusunun dik devamıdır (kullanıcı kararı, 17 Kasım 2026): C3'ün ekseninde, vorteks bulucu çapında dik yükselir; üstü düzdür, oradan düz yüzeyli (ruled) bir geçişle C2'nin volüt kanalına girer. Geçişin dış duvarı 45° ile kanalın üst kenarına, iç duvarı daha dik kanal tabanına iner; kanal volütün 1.0 m önünde yataydır. Riser ekseni C2'nin ekseninden kolon aralığı kadar uzaktadır (`layout.column_offset`, en geniş riser'a, R4'e göre). İlk 1.70·D_x'i C3'ün CFD çıkış borusudur. Yayınlanmış HFC2500 riser'ı (Ø3.35 m, [catalog.md](../catalog.md)) ve FLS'nin `h_tot`'u (19.38 m) bu tesisin değildir; twin 13–14 Ekim 2026 arasında onlarla, düz silindir olarak çalıştı. 14 Ekim – 17 Kasım 2026 arasında R2, C3'ün CFD çıkış borusu, 90° dirseği ve C2'nin gövdesine giden yatay bacağıydı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Çap (C3'in vorteks bulucusu D_x) | 3.150 m | türetilmiş |
| Dik riser, C3'in çatısından dönüşe (ilk 5.355 m CFD çıkış borusu) | 9.791 m | türetilmiş |
| Riserın dirsek altındaki eğik kesimi | 30 ° | şematik |
| Dirsek, merkez çizgisi boyu (Ø → C2 girişi) | 3.560 m | türetilmiş |
| Yatay kanal, C2'nin volütüne | 2.000 m | türetilmiş |
| Riser ekseni, C2'nin ekseninden | 6.792 m | türetilmiş |
| Toplam boy | 15.351 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 136.99 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 172.67 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Ayrı katı yok. R2'nin CFD'deki karşılığı C4 domeninin girişidir ([cyclone_C4.md](cyclone_C4.md)): dik riser'ın 1.0·D'si, geçiş ve yatay kanal; R2 onunla birebirdir (aynı çap, aynı kolon aralığı). Dik kısmın kalanı ve C3'ün çıkış borusu ile birleşimi domende yok.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına bir riser). Twin'in ön ısıtıcı kademesi bunları kullanır ([fluid_volumes.md](../fluid_volumes.md)).
