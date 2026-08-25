#!/bin/bash
# Run script for ed-eXploration-dashboard
# Detects display server and sets appropriate environment
# only required for wayland compatibility

# --- DETECT DISPLAY SERVER ---
if [ -n "$WAYLAND_DISPLAY" ]; then
    echo "🖥️  Wayland detected. Forcing X11 backend..."
    GDK_BACKEND=x11 ./ed-eXploration-dashboard "$@"
else
    echo "🖥️  X11 detected."
    ./ed-eXploration-dashboard "$@"
fi
