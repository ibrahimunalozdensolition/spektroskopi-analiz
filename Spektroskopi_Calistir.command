#!/bin/bash

# Spektroskopi Uygulaması Başlatma Betiği
# MacBook için çift tıklama ile çalıştırma

# Betik dosyasının bulunduğu dizine git
cd "$(dirname "$0")"

# Dosya izinlerini kontrol et ve gerekirse düzelt
SCRIPT_PATH="$(realpath "$0")"
if [ ! -x "$SCRIPT_PATH" ]; then
    echo "🔧 Dosya izinleri düzeltiliyor..."
    chmod +x "$SCRIPT_PATH"
    if [ $? -eq 0 ]; then
        echo "✅ İzinler başarıyla ayarlandı"
        echo "🔄 Betik yeniden başlatılıyor..."
        exec "$SCRIPT_PATH"
    else
        echo "❌ İzin ayarlama başarısız! Manuel olarak şu komutu çalıştırın:"
        echo "chmod +x '$SCRIPT_PATH'"
        echo ""
        echo "Devam etmek için herhangi bir tuşa basın..."
        read -n 1
        exit 1
    fi
fi

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

# Git varlığını kontrol et
if ! command -v git &> /dev/null; then
    echo "⚠️  Git bulunamadı! Güncelleme kontrolü atlanıyor..."
else
    echo "🔍 Güncelleme kontrol ediliyor..."
    
    # Git repository olup olmadığını kontrol et
    if [ -d ".git" ]; then
        # Mevcut branch'i al
        CURRENT_BRANCH=$(git branch --show-current)
        echo "📍 Mevcut branch: $CURRENT_BRANCH"
        
        # Remote'dan son değişiklikleri getir
        echo "📡 GitHub'dan güncellemeler kontrol ediliyor..."
        git fetch origin $CURRENT_BRANCH --quiet
        
        # Local ve remote arasındaki farkı kontrol et
        LOCAL_COMMIT=$(git rev-parse HEAD)
        REMOTE_COMMIT=$(git rev-parse origin/$CURRENT_BRANCH)
        
        if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
            echo ""
            echo "🆕 YENİ GÜNCELLEME BULUNDU!"
            echo "=================================================="
            
            # Değişiklikleri göster
            echo "📋 Güncellemeler:"
            git log --oneline $LOCAL_COMMIT..$REMOTE_COMMIT | head -5
            echo ""
            
            # Kullanıcıya sor
            echo "Güncellemeleri şimdi yüklemek istiyor musunuz? (y/n)"
            read -n 1 -r UPDATE_CHOICE
            echo ""
            
            if [[ $UPDATE_CHOICE =~ ^[Yy]$ ]]; then
                echo "⬇️  Güncellemeler indiriliyor..."
                
                # Değişiklikleri stash'le (eğer varsa)
                if ! git diff --quiet; then
                    echo "💾 Yerel değişiklikler geçici olarak kaydediliyor..."
                    git stash push -m "Auto-stash before update $(date)"
                fi
                
                # Güncellemeleri çek
                git pull origin $CURRENT_BRANCH --quiet
                
                if [ $? -eq 0 ]; then
                    echo "✅ Güncellemeler başarıyla yüklendi!"
                    
                    # Stash'lenmiş değişiklikler varsa geri yükle
                    if git stash list | grep -q "Auto-stash before update"; then
                        echo "🔄 Yerel değişiklikler geri yükleniyor..."
                        git stash pop --quiet
                    fi
                    
                    echo "🔄 Uygulama yeniden başlatılıyor..."
                    echo ""
                    exec "$SCRIPT_PATH"
                else
                    echo "❌ Güncelleme sırasında hata oluştu!"
                    echo "Manuel olarak 'git pull origin $CURRENT_BRANCH' komutunu çalıştırın."
                fi
            else
                echo "⏭️  Güncellemeler atlandı. Uygulama mevcut sürümle başlatılıyor..."
            fi
            echo ""
        else
            echo "✅ Uygulama güncel!"
        fi
    else
        echo "⚠️  Git repository bulunamadı. Güncelleme kontrolü atlanıyor..."
    fi
fi
echo ""

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
