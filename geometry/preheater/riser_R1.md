# Riser R1

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C2 → C1 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

R1'in iç çapı yayınlanmıştır (HFC2500). Gaz yolu çizimdeki gibidir ([plant_topology.md](../plant_topology.md)): C2'nin CFD çıkış borusu (çatının üstünde 7.871 m dik), 45°'lik bir daraltıcı (Ø4.63 → Ø3.07), R1'in **C2'nin ekseninde** Y'ye kadar dik kısmı, sonra ikiz C1'lerin her birine bir kol (R1 alanının yarısı): dik kısım, 90° dirsek, geçiş ve giriş kanalı. R1 17 Kasım 2026'dan beri düz (kullanıcı kararı); ikiz C1'ler C2'nin üstünde durur. 14 Ekim – 17 Kasım 2026 arasında C2'nin CFD dirseği ve bacağı gazı kalsinatöre doğru 11.3 m taşıyor, R1 orada bir dirsekle yükseliyordu (yol hacmi hat başına 517 m³; düz yol 322 m³).

Fiziksel sonucu: C2'nin vorteks bulucusundan çıkan dönen akım dirseklerle bozulmadan R1'e ve Y'ye ulaşır. Düz boruda dönme yavaş söner (çap başına ~%2–3) ve C2'den Y'ye yaklaşık 4 çaplık bir yol var. Daraltıcı açısal momentumu korurken eksenel momentumu artırır, dönme sayısını ~1/3 düşürür. Eksen simetrik girdap Y'de simetrik bölünür. Önceki düzende ise dirseğin hemen üstündeki kısa R1, Y'ye bir yana yığılmış bir profil veriyordu. Aynalı ikizlerin girişine ters yönlü dönme gelir. Kollardaki ~3.5 çaplık dik kısım, farin beslemesi, dirsek ve daralma bunu büyük ölçüde siler; ama C1 verimine etkisi ölçülmedi. Tek C1 CFD'sinin düzgün giriş profili her iki düzende de bir yaklaşımdır: Y'li bir giriş domeni gerekir. R1'de farin yoktur (besleme kollarda), bu yüzden kısalması gaz–farin temasını değiştirmez. Y'nin kendi kısa parçaları kolların boyuna katılır. FLS'nin `h_tot`'u (21.38 m) ile düz silindir okuması twin'de 13–14 Ekim 2026 arasında kullanıldı; bu tesisin değildir.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| C2 çıkış borusu yükselişi (Ø3.150) | 5.355 m | türetilmiş |
| R1 iç çapı (= C2 D_x, daraltıcı yok) | 3.150 m | türetilmiş |
| R1 dik boyu, C2 CFD çıkışından Y'ye | 2.138 m | türetilmiş |
| İkiz C1 kolu çapı (R1 alanının yarısı) | 2.227 m | türetilmiş |
| Kol başına boy (dik + 90° dirsek + geçiş + kanal) | 17.574 m | türetilmiş |
| Kol sayısı | 2 | türetilmiş |
| İkiz C1 kolları arası boşluk (cidardan cidara) | 1 m | modelleme |
| İkiz C1 eksenleri arası | 8.507 m | türetilmiş |
| İkiz C1 gövdeleri arası boşluk | 4.187 m | türetilmiş |
| Y'den her kolun R1 eksenine uzaklığı | 1.614 m | türetilmiş |
| Y'nin yüksekliği (R1 tepesinden kolların dik kısmına) | 2.075 m | türetilmiş |
| R1 ve kollar, C1 eksenlerinin önünde | 6.727 m | türetilmiş |
| **Ekipman hacmi (hat başına)** | 195.35 m³ | türetilmiş |
| **Duvar alanı (hat başına)** | 320.09 m² | türetilmiş |
<!-- END GENERATED -->

## CFD Geometry

Riser, C1'in CFD domenine **C1'in giriş kanalının önüne** eklenir (`geometry/macros/cyclone.bas`,
`RISER_ON = True`, çıktı `geometry/output/2500/C1_riser.*`). Ayrı bir katı değil, C1 akışkan
hacminin parçası. Aşağıdaki boyların hiçbiri yayınlanmış değil — **CFD için türetilmiş modelleme
seçimleri** (kullanıcı kararı, 28 Eylül 2026).

Gerekçe: C1'e farini giriş kanalının ucundan 542 K'de vermek iki yönlü DPM'i ve DDPM'i
ıraksattı; 542 K de gaz–farin ısı alışverişinin 80/20 riser/siklon paylaşımı varsayımıydı.
DTU'nun endüstriyel DDPM siklon çalışması (Mirzaei 2023) farini riser'a verir, ısı alışverişi
orada olur. Riser'la bu paylaşım ölçülen bir sonuç olur.

Kesit: **yuvarlak Ø2.171 m** — yayınlanmış Ø3.07 m ikiz C1'leri birlikte besler, C1 başına
alanının yarısı düşer (3.70 m²). 17.9 kg/s'de hız 8.7 m/s (638 K) – 10.6 m/s (776 K); DTU'nun
ölçtüğü riser hızları 7.5–9.3 m/s; tesis debisinde (C1 başına 28.76 kg/s) beslemenin altında ~16 m/s
(~800 K), üstünde ~12.5 m/s (603 K). Tesisteki gibi riser ve dirsek yuvarlak; siklona C1'in giriş
kanalından girilir, arada 1.5 m'lik bir yuvarlak→dikdörtgen geçiş var. Kanal 16 Kasım 2026'dan beri
volütün 0.86 × 3.00 m'lik yatay kanalı ([cyclone_C1.md](cyclone_C1.md)); önce 0.86 × 2.16 m'lik,
5° eğimli yarıktı.
Önceki sürümler (28 Eylül) kanal kesitini aşağıya kadar sürdürüyordu ve ince kalıyordu. Kare
siklon girişi elendi: aynı alanda 1.36 m'lik kenar vorteks bulucuya çarpar (halka 0.88 m).

Düzen (C1 koordinatları, siklon ekseni z, toz çıkışı z = 0; volütlü C1, 16 Kasım 2026, build
logu `geometry/output/2500/C1_cyclone_build.log`):
- Geçiş: kanal ekseni boyunca 1.5 m; (−4.500, 2.64, 9.940) merkezli daireden volüt kanalının uç
  yüzüne (merkez (−3.000, 2.64, 9.940), 0.86 × 3.00 m) loft. y'de daralır (yarım açı 24°), z'de
  genişler (yarım açı 15°). Loft hacmi 4.763 m³.
- Dirsek: daire, (−4.500, y, 7.769)'dan geçen y'ye paralel eksen etrafında 90°, düz yukarıdan
  yatay kanal eksenine döner; merkez çizgisi yarıçapı 2.171 m (1.0 D). Tepesi z = 11.025 m, çatının
  (11.44) altında. Dirsek (1.5 D → 1.0 D) ve geçiş (2.0 → 1.5 m) riser siklona yaklaşsın diye
  kısaltılmıştı (kullanıcı kararı, 29 Eylül 2026).
- Düz riser: eksen x = −6.671, y = 2.64; z 0.269 … 7.769 (7.5 m).
- Farin besleme oluğu ("distribution box"): riser'ın −x tarafında, 0.6 × 0.6 m kare kesitli,
  **yatayla 60° eğimli** bir boru; riser'dan dışarı doğru yükselir. Ekseni riser duvarını
  z = 4.769'da keser; riser ekseninden başlar (içteki kısmı birleşimde erir), duvardan eksen
  boyunca 1.0 m dışarı çıkar. Uç yüzünün merkezi (−8.256, 2.64, 5.635). Beslemenin üstünde
  3.0 m, altında 4.5 m riser var.
- Eski yarıklı düzende (Eylül – 16 Kasım 2026) dirsek 95° (90° + kanalın 5° eğimi), riser ekseni
  x = −6.843, y = 1.73, z 0.885 … 8.385, oluk duvarı z = 5.385'te kesiyordu; aşağıdaki mesh ve CFD
  sonucu o düzene aittir.
  Yatay bir stub farini riser duvarına şerit hâlinde döker. İki yönlü DPM'i ıraksatan da ince
  prizma hücrelerindeki bu duvar şeridiydi (T2, 28 Eylül). Eğimli olukla farin gaz akımına
  düşerek girer, enjeksiyon hızı da oluktaki serbest düşmeden türetilebilir. 60°, ham farinin
  40–45°'lik şev açısının üstünde; açı ve kesit için tesis kaynağı yok (kullanıcı kararı,
  29 Eylül 2026).

Boylar neden böyle: beslemeden siklon gövdesine yol ≈ 3.0 (riser) + 3.4 (90° dirsek) + 1.5 (geçiş)
+ 3.0 (kanal) ≈ 10.9 m, ~0.9 s (eski 95°'lik dirsekle 11.1 m). 90 µm'lik farinin ısıl zaman sabiti ~0.02 s, 200 µm'lik ~0.08 s,
yani farinin tamamına yakını siklona varmadan gazla dengeye gelebilir; sonuç yapay bir kısalığa
bağlı değil. Besleme altındaki 4.5 m (~2 D) gazın beslemeye gelişmiş varması, geri düşen iri
farinin de gaz girişinden hemen çıkmaması için. Önceki 2.5 m ince riser'ın 2 D_h'siydi; bu
riser'da yalnız 1.15 D ediyordu.

Riser gerçekte C2'nin çıkışından başlar ve çok daha uzundur; bu domen onun yalnız üst ucunu,
beslemeden C1'e kadarını temsil eder. Gaz tabanda düzgün profille girer.

Mesh (29 Eylül 2026, eski yarıklı geometri; volütlü domen henüz mesh'lenmedi): C1 seviye-0 tarifi. Ansys Meshing tet 0.15 m, 5 prizma
katmanı, ilk 5 mm, büyüme 1.2 → Fluent poly + `improve-quality` → **191,208 poly hücre**, min
orthogonal quality **0.313**, hücre hacmi toplamı 249.68 m³ (geometri 250.23).
(Eski geometride — yatay stub, besleme altı 2.5 m — 184,519 hücre ve min OQ 0.209'du.)

Gaz-yalnız sonuç (eski yarıklı geometri, 17.9 kg/s, URANS SST-CC, 603 K): C1 statik ΔP **500.8 Pa**, doğrulanmış 503.8'e göre
−%0.6. Riser'daki düşüş 64.3 Pa; bunun ~59 Pa'sı 8.3 → 16.5 m/s hızlanma. Farinli durum CFD ile
değil analitik olarak hesaplandı (DDPM terk edildi; bkz. [cyclone_C1.md](cyclone_C1.md), "Yüklü
Durum"). Riser'ın yüklü ΔP'si 190 Pa.

## Boundary Faces

- Riser tabanı (z = 0.269, daire 3.70 m², yeşil): gaz girişi — Fluent'te `inlet_gas`, mass-flow-inlet.
- Oluk ucu (merkez (−8.256, 2.64, 5.635), normali oluk ekseni boyunca, 0.36 m², mor): `meal_feed` —
  gaz için duvar. DPM enjeksiyon yüzeyi olarak kullanılmadı: farin oluğun kapalı ucundaki durgun
  gazda asılı kalıyor. Oluk geometride beslemenin yerini ve yüksekliğini belirliyor.
- Diğer yüzler duvar.

## Derived Properties

Ekipman hacmi ve duvar alanı Geometrik Ölçüler'deki tabloda (hat başına).
CFD domenindeki riser hacmi (volütlü C1): dirsek 12.62 m³ (90°) + düz riser 27.76 m³ + geçiş 4.763 m³
(loft, makro log'u) + oluk 0.370 m³ ≈ 45.5 m³. C1 + riser domeni **265.10 m³** (riser'sız C1
219.59 m³). Eski yarıklı domen 250.2 m³ idi (95°'lik dirsek 13.32 m³, geçiş ~4.2 m³); yatay stub ve
2.5 m'lik besleme altıyla 242.65 m³.
