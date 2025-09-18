import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from .constants import SETTINGS_FILE

class SettingsManager:   
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        self.default_settings = self._get_default_settings()
        self.current_settings = self.load_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Varsayılan ayarları döndür"""
        return {
            'led_names': {
                'UV LED (360nm)': 'UV',
                'Blue LED (450nm)': 'Blue',
                'IR LED (850nm)': 'IR850', 
                'IR LED (940nm)': 'IR940'
            },
            'custom_data': {
                'selected_sensor': None,
                'multiplier': 1.0,
                'unit': 'V'
            },
            'graph_settings': {
                'update_interval': 100,
                'max_data_points': 1000,
                'x_range_seconds': 60,
                'auto_scale': True
            },
            'calibration': {
                'functions': {},
                'last_calibration': {}
            },
            'connection': {
                'auto_connect': True,
                'last_connected_sensor': None,
                'scan_timeout': 7.0
            },
            'sampling': {
                'rate_ms': 500,
                'buffer_size': 100
            },
            'appearance': {
                'theme': 'dark'  # Sadece dark theme destekleniyor
            }
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Ayarları dosyadan yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Varsayılan ayarlarla birleştir (eksik anahtarları ekle)
                settings = self.default_settings.copy()
                self._deep_update(settings, loaded_settings)
                
                print("Ayarlar başarıyla yüklendi")
                return settings
            else:
                print("Ayar dosyası bulunamadı, varsayılan ayarlar kullanılıyor")
                return self.default_settings.copy()
                
        except Exception as e:
            print(f"Ayar yükleme hatası: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Ayarları dosyaya kaydet"""
        try:
            # Kaydetme zamanını ekle
            self.current_settings['last_updated'] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, indent=2, ensure_ascii=False)
            
            print("Ayarlar başarıyla kaydedildi")
            return True
            
        except Exception as e:
            print(f"Ayar kaydetme hatası: {e}")
            return False
    
    def get(self, key_path: str, default=None):
        """Noktalı yol ile ayar değeri al (örn: 'graph_settings.update_interval')"""
        keys = key_path.split('.')
        value = self.current_settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Noktalı yol ile ayar değeri belirle"""
        keys = key_path.split('.')
        target = self.current_settings
        
        try:
            # Son anahtara kadar git
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            # Son anahtarı ayarla
            target[keys[-1]] = value
            return True
            
        except Exception as e:
            print(f"Ayar belirleme hatası: {e}")
            return False
    
    def get_led_names(self) -> Dict[str, str]:
        """LED isimlerini al"""
        return self.get('led_names', {})
    
    def set_led_name(self, led_key: str, name: str) -> bool:
        """LED ismini ayarla"""
        return self.set(f'led_names.{led_key}', name)
    
    def get_calibration_function(self, sensor_key: str) -> Optional[Dict[str, Any]]:
        """Sensör için kalibrasyon fonksiyonunu al"""
        return self.get(f'calibration.functions.{sensor_key}')
    
    def set_calibration_function(self, sensor_key: str, function_data: Dict[str, Any]) -> bool:
        """Sensör için kalibrasyon fonksiyonunu ayarla"""
        return self.set(f'calibration.functions.{sensor_key}', function_data)
    
    # Sampling rate fonksiyonları kaldırıldı - tüm veriler direkt işlenir
    
    def get_theme(self) -> str:
        """Tema ayarını al - Sadece dark theme"""
        return 'dark'  # Her zaman dark theme döndür
    
    def set_theme(self, theme: str) -> bool:
        """Tema ayarını belirle - Sadece dark theme"""
        # Her zaman dark theme ayarla
        return self.set('appearance.theme', 'dark')
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """İç içe sözlükleri derin güncelleme"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def reset_to_defaults(self) -> bool:
        """Ayarları varsayılana sıfırla"""
        try:
            self.current_settings = self.default_settings.copy()
            return self.save_settings()
        except Exception as e:
            print(f"Ayar sıfırlama hatası: {e}")
            return False
    
    def export_settings(self, filename: str) -> bool:
        """Ayarları belirtilen dosyaya dışa aktar"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ayar dışa aktarma hatası: {e}")
            return False
    
    def import_settings(self, filename: str) -> bool:
        """Ayarları belirtilen dosyadan içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            self.current_settings = self.default_settings.copy()
            self._deep_update(self.current_settings, imported_settings)
            
            return self.save_settings()
        except Exception as e:
            print(f"Ayar içe aktarma hatası: {e}")
            return False

# Global settings instance
settings_manager = SettingsManager()
