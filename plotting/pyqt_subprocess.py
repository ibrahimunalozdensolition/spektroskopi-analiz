"""
PyQt Subprocess Yöneticisi - Tkinter ile çakışmayı önlemek için
"""

import subprocess
import json
import tempfile
import os
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import app_logger

class PyQtSubprocessManager:
    """PyQt'yi ayrı process'te çalıştıran yönetici"""
    
    def __init__(self):
        self.active_processes = {}
        self.data_files = {}
    
    def create_graph_window(self, window_id: str, selected_sensors: List[str], 
                           title: str, graph_type: str = "line") -> bool:
        """Ayrı process'te PyQt grafik penceresi oluştur"""
        try:
            # Geçici veri dosyası oluştur
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            data_file_path = temp_file.name
            temp_file.close()
            
            # Başlangıç verileri
            initial_data = {
                'window_id': window_id,
                'selected_sensors': selected_sensors,
                'title': title,
                'graph_type': graph_type,
                'timestamps': [],
                'data': {sensor: [] for sensor in selected_sensors}
            }
            
            with open(data_file_path, 'w') as f:
                json.dump(initial_data, f)
            
            # PyQt script'ini çalıştır
            script_path = os.path.join(os.path.dirname(__file__), 'pyqt_standalone.py')
            
            # Subprocess başlat
            process = subprocess.Popen([
                'python3', script_path, data_file_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.active_processes[window_id] = process
            self.data_files[window_id] = data_file_path
            
            app_logger.info(f"PyQt subprocess başlatıldı: {window_id}")
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
        """Grafik verilerini güncelle"""
        try:
            if window_id not in self.data_files:
                app_logger.warning(f"PyQt pencere bulunamadı: {window_id}")
                return
            
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
        """Grafik penceresini kapat"""
        try:
            if window_id in self.active_processes:
                process = self.active_processes[window_id]
                process.terminate()
                del self.active_processes[window_id]
            
            if window_id in self.data_files:
                data_file_path = self.data_files[window_id]
                if os.path.exists(data_file_path):
                    os.unlink(data_file_path)
                del self.data_files[window_id]
            
            app_logger.info(f"PyQt subprocess kapatıldı: {window_id}")
            
        except Exception as e:
            app_logger.error(f"PyQt subprocess kapatma hatası: {e}")
    
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
