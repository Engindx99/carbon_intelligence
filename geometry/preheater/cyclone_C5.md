# Cyclone C5

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §6, Ek). Referans hat: 2500 t/d.
**İkiz siklon** (kullanıcı kararı, 29 Eylül 2026): kalsinatörün çift kaz boynunun her kolu kendi C5'ine iner.
Farin borusu: [meal_pipe_C5.md](meal_pipe_C5.md)

## Geometrik Ölçüler

Yayınlanmış çap, tek bir C5'in tüm gaz akışını taşıdığı düzen içindir. İkiz düzende her C5 akışın yarısını taşır. Bu yüzden katalogdaki bütün ölçüler **1/√2 ile benzer ölçeklenir**:
- Giriş kesiti yarıya iner; giriş hızı ve bütün boyutsuz oranlar korunur.
- ΔP'nin ara kademe CFD'sinden Euler sayısıyla ölçeklenmesi olduğu gibi geçerli kalır.
- Bu, R1 riser'ında ve kaz boynunda uygulanan alan bölümü kuralının aynısıdır.

| Ölçü | Katalog (tek C5) | İkiz C5, her biri |
|---|---|---|
| Efektif iç çap, D | 6.50 m — HFC2500 (yayınlanmış) | **4.596 m** |
| Silindirik gövde yüksekliği | 3.53 m — FLS oranı | 2.496 m |
| Koni yüksekliği | 7.43 m — FLS oranı | 5.254 m |
| Vorteks bulucu çapı | 4.74 m — FLS oranı | 3.352 m |
| Vorteks bulucu boyu (daldırma) | 3.25 m — FLS oranı | 2.298 m |
| Toz çıkışı çapı | 0.83 m — FLS oranı | 0.587 m |
| Giriş genişliği | 1.30 m — FLS oranı | 0.919 m |
| Giriş yüksekliği | 9.59 m — FLS oranı | 6.781 m |

Volüt geometrisi: TBD — 2500 hattı için kaynak yok.

## CFD Geometry

İki C5 birebir aynıdır. **Tek bir C5 çözülür**, ikincisi onun kopyası olarak sayılır; her biri kalsinatörün bir `gas_outlet` yüzünden (Ø2.475) beslenir. Kalsinatör ile C5 arasındaki bağ, sınır yüzleri üzerinden kurulur: `gas_outlet_1/2` profilleri C5 girişine aktarılır. İki problem aynı mesh'e konmaz.

Katı henüz yok. `cyclone.bas` ile sağdaki sekiz sayıdan kurulabilir. Yuvarlak Ø2.475 inişten dikdörtgen girişe geçiş, C1 riser'ındaki loft ile aynı yoldan yapılır. Giriş, katalogdaki gibi gövdeden uzundur ve koniye iner; `cyclone.bas` bunu katalog ne diyorsa öyle kurar.

## Boundary Faces

TBD (katı yok).

## Derived Properties

Ekipman hacmi, her biri: **74.67 m³** (tek C5: 211.2 m³ × (1/√2)³). İki C5'in toplamı 149.3 m³; tek C5'e göre %29 daha az hacim, yani aynı giriş hızında kalma süresi 1/√2 kat kısalır. İkizin önısıtıcı modeli bu hacmi okumaz ve değişmez.
