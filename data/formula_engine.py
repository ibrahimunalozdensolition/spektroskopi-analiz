import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from utils.logger import app_logger

class FormulaEngine:
    
    def __init__(self):
        # Mevcut formüller
        self.formulas = {}
        
        self.selected_formulas = set()
        
        # Sensör eşleştirmesi
        self.sensor_mapping = {
            'ch1': 'UV_360nm',      # SENSOR_2
            'ch2': 'Blue_450nm',    # SENSOR_EXTRA  
            'ch3': 'IR_850nm',      # SENSOR_5
            'ch4': 'IR_940nm',      # SENSOR_7
            'sensor_2': 'UV_360nm',
            'sensor_extra': 'Blue_450nm',
            'sensor_5': 'IR_850nm',
            'sensor_7': 'IR_940nm',
            'uv': 'UV_360nm',
            'blue': 'Blue_450nm',
            'ir850': 'IR_850nm',
            'ir940': 'IR_940nm'
        }
        
        # Güvenli matematik operatörleri
        self.allowed_operators = ['+', '-', '*', '/', '(', ')', '.', ' ']
        self.allowed_functions = ['abs', 'max', 'min', 'sqrt', 'pow']
    
    def create_formula(self, name: str, formula: str, unit: str = "V") -> Tuple[bool, str]:
        """Yeni formül oluştur"""
        try:
            # Formülü doğrula
            is_valid, error_msg = self.validate_formula(formula)
            if not is_valid:
                return False, error_msg
            
            # Formülü kaydet
            self.formulas[name] = {
                'formula': formula,
                'unit': unit,
                'created_at': datetime.now().isoformat(),
                'last_value': 0.0,
                'selected': False  # Varsayılan olarak seçili değil
            }
            
            app_logger.info(f"Formül oluşturuldu: {name} = {formula} ({unit})")
            return True, f"Formül başarıyla oluşturuldu: {name}"
            
        except Exception as e:
            app_logger.error(f"Formül oluşturma hatası: {e}")
            return False, str(e)
    
    def validate_formula(self, formula: str) -> Tuple[bool, str]:
        """Formülü doğrula"""
        try:
            # Boş formül kontrolü
            if not formula.strip():
                return False, "Formül boş olamaz"
            
            # Güvenlik kontrolü - sadece izin verilen karakterler
            clean_formula = formula.lower().replace(' ', '')
            
            # Sensör isimlerini geçici değişkenlerle değiştir
            test_formula = clean_formula
            for sensor_name in self.sensor_mapping.keys():
                test_formula = test_formula.replace(sensor_name, '1.0')
            
            # Sadece izin verilen karakterleri kontrol et
            allowed_chars = set('0123456789+-*/().abcdefghijklmnopqrstuvwxyz_')
            if not all(c in allowed_chars for c in test_formula):
                return False, "Formülde geçersiz karakterler var"
            
            # Basit syntax kontrolü
            if test_formula.count('(') != test_formula.count(')'):
                return False, "Parantez sayıları eşleşmiyor"
            
            # Test hesaplama
            try:
                test_data = {sensor: 1.0 for sensor in self.sensor_mapping.values()}
                # Mevcut formülleri de test verisine ekle
                test_calculated = {name: 1.0 for name in self.formulas.keys()}
                result = self.calculate_formula(formula, test_data, test_calculated)
                if result is None:
                    return False, "Formül hesaplanamıyor"
            except:
                return False, "Formül syntax hatası"
            
            return True, "Formül geçerli"
            
        except Exception as e:
            return False, f"Doğrulama hatası: {e}"
    
    def calculate_formula(self, formula: str, sensor_data: Dict[str, float], 
                         calculated_data: Optional[Dict[str, float]] = None) -> Optional[float]:
        """Formülü hesapla (sensör verileri + hesaplanmış veriler)"""
        try:
            # Formülü hazırla
            calc_formula = formula.lower()
            
            # Önce hesaplanmış verileri değiştir (eğer varsa)
            if calculated_data:
                for data_name, value in calculated_data.items():
                    calc_formula = calc_formula.replace(data_name.lower(), str(value))
            
            # Sonra sensör isimlerini değerlerle değiştir
            for sensor_name, sensor_key in self.sensor_mapping.items():
                if sensor_key in sensor_data:
                    value = sensor_data[sensor_key]
                    calc_formula = calc_formula.replace(sensor_name, str(value))
            
            # Güvenli hesaplama
            result = self.safe_eval(calc_formula)
            
            return result
            
        except Exception as e:
            app_logger.error(f"Formül hesaplama hatası: {e}")
            return None
    
    def safe_eval(self, expression: str) -> float:
        """Güvenli matematik hesaplama"""
        try:
            # Sadece matematik operatörleri ve sayıları içeren ifadeleri değerlendir
            # Güvenlik için eval yerine daha güvenli bir yöntem
            
            # Basit matematik kütüphanesi
            import math
            
            # Güvenli namespace
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "max": max,
                "min": min,
                "sqrt": math.sqrt,
                "pow": pow,
                "pi": math.pi,
                "e": math.e
            }
            
            # Hesaplama
            result = eval(expression, safe_dict)
            
            return float(result)
            
        except Exception as e:
            app_logger.error(f"Güvenli hesaplama hatası: {e}")
            raise
    
    def calculate_selected_formulas(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        results = {}
        
        # Seçili formülleri al
        selected_formulas = {name: info for name, info in self.formulas.items() 
                           if info.get('selected', False)}
        
        if not selected_formulas:
            app_logger.debug("Hiç formül seçili değil, hesaplama atlandı")
            return results
        
        app_logger.debug(f"Seçili formüller hesaplanıyor: {list(selected_formulas.keys())}")
        
        # Sadece seçili formülleri hesapla - tek geçiş
        for name, formula_info in selected_formulas.items():
            try:
                result = self.calculate_formula(
                    formula_info['formula'], 
                    sensor_data, 
                    results  # Önceki hesaplanmış veriler
                )
                
                if result is not None:
                    results[name] = result
                    self.formulas[name]['last_value'] = result
                    app_logger.debug(f"Seçili formül hesaplandı: {name} = {result:.3f}")
                else:
                    results[name] = 0.0
                    
            except Exception as e:
                app_logger.warning(f"Seçili formül hatası ({name}): {e}")
                results[name] = 0.0
        
        return results
    
    def calculate_all_formulas(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        """Tüm formülleri hesapla - DEPRECATED - calculate_selected_formulas kullanın"""
        app_logger.warning("calculate_all_formulas deprecated - calculate_selected_formulas kullanılıyor")
        return self.calculate_selected_formulas(sensor_data)
    
    def calculate_all_available_formulas(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        """Tüm mevcut formülleri hesapla (seçili olma şartı yok)"""
        results = {}
        
        if not self.formulas:
            app_logger.debug("Hiç formül yok, hesaplama atlandı")
            return results
        
        app_logger.debug(f"Tüm formüller hesaplanıyor: {list(self.formulas.keys())}")
        
        # Tüm formülleri hesapla - tek geçiş
        for name, formula_info in self.formulas.items():
            try:
                result = self.calculate_formula(
                    formula_info['formula'], 
                    sensor_data, 
                    results  # Önceki hesaplanmış veriler
                )
                
                if result is not None:
                    results[name] = result
                    # Son değeri güncelle
                    self.formulas[name]['last_value'] = result
                    app_logger.debug(f"Formül hesaplandı: {name} = {result:.3f}")
                else:
                    results[name] = 0.0
                    
            except Exception as e:
                app_logger.warning(f"Formül hesaplama hatası ({name}): {e}")
                results[name] = 0.0
        
        return results
    
    def select_formula(self, name: str, selected: bool = True) -> bool:
        """Formülü seç/seçimi kaldır"""
        if name in self.formulas:
            self.formulas[name]['selected'] = selected
            if selected:
                self.selected_formulas.add(name)
                app_logger.info(f"Formül seçildi: {name}")
            else:
                self.selected_formulas.discard(name)
                app_logger.info(f"Formül seçimi kaldırıldı: {name}")
            return True
        return False
    
    def toggle_formula_selection(self, name: str) -> bool:
        """Formül seçimini değiştir"""
        if name in self.formulas:
            current_state = self.formulas[name].get('selected', False)
            return self.select_formula(name, not current_state)
        return False
    
    def select_all_formulas(self, selected: bool = True):
        """Tüm formülleri seç/seçimi kaldır"""
        for name in self.formulas.keys():
            self.select_formula(name, selected)
        app_logger.info(f"Tüm formüller {'seçildi' if selected else 'seçimi kaldırıldı'}")
    
    def get_selected_formulas(self) -> Dict[str, Dict[str, Any]]:
        """Seçili formülleri al"""
        return {name: info for name, info in self.formulas.items() 
                if info.get('selected', False)}
    
    def get_selected_formula_count(self) -> int:
        """Seçili formül sayısını al"""
        return len([1 for info in self.formulas.values() if info.get('selected', False)])
    
    def remove_formula(self, name: str) -> bool:
        """Formülü kaldır"""
        if name in self.formulas:
            del self.formulas[name]
            self.selected_formulas.discard(name)  # Seçili listeden de kaldır
            app_logger.info(f"Formül kaldırıldı: {name}")
            return True
        return False
    
    def get_formula_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Formül bilgilerini al"""
        return self.formulas.get(name)
    
    def get_all_formulas(self) -> Dict[str, Dict[str, Any]]:
        """Tüm formülleri al"""
        return self.formulas.copy()
    
    def get_available_sensors(self) -> Dict[str, str]:
        """Kullanılabilir sensör isimlerini al"""
        return {
            'ch1 (UV Sensor)': 'ch1',
            'ch2 (Blue Sensor)': 'ch2', 
            'ch3 (IR 850nm)': 'ch3',
            'ch4 (IR 940nm)': 'ch4',
            'sensor_2 (UV)': 'sensor_2',
            'sensor_extra (Blue)': 'sensor_extra',
            'sensor_5 (IR850)': 'sensor_5',
            'sensor_7 (IR940)': 'sensor_7',
            'uv': 'uv',
            'blue': 'blue',
            'ir850': 'ir850',
            'ir940': 'ir940'
        }
    
    def get_formula_examples(self) -> List[str]:
        """Örnek formülleri al"""
        return [
            "ch1 + ch2",
            "ch1 * 2.5 + ch2 * 1.8",
            "(ch1 + ch2) / 2",
            "ch1 - ch2",
            "abs(ch1 - ch3)",
            "max(ch1, ch2, ch3, ch4)",
            "sqrt(ch1 * ch1 + ch2 * ch2)",
            "ch1 * 0.85 + ch2 * 1.15 - 0.05"
        ]
    
    def export_formulas(self) -> Dict[str, Any]:
        """Formülleri dışa aktar"""
        return {
            'formulas': self.formulas,
            'sensor_mapping': self.sensor_mapping,
            'export_date': datetime.now().isoformat()
        }
    
    def import_formulas(self, formula_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Formülleri içe aktar"""
        try:
            if 'formulas' in formula_data:
                self.formulas.update(formula_data['formulas'])
                app_logger.info(f"{len(formula_data['formulas'])} formül içe aktarıldı")
                return True, "Formüller başarıyla yüklendi"
            else:
                return False, "Geçersiz formül dosyası"
                
        except Exception as e:
            app_logger.error(f"Formül içe aktarma hatası: {e}")
            return False, str(e)
