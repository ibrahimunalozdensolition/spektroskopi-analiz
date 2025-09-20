import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Any

from utils.logger import app_logger
from config.constants import SENSOR_INFO

class DetectorPanel:
    """4 Detector Real-Time Panel - UV, Blue, IR1, IR2"""
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.data_callback = None
        
        # Detector bilgileri
        self.detectors = {
            "UV_DETECTOR": {"name": "UV Detector", "sensor_key": "UV_360nm"},
            "BLUE_DETECTOR": {"name": "Blue Detector", "sensor_key": "Blue_450nm"},
            "IR_DETECTOR_1": {"name": "IR Detector 1", "sensor_key": "IR_850nm"},
            "IR_DETECTOR_2": {"name": "IR Detector 2", "sensor_key": "IR_940nm"}
        }
        
        # Veri label'ları
        self.raw_data_labels = {}
        self.cal_data_labels = {}
        
        # Mevcut değerler
        self.current_raw_values = {key: 0.0 for key in self.detectors.keys()}
        self.current_cal_values = {key: 0.0 for key in self.detectors.keys()}
        
        self.setup_panel()
    
    def set_data_callback(self, callback: Callable):
        """Veri callback'ini ayarla"""
        self.data_callback = callback
    
    def setup_panel(self):
        """Ana paneli kur"""
        # Scrollable container oluştur (formula_panel'deki gibi)
        canvas = tk.Canvas(self.parent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Canvas boyutu değiştiğinde responsive güncelleme
        def _on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Canvas genişliğini scrollable_frame'e uygula
            canvas_width = event.width
            canvas_items = canvas.find_all()
            if canvas_items:
                canvas.itemconfig(canvas_items[0], width=canvas_width)
        
        canvas.bind("<Configure>", _on_canvas_configure)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel binding for scrolling
        def _on_mousewheel(event):
            try:
                if hasattr(event, 'delta'):
                    if event.delta > 0:
                        canvas.yview_scroll(-1, "units")
                    elif event.delta < 0:
                        canvas.yview_scroll(1, "units")
                else:
                    if event.num == 4:
                        canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        canvas.yview_scroll(1, "units")
            except Exception as e:
                print(f"Scroll event error: {e}")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Ana içerik frame'i
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Başlık
        self.title_label = ttk.Label(main_frame, text="Real Time Panel", 
                               font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(0, 5))
        
        # 2x2 Grid için ana container
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Grid yapısını oluştur
        self.setup_detector_grid(grid_frame)
        
        # Veri güncelleme için timer başlat
        self.update_data()
        
        # Responsive font boyutları için pencere boyut değişikliğini dinle
        self.setup_responsive_fonts(main_frame)
    
    def setup_detector_grid(self, parent_frame):
        """2x2 detector grid'ini oluştur - responsive"""
        # Grid configuration - maksimum büyüme için minimum boyutlar
        parent_frame.grid_rowconfigure(0, weight=2, minsize=80)
        parent_frame.grid_rowconfigure(1, weight=2, minsize=80)
        parent_frame.grid_columnconfigure(0, weight=2, minsize=100)
        parent_frame.grid_columnconfigure(1, weight=2, minsize=100)
        
        # Parent frame'i responsive yap
        parent_frame.pack_configure(fill=tk.BOTH, expand=True)
        
        # Detector'ları sırayla yerleştir
        detector_keys = list(self.detectors.keys())
        
        # UV Detector - Sol üst (0,0)
        self.create_detector_box(parent_frame, detector_keys[0], 0, 0)
        
        # Blue Detector - Sağ üst (0,1)
        self.create_detector_box(parent_frame, detector_keys[1], 0, 1)
        
        # IR Detector 1 - Sol alt (1,0)
        self.create_detector_box(parent_frame, detector_keys[2], 1, 0)
        
        # IR Detector 2 - Sağ alt (1,1)
        self.create_detector_box(parent_frame, detector_keys[3], 1, 1)
    
    def create_detector_box(self, parent_frame, detector_key, row, col):
        """Tek bir detector box'ı oluştur"""
        detector_info = self.detectors[detector_key]
        
        # Ana detector frame'i - border ile
        detector_frame = ttk.LabelFrame(parent_frame, text=detector_info["name"], 
                                       padding=5, style="DetectorBox.TLabelframe")
        detector_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # İç kısım için grid - maksimum büyüme için
        detector_frame.grid_rowconfigure(0, weight=3, minsize=50)
        detector_frame.grid_columnconfigure(0, weight=3, minsize=60)
        detector_frame.grid_columnconfigure(1, weight=3, minsize=60)
        
        # RAW DATA bölümü - Sol
        raw_frame = ttk.LabelFrame(detector_frame, text="RAW DATA", padding=3)
        raw_frame.grid(row=0, column=0, padx=(0, 3), pady=0, sticky="nsew")
        
        # RAW DATA içeriği - responsive
        raw_value_label = ttk.Label(raw_frame, text="0.000", 
                                   font=("Arial", 24, "bold"), anchor="center")
        raw_value_label.pack(expand=True, fill=tk.BOTH)
        
        raw_unit_label = ttk.Label(raw_frame, text="V", 
                                  font=("Arial", 16), anchor="center")
        raw_unit_label.pack(fill=tk.X)
        
        # CAL bölümü - Sağ
        cal_frame = ttk.LabelFrame(detector_frame, text="CAL", padding=3)
        cal_frame.grid(row=0, column=1, padx=(3, 0), pady=0, sticky="nsew")
        
        # CAL içeriği - responsive
        cal_value_label = ttk.Label(cal_frame, text="0.000", 
                                   font=("Arial", 24, "bold"), anchor="center")
        cal_value_label.pack(expand=True, fill=tk.BOTH)
        
        cal_unit_label = ttk.Label(cal_frame, text="ppm", 
                                  font=("Arial", 16), anchor="center")
        cal_unit_label.pack(fill=tk.X)
        
        # Label'ları sakla
        self.raw_data_labels[detector_key] = {
            "value": raw_value_label,
            "unit": raw_unit_label
        }
        
        self.cal_data_labels[detector_key] = {
            "value": cal_value_label,
            "unit": cal_unit_label
        }
    
    def setup_responsive_fonts(self, main_frame):
        """Responsive font boyutları ayarla"""
        def update_fonts():
            try:
                # Ana frame'in boyutunu al
                main_frame.update_idletasks()
                width = main_frame.winfo_width()
                height = main_frame.winfo_height()
                
                # Boyuta göre font boyutunu hesapla (yükseklik öncelikli)
                height_factor = height // 20  # Yükseklik daha etkili
                width_factor = width // 50   # Genişlik daha az etkili
                size_factor = max(height_factor, width_factor)  # Yükseklik önceliği
                
                base_font_size = max(16, min(48, int(size_factor)))  # 16-48 arası (daha geniş)
                unit_font_size = max(12, min(24, int(size_factor * 0.6)))   # 12-24 arası
                title_font_size = max(18, min(36, int(size_factor * 0.8)))  # 18-36 arası
                
                # Başlık fontunu güncelle
                if hasattr(self, 'title_label'):
                    self.title_label.configure(font=("Arial", title_font_size, "bold"))
                
                # Tüm value label'ları güncelle
                for detector_key in self.detectors.keys():
                    if detector_key in self.raw_data_labels:
                        self.raw_data_labels[detector_key]["value"].configure(
                            font=("Arial", base_font_size, "bold")
                        )
                        self.raw_data_labels[detector_key]["unit"].configure(
                            font=("Arial", unit_font_size)
                        )
                    
                    if detector_key in self.cal_data_labels:
                        self.cal_data_labels[detector_key]["value"].configure(
                            font=("Arial", base_font_size, "bold")
                        )
                        self.cal_data_labels[detector_key]["unit"].configure(
                            font=("Arial", unit_font_size)
                        )
                        
            except Exception as e:
                app_logger.error(f"Responsive font güncelleme hatası: {e}")
        
        # İlk güncelleme
        main_frame.after(100, update_fonts)
        
        # Pencere boyutu değiştiğinde güncelle
        def on_configure(event):
            if event.widget == main_frame:
                main_frame.after_idle(update_fonts)
        
        main_frame.bind('<Configure>', on_configure)
    
    def update_data(self):
        """Veri güncelleme"""
        try:
            if self.data_callback:
                # Veri callback'inden güncel verileri al
                data = self.data_callback()
                if data:
                    self.update_display_values(data)
            
            # 100ms sonra tekrar güncelle
            self.parent_frame.after(100, self.update_data)
            
        except Exception as e:
            app_logger.error(f"Detector panel veri güncelleme hatası: {e}")
            # Hata durumunda da güncellemeye devam et
            self.parent_frame.after(100, self.update_data)
    
    def update_display_values(self, data):
        """Görüntülenen değerleri güncelle"""
        try:
            for detector_key, detector_info in self.detectors.items():
                sensor_key = detector_info["sensor_key"]
                
                # Raw data güncelle
                if "raw_data" in data and sensor_key in data["raw_data"]:
                    raw_value = data["raw_data"][sensor_key]
                    self.current_raw_values[detector_key] = raw_value
                    
                    if detector_key in self.raw_data_labels:
                        self.raw_data_labels[detector_key]["value"].configure(
                            text=f"{raw_value:.3f}"
                        )
                
                # Calibrated data güncelle
                if "calibrated_data" in data and sensor_key in data["calibrated_data"]:
                    cal_value = data["calibrated_data"][sensor_key]
                    self.current_cal_values[detector_key] = cal_value
                    
                    if detector_key in self.cal_data_labels:
                        self.cal_data_labels[detector_key]["value"].configure(
                            text=f"{cal_value:.3f}"
                        )
                        
        except Exception as e:
            app_logger.error(f"Detector panel değer güncelleme hatası: {e}")
    
    def apply_dark_theme(self):
        """Dark theme uygula"""
        try:
            style = ttk.Style()
            
            # Detector box style
            style.configure("DetectorBox.TLabelframe", 
                           background='#1a1a1a',
                           foreground='#e8e8e8',
                           borderwidth=2,
                           relief='solid')
            
            style.configure("DetectorBox.TLabelframe.Label",
                           background='#1a1a1a',
                           foreground='#e8e8e8',
                           font=("Arial", 16, "bold"))
            
            # Label'ları güncelle
            for detector_key in self.detectors.keys():
                if detector_key in self.raw_data_labels:
                    self.raw_data_labels[detector_key]["value"].configure(
                        background='#1a1a1a', foreground='#e8e8e8'
                    )
                    self.raw_data_labels[detector_key]["unit"].configure(
                        background='#1a1a1a', foreground='#e8e8e8'
                    )
                
                if detector_key in self.cal_data_labels:
                    self.cal_data_labels[detector_key]["value"].configure(
                        background='#1a1a1a', foreground='#e8e8e8'
                    )
                    self.cal_data_labels[detector_key]["unit"].configure(
                        background='#1a1a1a', foreground='#e8e8e8'
                    )
                    
        except Exception as e:
            app_logger.error(f"Detector panel dark theme hatası: {e}")
    
    def apply_light_theme(self):
        """Light theme uygula"""
        try:
            style = ttk.Style()
            
            # Detector box style - light
            style.configure("DetectorBox.TLabelframe", 
                           background='white',
                           foreground='black',
                           borderwidth=2,
                           relief='solid')
            
            style.configure("DetectorBox.TLabelframe.Label",
                           background='white',
                           foreground='black',
                           font=("Arial", 16, "bold"))
            
            # Label'ları güncelle - light theme
            for detector_key in self.detectors.keys():
                if detector_key in self.raw_data_labels:
                    self.raw_data_labels[detector_key]["value"].configure(
                        background='white', foreground='black'
                    )
                    self.raw_data_labels[detector_key]["unit"].configure(
                        background='white', foreground='black'
                    )
                
                if detector_key in self.cal_data_labels:
                    self.cal_data_labels[detector_key]["value"].configure(
                        background='white', foreground='black'
                    )
                    self.cal_data_labels[detector_key]["unit"].configure(
                        background='white', foreground='black'
                    )
                    
        except Exception as e:
            app_logger.error(f"Detector panel light theme hatası: {e}")
    
    def apply_current_theme(self):
        """Mevcut temayı uygula"""
        try:
            from config.settings import settings_manager
            current_theme = settings_manager.get_theme()
            
            if current_theme == 'dark':
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
                
        except Exception as e:
            app_logger.error(f"Detector panel tema uygulama hatası: {e}")
