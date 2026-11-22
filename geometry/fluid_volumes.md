# Twin hacim defteri

Twin'in her bölgesinin hangi akış hacmi üzerinden hesap yaptığı ve bu hacmin hangi dokümandan geldiği (kullanıcı, 13 Ekim 2026: "her ekipmanın gerçekten bir akış hacmi üzerinden hesaplama yaptığından emin olmalıyız").

Bütün ölçüler tek kaynaktan gelir (kullanıcı kararı, 14 Ekim 2026): `geometry/plant_geometry.yaml` ana ölçüleri bir kez yazar, `geometry/plant_geometry.py` hacimleri ve alanları türetir, twin onları `main.load_cfg` ile alır. `configs/twin_cfg.yaml` geometri yazmaz; yazarsa yükleyici reddeder. `tests/test_fluid_volumes.py` her bölgenin hücre hacimleri toplamının buradaki hacme eşit olduğunu denetler.

Tesis iki özdeş 2500 t/d hattıdır ([plant_topology.md](plant_topology.md)). Twin tek hattı toplam debiyle çözer, bu yüzden hat başına ekipmanların hacimleri ve duvar alanları ×2 alınır. Bu, toplanmış (lumped) bir modelde iki hattın tam eşdeğeridir.

## Bölgeler

Kademe numaraları twin'in gaz sırasıdır (kademe 1 = C4). Ön ısıtıcı satırları riser + siklon.

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Twin bölgesi | Ekipman | Hacim [m³] |
|---|---|---|
| Ön ısıtıcı, kademe 1 | R4 + 1 C4 (×2) | 285.43 + 566.49 = **851.92** |
| Ön ısıtıcı, kademe 2 | R3 + 1 C3 (×2) | 274.01 + 566.49 = **840.51** |
| Ön ısıtıcı, kademe 3 | R2 + 1 C2 (×2) | 274.01 + 566.49 = **840.51** |
| Ön ısıtıcı, kademe 4 | R1 + 2 C1 (×2) | 390.69 + 498.16 = **888.86** |
| Kalsinatör bölgesi | kalsinatör gövdesi, farin girişinden tavana (yakıt burada) | **775.91** |
| Kalsinatör bölgesi | kaz boynu, C5 girişlerine kadar | **684.84** |
| Kalsinatör bölgesi | C5 (×2) | **622.17** |
| Geçiş | fırının arka 30.83 m'si | **557.89** |
| Yanma | fırının ön 43.17 m'si | **781.19** |
| Soğutucu | ızgara kutusu | **358.80** |
<!-- END GENERATED -->

- **Siklon:** gövde + koni ([cyclone_C1.md](preheater/cyclone_C1.md) … [cyclone_C5.md](preheater/cyclone_C5.md)). C2–C4 C4'ün CFD gövdesiyle, C5 onun × 6.50 / 6.30'u; C1 hatta iki tane.
- **Riser:** R2–R4 alttaki siklonun CFD çıkış borusudur: çatının üstündeki yükseliş, 90° dirsek ve üstteki siklona yatay bacak, vorteks bulucu çapında. R1, C2'nin çıkış borusu, R1'in Y'ye kadar dik kısmı ve ikiz C1 kolları ([riser_R1.md](preheater/riser_R1.md) … [riser_R4.md](preheater/riser_R4.md); kullanıcı kararı, 14 Ekim 2026). 13–14 Ekim 2026 arasında twin yayınlanmış riser çaplarıyla FLS boylarını kullanıyordu (R1–R4 158–202 m³); onlar bu tesisin değil.
- **Twin kademesi** = alttaki riser'daki eş akımlı alışveriş + siklon (`pyroprocess/preheater/heat_transfer.py`).
- **Kalsinatör bölgesi** tek bir kanaldır (`calciner.zone_segments`): gövdenin farin girişinden yukarısı (yakıt burada yanar; alttaki gaz-yalnız kısmın duvarı da buna eklenir), C5 girişlerine kadar kaz boynu ve iki C5. C5'i riser değil kaz boynu kolu besler. Kalsinatör CFD'si kaz boynunu gövdenin yarı yüksekliğinde keser (833.77 m³); tesisin ve twin'in kaz boynu C5 girişine kadar iner ([gooseneck.md](preheater/gooseneck.md)).
- **Soğutucu:** alışverişler yatak hacminde (w · h · dz), gövde duvarı ızgara kutusunun.

## Hacmi olmayan ekipman (kaynak yok)

Bunlar twin'de yalnız akım devridir: hacim, duvar kaybı ve gecikme yoktur. Ölçüleri bir kaynaktan gelince bölge olarak eklenirler.

| Ekipman | Twin'de | Eksik olan |
|---|---|---|
| Tersiyer hava kanalı | soğutucunun tersiyer havası doğrudan kalsinatör girişine | boy (Ø2.439 türetilmiş; FLS R5 61 m, r 1.13 m, ama makale onu tersiyer kanal diye adlandırmaz) |
| Fırın başlığı | sekonder hava doğrudan yanma bölgesi girişine | bütün ölçüler (çizimde şematik) |
| Fırın giriş odası | fırın gazı doğrudan kalsinatöre, kalsinatör katısı doğrudan fırına | bütün ölçüler ([kiln_inlet_chamber.md](kiln/kiln_inlet_chamber.md): TBD) |
| Soğutucu vent'i | kütle artığı | `vent_outlet` ölçüsü ([cooler.md](cooler/cooler.md): TBD) |
| Farin boruları | farin doğrudan bir sonraki kademeye | hacim: — (meal_pipe_C*.md) |
