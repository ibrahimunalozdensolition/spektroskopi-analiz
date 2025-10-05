# Spectroscopy System User Guide

## Description

This advanced spectroscopy analysis application has been specially developed for **Prof. Dr. Uğur Aksu** to meet the requirements of modern analytical chemistry and spectroscopic research. The application provides comprehensive data acquisition, real-time analysis, and calibration capabilities for multi-wavelength spectroscopic measurements.

**🆕 Latest Update**: Automatic update system added - The application now checks for updates from GitHub automatically on startup!

### Key Features:
- **Multi-Sensor Support**: Simultaneous data collection from 4 different wavelength sensors (UV 360nm, Blue 450nm, IR 850nm, IR 940nm)
- **Real-Time Analysis**: Live data visualization and processing with customizable formulas
- **Advanced Calibration**: Precise calibration system with up to 5-point calibration curves
- **Data Export**: Professional CSV export functionality for further analysis
- **Custom Formula Engine**: Create complex mathematical formulas using sensor data
- **Professional Interface**: User-friendly PyQt5-based interface designed for laboratory use

This application represents a collaboration between advanced software engineering and analytical chemistry expertise, specifically tailored to support Prof. Dr. Uğur Aksu's research and educational activities in spectroscopic analysis.



## Main Controllers (Left-side management panel):

**Start:** Required for displaying calibrated data and creating graph screens. Data recording is also initiated.

**Stop:** When the Stop button is pressed, data recording is stopped.

**Calibration:** Provides calibration of data from 4 sensors. When this button is pressed, the "Calibration Panel" window opens.

### Calibration Panel

This window, which opens when the Calibration button is pressed, is used for calibrating spectroscopy sensors.

#### Sensor Selection:
- **Sensor to Calibrate:** Used to select the sensor to be calibrated
  - UV Sensor (360nm)
  - Blue Sensor (450nm) 
  - IR Sensor (850nm)
  - IR Sensor (940nm)
- **Molecule Name:** Enter the name of the molecule to be measured (optional)
- **Unit:** Enter the measurement unit (ppm, mg/L, mol/L, etc.)

#### Calibration Values Table:
- **No.:** Calibration point number (maximum 5 points)
- **Concentration:** Enter the known concentration value
- **Measured Value (V):** The voltage value measured from the sensor is automatically displayed
- **Status:** Status of the calibration point (Waiting/Saved/Loaded)
- **Action:** The calibration point is saved with the "OK" button

#### Control Panel:
- **CALIBRATE:** Becomes active after at least 3 points are saved, performs calibration calculation
- **Clear:** Clears all calibration data
- **Save:** Saves calibration data as a JSON file
- **Load:** Loads a previously saved calibration file
- **Close:** Closes the calibration window

#### Usage Steps:
1. Select the sensor to be calibrated
2. Enter the molecule name and unit
3. Enter the known concentration value
4. The sensor value will be updated automatically
5. Save the point by pressing the "OK" button
6. Repeat this process for at least 3 points
7. Complete the calibration by pressing the "CALIBRATE" button

**Export:** All data from the moment the Start button is pressed until the Stop button is pressed is exported in CSV format and made available for opening with Excel files. 

## Graph Windows:

**Raw Data:** Displays raw data from selected sensors on the screen in mV units.

**Calibrated Data:** Shows processed data resulting from the calibration process performed on the calibration screen for data from sensors.


## Real Time Panel:

Panel that displays data from 4 sensors in both calibrated and raw formats.

When made full screen, it grows without distorting the aspect ratio. Data is in scrollable format. On this screen, 4 sensors can be scrolled up and down together, providing comfortable viewing of the graphs.

## Custom Data Generator

How to use the formula-based data generation panel:

### Usage Steps:
1. First, write the name of the data you want to generate and write its formula.

### Operators and Functions You Can Use When Writing Formulas:
- **Operators:** +, -, *, /, (, )
- **Functions:** abs, max, min, sqrt, pow (exponentiation)

### Variables You Can Use When Writing Formulas:
- UV_360nm (ch1)
- Blue_450nm (ch2) 
- IR_850nm (ch3)
- IR_940nm (ch4)

### Units You Can Use When Writing Formulas:
- mV, Prime_Index, mol/L, Liter

### Example Formulas:
- `ch1 + ch2 + ch3` → Sum of UV, Blue and IR850 sensors (combined measurement of three wavelengths)
- `ch1 * 2.5 + ch2 * 1.8` → 2.5 times UV sensor + 1.8 times Blue sensor (weighted sum)
- `(ch1 + ch2) / 2` → Average of UV and Blue sensors (visible spectrum average)
- `ch1 - ch2` → Difference between UV and Blue sensor (spectral contrast)
- `abs(ch1 - ch3)` → Absolute difference between UV and IR850 (wavelength comparison)
- `max(ch1, ch2, ch3, ch4)` → Highest value among all sensors (maximum signal)
- `sqrt(ch1 * ch1 + ch2 * ch2)` → Geometric magnitude of UV and Blue sensors (vector length)(takes square root of output value)
- `pow(ch1, 2)` → Square of UV sensor (signal amplification, 3mV → 9)
- `ch1 * 0.85 + ch2 * 1.15 - 0.05` → Calibrated weighted sum (with offset correction)

### Live Mode:
Shows the result of the formula live while writing the formula. For the output of the generated formula to be obtained, both the data must be selected by double-clicking on the screen and live mode must be turned on. The reason for doing this process is to reduce processor load and provide performance on low-capacity computers. 

### Controls:
Importing another equation made with this program or exporting an existing equation. For use in other programs where this application exists. 

## Data Recording:

The purpose of the panel is to record data for 4 sensors for the selected duration (15 seconds by default).

This data is examined as raw_data and cal_data. If the threshold is more than 10% or less than 10% or between these two values, it gives an output in the form of a pop-up accordingly.

Which output is desired to be given, these texts are edited with the `status_messages.json` file located in the `config` folder.

### Editing Method:
- In the `sensor_order` section, as written, the states are written in the order in which the names of 4 sensors are written.
- After using the ":" sign, the message written in double quotes is shown when the desired state is achieved. 

### Comparison:
For comparison, two desired data are selected in the comparison section and the "Compare Selected Records" button is pressed. Then the comparison process is performed.

## About

The About screen provides information about the developer İbrahim ÜNAL, including both his email address and development motivation. It is also in the form of a short informational manifesto about application features. 



## Changing LED Names:

Name changes can be made from the `led_names` section in the `app_settings.json` file located on the main page.

The name given to the part that comes after the ":" sign (this applies to the inside of the quotation mark) will be applied when the application is restarted. 

