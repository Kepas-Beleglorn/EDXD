#!/bin/bash

GLIBC_VERSION=$(ldd --version | head -n1 | awk '{print $NF}')

echo "Your system's glibc version: $GLIBC_VERSION"
echo ""

# Parse version
MAJOR=$(echo $GLIBC_VERSION | cut -d. -f1)
MINOR=$(echo $GLIBC_VERSION | cut -d. -f2)
VERSION_NUM=$((MAJOR * 100 + MINOR))

if [ $VERSION_NUM -lt 235 ]; then
    echo "❌ Not compatible - glibc too old"
    echo "Recommended: Build from source with build.sh"
elif [ $VERSION_NUM -lt 239 ]; then
    echo "✅ Compatible with: edxd-dashboard-ubuntu-22.04.tar.gz"
    echo "   (Ubuntu 22.04, Linux Mint 21, etc.)"
elif [ $VERSION_NUM -lt 243 ]; then
    echo "✅ Compatible with: edxd-dashboard-ubuntu-24.04.tar.gz"
    echo "   (Ubuntu 24.04, Linux Mint 22, ZorinOS 17, etc.)"
else
    echo "✅ Compatible with: edxd-dashboard-ubuntu-latest.tar.gz"
    echo "   (Ubuntu 26.04+, newest distributions)"
fi
