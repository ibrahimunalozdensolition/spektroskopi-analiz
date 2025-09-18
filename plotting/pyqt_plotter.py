"""
PyQt Tabanlı İnteraktif Grafik Modülü
"""

import sys
import os
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
    """PyQt tabanlı interaktif grafik sınıfı"""
    
    def __init__(self):
        self.qt_app = None
        self.plot_widget = None
        self.plot_curves = {}
        self.is_initialized = False
        
        if PYQTGRAPH_AVAILABLE:
            self.setup_qt_application()
            self.setup_plot_widget()
    
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
        sensor_names = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        
        for i, sensor in enumerate(sensor_names):
            color = PLOT_COLORS[i % len(PLOT_COLORS)]
            self.plot_curves[sensor] = self.plot_widget.plot(
                [], [], 
                pen=pg.mkPen(color=color, width=2),
                name=sensor
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
            # Zaman verilerini saniye cinsine çevir
            start_time = timestamps[0]
            time_seconds = [(t - start_time).total_seconds() for t in timestamps]
            
            # Her sensör için veriyi güncelle - uzunluk kontrolü gevşetildi
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                if (sensor_key in data_dict and 
                    sensor_key in self.plot_curves and 
                    len(data_dict[sensor_key]) > 0):
                    
                    # Veri uzunluklarını eşitle
                    min_len = min(len(time_seconds), len(data_dict[sensor_key]))
                    if min_len > 0:
                        self.plot_curves[sensor_key].setData(
                            time_seconds[:min_len], 
                            data_dict[sensor_key][:min_len]
                        )
            
        except Exception as e:
            app_logger.error(f"PyQtGraph veri güncelleme hatası: {e}")
    
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
        
        if PYQTGRAPH_AVAILABLE:
            self.setup_custom_window()
    
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
                self.plot_curves[sensor_key] = self.plot_widget.plot(
                    [], [], 
                    pen=pg.mkPen(color=color, width=2),
                    name=sensor_key
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
            # Zaman verilerini saniye cinsine çevir
            start_time = timestamps[0]
            time_seconds = [(t - start_time).total_seconds() for t in timestamps]
            
            # Seçilen sensörler için veriyi güncelle
            for sensor_key in self.selected_sensors:
                if (sensor_key in data_dict and 
                    sensor_key in self.plot_curves and 
                    len(data_dict[sensor_key]) == len(time_seconds)):
                    
                    self.plot_curves[sensor_key].setData(time_seconds, data_dict[sensor_key])
            
        except Exception as e:
            app_logger.error(f"Özel PyQt veri güncelleme hatası: {e}")
    
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
