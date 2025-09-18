"""
Matplotlib Tabanlı Grafik Modülü (Fallback)
"""

import os
import platform

# Windows için matplotlib backend ayarları
if platform.system() == "Windows":
    os.environ['MPLBACKEND'] = 'TkAgg'
    # Windows'ta GUI threading problemlerini önle
    os.environ['MPLCONFIGDIR'] = os.path.join(os.path.expanduser("~"), ".matplotlib")

try:
    import matplotlib
    # Windows için backend'i zorla ayarla
    if platform.system() == "Windows":
        matplotlib.use('TkAgg', force=True)
    
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    MATPLOTLIB_AVAILABLE = True
    print(f"Matplotlib successfully imported - Backend: {matplotlib.get_backend()}")
    
except ImportError as e:
    print(f"Matplotlib import error: {e}")
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvasTkAgg = None
    matplotlib = None
import tkinter as tk
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

from config.constants import MATPLOTLIB_COLORS, DEFAULT_X_RANGE_SECONDS
from utils.logger import app_logger
from utils.helpers import filter_data_by_time_range, clean_sensor_name

class MatplotlibPlotter:
    """Matplotlib tabanlı grafik sınıfı"""
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # Grafik kontrol değişkenleri
        self.x_range = DEFAULT_X_RANGE_SECONDS
        self.y_min = None
        self.y_max = None
        
        self.setup_matplotlib_plot()
    
    def setup_matplotlib_plot(self):
        if not MATPLOTLIB_AVAILABLE:
            raise Exception("Matplotlib mevcut değil")
        
        try:
            self.fig, self.ax = plt.subplots(figsize=(8, 6))
            self.canvas = FigureCanvasTkAgg(self.fig, self.parent_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # İlk grafik ayarları
            self.setup_initial_plot()
            
            app_logger.info("Matplotlib grafik kuruldu")
            
        except Exception as e:
            app_logger.error(f"Matplotlib kurulum hatası: {e}")
            raise
    
    def setup_initial_plot(self):
        """İlk grafik ayarlarını yap"""
        self.ax.set_title("Real-Time Sensor Data")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Voltage (mV)")
        self.ax.grid(True, alpha=0.3)
        
        # Boş çizgiler oluştur (legend için)
        for i, (sensor_key, color) in enumerate(zip(
            ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm'],
            MATPLOTLIB_COLORS)):
            self.ax.plot([], [], label=sensor_key, color=color, linewidth=2)
        
        self.ax.legend()
        self.canvas.draw()
    
    def update_data(self, timestamps: List[datetime], 
                   data_dict: Dict[str, List[float]],
                   led_names: Optional[List[str]] = None):
        """Grafik verilerini güncelle"""
        try:
            self.ax.clear()
            self.ax.set_title("Real-Time Sensor Data")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Voltage (mV)")
            self.ax.grid(True, alpha=0.3)
            
            if not timestamps:
                self.canvas.draw()
                return
            
            # Zaman aralığına göre filtrele
            filtered_timestamps, filtered_data = filter_data_by_time_range(
                timestamps, data_dict, self.x_range)
            
            if not filtered_timestamps:
                self.canvas.draw()
                return
            
            # Grafik etiketlerini hazırla
            labels = led_names or ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
            if led_names:
                labels = [clean_sensor_name(name) for name in led_names]
            
            # Her sensör için çizgi çiz - veri uzunluklarını eşitle
            for i, (sensor_key, label, color) in enumerate(zip(
                ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm'],
                labels, MATPLOTLIB_COLORS)):
                
                if sensor_key in filtered_data and filtered_data[sensor_key]:
                    plot_data = filtered_data[sensor_key]
                    # Veri uzunluklarını eşitle
                    min_len = min(len(filtered_timestamps), len(plot_data))
                    if min_len > 0:
                        plot_times = filtered_timestamps[:min_len]
                        plot_values = plot_data[:min_len]
                        
                        self.ax.plot(plot_times, plot_values, 
                                   label=label, color=color, linewidth=2)
            
            # Y ekseni kontrolü
            if self.y_min is not None and self.y_max is not None:
                self.ax.set_ylim(self.y_min, self.y_max)
            
            self.ax.legend()
            self.canvas.draw()
            
        except Exception as e:
            app_logger.error(f"Matplotlib veri güncelleme hatası: {e}")
    
    def increase_x_range(self):
        """X eksen aralığını artır"""
        self.x_range = min(self.x_range * 1.5, 300)  # Maksimum 5 dakika
        app_logger.debug(f"X eksen aralığı artırıldı: {self.x_range}s")
    
    def decrease_x_range(self):
        """X eksen aralığını azalt"""
        self.x_range = max(self.x_range / 1.5, 10)  # Minimum 10 saniye
        app_logger.debug(f"X eksen aralığı azaltıldı: {self.x_range}s")
    
    def increase_y_range(self):
        """Y eksen aralığını artır"""
        try:
            current_ylim = self.ax.get_ylim()
            y_center = (current_ylim[0] + current_ylim[1]) / 2
            y_range = current_ylim[1] - current_ylim[0]
            new_range = y_range * 1.2
            self.y_min = y_center - new_range / 2
            self.y_max = y_center + new_range / 2
            app_logger.debug(f"Y eksen aralığı artırıldı: {self.y_min:.3f} - {self.y_max:.3f}")
        except Exception as e:
            app_logger.error(f"Y eksen artırma hatası: {e}")
    
    def decrease_y_range(self):
        """Y eksen aralığını azalt"""
        try:
            current_ylim = self.ax.get_ylim()
            y_center = (current_ylim[0] + current_ylim[1]) / 2
            y_range = current_ylim[1] - current_ylim[0]
            new_range = max(y_range / 1.2, 0.1)  # Minimum 0.1V aralık
            self.y_min = y_center - new_range / 2
            self.y_max = y_center + new_range / 2
            app_logger.debug(f"Y eksen aralığı azaltıldı: {self.y_min:.3f} - {self.y_max:.3f}")
        except Exception as e:
            app_logger.error(f"Y eksen azaltma hatası: {e}")
    
    def reset_view(self):
        """Grafik görünümünü sıfırla"""
        self.x_range = DEFAULT_X_RANGE_SECONDS
        self.y_min = None
        self.y_max = None
        app_logger.info("Matplotlib görünümü sıfırlandı")
    
    def set_title(self, title: str):
        """Grafik başlığını ayarla"""
        try:
            self.ax.set_title(title)
            self.canvas.draw()
        except Exception as e:
            app_logger.error(f"Matplotlib başlık ayarlama hatası: {e}")
    
    def set_axis_labels(self, x_label: str, y_label: str):
        """Eksen etiketlerini ayarla"""
        try:
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel(y_label)
            self.canvas.draw()
        except Exception as e:
            app_logger.error(f"Matplotlib eksen etiketi hatası: {e}")

class SpectrumPlotter:
    """Spektrum analizi grafiği"""
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.fig = None
        self.ax = None
        self.canvas = None
        
        self.setup_spectrum_plot()
    
    def setup_spectrum_plot(self):
        """Spektrum grafiği kur"""
        if not MATPLOTLIB_AVAILABLE:
            raise Exception("Matplotlib mevcut değil")
        
        try:
            self.fig, self.ax = plt.subplots(figsize=(8, 6))
            self.canvas = FigureCanvasTkAgg(self.fig, self.parent_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # İlk ayarlar
            self.ax.set_title("Spectrum Analysis")
            self.ax.set_xlabel("Sensor Type")
            self.ax.set_ylabel("Intensity (V)")
            self.ax.grid(True, alpha=0.3)
            
            # Boş spektrum çiz
            self.update_spectrum([0, 0, 0, 0])
            
            app_logger.info("Spektrum grafiği kuruldu")
            
        except Exception as e:
            app_logger.error(f"Spektrum grafik kurulum hatası: {e}")
            raise
    
    def update_spectrum(self, intensities: List[float], 
                       sensor_names: Optional[List[str]] = None):
        """Spektrum grafiğini güncelle"""
        try:
            self.ax.clear()
            self.ax.set_title("Spectrum Analysis")
            self.ax.set_xlabel("Sensor Type")
            self.ax.set_ylabel("Intensity (V)")
            self.ax.grid(True, alpha=0.3)
            
            # Sensör isimleri
            if sensor_names:
                labels = [clean_sensor_name(name) for name in sensor_names]
            else:
                labels = ['UV', 'Blue', 'IR850', 'IR940']
            
            # Bar grafik çiz
            bars = self.ax.bar(labels, intensities, width=0.6, alpha=0.7, 
                             color=MATPLOTLIB_COLORS)
            
            # Değerleri bar'ların üzerine yaz
            for bar, intensity in zip(bars, intensities):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                           f'{intensity:.3f}V', ha='center', va='bottom')
            
            self.canvas.draw()
            
        except Exception as e:
            app_logger.error(f"Spektrum güncelleme hatası: {e}")
