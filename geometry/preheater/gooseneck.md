# Gooseneck (kaz boynu)

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§5, Ek). Referans hat: 2500 t/d.
Bağlantı: kalsinatör tepesi → C5.

## Geometrik Ölçüler

Efektif iç çap: 3.50 m — (P) yayınlanmış
Boy: TBD — Hiçbir kaynakta yok

## CFD Geometry

Kaz boynu, kalsinatör katısının bir parçası olarak kurulur ([calciner.md](../calciner/calciner.md), [`calciner.bas`](../macros/calciner.bas)).

CFD'de kaz boynu **çift koldur**: tavandan iki kol çıkar, her biri dışarı döner ve kendi çıkış yüzüne iner. Her kolun çapı **Ø2.475 m**'dir, yani yayınlanmış Ø3.50'nin alanının yarısı; toplam kesit korunur. Gerekçe: Ø3.50'lik iki boru Ø5.50'lik tavana sığmaz (kullanıcı kararı, 29 Eylül 2026).

Boylar yayınlanmamıştır; C1 makrosunun modelleme oranları kullanılır:
- yükseliş 1.25 D = 3.094 m
- 180° dirsek, R = 1.5 D = 3.712 m
- iniş 3.094 m

## Boundary Faces

`gas_outlet_1` (+x) ve `gas_outlet_2` (−x): inen boruların aşağı bakan diskleri, her biri 4.811 m².

## Derived Properties

İki kolun toplam hacmi: 171.735 m³ (2 yükseliş + 2 dirsek + 2 iniş).
