# LumenOS
# LINUX ONLY FOR NOW WINDOWS VERSION COMING SOON
A Python application for controlling addressable RGB lighting systems through an Arduino

## Features
Control ARGB lighting effects (Static, Rainbow, Breathe, Chase, Off)

Adjust brightness and colors

Serial communication with Arduino devices

Real-time visualization

Preset saving and loading

# Arduino
1. Connect pins
     On the ARGB connector this project is designed for there is 3 pins. The pinout is

   | PIN 1 (5v power) | PIN 2 (Signal) | GAP | PIN 3 (Ground) |

Connect PIN 1 to the 5V on the arduino, connect PIN 2 to pin DIGITAL 6, connect PIN 3 to GND.

2. Run LumenOS_arduino.ino
# Python
## Installation instructions
1. Make a new folder to keep all files organized (recommended)

2. Change directories to the new folder

3. Make a Python venv:
This is needed to install the packages.
```bash
python3 -m venv venv
source venv/bin/activate
```
4. Install dependencies:
```bash
pip install PyQt5 pyserial Pillow pyinstaller
```
5. Run build.py:
This script creates the .PKG file.

6. Run install.py (recommended):
This script adds the application to the app drawer for easier access.
