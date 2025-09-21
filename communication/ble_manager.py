import asyncio
import threading
import struct
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import queue

try:
    import bleak
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
    print("Bleak (BLE) ready")
except ImportError:
    print("Bleak not found - BLE functionality will not be available")
    bleak = None
    BleakClient = None
    BleakScanner = None
    BLEAK_AVAILABLE = False

from config.constants import (
    BLE_CHARACTERISTICS, TARGET_SENSORS, BLE_SCAN_TIMEOUT,
    VOLTAGE_CONVERSION_FACTOR
)
from utils.logger import app_logger, log_connection_event, log_error
from utils.helpers import convert_raw_to_voltage, parse_ble_data, map_device_name

class BLEManager:
    def __init__(self, data_callback: Optional[Callable] = None):
        self.data_callback = data_callback
        self.disconnect_callback = None
        self.is_connected = False
        self.current_client = None
        self.current_device_address = None
        self.current_device_name = None
        
        self.available_devices: Dict[str, Dict[str, Any]] = {}
        
        self.data_queue = queue.Queue()
        self.sensor_values = {
            "SENSOR_2": 0,
            "SENSOR_5": 0,
            "SENSOR_7": 0,
            "SENSOR_EXTRA": 0
        }
        
        self.connection_thread = None
        self.is_scanning = False
    
    def is_available(self) -> bool:
        return BLEAK_AVAILABLE
    
    def set_disconnect_callback(self, callback: Optional[Callable] = None):
        """Bağlantı kopma callback'ini ayarla"""
        self.disconnect_callback = callback
    
    async def scan_devices(self, timeout: float = BLE_SCAN_TIMEOUT) -> Dict[str, Dict[str, Any]]:
        if not BLEAK_AVAILABLE:
            app_logger.error("Bleak kütüphanesi mevcut değil")
            return {}
        
        try:
            app_logger.info(f"BLE tarama başlatılıyor (timeout: {timeout}s)")
            
            try:
                devices = await BleakScanner.discover(timeout=timeout)
                found_devices = {}
                
                for device in devices:
                    device_name = device.name or "Unknown Device"
                    
                    if device_name in TARGET_SENSORS:
                        display_name = map_device_name(device_name)
                        
                        found_devices[display_name] = {
                            'address': device.address,
                            'original_name': device_name,
                            'rssi': getattr(device, 'rssi', 'N/A'),
                            'device_obj': device
                        }
                        
                        app_logger.info(f"Hedef cihaz bulundu: {display_name} ({device.address})")
                        
            except Exception as e:
                app_logger.warning(f"Eski BLE API başarısız, yeni API deneniyor: {e}")
                devices_dict = await BleakScanner.discover(timeout=timeout, return_adv=True)
                found_devices = {}
                
                for device, advertisement_data in devices_dict.items():
                    device_name = getattr(device, 'name', None) or "Unknown Device"
                    
                    if device_name in TARGET_SENSORS:
                        display_name = map_device_name(device_name)
                        
                        found_devices[display_name] = {
                            'address': getattr(device, 'address', 'Unknown'),
                            'original_name': device_name,
                            'rssi': getattr(advertisement_data, 'rssi', 'N/A'),
                            'device_obj': device
                        }
                        
                        app_logger.info(f"Hedef cihaz bulundu: {display_name} ({getattr(device, 'address', 'Unknown')})")
            
            app_logger.info(f"Tarama tamamlandı: {len(found_devices)} cihaz bulundu")
            return found_devices
            
        except Exception as e:
            app_logger.error(f"BLE tarama hatası: {e}")
            return {}
    
    def scan_devices_sync(self, timeout: float = BLE_SCAN_TIMEOUT) -> Dict[str, Dict[str, Any]]:
        try:
            return asyncio.run(self.scan_devices(timeout))
        except Exception as e:
            app_logger.error(f"Senkron BLE tarama hatası: {e}")
            return {}
    
    def scan_devices_threaded(self, callback: Optional[Callable] = None):
        if self.is_scanning:
            app_logger.warning("Tarama zaten devam ediyor")
            return
        
        def scan_thread():
            self.is_scanning = True
            try:
                devices = self.scan_devices_sync()
                self.available_devices.update(devices)
                
                if callback:
                    callback(devices)
                    
            except Exception as e:
                app_logger.error(f"Thread'li tarama hatası: {e}")
            finally:
                self.is_scanning = False
        
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def connect_to_device(self, device_address: str, device_name: str = "Unknown"):
        """Cihaza bağlan"""
        if not BLEAK_AVAILABLE:
            app_logger.error("Bleak kütüphanesi mevcut değil")
            return False
        
        if self.is_connected:
            app_logger.warning("Zaten bağlı, önce bağlantıyı kes")
            return False
        
        # Bağlantıyı thread'de başlat
        self.connection_thread = threading.Thread(
            target=self._connect_async_wrapper,
            args=(device_address, device_name),
            daemon=True
        )
        self.connection_thread.start()
        
        return True
    
    def _connect_async_wrapper(self, device_address: str, device_name: str):
        """Async bağlantı wrapper"""
        try:
            asyncio.run(self._connect_to_device_async(device_address, device_name))
        except Exception as e:
            app_logger.error(f"BLE bağlantı async wrapper hatası: {e}")
    
    async def _connect_to_device_async(self, device_address: str, device_name: str):
        """Async BLE bağlantısı"""
        try:
            app_logger.info(f"BLE bağlantısı kuruluyor: {device_name} ({device_address})")
            
            async with BleakClient(device_address) as client:
                self.current_client = client
                self.current_device_address = device_address
                self.current_device_name = device_name
                self.is_connected = True
                
                log_connection_event(app_logger, device_name, "CONNECTED", True)
                
                await self._setup_notifications(client)
                
                app_logger.info("BLE bağlantısı sonsuz mod aktif - timeout yok")
                
                while self.is_connected:
                    if not client.is_connected:
                        app_logger.warning("BLE cihazı bağlantısı kesildi")
                        self.disconnect()
                        break
                    await asyncio.sleep(2.0)  
                    
        except Exception as e:
            log_connection_event(app_logger, device_name, "CONNECTION_FAILED", False)
            log_error(app_logger, e, "BLE bağlantı hatası")
            self.is_connected = False
            self.current_client = None
    
    async def _setup_notifications(self, client: BleakClient):
        """BLE notification'ları kur"""
        try:
            for char_name, char_uuid in BLE_CHARACTERISTICS.items():
                try:
                    await client.start_notify(char_uuid, self._notification_handler)
                    app_logger.debug(f"Notification başlatıldı: {char_name} ({char_uuid})")
                except Exception as e:
                    app_logger.warning(f"Notification başlatma hatası {char_name}: {e}")
            
        except Exception as e:
            app_logger.error(f"Notification kurulum hatası: {e}")
    
    def _notification_handler(self, sender, data: bytes):
        """BLE notification handler"""
        try:
            # Veri alım zamanını hemen kaydet (zaman sıralama sorununu önler)
            receive_timestamp = datetime.now()
            
            app_logger.info(f"Raspberry Pi'dan veri alındı: {sender}, uzunluk: {len(data)}")
            
            # Veriyi parse et
            raw_value = parse_ble_data(data)
            if raw_value is None:
                return
            
            # Voltaja çevir
            voltage = convert_raw_to_voltage(raw_value)
            app_logger.info(f"Raspberry Pi verisi: Ham={raw_value}, Voltaj={voltage:.3f}V")
            
            # Sensör türünü belirle
            sensor_key = self._identify_sensor_from_uuid(str(sender))
            
            if sensor_key:
                self.sensor_values[sensor_key] = voltage
                
                # Veri paketini oluştur - timestamp'i en başta aldığımız zamanla kullan
                data_packet = {
                    'timestamp': receive_timestamp,  # Sabit zaman kullan
                    'sensor_key': sensor_key,  # Hangi sensörden geldiğini belirt
                    'sensor_2': voltage if sensor_key == "SENSOR_2" else 0,
                    'sensor_5': voltage if sensor_key == "SENSOR_5" else 0,
                    'sensor_7': voltage if sensor_key == "SENSOR_7" else 0,
                    'sensor_extra': voltage if sensor_key == "SENSOR_EXTRA" else 0
                }
                
                # Veri callback'ini çağır
                if self.data_callback:
                    self.data_callback(data_packet)
                
                # Queue'ya ekle
                self.data_queue.put(data_packet)
                
                app_logger.info(f"Raspberry Pi verisi işlendi: {sensor_key} = {voltage:.3f}V")
            
        except Exception as e:
            log_error(app_logger, e, "BLE notification handler hatası")
    
    def _identify_sensor_from_uuid(self, sender_uuid: str) -> Optional[str]:
        """UUID'den sensör türünü belirle"""
        try:
            # UUID'yi temizle
            clean_uuid = sender_uuid.split(' ')[0].split('(')[0].strip()
            
            # Karakteristik UUID'leri ile karşılaştır
            for sensor_key, uuid in BLE_CHARACTERISTICS.items():
                if clean_uuid.upper() == uuid.upper():
                    return sensor_key
            
            app_logger.warning(f"Bilinmeyen UUID: {sender_uuid}")
            return None
            
        except Exception as e:
            app_logger.error(f"UUID tanımlama hatası: {e}")
            return None
    
    def disconnect(self):
        """BLE bağlantısını kes"""
        try:
            self.is_connected = False
            
            if self.current_client:
                self.current_client = None
            
            device_name = self.current_device_name
            if device_name:
                log_connection_event(app_logger, device_name, "DISCONNECTED", True)
            
            # Değişkenleri sıfırla
            self.current_device_address = None
            self.current_device_name = None
            
            # Sensör değerlerini sıfırla
            for key in self.sensor_values:
                self.sensor_values[key] = 0
            
            app_logger.info("BLE bağlantısı kesildi")
            
            # Disconnect callback'ini çağır
            if self.disconnect_callback:
                try:
                    self.disconnect_callback(device_name)
                except Exception as callback_error:
                    app_logger.error(f"Disconnect callback hatası: {callback_error}")
            
        except Exception as e:
            log_error(app_logger, e, "BLE bağlantı kesme hatası")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Bağlantı durumu bilgilerini al"""
        return {
            'is_connected': self.is_connected,
            'device_name': self.current_device_name,
            'device_address': self.current_device_address,
            'available_devices_count': len(self.available_devices),
            'queue_size': self.data_queue.qsize(),
            'is_scanning': self.is_scanning
        }
    
    def get_available_devices(self) -> Dict[str, Dict[str, Any]]:
        """Mevcut cihazları al"""
        return self.available_devices.copy()
    
    def get_data_from_queue(self) -> List[Dict[str, Any]]:
        """Queue'dan veri al"""
        data_list = []
        try:
            while not self.data_queue.empty():
                data_list.append(self.data_queue.get_nowait())
        except queue.Empty:
            pass
        
        return data_list
    
    def set_data_callback(self, callback: Callable):
        """Veri callback fonksiyonunu ayarla"""
        self.data_callback = callback
    
    def clear_device_cache(self):
        """Cihaz önbelleğini temizle"""
        self.available_devices.clear()
        app_logger.info("Cihaz önbelleği temizlendi")
