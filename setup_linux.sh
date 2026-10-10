#!/usr/bin/env bash
# One-shot setup for Debian/Ubuntu-based Linux.
set -e
sudo apt update
sudo apt install -y python3 python3-venv python3-pip v4l-utils libgl1 libglib2.0-0
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo
echo "Done. Activate with:  source venv/bin/activate"
echo "Then run:             python motion_cam.py"
echo "If the camera fails to open, run: sudo usermod -aG video \$USER   (then log out and back in)"
