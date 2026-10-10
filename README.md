# Live Motion Cam

A small Python project that opens your **own computer's webcam**, shows the live video, and detects **movement** (and optionally **people**) in real time using OpenCV.

## Features

- Live video from the front/webcam camera
- Motion detection with green boxes around moving areas
- Optional person detection (`--detect-people`)
- Auto-record clips only while motion is happening (`--record`)
- Snapshots on keypress, FPS and timestamp overlay
- Headless mode for servers/SSH (`--no-display`)

## Privacy note

This program only accesses a camera attached to the machine it runs on, and it shows a live window while running. Only use it on devices and spaces where you have the right to record people, and tell anyone who is being recorded.

## Requirements

- Python 3.8+
- A webcam
- Linux, macOS or Windows (Linux instructions below)

## Quick start on Linux (Ubuntu/Debian)

```bash
git clone https://github.com/<your-username>/live-motion-cam.git
cd live-motion-cam
./setup_linux.sh          # installs system packages + creates venv + installs OpenCV
source venv/bin/activate
python motion_cam.py
```

Manual setup instead of the script:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip v4l-utils libgl1 libglib2.0-0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python motion_cam.py
```

### Check your camera on Linux

```bash
ls /dev/video*              # list camera devices
v4l2-ctl --list-devices     # friendly names
```

If you get a permission error, add yourself to the `video` group and log out/in:

```bash
sudo usermod -aG video $USER
```

If `/dev/video0` is not your camera, pick another index: `python motion_cam.py --camera 1`.

Other distros: Fedora `sudo dnf install python3 v4l-utils`, Arch `sudo pacman -S python v4l-utils`.

## Usage

```bash
python motion_cam.py                         # live view + motion detection
python motion_cam.py --detect-people         # also detect people
python motion_cam.py --record                # auto-record clips during motion
python motion_cam.py --camera 1 --width 1280 --height 720
python motion_cam.py --no-display --record   # headless, Ctrl+C to stop
```

| Option | Default | Description |
|---|---|---|
| `--camera` | 0 | Camera index |
| `--width` / `--height` | 640 / 480 | Capture resolution |
| `--min-area` | 1500 | Ignore motion smaller than this (raise to reduce noise) |
| `--threshold` | 25 | Sensitivity (lower = more sensitive) |
| `--detect-people` | off | HOG person detector |
| `--record` | off | Auto-record while motion + cooldown |
| `--cooldown` | 3.0 | Seconds to keep recording after motion stops |
| `--output` | captures | Folder for snapshots/clips |
| `--no-display` | off | No window |

**Keys:** `q` or `ESC` quit, `s` snapshot, `r` toggle recording.

## Troubleshooting

- **"Could not open camera"**: check `ls /dev/video*`, the `video` group, and that no other app (Zoom, browser) is using the camera.
- **No window / `cv2.error` on a headless server**: use `--no-display`.
- **Too many false detections**: increase `--min-area` or `--threshold`, and keep the camera still.
- **Black or low-FPS video**: lower the resolution, or try a different `--camera` index.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Initial commit: live motion cam"
git branch -M main
git remote add origin https://github.com/<your-username>/live-motion-cam.git
git push -u origin main
```

(Create the empty `live-motion-cam` repository on github.com first, without a README.)

## How it works

1. OpenCV reads frames from the webcam (V4L2 backend on Linux).
2. A MOG2 background subtractor learns the static scene; moving pixels become a mask.
3. The mask is cleaned up and contours larger than `--min-area` are treated as motion.
4. Optionally, OpenCV's built-in HOG people detector marks people in blue.

## License

MIT
