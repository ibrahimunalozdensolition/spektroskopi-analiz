import uasyncio as asyncio
import aioble
import bluetooth
import struct
import gc
import utime
import urandom
from machine import ADC, Pin

print("🔴 FAKE SENSOR-1 - Sahte veri modu başlatılıyor...")

l_d = 4     # LED DURATION
a_d = 3      # ADC DURATION
r_d = 250      # RECOVERY DURATION

l_d %= 200 # CAUTION !

# Pin tanımlamaları (gerçek main.py ile aynı)
Pin(26, Pin.IN)
Pin(27, Pin.IN)
Pin(28, Pin.IN)

sensor_2 = ADC(26)
sensor_5 = ADC(27)
sensor_7 = ADC(28)

led_1 = Pin(13, Pin.OUT)
led_3 = Pin(12, Pin.OUT)
led_4 = Pin(10, Pin.OUT)
led_6 = Pin(11, Pin.OUT)

# order: [sensor_2, sensor_5, sensor_7] (gerçek main.py'den)

WEIGHTS_LED4 = (1.2, 1.0, 0.8)
WEIGHTS_LED6 = (1.5, 1.0, 0.5)

# ------------------------------------------------

CONV_FACTOR = 3300.0 / 65535.0

SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
CHAR_UUIDS = {
    "SENSOR_2": bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_5": bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_7": bluetooth.UUID("6E400004-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_EXTRA": bluetooth.UUID("6E400005-B5A3-F393-E0A9-E50E24DCCA9E"),
}

# Sahte veri parametreleri
FAKE_BASE_VALUES = {
    "SENSOR_2": 760,      # UV sensörü (mV)
    "SENSOR_EXTRA": 760,  # Blue sensörü (mV)
    "SENSOR_5": 2550,     # IR sensörü 1 (ham değer, ters çevrilecek)
    "SENSOR_7": 2550      # IR sensörü 2 (ham değer, ters çevrilecek)
}

FAKE_VARIATIONS = {
    "SENSOR_2": 50,       # ±50mV
    "SENSOR_EXTRA": 50,   # ±50mV
    "SENSOR_5": 100,      # ±100mV
    "SENSOR_7": 100       # ±100mV
}

fake_trends = {"SENSOR_2": 0, "SENSOR_EXTRA": 0, "SENSOR_5": 0, "SENSOR_7": 0}
fake_counter = 0

def random_int(min_val, max_val):
    """Rastgele sayı üret"""
    try:
        return urandom.randint(min_val, max_val)
    except:
        return min_val + (utime.ticks_ms() % (max_val - min_val + 1))

def generate_fake_adc_value(sensor_key):
    global fake_counter, fake_trends
    
    base = FAKE_BASE_VALUES[sensor_key]
    variation = FAKE_VARIATIONS[sensor_key]
    
    # Temel gürültü
    noise = random_int(-variation, variation)
    value = base + noise
    
    # Trend simülasyonu
    if fake_counter % 50 == 0:
        fake_trends[sensor_key] = random_int(-1, 1)
    
    value += fake_trends[sensor_key] * 3
    
    # Ani değişimler
    if random_int(1, 100) <= 3:  # %3 olasılık
        spike = random_int(-100, 150) if sensor_key in ["SENSOR_2", "SENSOR_EXTRA"] else random_int(-200, 200)
        value += spike
    
    # Sınırla
    value = max(0, min(3300, value))
    
    # Drift
    if random_int(1, 100) <= 1:
        drift = random_int(-5, 5)
        FAKE_BASE_VALUES[sensor_key] = max(100, min(3200, FAKE_BASE_VALUES[sensor_key] + drift))
    
    return value

def measure_average(gpio: Pin, adc: ADC, delay_ms: int, sample_ms: int):
    """Sahte ölçüm - gerçek main.py ile aynı yapı"""
    gpio.value(1)
    utime.sleep_ms(delay_ms)

    # Sahte veri üret (ADC okuma simülasyonu)
    sensor_key = None
    if adc == sensor_2:
        sensor_key = "SENSOR_2"
    
    if sensor_key:
        fake_mv = generate_fake_adc_value(sensor_key)
    else:
        fake_mv = generate_fake_adc_value("SENSOR_2")  # Fallback
    
    # Sampling süresini simüle et
    utime.sleep_ms(sample_ms)

    gpio.value(0)
    
    # mV değerini döndür (gerçek main.py'deki gibi)
    return fake_mv

def measure_average_multi(gpio: Pin, adcs, delay_ms: int, sample_ms: int):
    """Sahte çoklu ölçüm - gerçek main.py ile aynı yapı"""
    gpio.value(1)
    utime.sleep_ms(delay_ms)

    # Her ADC için sahte veri üret
    mvs = []
    sensor_keys = ["SENSOR_2", "SENSOR_5", "SENSOR_7"]  # ADC sırası
    
    for i, adc in enumerate(adcs):
        if i < len(sensor_keys):
            fake_mv = generate_fake_adc_value(sensor_keys[i])
        else:
            fake_mv = generate_fake_adc_value("SENSOR_2")
        mvs.append(fake_mv)
        utime.sleep_us(20)  # Gerçek gecikme

    gpio.value(0)
    return mvs

def weighted_value(mv_list, weights):
    """Ağırlıklı ortalama (gerçek main.py'den kopyalandı)"""
    if not mv_list:
        return 0
    if len(mv_list) != len(weights):
        weights = [1.0] * len(mv_list)
    total_w = sum(weights)
    if total_w == 0:
        return 0
    s = 0.0
    for v, w in zip(mv_list, weights):
        s += float(v) * float(w)
    return int(s / total_w)

async def notify_if_conn(conn, char, mv_value):
    """BLE bildirim (düzeltilmiş versiyon)"""
    if not conn:
        return
    try:
        if not conn.is_connected():
            return
        payload = struct.pack("<H", int(mv_value) & 0xFFFF)
        await char.notify(conn, payload)  # notify kullan (write yerine)
        
        # Debug çıktısını azalt
        global fake_counter
        if fake_counter % 40 == 0:  # Her 40 ölçümde bir
            print("FAKE Notified", char.uuid, mv_value, "mV")
    except Exception as e:
        print("FAKE Notify failed for", char.uuid, ":", str(e))

async def peripheral():
    """Ana BLE döngüsü (gerçek main.py ile aynı yapı)"""
    global fake_counter
    
    while True:
        try:
            svc = aioble.Service(SERVICE_UUID)
            chars = {}
            for name, uuid in CHAR_UUIDS.items():
                chars[name] = aioble.Characteristic(svc, uuid, read=True, notify=True)

            try:
                aioble.register_services((svc,))
            except Exception:
                try:
                    aioble.register_services(svc)
                except Exception as e:
                    print("FAKE Service registration failed:", e)
                    await asyncio.sleep(5)
                    continue

            print("FAKE Advertising sensor-1")
            async with await aioble.advertise(100_000, name="sensor-1", services=[SERVICE_UUID]) as conn:
                print("FAKE Connected:", conn.device)
                print("🔴 SAHTE VERİ MODU AKTİF!")
                gc.collect()

                try:
                    while conn.is_connected():
                        fake_counter += 1
                        
                        # SENSOR_2: LED1 + sensor_2 (gerçek main.py ile aynı)
                        v1 = measure_average(led_1, sensor_2, (l_d-a_d), a_d)
                        await notify_if_conn(conn, chars["SENSOR_2"], v1)
                        await asyncio.sleep_ms(r_d)

                        # SENSOR_EXTRA: LED3 + sensor_2 (gerçek main.py ile aynı)
                        v3 = measure_average(led_3, sensor_2, (l_d-a_d), a_d)
                        await notify_if_conn(conn, chars["SENSOR_EXTRA"], v3)
                        await asyncio.sleep_ms(r_d)

                        # SENSOR_5: LED4 + multi sensor (gerçek main.py ile aynı)
                        mvs4 = measure_average_multi(led_4, (sensor_2, sensor_5, sensor_7), (l_d-a_d), a_d)
                        wv4 = weighted_value(mvs4, WEIGHTS_LED4)
                        wv4 = 3300 - wv4  # Ters çevirme (gerçek main.py'deki gibi)
                        await notify_if_conn(conn, chars["SENSOR_5"], wv4)
                        await asyncio.sleep_ms(r_d)

                        # SENSOR_7: LED6 + multi sensor (gerçek main.py ile aynı)
                        mvs6 = measure_average_multi(led_6, (sensor_2, sensor_5, sensor_7), (l_d-a_d), a_d)
                        wv6 = weighted_value(mvs6, WEIGHTS_LED6)
                        wv6 = 3300 - wv6  # Ters çevirme (gerçek main.py'deki gibi)
                        await notify_if_conn(conn, chars["SENSOR_7"], wv6)
                        await asyncio.sleep_ms(100)

                        # Garbage collection (gerçek main.py'deki gibi)
                        if utime.ticks_ms() % 10000 == 0:
                            gc.collect()
                            if fake_counter % 100 == 0:
                                print(f"🔴 FAKE: {fake_counter} sahte ölçüm tamamlandı")

                except Exception as e:
                    print("FAKE Connection loop error:", e)

        except Exception as e:
            print("FAKE Peripheral error:", e)
            await asyncio.sleep(5)

def main():
    """Ana fonksiyon (gerçek main.py ile aynı yapı)"""
    print("=" * 50)
    print("🔴 FAKE SENSOR-1 - SAHTE VERİ MODU")
    print("=" * 50)
    print("Gerçek main.py yapısı korundu")
    print("Sadece veri üretimi sahte!")
    print("Cihaz adı: sensor-1")
    print("=" * 50)
    
    asyncio.run(peripheral())

if __name__ == "__main__":
    main()
