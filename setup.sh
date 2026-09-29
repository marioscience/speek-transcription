#!/usr/bin/env bash
set -e

echo "=> Checking system dependencies..."
MISSING_PKGS=""
for pkg in python3-venv python3-pip portaudio19-dev xdotool ydotool ffmpeg; do
    if ! dpkg -l | grep -qw "$pkg"; then
        MISSING_PKGS="$MISSING_PKGS $pkg"
    fi
done

if [ -n "$MISSING_PKGS" ]; then
    echo "=> Missing packages detected. Installing:$MISSING_PKGS"
    sudo apt update
    sudo apt install -y $MISSING_PKGS
else
    echo "=> All system packages are installed."
fi

echo "=> Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e .

echo "=> Setup complete! Run the app with: source .venv/bin/activate && speek"
