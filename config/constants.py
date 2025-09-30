APP_TITLE = "Spectroscopy System - Data Monitoring | by Prof.Dr. Uğur AKSU"
APP_VERSION = "2.0.0"
APP_GEOMETRY = "1200x800"

BLE_CHARACTERISTICS = {
    "SENSOR_2": "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",
    "SENSOR_5": "6E400003-B5A3-F393-E0A9-E50E24DCCA9E", 
    "SENSOR_7": "6E400004-B5A3-F393-E0A9-E50E24DCCA9E",
    "SENSOR_EXTRA": "6E400005-B5A3-F393-E0A9-E50E24DCCA9E"
}

SENSOR_MAPPING = {
    'sensor_2': 'UV_360nm',      
    'sensor_extra': 'Blue_450nm',
    'sensor_5': 'IR_850nm',   
    'sensor_7': 'IR_940nm'      
}

LED_MAPPING = {
    'sensor_2': 'UV LED (360nm)',      
    'sensor_extra': 'Blue LED (450nm)', 
    'sensor_5': 'IR LED (850nm)',      
    'sensor_7': 'IR LED (940nm)'      
}

SENSOR_INFO = [
    ("UV Detector", "UV_360nm", "purple"),
    ("Blue Detector", "Blue_450nm", "blue"),
    ("IR Detector 1", "IR_850nm", "red"),
    ("IR Detector 2", "IR_940nm", "darkred")
]

LED_INFO = [
    ("UV LED (360nm)", "purple"),
    ("Blue LED (450nm)", "blue"),
    ("IR LED (850nm)", "red"),
    ("IR LED (940nm)", "darkred")
]

DEFAULT_SENSORS = [
    "PicoW-Sensors", 
    "sensor-1", 
    "sensor-2", 
    "sensor-3", 
    "sensor-4"
]

TARGET_SENSORS = ["PicoW-Sensors", "pico-sensors-1", "pico-sensors-2", "pico-sensors-3", "pico-sensors-4"]

MAX_DATA_POINTS = 1000
VOLTAGE_CONVERSION_FACTOR = 3300.0 / 65535.0 

PLOT_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
MATPLOTLIB_COLORS = ['purple', 'blue', 'red', 'darkred']

MIN_CALIBRATION_POINTS = 3
MAX_CALIBRATION_POINTS = 6

SETTINGS_FILE = "app_settings.json"
CALIBRATION_FILE_PREFIX = "calibration_"
EXPORT_FILE_PREFIX = "spectroscopy_export_"

WINDOW_PADDING = 10
FRAME_PADDING = 10
BUTTON_PADDING = 2

DEFAULT_X_RANGE_SECONDS = 60
MIN_X_RANGE_SECONDS = 10
MAX_X_RANGE_SECONDS = 300
DEFAULT_GRAPH_WIDTH = 10
DEFAULT_GRAPH_HEIGHT = 6
MIN_GRAPH_SIZE = 4
MAX_GRAPH_WIDTH = 16
MAX_GRAPH_HEIGHT = 12

BLE_SCAN_TIMEOUT = 10.0
BLE_CONNECTION_RETRY_DELAY = 1000 
AUTO_CONNECTION_DELAY = 1000 

DATA_BUFFER_SIZE = 10000  
UPDATE_INTERVAL_MS = 1000
MAX_MEMORY_BUFFER_SIZE = 100000  