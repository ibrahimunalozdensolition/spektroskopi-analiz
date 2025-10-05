#!/usr/bin/env python3
"""
Spektroskopi Uygulaması Otomatik Güncelleme Sistemi
Bu script uygulamanın GitHub'dan otomatik olarak güncellenmesini sağlar.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class AutoUpdater:
    def __init__(self, repo_url="git@github.com:SentralPrime/spektroskopi-analiz.git"):
        self.repo_url = repo_url
        self.project_root = Path(__file__).parent.parent
        self.update_log_file = self.project_root / "logs" / "update_log.json"
        self.last_check_file = self.project_root / "logs" / "last_update_check.json"
        
        # Log dizinini oluştur
        self.update_log_file.parent.mkdir(exist_ok=True)
    
    def log_message(self, message, level="INFO"):
        """Güncelleme mesajlarını logla"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        
        print(f"[{timestamp}] {level}: {message}")
        
        # Log dosyasına yaz
        try:
            if self.update_log_file.exists():
                with open(self.update_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Son 100 log kaydını tut
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(self.update_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Log yazma hatası: {e}")
    
    def should_check_for_updates(self):
        """Son kontrol zamanını kontrol et (günde bir kez)"""
        try:
            if not self.last_check_file.exists():
                return True
            
            with open(self.last_check_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_check = datetime.fromisoformat(data['last_check'])
            now = datetime.now()
            
            # 24 saatten fazla geçmişse güncelleme kontrol et
            return (now - last_check) > timedelta(hours=24)
        except Exception:
            return True
    
    def update_last_check_time(self):
        """Son kontrol zamanını güncelle"""
        try:
            data = {
                "last_check": datetime.now().isoformat(),
                "version": self.get_current_version()
            }
            with open(self.last_check_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log_message(f"Son kontrol zamanı güncellenemedi: {e}", "ERROR")
    
    def get_current_version(self):
        """Mevcut commit hash'ini al"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # İlk 8 karakter
        except Exception:
            pass
        return "unknown"
    
    def check_git_status(self):
        """Git durumunu kontrol et"""
        try:
            # Git repository olup olmadığını kontrol et
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log_message("Bu dizin bir git repository değil", "ERROR")
                return False
            
            # Değişiklik var mı kontrol et
            if result.stdout.strip():
                self.log_message("Yerel değişiklikler tespit edildi, güncelleme atlanıyor", "WARNING")
                return False
            
            return True
        except subprocess.TimeoutExpired:
            self.log_message("Git status komutu zaman aşımına uğradı", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"Git status kontrolü başarısız: {e}", "ERROR")
            return False
    
    def fetch_updates(self):
        """Remote'dan güncellemeleri çek"""
        try:
            self.log_message("Remote güncellemeler kontrol ediliyor...")
            
            result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.log_message(f"Git fetch başarısız: {result.stderr}", "ERROR")
                return False
            
            return True
        except subprocess.TimeoutExpired:
            self.log_message("Git fetch zaman aşımına uğradı", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"Git fetch hatası: {e}", "ERROR")
            return False
    
    def check_for_updates(self):
        """Güncelleme var mı kontrol et"""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log_message(f"Güncelleme kontrolü başarısız: {result.stderr}", "ERROR")
                return False
            
            update_count = int(result.stdout.strip())
            return update_count > 0
        except Exception as e:
            self.log_message(f"Güncelleme kontrol hatası: {e}", "ERROR")
            return False
    
    def apply_updates(self):
        """Güncellemeleri uygula"""
        try:
            self.log_message("Güncellemeler uygulanıyor...")
            
            # Önce stash yap (güvenlik için)
            subprocess.run(
                ["git", "stash", "push", "-m", "Auto-update stash"],
                cwd=self.project_root,
                capture_output=True,
                timeout=10
            )
            
            # Pull yap
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.log_message(f"Git pull başarısız: {result.stderr}", "ERROR")
                return False
            
            self.log_message("Güncellemeler başarıyla uygulandı!", "SUCCESS")
            return True
        except subprocess.TimeoutExpired:
            self.log_message("Git pull zaman aşımına uğradı", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"Güncelleme uygulama hatası: {e}", "ERROR")
            return False
    
    def update_requirements(self):
        """Requirements.txt güncellemelerini kontrol et ve uygula"""
        try:
            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                return True
            
            self.log_message("Python paketleri kontrol ediliyor...")
            
            # Virtual environment aktif mi kontrol et
            if not os.environ.get('VIRTUAL_ENV'):
                self.log_message("Virtual environment aktif değil, paket güncellemesi atlanıyor", "WARNING")
                return True
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.log_message(f"Paket güncellemesi başarısız: {result.stderr}", "WARNING")
                return False
            
            self.log_message("Python paketleri güncellendi", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"Requirements güncelleme hatası: {e}", "WARNING")
            return False
    
    def run_update_check(self, force=False):
        """Ana güncelleme kontrolü"""
        try:
            # Zorla güncelleme değilse ve son kontrol yakınsa atla
            if not force and not self.should_check_for_updates():
                self.log_message("Son güncelleme kontrolü yakın zamanda yapıldı, atlanıyor")
                return True
            
            self.log_message("Otomatik güncelleme kontrolü başlatılıyor...")
            
            # Git durumunu kontrol et
            if not self.check_git_status():
                return False
            
            # Remote'dan güncellemeleri çek
            if not self.fetch_updates():
                return False
            
            # Güncelleme var mı kontrol et
            if not self.check_for_updates():
                self.log_message("Güncelleme bulunamadı, uygulama güncel")
                self.update_last_check_time()
                return True
            
            self.log_message("Yeni güncellemeler bulundu!")
            
            # Güncellemeleri uygula
            if self.apply_updates():
                # Requirements'ı güncelle
                self.update_requirements()
                self.update_last_check_time()
                self.log_message("Tüm güncellemeler başarıyla tamamlandı!", "SUCCESS")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_message(f"Güncelleme süreci hatası: {e}", "ERROR")
            return False

def main():
    """Ana fonksiyon"""
    updater = AutoUpdater()
    
    # Komut satırı argümanlarını kontrol et
    force_update = "--force" in sys.argv
    
    try:
        success = updater.run_update_check(force=force_update)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        updater.log_message("Güncelleme kullanıcı tarafından iptal edildi", "WARNING")
        sys.exit(1)
    except Exception as e:
        updater.log_message(f"Beklenmeyen hata: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
