# Geometri ölçü envanteri

Bu belge, 2026-09-21 tarihli kaynak araştırmasında bulunan **bütün geometrik ölçüleri** tek yerde toplar: hem kataloğa girenleri hem de katalog dışında bırakılanları. Kataloğa ya da koda yeni bir değer eklemez.

- **A bölümü, `geometry/catalog.py` ve `SOURCES.md` içindeki ölçüler.** Elle yazılmadı; katalogdan bir betikle üretildi. Kaynağı olmayan alanlar da "—" satırı olarak dahil.
- **B bölümü, araştırmada bulunup katalog dışında bırakılan ölçüler.** Her kaydın atanmama nedeni ve doğrulama düzeyi yazılı.
- **C bölümü, geometrik olmayan ve bu yüzden hariç tutulan değerler.**
- **D bölümü, CFD aşaması için özet.**

## Göstergeler

**Yayın durumu:**

| Durum | Anlamı |
|---|---|
| Yayınlanmış (P) | Değer kaynakta doğrudan yazıyor. 2·r gibi basit aritmetik dönüşümler de bu grupta. |
| Türetilmiş (R) | Yayınlanmış bir değer ile FLS'nin SOURCES.md'de adı geçen tek bir oranının çarpımı (`derived_from_reference`). |
| Model varsayımı (M) | Değer kaynakta yazıyor, ama ölçüm değil, kaynağın kendi modelleme varsayımı. |
| — | Hiçbir kaynakta bulunamadı. Türetilmedi. |

**Doğrulama düzeyi (yalnızca B bölümünde):**

| Düzey | Anlamı |
|---|---|
| **H-ben** | Kaynak sayfanın ya da PDF'in ham metnini ben okudum ve değeri birebir buldum. |
| **H-ajan** | Ham metni araştırma ajanı okudu; ben ayrıca doğrulamadım. |
| **Özet** | Değer yalnızca özetleyici bir araçtan ya da arama motoru parçacığından geliyor. **Doğrulanmadı.** |

**Birimler:** SI, eğim % ve dönüş hızı rpm cinsinden. Φ satıcının verdiği çelik gövde iç çapı, "efektif" ise refrakterin içindeki çap. Akışkan hacmi efektif çapla kurulur.

**Kısaltmalar:** Kaynak kimlikleri (PF1500, HFC2500 vb.) SOURCES.md'deki kaynak tablosundaki kimliklerdir. B bölümündeki yeni kimlikler B.0'da tanımlı.

---

## A. Katalogdaki ölçüler (SOURCES.md)

348 alan: 125 yayınlanmış (P), 130 türetilmiş (R), 10 model varsayımı (M), 83 kaynaksız (—).

Tüm hatlar için geçerli notlar:
- **Türetilmiş siklon ölçüleri:** FLS'deki aynı numaralı kademenin oranlarından gelir (C_k ↔ Cy_k).
- **C1 değerleri:** 1500, 2500 ve 5000 hatlarında C1 çoklu siklondur. FLS'nin üst kademesi ise tek siklondur (Cy1). Bu yüzden bu hatlardaki C1 değerleri bir **aktarım varsayımı** taşır.
- **Giriş ölçüleri:** Her hatta giriş genişliği ve yüksekliği, FLS'nin `w_in = 0.4 r_c` model varsayımına dayanır.
- **Riserler:** Riser eşlemesi (R_k: C(k+1) → C(k)) FLS Tablo 7'de açıkça yazılıdır. Riser şekli ise belirsizdir (SOURCES.md, "Açık belirsizlikler").

### A.1 Hat 1500 t/d — 1 dizi

| Ekipman | Parametre | Değer | Kaynak (ref) | Yayın durumu | Katalog | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|
| Hat | Kapasite | 1500 t/d | PF1500 | Yayınlanmış (P) | 1500 | Geometri değil | — |
| Fırın | Çelik gövde iç çapı (Φ, astar öncesi) | 3.5 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Fırın | Efektif iç çap | 3.179 m | PF1500 × FLS:kiln_eff_over_shell | Türetilmiş (R) | 1500 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Boy / yükseklik | 54 m | PF1500 | Yayınlanmış (P) | 1500 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Eğim | 4 % | PF1500 | Yayınlanmış (P) | 1500 | Kule dışı — fırın ekseni eğimi | — |
| Fırın | Dönüş hızı, min | 0.4 rpm | PF1500 | Yayınlanmış (P) | 1500 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, max | 3.96 rpm | PF1500 | Yayınlanmış (P) | 1500 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, işletme | — | kaynak yok | — | 1500 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Izgara alanı | 61.8 m² | PF1500 | Yayınlanmış (P) | 1500 | Tek başına yetersiz (L×W yok) | — |
| Soğutucu | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Genişlik | — | kaynak yok | — | 1500 (boş) | — | Bulunamadı; türetilmedi |
| Kalsinatör | Çelik gövde iç çapı (Φ, astar öncesi) | 6.3 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Kalsinatör | Efektif iç çap | 5.898 m | PF1500 × FLS:calciner_eff_over_shell | Türetilmiş (R) | 1500 | Evet — kalsinatör katısı | — |
| Kalsinatör | Boy / yükseklik | 31.596 m | PF1500 × FLS:calciner_eff_over_shell × FLS:calciner_H/D | Türetilmiş (R) | 1500 | Evet — kalsinatör katısı | — |
| Kaz boynu | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 1500 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Kaz boynu | Efektif iç çap | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Kaz boynu | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Siklon C1 | Çelik gövde iç çapı (Φ, astar öncesi) | 4.3 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C1 | Efektif iç çap | 4.132 m | PF1500 × FLS:eff_over_shell[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Silindirik gövde yüksekliği | 6.498 m | PF1500 × FLS:eff_over_shell[1] × FLS:barrel_h/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Koni yüksekliği | 4.45 m | PF1500 × FLS:eff_over_shell[1] × FLS:cone_h/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu boyu (daldırma) | 2.066 m | PF1500 × FLS:eff_over_shell[1] × FLS:vortex_len/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu çapı | 2.3 m | PF1500 × FLS:eff_over_shell[1] × FLS:vortex_D/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Toz çıkışı çapı | 0.383 m | PF1500 × FLS:eff_over_shell[1] × FLS:dust_D/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Giriş genişliği | 0.826 m | PF1500 × FLS:eff_over_shell[1] × FLS:inlet_w/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in FLS model varsayımına dayanır |
| Siklon C1 | Giriş yüksekliği | 4.752 m | PF1500 × FLS:eff_over_shell[1] × FLS:inlet_h/D[1] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in FLS model varsayımına dayanır |
| Siklon C1 | Giriş kesit alanı | — | kaynak yok | — | 1500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C2 | Çelik gövde iç çapı (Φ, astar öncesi) | 5.6 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C2 | Efektif iç çap | 5.319 m | PF1500 × FLS:eff_over_shell[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Silindirik gövde yüksekliği | 3.198 m | PF1500 × FLS:eff_over_shell[2] × FLS:barrel_h/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Koni yüksekliği | 5.678 m | PF1500 × FLS:eff_over_shell[2] × FLS:cone_h/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu boyu (daldırma) | 2.66 m | PF1500 × FLS:eff_over_shell[2] × FLS:vortex_len/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu çapı | 3.791 m | PF1500 × FLS:eff_over_shell[2] × FLS:vortex_D/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Toz çıkışı çapı | 0.702 m | PF1500 × FLS:eff_over_shell[2] × FLS:dust_D/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C2 | Giriş genişliği | 1.069 m | PF1500 × FLS:eff_over_shell[2] × FLS:inlet_w/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş yüksekliği | 7.594 m | PF1500 × FLS:eff_over_shell[2] × FLS:inlet_h/D[2] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş kesit alanı | — | kaynak yok | — | 1500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C3 | Çelik gövde iç çapı (Φ, astar öncesi) | 5.6 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C3 | Efektif iç çap | 5.272 m | PF1500 × FLS:eff_over_shell[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Silindirik gövde yüksekliği | 2.691 m | PF1500 × FLS:eff_over_shell[3] × FLS:barrel_h/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Koni yüksekliği | 6.076 m | PF1500 × FLS:eff_over_shell[3] × FLS:cone_h/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu boyu (daldırma) | 2.636 m | PF1500 × FLS:eff_over_shell[3] × FLS:vortex_len/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu çapı | 3.869 m | PF1500 × FLS:eff_over_shell[3] × FLS:vortex_D/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Toz çıkışı çapı | 0.702 m | PF1500 × FLS:eff_over_shell[3] × FLS:dust_D/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C3 | Giriş genişliği | 1.053 m | PF1500 × FLS:eff_over_shell[3] × FLS:inlet_w/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş yüksekliği | 7.915 m | PF1500 × FLS:eff_over_shell[3] × FLS:inlet_h/D[3] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş kesit alanı | — | kaynak yok | — | 1500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C4 | Çelik gövde iç çapı (Φ, astar öncesi) | 5.9 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C4 | Efektif iç çap | 5.537 m | PF1500 × FLS:eff_over_shell[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Silindirik gövde yüksekliği | 3.037 m | PF1500 × FLS:eff_over_shell[4] × FLS:barrel_h/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Koni yüksekliği | 6.413 m | PF1500 × FLS:eff_over_shell[4] × FLS:cone_h/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu boyu (daldırma) | 2.784 m | PF1500 × FLS:eff_over_shell[4] × FLS:vortex_len/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu çapı | 4.07 m | PF1500 × FLS:eff_over_shell[4] × FLS:vortex_D/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Toz çıkışı çapı | 0.71 m | PF1500 × FLS:eff_over_shell[4] × FLS:dust_D/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C4 | Giriş genişliği | 1.112 m | PF1500 × FLS:eff_over_shell[4] × FLS:inlet_w/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş yüksekliği | 8.296 m | PF1500 × FLS:eff_over_shell[4] × FLS:inlet_h/D[4] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş kesit alanı | — | kaynak yok | — | 1500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C5 | Çelik gövde iç çapı (Φ, astar öncesi) | 5.9 m | PF1500 | Yayınlanmış (P) | 1500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C5 | Efektif iç çap | 5.584 m | PF1500 × FLS:eff_over_shell[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Silindirik gövde yüksekliği | 3.037 m | PF1500 × FLS:eff_over_shell[5] × FLS:barrel_h/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Koni yüksekliği | 6.381 m | PF1500 × FLS:eff_over_shell[5] × FLS:cone_h/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu boyu (daldırma) | 2.792 m | PF1500 × FLS:eff_over_shell[5] × FLS:vortex_len/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu çapı | 4.07 m | PF1500 × FLS:eff_over_shell[5] × FLS:vortex_D/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Toz çıkışı çapı | 0.71 m | PF1500 × FLS:eff_over_shell[5] × FLS:dust_D/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | — |
| Siklon C5 | Giriş genişliği | 1.12 m | PF1500 × FLS:eff_over_shell[5] × FLS:inlet_w/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş yüksekliği | 8.238 m | PF1500 × FLS:eff_over_shell[5] × FLS:inlet_h/D[5] | Türetilmiş (R) | 1500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş kesit alanı | — | kaynak yok | — | 1500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 1500 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Efektif iç çap | 3.822 m | PF1500 × FLS:eff_over_shell[2] × FLS:riser_D/D_src[1] | Türetilmiş (R) | 1500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R1 (C2→C1) | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç çapı (2 r_u) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 1500 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Efektif iç çap | 3.822 m | PF1500 × FLS:eff_over_shell[3] × FLS:riser_D/D_src[2] | Türetilmiş (R) | 1500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R2 (C3→C2) | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç çapı (2 r_u) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 1500 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Efektif iç çap | 4.023 m | PF1500 × FLS:eff_over_shell[4] × FLS:riser_D/D_src[3] | Türetilmiş (R) | 1500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R3 (C4→C3) | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç çapı (2 r_u) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 1500 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Efektif iç çap | 4.023 m | PF1500 × FLS:eff_over_shell[5] × FLS:riser_D/D_src[4] | Türetilmiş (R) | 1500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R4 (C5→C4) | Boy / yükseklik | — | kaynak yok | — | 1500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç çapı (2 r_u) | — | kaynak yok | — | 1500 (boş) | Eksik | Bulunamadı; türetilmedi |

### A.2 Hat 2500 t/d — 1 dizi

| Ekipman | Parametre | Değer | Kaynak (ref) | Yayın durumu | Katalog | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|
| Hat | Kapasite | 2500 t/d | HFC2500 | Yayınlanmış (P) | 2500 | Geometri değil | — |
| Fırın | Çelik gövde iç çapı (Φ, astar öncesi) | 4 m | PF2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Fırın | Efektif iç çap | 3.633 m | PF2500 × FLS:kiln_eff_over_shell | Türetilmiş (R) | 2500 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Boy / yükseklik | 60 m | PF2500 | Yayınlanmış (P) | 2500 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Eğim | 4 % | PF2500 | Yayınlanmış (P) | 2500 | Kule dışı — fırın ekseni eğimi | — |
| Fırın | Dönüş hızı, min | 0.39 rpm | PF2500 | Yayınlanmış (P) | 2500 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, max | 4.1 rpm | PF2500 | Yayınlanmış (P) | 2500 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, işletme | — | kaynak yok | — | 2500 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Izgara alanı | 65 m² | PF2500 | Yayınlanmış (P) | 2500 | Tek başına yetersiz (L×W yok) | — |
| Soğutucu | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Genişlik | — | kaynak yok | — | 2500 (boş) | — | Bulunamadı; türetilmedi |
| Kalsinatör | Çelik gövde iç çapı (Φ, astar öncesi) | 6 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Kalsinatör | Efektif iç çap | 5.5 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — kalsinatör katısı | — |
| Kalsinatör | Boy / yükseklik | 29.464 m | HFC2500 × FLS:calciner_H/D | Türetilmiş (R) | 2500 | Evet — kalsinatör katısı | — |
| Kaz boynu | Çelik gövde iç çapı (Φ, astar öncesi) | 4 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Kaz boynu | Efektif iç çap | 3.5 m | HFC2500 | Yayınlanmış (P) | 2500 | Kısmen — yalnızca kesit (boy yok) | — |
| Kaz boynu | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Siklon C1 | Çelik gövde iç çapı (Φ, astar öncesi) | 4.7 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C1 | Efektif iç çap | 4.32 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — tek siklon katısı | — |
| Siklon C1 | Silindirik gövde yüksekliği | 6.793 m | HFC2500 × FLS:barrel_h/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Koni yüksekliği | 4.652 m | HFC2500 × FLS:cone_h/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu boyu (daldırma) | 2.16 m | HFC2500 × FLS:vortex_len/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu çapı | 2.404 m | HFC2500 × FLS:vortex_D/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Toz çıkışı çapı | 0.401 m | HFC2500 × FLS:dust_D/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Giriş genişliği | 0.864 m | HFC2500 × FLS:inlet_w/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Giriş yüksekliği | 4.968 m | HFC2500 × FLS:inlet_h/D[1] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Giriş kesit alanı | — | kaynak yok | — | 2500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C2 | Çelik gövde iç çapı (Φ, astar öncesi) | 6.6 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C2 | Efektif iç çap | 6.1 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Silindirik gövde yüksekliği | 3.667 m | HFC2500 × FLS:barrel_h/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Koni yüksekliği | 6.511 m | HFC2500 × FLS:cone_h/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu boyu (daldırma) | 3.05 m | HFC2500 × FLS:vortex_len/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu çapı | 4.347 m | HFC2500 × FLS:vortex_D/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Toz çıkışı çapı | 0.805 m | HFC2500 × FLS:dust_D/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C2 | Giriş genişliği | 1.225 m | HFC2500 × FLS:inlet_w/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş yüksekliği | 8.709 m | HFC2500 × FLS:inlet_h/D[2] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş kesit alanı | — | kaynak yok | — | 2500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C3 | Çelik gövde iç çapı (Φ, astar öncesi) | 6.8 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C3 | Efektif iç çap | 6.3 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Silindirik gövde yüksekliği | 3.215 m | HFC2500 × FLS:barrel_h/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Koni yüksekliği | 7.26 m | HFC2500 × FLS:cone_h/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu boyu (daldırma) | 3.15 m | HFC2500 × FLS:vortex_len/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu çapı | 4.622 m | HFC2500 × FLS:vortex_D/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Toz çıkışı çapı | 0.839 m | HFC2500 × FLS:dust_D/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C3 | Giriş genişliği | 1.258 m | HFC2500 × FLS:inlet_w/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş yüksekliği | 9.458 m | HFC2500 × FLS:inlet_h/D[3] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş kesit alanı | — | kaynak yok | — | 2500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C4 | Çelik gövde iç çapı (Φ, astar öncesi) | 6.8 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C4 | Efektif iç çap | 6.3 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Silindirik gövde yüksekliği | 3.455 m | HFC2500 × FLS:barrel_h/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Koni yüksekliği | 7.296 m | HFC2500 × FLS:cone_h/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu boyu (daldırma) | 3.168 m | HFC2500 × FLS:vortex_len/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu çapı | 4.631 m | HFC2500 × FLS:vortex_D/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Toz çıkışı çapı | 0.808 m | HFC2500 × FLS:dust_D/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C4 | Giriş genişliği | 1.265 m | HFC2500 × FLS:inlet_w/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş yüksekliği | 9.439 m | HFC2500 × FLS:inlet_h/D[4] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş kesit alanı | — | kaynak yok | — | 2500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C5 | Çelik gövde iç çapı (Φ, astar öncesi) | 7 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C5 | Efektif iç çap | 6.5 m | HFC2500 | Yayınlanmış (P) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Silindirik gövde yüksekliği | 3.535 m | HFC2500 × FLS:barrel_h/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Koni yüksekliği | 7.427 m | HFC2500 × FLS:cone_h/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu boyu (daldırma) | 3.25 m | HFC2500 × FLS:vortex_len/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu çapı | 4.737 m | HFC2500 × FLS:vortex_D/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Toz çıkışı çapı | 0.826 m | HFC2500 × FLS:dust_D/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | — |
| Siklon C5 | Giriş genişliği | 1.304 m | HFC2500 × FLS:inlet_w/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş yüksekliği | 9.588 m | HFC2500 × FLS:inlet_h/D[5] | Türetilmiş (R) | 2500 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş kesit alanı | — | kaynak yok | — | 2500 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ, astar öncesi) | 3.45 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R1 (C2→C1) | Efektif iç çap | 3.07 m | HFC2500 | Yayınlanmış (P) | 2500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R1 (C2→C1) | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç çapı (2 r_u) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ, astar öncesi) | 3.85 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R2 (C3→C2) | Efektif iç çap | 3.35 m | HFC2500 | Yayınlanmış (P) | 2500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R2 (C3→C2) | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç çapı (2 r_u) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ, astar öncesi) | 3.95 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R3 (C4→C3) | Efektif iç çap | 3.45 m | HFC2500 | Yayınlanmış (P) | 2500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R3 (C4→C3) | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç çapı (2 r_u) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ, astar öncesi) | 4.1 m | HFC2500 | Yayınlanmış (P) | 2500 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R4 (C5→C4) | Efektif iç çap | 3.6 m | HFC2500 | Yayınlanmış (P) | 2500 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R4 (C5→C4) | Boy / yükseklik | — | kaynak yok | — | 2500 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç çapı (2 r_u) | — | kaynak yok | — | 2500 (boş) | Eksik | Bulunamadı; türetilmedi |

### A.3 Hat 5000 t/d — 2 dizi

| Ekipman | Parametre | Değer | Kaynak (ref) | Yayın durumu | Katalog | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|
| Hat | Kapasite | 5000 t/d | PF5000 | Yayınlanmış (P) | 5000 | Geometri değil | — |
| Fırın | Çelik gövde iç çapı (Φ, astar öncesi) | 4.8 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Fırın | Efektif iç çap | 4.36 m | PF5000 × FLS:kiln_eff_over_shell | Türetilmiş (R) | 5000 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Boy / yükseklik | 74 m | PF5000 | Yayınlanmış (P) | 5000 | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Eğim | 4 % | PF5000 | Yayınlanmış (P) | 5000 | Kule dışı — fırın ekseni eğimi | — |
| Fırın | Dönüş hızı, min | 0.6 rpm | PF5000 | Yayınlanmış (P) | 5000 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, max | 4 rpm | PF5000 | Yayınlanmış (P) | 5000 | Geometri değil — duvar hareketi sınır koşulu | — |
| Fırın | Dönüş hızı, işletme | — | kaynak yok | — | 5000 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Izgara alanı | 119.6 m² | PF5000 | Yayınlanmış (P) | 5000 | Tek başına yetersiz (L×W yok) | — |
| Soğutucu | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Genişlik | — | kaynak yok | — | 5000 (boş) | — | Bulunamadı; türetilmedi |
| Kalsinatör | Çelik gövde iç çapı (Φ, astar öncesi) | 7.2 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Kalsinatör | Efektif iç çap | 6.74 m | PF5000 × FLS:calciner_eff_over_shell | Türetilmiş (R) | 5000 | Evet — kalsinatör katısı | — |
| Kalsinatör | Boy / yükseklik | 30 m | PF5000 | Yayınlanmış (P) | 5000 | Evet — kalsinatör katısı | — |
| Kaz boynu | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 5000 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Kaz boynu | Efektif iç çap | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Kaz boynu | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Siklon C1 | Çelik gövde iç çapı (Φ, astar öncesi) | 5 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C1 | Efektif iç çap | 4.805 m | PF5000 × FLS:eff_over_shell[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Silindirik gövde yüksekliği | 7.556 m | PF5000 × FLS:eff_over_shell[1] × FLS:barrel_h/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Koni yüksekliği | 5.174 m | PF5000 × FLS:eff_over_shell[1] × FLS:cone_h/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu boyu (daldırma) | 2.403 m | PF5000 × FLS:eff_over_shell[1] × FLS:vortex_len/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Vorteks bulucu çapı | 2.674 m | PF5000 × FLS:eff_over_shell[1] × FLS:vortex_D/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Toz çıkışı çapı | 0.446 m | PF5000 × FLS:eff_over_shell[1] × FLS:dust_D/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| Siklon C1 | Giriş genişliği | 0.961 m | PF5000 × FLS:eff_over_shell[1] × FLS:inlet_w/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in FLS model varsayımına dayanır |
| Siklon C1 | Giriş yüksekliği | 5.526 m | PF5000 × FLS:eff_over_shell[1] × FLS:inlet_h/D[1] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in FLS model varsayımına dayanır |
| Siklon C1 | Giriş kesit alanı | — | kaynak yok | — | 5000 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C2 | Çelik gövde iç çapı (Φ, astar öncesi) | 6.9 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C2 | Efektif iç çap | 6.554 m | PF5000 × FLS:eff_over_shell[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Silindirik gövde yüksekliği | 3.94 m | PF5000 × FLS:eff_over_shell[2] × FLS:barrel_h/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Koni yüksekliği | 6.996 m | PF5000 × FLS:eff_over_shell[2] × FLS:cone_h/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu boyu (daldırma) | 3.277 m | PF5000 × FLS:eff_over_shell[2] × FLS:vortex_len/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu çapı | 4.67 m | PF5000 × FLS:eff_over_shell[2] × FLS:vortex_D/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Toz çıkışı çapı | 0.865 m | PF5000 × FLS:eff_over_shell[2] × FLS:dust_D/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C2 | Giriş genişliği | 1.317 m | PF5000 × FLS:eff_over_shell[2] × FLS:inlet_w/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş yüksekliği | 9.358 m | PF5000 × FLS:eff_over_shell[2] × FLS:inlet_h/D[2] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C2 | Giriş kesit alanı | — | kaynak yok | — | 5000 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C3 | Çelik gövde iç çapı (Φ, astar öncesi) | 6.9 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C3 | Efektif iç çap | 6.496 m | PF5000 × FLS:eff_over_shell[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Silindirik gövde yüksekliği | 3.315 m | PF5000 × FLS:eff_over_shell[3] × FLS:barrel_h/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Koni yüksekliği | 7.486 m | PF5000 × FLS:eff_over_shell[3] × FLS:cone_h/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu boyu (daldırma) | 3.248 m | PF5000 × FLS:eff_over_shell[3] × FLS:vortex_len/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu çapı | 4.767 m | PF5000 × FLS:eff_over_shell[3] × FLS:vortex_D/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Toz çıkışı çapı | 0.865 m | PF5000 × FLS:eff_over_shell[3] × FLS:dust_D/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C3 | Giriş genişliği | 1.297 m | PF5000 × FLS:eff_over_shell[3] × FLS:inlet_w/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş yüksekliği | 9.752 m | PF5000 × FLS:eff_over_shell[3] × FLS:inlet_h/D[3] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C3 | Giriş kesit alanı | — | kaynak yok | — | 5000 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C4 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.2 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C4 | Efektif iç çap | 6.757 m | PF5000 × FLS:eff_over_shell[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Silindirik gövde yüksekliği | 3.706 m | PF5000 × FLS:eff_over_shell[4] × FLS:barrel_h/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Koni yüksekliği | 7.826 m | PF5000 × FLS:eff_over_shell[4] × FLS:cone_h/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu boyu (daldırma) | 3.398 m | PF5000 × FLS:eff_over_shell[4] × FLS:vortex_len/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu çapı | 4.967 m | PF5000 × FLS:eff_over_shell[4] × FLS:vortex_D/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Toz çıkışı çapı | 0.866 m | PF5000 × FLS:eff_over_shell[4] × FLS:dust_D/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C4 | Giriş genişliği | 1.357 m | PF5000 × FLS:eff_over_shell[4] × FLS:inlet_w/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş yüksekliği | 10.124 m | PF5000 × FLS:eff_over_shell[4] × FLS:inlet_h/D[4] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C4 | Giriş kesit alanı | — | kaynak yok | — | 5000 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Siklon C5 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.2 m | PF5000 | Yayınlanmış (P) | 5000 | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C5 | Efektif iç çap | 6.815 m | PF5000 × FLS:eff_over_shell[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Silindirik gövde yüksekliği | 3.706 m | PF5000 × FLS:eff_over_shell[5] × FLS:barrel_h/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Koni yüksekliği | 7.787 m | PF5000 × FLS:eff_over_shell[5] × FLS:cone_h/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu boyu (daldırma) | 3.407 m | PF5000 × FLS:eff_over_shell[5] × FLS:vortex_len/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu çapı | 4.967 m | PF5000 × FLS:eff_over_shell[5] × FLS:vortex_D/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Toz çıkışı çapı | 0.866 m | PF5000 × FLS:eff_over_shell[5] × FLS:dust_D/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | — |
| Siklon C5 | Giriş genişliği | 1.367 m | PF5000 × FLS:eff_over_shell[5] × FLS:inlet_w/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş yüksekliği | 10.053 m | PF5000 × FLS:eff_over_shell[5] × FLS:inlet_h/D[5] | Türetilmiş (R) | 5000 | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır |
| Siklon C5 | Giriş kesit alanı | — | kaynak yok | — | 5000 (boş) | Kontrol amaçlı (w×h ile tutarlılık) | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 5000 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Efektif iç çap | 4.709 m | PF5000 × FLS:eff_over_shell[2] × FLS:riser_D/D_src[1] | Türetilmiş (R) | 5000 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R1 (C2→C1) | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R1 (C2→C1) | Uç çapı (2 r_u) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 5000 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Efektif iç çap | 4.709 m | PF5000 × FLS:eff_over_shell[3] × FLS:riser_D/D_src[2] | Türetilmiş (R) | 5000 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R2 (C3→C2) | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R2 (C3→C2) | Uç çapı (2 r_u) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 5000 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Efektif iç çap | 4.909 m | PF5000 × FLS:eff_over_shell[4] × FLS:riser_D/D_src[3] | Türetilmiş (R) | 5000 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R3 (C4→C3) | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R3 (C4→C3) | Uç çapı (2 r_u) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | 5000 (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Efektif iç çap | 4.909 m | PF5000 × FLS:eff_over_shell[5] × FLS:riser_D/D_src[4] | Türetilmiş (R) | 5000 | Kısmen — yalnızca kesit (boy/şekil yok) | — |
| Riser R4 (C5→C4) | Boy / yükseklik | — | kaynak yok | — | 5000 (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç konisi boyu (h_cl) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |
| Riser R4 (C5→C4) | Uç çapı (2 r_u) | — | kaynak yok | — | 5000 (boş) | Eksik | Bulunamadı; türetilmedi |

### A.4 Hat FLS (FLS referans kulesi) — 1 dizi

| Ekipman | Parametre | Değer | Kaynak (ref) | Yayın durumu | Katalog | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|
| Hat | Kapasite | — | kaynak yok | — | FLS (boş) | Geometri değil | Bulunamadı; türetilmedi |
| Fırın | Çelik gövde iç çapı (Φ, astar öncesi) | 4.36 m | FLS: 2 r_r[kiln] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Fırın | Efektif iç çap | 3.96 m | FLS: 2 r_c[kiln] | Yayınlanmış (P) | FLS | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Boy / yükseklik | 51 m | FLS: L[kiln] | Yayınlanmış (P) | FLS | Kule dışı — fırın hacmi için kullanılabilir (builder yok) | — |
| Fırın | Eğim | — | kaynak yok | — | FLS (boş) | — | Bulunamadı; türetilmedi |
| Fırın | Dönüş hızı, min | — | kaynak yok | — | FLS (boş) | — | Bulunamadı; türetilmedi |
| Fırın | Dönüş hızı, max | — | kaynak yok | — | FLS (boş) | — | Bulunamadı; türetilmedi |
| Fırın | Dönüş hızı, işletme | 4 rpm | FLS: kiln rotation, scenario text | Yayınlanmış (P) | FLS | Geometri değil — duvar hareketi sınır koşulu | — |
| Soğutucu | Izgara alanı | — | kaynak yok | — | FLS (boş) | — | Bulunamadı; türetilmedi |
| Soğutucu | Boy / yükseklik | 36 m | FLS: L[cooler] | Yayınlanmış (P) | FLS | Kısmen — soğutucu kutusu (builder yok) | — |
| Soğutucu | Genişlik | 4 m | FLS: w[cooler] | Yayınlanmış (P) | FLS | Kısmen — soğutucu kutusu (builder yok) | — |
| Kalsinatör | Çelik gövde iç çapı (Φ, astar öncesi) | 6.58 m | FLS: 2 r_r[calciner] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Kalsinatör | Efektif iç çap | 6.16 m | FLS: 2 r_c[calciner] | Yayınlanmış (P) | FLS | Evet — kalsinatör katısı | — |
| Kalsinatör | Boy / yükseklik | 33 m | FLS: h_tot[calciner] | Yayınlanmış (P) | FLS | Evet — kalsinatör katısı | — |
| Kaz boynu | Çelik gövde iç çapı (Φ, astar öncesi) | — | kaynak yok | — | FLS (boş) | Doğrudan değil — akışkan hacmi efektif çapla kurulur | Bulunamadı; türetilmedi |
| Kaz boynu | Efektif iç çap | — | kaynak yok | — | FLS (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Kaz boynu | Boy / yükseklik | — | kaynak yok | — | FLS (boş) | Eksik — kule kurulamaz | Bulunamadı; türetilmedi |
| Siklon C1 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.18 m | FLS: 2 r_r[Cy1] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C1 | Efektif iç çap | 6.9 m | FLS: 2 r_c[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Silindirik gövde yüksekliği | 10.85 m | FLS: h_t - h_c[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Koni yüksekliği | 7.43 m | FLS: h_c[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Vorteks bulucu boyu (daldırma) | 3.45 m | FLS: h_x[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Vorteks bulucu çapı | 3.84 m | FLS: 2 r_x[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Toz çıkışı çapı | 0.64 m | FLS: 2 r_d[Cy1] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C1 | Giriş genişliği | 1.38 m | FLS: w_in[Cy1] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C1 | Giriş yüksekliği | 7.935 m | FLS: A_in / w_in[Cy1] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C1 | Giriş kesit alanı | 10.95 m² | FLS: A_in[Cy1] | Yayınlanmış (P) | FLS | Kontrol amaçlı (w×h ile tutarlılık) | — |
| Siklon C2 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.18 m | FLS: 2 r_r[Cy2] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C2 | Efektif iç çap | 6.82 m | FLS: 2 r_c[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Silindirik gövde yüksekliği | 4.1 m | FLS: h_t - h_c[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Koni yüksekliği | 7.28 m | FLS: h_c[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu boyu (daldırma) | 3.41 m | FLS: h_x[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Vorteks bulucu çapı | 4.86 m | FLS: 2 r_x[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Toz çıkışı çapı | 0.9 m | FLS: 2 r_d[Cy2] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C2 | Giriş genişliği | 1.37 m | FLS: w_in[Cy2] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C2 | Giriş yüksekliği | 9.737 m | FLS: A_in / w_in[Cy2] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C2 | Giriş kesit alanı | 13.34 m² | FLS: A_in[Cy2] | Yayınlanmış (P) | FLS | Kontrol amaçlı (w×h ile tutarlılık) | — |
| Siklon C3 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.18 m | FLS: 2 r_r[Cy3] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C3 | Efektif iç çap | 6.76 m | FLS: 2 r_c[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Silindirik gövde yüksekliği | 3.45 m | FLS: h_t - h_c[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Koni yüksekliği | 7.79 m | FLS: h_c[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu boyu (daldırma) | 3.38 m | FLS: h_x[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Vorteks bulucu çapı | 4.96 m | FLS: 2 r_x[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Toz çıkışı çapı | 0.9 m | FLS: 2 r_d[Cy3] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C3 | Giriş genişliği | 1.35 m | FLS: w_in[Cy3] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C3 | Giriş yüksekliği | 10.148 m | FLS: A_in / w_in[Cy3] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C3 | Giriş kesit alanı | 13.7 m² | FLS: A_in[Cy3] | Yayınlanmış (P) | FLS | Kontrol amaçlı (w×h ile tutarlılık) | — |
| Siklon C4 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.48 m | FLS: 2 r_r[Cy4] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C4 | Efektif iç çap | 7.02 m | FLS: 2 r_c[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Silindirik gövde yüksekliği | 3.85 m | FLS: h_t - h_c[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Koni yüksekliği | 8.13 m | FLS: h_c[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu boyu (daldırma) | 3.53 m | FLS: h_x[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Vorteks bulucu çapı | 5.16 m | FLS: 2 r_x[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Toz çıkışı çapı | 0.9 m | FLS: 2 r_d[Cy4] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C4 | Giriş genişliği | 1.41 m | FLS: w_in[Cy4] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C4 | Giriş yüksekliği | 10.518 m | FLS: A_in / w_in[Cy4] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C4 | Giriş kesit alanı | 14.83 m² | FLS: A_in[Cy4] | Yayınlanmış (P) | FLS | Kontrol amaçlı (w×h ile tutarlılık) | — |
| Siklon C5 | Çelik gövde iç çapı (Φ, astar öncesi) | 7.48 m | FLS: 2 r_r[Cy5] | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Siklon C5 | Efektif iç çap | 7.08 m | FLS: 2 r_c[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Silindirik gövde yüksekliği | 3.85 m | FLS: h_t - h_c[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Koni yüksekliği | 8.09 m | FLS: h_c[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu boyu (daldırma) | 3.54 m | FLS: h_x[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Vorteks bulucu çapı | 5.16 m | FLS: 2 r_x[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Toz çıkışı çapı | 0.9 m | FLS: 2 r_d[Cy5] | Yayınlanmış (P) | FLS | Evet — tek siklon katısı | — |
| Siklon C5 | Giriş genişliği | 1.42 m | FLS: w_in[Cy5] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C5 | Giriş yüksekliği | 10.444 m | FLS: A_in / w_in[Cy5] | Model varsayımı (M) | FLS | Evet — tek siklon katısı | w_in FLS model varsayımına dayanır; w_in = 0.4 r_c makalenin varsayımı |
| Siklon C5 | Giriş kesit alanı | 14.83 m² | FLS: A_in[Cy5] | Yayınlanmış (P) | FLS | Kontrol amaçlı (w×h ile tutarlılık) | — |
| Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ, astar öncesi) | 4.94 m | FLS: 2 r_r[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R1 (C2→C1) | Efektif iç çap | 4.9 m | FLS: 2 r_c[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Kısmen — kesit; riser şekli belirsiz | — |
| Riser R1 (C2→C1) | Boy / yükseklik | 21.38 m | FLS: h_tot[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R1 (C2→C1) | Uç konisi boyu (h_cl) | 4.83 m | FLS: h_cl[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R1 (C2→C1) | Uç çapı (2 r_u) | 3.44 m | FLS: 2 r_u[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ, astar öncesi) | 4.94 m | FLS: 2 r_r[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R2 (C3→C2) | Efektif iç çap | 4.9 m | FLS: 2 r_c[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Kısmen — kesit; riser şekli belirsiz | — |
| Riser R2 (C3→C2) | Boy / yükseklik | 19.38 m | FLS: h_tot[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R2 (C3→C2) | Uç konisi boyu (h_cl) | 4.18 m | FLS: h_cl[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R2 (C3→C2) | Uç çapı (2 r_u) | 3.8 m | FLS: 2 r_u[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ, astar öncesi) | 5.14 m | FLS: 2 r_r[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R3 (C4→C3) | Efektif iç çap | 5.1 m | FLS: 2 r_c[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Kısmen — kesit; riser şekli belirsiz | — |
| Riser R3 (C4→C3) | Boy / yükseklik | 20.37 m | FLS: h_tot[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R3 (C4→C3) | Uç konisi boyu (h_cl) | 4.18 m | FLS: h_cl[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R3 (C4→C3) | Uç çapı (2 r_u) | 3.8 m | FLS: 2 r_u[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ, astar öncesi) | 5.14 m | FLS: 2 r_r[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Doğrudan değil — akışkan hacmi efektif çapla kurulur | — |
| Riser R4 (C5→C4) | Efektif iç çap | 5.1 m | FLS: 2 r_c[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Kısmen — kesit; riser şekli belirsiz | — |
| Riser R4 (C5→C4) | Boy / yükseklik | 19.87 m | FLS: h_tot[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R4 (C5→C4) | Uç konisi boyu (h_cl) | 4.37 m | FLS: h_cl[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |
| Riser R4 (C5→C4) | Uç çapı (2 r_u) | 3.98 m | FLS: 2 r_u[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | Yayınlanmış (P) | FLS | Hayır — riser şekli belirsiz (SOURCES.md) | Tablo 8 sütun anlamı metin/denklemlerle çelişik |

---

## B. Araştırmada bulunan, katalog dışında bırakılan ölçüler

### B.0 Bu bölümde yeni geçen kaynaklar

| ID | Kaynak | Tesis |
|---|---|---|
| **RSP1500** | [RSP预分解窑生产线改造设计](https://m.ccement.com/news/content/700902.html) | Kuzeydoğu Çin'de "HS" şirketi. 1990'larda kurulmuş 1000 t/d kapasiteli RSP hattı, 1500 t/d'ye göre yeniden tasarlanmış; fiilen ortalama 1400, en fazla 1600 t/d. Gerçek tesis, genişletme projesi. |
| **TCDRI5000** | [预分解窑烧成系统的技改](http://www.pengfei.com.cn/pengfei/News/Technical_News/2017/0329/2676.html) (Pengfei, 2017) | Tianjin enstitüsü tasarımı 5000 t/d hat: çift dizi, 5 kademe, DD kalsinatör, 2004'te devreye alınmış, fiilen 5900 t/d. Gerçek tesis, genişletme projesi. |
| **FLS-T8** | arXiv 2504.02886 v1, Tablo 8 | Katalogdaki FLS kaynağıyla aynı tablo; burada katalogda kullanılmayan sütunlar listeleniyor. |
| **FLS-Cy** | arXiv 2409.10916, Tablo II | FLS siklon tablosunun yuvarlatılmış hali. |
| **FLS-Ca** | arXiv 2405.03208 (kalsinatör makalesi) | FLS kalsinatörü. |
| **HB** | Holderbank Cement Seminar 2000 ([Suspension preheater](https://archive.org/stream/HolderbankCementEngineeringBook/Pg_2038-2059_suspensionPreheater_djvu.txt), [Kiln systems](https://archive.org/download/HolderbankCementEngineeringBook/Pg_1992-2025_kilnSystems-Overview_djvu.txt)) | Tasarım kılavuzu; OCR metni. |
| **LCDRI** | [lcdri.cn/xx/437](https://www.lcdri.cn/xx/437.html) | Luoyang tasarım enstitüsünün standart hatları. |
| **AGICO-R** | [AGICO 2500 retrofit](https://cementplantequipment.com/2500-tons-clinker-plant-retrofit-project/) | 2500 t/d tasarımlı tesis, 3000 t/d'ye büyütülmüş. |
| **GUIGANG** | [sohu 169371785](https://www.sohu.com/a/169371785_771169) | Guigang 2500 t/d hattı, TDF kalsinatörden TTF'ye dönüştürülmüş. |
| **AGICO-K** | [AGICO rotary kiln revamp](https://cement-plants.com/rotary-kiln-revamp-project/) | 5000 t/d tesis, 6330 t/d'ye büyütülmüş. |
| Diğerleri | Kayıt satırında bağlantısıyla verildi | |

### B.1 Ham metni benim doğruladığım ölçüler (H-ben)

| Hat/tesis | Ekipman | Parametre | Değer | Kaynak | Yayın durumu | Katalog | Neden atanmadı | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|---|---|
| PF2500 | Siklon C1 | Gövde çapı | 2 × Φ4.6 m | PF2500 | P | — | 2500 önısıtıcısı, efektif çapları da yayınlayan HFC2500'den alındı | Hayır (efektif çap yok) | HFC değerinden en fazla %2 farklı |
| PF2500 | Siklon C2 / C3 | Gövde çapı | Φ6.5 / Φ6.5 m | PF2500 | P | — | Aynı gerekçe | Hayır | — |
| PF2500 | Siklon C4 / C5 | Gövde çapı | Φ6.8 / Φ6.8 m | PF2500 | P | — | Aynı gerekçe | Hayır | — |
| PF2500 | Kalsinatör | Φ × H | 5.05 × 30.0 m | PF2500 | P | — | Kalsinatör HFC2500'den alındı (Φ6.0 gövde / Φ5.5 efektif). Pengfei'ninki farklı bir kalsinatör | Hayır (tasarımı farklı) | HFC kalsinatörünün yüksekliği katalogda R olarak 29.46 m. Bu 30 m ile yakın, ama ekipman aynı değil. |
| PF2500 | Soğutucu | Model | LBT32216 (başka bir Pengfei sayfasında LBT2500, 65 m²) | [Pengfei 2500](http://www.cementplant-engineering.com/products/cement-production-line/76.html) | P | — | Alan değil, model adı | Hayır | İki Pengfei sayfası farklı soğutucu modeli veriyor |
| RSP1500 | Siklon C1 | Çap, genişletme öncesi → sonrası | φ3.1 → φ3.7 m | RSP1500 | P | — | Başka tesis (RSP), genişletme parçası | Kısmen: yalnızca tek çap | Gövde mi efektif mi, belirtilmemiş |
| RSP1500 | Siklon C1–C5 | Vorteks bulucu (内筒) çapı, sonrası | C1 1.736, C2 2.484, C3 2.621, C4 2.701, C5 2.770 m | RSP1500 | P | — | Başka tesis; bu tesisin C2–C5 gövde çapları yayınlanmamış | Hayır (siklonun geri kalanı yok) | — |
| RSP1500 | Siklon C1–C5 | Vorteks bulucu çapı / efektif çap | Sonrası: C1 0.46, C2 0.60, C3 0.63, C4 0.66, C5 0.62. Öncesi: C1 0.46, C2–C5 0.50–0.52 | RSP1500 | P | — | Katalog FLS dışında oran kabul etmiyor (kural 2) | Hayır | FLS oranlarından (0.56–0.74) belirgin biçimde küçük |
| RSP1500 | Kalsinatör (MC odası) | Φ × H, hacim | φ4.3 × 13 m, 188 m³ | RSP1500 | P | — | Başka tesis, RSP tipi kalsinatör | Hayır | Genişletme öncesi değer |
| RSP1500 | Kalsinatör | Alt boğaz kesiti, öncesi → sonrası | 0.9 × 0.9 → 1.11 × 1.11 m | RSP1500 | P | — | Başka tesis | Hayır | Bulunan **tek kalsinatör giriş boğazı ölçüsü** |
| RSP1500 | Kaz boynu | Φ × L | φ3.1 × 31 m | RSP1500 | P | — | Başka tesisin genişletme parçası. PF1500'ün kalsinatörü CDC tipi, Φ6.3 | Hayır | Gövde mi efektif mi belirtilmemiş. 31 m'nin tüm borunun ekseni mi düz bir parça mı olduğu belirsiz. |
| RSP1500 | Kalsinatör + kaz boynu | Hacim | 422 m³ | RSP1500 | P | — | Aynı gerekçe | Hayır | — |
| RSP1500 | Tersiyer hava kanalı | Efektif iç çap | φ1577 mm, yatay yerleşim | RSP1500 | P | — | Tersiyer kanal kapsam dışı (Kararlar, 3) | Hayır | Genişletmede yeniden döşenmiş |
| RSP1500 | Fırın besleme bacası (下料竖井) | Kesit | 6.4 × 2.96 m | RSP1500 | P | — | Kulede fırın giriş odası yok; başka tesis | Hayır | Bulunan **tek fırın girişi ölçüsü** |
| RSP1500 | Fırın başlığı | Kesit | 6.4 × 3.77 m | RSP1500 | P | — | Kapsam dışı ekipman | Hayır | — |
| RSP1500 | Kalsinatör kömür hattı | Taşıma borusu / meme çapı | φ214 / φ151 mm (öncesi φ480) | RSP1500 | P | — | Yakıt enjeksiyonu kapsam dışı | Hayır | Kaynak bu değerleri kendi formülüyle hesaplamış |
| TCDRI5000 | Fırın | Φ × L | Ф4.8 × 72 m | TCDRI5000 | P | — | PF5000'den (Φ4.8 × 74) farklı bir tesis | Hayır | — |
| TCDRI5000 | Soğutucu | Izgara alanı | 119.3 m² | TCDRI5000 | P | — | Farklı tesis | Hayır | Metinde "119.3m", ² işareti HTML'de kaybolmuş |
| TCDRI5000 | Kalsinatör | Düz gövde yüksekliği; yükseltme | 22 m; +12.5 m | TCDRI5000 | P | — | Farklı tesis, DD tipi kalsinatör | Hayır | Çap yayınlanmamış |
| TCDRI5000 | Kalsinatör | Düz gövde hacmi, öncesi → sonrası | 823 → 1290 m³ | TCDRI5000 | P | — | Aynı gerekçe | Hayır | — |
| TCDRI5000 | Kalsinatör çıkışı | Yükseltme sonrası konum | ≈13 m yukarı | TCDRI5000 | P | — | Aynı gerekçe | Hayır | — |
| TCDRI5000 | Kaz boynu | Kesit; toplam yükseklik; hacim | 5.4 × 4.4 m dikdörtgen; 18 m; 330 m³ | TCDRI5000 | P | — | Farklı tesis. Kesit dikdörtgen; boyu çelik taşıyıcı kirişlerine göre belirlenmiş | Hayır | Özgün tasarımda kaz boynu yok |
| TCDRI5000 | Kalsinatör + kaz boynu | Hacim | 1620 m³ | TCDRI5000 | P | — | Aynı gerekçe | Hayır | — |
| TCDRI5000 | Kalsinatör → C5 (özgün) | Bağlantı biçimi | Yatay kanal ("平管道"), ölçü yok | TCDRI5000 | P (nitel) | — | Ölçü yok | Hayır | — |
| TCDRI5000 | Tersiyer hava kanalı | Çerçeve içindeki yatay boy; dirsek sayısı | 34.4 m; 4 × 90° | TCDRI5000 | P | — | Tersiyer kanal kapsam dışı | Hayır | Kanalın çapı yok |
| TCDRI5000 | Tersiyer girişi | Kalsinatörde kapladığı yükseklik | Düz gövdede ≈3 m; eski giriş koninin üstünde 2.3 m | TCDRI5000 | P | — | Kapsam dışı | Hayır | — |
| TCDRI5000 | Siklon C5 volüt | Biçim; eksantriklik; giriş efektif kesiti | 270°, üç merkezli, eşit yükseklikli koni; 450 mm; 8.1 m² (özgün) | TCDRI5000 | P | — | Farklı tesis. Katalogda volüt modellenmiyor | Hayır | Bulunan **tek volüt ölçüsü** |
| FLS-T8 | Siklon Cy1–Cy5 | Duvar dış yarıçapı r_w | 3.60, 3.60, 3.60, 3.75, 3.75 m | FLS-T8 | P | — | Katalog yalnızca r_c (efektif) ve r_r'yi (gövde) kullanıyor | Hayır (hacmin dışında) | — |
| FLS-T8 | Siklon Cy1–Cy5 | Giriş ekseninin yarıçapı r_in | 2.76, 2.73, 2.70, 2.82, 2.83 m | FLS-T8 | P | — | r_c − w_in/2'ye eşit, yani w_in model varsayımına bağlı; bileşen katısı girişi duvara teğet kuruyor | Hayır (kurulan katıyla tutarlı) | — |
| FLS-T8 | Siklon Cy1–Cy5 | l_in | 0.1 m (hepsi) | FLS-T8 | P | — | Anlamı makalede tanımlanmamış | Hayır | Belirsiz |
| FLS-Cy | Siklon | Duvar kalınlığı | 0.008 m | FLS-Cy | P | — | Çelik duvar; akışkan hacminin dışında | Hayır | Vorteks bulucu duvarı değil |
| FLS-T8 | Riser R1–R4 | Duvar dış yarıçapı r_w | 2.48, 2.48, 2.58, 2.58 m | FLS-T8 | P | — | Hacmin dışında | Hayır | — |
| FLS-T8 | Riser R1–R4 | r_l | 2.45 m (hepsi) | FLS-T8 | P | — | Riser şekli belirsiz | Hayır | R3 ve R4'te r_l, r_c'den (2.55) küçük |
| FLS-T8 | Riser R1–R4 | h_cu | 0 | FLS-T8 | P | — | Sütun anlamı çelişik | Hayır | Tanımına göre denklem (34a)'da sıfıra bölme ortaya çıkıyor |
| FLS-T8 | R5 | h_tot, h_cl, h_cu, r_c, r_r, r_w, r_l, r_u | 61.0, 61.0, 0, 1.13, 1.33, 1.34, 1.13, 1.13 m | FLS-T8 | P | — | Tablo 7'ye göre soğutucudan kalsinatöre gidiyor; metin tersiyer boru olduğunu ima ediyor ama açıkça söylemiyor. Tersiyer kanal kapsam dışı. | Hayır | Aynı sütun belirsizliği geçerli |
| FLS-T8 | Kalsinatör | h_cl, h_cu, r_w, r_l, r_u | 33.0, 0, 3.30, 3.08, 3.08 m | FLS-T8 | P | — | Katalog yalnızca D ve h_tot'u kullanıyor | Hayır | r_l = r_u = r_c, yani düz silindir. h_cl ve h_cu çelişik. |
| FLS-Ca | Kalsinatör | Refrakter kalınlığı; kabuk kalınlığı | 0.21 m; 0.01 m | FLS-Ca | P | — | Hacmin dışında | Hayır | r_r − r_c = 0.21, r_w − r_r = 0.01 ile tutarlı |
| FLS-T8 | Fırın | ψ | 2° | FLS-T8 | P | — | Anlamı tanımsız (muhtemelen eğim) | Hayır | Belirsiz |
| FLS-T8 | Soğutucu | Yükseklik h | 3 m | FLS-T8 | P | — | Soğutucu kule dışında | Kısmen (soğutucu kutusu) | — |
| FLS-T8 | Soğutucu | Çatı bölümleri A_y1–A_y4 | 12.1, 22.5, 49.0, 60.5 m² | FLS-T8 | P | — | Soğutucu kule dışında | Kısmen | Sırasıyla fırına, tersiyer boruya, çıkışı olmayan kısma ve ortama bağlı. Toplamı 144.1 m² = 36 × 4 (kendi hesabım). |
| HB | Siklon kademesi | Şekildeki "Typical figures" | "α max 25°", "β ≈ 65°" | HB | P (OCR) | — | OCR bozuk; açıların neyi gösterdiği okunamıyor | Hayır | Belirsiz |

### B.2 Ham metni araştırma ajanının okuduğu ölçüler (H-ajan)

| Hat/tesis | Ekipman | Parametre | Değer | Kaynak | Yayın durumu | Katalog | Neden atanmadı | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|---|---|
| GUIGANG 2500 | Kalsinatör | Efektif hacim, öncesi → sonrası | 393 → 611 m³ (ana gövde 533 + kanal 78) | GUIGANG | P | — | Yalnızca hacim; farklı tesis, TDF → TTF | Hayır | — |
| HB | Fırın zarfı (1500–10 000 t/d) | D; L; L/D; eğim | 3.5–6.2 m; 40–105 m; 10–16; %3.5–4 | HB | P (aralık) | — | Tasarım aralığı, tek bir ekipmanın ölçüsü değil | Hayır | OCR metni |

### B.3 Yalnızca özetten ya da arama parçacığından gelen ölçüler (**doğrulanmadı**)

Bu değerler yalnızca aramanın izini kaydetmek için listelenmiştir. **Hiçbiri katalog adayı değildir.** Ham kaynak metni okunup doğrulanmadan hiçbir hesapta ya da geometride kullanılmaz.

| Hat/tesis | Ekipman | Parametre | Değer | Kaynak | Yayın durumu | Katalog | Neden atanmadı | CFD kullanımı | Belirsizlik / not |
|---|---|---|---|---|---|---|---|---|---|
| LCDRI 1500 | Fırın; soğutucu | Φ × L; alan | Φ3.5 × 52 m; 41 m² | LCDRI | P? | — | Doğrulanmadı; 1500 hattı PF1500'den alındı | Hayır | PF1500 soğutucusu 61.8 m², çelişiyor |
| LCDRI 2500 | Fırın; soğutucu | Eğim; alan | %3.5; LBTF2500, 65.54 m² | LCDRI | P? | — | Doğrulanmadı | Hayır | — |
| LCDRI 3500 | Fırın; soğutucu | Φ × L, eğim; alan | Φ4.5 × 54 m, %3.5; LYB-3750, 88 m² | LCDRI | P? | — | Doğrulanmadı; 3000–3500 hattı katalogda yok | Hayır | — |
| LCDRI 5000 | Fırın; soğutucu | Φ × L, eğim; alan | Φ5 × 60 m (iki destekli), %3.5; LCB5700, 136 m² | LCDRI | P? | — | Doğrulanmadı | Hayır | — |
| AGICO-R 2500→3000 | Siklon C1 | Çap, öncesi → sonrası | Φ4.6 → Φ5.4 m | AGICO-R | P? | — | Farklı tesis; doğrulanmadı | Hayır | Arama parçacığında da aynı değer geçiyor |
| AGICO-R 2500→3000 | Riserler C5→C4, C4→C3, C3→C2, C2→C1 | Çap, öncesi → sonrası | 3.86→4.56, 3.86→4.46, 3.74→4.26, 3.52→4.06 m | AGICO-R | P? | — | Farklı tesis; doğrulanmadı | Hayır | Bulunan **tek başka riser çapı seti**. Riser boyu yok. |
| AGICO-R | Kalsinatör; tersiyer kanal; soğutucu | Hacim; çap; alan | ≈763 m³; 2.2 → 2.4 m; 62.4 → 90.1 m² | AGICO-R | P? | — | Farklı tesis; tersiyer kanal kapsam dışı | Hayır | — |
| AGICO-R | Fırın | Φ × L; hız | Φ4.0 × 60 m; 0.41–4.07 rpm | AGICO-R | P? | — | Aynı ölçü katalogda PF2500'den var | Hayır | — |
| GUIGANG | Soğutucu | Model; alan | TC-1164; 61.2 m² | GUIGANG | P? | — | Farklı tesis | Hayır | Çift dizili hat |
| [ccement 702313](https://www.ccement.com/news/content/702313.html) 2500 | Fırın | Φ × L | Φ4.0 × 60 m | — | P? | — | Aynı ölçü katalogda var | Hayır | — |
| [Pengfei 2000](https://jspengfei.en.made-in-china.com/product/rbkQRxpJmDhi/China-2000tpd-Cement-Production-Line.html) | Siklonlar | Gövde çapı | PF2500 sayfasıyla aynı set | — | P? | — | 2000 t/d hattı katalogda yok | Hayır | — |
| [AGICO AG5/3200](https://cementplantequipment.com/products/cyclone-preheater/) | Fırın | Φ × L | Φ4.3 × 64 m | — | P? | — | 3000 hattı çıkarıldı | Hayır | — |
| [ccement 27855217306475001](https://m.ccement.com/news/content/27855217306475001.html) | Fırın; soğutucu | Φ × L; alan, öncesi → sonrası | Φ4.3 × 64 m; 80.46 → 105.4 m² | — | P? | — | 3000 hattı çıkarıldı; KHD genişletmesi | Hayır | Tek dizi |
| [ftxny 897](https://www.ftxny.com/hghhssdt/897.html) | Fırın | Φ × L | Ø4.3 × 66 m | — | P? | — | 3000 hattı çıkarıldı | Hayır | — |
| Henan 3300 t/d (snkjw aid=378, sayfa artık 404) | Siklonlar; kalsinatör | Gövde çapı; çap | C1 2-Φ5.05, C2 Φ7.36, C3–C5 Φ7.66 m; MFC Φ5.65 m | Yalnızca parçacık | P? | — | Doğrulanamıyor; 3000 hattı çıkarıldı | Hayır | **Doğrulanamaz** |
| [ftxny 602](https://www.ftxny.com/m/view.php?aid=602) 5000 | Fırın | Φ × L; eğim; hız | Φ4.8 × 72 m; %3.5; 0.396–3.96 rpm | — | P? | — | Farklı tesis | Hayır | — |
| AGICO-K 5000→6330 | Siklonlar | Gövde çapı | C1 4-Φ4.7; C2–C5 2-Φ6.8 m | AGICO-K | P? | — | Farklı tesis; doğrulanmadı | Hayır | PF5000'den (Φ5.0 / 6.9 / 7.2) farklı |
| AGICO-K | Kalsinatör; soğutucu; fırın | Φ × H; alan; Φ × L, eğim, hız | TTF 7.6 × 59.75 m; 136.2 m²; Φ4.8 × 74 m, %4, 0.4–4 rpm | AGICO-K | P? | — | Farklı tesis | Hayır | — |
| [ccement 8924717391779](https://www.ccement.com/news/content/8924717391779.html) 5000 | Fırın; kalsinatör; soğutucu | Φ × L, eğim, hız; tip; model | Φ5.0 × 74 m, %4, 0.35–4 rpm; NST-I; NC42365 | — | P? | — | Farklı tesis | Hayır | — |
| [fs755 3721](https://fs755.com/news/show-3721.html) 5000 | Kalsinatör | Φ × H; hacim | TDF Φ7.4 × 27 m; 848 m³ | — | P? | — | Farklı tesis | Hayır | — |
| [cementl 5000](https://www.cementl.com/solution/5000-tpd-cement-production-line/) | Kalsinatör; soğutucu | Girdap odası Φ; karışım odası Φ; alan | 5.3 m; 7.7 m; CRJ3-9, 133.056 m² | — | P? | — | Farklı tesis | Hayır | — |
| [fs755 2827](https://fs755.com/news/show-2827.html) 5000 | Soğutucu | Model | NC39325 | — | P? | — | Alan değil | Hayır | — |
| [sohu 446543828](https://www.sohu.com/a/446543828_771169) 5000 | Boru tipi kalsinatör (KHD genişletmesi) | Φ; H; hacim | ≈5.4 m; ≈70 m; ≈3000 m³ | — | P? (yaklaşık) | — | Farklı tesis; değerler "yaklaşık" | Hayır | — |
| [ccement 701433](https://m.ccement.com/news/content/701433.html) 2000 | Tersiyer hava kanalı | Gövde / efektif çap | Φ2200 / Φ1800 mm | — | P? | — | Tersiyer kanal kapsam dışı | Hayır | — |
| [MDPI Energies 18(24):6419](https://doi.org/10.3390/en18246419) | Kalsinatör; kaz boynu | Ana gövde Φ; akış yolu; kaz boynu bölgesi | 6.0 m; 101 m; 62.5–101 m | Yalnızca parçacık (site 403) | P? | — | Doğrulanamadı | Hayır | Kaz boynu çapı yok |
| [Energy 2024, S0360544224016992](https://www.sciencedirect.com/science/article/abs/pii/S0360544224016992) | Önısıtıcı; kalsinatör | Yükseklik | 95.58 m; gövde 72.94 m | Yalnızca özet parçacığı | P? | — | Doğrulanamadı | Hayır | — |
| [ITB JTMS 13793](https://journals.itb.ac.id/index.php/jtms/article/view/13793) 5000 | Kalsinatör | Uzatma | +2.5 m | Yalnızca parçacık | P? | — | Doğrulanamadı | Hayır | — |
| Ohorongo (0.7 Mt/y); Ketton fırın 8 | Önısıtıcı kulesi | Yükseklik | 109 m; ≈80 m | Ajan özeti, URL kayıtlı değil | P? | — | Kapasite sınıfına bağlanamıyor | Hayır | — |

---

## C. Geometrik olmadığı için envantere alınmayan değerler

Araştırmada bulunan ama ölçü olmayan değerler. Kurallarımız gereği hiçbirinden ölçü türetilmedi.

- **Gaz hızları:**
  - HFC2500: siklon kesitlerinde 3.6–5.0 m/s, kanallarda 15.6–16.4 m/s, kalsinatörde 6.9, kaz boynunda 17.5 m/s.
  - RSP1500: kalsinatörde 7.56, çıkış kanalında 14.5, boğazda 32.82 m/s, tersiyer kanalda 19–20 m/s.
  - Holderbank tasarım kuralları: siklon girişi 10–15, kanal 10–20 m/s.
- **Gaz kalma süreleri:**
  - HFC2500: kanallarda 0.50–0.69 s, kalsinatörde 3.19 s, kaz boynunda 1.89 s.
  - TCDRI5000: kalsinatörde 2.2 → 3.6 s, kaz boynunda 1.0 s.
  - Holderbank: kalsinatör için 2–3.5 s.
- **Özgül gaz hacimleri:** ≈1.3–1.68 Nm³/kg klinker.
- **Soğutucu yükleri:** 30–40 t/(m²·d).

---

## D. CFD aşaması için özet

| Hat | Tek siklon katıları (C1–C5) | Kalsinatör katısı | Riser | Kaz boynu | Kule |
|---|---|---|---|---|---|
| 1500 | Kurulabilir (R, varsayımlı) | Kurulabilir (R/R) | Yalnızca kesit (R) | Yok | Kurulamaz |
| 2500 | Kurulabilir (efektif çap P, geri kalanı R) | Kurulabilir (D P, H R) | Yalnızca kesit (P) | Kesit (P), boy yok | Kurulamaz |
| 5000 | Kurulabilir (R, varsayımlı) | Kurulabilir (D R, H P) | Yalnızca kesit (R) | Yok | Kurulamaz (ayrıca çift dizi) |
| FLS | Kurulabilir (P; giriş M) | Kurulabilir (P) | Kesit (P); boy var ama şekil belirsiz | Yok (tasarımda eleman yok) | Kurulamaz |

**Hiçbir kaynakta bulunamayan ölçüler:**
- Satıcı hatlarında riser boyları;
- kataloğa atanabilecek bir kaz boynu boyu;
- kalsinatör giriş boğazı ve fırın giriş odası (yalnızca RSP1500'de, başka bir tesis için var);
- siklon volüt geometrisi (yalnızca TCDRI5000'de C5 için nitel bilgi var).

Bu eksiklerin hiçbiri katalog dışındaki değerlerle kapatılmaz:
- B.1'deki kaz boynu, riser ve kalsinatör girişi ölçüleri başka tesislere ve başka ekipman tasarımlarına aittir.
- B.3'teki değerler doğrulanmamıştır.
