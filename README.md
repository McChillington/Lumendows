# LumenOS
#  LINUX ONLY FOR NOW
A Python application for controlling addressable RGB lighting systems.

## Features

- Control ARGB lighting effects (Static, Rainbow, Breathe, Chase, Off)
- Adjust brightness and colors
- Serial communication with Arduino devices
- Real-time visualization
- Preset saving and loading

## Installation instructions
1. Make a new folder tp keep all files organized (recomended)
2. change directories to the folder
3. make python venv
   this is needed to install the packages. This step is required on Linux but not on windows. However it simplifies package managment so this step is recomended regardless.
   Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
Windows:
   ```bash
      python -m venv venv
      venv\Scripts\activate
```
5. Install dependencies:
      ```bash
         pip install PyQt5 pyserial Pillow pyinstaller

6. Run build.py:
   This script makes the application 
