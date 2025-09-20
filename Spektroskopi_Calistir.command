#!/bin/bash

# Spektroskopi Uygulaması Başlatma Betiği
# MacBook için çift tıklama ile çalıştırma

# Betik dosyasının bulunduğu dizine git
cd "$(dirname "$0")"

# Terminal penceresinin başlığını ayarla
echo -e "\033]0;Spektroskopi Uygulaması\007"

# Başlık göster
echo "=================================================="
echo "      SPEKTROSKOPI UYGULAMASI BAŞLATILIYOR        "
echo "=================================================="
echo ""

# Python3.13 varlığını kontrol et
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 bulunamadı!"
    echo "Python 3.13'ü yüklemek için:"
    echo "brew install python@3.13"
    echo ""
    echo "Devam etmek için herhangi bir tuşa basın..."
    read -n 1
    exit 1
fi

echo "✅ Python 3.13 bulundu: $(python3.13 --version)"

# Virtual environment kontrol et ve oluştur/aktifleştir
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    python3.13 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Virtual environment oluşturulamadı!"
        echo "Devam etmek için herhangi bir tuşa basın..."
        read -n 1
        exit 1
    fi
fi

echo "🔧 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# Pip'i güncelle
echo "🔄 Pip güncelleniyor..."
python3.13 -m pip install --upgrade pip

# Gerekli paketleri yükle
if [ -f "requirements.txt" ]; then
    echo "📋 Gerekli paketler kontrol ediliyor..."
    python3.13 -m pip install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Paket yüklemesi başarısız!"
        echo "Devam etmek için herhangi bir tuşa basın..."
        read -n 1
        exit 1
    fi
    echo "✅ Tüm paketler hazır"
else
    echo "⚠️  requirements.txt bulunamadı, temel paketler yükleniyor..."
    python3.13 -m pip install -q matplotlib numpy scipy pillow bleak python-dateutil PyYAML PyQt5
fi

# Uygulamayı başlat
echo ""
echo "🚀 Spektroskopi uygulaması başlatılıyor..."
echo ""

python3.13 main.py

# Uygulama kapandıktan sonra
echo ""
echo "=================================================="
echo "         UYGULAMA KAPATILDI                       "
echo "=================================================="
echo ""
echo "Pencereyi kapatmak için herhangi bir tuşa basın..."
read -n 1
