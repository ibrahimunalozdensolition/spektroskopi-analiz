  - CPU yoğunluğu artıyor ve GUI thread'i bloklanıyor
  2. BLE BAĞLANTI YÖNETİMİ SORUNLARI

  Sebep: ble_manager.py:154-178 - Async BLE bağlantısı düzgün kapanmıyor
  - _connect_to_device_async fonksiyonunda sonsuz döngü (satır 171-172)
  - BLE bağlantısı kesildiğinde thread'ler temizlenmiyor
  - Otomatik bağlantı taraması 10 saniye sürebiliyor

  3. PYQT SUBPROCESS SORUNLARI

  Sebep: Log'larda PyQt subprocess açma/kapama döngüsü görülüyor
  - "PyQt subprocess kapatıldı: raw_data" → "PyQt subprocess başlatıldı: raw_data"
  - Thread'ler arası iletişim sorunları

  4. GUI GÜNCELLEME SIKIŞMASI

  Sebep: main_window.py:371-379 - Çoklu timer'lar çakışıyor
  - update_data() her 100ms
  - update_plots(), update_sensor_displays(), update_custom_panels() eş zamanlı çalışıyor
  - Tkinter main thread'i aşırı yükleniyor

  ⚠️ İKİNCİL SORUNLAR

  5. BELLEK YÖNETİMİ

  - data_processor.py:136-146 - Büyük veri listeleri sürekli kopyalanıyor
  - measurements, raw_data, calibrated_data dictionary'leri limit kontrolü eksik
  - PyQt grafiklerinde eski veriler temizlenmiyor

  6. TEMA GÜNCELLEMELERİ

  - main_window.py:574-577 - Dark theme widget'lar sürekli güncelleniyor
  - Her 50ms, 150ms'de tema uygulanıyor (gereksiz)

  💡 ÇÖZİM ÖNERİLERİ

  ACIL ÇÖZİM:

  1. Formül hesaplama sıklığını azalt:
    - UPDATE_INTERVAL_MS'yi 100ms'den 1000ms'ye çıkar
    - Formül hesaplamayı sadece yeni veri geldiğinde yap
  2. BLE async döngüsünü düzelt:
    - while self.is_connected: döngüsüne timeout ekle
    - Thread temizleme mekanizması ekle
  3. PyQt subprocess yönetimini iyileştir:
    - Grafik pencerelerini gereksiz kapatma/açma
    - Render thread'lerini optimize et

  ORTA VADELİ ÇÖZİM:

  1. Veri buffer'larda maksimum boyut limiti koy
  2. GUI güncelleme timer'larını senkronize et
  3. Tema uygulamalarını tek sefere indir
  4. Bellek temizleme mekanizması ekle

  UZUN VADELİ ÇÖZİM:

  1. BLE manager'ı async/await pattern'ine tam geç
  2. Veri processing'i ayrı thread'de yap
  3. PyQt grafikleri için connection pooling ekle

  En kritik sorun: Her 100ms'de çalışan formül hesaplama döngüsü. Bu hemen 1000ms'ye çıkarılmalı.

