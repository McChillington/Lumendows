#!/usr/bin/env python3
"""
Build script for LumenOS
"""

import os
import subprocess
import sys
import shutil

def build_application():
    print("Building LumenOS...")
    
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Build with PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=LumenOS',
        '--icon=LumenOS.png',
        '--add-data=LumenOS.png:.',
        '--add-data=LumenOS_config.json:.',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=serial',
        '--hidden-import=serial.tools.list_ports',
        '--noconfirm',
        'LumenOS.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        print("STDERR:", result.stderr)
        return False
    
    print("Build successful!")
    
    # Copy additional files to dist directory
    files_to_copy = ['LumenOS.png', 'LumenOS_config.json']
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, 'dist/')
    
    print("Files copied to dist directory")
    print("\nTo run: ./dist/LumenOS")
    return True

if __name__ == '__main__':
    if build_application():
        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed!")
        sys.exit(1)