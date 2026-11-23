# Soğutucu CFD hacmi (cooler_cfd)

Tesis: 5000 t/d, ızgara 4 × 29,9 m ([cooler.md](cooler.md)). Bu hacim soğutucunun gaz tarafını modellemek için kuruldu (kullanıcı kararları, 23 Kasım 2026: segment havası FLS biçiminde, twin'in toplamına ölçekli; alev hacmine tek yönlü bağlantı, hood düzleminden; giriş ızgarası literatürden). Katı `geometry/macros/cooler.bas` → `cooler.SLDPRT` / `.step`. Yerleşim `plant_geometry.cooler_cfd()`, sınır değerleri `plant_geometry.cooler_boundaries()`.

Hacmin parçaları (iki gövde, ortak yüzleri `bed_top`):
- **Yatak (`bed`):** ızgara üstünde 0,409 m'lik klinker dilimi, gözenekli hücre bölgesi.
- **Üst boşluk (`freeboard`):** yataktan tavana; tavanda hood'un iki açıklığı, ortanın bir segment ilerisinde vent kanalı.
- **Giriş ızgarası (CIS):** ilk segment, sıcak uca doğru 12° yükselen sabit ızgara; ardından düz ızgara.

## Sınır değerleri

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Soğutma havası (kg/kg klinker) | 2.2 kg/kg | literatür |
| Soğutma havası toplamı | 127.315 kg/s | türetilmiş |
| FLS referansının hava oranı (yalnız biçim kullanılır) | 3.569 kg/kg | türetilmiş |
| `grate_air_1` (12.227 m²) | kütle debisi girişi, 27.491 kg/s, 293.1 K | undergrate air, FLS segment share (the inclined inlet) |
| `grate_air_2` (11.960 m²) | kütle debisi girişi, 12.478 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_3` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_4` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_5` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_6` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_7` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_8` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_9` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `grate_air_10` (11.960 m²) | kütle debisi girişi, 10.918 kg/s, 293.1 K | undergrate air, FLS segment share |
| `hood_1` (11.960 m²) | kütle debisi çıkışı, 18.480 kg/s | to the kiln: the secondary air (kiln_flame secondary_air_in less the seal's leak) |
| `hood_2` (11.960 m²) | kütle debisi çıkışı, 54.925 kg/s | to the tertiary air duct (kiln_flame tertiary_supply_in) |
| `vent_out` (6.146 m²) | basınç çıkışı | 0 Pa gauge (reference); the vent air, the rest |
| `bed_top` (119.867 m²) | iç yüz (iki gövdenin ortak yüzü) | the bed's top: shared face of the bed and the freeboard |
| `clinker_out` (1.637 m²) | iç yüz (iki gövdenin ortak yüzü) | the bed's end at the grate's end (shared with the freeboard): the clinker leaves the porous zone here (its enthalpy out, model); target 65 K over ambient (CII manual, IKN) |
| `hrb_deck` (16.000 m²) | duvar | the roller breaker's deck past the grate's end; the chute under it is closed by the clinker column (no false air, model) |
| Yatak gözenekliliği | 0.4 | literatür |
| Nodül çapı | 15.0 mm | modelleme |
| Viskoz direnç 1/α (Ergun) | 3750000 1/m² | türetilmiş |
| Atalet direnci C₂ (Ergun) | 2187.5 1/m | türetilmiş |
| Klinker debisi (yatakta) | 57.870 kg/s | türetilmiş |
| Klinkerin hızı (ızgara hızı) | 0.01854 m/s | türetilmiş |
| Vent havası sıcaklığı (boyutlandırma) | 523.15 K | literatür |
| Vent kanalı hızı | 13 m/s | literatür |
| Vent hacimsel debisi | 79.90 m³/s | türetilmiş |
| Vent havası (kütle dengesi) | 53.910 kg/s | türetilmiş |
<!-- END GENERATED -->

## Alev hacmiyle bağlantı (tek yönlü)

- `hood_1` ve `hood_2` alev hacminin `secondary_air_in` ve `tertiary_supply_in` yüzleriyle aynı yerde ve aynı boyda (birer segment × ızgara genişliği). Soğutucunun tavanı düz; bu iki segment tavandan split line ile ayrılmış iki yüz. Alev hacminin hood tabanı da düz ve aynı yerden ikiye bölünmüş; önceki 0,25/0,50 m'lik ağızlar ve tavandaki basamaklar kaldırıldı (kullanıcı, 23 Kasım 2026). İki hacim böylece boşluk ve bindirme olmadan yüz yüze buluşuyor; montajda (`kiln_outlet_assembly`) soğutucu, hood ve fırın tek, kesintisiz bir gaz yolu (kullanıcı, 23 Kasım 2026). Yerleşim: `plant_geometry.cooler_placement()`.
- **Sıra:** önce soğutucu koşulur. Hood yüzlerindeki hız, sıcaklık ve türbülans profilleri alev hacmine giriş olarak verilir. Alev hacmi bugün düz değerlerle kuruludur (ikincil 1250 K'den karışım 1052 K, tersiyer 1073 K).
- **Debi:** `hood_1` fırının ikincil havası. Çıkış contasının kaçağı burada yoktur; hood'da eklenir (alev hacminin kararı). `hood_2` tersiyer havadır.
- **Ters etki:** hood'daki geri dönüş soğutucuya geri yansımaz. Bu bağlantı hood düzleminde akışın yukarı yönlü olduğunu varsayar; soğutucu koşusunda bu yüzlerde ters akış raporlanmalıdır.

## Mekanik parçalar (CFD dışı)

`cooler_body.bas` (`plant_geometry.cooler_body()`) soğutucunun mekanik parçalarını basit zarflar olarak kurar; montajda soğutucuyla aynı yerleşimle durur (kullanıcı, 23 Kasım 2026). Parçalar: refrakter kasa, segment başına bir ızgara altı odası, hava dağıtım plakaları, Cross-Bar şeritlerinin hidrolik silindirleri, segment başına bir soğutma fanı (salyangoz, emiş konisi, motor, odaya kanal), soğuk uçta HRB silindirleri ve motorları, altında zemine inen çıkış oluğu.

- Şeritler: 1,2 m'lik Cross-Bar biriminde 2 hareketli çerçeve → şerit 0,6 m; 4,0 m genişlik 7 eşit şeride bölündü (şematik). Şerit başına 2 silindir, ilk odada hidrolik yok (FLSmidth broşürü).
- Fanlar: debi segmentin havası (ortam sıcaklığında), basınç sıcak uçta 7,3 kPa'dan soğuk uçta 2,9 kPa'ya doğrusal; boyut fan yasalarıyla (`id_fan()` gibi).
- Izgara altı yüksekliği zeminden türetilir (fırın ekseninin şematik yüksekliğine bağlı); Holderbank kesitindeki oranın (≈ 0,56 W) altında kalır.

## Klinker çıkışı (kullanıcı, 23 Kasım 2026)

Soğutucu son kırmayı da yapar: ızgaranın ucunda, onun devamında yatay bir valsli kırıcı döşemesi (Fuller HRB, Cross-Bar'ın varsayılan kırıcısı, "standard end-of-cooler arrangement"). Taşıma silindirlerinin aralığından ince klinker düşer, iriler kırma silindirlerinde kırılır; son kırma silindiri biraz aşağıdadır. Klinker döşemenin altındaki oluğa düşer (Holderbank 2000 Şekil 5: kırıcı uçta, kasa üstünde).

- CFD: üst boşluk HRB döşemesinin üstüne uzar (x = L … L + L_HRB, L_HRB = 4 silindir × 1,0 m = 4,0 m); uç duvar x = L + L_HRB'de.
- `clinker_out`: yatağın x = L'deki uç yüzü (yatak ile üst boşluğun ortak yüzü, interior). Klinker gözenekli bölgeyi burada terk eder; hareketli yatakla enerji hesabında entalpisi buradan çıkar (model; kaynakta CFD yöntemi bulunamadı). Ölçüt: 65 K + ortam (CII el kitabı, IKN; Holcim ≈ 90 K + ortam).
- `hrb_deck`: döşemenin üst yüzü, duvar. Altındaki oluk klinker sütunuyla kapalı kabul edildi: sahte hava yok (model; Holderbank klinker çıkışını sahte hava yollarından sayar).
- Silindir sayısı (broşür 3–6, üretime göre) model; çap, aralık, son silindirin düşüklüğü şematik.
- Dışarıda: zincir perde (Holderbank Şekil 5), silindirlerin aralığından düşen ince klinker, tava konveyör.

## Kapsam: dahil olanlar, dışarıda kalanlar (CLAUDE.md kural 10)

| Fiziksel olay / öğe | Durum | Neden kabul edilebilir | Etkilenen çıktılar |
|---|---|---|---|
| Çapraz akış: hava ızgaradan yatağın içinden yukarı | Dahil; segment başına kütle debisi girişi | Soğutucunun ısı geçişinin temeli | — |
| Segment havası dağılımı | FLS biçimi (1: %21,6, 2: %9,8, 3–10: %8,6), toplam 2,2 kg/kg | Gerçek soğutucular sıcak uca daha çok hava verir; twin şimdilik düzgün dağıtıyor (ertelendi) | Twin ile karşılaştırma |
| Giriş ızgarası (CIS) | Dahil; 12°, bir segment boyunda | Eğim yayınlanmış (Fuller patenti), boyu yayınlanmamış (model) | İkincil havanın sıcaklığı, girişte yatak |
| Klinker yatağı | Gözenekli bölge, sabit derinlik 0,409 m, ızgara hızında hareket | FLS tasarım yatağı; derinlik debiyle değişir (`cooler.md`) | Basınç kaybı, ısı geçişi |
| Yatağın girişte kabarması, yığılma, "kardan adam" | Yok | Düz yatak ilk adım; Holderbank girişteki dağılımı bir işletme sorunu olarak anlatıyor | Segment 1 havası |
| Izgara plakaları, bölme duvarları, kenar contaları | Yok; segmentler yalnız taban yüzünün bölünmesiyle | Hava debisi segment başına verildiği için plakalar debiyi değiştirmez; yerel jetler yatak içinde dağılır | Yatak altında yerel hız |
| Plakalardaki akış regülatörleri (Cross-Bar MFR) | Kütle debisi girişinin gerekçesi | Fuller: "Constant air flow irrespective of overgrate conditions"; debi yatak direncinden bağımsız | — |
| Taşıyıcı çubuklar (ızgaranın ~90 mm üstünde, şeritler halinde ileri-geri) | Yok; yatak gözenekli bölge, klinker ortalama ızgara hızıyla | Çubuklar yatağın içinde kalır; etkileri karışma ve kesme, gaz tarafına değil | Yatak içi karışma, şerit başına hız farkı |
| Giriş ızgarasındaki hava patlatma (ABC) | Yok | Aralıklı, kısa süreli; ortalama akışı belirlemez | Giriş yatağının dağılımı |
| Giriş ızgarasının ucundaki basamak | Yok; eğim düz ızgaraya iner (kullanıcı kararı) | Yüksekliği yayınlanmamış | Giriş bölümünde yatak kalınlığı |
| Giriş hunisi (eğimli yan duvarlar) | Var, hood'da (alev hacmi, 60°) | Fuller ABC Inlet görseli; ölçüsü yayınlanmamış, açı model | Hood'daki geri dönüş |
| Fırından düşen klinker perdesi (~3 m; ikincil hava içinden yukarı çıkar) | Yok; yatak x = 0'dan başlar | Perdenin yüzeyi yatağınkinin yanında küçük; ilk adımlarda ihmal (adım 3: DPM) | İkincil havanın sıcaklığı |
| Sıcak hava geri dönüşü (Fuller, ≤ 130 °C) | Yok | Bu tesiste yok; hava ortam sıcaklığında | — |
| Kırıcı, klinker çıkışı | Yok | Gaz tarafına etkisi küçük; yatak bölge olarak hacmi terk eder | Soğuk uçta akış |
| Ara hava çekişi (middle air) | Yok | Twin'de yok; kurutma için kullanılmıyor | Vent debisi |
| Ara duvar / perde | Yok | Bu tesiste kaynak yok; modern soğutucularda zorunlu değil | İkincil/tersiyer ile vent arasındaki ayrılma noktası |
| Toz (vent ve tersiyerde) | Yok | İlk adımda temiz hava | Radyasyon, vent kanalı |
| Kasa ısı kaybı | Adiyabatik duvar (ilk adım) | Twin'de soğutucu kasası için ayrı terim yok | Hava sıcaklıkları |

## Yöntem (önerilen; temel model ve artımlı adımlar, kural 9)

Literatürdeki ızgaralı soğutucu CFD'leri yatağı gözenekli ortam olarak modelliyor:
- Gaz ile klinker arasında yerel ısıl dengesizlik (LTNE) var; sıcaklık farkı büyük olduğu için denge varsayımı uygun değil (Moving packed bed, Applied Energy 2018; JADCR 2025 ızgara soğutucusu LTNE modeli).
- Klinkerin hareketi için ya dinamik ağ (dengede) ya da UDF/UDS kullanılıyor.
- Fluent'in denge-dışı gözenekli modeli katı için ayrı bir hücre bölgesi açar. Uyumsuz ara yüzlerle çalışmaz, bu yüzden `bed_top` ortak ağ (share topology) ile ağlanmalıdır.

| Adım | Fizik | Model | Amaç / kabul ölçütü |
|---|---|---|---|
| 0 | İzotermal akış | RANS, realizable k-ε; yatak Ergun dirençleri (aşağıda) | Kütle dengesi < %0,1; hood ve vent yüzlerinde ters akış yok; segment başına basınç kaybı |
| 1 | Isı, katı sıcaklığı sabit | Denge-dışı gözenekli model; katı sıcaklık profili x boyunca twin'den ya da FLS modelinden; Wakao–Kaguei h_sf | İkincil ve tersiyer havanın sıcaklığı ve enerji dengesi |
| 2 | Hareketli katının enerjisi | Katı enerjisi UDS ile x yönünde ızgara hızında taşınır, giriş 1400 °C civarı (fırın çıkışı) | Klinker çıkışı ortam + ~65–100 K; ikincil ~1050–1250 K (VDZ/CEMCAP); vent 200–300 °C (Holderbank) |
| 3 | Radyasyon ve duyarlılık | Üst boşlukta DO; d_p (10–40 mm), segment profili, CIS boyu ve eğimi; gerekirse fırın ağzından düşen klinker DPM ile (hood + soğutucu, tek yönlü çiftleme), ikincil havaya etkisi için | Hava sıcaklıklarındaki değişim |

Uygulama notları:
- **Basınç kaybının mertebesi (Ergun, bu tablodaki direnç değerleriyle):**
  - Segment 1: soğuk havada yaklaşık 1,9 kPa; 1000 °C'de yaklaşık 8,8 kPa.
  - Segment 3: soğuk havada 0,3 kPa; 1000 °C'de 1,6 kPa.
  - Bu değerler soğutucu fanlarının basınç sınıfında. Segment debisi kütle girişiyle verildiği için basınç kaybı debiyi değiştirmez.
- **Ağ:** yatakta derinlik boyunca en az 8–10 hücre. Üst boşlukta 0,1–0,2 m, vent ve hood yüzlerinde daha ince.
- **Kabul (kural 9):** residuallar, kütle ve enerji dengeleri, hood ve vent çıkış sıcaklıkları ve yatak basınç kaybı raporlanmadan çözüm kabul edilmez.

## Açık konular

- **CIS boyu** yayınlanmamış: bir segment alındı (model). Eğim olarak 12° kullanıldı; US 5,419,698'e göre 20°.
- **Vent'in yeri:** tavanda, ortanın bir segment soğuk uca doğru ilerisinde, x = L/2 + 1 segment = 17,94 m (kullanıcı, 23 Kasım 2026; önce son segmentin üstündeydi, Holderbank'in şemasında vent havası soğuk uçtan çıkıyor). Hız, toz yüklü kanal notundaki aralıktan (abrasif toz 10–16 m/s) alındı. Bu soğutucuya özgü bir kaynak değil.
- **Hava toplamı** twin'in 2,2 kg/kg'ı; FLS referansı 3,57 kg/kg kullanıyor.
- **Twin:** segment profili ve CIS yok; "geometri hazır" denince değerlendirilecek.

## Kaynaklar

- Fuller, "Heavy-duty Roller Breaker" broşürü, C 1-26 400-8-ENG V2 (2025): 3–6 silindir; taşıma ve kırma silindirleri; HRB, Cross-Bar'ın varsayılan kırıcısı.
- CII Thermal Energy Efficiency Manual; IKN pendulum cooler: klinker çıkışı 65 °C + ortam.

- FLSmidth, "FLSmidth Cross-Bar Cooler" broşürü, C 01-11 400-4-ENG V2 (2011): 1,2 / 1,8 m genişlik, 3,0 / 4,2 m uzunlukta standart birimler; birimde 2 / 3 hareketli çerçeve; şerit başına 2 veya 4 hidrolik silindir; ilk ızgara altı odasında hidrolik yok.
- Holderbank Cement Seminar 2000, Clinker Coolers, Şekil 5: kesit, fanlar kasanın yanında ızgara altı seviyesinde; valsli kırıcı.
- cementequipment.org, clinker cooler notu: fan basınçları sıcak uçtan soğuk uca 7,3 → 2,9 kPa.

- M. Svensen, F. Leal da Silva, A. Pigazo Merino, S. Sampath, J. B. Jørgensen, "A Dynamic Cooler Model for Cement Clinker Production", arXiv:2409.09076 (2024).
- "Holderbank" Cement Seminar 2000, Process Technology II – Kiln Systems, "Clinker Coolers" (s. 124–139): vent havası 200–300 °C; çalışmada 1,6–2,3 Nm³/kg; "Inclined inlet section without moving rows".
- US 2,371,513 (Fuller, 1945), "Material cooler": giriş ızgarasının eğimi "about 12 degrees". US 5,419,698: ilk basamaklı ızgara yaklaşık 20°.
- Fuller Technologies, "Cross-Bar Cooler – The Art of Cooling Clinker", broşür C 03-21400-44-ENG V4 (2025): mekanik akış regülatörleri (sabit debi), çubuklar ızgaranın ~90 mm üstünde, hareketsiz yatay ızgara, ABC giriş (sabit, eğimli, ızgara içi hava patlatma, eğimli yan duvarlar), sıcak hava geri dönüşü ≤ 130 °C. Sayısal ölçü vermiyor.
