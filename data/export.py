import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from tkinter import messagebox

from utils.logger import app_logger
from utils.helpers import format_csv_value, generate_filename

class DataExporter:
    """Veri dışa aktarma sınıfı"""
    
    def __init__(self):
        self.last_export_filename = None
    
    def export_to_csv(self, export_data: List[Dict[str, Any]], 
                     filename: Optional[str] = None,
                     excel_compatible: bool = True) -> Tuple[bool, str]:
        """Verileri CSV formatında dışa aktar"""
        try:
            if not export_data:
                return False, "Dışa aktarılacak veri yok"
            
            if filename is None:
                filename = generate_filename("spectroscopy_export", "csv")
            
            # Excel uyumluluğu için encoding ve delimiter
            encoding = 'utf-8-sig' if excel_compatible else 'utf-8'
            delimiter = ';' if excel_compatible else ','
            
            with open(filename, 'w', encoding=encoding, newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Header row
                headers = [
                    'Time',
                    'UV Detector (Raw V)', 'UV Detector (Cal)',
                    'Blue Detector (Raw V)', 'Blue Detector (Cal)', 
                    'IR Detector 1 (Raw V)', 'IR Detector 1 (Cal)',
                    'IR Detector 2 (Raw V)', 'IR Detector 2 (Cal)'
                ]
                writer.writerow(headers)
                
                # Data rows
                for row_data in export_data:
                    timestamp = row_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
                    raw_data = row_data['raw_data']
                    cal_data = row_data['calibrated_data']
                    
                    # Format values for Excel compatibility
                    def format_value(value, is_calibrated=False):
                        if value is None or (is_calibrated and value is None):
                            return ""
                        return format_csv_value(value) if excel_compatible else f"{value:.3f}"
                    
                    csv_row = [
                        timestamp,
                        format_value(raw_data.get('UV_360nm', 0)),
                        format_value(cal_data.get('UV_360nm'), True),
                        format_value(raw_data.get('Blue_450nm', 0)),
                        format_value(cal_data.get('Blue_450nm'), True),
                        format_value(raw_data.get('IR_850nm', 0)),
                        format_value(cal_data.get('IR_850nm'), True),
                        format_value(raw_data.get('IR_940nm', 0)),
                        format_value(cal_data.get('IR_940nm'), True)
                    ]
                    
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
                filename = generate_filename("spectroscopy_export", "json")
            
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
