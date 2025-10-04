import uasyncio as asyncio
import aioble
import bluetooth
import struct
import gc
import utime
from machine import ADC, Pin

l_d = 100     # LED DURATION 
a_d = 40      # ADC DURATION
r_d = 20      # RECOVERY DURATION 

l_d %= 200 # CAUTION !

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

# order: [sensor_2, sensor_5, sensor_7]

WEIGHTS_LED4 = (1.2, 0.2, 1.6)
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
    elif avg_mv > 3300:
        avg_mv = 3300
    return avg_mv


def measure_average_multi(gpio: Pin, adcs, delay_ms: int, sample_ms: int):
    
    gpio.value(1)
    utime.sleep_ms(delay_ms)

    sums = [0] * len(adcs)
    n = 0
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < sample_ms:
        for i, adc in enumerate(adcs):
            sums[i] += adc.read_u16()
            
            utime.sleep_us(20)
        n += 1

    gpio.value(0)
    if n == 0:
        return [0] * len(adcs)

    mvs = []
    for s in sums:
        avg_raw = s / n
        mv = int(avg_raw * CONV_FACTOR)
        if mv < 0:
            mv = 0
        elif mv > 3300:
            mv = 3300
        mvs.append(mv)
    return mvs


def weighted_value(mv_list, weights):
    """
    Compute weighted average of mv_list using weights tuple/list.
    If sum(weights) == 0 returns 0.
    """
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
                        v1 = measure_average(led_1, sensor_2,(l_d-a_d),a_d)
                        await notify_if_conn(conn, chars["SENSOR_2"], v1)
                        await asyncio.sleep_ms(r_d)

                        v3 = measure_average(led_3, sensor_2,(l_d-a_d),a_d)
                        await notify_if_conn(conn, chars["SENSOR_EXTRA"], v3)
                        await asyncio.sleep_ms(r_d)

                        
                        mvs4 = measure_average_multi(led_4, (sensor_2, sensor_5, sensor_7),(l_d-a_d),a_d)
                        wv4 = weighted_value(mvs4, WEIGHTS_LED4)
                        await notify_if_conn(conn, chars["SENSOR_5"], wv4)
                        await asyncio.sleep_ms(r_d)

                        
                        mvs6 = measure_average_multi(led_6, (sensor_2, sensor_5, sensor_7),(l_d-a_d),a_d)
                        wv6 = weighted_value(mvs6, WEIGHTS_LED6)
                        await notify_if_conn(conn, chars["SENSOR_7"], wv6)
                        await asyncio.sleep_ms(100)

                        if utime.ticks_ms() % 10000 == 0:
                            gc.collect()

                except Exception as e:
                    print("Connection loop error:", e)

        except Exception as e:
            print("Peripheral error:", e)
            await asyncio.sleep(5)


def main():
    asyncio.run(peripheral())


if __name__ == "__main__":
    main()