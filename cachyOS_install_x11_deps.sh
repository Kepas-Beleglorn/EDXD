#!/bin/bash
# Install X11 packages for wxPython on CachyOS (non-interactive)

echo "🔄 Updating package database..."
sudo pacman -Sy

echo "📦 Installing X11 packages..."
sudo pacman -S --noconfirm xorg-server xorg-xrandr libx11 libxcb

if [ $? -eq 0 ]; then
    echo "✅ Installation complete!"
    echo "   Please log out and log back in for changes to take effect."
else
    echo "❌ Installation failed."
    echo "   Try checking CachyOS-specific package names:"
    echo "   pacman -Ss xorg | head -20"
    exit 1
fi
