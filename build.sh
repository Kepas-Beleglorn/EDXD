#!/bin/bash
# Build script for ed-eXploration-dashboard
# This creates a binary from current source code.
set -e # Exit on error

# --- CONFIGURATION ---
PYTHON_VERSION="3.14"
OUTPUT_DIR="."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --out)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--out /output-path]"
            exit 1
            ;;
    esac
done

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# --- CHECK PYTHON INSTALLATION ---
echo "🔍 Checking Python $PYTHON_VERSION installation..."

if ! command -v python$PYTHON_VERSION &> /dev/null; then
    echo "❌ Python $PYTHON_VERSION is not installed."
    echo ""
    read -p "⚠️  Would you like to install Python $PYTHON_VERSION now? (requires sudo) [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing Python $PYTHON_VERSION..."
        sudo apt update
        sudo apt install python$PYTHON_VERSION python$PYTHON_VERSION-venv -y
        echo "✅ Python $PYTHON_VERSION installed successfully."
    else
        echo "⚠️  Python $PYTHON_VERSION is required. Aborting."
        exit 1
    fi
else
    PYTHON_PATH=$(which python$PYTHON_VERSION)
    echo "✅ Python $PYTHON_VERSION found at: $PYTHON_PATH"
fi

# --- EXTRACT VERSION FROM pyproject.toml ---
echo "📖 Reading version from pyproject.toml..."

if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found in current directory."
    exit 1
fi

VERSION=$(grep -m1 'version = ' pyproject.toml | sed 's/.*version = "\(.*\)".*/\1/')

if [ -z "$VERSION" ]; then
    echo "❌ Error: Could not extract version from pyproject.toml"
    exit 1
fi

echo "✅ Version: $VERSION"
echo ""

# --- CLEANUP AND BUILD ---
echo "🚀 Starting build..."

# 1. Clean previous builds
rm -rf build dist EDXD/_version.py

# 2. Inject the version
echo "VERSION = '$VERSION'" > EDXD/_version.py

# Verify injection
if grep -q "$VERSION" EDXD/_version.py; then
    echo "✅ Version injected successfully."
else
    echo "❌ Error: Failed to write version string."
    exit 1
fi

# 3. Prepare Environment
echo "📦 Preparing environment..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install pyinstaller > /dev/null 2>&1
pip install -e . > /dev/null 2>&1

# 4. Build
echo "🔨 Compiling executable..."
pyinstaller --onefile EDXD/main.py --name ed-eXploration-dashboard

# 5. Deploy
echo "📂 Copying to output directory..."
cp -fv ./dist/ed-eXploration-dashboard "$OUTPUT_DIR/"
cp -fv ./run_edxd.sh "$OUTPUT_DIR/"
chmod +x "$OUTPUT_DIR/run_edxd.sh"
echo "✅ Binary and run script placed at: $OUTPUT_DIR/"

# 6. Cleanup
rm EDXD/_version.py

echo ""
echo "✅ Build complete!"
echo "   Version: $VERSION"
echo "   Output directory: $OUTPUT_DIR"
