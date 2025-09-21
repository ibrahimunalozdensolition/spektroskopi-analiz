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
        
        if not self.pyqt_manager.is_window_active("raw_data"):
            pass  
        
        success = self.pyqt_manager.create_graph_window(
            "raw_data", 
            selected_sensors, 
            "Raw Data - Real Time",
            "line"
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
        
        if not self.pyqt_manager.is_window_active("cal_data"):
            pass  # Pencere zaten kapalı, yeniden açmaya gerek yok
        
        success = self.pyqt_manager.create_graph_window(
            "cal_data", 
            selected_sensors, 
            "Calibrated Data - Real Time",
            "line"
        )
        
        if success:
            app_logger.info(f"Calibrated Data PyQt grafiği oluşturuldu: {selected_sensors}")
        else:
            messagebox.showerror("Error", "Calibrated Data grafiği oluşturulamadı!")
    
    def update_graphs(self, timestamps: List, raw_data: Dict[str, List], 
                     spectrum_data: List[float], calibrated_data: Dict[str, List]):
        try:
            if not timestamps or len(timestamps) < 2:
                return
                
            if timestamps and raw_data:
                app_logger.debug(f"RealTimePanel veri alındı: {len(timestamps)} zaman, {len(raw_data)} sensör")
                
                # Raw Data grafiği güncelle (mV formatında)
                if self.pyqt_manager.is_window_active("raw_data"):
                    app_logger.debug("Raw Data penceresi güncelleniyor...")
                    # Raw data'yı mV formatına çevir (4 haneli sayı)
                    formatted_raw_data = {}
                    for sensor_key, values in raw_data.items():
                        if sensor_key != 'timestamps' and values:
                            # Değerleri mV olarak formatla (4 haneli)
                            formatted_values = [max(0, min(9999, int(v))) for v in values]
                            formatted_raw_data[sensor_key] = formatted_values
                    
                    self.pyqt_manager.update_graph_data("raw_data", timestamps, formatted_raw_data)
                
                # Calibrated Data grafiği güncelle (N/A kontrolü ile)
                if self.pyqt_manager.is_window_active("cal_data"):
                    app_logger.debug("Cal Data penceresi güncelleniyor...")
                    
                    # Debug: Calibrated data durumunu kontrol et
                    app_logger.debug(f"Calibrated data keys: {list(calibrated_data.keys())}")
                    for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                        if sensor_key in calibrated_data:
                            data_length = len(calibrated_data[sensor_key]) if calibrated_data[sensor_key] else 0
                            app_logger.debug(f"{sensor_key} calibrated data length: {data_length}")
                    
                    # Calibrated data kontrolü ve N/A işleme
                    processed_cal_data = {}
                    for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                        if (sensor_key in calibrated_data and 
                            calibrated_data[sensor_key] and 
                            len(calibrated_data[sensor_key]) > 0):
                            # Calibrated data mevcut
                            processed_cal_data[sensor_key] = calibrated_data[sensor_key]
                            app_logger.debug(f"{sensor_key}: Calibrated data kullanılıyor ({len(calibrated_data[sensor_key])} nokta)")
                        else:
                            # N/A durumu - 0 değeri ile göster (grafik için)
                            processed_cal_data[sensor_key] = [0] * len(timestamps)
                            app_logger.debug(f"{sensor_key}: N/A durumu - 0 değerleri kullanılıyor")
                    
                    self.pyqt_manager.update_graph_data("cal_data", timestamps, processed_cal_data)
                
        except Exception as e:
            app_logger.error(f"Real time panel güncelleme hatası: {e}")
    
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


