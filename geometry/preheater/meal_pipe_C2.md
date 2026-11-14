# Meal pipe C2 (farin borusu)

Referans hat: 2500 t/d.
Bağlantı: C2 toz çıkışı → Riser R3 (C4→C3), [riser_R3.md](riser_R3.md). Topoloji: kullanıcı kararı (standart 5 kademe), kaynak yok.

## Geometrik Ölçüler

Adet: 1
("TBD": yayınlanmış kaynak yok. Model değerleri aşağıdaki "Boyutlandırma" bölümünde.)
İç çap: TBD — Kaynak yok
Boy: TBD — Kaynak yok
Yatayla eğim açısı: TBD — Kaynak yok
Güzergâh / dirsekler: TBD — Kaynak yok
Klape konumu: TBD — Kaynak yok
Varış noktasındaki giriş yüksekliği: TBD — Kaynak yok

Arayüz: başlangıç yüzü siklonun toz çıkışıdır (çapı [cyclone_C2.md](cyclone_C2.md)'deki tabloda). Bu değer siklonun ölçüsüdür, borunun çapı değildir.

## CFD Geometry

Katı yok. CFD domenine dahil değil. Farin klapesi, farinin kullanmadığı kesiti kapatarak gazın bu yoldan kaçmasını önler; bu yüzden siklonun toz çıkışı bir sınır yüzüdür (eski karar 4, Holderbank s. 65).

## Boundary Faces

TBD (katı yok).

## Derived Properties

Ekipman hacmi: —

## Boyutlandırma (16 Kasım 2026, kullanıcı kararı)

Yukarıdaki "TBD" satırlar kaynak olmadığı içindir; bu bölüm bir **model** değeridir (Estimated), yayınlanmış bir ölçü değildir. Elimizdeki tek literatür boru kalsinatörün farin besleme borusudur (Ø0.8485 m, Fidaros 2007 × √2, [calciner.md](../calciner/calciner.md)); bir hattın C4 farinini taşır. Bütün meal pipe'lar o borunun kütle akışıyla (tabloda) boyutlanır. Eğim kalsinatör borusunun literatür değeridir (60°). **Boy, güzergâh ve klape konumu yerleşime bağlıdır, kaynak yok: listelenir, boyutlandırılmaz.**

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Boru sayısı (hat başına) | 1 | yerleşim kararı |
| Hat başına farin debisi | 44.85 kg/s | modelleme |
| Bir borunun debisi | 44.85 kg/s | türetilmiş |
| Kütle akışı (kalsinatör borusunun) | 79.3 kg/(m² s) | türetilmiş |
| İç çap | 0.849 m | kütle akışı ölçeği |
| Kesit alanı | 0.565 m² | türetilmiş |
| Yatayla eğim | 60 ° | literatür (kalsinatör borusu) |
| Siklonun toz çıkışı çapı (arayüz, boru çapı değil) | 0.810 m | türetilmiş |
<!-- END GENERATED -->
