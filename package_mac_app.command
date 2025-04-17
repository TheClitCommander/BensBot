#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Clear the terminal
clear

# Display header
echo "=========================================="
echo "    BENBOT DASHBOARD PACKAGER (macOS)    "
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 from python.org."
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Inform the user
echo "🔹 This script will package the BenBot Dashboard as a desktop application."
echo "🔹 This may take a few minutes."
echo ""

# Check for virtual environment or create one
if [ ! -d "packaging_venv" ]; then
    echo "📦 Creating a virtual environment for packaging..."
    python3 -m venv packaging_venv
    if [ ! -d "packaging_venv" ]; then
        echo "❌ Failed to create virtual environment. Please check your Python installation."
        echo "Press any key to exit..."
        read -n 1
        exit 1
    fi
else
    echo "📦 Using existing virtual environment..."
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source packaging_venv/bin/activate

# Install required packages in the virtual environment
echo "📦 Installing required packages in virtual environment..."
python -m pip install --upgrade pip
python -m pip install pyinstaller pillow

# Create app icon using the modified script
echo "🎨 Creating app icon..."
python - << 'ENDPYTHON'
try:
    import os
    from PIL import Image, ImageDraw
    
    if not os.path.exists("app_icon.png"):
        # Create a simple blue square icon with white border
        img = Image.new('RGB', (256, 256), color=(54, 130, 206))
        draw = ImageDraw.Draw(img)
        draw.rectangle((20, 20, 236, 236), outline=(255, 255, 255), width=10)
        draw.rectangle((60, 80, 196, 176), outline=(255, 255, 255), width=5)
        
        # Save the icon
        img.save("app_icon.png")
        print("✅ Created app icon: app_icon.png")
    else:
        print("✅ Using existing app icon")
except Exception as e:
    print(f"⚠️ Couldn't create icon: {e}")
    print("The app will use default PyInstaller icon")
ENDPYTHON

# Package the application
echo "🚀 Packaging application with PyInstaller..."
if [ -f "app_icon.png" ]; then
    # Convert PNG to ICNS for macOS
    if [ ! -f "app_icon.icns" ]; then
        if command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
            echo "🔄 Converting icon to macOS format..."
            # Create iconset directory
            mkdir -p app_icon.iconset
            # Generate different sizes
            sips -z 16 16 app_icon.png --out app_icon.iconset/icon_16x16.png >/dev/null 2>&1
            sips -z 32 32 app_icon.png --out app_icon.iconset/icon_32x32.png >/dev/null 2>&1
            sips -z 64 64 app_icon.png --out app_icon.iconset/icon_32x32@2x.png >/dev/null 2>&1
            sips -z 128 128 app_icon.png --out app_icon.iconset/icon_128x128.png >/dev/null 2>&1
            sips -z 256 256 app_icon.png --out app_icon.iconset/icon_128x128@2x.png >/dev/null 2>&1
            sips -z 256 256 app_icon.png --out app_icon.iconset/icon_256x256.png >/dev/null 2>&1
            sips -z 512 512 app_icon.png --out app_icon.iconset/icon_256x256@2x.png >/dev/null 2>&1
            sips -z 512 512 app_icon.png --out app_icon.iconset/icon_512x512.png >/dev/null 2>&1
            # Convert iconset to icns
            iconutil -c icns app_icon.iconset -o app_icon.icns
            rm -rf app_icon.iconset
            ICON_PARAM="--icon=app_icon.icns"
        else
            echo "⚠️ Icon conversion tools not found, using PNG icon"
            ICON_PARAM="--icon=app_icon.png"
        fi
    else
        ICON_PARAM="--icon=app_icon.icns"
    fi
    
    # Run PyInstaller with icon
    pyinstaller --name=BenBotDashboard --onefile --windowed --clean $ICON_PARAM simple_dashboard.py
else
    # Run PyInstaller without icon
    pyinstaller --name=BenBotDashboard --onefile --windowed --clean simple_dashboard.py
fi

# Deactivate virtual environment
deactivate

# Check if packaging was successful
if [ -d "dist/BenBotDashboard.app" ]; then
    echo ""
    echo "✅ Successfully created BenBotDashboard.app"
    
    # Ask to copy to Applications folder
    echo ""
    echo "Would you like to copy the app to your Applications folder? (y/n)"
    read -n 1 response
    echo ""
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp -R "dist/BenBotDashboard.app" "/Applications/"
        echo "✅ Copied to Applications folder. You can now run the app from there."
    else
        echo "You can manually copy dist/BenBotDashboard.app to your Applications folder."
    fi
    
    # Ask to copy to Desktop
    echo ""
    echo "Would you like to copy the app to your Desktop? (y/n)"
    read -n 1 response
    echo ""
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp -R "dist/BenBotDashboard.app" "$HOME/Desktop/"
        echo "✅ Copied to Desktop. You can now run the app from there."
    fi
else
    echo ""
    echo "❌ Something went wrong during packaging."
    echo "Check the output above for errors."
fi

echo ""
echo "Press any key to exit..."
read -n 1 