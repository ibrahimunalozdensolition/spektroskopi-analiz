"""
PyQt Tabanlı İnteraktif Grafik Modülü
"""

import sys
import os
import json
import platform
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Windows için PyQt ayarları
if platform.system() == "Windows":
    # Windows'ta DPI scaling problemlerini önle
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_SCALE_FACTOR'] = '1'
    # Windows'ta OpenGL problemlerini önle
    os.environ['QT_OPENGL'] = 'software'

try:
    import pyqtgraph as pg
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    # Windows için ek ayarlar
    if platform.system() == "Windows":
        # High DPI support
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    PYQTGRAPH_AVAILABLE = True
    print(f"PyQtGraph ready for interactive plotting - Platform: {platform.system()}")
    
except ImportError as e:
    print(f"PyQtGraph not found - using matplotlib fallback: {e}")
    PYQTGRAPH_AVAILABLE = False
    pg = None
    QApplication = None

from config.constants import PLOT_COLORS, MATPLOTLIB_COLORS
from utils.logger import app_logger
from utils.helpers import filter_data_by_time_range

class PyQtPlotter:
    
    def __init__(self):
        self.qt_app = None
        self.plot_widget = None
        self.plot_curves = {}
        self.is_initialized = False
        
        # LED isimlerini yükle
        self.led_names = self._load_app_settings()
        
        if PYQTGRAPH_AVAILABLE:
            self.setup_qt_application()
            self.setup_plot_widget()
    
    def _load_app_settings(self):
        try:
            # Script'in bulunduğu dizinin parent dizininde app_settings.json'ı ara
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            settings_path = os.path.join(parent_dir, 'app_settings.json')
            
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings.get('led_names', {})
            else:
                app_logger.warning(f"app_settings.json bulunamadı: {settings_path}")
                return {}
        except Exception as e:
            app_logger.error(f"Settings yükleme hatası: {e}")
            return {}
    
    def _get_led_name_for_sensor(self, sensor_key: str) -> str:
        """Sensor key'e göre LED ismini döndür"""
        default_names = {
            'UV_360nm': 'UV LED (360nm)',
            'Blue_450nm': 'Blue LED (450nm)', 
            'IR_850nm': 'IR LED (850nm)',
            'IR_940nm': 'IR LED (940nm)'
        }
        
        # Sensor key'e göre LED ismini bul - value'ları kullan
        led_name = None
        if sensor_key == 'UV_360nm':
            key = next((key for key in self.led_names.keys() if '360nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'Blue_450nm':
            key = next((key for key in self.led_names.keys() if '450nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'IR_850nm':
            key = next((key for key in self.led_names.keys() if '850nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'IR_940nm':
            key = next((key for key in self.led_names.keys() if '940nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        
        if not led_name:
            led_name = default_names.get(sensor_key, sensor_key)
        
        return led_name
    
    def setup_qt_application(self):
        """Qt Application kurulumu"""
        try:
            # Global QApplication kontrolü
            existing_app = QApplication.instance()
            if not existing_app:
                self.qt_app = QApplication(sys.argv)
                app_logger.info("Yeni QApplication oluşturuldu")
            else:
                self.qt_app = existing_app
                app_logger.info("Mevcut QApplication kullanılıyor")
            
            # QApplication'ın düzgün çalıştığını kontrol et
            if self.qt_app:
                app_logger.info("Qt Application başarıyla kuruldu")
            else:
                raise Exception("QApplication oluşturulamadı")
            
        except Exception as e:
            app_logger.error(f"Qt Application kurulum hatası: {e}")
            raise
    
    def setup_plot_widget(self):
        """PyQtGraph widget kurulumu"""
        try:
            # PyQtGraph widget oluştur
            self.plot_widget = pg.PlotWidget()
            
            # Grafik ayarları
            self.plot_widget.setLabel('left', 'Voltage (mV)')
            self.plot_widget.setLabel('bottom', 'Time (seconds)')
            self.plot_widget.setTitle('Real-Time Sensor Data - Interactive View')
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
            self.plot_widget.enableAutoRange()
            self.plot_widget.setMouseEnabled(x=True, y=True)
            
            # Plot curves oluştur
            self.setup_plot_curves()
            
            # Legend ekle
            self.plot_widget.addLegend()
            
            self.is_initialized = True
            app_logger.info("PyQtGraph widget kuruldu")
            
        except Exception as e:
            app_logger.error(f"PyQtGraph widget kurulum hatası: {e}")
            raise
    
    def setup_plot_curves(self):
        """Grafik eğrilerini kurulum"""
        sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        
        for i, sensor_key in enumerate(sensor_keys):
            color = PLOT_COLORS[i % len(PLOT_COLORS)]
            
            # LED ismini app_settings.json'dan çek
            led_name = self._get_led_name_for_sensor(sensor_key)
            
            self.plot_curves[sensor_key] = self.plot_widget.plot(
                [], [], 
                pen=pg.mkPen(color=color, width=2),
                name=led_name
            )
    
    def show_window(self, title: str = "Interactive Real-Time Sensor Data", 
                   size: Tuple[int, int] = (800, 600)):
        """Grafik penceresini göster"""
        if not self.is_initialized:
            app_logger.warning("PyQtGraph widget henüz kurulmadı")
            return False
        
        try:
            self.plot_widget.show()
            self.plot_widget.resize(*size)
            self.plot_widget.setWindowTitle(title)
            
            app_logger.info(f"PyQtGraph penceresi açıldı: {title}")
            return True
            
        except Exception as e:
            app_logger.error(f"PyQtGraph pencere açma hatası: {e}")
            return False
    
    def update_data(self, timestamps: List[datetime], 
                   data_dict: Dict[str, List[float]]):
        """Grafik verilerini güncelle"""
        if not self.is_initialized or not timestamps:
            return
        
        try:
            # Veri doğrulama - boş veya geçersiz veriler için kontrol
            if not isinstance(timestamps, list) or len(timestamps) == 0:
                app_logger.warning("PyQtGraph: Geçersiz timestamp verisi")
                return
            
            # Zaman verilerini saniye cinsine çevir
            start_time = timestamps[0]
            time_seconds = [(t - start_time).total_seconds() for t in timestamps]
            
            # Veri senkronizasyonu için güvenli uzunluk hesaplama
            valid_data_found = False
            
            # Her sensör için veriyi güncelle - sıkı uzunluk kontrolü
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                if (sensor_key in data_dict and 
                    sensor_key in self.plot_curves and 
                    isinstance(data_dict[sensor_key], list) and
                    len(data_dict[sensor_key]) > 0):
                    
                    sensor_data = data_dict[sensor_key]
                    
                    # Veri uzunluklarını kesin olarak eşitle
                    min_len = min(len(time_seconds), len(sensor_data))
                    
                    # Minimum veri kontrolü - çok az veri varsa güncelleme yapma
                    if min_len >= 1:
                        # Veri türü kontrolü - sayısal değerler olduğundan emin ol
                        try:
                            clean_time_data = time_seconds[:min_len]
                            clean_sensor_data = [float(x) for x in sensor_data[:min_len]]
                            
                            self.plot_curves[sensor_key].setData(clean_time_data, clean_sensor_data)
                            valid_data_found = True
                            
                        except (ValueError, TypeError) as ve:
                            app_logger.warning(f"PyQtGraph {sensor_key} veri dönüşüm hatası: {ve}")
                            continue
                    else:
                        app_logger.debug(f"PyQtGraph {sensor_key}: Yetersiz veri (min_len={min_len})")
            
            if not valid_data_found:
                app_logger.warning("PyQtGraph: Hiç geçerli sensör verisi bulunamadı")
            
        except Exception as e:
            app_logger.error(f"PyQtGraph veri güncelleme hatası: {e}")
            import traceback
            app_logger.debug(f"PyQtGraph traceback: {traceback.format_exc()}")
    
    def reset_view(self):
        """Grafik görünümünü sıfırla"""
        if not self.is_initialized:
            return
        
        try:
            self.plot_widget.enableAutoRange()
            self.plot_widget.autoRange()
            app_logger.info("PyQtGraph görünümü sıfırlandı")
            
        except Exception as e:
            app_logger.error(f"PyQtGraph görünüm sıfırlama hatası: {e}")
    
    def set_axis_labels(self, x_label: str, y_label: str):
        """Eksen etiketlerini ayarla"""
        if not self.is_initialized:
            return
        
        try:
            self.plot_widget.setLabel('bottom', x_label)
            self.plot_widget.setLabel('left', y_label)
            
        except Exception as e:
            app_logger.error(f"PyQtGraph eksen etiketi hatası: {e}")
    
    def set_title(self, title: str):
        """Grafik başlığını ayarla"""
        if not self.is_initialized:
            return
        
        try:
            self.plot_widget.setTitle(title)
            
        except Exception as e:
            app_logger.error(f"PyQtGraph başlık ayarlama hatası: {e}")
    
    def close_window(self):
        """Grafik penceresini kapat"""
        if not self.is_initialized:
            return
        
        try:
            if self.plot_widget:
                self.plot_widget.close()
            app_logger.info("PyQtGraph penceresi kapatıldı")
            
        except Exception as e:
            app_logger.error(f"PyQtGraph pencere kapatma hatası: {e}")
    
    def is_available(self) -> bool:
        """PyQtGraph kullanılabilir mi?"""
        return PYQTGRAPH_AVAILABLE and self.is_initialized
    
    def update_legend_names(self, sensor_names: List[str]):
        """Legend isimlerini güncelle"""
        if not self.is_initialized:
            return
        
        try:
            # Mevcut curves'leri güncelle
            sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
            
            for i, (sensor_key, name) in enumerate(zip(sensor_keys, sensor_names)):
                if sensor_key in self.plot_curves and i < len(sensor_names):
                    # PyQtGraph'ta legend ismini değiştirmek için curve'ü yeniden oluştur
                    color = PLOT_COLORS[i % len(PLOT_COLORS)]
                    
                    # Eski curve'ü kaldır
                    self.plot_widget.removeItem(self.plot_curves[sensor_key])
                    
                    # Yeni curve oluştur
                    self.plot_curves[sensor_key] = self.plot_widget.plot(
                        [], [], 
                        pen=pg.mkPen(color=color, width=2),
                        name=name
                    )
            
            app_logger.info("PyQtGraph legend isimleri güncellendi")
            
        except Exception as e:
            app_logger.error(f"PyQtGraph legend güncelleme hatası: {e}")

class CustomGraphWindow:
    """Özelleştirilebilir PyQt grafik penceresi"""
    
    def __init__(self, selected_sensors: List[str], title: str = "Custom Graph"):
        self.selected_sensors = selected_sensors
        self.title = title
        self.plot_widget = None
        self.plot_curves = {}
        self.is_open = False
        
        # LED isimlerini yükle
        self.led_names = self._load_app_settings()
        
        if PYQTGRAPH_AVAILABLE:
            self.setup_custom_window()
    
    def _load_app_settings(self):
        """app_settings.json dosyasından LED isimlerini yükle"""
        try:
            # Script'in bulunduğu dizinin parent dizininde app_settings.json'ı ara
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            settings_path = os.path.join(parent_dir, 'app_settings.json')
            
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings.get('led_names', {})
            else:
                app_logger.warning(f"app_settings.json bulunamadı: {settings_path}")
                return {}
        except Exception as e:
            app_logger.error(f"Settings yükleme hatası: {e}")
            return {}
    
    def _get_led_name_for_sensor(self, sensor_key: str) -> str:
        """Sensor key'e göre LED ismini döndür"""
        default_names = {
            'UV_360nm': 'UV LED (360nm)',
            'Blue_450nm': 'Blue LED (450nm)', 
            'IR_850nm': 'IR LED (850nm)',
            'IR_940nm': 'IR LED (940nm)'
        }
        
        # Sensor key'e göre LED ismini bul - value'ları kullan
        led_name = None
        if sensor_key == 'UV_360nm':
            key = next((key for key in self.led_names.keys() if '360nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'Blue_450nm':
            key = next((key for key in self.led_names.keys() if '450nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'IR_850nm':
            key = next((key for key in self.led_names.keys() if '850nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        elif sensor_key == 'IR_940nm':
            key = next((key for key in self.led_names.keys() if '940nm' in key), None)
            led_name = self.led_names.get(key) if key else None
        
        if not led_name:
            led_name = default_names.get(sensor_key, sensor_key)
        
        return led_name
    
    def setup_custom_window(self):
        """Özel grafik penceresini kur"""
        try:
            # QApplication kontrolü
            from PyQt5.QtWidgets import QApplication
            import sys
            
            if not QApplication.instance():
                qt_app = QApplication(sys.argv)
                app_logger.info("QApplication oluşturuldu (CustomGraphWindow)")
            
            self.plot_widget = pg.PlotWidget()
            
            # Grafik ayarları
            self.plot_widget.setLabel('left', 'Value')
            self.plot_widget.setLabel('bottom', 'Time (seconds)')
            self.plot_widget.setTitle(self.title)
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
            self.plot_widget.enableAutoRange()
            self.plot_widget.setMouseEnabled(x=True, y=True)
            
            # Seçilen sensörler için curves oluştur
            for i, sensor_key in enumerate(self.selected_sensors):
                color = PLOT_COLORS[i % len(PLOT_COLORS)]
                
                # LED ismini app_settings.json'dan çek
                led_name = self._get_led_name_for_sensor(sensor_key)
                
                self.plot_curves[sensor_key] = self.plot_widget.plot(
                    [], [], 
                    pen=pg.mkPen(color=color, width=2),
                    name=led_name
                )
            
            # Legend ekle
            self.plot_widget.addLegend()
            
            app_logger.info(f"Özel PyQt grafik penceresi oluşturuldu: {self.title}")
            
        except Exception as e:
            app_logger.error(f"Özel PyQt pencere kurulum hatası: {e}")
            raise
    
    def show(self, size: Tuple[int, int] = (900, 700)):
        """Pencereyi göster"""
        if not PYQTGRAPH_AVAILABLE or not self.plot_widget:
            return False
        
        try:
            self.plot_widget.show()
            self.plot_widget.resize(*size)
            self.plot_widget.setWindowTitle(self.title)
            self.is_open = True
            
            return True
            
        except Exception as e:
            app_logger.error(f"Özel PyQt pencere gösterme hatası: {e}")
            return False
    
    def update_data(self, timestamps: List[datetime], 
                   data_dict: Dict[str, List[float]]):
        """Veriyi güncelle"""
        if not self.is_open or not timestamps:
            return
        
        try:
            # Veri doğrulama
            if not isinstance(timestamps, list) or len(timestamps) == 0:
                app_logger.warning("CustomGraphWindow: Geçersiz timestamp verisi")
                return
            
            # Zaman verilerini saniye cinsine çevir
            start_time = timestamps[0]
            time_seconds = [(t - start_time).total_seconds() for t in timestamps]
            
            valid_updates = 0
            
            # Seçilen sensörler için veriyi güncelle - sıkı senkronizasyon kontrolü
            for sensor_key in self.selected_sensors:
                if (sensor_key in data_dict and 
                    sensor_key in self.plot_curves and 
                    isinstance(data_dict[sensor_key], list) and
                    len(data_dict[sensor_key]) > 0):
                    
                    sensor_data = data_dict[sensor_key]
                    
                    # Veri uzunluklarını kesin olarak eşitle
                    min_len = min(len(time_seconds), len(sensor_data))
                    
                    if min_len >= 1:
                        try:
                            clean_time_data = time_seconds[:min_len]
                            clean_sensor_data = [float(x) for x in sensor_data[:min_len]]
                            
                            self.plot_curves[sensor_key].setData(clean_time_data, clean_sensor_data)
                            valid_updates += 1
                            
                        except (ValueError, TypeError) as ve:
                            app_logger.warning(f"CustomGraphWindow {sensor_key} veri dönüşüm hatası: {ve}")
                            continue
                    else:
                        app_logger.debug(f"CustomGraphWindow {sensor_key}: Yetersiz veri (min_len={min_len})")
            
            if valid_updates == 0:
                app_logger.warning("CustomGraphWindow: Hiç geçerli sensör verisi güncellenmedi")
            
        except Exception as e:
            app_logger.error(f"Özel PyQt veri güncelleme hatası: {e}")
            import traceback
            app_logger.debug(f"CustomGraphWindow traceback: {traceback.format_exc()}")
    
    def close(self):
        """Pencereyi kapat"""
        if self.plot_widget:
            try:
                self.plot_widget.close()
                self.is_open = False
                app_logger.info(f"Özel PyQt penceresi kapatıldı: {self.title}")
            except Exception as e:
                app_logger.error(f"Özel PyQt pencere kapatma hatası: {e}")
    
    def is_window_open(self) -> bool:
        """Pencere açık mı?"""
        return self.is_open and self.plot_widget is not None
