# CFD çalışma dokümanı: 2500 t/d referans hattı

Bu dosya CFD çalışmasında doğrudan kullanılmak için hazırlandı. Kaynaklar, provenance ve katalog dışında kalan ölçüler burada yok; onlar [SOURCES.md](SOURCES.md) ve [INVENTORY.md](INVENTORY.md) içinde. Buradaki bütün değerler `geometry/catalog.py`'den gelir ve yeni ölçü içermez.

**P** = kaynakta yayınlanmış, **R** = yayınlanmış bir değerin FLS oranıyla türetilmesi (`derived_from_reference`). Bütün uzunluklar metre, bütün çaplar efektif iç çaptır (refrakterin içi).

## 1. Referans hat: 2500 t/d

- **Önısıtıcı ve kalsinatör:** Hefei enstitüsünün HFC2500 tasarımı (2005). Efektif çaplar yayınlanmış (P).
- **Siklonların diğer ölçüleri:** FLS referans kulesinin, aynı numaralı kademesinin oranlarından türetilmiş (R).
- **Fırın ve soğutucu:** Jiangsu Pengfei 2500 hattı.
- **Yapı:** Tek dizi, beş kademe. C1 iki siklondan oluşur, C2–C5 tekli.

Bu seçim yalnızca geometri referansıdır. Twin'in beslemesini ya da kapasitesini değiştirmez (`geometry.reference_line: "2500"`).

## 2. İlk prototip: C2 siklonu

C2'nin seçilme nedeni, C1'e özgü aktarım varsayımını (FLS'nin tek üst siklonundan çoklu C1'e) taşımaması.

### 2.1 Geometri

| Ölçü | Değer [m] | Durum |
|---|---|---|
| Efektif iç çap D | 6.10 | P |
| Silindirik gövde yüksekliği | 3.67 | R |
| Koni yüksekliği | 6.51 | R |
| Vorteks bulucu çapı | 4.35 | R |
| Vorteks bulucu boyu (daldırma) | 3.05 | R |
| Toz çıkışı çapı | 0.80 | R |
| Giriş genişliği × yüksekliği | 1.23 × 8.71 | R, FLS'nin `w_in = 0.4 r_c` model varsayımına dayanır |

Bu ölçülerden hesaplanan büyüklükler:

| Büyüklük | Değer |
|---|---|
| Toplam yükseklik (gövde + koni) | 10.18 m |
| Koni duvarının yatayla açısı | 67.9° (farinin 40°'lik yığılma açısının üstünde) |
| Giriş kesiti; hidrolik çapı | 10.67 m²; 2.15 m |
| Vorteks bulucu kesiti | 14.84 m² |
| Toz çıkışı kesiti | 0.509 m² |
| Islak alan (gövde + çatı halkası + koni) | 160.9 m² |

### 2.2 CFD domeni: koordinatlar

Siklonun ekseni z, toz çıkışı z = 0'da. Bu değerler `components.cyclone_layout` fonksiyonunun çıktısıdır.

| Bölge | Konum |
|---|---|
| Koni | z = 0 → 6.511 m (Φ0.80 → Φ6.10) |
| Silindirik gövde | z = 6.511 → 10.179 m (çatı) |
| Giriş kanalı | x = −3.660 → 0, y = 1.825 → 3.050, z = 1.469 → 10.179 m. Gövdeye teğet; gaz +x yönünde girer. |
| Vorteks bulucu duvarı | z = 7.129 → 10.179 m, 0.012 m kalınlığında (oyulmuş) |
| Çıkış borusu (vorteks bulucunun içi) | z = 7.129 → 14.526 m, Φ4.35 |

**Sınır yüzleri:**
- giriş kanalının x = −3.660 m'deki yüzü (giriş),
- çıkış borusunun z = 14.526 m'deki üst yüzü (çıkış),
- z = 0'daki toz çıkışı diski.

Diğer bütün yüzler duvardır.

**Hazırlanmış dosya:** Tek parça, kapalı katı `geometry/output/2500/C2.step` (ayrıca `.stl`). Nasıl üretildiği bölüm 6'da.

## 3. Hacim ayrımı: ekipman hacmi ve CFD domen hacmi

| C2 | Hacim [m³] |
|---|---|
| **Ekipman hacmi** (gövde + koni; `properties.cyclone_properties().body_volume`) | **180.1** |
| + Giriş kanalının gövde ve koninin dışında kalan kısmı | 29.0 |
| + Çatının üstündeki çıkış borusu | 64.5 |
| − Vorteks bulucu duvarı | 0.5 |
| **CFD domen hacmi** (`C2.step`) | **273.1** |

**Kalma süresi, holdup ve benzeri fiziksel hesaplar ekipman hacmini kullanır.** CFD domen hacmi, modelleme parametrelerine bağlı uzatmaları içerir; fiziksel hesapta kullanılmaz.

## 4. CFD sınır varsayımları

Bunlar **tesis ölçüsü değildir ve kaynakları yoktur**. Modelleme seçimidir, config'teki `geometry.cfd_boundary` bölümünde tanımlıdır ve kodda varsayılan değerleri yoktur.

| Parametre | Değer | Etkisi (C2) |
|---|---|---|
| `inlet_extension_over_D` | 0.6 | Giriş yüzü eksenden 0.6 D uzakta. En az 0.401 olmalı, yoksa yüz gövdenin içinde kalır; kod bunu kontrol eder. Her +1 D için hacim ≈ +65 m³. |
| `outlet_extension_over_vortex_D` | 1.0 | Çıkış yüzü çatıdan 1 vorteks bulucu çapı yukarıda. Hacme en çok etki eden parametre: her +1 çap için ≈ +64.5 m³. |
| `vortex_finder_wall_m` | 0.012 m | İnce bir ayırıcı duvar; hacme etkisi yaklaşık %0.2. |

**Geometrideki modelleme sadeleştirmeleri:**
- Yayınlanmış 270°'lik volüt modellenmiyor; giriş düz, teğet bir kanal.
- Yayınlanmış giriş yüksekliği (8.71 m) gövdeden (3.67 m) uzun. Bu yüzden giriş kanalı koni bölgesine iniyor ve katalog ölçüleri düzeltilmeden olduğu gibi kuruluyor.
- Farin borusu yok; toz çıkışı bir sınır yüzü.

## 5. Eksik ya da belirsiz geometri

Aşağıdakiler şu an **kurulamıyor**. Bunlar CFD ile türetilmeyecek; bir kaynak ya da açık bir kullanıcı kararı gerekiyor.

| Konu | Durum |
|---|---|
| R1–R4 riser boyları | Hiçbir kaynakta yayınlanmamış. |
| Riser şekli | FLS makalesinin metni ile denklemleri çelişiyor (SOURCES.md, "Açık belirsizlikler"). Riser katısı ve hacmi yok. |
| Kaz boynu boyu | Hiçbir kaynakta yok. Çapı var: Φ3.50 (P). |
| Kule yerleşimi | Eksen ofsetleri, dirsekler, C1'deki Y ayrımı: `LayoutParams` alanları tanımlı, değerleri yok. Kule, `tower.build_tower` ile eksik alanları sayarak reddediliyor. |
| Volüt geometrisi, kalsinatör giriş boğazı, fırın giriş odası | 2500 hattı için kaynak yok. |
| Tersiyer hava kanalı | Karar gereği kapsam dışı; kalsinatör tabanı tek giriş. |

**CFD ile belirlenecek olanlar tesis geometrisi değil, bölüm 4'teki üç sınır parametresi.** Bunların sonuca etkisi bir duyarlılık çalışmasıyla gösterilecek.

## 6. İş akışı

1. **Katıyı üret.** CadQuery ayrı bir dizinde kurulu (`requirements-cad.txt`):
   ```
   PYTHONPATH=/home/wsl/.cad-libs:. python3 -m geometry --export
   ```
   Komut `geometry/output/2500/` altına C1–C5 ve kalsinatörün STEP/STL dosyalarını yazar, ekipman ve CFD hacimlerini yan yana basar.
2. **Kontrol et.** `C2.step` tek parça ve kapalı bir katı olmalı, hacmi 273.1 m³ olmalı. Aynı kontrolü `tests/test_geometry_solid.py` yapıyor.
3. **Ağı oluştur ve sınırları ata.** STEP dosyası bir ağ oluşturucuya aktarılır ve bölüm 2.2'deki üç sınır yüzü adlandırılır. Ağ oluşturucu ve çözücü seçimi bu dokümanın kapsamında değil.
4. **İşletme koşullarını gir.** Gaz debisi, sıcaklık ve toz yükü twin'den ya da tesis verisinden gelir. Bu doküman bunların değerini vermez.
5. **Sınır parametrelerinin duyarlılığını ölç.** Önce çıkış uzatması (en baskın), sonra giriş uzatması değiştirilir. Parametreler yalnızca config'ten değiştirilir.
6. **Sonraki adımlar:**
   - C3–C5 siklonları aynı yolla kurulabilir.
   - C1 aktarım varsayımını taşıdığı için bu varsayım not edilerek kurulmalı.
   - Kalsinatör şu an Φ5.50 × 29.46 m'lik düz bir silindir (D P, H R); tabanı tek giriş, tepesi çıkış.
   - Kule, bölüm 5'teki eksikler kapanmadan kurulamaz.

## Ek: 2500 hattının diğer hazır bileşenleri

| Bileşen | Ölçü [m] | Durum | Ekipman hacmi [m³] |
|---|---|---|---|
| C1 (×2, her biri) | D 4.32; gövde 6.79; koni 4.65; vorteks bulucu Φ2.40 × 2.16; toz Φ0.40; giriş 0.86 × 4.97 | D P, diğerleri R; C1 aktarım varsayımı | 124.6 |
| C3 | D 6.30; gövde 3.22; koni 7.26; vorteks bulucu Φ4.62 × 3.15; toz Φ0.84; giriş 1.26 × 9.46 | D P, diğerleri R | 187.0 |
| C4 | D 6.30; gövde 3.46; koni 7.30; vorteks bulucu Φ4.63 × 3.17; toz Φ0.81; giriş 1.27 × 9.44 | D P, diğerleri R | 194.5 |
| C5 | D 6.50; gövde 3.53; koni 7.43; vorteks bulucu Φ4.74 × 3.25; toz Φ0.83; giriş 1.30 × 9.59 | D P, diğerleri R | 211.2 |
| Kalsinatör | Φ5.50 × 29.46 | D P, H R | 700.0 |
| Riserler R1–R4 (C2→C1 … C5→C4) | Φ3.07 / 3.35 / 3.45 / 3.60; boy yok | P, yalnızca kesit | — |
| Kaz boynu | Φ3.50; boy yok | P, yalnızca kesit | — |
| Fırın (kule dışı) | Φ3.633 × 60; eğim %4; 0.39–4.10 rpm | D R, diğerleri P | 622.0 |
| Soğutucu (kule dışı) | Izgara alanı 65 m² | P | — |
