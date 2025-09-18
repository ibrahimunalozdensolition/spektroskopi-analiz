"""
Grafik Yöneticisi - PyQt ve Matplotlib arasında koordinasyon
"""

import tkinter as tk
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .pyqt_plotter import PyQtPlotter, CustomGraphWindow, PYQTGRAPH_AVAILABLE
from .matplotlib_plotter import MatplotlibPlotter, SpectrumPlotter
from utils.logger import app_logger

class PlotManager:
    """Grafik yöneticisi sınıfı"""
    
    def __init__(self, realtime_frame: Optional[tk.Frame], spectrum_frame: tk.Frame):
        self.realtime_frame = realtime_frame
        self.spectrum_frame = spectrum_frame
        
        # Grafik nesneleri
        self.pyqt_plotter = None
        self.matplotlib_plotter = None
        self.spectrum_plotter = None
        
        # Özel grafik pencereleri
        self.custom_windows: Dict[str, CustomGraphWindow] = {}
        
        # Grafik tercihi
        self.use_pyqt = PYQTGRAPH_AVAILABLE
        
        self.setup_plotters()
    
    def setup_plotters(self):
        """Grafik sistemlerini kur - Windows uyumlu"""
        import platform
        
        try:
            platform_name = platform.system()
            app_logger.info(f"Grafik sistemi kuruluyor - Platform: {platform_name}")
            
            # PyQt kurulumu dene
            if PYQTGRAPH_AVAILABLE:
                try:
                    self.pyqt_plotter = PyQtPlotter()
                    self.use_pyqt = True
                    app_logger.info(f"PyQt grafik sistemi kuruldu - {platform_name}")
                    
                except Exception as e:
                    app_logger.warning(f"PyQt kurulum hatası ({platform_name}), matplotlib'e geçiliyor: {e}")
                    self.use_pyqt = False
            else:
                app_logger.info(f"PyQtGraph mevcut değil ({platform_name}) - matplotlib kullanılacak")
                self.use_pyqt = False
            
            # Matplotlib fallback (sadece realtime_frame varsa)
            if not self.use_pyqt and self.realtime_frame:
                try:
                    self.matplotlib_plotter = MatplotlibPlotter(self.realtime_frame)
                    app_logger.info(f"Matplotlib grafik sistemi kuruldu - {platform_name}")
                except Exception as e:
                    app_logger.error(f"Matplotlib kurulum hatası ({platform_name}): {e}")
                    if platform_name == "Windows":
                        app_logger.error("Windows'ta grafik problemi: Matplotlib backend veya kütüphane eksikliği")
                    # Grafik olmadan devam et
                    self.matplotlib_plotter = None
            
            # Spektrum grafiği (her zaman matplotlib)
            try:
                self.spectrum_plotter = SpectrumPlotter(self.spectrum_frame)
                app_logger.info(f"Spektrum grafiği kuruldu - {platform_name}")
            except Exception as e:
                app_logger.error(f"Spektrum grafik kurulum hatası ({platform_name}): {e}")
                self.spectrum_plotter = None
            
        except Exception as e:
            app_logger.error(f"Grafik sistemi kurulum hatası: {e}")
            raise
    
    def show_realtime_window(self, title: str = "Interactive Real-Time Sensor Data"):
        """Real-time grafik penceresini göster"""
        if self.use_pyqt and self.pyqt_plotter:
            return self.pyqt_plotter.show_window(title)
        return False
    
    def update_realtime_data(self, timestamps: List[datetime], 
                           data_dict: Dict[str, List[float]],
                           led_names: Optional[List[str]] = None):
        """Real-time grafik verilerini güncelle"""
        try:
            if self.use_pyqt and self.pyqt_plotter:
                self.pyqt_plotter.update_data(timestamps, data_dict)
            elif self.matplotlib_plotter:
                self.matplotlib_plotter.update_data(timestamps, data_dict, led_names)
            
        except Exception as e:
            app_logger.error(f"Real-time veri güncelleme hatası: {e}")
    
    def update_spectrum_data(self, intensities: List[float], 
                           sensor_names: Optional[List[str]] = None):
        """Spektrum grafiği güncelle"""
        try:
            if self.spectrum_plotter:
                self.spectrum_plotter.update_spectrum(intensities, sensor_names)
                
        except Exception as e:
            app_logger.error(f"Spektrum güncelleme hatası: {e}")
    
    def reset_realtime_view(self):
        """Real-time grafik görünümünü sıfırla"""
        try:
            if self.use_pyqt and self.pyqt_plotter:
                self.pyqt_plotter.reset_view()
            elif self.matplotlib_plotter:
                self.matplotlib_plotter.reset_view()
                
        except Exception as e:
            app_logger.error(f"Grafik sıfırlama hatası: {e}")
    
    def adjust_x_range(self, increase: bool):
        """X eksen aralığını ayarla"""
        try:
            if not self.use_pyqt and self.matplotlib_plotter:
                if increase:
                    self.matplotlib_plotter.increase_x_range()
                else:
                    self.matplotlib_plotter.decrease_x_range()
                    
        except Exception as e:
            app_logger.error(f"X eksen ayarlama hatası: {e}")
    
    def adjust_y_range(self, increase: bool):
        """Y eksen aralığını ayarla"""
        try:
            if not self.use_pyqt and self.matplotlib_plotter:
                if increase:
                    self.matplotlib_plotter.increase_y_range()
                else:
                    self.matplotlib_plotter.decrease_y_range()
                    
        except Exception as e:
            app_logger.error(f"Y eksen ayarlama hatası: {e}")
    
    def update_legend_names(self, sensor_names: List[str]):
        """Legend isimlerini güncelle"""
        try:
            if self.use_pyqt and self.pyqt_plotter:
                clean_names = [clean_sensor_name(name) for name in sensor_names]
                self.pyqt_plotter.update_legend_names(clean_names)
                
        except Exception as e:
            app_logger.error(f"Legend güncelleme hatası: {e}")
    
    def create_custom_window(self, window_id: str, selected_sensors: List[str], 
                           title: str = "Custom Graph") -> bool:
        """Özel grafik penceresi oluştur"""
        try:
            if not PYQTGRAPH_AVAILABLE:
                app_logger.warning("PyQtGraph mevcut değil, özel pencere oluşturulamıyor")
                return False
            
            if window_id in self.custom_windows:
                # Mevcut pencereyi kapat
                self.custom_windows[window_id].close()
                del self.custom_windows[window_id]
            
            # Yeni pencere oluştur
            custom_window = CustomGraphWindow(selected_sensors, title)
            if custom_window.show():
                self.custom_windows[window_id] = custom_window
                app_logger.info(f"Özel grafik penceresi oluşturuldu: {window_id}")
                return True
            
        except Exception as e:
            app_logger.error(f"Özel pencere oluşturma hatası: {e}")
        
        return False
    
    def update_custom_window(self, window_id: str, timestamps: List[datetime], 
                           data_dict: Dict[str, List[float]]):
        """Özel grafik penceresini güncelle"""
        try:
            if window_id in self.custom_windows:
                self.custom_windows[window_id].update_data(timestamps, data_dict)
                
        except Exception as e:
            app_logger.error(f"Özel pencere güncelleme hatası: {e}")
    
    def close_custom_window(self, window_id: str):
        """Özel grafik penceresini kapat"""
        try:
            if window_id in self.custom_windows:
                self.custom_windows[window_id].close()
                del self.custom_windows[window_id]
                app_logger.info(f"Özel grafik penceresi kapatıldı: {window_id}")
                
        except Exception as e:
            app_logger.error(f"Özel pencere kapatma hatası: {e}")
    
    def close_all_custom_windows(self):
        """Tüm özel grafik pencerelerini kapat"""
        try:
            for window_id in list(self.custom_windows.keys()):
                self.close_custom_window(window_id)
                
        except Exception as e:
            app_logger.error(f"Tüm özel pencere kapatma hatası: {e}")
    
    def is_custom_window_open(self, window_id: str) -> bool:
        """Özel pencere açık mı?"""
        return (window_id in self.custom_windows and 
                self.custom_windows[window_id].is_window_open())
    
    def get_plot_info(self) -> Dict[str, any]:
        """Grafik sistemi bilgilerini al"""
        return {
            'using_pyqt': self.use_pyqt,
            'pyqt_available': PYQTGRAPH_AVAILABLE,
            'custom_windows_count': len(self.custom_windows),
            'custom_window_ids': list(self.custom_windows.keys())
        }
