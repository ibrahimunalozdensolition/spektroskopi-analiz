import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable, Any
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvasTkAgg = None

from utils.logger import app_logger
from config.constants import MATPLOTLIB_COLORS
from utils.helpers import clean_sensor_name

class CustomizablePanel:   
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        
        self.custom_sensor = None
        self.multiplier_value = None
        self.custom_value_label = None
        self.custom_unit_label = None
        self.current_settings_label = None
        
        self.led_checkboxes = {}
        self.create_graph_btn = None
        self.close_graph_btn = None
        
        self.graph_window = None
        self.graph_fig = None
        self.graph_ax = None
        self.graph_canvas = None
        self.graph_lines = {}
        
        self.custom_data = {
            'selected_sensor': None,
            'multiplier': 1.0,
            'current_value': 0.0,
            'unit': 'V'
        }
        
        self.data_callback = None
        self.settings_callback = None
        
        self.setup_panel()
    
    def set_callbacks(self, data_callback: Optional[Callable] = None,
                     settings_callback: Optional[Callable] = None):
        self.data_callback = data_callback
        self.settings_callback = settings_callback
    
    def setup_panel(self):
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="Customizable Data Display", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        self.setup_data_selection_panel(main_frame)
        
        self.setup_multiplier_panel(main_frame)
        
        self.setup_current_settings_panel(main_frame)
        
        self.setup_data_display_panel(main_frame)
        
        self.setup_graph_creation_panel(main_frame)
    
    def setup_data_selection_panel(self, parent_frame):
        data_frame = ttk.LabelFrame(parent_frame, text="Data Selection", padding=10)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        sensor_select_frame = ttk.Frame(data_frame)
        sensor_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sensor_select_frame, text="Select Sensor to Display:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.custom_sensor = ttk.Combobox(sensor_select_frame, width=20, state="readonly")
        self.custom_sensor['values'] = ["UV Sensor (360nm)", "Blue Sensor (450nm)", 
                                       "IR Sensor (850nm)", "IR Sensor (940nm)"]
        self.custom_sensor.pack(side=tk.LEFT, padx=(10, 0))
        self.custom_sensor.bind('<<ComboboxSelected>>', self.on_custom_sensor_selected)
    
    def setup_multiplier_panel(self, parent_frame):
        multiplier_frame = ttk.LabelFrame(parent_frame, text="Data Multiplier", padding=10)
        multiplier_frame.pack(fill=tk.X, pady=(0, 10))
        
        mult_input_frame = ttk.Frame(multiplier_frame)
        mult_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mult_input_frame, text="Multiplier Value:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.multiplier_value = ttk.Entry(mult_input_frame, width=15)
        self.multiplier_value.pack(side=tk.LEFT, padx=(10, 0))
        self.multiplier_value.insert(0, "1.0")
        
        apply_btn = ttk.Button(mult_input_frame, text="Apply Multiplier", 
                              command=self.apply_multiplier)
        apply_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_current_settings_panel(self, parent_frame):
        
        settings_frame = ttk.LabelFrame(parent_frame, text="Current Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_settings_label = ttk.Label(settings_frame, 
                                               text="No sensor selected", 
                                               font=("Arial", 16, "bold"))
        self.current_settings_label.pack()
    
    def setup_data_display_panel(self, parent_frame):
        
        display_frame = ttk.LabelFrame(parent_frame, text="Custom Data Display", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        
        value_frame = ttk.Frame(display_frame)
        value_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(value_frame, text="Current Value:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.custom_value_label = ttk.Label(value_frame, text="0.000", 
                                           font=("Arial", 16, "bold"), 
                                           foreground="blue")
        self.custom_value_label.pack(side=tk.LEFT, padx=(10, 0))
        
        
        unit_frame = ttk.Frame(display_frame)
        unit_frame.pack(fill=tk.X)
        
        ttk.Label(unit_frame, text="Unit:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        self.custom_unit_label = ttk.Label(unit_frame, text="V", 
                                          font=("Arial", 16, "bold"))
        self.custom_unit_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_graph_creation_panel(self, parent_frame):
        
        graph_frame = ttk.LabelFrame(parent_frame, text="Real-Time Graph Creation", padding=10)
        graph_frame.pack(fill=tk.X, pady=(10, 0))
        
        
        led_select_frame = ttk.Frame(graph_frame)
        led_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(led_select_frame, text="Select LEDs for Graph:", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        led_names = ['UV LED (360nm)', 'Blue LED (450nm)', 'IR LED (850nm)', 'IR LED (940nm)']
        led_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        
        checkbox_frame = ttk.Frame(led_select_frame)
        checkbox_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        for i, (led_name, led_key) in enumerate(zip(led_names, led_keys)):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(checkbox_frame, text=led_name, variable=var)
            cb.pack(side=tk.LEFT, padx=5)
            self.led_checkboxes[led_key] = var
        
        graph_btn_frame = ttk.Frame(graph_frame)
        graph_btn_frame.pack(fill=tk.X)
        
        self.create_graph_btn = ttk.Button(graph_btn_frame, text="Create Real-Time Graph", 
                                          command=self.create_realtime_graph,
                                          style="Blue.TButton")
        self.create_graph_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.close_graph_btn = ttk.Button(graph_btn_frame, text="Close Graph", 
                                         command=self.close_realtime_graph,
                                         state=tk.DISABLED)
        self.close_graph_btn.pack(side=tk.LEFT)
    
    def on_custom_sensor_selected(self, event):
        selected = self.custom_sensor.get()
        if selected:
            sensor_mapping = {
                "UV Sensor (360nm)": "UV_360nm",
                "Blue Sensor (450nm)": "Blue_450nm", 
                "IR Sensor (850nm)": "IR_850nm",
                "IR Sensor (940nm)": "IR_940nm"
            }
            
            if selected in sensor_mapping:
                self.custom_data['selected_sensor'] = sensor_mapping[selected]
                self.update_custom_settings_display()
                messagebox.showinfo("Sensor Selected", f"Selected sensor: {selected}")
    
    def apply_multiplier(self):
        try:
            multiplier = float(self.multiplier_value.get())
            if multiplier <= 0:
                messagebox.showerror("Error", "Çarpan 0'dan büyük olmalı!")
                return
            
            self.custom_data['multiplier'] = multiplier
            self.update_custom_settings_display()
            
            if self.settings_callback:
                self.settings_callback('multiplier', multiplier)
            
            messagebox.showinfo("Multiplier Applied", f"Çarpan ayarlandı: {multiplier}")
            
        except ValueError:
            messagebox.showerror("Error", "Çarpan için geçerli bir sayı girin!")
    
    def update_custom_settings_display(self):
        if self.custom_data['selected_sensor']:
            sensor_name = self.custom_sensor.get()
            multiplier = self.custom_data['multiplier']
            settings_text = f"Selected: {sensor_name}\nMultiplier: {multiplier}"
            self.current_settings_label.configure(text=settings_text)
        else:
            self.current_settings_label.configure(text="No sensor selected")
    
    def update_data_display(self, latest_values: Dict[str, float], 
                           calibration_functions: Dict[str, Any]):
        if self.custom_data['selected_sensor'] and self.custom_data['selected_sensor'] in latest_values:
            sensor_key = self.custom_data['selected_sensor']
            raw_value = latest_values[sensor_key]
            multiplied_value = raw_value * self.custom_data['multiplier']
            
            self.custom_value_label.configure(text=f"{multiplied_value:.3f}")
            self.custom_data['current_value'] = multiplied_value
            
            if sensor_key in calibration_functions and calibration_functions[sensor_key]:
                unit = calibration_functions[sensor_key].get('unit', 'V')
                self.custom_unit_label.configure(text=unit)
                self.custom_data['unit'] = unit
            else:
                self.custom_unit_label.configure(text="V")
                self.custom_data['unit'] = "V"
    
    def create_realtime_graph(self):
        selected_leds = []
        for led_key, var in self.led_checkboxes.items():
            if var.get():
                selected_leds.append(led_key)
        
        if not selected_leds:
            messagebox.showwarning("Warning", "Grafik için en az bir LED seçin!")
            return
        
        self.graph_window = tk.Toplevel(self.parent_frame)
        self.graph_window.title("Custom Real-Time Graph")
        self.graph_window.geometry("800x600")
        self.graph_window.resizable(True, True)
        
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib gerekli ancak yüklü değil!")
            return
        
        self.graph_fig, self.graph_ax = plt.subplots(figsize=(10, 6))
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, self.graph_window)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.graph_ax.set_title("Custom Real-Time Sensor Data")
        self.graph_ax.set_xlabel("Time")
        self.graph_ax.set_ylabel("Voltage (V)")
        self.graph_ax.grid(True, alpha=0.3)
        
        self.graph_lines = {}
        for i, led_key in enumerate(selected_leds):
            color = MATPLOTLIB_COLORS[i % len(MATPLOTLIB_COLORS)]
            line, = self.graph_ax.plot([], [], label=led_key, color=color, linewidth=2)
            self.graph_lines[led_key] = line
        
        self.graph_ax.legend()
        self.graph_canvas.draw()
        
        self.create_graph_btn.configure(state=tk.DISABLED)
        self.close_graph_btn.configure(state=tk.NORMAL)
        
        self.update_custom_graph()
        
        self.graph_window.protocol("WM_DELETE_WINDOW", self.close_realtime_graph)
        
        messagebox.showinfo("Graph Created", f"Real-time grafik {len(selected_leds)} LED ile oluşturuldu!")
        app_logger.info(f"Özel real-time grafik oluşturuldu: {len(selected_leds)} LED")
    
    def close_realtime_graph(self):
        if self.graph_window:
            self.graph_window.destroy()
            self.graph_window = None
            self.graph_fig = None
            self.graph_ax = None
            self.graph_canvas = None
            self.graph_lines = {}
            
            self.create_graph_btn.configure(state=tk.NORMAL)
            self.close_graph_btn.configure(state=tk.DISABLED)
            
            app_logger.info("Custom real-time graph closed")
    
    def update_custom_graph(self):
        if not self.graph_window or not self.graph_ax:
            return
        
        try:
            if self.data_callback:
                timestamps, measurements = self.data_callback()
                
                if timestamps and measurements:
                    self.graph_ax.clear()
                    self.graph_ax.set_title("Custom Real-Time Sensor Data")
                    self.graph_ax.set_xlabel("Time")
                    self.graph_ax.set_ylabel("Voltage (V)")
                    self.graph_ax.grid(True, alpha=0.3)
                    
                    start_idx = max(0, len(timestamps) - 100)
                    plot_times = timestamps[start_idx:]
                    
                    for i, led_key in enumerate(self.graph_lines.keys()):
                        if led_key in measurements and len(measurements[led_key]) > start_idx:
                            plot_data = measurements[led_key][start_idx:]
                            color = MATPLOTLIB_COLORS[i % len(MATPLOTLIB_COLORS)]
                            
                            self.graph_ax.plot(plot_times[:len(plot_data)], plot_data, 
                                             label=led_key, color=color, linewidth=2)
                    
                    self.graph_ax.legend()
                    self.graph_canvas.draw()
            
        except Exception as e:
            app_logger.error(f"Custom graph update error: {e}")
        
        # Sonraki güncelleme için zamanla
        if self.graph_window:
            self.graph_window.after(100, self.update_custom_graph)
    
    def load_settings(self, settings: Dict[str, Any]):
        try:
            if 'custom_data' in settings:
                custom_settings = settings['custom_data']
            
                if custom_settings.get('selected_sensor'):
                    sensor_mapping = {
                        "UV_360nm": "UV Sensor (360nm)",
                        "Blue_450nm": "Blue Sensor (450nm)",
                        "IR_850nm": "IR Sensor (850nm)",
                        "IR_940nm": "IR Sensor (940nm)"
                    }
                    
                    sensor_key = custom_settings['selected_sensor']
                    if sensor_key in sensor_mapping:
                        self.custom_sensor.set(sensor_mapping[sensor_key])
                        self.custom_data['selected_sensor'] = sensor_key
                
                if 'multiplier' in custom_settings:
                    multiplier = custom_settings['multiplier']
                    self.multiplier_value.delete(0, tk.END)
                    self.multiplier_value.insert(0, str(multiplier))
                    self.custom_data['multiplier'] = multiplier
                
                if 'unit' in custom_settings:
                    self.custom_data['unit'] = custom_settings['unit']
                
                self.update_custom_settings_display()
                
        except Exception as e:
            app_logger.error(f"Custom panel settings load error: {e}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        return {
            'selected_sensor': self.custom_data['selected_sensor'],
            'multiplier': self.custom_data['multiplier'],
            'unit': self.custom_data['unit']
        }

class CalibratedDataPanel:
    
    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        
        self.calibrated_checkboxes = {}
        self.calibrated_values = {}
        self.calibrated_units = {}
        self.calibration_status_label = None
        
        self.calibrated_graph_window = None
        self.cal_live_fig = None
        self.cal_live_ax = None
        self.cal_live_canvas = None
        self.cal_graph_sensors = []
        
        self.graph_data_points = None
        self.graph_update_interval = None
        self.graph_width = None
        self.graph_height = None
        self.graph_points_label = None
        self.graph_interval_label = None
        
        self.data_callback = None
        
        self.setup_panel()
    
    def set_data_callback(self, callback: Callable):
        self.data_callback = callback
    
    def setup_panel(self):
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="Calibrated Data Display", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        self.setup_sensor_selection_panel(main_frame)
        
        self.setup_status_panel(main_frame)
    
    def setup_sensor_selection_panel(self, parent_frame):
        selection_frame = ttk.LabelFrame(parent_frame, text="Sensor Selection", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 20))
        
        right_frame = ttk.Frame(selection_frame)
        right_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Label(right_frame, text="Select Sensors to Display:", 
                 font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        sensor_names = ['UV Sensor (360nm)', 'Blue Sensor (450nm)', 'IR Sensor (850nm)', 'IR Sensor (940nm)']
        sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        
        for i, (sensor_name, sensor_key) in enumerate(zip(sensor_names, sensor_keys)):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(right_frame, text=sensor_name, variable=var,
                                command=lambda sk=sensor_key: self.on_calibrated_sensor_toggled(sk))
            cb.pack(anchor=tk.W, pady=2)
            self.calibrated_checkboxes[sensor_key] = var
        
        left_frame = ttk.Frame(selection_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Current Calibrated Values:", 
                 font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        for sensor_key in sensor_keys:
            sensor_frame = ttk.Frame(left_frame)
            sensor_frame.pack(fill=tk.X, pady=2)
            
            sensor_name = sensor_names[sensor_keys.index(sensor_key)]
            ttk.Label(sensor_frame, text=f"{sensor_name}:", width=20,
                     font=("Arial", 16, "bold")).pack(side=tk.LEFT)
            
            value_label = ttk.Label(sensor_frame, text="0.000", width=15, 
                                  font=("Arial", 16, "bold"))
            value_label.pack(side=tk.LEFT, padx=(5, 0))
            
            unit_label = ttk.Label(sensor_frame, text="V", width=10,
                                 font=("Arial", 16, "bold"))
            unit_label.pack(side=tk.LEFT, padx=(5, 0))
            
            self.calibrated_values[sensor_key] = value_label
            self.calibrated_units[sensor_key] = unit_label
    
    def setup_status_panel(self, parent_frame):
        status_frame = ttk.LabelFrame(parent_frame, text="Status Information", padding=10)
        status_frame.pack(fill=tk.X, pady=(20, 0))

        self.calibration_status_label = ttk.Label(status_frame, 
                                                text="No sensors calibrated", 
                                                foreground="orange")
        self.calibration_status_label.pack(anchor=tk.W)
        
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.pack(side=tk.RIGHT, pady=(10, 0))
        
        update_btn = ttk.Button(buttons_frame, text="Update Display", 
                               command=self.update_calibrated_display,
                               style="Blue.TButton")
        update_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        graph_btn = ttk.Button(buttons_frame, text="Create Live Graph from selected sensors", 
                              command=self.open_calibrated_graph_window,
                              style="Green.TButton")
        graph_btn.pack(side=tk.LEFT)
    
    def on_calibrated_sensor_toggled(self, sensor_key: str):
        is_checked = self.calibrated_checkboxes[sensor_key].get()
        if is_checked:
            self.update_sensor_calibrated_value(sensor_key)
        else:
            self.calibrated_values[sensor_key].configure(text="0.000")
    
    def update_sensor_calibrated_value(self, sensor_key: str):
        try:
            if self.data_callback:
                calibrated_data = self.data_callback('calibrated')
                calibration_functions = self.data_callback('calibration_functions')
                
                if (sensor_key in calibrated_data and 
                    calibrated_data[sensor_key] and
                    sensor_key in calibration_functions and
                    calibration_functions[sensor_key]):
                    
                    calibrated_value = calibrated_data[sensor_key][-1]
                    unit = calibration_functions[sensor_key].get('unit', 'V')
                    
                    self.calibrated_values[sensor_key].configure(text=f"{calibrated_value:.3f}")
                    self.calibrated_units[sensor_key].configure(text=unit)
                else:
                    self.calibrated_values[sensor_key].configure(text="0.000")
                    self.calibrated_units[sensor_key].configure(text="V")
                    
        except Exception as e:
            app_logger.error(f"Calibrated value update error: {e}")
    
    def update_calibrated_display(self):
        try:
            if self.data_callback:
                calibration_functions = self.data_callback('calibration_functions')
                
                calibrated_count = sum(1 for func in calibration_functions.values() if func is not None)
                
                if calibrated_count > 0:
                    self.calibration_status_label.configure(
                        text=f"{calibrated_count} sensor(s) calibrated", 
                        foreground="green"
                    )
                else:
                    self.calibration_status_label.configure(
                        text="No sensors calibrated", 
                        foreground="orange"
                    )
                
                for sensor_key, checkbox in self.calibrated_checkboxes.items():
                    if checkbox.get():
                        self.update_sensor_calibrated_value(sensor_key)
                        
        except Exception as e:
            app_logger.error(f"Calibrated display update error: {e}")
    
    def open_calibrated_graph_window(self):
        """Kalibre veri canlı grafik penceresi aç"""
        selected_sensors = []
        sensor_names = ['UV Sensor (360nm)', 'Blue Sensor (450nm)', 'IR Sensor (850nm)', 'IR Sensor (940nm)']
        sensor_keys = ['UV_360nm', 'Blue_450nm', 'IR_850nm', 'IR_940nm']
        
        for i, sensor_key in enumerate(sensor_keys):
            if sensor_key in self.calibrated_checkboxes and self.calibrated_checkboxes[sensor_key].get():
                selected_sensors.append((sensor_names[i], sensor_key))
        
        if not selected_sensors:
            messagebox.showwarning("Warning", "En az bir sensör seçin!")
            return
        
        self.calibrated_graph_window = tk.Toplevel(self.parent_frame)
        self.calibrated_graph_window.title("Live Calibrated Data Graph")
        self.calibrated_graph_window.geometry("900x700")
        
        main_frame = ttk.Frame(self.calibrated_graph_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        graph_frame = ttk.Frame(main_frame)
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib gerekli ancak yüklü değil!")
            return
        
        self.cal_live_fig, self.cal_live_ax = plt.subplots(figsize=(10, 6))
        self.cal_live_canvas = FigureCanvasTkAgg(self.cal_live_fig, graph_frame)
        self.cal_live_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.setup_graph_settings_panel(main_frame)
        
        self.cal_graph_sensors = selected_sensors
        
        self.setup_calibrated_live_graph()
        self.update_calibrated_graph()
        
        app_logger.info(f"Calibrated data live graph created: {len(selected_sensors)} sensor")
    
    def setup_graph_settings_panel(self, parent_frame):
        settings_frame = ttk.LabelFrame(parent_frame, text="Graph Settings", padding=10)
        settings_frame.pack(fill=tk.X)
        
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="Data Points:").pack(side=tk.LEFT)
        self.graph_data_points = ttk.Scale(row1, from_=50, to=1000, orient=tk.HORIZONTAL)
        self.graph_data_points.set(200)
        self.graph_data_points.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 20))
        self.graph_points_label = ttk.Label(row1, text="200 points")
        self.graph_points_label.pack(side=tk.LEFT)
        self.graph_data_points.configure(command=self.update_graph_points_label)
        
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row2, text="Update Interval:").pack(side=tk.LEFT)
        self.graph_update_interval = ttk.Scale(row2, from_=100, to=2000, orient=tk.HORIZONTAL)
        self.graph_update_interval.set(500)
        self.graph_update_interval.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 20))
        self.graph_interval_label = ttk.Label(row2, text="500 ms")
        self.graph_interval_label.pack(side=tk.LEFT)
        self.graph_update_interval.configure(command=self.update_graph_interval_label)
        
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row3, text="Graph Width:").pack(side=tk.LEFT)
        self.graph_width = ttk.Scale(row3, from_=6, to=16, orient=tk.HORIZONTAL)
        self.graph_width.set(10)
        self.graph_width.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        ttk.Label(row3, text="Height:").pack(side=tk.LEFT)
        self.graph_height = ttk.Scale(row3, from_=4, to=12, orient=tk.HORIZONTAL)
        self.graph_height.set(6)
        self.graph_height.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 20))
        
        apply_btn = ttk.Button(row3, text="Apply Size", 
                              command=self.apply_graph_size,
                              style="Blue.TButton")
        apply_btn.pack(side=tk.LEFT)
    
    def update_graph_points_label(self, value):
        points = int(float(value))
        self.graph_points_label.configure(text=f"{points} points")
    
    def update_graph_interval_label(self, value):
        interval = int(float(value))
        self.graph_interval_label.configure(text=f"{interval} ms")
    
    def apply_graph_size(self):
        try:
            width = int(self.graph_width.get())
            height = int(self.graph_height.get())
            
            if self.cal_live_fig:
                self.cal_live_fig.set_size_inches(width, height)
                self.cal_live_canvas.draw()
                
                app_logger.info(f"Graph size updated: {width}x{height}")
            
        except Exception as e:
            app_logger.error(f"Graph size update error: {e}")
    
    def setup_calibrated_live_graph(self):
        self.cal_live_ax.set_title("Live Calibrated Data")
        self.cal_live_ax.set_xlabel("Time")
        self.cal_live_ax.set_ylabel("Calibrated Value")
        self.cal_live_ax.grid(True, alpha=0.3)
        
        colors = MATPLOTLIB_COLORS
        for i, (sensor_name, sensor_key) in enumerate(self.cal_graph_sensors):
            color = colors[i % len(colors)]
            clean_name = clean_sensor_name(sensor_name)
            self.cal_live_ax.plot([], [], label=clean_name, color=color, linewidth=2)
        
        self.cal_live_ax.legend()
        self.cal_live_canvas.draw()
    
    def update_calibrated_graph(self):
        try:
            if not hasattr(self, 'calibrated_graph_window') or not self.calibrated_graph_window.winfo_exists():
                return
            
            # Get data
            if self.data_callback:
                calibrated_data = self.data_callback('calibrated')
                
                if calibrated_data and calibrated_data.get('timestamps'):
                    # Number of data points to display
                    max_points = int(self.graph_data_points.get())
                    
                    # Clear and setup graph
                    self.cal_live_ax.clear()
                    self.cal_live_ax.set_title("Live Calibrated Data")
                    self.cal_live_ax.set_xlabel("Time")
                    self.cal_live_ax.set_ylabel("Calibrated Value")
                    self.cal_live_ax.grid(True, alpha=0.3)
                    
                    times = calibrated_data['timestamps']
                    if len(times) > 1:
                        # Son N veri noktasını göster
                        start_idx = max(0, len(times) - max_points)
                        plot_times = times[start_idx:]
                        
                        # Her seçili sensör için çiz
                        colors = MATPLOTLIB_COLORS
                        for i, (sensor_name, sensor_key) in enumerate(self.cal_graph_sensors):
                            if sensor_key in calibrated_data and len(calibrated_data[sensor_key]) > start_idx:
                                plot_data = calibrated_data[sensor_key][start_idx:]
                                color = colors[i % len(colors)]
                                clean_name = clean_sensor_name(sensor_name)
                                
                                self.cal_live_ax.plot(plot_times[:len(plot_data)], plot_data, 
                                                    label=clean_name, color=color, linewidth=2)
                    
                    self.cal_live_ax.legend()
                    self.cal_live_canvas.draw()
            
            # Sonraki güncelleme için zamanla
            interval = int(self.graph_update_interval.get())
            self.calibrated_graph_window.after(interval, self.update_calibrated_graph)
            
        except Exception as e:
            app_logger.error(f"Kalibre grafik güncelleme hatası: {e}")
            # Hata durumunda da güncellemeyi devam ettir
            try:
                interval = int(self.graph_update_interval.get())
                self.calibrated_graph_window.after(interval, self.update_calibrated_graph)
            except:
                pass
