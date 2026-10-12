# Katalog ölçüleri

Üç referans hattın yayınlanmış ve türetilmiş ölçüleri. Bileşen dokümanları
(`geometry/<ekipman>/*.md`) yalnızca 2500 hattını anlatır; başka bir hattı ya da
`cyclone.bas` ile başka bir kademeyi kurmak isteyen buradaki sayıları kullanır.

Bu tablo `geometry/catalog.py` içinde yaşıyordu ve değerleri `tests/test_geometry_catalog.py`
sabitliyordu. Paket `c99b93a` ile kaldırıldı, testler de yetim kaldığı için silindi;
sayıların kendisi burada kaldı. Kod hâlâ gerekirse: `git show c99b93a^:geometry/catalog.py`.

## Siklonlar

Metre. Sütunlar: `D, barrel_h, cone_h, vortex_len, vortex_D, dust_D, inlet_w, inlet_h`.

### 1500 t/d

| Kademe | D | barrel_h | cone_h | vortex_len | vortex_D | dust_D | inlet_w | inlet_h |
|---|---|---|---|---|---|---|---|---|
| C1 | 4.132 | 6.50 | 4.45 | 2.07 | 2.30 | 0.38 | 0.83 | 4.75 |
| C2 | 5.319 | 3.20 | 5.68 | 2.66 | 3.79 | 0.70 | 1.07 | 7.59 |
| C3 | 5.272 | 2.69 | 6.08 | 2.64 | 3.87 | 0.70 | 1.05 | 7.91 |
| C4 | 5.537 | 3.04 | 6.41 | 2.78 | 4.07 | 0.71 | 1.11 | 8.30 |
| C5 | 5.584 | 3.04 | 6.38 | 2.79 | 4.07 | 0.71 | 1.12 | 8.24 |

### 2500 t/d — referans hat

| Kademe | D | barrel_h | cone_h | vortex_len | vortex_D | dust_D | inlet_w | inlet_h |
|---|---|---|---|---|---|---|---|---|
| C1 | 4.32 | 6.79 | 4.65 | 2.16 | 2.40 | 0.40 | 0.86 | 4.97 |
| C2 | 6.10 | 3.67 | 6.51 | 3.05 | 4.35 | 0.80 | 1.23 | 8.71 |
| C3 | 6.30 | 3.22 | 7.26 | 3.15 | 4.62 | 0.84 | 1.26 | 9.46 |
| C4 | 6.30 | 3.46 | 7.30 | 3.17 | 4.63 | 0.81 | 1.27 | 9.44 |
| C5 | 6.50 | 3.53 | 7.43 | 3.25 | 4.74 | 0.83 | 1.30 | 9.59 |

### 5000 t/d

| Kademe | D | barrel_h | cone_h | vortex_len | vortex_D | dust_D | inlet_w | inlet_h |
|---|---|---|---|---|---|---|---|---|
| C1 | 4.805 | 7.56 | 5.17 | 2.40 | 2.67 | 0.45 | 0.96 | 5.53 |
| C2 | 6.554 | 3.94 | 7.00 | 3.28 | 4.67 | 0.86 | 1.32 | 9.36 |
| C3 | 6.496 | 3.32 | 7.49 | 3.25 | 4.77 | 0.86 | 1.30 | 9.75 |
| C4 | 6.757 | 3.71 | 7.83 | 3.40 | 4.97 | 0.87 | 1.36 | 10.12 |
| C5 | 6.815 | 3.71 | 7.79 | 3.41 | 4.97 | 0.87 | 1.37 | 10.05 |

## Riser iç çapları

R1–R4, metre. R_k, Cy(k+1)'den çıkar.

| Hat | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| 1500 | 3.82 | 3.82 | 4.02 | 4.02 |
| 2500 | 3.07 | 3.35 | 3.45 | 3.60 |
| 5000 | 4.71 | 4.71 | 4.91 | 4.91 |

## Provenance

Her değer ya **yayınlanmış** ya da **tek bir adlandırılmış FLS oranından türetilmiş**;
hiçbir kaynağın vermediği ölçü tahmin edilmez, `TBD` kalır. Yayınlanmış olanlar
genellikle yalnızca efektif iç çap D'dir; gövde yüksekliği, koni, vorteks bulucu,
toz çıkışı ve giriş ölçüleri D'den FLS oranlarıyla türetilir.

Tanımlı FLS oranları:

```
eff_over_shell   barrel_h/D   cone_h/D   vortex_len/D   vortex_D/D
dust_D/D   inlet_w/D   inlet_h/D   riser_D/D_src
calciner_eff_over_shell   calciner_H/D   kiln_eff_over_shell
```

## Kaynaklar

| Anahtar | Kaynak |
|---|---|
| `PF1500` | Jiangsu Pengfei, 1500 t/d hattı — <http://www.cementplant-engineering.com/products/cement-production-line/77.html> |
| `PF2500` | Jiangsu Pengfei, "3000tpd" başlıklı sayfa, fırın sistemi 2500 t/d — <https://www.cementmachinery.com/Cement_Machinery/products/Production_line_EP_EPC/Cement_Production_Line/2020/0331/2670.html> |
| `HFC2500` | Hefei enstitüsü, HFC2500 t/d preheater-kalsinatör tasarımı, 2005 — <https://m.ccement.com/news/content/700825.html> |
| `PF5000` | Jiangsu Pengfei, 5000 t/d hattı — <https://jspengfei.en.made-in-china.com/product/BewmtGNcXDha/China-5000t-D-Cement-Production-Line.html> |
| `FLS` | Svensen ve diğerleri, FLSmidth referans senaryosu, arXiv 2504.02886, Tablo 8 — <https://arxiv.org/abs/2504.02886> |

## Bu tablodan sapmalar

Bir bileşen dokümanı katalog değerinden bilerek sapabilir; sapma o dokümanda gerekçesiyle
yazılır ve bu tablo değişmez. Şu anki sapmalar:

- [cyclone_C1.md](preheater/cyclone_C1.md) — giriş yüksekliği 4.97 yerine **2.16 m**.
  Yayınlanmış uzun giriş 270°'lik volütle beslendiği için anlamlı; CFD modeli volütü
  kurmadığından gerekçesini kaybediyor.
- [cyclone_C4.md](preheater/cyclone_C4.md) — CFD'de giriş 1.27 × 9.44 yerine **volütlü 3.40 × 2.912 m**
  (aynı alan). Katalog girişi gövde ile vorteks bulucu arasına sığmıyor ve koninin dibine iniyor; tesis
  bunu volütle çözer, model de basit bir volüt kurar. Gövde **3.46 yerine 6.30 m** (h = D): FLS oranı
  vorteks bulucu ağzını koninin 0.29 m üstüne koyuyordu (kullanıcı kararları, 4 Ekim 2026). Daldırma
  **3.17 yerine 3.90 m** (S/a 1.15): katalog daldırması 3.40 m'lik girişten kısaydı, ağız giriş tabanının
  üstünde kalıyordu (kullanıcı kararı, 5 Ekim 2026). C2 ve C3
  C4 ile özdeş olduğu için aynı sapmaları taşır.
- [cyclone_C2.md](preheater/cyclone_C2.md), [cyclone_C3.md](preheater/cyclone_C3.md) — ara kademeler
  **C4 ile özdeş** (kullanıcı kararı, 27 Eylül 2026). C1 (üst, ikiz) ve C5 (alt) kendi ölçülerini
  koruyor. C3 ve C4'ün yayınlanmış çapı zaten ortak (6.30 m) ve oranları birkaç yüzde içinde;
  asıl değişen C2 (6.10 → 6.30 m). Gerekçe: tek bir ara kademe CFD'si C2–C4'ü ölçeklemesiz
  temsil eder; kademeler arasındaki gaz hacmi farkı ölçülere değil giriş hızına yansır ve
  Euler sayısı üzerinden taşınır. Birçok tesiste ara kademeler aynı gövde ölçüsüyle yapılır.
  C5 bilerek dışarıda: çapı yayınlanmış (6.50 m) ve en sıcak, en büyük hacimli gazı taşıdığı
  için büyük; 6.30'a indirmek giriş hızını ~%6.5, ΔP'yi ~%13 artırırdı. Oranları ara kademeyle
  %1–2 içinde aynı olduğundan ΔP'si ara kademe CFD'sinin Euler sayısıyla ölçeklenir. Bunun
  birebir geçerli olması için C5, CFD'deki C4'ün benzer ölçeklenmiş hâli olarak kurulur
  (aşağıda).
- [riser_R1.md](preheater/riser_R1.md) — CFD'de C1'in önüne eklenen riser yuvarlak **Ø2.171 m**:
  yayınlanmış Ø3.07 m ikiz C1'leri birlikte beslediği için C1 başına alanının yarısı. 1.5 m'lik
  bir geçişle C1 giriş kanalına (0.86 × 2.16) bağlanır (kullanıcı kararı, 29 Eylül 2026).
  Riser'ın boyları yayınlanmamış, CFD için türetilmiştir; tablo değişmez.
- [calciner.md](calciner/calciner.md) — tesisin kalsinatörü **5000 t/d**: PF5000 gövdesi Ø7.2 → efektif
  Ø6.74 (FLS oranı), 30.0 m (yayınlanmış). Boğaz ve tersiyer kanal 2500 sınıfının literatür akışlarının
  iki katından türetilir (kullanıcı kararı, 12 Ekim 2026).
- [gooseneck.md](preheater/gooseneck.md) — kaz boynu CFD'de bir **Y**: tavandan Ø4.95 tek boyun, tepesinde
  iki Ø3.50 kol. Her kol bir hattın gazını taşır, yani yayınlanmış 2500 boynunun çapındadır; iki Ø3.50
  boru Ø6.74'lük tavana sığmadığı için boyun ortaktır (kullanıcı kararı, 12 Ekim 2026). Önceki 2500
  kalsinatöründe iki ayrı Ø2.475 kol vardı (29 Eylül 2026).
- [cyclone_C5.md](preheater/cyclone_C5.md) — **hat başına bir C5**, D yayınlanmış 6.50 m. Diğer
  ölçüler tablodan değil, **CFD'deki C4'ün ölçüleri × 6.50 / 6.30**: C4'ün sapmalarını (volüt, h = D,
  S/a 1.15) taşır, onunla tam geometrik benzerdir. Euler sayısı ve volüt α'sı ölçeklemesiz geçer
  (kullanıcı kararı, 12 Ekim 2026). Önceki ikiz C5 düzeni (29 Eylül 2026, her biri × 1/√2) kalktı.

**Tesis: iki özdeş 2500 t/d hattı** (kullanıcı kararı, 12 Ekim 2026). Toplam kapasite 5000 t/d. Her
hat bu tablonun 2500 satırı ve yukarıdaki sapmalarla kurulur; her hatta ikiz C1, C2, C3, C4 ve C5,
toplam 12 siklon. Siklonlar CFD'si çözülen ölçülerdedir; ikinci hat birinin kopyasıdır. Kalsinatör,
kaz boynu, TAD, fırın ve soğutucu 5000 t/d'nindir (PF5000, [plant_topology.md](plant_topology.md)). Fırın
2500'deki kuralla: yayınlanmış gövde çapı efektif çap, eğim %3 (kullanıcı kararı, 12 Ekim 2026).
