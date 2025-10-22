
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional, Callable, Any

from .ble_manager import BLEManager
from config.constants import DEFAULT_SENSORS, TARGET_SENSORS
from utils.logger import app_logger, log_connection_event
from utils.helpers import map_device_name

class SensorScanner:
    """Sensör tarama ve bağlantı yöneticisi"""
    
    def __init__(self, ble_manager: BLEManager):
        self.ble_manager = ble_manager
        self.scan_callback = None
        self.connection_callback = None
        
        # UI bileşenleri (dışarıdan set edilecek)
        self.sensor_combo = None
        self.scan_button = None
        self.status_label = None
        
        # Durum takibi
        self.current_selected_sensor = None
        self.auto_connection_enabled = True
        
        # Thread yönetimi - aynı anda sadece 1 thread
        self.active_scan_thread = None
        self.is_scanning = False
    
    def set_ui_components(self, sensor_combo, scan_button, status_label):
        """UI bileşenlerini ayarla"""
        self.sensor_combo = sensor_combo
        self.scan_button = scan_button
        self.status_label = status_label
        
        # Combo box değerlerini ayarla
        if self.sensor_combo:
            self.sensor_combo['values'] = DEFAULT_SENSORS
            self.sensor_combo.bind('<<ComboboxSelected>>', self.on_sensor_selection_changed)
    
    def set_callbacks(self, scan_callback: Optional[Callable] = None,
                     connection_callback: Optional[Callable] = None):
        """Callback fonksiyonlarını ayarla"""
        self.scan_callback = scan_callback
        self.connection_callback = connection_callback
    
    def scan_and_connect_sensors(self):
        """Sensörleri tara ve ilk bulduğuna bağlan - thread yönetimi optimize edildi"""
        if not self.ble_manager.is_available():
            if self.status_label:
                self.status_label.configure(text="Bleak Not Available", foreground="red")
            messagebox.showerror("Error", "Bleak library not installed!")
            return
        
        # Zaten tarama yapılıyorsa çık
        if self.is_scanning:
            app_logger.warning("Tarama zaten devam ediyor, yeni thread oluşturulmadı")
            return
            
        # Önceki thread'i temizle
        if self.active_scan_thread and self.active_scan_thread.is_alive():
            app_logger.warning("Önceki tarama thread'i hala aktif, bekleniyor...")
            return
        
        # UI güncelle
        if self.scan_button:
            self.scan_button.configure(state=tk.DISABLED, text="Scanning...")
        
        def scan_thread():
            self.is_scanning = True  # Tarama başladı
            try:
                # Cihazları tara
                devices = self.ble_manager.scan_devices_sync()
                
                if devices:
                    # Available devices'ı güncelle
                    self.ble_manager.available_devices.update(devices)
                    
                    # İlk cihazı seç
                    first_device = list(devices.keys())[0]
                    
                    # UI'yi güncelle (thread-safe)
                    if self.sensor_combo:
                        try:
                            self.sensor_combo.after(100, 
                                lambda: self.sensor_combo.set(first_device))
                        except RuntimeError:
                            app_logger.warning("UI güncelleme hatası - main thread mevcut değil")
                    
                    # Direkt bağlantı kur (döngüye girmemek için)
                    device_info = devices[first_device]
                    app_logger.info(f"{first_device} cihazına bağlanılıyor...")
                    
                    success = self.ble_manager.connect_to_device(
                        device_info['address'], 
                        first_device
                    )
                    
                    if success:
                        self.current_selected_sensor = first_device
                        # UI durumunu güncelle
                        if self.status_label:
                            try:
                                self.status_label.after(100, 
                                    lambda: self.status_label.configure(text=first_device, foreground="green"))
                            except RuntimeError:
                                pass
                        
                        # Callback çağır
                        if self.connection_callback:
                            self.connection_callback(first_device, device_info, True)
                    
                    # Callback çağır
                    if self.scan_callback:
                        self.scan_callback(devices)
                        
                else:
                    # Hiç cihaz bulunamadı
                    if self.status_label:
                        try:
                            self.status_label.after(100, 
                                lambda: self.status_label.configure(text="No devices found", foreground="orange"))
                        except RuntimeError:
                            app_logger.warning("Cihaz bulunamadı mesajı gösterilemedi")
                
            except Exception as e:
                log_error(app_logger, e, "Tarama thread hatası")
            finally:
                self.is_scanning = False  # Tarama bitti
                # Scan butonunu geri aç
                if self.scan_button:
                    try:
                        self.scan_button.after(100, 
                            lambda: self.scan_button.configure(state=tk.NORMAL, text="🔍 Scan & Connect"))
                    except RuntimeError:
                        app_logger.warning("Scan butonu güncellenemedi")
        
        # Thread oluştur ve referansı sakla
        self.active_scan_thread = threading.Thread(target=scan_thread, daemon=True)
        self.active_scan_thread.start()
        app_logger.debug("Yeni tarama thread'i başlatıldı")
    
    def on_sensor_selection_changed(self, event):
        """Sensör seçimi değiştiğinde çağrılır"""
        selected_sensor = self.sensor_combo.get() if self.sensor_combo else None
        
        if not selected_sensor:
            return
        
        # Aynı sensör seçildiyse hiçbir şey yapma
        if self.current_selected_sensor == selected_sensor:
            return
        
        app_logger.info(f"Sensör değişikliği: {self.current_selected_sensor} -> {selected_sensor}")
        
        # Eğer bağlı ise önce disconnect yap
        if self.ble_manager.is_connected:
            app_logger.info(f"{self.current_selected_sensor} bağlantısı kesiliyor...")
            self.ble_manager.disconnect()
            
            # Kısa bekleme sonrası yeni sensöre bağlan
            self.connect_to_sensor_delayed(selected_sensor, 1000)
        else:
            # Bağlı değilse direkt yeni sensöre bağlanmaya çalış
            self.connect_to_selected_sensor(selected_sensor)
    
    def connect_to_sensor_delayed(self, sensor_name: str, delay_ms: int):
        """Gecikmeli sensör bağlantısı"""
        if self.sensor_combo:
            try:
                self.sensor_combo.after(delay_ms, 
                    lambda: self.connect_to_selected_sensor(sensor_name))
            except RuntimeError:
                app_logger.warning("Gecikmeli bağlantı programlanamadı")
    
    def connect_to_selected_sensor(self, sensor_name: str):
        """Seçilen sensöre bağlan"""
        # Önce current_selected_sensor'ı güncelle
        self.current_selected_sensor = sensor_name
        
        if sensor_name in self.ble_manager.available_devices:
            # Mevcut cihaza bağlan
            device_info = self.ble_manager.available_devices[sensor_name]
            app_logger.info(f"{sensor_name} cihazına bağlanılıyor...")
            
            success = self.ble_manager.connect_to_device(
                device_info['address'], 
                sensor_name
            )
            
            if success:
                # UI durumunu güncelle
                if self.status_label:
                    self.status_label.configure(text=sensor_name, foreground="green")
                
                # Callback çağır
                if self.connection_callback:
                    self.connection_callback(sensor_name, device_info, True)
            else:
                # Bağlantı başarısız
                if self.status_label:
                    self.status_label.configure(text="Connection Failed", foreground="red")
                
                if self.connection_callback:
                    self.connection_callback(sensor_name, device_info, False)
        else:
            # Cihaz bulunamadı, tara
            app_logger.info(f"{sensor_name} aranıyor...")
            self.scan_and_connect_to_sensor(sensor_name)
    
    def scan_and_connect_to_sensor(self, sensor_name: str):
        """Belirli sensörü tara ve bağlan - thread yönetimi optimize edildi"""
        # Zaten tarama yapılıyorsa çık
        if self.is_scanning:
            app_logger.warning(f"{sensor_name} tarama atlandı - zaten tarama devam ediyor")
            return
            
        def scan_thread():
            self.is_scanning = True
            try:
                # Tarama yap
                devices = self.ble_manager.scan_devices_sync()
                
                if sensor_name in devices:
                    # Cihaz bulundu, available_devices'a ekle ve bağlan
                    self.ble_manager.available_devices.update(devices)
                    device_info = devices[sensor_name]
                    app_logger.info(f"{sensor_name} cihazına bağlanılıyor...")
                    
                    success = self.ble_manager.connect_to_device(
                        device_info['address'], 
                        sensor_name
                    )
                    
                    if success:
                        # UI durumunu güncelle
                        if self.status_label:
                            self.status_label.configure(text=sensor_name, foreground="green")
                        
                        # Callback çağır
                        if self.connection_callback:
                            self.connection_callback(sensor_name, device_info, True)
                    else:
                        # Bağlantı başarısız
                        if self.status_label:
                            self.status_label.configure(text="Connection Failed", foreground="red")
                        
                        if self.connection_callback:
                            self.connection_callback(sensor_name, device_info, False)
                else:
                    # Cihaz bulunamadı
                    app_logger.warning(f"{sensor_name} bulunamadı")
                    if self.status_label:
                        self.status_label.configure(text=f"{sensor_name} Not Found", foreground="red")
                
            except Exception as e:
                log_error(app_logger, e, f"{sensor_name} tarama hatası")
            finally:
                self.is_scanning = False
        
        # Thread oluştur ve referansı sakla
        self.active_scan_thread = threading.Thread(target=scan_thread, daemon=True)
        self.active_scan_thread.start()
        app_logger.debug(f"{sensor_name} için yeni tarama thread'i başlatıldı")
    
    def disconnect_current_sensor(self):
        """Mevcut sensör bağlantısını kes"""
        try:
            if self.ble_manager.is_connected:
                self.ble_manager.disconnect()
                
                # UI güncelle
                if self.status_label:
                    self.status_label.configure(text="Not Connected", foreground="red")
                
                app_logger.info(f"{self.current_selected_sensor} bağlantısı kesildi")
                
                # Callback çağır
                if self.connection_callback:
                    self.connection_callback(self.current_selected_sensor, None, False)
                
        except Exception as e:
            log_error(app_logger, e, "Bağlantı kesme hatası")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Bağlantı bilgilerini al"""
        ble_status = self.ble_manager.get_connection_status()
        
        return {
            'current_sensor': self.current_selected_sensor,
            'is_connected': ble_status['is_connected'],
            'device_address': ble_status['device_address'],
            'available_devices': list(self.ble_manager.available_devices.keys()),
            'is_scanning': ble_status['is_scanning']
        }
    
    def enable_auto_connection(self, enabled: bool = True):
        """Otomatik bağlantıyı aç/kapat"""
        self.auto_connection_enabled = enabled
        app_logger.info(f"Otomatik bağlantı: {'açık' if enabled else 'kapalı'}")
    
    def start_auto_connection(self):
        """Otomatik bağlantıyı başlat"""
        if not self.auto_connection_enabled:
            return
        
        app_logger.info("Otomatik bağlantı başlatılıyor...")
        
        # Kısa gecikme sonrası tarama başlat
        if self.sensor_combo:
            try:
                self.sensor_combo.after(1000, self.scan_and_connect_sensors)
            except RuntimeError:
                app_logger.warning("Otomatik bağlantı programlanamadı")
