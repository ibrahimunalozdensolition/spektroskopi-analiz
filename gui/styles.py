from tkinter import ttk
from typing import Dict

class StyleManager:    
    def __init__(self):
        self.style = ttk.Style()
        self.setup_styles()
    
    def setup_styles(self):
        self.setup_button_styles()
        self.setup_label_styles()
        self.setup_frame_styles()
    
    def setup_button_styles(self):
        self.style.configure("Green.TButton", 
                           foreground="white", 
                           background="green",
                           font=("Arial", 10, "bold"))
        
        self.style.configure("Red.TButton", 
                           foreground="white", 
                           background="red",
                           font=("Arial", 10, "bold"))
        
        self.style.configure("Blue.TButton", 
                           foreground="white", 
                           background="blue",
                           font=("Arial", 10, "bold"))
        self.style.configure("Orange.TButton", 
                           foreground="white", 
                           background="orange",
                           font=("Arial", 10, "bold"))
        
        self.style.configure("Purple.TButton", 
                           foreground="white", 
                           background="purple",
                           font=("Arial", 10, "bold"))
        
        self.style.configure("DarkGreen.TButton", 
                           foreground="white", 
                           background="darkgreen",
                           font=("Arial", 10, "bold"))
    
    def setup_label_styles(self):
        self.style.configure("Title.TLabel",
                           font=("Arial", 16, "bold"),
                           foreground="white")
        
        self.style.configure("Subtitle.TLabel",
                           font=("Arial", 12, "bold"),
                           foreground="white")
        
        self.style.configure("Value.TLabel",
                           font=("Arial", 11, "bold"),
                           foreground="white")
        
        self.style.configure("Success.TLabel",
                           font=("Arial", 11, "bold"),
                           foreground="green")
        
        self.style.configure("Error.TLabel",
                           font=("Arial", 11, "bold"),
                           foreground="red")
        
        self.style.configure("Warning.TLabel",
                           font=("Arial", 11, "bold"),
                           foreground="orange")
        
        self.style.configure("Info.TLabel",
                           font=("Arial", 10),
                           foreground="blue")
    
    def setup_frame_styles(self):
        self.style.configure("Main.TFrame",
                           relief="solid",
                           borderwidth=1)
        
        self.style.configure("Highlight.TFrame",
                           relief="raised",
                           borderwidth=2)
    
    def get_sensor_colors(self) -> Dict[str, str]:
        return {
            'UV_360nm': 'purple',
            'Blue_450nm': 'blue',
            'IR_850nm': 'red',
            'IR_940nm': 'darkred'
        }
    
    def get_led_colors(self) -> Dict[str, str]:
        return {
            'UV LED (360nm)': 'purple',
            'Blue LED (450nm)': 'blue',
            'IR LED (850nm)': 'red',
            'IR LED (940nm)': 'darkred'
        }
    
    def apply_dark_theme(self):
        try:
            self.style.theme_use('default')
            self.style.theme_use('clam')  # Base theme
            
            dark_bg = '#1a1a1a'        # Ana arkaplan (daha koyu)
            panel_bg = '#252525'       # Panel arkaplan (daha koyu)
            input_bg = '#333333'       # Input arkaplan
            text_color = '#e8e8e8'      # Ana yazı rengi (daha yumuşak beyaz)
            text_secondary = '#a0a0a0'  # İkincil yazı rengi
            border_color = '#404040'    # Kenarlık rengi
            highlight_bg = '#3a3a3a'    # Vurgu arkaplan
            
            self.style.configure('TLabel', 
                               background=dark_bg, 
                               foreground=text_color)
            
            self.style.map('TLabel',
                         background=[('disabled', '#2a2a2a')],
                         foreground=[('disabled', '#666666')])
            
            self.style.configure('TFrame', 
                               background=dark_bg)
            
            self.style.configure('TLabelFrame', 
                               background=dark_bg, 
                               foreground=text_color,
                               borderwidth=1,
                               relief='solid')
            
            self.style.configure('TLabelFrame.Label',
                               background=dark_bg,
                               foreground=text_color,
                               font=('Arial', 10, 'bold'))
            
            self.style.configure('BigLabel.TLabelframe',
                               background=dark_bg,
                               foreground=text_color,
                               borderwidth=2,
                               relief='raised')
            
            self.style.configure('BigLabel.TLabelframe.Label',
                               background=dark_bg,
                               foreground=text_color,
                               font=('Arial', 12, 'bold'))
            
            self.style.configure('TButton', 
                               background=input_bg, 
                               foreground=text_color,
                               borderwidth=1,
                               relief='raised',
                               font=('Arial', 9),
                               focuscolor='none')
            
            self.style.map('TButton',
                         background=[('active', highlight_bg),
                                   ('pressed', '#2a2a2a'),
                                   ('disabled', '#2a2a2a')],
                         foreground=[('active', text_color),
                                   ('pressed', text_color),
                                   ('disabled', '#666666')])
            
            self.style.configure('TNotebook', 
                               background=dark_bg,
                               borderwidth=0)
            
            self.style.configure('TNotebook.Tab', 
                               background=panel_bg,
                               foreground=text_color,
                               padding=[12, 8],
                               font=('Arial', 10, 'bold'))
            
            self.style.map('TNotebook.Tab',
                         background=[('selected', input_bg),
                                   ('active', '#4a4a4a')],
                         foreground=[('selected', text_color),
                                   ('active', text_color)])
            
            # Input bileşenleri
            self.style.configure('TCombobox', 
                               fieldbackground=input_bg, 
                               foreground=text_color,
                               background=input_bg,
                               borderwidth=1,
                               relief='solid',
                               arrowcolor=text_color,
                               focuscolor='none')
            
            self.style.map('TCombobox',
                         fieldbackground=[('readonly', input_bg),
                                        ('disabled', '#2a2a2a')],
                         foreground=[('readonly', text_color),
                                   ('disabled', '#666666')])
            
            self.style.configure('TEntry', 
                               fieldbackground=input_bg, 
                               foreground=text_color,
                               borderwidth=1,
                               relief='solid',
                               focuscolor='none')
            
            self.style.map('TEntry',
                         fieldbackground=[('focus', input_bg),
                                        ('disabled', '#2a2a2a'),
                                        ('readonly', input_bg)],
                         foreground=[('focus', text_color),
                                   ('disabled', '#666666'),
                                   ('readonly', text_color)],
                         bordercolor=[('focus', '#555555'),
                                    ('!focus', border_color)])
            
            # Scale (kaydırıcı) - güvenli stil
            try:
                self.style.configure('TScale', 
                                   background=dark_bg,
                                   troughcolor=panel_bg,
                                   borderwidth=0)
                
                # Scale layout elementlerini de güncelle
                self.style.configure('Horizontal.TScale', 
                                   background=dark_bg,
                                   troughcolor=panel_bg,
                                   borderwidth=0)
                                   
            except Exception as scale_error:
                print(f"Scale stil hatası: {scale_error}")
                # Fallback - temel renkleri ayarla
                try:
                    self.style.configure('TScale', background=dark_bg)
                except:
                    pass
            
            # Checkbox
            self.style.configure('TCheckbutton', 
                               background=dark_bg, 
                               foreground=text_color,
                               font=('Arial', 9))
            
            # Progressbar
            self.style.configure('TProgressbar',
                               background=input_bg,
                               troughcolor=panel_bg,
                               borderwidth=1,
                               lightcolor=input_bg,
                               darkcolor=input_bg)
            
            # Separator
            self.style.configure('TSeparator',
                               background=border_color)
            
            # Renkli butonları güncelle
            self.update_colored_buttons_for_dark_theme()
            
            # Özel dark theme stilleri
            self.setup_dark_theme_styles()
            
            # Stilleri zorla uygula
            self.force_apply_dark_styles()
            
            # Tkinter bileşenleri için root stilini ayarla
            self.apply_tkinter_dark_theme()
            
        except Exception as e:
            print(f"Koyu tema uygulama hatası: {e}")
    
# Light theme kaldırıldı - Sadece dark theme destekleniyor
    
    def update_colored_buttons_for_dark_theme(self):
        """Renkli butonları dark theme için optimize et"""
        # START butonu - daha koyu yeşil
        self.style.configure("Green.TButton", 
                           foreground="white", 
                           background="#2d5a2d",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("Green.TButton",
                     background=[('active', '#3d6a3d'),
                               ('pressed', '#1d4a1d')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
        
        # STOP butonu - daha koyu kırmızı
        self.style.configure("Red.TButton", 
                           foreground="white", 
                           background="#5a2d2d",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("Red.TButton",
                     background=[('active', '#6a3d3d'),
                               ('pressed', '#4a1d1d')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
        
        self.style.configure("Blue.TButton", 
                           foreground="white", 
                           background="#2d2d5a",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("Blue.TButton",
                     background=[('active', '#3d3d6a'),
                               ('pressed', '#1d1d4a')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
        
        self.style.configure("Orange.TButton", 
                           foreground="white", 
                           background="#5a4a2d",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("Orange.TButton",
                     background=[('active', '#6a5a3d'),
                               ('pressed', '#4a3a1d')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
        
        self.style.configure("Purple.TButton", 
                           foreground="white", 
                           background="#4a2d5a",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("Purple.TButton",
                     background=[('active', '#5a3d6a'),
                               ('pressed', '#3a1d4a')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
        
        self.style.configure("DarkGreen.TButton", 
                           foreground="white", 
                           background="#1a3d1a",
                           font=("Arial", 10, "bold"),
                           borderwidth=1,
                           relief='raised',
                           focuscolor='none')
        
        self.style.map("DarkGreen.TButton",
                     background=[('active', '#2a4d2a'),
                               ('pressed', '#0a2d0a')],
                     foreground=[('active', 'white'),
                               ('pressed', 'white')])
    
    def setup_dark_theme_styles(self):
        """Dark theme için özel stiller"""
        try:
            self.style.configure('Dark.TEntry',
                              fieldbackground='#333333',
                              foreground='#e8e8e8',
                              borderwidth=1,
                              relief='solid',
                              focuscolor='none')
            
            self.style.map('Dark.TEntry',
                         fieldbackground=[('focus', '#333333'),
                                        ('disabled', '#2a2a2a')],
                         foreground=[('focus', '#e8e8e8'),
                                   ('disabled', '#666666')],
                         bordercolor=[('focus', '#555555'),
                                    ('!focus', '#404040')])
            
            self.style.configure('Dark.TLabel',
                              background='#1a1a1a',
                              foreground='#e8e8e8')
            
            self.style.configure('Dark.TFrame',
                              background='#1a1a1a')
            
            self.style.configure('Dark.TLabelFrame',
                              background='#1a1a1a',
                              foreground='#e8e8e8',
                              borderwidth=1,
                              relief='solid')
            
            self.style.configure('Dark.TLabelFrame.Label',
                              background='#1a1a1a',
                              foreground='#e8e8e8',
                              font=('Arial', 10, 'bold'))
            
            # Dark Combobox stili
            self.style.configure('Dark.TCombobox',
                              fieldbackground='#333333',
                              foreground='#e8e8e8',
                              background='#333333',
                              borderwidth=1,
                              relief='solid',
                              arrowcolor='#e8e8e8',
                              focuscolor='none')
            
            self.style.map('Dark.TCombobox',
                         fieldbackground=[('readonly', '#333333'),
                                        ('disabled', '#2a2a2a')],
                         foreground=[('readonly', '#e8e8e8'),
                                   ('disabled', '#666666')],
                         background=[('readonly', '#333333'),
                                   ('disabled', '#2a2a2a')])
            
            # Scale için layout problemini önlemek için sadece temel stilleri güncelle
            # Dark.TScale kullanmıyoruz çünkü layout sorunlarına neden oluyor
                              
        except Exception as e:
            print(f"Dark theme stil kurulum hatası: {e}")
    
    def force_apply_dark_styles(self):
        """Dark theme stillerini zorla uygula"""
        try:
            # Temel stilleri tekrar uygula
            dark_bg = '#1a1a1a'
            text_color = '#e8e8e8'
            input_bg = '#333333'
            
            # Tüm TTK widget'lar için varsayılan renkleri zorla ayarla
            for widget_class in ['TLabel', 'TFrame', 'TLabelFrame', 'TButton', 
                               'TEntry', 'TCombobox', 'TScale', 'TCheckbutton']:
                try:
                    if widget_class in ['TLabel', 'TFrame']:
                        self.style.configure(widget_class, 
                                           background=dark_bg, 
                                           foreground=text_color)
                    elif widget_class == 'TLabelFrame':
                        self.style.configure(widget_class, 
                                           background=dark_bg, 
                                           foreground=text_color)
                        self.style.configure(f'{widget_class}.Label',
                                           background=dark_bg,
                                           foreground=text_color)
                except Exception as e:
                    print(f"Stil zorla uygulama hatası ({widget_class}): {e}")
                    
        except Exception as e:
            print(f"Zorla stil uygulama hatası: {e}")
    
    def apply_tkinter_dark_theme(self):
        """Tkinter bileşenleri için dark theme ayarları"""
        try:
            import tkinter as tk
            
            # Tkinter için varsayılan renkler ayarla - daha koyu tema
            tk._default_root.option_add('*Background', '#1a1a1a')
            tk._default_root.option_add('*Foreground', '#e8e8e8')
            tk._default_root.option_add('*selectBackground', '#3a3a3a')
            tk._default_root.option_add('*selectForeground', '#ffffff')
            tk._default_root.option_add('*insertBackground', '#e8e8e8')
            
            # Tüm widget'lar için genel ayarlar
            tk._default_root.option_add('*highlightBackground', '#1a1a1a')
            tk._default_root.option_add('*highlightColor', '#404040')
            tk._default_root.option_add('*disabledForeground', '#666666')
            tk._default_root.option_add('*disabledBackground', '#2a2a2a')
            
            # Listbox için özel ayarlar - daha koyu
            tk._default_root.option_add('*Listbox*Background', '#252525')
            tk._default_root.option_add('*Listbox*Foreground', '#e8e8e8')
            tk._default_root.option_add('*Listbox*selectBackground', '#3a3a3a')
            tk._default_root.option_add('*Listbox*selectForeground', '#ffffff')
            tk._default_root.option_add('*Listbox*borderWidth', '1')
            tk._default_root.option_add('*Listbox*relief', 'solid')
            tk._default_root.option_add('*Listbox*highlightThickness', '0')
            
            # Text widget için ayarlar
            tk._default_root.option_add('*Text*Background', '#252525')
            tk._default_root.option_add('*Text*Foreground', '#e8e8e8')
            tk._default_root.option_add('*Text*selectBackground', '#3a3a3a')
            tk._default_root.option_add('*Text*selectForeground', '#ffffff')
            tk._default_root.option_add('*Text*insertBackground', '#e8e8e8')
            
        except Exception as e:
            print(f"Tkinter dark theme uygulama hatası: {e}")
    
# Light theme Tkinter fonksiyonu kaldırıldı - Sadece dark theme destekleniyor
    
    def apply_dark_theme_to_widget(self, widget, widget_type='default'):
        """Mevcut widget'a dark theme uygula"""
        try:
            if widget_type == 'listbox':
                widget.configure(
                    bg='#252525', 
                    fg='#e8e8e8',
                    selectbackground='#3a3a3a', 
                    selectforeground='#ffffff',
                    borderwidth=1, 
                    relief='solid', 
                    highlightthickness=0,
                    activestyle='none'
                )
            elif widget_type == 'entry':
                widget.configure(
                    bg='#333333',
                    fg='#e8e8e8',
                    insertbackground='#e8e8e8',
                    selectbackground='#3a3a3a',
                    selectforeground='#ffffff',
                    borderwidth=1,
                    relief='solid',
                    highlightthickness=0
                )
            elif widget_type == 'text':
                widget.configure(
                    bg='#252525',
                    fg='#e8e8e8',
                    insertbackground='#e8e8e8',
                    selectbackground='#3a3a3a',
                    selectforeground='#ffffff',
                    borderwidth=1,
                    relief='solid',
                    highlightthickness=0
                )
            elif widget_type == 'label':
                widget.configure(
                    bg='#1a1a1a',
                    fg='#e8e8e8'
                )
            elif widget_type == 'frame':
                widget.configure(
                    bg='#1a1a1a'
                )
        except Exception as e:
            print(f"Widget dark theme uygulama hatası: {e}")
    
    def get_style(self) -> ttk.Style:
        """Style nesnesini al"""
        return self.style
