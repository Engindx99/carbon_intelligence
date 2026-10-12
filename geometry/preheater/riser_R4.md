# Riser R4

Kaynak doküman: `geometry/CFD_VIEW.pdf` (§1, §5, Ek). Referans hat: 2500 t/d.
Bağlantı: C5 → C4 (CFD_VIEW.pdf: "Riserler R1–R4 (C2→C1 … C5→C4)").

## Geometrik Ölçüler

Efektif iç çap: 3.60 m — HFC2500 (yayınlanmış)
Boy: 19.87 m — FLS R4'in `h_tot`'u, arXiv 2504.02886 Tablo 8 (yayınlanmış; tesis riser'ının boyu yayınlanmamış, FLS'ninki aktarıldı)
Şekil: düz silindir, tesisin yayınlanmış çapıyla (kullanıcı kararı, 13 Ekim 2026). FLS'de metin ile denklemler riser'ın uç konisinde çelişiyor (`c99b93a^:geometry/SOURCES.md`, "Açık belirsizlikler"). İki okuma `h_tot`'ta birleşir, koni yalnız FLS'nin kendi çaplarına aittir; aradaki hacim farkı ≤ %6. 21 Eylül 2026'daki "riser hacmi hesaplanmaz" kararının yerini bu karar aldı: twin'in ön ısıtıcı kademesi riser + siklon hacmiyle çalışır.
Dirsek geometrisi: TBD — `LayoutParams` alanı tanımlı, değeri yok

## CFD Geometry

Riser katısı ve hacmi yok.

## Boundary Faces

TBD (riser katısı yok).

## Derived Properties

Ekipman hacmi: 202.25 m³ (π/4 · 3.60² · 19.87; hat başına bir riser)
Duvar alanı: 224.72 m² (π · 3.60 · 19.87)
