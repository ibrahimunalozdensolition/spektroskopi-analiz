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
from gui.recording_panel import RecordingPanel
from utils.logger import app_logger, log_system_event

class SpektroskpiGUI:    
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)
        
        self.style_manager = StyleManager()
        
        self.ble_manager = BLEManager(self.on_data_received)
        self.data_processor = DataProcessor()
        self.calibration_manager = CalibrationManager()
        self.data_exporter = DataExporter()
        
        self.sensor_scanner = SensorScanner(self.ble_manager)
        
        self.sensor_combo = None
        self.scan_btn = None
        self.status_label = None
        self.sensor_labels = {}
        
        self.start_btn = None
        self.stop_btn = None
        self.calibration_btn = None
        self.export_btn = None
        self.exit_btn = None
        
        self.sampling_label = None
        

        
        self.calibration_window = None
        self.formula_panel = None
        self.realtime_panel = None
        self.recording_panel = None
        
        self.notebook = None
        
        self.load_app_settings()
        self.apply_saved_theme()  
        
        self.setup_ui()
        self.setup_plots()
        
        self.root.after(500, self.apply_initial_theme_to_widgets)
        
        
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
        
        self.setup_connection_panel(main_frame)
        
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
            label="Koyu Tema (Aktif)", 
            variable=self.theme_var, 
            value="dark",
            command=self.change_theme,
            state=tk.DISABLED  
        )
    
    def setup_connection_panel(self, parent_frame):
        connection_frame = ttk.LabelFrame(parent_frame, text="BLE Connection", padding=10)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        self.connection_frame = connection_frame  
        
        connection_row = ttk.Frame(connection_frame)
        connection_row.pack(fill=tk.X)
        self.connection_row = connection_row  
        
        sensor_text_label = ttk.Label(connection_row, text="Sensor:", font=("Arial", 11, "bold"))
        sensor_text_label.pack(side=tk.LEFT)
        self.sensor_text_label = sensor_text_label  
        
        self.sensor_combo = ttk.Combobox(connection_row, width=20, state="readonly")
        self.sensor_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        status_text_label = ttk.Label(connection_row, text="Status:", font=("Arial", 11, "bold"))
        status_text_label.pack(side=tk.LEFT)
        self.status_text_label = status_text_label  
        
        self.status_label = ttk.Label(connection_row, text="Not Connected", 
                                     font=("Arial", 11, "bold"), foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(5, 15))
        
        self.scan_btn = ttk.Button(connection_row, text="🔍 Scan & Connect", 
                                  command=self.scan_and_connect_sensors,
                                  style="Green.TButton")
        self.scan_btn.pack(side=tk.RIGHT, padx=5)

        self.sensor_scanner.set_ui_components(self.sensor_combo, self.scan_btn, self.status_label)
        self.sensor_scanner.set_callbacks(
            scan_callback=self.on_scan_completed,
            connection_callback=self.on_connection_changed
        )
    
    def setup_left_panel(self, parent_frame):
        
        left_panel = ttk.Frame(parent_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        
        self.setup_live_data_panel(left_panel)
        
        
        self.setup_main_control_panel(left_panel)
        
        
        
        self.setup_settings_panel(left_panel)
    
    def setup_live_data_panel(self, parent_frame):
        
        live_data_frame = ttk.LabelFrame(parent_frame, text="Live Measurements", padding=10)
        live_data_frame.pack(fill=tk.X, pady=(0, 10))
        
        
        self.setup_sensor_values_panel(live_data_frame)
    
    
    def setup_sensor_values_panel(self, parent_frame):
        
        sensor_frame = ttk.LabelFrame(parent_frame, text="Photodiode Values", padding=5)
        sensor_frame.pack(fill=tk.X)
        
        for sensor_name, sensor_key, color in SENSOR_INFO:
            main_frame = ttk.Frame(sensor_frame)
            main_frame.pack(fill=tk.X, pady=4, padx=5)
            
            
            ttk.Label(main_frame, text=f"{sensor_name}:", width=15,
                    font=("Arial", 16, "bold"), anchor='w').pack(side=tk.LEFT)
            
            
            value_frame = ttk.Frame(main_frame)
            value_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            
            raw_frame = ttk.Frame(value_frame)
            raw_frame.pack(side=tk.TOP, fill=tk.X)
            ttk.Label(raw_frame, text="Raw:", font=("Arial", 16)).pack(side=tk.LEFT)
            raw_label = ttk.Label(raw_frame, text="0000 mV", width=12,
                                 font=("Arial", 16, "bold"))
            raw_label.pack(side=tk.RIGHT)
            
            
            cal_frame = ttk.Frame(value_frame)
            cal_frame.pack(side=tk.TOP, fill=tk.X)
            ttk.Label(cal_frame, text="Cal:", font=("Arial", 16)).pack(side=tk.LEFT)
            cal_label = ttk.Label(cal_frame, text="0.000 ppm", width=12,
                                 font=("Arial", 16, "bold"))
            cal_label.pack(side=tk.RIGHT)
            
            self.sensor_labels[sensor_name] = {
                'raw': raw_label,
                'calibrated': cal_label,
                'key': sensor_key
            }
    
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
        main_frame = ttk.Frame(self.about_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(main_frame, text="Spectroscopy Data Analyzer", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        version_label = ttk.Label(main_frame, text="Version 2.0", 
                                 font=("Arial", 12))
        version_label.pack(pady=(0, 30))
        
        dev_frame = ttk.LabelFrame(main_frame, text="Developer Information", padding=20)
        dev_frame.pack(fill=tk.X, pady=(0, 20))
        
        dev_info_text = """Developed by: Ibrahim Ünal

This application has been developed for Prof. Dr. Ugur Aksu.

All rights reserved."""

        dev_label = ttk.Label(dev_frame, text=dev_info_text, 
                             font=("Arial", 12), justify=tk.CENTER)
        dev_label.pack(pady=20)
        
        footer_label = ttk.Label(main_frame, 
                                text="© 2024 Ibrahim Ünal - All rights reserved", 
                                font=("Arial", 10, "italic"))
        footer_label.pack(side=tk.BOTTOM, pady=(30, 0))

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
            
            for sensor_name, labels in self.sensor_labels.items():
                sensor_key = labels['key']
                
                if sensor_key in latest_values:
                    raw_value = latest_values[sensor_key]
                    calibrated_value = latest_calibrated.get(sensor_key, raw_value)
                    
                    labels['raw'].configure(text=f"{int(raw_value):04d} mV")
                    
                    unit = "mV"
                    if (sensor_key in calibration_functions and 
                        calibration_functions[sensor_key]):
                        unit = calibration_functions[sensor_key].get('unit', 'V')
                    
                    labels['calibrated'].configure(text=f"{calibrated_value:.0f} {unit}")
                    
                    self.update_calibration_window_measurements(sensor_key, raw_value)
            
            
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
        
        # Sensör değerlerini sıfırla
        for sensor_name, labels in self.sensor_labels.items():
            labels['raw'].configure(text="0000 mV")
            labels['calibrated'].configure(text="0.000 ppm")
        
        log_system_event(app_logger, "DATA_CLEARED")
        messagebox.showinfo("Clear", "Tüm veriler temizlendi!")
    
    def change_theme(self):
        """Tema değiştir - Sadece Dark Theme"""
        try:
            # Sadece dark theme - her zaman dark uygula
            self.theme_var.set('dark')
            
            # Temayı kaydet
            settings_manager.set_theme('dark')
            settings_manager.save_settings()
            
            # Dark temayı uygula
            self.style_manager.apply_dark_theme()
            # Ana pencere arkaplan rengini ayarla
            self.root.configure(bg='#1a1a1a')
            # Mevcut widget'ları güncelle (tek seferlik)
            self.update_existing_widgets_theme('dark')
            
            app_logger.info("Dark tema uygulandı")
            
        except Exception as e:
            app_logger.error(f"Tema değiştirme hatası: {e}")
            messagebox.showerror("Hata", f"Tema değiştirilemedi: {e}")
    
    def apply_saved_theme(self):
        """Dark theme uygula - Tek tema modu"""
        try:
            # Sadece dark theme - light theme kaldırıldı
            self.theme_var.set('dark')
            
            # Dark theme uygula
            self.style_manager.apply_dark_theme()
            # Ana pencere arkaplan rengini ayarla
            self.root.configure(bg='#1a1a1a')
            # Mevcut widget'ları güncelle
            self.update_existing_widgets_theme('dark')
                
        except Exception as e:
            app_logger.error(f"Dark tema uygulama hatası: {e}")
    
    def update_existing_widgets_theme(self, theme):
        """Mevcut widget'ların temasını güncelle - Sadece Dark Theme"""
        try:
            # Sadece dark theme - her zaman dark uygula
            # Sol panel widget'larını güncelle
            self.apply_dark_theme_to_left_panel()
            
            # Formula panel'deki widget'ları güncelle
            if hasattr(self, 'formula_panel') and self.formula_panel:
                # Listbox güncelle
                if hasattr(self.formula_panel, 'formula_listbox'):
                    self.style_manager.apply_dark_theme_to_widget(
                        self.formula_panel.formula_listbox, 'listbox'
                    )
                
                # Entry widget'larını güncelle
                self.formula_panel.apply_dark_theme_to_entries()
            
            # Recording panel'deki widget'ları güncelle
            if hasattr(self, 'recording_panel') and self.recording_panel:
                self.recording_panel.apply_dark_theme()
                
            # Real time panel'deki widget'ları güncelle
            if hasattr(self, 'realtime_panel') and self.realtime_panel:
                # Real time panel için gerekli güncellemeler
                pass
            
            # About paneli için tema uygula
            if hasattr(self, 'about_frame') and self.about_frame:
                self.apply_dark_theme_to_about_panel()
                
        except Exception as e:
            app_logger.error(f"Widget tema güncelleme hatası: {e}")
    
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
            
           
            for sensor_name, labels in self.sensor_labels.items():
                try:
                    if 'raw' in labels and labels['raw']:
                        labels['raw'].configure(style='Dark.TLabel')
                        widgets_updated += 1
                    if 'calibrated' in labels and labels['calibrated']:
                        labels['calibrated'].configure(style='Dark.TLabel')
                        widgets_updated += 1
                except Exception as e:
                    app_logger.warning(f"Sensör label ({sensor_name}) tema hatası: {e}")
            
            app_logger.info(f"Sol panel dark theme uygulandı - {widgets_updated} widget güncellendi")
            
        except Exception as e:
            app_logger.error(f"Sol panel dark theme uygulama hatası: {e}")
    
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
