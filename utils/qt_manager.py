"""
Qt Application Yöneticisi - Global QApplication Kurulumu
"""

import sys
from typing import Optional

try:
    from PyQt5.QtWidgets import QApplication
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    QApplication = None

from utils.logger import app_logger

class QtManager:
    """Qt Application yöneticisi"""
    
    _instance = None
    _qt_app = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QtManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.setup_qt_application()
    
    def setup_qt_application(self):
        """Global QApplication kurulumu"""
        if not QT_AVAILABLE:
            app_logger.warning("Qt kütüphanesi mevcut değil")
            return False
        
        try:
            # Mevcut QApplication var mı kontrol et
            existing_app = QApplication.instance()
            
            if existing_app is None:
                # Yeni QApplication oluştur
                self._qt_app = QApplication(sys.argv)
                app_logger.info("Global QApplication oluşturuldu")
            else:
                # Mevcut QApplication'ı kullan
                self._qt_app = existing_app
                app_logger.info("Mevcut QApplication kullanılıyor")
            
            return True
            
        except Exception as e:
            app_logger.error(f"QApplication kurulum hatası: {e}")
            return False
    
    def get_qt_app(self) -> Optional[QApplication]:
        """QApplication instance'ını al"""
        return self._qt_app
    
    def is_available(self) -> bool:
        """Qt kullanılabilir mi?"""
        return QT_AVAILABLE and self._qt_app is not None
    
    def ensure_qt_app(self) -> bool:
        """QApplication'ın mevcut olduğundan emin ol"""
        if not self.is_available():
            return self.setup_qt_application()
        return True

# Global instance
qt_manager = QtManager()
