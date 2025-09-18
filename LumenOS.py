import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QComboBox, 
                             QLabel, QGroupBox, QColorDialog, QFrame, QScrollArea,
                             QGridLayout, QSizePolicy, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
import json
import os
import math
import time
import subprocess

# Fix for taskbar pinning and working directory issues
if getattr(sys, 'frozen', False):
    # Running as compiled executable - change to executable directory
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
else:
    # Running as script - use script directory
    application_path = os.path.dirname(os.path.abspath(__file__))

class ARGBController(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("LumenOS - ARGB Controller")
        self.setGeometry(100, 100, 900, 800)
        
        # Set application icon
        self.set_application_icon()
        
        # Create desktop entry on first run
        self.create_desktop_entry()
        
        self.serial_port = None
        self.current_color = QColor(255, 255, 255)
        self.current_brightness = 100
        self.current_effect = "Static"
        self.config_file = "LumenOS_config.json"
        self.rainbow_offset = 0
        self.breathe_value = 0
        self.chase_position = 0
        
        self.init_ui()
        self.load_config()
        self.scan_serial_ports()
        self.auto_connect_arduino()
        
    def set_application_icon(self):
        """Set application icon using multiple methods for compatibility"""
        icon_paths = [
            'LumenOS.png',
            os.path.join(application_path, 'LumenOS.png'),
            os.path.join(os.path.dirname(sys.executable), 'LumenOS.png'),
        ]
        
        for path in icon_paths:
            try:
                if os.path.exists(path):
                    self.setWindowIcon(QIcon(path))
                    QApplication.setWindowIcon(QIcon(path))
                    print(f"Icon loaded from: {path}")
                    break
            except Exception as e:
                print(f"Failed to load icon from {path}: {e}")
                continue
    
    def create_desktop_entry(self):
        """Create desktop entry file for application menu integration"""
        # Get the correct executable path
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
        else:
            executable_path = os.path.join(application_path, 'LumenOS.py')
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Name=LumenOS
Comment=Control ARGB lighting systems
Exec={executable_path}
Icon={os.path.join(application_path, 'LumenOS.png')}
Terminal=false
Type=Application
Categories=Utility;
Keywords=argb;rgb;lighting;
StartupWMClass=LumenOS - ARGB Controller
"""
        
        desktop_path = os.path.expanduser("~/.local/share/applications/LumenOS.desktop")
        
        try:
            os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
            if not os.path.exists(desktop_path):
                with open(desktop_path, 'w') as f:
                    f.write(desktop_content)
                os.chmod(desktop_path, 0o755)
                # Update desktop database
                subprocess.run(['update-desktop-database', os.path.expanduser('~/.local/share/applications')], 
                              check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Desktop entry created successfully")
        except Exception as e:
            print(f"Note: Could not create desktop entry: {e}")
    
    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for device and mode selection
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(5, 5, 5, 5)
        
        # Device selection
        device_group = QGroupBox("Device Configuration")
        device_layout = QVBoxLayout()
        
        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.scan_serial_ports)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        device_layout.addWidget(QLabel("Serial Port:"))
        device_layout.addWidget(self.port_combo)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addWidget(self.connect_btn)
        device_group.setLayout(device_layout)
        left_panel.addWidget(device_group)
        
        # Mode selection
        mode_group = QGroupBox("Effects")
        mode_layout = QVBoxLayout()
        
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["Static", "Rainbow", "Breathe", "Chase", "Off"])
        self.effect_combo.currentTextChanged.connect(self.effect_changed)
        
        mode_layout.addWidget(QLabel("Select Effect:"))
        mode_layout.addWidget(self.effect_combo)
        mode_group.setLayout(mode_layout)
        left_panel.addWidget(mode_group)
        
        # Color selection
        color_group = QGroupBox("Color")
        color_layout = QVBoxLayout()
        
        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.select_color)
        
        # Color preview
        self.color_preview = QLabel()
        self.color_preview.setFixedHeight(40)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray;")
        
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.color_preview)
        color_group.setLayout(color_layout)
        left_panel.addWidget(color_group)
        
        # Brightness control
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QVBoxLayout()
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.setValue(self.current_brightness)
        self.brightness_slider.valueChanged.connect(self.brightness_changed)
        
        self.brightness_label = QLabel(f"Brightness: {self.current_brightness}")
        
        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_slider)
        brightness_group.setLayout(brightness_layout)
        left_panel.addWidget(brightness_group)
        
        # Presets and actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.save_btn = QPushButton("Save Preset")
        self.save_btn.clicked.connect(self.save_preset)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        
        action_layout.addWidget(self.apply_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.test_btn)
        action_group.setLayout(action_layout)
        left_panel.addWidget(action_group)
        
        # Add stretch to push everything to the top
        left_panel.addStretch()
        
        # Right panel for visualization and debug
        right_panel = QVBoxLayout()
        
        # Visualization area - simulated fans
        vis_group = QGroupBox("Visualization")
        vis_layout = QVBoxLayout()
        
        # Create a scroll area for visualization
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        
        # Create fan visualizations (2 fans with 12 LEDs each)
        self.led_widgets = []
        for fan_idx in range(2):
            fan_group = QGroupBox(f"Fan {fan_idx + 1}")
            fan_layout = QVBoxLayout()
            
            # Create a grid of LEDs
            led_grid = QGridLayout()
            led_grid.setSpacing(5)
            
            for led_idx in range(12):
                row = led_idx // 4
                col = led_idx % 4
                
                led = QLabel()
                led.setFixedSize(30, 30)
                led.setStyleSheet("background-color: black; border: 1px solid gray; border-radius: 15px;")
                led_grid.addWidget(led, row, col)
                self.led_widgets.append(led)
            
            fan_layout.addLayout(led_grid)
            fan_group.setLayout(fan_layout)
            scroll_layout.addWidget(fan_group, 0, fan_idx)
        
        scroll.setWidget(scroll_content)
        vis_layout.addWidget(scroll)
        vis_group.setLayout(vis_layout)
        right_panel.addWidget(vis_group)
        
        # Debug console
        debug_group = QGroupBox("Debug Console")
        debug_layout = QVBoxLayout()
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setReadOnly(True)
        
        debug_layout.addWidget(self.debug_text)
        debug_group.setLayout(debug_layout)
        right_panel.addWidget(debug_group)
        
        # Status area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.connection_status = QLabel("Not connected to any device")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.connection_status)
        status_group.setLayout(status_layout)
        right_panel.addWidget(status_group)
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(300)
        
        main_layout.addWidget(left_widget)
        main_layout.addLayout(right_panel)
        
        # Set up a timer to update visualization
        self.viz_timer = QTimer()
        self.viz_timer.timeout.connect(self.update_visualization)
        self.viz_timer.start(100)  # Update every 100ms
        
    def log_debug(self, message):
        """Add a message to the debug console"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        self.debug_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.debug_text.verticalScrollBar().setValue(
            self.debug_text.verticalScrollBar().maximum()
        )
        
    def scan_serial_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)
        self.log_debug(f"Found {len(ports)} serial ports")
    
    def auto_connect_arduino(self):
        """Automatically find and connect to an Arduino device."""
        self.log_debug("Attempting to auto-connect to Arduino...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Check for common Arduino identifiers
            if "Arduino" in port.description or (port.vid == 0x2341 or port.pid == 0x0043):
                self.log_debug(f"Found potential Arduino device at {port.device}")
                self.port_combo.setCurrentText(port.device)
                self.toggle_connection()
                return # Exit after connecting to the first one found
        self.log_debug("No Arduino device found for auto-connection.")

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connection_status.setText("Not connected to any device")
            self.log_debug("Disconnected from serial port")
        else:
            selected_port = self.port_combo.currentText()
            if selected_port:
                try:
                    self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                    # Add a small delay to allow the connection to establish
                    time.sleep(2)
                    self.connect_btn.setText("Disconnect")
                    self.status_label.setText("Connected")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connection_status.setText(f"Connected to {selected_port} at 9600 baud")
                    self.log_debug(f"Connected to {selected_port} at 9600 baud")
                    
                    # Clear any pending data in the serial buffer
                    self.serial_port.reset_input_buffer()
                    
                    # Send test command to verify communication
                    self.serial_port.write("get status\n".encode())
                    time.sleep(0.5)
                    if self.serial_port.in_waiting:
                        response = self.serial_port.readline().decode().strip()
                        self.log_debug(f"Arduino response: {response}")
                    
                except serial.SerialException as e:
                    error_msg = f"Failed to connect: {str(e)}"
                    self.log_debug(error_msg)
                    QMessageBox.critical(self, "Connection Error", error_msg)
            else:
                self.log_debug("No serial port selected")
                QMessageBox.warning(self, "No Port Selected", "Please select a serial port first.")
    
    def test_connection(self):
        """Test the serial connection by sending a simple command"""
        if not self.serial_port or not self.serial_port.is_open:
            self.log_debug("Not connected to any device")
            return
            
        try:
            self.log_debug("Testing connection...")
            self.serial_port.write("get status\n".encode())
            
            # Wait for response
            time.sleep(0.5)
            if self.serial_port.in_waiting:
                response = self.serial_port.readline().decode().strip()
                self.log_debug(f"Test response: {response}")
            else:
                self.log_debug("No response from Arduino")
                
        except Exception as e:
            self.log_debug(f"Test failed: {str(e)}")
    
    def select_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Select LED Color")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray;")
            self.log_debug(f"Selected color: R={color.red()}, G={color.green()}, B={color.blue()}")
    
    def brightness_changed(self, value):
        self.current_brightness = value
        self.brightness_label.setText(f"Brightness: {value}")
        self.log_debug(f"Brightness changed to: {value}")
    
    def effect_changed(self, effect_name):
        self.current_effect = effect_name
        self.log_debug(f"Effect changed to: {effect_name}")
        
        # Enable/disable color selection based on effect
        if effect_name in ["Rainbow", "Off"]:
            self.color_btn.setEnabled(False)
        else:
            self.color_btn.setEnabled(True)
    
    def apply_settings(self):
        if not self.serial_port or not self.serial_port.is_open:
            self.log_debug("Cannot apply settings: Not connected to device")
            QMessageBox.warning(self, "Not Connected", "Please connect to a device first.")
            return
        
        try:
            # Clear any pending data
            self.serial_port.reset_input_buffer()
            
            # Set brightness
            brightness_cmd = f"set brightness {self.current_brightness}\n"
            self.serial_port.write(brightness_cmd.encode())
            self.log_debug(f"Sent: {brightness_cmd.strip()}")
            time.sleep(0.1)
            
            # Set effect
            if self.current_effect == "Static":
                r, g, b = self.current_color.red(), self.current_color.green(), self.current_color.blue()
                color_cmd = f"set color {r} {g} {b}\n"
                self.serial_port.write(color_cmd.encode())
                self.log_debug(f"Sent: {color_cmd.strip()}")
                time.sleep(0.1)
                
                effect_cmd = "effect static\n"
                self.serial_port.write(effect_cmd.encode())
                self.log_debug(f"Sent: {effect_cmd.strip()}")
                
            elif self.current_effect == "Rainbow":
                effect_cmd = "effect rainbow\n"
                self.serial_port.write(effect_cmd.encode())
                self.log_debug(f"Sent: {effect_cmd.strip()}")
                
            elif self.current_effect == "Breathe":
                r, g, b = self.current_color.red(), self.current_color.green(), self.current_color.blue()
                effect_cmd = f"effect breathe {r} {g} {b}\n"
                self.serial_port.write(effect_cmd.encode())
                self.log_debug(f"Sent: {effect_cmd.strip()}")
                
            elif self.current_effect == "Chase":
                r, g, b = self.current_color.red(), self.current_color.green(), self.current_color.blue()
                effect_cmd = f"effect chase {r} {g} {b}\n"
                self.serial_port.write(effect_cmd.encode())
                self.log_debug(f"Sent: {effect_cmd.strip()}")
                
            elif self.current_effect == "Off":
                effect_cmd = "effect off\n"
                self.serial_port.write(effect_cmd.encode())
                self.log_debug(f"Sent: {effect_cmd.strip()}")
            
            # Check for response
            time.sleep(0.5)
            if self.serial_port.in_waiting:
                response = self.serial_port.readline().decode().strip()
                self.log_debug(f"Arduino response: {response}")
                
        except serial.SerialException as e:
            error_msg = f"Failed to send command: {str(e)}"
            self.log_debug(error_msg)
            QMessageBox.critical(self, "Communication Error", error_msg)
    
    def save_preset(self):
        # Save current settings to config file
        config = {
            "color": {
                "r": self.current_color.red(),
                "g": self.current_color.green(),
                "b": self.current_color.blue()
            },
            "brightness": self.current_brightness,
            "effect": self.current_effect
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            self.log_debug("Preset saved successfully")
            QMessageBox.information(self, "Preset Saved", "Current settings have been saved.")
        except Exception as e:
            error_msg = f"Failed to save preset: {str(e)}"
            self.log_debug(error_msg)
            QMessageBox.critical(self, "Save Error", error_msg)
    
    def load_config(self):
        # Load settings from config file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                if "color" in config:
                    color = config["color"]
                    self.current_color = QColor(color["r"], color["g"], color["b"])
                    self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray;")
                
                if "brightness" in config:
                    self.current_brightness = config["brightness"]
                    self.brightness_slider.setValue(self.current_brightness)
                    self.brightness_label.setText(f"Brightness: {self.current_brightness}")
                
                if "effect" in config:
                    self.current_effect = config["effect"]
                    index = self.effect_combo.findText(self.current_effect)
                    if index >= 0:
                        self.effect_combo.setCurrentIndex(index)
                
                self.log_debug("Configuration loaded from file")
                        
            except Exception as e:
                self.log_debug(f"Error loading config: {e}")
    
    def reset_defaults(self):
        # Reset to default settings
        self.current_color = QColor(255, 255, 255)
        self.current_brightness = 100
        self.current_effect = "Static"
        
        self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray;")
        self.brightness_slider.setValue(self.current_brightness)
        self.brightness_label.setText(f"Brightness: {self.current_brightness}")
        self.effect_combo.setCurrentText("Static")
        
        self.log_debug("Reset to default settings")
        
        # Apply defaults to device if connected
        if self.serial_port and self.serial_port.is_open:
            self.apply_settings()
    
    def update_visualization(self):
        # Update LED visualization based on current settings
        if self.current_effect == "Off":
            for led in self.led_widgets:
                led.setStyleSheet("background-color: black; border: 1px solid gray; border-radius: 15px;")
        elif self.current_effect == "Static":
            color_style = f"background-color: {self.current_color.name()}; border: 1px solid gray; border-radius: 15px;"
            for led in self.led_widgets:
                led.setStyleSheet(color_style)
        elif self.current_effect == "Rainbow":
            # Simulate rainbow effect
            self.rainbow_offset = (self.rainbow_offset + 5) % 256
            for i, led in enumerate(self.led_widgets):
                hue = (i * 256 / len(self.led_widgets) + self.rainbow_offset) % 256
                color = QColor.fromHsv(int(hue), 255, self.current_brightness)
                led.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray; border-radius: 15px;")
        elif self.current_effect == "Breathe":
            # Simulate breathe effect
            self.breathe_value = (self.breathe_value + 0.05) % (2 * math.pi)
            intensity = (math.sin(self.breathe_value) + 1) / 2  # Value between 0 and 1
            r = int(self.current_color.red() * intensity)
            g = int(self.current_color.green() * intensity)
            b = int(self.current_color.blue() * intensity)
            color = QColor(r, g, b)
            for led in self.led_widgets:
                led.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray; border-radius: 15px;")
        elif self.current_effect == "Chase":
            # Simulate chase effect
            self.chase_position = (self.chase_position + 1) % len(self.led_widgets)
            for i, led in enumerate(self.led_widgets):
                if (i - self.chase_position) % 12 < 4:  # 4 LEDs lit at a time
                    led.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray; border-radius: 15px;")
                else:
                    led.setStyleSheet("background-color: black; border: 1px solid gray; border-radius: 15px;")
    
    def closeEvent(self, event):
        # Clean up on exit
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.log_debug("Serial port closed on exit")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application icon
    icon_paths = [
        'LumenOS.png',
        os.path.join(application_path, 'LumenOS.png'),
    ]
    
    for path in icon_paths:
        try:
            if os.path.exists(path):
                app.setWindowIcon(QIcon(path))
                break
        except:
            continue
    
    controller = ARGBController()
    controller.show()
    
    sys.exit(app.exec_())