# CFD görünümü: kullanılabilir ölçüler

Bu belge [INVENTORY.md](INVENTORY.md)'deki mevcut verinin **CFD çalışması için filtrelenmiş görünümüdür**. Yeni ölçü eklemez; katalog, kod ve geometri değerleri değişmez. Kaynak envanteri olarak INVENTORY.md geçerliliğini korur. Katalog satırları `geometry/catalog.py`'den bir betikle filtrelendi; diğer satırlar INVENTORY.md B.1'den birebir alındı.

## Kategoriler

| Kategori | Anlamı |
|---|---|
| `CFD-ready` | Doğrudan geometri kurmak için yeterli ve güvenilir. |
| `CFD-supporting` | Tek başına geometri kurdurmaz, ama CFD modelini destekler: kesit, duvar, sınır koşulu, kontrol. |
| `reference-only` | Başka bir tesise ait ya da modele doğrudan aktarılmamalı. |
| `blocked` | Eksik ya da belirsiz; şu an kullanılamaz. |

**Uygulanan kurallar:**
- **R değerleri:** `CFD-ready` olabilir. Dayandıkları varsayım ise Not sütununda yazılıdır: C1'e aktarım varsayımı ve `w_in` model varsayımı.
- **Çelik gövde çapı (Φ):** Akışkan hacmi efektif çapla kurulduğu için `CFD-supporting`.
- **Riser:** Çapı `CFD-supporting`. Boyu ya da şekli eksik veya belirsizse `blocked`.
- **Kaz boynu:** Çapı `CFD-supporting`, boyu `blocked`.
- **Fırın ve soğutucu:** Kule dışında kalır; bunlar için katı üreten kod henüz yok.
- **B.2 ve B.3 hiç dahil edilmedi** (bölüm 5).
- **CFD sınır parametreleri** (`geometry.cfd_boundary`) ölçü değildir. Yalnızca bölüm 6'da, prototipi kurmak için gerekli oldukları için ayrı bir tabloda gösterilir.

## Özet

| Kapsam | `CFD-ready` | `CFD-supporting` | `reference-only` | `blocked` |
|---|---|---|---|---|
| 2500 (katalog) | 44 | 22 | 0 | 5 |
| FLS (katalog) | 44 | 23 | 0 | 15 |
| FLS (katalog dışı, B.1) | 0 | 9 | 1 | 5 |
| 1500 (yalnızca kapanmış parçalar) | 44 | — | — | — |
| 5000 (yalnızca kapanmış parçalar) | 44 | — | — | — |
| Başka tesisler (B.1) | 0 | 0 | 27 | 1 |
| B.2 / B.3 | dahil edilmedi | | | |

---

## 1. Hat 2500 (öncelik 1)

Önısıtıcı ve kalsinatörün efektif çapları HFC2500'de yayınlanmış (P). Siklonların diğer ölçüleri FLS oranlarıyla türetilmiş (R). Fırın ve soğutucu PF2500'den.

**Kapanan ekipmanlar:** C1–C5 siklonlar, kalsinatör, fırın.
**Kapanmayanlar:** R1–R4 riserlerin boyları, kaz boynunun boyu.

| Hat | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| 2500 | Hat | Kapasite | 2500 t/d | P | HFC2500 | `CFD-supporting` | Geometri değil; işletme bağlamı |
| 2500 | Fırın | Çelik gövde iç çapı (Φ) | 4 m | P | PF2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Fırın | Efektif iç çap | 3.633 m | R | PF2500 × FLS:kiln_eff_over_shell | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 2500 | Fırın | Boy / yükseklik | 60 m | P | PF2500 | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 2500 | Fırın | Eğim | 4 % | P | PF2500 | `CFD-supporting` | Fırın ekseni eğimi |
| 2500 | Fırın | Dönüş hızı, min | 0.39 rpm | P | PF2500 | `CFD-supporting` | Duvar hareketi sınır koşulu |
| 2500 | Fırın | Dönüş hızı, max | 4.1 rpm | P | PF2500 | `CFD-supporting` | Duvar hareketi sınır koşulu |
| 2500 | Soğutucu | Izgara alanı | 65 m² | P | PF2500 | `CFD-supporting` | Tek başına kutu kurdurmaz (L×W yok) |
| 2500 | Kalsinatör | Çelik gövde iç çapı (Φ) | 6 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Kalsinatör | Efektif iç çap | 5.5 m | P | HFC2500 | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| 2500 | Kalsinatör | Boy / yükseklik | 29.464 m | R | HFC2500 × FLS:calciner_H/D | `CFD-ready` | Silindir D × H; taban tek giriş sınırı; H türetilmiş |
| 2500 | Kaz boynu | Çelik gövde iç çapı (Φ) | 4 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Kaz boynu | Efektif iç çap | 3.5 m | P | HFC2500 | `CFD-supporting` | Yalnızca kesit; boy yok |
| 2500 | Kaz boynu | Boy / yükseklik | — | — | kaynak yok | `blocked` | Kaz boynu boyu hiçbir kaynakta yok |
| 2500 | Siklon C1 | Çelik gövde iç çapı (Φ) | 4.7 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Siklon C1 | Efektif iç çap | 4.32 m | P | HFC2500 | `CFD-ready` | — |
| 2500 | Siklon C1 | Silindirik gövde yüksekliği | 6.793 m | R | HFC2500 × FLS:barrel_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 2500 | Siklon C1 | Koni yüksekliği | 4.652 m | R | HFC2500 × FLS:cone_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 2500 | Siklon C1 | Vorteks bulucu boyu | 2.16 m | R | HFC2500 × FLS:vortex_len/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 2500 | Siklon C1 | Vorteks bulucu çapı | 2.404 m | R | HFC2500 × FLS:vortex_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 2500 | Siklon C1 | Toz çıkışı çapı | 0.401 m | R | HFC2500 × FLS:dust_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 2500 | Siklon C1 | Giriş genişliği | 0.864 m | R | HFC2500 × FLS:inlet_w/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C1 | Giriş yüksekliği | 4.968 m | R | HFC2500 × FLS:inlet_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C2 | Çelik gövde iç çapı (Φ) | 6.6 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Siklon C2 | Efektif iç çap | 6.1 m | P | HFC2500 | `CFD-ready` | — |
| 2500 | Siklon C2 | Silindirik gövde yüksekliği | 3.667 m | R | HFC2500 × FLS:barrel_h/D[2] | `CFD-ready` | — |
| 2500 | Siklon C2 | Koni yüksekliği | 6.511 m | R | HFC2500 × FLS:cone_h/D[2] | `CFD-ready` | — |
| 2500 | Siklon C2 | Vorteks bulucu boyu | 3.05 m | R | HFC2500 × FLS:vortex_len/D[2] | `CFD-ready` | — |
| 2500 | Siklon C2 | Vorteks bulucu çapı | 4.347 m | R | HFC2500 × FLS:vortex_D/D[2] | `CFD-ready` | — |
| 2500 | Siklon C2 | Toz çıkışı çapı | 0.805 m | R | HFC2500 × FLS:dust_D/D[2] | `CFD-ready` | — |
| 2500 | Siklon C2 | Giriş genişliği | 1.225 m | R | HFC2500 × FLS:inlet_w/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C2 | Giriş yüksekliği | 8.709 m | R | HFC2500 × FLS:inlet_h/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C3 | Çelik gövde iç çapı (Φ) | 6.8 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Siklon C3 | Efektif iç çap | 6.3 m | P | HFC2500 | `CFD-ready` | — |
| 2500 | Siklon C3 | Silindirik gövde yüksekliği | 3.215 m | R | HFC2500 × FLS:barrel_h/D[3] | `CFD-ready` | — |
| 2500 | Siklon C3 | Koni yüksekliği | 7.26 m | R | HFC2500 × FLS:cone_h/D[3] | `CFD-ready` | — |
| 2500 | Siklon C3 | Vorteks bulucu boyu | 3.15 m | R | HFC2500 × FLS:vortex_len/D[3] | `CFD-ready` | — |
| 2500 | Siklon C3 | Vorteks bulucu çapı | 4.622 m | R | HFC2500 × FLS:vortex_D/D[3] | `CFD-ready` | — |
| 2500 | Siklon C3 | Toz çıkışı çapı | 0.839 m | R | HFC2500 × FLS:dust_D/D[3] | `CFD-ready` | — |
| 2500 | Siklon C3 | Giriş genişliği | 1.258 m | R | HFC2500 × FLS:inlet_w/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C3 | Giriş yüksekliği | 9.458 m | R | HFC2500 × FLS:inlet_h/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C4 | Çelik gövde iç çapı (Φ) | 6.8 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Siklon C4 | Efektif iç çap | 6.3 m | P | HFC2500 | `CFD-ready` | — |
| 2500 | Siklon C4 | Silindirik gövde yüksekliği | 3.455 m | R | HFC2500 × FLS:barrel_h/D[4] | `CFD-ready` | — |
| 2500 | Siklon C4 | Koni yüksekliği | 7.296 m | R | HFC2500 × FLS:cone_h/D[4] | `CFD-ready` | — |
| 2500 | Siklon C4 | Vorteks bulucu boyu | 3.168 m | R | HFC2500 × FLS:vortex_len/D[4] | `CFD-ready` | — |
| 2500 | Siklon C4 | Vorteks bulucu çapı | 4.631 m | R | HFC2500 × FLS:vortex_D/D[4] | `CFD-ready` | — |
| 2500 | Siklon C4 | Toz çıkışı çapı | 0.808 m | R | HFC2500 × FLS:dust_D/D[4] | `CFD-ready` | — |
| 2500 | Siklon C4 | Giriş genişliği | 1.265 m | R | HFC2500 × FLS:inlet_w/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C4 | Giriş yüksekliği | 9.439 m | R | HFC2500 × FLS:inlet_h/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C5 | Çelik gövde iç çapı (Φ) | 7 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Siklon C5 | Efektif iç çap | 6.5 m | P | HFC2500 | `CFD-ready` | — |
| 2500 | Siklon C5 | Silindirik gövde yüksekliği | 3.535 m | R | HFC2500 × FLS:barrel_h/D[5] | `CFD-ready` | — |
| 2500 | Siklon C5 | Koni yüksekliği | 7.427 m | R | HFC2500 × FLS:cone_h/D[5] | `CFD-ready` | — |
| 2500 | Siklon C5 | Vorteks bulucu boyu | 3.25 m | R | HFC2500 × FLS:vortex_len/D[5] | `CFD-ready` | — |
| 2500 | Siklon C5 | Vorteks bulucu çapı | 4.737 m | R | HFC2500 × FLS:vortex_D/D[5] | `CFD-ready` | — |
| 2500 | Siklon C5 | Toz çıkışı çapı | 0.826 m | R | HFC2500 × FLS:dust_D/D[5] | `CFD-ready` | — |
| 2500 | Siklon C5 | Giriş genişliği | 1.304 m | R | HFC2500 × FLS:inlet_w/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Siklon C5 | Giriş yüksekliği | 9.588 m | R | HFC2500 × FLS:inlet_h/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 2500 | Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ) | 3.45 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Riser R1 (C2→C1) | Efektif iç çap | 3.07 m | P | HFC2500 | `CFD-supporting` | Yalnızca kesit; riser boyu/şekli yok |
| 2500 | Riser R1 (C2→C1) | Boy / yükseklik | — | — | kaynak yok | `blocked` | Riser boyu hiçbir kaynakta yok; kule kurulamaz |
| 2500 | Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ) | 3.85 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Riser R2 (C3→C2) | Efektif iç çap | 3.35 m | P | HFC2500 | `CFD-supporting` | Yalnızca kesit; riser boyu/şekli yok |
| 2500 | Riser R2 (C3→C2) | Boy / yükseklik | — | — | kaynak yok | `blocked` | Riser boyu hiçbir kaynakta yok; kule kurulamaz |
| 2500 | Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ) | 3.95 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Riser R3 (C4→C3) | Efektif iç çap | 3.45 m | P | HFC2500 | `CFD-supporting` | Yalnızca kesit; riser boyu/şekli yok |
| 2500 | Riser R3 (C4→C3) | Boy / yükseklik | — | — | kaynak yok | `blocked` | Riser boyu hiçbir kaynakta yok; kule kurulamaz |
| 2500 | Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ) | 4.1 m | P | HFC2500 | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| 2500 | Riser R4 (C5→C4) | Efektif iç çap | 3.6 m | P | HFC2500 | `CFD-supporting` | Yalnızca kesit; riser boyu/şekli yok |
| 2500 | Riser R4 (C5→C4) | Boy / yükseklik | — | — | kaynak yok | `blocked` | Riser boyu hiçbir kaynakta yok; kule kurulamaz |

---

## 2. FLS referans geometrisi (öncelik 2)

Bu hat bağımsız bir referans hattır. Ölçüler yayınlanmıştır (P); yalnızca giriş genişliği ve yüksekliği modelleme varsayımıdır (M). Riser eşlemesi Tablo 7'de açıkça yazılıdır, ama riser şekli belirsizdir.

### 2.1 Katalogdaki FLS ölçüleri

| Hat | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| FLS | Fırın | Çelik gövde iç çapı (Φ) | 4.36 m | P | FLS: 2 r_r[kiln] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Fırın | Efektif iç çap | 3.96 m | P | FLS: 2 r_c[kiln] | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| FLS | Fırın | Boy / yükseklik | 51 m | P | FLS: L[kiln] | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| FLS | Fırın | Dönüş hızı, işletme | 4 rpm | P | FLS: kiln rotation, scenario text | `CFD-supporting` | Duvar hareketi sınır koşulu |
| FLS | Soğutucu | Boy / yükseklik | 36 m | P | FLS: L[cooler] | `CFD-supporting` | Soğutucu kutusu için; yükseklik katalogda yok |
| FLS | Soğutucu | Genişlik | 4 m | P | FLS: w[cooler] | `CFD-supporting` | Soğutucu kutusu için; yükseklik katalogda yok |
| FLS | Kalsinatör | Çelik gövde iç çapı (Φ) | 6.58 m | P | FLS: 2 r_r[calciner] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Kalsinatör | Efektif iç çap | 6.16 m | P | FLS: 2 r_c[calciner] | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| FLS | Kalsinatör | Boy / yükseklik | 33 m | P | FLS: h_tot[calciner] | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| FLS | Kaz boynu | Çelik gövde iç çapı (Φ) | — | — | kaynak yok | `blocked` | Kaz boynu ölçüsü hiçbir kaynakta yok |
| FLS | Kaz boynu | Efektif iç çap | — | — | kaynak yok | `blocked` | Kaz boynu ölçüsü hiçbir kaynakta yok |
| FLS | Kaz boynu | Boy / yükseklik | — | — | kaynak yok | `blocked` | Kaz boynu boyu hiçbir kaynakta yok |
| FLS | Siklon C1 | Çelik gövde iç çapı (Φ) | 7.18 m | P | FLS: 2 r_r[Cy1] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Siklon C1 | Efektif iç çap | 6.9 m | P | FLS: 2 r_c[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Silindirik gövde yüksekliği | 10.85 m | P | FLS: h_t - h_c[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Koni yüksekliği | 7.43 m | P | FLS: h_c[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Vorteks bulucu boyu | 3.45 m | P | FLS: h_x[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Vorteks bulucu çapı | 3.84 m | P | FLS: 2 r_x[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Toz çıkışı çapı | 0.64 m | P | FLS: 2 r_d[Cy1] | `CFD-ready` | — |
| FLS | Siklon C1 | Giriş genişliği | 1.38 m | M | FLS: w_in[Cy1] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C1 | Giriş yüksekliği | 7.935 m | M | FLS: A_in / w_in[Cy1] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C1 | Giriş kesit alanı | 10.95 m² | P | FLS: A_in[Cy1] | `CFD-supporting` | Giriş w × h kontrolü |
| FLS | Siklon C2 | Çelik gövde iç çapı (Φ) | 7.18 m | P | FLS: 2 r_r[Cy2] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Siklon C2 | Efektif iç çap | 6.82 m | P | FLS: 2 r_c[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Silindirik gövde yüksekliği | 4.1 m | P | FLS: h_t - h_c[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Koni yüksekliği | 7.28 m | P | FLS: h_c[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Vorteks bulucu boyu | 3.41 m | P | FLS: h_x[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Vorteks bulucu çapı | 4.86 m | P | FLS: 2 r_x[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Toz çıkışı çapı | 0.9 m | P | FLS: 2 r_d[Cy2] | `CFD-ready` | — |
| FLS | Siklon C2 | Giriş genişliği | 1.37 m | M | FLS: w_in[Cy2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C2 | Giriş yüksekliği | 9.737 m | M | FLS: A_in / w_in[Cy2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C2 | Giriş kesit alanı | 13.34 m² | P | FLS: A_in[Cy2] | `CFD-supporting` | Giriş w × h kontrolü |
| FLS | Siklon C3 | Çelik gövde iç çapı (Φ) | 7.18 m | P | FLS: 2 r_r[Cy3] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Siklon C3 | Efektif iç çap | 6.76 m | P | FLS: 2 r_c[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Silindirik gövde yüksekliği | 3.45 m | P | FLS: h_t - h_c[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Koni yüksekliği | 7.79 m | P | FLS: h_c[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Vorteks bulucu boyu | 3.38 m | P | FLS: h_x[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Vorteks bulucu çapı | 4.96 m | P | FLS: 2 r_x[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Toz çıkışı çapı | 0.9 m | P | FLS: 2 r_d[Cy3] | `CFD-ready` | — |
| FLS | Siklon C3 | Giriş genişliği | 1.35 m | M | FLS: w_in[Cy3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C3 | Giriş yüksekliği | 10.148 m | M | FLS: A_in / w_in[Cy3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C3 | Giriş kesit alanı | 13.7 m² | P | FLS: A_in[Cy3] | `CFD-supporting` | Giriş w × h kontrolü |
| FLS | Siklon C4 | Çelik gövde iç çapı (Φ) | 7.48 m | P | FLS: 2 r_r[Cy4] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Siklon C4 | Efektif iç çap | 7.02 m | P | FLS: 2 r_c[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Silindirik gövde yüksekliği | 3.85 m | P | FLS: h_t - h_c[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Koni yüksekliği | 8.13 m | P | FLS: h_c[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Vorteks bulucu boyu | 3.53 m | P | FLS: h_x[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Vorteks bulucu çapı | 5.16 m | P | FLS: 2 r_x[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Toz çıkışı çapı | 0.9 m | P | FLS: 2 r_d[Cy4] | `CFD-ready` | — |
| FLS | Siklon C4 | Giriş genişliği | 1.41 m | M | FLS: w_in[Cy4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C4 | Giriş yüksekliği | 10.518 m | M | FLS: A_in / w_in[Cy4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C4 | Giriş kesit alanı | 14.83 m² | P | FLS: A_in[Cy4] | `CFD-supporting` | Giriş w × h kontrolü |
| FLS | Siklon C5 | Çelik gövde iç çapı (Φ) | 7.48 m | P | FLS: 2 r_r[Cy5] | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Siklon C5 | Efektif iç çap | 7.08 m | P | FLS: 2 r_c[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Silindirik gövde yüksekliği | 3.85 m | P | FLS: h_t - h_c[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Koni yüksekliği | 8.09 m | P | FLS: h_c[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Vorteks bulucu boyu | 3.54 m | P | FLS: h_x[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Vorteks bulucu çapı | 5.16 m | P | FLS: 2 r_x[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Toz çıkışı çapı | 0.9 m | P | FLS: 2 r_d[Cy5] | `CFD-ready` | — |
| FLS | Siklon C5 | Giriş genişliği | 1.42 m | M | FLS: w_in[Cy5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C5 | Giriş yüksekliği | 10.444 m | M | FLS: A_in / w_in[Cy5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| FLS | Siklon C5 | Giriş kesit alanı | 14.83 m² | P | FLS: A_in[Cy5] | `CFD-supporting` | Giriş w × h kontrolü |
| FLS | Riser R1 (C2→C1) | Çelik gövde iç çapı (Φ) | 4.94 m | P | FLS: 2 r_r[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Riser R1 (C2→C1) | Efektif iç çap | 4.9 m | P | FLS: 2 r_c[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Kesit; riser şekli belirsiz |
| FLS | Riser R1 (C2→C1) | Boy / yükseklik | 21.38 m | P | FLS: h_tot[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R1 (C2→C1) | Uç konisi boyu (h_cl) | 4.83 m | P | FLS: h_cl[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R1 (C2→C1) | Uç çapı (2 r_u) | 3.44 m | P | FLS: 2 r_u[R1]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R2 (C3→C2) | Çelik gövde iç çapı (Φ) | 4.94 m | P | FLS: 2 r_r[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Riser R2 (C3→C2) | Efektif iç çap | 4.9 m | P | FLS: 2 r_c[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Kesit; riser şekli belirsiz |
| FLS | Riser R2 (C3→C2) | Boy / yükseklik | 19.38 m | P | FLS: h_tot[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R2 (C3→C2) | Uç konisi boyu (h_cl) | 4.18 m | P | FLS: h_cl[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R2 (C3→C2) | Uç çapı (2 r_u) | 3.8 m | P | FLS: 2 r_u[R2]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R3 (C4→C3) | Çelik gövde iç çapı (Φ) | 5.14 m | P | FLS: 2 r_r[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Riser R3 (C4→C3) | Efektif iç çap | 5.1 m | P | FLS: 2 r_c[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Kesit; riser şekli belirsiz |
| FLS | Riser R3 (C4→C3) | Boy / yükseklik | 20.37 m | P | FLS: h_tot[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R3 (C4→C3) | Uç konisi boyu (h_cl) | 4.18 m | P | FLS: h_cl[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R3 (C4→C3) | Uç çapı (2 r_u) | 3.8 m | P | FLS: 2 r_u[R3]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R4 (C5→C4) | Çelik gövde iç çapı (Φ) | 5.14 m | P | FLS: 2 r_r[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Akışkan hacmi değil; astar kalınlığı/duvar ısıl modeli için |
| FLS | Riser R4 (C5→C4) | Efektif iç çap | 5.1 m | P | FLS: 2 r_c[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `CFD-supporting` | Kesit; riser şekli belirsiz |
| FLS | Riser R4 (C5→C4) | Boy / yükseklik | 19.87 m | P | FLS: h_tot[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R4 (C5→C4) | Uç konisi boyu (h_cl) | 4.37 m | P | FLS: h_cl[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |
| FLS | Riser R4 (C5→C4) | Uç çapı (2 r_u) | 3.98 m | P | FLS: 2 r_u[R4]; connection: FLS Table 7, R_k from Cy(k+1) to Cy(k) | `blocked` | Tablo 8 sütun anlamı metin/denklemlerle çelişik (SOURCES.md) |

### 2.2 Katalog dışı FLS ölçüleri (INVENTORY.md B.1, ham metni doğrulanmış)

Aynı referans kulesine aitler, ama katalogda yer almıyorlar.

| Hat | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| FLS | Siklon Cy1–Cy5 | Duvar dış yarıçapı r_w | 3.60, 3.60, 3.60, 3.75, 3.75 m | P | FLS-T8 | `CFD-supporting` | Duvar ısıl modeli; akışkan hacminin dışında |
| FLS | Siklon | Duvar kalınlığı | 0.008 m | P | FLS-Cy | `CFD-supporting` | Çelik duvar; vorteks bulucu duvarı değil |
| FLS | Siklon Cy1–Cy5 | Giriş ekseninin yarıçapı r_in | 2.76, 2.73, 2.70, 2.82, 2.83 m | P | FLS-T8 | `CFD-supporting` | r_c − w_in/2'ye eşit; w_in model varsayımına bağlı; teğet girişle tutarlı |
| FLS | Siklon Cy1–Cy5 | l_in | 0.1 m | P | FLS-T8 | `blocked` | Anlamı makalede tanımlanmamış |
| FLS | Riser R1–R4 | Duvar dış yarıçapı r_w | 2.48, 2.48, 2.58, 2.58 m | P | FLS-T8 | `CFD-supporting` | Duvar ısıl modeli |
| FLS | Riser R1–R4 | r_l | 2.45 m | P | FLS-T8 | `blocked` | Riser şekli belirsiz |
| FLS | Riser R1–R4 | h_cu | 0 | P | FLS-T8 | `blocked` | Sütun anlamı çelişik; denklem (34a)'da sıfıra bölme |
| FLS | R5 | h_tot, r_c, r_r, r_w | 61.0, 1.13, 1.33, 1.34 m | P | FLS-T8 | `reference-only` | Tersiyer boru olduğu ima ediliyor; tersiyer kanal kapsam dışı |
| FLS | Kalsinatör | h_cl, h_cu | 33.0, 0 m | P | FLS-T8 | `blocked` | Sütun anlamı çelişik; katalog yalnızca D ve h_tot kullanıyor |
| FLS | Kalsinatör | r_l, r_u | 3.08, 3.08 m | P | FLS-T8 | `CFD-supporting` | r_c'ye eşit, yani düz silindiri destekliyor |
| FLS | Kalsinatör | r_w | 3.30 m | P | FLS-T8 | `CFD-supporting` | Duvar ısıl modeli |
| FLS | Kalsinatör | Refrakter / kabuk kalınlığı | 0.21 / 0.01 m | P | FLS-Ca | `CFD-supporting` | Duvar ısıl modeli |
| FLS | Fırın | ψ | 2° | P | FLS-T8 | `blocked` | Anlamı tanımsız (muhtemelen eğim) |
| FLS | Soğutucu | Yükseklik h | 3 m | P | FLS-T8 | `CFD-supporting` | Katalogdaki L × W ile bir kutu kapanır; ama h katalogda yok ve soğutucu için kod yok |
| FLS | Soğutucu | Çatı bölümleri A_y1–A_y4 | 12.1, 22.5, 49.0, 60.5 m² | P | FLS-T8 | `CFD-supporting` | Çatı sınırının bölümlenmesi: fırına, tersiyer boruya, çıkışsız kısma, ortama |

---

## 3. Hat 1500 ve 5000 (öncelik 3): yalnızca kapanmış parçalar

Bu iki hatta **yalnızca geometrisi kapanan parçalar** listeleniyor: C1–C5 siklonlar, kalsinatör ve fırının D × L değerleri.

**Uyarılar:**
- Siklon ölçülerinin hepsi türetilmiştir (R). Efektif çap bile satıcının verdiği gövde çapının FLS astar oranıyla çarpımıdır.
- 5000 çift dizilidir. Siklon adetleri tüm kademeyi, riser çapları tek diziyi gösterir.

**Burada gösterilmeyenler** (ayrıntı INVENTORY.md A.1 ve A.3'te):
- Riser çapları: `CFD-supporting`.
- Riser boyları, kaz boynu çapı ve boyu: `blocked`.
- Çelik gövde çapları ile fırın eğimi ve hızı: `CFD-supporting`.

### 3.1 Hat 1500

| Hat | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| 1500 | Fırın | Efektif iç çap | 3.179 m | R | PF1500 × FLS:kiln_eff_over_shell | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 1500 | Fırın | Boy / yükseklik | 54 m | P | PF1500 | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 1500 | Kalsinatör | Efektif iç çap | 5.898 m | R | PF1500 × FLS:calciner_eff_over_shell | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| 1500 | Kalsinatör | Boy / yükseklik | 31.596 m | R | PF1500 × FLS:calciner_eff_over_shell × FLS:calciner_H/D | `CFD-ready` | Silindir D × H; taban tek giriş sınırı; H türetilmiş |
| 1500 | Siklon C1 | Efektif iç çap | 4.132 m | R | PF1500 × FLS:eff_over_shell[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Silindirik gövde yüksekliği | 6.498 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:barrel_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Koni yüksekliği | 4.45 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:cone_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Vorteks bulucu boyu | 2.066 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:vortex_len/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Vorteks bulucu çapı | 2.3 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:vortex_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Toz çıkışı çapı | 0.383 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:dust_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 1500 | Siklon C1 | Giriş genişliği | 0.826 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:inlet_w/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C1 | Giriş yüksekliği | 4.752 m | R | PF1500 × FLS:eff_over_shell[1] × FLS:inlet_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C2 | Efektif iç çap | 5.319 m | R | PF1500 × FLS:eff_over_shell[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Silindirik gövde yüksekliği | 3.198 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:barrel_h/D[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Koni yüksekliği | 5.678 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:cone_h/D[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Vorteks bulucu boyu | 2.66 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:vortex_len/D[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Vorteks bulucu çapı | 3.791 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:vortex_D/D[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Toz çıkışı çapı | 0.702 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:dust_D/D[2] | `CFD-ready` | — |
| 1500 | Siklon C2 | Giriş genişliği | 1.069 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:inlet_w/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C2 | Giriş yüksekliği | 7.594 m | R | PF1500 × FLS:eff_over_shell[2] × FLS:inlet_h/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C3 | Efektif iç çap | 5.272 m | R | PF1500 × FLS:eff_over_shell[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Silindirik gövde yüksekliği | 2.691 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:barrel_h/D[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Koni yüksekliği | 6.076 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:cone_h/D[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Vorteks bulucu boyu | 2.636 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:vortex_len/D[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Vorteks bulucu çapı | 3.869 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:vortex_D/D[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Toz çıkışı çapı | 0.702 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:dust_D/D[3] | `CFD-ready` | — |
| 1500 | Siklon C3 | Giriş genişliği | 1.053 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:inlet_w/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C3 | Giriş yüksekliği | 7.915 m | R | PF1500 × FLS:eff_over_shell[3] × FLS:inlet_h/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C4 | Efektif iç çap | 5.537 m | R | PF1500 × FLS:eff_over_shell[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Silindirik gövde yüksekliği | 3.037 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:barrel_h/D[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Koni yüksekliği | 6.413 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:cone_h/D[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Vorteks bulucu boyu | 2.784 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:vortex_len/D[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Vorteks bulucu çapı | 4.07 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:vortex_D/D[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Toz çıkışı çapı | 0.71 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:dust_D/D[4] | `CFD-ready` | — |
| 1500 | Siklon C4 | Giriş genişliği | 1.112 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:inlet_w/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C4 | Giriş yüksekliği | 8.296 m | R | PF1500 × FLS:eff_over_shell[4] × FLS:inlet_h/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C5 | Efektif iç çap | 5.584 m | R | PF1500 × FLS:eff_over_shell[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Silindirik gövde yüksekliği | 3.037 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:barrel_h/D[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Koni yüksekliği | 6.381 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:cone_h/D[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Vorteks bulucu boyu | 2.792 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:vortex_len/D[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Vorteks bulucu çapı | 4.07 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:vortex_D/D[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Toz çıkışı çapı | 0.71 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:dust_D/D[5] | `CFD-ready` | — |
| 1500 | Siklon C5 | Giriş genişliği | 1.12 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:inlet_w/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 1500 | Siklon C5 | Giriş yüksekliği | 8.238 m | R | PF1500 × FLS:eff_over_shell[5] × FLS:inlet_h/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |

### 3.2 Hat 5000

| Hat | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| 5000 | Fırın | Efektif iç çap | 4.36 m | R | PF5000 × FLS:kiln_eff_over_shell | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 5000 | Fırın | Boy / yükseklik | 74 m | P | PF5000 | `CFD-ready` | Silindir; kule dışı, fırın CFD'si için (builder yok) |
| 5000 | Kalsinatör | Efektif iç çap | 6.74 m | R | PF5000 × FLS:calciner_eff_over_shell | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| 5000 | Kalsinatör | Boy / yükseklik | 30 m | P | PF5000 | `CFD-ready` | Silindir D × H; taban tek giriş sınırı |
| 5000 | Siklon C1 | Efektif iç çap | 4.805 m | R | PF5000 × FLS:eff_over_shell[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Silindirik gövde yüksekliği | 7.556 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:barrel_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Koni yüksekliği | 5.174 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:cone_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Vorteks bulucu boyu | 2.403 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:vortex_len/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Vorteks bulucu çapı | 2.674 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:vortex_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Toz çıkışı çapı | 0.446 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:dust_D/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı |
| 5000 | Siklon C1 | Giriş genişliği | 0.961 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:inlet_w/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C1 | Giriş yüksekliği | 5.526 m | R | PF5000 × FLS:eff_over_shell[1] × FLS:inlet_h/D[1] | `CFD-ready` | FLS tek Cy1 → çoklu C1 aktarım varsayımı; w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C2 | Efektif iç çap | 6.554 m | R | PF5000 × FLS:eff_over_shell[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Silindirik gövde yüksekliği | 3.94 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:barrel_h/D[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Koni yüksekliği | 6.996 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:cone_h/D[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Vorteks bulucu boyu | 3.277 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:vortex_len/D[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Vorteks bulucu çapı | 4.67 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:vortex_D/D[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Toz çıkışı çapı | 0.865 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:dust_D/D[2] | `CFD-ready` | — |
| 5000 | Siklon C2 | Giriş genişliği | 1.317 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:inlet_w/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C2 | Giriş yüksekliği | 9.358 m | R | PF5000 × FLS:eff_over_shell[2] × FLS:inlet_h/D[2] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C3 | Efektif iç çap | 6.496 m | R | PF5000 × FLS:eff_over_shell[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Silindirik gövde yüksekliği | 3.315 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:barrel_h/D[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Koni yüksekliği | 7.486 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:cone_h/D[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Vorteks bulucu boyu | 3.248 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:vortex_len/D[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Vorteks bulucu çapı | 4.767 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:vortex_D/D[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Toz çıkışı çapı | 0.865 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:dust_D/D[3] | `CFD-ready` | — |
| 5000 | Siklon C3 | Giriş genişliği | 1.297 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:inlet_w/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C3 | Giriş yüksekliği | 9.752 m | R | PF5000 × FLS:eff_over_shell[3] × FLS:inlet_h/D[3] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C4 | Efektif iç çap | 6.757 m | R | PF5000 × FLS:eff_over_shell[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Silindirik gövde yüksekliği | 3.706 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:barrel_h/D[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Koni yüksekliği | 7.826 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:cone_h/D[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Vorteks bulucu boyu | 3.398 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:vortex_len/D[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Vorteks bulucu çapı | 4.967 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:vortex_D/D[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Toz çıkışı çapı | 0.866 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:dust_D/D[4] | `CFD-ready` | — |
| 5000 | Siklon C4 | Giriş genişliği | 1.357 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:inlet_w/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C4 | Giriş yüksekliği | 10.124 m | R | PF5000 × FLS:eff_over_shell[4] × FLS:inlet_h/D[4] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C5 | Efektif iç çap | 6.815 m | R | PF5000 × FLS:eff_over_shell[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Silindirik gövde yüksekliği | 3.706 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:barrel_h/D[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Koni yüksekliği | 7.787 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:cone_h/D[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Vorteks bulucu boyu | 3.407 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:vortex_len/D[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Vorteks bulucu çapı | 4.967 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:vortex_D/D[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Toz çıkışı çapı | 0.866 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:dust_D/D[5] | `CFD-ready` | — |
| 5000 | Siklon C5 | Giriş genişliği | 1.367 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:inlet_w/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |
| 5000 | Siklon C5 | Giriş yüksekliği | 10.053 m | R | PF5000 × FLS:eff_over_shell[5] × FLS:inlet_h/D[5] | `CFD-ready` | w_in = 0.4 r_c FLS model varsayımı |

---

## 4. Başka tesislere ait ölçüler (öncelik 4): `reference-only`

INVENTORY.md B.1'den, ham metni doğrudan doğrulanmış kayıtlar. **Hepsi başka tesislere ya da seçilmemiş ekipman setlerine aittir. Modele doğrudan aktarılmaz.** Yalnızca karşılaştırma ve makullük kontrolü için kullanılabilirler.

| Hat/tesis | Ekipman | Parametre | Değer | P/R/M | Kaynak | Kategori | Not |
|---|---|---|---|---|---|---|---|
| PF2500 (seçilmeyen set) | Siklon C1 | Gövde çapı | 2 × Φ4.6 m | P | PF2500 | `reference-only` | 2500 önısıtıcısı HFC2500'den alındı |
| PF2500 (seçilmeyen set) | Siklon C2 / C3 | Gövde çapı | Φ6.5 / Φ6.5 m | P | PF2500 | `reference-only` | Aynı gerekçe |
| PF2500 (seçilmeyen set) | Siklon C4 / C5 | Gövde çapı | Φ6.8 / Φ6.8 m | P | PF2500 | `reference-only` | Aynı gerekçe |
| PF2500 (seçilmeyen set) | Kalsinatör | Φ × H | 5.05 × 30.0 m | P | PF2500 | `reference-only` | HFC kalsinatöründen farklı bir ekipman |
| PF2500 | Soğutucu | Model | LBT32216 | P | Pengfei 2500 | `reference-only` | Başka bir Pengfei sayfası LBT2500 veriyor |
| RSP1500 | Siklon C1 | Çap, öncesi → sonrası | φ3.1 → φ3.7 m | P | RSP1500 | `reference-only` | Başka tesis (RSP genişletmesi) |
| RSP1500 | Siklon C1–C5 | Vorteks bulucu çapı | 1.736, 2.484, 2.621, 2.701, 2.770 m | P | RSP1500 | `reference-only` | Başka tesis |
| RSP1500 | Siklon C1–C5 | Vorteks bulucu çapı / efektif çap | 0.46, 0.60, 0.63, 0.66, 0.62 | P | RSP1500 | `reference-only` | FLS oranlarından küçük; katalog FLS dışında oran kabul etmiyor |
| RSP1500 | Kalsinatör (MC odası) | Φ × H, hacim | φ4.3 × 13 m, 188 m³ | P | RSP1500 | `reference-only` | Başka tesis |
| RSP1500 | Kalsinatör | Alt boğaz kesiti | 0.9 × 0.9 → 1.11 × 1.11 m | P | RSP1500 | `reference-only` | Bulunan tek boğaz ölçüsü, başka tesise ait |
| RSP1500 | Kaz boynu | Φ × L | φ3.1 × 31 m | P | RSP1500 | `reference-only` | Başka tesis; gövde/efektif ve boyun ne olduğu belirsiz |
| RSP1500 | Kalsinatör + kaz boynu | Hacim | 422 m³ | P | RSP1500 | `reference-only` | — |
| RSP1500 | Tersiyer hava kanalı | Efektif çap | φ1577 mm | P | RSP1500 | `reference-only` | Tersiyer kanal kapsam dışı |
| RSP1500 | Fırın besleme bacası | Kesit | 6.4 × 2.96 m | P | RSP1500 | `reference-only` | Bulunan tek fırın girişi ölçüsü, başka tesise ait |
| RSP1500 | Fırın başlığı | Kesit | 6.4 × 3.77 m | P | RSP1500 | `reference-only` | — |
| RSP1500 | Kalsinatör kömür hattı | Taşıma borusu / meme | φ214 / φ151 mm | P | RSP1500 | `reference-only` | Kaynak kendi formülüyle hesaplamış |
| TCDRI5000 | Fırın | Φ × L | Ф4.8 × 72 m | P | TCDRI5000 | `reference-only` | PF5000'den farklı bir tesis |
| TCDRI5000 | Soğutucu | Izgara alanı | 119.3 m² | P | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Kalsinatör | Düz gövde yüksekliği; yükseltme | 22 m; +12.5 m | P | TCDRI5000 | `reference-only` | DD tipi kalsinatör; çap yayınlanmamış |
| TCDRI5000 | Kalsinatör | Düz gövde hacmi | 823 → 1290 m³ | P | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Kalsinatör çıkışı | Yükseltme sonrası konum | ≈13 m yukarı | P | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Kaz boynu | Kesit; yükseklik; hacim | 5.4 × 4.4 m dikdörtgen; 18 m; 330 m³ | P | TCDRI5000 | `reference-only` | Dikdörtgen kesit; boyu çelik taşıyıcı kirişlerine göre belirlenmiş |
| TCDRI5000 | Kalsinatör + kaz boynu | Hacim | 1620 m³ | P | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Kalsinatör → C5 (özgün) | Bağlantı biçimi | Yatay kanal, ölçü yok | P (nitel) | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Tersiyer hava kanalı | Yatay boy; dirsek sayısı | 34.4 m; 4 × 90° | P | TCDRI5000 | `reference-only` | Tersiyer kanal kapsam dışı |
| TCDRI5000 | Tersiyer girişi | Kalsinatörde kapladığı yükseklik | ≈3 m; 2.3 m | P | TCDRI5000 | `reference-only` | — |
| TCDRI5000 | Siklon C5 volüt | Biçim; eksantriklik; giriş kesiti | 270°, üç merkezli; 450 mm; 8.1 m² | P | TCDRI5000 | `reference-only` | Bulunan tek volüt ölçüsü; katalogda volüt modellenmiyor |
| HB | Siklon kademesi | "Typical figures" | "α max 25°", "β ≈ 65°" | P (OCR) | HB | `blocked` | OCR bozuk; açıların neyi gösterdiği belirsiz |

---

## 5. Dahil edilmeyenler (öncelik 5)

- **B.2** (yalnızca araştırma ajanının gördüğü 2 kayıt) ve **B.3** (yalnızca özet ya da arama parçacığından gelen 27 `P?` kayıt) CFD çalışma verisine **dahil edilmedi**.
- B.3'teki hiçbir değer, ham kaynak metni okunup doğrulanmadan kullanılmayacak. Bu değerler yalnızca INVENTORY.md'de, aramanın izi olarak durur.
- Geometrik olmayan değerler (hızlar, kalma süreleri) INVENTORY.md C bölümündedir; burada yer almaz.

---

## 6. İlk CFD için kullanılacak veri seti

**Kapsam:** 2500 hattında **tek bir siklonun** akışkan hacmi (`geometry/components.py`). Her kademe için aynı sekiz ölçü gerekir. Bunlar katalogdaki 2500 değerleridir ve hepsi `CFD-ready`.

**İlk prototip: 2500 hattının C2 siklonu** (kullanıcı kararı, 2026-09-21). Gerekçe: C2–C5 ölçüleri, C1'e özgü aktarım varsayımına (FLS'nin tek üst siklonundan çoklu C1'e aktarım) dayanmaz; bu yüzden C2 ilk prototip için daha temiz bir referanstır. Beş kademelik veri seti, diğer kademeler için referans olarak aşağıda olduğu gibi korunur.

| Parametre | C1 (×2) | C2 | C3 | C4 | C5 | P/R/M | Kaynak |
|---|---|---|---|---|---|---|---|
| Efektif iç çap [m] | 4.32 | 6.1 | 6.3 | 6.3 | 6.5 | P | HFC2500 |
| Silindirik gövde yüksekliği [m] | 6.793 | 3.667 | 3.215 | 3.455 | 3.535 | R | HFC2500 × FLS:barrel_h/D[Cy_k] |
| Koni yüksekliği [m] | 4.652 | 6.511 | 7.26 | 7.296 | 7.427 | R | HFC2500 × FLS:cone_h/D[Cy_k] |
| Vorteks bulucu boyu [m] | 2.16 | 3.05 | 3.15 | 3.168 | 3.25 | R | HFC2500 × FLS:vortex_len/D[Cy_k] |
| Vorteks bulucu çapı [m] | 2.404 | 4.347 | 4.622 | 4.631 | 4.737 | R | HFC2500 × FLS:vortex_D/D[Cy_k] |
| Toz çıkışı çapı [m] | 0.401 | 0.805 | 0.839 | 0.808 | 0.826 | R | HFC2500 × FLS:dust_D/D[Cy_k] |
| Giriş genişliği [m] | 0.864 | 1.225 | 1.258 | 1.265 | 1.304 | R | HFC2500 × FLS:inlet_w/D[Cy_k] |
| Giriş yüksekliği [m] | 4.968 | 8.709 | 9.458 | 9.439 | 9.588 | R | HFC2500 × FLS:inlet_h/D[Cy_k] |

Ölçüler üzerine notlar:
- **Efektif çap** HFC2500'de yayınlanmış (P). Diğer yedi ölçü FLS'nin aynı numaralı kademesinin oranıyla türetilmiş (R).
- **C1:** Değerleri FLS'nin tek, büyük üst siklonundan çoklu C1'e aktarım varsayımı taşır. Kademe iki siklondan oluşur; burada bir tanesi verilmiştir.
- **Giriş genişliği ve yüksekliği:** FLS'nin `w_in = 0.4 r_c` model varsayımına dayanır. C2–C5'te yayınlanmış giriş yüksekliği gövdeden uzundur, bu yüzden kanal koni bölgesine iner.
- **Toz çıkışı:** Çıkış sınır yüzüdür; farin borusu yok.
- **Volüt:** Modellenmiyor; giriş düz ve teğet bir kanaldır.

Katıyı kurmak için ayrıca şu **CFD modelleme parametreleri** gerekir. Bunlar tesis ölçüsü değildir ve kaynakları yoktur:

| Parametre | Değer | Durum |
|---|---|---|
| `inlet_extension_over_D` | 0.6 | CFD modelleme parametresi (`geometry.cfd_boundary`); tesis ölçüsü değil, kaynağı yok |
| `outlet_extension_over_vortex_D` | 1.0 | CFD modelleme parametresi (`geometry.cfd_boundary`); tesis ölçüsü değil, kaynağı yok |
| `vortex_finder_wall_m` | 0.012 | CFD modelleme parametresi (`geometry.cfd_boundary`); tesis ölçüsü değil, kaynağı yok |

**Hacim ayrımı:** Kalma süresi gibi fiziksel hesaplarda **ekipman hacmi** kullanılır (`properties.py`, `body_volume`). CFD katısının hacmi ise giriş ve çıkış uzatmalarını da içerir. Örneğin C2'nin ekipman hacmi 180.1 m³, CFD katısı 273.1 m³.

**Bu veri setine girmeyenler:**
- Riserler, kaz boynu ve kule. Riser boyları, kaz boynu boyu ve riser şekli `blocked`.
- Tersiyer kanal ve fırın giriş odası: kapsam dışı ya da kaynaksız.
- Bölüm 4'teki `reference-only` değerler.
