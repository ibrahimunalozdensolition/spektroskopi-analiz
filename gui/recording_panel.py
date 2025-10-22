import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import threading
import time
import json
import os

from utils.logger import app_logger
from config.constants import SENSOR_INFO

class RecordingPanel:
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        
        # UI bileşenleri
        self.record_btn = None
        self.stop_btn = None
        self.progress_bar = None
        self.time_label = None
        self.status_label = None
        
        # Sensör sonuç label'ları
        self.sensor_result_labels = {}
        
        # Karşılaştırma combobox'ları
        self.first_record_combo = None
        self.second_record_combo = None
        
        # Recording durumu
        self.is_recording = False
        self.recording_thread = None
        self.start_time = None
        self.recorded_data = {
            'raw': {'UV_360nm': [], 'Blue_450nm': [], 'IR_850nm': [], 'IR_940nm': []},
            'calibrated': {'UV_360nm': [], 'Blue_450nm': [], 'IR_850nm': [], 'IR_940nm': []},
            'custom': {'timestamps': []}
        }
        
        # Veri callback
        self.data_callback = None
        
        # Data processor referansı (custom data almak için)
        self.data_processor = None
        
        self.recording_duration = 15
        
        self.records_dir = "records"
        self.ensure_records_directory()
        
        self.last_record_data = None
        
        self.status_messages = self.load_status_messages()
        
        self.setup_panel()
        
        self.apply_current_theme()
    
    def set_data_callback(self, callback: Callable):
        self.data_callback = callback
    
    def set_data_processor(self, data_processor):
        """Data processor referansını ayarla"""
        self.data_processor = data_processor
    
    def load_status_messages(self) -> Dict:
        try:
            status_file = os.path.join("config", "status_messages.json")
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                app_logger.warning(f"Status messages file not found: {status_file}")
                return {"status_combinations": {}, "sensor_order": [], "sensor_names": {}}
        except Exception as e:
            app_logger.error(f"Error loading status messages: {e}")
            return {"status_combinations": {}, "sensor_order": [], "sensor_names": {}}
    
    def setup_panel(self):
        """Ana paneli kur"""
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Data Recording & Averaging", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Üst kısım - Kontroller
        self.setup_controls_panel(main_frame)
        
        # Orta kısım - Progress ve Status
        self.setup_progress_panel(main_frame)
        
        # Alt kısım - Kayıtlar ve Karşılaştırma
        self.setup_records_panel(main_frame)
    
    def setup_controls_panel(self, parent_frame):
        """Kontrol paneli"""
        controls_frame = ttk.LabelFrame(parent_frame, text="Recording Controls", padding=15)
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Açıklama
        desc_label = ttk.Label(controls_frame, 
                              text="Press 'Start Recording' to collect data ",
                              font=("Arial", 16))
        desc_label.pack(pady=(0, 10))
        
        # Butonlar
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X)
        
        self.record_btn = ttk.Button(button_frame, text="🔴 Start Recording", 
                                    command=self.start_recording,
                                    style="Green.TButton")
        self.record_btn.pack(side=tk.LEFT, padx=(0, 16))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop Recording", 
                                  command=self.stop_recording,
                                  style="Red.TButton",
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Kayıt süresi ayarı
        duration_frame = ttk.Frame(controls_frame)
        duration_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(duration_frame, text="Recording Duration:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.duration_var = tk.IntVar(value=15)
        duration_spinbox = ttk.Spinbox(duration_frame, from_=5, to=60, width=10,
                                      textvariable=self.duration_var,
                                      command=self.update_duration)
        duration_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(duration_frame, text="seconds", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Kayıt dosya ayarları
        self.setup_file_settings_panel(controls_frame)
    
    def setup_file_settings_panel(self, parent_frame):
        """Dosya kayıt ayarları paneli"""
        from tkinter import filedialog
        
        # Ayırıcı çizgi
        separator = ttk.Separator(parent_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(15, 10))
        
        # Dosya ayarları başlığı
        ttk.Label(parent_frame, text="File Settings", 
                 font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Dosya adı satırı
        filename_frame = ttk.Frame(parent_frame)
        filename_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(filename_frame, text="File Name:", 
                 font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT)
        
        self.filename_var = tk.StringVar(value=f"Record_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var, width=40)
        filename_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(filename_frame, text="🔄 Auto Generate", 
                  command=self.auto_generate_filename,
                  style="Blue.TButton").pack(side=tk.LEFT)
        
        # Kayıt yeri satırı
        location_frame = ttk.Frame(parent_frame)
        location_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(location_frame, text="Save Location:", 
                 font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT)
        
        self.location_var = tk.StringVar(value=os.path.abspath(self.records_dir))
        location_entry = ttk.Entry(location_frame, textvariable=self.location_var, 
                                   width=50, state='readonly')
        location_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(location_frame, text="📁 Browse", 
                  command=self.browse_save_location,
                  style="Blue.TButton").pack(side=tk.LEFT)
        
        # Bilgi etiketi
        info_label = ttk.Label(parent_frame, 
                              text="💡 Records will be saved as JSON files in the selected location",
                              font=("Arial", 9), foreground="gray")
        info_label.pack(anchor=tk.W, pady=(5, 0))
    
    def auto_generate_filename(self):
        """Otomatik dosya adı oluştur"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename_var.set(f"Record_{timestamp}")
        app_logger.info(f"Auto-generated filename: Record_{timestamp}")
    
    def browse_save_location(self):
        """Kayıt yeri seç"""
        from tkinter import filedialog
        
        directory = filedialog.askdirectory(
            title="Select Save Location",
            initialdir=self.records_dir
        )
        
        if directory:
            self.records_dir = directory
            self.location_var.set(os.path.abspath(directory))
            app_logger.info(f"Save location changed: {directory}")
            
            # Kayıtlar listesini güncelle
            self.load_records_list()
    
    def setup_progress_panel(self, parent_frame):
        """Progress ve durum paneli"""
        progress_frame = ttk.LabelFrame(parent_frame, text="Recording Progress", padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Zaman ve durum bilgisi
        info_frame = ttk.Frame(progress_frame)
        info_frame.pack(fill=tk.X)
        
        self.time_label = ttk.Label(info_frame, text="Ready to record", 
                                   font=("Arial", 12, "bold"))
        self.time_label.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(info_frame, text="Status: Idle", 
                                     font=("Arial", 10))
        self.status_label.pack(side=tk.RIGHT)
    
    def setup_records_panel(self, parent_frame):
        """Kayıtlar ve karşılaştırma paneli"""
        records_frame = ttk.LabelFrame(parent_frame, text="Records & Comparison", padding=15)
        records_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sol taraf - Eski kayıtlar
        left_frame = ttk.Frame(records_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_frame, text="Previous Records:", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Kayıtlar listesi
        self.records_listbox = tk.Listbox(left_frame, height=8, font=("Arial", 16),
                                         bg='#252525', fg='#e8e8e8',
                                         selectbackground='#3a3a3a', selectforeground='#ffffff',
                                         borderwidth=1, relief='solid', highlightthickness=0)
        self.records_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Refresh butonu
        ttk.Button(left_frame, text="Refresh Records", 
                  command=self.load_records_list).pack(fill=tk.X)
        
        # Sağ taraf - Karşılaştırma
        right_frame = ttk.Frame(records_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Comparison:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Karşılaştırma seçimi - İki ayrı combobox
        compare_frame = ttk.Frame(right_frame)
        compare_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Birinci kayıt seçimi
        first_record_frame = ttk.Frame(compare_frame)
        first_record_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(first_record_frame, text="First Record:", font=("Arial", 16, "bold")).pack(anchor=tk.W)
        self.first_record_combo = ttk.Combobox(first_record_frame, state="readonly", width=30)
        self.first_record_combo.pack(fill=tk.X, pady=(2, 0))
        
        # İkinci kayıt seçimi
        second_record_frame = ttk.Frame(compare_frame)
        second_record_frame.pack(fill=tk.X, pady=(5, 10))
        ttk.Label(second_record_frame, text="Second Record:", font=("Arial", 16, "bold")).pack(anchor=tk.W)
        self.second_record_combo = ttk.Combobox(second_record_frame, state="readonly", width=30)
        self.second_record_combo.pack(fill=tk.X, pady=(2, 0))
        
        # Karşılaştırma butonu
        ttk.Button(compare_frame, text="Compare Selected Records", 
                  command=self.compare_two_records,
                  style="Blue.TButton").pack(fill=tk.X, pady=(5, 0))
        
        # Karşılaştırma sonuçları
        self.comparison_frame = ttk.Frame(right_frame)
        self.comparison_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Karşılaştırma sonuçları başlığı
        ttk.Label(self.comparison_frame, text="Comparison Results:", 
                 font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Sonuçlar için scrollable text
        self.comparison_text = tk.Text(self.comparison_frame, height=6, width=40,
                                      bg='#252525', fg='#e8e8e8',
                                      insertbackground='#e8e8e8',
                                      selectbackground='#3a3a3a',
                                      selectforeground='#ffffff',
                                      borderwidth=1, relief='solid',
                                      font=("Courier", 16))
        self.comparison_text.pack(fill=tk.BOTH, expand=True)
        
        # Başlangıçta kayıtları yükle
        self.load_records_list()
    
    def update_duration(self):
        self.recording_duration = self.duration_var.get()
        app_logger.info(f"Recording duration updated: {self.recording_duration} seconds")
    
    def start_recording(self):
        if self.is_recording:
            app_logger.warning("Recording already in progress")
            return
        
        if not self.data_callback:
            app_logger.error("Data callback not set!")
            if self.status_label:
                self.status_label.configure(text="Status: Error - No data source")
            messagebox.showerror("Error", "Data source not connected! Please check BLE connection.")
            return
        
        # Test callback'i
        try:
            test_data = self.data_callback()
            app_logger.debug(f"Test callback successful: {test_data is not None}")
        except Exception as test_error:
            app_logger.error(f"Data callback test failed: {test_error}")
            messagebox.showerror("Error", f"Cannot get data from sensors: {test_error}")
            return
        
        # UI durumunu güncelle
        self.record_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        self.status_label.configure(text="Status: Recording...")
        
        # Veri listelerini temizle
        for data_type in ['raw', 'calibrated', 'custom']:
            for sensor_key in self.recorded_data[data_type]:
                self.recorded_data[data_type][sensor_key].clear()
        
        # Recording durumunu ayarla
        self.is_recording = True
        self.start_time = datetime.now()
        
        # Recording thread'ini başlat
        self.recording_thread = threading.Thread(target=self.recording_worker)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        app_logger.info(f"Recording started for {self.recording_duration} seconds")
    
    def stop_recording(self):
        """Kayıt durdur"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # UI durumunu güncelle
        self.record_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="Status: Processing...")
        
        # Sonuçları hesapla
        self.calculate_and_display_results()
        
        app_logger.info("Recording stopped by user")
    
    def recording_worker(self):
        """Recording worker thread"""
        try:
            app_logger.debug("Recording worker started")
            sample_count = 0
            
            while self.is_recording:
                current_time = datetime.now()
                elapsed = (current_time - self.start_time).total_seconds()
                
                # Süre doldu mu kontrol et
                if elapsed >= self.recording_duration:
                    self.is_recording = False
                    app_logger.debug(f"Recording duration reached: {elapsed:.1f}s")
                    break
                
                # Veri al
                if self.data_callback:
                    try:
                        latest_data = self.data_callback()
                        app_logger.debug(f"Got data from callback: raw keys={list(latest_data.get('raw', {}).keys()) if latest_data else 'None'}")
                        
                        if latest_data and 'raw' in latest_data and 'calibrated' in latest_data:
                            data_added = False
                            
                            # Raw verileri kaydet
                            for sensor_key in self.recorded_data['raw']:
                                if sensor_key in latest_data['raw']:
                                    value = latest_data['raw'][sensor_key]
                                    # Değer kontrolünü gevşet - 0 değeri de kabul et
                                    if value is not None:  
                                        self.recorded_data['raw'][sensor_key].append(value)
                                        data_added = True
                            
                            # Calibrated verileri kaydet
                            for sensor_key in self.recorded_data['calibrated']:
                                if sensor_key in latest_data['calibrated']:
                                    value = latest_data['calibrated'][sensor_key]
                                    if value is not None:  
                                        self.recorded_data['calibrated'][sensor_key].append(value)
                            
                            # Custom data kaydet (data_processor'dan al)
                            if self.data_processor and data_added:
                                try:
                                    custom_data = self.data_processor.get_custom_data()
                                    if custom_data and 'timestamps' in custom_data and len(custom_data['timestamps']) > 0:
                                        # Timestamp ekle
                                        self.recorded_data['custom']['timestamps'].append(current_time)
                                        
                                        # Her custom formula için son değeri al
                                        for formula_name, values in custom_data.items():
                                            if formula_name != 'timestamps' and len(values) > 0:
                                                if formula_name not in self.recorded_data['custom']:
                                                    self.recorded_data['custom'][formula_name] = []
                                                self.recorded_data['custom'][formula_name].append(values[-1])
                                except Exception as custom_error:
                                    app_logger.error(f"Custom data recording error: {custom_error}")
                            
                            if data_added:
                                sample_count += 1
                                if sample_count % 10 == 0:  # Her 10 örnekte bir log
                                    app_logger.debug(f"Recorded {sample_count} samples")
                        else:
                            app_logger.warning(f"Data callback returned incomplete data: {latest_data}")
                    except Exception as cb_error:
                        app_logger.error(f"Data callback error: {cb_error}")
                
                # Progress bar ve zaman güncelle (UI thread'de)
                progress = min((elapsed / self.recording_duration) * 100, 100)
                remaining = max(0, self.recording_duration - elapsed)
                
                self.parent_frame.after(0, lambda p=progress, r=remaining: self.update_ui_progress(p, r))
                
                # 100ms bekle
                time.sleep(0.1)
            
            # Recording tamamlandı
            app_logger.info(f"Recording completed with {sample_count} total samples")
            self.parent_frame.after(0, self.recording_completed)
                
        except Exception as e:
            app_logger.error(f"Recording worker error: {e}", exc_info=True)
            self.parent_frame.after(0, self.recording_error)
    
    def update_ui_progress(self, progress: float, remaining: float):
        """UI progress güncelle"""
        try:
            if self.progress_bar:
                self.progress_bar['value'] = progress
            if self.time_label:
                self.time_label.configure(text=f"Recording... {remaining:.1f}s remaining")
        except Exception as e:
            app_logger.error(f"UI progress update error: {e}")
    
    def recording_completed(self):
        """Kayıt tamamlandı"""
        self.is_recording = False
        
        # UI durumunu güncelle
        self.record_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar['value'] = 100
        self.time_label.configure(text="Recording completed!")
        self.status_label.configure(text="Status: Processing...")
        
        # Sonuçları hesapla
        self.calculate_and_display_results()
        
        app_logger.info("Recording completed successfully")
    
    def recording_error(self):
        """Kayıt hatası"""
        self.is_recording = False
        
        # UI durumunu güncelle
        self.record_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="Status: Error occurred")
        self.time_label.configure(text="Recording failed!")
        
        app_logger.error("Recording failed due to error")
    
    def calculate_and_display_results(self):
        """Sonuçları hesapla ve kaydet"""
        try:
            results = {'raw': {}, 'calibrated': {}}
            
            # Debug: Kaydedilen veri sayılarını logla
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                raw_count = len(self.recorded_data['raw'][sensor_key])
                cal_count = len(self.recorded_data['calibrated'][sensor_key])
                app_logger.debug(f"{sensor_key}: {raw_count} raw, {cal_count} calibrated samples")
            
            # Her sensör için ortalama hesapla
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                # Raw ortalama
                raw_data = self.recorded_data['raw'][sensor_key]
                if raw_data:
                    results['raw'][sensor_key] = sum(raw_data) / len(raw_data)
                    app_logger.debug(f"{sensor_key} raw avg: {results['raw'][sensor_key]:.3f}")
                else:
                    results['raw'][sensor_key] = 0.0
                    app_logger.warning(f"{sensor_key} has no raw data!")
                
                # Calibrated ortalama
                cal_data = self.recorded_data['calibrated'][sensor_key]
                if cal_data:
                    results['calibrated'][sensor_key] = sum(cal_data) / len(cal_data)
                    app_logger.debug(f"{sensor_key} cal avg: {results['calibrated'][sensor_key]:.3f}")
                else:
                    results['calibrated'][sensor_key] = 0.0
                    app_logger.warning(f"{sensor_key} has no calibrated data!")
            
            
            # JSON kaydetme pop-up'ı göster (otomatik karşılaştırma kaldırıldı)
            self.save_record_with_popup(results)
            
            # Log sonuçları
            total_samples = sum(len(self.recorded_data['raw'][key]) for key in self.recorded_data['raw'])
            app_logger.info(f"Recording results calculated - Total samples: {total_samples}")
            
            if self.status_label:
                self.status_label.configure(text=f"Status: Completed ({total_samples} samples)")
            
        except Exception as e:
            app_logger.error(f"Results calculation error: {e}", exc_info=True)
            if self.status_label:
                self.status_label.configure(text="Status: Calculation error")
    
    def ensure_records_directory(self):
        """Records klasörünün var olduğundan emin ol"""
        try:
            if not os.path.exists(self.records_dir):
                os.makedirs(self.records_dir)
                app_logger.info(f"Records directory created: {self.records_dir}")
        except Exception as e:
            app_logger.error(f"Records directory creation error: {e}")
    
    def convert_datetime_to_string(self, data):
        """Datetime objelerini ISO string formatına çevir (JSON serializable)"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self.convert_datetime_to_string(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.convert_datetime_to_string(item) for item in data]
        else:
            return data
    
    def save_record_with_popup(self, results: Dict):
        """Kullanıcının belirlediği isim ve konumda kayıt yap"""
        try:
            # Dosya adını al (eğer boşsa otomatik oluştur)
            record_name = self.filename_var.get().strip()
            if not record_name:
                record_name = f"Record_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.filename_var.set(record_name)
            
            # Onay al
            result = messagebox.askyesno(
                "Save Record",
                f"Save this recording?\n\n"
                f"File Name: {record_name}.json\n"
                f"Location: {self.records_dir}\n\n"
                f"Duration: {self.recording_duration} seconds\n"
                f"Samples: {sum(len(self.recorded_data['raw'][key]) for key in self.recorded_data['raw'])}"
            )
            
            if result:
                # Kayıt verilerini hazırla (datetime'ları string'e çevir)
                serializable_recorded_data = self.convert_datetime_to_string(self.recorded_data)
                
                record_data = {
                    'name': record_name,
                    'timestamp': datetime.now().isoformat(),
                    'duration': self.recording_duration,
                    'samples_count': sum(len(self.recorded_data['raw'][key]) for key in self.recorded_data['raw']),
                    'results': results,
                    'raw_data': serializable_recorded_data
                }
                
                # JSON dosyasına kaydet
                filename = f"{record_name}.json"
                filepath = os.path.join(self.records_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(record_data, f, indent=2, ensure_ascii=False)
                
                # Son kaydı sakla
                self.last_record_data = record_data
                
                # Kayıtlar listesini güncelle
                self.load_records_list()
                
                # Sadece başarı mesajı göster
                messagebox.showinfo(
                    "Record Saved", 
                    f"Record '{record_name}' saved successfully!\n\nFile: {filepath}"
                )
                
                app_logger.info(f"Record saved: {filepath}")
                
                # Bir sonraki kayıt için dosya adını otomatik güncelle
                self.auto_generate_filename()
                
        except Exception as e:
            app_logger.error(f"Record save error: {e}")
            messagebox.showerror("Save Error", f"Failed to save record: {e}")
    
    def load_records_list(self):
        """Kayıtlar listesini yükle"""
        try:
            self.records_listbox.delete(0, tk.END)
            
            if not os.path.exists(self.records_dir):
                return
            
            # JSON dosyalarını bul
            json_files = [f for f in os.listdir(self.records_dir) if f.endswith('.json')]
            json_files.sort(reverse=True)  # En yeni önce
            
            # Combobox için liste
            combo_values = []
            
            for filename in json_files:
                try:
                    filepath = os.path.join(self.records_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Listbox'a ekle
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    display_text = f"{data['name']} - {timestamp.strftime('%Y-%m-%d %H:%M')}"
                    self.records_listbox.insert(tk.END, display_text)
                    
                    # Combobox için ekle
                    combo_values.append(data['name'])
                    
                except Exception as e:
                    app_logger.warning(f"Error loading record {filename}: {e}")
            
            # Her iki combobox'ı güncelle
            self.first_record_combo['values'] = combo_values
            self.second_record_combo['values'] = combo_values
            
            # Eğer kayıt varsa, ilk ikisini seç
            if len(combo_values) > 0:
                self.first_record_combo.current(0)
            if len(combo_values) > 1:
                self.second_record_combo.current(1)
            
        except Exception as e:
            app_logger.error(f"Records list load error: {e}")
    
    def compare_two_records(self):
        """İki seçili kaydı karşılaştır"""
        try:
            first_name = self.first_record_combo.get()
            second_name = self.second_record_combo.get()
            
            if not first_name or not second_name:
                messagebox.showwarning("No Selection", "Please select two records to compare!")
                return
            
            if first_name == second_name:
                messagebox.showwarning("Same Record", "Please select two different records!")
                return
            
            # Birinci kaydı yükle
            first_filepath = os.path.join(self.records_dir, f"{first_name}.json")
            if not os.path.exists(first_filepath):
                messagebox.showerror("File Not Found", f"First record file not found: {first_name}")
                return
            
            with open(first_filepath, 'r', encoding='utf-8') as f:
                first_data = json.load(f)
            
            # İkinci kaydı yükle
            second_filepath = os.path.join(self.records_dir, f"{second_name}.json")
            if not os.path.exists(second_filepath):
                messagebox.showerror("File Not Found", f"Second record file not found: {second_name}")
                return
            
            with open(second_filepath, 'r', encoding='utf-8') as f:
                second_data = json.load(f)
            
            # Karşılaştırma yap (first_data = eski, second_data = yeni)
            comparison_results = self.perform_comparison(first_data, second_data)
            
            # Status pattern oluştur ve mesaj bul
            sensor_order = self.status_messages.get('sensor_order', ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm'])
            status_list = []
            
            for sensor_key in sensor_order:
                if sensor_key in comparison_results:
                    # Calibrated değerleri kullan
                    status = comparison_results[sensor_key]['calibrated']['change']['status']
                    status_list.append(status)
                else:
                    status_list.append('STABLE')
            
            status_pattern = ','.join(status_list)
            
            # Mesaj bul ve pop-up göster
            status_combinations = self.status_messages.get('status_combinations', {})
            message = status_combinations.get(status_pattern, '')
            
            if message:
                messagebox.showinfo(
                    "Comparison Analysis",
                    f"Pattern Detected: [{status_pattern}]\n\n{message}\n\nComparison: {first_name} → {second_name}"
                )
            
            # Sonuçları göster
            self.display_comparison_results(comparison_results, first_name, second_name)
            
        except Exception as e:
            app_logger.error(f"Comparison error: {e}")
            messagebox.showerror("Comparison Error", f"Failed to perform comparison: {e}")
    
    def perform_comparison(self, old_data: Dict, new_data: Dict) -> Dict:
        """İki kayıt arasında karşılaştırma yap"""
        results = {}
        
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            # Raw karşılaştırma
            old_raw = old_data['results']['raw'].get(sensor_key, 0.0)
            new_raw = new_data['results']['raw'].get(sensor_key, 0.0)
            raw_change = self.calculate_change_status(old_raw, new_raw)
            
            # Calibrated karşılaştırma
            old_cal = old_data['results']['calibrated'].get(sensor_key, 0.0)
            new_cal = new_data['results']['calibrated'].get(sensor_key, 0.0)
            cal_change = self.calculate_change_status(old_cal, new_cal)
            
            results[sensor_key] = {
                'raw': {
                    'old': old_raw,
                    'new': new_raw,
                    'change': raw_change
                },
                'calibrated': {
                    'old': old_cal,
                    'new': new_cal,
                    'change': cal_change
                }
            }
        
        return results
    
    def calculate_change_status(self, old_value: float, new_value: float) -> Dict:
        """Değişim durumunu hesapla"""
        if old_value == 0:
            if new_value == 0:
                return {'status': 'STABLE', 'percentage': 0.0}
            else:
                return {'status': 'HIGH', 'percentage': float('inf')}
        
        percentage_change = ((new_value - old_value) / old_value) * 100
        
        if percentage_change >= 10:
            status = 'HIGH'
        elif percentage_change <= -10:
            status = 'LOW'
        else:
            status = 'STABLE'
        
        return {
            'status': status,
            'percentage': percentage_change
        }
    
    def display_comparison_results(self, results: Dict, first_record: str, second_record: str):
        """Karşılaştırma sonuçlarını göster"""
        try:
            # Text widget'ı temizle
            self.comparison_text.delete(1.0, tk.END)
            
            # Başlık
            header = f"📊 Comparison Results\n"
            header += f"Old: {first_record}\n"
            header += f"New: {second_record}\n"
            header += "=" * 50 + "\n\n"
            self.comparison_text.insert(tk.END, header)
            
            # Her sensör için sonuçları göster
            sensor_names = {
                'UV_360nm': 'UV Detector',
                'Blue_450nm': 'Blue Detector', 
                'IR_850nm': 'IR Detector 1',
                'IR_940nm': 'IR Detector 2'
            }
            
            for sensor_key, sensor_name in sensor_names.items():
                if sensor_key in results:
                    sensor_result = results[sensor_key]
                    
                    # Sensör başlığı
                    self.comparison_text.insert(tk.END, f"📊 {sensor_name}:\n")
                    
                    # Raw sonuçları
                    raw = sensor_result['raw']
                    raw_line = f"  Raw: {raw['old']:.3f}V → {raw['new']:.3f}V "
                    raw_line += f"({raw['change']['percentage']:+.1f}%) "
                    raw_line += f"[{raw['change']['status']}]\n"
                    self.comparison_text.insert(tk.END, raw_line)
                    
                    # Calibrated sonuçları
                    cal = sensor_result['calibrated']
                    cal_line = f"  Cal: {cal['old']:.3f}ppm → {cal['new']:.3f}ppm "
                    cal_line += f"({cal['change']['percentage']:+.1f}%) "
                    cal_line += f"[{cal['change']['status']}]\n\n"
                    self.comparison_text.insert(tk.END, cal_line)
            
            # Legend
            legend = "\nLegend:\n"
            legend += "HIGH  = >+10% increase\n"
            legend += "STABLE = -10% to +10% change\n"
            legend += "LOW   = <-10% decrease\n"
            self.comparison_text.insert(tk.END, legend)
            
        except Exception as e:
            app_logger.error(f"Comparison display error: {e}")
    
    def get_recording_status(self) -> Dict:
        """Recording durumunu al"""
        return {
            'is_recording': self.is_recording,
            'duration': self.recording_duration,
            'elapsed': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    def apply_current_theme(self):
        """Mevcut temayı uygula"""
        try:
            # Settings'ten tema bilgisini al
            from config.settings import settings_manager
            current_theme = settings_manager.get_theme()
            
            if current_theme == 'dark':
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
                
        except Exception as e:
            app_logger.error(f"Recording panel tema uygulama hatası: {e}")
    
    def apply_dark_theme(self):
        """Dark theme uygula"""
        try:
            # Spinbox için dark theme
            if hasattr(self, 'duration_var'):
                # TTK Spinbox için özel stil uygulama gerekebilir
                pass
            
            app_logger.debug("Recording panel dark theme uygulandı")
            
        except Exception as e:
            app_logger.error(f"Recording panel dark theme hatası: {e}")
    
    def apply_light_theme(self):
        try:
            # Spinbox için light theme
            if hasattr(self, 'duration_var'):
                # TTK Spinbox için özel stil uygulama gerekebilir
                pass
            
            app_logger.debug("Recording panel light theme uygulandı")
            
        except Exception as e:
            app_logger.error(f"Recording panel light theme hatası: {e}")
