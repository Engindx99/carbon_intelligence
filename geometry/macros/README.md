# SolidWorks makroları

`geometry/` paketi `c99b93a` ile silindiğinden CFD katılarını üreten bir araç kalmamıştı.
Bu dizin onun yerini alır: bileşen dokümanlarındaki ölçülerden SolidWorks içinde
akışkan hacmini kuran, kendini doğrulayan ve dışa aktaran makrolar.

| Dosya | Ne yapar |
|---|---|
| `cyclone.bas` | Tek bir siklonun CFD akışkan hacmi → STEP (AP214) + STL + SLDPRT |

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

Dosyanın başındaki parametre bloğundaki sekiz katalog ölçüsünü ve `CYCLONE_NAME`'i değiştir.
Başka hiçbir yerde çıplak sayı yok — geri kalan her koordinat bunlardan hesaplanır.
Bütün hatların bütün kademeleri [`geometry/catalog.md`](../catalog.md) içinde:
`D, barrel_h, cone_h, vortex_len, vortex_D, dust_D, inlet_w, inlet_h`.

C2–C5'te yayınlanmış giriş yüksekliği gövdeden uzundur ve kanal bilerek koni bölgesine iner.
Bu bir hata değildir, makro düzeltmez — katalog ne diyorsa o kurulur.
Eğimi olmayan bir siklon için `INLET_SLOPE_DEG = 0` yeterlidir.

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

**`INLET_TANGENT_RELIEF = 0.0 m`** — Kanalın dış duvarı gövdeye tam teğet; gerçek geometri
bu ve `cyclone_C1.md` de bunu söylüyor. Bedeli, birleşimin teğet çizgi boyunca sıfır açılı
bir bıçak kenarına kapanması ve Fluent Meshing'in orada sliver hücre üretmesi.
Fluent zorlanırsa `0.02` yap: **her iki** kanal duvarı içeri kayar, yani kullanılan
0.86 × 2.16 kesiti ve dolayısıyla giriş hızı birebir korunur. Vorteks bulucuya kalan
pay 0.050 m olduğundan 0.05'e dayanmadan kal — 0.02 güvenli. Kullanırsan `cyclone_C1.md`'ye yaz.

**Kanal boyu `L_INLET = 3.0 m`** — Gövdenin teğet düzleminden (x = 0) dışarı, kanal ekseni
boyunca, **kesit ağırlık merkezinden** ölçülür. Yüz eğik olduğu için başka bir datum
seçilirse boy ±0.22 m belirsiz kalır; ağırlık merkezi datumu ayrıca hacim formülünü
tam yapar. Bu bir tesis ölçüsü olduğundan `twin_cfg.yaml`'daki
`inlet_extension_over_D` C1 için kullanılmaz.

Volüt modellenmez; farin borusu yoktur, toz çıkışı bir sınır yüzüdür.

## Makro kendini nasıl doğrular

Hiçbir şey dışa aktarılmadan önce, her adım kapalı formdaki aritmetikle karşılaştırılır —
önceki bir çalıştırmayla değil. Herhangi biri düşerse makro durur, **hiçbir dosya yazmaz**
ve parçayı ekranda inceleme için bırakır.

* **Ön kontroller** — giriş yüzü gövdenin dışında mı, kanal toz çıkışının altına iniyor mu,
  vorteks bulucu duvarı sığıyor mu, kanalın iç duvarı vorteks bulucuya çarpıyor mu,
  açıklık çatının altında mı. Silinen `cyclone_layout()`'un reddettiği dördü artı eğimin
  getirdiği ikisi.
* **Adım başına hacim** — 4 adımın her birinin beklenen hacmi kapalı formda hesaplanır ve
  ‰1 toleransla karşılaştırılır. En sıkı olanı ilki: gövde + koni = **124.54 m³**,
  dokümanın fiziksel hesapta kullandığı sayı.
* **Adım başına sınırlayıcı kutu** — yanlış düzlem eşlemesini, ters eğimi, ters ötelemeyi
  metre mertebesinde yakalar.
* **Gövde sayısı** — her adımda tam olarak 1. İkiye çıkması birleşimin tutmadığı demektir.
* **Kapalılık** — her kenarın tam iki komşu yüzü olmalı. Serbest kenar = açık kabuk = CFD'de
  kaçak.
* **Sınır yüzleri** — `meal_inlet` / `gas_outlet` / `dust_outlet` her biri tam bir kez
  bulunmalı ve alanları sırasıyla 1.858 / 4.524 / 0.126 m² çıkmalı. İki giriş yüzü bulunması,
  kanalın gövdeye girememiş ve uç kapağının açıklığı tıkıyor olması demektir.

## Sınır yüzlerinin Fluent'e taşınması

Yüzler adla değil, **ne oldukları** ile bulunur: yüzey düzlem mi, normali ne, üzerindeki
nokta nerede. Boolean sonrası yüz adları yeniden üretildiği için `SelectByID2` ile ad
araması kırılgandır.

Her sınıfa ayrı bir renk atanır; AP214 yüz renklerini taşır, Fluent Meshing bunlardan
named selection üretir.

| Sınır | Renk | Alan |
|---|---|---|
| `meal_inlet` | yeşil | 1.858 m² |
| `gas_outlet` | mavi | 4.524 m² |
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

## Sonraki adımlar

* Makro mesher'a bir **Body of Influence** silindiri de üretebilir (`BuildBoi`: eksende
  r = `BOI_RADIUS`, z = 0 → çatı + `BOI_ROOF_MARGIN`, ayrı bir `<ad>_boi.step`). `EXPORT_BOI`
  ile **kapalı**. Açarsan ön kontrol yarıçapın gerçek yüzeylerin hepsinden en az `BOI_CLEARANCE`
  uzakta olduğunu zorlar — bir iyileştirme cephesi geometrik kenara oturduğunda orada sliver
  çıkıyor (ölçüldü: r = 1.25'te orthogonal quality 0.015). Kapalı olmasının sebebi geometri
  değil, Fluent Meshing'in iki gövdeli geometride bölgeleri ayırmaması.
* **Düzlem tarafı düzeltmesinden sonra makro henüz çalıştırılmadı.** Diskteki
  `C1.step` (24 Eylül 2026, 22:28) hâlâ kanalı −y'de taşıyan aynalanmış sürüm;
  Fluent'teki mesh ve çözüm ondan üretildi ve geçerli (tek siklonda ayna görüntüsü
  birebir aynı fiziktir). Makro bir dahaki koşuda kanalı +y'ye koymalı ve
  `meal_inlet` yüzünün y ağırlık merkezi **+1.73 m** çıkmalı — ölçüp doğrula.
* Üretilen `C1.step`'i Fluent Meshing'e alıp renklerden named selection üretimini
  doğrulamak — dışarıdan teyit edilmemiş tek halka bu.
* İstenirse sınır başına ayrı STL patch'i (`IFace2::GetTessTriangles`) — OpenFOAM'a
  geçilirse gerekir, Fluent + AP214 için gerekmez.
* C2–C5: parametre bloğundaki sekiz sayıyı değiştirmek yeterli. C2 için beklenen
  ekipman hacmi 180.1 m³ (`cyclone_C2.md`), bağımsız bir doğrulama noktası.
