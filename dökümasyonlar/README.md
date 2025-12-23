# LED Datasheet Özeti ve Isınmayı Azaltmak İçin Önerilen Zamanlamalar

Bu klasördeki LED datasheet’lerinden çıkarılan limitler ve bu projede kullanılan `l_d / a_d / r_d` zamanlamaları için öneriler aşağıdadır.

## Projedeki LED eşleşmesi

- `led_1`: UV (360nm) → `NADH_LED_QLUV07M3QCV.pdf`
- `led_3`: Blue (450nm) → `FAD_LEDS450-SpecSheet.pdf`
- `led_4`: IR (850nm) → `Sitokrom_850_LED_SFH 4059SR_EN.pdf`
- `led_6`: IR (940nm) → `Glukoz_LED_B15V1IR--A1C000152U1930 V1.2.pdf`

## Datasheet’lerden kritik limitler (özet)

### UV 360nm — QLUV07M3QCV

- Tipik çalışma noktası (25°C): IF = 700 mA, VF typ 3.7 V (max 4.0 V), dalga boyu 365–370 nm, radiant power typ 755 mW (max 950 mW)
- Absolute Maximum Rating (25°C): Pd 4000 mW, IF 1000 mA, IFP 1100 mA, Tj 125°C, Top -40…85°C, Rth(J-S) 8 °C/W
- IFP koşulu: Duty 1/10 @ 10 kHz

### Blue 450nm — LEDS450

- Peak wavelength: 450 nm (445…455 nm)
- Continuous çalışma akımı: 150 mA
- Forward voltage @150 mA: typ 6.3 V (6.0…6.6 V)
- Optical output power @150 mA: typ 250 mW
- Değerler 25°C mount sıcaklığı için verilmiş

### IR 850nm — SFH 4059SR

- Maximum Ratings (TA=25°C): IF max 50 mA, Ptot max 175 mW, VR max 5 V, Top -40…85°C
- Pulsed limit: tp ≤ 300 µs ve D ≤ 0.005 iken IF pulse max 0.7 A
- Thermal: RthJS(real) max 260 K/W, RthJA max 420 K/W
- Dalga boyu: centroid 850 nm, peak 860 nm

### IR 940nm — B15V1IR

- Absolute Maximum Rating (25°C): IF 100 mA, IFP 1 A, VR 5 V, Topr -40…+85°C
- IFP koşulu: Pulse Width ≤ 100 µs ve Duty ≤ 1%
- IF=100 mA için: peak wavelength 940 nm, VF typ 1.55 V (1.2…1.8 V), radiant intensity typ 92 mW/sr

## Isınmayı azaltmak için zamanlama mantığı

Pico tarafında ölçüm sırası boyunca LED açık kalma süresi `l_d` (ms) olarak uygulanır; ADC örnekleme penceresi `a_d` (ms) ve LED açıldıktan sonra örnekleme başlamadan önce beklenen süre `(l_d - a_d)` (ms) olur. LED kapandıktan sonra bir sonraki adıma geçmeden önce `r_d` (ms) beklenir.

Bu projede BLE ile gönderilen `l_d / a_d / r_d` değerleri tek bayt olduğu için pratik üst sınır 255 ms’dir.

## Isınma olmaması için önerilen başlangıç ayarı

Isıyı en hızlı düşüren parametre LED’in görev çevrimini küçültmektir. IR 850 ve IR 940 datasheet’lerinde yüksek tepe akım için duty kısıtları görüldüğü için güvenli tarafta kalacak başlangıç seti:

- `l_d = 4 ms`
- `a_d = 3 ms`
- `r_d = 250 ms`

Bu ayar, aynı döngüde 4 LED ölçümü yapıldığı varsayımıyla ortalama görev çevrimini düşük tutar ve LED’lerin ısınmasını belirgin şekilde azaltır. Gürültü/kararlılık ihtiyacına göre önce `a_d` (ör. 2–6 ms aralığında) küçük adımlarla artırılıp, ısınma gözlenirse `r_d` büyütülmelidir.

## LED’e göre pratik öneri (aynı protokol içinde)

- UV (360nm): yüksek akım sürülüyorsa ısınmaya en hassas LED olur; `r_d` değerini mümkün olan en yüksekte tutmak (250–255 ms) daha güvenlidir.
- Blue (450nm): Vf yüksek olduğu için elektriksel güç artar; kısa `l_d` ve yüksek `r_d` tercih edilir.
- IR (850nm, 940nm): datasheet’lerde tepe akım/pulse koşulları var; kısa `l_d` ısıyı ciddi azaltır.

