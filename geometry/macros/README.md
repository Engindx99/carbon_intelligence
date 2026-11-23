# SolidWorks makroları

`geometry/` paketi `c99b93a` ile silindiğinden CFD katılarını üreten bir araç kalmamıştı.
Bu dizin onun yerini alır: bileşen dokümanlarındaki ölçülerden SolidWorks içinde
akışkan hacmini kuran, kendini doğrulayan ve dışa aktaran makrolar.

| Dosya | Ne yapar |
|---|---|
| `cyclone.bas` | Tek bir siklonun CFD akışkan hacmi → STEP (AP214) + STL + SLDPRT |
| `calciner.bas` | ILC kalsinatörün CFD akışkan hacmi: boğaz + koni + gövde, kaz boynu (üç düz mitreli parça: 45° yukarı, yatay, 45° aşağı; sonra düşey kanal ve dikeyden 60° ayrılan Y kolları, C5'in giriş eksenindeki dikey çıkış yüzlerine yatay uçlar), iki farin borusu, teğetsel tersiyer hava kanalı, iki yakıt borusu; sınır yüzleri boyalı → STEP (AP214) + STL + SLDPRT. Ölçüler ve kaynakları: [`calciner.md`](../calciner/calciner.md) |
| `kiln.bas` | Döner fırın tüpünün CFD akışkan hacmi: yayınlanmış D 4.8 m × L 74 m'lik düz silindir (eksen z, arka uç z = 0, ocak ucu z = L); eğim katıya işlenmez, tabloda kalır; `kiln_back` / `kiln_hood` uç yüzleri boyalı → STEP (AP214) + STL + SLDPRT, log `kiln_build.log`. Ölçüler: [`kiln.md`](../kiln/kiln.md) |
| `kiln_wall.bas` | **CFD için değil**: fırın duvarı, twin'in modellediği hâliyle ([`physics/shell.py`](../../physics/shell.py), r_inner = D/2): tek tuğla borusu (en içte, sıcak yüzü D = 4.8 m akış çapı) ve tek sac borusu (Ø5.30 m), ikisi de tüm 74 m boyunca; coating yok (şimdilik). Bölgeler (geçiş z 0..transition_L alümina, yanma magnezya-spinel) yalnızca tuğla cinsiyle ayrılır: model bölmesi, katıda birleşim yok. Tuğlalar ISO 5417 radyal kamalar (A 103, L 198 mm; halkada 160): fırının iki uç halkası tuğla tuğla kurulur (2 × 160 gövde, `brick_ring_<k>_<iii>`; kopyalar `Body2.Copy` + `ApplyTransform` + `CreateFeatureFromBody3`, yeri centroid'den doğrulanır). Gövde adları, hacim ve sınırlar doğrulanır → SLDPRT + STEP (AP214), log `kiln_wall_build.log`. Paftası `drawings.bas` → `kiln` (fırının tek paftası: gaz çapı + duvar, `geometry/drawings/kiln/`; CFD katısının z0 başlangıcı kesitte işaretli) (yan görünüş, eksen boyunca kesit A-A, uç görünüş C 1:50, hood ucu detay B 1:10, tuğla halkası detay D 1:5; katman lejantı shell.py'den üretilir) |
| `kiln_rotax.bas` | **CFD için değil**: fırının mekanik parçaları, FLS ROTAX-2 referanslı, basit zarflar (kullanıcı, 22 Kas 2026: fırın ölçüleri değişmez, yalnızca parçalar eklenir): iki tayr (teğet askı konsollarıyla) ve altlarındaki kalın sac kuşağı, iki makaralı iki istasyon (mil, yatak, şase, beton ayak), giriş istasyonunda sürtünmeli tahrik (2 dişli kutusu + 2 ana motor) ve hidrolik eksenel itme makarası, giriş/çıkış sızdırmazlığı, çıkış toz bacaları, burun halkası fanı, 3 sac soğutma fanı, yürüme köprüsü. Gövdelerin hepsi (ölçü, yer, hacim, sınır) [`plant_geometry.kiln_rotax()`](../plant_geometry.py)'dan üretilen `KRX_` dizgilerinden gelir; makro modeler gövdeleri kurar, adlandırır, boyar, hacim ve kesin sınırlarını doğrular → SLDPRT + STEP, log `kiln_rotax_build.log`. Çerçeve `kiln_wall.bas` ile aynı (eksen z, y yukarı); eğim kurulmaz, ayaklar eğimli zemine iner. `assembly` yordamı fırının tamamını kurar: `kiln_wall.SLDPRT` + `kiln_rotax.SLDPRT` aynı orijinde, sabit → `kiln_assembly.SLDASM` (log `kiln_assembly_build.log`) |
| `cooler.bas` | Izgaralı soğutucunun CFD akışkan hacmi ([`cooler.md`](../cooler/cooler.md)): 29.9 × 4 × 3 m kutu, tek gövde; taban FLS'nin 10 segmentine bölünür (`grate_air_1..10`), tavan hood açıklığının sonunda bir kez bölünür (`hood_opening`, x 0..5.98 m); bölme çizgileri `IModelDoc2.InsertSplitLineProject` ile (yöntem `FeatureManager`'da değil `ModelDoc2`'dedir). Vent çıkışı kaynak olmadığı için yapılmaz → STEP (AP214) + STL + SLDPRT, log `cooler_build.log` |
| `c1_twin.bas` | Bir hattın ikiz C1'i ve ortak R1'i tek akışkan hacmi olarak: doğrulanmış `C1_riser.SLDPRT` (salt okunur, sonda değişmediği kontrol edilir) 90° döndürülüp iki kez yerleştirilir, ikincisi birincinin aynası; giriş kanalları birbirine bakar, R1 simetri düzleminde önde, kısa düz kök + her kola bir loft (pantolon Y). Aralık ve Y `plant_geometry.c1_twin`'den türetilir (Estimated) → SLDPRT + STEP, log `geometry/output/2500/c1_twin_build.log`. Önce `cyclone.bas` ile `C1_riser` kurulmalı |
| `kiln_inlet_chamber.bas` | Fırın giriş odasının CFD akışkan hacmi ([`kiln_inlet_chamber.md`](../kiln/kiln_inlet_chamber.md)): yerleşimin 6.8 m karesi, düz tavan; x-z profili bir üçgen (taban fırın ağzının alt dudağından karşı üst köşeye tek rampa, +x duvarı, tavan) iki yöne ekstrüde, tavana boğaz diski (D 3.130 m, 1 mm) eklenir; +x duvarında fırın ağzı dairesi `InsertSplitLineProject` ile bölünür. Sınır yüzleri: `kiln_gas_inlet` (kırmızı), `throat_outlet` (mavi), geri kalanı duvar (gri). Farin girişi yapılmaz (çözücüde enjekte edilir) → STEP (AP214) + STL + SLDPRT, log `kiln_inlet_chamber_build.log` |
| `id_fan.bas` | ID fanın CFD akışkan hacmi ([`id_fan.md`](../fan/id_fan.md)), **üç ayrı gövde** (MRF arayüzleri için): `rotor` (dönen bölge: düz göbek y = 0, gözden uca konik örtü, r_MRF'ye kadar halka; z adet tek yaylı plaka kanat göbekten örtüye kesilir), `volute` (log spirali r = R3 e^(Kθ), büyümesi çıkış hızından; sabit genişlik B = 3·b2, yuvarlak dil burnu, 45° yukarı düz çıkış, evasé yok; r_MRF delik), `inlet` (ön yan sacın dışında giriş kutusu, yüzü +x'e bakar, + sacdan göze koni). Eksen y, çark +x'ten +z'ye döner. Sınır yüzleri: `fan_inlet` (kırmızı), `fan_outlet` (mavi), `interface_eye` (sarı) ve `interface_rim` (yeşil) her iki tarafta, `blade` (turuncu), duvar (gri). Kaçak boşlukları ve göbek arkası/örtü dışı boşluklar yok; damper/IGV yok → STEP (AP214) + STL + SLDPRT, log `id_fan_build.log` |
| `kiln_burner.bas` | Fırın brülörünün (JETFLEX 2.0, sabit memeler) CFD akış hacmi ([`kiln_burner.md`](../kiln/kiln_burner.md); kullanıcı, 22 Kas 2026: yalnız brülör kanalları, ileride alev alanına takılmak üzere), **üç ayrı gövde**: `coal` (merkezin biraz üstünde düz katı yakıt borusu), `axial` (ön plakanın arkasında halka plenum + plakadan geçen 20 dikdörtgen yarık, uzun kenarı teğetten 13°), `swirl` (halka plenum + eksenden 30° eğik, +θ yönüne 40 kare delik). Uç düzlemi z = 0, akış +z (fırına). Uç düzeni Fuller broşürünün kesiti (görsel oranları); ölçek: yarıklar twin'in eksenel havasını kılavuzun 285 mbar'ında geçirsin; kömür borusu hızı (30 m/s) bir kontrol. Gövdeler `plant_geometry.kiln_burner()`'den üretilen `KBR_` dizgileri (silindir, halka, döndürülmüş kutu, eğik prizma + dilim kesişimi), kanal başına birleştirilir; hacim, sınır ve yüzler doğrulanır. Sınır yüzleri: `coal_inlet`/`axial_inlet`/`swirl_inlet` (kırmızı tonları), `coal_outlet`/`axial_outlet` (20 yüz)/`swirl_outlet` (40 yüz) (mavi tonları), duvar (gri). Lans, ateşleyici, alev tarayıcı akış yolu değil → STEP (AP214) + STL + SLDPRT + önizleme jpg, log `kiln_burner_build.log` |
| `kiln_burner_body.bas` | **CFD için değil**: brülörün tamamı, basit zarflar (kullanıcı, 22 Kas 2026): refrakter uç halkası ve boru, içinde çelik brülör borusu (deliği kanal katısının eksenel plenumu), bağlantı flanşı ve önündeki taşıyıcı levha (boruyu saran halka, kirişe boyun, ayak levhası), iki ucu flanşlı hava bağlantı kafası, -x yanında hava dirseği (kafadan dik çıkan boyun, tek pürüzsüz uzun yarıçaplı 90° kıvrımla (R = 1,5 × dış çap, ASME B16.9 LR) yukarı, flanş doğrudan kıvrımın ucunda; kıvrım geçici bir parçada halka kesitin döndürülmesiyle kurulup taşınır, `tor`) ve flanşlı ikinci giriş, genleşme körüğü, arkada kömür girişi borusu (flanşa 1,0 D kala uzun yarıçaplı kıvrımla 12° yukarı eğik; soğutma havası nozulu boruya dik, dirsek gibi -x yönünde, 30° yukarı) ve flanşı, sırt sırta iki U profil kiriş (her birinin açık yüzünde flanşları birleştiren eğik levha, uçları flanş yüzlerinde kırpılı: `cut_`; arka uçta her iki açık yanda dikdörtgen levha; alın levhası, pimler) ve arka askı; uçtan genleşme körüğünün arka duvarından geçip 0,8 D gerisine uzanan yakıt lansı, alev tarayıcısı ve ateşleyici boruları (broşür s. 5 uç, s. 4 "expansion joint for guiding fuel injection pipes", s. 3 yan görünüş; kanallara değmez, CFD etkisi yok) çelik borunun içinde eş merkezli çekirdek ve swirl boruları (yarıçapları kanal katısının plenumları, oralarda birleşir) ve ortak yakıt borusu (CFD kömür borusuna uzanır), kafada bölme: ön oda dirsek = eksenel hava, arka oda 2. giriş = swirl havası (model varsayımı; broşür s. 4 "iki hava sistemi", "straight, uninterrupted pipe"); paftada kafa ön odasından kesit B-B 1:10 (23 Kas 2026: arka bölüm broşür kapağının yakın görünüşü ve alternatif yakıtlı yan görünüşü gibi; borular, kafa ve körük içi boş, akış yolu flanşlardan çelik boruya kadar açık: `tube` ve gruptan sonra kesilen `void_` gövdeleri). Boylar Fuller broşürünün yan görünüşünden uç çapına oran, kapaktaki ayrıntılar schematic; `kiln_burner()`'ın D_uç'u ile ölçeklenir (`plant_geometry.kiln_burner_body()`, `KBB_` dizgileri: parça grupları birleştirilip bir gövde olur, 42 parça → 12 gövde); kurucu `kiln_rotax.bas`'ınki, gruplar ve yönlendirilmiş kutu eklenmiş → SLDPRT + STEP + arka yakın görünüş `kiln_burner_body_rear.jpg`, log `kiln_burner_body_build.log`. `assembly` yordamı `kiln_burner.SLDPRT` (kanallar) + bu parça → `kiln_burner_assembly.SLDASM` + jpg |
| `kiln_flame.bas` | Alev bölgesinin CFD hacmi (kullanıcı, 23 Kas 2026: fırın çıkışı + brülör entegrasyonu; CFD koşuları sonra): hood (çıkış contasının dış yarıçapı + pay; derinlik soğutucunun iki hood segmenti; tesis yatayında, fırın çerçevesine 3 % ile döndürülmüş), fırın deliği yanma bölgesi boyunca (twin'in `burning_L`'si, z 30,83 m'den), tabanda soğutucunun iki segment ağzı, tavanda tersiyer hava ağzı, `kiln_burner.SLDPRT`'nin üç kanalı yerleştirilmiş (uç fırının 0,25 m içinde, eksen üzerinde, eksene paralel: literatür), brülörün kendisi (uç halkası, refrakter) kesilmiş (`plant_geometry.kiln_flame()`, `KFL_` dizgileri). Sınırlar: `secondary_air_in`, `tertiary_supply_in`, `tertiary_air_out`, `kiln_gas_out`, `coal_in`, `axial_in`, `swirl_in`, duvar. Klinker yatağı yok (`kiln.bas` gibi) → SLDPRT + STEP + jpg, log `kiln_flame_build.log`. `assembly` yordamı `kiln_wall` + `kiln_rotax` + brülör (kanallar ve gövde, dönüşümle) + bu hacim → `kiln_outlet_assembly.SLDASM` + jpg; paftası `drawings.kiln_flame` |
| `drawings.bas` | **CFD için değil**: ekipmanların iç (akışkan) geometrisinin ISO teknik resmi (A1, 1. açı, ISO 5457 çerçeve, ISO 7200 antet), CFD katısından gerçek izdüşüm, kesit ve detay görünüşleri; ölçüler katının kenarlarından alınır, okunur ve kaynakla karşılaştırılır; Estimated ölçüler " E" ekli; parametre tablosu kaynak ve durumla → `geometry/drawings/<ad>/<ad>.pdf` + `.dxf`, log `geometry/output/2500/drawings_<ad>_build.log`. Önce katı kurulmalı (C1 için `cyclone.bas`, C1 durumunda `RISER_ON = False`; ikiz için `c1_twin.bas`; C4 ve C5 için `cyclone.bas`, `VOLUTE_ON`; kalsinatör için `calciner.bas`; fırın için `kiln.bas`; soğutucu için `cooler.bas`; fırın giriş odası için `kiln_inlet_chamber.bas`; ID fan için `id_fan.bas`; brülör için `kiln_burner.bas`, brülörün tamamı için `kiln_burner_body.bas`; alev bölgesi için `kiln_flame.bas`). Çalıştırılacak makro: `main` (C1), `c1_twin` (ikiz C1 + R1), `c4` (C2, C3 ve C4: aynı geometri), `c5`, `calciner` (vessel, boğaz, kaz boynu, tersiyer hava, farin ve yakıt boruları), `kiln` (fırının tek paftası, `kiln_wall.SLDPRT`'den: gaz çapı + tuğla/sac duvar; yan görünüş, kesit A-A 1:200, uç görünüş C 1:50, detay B 1:10, detay D 1:5; CFD katısı `kiln.SLDPRT` z0'dan başlar, kesitte işaretli), `kiln_rotax` (ROTAX-2 parçaları, `kiln_rotax.SLDPRT`'den: yan görünüş ve plan 1:200, giriş istasyonundan kesit A-A 1:50, tayr detayı B 1:25; fırın sacı phantom; tayr açıklığı, tayr genişliği, tayr altı kuşak boyu, tayr çapı ve kalınlığı, makara çapı ölçülü, schematic değerler yalnızca tabloda), `kiln_burner_body` (brülörün tamamı, zarflar: yan görünüş ve plan 1:20, arkadan uç görünüşü 1:10; toplam boy (planda, uçtan kömür flanşının arka yüz merkezine), refrakter boyu ve çapı, uç halkası boyu, kafa boyu, flanş çapı), `kiln_burner` (JETFLEX 2.0 kanalları, `kiln_burner.SLDPRT`'den: fırından bakışla uç görünüşü 1:2.5, eksen boyunca kesit A-A ve dış yan görünüş 1:5, yarık/delik detayı B 1:1; kömür borusu çapı, plenum dış çapları, kömür borusu boyu, plenum boyu, ön plaka), `cooler` (yan, plan, alttan taban görünüşü 1:100 + uç görünüşü 1:50; L, w, H, segment, hood)., `kiln_inlet_chamber` (1:50, birinci açı: yan görünüş, altında plan, solunda +x duvarından görünüş; plan kenarı, duvar yüksekliği, boğaz D, ağız D, rampa açısı), `id_fan` (1:50 önden/plan/+x görünüşü + yalnız rotor gövdesi 1:20 iki görünüş, `IView.Bodies` ile; B, çıkış yüksekliği, kutu yüksekliği/derinliği, D1, D2, b2; b1 yalnız tabloda, göz dairesi dış görünüşlerde gizli) `kiln_flame` (alev bölgesi hacmi: yan görünüş, eksenden kesit A-A ve plan 1:200, brülör tarafından hood 1:100; hood derinliği, segment boyu, fırın deliği çapı, uçtan gaz çıkışına boy, tersiyer ağzı çapı; hood W ve H schematic değerlere dayanır, yalnız tabloda) Envanter ve JSON: `python3 tools/gen_drawings.py` |
| `pid.bas` | **CFD için değil**: tesisin P&ID'si, twin'in modellediği hâliyle: dört A1 çizim sayfası (SLDDRW + PDF + DXF), ölçeksiz, ISO 10628 / ISA 5.1 sembolleri, ızgara hücrelerine yerleşim. Topoloji, etiket, hat ve enstrüman [`geometry/pid/pid.yaml`](../pid/pid.yaml)'dan; hat boyutu `plant_geometry.yaml`'dan; enstrüman twin'in kendi değişkenleri (kapsam: `tools/pid/scope.py`). Çalıştırılacak makro sayfa başına bir tane: `preheater` (PH), `calciner` (CA), `kiln` (KI), `cooler` (CO). Önce `python3 tools/gen_geometry.py`. Çıktı `geometry/drawings/pid/pid_<SH>.pdf` + `.dxf` + `.stamp` (paftanın çizildiği kaynağın parmak izi, `PID_<SH>_HASH`; kayıtlar veya makro kodu değişince `tests/test_pid.py` makro yeniden çalıştırılana kadar kırmızı kalır), log `geometry/output/2500/pid_<SH>_build.log`. Bkz. [`pid.md`](../pid/pid.md) |
| `plant_topology_2d.bas` | **CFD için değil**: tesis topolojisinin gerçek ölçekli 2D çizimi: SolidWorks çizim sayfası (SLDDRW, A1, 1:200) ve PDF. İki hatlı ön ısıtıcı (12 siklon), ILC kalsinatör, fırın, soğutucu ve başlık; gaz, farin ve hava yolları renkli katmanlarda, ana kanallar gerçek çapında, akış okları, lejant ve antet. Bkz. [`plant_topology.md`](../plant_topology.md) |

`calciner.bas`, `kiln.bas` ve `cooler.bas` aynı yoldan çalıştırılır (makro adı ör. `calciner.swp`) ve `cyclone.bas`'ın doğrulanmış
yardımcılarını (çizim ekseni kalibrasyonu, boyama, dışa aktarma) kendi içinde kopya olarak taşır; makrolar birbirinden bağımsızdır.

**Ölçüler makroda yazılmaz.** (`pid.bas`'ın topolojisi ve enstrümanları da: `geometry/pid/pid.yaml`'dan üretilen `PID_<SH>_n` Const'ları.) Her makronun başında `' BEGIN GENERATED (tools/gen_geometry.py)` ile `' END GENERATED` arasında bir Const bloğu var; `tools/gen_geometry.py` onu `geometry/plant_geometry.yaml`'dan (tesisin tek ölçü kaynağı) yazar. Bloğu elle düzenleme: ölçüyü yaml'da değiştir, `python3 tools/gen_geometry.py` çalıştır, makroyu SolidWorks'e yeniden import et. `python3 tools/gen_geometry.py --check` bayat bir blok bulursa hata verir (`tests/test_geometry_single_source.py` de).

Kaynak `.bas` olarak tutulur: VBA modülünün düz metin biçimi, `git diff` ile okunabilir.
SolidWorks'ün ürettiği `.swp` ikili bir dosyadır, depoya girmez.

## Çalıştırma

1. SolidWorks → **Tools → Macro → New**, bir `.swp` adı ver (ör. `cyclone.swp`).
2. Açılan VBA düzenleyicisinde **File → Import File…** → `cyclone.bas`.
3. Varsayılan boş modülü (`Module1`) sil.
4. **Run** (F5) → `main`.

Makro `geometry/output/2500/` altına `C1.step`, `C1.stl` ve `C1.SLDPRT` yazar.
Bu dizin `.gitignore`'da.

Yeni bir parça açmaya gerek yok; makro kendi parçasını oluşturur.

## Başka bir siklon üretmek

Dosyanın başında `CYCLONE_NAME`'i seç: `"C1"`, `"C4"` ya da `"C5"`. Her siklonun ölçüleri üretilen
bloktadır (`C1_*`, `C4_*`, `C5_*`); `SelectCyclone` onları seçer ve kendine özgü modelleme seçimlerinin gerekçelerini taşır; geri kalan
her koordinat bunlardan hesaplanır. Bütün hatların bütün kademeleri
[`geometry/catalog.md`](../catalog.md) içinde:
`D, barrel_h, cone_h, vortex_len, vortex_D, dust_D, inlet_w, inlet_h`.

- **C1:** gövdeden geçen teğetsel yarık giriş (2.16 m yükseklik, katalogdan sapma), 5° eğim,
  riser ve 180° kaz boynu çıkış.
- **C4 (C2 ve C3 de aynı):** katalog girişi 1.27 m genişliğiyle gövde ile vorteks bulucu arasına
  sığmıyor, bu yüzden giriş basit bir **volütle** kuruluyor (`VOLUTE_ON`). Volüt, çatıdan aşağı
  ekstrüde edilen düz bir kanal ve 180°'lik bir Arşimet sarmalı. Giriş 3.40 × 2.912 m: gövde
  katalog girişinin tesis debisindeki alanıyla. Gövde h = D = 6.30 m (katalog 3.46). Çıkış 90°
  dirsek (R 1.0 D_x) ve 1.0 D_x yatay bacak (`OUTLET_TURN_DEG = 90`), riser yok (kullanıcı
  kararları, 4 Ekim 2026). Daldırma 3.90 m (katalog 3.17): S/a 1.15, vorteks bulucu ağzı giriş
  tabanının 0.5 m altında (kullanıcı kararı, 5 Ekim 2026).
- **C5 (hat başına bir tane):** C4'ün bütün ölçüleri × 6.50 / 6.30 = 1.0317. CFD'si çözülen
  C4'le geometrik benzer; C4'ün Euler sayısı ve volüt girdabı ölçeklemesiz taşınır, C5'e ayrı
  CFD gerekmez (kullanıcı kararı, 12 Ekim 2026). Çıkış C4'teki gibi 90° dirsek, R4'e gider.

Yeni bir siklon eklemek için `SelectCyclone`'a bir `Case` ekle.

## Koordinat sistemi

Eksen **z**, toz çıkışı **z = 0**, gaz **+x** yönünde girer — `cyclone_C2.md`'nin kurduğu
kural. Gaz y ∈ [R − inlet_w, R] aralığından girdiği için girdap **yukarıdan bakıldığında
saat yönündedir**. (Silinen `geometry/components.py` docstring'i "anticlockwise" diyordu;
o yazı yanlıştı, kurduğu geometri buydu.)

## Modelleme kararları

Bunlar tesis ölçüsü değil, kaynakları yok; makronun parametre bloğunda ve
`cyclone_C1.md`'de belgelidir.

**`INLET_ROOF_CLEARANCE = 0.05 m`** — Kanal siklona doğru 5° iniyor, yani gövdedeki
açıklığın **üst** kenarında en yüksek noktasında. Üst kenarı doğrudan çatıya dayamak,
kanalı gövdenin izdüşümü üzerinde çatının üstüne çıkarır ve çatı plakasının üzerinde
sivrilerek biten, çıkmaz bir akışkan kaması bırakır. Bu boşluk çatıyı düz, açıklığı da
gövdedeki temiz bir delik olarak tutar. Sıfır olamaz: sıfırda kanal tavanı, siklon çatısı
ve gövde tek bir dejenere noktada buluşur.

**`INLET_TONGUE = 0.05 m`** — Kanal, gövdeye teğet düzlemine varmadan **x = −√(t(2R−t))**'de
biter; uç kapağının dışarıda kalan `t` genişliğindeki şeridi kör bir yüz olarak ayakta kalır.
Gerçek makinedeki cut-water'ın karşılığı.

Kanalın dış duvarı (y = R düzlemi) ile gövde (r = R silindiri) x = 0'da **teğettir**. Oraya
kadar sürdürülürse birleşim sıfır açılı bir kenara kapanır ve akışkan o çizgi boyunca sıfıra
iner. Bu, modelde **mesh'in ulaşamadığı tek kusur**: dihedral açı ölçekten bağımsızdır, hücreyi
yarıya indirince aynı sliver yarı boyunda geri gelir — ölçüldü, en-boy oranı incelttikçe 79'dan
175'e çıktı. Diğer bütün ince yapılar birer **genişliktir** ve yerel yüzey boyutlandırmasıyla
kapanır; açı kapanmaz.

Erken bitince teğetlik x = −xTrim ile 0 arasında **katı kabuğun içinde** kalır, akışkan
sınırlamaz, mesh'lenmez. Kesilen akışkan 0.0166 m³ (domenin %0.011'i) ve katalog kesiti
0.86 × 2.16 ile 16.5 m/s giriş hızı **aynen korunur**.

Dil yüzü bir çıkıntı: 0.02 m yüzey boyutuyla 2.5, 0.0125 m ile 4 eleman. Yüzün normali x ekseni
boyunca olduğu için `TagBoundaryFaces` onu giriş yüzü sanmaz (fark |cos5°−1| = 0.0038,
`DIR_TOL` = 1e-6).

**`INLET_TANGENT_RELIEF = 0.0 m`** — Aynı kusura eski, daha pahalı çözüm: dış duvarı kanal
boyunca içeri çeker. Açıyı 0'dan 9.56°'ye açar ama kamanın **ucunu yok etmez**, yalnızca
x = −0.359'a taşır; üstelik kesit götürür (0.86 → 0.83 m, giriş hızı 17.1 m/s). Dil varken
gereksiz, 0'da tutulur — makro ikisinin birlikte kullanılmasını reddeder.

**Kanal boyu `L_INLET = 3.0 m`** — Gövdenin teğet düzleminden (x = 0) dışarı, kanal ekseni
boyunca, **kesit ağırlık merkezinden** ölçülür. Yüz eğik olduğu için başka bir datum
seçilirse boy ±0.22 m belirsiz kalır; ağırlık merkezi datumu ayrıca hacim formülünü
tam yapar. Bu bir tesis ölçüsü olduğundan `twin_cfg.yaml`'daki
`inlet_extension_over_D` C1 için kullanılmaz.

**Çıkış kaz boynu** — Çıkış borusu çatının üstünde `OUTLET_EXT_OVER_VORTEX_D = 1.25` (3.0 m; 29 Eylül'de kaz boynu tesisteki gibi çatıya yakın dursun diye 2.5'ten yarıya indirildi; oran artık siklon başına `SelectCyclone`'da, C4 / C5'te 1.70, 14 Ekim 2026)
düz yükselir, sonra **180°'lik bir dirsekle** (merkez çizgisi yarıçapı `ELBOW_R_OVER_VORTEX_D = 1.5`
→ 3.6 m, eksen (+3.6, y, 14.44)) +x yönüne dönüp aşağı iner ve `OUTLET_DOWN_OVER_VORTEX_D` kadar (yükselişe eşit, 3.0 m; bacakları eşit
düz bir U) düz iner. `gas_outlet` bu borunun ucundaki, aşağı bakan yatay disktir (x = 7.2, z = 11.44). Bu yüz çatıyla aynı düzlemde ama x'te gövdenin dışında; etiketleme onu yüzün x alt sınırıyla (> R) ayırır.
C1 en üst siklon; tesiste gaz duct'ı böyle ters U biçiminde fana iner (kullanıcı kararı, 29 Eylül
2026). +x yönü riser'ın ters tarafı. 28 Eylül'e kadar çıkış 90° dirsek + −x'e 4.8 m yatay
kanaldı; doğrulanmış gaz-yalnız sonuçlar (200.94 m³'lük `C1.step`) o geometriye aittir.

Gerekçe ölçülmüş: düz borunun ucundaki çıkış yüzünde, girdap güçlenince (k-ω SST, 26 Eylül 2026)
alanın **%38'inde geri akış** vardı. Kütle dengesizliği, ΔP ve geri akış oranı aynı
18 iterasyonluk periyotla birlikte salınıyordu (korelasyon ~0.8). Girdap düz boruda çok yavaş
söndüğü için uzatma bunu makul bir boyda çözmez; dirsek girdabı ve ters akım çekirdeğini kırar.
Tesiste de gaz C1'den fana giden bir kanala döner. Dönüş yönü tek siklon için keyfi; kaynak
aşağı akış kanalını yerleştirmiyor. Yükseliş 2.5'te bırakıldı, böylece %38'i ölçen koşuya
göre değişen tek şey dirsek oldu.

Dirsek, borunun z = 14.44'teki kesit diskinin, aynı düzlemdeki y'ye paralel bir eksen etrafında
180° döndürülmesiyle kurulur (yarım torus) ve aynı düzleme geri iner; inen boru o düzlemden aşağı
extrude edilir. Hacmi Pappus'tan tamdır: A · π · R_b.
Dönüş yönü ölçülür, varsayılmaz: ters dönerse hacim ve kutunun tepesi söyler, diğer yön denenir.

Volüt modellenmez; farin borusu yoktur, toz çıkışı bir sınır yüzüdür.

**Riser ve farin beslemesi (`RISER_ON = True`, 28 Eylül 2026)** — Gaz artık giriş kanalının
ucundan değil, önündeki dikey bir **riser**'ın tabanından girer; farin riser'a duvarından giren
eğimli bir **besleme oluğundan** verilir (tesisteki "distribution box"). Gerekçe: farini kanal ucundan
542 K'de vermek hem iki yönlü DPM'i hem DDPM'i ıraksattı, 542 K de gaz–farin ısı alışverişinin
80/20 riser/siklon paylaşımı *varsayımıydı*. DTU'nun endüstriyel DDPM siklonu (Mirzaei 2023)
farini aynı nedenle riser'a verir; ısı alışverişi orada olur ve paylaşım artık bir sonuçtur.

* **Kesit** — tesisteki gibi **yuvarlak** riser ve dirsek. Yayınlanmış R1 (Ø3.07 m) ikiz C1'leri
  birlikte besler; C1'e alanının yarısı düşer: **Ø2.171 m, 3.70 m²** (`D_RISER_SRC`,
  `RISER_AREA_SHARE = 0.5`). 17.9 kg/s'de hız 8.7–10.6 m/s (DTU'nun riser'ı 7.5–9.3 m/s).
  Siklona yine doğrulanmış **0.86 × 2.16 m**'lik kanaldan girilir. Kare giriş elendi: 1.36 m'lik
  kare vorteks bulucuya çarpar, halka 0.88 m (kullanıcı kararları, 28–29 Eylül 2026).
* **Geçiş** — kanal ekseni boyunca `RISER_TRANS_LEN = 1.5 m`: G = (−4.483, 1.73, 10.547)'deki
  daireden kanalın uç yüzündeki dikdörtgene bir **loft** (y'de yarım açı 24°). İki profil de var
  olan düzlem yüzlerdir, geometriyle bulunur; eğik düzlemde çizim gerekmez. Loft hacminin
  kapalı formu yok, bu yüzden tek gevşek kontrol burada: hacim iki uç prizmanın arasında
  (2.79…5.55 m³) olmalı; ölçülen değer log'a yazılır ve oluk bunun üstüne ‰1 ile doğrulanır.
* **Dirsek** — daire, y'ye paralel bir eksen etrafında **90° + eğim = 95°** döndürülür (çıkış
  dirseğiyle aynı yapı); merkez çizgisi yarıçapı `RISER_BEND_R_OVER_D = 1.0` → 2.171 m, eksen
  (−4.672, y, 8.385). Son kesiti G'deki dairedir. Tepesi z = 11.64 m (gövdenin dışında).
  Hacim Pappus: π r² · R_b · (π/2 + 5°) = 13.32 m³. Dirsek 1.5 D'den, geçiş 2.0 m'den
  riser siklona 1.7 m yaklaşsın diye kısaltıldı (29 Eylül 2026); 3.0 m'lik kanal yayınlanmış ölçü, kalır.
* **Riser** — eksen x = −6.843, y = 1.73; z = 8.385'ten aşağı: beslemeye `RISER_ABOVE_FEED = 3.0 m`,
  besleme altında `RISER_BELOW_FEED = 4.5 m` (~2 D); taban **z = 0.885**. Hacim 27.76 m³. Beslemeden
  gövdeye yol ~11 m; 200 µm'lik farinin ısıl zaman sabiti ~0.08 s. Besleme altı 2.5 m idi, ama bu
  ince riser'ın 2 D_h'siydi, bu riser'da 1.15 D ediyordu (29 Eylül 2026).
* **Besleme oluğu** — 0.6 × 0.6 m kare kesit, yatayla `FEED_SLOPE_DEG = 60°`, riser'dan −x yönünde
  dışarı doğru yükselir; ekseni riser duvarını z = 5.385'te keser. Riser ekseninde z = 3.505'ten
  başlar (içteki kısmı birleşimde erir), duvardan eksen boyunca `FEED_DEPTH = 1.0 m` dışarı çıkar.
  Bu değer (H/2)·tan θ = 0.52'yi aşmalı, yoksa uç yüzün bir kenarı riser'ın içinde kalır.
  Kanal gibi yan görünüşü (x–z'de dönmüş bir dikdörtgen) y = 1.43 düzlemine çizilip y boyunca
  0.6 m extrude edilir. Uç yüzünün merkezi (−8.428, 1.73, 6.251). Hacim kapalı formda
  0.6·[0.6·L − segment/cos θ] = 0.370 m³, L = r/cos θ + 1.0 = 3.171 m (θ = 0'da düz stub'ın
  formülü). Yatay stub farini duvara şerit hâlinde döküyordu; iki yönlü DPM'i ıraksatan buydu
  (kullanıcı kararı, 29 Eylül 2026).
* Dirsek ve riser, loft onları birleştirene kadar **ikinci bir gövde** olarak durur; 7–8.
  aşamalar iki gövdenin toplam hacmi ve ortak kutusuyla kontrol edilir.

`RISER_ON = False` riser'sız, kaz boyunlu gaz-yalnız domeni kurar ve `C1.*` adıyla yazar (doğrulanmış
90° dirsekli domen değil; o, commit 1249eb9'daki makroda);
açıkken çıktı `C1_riser.*`. Riser açıkken domen **≈ 250.2 m³** (eşit bacaklı kaz boynuyla;
loft'a bağlı, log kesin değeri verir), riser'sız ≈ 204.8 m³. Kutu değişir: x min = −8.688 (oluk ucunun alt kenarı), x max = 8.4 (inen boru),
y max = 2.815 (yuvarlak kesit).

## Makro kendini nasıl doğrular

Hiçbir şey dışa aktarılmadan önce, her adım kapalı formdaki aritmetikle karşılaştırılır —
önceki bir çalıştırmayla değil. Herhangi biri düşerse makro durur, **hiçbir dosya yazmaz**
ve parçayı ekranda inceleme için bırakır.

* **Ön kontroller** — giriş yüzü gövdenin dışında mı, kanal toz çıkışının altına iniyor mu,
  vorteks bulucu duvarı sığıyor mu, kanalın iç duvarı vorteks bulucuya çarpıyor mu,
  açıklık çatının altında mı. Silinen `cyclone_layout()`'un reddettiği dördü artı eğimin
  getirdiği ikisi.
* **Adım başına hacim** — 6 adımın (riser açıkken 10) her birinin beklenen hacmi kapalı formda
  hesaplanır ve ‰1 toleransla karşılaştırılır. En sıkı olanı ilki: gövde + koni = **124.54 m³**,
  dokümanın fiziksel hesapta kullandığı sayı. 6. adımın sonunda domen **200.94 m³**, riser,
  dirseği, geçişi, oluğu ve kaz boynuyla **≈ 250.2 m³**. Loft'un hacmi yalnız bir aralıkla kontrol edilir
  (kapalı formu yok). Oluğun y yönü hacimle ayırt edilemez: ters yönde fark ~0.14 m³, yani ‰1'in
  altında. Bu yüzden uç yüzü bulunur ve y aralığı okunur; ters dönen riser dirseği aşağı gider
  ve kendi gövdesinin kutusuyla yakalanır.
* **Riser ön kontrolleri** — riser kanaldan geniş, geçiş boyu > 0, geçişin yuvarlak ucu gövdeden
  uzak, dirsek kendi içinden geçmiyor, dirsek çıkış
  borusuna ve çıkış dirseğine ulaşmıyor, oluğun duvardaki açıklığı dirsekle taban arasına sığıyor,
  uç yüzü tamamen riser'ın dışında, başlangıç yüzü riser'ın içinde ve tabanın üstünde, eğim
  0–90° arasında, riser tabanı z = 0'ın üstünde.
* **Adım başına sınırlayıcı kutu** — yanlış düzlem eşlemesini, ters eğimi, ters ötelemeyi
  metre mertebesinde yakalar.
* **Gövde sayısı** — her adımda tam olarak 1. İkiye çıkması birleşimin tutmadığı demektir.
* **Kapalılık** — her kenarın tam iki komşu yüzü olmalı. Serbest kenar = açık kabuk = CFD'de
  kaçak.
* **Sınır yüzleri** — `meal_inlet` / `gas_outlet` / `dust_outlet` her biri tam bir kez
  bulunmalı ve alanları sırasıyla 1.858 / 4.524 / 0.126 m² çıkmalı. İki giriş yüzü bulunması,
  kanalın gövdeye girememiş ve uç kapağının açıklığı tıkıyor olması demektir. Riser
  açıkken kanal eksenine dik **hiç** yüz kalmamalı (dirsek kanal ucunda erimiş olmalı); giriş
  yüzü riser tabanıdır (daire, 3.70 m²) ve `meal_feed` 0.36 m² tam bir kez bulunur.

## Sınır yüzlerinin Fluent'e taşınması

Yüzler adla değil, **ne oldukları** ile bulunur: yüzey düzlem mi, normali ne, üzerindeki
nokta nerede. Boolean sonrası yüz adları yeniden üretildiği için `SelectByID2` ile ad
araması kırılgandır.

Her sınıfa ayrı bir renk atanır; AP214 yüz renklerini taşır, Fluent Meshing bunlardan
named selection üretir.

| Sınır | Renk | Alan |
|---|---|---|
| `meal_inlet` | yeşil | 1.858 m², kanalın ucu; riser açıkken riser tabanı (z = 0.885, daire 3.70 m²), Fluent'te `inlet_gas` |
| `meal_feed` | mor | 0.36 m², yalnız riser açıkken; oluğun eğik uç yüzü; gaz için duvar, DPM için enjeksiyon yüzeyi |
| `gas_outlet` | mavi | 4.524 m², inen borunun ucu, z = 11.44 (çatı düzlemi, x = 6.0–8.4), aşağı bakar |
| `dust_outlet` | turuncu | 0.126 m² |
| duvarlar | gri | — |

AP203 renk taşımaz; şema `swStepAP = 214` olarak ayarlanır.

STL metre cinsinden ve **pozitif uzaya ötelenmeden** yazılır. Öteleme açık kalsaydı model
sessizce kaydırılır ve doğrulanan koordinat sistemi (toz çıkışı z = 0) anlamını yitirirdi.
Sapma 1e-3 m / açısal 0.1 rad — silinen `geometry/export.py`'nin CadQuery çıktısı için
kullandığı değerler, ikisi karşılaştırılabilir kalsın diye.

## Makro global ayarları değiştirir ve geri alır

`AddToDB`, `DisplayWhenAdded`, `swPerformanceVerifyOnRebuild` ve `swInputDimValOnCreate`
uygulama düzeyinde durumdur. Makro bunları değiştirir ve çıkarken — başarılı da olsa,
hata da verse — eski değerlerine döndürür. `AddToDB` açık kalırsa aynı SolidWorks
oturumundaki elle çizimler bozulur.

`swPerformanceVerifyOnRebuild` bilerek **açılır**: yavaştır ama non-manifold geometri
üretmiş bir Boolean'ın sessizce kabul edilmesini engelleyen şey odur.

## Kanal nasıl kuruluyor

Kanal, kendi **yan görünüşü** olarak çiziliyor: x–z düzleminde kestiği dörtgen, kanalın
iç duvarının düzleminde (y = 1.30) çizilip y boyunca giriş genişliği kadar ötelenerek
katılaştırılıyor. 5° eğim ve eğik giriş yüzü çizimin içinde taşınıyor, dolayısıyla
öteleme sıradan, ana eksen boyunca, kör (blind) bir öteleme oluyor.

Dörtgenin siklon tarafındaki kenarı doğrudan gövdenin teğet düzlemi (x = 0). Kanalın
tam orada bitmesi gerekiyor: erken biterse uç kapağı birleşmeden sağ çıkıp açıklığı
tıkar, geç biterse gövdenin karşı tarafından dışarı taşar — çünkü y = R'de gövde
x = 0'dan öteye gitmiyor.

Bu kurgu, ilk denemede takılan üç şeyi birden ortadan kaldırıyor: 3B çizim, üç noktadan
referans düzlem ve "Up To Surface" bitiş koşulu. Yerine kalan iki işlem — mesafe
ötelemeli referans düzlem ve kör öteleme — API'nin en çok yürünmüş yolları.
Her ikisinin de yönü tahmin edilmiyor: düzlem kurulup üzerinde bir nokta sınanıyor,
öteleme yapılıp hacmi ölçülüyor; yanlış tarafa düşerse geri alınıp ters yönde
tekrarlanıyor.

## Derleme hatası alırsanız

Makro erken bağlama (early binding) kullanır: `swStepAP`, `swSTLDontTranslateToPositive`,
`swRefPlaneReferenceConstraint_Distance` gibi sabitler SolidWorks'ün kendi
tip kütüphanesinden gelir, sayısal değerleri dosyaya yazılmamıştır. Bu bilerek yapıldı —
yanlış bir sayısal sabit sessizce yanlış davranır, yanlış bir **ad** ise derleme anında
"Variable not defined" der ve nerede olduğunu gösterir.

Böyle bir hata alırsanız: VBA düzenleyicisinde **F2** (Object Browser), sabiti arayın,
kurulu sürümdeki adıyla değiştirin. Sabit adları SolidWorks sürümleri arasında nadiren
değişir; geometri kodunun geri kalanı bundan etkilenmez.

`Tools → References` altında **SOLIDWORKS 20xx Type Library** ve **SOLIDWORKS Constant
type library** işaretli olmalı. Tools → Macro → New ile açılan bir makroda ikisi de
varsayılan olarak gelir.

## SolidWorks'ün dört sürprizi

Hepsi makroda çözülü, ama not düşmeye değer — başka bir makro yazarken aynı yere
düşülüyor.

**Çizim düzleminin eksen yönü düzlemden düzleme değişiyor.** `ModelToSketchTransform`'un
bildirdiği eşleme ile `CreateLine`'ın koordinatları yorumlaması aynı şey değil, ve fark
her düzlemde aynı bile değil: 2026 SP4.1'de `Sağ Düzlem` için `u × −1, v × +1`,
kanalın ofset düzlemi için `u × +1, v × −1` ölçüldü. Bu yüzden makro varsaymıyor,
her düzlemde bir test dikdörtgeni kurup ölçüyor.

**`ModelToSketchTransform`'un ötelemesi adının vaat ettiği yönde değil.** Üçüncü
bileşeni sıfırla karşılaştırmak, noktanın düzlem üzerinde olduğunu değil,
noktanın düzlemin **orijine göre aynası** üzerinde olduğunu da kabul eder.
`InsertRefPlane` ofset düzlemi hangi tarafa koyacağını kendi seçtiği ve makro da
tarafı bu karşılaştırmayla denetlediği için, kanal düzlemi y = +1.30 yerine
y = −1.30'da kuruldu ve bütün kanal −y'de, aynalanmış olarak çıktı. Makronun
hiçbir kontrolü bunu göremedi: gövde y'de simetrik olduğu için sınırlayıcı kutu
tuttu, ayna hacmi değiştirmediği için hacim tuttu, giriş yüzü aynı kaldığı için
alan tuttu. İlk üretilen `C1.step` bu hâldeydi ve hata ancak Fluent'te giriş
yüzünün y ağırlık merkezi okunarak bulundu.

Çözüm iki parçalı ve ikisi de ölçüme dayanıyor: düzlemin **nerede olduğu** artık
üzerine bırakılan test bloğunun sınırlayıcı kutusundan okunuyor (`OffsetPlane`,
`ProbeLandsWhereAsked`'ın üçüncü ekseni), noktaların **eş düzlemli olduğu** ise
aynı çizimdeki ilk noktaya göre karşılaştırılıyor (`G2S`) — mutlak değere hiçbir
yerde anlam yüklenmiyor. Ders: bir düzlemin yerini onun kendi dönüşümüne sorma,
üstüne bir şey koyup nereye düştüğüne bak.

**`IModelDocExtension::SaveAs` başarılı olduğu hâlde `False` dönebiliyor.** Dosya
diske yazıldı, hata kodu 0 geldi, dönüş değeri yine de `False`'tu. Makro dönüş
değerini hiç kullanmıyor; sonucu hata kodundan ve dosyanın gerçekten diskte
olmasından okuyor.

**`IFace2::MaterialPropertyValues` yanlış diziyi itirazsız yutuyor.** VBA'nın
`Array(...)` çağrısı Variant-içinde-Variant dizisi üretir; özellik bunu kabul edip
kırmızı ve mavi kanalları sıfırda bırakmış, üç ayrı sınır rengi iki renge düşmüştü —
hata yok, uyarı yok, sadece yanlış STEP. Tipli `Double` dizisi doğru çalışıyor.
Renkler sınır adlarını Fluent'e taşıyan tek kanal olduğu için makro artık atadığı
rengi geri okuyup kontrol ediyor. (`IFace2`'de `SetMaterialPropertyValues2` yok;
çağrılırsa çalışma anında "Object doesn't support this property or method" verir.)

## Body of Influence

Makro, siklonun yanı sıra mesher'a bir **Body of Influence** silindiri üretir
(`BuildBoi`, ayrı bir `<ad>_boi.step`). `EXPORT_BOI = True` ile **açık**.

```
r     = BOI_RADIUS                    0.80 m
taban = koninin BOI_RADIUS + BOI_CLEARANCE'e açıldığı yükseklik   z = 2.135 m  (türetilir)
tavan = çatı + BOI_ROOF_MARGIN                                    z = 12.440 m
hacim = 20.719 m³
```

Yarıçap ölçülmüş bir sayı: ilk çözülmüş koşuda z = 8 m'de alınan teğetsel hız
profili, hızın r = 1.0 m'ye kadar doğrusal yükseldiğini gösterdi — yani çözücü
0.25–0.35 m olması gereken çekirdeği 1 m'lik bir katı tekerleğe yayıyor. Profil
ayrıca x = +0.35'te sıfırlanıyor, girdap ekseni merkezden kaymış. 0.80 m ikisini
de kapsar. Önceki 1.6 m değeri, çekirdeğin gerçekten ihtiyaç duyduğu 0.04 m
elemanla ~1.5 milyon hücre ederdi; 0.80 m ~320 bin eder.

Taban **türetilir, ayarlanmaz**: koni duvarını kestiği yerde bir iyileştirme
cephesi oluşur ve cephenin geometrik yüzeye oturması sliver üretir (ölçüldü:
r = 1.25'te orthogonal quality 0.015). Ön kontrol hem bu tabanı hem de yarıçapın
gövde duvarına ve vorteks bulucuya `BOI_CLEARANCE` kadar uzak kalmasını zorlar.

**Mesher'a nasıl verilir.** İlk denemede silindir siklonun kendi parçasına
eklenmişti; watertight workflow onu akışkan bölgeye kaynaştırdı ve koni içinde
kayboldu. Doğrusu iki STEP'i ayrı dosya olarak vermek:

```
Import Geometry → Import Type: Multiple Files → C1.step + C1_boi.step
Add Local Sizing → Body of Influence → yalnızca BOI gövdesini seç → 0.04 m
```

## Sonraki adımlar

* Çekirdek inceltmesi yapılmış mesh'le RSM koşusu; karşılaştırma tabanı
  `cyclone_C1.md`'deki 254.4 Pa / 26.1 m/s ve z = 8 m teğetsel hız profili.
* Üretilen `C1.step`'i Fluent Meshing'e alıp renklerden named selection üretimini
  doğrulamak — dışarıdan teyit edilmemiş tek halka bu.
* İstenirse sınır başına ayrı STL patch'i (`IFace2::GetTessTriangles`) — OpenFOAM'a
  geçilirse gerekir, Fluent + AP214 için gerekmez.
* C2–C5: parametre bloğundaki sekiz sayıyı değiştirmek yeterli. C2 için beklenen
  ekipman hacmi 180.1 m³ (`cyclone_C2.md`), bağımsız bir doğrulama noktası.

## Çizim makrosunun dersleri (kalsinatör, fırın, soğutucu, 14-16 Kasım 2026)

* Kenardan görünen bir daire boyutlandırmada bir çizgi gibi ölçülür (`D_TA`, ön görünüşten `D_feed`); eğik ya da kısmi bir daire yarıçap olarak ölçülür. Tam çap için dairenin tam göründüğü görünüş seçilir.
* Eksen boyunca bakılan uç görünüşünde yakın uçtaki daire uzaktakini gizler: görünür olan seçilir (`D_kiln` z = L ucunda).
* Hangi uç yüzün öne düştüğü varsayılmaz, `FindEdge` ile bulunur (`DimensionCooler`).
* Sayfa ölçeğinden farklı bir görünüş (1:50 uç görünüşü) `scaleD`'yi yalnız o görünümün kurulumu için değiştirerek yapılır.
* Çizim makrosu CFD katısını salt okunur açar, sonda dosya damgasını doğrular; boyutlar katının kenarlarından okunur ve yaml ile karşılaştırılır (`MISMATCH`/`MISSING`).
* Küçültülmüş SolidWorks görünüm çizmez: gizli çizgiler ve teğet kenarlar kaybolur, onlara bağlı ölçü `MISSING` olur. `drawings.bas` pencereyi çalışma süresince açar, sonra geri küçültür. Ölçülerde ondalık ayırıcı nokta: Türkçe Windows'ta sistem ayırıcısı virgüldür, makro bu sistem ayarını çalışma süresince değiştirip geri alır.
* Her paftanın altındaki "SOLIDWORKS Eğitim Ürünü. Yalnızca Eğitim Amaçlı Kullanım İçindir." yazısını SolidWorks'ün eğitim lisansı basar; makro kaldıramaz. Ticari lisanslı bir SolidWorks'te makrolar yeniden çalıştırılınca kaybolur. `tools/sheet_overlaps.py` bu satırı çakışma sayımına katmaz.
* Belge numarası: ekipman paftaları `CI-<alan>-<ekipman>-001`, P&ID paftaları `CI-<alan>-PID-<pafta no>` (`pid.yaml`'daki `id`); alan PH ön ısıtıcı (siklonlar, ikiz C1, ID fan), CA kalsinatör, RK döner fırın, CL soğutucu.

## Makroları WSL'den çalıştırmak

SolidWorks açıkken `python3 tools/sw_run.py drawings.c5 pid.kiln ...` makroları WSL'den çalıştırır. Bir kerelik kurulum: SolidWorks'te yeni bir makro `geometry/output/loader.swp` olarak kaydedilir ve içine yalnız `loader.bas` (`sw_loader` modülü) alınır. Her çalıştırmada önce `sw_loader.reload` güncel `drawings.bas` ve `pid.bas`'ı bu projeye yeniden alır ve kaydeder; elle import gerekmez. Çalışma süresince `geometry/output/quiet.flag` makroların kapanış penceresini atlatır; her işin açtığı belgeler iş bitince kapatılır.

## Çizimi olmayan seçimler (16 Kasım 2026)

CFD katısı ve çizimi olmayan, ama prosese göre seçilen ekipman `plant_geometry.yaml`'da kendi bölümüyle ve `geometry/` altında kendi dokümanıyla tutulur (hepsi "Estimated", kaynakları dokümanda): ID fan ([`fan/id_fan.md`](../fan/id_fan.md)), JETFLEX yakıcı ([`kiln/kiln_burner.md`](../kiln/kiln_burner.md)), kiln başlığı ve giriş odası hız kontrolü ([`kiln/kiln_hood.md`](../kiln/kiln_hood.md), [`kiln/kiln_inlet_chamber.md`](../kiln/kiln_inlet_chamber.md)), meal pipe'lar C1–C5 (her `meal_pipe_C*.md`'nin sonundaki bölüm). Hesaplar `plant_geometry.py`'de (`id_fan`, `kiln_burner`, `kiln_hood`, `kiln_inlet_chamber`, `meal_pipes`).
