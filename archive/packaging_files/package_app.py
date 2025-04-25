#!/usr/bin/env python3
"""
Package the simple dashboard as a desktop application
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])  # For icon handling

def create_app_icon():
    """Create a simple app icon if none exists"""
    if os.path.exists("app_icon.png"):
        return
    
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple blue square icon with white border
        img = Image.new('RGB', (256, 256), color=(54, 130, 206))
        draw = ImageDraw.Draw(img)
        draw.rectangle((20, 20, 236, 236), outline=(255, 255, 255), width=10)
        draw.rectangle((60, 80, 196, 176), outline=(255, 255, 255), width=5)
        
        # Save the icon
        img.save("app_icon.png")
        print("Created app icon: app_icon.png")
    except Exception as e:
        print(f"Couldn't create icon: {e}")
        print("The app will use default PyInstaller icon")

def package_app():
    """Package the app using PyInstaller"""
    
    # Determine platform-specific settings
    system = platform.system()
    print(f"Packaging for {system} platform...")
    
    # Basic PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=TradingDashboard",
        "--onefile",
        "--windowed",  # No console window
        "--clean",
    ]
    
    # Add icon if available
    if os.path.exists("app_icon.png"):
        if system == "Darwin":  # macOS
            # Convert to icns for macOS
            try:
                if not os.path.exists("app_icon.icns"):
                    subprocess.check_call([
                        "sips", "-s", "format", "icns", 
                        "app_icon.png", "--out", "app_icon.icns"
                    ])
                pyinstaller_cmd.extend(["--icon=app_icon.icns"])
            except Exception as e:
                print(f"Couldn't convert icon: {e}")
                print("Using original PNG icon")
                pyinstaller_cmd.extend(["--icon=app_icon.png"])
        else:
            pyinstaller_cmd.extend(["--icon=app_icon.png"])
    
    # Add the main script
    pyinstaller_cmd.append("simple_dashboard.py")
    
    # Run PyInstaller
    print("Running PyInstaller with command:")
    print(" ".join(pyinstaller_cmd))
    subprocess.check_call(pyinstaller_cmd)
    
    print("\nApplication packaged successfully!")
    
    # Provide location of the executable
    if system == "Darwin":  # macOS
        app_path = Path("dist/TradingDashboard.app")
    elif system == "Windows":
        app_path = Path("dist/TradingDashboard.exe")
    else:  # Linux
        app_path = Path("dist/TradingDashboard")
    
    print(f"\nYou can find your application at: {app_path.absolute()}")
    print("\nYou can now distribute this file to run the dashboard as a desktop application.")

def main():
    """Main script function"""
    print("=== Packaging Trading Dashboard as Desktop Application ===\n")
    
    # Install dependencies
    install_dependencies()
    
    # Create app icon
    create_app_icon()
    
    # Package the application
    package_app()

if __name__ == "__main__":
    main() 