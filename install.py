#!/usr/bin/env python3
"""
Installation script for LumenOS
"""

import os
import shutil
import subprocess
import sys

def install_application():
    print("Installing LumenOS...")
    
    # Determine source and destination paths
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        source_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        source_dir = os.path.dirname(os.path.abspath(__file__))
    
    install_dir = os.path.expanduser("~/Applications/LumenOS")
    
    # Create installation directory
    os.makedirs(install_dir, exist_ok=True)
    
    # Copy files
    files_to_copy = ['LumenOS', 'LumenOS.png', 'LumenOS_config.json']
    for file in files_to_copy:
        source_path = os.path.join(source_dir, file)
        if os.path.exists(source_path):
            dest_path = os.path.join(install_dir, file)
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {file}")
    
    # Make executable
    executable_path = os.path.join(install_dir, 'LumenOS')
    os.chmod(executable_path, 0o755)
    
    # Create desktop entry
    create_desktop_entry(install_dir)
    
    print(f"\nInstallation complete! LumenOS is installed at: {install_dir}")
    print("You can now find 'LumenOS' in your application menu.")

def create_desktop_entry(install_dir):
    """Create desktop entry file"""
    desktop_content = f"""[Desktop Entry]
Version=1.0
Name=LumenOS
Comment=Control ARGB lighting systems
Exec={os.path.join(install_dir, 'LumenOS')}
Icon={os.path.join(install_dir, 'LumenOS.png')}
Terminal=false
Type=Application
Categories=Utility;
Keywords=argb;rgb;lighting;
StartupWMClass=LumenOS - ARGB Controller
"""
    
    desktop_path = os.path.expanduser("~/.local/share/applications/LumenOS.desktop")
    
    try:
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_path, 0o755)
        
        # Update desktop database
        subprocess.run(['update-desktop-database', os.path.expanduser('~/.local/share/applications')], 
                      check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Desktop entry created successfully")
    except Exception as e:
        print(f"Failed to create desktop entry: {e}")

if __name__ == '__main__':
    install_application()