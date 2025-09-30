import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable, Any

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
    print("PyQtGraph ready for realtime panel")
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None
    print("PyQtGraph not available for realtime panel")

from utils.logger import app_logger
from config.constants import PLOT_COLORS, MATPLOTLIB_COLORS
from config.settings import settings_manager
from plotting.pyqt_subprocess import PyQtSubprocessManager

class RealTimePanel:    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.raw_data_checkboxes = {}
        self.cal_data_checkboxes = {}
        self.pyqt_manager = PyQtSubprocessManager()
        self.raw_data_btn = None
        self.cal_data_btn = None
        self.data_callback = None
        
        self.setup_panel()

    def set_data_callback(self, callback: Callable):
        self.data_callback = callback
    
    def setup_panel(self):
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="Real Time Data Visualization", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        boxes_frame = ttk.Frame(main_frame)
        boxes_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_raw_data_box(boxes_frame)

        self.setup_cal_data_box(boxes_frame)
    
    def setup_raw_data_box(self, parent_frame):
        style = ttk.Style()
        style.configure("BigLabel.TLabelframe.Label", font=("Arial", 14, "bold"))
        
        raw_frame = ttk.LabelFrame(parent_frame, text="1. Raw Data", padding=10, style="BigLabel.TLabelframe")
        raw_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        sensor_frame = ttk.Frame(raw_frame)
        sensor_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sensor_frame, text="Select Sensors:", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        checkbox_frame = ttk.Frame(sensor_frame)
        checkbox_frame.pack(fill=tk.X, pady=(5, 0))
        
        led_names = settings_manager.get_led_names()
        sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        led_key_mapping = {
            'UV_360nm': 'UV LED (360nm)',
            'Blue_450nm': 'Blue LED (450nm)', 
            'IR_850nm': 'IR LED (850nm)',
            'IR_940nm': 'IR LED (940nm)'
        }
        sensor_names = [led_names.get(led_key_mapping[key], led_key_mapping[key]) for key in sensor_keys]
        
        for i, (sensor_name, sensor_key) in enumerate(zip(sensor_names, sensor_keys)):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(checkbox_frame, text=sensor_name, variable=var)
            if i < 2:
                cb.pack(side=tk.LEFT, padx=(0, 20))
            else:
                cb.pack(side=tk.LEFT, padx=(0, 20))
            self.raw_data_checkboxes[sensor_key] = var
        
        button_frame = ttk.Frame(raw_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.raw_data_btn = ttk.Button(button_frame, text="Create Graph", 
                                      command=self.create_raw_data_graph,
                                      style="Green.TButton")
        self.raw_data_btn.pack(side=tk.RIGHT)
        
        
    
        
        
    
    def setup_cal_data_box(self, parent_frame):
        style = ttk.Style()
        style.configure("BigLabel.TLabelframe.Label", font=("Arial", 14, "bold"))
        
        cal_frame = ttk.LabelFrame(parent_frame, text="2. Calibrated Data", padding=10, style="BigLabel.TLabelframe")
        cal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sensör seçimi
        sensor_frame = ttk.Frame(cal_frame)
        sensor_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sensor_frame, text="Select Sensors:", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        # 4 sensör checkbox'ı
        checkbox_frame = ttk.Frame(sensor_frame)
        checkbox_frame.pack(fill=tk.X, pady=(5, 0))
        
        led_names = settings_manager.get_led_names()
        sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        led_key_mapping = {
            'UV_360nm': 'UV LED (360nm)',
            'Blue_450nm': 'Blue LED (450nm)', 
            'IR_850nm': 'IR LED (850nm)',
            'IR_940nm': 'IR LED (940nm)'
        }
        sensor_names = [led_names.get(led_key_mapping[key], led_key_mapping[key]) for key in sensor_keys]
        
        for i, (sensor_name, sensor_key) in enumerate(zip(sensor_names, sensor_keys)):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(checkbox_frame, text=sensor_name, variable=var)
            if i < 2:
                cb.pack(side=tk.LEFT, padx=(0, 20))
            else:
                cb.pack(side=tk.LEFT, padx=(0, 20))
            self.cal_data_checkboxes[sensor_key] = var
        
        button_frame = ttk.Frame(cal_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.cal_data_btn = ttk.Button(button_frame, text="Create Graph", 
                                      command=self.create_cal_data_graph,
                                      style="Purple.TButton")
        self.cal_data_btn.pack(side=tk.RIGHT)
        
        
    
    def create_raw_data_graph(self):
        if not PYQTGRAPH_AVAILABLE:
            messagebox.showerror("Error", "PyQtGraph gerekli ancak yüklü değil!")
            return
        
        selected_sensors = []
        for sensor_key, var in self.raw_data_checkboxes.items():
            if var.get():
                selected_sensors.append(sensor_key)
        
        if not selected_sensors:
            messagebox.showwarning("Warning", "En az bir sensör seçin!")
            return
        
        # Pencere zaten aktifse, gereksiz yeniden oluşturma
        if self.pyqt_manager.is_window_active("raw_data"):
            app_logger.info("Raw Data penceresi zaten aktif, yeniden oluşturulmuyor")
            return
        
        # Mevcut verileri al
        current_timestamps = []
        current_data = {}
        
        if self.data_callback:
            try:
                timestamps, raw_data, spectrum_data, calibrated_data = self.data_callback()
                if timestamps and raw_data:
                    current_timestamps = timestamps
                    current_data = raw_data
                    app_logger.info(f"Grafik için mevcut veri gönderiliyor: {len(timestamps)} nokta")
            except Exception as e:
                app_logger.warning(f"Mevcut veri alınamadı: {e}")
        
        success = self.pyqt_manager.create_graph_window(
            "raw_data", 
            selected_sensors, 
            "Raw Data - Real Time",
            "line",
            current_timestamps,
            current_data
        )
        
        if success:
            app_logger.info(f"Raw Data PyQt grafiği oluşturuldu: {selected_sensors}")
        else:
            messagebox.showerror("Error", "Raw Data grafiği oluşturulamadı!")
    
    
    def create_cal_data_graph(self):
        if not PYQTGRAPH_AVAILABLE:
            messagebox.showerror("Error", "PyQtGraph gerekli ancak yüklü değil!")
            return
        
        selected_sensors = []
        for sensor_key, var in self.cal_data_checkboxes.items():
            if var.get():
                selected_sensors.append(sensor_key)
        
        if not selected_sensors:
            messagebox.showwarning("Warning", "En az bir sensör seçin!")
            return
        
        # Calibrated data kontrolü - veri yoksa uyar
        if self.data_callback:
            try:
                # Ana pencereden calibrated data'yı kontrol et
                from gui.main_window import SpektroskpiGUI
                main_window = None
                for widget in self.parent_frame.winfo_toplevel().winfo_children():
                    if hasattr(widget, 'master') and hasattr(widget.master, 'data_processor'):
                        main_window = widget.master
                        break
                
                if main_window and hasattr(main_window, 'data_processor'):
                    calibrated_data = main_window.data_processor.get_calibrated_data()
                    has_cal_data = any(
                        sensor_key in calibrated_data and 
                        calibrated_data[sensor_key] and 
                        len(calibrated_data[sensor_key]) > 0 
                        for sensor_key in selected_sensors
                    )
                    
                    if not has_cal_data:
                        result = messagebox.askyesno(
                            "Calibrated Data N/A", 
                            "Seçilen sensörler için kalibrasyon verisi bulunamadı.\n\n"
                            "Grafik N/A değerleri gösterecek.\n\n"
                            "Devam etmek istiyor musunuz?"
                        )
                        if not result:
                            return
            except Exception as e:
                app_logger.warning(f"Calibrated data kontrolü yapılamadı: {e}")
        
        # Pencere zaten aktifse, gereksiz yeniden oluşturma
        if self.pyqt_manager.is_window_active("cal_data"):
            app_logger.info("Calibrated Data penceresi zaten aktif, yeniden oluşturulmuyor")
            return
        
        # Mevcut verileri al
        current_timestamps = []
        current_data = {}
        
        if self.data_callback:
            try:
                timestamps, raw_data, spectrum_data, calibrated_data = self.data_callback()
                if timestamps and calibrated_data:
                    current_timestamps = timestamps
                    current_data = calibrated_data
                    app_logger.info(f"Calibrated grafik için mevcut veri gönderiliyor: {len(timestamps)} nokta")
            except Exception as e:
                app_logger.warning(f"Mevcut calibrated veri alınamadı: {e}")
        
        success = self.pyqt_manager.create_graph_window(
            "cal_data", 
            selected_sensors, 
            "Calibrated Data - Real Time",
            "line",
            current_timestamps,
            current_data
        )
        
        if success:
            app_logger.info(f"Calibrated Data PyQt grafiği oluşturuldu: {selected_sensors}")
        else:
            messagebox.showerror("Error", "Calibrated Data grafiği oluşturulamadı!")
    
    def update_graphs(self, timestamps: List, raw_data: Dict[str, List], 
                     spectrum_data: List[float], calibrated_data: Dict[str, List]):
        try:
            # Gelişmiş veri doğrulama
            if not self._validate_graph_data(timestamps, raw_data, calibrated_data):
                return
                
            if timestamps and raw_data:
                app_logger.debug(f"RealTimePanel veri alındı: {len(timestamps)} zaman, {len(raw_data)} sensör")
                
                # BÜYÜK VERİ SETİ OPTİMİZASYONU - Son 1000 veri noktasını göster
                max_display_points = 1000
                if len(timestamps) > max_display_points:
                    display_timestamps = timestamps[-max_display_points:]
                    display_raw_data = {}
                    for sensor_key, values in raw_data.items():
                        if sensor_key != 'timestamps' and values and len(values) > max_display_points:
                            display_raw_data[sensor_key] = values[-max_display_points:]
                        else:
                            display_raw_data[sensor_key] = values
                    app_logger.debug(f"VERİ OPTİMİZASYONU: {len(timestamps)} -> {len(display_timestamps)} veri noktası (grafik performansı için)")
                else:
                    display_timestamps = timestamps
                    display_raw_data = raw_data
                
                # Raw Data grafiği güncelle (mV formatında)
                if self.pyqt_manager.is_window_active("raw_data"):
                    app_logger.debug("Raw Data penceresi güncelleniyor...")
                    # Raw data'yı mV formatına çevir (4 haneli sayı)
                    formatted_raw_data = {}
                    for sensor_key, values in display_raw_data.items():
                        if sensor_key != 'timestamps' and values:
                            # Değerleri mV olarak formatla (4 haneli)
                            formatted_values = [max(0, min(9999, int(v))) for v in values]
                            formatted_raw_data[sensor_key] = formatted_values
                    
                    self.pyqt_manager.update_graph_data("raw_data", display_timestamps, formatted_raw_data)
                
                # Calibrated Data grafiği güncelle (N/A kontrolü ile) - OPTİMİZE EDİLDİ
                if self.pyqt_manager.is_window_active("cal_data"):
                    app_logger.debug("Cal Data penceresi güncelleniyor...")
                    
                    # Calibrated data için de aynı optimizasyon
                    display_cal_data = {}
                    if len(timestamps) > max_display_points:
                        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                            if (sensor_key in calibrated_data and 
                                calibrated_data[sensor_key] and 
                                len(calibrated_data[sensor_key]) > max_display_points):
                                display_cal_data[sensor_key] = calibrated_data[sensor_key][-max_display_points:]
                            elif (sensor_key in calibrated_data and calibrated_data[sensor_key]):
                                display_cal_data[sensor_key] = calibrated_data[sensor_key]
                            else:
                                # N/A durumu - son 1000 nokta için 0 değeri
                                display_cal_data[sensor_key] = [0] * len(display_timestamps)
                    else:
                        # Tüm veri seti küçük - normal işlem
                        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                            if (sensor_key in calibrated_data and 
                                calibrated_data[sensor_key] and 
                                len(calibrated_data[sensor_key]) > 0):
                                display_cal_data[sensor_key] = calibrated_data[sensor_key]
                            else:
                                # N/A durumu - 0 değeri ile göster
                                display_cal_data[sensor_key] = [0] * len(timestamps)
                    
                    self.pyqt_manager.update_graph_data("cal_data", display_timestamps, display_cal_data)
                
        except Exception as e:
            app_logger.error(f"Real time panel güncelleme hatası: {e}")
    
    def _validate_graph_data(self, timestamps: List, raw_data: Dict[str, List], 
                           calibrated_data: Dict[str, List]) -> bool:
        """Grafik verilerini doğrula"""
        try:
            # Temel veri kontrolü
            if not timestamps or len(timestamps) < 1:
                app_logger.debug("RealTimePanel: Timestamp verisi yok veya yetersiz")
                return False
            
            # Timestamps türü kontrolü
            if not isinstance(timestamps, list):
                app_logger.warning("RealTimePanel: Timestamps list tipinde değil")
                return False
            
            # Raw data kontrolü
            if not isinstance(raw_data, dict):
                app_logger.warning("RealTimePanel: Raw data dict tipinde değil")
                return False
            
            # Calibrated data kontrolü
            if not isinstance(calibrated_data, dict):
                app_logger.warning("RealTimePanel: Calibrated data dict tipinde değil")
                return False
            
            # Sensör verilerinin uzunluk kontrolü
            expected_sensors = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
            timestamp_count = len(timestamps)
            
            for sensor_key in expected_sensors:
                # Raw data kontrolleri
                if sensor_key in raw_data:
                    if not isinstance(raw_data[sensor_key], list):
                        app_logger.warning(f"RealTimePanel: {sensor_key} raw data list tipinde değil")
                        continue
                    
                    raw_len = len(raw_data[sensor_key])
                    if raw_len > 0 and abs(raw_len - timestamp_count) > 1:
                        app_logger.warning(f"RealTimePanel: {sensor_key} raw data uzunluk uyumsuzluğu (timestamps: {timestamp_count}, data: {raw_len})")
                
                # Calibrated data kontrolleri
                if sensor_key in calibrated_data:
                    if not isinstance(calibrated_data[sensor_key], list):
                        app_logger.warning(f"RealTimePanel: {sensor_key} calibrated data list tipinde değil")
                        continue
                    
                    cal_len = len(calibrated_data[sensor_key])
                    if cal_len > 0 and abs(cal_len - timestamp_count) > 1:
                        app_logger.warning(f"RealTimePanel: {sensor_key} calibrated data uzunluk uyumsuzluğu (timestamps: {timestamp_count}, data: {cal_len})")
            
            # Minimum veri eşiği kontrolü
            has_valid_raw_data = any(
                sensor_key in raw_data and 
                isinstance(raw_data[sensor_key], list) and 
                len(raw_data[sensor_key]) > 0 
                for sensor_key in expected_sensors
            )
            
            if not has_valid_raw_data:
                app_logger.debug("RealTimePanel: Hiç geçerli raw data bulunamadı")
                return False
            
            return True
            
        except Exception as e:
            app_logger.error(f"RealTimePanel veri doğrulama hatası: {e}")
            return False
    
    def close_all_windows(self):
        try:
            self.pyqt_manager.close_all_windows()
            app_logger.info("Tüm real time grafik pencereleri kapatıldı")
            
        except Exception as e:
            app_logger.error(f"Grafik pencere kapatma hatası: {e}")
    
    def apply_current_theme(self):
        try:
            from config.settings import settings_manager
            current_theme = settings_manager.get_theme()
            
            # Bu panel butonları otomatik olarak StyleManager tarafından güncelleniyor
            app_logger.debug(f"Realtime panel {current_theme} tema uygulandı")
            
        except Exception as e:
            app_logger.error(f"Realtime panel tema uygulama hatası: {e}")


