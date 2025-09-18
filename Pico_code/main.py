import uasyncio as asyncio
import aioble
import bluetooth
import struct
import gc
import utime
import urandom

CONV_FACTOR = 3300.0 / 65535.0

fake_sensor_values = {
    "SENSOR_2": 1200,    # UV 360nm - düşük sinyal
    "SENSOR_5": 1800,    # Blue 450nm - orta sinyal  
    "SENSOR_7": 2200,    # IR 850nm - yüksek sinyal
    "SENSOR_EXTRA": 1400 # IR 940nm - orta-düşük sinyal
}

sensor_momentum = {
    "SENSOR_2": 1200,
    "SENSOR_5": 1800,
    "SENSOR_7": 2200,
    "SENSOR_EXTRA": 1400
}  

SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
CHAR_UUIDS = {
    "SENSOR_2": bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_5": bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_7": bluetooth.UUID("6E400004-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_EXTRA": bluetooth.UUID("6E400005-B5A3-F393-E0A9-E50E24DCCA9E"),
}

def generate_realistic_sensor_data(sensor_name):
    global sensor_momentum
    
    base_value = fake_sensor_values[sensor_name]
    current_momentum = sensor_momentum[sensor_name]
    
    # Küçük rastgele değişim (-15 ile +15 mV arası)
    small_change = urandom.randint(-15, 15)
    
    # Momentum ile smooth geçiş (90% eski değer, 10% yeni hedef)
    target_value = base_value + small_change
    new_value = int(current_momentum * 0.9 + target_value * 0.1)
    
    # Bazen daha büyük değişimler (spektroskopi ölçümlerini simüle eder)
    if urandom.randint(1, 100) <= 5:  # %5 ihtimalle
        trend_change = urandom.randint(-50, 50)
        new_value += trend_change
    
    # Değer sınırlaması
    if new_value < 100:
        new_value = 100
    elif new_value > 3200:
        new_value = 3200
    
    # Momentum'u güncelle
    sensor_momentum[sensor_name] = new_value
    
    return new_value

def measure_average_fake(sensor_name, delay_ms: int, sample_ms: int):
    utime.sleep_ms(delay_ms)
    fake_mv = generate_realistic_sensor_data(sensor_name)
    utime.sleep_ms(sample_ms)
    return fake_mv

async def notify_if_conn(conn, char, mv_value):
    if not conn or not conn.is_connected():
        return
    try:
        payload = struct.pack("<H", int(mv_value) & 0xFFFF)
        
        await char.notify(conn, payload)
        print("Notified", char.uuid, mv_value, "mV")
    except Exception as e:
        print("Notify/write failed:", e)

async def peripheral():
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
                    print("Service registration failed:", e)
                    await asyncio.sleep(5)
                    continue

            print("Advertising pico-sensors-2")
            async with await aioble.advertise(100_000, name="pico-sensors-4", services=[SERVICE_UUID]) as conn:
                print("Connected:", conn.device)
                gc.collect()
                
                try:
                    cycle_count = 0
                    while conn.is_connected():
                        sensor_data = {
                            "SENSOR_2": measure_average_fake("SENSOR_2", 10, 10),
                            "SENSOR_EXTRA": measure_average_fake("SENSOR_EXTRA", 10, 10), 
                            "SENSOR_5": measure_average_fake("SENSOR_5", 10, 10),
                            "SENSOR_7": measure_average_fake("SENSOR_7", 10, 10)
                        }
                        
                        for sensor_name, value in sensor_data.items():
                            await notify_if_conn(conn, chars[sensor_name], value)
                            await asyncio.sleep_ms(5)  
                        
                        await asyncio.sleep_ms(100)  
                        
                        cycle_count += 1
                        if cycle_count >= 500:  # ~60 saniyede bir
                            gc.collect()
                            cycle_count = 0
                            
                except Exception as e:
                    print("Connection loop error:", e)
                    
        except Exception as e:
            print("Peripheral error:", e)
            await asyncio.sleep(5)

def main():
    asyncio.run(peripheral())

if __name__ == "__main__":
    main()