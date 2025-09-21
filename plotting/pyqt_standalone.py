#!/usr/bin/env python3
"""
Standalone PyQt Grafik Penceresi - Tkinter'dan ayrı process'te çalışır
"""

import sys
import json
import time
import os
from datetime import datetime
from typing import Dict, List

try:
    import pyqtgraph as pg
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QLabel
    from PyQt5.QtCore import QTimer
    from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
    PYQT_AVAILABLE = True
except ImportError:
    print("PyQt5 veya PyQtGraph yüklü değil!")
    sys.exit(1)

class StandalonePlotWindow:
    """Standalone PyQt grafik penceresi"""
    
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.main_widget = None
        self.plot_widget = None
        self.plot_curves = {}
        self.update_timer = None

        # Başlangıç verilerini yükle
        self.load_initial_data()

        # Grafik penceresi oluştur
        self.setup_plot_window()

        # Güncelleme timer'ı başlat
        self.setup_update_timer()
    
    def load_initial_data(self):
        """Başlangıç verilerini yükle"""
        try:
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
            
            self.window_id = data.get('window_id', 'unknown')
            self.selected_sensors = data.get('selected_sensors', [])
            self.title = data.get('title', 'PyQt Graph')
            self.graph_type = data.get('graph_type', 'line')
            
            print(f"Başlangıç verileri yüklendi: {self.title}")
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.selected_sensors = []
            self.title = "PyQt Graph"
    
    def setup_plot_window(self):
        """Grafik penceresini kur"""
        try:
            # Ana widget oluştur
            self.main_widget = QWidget()
            layout = QVBoxLayout(self.main_widget)

            # Üst başlık ekle
            self.create_main_title(layout)

            # LED Renk Göstergesi
            self.create_led_legend(layout)

            # Plot widget oluştur
            self.plot_widget = pg.PlotWidget()

            # Grafik ayarları - Y ekseni formatını belirle
            if "Calibrated" in self.title:
                self.plot_widget.setLabel('left', 'Calibrated Value (N/A if no calibration)')
            else:
                self.plot_widget.setLabel('left', 'Voltage (mV)')
            
            self.plot_widget.setLabel('bottom', 'Time (seconds)')
            # Title'ı kaldırdık, üstte büyük başlık var
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
            self.plot_widget.enableAutoRange()
            self.plot_widget.setMouseEnabled(x=True, y=True)

            # Sensörler için curves oluştur - Beyaz, Mavi, Kırmızı, Yeşil
            colors = ['#FFFFFF', '#0066FF', '#FF0000', '#00CC00']  # Beyaz, Mavi, Kırmızı, Yeşil
            for i, sensor_key in enumerate(self.selected_sensors):
                color = colors[i % len(colors)]
                curve = self.plot_widget.plot(
                    [], [],
                    pen=pg.mkPen(color=color, width=3),  # Çizgi kalınlığını artırdık
                    name=sensor_key
                )
                self.plot_curves[sensor_key] = curve

            # Plot widget'ı layout'a ekle
            layout.addWidget(self.plot_widget)

            # Legend ekle
            if self.selected_sensors:
                self.plot_widget.addLegend()

            # Ana widget'ı göster
            self.main_widget.show()
            self.main_widget.resize(950, 700)
            
            # Pencere başlığını ayarla
            if "Raw Data" in self.title:
                window_title = "Spektroskopi - Raw Data Visualization"
            elif "Calibrated Data" in self.title:
                window_title = "Spektroskopi - Calibrated Data Visualization"
            else:
                window_title = f"Spektroskopi - {self.title}"
            
            self.main_widget.setWindowTitle(window_title)

            print(f"PyQt grafik penceresi oluşturuldu: {self.title}")

        except Exception as e:
            print(f"Grafik penceresi kurulum hatası: {e}")

    def create_main_title(self, layout):
        """Ana başlığı oluştur"""
        try:
            # Başlık widget'ı
            title_widget = QWidget()
            title_layout = QHBoxLayout(title_widget)
            title_layout.setContentsMargins(10, 10, 10, 5)
            
            # Başlık metnini belirle
            if "Raw Data" in self.title:
                title_text = "📊 Raw Data"
                title_color = "#FF6B6B"  # Kırmızı
            elif "Calibrated Data" in self.title:
                title_text = "📈 Calibrated Data"
                title_color = "#4ECDC4"  # Turkuaz
            else:
                title_text = f"📊 {self.title}"
                title_color = "#333333"  # Koyu gri
            
            # Başlık etiketi
            main_title = QLabel(title_text)
            main_title.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {title_color};
                    padding: 5px 10px;
                    border: 2px solid {title_color};
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.9);
                }}
            """)
            
            title_layout.addWidget(main_title)
            title_layout.addStretch()  # Sola yasla
            
            # Layout'a ekle
            layout.addWidget(title_widget)
            
        except Exception as e:
            print(f"Ana başlık oluşturma hatası: {e}")

    def create_led_legend(self, layout):
        """LED renk göstergesini oluştur"""
        try:
            # LED renk mapping - Beyaz, Mavi, Kırmızı, Yeşil
            led_info = {
                'UV_360nm': ('UV LED (360nm)', '#FFFFFF'),    # Beyaz
                'Blue_450nm': ('Blue LED (450nm)', '#0066FF'), # Mavi
                'IR_850nm': ('IR LED (850nm)', '#FF0000'),     # Kırmızı
                'IR_940nm': ('IR LED (940nm)', '#00CC00')      # Yeşil
            }

            # Legend container
            legend_widget = QWidget()
            legend_layout = QHBoxLayout(legend_widget)
            legend_layout.setContentsMargins(10, 5, 10, 5)

            # Başlık
            title_label = QLabel("LED Color Legend:")
            title_label.setStyleSheet("font-weight: bold; margin-right: 10px;")
            legend_layout.addWidget(title_label)

            # Her LED için renk kutusu ve etiket
            for sensor_key in self.selected_sensors:
                if sensor_key in led_info:
                    led_name, color_hex = led_info[sensor_key]

                    # Renk kutusu
                    color_label = QLabel("█")
                    if color_hex == '#FFFFFF':  # Beyaz renk için border ekle
                        color_label.setStyleSheet(f"color: {color_hex}; font-size: 20px; margin-right: 3px; border: 1px solid #333333;")
                    else:
                        color_label.setStyleSheet(f"color: {color_hex}; font-size: 20px; margin-right: 3px;")
                    legend_layout.addWidget(color_label)

                    # LED adı
                    name_label = QLabel(led_name)
                    name_label.setStyleSheet("margin-right: 15px;")
                    legend_layout.addWidget(name_label)

            # Spacer
            legend_layout.addStretch()

            # Legend'ı layout'a ekle
            layout.addWidget(legend_widget)

        except Exception as e:
            print(f"LED legend oluşturma hatası: {e}")
    
    def setup_update_timer(self):
        """Güncelleme timer'ını kur"""
        try:
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_data)
            self.update_timer.start(500)  # 500ms'de bir güncelle
            
            print("Güncelleme timer'ı başlatıldı")
            
        except Exception as e:
            print(f"Timer kurulum hatası: {e}")
    
    def update_data(self):
        """Veri dosyasından güncel verileri yükle ve grafiği güncelle"""
        try:
            if not os.path.exists(self.data_file_path):
                return
            
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
            
            if 'timestamps' in data and 'data' in data:
                timestamps_iso = data['timestamps']
                sensor_data = data['data']
                
                print(f"Veri güncelleme: {len(timestamps_iso)} zaman noktası, {len(sensor_data)} sensör")
                print(f"Gelen sensör anahtarları: {list(sensor_data.keys())}")
                print(f"Beklenen sensörler: {self.selected_sensors}")
                
                # Zaman verilerini datetime'a çevir
                if timestamps_iso and sensor_data:
                    timestamps = [datetime.fromisoformat(t) for t in timestamps_iso]
                    
                    # Zaman sıralaması kontrolü - geriye giden zamanları düzelt
                    sorted_timestamps = []
                    last_time = None
                    
                    for t in timestamps:
                        if last_time is None:
                            sorted_timestamps.append(t)
                            last_time = t
                        elif t >= last_time:
                            sorted_timestamps.append(t)
                            last_time = t
                        else:
                            # Geriye giden zaman - son zamandan 1ms sonra ayarla
                            corrected_time = last_time + timedelta(milliseconds=1)
                            sorted_timestamps.append(corrected_time)
                            last_time = corrected_time
                            print(f"Zaman sıralama düzeltildi: {t} -> {corrected_time}")
                    
                    # Zaman verilerini saniye cinsine çevir
                    if len(sorted_timestamps) > 0:
                        start_time = sorted_timestamps[0]
                        time_seconds = [(t - start_time).total_seconds() for t in sorted_timestamps]
                        
                        # Her sensör için veriyi güncelle
                        for sensor_key in self.selected_sensors:
                            if sensor_key in sensor_data:
                                if sensor_key in self.plot_curves:
                                    sensor_values = sensor_data[sensor_key]
                                    
                                    # Veri formatını kontrol et ve işle
                                    processed_values = []
                                    for value in sensor_values:
                                        if "Calibrated" in self.title:
                                            # Calibrated data için N/A kontrolü
                                            if value is None or (isinstance(value, (int, float)) and value == 0):
                                                processed_values.append(float('nan'))  # N/A için NaN kullan
                                            else:
                                                processed_values.append(float(value))
                                        else:
                                            # Raw data için mV formatı (4 haneli)
                                            if isinstance(value, (int, float)):
                                                processed_values.append(max(0, min(9999, int(value))))
                                            else:
                                                processed_values.append(0)
                                    
                                    # Veri uzunluklarını eşitle
                                    min_len = min(len(time_seconds), len(processed_values))
                                    if min_len > 0:
                                        self.plot_curves[sensor_key].setData(
                                            time_seconds[:min_len], 
                                            processed_values[:min_len]
                                        )
                                        print(f"Sensör güncellendi: {sensor_key}, {min_len} nokta")
                                else:
                                    print(f"Plot curve bulunamadı: {sensor_key}")
                            else:
                                print(f"Sensör verisi bulunamadı: {sensor_key}")
            
        except Exception as e:
            print(f"Veri güncelleme hatası: {e}")

def main():
    """Ana fonksiyon"""
    if len(sys.argv) != 2:
        print("Kullanım: python3 pyqt_standalone.py <data_file_path>")
        sys.exit(1)
    
    data_file_path = sys.argv[1]
    
    # QApplication oluştur
    app = QApplication(sys.argv)
    
    # Grafik penceresi oluştur
    window = StandalonePlotWindow(data_file_path)
    
    # Uygulama döngüsünü başlat
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
