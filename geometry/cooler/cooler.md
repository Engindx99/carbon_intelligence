# Cooler (soğutucu)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, Ek). Tesis: 5000 t/d ([plant_topology.md](../plant_topology.md)). Kule dışı.
Tip: ızgaralı soğutucu (grate cooler), çapraz akış: hava ızgaranın altından yatağın içinden yukarı geçer, klinker ızgara boyunca ilerler.
Kaynak: Jiangsu Pengfei 5000 t/d hattı (PF5000; değerler `c99b93a^:geometry/catalog.py`'de kayıtlıydı) ve FLS referans soğutucusu (Svensen ve diğ. 2024, aşağıda).

12 Ekim 2026'ya kadar 2500 t/d hattının soğutucusuydu: 65 m², Jiangsu Pengfei 2500.

## Kaynaklar

| ID | Kaynak | İçerik |
|---|---|---|
| **PF5000** | Jiangsu Pengfei 5000 t/d hattı ([geometry/catalog.md](../catalog.md)) | Soğutucu LBT36352, ızgara alanı 119.6 m² |
| **FLS-cooler** | Svensen, Leal da Silva, Pigazo Merino, Sampath, Jørgensen, "A Dynamic Cooler Model for Cement Clinker Production", arXiv:2409.09076 (2024), §IV ve Tablo II | "We consider a 36 m long cooler with 4 m width and 3 m tall." "191 ton/h clinker production." "The grate belts were run uniformly with a residence time of 36 min, 0.017 m/s." "We use a 10-segment model". Segment havaları 40.89 / 18.56 / 8 × 16.24 kg/s; gözeneklilik 0.4 (kaynak [3]); katı yoğunlukları (Tablo II, g/cm³): C3S 3.13, C3A 3.04, C4AF 3.7–3.9 |

FLS soğutucusu, twin'in çapraz akış hücre yapısının da kaynağıdır (`pyroprocess/cooler/gas_phase.py`). 191 t/h ≈ 4600 t/d ile 5000 t/d tesise en yakın yayınlanmış ızgara.

## Geometrik Ölçüler

| Ölçü | Değer | Kaynak / türetme |
|---|---|---|
| Izgara alanı | 119.6 m² | PF5000 (yayınlanmış) |
| Izgara genişliği w | 4.0 m | FLS-cooler (yayınlanmış) |
| Izgara boyu L | **29.90 m** | 119.6 / 4.0 (türetilmiş; kullanıcı kararı, 13 Ekim 2026: alan tesisin, genişlik FLS'nin) |
| Gövde yüksekliği H | 3.0 m | FLS-cooler (yayınlanmış): ızgaradan tavana, yatak ve üstündeki hava |
| Yatak gözenekliliği ε | 0.4 | FLS-cooler, kaynağının [3] değeri |
| Klinker katı yoğunluğu ρ_s | 3178 kg/m³ | Tablo II, FLS klinker bileşiminde (%79.96 C3S, 9.76 C3A, 10.28 C4AF) kütle-ağırlıklı harmonik ortalama; C4AF için 3.7–3.9'un ortası 3.8 (türetilmiş) |
| Yığın yoğunluğu ρ_b | 1907 kg/m³ | (1 − ε) ρ_s (türetilmiş) |
| Tasarım yatak derinliği h₀ | **0.409 m** | FLS sürekliliği: ṁ = ρ_b w h v → 53.06 kg/s / (1907 · 4.0 · 0.017) (türetilmiş) |
| Izgara hızı v | **0.01854 m/s** | 5000 t/d = 57.87 kg/s klinkerin h₀'da taşınması: ṁ / (ρ_b w h₀) (türetilmiş) |
| Kalma süresi | 26.9 dk | L / v (FLS-cooler: 36 m / 0.017 m/s = 35.3 dk, metinde "36 min") |

**Yatak derinliği bir işletme sonucudur, sabit bir ölçü değildir** (kullanıcı kararı, 13 Ekim 2026). Izgara hızı operatörün girdisidir; klinker debisi değişince yatak derinliği h = ṁ / (ρ_b w v) ile değişir. h₀ yalnız tasarım noktasıdır. Twin'in bugünkü şişkin klinker debisinde (~69.9 kg/s, eksik kalsinasyon) yatak 0.49 m'dir.

## CFD Geometry

Makro yok: soğutucu CFD'si henüz planlı değil, akış hacmi bu dokümanda tanımlanır (kullanıcı kararı, 13 Ekim 2026). Kurulduğunda `calciner.bas` düzenini izler.

Koordinatlar: **x** ızgara boyunca, sıcak uçta (başlığın altı, klinkerin düştüğü yer) **x = 0**; **y** genişlik, eksende y = 0; **z** ızgara düzleminden yukarı.

```
gövde (akış hacmi)  kutu, x 0 .. 29.90, y ±2.00, z 0 .. 3.00
klinker yatağı      kutunun alt dilimi, z 0 .. h (tasarımda h₀ = 0.409)
                    gözenekli bölge: ε 0.4, katı x yönünde v = 0.01854 m/s ile hareket eder
hava boşluğu        z h .. 3.00
```

En basit yeterli hacim budur: ızgara plakaları, bölme (compartment) duvarları, kırıcı ve klinker düşme kanalı yoktur. Yatak ayrı bir gövde değil, kutunun içinde bir hücre bölgesidir (Fluent'te gözenekli bölge ya da hareketli yatak). Bölmeler yalnız taban yüzünün bölünmesiyle temsil edilir.

## Boundary Faces

| Ad | Tip | Alan |
|---|---|---|
| `grate_air_1` … `grate_air_10` | mass-flow-inlet | Taban (z = 0), FLS'nin 10 segmentine bölünmüş: her biri 2.990 × 4.0 m = 11.96 m² |
| `hood_opening` | pressure-outlet | Tavan (z = 3.0), sıcak uçtaki ilk iki segmentin üstü: x 0 .. 5.98, 23.92 m². FLS'de 1. segmentin havası fırına (sekonder), 2.'ninki tersiyere gider; ikisi de başlıktan çıkar |
| `vent_outlet` | pressure-outlet | TBD: yeri soğuk uçta tavan, ölçüsü için kaynak yok. Gerekirse kalsinatör boğazı gibi literatür debisi ÷ literatür hızıyla türetilir |
| `wall` | wall | Geri kalan: iki yan duvar, iki uç duvar, tavanın açık olmayan kısmı |

Klinkerin giriş ve çıkış yüzleri yoktur: yatak bir bölgedir, katı hızı orada verilir.

## Derived Properties

```
gövde hacmi        29.90 × 4.0 × 3.0   = 358.80 m³
tasarım yatağı     29.90 × 4.0 × 0.409 =  48.93 m³
tasarım birikimi   1907 × 48.93        ≈  93.3 t klinker
segment            2.990 × 4.0         =  11.96 m²
```

Ekipman hacmi: **358.80 m³**.
