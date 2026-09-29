# Riser R1

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C2 → C1 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

Efektif iç çap: 3.07 m — HFC2500 (yayınlanmış)
Boy: TBD — Hiçbir kaynakta yayınlanmamış
Şekil: TBD — FLS makalesinin metni ile denklemleri çelişiyor (SOURCES.md, "Açık belirsizlikler")
Dirsek geometrisi: TBD — `LayoutParams` alanı tanımlı, değeri yok

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
ölçtüğü riser hızları 7.5–9.3 m/s. Tesisteki gibi riser ve dirsek yuvarlak; siklona doğrulanmış
0.86 × 2.16 m'lik dikdörtgen kanaldan girilir, arada 1.5 m'lik bir yuvarlak→dikdörtgen geçiş var.
Önceki sürümler (28 Eylül) kanal kesitini aşağıya kadar sürdürüyordu ve ince kalıyordu. Kare
siklon girişi elendi: aynı alanda 1.36 m'lik kenar vorteks bulucuya çarpar (halka 0.88 m).

Düzen (C1 koordinatları, siklon ekseni z, toz çıkışı z = 0):
- Geçiş: kanal ekseni boyunca 1.5 m; (−4.483, 1.73, 10.547) merkezli daireden kanalın uç
  yüzüne (merkez (−2.989, 1.73, 10.416)) loft. y'de yarım açı 24°.
- Dirsek: daire, (−4.672, y, 8.385)'ten geçen y'ye paralel eksen etrafında 95° (90° + kanalın
  5° eğimi), düz yukarıdan kanal eksenine döner; merkez çizgisi yarıçapı 2.171 m (1.0 D).
  Tepesi z = 11.64 m. Dirsek (1.5 D → 1.0 D) ve geçiş (2.0 → 1.5 m) riser siklona 1.7 m
  yaklaşsın diye kısaltıldı (kullanıcı kararı, 29 Eylül 2026).
- Düz riser: eksen x = −6.843, y = 1.73; z 0.885 … 8.385 (7.5 m).
- Farin besleme oluğu ("distribution box"): riser'ın −x tarafında, 0.6 × 0.6 m kare kesitli,
  **yatayla 60° eğimli** bir boru; riser'dan dışarı doğru yükselir. Ekseni riser duvarını
  z = 5.385'te keser; riser ekseninde z = 3.505'ten başlar (içteki kısmı birleşimde erir),
  duvardan eksen boyunca 1.0 m dışarı çıkar. Uç yüzünün merkezi (−8.428, 1.73, 6.251).
  Duvardaki açıklık z ≈ 4.71 … 5.99. Beslemenin üstünde 3.0 m, altında 4.5 m riser var.
  Yatay bir stub farini riser duvarına şerit hâlinde döker. İki yönlü DPM'i ıraksatan da ince
  prizma hücrelerindeki bu duvar şeridiydi (T2, 28 Eylül). Eğimli olukla farin gaz akımına
  düşerek girer, enjeksiyon hızı da oluktaki serbest düşmeden türetilebilir. 60°, ham farinin
  40–45°'lik şev açısının üstünde; açı ve kesit için tesis kaynağı yok (kullanıcı kararı,
  29 Eylül 2026).

Boylar neden böyle: beslemeden siklon gövdesine yol ≈ 3.0 (riser) + 3.6 (dirsek) + 1.5 (geçiş)
+ 3.0 (kanal) ≈ 11.1 m, ~0.9 s. 90 µm'lik farinin ısıl zaman sabiti ~0.02 s, 200 µm'lik ~0.08 s,
yani farinin tamamına yakını siklona varmadan gazla dengeye gelebilir; sonuç yapay bir kısalığa
bağlı değil. Besleme altındaki 4.5 m (~2 D) gazın beslemeye gelişmiş varması, geri düşen iri
farinin de gaz girişinden hemen çıkmaması için. Önceki 2.5 m ince riser'ın 2 D_h'siydi; bu
riser'da yalnız 1.15 D ediyordu.

Riser gerçekte C2'nin çıkışından başlar ve çok daha uzundur; bu domen onun yalnız üst ucunu,
beslemeden C1'e kadarını temsil eder. Gaz tabanda düzgün profille girer.

Mesh (29 Eylül 2026, **eski geometri**: yatay stub, besleme altı 2.5 m; oluk ve uzun riser
geldiği için yeniden kurulacak): C1 seviye-0 tarifi (Ansys
Meshing tet 0.15 m, 5 prizma katmanı, ilk 5 mm, büyüme 1.2) → 481,212 tet/prizma → Fluent poly
+ `improve-quality` → **184,519 poly hücre**, min orthogonal quality **0.209** (doğrulanmış C1
seviye-0: 0.22), max aspect ratio 25, hücre hacmi toplamı 242.13 m³ (geometri 242.65). En kötü
hücre, riser değil, gövdedeki giriş açıklığının çatı altındaki ucu.

## Boundary Faces

- Riser tabanı (z = 0.885, daire 3.70 m², yeşil): gaz girişi — Fluent'te `inlet_gas`, mass-flow-inlet.
- Oluk ucu (merkez (−8.428, 1.73, 6.251), normali oluk ekseni boyunca, 0.36 m², mor): `meal_feed` —
  gaz için duvar, DPM için enjeksiyon yüzeyi.
- Diğer yüzler duvar.

## Derived Properties

Ekipman hacmi: — (tesis riser'ının boyu yayınlanmamış)
CFD domenindeki riser hacmi: dirsek 13.32 m³ + düz riser 27.76 m³ + geçiş ~4.2 m³ (loft, kesin
değer makro log'unda) + oluk 0.370 m³ ≈ 45.6 m³ (C1 + riser domeni, kaz boyunlu çıkışla ≈ 250.2 m³;
yatay stub ve 2.5 m'lik besleme altıyla 242.65 m³ idi)
