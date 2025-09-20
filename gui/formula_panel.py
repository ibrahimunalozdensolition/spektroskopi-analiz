"""
Formül Tabanlı Veri Üretim Paneli
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Callable, Any
import json

from data.formula_engine import FormulaEngine
from utils.logger import app_logger
from config.settings import settings_manager
from datetime import datetime

class FormulaPanel:
    """Formül tabanlı veri üretim paneli"""
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.formula_engine = FormulaEngine()
        
        # UI bileşenleri
        self.formula_name_entry = None
        self.formula_entry = None
        self.unit_entry = None
        self.formula_listbox = None
        self.current_value_label = None
        self.current_unit_label = None
        self.example_label = None
        
        # Veri callback
        self.data_callback = None
        
        # Mevcut hesaplanan değerler
        self.calculated_values = {}
        
        # Live modu durumu
        self.is_live_active = False
        self.live_button = None
        
        # Zamanlama kontrolü (formül hesaplama için)
        self.last_calculation_time = datetime.now()
        self.calculation_interval_ms = 500  # 500ms'de bir hesapla
        
        # Scroll için canvas referansı
        self.canvas = None
        self.scrollable_frame = None
        
        self.setup_panel()
    
    def set_data_callback(self, callback: Callable):
        """Veri callback'ini ayarla"""
        self.data_callback = callback
    
    def setup_panel(self):
        """Ana paneli kur"""
        # Scrollable container oluştur
        self.canvas = tk.Canvas(self.parent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Canvas genişliğini içeriğe göre ayarla
        def _configure_canvas(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            canvas_width = event.width
            # Canvas'ta window varsa genişliğini ayarla
            canvas_items = self.canvas.find_all()
            if canvas_items:
                self.canvas.itemconfig(canvas_items[0], width=canvas_width)
        
        self.canvas.bind("<Configure>", _configure_canvas)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel binding for scrolling (macOS compatible)
        def _on_mousewheel(event):
            # macOS ve diğer platformlar için uyumlu scroll
            try:
                if hasattr(event, 'delta'):
                    if event.delta > 0:
                        self.canvas.yview_scroll(-1, "units")
                    elif event.delta < 0:
                        self.canvas.yview_scroll(1, "units")
                else:
                    # Linux için
                    if event.num == 4:
                        self.canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        self.canvas.yview_scroll(1, "units")
            except Exception as e:
                print(f"Scroll event error: {e}")
        
        def _bind_mousewheel(event):
            # macOS için
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux için
            self.canvas.bind_all("<Button-4>", _on_mousewheel)
            self.canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        
        # Canvas'a odaklanabilirlik ekle
        self.canvas.focus_set()
        self.canvas.bind('<Enter>', _bind_mousewheel)
        self.canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Canvas'a tıklandığında da scroll aktif olsun
        self.canvas.bind('<Button-1>', lambda e: self.canvas.focus_set())
        
        # Scrollable frame'e de mouse wheel binding ekle
        def _bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_to_mousewheel(child)
        
        # İlk binding
        _bind_mousewheel(None)
        
        # scrollable_frame ve çocuklarına da binding ekle
        def _recursive_bind(widget):
            try:
                widget.bind("<MouseWheel>", _on_mousewheel)
                widget.bind("<Button-4>", _on_mousewheel) 
                widget.bind("<Button-5>", _on_mousewheel)
                for child in widget.winfo_children():
                    _recursive_bind(child)
            except:
                pass
        
        # Frame oluşturulduktan sonra binding eklemek için callback
        def _delayed_bind():
            try:
                _recursive_bind(self.scrollable_frame)
            except:
                pass
        
        # 100ms sonra binding ekle (widget'lar oluşturulduktan sonra)
        self.parent_frame.after(100, _delayed_bind)
        
        # Scroll binding'ini yenilemek için fonksiyonu sakla
        self._refresh_scroll_binding = _delayed_bind

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Ana içerik frame'i scrollable_frame içinde oluştur
        main_frame = ttk.Frame(self.scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık ve Live butonu - aynı satırda
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(title_frame, text="Custom Data Generator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Live butonu - sağ tarafta
        self.live_button = ttk.Button(title_frame, text="🔴 Live OFF", 
                                     command=self.toggle_live_mode,
                                     style="Red.TButton")
        self.live_button.pack(side=tk.RIGHT)
        
        # Üst kısım - Formül oluşturma
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_formula_creation_panel(top_frame)
        
        # Orta kısım - Mevcut formüller (en büyük alan)
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.setup_current_formulas_panel(middle_frame)
        
        # Alt kısım - İki sütunlu düzen
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        # Sol sütun - Hesaplanan değerler
        left_bottom = ttk.Frame(bottom_frame)
        left_bottom.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.setup_calculated_values_panel(left_bottom)
        
        # Sağ sütun - Kontrol paneli
        right_bottom = ttk.Frame(bottom_frame)
        right_bottom.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        self.setup_control_panel(right_bottom)
        
        # Uygulama açıldığında formülleri yükle
        self.load_formulas_from_settings()
        
        # Dark theme'i uygula (eğer gerekiyorsa)
        self.apply_current_theme()
        
        # Scroll binding'ini son kez yenile (tüm widget'lar oluşturulduktan sonra)
        self.parent_frame.after(500, self._refresh_scroll_binding)
    
    def setup_formula_creation_panel(self, parent_frame):
        """Formül oluşturma paneli"""
        create_frame = ttk.LabelFrame(parent_frame, text="Create New Data Type", padding=15)
        create_frame.pack(fill=tk.X, pady=(0, 15))
        
        # İsim ve Unit girişi (aynı satırda)
        name_frame = ttk.Frame(create_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Data Name:", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.formula_name_entry = ttk.Entry(name_frame, width=25, font=("Arial", 16))
        self.formula_name_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(name_frame, text="Unit:", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.unit_entry = ttk.Entry(name_frame, width=12, font=("Arial", 16))
        self.unit_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.unit_entry.insert(0, "ppm")
        
        # Formül girişi (geniş satır)
        formula_frame = ttk.Frame(create_frame)
        formula_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(formula_frame, text="Formula:", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Formül girişi ve buton aynı satırda
        entry_button_frame = ttk.Frame(formula_frame)
        entry_button_frame.pack(fill=tk.X)
        
        self.formula_entry = ttk.Entry(entry_button_frame, font=("Arial", 16))
        self.formula_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Oluştur butonu
        create_btn = ttk.Button(entry_button_frame, text="✓ Create", 
                               command=self.create_formula,
                               style="Green.TButton")
        create_btn.pack(side=tk.RIGHT)
        
        help_frame = ttk.LabelFrame(create_frame, text="Quick Reference", padding=10)
        help_frame.pack(fill=tk.X, pady=(10, 0))
        
        help_content_frame = ttk.Frame(help_frame)
        help_content_frame.pack(fill=tk.X)
        
        left_col = ttk.Frame(help_content_frame)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_col, text=" Available Sensors:", font=("Arial", 16, "bold")).pack(anchor=tk.W)
        sensor_text = self.get_sensor_text_from_settings()
        self.sensor_info_label = ttk.Label(left_col, text=sensor_text, font=("Arial", 16))
        self.sensor_info_label.pack(anchor=tk.W, padx=(10, 0))
        
        # Sağ sütun - Formüller
        right_col = ttk.Frame(help_content_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(right_col, text="⚡ Created Data:", font=("Arial", 16, "bold")).pack(anchor=tk.W)
        self.created_formulas_label = ttk.Label(right_col, text="None yet", 
                                               font=("Arial", 16))
        self.created_formulas_label.pack(anchor=tk.W, padx=(10, 0))
        

        

    
    def setup_current_formulas_panel(self, parent_frame):
        """Mevcut formüller paneli"""
        formulas_frame = ttk.LabelFrame(parent_frame, text="📋 Current Formulas", padding=15)
        formulas_frame.pack(fill=tk.BOTH, expand=True)
        
        list_frame = ttk.Frame(formulas_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.formula_listbox = tk.Listbox(list_frame, height=10, font=("Consolas", 16),
                                        bg='#252525', fg='#e8e8e8',
                                        selectbackground='#3a3a3a', selectforeground='#ffffff',
                                        borderwidth=1, relief='solid', highlightthickness=0,
                                        activestyle='none')
        self.formula_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.formula_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.formula_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Seçim olayı
        self.formula_listbox.bind('<<ListboxSelect>>', self.on_formula_selected)
        self.formula_listbox.bind('<Double-Button-1>', self.on_formula_double_click)
        
        # Status label - seçili formül sayısı
        self.status_label = ttk.Label(formulas_frame, text="Seçili formül sayısı: 0", 
                                     font=("Arial", 16, "italic"))
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Butonlar - modern ikonlarla
        button_frame = ttk.Frame(formulas_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="🗑️ Remove", 
                  command=self.remove_selected_formula,
                  style="Red.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="✏️ Edit", 
                  command=self.edit_selected_formula).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🧪 Test", 
                  command=self.test_selected_formula,
                  style="Blue.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="☑ Select All", 
                  command=self.select_all_formulas,
                  style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="☐ Deselect All", 
                  command=self.deselect_all_formulas,
                  style="Orange.TButton").pack(side=tk.LEFT)
    
    def setup_calculated_values_panel(self, parent_frame):
        """Hesaplanan değerler paneli"""
        values_frame = ttk.LabelFrame(parent_frame, text="📊 Live Results (OFF)", padding=10)
        values_frame.pack(fill=tk.BOTH, expand=True)
        self.live_results_frame = values_frame  # Referansı sakla
        
        # Değer gösterimi - daha büyük ve merkezi
        value_display_frame = ttk.Frame(values_frame)
        value_display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sol taraf - Label
        ttk.Label(value_display_frame, text="Current Value:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Sağ taraf - Değer ve birim
        value_container = ttk.Frame(value_display_frame)
        value_container.pack(side=tk.RIGHT)
        
        self.current_value_label = ttk.Label(value_container, text="0.000", 
                                           font=("Arial", 16, "bold"))
        self.current_value_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.current_unit_label = ttk.Label(value_container, text="V", 
                                          font=("Arial", 16))
        self.current_unit_label.pack(side=tk.LEFT)
        
        # Ayırıcı çizgi
        separator = ttk.Separator(values_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        # Seçili formül bilgisi
        info_frame = ttk.Frame(values_frame)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text="Selected Formula:", 
                 font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 3))
        
        self.selected_formula_label = ttk.Label(info_frame, text="None selected", 
                                              font=("Arial", 16), wraplength=400)
        self.selected_formula_label.pack(anchor=tk.W, padx=(10, 0))
    
    def setup_control_panel(self, parent_frame):
        """Kontrol paneli"""
        control_frame = ttk.LabelFrame(parent_frame, text="⚙️ Controls", padding=10)
        control_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst satır - Dosya işlemleri
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="File Operations:", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        file_buttons_frame = ttk.Frame(file_frame)
        file_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(file_buttons_frame, text="💾 Save Formulas", 
                  command=self.save_formulas).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(file_buttons_frame, text="📂 Load Formulas", 
                  command=self.load_formulas).pack(side=tk.LEFT)
        
    
    def create_formula(self):
        """Yeni formül oluştur"""
        name = self.formula_name_entry.get().strip()
        formula = self.formula_entry.get().strip()
        unit = self.unit_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Veri ismi girin!")
            return
        
        if not formula:
            messagebox.showerror("Error", "Formül girin!")
            return
        
        # Formülü oluştur
        success, message = self.formula_engine.create_formula(name, formula, unit)
        
        if success:
            # UI'yi güncelle
            self.update_formula_list()
            self.clear_inputs()
            
            # Settings'e kaydet
            self.save_formulas_to_settings()
            
            messagebox.showinfo("Success", message)
            app_logger.info(f"Yeni formül oluşturuldu: {name}")
        else:
            messagebox.showerror("Error", f"Formül oluşturulamadı:\n{message}")
    
    def update_formula_list(self):
        """Formül listesini güncelle - seçim durumu ile"""
        self.formula_listbox.delete(0, tk.END)
        
        for name, info in self.formula_engine.get_all_formulas().items():
            formula = info['formula']
            unit = info['unit']
            last_value = info.get('last_value', 0.0)
            selected = info.get('selected', False)
            
            # Seçili formülleri işaretle
            checkbox = "☑" if selected else "☐"
            display_text = f"{checkbox} {name} = {formula} [{unit}] → {last_value:.0f}"
            self.formula_listbox.insert(tk.END, display_text)
        
        self.update_created_formulas_display()
        
        if hasattr(self, 'status_label'):
            selected_count = self.formula_engine.get_selected_formula_count()
            self.status_label.configure(text=f"Seçili formül sayısı: {selected_count}")
    
    def on_formula_selected(self, event):
        """Formül seçildiğinde"""
        selection = self.formula_listbox.curselection()
        if selection:
            index = selection[0]
            formula_names = list(self.formula_engine.get_all_formulas().keys())
            
            if index < len(formula_names):
                formula_name = formula_names[index]
                formula_info = self.formula_engine.get_formula_info(formula_name)
                
                if formula_info:
                    # Seçili formül bilgisini göster
                    self.selected_formula_label.configure(
                        text=f"{formula_name} = {formula_info['formula']}"
                    )
                    
                    # Mevcut değeri göster
                    self.current_value_label.configure(text=f"{formula_info['last_value']:.0f}")
                    self.current_unit_label.configure(text=formula_info['unit'])
    
    def on_formula_double_click(self, event):
        """Formül double-click - seçimi değiştir"""
        selection = self.formula_listbox.curselection()
        if selection:
            index = selection[0]
            formula_names = list(self.formula_engine.get_all_formulas().keys())
            
            if index < len(formula_names):
                formula_name = formula_names[index]
                # Formül seçimini değiştir
                success = self.formula_engine.toggle_formula_selection(formula_name)
                if success:
                    # Liste görünümünü güncelle
                    self.update_formula_list()
                    
                    selected_count = self.formula_engine.get_selected_formula_count()
                    app_logger.info(f"Formül seçimi değişti: {formula_name}, Toplam seçili: {selected_count}")
                    
                    # Status güncelle
                    if hasattr(self, 'status_label'):
                        self.status_label.configure(text=f"Seçili formül sayısı: {selected_count}")
    
    def select_all_formulas(self):
        self.formula_engine.select_all_formulas(True)
        self.update_formula_list()
        selected_count = self.formula_engine.get_selected_formula_count()
        app_logger.info(f"Tüm formüller seçildi: {selected_count} formül")
        messagebox.showinfo("Success", f"{selected_count} formül seçildi")
    
    def deselect_all_formulas(self):
        """Tüm formül seçimlerini kaldır"""
        self.formula_engine.select_all_formulas(False)
        self.update_formula_list()
        selected_count = self.formula_engine.get_selected_formula_count()
        app_logger.info(f"Tüm formül seçimleri kaldırıldı: {selected_count} formül")
        messagebox.showinfo("Success", "Tüm formül seçimleri kaldırıldı")
    
    def remove_selected_formula(self):
        """Seçili formülü kaldır"""
        selection = self.formula_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Kaldırılacak formül seçin!")
            return
        
        index = selection[0]
        formula_names = list(self.formula_engine.get_all_formulas().keys())
        
        if index < len(formula_names):
            formula_name = formula_names[index]
            
            result = messagebox.askyesno("Confirm", f"'{formula_name}' formülünü kaldırmak istediğinizden emin misiniz?")
            if result:
                success = self.formula_engine.remove_formula(formula_name)
                if success:
                    self.update_formula_list()
                    self.clear_selection()
                    
                    # Settings'i güncelle
                    self.save_formulas_to_settings()
                    
                    messagebox.showinfo("Success", f"'{formula_name}' formülü kaldırıldı!")
    
    def edit_selected_formula(self):
        """Seçili formülü düzenle"""
        selection = self.formula_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Düzenlenecek formül seçin!")
            return
        
        index = selection[0]
        formula_names = list(self.formula_engine.get_all_formulas().keys())
        
        if index < len(formula_names):
            formula_name = formula_names[index]
            formula_info = self.formula_engine.get_formula_info(formula_name)
            
            if formula_info:
                # Girişlere mevcut değerleri yükle
                self.formula_name_entry.delete(0, tk.END)
                self.formula_name_entry.insert(0, formula_name)
                
                self.formula_entry.delete(0, tk.END)
                self.formula_entry.insert(0, formula_info['formula'])
                
                self.unit_entry.delete(0, tk.END)
                self.unit_entry.insert(0, formula_info['unit'])
                
                # Eski formülü kaldır
                self.formula_engine.remove_formula(formula_name)
                self.update_formula_list()
    
    def test_selected_formula(self):
        """Seçili formülü test et"""
        selection = self.formula_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Test edilecek formül seçin!")
            return
        
        # Test verisi al
        if self.data_callback:
            try:
                latest_values = self.data_callback()
                if latest_values:
                    # Hesapla
                    results = self.formula_engine.calculate_all_formulas(latest_values)
                    
                    # Sonuçları göster
                    result_text = "Test Results:\n\n"
                    for name, value in results.items():
                        formula_info = self.formula_engine.get_formula_info(name)
                        unit = formula_info['unit'] if formula_info else 'V'
                        result_text += f"{name}: {value:.0f} {unit}\n"
                    
                    messagebox.showinfo("Test Results", result_text)
                else:
                    messagebox.showwarning("Warning", "Test için veri yok!")
            except Exception as e:
                messagebox.showerror("Error", f"Test hatası: {e}")
        else:
            messagebox.showwarning("Warning", "Veri kaynağı mevcut değil!")
    
    def calculate_all_formulas(self):
        """Tüm formülleri hesapla"""
        if self.data_callback:
            try:
                latest_values = self.data_callback()
                if latest_values:
                    self.calculated_values = self.formula_engine.calculate_all_formulas(latest_values)
                    self.update_formula_list()
                    self.update_created_formulas_display()
                    app_logger.info(f"{len(self.calculated_values)} formül hesaplandı")
            except Exception as e:
                app_logger.error(f"Formül hesaplama hatası: {e}")
    
    def toggle_live_mode(self):
        """Live modu aç/kapat"""
        try:
            self.is_live_active = not self.is_live_active
            
            if self.is_live_active:
                # Live modu aktif
                self.live_button.configure(text="🟢 Live ON", style="Green.TButton")
                if hasattr(self, 'live_results_frame'):
                    self.live_results_frame.configure(text="📊 Live Results (ON)")
                app_logger.info("Live mod aktifleştirildi")
            else:
                # Live modu pasif
                self.live_button.configure(text="🔴 Live OFF", style="Red.TButton")
                if hasattr(self, 'live_results_frame'):
                    self.live_results_frame.configure(text="📊 Live Results (OFF)")
                app_logger.info("Live mod deaktifleştirildi")
                
        except Exception as e:
            app_logger.error(f"Live mod değiştirme hatası: {e}")
    
    def update_calculated_values_display(self, sensor_data: Dict[str, float]):
        """Hesaplanan değerleri güncelle (sadece Live modu aktifken)"""
        try:
            if not self.is_live_active:
                return
                
            current_time = datetime.now()
            time_since_last_calc = (current_time - self.last_calculation_time).total_seconds() * 1000
            
            if time_since_last_calc >= self.calculation_interval_ms:
                if self.formula_engine.formulas:
                    self.calculated_values = self.formula_engine.calculate_selected_formulas(sensor_data)
                    
                    # Formül listesini güncelle (değerler ile)
                    self.update_formula_list()
                    
                    # Seçili formülün değerini göster
                    selection = self.formula_listbox.curselection()
                    if selection:
                        index = selection[0]
                        formula_names = list(self.formula_engine.get_all_formulas().keys())
                        
                        if index < len(formula_names):
                            formula_name = formula_names[index]
                            if formula_name in self.calculated_values:
                                value = self.calculated_values[formula_name]
                                formula_info = self.formula_engine.get_formula_info(formula_name)
                                unit = formula_info['unit'] if formula_info else 'V'
                                
                                self.current_value_label.configure(text=f"{value:.0f}")
                                self.current_unit_label.configure(text=unit)
                
                # Son hesaplama zamanını güncelle
                self.last_calculation_time = current_time
                
        except Exception as e:
            app_logger.error(f"Hesaplanan değer güncelleme hatası: {e}")
    
    def clear_inputs(self):
        """Girişleri temizle"""
        self.formula_name_entry.delete(0, tk.END)
        self.formula_entry.delete(0, tk.END)
        self.unit_entry.delete(0, tk.END)
        self.unit_entry.insert(0, "ppm")
    
    def clear_selection(self):
        """Seçimi temizle"""
        self.selected_formula_label.configure(text="None selected")
        self.current_value_label.configure(text="0.000")
        self.current_unit_label.configure(text="V")
    
    def clear_all_formulas(self):
        """Tüm formülleri temizle"""
        if not self.formula_engine.formulas:
            messagebox.showinfo("Info", "Temizlenecek formül yok!")
            return
        
        result = messagebox.askyesno("Confirm", "Tüm formülleri silmek istediğinizden emin misiniz?")
        if result:
            self.formula_engine.formulas.clear()
            self.calculated_values.clear()
            self.update_formula_list()
            self.clear_selection()
            
            # Settings'i güncelle
            self.save_formulas_to_settings()
            
            messagebox.showinfo("Success", "Tüm formüller temizlendi!")
    
    def save_formulas(self):
        """Formülleri kaydet"""
        if not self.formula_engine.formulas:
            messagebox.showinfo("Info", "Kaydedilecek formül yok!")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Formülleri Kaydet",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                export_data = self.formula_engine.export_formulas()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Formüller kaydedildi: {filename}")
                app_logger.info(f"Formüller kaydedildi: {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Kaydetme hatası: {e}")
            app_logger.error(f"Formül kaydetme hatası: {e}")
    
    def load_formulas(self):
        """Formülleri yükle"""
        try:
            filename = filedialog.askopenfilename(
                title="Formül Dosyası Seç",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                success, message = self.formula_engine.import_formulas(import_data)
                
                if success:
                    self.update_formula_list()
                    messagebox.showinfo("Success", message)
                    app_logger.info(f"Formüller yüklendi: {filename}")
                else:
                    messagebox.showerror("Error", f"Yükleme hatası: {message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Dosya okuma hatası: {e}")
            app_logger.error(f"Formül yükleme hatası: {e}")
    
    def get_sensor_text_from_settings(self) -> str:
        """Settings'ten sensör isimlerini alıp metin oluştur"""
        try:
            # Settings'ten LED isimlerini al
            led_names = settings_manager.get_led_names()
            
            # LED isimlerini temizle ve kısalt
            clean_names = []
            led_keys = ['UV LED (360nm)', 'Blue LED (450nm)', 'IR LED (850nm)', 'IR LED (940nm)']
            
            for i, led_key in enumerate(led_keys):
                if led_key in led_names:
                    # LED ismini temizle
                    clean_name = led_names[led_key].replace(" LED", "").split(" (")[0].strip()
                    channel = f"ch{i+1}"
                    clean_names.append(f"{channel}({clean_name})")
                else:
                    # Varsayılan isimler
                    defaults = ["UV", "Blue", "IR850", "IR940"]
                    clean_names.append(f"ch{i+1}({defaults[i]})")
            
            # Metin oluştur (sadece ch1-ch4)
            sensor_text = ", ".join(clean_names)
            return sensor_text
            
        except Exception as e:
            app_logger.error(f"Sensör metin oluşturma hatası: {e}")
            # Varsayılan metin (sadece ch1-ch4)
            return "ch1(UV), ch2(Blue), ch3(IR850), ch4(IR940)"
    
    def update_sensor_info(self):
        """Sensör bilgilerini güncelle"""
        try:
            if hasattr(self, 'sensor_info_label'):
                new_text = self.get_sensor_text_from_settings()
                self.sensor_info_label.configure(text=new_text)
                app_logger.info("Sensör bilgileri güncellendi")
        except Exception as e:
            app_logger.error(f"Sensör bilgi güncelleme hatası: {e}")
    
    def get_calculated_values(self) -> Dict[str, float]:
        """Hesaplanan değerleri al"""
        return self.calculated_values.copy()
    
    def is_live_mode_active(self) -> bool:
        """Live modunun aktif olup olmadığını kontrol et"""
        return self.is_live_active
    
    def update_created_formulas_display(self):
        """Oluşturulan formül isimlerini güncelle"""
        try:
            formula_names = list(self.formula_engine.get_all_formulas().keys())
            
            if formula_names:
                # İlk 5 formül ismini göster, fazlası varsa "..." ekle
                display_names = formula_names[:5]
                if len(formula_names) > 5:
                    display_names.append("...")
                
                created_text = ", ".join(display_names)
                self.created_formulas_label.configure(text=created_text)
            else:
                self.created_formulas_label.configure(text="None yet")
                
        except Exception as e:
            app_logger.error(f"Oluşturulan formül görünüm güncelleme hatası: {e}")
    
    def load_formulas_from_settings(self):
        """Uygulama açıldığında formülleri settings'ten yükle"""
        try:
            # Settings'ten formül verilerini al
            formula_data = settings_manager.get('formulas', {})
            
            if formula_data and 'formulas' in formula_data:
                success, message = self.formula_engine.import_formulas(formula_data)
                if success:
                    self.update_formula_list()
                    self.update_created_formulas_display()
                    app_logger.info(f"Uygulama başlangıcında formüller yüklendi: {len(formula_data['formulas'])}")
                else:
                    app_logger.warning(f"Formül yükleme hatası: {message}")
            else:
                app_logger.info("Kaydedilmiş formül bulunamadı")
                
        except Exception as e:
            app_logger.error(f"Settings'ten formül yükleme hatası: {e}")
    
    def save_formulas_to_settings(self):
        """Formülleri settings'e kaydet"""
        try:
            formula_data = self.formula_engine.export_formulas()
            settings_manager.set('formulas', formula_data)
            settings_manager.save_settings()
            app_logger.info(f"Formüller settings'e kaydedildi: {len(formula_data['formulas'])}")
            return True
        except Exception as e:
            app_logger.error(f"Settings'e formül kaydetme hatası: {e}")
            return False
    
    def get_formula_count(self) -> int:
        """Formül sayısını al"""
        return len(self.formula_engine.formulas)
    
    def apply_current_theme(self):
        """Mevcut temayı uygula"""
        try:
            from config.settings import settings_manager
            current_theme = settings_manager.get_theme()
            
            if current_theme == 'dark':
                # Listbox için dark theme uygula
                if hasattr(self, 'formula_listbox'):
                    self.formula_listbox.configure(
                        bg='#252525', 
                        fg='#e8e8e8',
                        selectbackground='#3a3a3a', 
                        selectforeground='#ffffff',
                        borderwidth=1, 
                        relief='solid', 
                        highlightthickness=0,
                        activestyle='none'
                    )
                
                # TTK Entry widget'larına dark theme uygula
                self.apply_dark_theme_to_entries()
            else:
                # Light theme
                if hasattr(self, 'formula_listbox'):
                    self.formula_listbox.configure(
                        bg='white', 
                        fg='black',
                        selectbackground='#0078d4', 
                        selectforeground='white',
                        borderwidth=1, 
                        relief='solid', 
                        highlightthickness=0,
                        activestyle='none'
                    )
                
                # TTK Entry widget'larına light theme uygula
                self.apply_light_theme_to_entries()
                
        except Exception as e:
            app_logger.error(f"Tema uygulama hatası: {e}")
    
    def apply_dark_theme_to_entries(self):
        """TTK Entry widget'larına dark theme uygula"""
        try:
            # Entry widget'larının listesi
            entries = [
                self.formula_name_entry,
                self.unit_entry,
                self.formula_entry
            ]
            
            for entry in entries:
                if entry:
                    # TTK Entry için style güncellemesi
                    entry.configure(style='Dark.TEntry')
            
            # Dark.TEntry stilini tanımla
            from tkinter import ttk
            style = ttk.Style()
            style.configure('Dark.TEntry',
                          fieldbackground='#333333',
                          foreground='#e8e8e8',
                          borderwidth=1,
                          relief='solid',
                          focuscolor='none')
            
            style.map('Dark.TEntry',
                    fieldbackground=[('focus', '#333333'),
                                   ('disabled', '#2a2a2a')],
                    foreground=[('focus', '#e8e8e8'),
                              ('disabled', '#666666')],
                    bordercolor=[('focus', '#555555'),
                               ('!focus', '#404040')])
                               
        except Exception as e:
            app_logger.error(f"Entry dark theme uygulama hatası: {e}")
    
    def apply_light_theme_to_entries(self):
        """TTK Entry widget'larına light theme uygula"""
        try:
            # Entry widget'larının listesi
            entries = [
                self.formula_name_entry,
                self.unit_entry,
                self.formula_entry
            ]
            
            for entry in entries:
                if entry:
                    # TTK Entry için style güncellemesi
                    entry.configure(style='Light.TEntry')
            
            # Light.TEntry stilini tanımla
            from tkinter import ttk
            style = ttk.Style()
            style.configure('Light.TEntry',
                          fieldbackground='white',
                          foreground='black',
                          borderwidth=1,
                          relief='solid',
                          focuscolor='none')
            
            style.map('Light.TEntry',
                    focuscolor=[('focus', '#0078d4')],
                    bordercolor=[('focus', '#0078d4')])
            
        except Exception as e:
            app_logger.error(f"Entry light theme uygulama hatası: {e}")
