# Meal pipe C5 (farin borusu)

Referans hat: 2500 t/d.
Bağlantı: C5 toz çıkışı → Fırın giriş odası, [kiln_inlet_chamber.md](../kiln/kiln_inlet_chamber.md). Topoloji: kullanıcı kararı (standart 5 kademe), kaynak yok.

## Geometrik Ölçüler

Adet: 1
("TBD": yayınlanmış kaynak yok. Model değerleri aşağıdaki "Boyutlandırma" bölümünde.)
İç çap: TBD — Kaynak yok
Boy: TBD — Kaynak yok
Yatayla eğim açısı: TBD — Kaynak yok
Güzergâh / dirsekler: TBD — Kaynak yok
Klape konumu: TBD — Kaynak yok
Varış noktasındaki giriş yüksekliği: TBD — Kaynak yok

Arayüz: başlangıç yüzü siklonun toz çıkışıdır (çapı [cyclone_C5.md](cyclone_C5.md)'deki tabloda). Bu değer siklonun ölçüsüdür, borunun çapı değildir.

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
| Hat başına farin debisi | 29.988 kg/s | modelleme |
| Bir borunun debisi | 29.99 kg/s | türetilmiş |
| Kütle akışı (kalsinatör borusunun) | 79.3 kg/(m² s) | türetilmiş |
| İç çap | 0.694 m | kütle akışı ölçeği |
| Kesit alanı | 0.378 m² | türetilmiş |
| Yatayla eğim | 60 ° | literatür (kalsinatör borusu) |
| Siklonun toz çıkışı çapı (arayüz, boru çapı değil) | 0.836 m | türetilmiş |
<!-- END GENERATED -->
