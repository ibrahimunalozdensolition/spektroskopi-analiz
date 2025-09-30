import uasyncio as asyncio
import aioble
import bluetooth
import struct
import gc
import utime
from machine import ADC, Pin


status_led = Pin("LED", Pin.OUT)
 

sensor_2 = ADC(0)   
sensor_5 = ADC(1)   
sensor_7 = ADC(2)   

led_1 = Pin(13, Pin.OUT)
led_3 = Pin(12, Pin.OUT)
led_4 = Pin(10, Pin.OUT)
led_6 = Pin(11, Pin.OUT)

CONV_FACTOR = 3300.0 / 65535.0  

SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
CHAR_UUIDS = {
    "SENSOR_2": bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_5": bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_7": bluetooth.UUID("6E400004-B5A3-F393-E0A9-E50E24DCCA9E"),
    "SENSOR_EXTRA": bluetooth.UUID("6E400005-B5A3-F393-E0A9-E50E24DCCA9E"),
}

def measure_average(gpio: Pin, adc: ADC, delay_ms: int, sample_ms: int):
    gpio.value(1)
    utime.sleep_ms(delay_ms)

    s = 0
    n = 0
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < sample_ms:
        s += adc.read_u16()
        n += 1

    gpio.value(0)
    if n == 0:
        return 0
    avg_raw = s / n
    avg_mv = int(avg_raw * CONV_FACTOR)
    if avg_mv < 0:
        avg_mv = 0
    elif avg_mv > 0xFFFF:
        avg_mv = 0xFFFF
    return avg_mv

async def blink_status_led():
    while True:
        status_led.value(1)
        await asyncio.sleep_ms(500)
        status_led.value(0)
        await asyncio.sleep_ms(500)

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
                    while conn.is_connected():
                        v1 = measure_average(led_1, sensor_2, 60, 40)
                        await notify_if_conn(conn, chars["SENSOR_2"], v1)
                        await asyncio.sleep_ms(20)

                        v3 = measure_average(led_3, sensor_2, 60, 40)
                        await notify_if_conn(conn, chars["SENSOR_EXTRA"], v3)
                        await asyncio.sleep_ms(20)

                        v4 = measure_average(led_4, sensor_5, 60, 40)
                        await notify_if_conn(conn, chars["SENSOR_5"], v4)
                        await asyncio.sleep_ms(20)

                        v6 = measure_average(led_6, sensor_7, 60, 40)
                        await notify_if_conn(conn, chars["SENSOR_7"], v6)
                        await asyncio.sleep_ms(100)
                        
                        if utime.ticks_ms() % 10000 == 0:
                            gc.collect()
                            
                except Exception as e:
                    print("Connection loop error:", e)
                    
        except Exception as e:
            print("Peripheral error:", e)
            await asyncio.sleep(5)

async def main():
    print("Pico W başlatılıyor...")
    print("LED yanıp sönmeye başlıyor")
    
    blink_task = asyncio.create_task(blink_status_led())
    peripheral_task = asyncio.create_task(peripheral())
    
    try:
        await asyncio.gather(blink_task, peripheral_task)
    except KeyboardInterrupt:
        print("Program durduruldu")
    except Exception as e:
        print("Ana program hatası:", e)

if __name__ == "__main__":
    asyncio.run(main())
