"""
PyQt Subprocess Yöneticisi - Tkinter ile çakışmayı önlemek için
"""

import subprocess
import json
import tempfile
import os
import threading
import platform
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import app_logger

class PyQtSubprocessManager:
    """PyQt'yi ayrı process'te çalıştıran yönetici"""
    
    def __init__(self):
        self.active_processes = {}
        self.data_files = {}
        self.last_update_times = {}  # Son güncelleme zamanlarını takip et
        self.update_throttle_ms = 500  # Minimum güncelleme aralığı (ms) - DONMA ÖNLEMİ: 100->500
    
    def _get_python_command(self) -> str:
        """Platform'a göre python komutunu belirle"""
        system = platform.system().lower()
        if system == "windows":
            return "python"
        else:  # macOS, Linux ve diğerleri için
            return "python3"
    
    def create_graph_window(self, window_id: str, selected_sensors: List[str], 
                           title: str, graph_type: str = "line", 
                           initial_timestamps: List = None, initial_data: Dict = None) -> bool:
        try:
            # Geçici veri dosyası oluştur
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            data_file_path = temp_file.name
            temp_file.close()
            
            # Başlangıç verileri - mevcut veriler varsa kullan
            graph_data = {
                'window_id': window_id,
                'selected_sensors': selected_sensors,
                'title': title,
                'graph_type': graph_type,
                'timestamps': initial_timestamps if initial_timestamps else [],
                'data': {}
            }
            
            # Her sensör için veri hazırla
            for sensor in selected_sensors:
                if initial_data and sensor in initial_data:
                    graph_data['data'][sensor] = initial_data[sensor]
                else:
                    graph_data['data'][sensor] = []
            
            with open(data_file_path, 'w') as f:
                json.dump(graph_data, f)
            
            # PyQt script'ini çalıştır
            script_path = os.path.join(os.path.dirname(__file__), 'pyqt_standalone.py')
            
            # Subprocess başlat - PIPE dolma problemini çöz
            python_cmd = self._get_python_command()
            
            # DEVNULL kullanarak pipe dolma problemini önle
            with open(os.devnull, 'w') as devnull:
                process = subprocess.Popen([
                    python_cmd, script_path, data_file_path
                ], stdout=devnull, stderr=devnull, 
                   start_new_session=True)  # Yeni session - zombie process önleme
            
            self.active_processes[window_id] = process
            self.data_files[window_id] = data_file_path
            
            app_logger.info(f"PyQt subprocess başlatıldı (PIPE-safe): {window_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"PyQt subprocess başlatma hatası: {e}")
            return False
    
    def _clean_data_for_json(self, data: Any) -> Any:
        """Veriyi JSON serializable hale getir"""
        if isinstance(data, dict):
            return {k: self._clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_json(item) for item in data]
        elif hasattr(data, 'isoformat'):  # datetime nesnesi
            return data.isoformat()
        elif hasattr(data, '__dict__'):  # Diğer nesneler
            return str(data)
        else:
            return data
    
    def update_graph_data(self, window_id: str, timestamps: List, 
                         data_dict: Dict[str, List[float]]):
        """Grafik verilerini güncelle - throttling ile"""
        try:
            if window_id not in self.data_files:
                app_logger.warning(f"PyQt pencere bulunamadı: {window_id}")
                return
            
            # Güncelleme throttling - çok sık güncellemeyi önle
            current_time = datetime.now()
            if window_id in self.last_update_times:
                time_diff = (current_time - self.last_update_times[window_id]).total_seconds() * 1000
                if time_diff < self.update_throttle_ms:
                    app_logger.debug(f"PyQt güncelleme throttled: {window_id} (son güncelleme: {time_diff:.1f}ms önce)")
                    return
            
            self.last_update_times[window_id] = current_time
            data_file_path = self.data_files[window_id]
            
            # Mevcut konfigürasyonu oku
            try:
                with open(data_file_path, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = {}
            
            # Timestamps'i güvenli şekilde string'e çevir
            timestamps_str = []
            if timestamps:
                for t in timestamps:
                    try:
                        if hasattr(t, 'isoformat'):
                            timestamps_str.append(t.isoformat())
                        else:
                            timestamps_str.append(str(t))
                    except Exception as ts_e:
                        app_logger.warning(f"Timestamp çevirme hatası: {ts_e}")
                        timestamps_str.append("invalid")
            
            # Tüm veriyi temizle (datetime nesnelerini string'e çevir)
            clean_data_dict = self._clean_data_for_json(data_dict)
            
            update_data = existing_data.copy()
            update_data.update({
                'timestamps': timestamps_str,
                'data': clean_data_dict if clean_data_dict else {}
            })
            
            # Debug log
            app_logger.debug(f"PyQt veri güncelleniyor: {window_id}, {len(timestamps_str)} timestamp, {len(clean_data_dict) if clean_data_dict else 0} sensör")
            
            # Dosyaya yaz
            with open(data_file_path, 'w') as f:
                json.dump(update_data, f, indent=2)
            
            app_logger.info(f"PyQt veri başarıyla güncellendi: {window_id}")
            
        except Exception as e:
            app_logger.error(f"PyQt veri güncelleme hatası: {e}")
            import traceback
            app_logger.error(f"Traceback: {traceback.format_exc()}")
    
    def close_window(self, window_id: str):
        """Grafik penceresini kapat - gelişmiş process temizleme"""
        try:
            if window_id in self.active_processes:
                process = self.active_processes[window_id]
                
                # Önce nazikçe terminate dene
                process.terminate()
                
                # 2 saniye bekle
                import time
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Hala çalışıyorsa zorla öldür
                    app_logger.warning(f"Process {window_id} zorla öldürülüyor")
                    process.kill()
                    process.wait()  # Zombie process önleme
                
                del self.active_processes[window_id]
                app_logger.info(f"PyQt subprocess temizlendi: {window_id}")
            
            # Data file temizleme
            if window_id in self.data_files:
                data_file_path = self.data_files[window_id]
                if os.path.exists(data_file_path):
                    try:
                        os.unlink(data_file_path)
                    except OSError as e:
                        app_logger.warning(f"Data file silinemedi {data_file_path}: {e}")
                del self.data_files[window_id]
            
            # Update time temizleme
            if window_id in self.last_update_times:
                del self.last_update_times[window_id]
            
            app_logger.info(f"PyQt subprocess kapatıldı: {window_id}")
            
        except Exception as e:
            app_logger.error(f"PyQt subprocess kapatma hatası: {e}")
            import traceback
            app_logger.debug(f"Close window traceback: {traceback.format_exc()}")
    
    def close_all_windows(self):
        """Tüm grafik pencerelerini kapat"""
        for window_id in list(self.active_processes.keys()):
            self.close_window(window_id)
    
    def is_window_active(self, window_id: str) -> bool:
        """Pencere aktif mi?"""
        if window_id not in self.active_processes:
            return False
        
        process = self.active_processes[window_id]
        return process.poll() is None  # None = hala çalışıyor
