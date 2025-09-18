"""
Spektroskopi Sistemi Loglama Modülü
"""

import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(name: str = "spektroskopi", 
                log_level: int = logging.INFO,
                log_to_file: bool = True,
                log_to_console: bool = True) -> logging.Logger:
    """Logger kurulumu"""
    
    # Logger oluştur
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Eğer handler'lar zaten eklenmişse, tekrar ekleme
    if logger.handlers:
        return logger
    
    # Formatter oluştur
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        # Log dizinini oluştur
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Log dosya ismi
        log_filename = os.path.join(log_dir, f"spektroskopi_{datetime.now().strftime('%Y%m%d')}.log")
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """Hata loglama yardımcı fonksiyonu"""
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)

def log_system_event(logger: logging.Logger, event: str, details: Optional[str] = None):
    """Sistem olayı loglama"""
    msg = f"SYSTEM EVENT: {event}"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def log_data_event(logger: logging.Logger, sensor: str, value: float, event_type: str = "measurement"):
    """Veri olayı loglama"""
    logger.debug(f"DATA {event_type.upper()}: {sensor} = {value:.3f}V")

def log_calibration_event(logger: logging.Logger, sensor: str, action: str, details: Optional[str] = None):
    """Kalibrasyon olayı loglama"""
    msg = f"CALIBRATION: {sensor} - {action}"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def log_connection_event(logger: logging.Logger, device: str, action: str, success: bool = True):
    """Bağlantı olayı loglama"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"CONNECTION {status}: {device} - {action}")

# Global logger instance
app_logger = setup_logger()
