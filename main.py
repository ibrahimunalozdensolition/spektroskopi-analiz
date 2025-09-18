#!/usr/bin/env python3
"""
Spektroskopi Sistemi Ana Başlatma Dosyası
Prof. Dr. Uğur AKSU'ya aittir.
Geliştirici: İbrahim ÜNAL
"""

import tkinter as tk
import sys
import os

# Proje kök dizinini Python path'ine ekle
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.main_window import SpektroskpiGUI
from utils.logger import setup_logger

def show_copyright_dialog():
    """Copyright bilgilerini gösteren splash screen"""
    splash_root = tk.Tk()
    splash_root.title("Spektroskopi")
    splash_root.geometry("800x600")
    splash_root.resizable(False, False)
    splash_root.configure(bg='black')
    
    # Pencereyi merkeze al
    splash_root.update_idletasks()
    x = (splash_root.winfo_screenwidth() // 2) - (800 // 2)
    y = (splash_root.winfo_screenheight() // 2) - (600 // 2)
    splash_root.geometry(f"800x600+{x}+{y}")
    
    # Ana container
    container = tk.Frame(splash_root, bg='black')
    container.pack(fill='both', expand=True, padx=50, pady=50)
    
    # Başlık alanı
    title_frame = tk.Frame(container, bg='black')
    title_frame.pack(fill='x', pady=(0, 40))
    
    title_label = tk.Label(title_frame, text="SPECTROSCOPY SYSTEM", 
                          font=('Arial', 24, 'bold'), bg='black', fg='white')
    title_label.pack()
    
    subtitle_label = tk.Label(title_frame, text="Advanced Spectral Analysis Software", 
                             font=('Arial', 14, 'italic'), bg='black', fg='#cccccc')
    subtitle_label.pack(pady=(5, 0))
    
    # İçerik alanı
    content_frame = tk.Frame(container, bg='black')
    content_frame.pack(fill='both', expand=True, pady=(0, 40))
    
    # Sahiplik bilgisi
    owner_label = tk.Label(content_frame, text="This application belongs to Prof. Dr. Ugur Aksu", 
                          font=('Arial', 16, 'bold'), bg='black', fg='white')
    owner_label.pack(pady=(20, 30))
    
    # Geliştirici bilgisi
    
    
    # Ayırıcı çizgi
    separator = tk.Frame(content_frame, height=2, bg='#333333')
    separator.pack(fill='x', pady=20)
    
    # Copyright ve haklar
    rights_text = """All rights reserved
Unauthorized copying, distribution or modification of this software is prohibited"""
    
    rights_label = tk.Label(content_frame, text=rights_text, 
                           font=('Arial', 12), bg='black', fg='#cccccc',
                           justify='center')
    rights_label.pack(pady=(0, 20))
    
    copyright_label = tk.Label(content_frame, text="© 2025 All rights reserved", 
                              font=('Arial', 11, 'bold'), bg='black', fg='white')
    copyright_label.pack()
    
    # Buton alanı
    button_frame = tk.Frame(container, bg='black')
    button_frame.pack(fill='x')
    
    def close_splash():
        splash_root.destroy()
        start_main_application()
    
    # OK butonu
    ok_button = tk.Button(button_frame, text="OK", 
                         font=('Arial', 16, 'bold'),
                         bg='white', fg='black',
                         width=15, height=2,
                         relief='flat',
                         cursor='hand2',
                         command=close_splash)
    ok_button.pack(pady=20)
    
    # Hover efekti
    def on_enter(e):
        ok_button.configure(bg='#f0f0f0')
    
    def on_leave(e):
        ok_button.configure(bg='white')
    
    ok_button.bind("<Enter>", on_enter)
    ok_button.bind("<Leave>", on_leave)
    
    # Enter tuşu ile de kapatılabilsin
    splash_root.bind('<Return>', lambda e: close_splash())
    splash_root.focus_set()
    
    # Pencereyi en üstte tut
    splash_root.attributes('-topmost', True)
    
    splash_root.mainloop()

def start_main_application():
    """Ana uygulamayı başlat"""
    try:
        # Logger'ı başlat
        logger = setup_logger()
        logger.info("Spektroskopi uygulaması başlatılıyor...")
        
        # Ana Tkinter root penceresi oluştur
        root = tk.Tk()
        
        # Ana GUI uygulamasını başlat
        app = SpektroskpiGUI(root)
        
        # Uygulama döngüsünü başlat
        root.mainloop()
        
    except Exception as e:
        print(f"Uygulama başlatma hatası: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Ana giriş noktası"""
    # Copyright dialog'unu göster
    show_copyright_dialog()

if __name__ == "__main__":
    main()
