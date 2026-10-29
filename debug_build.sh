#!/bin/bash
# THIS CREATES A DEBUG BUILD FROM CURRENT SOURCE CODE! USE AT OWN RISK! PATHS WILL VERY LIKELY DIFFER FROM YOURS!
set -e # Exit on error

# Parse arguments
DEFAULT_OUT="/mnt/games/ED/EDXD_test/"
OUT_DIR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)
            OUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--out <output_directory>]"
            exit 1
            ;;
    esac
done
# Use default if --out was not provided
if [ -z "$OUT_DIR" ]; then
    OUT_DIR="$DEFAULT_OUT"
fi
# Ensure trailing slash so cp treats it as a directory
OUT_DIR="${OUT_DIR%/}/"

# --- CONFIGURATION ---
BASE_VERSION="!!!>>> DEBUG"

# Generate a timestamp: YYYY-MM-DD HH:MM
# Format options:
#   "+%Y-%m-%d %H:%M" -> 2026-04-15 14:30
#   "+%Y%m%d-%H%M"   -> 20260415-1430 (compact, no spaces)
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M-%S")

# Combine them
VERSION_STRING="$BASE_VERSION ($TIMESTAMP) <<<!!!"
# ---------------------

echo "🚀 Starting build for version: $VERSION_STRING"

# 1. Clean previous builds (Critical for detecting changes)
rm -rf build dist EDXD/_version.py

# 2. Inject the version
# Note: We escape the single quotes inside the Python string if needed,
# but since timestamps usually only contain numbers and colons/dashes,
# direct insertion into single quotes is safe.
echo "VERSION = '$VERSION_STRING'" > EDXD/_version.py

# Verify injection
if grep -q "$VERSION_STRING" EDXD/_version.py; then
    echo "✅ Version string injected successfully."
else
    echo "❌ Error: Failed to write version string."
    exit 1
fi

# 3. Prepare Environment
source .venv/bin/activate
pip install --upgrade pip
pip install pyinstaller
pip install -e .

# 4. Build
echo "📦 Compiling executable..."
pyinstaller --onefile EDXD/main.py --name ed-eXploration-dashboard

# 5. Deploy
echo "📂 Copying to target directory..."
mkdir -p "$OUT_DIR"
cp -fv ./dist/ed-eXploration-dashboard "$OUT_DIR"

# 6. Cleanup
rm EDXD/_version.py

echo "✅ Build complete!"
echo "   Version embedded: $VERSION_STRING"
