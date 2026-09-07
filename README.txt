sudo apt update
sudo apt install -y python3-picamera2 python3-venv

cd ~
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python stream.py
