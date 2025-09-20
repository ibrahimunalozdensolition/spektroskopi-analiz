import tkinter as tk
from tkinter import ttk, messagebox
import queue
from datetime import datetime
from typing import Dict, List, Optional, Any

from config.settings import settings_manager
from config.constants import (
    APP_TITLE, APP_GEOMETRY, SENSOR_INFO, LED_INFO,
    UPDATE_INTERVAL_MS
)
from communication.ble_manager import BLEManager
from communication.sensor_scanner import SensorScanner
from data.data_processor import DataProcessor
from data.calibration import CalibrationManager
from data.export import DataExporter

from gui.styles import StyleManager
from gui.calibration_window import CalibrationWindow
from gui.formula_panel import FormulaPanel
from gui.realtime_panel import RealTimePanel
from gui.detector_panel import DetectorPanel
from gui.recording_panel import RecordingPanel
from utils.logger import app_logger, log_system_event

class SpektroskpiGUI:    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)
        
        self.style_manager = StyleManager()
        
        self.ble_manager = BLEManager(self.on_data_received)
        self.ble_manager.set_disconnect_callback(self.on_ble_disconnected)
        self.data_processor = DataProcessor()
        self.calibration_manager = CalibrationManager()
        self.data_exporter = DataExporter()
        
        self.sensor_scanner = SensorScanner(self.ble_manager)
        
        self.sensor_combo = None
        self.scan_btn = None
        self.status_label = None
        
        self.start_btn = None
        self.stop_btn = None
        self.calibration_btn = None
        self.export_btn = None
        self.exit_btn = None
        
        self.sampling_label = None
        

        
        self.calibration_window = None
        self.formula_panel = None
        self.realtime_panel = None
        self.detector_panel = None
        self.recording_panel = None
        
        self.notebook = None
        
        self.load_app_settings()
        self.setup_ui()
        self.setup_plots()
        
        # Sistem temasını uygula
        self.apply_system_theme()
        
        
        if self.formula_panel:
            self.formula_panel.update_sensor_info()
        
        self.start_auto_connection()
        
        self.update_data()
        
        
        app_logger.info("Ana GUI başlatıldı")
    
    def setup_ui(self):
        # Menü çubuğu
        self.setup_menu()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.main_frame = main_frame  
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_left_panel(content_frame)
        
        self.setup_right_panel(content_frame)
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Tema", menu=theme_menu)
        
        self.theme_var = tk.StringVar(value=settings_manager.get_theme())
        theme_menu.add_radiobutton(
            label="Açık Tema", 
            variable=self.theme_var, 
            value="light",
            command=self.change_theme
        )
        theme_menu.add_radiobutton(
            label="Koyu Tema", 
            variable=self.theme_var, 
            value="dark",
            command=self.change_theme
        )
    
    def setup_connection_panel(self, parent_frame):
        connection_frame = ttk.LabelFrame(parent_frame, text="BLE Connection", padding=10)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        self.connection_frame = connection_frame  
        
        # Sensor seçimi - ilk satır
        sensor_row = ttk.Frame(connection_frame)
        sensor_row.pack(fill=tk.X, pady=(0, 5))
        
        sensor_text_label = ttk.Label(sensor_row, text="Sensor:", font=("Arial", 11, "bold"))
        sensor_text_label.pack(side=tk.LEFT)
        self.sensor_text_label = sensor_text_label  
        
        self.sensor_combo = ttk.Combobox(sensor_row, width=30, state="readonly")
        self.sensor_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Status gösterimi - ikinci satır
        status_row = ttk.Frame(connection_frame)
        status_row.pack(fill=tk.X, pady=(0, 5))
        
        status_text_label = ttk.Label(status_row, text="Status:", font=("Arial", 11, "bold"))
        status_text_label.pack(side=tk.LEFT)
        self.status_text_label = status_text_label  
        
        self.status_label = ttk.Label(status_row, text="Not Connected", 
                                     font=("Arial", 11, "bold"), foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Scan butonu - üçüncü satır
        button_row = ttk.Frame(connection_frame)
        button_row.pack(fill=tk.X, pady=(5, 0))
        
        self.scan_btn = ttk.Button(button_row, text="🔍 Scan & Connect", 
                                  command=self.scan_and_connect_sensors,
                                  style="Green.TButton")
        self.scan_btn.pack(fill=tk.X)

        self.sensor_scanner.set_ui_components(self.sensor_combo, self.scan_btn, self.status_label)
        self.sensor_scanner.set_callbacks(
            scan_callback=self.on_scan_completed,
            connection_callback=self.on_connection_changed
        )
    
    def setup_left_panel(self, parent_frame):
        
        left_panel = ttk.Frame(parent_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # BLE Connection panel - üst kısımda tam genişlik
        self.setup_connection_panel(left_panel)
        
        # Main Controls panel - ortada
        self.setup_main_control_panel(left_panel)
        
        # Settings panel - alt kısımda
        self.setup_settings_panel(left_panel)
    
    def setup_main_control_panel(self, parent_frame):
        main_control_frame = ttk.LabelFrame(parent_frame, text="Main Controls", padding=10)
        main_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(main_control_frame, text="START", 
                                   command=self.start_system, 
                                   style="Green.TButton")
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = ttk.Button(main_control_frame, text="STOP", 
                                  command=self.stop_system, 
                                  state=tk.DISABLED,
                                  style="Red.TButton")
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        self.calibration_btn = ttk.Button(main_control_frame, text="CALIBRATION", 
                                         command=self.open_calibration_window)
        self.calibration_btn.pack(fill=tk.X, pady=2)
        
        self.export_btn = ttk.Button(main_control_frame, text="EXPORT", 
                                    command=self.export_data, 
                                    state=tk.DISABLED,
                                    style="Blue.TButton")
        self.export_btn.pack(fill=tk.X, pady=2)
        
        self.exit_btn = ttk.Button(main_control_frame, text="EXIT", 
                                  command=self.exit_application,
                                  style="Orange.TButton")
        self.exit_btn.pack(fill=tk.X, pady=2)
    
   
    def setup_settings_panel(self, parent_frame):
        settings_frame = ttk.LabelFrame(parent_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X)
        
    
    def setup_right_panel(self, parent_frame):
        right_panel = ttk.Frame(parent_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
    
    def setup_plots(self):
        # Real-time panel (yeni 3 box tasarımı)
        self.realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_frame, text="Graph Windows")
        self.realtime_panel = RealTimePanel(self.realtime_frame)
        self.realtime_panel.set_data_callback(self.get_data_for_realtime_panel)
        # Detector panel (4 detector real-time)
        self.detector_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.detector_frame, text="Real Time Panel")
        self.detector_panel = DetectorPanel(self.detector_frame)
        self.detector_panel.set_data_callback(self.get_data_for_detector_panel)

        
        self.formula_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.formula_frame, text="Custom Data Generator")
        self.formula_panel = FormulaPanel(self.formula_frame)
        self.formula_panel.set_data_callback(self.get_data_for_formula_panel)
        
        self.recording_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recording_frame, text="Data Recording")
        self.recording_panel = RecordingPanel(self.recording_frame)
        self.recording_panel.set_data_callback(self.get_data_for_recording_panel)
        
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text="About")
        self.setup_about_panel()
        
    
    def setup_about_panel(self):
        # Ana scrollable frame
        canvas = tk.Canvas(self.about_frame)
        scrollbar = ttk.Scrollbar(self.about_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="About the Spectrum Device", 
                               font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 30))
        
        # Introduction
        intro_frame = ttk.LabelFrame(main_frame, text="Introduction", padding=10)
        intro_frame.pack(fill=tk.X, pady=(0, 15))
        
        intro_text = """This spectrum device was developed to provide university students and researchers with an accessible and practical tool for analyzing light spectra. The main goal of the project is to create an educational and research-oriented device with reliable performance."""
        
        intro_label = ttk.Label(intro_frame, text=intro_text, 
                               font=("Arial", 11), justify=tk.LEFT, wraplength=700)
        intro_label.pack(anchor="w")
        
        # Features
        features_frame = ttk.LabelFrame(main_frame, text="Features", padding=10)
        features_frame.pack(fill=tk.X, pady=(0, 15))
        
        features_text = """• Wide wavelength measurement range
• High sensitivity and accuracy
• Bluetooth data transfer
• Portable design
• User-friendly software integration"""
        
        features_label = ttk.Label(features_frame, text=features_text, 
                                  font=("Arial", 11), justify=tk.LEFT)
        features_label.pack(anchor="w")
        
        # Working Principle
        principle_frame = ttk.LabelFrame(main_frame, text="Working Principle", padding=10)
        principle_frame.pack(fill=tk.X, pady=(0, 15))
        
        principle_text = """The device captures light from a source and separates it into wavelengths. The data obtained by the sensor is digitized and transferred to a computer system. Dedicated software processes this data to display and analyze the spectrum."""
        
        principle_label = ttk.Label(principle_frame, text=principle_text, 
                                   font=("Arial", 11), justify=tk.LEFT, wraplength=700)
        principle_label.pack(anchor="w")
        
        # Development Motivation
        motivation_frame = ttk.LabelFrame(main_frame, text="Development Motivation", padding=10)
        motivation_frame.pack(fill=tk.X, pady=(0, 15))
        
        motivation_text = """This device was developed at the request of my esteemed professor, Prof. Dr. Uğur Aksu. It was designed to contribute to academic studies and provide students with practical experience. In addition, the performance and reliability of the device will also be tested in hospitals."""
        
        motivation_label = ttk.Label(motivation_frame, text=motivation_text, 
                                    font=("Arial", 11), justify=tk.LEFT, wraplength=700)
        motivation_label.pack(anchor="w")
        
        # About the Developer
        dev_frame = ttk.LabelFrame(main_frame, text="About the Developer", padding=10)
        dev_frame.pack(fill=tk.X, pady=(0, 15))
        
        dev_text = """My name is İbrahim Ünal. You can contact me at ibrahimunalofficial@gmail.com.

In this project, I undertook the following tasks:
• PCB assembly
• Software development
• Selection of suitable components
• Designing and arranging the external structure of the device"""
        
        dev_label = ttk.Label(dev_frame, text=dev_text, 
                             font=("Arial", 11), justify=tk.LEFT, wraplength=700)
        dev_label.pack(anchor="w")
        
        # Footer
        footer_label = ttk.Label(main_frame, 
                                text="© 2024 İbrahim Ünal - All rights reserved", 
                                font=("Arial", 10, "italic"))
        footer_label.pack(pady=(30, 0))
        
        # Scrollbar'ı pack et
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_data_received(self, data_packet: Dict[str, Any]):
        try:
            self.data_processor.process_incoming_data(data_packet)
            
        except Exception as e:
            app_logger.error(f"Veri alma hatası: {e}")
    
    def update_data(self):
        try:
            data_list = self.ble_manager.get_data_from_queue()
            for data in data_list:
                self.data_processor.process_incoming_data(data)
            
            if data_list:
                app_logger.debug(f"{len(data_list)} veri paketi işlendi")
            
        except Exception as e:
            app_logger.error(f"Veri güncelleme hatası: {e}")
        
        self.update_plots()
        
        self.update_sensor_displays()
        
        self.update_custom_panels()
        
        self.root.after(UPDATE_INTERVAL_MS, self.update_data)
    
    def update_plots(self):
        if not self.data_processor.has_data():
            return
        
        if not self.data_processor.system_running:
            return
        
        pass
    
    def update_sensor_displays(self):   
        try:
            latest_values = self.data_processor.get_latest_values()
            latest_calibrated = self.data_processor.get_latest_calibrated_values()
            calibration_functions = self.calibration_manager.calibration_functions
            
            # Sensor labels kaldırıldı - live measurements artık Real Time Panel'de gösteriliyor
            
            
        except Exception as e:
            app_logger.error(f"Sensör görünüm güncelleme hatası: {e}")
    
    def update_calibration_window_measurements(self, sensor_key: str, raw_value: float):
        try:
            if (self.calibration_window and 
                self.calibration_window.is_window_open()):
                self.calibration_window.update_live_measurement(sensor_key, raw_value)
        except Exception as e:
            app_logger.error(f"Kalibrasyon penceresi ölçüm güncelleme hatası: {e}")
    
    
    def update_custom_panels(self):
        try:
            # Formül paneli - sadece sistem çalışırken güncelle
            if self.formula_panel and self.data_processor.system_running:
                latest_values = self.data_processor.get_latest_values()
                if any(v > 0 for v in latest_values.values()):  
                    self.formula_panel.update_calculated_values_display(latest_values)
            
            if self.realtime_panel and self.data_processor.system_running:
                timestamps, raw_data, spectrum_data, calibrated_data = self.get_data_for_realtime_panel()
                if timestamps and len(timestamps) > 1:  
                    app_logger.debug(f"RealTimePanel'e veri gönderiliyor: {len(timestamps)} timestamp")
                    self.realtime_panel.update_graphs(timestamps, raw_data, spectrum_data, calibrated_data)
            
        except Exception as e:
            app_logger.error(f"Özel panel güncelleme hatası: {e}")
    
    def scan_and_connect_sensors(self):
        self.sensor_scanner.scan_and_connect_sensors()
    
    def on_scan_completed(self, devices: Dict[str, Any]):
        app_logger.info(f"Tarama tamamlandı: {len(devices)} cihaz bulundu")
    
    def on_connection_changed(self, sensor_name: str, device_info: Optional[Dict], connected: bool):
        if connected:
            app_logger.info(f"Bağlantı kuruldu: {sensor_name}")
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(foreground='#4CAF50')  
        else:
            app_logger.info(f"Bağlantı kesildi: {sensor_name}")
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(foreground='#F44336')  
    
    def on_ble_disconnected(self, device_name: str = None):
        """BLE bağlantısı koptuğunda çağrılır"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(
                    text="Pico W ile bağlantı kesildi",
                    foreground='#F44336'
                )
            
            app_logger.info(f"BLE bağlantı kopma callback çağrıldı: {device_name}")
            
        except Exception as e:
            app_logger.error(f"BLE disconnect callback hatası: {e}")
    
    def start_system(self):
        if not self.ble_manager.is_connected:
            messagebox.showwarning("Warning", "Önce sisteme bağlanın!")
            return
        
        self.data_processor.set_system_state(True)
        
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.export_btn.configure(state=tk.DISABLED)
        
        log_system_event(app_logger, "SYSTEM_STARTED", "Real-time processing enabled")
        messagebox.showinfo("System", "Sistem başlatıldı!")
    
    def stop_system(self):
        self.data_processor.set_system_state(False)
        
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.export_btn.configure(state=tk.NORMAL)
        
        log_system_event(app_logger, "SYSTEM_STOPPED")
        messagebox.showinfo("System", "Sistem durduruldu! Export butonu aktifleştirildi.")
    
    def open_calibration_window(self):
        if not self.calibration_window:
            self.calibration_window = CalibrationWindow(self.root, self.calibration_manager)
            self.calibration_window.set_callbacks(
                data_callback=self.get_current_sensor_value,
                led_control_callback=self.control_calibration_led
            )
        
        self.calibration_window.open_window()
    
    def export_data(self):
        """Verileri dışa aktar"""
        if self.data_processor.system_running:
            messagebox.showwarning("Warning", "Export sadece sistem durdurulduktan sonra kullanılabilir!")
            return
        
        if not self.data_processor.has_data():
            messagebox.showwarning("Warning", "Dışa aktarılacak veri yok!")
            return
        
        try:
            # Export verilerini hazırla
            export_data = self.data_processor.export_data_for_csv()
            
            # CSV'ye aktar
            success, result = self.data_exporter.export_to_csv(export_data)
            
            if success:
                # Özet oluştur ve göster
                summary = self.data_exporter.create_export_summary(export_data)
                self.data_exporter.show_export_success_message(result, summary)
                
                log_system_event(app_logger, "DATA_EXPORTED", f"File: {result}")
            else:
                messagebox.showerror("Error", f"Veri dışa aktarılamadı: {result}")
                
        except Exception as e:
            app_logger.error(f"Veri dışa aktarma hatası: {e}")
            messagebox.showerror("Error", f"Veri dışa aktarılamadı: {e}")
    
    def clear_data(self):
        """Verileri temizle"""
        self.data_processor.clear_all_data()
        
        # Sensör değerleri artık Real Time Panel'de sıfırlanıyor
        
        log_system_event(app_logger, "DATA_CLEARED")
        messagebox.showinfo("Clear", "Tüm veriler temizlendi!")
    
    def change_theme(self):
        """Tema değiştir"""
        try:
            selected_theme = self.theme_var.get()
            
            # Temayı kaydet
            settings_manager.set_theme(selected_theme)
            settings_manager.save_settings()
            
            # Temayı uygula
            self.apply_system_theme()
            
            app_logger.info(f"{selected_theme.title()} tema uygulandı")
            
        except Exception as e:
            app_logger.error(f"Tema değiştirme hatası: {e}")
            messagebox.showerror("Hata", f"Tema değiştirilemedi: {e}")
    
    def apply_system_theme(self):
        """Sistem temasını uygula"""
        try:
            # Önce sistem temasını kontrol et
            system_theme = settings_manager.detect_system_theme()
            saved_theme = settings_manager.get('appearance.theme', None)
            
            # Eğer kaydedilmiş tema yoksa, sistem temasını kullan
            if not saved_theme:
                current_theme = system_theme
                settings_manager.set_theme(current_theme)
                settings_manager.save_settings()
                app_logger.info(f"Sistem teması algılandı ve kaydedildi: {current_theme}")
            else:
                current_theme = saved_theme
            
            self.theme_var.set(current_theme)
            
            # StyleManager ile temayı uygula
            self.style_manager.apply_theme(current_theme)
            
            # Ana pencere arka plan rengini ayarla
            if current_theme == 'dark':
                self.root.configure(bg='#1a1a1a')
            else:
                # Light theme için beyaz arka plan
                self.root.configure(bg='white')
            
            # Panel'lara tema uygula
            self.apply_theme_to_panels(current_theme)
            
            app_logger.info(f"Tema uygulandı: {current_theme} (sistem: {system_theme})")
                
        except Exception as e:
            app_logger.error(f"Sistem tema uygulama hatası: {e}")
    
    def apply_theme_to_panels(self, theme):
        """Panel'lara tema uygula"""
        try:
            # Formula panel
            if hasattr(self, 'formula_panel') and self.formula_panel:
                self.formula_panel.apply_current_theme()
            
            # Recording panel
            if hasattr(self, 'recording_panel') and self.recording_panel:
                self.recording_panel.apply_current_theme()
            
            # Custom panel
            if hasattr(self, 'custom_panel') and self.custom_panel:
                self.custom_panel.apply_current_theme()
            
            # Realtime panel
            if hasattr(self, 'realtime_panel') and self.realtime_panel:
                self.realtime_panel.apply_current_theme()
            
            # Calibration window (eğer açıksa)
            if hasattr(self, 'calibration_window') and self.calibration_window:
                self.calibration_window.apply_current_theme()
            
            # Detector panel
            if hasattr(self, 'detector_panel') and self.detector_panel:
                self.detector_panel.apply_current_theme()
                
        except Exception as e:
            app_logger.error(f"Panel tema uygulama hatası: {e}")
    
    def apply_dark_theme_to_left_panel(self):

        try:
            widgets_updated = 0
            
            if hasattr(self, 'main_frame') and self.main_frame:
                try:
                    self.main_frame.configure(background='#1a1a1a')
                    widgets_updated += 1
                    app_logger.debug("Main frame dark theme uygulandı")
                except Exception as e:
                    app_logger.debug(f"Main frame renk ayarlama hatası: {e}")
          
            if hasattr(self, 'connection_frame') and self.connection_frame:
                try:
                    
                    self.connection_frame.configure(background='#1a1a1a')
                    widgets_updated += 1
                    app_logger.debug("Connection frame dark theme uygulandı")
                except Exception as e:
                    app_logger.debug(f"Connection frame direkt renk ayarlama hatası (normal): {e}")
            
            
            if hasattr(self, 'connection_row') and self.connection_row:
                try:
                    self.connection_row.configure(background='#1a1a1a')
                    widgets_updated += 1
                    app_logger.debug("Connection row dark theme uygulandı")
                except Exception as e:
                    app_logger.debug(f"Connection row direkt renk ayarlama hatası (normal): {e}")
            
            
            if hasattr(self, 'sensor_text_label') and self.sensor_text_label:
                try:
                    self.sensor_text_label.configure(
                        background='#1a1a1a',
                        foreground='#e8e8e8'
                    )
                    widgets_updated += 1
                    app_logger.debug("Sensor text label dark theme uygulandı")
                except Exception as e:
                    app_logger.warning(f"Sensor text label tema hatası: {e}")
            
            
            if hasattr(self, 'status_text_label') and self.status_text_label:
                try:
                    self.status_text_label.configure(
                        background='#1a1a1a',
                        foreground='#e8e8e8'
                    )
                    widgets_updated += 1
                    app_logger.debug("Status text label dark theme uygulandı")
                except Exception as e:
                    app_logger.warning(f"Status text label tema hatası: {e}")
            
            
            if hasattr(self, 'status_label') and self.status_label:
                try:
                    self.status_label.configure(background='#1a1a1a')

                    current_text = self.status_label.cget('text')
                    if 'Connected' in current_text and 'Not' not in current_text:
                        self.status_label.configure(foreground='#4CAF50')  
                    else:
                        self.status_label.configure(foreground='#F44336')  
                    widgets_updated += 1
                    app_logger.debug("Status label dark theme uygulandı")
                except Exception as e:
                    app_logger.warning(f"Status label tema hatası: {e}")
            
           
            if hasattr(self, 'sensor_combo') and self.sensor_combo:
                widgets_updated += 1
                app_logger.debug("Sensor combo dark theme (global stil ile) uygulandı")
            
            
            
           
            if hasattr(self, 'sampling_label') and self.sampling_label:
                try:
                    self.sampling_label.configure(style='Dark.TLabel')
                    widgets_updated += 1
                    app_logger.debug("Sampling label dark theme uygulandı")
                except Exception as e:
                    app_logger.warning(f"Sampling label tema hatası: {e}")
            
            # Sensor labels kaldırıldı - tema artık Real Time Panel'de uygulanıyor
            
            # Main Controls butonları
            if hasattr(self, 'start_btn') and self.start_btn:
                try:
                    self.start_btn.configure(style='Green.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Start button tema hatası: {e}")
            
            if hasattr(self, 'stop_btn') and self.stop_btn:
                try:
                    self.stop_btn.configure(style='Red.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Stop button tema hatası: {e}")
            
            if hasattr(self, 'export_btn') and self.export_btn:
                try:
                    self.export_btn.configure(style='Blue.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Export button tema hatası: {e}")
            
            if hasattr(self, 'calibration_btn') and self.calibration_btn:
                try:
                    # Dark theme için varsayılan stil
                    self.calibration_btn.configure(style='TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Calibration button tema hatası: {e}")
            
            app_logger.info(f"Sol panel dark theme uygulandı - {widgets_updated} widget güncellendi")
            
        except Exception as e:
            app_logger.error(f"Sol panel dark theme uygulama hatası: {e}")
    
    def apply_light_theme_to_left_panel(self):
        """Sol panel widget'larına light theme uygula"""
        try:
            widgets_updated = 0
            
            if hasattr(self, 'main_frame') and self.main_frame:
                self.main_frame.configure(bg='white')
                widgets_updated += 1
            
            # Connection frame
            if hasattr(self, 'connection_frame') and self.connection_frame:
                try:
                    self.connection_frame.configure(style='TLabelFrame')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Connection frame tema hatası: {e}")
            
            # Sensor combo
            if hasattr(self, 'sensor_combo') and self.sensor_combo:
                try:
                    self.sensor_combo.configure(style='TCombobox')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Sensor combo tema hatası: {e}")
            
            # Status label
            if hasattr(self, 'status_label') and self.status_label:
                try:
                    self.status_label.configure(style='TLabel')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Status label tema hatası: {e}")
            
            # Main Controls butonları
            if hasattr(self, 'start_btn') and self.start_btn:
                try:
                    self.start_btn.configure(style='Green.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Start button tema hatası: {e}")
            
            if hasattr(self, 'stop_btn') and self.stop_btn:
                try:
                    self.stop_btn.configure(style='Red.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Stop button tema hatası: {e}")
            
            if hasattr(self, 'export_btn') and self.export_btn:
                try:
                    self.export_btn.configure(style='Blue.TButton')
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Export button tema hatası: {e}")
            
            if hasattr(self, 'calibration_btn') and self.calibration_btn:
                try:
                    self.calibration_btn.configure(style='TButton')  # Default style for light theme
                    widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Calibration button tema hatası: {e}")
            
            app_logger.info(f"Sol panel light theme uygulandı - {widgets_updated} widget güncellendi")
            
        except Exception as e:
            app_logger.error(f"Sol panel light theme uygulama hatası: {e}")
    
    def apply_dark_theme_to_about_panel(self):
       
        try:
            # About frame'deki tüm widget'ları bul ve tema uygula
            def apply_to_widget(widget):
                try:
                    widget_class = widget.winfo_class()
                    if widget_class in ['TLabel', 'Label']:
                        if hasattr(widget, 'configure'):
                            widget.configure(style='Dark.TLabel')
                    elif widget_class in ['TLabelframe', 'Labelframe']:
                        if hasattr(widget, 'configure'):
                            widget.configure(style='Dark.TLabelframe')
                    elif widget_class in ['TFrame', 'Frame']:
                        if hasattr(widget, 'configure'):
                            widget.configure(style='Dark.TFrame')
                except Exception as e:
                    app_logger.debug(f"About panel widget tema hatası: {e}")
            
           
            if hasattr(self, 'about_frame') and self.about_frame:
                def traverse_widgets(parent):
                    apply_to_widget(parent)
                    for child in parent.winfo_children():
                        traverse_widgets(child)
                
                traverse_widgets(self.about_frame)
            
            app_logger.debug("About panel dark theme uygulandı")
            
        except Exception as e:
            app_logger.error(f"About panel dark theme hatası: {e}")
    
    def apply_initial_theme_to_widgets(self):
       
        try:
            current_theme = settings_manager.get_theme()
            if current_theme == 'dark':
                self.apply_dark_theme_to_left_panel()
        except Exception as e:
            app_logger.error(f"Başlangıç tema uygulama hatası: {e}")
    
    def exit_application(self):
        result = messagebox.askyesno("Exit", "Programdan çıkmak istediğinizden emin misiniz?")
        if result:
           
            if self.ble_manager.is_connected:
                self.ble_manager.disconnect()
            

            
           
            if self.realtime_panel:
                self.realtime_panel.close_all_windows()
            
            if self.detector_panel:
                # Detector panel için özel cleanup varsa eklenebilir
                pass
            
           
            settings_manager.save_settings()
            
            log_system_event(app_logger, "APPLICATION_EXIT")
            
           
            self.root.quit()
            self.root.destroy()
    
   
    

    
    
    
    def load_app_settings(self):
        try:
            calibration_functions = {}
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                func = settings_manager.get_calibration_function(sensor_key)
                if func:
                    calibration_functions[sensor_key] = func
            
            self.data_processor.set_calibration_functions(calibration_functions)
            self.calibration_manager.calibration_functions = calibration_functions
            
            if self.formula_panel:
                self.formula_panel.load_formulas_from_settings()
            
            app_logger.info("Uygulama ayarları yüklendi")
            
        except Exception as e:
            app_logger.error(f"Ayar yükleme hatası: {e}")
    
    def start_auto_connection(self):
        if self.ble_manager.is_available():
            self.sensor_scanner.start_auto_connection()
        else:
            app_logger.warning("BLE mevcut değil, otomatik bağlantı devre dışı")
    
    def get_current_sensor_value(self) -> float:
        try:
            latest_values = self.data_processor.get_latest_values()
            
            if (self.calibration_window and 
                hasattr(self.calibration_window, 'selected_sensor') and
                self.calibration_window.selected_sensor):
                
                selected = self.calibration_window.selected_sensor.get()
                sensor_mapping = {
                    "UV Sensor (360nm)": "UV_360nm",
                    "Blue Sensor (450nm)": "Blue_450nm",
                    "IR Sensor (850nm)": "IR_850nm",
                    "IR Sensor (940nm)": "IR_940nm"
                }
                
                if selected in sensor_mapping:
                    sensor_key = sensor_mapping[selected]
                    # Sadece gerçek Raspberry Pi verilerini döndür
                    value = latest_values.get(sensor_key, 0.0)
                    
                    if value > 0.0:
                        app_logger.debug(f"Gerçek veri: {sensor_key} = {value:.3f}V")
                    else:
                        app_logger.debug(f"Henüz veri yok: {sensor_key}")
                    
                    return value
            
            return 0.0
            
        except Exception as e:
            app_logger.error(f"Mevcut sensör değeri alma hatası: {e}")
            return 0.0
    
    def control_calibration_led(self, sensor_name: Optional[str], turn_on: bool):
        """Kalibrasyon LED kontrolü (UI'da artık LED göstergesi yok)"""
        # LED kontrolü artık sadece backend'de yapılacak
        pass
    
    def get_data_for_formula_panel(self) -> Dict[str, float]:
        """Formül paneli için en son sensör değerlerini al"""
        try:
            return self.data_processor.get_latest_values()
        except Exception as e:
            app_logger.error(f"Formül panel veri alma hatası: {e}")
            return {}
    

    
    def on_custom_settings_changed(self, setting_key: str, value: Any):
        """Özel ayar değiştiğinde çağrılır"""
        try:
            settings_manager.set(f'custom_data.{setting_key}', value)
            settings_manager.save_settings()
            app_logger.info(f"Özel ayar güncellendi: {setting_key} = {value}")
            
        except Exception as e:
            app_logger.error(f"Özel ayar güncelleme hatası: {e}")
    
    def get_data_for_realtime_panel(self) -> tuple:
        """Real time panel için veri al"""
        try:
            measurements = self.data_processor.get_measurements()
            calibrated_data = self.data_processor.get_calibrated_data()
            spectrum_intensities = self.data_processor.get_spectrum_intensities()
            
            # Eğer measurements boşsa, last_sensor_values'tan veri oluştur
            timestamps = measurements['timestamps']
            if not timestamps and any(self.data_processor.last_sensor_values.values()):
                # Son sensör değerleriyle tek noktalık veri oluştur
                current_time = datetime.now()
                timestamps = [current_time]
                
                # Son değerlerle measurements oluştur
                temp_measurements = {
                    'timestamps': timestamps,
                    'UV_360nm': [self.data_processor.last_sensor_values['UV_360nm']],
                    'Blue_450nm': [self.data_processor.last_sensor_values['Blue_450nm']],
                    'IR_850nm': [self.data_processor.last_sensor_values['IR_850nm']],
                    'IR_940nm': [self.data_processor.last_sensor_values['IR_940nm']]
                }
                
                app_logger.debug(f"RealTimePanel için son değerlerden veri oluşturuldu")
                return (timestamps, temp_measurements, spectrum_intensities, calibrated_data)
            
            # Debug: Veri durumunu kontrol et
            if timestamps:
                app_logger.debug(f"RealTimePanel için veri hazırlandı: {len(timestamps)} zaman noktası")
            else:
                app_logger.debug("RealTimePanel için veri yok")
            
            return (
                timestamps, 
                measurements, 
                spectrum_intensities,
                calibrated_data
            )
        except Exception as e:
            app_logger.error(f"Real time panel veri alma hatası: {e}")
            return [], {}, [], {}
    
    def get_data_for_recording_panel(self) -> Dict[str, Dict[str, float]]:
        """Recording panel için veri al"""
        try:
            # Raw data
            raw_values = self.data_processor.get_latest_values()
            
            # Calibrated data
            calibrated_values = self.data_processor.get_latest_calibrated_values()
            
            return {
                'raw': raw_values,
                'calibrated': calibrated_values
            }
            
        except Exception as e:
            app_logger.error(f"Recording panel veri alma hatası: {e}")
            return {
                'raw': {},
                'calibrated': {}
            }
    
    def get_data_for_detector_panel(self) -> Dict[str, Dict[str, float]]:
        """Detector panel için veri al"""
        try:
            # Raw data
            raw_values = self.data_processor.get_latest_values()
            
            # Calibrated data
            calibrated_values = self.data_processor.get_latest_calibrated_values()
            
            return {
                'raw_data': raw_values,
                'calibrated_data': calibrated_values
            }
            
        except Exception as e:
            app_logger.error(f"Detector panel veri alma hatası: {e}")
            return {
                'raw_data': {},
                'calibrated_data': {}
            }
