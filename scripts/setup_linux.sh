#!/usr/bin/env bash
# Headless Linux Automated Setup for Strata Desktop MoE (PRJ-17)
# Supports Arch Linux / Omarchy and Ubuntu 24.04

set -euo pipefail

echo "=== Setting up Strata Desktop MoE on Headless Linux ==="

# 1. Detect Package Manager and Install Dependencies
if command -v pacman &>/dev/null; then
    echo "Detected Arch / Omarchy Linux..."
    sudo pacman -S --needed --noconfirm base-devel git python python-pip cuda
elif command -v apt-get &>/dev/null; then
    echo "Detected Debian / Ubuntu Linux..."
    sudo apt-get update
    sudo apt-get install -y build-essential git python3 python3-pip python3-venv
fi

# 2. Setup Python venv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 3. Clone Strata upstream
if [ ! -d "engine" ]; then
    echo "Cloning upstream Strata engine..."
    git clone https://github.com/Niko1221/Strata.git engine
fi

# 4. Permissions and IPC lock
echo "Configuring memlock limits in /etc/security/limits.d/99-strata.conf..."
sudo tee /etc/security/limits.d/99-strata.conf > /dev/null << 'EOF'
* soft memlock unlimited
* hard memlock unlimited
EOF

echo "Setup complete. To launch Strata on Headless Linux:"
echo "cd engine && ./setup.sh --family coder --context 65536 --draft-vocab en --low-ram resident --calibrate"
