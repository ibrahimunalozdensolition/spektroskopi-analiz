import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from tkinter import messagebox

from utils.logger import app_logger
from utils.helpers import format_csv_value, generate_filename
from data.formula_engine import FormulaEngine

class DataExporter:
    """Veri dışa aktarma sınıfı"""
    
    def __init__(self):
        self.last_export_filename = None
        self.led_names = self._load_led_names()
        self.export_folder = "exported_data"
        self._ensure_export_folder_exists()
        self.formula_engine = FormulaEngine()
        self._load_formulas_from_settings()
    
    def _ensure_export_folder_exists(self):
        try:
            if not os.path.exists(self.export_folder):
                os.makedirs(self.export_folder)
                app_logger.info(f"Export klasörü oluşturuldu: {self.export_folder}")
        except Exception as e:
            app_logger.error(f"Export klasörü oluşturulamadı: {e}")
            # Klasör oluşturulamazsa ana dizini kullan
            self.export_folder = "."
    
    def _load_led_names(self) -> Dict[str, str]:
        """app_settings.json dosyasından LED isimlerini yükle"""
        try:
            settings_path = 'app_settings.json'
            
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings.get('led_names', {})
            else:
                app_logger.warning(f"app_settings.json bulunamadı: {settings_path}")
                return {}
        except Exception as e:
            app_logger.error(f"LED isimleri yükleme hatası: {e}")
            return {}
    
    def _get_led_name_for_sensor(self, sensor_key: str) -> str:
        """Sensor key'e göre LED ismini döndür"""
        default_names = {
            'UV_360nm': 'UV Detector',
            'Blue_450nm': 'Blue Detector', 
            'IR_850nm': 'IR Detector 1',
            'IR_940nm': 'IR Detector 2'
        }
        
        # Sensor key'e göre LED ismini bul
        led_name = None
        if sensor_key == 'UV_360nm':
            led_name = next((value for key, value in self.led_names.items() if '360nm' in key), None)
        elif sensor_key == 'Blue_450nm':
            led_name = next((value for key, value in self.led_names.items() if '450nm' in key), None)
        elif sensor_key == 'IR_850nm':
            led_name = next((value for key, value in self.led_names.items() if '850nm' in key), None)
        elif sensor_key == 'IR_940nm':
            led_name = next((value for key, value in self.led_names.items() if '940nm' in key), None)
        
        if not led_name:
            led_name = default_names.get(sensor_key, sensor_key)
        
        return led_name
    
    def _load_formulas_from_settings(self):
        """app_settings.json'dan formülleri yükle"""
        try:
            settings_path = 'app_settings.json'
            
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                formulas_data = settings.get('formulas', {})
                if 'formulas' in formulas_data:
                    self.formula_engine.formulas = formulas_data['formulas']
                    app_logger.info(f"Export için {len(self.formula_engine.formulas)} formül yüklendi")
                
                if 'sensor_mapping' in formulas_data:
                    self.formula_engine.sensor_mapping.update(formulas_data['sensor_mapping'])
                    
        except Exception as e:
            app_logger.error(f"Formül yükleme hatası: {e}")
    
    def _calculate_all_custom_data(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tüm custom data değerlerini yeniden hesapla (export sırasında)"""
        try:
            # Raw data'dan sensor değerlerini al
            raw_data = row_data['raw_data']
            sensor_data = {
                'UV_360nm': raw_data.get('UV_360nm', 0),
                'Blue_450nm': raw_data.get('Blue_450nm', 0),
                'IR_850nm': raw_data.get('IR_850nm', 0),
                'IR_940nm': raw_data.get('IR_940nm', 0)
            }
            
            # Tüm formülleri yeniden hesapla
            calculated_values = self.formula_engine.calculate_all_available_formulas(sensor_data)
            
            # Hesaplanan değerleri döndür (mevcut custom data'yı görmezden gel)
            return calculated_values
            
        except Exception as e:
            app_logger.error(f"Custom data hesaplama hatası: {e}")
            return {}
    
    def export_to_csv(self, export_data: List[Dict[str, Any]], 
                     filename: Optional[str] = None,
                     excel_compatible: bool = True) -> Tuple[bool, str]:
        """Verileri CSV formatında dışa aktar"""
        try:
            if not export_data:
                return False, "Dışa aktarılacak veri yok"
            
            if filename is None:
                base_filename = generate_filename("spectroscopy_export", "csv")
                filename = os.path.join(self.export_folder, base_filename)
            else:
                # Eğer kullanıcı dosya adı verdiyse, export klasörüne koy
                if not os.path.dirname(filename):  # Sadece dosya adı verilmişse
                    filename = os.path.join(self.export_folder, filename)
            
            # Excel uyumluluğu için encoding ve delimiter
            encoding = 'utf-8-sig' if excel_compatible else 'utf-8'
            delimiter = ';' if excel_compatible else ','
            
            with open(filename, 'w', encoding=encoding, newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Header row - önce custom data formüllerini belirle
                custom_formulas = set()
                for row_data in export_data:
                    if 'custom_data' in row_data:
                        custom_formulas.update(row_data['custom_data'].keys())
                
                # LED isimlerini app_settings.json'dan çek
                uv_name = self._get_led_name_for_sensor('UV_360nm')
                blue_name = self._get_led_name_for_sensor('Blue_450nm')
                ir850_name = self._get_led_name_for_sensor('IR_850nm')
                ir940_name = self._get_led_name_for_sensor('IR_940nm')
                
                headers = [
                    'Time',
                    f'{uv_name} (Raw mV)', f'{uv_name} (Cal)',
                    f'{blue_name} (Raw mV)', f'{blue_name} (Cal)', 
                    f'{ir850_name} (Raw mV)', f'{ir850_name} (Cal)',
                    f'{ir940_name} (Raw mV)', f'{ir940_name} (Cal)'
                ]
                
                # Custom data başlıklarını ekle
                for formula_name in sorted(custom_formulas):
                    headers.append(f'Custom: {formula_name}')
                
                writer.writerow(headers)
                
                # Data rows
                for row_data in export_data:
                    raw_data = row_data['raw_data']
                    
                    # Raw data tümü 0 ise bu satırı atla
                    if all(raw_data.get(sensor, 0) == 0 for sensor in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']):
                        continue
                    
                    timestamp = row_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
                    cal_data = row_data['calibrated_data']
                    
                    custom_data = self._calculate_all_custom_data(row_data)
                    
                    # Format values for Excel compatibility
                    def format_value(value, is_calibrated=False, is_raw=False, is_custom=False):
                        if value is None or (is_calibrated and value is None):
                            return ""
                        if is_raw or is_custom:
                            # Raw data ve custom data için virgülden sonra basamak yok (tam sayı)
                            return format_csv_value(int(value), decimal_places=0) if excel_compatible else f"{int(value)}"
                        else:
                            # Calibrated data için 3 basamak
                            return format_csv_value(value, decimal_places=3) if excel_compatible else f"{value:.3f}"
                    
                    csv_row = [
                        timestamp,
                        format_value(raw_data.get('UV_360nm', 0), is_raw=True),
                        format_value(cal_data.get('UV_360nm'), is_calibrated=True),
                        format_value(raw_data.get('Blue_450nm', 0), is_raw=True),
                        format_value(cal_data.get('Blue_450nm'), is_calibrated=True),
                        format_value(raw_data.get('IR_850nm', 0), is_raw=True),
                        format_value(cal_data.get('IR_850nm'), is_calibrated=True),
                        format_value(raw_data.get('IR_940nm', 0), is_raw=True),
                        format_value(cal_data.get('IR_940nm'), is_calibrated=True)
                    ]
                    
                    # Custom data değerlerini ekle
                    for formula_name in sorted(custom_formulas):
                        value = custom_data.get(formula_name)
                        if value is not None:
                            csv_row.append(format_value(value, is_custom=True))
                        else:
                            csv_row.append("")  
                    
                    writer.writerow(csv_row)
            
            self.last_export_filename = filename
            app_logger.info(f"Veri CSV formatında dışa aktarıldı: {filename}")
            return True, filename
            
        except Exception as e:
            app_logger.error(f"CSV dışa aktarma hatası: {e}")
            return False, str(e)
    
    def export_to_json(self, export_data: List[Dict[str, Any]], 
                      filename: Optional[str] = None) -> Tuple[bool, str]:
        """Verileri JSON formatında dışa aktar"""
        try:
            if not export_data:
                return False, "Dışa aktarılacak veri yok"
            
            if filename is None:
                base_filename = generate_filename("spectroscopy_export", "json")
                filename = os.path.join(self.export_folder, base_filename)
            else:
                # Eğer kullanıcı dosya adı verdiyse, export klasörüne koy
                if not os.path.dirname(filename):  # Sadece dosya adı verilmişse
                    filename = os.path.join(self.export_folder, filename)
            
            # JSON formatı için veriyi hazırla
            json_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'data_points': len(export_data),
                    'format_version': '1.0'
                },
                'data': []
            }
            
            for row_data in export_data:
                json_row = {
                    'timestamp': row_data['timestamp'].isoformat(),
                    'raw_data': row_data['raw_data'],
                    'calibrated_data': row_data['calibrated_data']
                }
                json_data['data'].append(json_row)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.last_export_filename = filename
            app_logger.info(f"Veri JSON formatında dışa aktarıldı: {filename}")
            return True, filename
            
        except Exception as e:
            app_logger.error(f"JSON dışa aktarma hatası: {e}")
            return False, str(e)
    
    def export_calibration_data(self, calibration_functions: Dict[str, Any],
                               filename: Optional[str] = None) -> Tuple[bool, str]:
        """Kalibrasyon verilerini dışa aktar"""
        try:
            if filename is None:
                filename = generate_filename("calibration_functions", "json")
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'calibration_functions',
                    'version': '1.0'
                },
                'calibration_functions': calibration_functions
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Kalibrasyon verileri dışa aktarıldı: {filename}")
            return True, filename
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon dışa aktarma hatası: {e}")
            return False, str(e)
    
    def import_calibration_data(self, filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Kalibrasyon verilerini içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Formatı kontrol et
            if 'calibration_functions' not in import_data:
                return False, "Geçersiz kalibrasyon dosyası formatı", None
            
            calibration_functions = import_data['calibration_functions']
            
            app_logger.info(f"Kalibrasyon verileri içe aktarıldı: {filename}")
            return True, "Kalibrasyon başarıyla yüklendi", calibration_functions
            
        except Exception as e:
            app_logger.error(f"Kalibrasyon içe aktarma hatası: {e}")
            return False, str(e), None
    
    def create_export_summary(self, export_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export özeti oluştur"""
        if not export_data:
            return {}
        
        try:
            summary = {
                'total_data_points': len(export_data),
                'time_range': {
                    'start': export_data[0]['timestamp'].isoformat(),
                    'end': export_data[-1]['timestamp'].isoformat(),
                    'duration_minutes': (export_data[-1]['timestamp'] - 
                                       export_data[0]['timestamp']).total_seconds() / 60
                },
                'sensors': {}
            }
            
            # Her sensör için özet
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                raw_values = [row['raw_data'].get(sensor_key, 0) for row in export_data]
                cal_values = [row['calibrated_data'].get(sensor_key) for row in export_data 
                            if row['calibrated_data'].get(sensor_key) is not None]
                
                sensor_summary = {
                    'raw_data': {
                        'count': len([v for v in raw_values if v > 0]),
                        'min': min(raw_values) if raw_values else 0,
                        'max': max(raw_values) if raw_values else 0,
                        'mean': sum(raw_values) / len(raw_values) if raw_values else 0
                    }
                }
                
                if cal_values:
                    sensor_summary['calibrated_data'] = {
                        'count': len(cal_values),
                        'min': min(cal_values),
                        'max': max(cal_values),
                        'mean': sum(cal_values) / len(cal_values)
                    }
                
                summary['sensors'][sensor_key] = sensor_summary
            
            return summary
            
        except Exception as e:
            app_logger.error(f"Export özeti oluşturma hatası: {e}")
            return {}
    
    def show_export_success_message(self, filename: str, summary: Optional[Dict[str, Any]] = None):
        """Export başarı mesajını göster"""
        try:
            message = f"Data exported to {filename} in CSV format!"
            
            if summary:
                data_points = summary.get('total_data_points', 0)
                duration = summary.get('time_range', {}).get('duration_minutes', 0)
                message += f"\n\nSummary:\n• {data_points} data points\n• {duration:.1f} minutes duration"
            
            messagebox.showinfo("Success", message)
            
        except Exception as e:
            app_logger.error(f"Export mesaj gösterme hatası: {e}")
    
    def get_last_export_filename(self) -> Optional[str]:
        """Son export dosya ismini al"""
        return self.last_export_filename
