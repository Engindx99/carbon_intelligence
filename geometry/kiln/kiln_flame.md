# Alev bölgesi CFD hacmi (kiln_flame)

Tesis: 5000 t/d, tek fırın, Ø4,8 × 60 m. Bu hacim fırın çıkışını ve brülörü birlikte modellemek için kuruldu (kullanıcı kararı, 23 Kasım 2026: yerleşim + hood + alev bölgesi CFD hacmi; CFD koşuları sonra). Katı `geometry/macros/kiln_flame.bas` → `kiln_flame.SLDPRT` / `.step`. Yerleşim `plant_geometry.kiln_flame()`, sınır değerleri `plant_geometry.kiln_flame_boundaries()`. Pafta `geometry/drawings/kiln_flame/`.

Hacmin parçaları:
- **Hood:** contayı saran kutu ([kiln_hood.md](kiln_hood.md)).
- **Fırın deliği:** yanma bölgesi boyunca; klinker yatağı kesilmiş.
- **Soğutucu ağızları:** soğutucunun iki segment ağzı.
- **Tersiyer hava çıkışı:** tavanda; çıkış yüzü tavandan 3 D yukarıda.
- **Brülör:** JETFLEX 2.0'ın üç kanalı ([kiln_burner.md](kiln_burner.md)), ucu fırının 0,25 m içinde, eksende; brülörün kendi hacmi çıkarılmış.

## CFD Geometry

<!-- BEGIN GENERATED (tools/gen_geometry.py) -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->
| Ölçü | Değer | Kaynak |
|---|---|---|
| Fırın deliğinin başı (kiln_gas_out), z | 25.00 m | türetilmiş |
| Brülör ucundan gaz çıkışına | 34.75 m | türetilmiş |
| Alev boyu tahmini (Sarkar 2009, D ile ölçekli) | 12.66 m | türetilmiş |
| Tersiyer çıkışı, tavandan | 7.32 m | türetilmiş |
| Yatak doluluğu (süreklilik) | 6.20 % | türetilmiş |
| Yatak yüzeyi genişliği | 3.04 m | türetilmiş |
| Yatakta geçiş süresi (yanma bölgesi) | 15.83 dk | türetilmiş |
| `secondary_air_in` (11.960 m²) | kütle debisi girişi, 23.759 kg/s, 1052.0 K | secondary air + the outlet seal's leak (no face of its own), mixed |
| `tertiary_supply_in` (11.960 m²) | kütle debisi girişi, 54.925 kg/s, 1073.2 K | cooler segment 2: the tertiary air's supply |
| `tertiary_air_out` (4.673 m²) | kütle debisi çıkışı, 54.925 kg/s | to the calciner: the calciner's tertiary air inlet flow |
| `kiln_gas_out` (16.974 m²) | basınç çıkışı | 0 Pa gauge (reference); carries the rest |
| `bed` (106.249 m²) | duvar | clinker bed surface (kiln_bed()); its temperature from the twin's burning zone, set in the CFD |
| `coal_in` (0.034 m²) | kütle debisi girişi, 1.254 kg/s, 293.1 K | conveying air (not in the twin) + the petcoke |
| `axial_in` (0.036 m²) | kütle debisi girişi, 1.938 kg/s, 293.1 K | the twin's primary air, axial share |
| `swirl_in` (0.027 m²) | kütle debisi girişi, 0.702 kg/s, 293.1 K | the twin's primary air, swirl share |
| Petrokok debisi | 2.095 kg/s | türetilmiş |
| Tane dağılımı: Rosin-Rammler ortalama çap | 34.193 µm | literatür |
| Tane dağılımı: n | 0.944 | literatür |
| Tane dağılımı: en küçük çap | 0.724 µm | literatür |
| Tane dağılımı: en büyük çap | 138.038 µm | literatür |
| Girişler toplamı (hava + yakıt) | 84.674 kg/s | türetilmiş |
| Fırın gazı çıkışı (kütle dengesi) | 29.749 kg/s | türetilmiş |
<!-- END GENERATED -->

## Kapsam: dahil olanlar, dışarıda kalanlar (CLAUDE.md kural 10)

| Fiziksel olay / öğe | Durum | Neden kabul edilebilir | Etkilenen çıktılar |
|---|---|---|---|
| Brülör kanallarının akışı (eksenel yarıklar, swirl delikleri, petrokok borusu) | Dahil, kanallar hacmin parçası | Jetlerin momentumu ve swirl alevi biçimlendirir | — |
| Hood'daki ikincil hava akışı, tersiyer hava ayrılması | Dahil | Alevin hava beslemesi ve hood içindeki geri dönüş bunlardan gelir | — |
| Klinker yatağı | Yüzey olarak dahil (süreklilikten doluluk, 40° yığılma açısı); yatağın içi yok | Gaz tarafı için yatak bir duvar; yaygın yaklaşım (Alcaide-Moreno 2023: sıcaklık profilli hareketli duvar) | Yatağa ısı akısı, yatağın sıcaklık profili verilmelidir |
| Yatağın dönme hareketi | Yok (sabit duvar) | Yatak hızı yaklaşık 0,02 m/s; gaz hızının yanında ihmal edilebilir | Yatak yüzeyindeki sınır tabaka |
| Çıkış contası kaçağı | Ayrı yüz yok; ikincil havayla segment 1'den, karışım sıcaklığında (kullanıcı kararı) | Kütle ve enerji twin ile tutar | Contadaki yerel soğuk hava jeti |
| Petrokok taşıma havası | Dahil (`coal_in`) | Gerçek debi; twin'de yok (açık bulgu) | Twin ile karşılaştırma |
| Fırının eğimi (%3) | Katıda yok; hood fırın çerçevesine döndürülmüş | Akışa etkisi ihmal edilebilir; yerçekimi vektörü eğime göre verilir | — |
| Kaplama (coating), astar ayrıntısı | Yok | Duvar ısıl direnç olarak verilir (physics/shell.py) | Kabuk kaybı |
| Hood kapıları, gözetleme delikleri, yakıt lansı, ateşleyici | Yok | Alternatif yakıt yok; akışa katkısı küçük | — |
| Soğutucudan gelen klinker tozu, ikincil havadaki toz | Yok | İlk adımda temiz hava | Radyasyon (toz saçılması) |

## Yöntem (önerilen; temel model ve artımlı adımlar, kural 9)

Literatürdeki endüstriyel çimento fırını alev CFD'leri aynı model ailesini kullanıyor:
- **Alcaide-Moreno ve diğ. 2023:** 64 m fırın, Fluent; realizable k-ε + enhanced wall treatment, DO + WSGGM, species transport + eddy-dissipation, DPM.
- **CEMCAP / SINTEF (Bakken, Ditaranto ve diğ.):** 60 m × Ø3,76 m, 3000 t/d, Fluent; k-ω SST, finite-rate/eddy-dissipation 7 adım, DO + WSGGM, duvar sıcaklığı BAT profiline sabit.

| Adım | Fizik | Model | Amaç / kabul ölçütü |
|---|---|---|---|
| 0 | İzotermal akış, yanma yok | RANS, realizable k-ε + EWT (karşılaştırma: SST), sıkıştırılamaz ideal gaz | Hood'daki geri dönüş, jetlerin ikincil havayı sürüklemesi; kütle dengesi < %0,1; tersiyer çıkışında ters akış yok |
| 1 | Gaz fazı ısı + radyasyon, yanma yok | Enerji, DO (S4 başlangıç), WSGGM; yatak ve duvar sıcaklıkları sabit | Enerji dengesi; duvara ve yatağa ısı akısının mertebesi |
| 2 | Petrokok yanması | DPM (Rosin-Rammler, aşağıda), tek hızlı uçucu çıkışı, kinetik/difüzyon sınırlı char yanması, uçucu için 2 adımlı EDM; parçacık radyasyonu (ε 0,7) | Alev boyu (literatür: yaklaşık 12 m), yanma tamlığı > %99 çıkışta, O₂ çıkışta twin ile |
| 3 | Duyarlılık | Swirl yönü, meme açısı, brülör kaçıklığı, yatak sıcaklık profili | Alev boyu ve yatağa ısı akısı profilindeki değişim |

Uygulama notları:
- **Ağ:** brülör ucunda kanallar ve uç halkası en az 1–2 mm, alev bölgesinde 20–50 mm, uzak hacimde 0,2–0,3 m. Kaynaktaki iki model 1,6–2,3 M hücre.
- **Brülör kanalları:** iç yarıkları ve delikleri birlikte ağlamak pahalıysa önce yalnız brülör koşulur, çıkış profili alev hacmine taşınır (Alcaide-Moreno 2023'ün yolu). Kanallar hacmin parçası olduğu için her iki yol açık.
- **Yatak sıcaklığı:** twin'in yanma bölgesi yatak profilinden verilir (twin "geometri hazır" denince koşulacak).
- **Yatak sınırı:** Alcaide-Moreno 2023, yatağı fırın girişine doğru hareket eden, ölçülmüş sıcaklık profilli bir duvar olarak modelliyor (emisivite 0,8).
- **Kabul (kural 9):** residuallar, kütle ve enerji dengeleri, çıkış O₂/CO ve alev boyu raporlanmadan çözüm kabul edilmez.

## Açık konular

- **Hood genişliği ve yüksekliği** şematik değerlere dayanıyor: conta derinliği ve fırın ekseninin soğutucu tavanı üstündeki yüksekliği. 23 Kasım 2026 araştırmasında ikisi için de yayınlanmış ölçü bulunamadı; kullanıcı kararıyla şematik kaldılar. Fuller'ın çıkış lamel contası broşüründeki görsel, conta halkasının fırın ucunun yaklaşık 1,4–1,5 katı olduğunu gösteriyor (modelde 1,34). Bu oranla hood hızı 3,55 m/s'ye, yani 4–10 m/s bandının altına düşerdi: conta boyutu ile hız ölçütü arasında bir gerilim var.
- **Alev boyu** tek bir kaynağa dayanıyor (Sarkar ve Bhad 2009 özeti); hacim tahminin 2,7 katı.
- **Fırının dönme yönü** (yatak +x tarafına yükseliyor) ve **swirl yönü** yayınlanmamış; ikisi de `model`.
- **Twin:** taşıma havası yok; yakıt ısısı yanma bölgesine eksenel ağırlıklarla dağıtılıyor, alev boyuyla karşılaştırılmalı.

## Kaynaklar

- A. Alcaide-Moreno, M. Á. Castán-Lascorz, V. Tavares, "An industrial-scale cement rotary kiln CFD model to characterise alternative fuel combustion profiles", ECOS 2023, s. 448–459, doi 10.52202/069564-0041.
- J. Bakken, M. Ditaranto, N. E. Haugen, Ø. Langørgen, "Modeling of full scale oxy-fuel cement rotary kiln", CEMCAP çalıştayı, SINTEF Energi, 30 Kasım 2018; M. Ditaranto, J. Bakken, Int. J. Greenhouse Gas Control 83 (2019) 166–175.
- S. Sarkar, D. Bhad, "CFD modeling of a cement kiln with multi channel burner for optimization of flame profile", 7th Int. Conf. on CFD in the Minerals and Process Industries, CSIRO, Melbourne, 2009 (özetten).
