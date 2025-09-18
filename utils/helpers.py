"""
Spektroskopi Sistemi Yardımcı Fonksiyonlar
"""

import struct
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

def convert_raw_to_voltage(raw_value: int) -> float:
    """Ham ADC değerini voltaja çevir"""
    # Raspberry Pi Pico W ADC: 0-65535 -> 0-3.3V
    voltage_mv = raw_value
    return voltage_mv 

def parse_ble_data(data: bytes) -> Optional[int]:
    """BLE verisini parse et"""
    try:
        if len(data) == 2:
            # 16-bit unsigned integer (little-endian)
            return struct.unpack("<H", data)[0]
        else:
            print(f"Beklenmeyen veri uzunluğu: {len(data)}")
            return None
    except Exception as e:
        print(f"BLE veri parse hatası: {e}")
        return None

def format_timestamp(timestamp: datetime, format_type: str = "display") -> str:
    """Zaman damgasını formatla"""
    if format_type == "display":
        return timestamp.strftime('%H:%M:%S')
    elif format_type == "file":
        return timestamp.strftime('%Y%m%d_%H%M%S')
    elif format_type == "csv":
        return timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
    else:
        return timestamp.isoformat()

def calculate_time_difference(start_time: datetime, end_time: datetime) -> float:
    """İki zaman arasındaki farkı milisaniye cinsinden hesapla"""
    return (end_time - start_time).total_seconds() * 1000

def filter_data_by_time_range(timestamps: List[datetime], 
                             data_arrays: Dict[str, List[float]], 
                             range_seconds: int) -> Tuple[List[datetime], Dict[str, List[float]]]:
    """Belirtilen zaman aralığındaki verileri filtrele - sabit referans zamanla"""
    if not timestamps:
        return [], {}
    
    # En son timestamp'i referans al (sabit nokta)
    latest_time = timestamps[-1] if timestamps else datetime.now()
    start_time = latest_time - timedelta(seconds=range_seconds)
    
    # Zaman aralığındaki indeksleri bul
    filtered_indices = []
    for i, timestamp in enumerate(timestamps):
        if timestamp >= start_time:
            filtered_indices.append(i)
    
    if not filtered_indices:
        # Eğer hiç veri yoksa son N veri noktasını al
        max_points = min(len(timestamps), range_seconds * 2)  # Yaklaşık tahmin
        if max_points > 0:
            start_idx = len(timestamps) - max_points
            filtered_timestamps = timestamps[start_idx:]
            filtered_data = {}
            for key, data_list in data_arrays.items():
                if len(data_list) > start_idx:
                    filtered_data[key] = data_list[start_idx:]
                else:
                    filtered_data[key] = []
            return filtered_timestamps, filtered_data
        return [], {}
    
    start_idx = filtered_indices[0]
    
    # Filtrelenmiş verileri oluştur - uzunluk kontrolü
    filtered_timestamps = timestamps[start_idx:]
    filtered_data = {}
    
    for key, data_list in data_arrays.items():
        if len(data_list) > start_idx:
            # Veri uzunluğunu timestamp uzunluğuyla eşitle
            data_slice = data_list[start_idx:]
            min_len = min(len(filtered_timestamps), len(data_slice))
            filtered_data[key] = data_slice[:min_len]
        else:
            filtered_data[key] = []
    
    # Son kontrol: tüm veriler aynı uzunlukta olmalı
    if filtered_timestamps:
        min_length = len(filtered_timestamps)
        for key in filtered_data:
            if len(filtered_data[key]) > min_length:
                filtered_data[key] = filtered_data[key][:min_length]
    
    return filtered_timestamps, filtered_data

def calculate_moving_average(data: List[float], window_size: int = 5) -> List[float]:
    """Hareketli ortalama hesapla"""
    if len(data) < window_size:
        return data.copy()
    
    averaged_data = []
    for i in range(len(data)):
        if i < window_size - 1:
            # İlk değerler için mevcut verilerin ortalamasını al
            avg = sum(data[:i+1]) / (i+1)
        else:
            # Pencere boyutunda ortalama al
            avg = sum(data[i-window_size+1:i+1]) / window_size
        averaged_data.append(avg)
    
    return averaged_data

def validate_calibration_data(concentrations: List[float], 
                            voltages: List[float]) -> Tuple[bool, str]:
    """Kalibrasyon verilerini doğrula"""
    if len(concentrations) != len(voltages):
        return False, "Konsantrasyon ve voltaj listelerinin uzunlukları eşit olmalı"
    
    if len(concentrations) < 3:
        return False, "En az 3 kalibrasyon noktası gerekli"
    
    # Negatif değer kontrolü
    if any(c < 0 for c in concentrations):
        return False, "Konsantrasyon değerleri negatif olamaz"
    
    if any(v < 0 for v in voltages):
        return False, "Voltaj değerleri negatif olamaz"
    
    # Tekrarlanan değer kontrolü
    if len(set(concentrations)) != len(concentrations):
        return False, "Konsantrasyon değerleri benzersiz olmalı"
    
    if len(set(voltages)) != len(voltages):
        return False, "Voltaj değerleri benzersiz olmalı"
    
    return True, "Kalibrasyon verileri geçerli"

def perform_linear_regression(x_values: List[float], 
                            y_values: List[float]) -> Dict[str, float]:
    """Doğrusal regresyon hesapla"""
    if not NUMPY_AVAILABLE:
        # NumPy olmadan basit regresyon
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # R² hesapla
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        y_pred = [slope * x + intercept for x in x_values]
        ss_res = sum((y - y_p) ** 2 for y, y_p in zip(y_values, y_pred))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared)
        }
    else:
        # NumPy ile gelişmiş regresyon
        x = np.array(x_values)
        y = np.array(y_values)
        
        # Doğrusal regresyon katsayıları: y = slope * x + intercept
        A = np.vstack([x, np.ones(len(x))]).T
        coeffs = np.linalg.lstsq(A, y, rcond=None)[0]
        slope, intercept = coeffs
        
        # R² hesapla
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared)
        }

def apply_calibration(raw_value: float, calibration_function: Dict[str, float]) -> float:
    """Kalibrasyon fonksiyonunu uygula"""
    if not calibration_function:
        return raw_value
    
    slope = calibration_function.get('slope', 1.0)
    intercept = calibration_function.get('intercept', 0.0)
    
    calibrated = slope * raw_value + intercept
    return max(0, calibrated)  # Negatif değerleri sıfır yap

def clean_sensor_name(sensor_name: str) -> str:
    """Sensör ismini temizle (grafik etiketleri için)"""
    return sensor_name.replace(" LED", "").split(" (")[0].strip()

def get_sensor_display_name(sensor_key: str, led_names: Dict[str, str]) -> str:
    """Sensör görüntüleme ismini al"""
    led_mapping = {
        'UV_360nm': 'UV LED (360nm)',
        'Blue_450nm': 'Blue LED (450nm)',
        'IR_850nm': 'IR LED (850nm)',
        'IR_940nm': 'IR LED (940nm)'
    }
    
    if sensor_key in led_mapping:
        original_name = led_mapping[sensor_key]
        if original_name in led_names:
            return led_names[original_name]
    
    return sensor_key

def limit_data_points(data_dict: Dict[str, List], max_points: int = 1000):
    """Veri noktalarını sınırla"""
    for key, data_list in data_dict.items():
        if len(data_list) > max_points:
            data_dict[key] = data_list[-max_points:]

def generate_filename(prefix: str, extension: str = "csv") -> str:
    """Zaman damgası ile dosya ismi oluştur"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.{extension}"

def safe_float_conversion(value: str, default: float = 0.0) -> float:
    """Güvenli float dönüşümü"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def format_csv_value(value: float, decimal_places: int = 3) -> str:
    """CSV için değer formatla (Türkçe Excel uyumlu)"""
    formatted = f"{value:.{decimal_places}f}"
    return formatted.replace('.', ',')  # Türkçe Excel için virgül

def extract_device_address(device_string: str) -> str:
    """Cihaz string'inden MAC adresini çıkar"""
    if "(" in device_string and ")" in device_string:
        start = device_string.find("(") + 1
        end = device_string.find(")", start)
        address = device_string[start:end]
        
        # RSSI bilgisini temizle
        if "] [RSSI:" in address:
            address = address.split("] [RSSI:")[0]
        
        return address.strip()
    else:
        return device_string.strip()

def map_device_name(original_name: str) -> str:
    """Cihaz ismini görüntüleme formatına çevir"""
    if original_name == "PicoW-Sensors":
        return "PicoW-Sensors"
    elif original_name.startswith("pico-sensors-"):
        sensor_number = original_name.replace("pico-sensors-", "")
        return f"sensor-{sensor_number}"
    else:
        return original_name
