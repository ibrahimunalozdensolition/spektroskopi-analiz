"""
Kalibrasyon İşlemleri Modülü
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from utils.logger import app_logger, log_calibration_event
from utils.helpers import (
    validate_calibration_data, perform_linear_regression, 
    apply_calibration, generate_filename
)
from config.constants import MIN_CALIBRATION_POINTS, MAX_CALIBRATION_POINTS

class CalibrationManager:
    """Kalibrasyon yöneticisi sınıfı"""
    
    def __init__(self):
        # Kalibrasyon fonksiyonları
        self.calibration_functions = {
            'UV_360nm': None,
            'Blue_450nm': None,
            'IR_850nm': None,
            'IR_940nm': None
        }
        
        # Kalibrasyon verileri (geçici)
        self.calibration_data = {
            'concentrations': [],
            'voltages': [],
            'sensor_key': None,
            'molecule_name': '',
            'unit': 'ppm'
        }
        
        # Kalibrasyon geçmişi
        self.calibration_history = []
    
    def start_calibration(self, sensor_key: str, molecule_name: str = "", unit: str = "ppm"):
        """Kalibrasyon sürecini başlat"""
        valid_sensors = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        if sensor_key not in valid_sensors:
            app_logger.error(f"Geçersiz sensör anahtarı: {sensor_key}")
            return False
        
        # Kalibrasyon verilerini sıfırla
        self.calibration_data = {
            'concentrations': [],
            'voltages': [],
            'sensor_key': sensor_key,
            'molecule_name': molecule_name,
            'unit': unit
        }
        
        log_calibration_event(app_logger, sensor_key, "CALIBRATION_STARTED", 
                            f"Molecule: {molecule_name}, Unit: {unit}")
        return True
    
    def add_calibration_point(self, concentration: float, voltage: float) -> bool:
        """Kalibrasyon noktası ekle"""
        if self.calibration_data['sensor_key'] is None:
            app_logger.error("Kalibrasyon başlatılmamış")
            return False
        
        if len(self.calibration_data['concentrations']) >= MAX_CALIBRATION_POINTS:
            app_logger.warning(f"Maksimum kalibrasyon noktası sayısına ulaşıldı: {MAX_CALIBRATION_POINTS}")
            return False
        
        try:
            self.calibration_data['concentrations'].append(concentration)
            self.calibration_data['voltages'].append(voltage)
            
            log_calibration_event(app_logger, self.calibration_data['sensor_key'], 
                                "POINT_ADDED", f"C={concentration}, V={voltage:.3f}")
            return True
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon noktası ekleme hatası: {e}")
            return False
    
    def remove_calibration_point(self, index: int) -> bool:
        """Kalibrasyon noktasını kaldır"""
        try:
            if 0 <= index < len(self.calibration_data['concentrations']):
                removed_conc = self.calibration_data['concentrations'].pop(index)
                removed_volt = self.calibration_data['voltages'].pop(index)
                
                log_calibration_event(app_logger, self.calibration_data['sensor_key'], 
                                    "POINT_REMOVED", f"Index={index}, C={removed_conc}, V={removed_volt:.3f}")
                return True
            else:
                app_logger.error(f"Geçersiz indeks: {index}")
                return False
                
        except Exception as e:
            app_logger.error(f"Kalibrasyon noktası kaldırma hatası: {e}")
            return False
    
    def calculate_calibration(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Kalibrasyon hesapla"""
        if self.calibration_data['sensor_key'] is None:
            return False, "Kalibrasyon başlatılmamış", None
        
        concentrations = self.calibration_data['concentrations']
        voltages = self.calibration_data['voltages']
        
        # Veri doğrulama
        is_valid, error_msg = validate_calibration_data(concentrations, voltages)
        if not is_valid:
            return False, error_msg, None
        
        try:
            # Doğrusal regresyon hesapla
            regression_result = perform_linear_regression(voltages, concentrations)
            
            # Kalibrasyon fonksiyonu oluştur
            calibration_function = {
                'slope': regression_result['slope'],
                'intercept': regression_result['intercept'],
                'r_squared': regression_result['r_squared'],
                'molecule': self.calibration_data['molecule_name'],
                'unit': self.calibration_data['unit'],
                'calibration_points': len(concentrations),
                'created_at': datetime.now().isoformat()
            }
            
            # Kalibrasyon fonksiyonunu kaydet
            sensor_key = self.calibration_data['sensor_key']
            self.calibration_functions[sensor_key] = calibration_function
            
            # Geçmişe ekle
            self.calibration_history.append({
                'sensor_key': sensor_key,
                'function': calibration_function.copy(),
                'data_points': list(zip(concentrations, voltages))
            })
            
            log_calibration_event(app_logger, sensor_key, "CALIBRATION_COMPLETED", 
                                f"R²={regression_result['r_squared']:.4f}")
            
            return True, "Kalibrasyon başarılı", calibration_function
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon hesaplama hatası: {e}")
            return False, f"Hesaplama hatası: {str(e)}", None
    
    def apply_calibration_to_value(self, sensor_key: str, raw_value: float) -> float:
        """Tek değere kalibrasyon uygula"""
        if sensor_key in self.calibration_functions:
            cal_func = self.calibration_functions[sensor_key]
            return apply_calibration(raw_value, cal_func)
        else:
            return raw_value
    
    def get_calibration_function(self, sensor_key: str) -> Optional[Dict[str, Any]]:
        """Sensör için kalibrasyon fonksiyonunu al"""
        return self.calibration_functions.get(sensor_key)
    
    def set_calibration_function(self, sensor_key: str, function_data: Dict[str, Any]):
        """Kalibrasyon fonksiyonunu ayarla"""
        if sensor_key in self.calibration_functions:
            self.calibration_functions[sensor_key] = function_data
            log_calibration_event(app_logger, sensor_key, "FUNCTION_SET")
    
    def remove_calibration(self, sensor_key: str) -> bool:
        """Sensör kalibrasyonunu kaldır"""
        if sensor_key in self.calibration_functions:
            self.calibration_functions[sensor_key] = None
            log_calibration_event(app_logger, sensor_key, "CALIBRATION_REMOVED")
            return True
        return False
    
    def clear_current_calibration_data(self):
        """Mevcut kalibrasyon verilerini temizle"""
        self.calibration_data = {
            'concentrations': [],
            'voltages': [],
            'sensor_key': None,
            'molecule_name': '',
            'unit': 'ppm'
        }
        app_logger.info("Mevcut kalibrasyon verileri temizlendi")
    
    def get_calibration_status(self) -> Dict[str, bool]:
        """Tüm sensörlerin kalibrasyon durumunu al"""
        return {
            sensor_key: (func is not None) 
            for sensor_key, func in self.calibration_functions.items()
        }
    
    def get_calibrated_sensors_count(self) -> int:
        """Kalibre edilmiş sensör sayısını al"""
        return sum(1 for func in self.calibration_functions.values() if func is not None)
    
    def export_calibration(self, filename: Optional[str] = None) -> Tuple[bool, str]:
        """Kalibrasyon verilerini dışa aktar"""
        try:
            if filename is None:
                filename = generate_filename("calibration", "json")
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'calibration_functions': self.calibration_functions,
                'calibration_history': self.calibration_history[-10:]  # Son 10 kalibrasyon
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Kalibrasyon verileri dışa aktarıldı: {filename}")
            return True, filename
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon dışa aktarma hatası: {e}")
            return False, str(e)
    
    def import_calibration(self, filename: str) -> Tuple[bool, str]:
        """Kalibrasyon verilerini içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Kalibrasyon fonksiyonlarını yükle
            if 'calibration_functions' in import_data:
                for sensor_key, func_data in import_data['calibration_functions'].items():
                    if sensor_key in self.calibration_functions:
                        self.calibration_functions[sensor_key] = func_data
                        if func_data:
                            log_calibration_event(app_logger, sensor_key, "FUNCTION_IMPORTED")
            
            # Geçmişi yükle
            if 'calibration_history' in import_data:
                self.calibration_history.extend(import_data['calibration_history'])
            
            app_logger.info(f"Kalibrasyon verileri içe aktarıldı: {filename}")
            return True, "Kalibrasyon başarıyla yüklendi"
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon içe aktarma hatası: {e}")
            return False, str(e)
    
    def get_calibration_equation(self, sensor_key: str) -> Optional[str]:
        """Kalibrasyon denklemini string olarak al"""
        if sensor_key in self.calibration_functions:
            func = self.calibration_functions[sensor_key]
            if func:
                slope = func.get('slope', 0)
                intercept = func.get('intercept', 0)
                unit = func.get('unit', 'V')
                return f"Concentration = {slope:.0f} × Voltage + {intercept:.0f} ({unit})"
        
        return None
    
    def validate_current_calibration(self) -> Tuple[bool, str]:
        """Mevcut kalibrasyon verilerini doğrula"""
        concentrations = self.calibration_data['concentrations']
        voltages = self.calibration_data['voltages']
        
        return validate_calibration_data(concentrations, voltages)
    
    def get_current_calibration_info(self) -> Dict[str, Any]:
        """Mevcut kalibrasyon bilgilerini al"""
        return {
            'sensor_key': self.calibration_data['sensor_key'],
            'molecule_name': self.calibration_data['molecule_name'],
            'unit': self.calibration_data['unit'],
            'points_count': len(self.calibration_data['concentrations']),
            'points_data': list(zip(self.calibration_data['concentrations'], 
                                  self.calibration_data['voltages'])),
            'is_ready': len(self.calibration_data['concentrations']) >= MIN_CALIBRATION_POINTS
        }
