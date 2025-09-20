import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Callable, Any
import threading
import time

from data.calibration import CalibrationManager
from utils.logger import app_logger
from config.constants import MIN_CALIBRATION_POINTS, MAX_CALIBRATION_POINTS

class CalibrationWindow:
    """Kalibrasyon penceresi sınıfı"""
    
    def __init__(self, parent, calibration_manager: CalibrationManager):
        self.parent = parent
        self.calibration_manager = calibration_manager
        self.window = None
        
        # UI bileşenleri
        self.selected_sensor = None
        self.molecule_name = None
        self.molecule_unit = None
        self.calibration_entries = []
        self.calibration_values = []
        self.calibration_status = []
        self.calibrate_btn = None
        self.cal_status = None
        
        # Veri callback'i (dışarıdan set edilecek)
        self.data_callback = None
        self.led_control_callback = None
    
    def set_callbacks(self, data_callback: Optional[Callable] = None,
                     led_control_callback: Optional[Callable] = None):
        """Callback fonksiyonlarını ayarla"""
        self.data_callback = data_callback
        self.led_control_callback = led_control_callback
    
    def open_window(self):
        """Kalibrasyon penceresini aç"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Calibration Panel")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        self.setup_calibration_panel()
        
        app_logger.info("Kalibrasyon penceresi açıldı")
    
    def setup_calibration_panel(self):
        """Gelişmiş kalibrasyon paneli kurulumu"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Spectroscopy Calibration Panel", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Üst panel - Sensör seçimi
        self.setup_sensor_selection_panel(main_frame)
        
        # Kalibrasyon tablosu
        self.setup_calibration_table(main_frame)
        
        # Alt panel - Kontroller
        self.setup_control_panel(main_frame)
    
    def setup_sensor_selection_panel(self, parent_frame):
        """Sensör seçim paneli"""
        sensor_frame = ttk.LabelFrame(parent_frame, text="Sensor Selection", padding=10)
        sensor_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sensör seçimi
        sensor_select_frame = ttk.Frame(sensor_frame)
        sensor_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sensor_select_frame, text="Sensor to Calibrate:").pack(side=tk.LEFT)
        self.selected_sensor = ttk.Combobox(sensor_select_frame, width=20, state="readonly")
        self.selected_sensor['values'] = ["UV Sensor (360nm)", "Blue Sensor (450nm)", 
                                         "IR Sensor (850nm)", "IR Sensor (940nm)"]
        self.selected_sensor.pack(side=tk.LEFT, padx=(10, 0))
        self.selected_sensor.bind('<<ComboboxSelected>>', self.on_sensor_selected)
        
        # Molekül bilgileri
        molecule_frame = ttk.Frame(sensor_frame)
        molecule_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(molecule_frame, text="Molecule Name:").pack(side=tk.LEFT)
        self.molecule_name = ttk.Entry(molecule_frame, width=15)
        self.molecule_name.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(molecule_frame, text="Unit:").pack(side=tk.LEFT)
        self.molecule_unit = ttk.Entry(molecule_frame, width=10)
        self.molecule_unit.pack(side=tk.LEFT, padx=(10, 0))
        self.molecule_unit.insert(0, "ppm")
    
    def setup_calibration_table(self, parent_frame):
        """Kalibrasyon tablosu kurulumu"""
        table_frame = ttk.LabelFrame(parent_frame, text="Calibration Values", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tablo başlıkları
        headers_frame = ttk.Frame(table_frame)
        headers_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(headers_frame, text="No.", width=5, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_frame, text="Concentration", width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_frame, text="Measured Value (V)", width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_frame, text="Status", width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_frame, text="Action", width=10, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Kalibrasyon satırları
        self.calibration_entries = []
        self.calibration_values = []
        self.calibration_status = []
        
        for i in range(MAX_CALIBRATION_POINTS):
            row_frame = ttk.Frame(table_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            # Satır numarası
            ttk.Label(row_frame, text=str(i+1), width=5).pack(side=tk.LEFT, padx=5)
            
            # Konsantrasyon girişi
            conc_entry = ttk.Entry(row_frame, width=15)
            conc_entry.pack(side=tk.LEFT, padx=5)
            
            # Ölçülen değer
            value_label = ttk.Label(row_frame, text="0.000", width=15, relief=tk.SUNKEN)
            value_label.pack(side=tk.LEFT, padx=5)
            
            # Durum
            status_label = ttk.Label(row_frame, text="Waiting", width=15, foreground="orange")
            status_label.pack(side=tk.LEFT, padx=5)
            
            # OK butonu
            ok_btn = ttk.Button(row_frame, text="OK", width=8, 
                               command=lambda idx=i: self.record_calibration_point(idx))
            ok_btn.pack(side=tk.LEFT, padx=5)
            
            self.calibration_entries.append(conc_entry)
            self.calibration_values.append(value_label)
            self.calibration_status.append(status_label)
    
    def setup_control_panel(self, parent_frame):
        """Kontrol paneli kurulumu"""
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Sol taraf - Kalibrasyon butonları
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side=tk.LEFT)
        
        self.calibrate_btn = ttk.Button(left_controls, text="CALIBRATE", 
                                       command=self.perform_calibration,
                                       state=tk.DISABLED,
                                       style="Purple.TButton")
        self.calibrate_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(left_controls, text="Clear", 
                  command=self.clear_calibration_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(left_controls, text="Take Reference", 
                  command=self.take_reference).pack(side=tk.LEFT, padx=5)
        
        # Sağ taraf - Dosya işlemleri
        right_controls = ttk.Frame(control_frame)
        right_controls.pack(side=tk.RIGHT)
        
        ttk.Button(right_controls, text="Save", 
                  command=self.save_calibration).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(right_controls, text="Load", 
                  command=self.load_calibration).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(right_controls, text="Close", 
                  command=self.close_window).pack(side=tk.LEFT, padx=5)
        
        # Durum çubuğu
        status_frame = ttk.Frame(parent_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.cal_status = ttk.Label(status_frame, text="Kalibrasyon için sensör seçin...", 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.cal_status.pack(fill=tk.X)
    
    def on_sensor_selected(self, event):
        """Sensör seçildiğinde çağrılır"""
        selected = self.selected_sensor.get()
        
        if not selected:
            return
        
        # LED kontrolü
        if self.led_control_callback:
            self.led_control_callback(selected, True)
        
        # Kalibrasyon başlat
        sensor_mapping = {
            "UV Sensor (360nm)": "UV_360nm",
            "Blue Sensor (450nm)": "Blue_450nm",
            "IR Sensor (850nm)": "IR_850nm",
            "IR Sensor (940nm)": "IR_940nm"
        }
        
        if selected in sensor_mapping:
            sensor_key = sensor_mapping[selected]
            molecule_name = self.molecule_name.get()
            unit = self.molecule_unit.get()
            
            success = self.calibration_manager.start_calibration(sensor_key, molecule_name, unit)
            if success:
                self.cal_status.configure(text=f"Kalibrasyon başlatıldı: {selected}")
                app_logger.info(f"Kalibrasyon başlatıldı: {selected}")
            else:
                self.cal_status.configure(text="Kalibrasyon başlatma hatası")
    
    def record_calibration_point(self, index: int):
        """Kalibrasyon noktasını kaydet"""
        if not self.selected_sensor.get():
            messagebox.showwarning("Warning", "Önce bir sensör seçin!")
            return
        
        # Konsantrasyon değerini kontrol et
        try:
            concentration = float(self.calibration_entries[index].get())
        except ValueError:
            messagebox.showerror("Error", "Geçerli bir konsantrasyon değeri girin!")
            return
        
        # Mevcut sensör değerini al (Raspberry Pi'dan gerçek veri)
        current_value = self.get_current_sensor_value()
        
        # Kalibrasyon noktasını ekle
        success = self.calibration_manager.add_calibration_point(concentration, current_value)
        
        if success:
            # UI güncelle
            self.calibration_values[index].configure(text=f"{current_value:.3f}")
            self.calibration_status[index].configure(text="Saved", foreground="green")
            
            # Kalibrasyon butonunu kontrol et
            completed_points = sum(1 for status in self.calibration_status 
                                 if status.cget("text") == "Saved")
            
            if completed_points >= MIN_CALIBRATION_POINTS:
                self.calibrate_btn.configure(state=tk.NORMAL)
            
            messagebox.showinfo("Record", 
                              f"Nokta {index+1} kaydedildi!\n"
                              f"Konsantrasyon: {concentration}\n"
                              f"Değer: {current_value:.3f}V")
            
            app_logger.info(f"Kalibrasyon noktası kaydedildi: {index+1}")
        else:
            messagebox.showerror("Error", "Kalibrasyon noktası kaydedilemedi!")
    
    def get_current_sensor_value(self) -> float:
        """Mevcut sensör değerini al"""
        # Bu fonksiyon gerçek sistemde data_callback'den gelecek
        if self.data_callback:
            try:
                return self.data_callback()
            except Exception as e:
                app_logger.error(f"Data callback hatası: {e}")
        
        # Gerçek veri yoksa 0.0 döndür
        return 0.0
    
    def perform_calibration(self):
        """Kalibrasyon hesapla"""
        try:
            success, message, calibration_function = self.calibration_manager.calculate_calibration()
            
            if success and calibration_function:
                # Başarılı kalibrasyon
                slope = calibration_function['slope']
                intercept = calibration_function['intercept']
                r_squared = calibration_function['r_squared']
                
                self.cal_status.configure(text=f"Kalibrasyon tamamlandı - R² = {r_squared:.4f}")
                
                messagebox.showinfo("Calibration Successful", 
                                  f"Kalibrasyon tamamlandı!\n\n"
                                  f"Denklem: konsantrasyon = {slope:.3f} × voltaj + {intercept:.3f}\n"
                                  f"R² = {r_squared:.3f}\n\n"
                                  f"Bu fonksiyon artık voltaj okumalarını konsantrasyon değerlerine çevirmek için kullanılacak.")
                
                app_logger.info(f"Kalibrasyon başarılı: R² = {r_squared:.4f}")
                
            else:
                # Kalibrasyon hatası
                self.cal_status.configure(text=f"Kalibrasyon hatası: {message}")
                messagebox.showerror("Calibration Error", f"Kalibrasyon hatası:\n{message}")
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon hesaplama hatası: {e}")
            messagebox.showerror("Error", f"Kalibrasyon hesaplama hatası: {e}")
    
    def clear_calibration_data(self):
        """Kalibrasyon verilerini temizle"""
        for i in range(MAX_CALIBRATION_POINTS):
            self.calibration_entries[i].delete(0, tk.END)
            self.calibration_values[i].configure(text="0.000")
            self.calibration_status[i].configure(text="Waiting", foreground="orange")
        
        self.calibrate_btn.configure(state=tk.DISABLED)
        self.calibration_manager.clear_current_calibration_data()
        
        self.cal_status.configure(text="Kalibrasyon verileri temizlendi")
        app_logger.info("Kalibrasyon verileri temizlendi")
    
    def take_reference(self):
        """Referans ölçümü al"""
        if not self.data_callback:
            messagebox.showwarning("Warning", "Sistem bağlantısı gerekli!")
            return
        
        self.cal_status.configure(text="Referans ölçümü alınıyor...")
        
        def reference_process():
            try:
                sample_count = 10
                measurements = []
                
                # Ortam ışığı ölçümü (tüm LED'ler kapalı)
                time.sleep(1)
                
                for i in range(sample_count):
                    # Referans ölçümü (gerçek sensör verisi)
                    value = self.get_current_sensor_value()
                    measurements.append(value)
                    time.sleep(0.1)
                
                ref_value = sum(measurements) / len(measurements)
                
                # İlk değere referans değerini yaz
                if self.calibration_entries:
                    self.calibration_entries[0].delete(0, tk.END)
                    self.calibration_entries[0].insert(0, f"{ref_value:.3f}")
                
                self.cal_status.configure(text=f"Referans alındı: {ref_value:.3f}V")
                messagebox.showinfo("Reference", f"Referans değeri: {ref_value:.3f}V")
                
                app_logger.info(f"Referans ölçümü tamamlandı: {ref_value:.3f}V")
                
            except Exception as e:
                self.cal_status.configure(text=f"Referans hatası: {str(e)}")
                messagebox.showerror("Error", f"Referans ölçümü hatası: {e}")
                app_logger.error(f"Referans ölçümü hatası: {e}")
        
        ref_thread = threading.Thread(target=reference_process, daemon=True)
        ref_thread.start()
    
    def save_calibration(self):
        """Kalibrasyon verilerini kaydet"""
        try:
            success, filename = self.calibration_manager.export_calibration()
            
            if success:
                self.cal_status.configure(text=f"Kalibrasyon kaydedildi: {filename}")
                messagebox.showinfo("Success", f"Kalibrasyon kaydedildi: {filename}")
                app_logger.info(f"Kalibrasyon kaydedildi: {filename}")
            else:
                messagebox.showerror("Error", f"Kalibrasyon kaydedilemedi: {filename}")
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon kaydetme hatası: {e}")
            messagebox.showerror("Error", f"Kalibrasyon kaydedilemedi: {e}")
    
    def load_calibration(self):
        """Kalibrasyon verilerini yükle"""
        try:
            filename = filedialog.askopenfilename(
                title="Kalibrasyon Dosyası Seç",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            success, message = self.calibration_manager.import_calibration(filename)
            
            if success:
                self.cal_status.configure(text=f"Kalibrasyon yüklendi: {filename}")
                messagebox.showinfo("Success", message)
                app_logger.info(f"Kalibrasyon yüklendi: {filename}")
                
                # UI'yi güncelle
                self.update_calibration_display()
            else:
                messagebox.showerror("Error", f"Kalibrasyon yüklenemedi: {message}")
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon yükleme hatası: {e}")
            messagebox.showerror("Error", f"Kalibrasyon yüklenemedi: {e}")
    
    def update_calibration_display(self):
        """Kalibrasyon görünümünü güncelle"""
        try:
            # Mevcut kalibrasyon bilgilerini al
            cal_info = self.calibration_manager.get_current_calibration_info()
            
            if cal_info['sensor_key']:
                # Sensor dropdown'ını güncelle
                sensor_mapping = {
                    "UV_360nm": "UV Sensor (360nm)",
                    "Blue_450nm": "Blue Sensor (450nm)",
                    "IR_850nm": "IR Sensor (850nm)",
                    "IR_940nm": "IR Sensor (940nm)"
                }
                
                sensor_key = cal_info['sensor_key']
                if sensor_key in sensor_mapping:
                    self.selected_sensor.set(sensor_mapping[sensor_key])
                
                # Molekül bilgilerini güncelle
                self.molecule_name.delete(0, tk.END)
                self.molecule_name.insert(0, cal_info['molecule_name'])
                
                self.molecule_unit.delete(0, tk.END)
                self.molecule_unit.insert(0, cal_info['unit'])
                
                # Kalibrasyon noktalarını güncelle
                points_data = cal_info['points_data']
                for i, (conc, volt) in enumerate(points_data):
                    if i < len(self.calibration_entries):
                        self.calibration_entries[i].delete(0, tk.END)
                        self.calibration_entries[i].insert(0, str(conc))
                        
                        self.calibration_values[i].configure(text=f"{volt:.3f}")
                        self.calibration_status[i].configure(text="Loaded", foreground="blue")
                
                # Kalibrasyon butonunu aktifleştir
                if cal_info['is_ready']:
                    self.calibrate_btn.configure(state=tk.NORMAL)
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon görünüm güncelleme hatası: {e}")
    
    def update_live_measurement(self, sensor_key: str, raw_value: float):
        """Canlı ölçüm değerlerini güncelle"""
        try:
            # Kalibrasyon penceresi açık değilse çık
            if not self.window or not self.window.winfo_exists():
                return
                
            # Seçili sensör ile eşleşen ölçümü güncelle
            current_cal_info = self.calibration_manager.get_current_calibration_info()
            
            if current_cal_info['sensor_key'] == sensor_key:
                # Bekleyen (Waiting) durumundaki tüm değerleri güncelle
                for i, status_label in enumerate(self.calibration_status):
                    if status_label.cget("text") == "Waiting":
                        self.calibration_values[i].configure(text=f"{raw_value:.3f}")
                        app_logger.debug(f"Kalibrasyon değeri güncellendi: {i+1} -> {raw_value:.3f}V")
                        
        except Exception as e:
            app_logger.error(f"Canlı ölçüm güncelleme hatası: {e}")
    
    def close_window(self):
        """Pencereyi kapat"""
        try:
            # LED'leri kapat
            if self.led_control_callback:
                self.led_control_callback(None, False)
            
            if self.window:
                self.window.destroy()
                self.window = None
            
            app_logger.info("Kalibrasyon penceresi kapatıldı")
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon penceresi kapatma hatası: {e}")
    
    def is_window_open(self) -> bool:
        """Pencere açık mı?"""
        return self.window is not None and self.window.winfo_exists()
    
    def get_calibration_status_text(self) -> str:
        """Kalibrasyon durum metnini al"""
        try:
            status = self.calibration_manager.get_calibration_status()
            calibrated_count = sum(status.values())
            
            if calibrated_count > 0:
                return f"{calibrated_count} sensör kalibre edildi"
            else:
                return "Hiç sensör kalibre edilmedi"
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon durum metni hatası: {e}")
            return "Kalibrasyon durumu bilinmiyor"
    
    def apply_current_theme(self):
        """Mevcut temayı uygula"""
        try:
            from config.settings import settings_manager
            current_theme = settings_manager.get_theme()
            
            # Bu panel butonları otomatik olarak StyleManager tarafından güncelleniyor
            app_logger.debug(f"Calibration window {current_theme} tema uygulandı")
            
        except Exception as e:
            app_logger.error(f"Calibration window tema uygulama hatası: {e}")