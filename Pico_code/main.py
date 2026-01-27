import uasyncio as asyncio
import aioble
import bluetooth
import struct
import gc
import utime
from machine import ADC, Pin

l_d = 4     # LED DURATION 
a_d = 3      # ADC DURATION
r_d = 250      # RECOVERY DURATION 

l_d %= 200

system_running = False
led_1_enabled = False
led_3_enabled = False
led_4_enabled = False
led_6_enabled = False

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
    "LED_CONTROL": bluetooth.UUID("6E400006-B5A3-F393-E0A9-E50E24DCCA9E"),
}


def measure_average(gpio: Pin, adc: ADC, delay_ms: int, sample_ms: int, is_enabled: bool):
    if is_enabled:
        gpio.value(1)
        utime.sleep_ms(delay_ms)
    
    s = 0
    n = 0
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < sample_ms:
        s += adc.read_u16()
        n += 1

    if is_enabled:
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


def measure_average_multi(gpio: Pin, adcs, delay_ms: int, sample_ms: int, is_enabled: bool):
    if is_enabled:
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

    if is_enabled:
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
    if not conn:
        return
    try:
        if not conn.is_connected():
            return
        payload = struct.pack("<H", int(mv_value) & 0xFFFF)
        char.notify(conn, payload)
        print("Notified", char.uuid, mv_value, "mV")
    except Exception as e:
        print("Notify failed for", char.uuid, ":", str(e))


def parse_control_command(data):
    global led_1_enabled, led_3_enabled, led_4_enabled, led_6_enabled
    global system_running, l_d, a_d, r_d
    
    if len(data) == 1:
        command_byte = data[0]
        if command_byte == 0x00:
            led_1_enabled = False
            led_3_enabled = False
            led_4_enabled = False
            led_6_enabled = False
            print("All LEDs disabled - system still running")
        elif command_byte == 0xFF:
            led_1_enabled = True
            led_3_enabled = True
            led_4_enabled = True
            led_6_enabled = True
            print("All LEDs enabled")
        else:
            led_1_enabled = bool(command_byte & 0x01)
            led_3_enabled = bool(command_byte & 0x02)
            led_4_enabled = bool(command_byte & 0x04)
            led_6_enabled = bool(command_byte & 0x08)
            print("LED states: L1={}, L3={}, L4={}, L6={}".format(
                led_1_enabled, led_3_enabled, led_4_enabled, led_6_enabled))
    
    elif len(data) == 2:
        if data[0] == 0x00 and data[1] == 0x00:
            system_running = False
            led_1_enabled = False
            led_3_enabled = False
            led_4_enabled = False
            led_6_enabled = False
            print("STOP command - system stopped")
    
    elif len(data) >= 4:
        l_d = data[0]
        a_d = data[1]
        r_d = data[2]
        led_mask = data[3]
        
        led_1_enabled = bool(led_mask & 0x01)
        led_3_enabled = bool(led_mask & 0x02)
        led_4_enabled = bool(led_mask & 0x04)
        led_6_enabled = bool(led_mask & 0x08)
        
        system_running = True
        print("START - l_d={}, a_d={}, r_d={}, LEDs: L1={}, L3={}, L4={}, L6={}".format(
            l_d, a_d, r_d, led_1_enabled, led_3_enabled, led_4_enabled, led_6_enabled))


async def peripheral():
    global led_1_enabled, led_3_enabled, led_4_enabled, led_6_enabled
    while True:
        try:
            svc = aioble.Service(SERVICE_UUID)
            chars = {}
            for name, uuid in CHAR_UUIDS.items():
                if name == "LED_CONTROL":
                    chars[name] = aioble.Characteristic(svc, uuid, read=True, write=True, notify=False)
                else:
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

            print("Advertising pico-sensors-3")
            async with await aioble.advertise(100_000, name="pico-sensors-3", services=[SERVICE_UUID]) as conn:
                print("Connected:", conn.device)
                print("Waiting for START command...")
                gc.collect()
                
                cycle_count = 0

                try:
                    while conn.is_connected():
                        cycle_count += 1
                        
                        try:
                            data = chars["LED_CONTROL"].read()
                            if data and len(data) > 0:
                                parse_control_command(data)
                        except Exception as e:
                            if cycle_count % 100 == 0:
                                print("Control read error (ignored):", e)
                        
                        if not system_running:
                            await asyncio.sleep_ms(50)
                            continue
                        
                        v1 = measure_average(led_1, sensor_2, (l_d-a_d), a_d, led_1_enabled)
                        v1 = 3300 - v1
                        await notify_if_conn(conn, chars["SENSOR_2"], v1)
                        await asyncio.sleep_ms(r_d)

                        v3 = measure_average(led_3, sensor_2, (l_d-a_d), a_d, led_3_enabled)
                        await notify_if_conn(conn, chars["SENSOR_EXTRA"], v3)
                        await asyncio.sleep_ms(r_d)

                        mvs4 = measure_average_multi(led_4, (sensor_2, sensor_5, sensor_7), (l_d-a_d), a_d, led_4_enabled)
                        wv4 = weighted_value(mvs4, WEIGHTS_LED4)
                        wv4=3300-wv4
                        await notify_if_conn(conn, chars["SENSOR_7"], wv4)
                        await asyncio.sleep_ms(r_d)

                        mvs6 = measure_average_multi(led_6, (sensor_2, sensor_5, sensor_7), (l_d-a_d), a_d, led_6_enabled)
                        wv6 = weighted_value(mvs6, WEIGHTS_LED6)
                        wv6=3300-wv6
                        await notify_if_conn(conn, chars["SENSOR_5"], wv6)
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