# Twin hacim defteri

Twin'in her bölgesinin hangi akış hacmi üzerinden hesap yaptığı ve bu hacmin hangi dokümandan geldiği (kullanıcı, 13 Ekim 2026: "her ekipmanın gerçekten bir akış hacmi üzerinden hesaplama yaptığından emin olmalıyız"). `tests/test_fluid_volumes.py` bu tabloyu twin'e karşı denetler: her bölgenin hücre hacimlerinin toplamı dokümandaki "Ekipman hacmi"ne ‰1 içinde eşit olmalıdır.

Tesis iki özdeş 2500 t/d hattıdır ([plant_topology.md](plant_topology.md)). Twin tek hattı toplam debiyle çözer, bu yüzden hat başına ekipmanların hacimleri ve duvar alanları ×2 alınır. Bu, toplanmış (lumped) bir modelde iki hattın tam eşdeğeridir.

## Bölgeler

| Twin bölgesi | Ekipman | Doküman hacmi [m³] | Twin hacmi [m³] | Durum |
|---|---|---|---|---|
| Ön ısıtıcı, kademe 1 | C5 (×2) | 622.0 | 69.3 | ✘ Ø4.2 × 25 m yer tutucunun beşte biri |
| Ön ısıtıcı, kademe 2 | R4 + C4 (×2) | 970.9 | 69.3 | ✘ |
| Ön ısıtıcı, kademe 3 | R3 + C3 (×2) | 947.2 | 69.3 | ✘ |
| Ön ısıtıcı, kademe 4 | R2 + C2 (×2) | 908.0 | 69.3 | ✘ |
| Ön ısıtıcı, kademe 5 | R1 + 2 C1 (×2) | 814.7 | 69.3 | ✘ |
| Kalsinatör | kalsinatör (koni + gövde) | 1009.71 | 1070.4 | ≈ Ø6.74 × 30 m silindir; koni yok |
| — | kaz boynu (Y) | 833.77 | — | ✘ Twin'de yok |
| Geçiş | fırının arka 30.83 m'si | 557.89 | 557.89 | ✔ |
| Yanma | fırının ön 43.17 m'si | 781.19 | 781.19 | ✔ |
| Soğutucu | ızgara kutusu | 358.80 (yatak ~48.9) | yatak w·h·dz | ✔ Alışverişler yatak hacminde, gövde duvarı kutunun |

Kademe hacimleri:
- Siklon: gövde + koni ([cyclone_C1.md](preheater/cyclone_C1.md) … [cyclone_C5.md](preheater/cyclone_C5.md)). C2–C4 CFD gövdesiyle 283.2 m³, C5 311.0 m³, C1 124.54 m³ ve hatta iki tane.
- Riser: yayınlanmış çap × FLS boyu, düz silindir ([riser_R1.md](preheater/riser_R1.md) … [riser_R4.md](preheater/riser_R4.md)): R1 158.26, R2 170.82, R3 190.42, R4 202.25 m³.
- Twin kademesi = alttaki riser'daki eş akımlı alışveriş + siklon (`pyroprocess/preheater/heat_transfer.py`). C5'i riser değil kaz boynu kolu besler; o hacim kalsinatör bölgesindedir.

## Hacmi olmayan ekipman (kaynak yok)

Bunlar twin'de yalnız akım devridir: hacim, duvar kaybı ve gecikme yoktur. Ölçüleri bir kaynaktan gelince bölge olarak eklenirler.

| Ekipman | Twin'de | Eksik olan |
|---|---|---|
| Tersiyer hava kanalı | soğutucunun tersiyer havası doğrudan kalsinatör girişine | boy (Ø2.439 türetilmiş; FLS R5 61 m, r 1.13 m, ama makale onu tersiyer kanal diye adlandırmaz) |
| Fırın başlığı | sekonder hava doğrudan yanma bölgesi girişine | bütün ölçüler (çizimde şematik) |
| Fırın giriş odası | fırın gazı doğrudan kalsinatöre, kalsinatör katısı doğrudan fırına | bütün ölçüler ([kiln_inlet_chamber.md](kiln/kiln_inlet_chamber.md): TBD) |
| Soğutucu vent'i | kütle artığı | `vent_outlet` ölçüsü ([cooler.md](cooler/cooler.md): TBD) |
| Farin boruları | farin doğrudan bir sonraki kademeye | hacim: — (meal_pipe_C*.md) |
