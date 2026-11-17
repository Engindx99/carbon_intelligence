# Meal pipe C1 (farin borusu)

Referans hat: 2500 t/d.
Bağlantı: C1 toz çıkışı → Riser R2 (C3→C2), [riser_R2.md](riser_R2.md). Topoloji: kullanıcı kararı (standart 5 kademe), kaynak yok.

## Geometrik Ölçüler

Adet (her C1 siklonu için bir boru): 2
("TBD": yayınlanmış kaynak yok. Model değerleri aşağıdaki "Boyutlandırma" bölümünde.)
İç çap: TBD — Kaynak yok
Boy: TBD — Kaynak yok
Yatayla eğim açısı: TBD — Kaynak yok
Güzergâh / dirsekler: TBD — Kaynak yok
Klape konumu: TBD — Kaynak yok
Varış noktasındaki giriş yüksekliği: TBD — Kaynak yok

Arayüz: başlangıç yüzü siklonun toz çıkışıdır (çapı [cyclone_C1.md](cyclone_C1.md)'deki tabloda). Bu değer siklonun ölçüsüdür, borunun çapı değildir.

## CFD Geometry

Katı yok. CFD domenine dahil değil. Farin klapesi, farinin kullanmadığı kesiti kapatarak gazın bu yoldan kaçmasını önler; bu yüzden siklonun toz çıkışı bir sınır yüzüdür (eski karar 4, Holderbank s. 65).

## Boundary Faces

TBD (katı yok).

## Derived Properties

Ekipman hacmi: —

## Boyutlandırma (16 Kasım 2026, kullanıcı kararı)

Yukarıdaki "TBD" satırlar kaynak olmadığı içindir; bu bölüm bir **model** değeridir (Estimated), yayınlanmış bir ölçü değildir. Elimizdeki tek literatür boru kalsinatörün farin besleme borusudur (Ø0.8485 m, Fidaros 2007 × √2, [calciner.md](../calciner/calciner.md)); bir hattın C4 farinini taşır. Bütün meal pipe'lar o borunun kütle akışıyla (tabloda) boyutlanır. Eğim kalsinatör borusunun literatür değeridir (60°). **Boy, güzergâh ve klape konumu yerleşime bağlıdır, kaynak yok: listelenir, boyutlandırılmaz.**

C1'in toz çıkışı (Ø0.400 m, FLS oranı dust_D/D ≈ 0.092; C2–C5'te ≈ 0.13) bu borudan dardır ve aynı farini boru akışının ~2.25 katıyla taşır (tabloda). İki ölçü farklı kaynaklara dayandığı için ayrı tutulur (kullanıcı kararı, 16 Kasım 2026): preheater siklonunun çıkışı için bir tasarım akışı veren kaynak bulunamadı; CFD'de toz çıkışı duvar sınır koşuludur, twin bu çapı kullanmaz.

**Toz çıkışı akısı, FLS referansıyla (16 Kasım 2026, kullanıcı onayı; ölçü değişmedi).** Siklonun toz çıkışı için kıyas borunun akısı değil, aynı tasarım ailesinin siklon çıkışıdır. Svensen ve diğ. 2025 (arXiv 2504.02886) Tablo 8'deki FLS referans senaryosunda Cy1 r_c 3.45 / r_d 0.32 m (D 6.90, D_d 0.64 m; D_d/D 0.093), Cy2–Cy5 r_d 0.45 m (D_d/D 0.127–0.133); besleme 85.7 kg/s. Referansın Cy1 çıkışı bu farini 0.322 m²'den, yani **≥ 266 kg/(m² s)** ile geçirir (dönen toz hariç). Buradaki ikiz C1'ler hattın 44.85 kg/s'ini toplam 0.251 m²'den, ~178 kg/(m² s) ile (döngü tozuyla ~200) geçirir: referanstan düşük. Klapeli koni çıkışı gaz sızdırmazlığı için bilerek dardır; 79 kg/(m² s) bir eğik borunun değeridir ve çıkış için ölçüt değildir. Stairmand'ın D_d/D 0.25–0.375'i düşük yüklü, klapesiz siklonlarındır.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Boru sayısı (hat başına) | 2 | yerleşim kararı |
| Hat başına farin debisi | 44.85 kg/s | modelleme |
| Bir borunun debisi (hat başına borunun yarısı) | 22.43 kg/s | türetilmiş |
| Kütle akışı (kalsinatör borusunun) | 79.3 kg/(m² s) | türetilmiş |
| İç çap | 0.600 m | kütle akışı ölçeği |
| Kesit alanı | 0.283 m² | türetilmiş |
| Yatayla eğim | 60 ° | literatür (kalsinatör borusu) |
| Siklonun toz çıkışı çapı (arayüz, boru çapı değil) | 0.400 m | türetilmiş |
| Toz çıkışındaki kütle akışı (aynı debi) | 178.5 kg/(m² s) | türetilmiş |
| Toz çıkışı akışı / boru akışı | 2.25 | türetilmiş |
<!-- END GENERATED -->
