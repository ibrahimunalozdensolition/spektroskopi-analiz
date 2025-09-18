import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from config.constants import (
    SENSOR_MAPPING, LED_MAPPING, MAX_DATA_POINTS, 
    DATA_BUFFER_SIZE, MAX_MEMORY_BUFFER_SIZE
)
from utils.logger import app_logger, log_data_event
from utils.helpers import limit_data_points, calculate_moving_average

class DataProcessor:
    """Veri işleme sınıfı"""
    
    def __init__(self):
        # Ana veri depoları
        self.measurements = {
            'UV_360nm': [],
            'Blue_450nm': [],
            'IR_850nm': [],
            'IR_940nm': [],
            'timestamps': []
        }
        
        self.raw_data = {
            'UV_360nm': [],
            'Blue_450nm': [],
            'IR_850nm': [],
            'IR_940nm': [],
            'timestamps': []
        }
        
        self.calibrated_data = {
            'UV_360nm': [],
            'Blue_450nm': [],
            'IR_850nm': [],
            'IR_940nm': [],
            'timestamps': []
        }
        
        # Veri buffer (örnekleme için)
        self.data_buffer = {
            'UV_360nm': [],
            'Blue_450nm': [],
            'IR_850nm': [],
            'IR_940nm': [],
            'timestamps': []
        }
        
        # Zamanlama kontrolü
        self.last_output_time = datetime.now()
        self.last_display_time = datetime.now()  # Display için ayrı zaman
        # Sampling rate kaldırıldı - tüm veriler direkt işlenir
        
        # Sistem durumu
        self.system_running = False
        self.system_stopped = True
        
        # Kalibrasyon fonksiyonları (dışarıdan set edilecek)
        self.calibration_functions = {}
        
        # Son sensör değerleri (tüm sensörler için)
        self.last_sensor_values = {
            'UV_360nm': 0.0,
            'Blue_450nm': 0.0,
            'IR_850nm': 0.0,
            'IR_940nm': 0.0
        }
    
    def _cleanup_synchronized_buffers(self):
        try:
            if 'timestamps' not in self.measurements:
                return
                
            current_length = len(self.measurements['timestamps'])
            
            # CPU dostu büyük buffer - 3000 veri noktası limiti
            buffer_limit = 3000
            
            # Sadece limit aşıldığında temizle
            if current_length > buffer_limit:
                keep_size = int(buffer_limit * 0.8)  # 2400 veri noktası tut
                app_logger.info(f"CPU dostu buffer temizleme: {current_length} -> {keep_size} veri noktası")
                
                # Tüm buffer'ları senkronize şekilde temizle
                for key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm', 'timestamps']:
                    if key in self.measurements and len(self.measurements[key]) > keep_size:
                        # Son N veriyi tut - veri sıralaması korunur
                        self.measurements[key] = self.measurements[key][-keep_size:]
                
                # Temizlik sonrası senkronizasyon kontrolü
                self._verify_buffer_synchronization()
                
                # Garbage collection önerisi
                import gc
                gc.collect()
                app_logger.debug("Buffer temizleme tamamlandı, garbage collection çalıştırıldı")
            else:
                # Limit aşılmadı, temizlik yapma (CPU tasarrufu)
                app_logger.debug(f"Buffer temizleme atlandı: {current_length}/{buffer_limit} veri noktası")
                        
        except Exception as e:
            app_logger.error(f"Senkronize buffer temizleme hatası: {e}")
    
    def _verify_buffer_synchronization(self):
        """Buffer senkronizasyonunu doğrula"""
        try:
            lengths = {}
            for key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm', 'timestamps']:
                if key in self.measurements:
                    lengths[key] = len(self.measurements[key])
            
            # Tüm uzunluklar aynı mı?
            unique_lengths = set(lengths.values())
            if len(unique_lengths) > 1:
                app_logger.warning(f"Buffer senkronizasyon hatası: {lengths}")
                # En kısa uzunluğa göre düzelt
                min_length = min(lengths.values())
                for key in lengths.keys():
                    if key in self.measurements:
                        self.measurements[key] = self.measurements[key][-min_length:]
                app_logger.info(f"Buffer senkronizasyonu düzeltildi: {min_length} veri noktası")
            else:
                app_logger.debug(f"Buffer senkronizasyonu OK: {list(unique_lengths)[0]} veri noktası")
                
        except Exception as e:
            app_logger.error(f"Buffer senkronizasyon doğrulama hatası: {e}")
    
    def set_calibration_functions(self, calibration_functions: Dict[str, Dict[str, Any]]):
        """Kalibrasyon fonksiyonlarını ayarla"""
        self.calibration_functions = calibration_functions
    
    # set_sampling_rate fonksiyonu kaldırıldı - tüm veriler direkt işlenir
    
    def set_system_state(self, running: bool):
        """Sistem durumunu ayarla"""
        self.system_running = running
        self.system_stopped = not running
        
        if running:
            # Sistem başladığında buffer'ları temizle
            self.clear_buffers()
            self.last_output_time = datetime.now()
            self.last_display_time = datetime.now()
            app_logger.info("Sistem başlatıldı - veri işleme aktif")
        else:
            app_logger.info("Sistem durduruldu - veri işleme pasif")
    
    def process_incoming_data(self, data_packet: Dict[str, Any]) -> bool:
        """Gelen veri paketini işle"""
        try:
            current_time = data_packet.get('timestamp', datetime.now())
            
            # Sistem durumuna göre işlem yap
            if not self.system_running and self.system_stopped:
                # Sadece real-time display için işle
                return self._process_realtime_display_only(data_packet)
            else:
                # Tam veri işleme
                return self._process_full_data(data_packet)
                
        except Exception as e:
            app_logger.error(f"Veri işleme hatası: {e}")
            return False
    
    def _process_realtime_display_only(self, data_packet: Dict[str, Any]) -> bool:
        """Real-time display için veri işle (tüm veriler direkt işlenir)"""
        try:
            current_time = data_packet.get('timestamp', datetime.now())
            
            # Önce gelen veriyi son değerlere kaydet
            for pi_sensor, gui_sensor in SENSOR_MAPPING.items():
                if pi_sensor in data_packet and data_packet[pi_sensor] > 0:
                    raw_value = data_packet[pi_sensor]
                    self.last_sensor_values[gui_sensor] = raw_value
                    log_data_event(app_logger, f"{pi_sensor}->{gui_sensor}", raw_value, "realtime_update")
            
            for gui_sensor in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                current_value = self.last_sensor_values[gui_sensor]
                self.measurements[gui_sensor].append(current_value)
            
            self._cleanup_synchronized_buffers()
            
            # Tek timestamp ekle
            self.measurements['timestamps'].append(current_time)
            
            # Display zamanını güncelle
            self.last_display_time = current_time
            app_logger.debug(f"Display güncellendi: UV={int(self.last_sensor_values['UV_360nm']):04d}mV, "
                           f"Blue={int(self.last_sensor_values['Blue_450nm']):04d}mV, "
                           f"IR850={int(self.last_sensor_values['IR_850nm']):04d}mV, "
                           f"IR940={int(self.last_sensor_values['IR_940nm']):04d}mV")
            return True
            
        except Exception as e:
            app_logger.error(f"Real-time display işleme hatası: {e}")
            return False
    
    def _process_full_data(self, data_packet: Dict[str, Any]) -> bool:
        """Tam veri işleme (örnekleme ile)"""
        try:
            current_time = data_packet.get('timestamp', datetime.now())
            
            # Gelen veriyi buffer'a ekle
            for pi_sensor, gui_sensor in SENSOR_MAPPING.items():
                if pi_sensor in data_packet and data_packet[pi_sensor] > 0:
                    raw_value = data_packet[pi_sensor]
                    self.data_buffer[gui_sensor].append(raw_value)
            
            # Tüm veriler direkt işlenir - sampling rate kontrolü kaldırıldı
            return self._process_averaged_data(current_time)
            
        except Exception as e:
            app_logger.error(f"Tam veri işleme hatası: {e}")
            return False
    
    def _process_averaged_data(self, current_time: datetime) -> bool:
        """Ortalama alınmış veriyi işle"""
        try:
            app_logger.debug("Veri işleme tamamlandı - sampling rate kontrolü kaldırıldı")
            
            # Her sensör için ortalama hesapla
            for gui_sensor in SENSOR_MAPPING.values():
                if self.data_buffer[gui_sensor]:
                    # Ortalama hesapla
                    avg_raw_value = sum(self.data_buffer[gui_sensor]) / len(self.data_buffer[gui_sensor])
                    buffer_size = len(self.data_buffer[gui_sensor])
                    
                    app_logger.debug(f"{gui_sensor}: {buffer_size} veri noktası ortalaması = {int(avg_raw_value):04d}mV")
                    
                    # Ana veri depolarına ekle
                    self.measurements[gui_sensor].append(avg_raw_value)
                    self.raw_data[gui_sensor].append(avg_raw_value)
                    
                    # Kalibrasyon uygula
                    calibrated_value = self._apply_calibration(gui_sensor, avg_raw_value)
                    self.calibrated_data[gui_sensor].append(calibrated_value)
                    
                    # Buffer'ı temizle
                    self.data_buffer[gui_sensor] = []
                    
                    log_data_event(app_logger, gui_sensor, avg_raw_value, "averaged")
            
            # Zaman damgası ekle
            self.measurements['timestamps'].append(current_time)
            self.raw_data['timestamps'].append(current_time)
            self.calibrated_data['timestamps'].append(current_time)
            
            # Son çıktı zamanını güncelle
            self.last_output_time = current_time
            
            # Veri limitini kontrol et
            self._limit_data_points()
            
            return True
            
        except Exception as e:
            app_logger.error(f"Ortalama veri işleme hatası: {e}")
            return False
    
    def _apply_calibration(self, sensor_key: str, raw_value: float) -> float:
        """Kalibrasyon uygula"""
        if (sensor_key in self.calibration_functions and 
            self.calibration_functions[sensor_key] is not None):
            
            cal_func = self.calibration_functions[sensor_key]
            slope = cal_func.get('slope', 1.0)
            intercept = cal_func.get('intercept', 0.0)
            
            calibrated = slope * raw_value + intercept
            return max(0, calibrated)  # Negatif değerleri sıfır yap
        else:
            return raw_value  # Kalibrasyon yoksa ham değeri döndür
    
    def _limit_data_points(self):
        """Veri noktalarını sınırla - bellek yönetimi iyileştirmesi"""
        for data_store in [self.measurements, self.raw_data, self.calibrated_data]:
            # Her data store için bellek limiti kontrolü
            for key, data_list in data_store.items():
                if isinstance(data_list, list) and len(data_list) > MAX_MEMORY_BUFFER_SIZE:
                    # Yarı yarıya azalt - bellek sızıntısını önle
                    data_store[key] = data_list[-(MAX_MEMORY_BUFFER_SIZE//2):]
                    app_logger.debug(f"Bellek yönetimi: {key} buffer'ı {len(data_list)}'dan {len(data_store[key])}'e düşürüldü")
            
            # Eski limit fonksiyonunu da çalıştır
            limit_data_points(data_store, MAX_DATA_POINTS)
    
    def clear_buffers(self):
        """Veri buffer'larını temizle"""
        for sensor in self.data_buffer:
            self.data_buffer[sensor] = []
        app_logger.info("Veri buffer'ları temizlendi")
    
    def clear_all_data(self):
        """Tüm verileri temizle"""
        for data_store in [self.measurements, self.raw_data, self.calibrated_data, self.data_buffer]:
            for key in data_store:
                data_store[key] = []
        
        app_logger.info("Tüm veriler temizlendi")
    
    def get_measurements(self) -> Dict[str, List]:
        """Ölçüm verilerini al"""
        return self.measurements.copy()
    
    def get_raw_data(self) -> Dict[str, List]:
        """Ham verileri al"""
        return self.raw_data.copy()
    
    def get_calibrated_data(self) -> Dict[str, List]:
        """Kalibre edilmiş verileri al"""
        return self.calibrated_data.copy()
    
    def get_latest_values(self) -> Dict[str, float]:
        """En son değerleri al (tüm sensörler için)"""
        # Önce son sensör değerlerini döndür (daha güncel)
        latest_values = self.last_sensor_values.copy()
        
        # Eğer measurements'ta daha yeni veri varsa onu kullan
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            if sensor_key in self.measurements and self.measurements[sensor_key]:
                measurement_value = self.measurements[sensor_key][-1]
                # Son ölçüm değeri varsa onu kullan
                if measurement_value > 0:
                    latest_values[sensor_key] = measurement_value
        
        return latest_values
    
    def get_latest_calibrated_values(self) -> Dict[str, float]:
        """En son kalibre edilmiş değerleri al"""
        latest_values = {}
        
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            if sensor_key in self.calibrated_data and self.calibrated_data[sensor_key]:
                latest_values[sensor_key] = self.calibrated_data[sensor_key][-1]
            else:
                latest_values[sensor_key] = 0.0
        
        return latest_values
    
    def get_spectrum_intensities(self, average_points: int = 10) -> List[float]:
        """Spektrum analizi için yoğunluk değerlerini al"""
        intensities = []
        
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            if sensor_key in self.measurements and self.measurements[sensor_key]:
                # Son N ölçümün ortalamasını al
                recent_data = self.measurements[sensor_key][-average_points:]
                if NUMPY_AVAILABLE and np:
                    intensity = np.mean(recent_data) if recent_data else 0.0
                else:
                    intensity = sum(recent_data) / len(recent_data) if recent_data else 0.0
                intensities.append(intensity)
            else:
                intensities.append(0.0)
        
        return intensities
    
    def get_data_statistics(self) -> Dict[str, Dict[str, float]]:
        """Veri istatistiklerini al"""
        stats = {}
        
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            if sensor_key in self.measurements and self.measurements[sensor_key]:
                data = self.measurements[sensor_key]
                if NUMPY_AVAILABLE and np:
                    data_array = np.array(data)
                    stats[sensor_key] = {
                        'count': len(data),
                        'mean': float(np.mean(data_array)),
                        'std': float(np.std(data_array)),
                        'min': float(np.min(data_array)),
                        'max': float(np.max(data_array)),
                        'latest': float(data[-1]) if len(data) > 0 else 0.0
                    }
                else:
                    # NumPy olmadan basit istatistik
                    stats[sensor_key] = {
                        'count': len(data),
                        'mean': sum(data) / len(data) if data else 0.0,
                        'std': 0.0,  # Standart sapma hesabı karmaşık
                        'min': min(data) if data else 0.0,
                        'max': max(data) if data else 0.0,
                        'latest': data[-1] if data else 0.0
                    }
            else:
                stats[sensor_key] = {
                    'count': 0,
                    'mean': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'latest': 0.0
                }
        
        return stats
    
    def apply_smoothing(self, sensor_key: str, window_size: int = 5) -> List[float]:
        """Veri düzgünleştirme uygula"""
        if sensor_key in self.measurements and self.measurements[sensor_key]:
            return calculate_moving_average(self.measurements[sensor_key], window_size)
        else:
            return []
    
    def get_data_in_time_range(self, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """Belirtilen zaman aralığındaki verileri al"""
        if not self.measurements['timestamps']:
            return {}
        
        # Zaman aralığındaki indeksleri bul
        filtered_indices = []
        for i, timestamp in enumerate(self.measurements['timestamps']):
            if start_time <= timestamp <= end_time:
                filtered_indices.append(i)
        
        if not filtered_indices:
            return {}
        
        # Filtrelenmiş verileri oluştur
        filtered_data = {}
        
        for key in self.measurements:
            if key == 'timestamps':
                filtered_data[key] = [self.measurements[key][i] for i in filtered_indices]
            else:
                filtered_data[key] = [self.measurements[key][i] for i in filtered_indices 
                                    if i < len(self.measurements[key])]
        
        return filtered_data
    
    def get_active_sensors_from_data(self, data_packet: Dict[str, Any]) -> List[str]:
        """Veri paketinden aktif sensörleri belirle"""
        active_sensors = []
        
        for pi_sensor, value in data_packet.items():
            if pi_sensor.startswith('sensor_') and value > 0:
                active_sensors.append(pi_sensor)
        
        return active_sensors
    
    def get_led_status_from_data(self, data_packet: Dict[str, Any]) -> Dict[str, bool]:
        """Veri paketinden LED durumlarını belirle"""
        led_status = {}
        active_sensors = self.get_active_sensors_from_data(data_packet)
        
        # Tüm LED'leri kapalı olarak başlat
        for led_name in LED_MAPPING.values():
            led_status[led_name] = False
        
        # Aktif sensörlerin LED'lerini aç
        for sensor in active_sensors:
            if sensor in LED_MAPPING:
                led_name = LED_MAPPING[sensor]
                led_status[led_name] = True
        
        return led_status
    
    def has_data(self) -> bool:
        """Veri var mı?"""
        return len(self.measurements['timestamps']) > 0
    
    def get_data_count(self) -> int:
        """Toplam veri sayısını al"""
        return len(self.measurements['timestamps'])
    
    def get_buffer_status(self) -> Dict[str, int]:
        """Buffer durumunu al"""
        return {sensor: len(data_list) for sensor, data_list in self.data_buffer.items()}
    
    def export_data_for_csv(self) -> List[Dict[str, Any]]:
        """CSV export için veri hazırla"""
        export_data = []
        
        if not self.measurements['timestamps']:
            return export_data
        
        for i in range(len(self.measurements['timestamps'])):
            row = {
                'timestamp': self.measurements['timestamps'][i],
                'raw_data': {},
                'calibrated_data': {}
            }
            
            # Ham veri
            for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
                if i < len(self.raw_data[sensor_key]):
                    row['raw_data'][sensor_key] = self.raw_data[sensor_key][i]
                else:
                    row['raw_data'][sensor_key] = 0.0
                
                # Kalibre edilmiş veri (sadece kalibrasyon varsa)
                if (sensor_key in self.calibration_functions and 
                    self.calibration_functions[sensor_key] is not None and
                    i < len(self.calibrated_data[sensor_key])):
                    row['calibrated_data'][sensor_key] = self.calibrated_data[sensor_key][i]
                else:
                    row['calibrated_data'][sensor_key] = None
            
            export_data.append(row)
        
        return export_data
    
    def get_calibration_status(self) -> Dict[str, bool]:
        """Kalibrasyon durumunu al"""
        status = {}
        
        for sensor_key in ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']:
            status[sensor_key] = (sensor_key in self.calibration_functions and 
                                self.calibration_functions[sensor_key] is not None)
        
        return status
