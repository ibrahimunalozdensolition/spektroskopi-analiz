#!/bin/bash

# Spektroskopi Uygulaması Manuel Güncelleme Betiği
# Bu script uygulamayı manuel olarak günceller

# Betik dosyasının bulunduğu dizine git
cd "$(dirname "$0")"

# Terminal penceresinin başlığını ayarla
echo -e "\033]0;Spektroskopi Güncelleme\007"

# Başlık göster
echo "=================================================="
echo "      SPEKTROSKOPI UYGULAMASI GÜNCELLENİYOR       "
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

# Virtual environment kontrol et ve aktifleştir
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment bulunamadı!"
    echo "Önce ana uygulamayı çalıştırın: ./Spektroskopi_Calistir.command"
    echo ""
    echo "Devam etmek için herhangi bir tuşa basın..."
    read -n 1
    exit 1
fi

echo "🔧 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# Zorla güncelleme yap
echo "🔄 Zorla güncelleme başlatılıyor..."
python3.13 utils/auto_updater.py --force

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "         GÜNCELLEME BAŞARIYLA TAMAMLANDI          "
    echo "=================================================="
    echo ""
    echo "Artık uygulamayı çalıştırabilirsiniz:"
    echo "./Spektroskopi_Calistir.command"
else
    echo ""
    echo "=================================================="
    echo "           GÜNCELLEME BAŞARISIZ OLDU              "
    echo "=================================================="
    echo ""
    echo "Lütfen log dosyalarını kontrol edin:"
    echo "logs/update_log.json"
fi

echo ""
echo "Pencereyi kapatmak için herhangi bir tuşa basın..."
read -n 1
