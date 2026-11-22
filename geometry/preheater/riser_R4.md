# Riser R4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C5 → C4 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R4, C5'in çıkış borusunun dik devamıdır (kullanıcı kararı, 17 Kasım 2026): C5'in ekseninde, vorteks bulucu çapında dik yükselir; üstü düzdür, oradan düz yüzeyli (ruled) bir geçişle C4'ün volüt kanalına girer. Geçişin dış duvarı 45° ile kanalın üst kenarına, iç duvarı daha dik kanal tabanına iner; kanal volütün 1.0 m önünde yataydır. Riser ekseni C4'ün ekseninden kolon aralığı kadar uzaktadır (`layout.column_offset`, en geniş riser'a, R4'e göre). İlk 1.70·D_x'i C5'in CFD çıkış borusudur. Yayınlanmış HFC2500 riser'ı (Ø3.60 m, [catalog.md](../catalog.md)) ve FLS'nin `h_tot`'u (19.87 m) bu tesisin değildir; twin 13–14 Ekim 2026 arasında onlarla, düz silindir olarak çalıştı. 14 Ekim – 17 Kasım 2026 arasında R4, C5'in CFD çıkış borusu, 90° dirseği ve C4'ün gövdesine giden yatay bacağıydı.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Çap (C5'in vorteks bulucusu D_x) | 3.250 m | türetilmiş |
| Dik riser, C5'in çatısından dönüşe (ilk 5.525 m CFD çıkış borusu) | 7.036 m | türetilmiş |
| Riserdan kanala eğik kanalın eğimi | 45 ° | şematik |
| Riserın üst ucu + eğik kanal, merkez çizgisi boyu (→ C4 girişi) | 6.590 m | türetilmiş |
| Yatay kanal, C4'ün volütüne | 2.000 m | türetilmiş |
| Riser ekseni, C4'ün ekseninden | 6.803 m | türetilmiş |
| Toplam boy | 15.626 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 142.71 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 176.54 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Ayrı katı yok. R4'ün CFD'deki karşılığı C4 domeninin girişidir ([cyclone_C4.md](cyclone_C4.md)): dik riser'ın 1.0·D'si, geçiş ve yatay kanal. R4 C5'in D_x'iyle (4.777 m) domenin riser'ından %3 geniştir; kolon aralığı aynıdır. Dik kısmın kalanı ve C5'in çıkış borusu ile birleşimi domende yok.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına bir riser). Twin'in ön ısıtıcı kademesi bunları kullanır ([fluid_volumes.md](../fluid_volumes.md)).
