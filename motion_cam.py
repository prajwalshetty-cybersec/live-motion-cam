#!/usr/bin/env python3
"""Live Motion Cam: live webcam feed with motion and person detection.

Controls (when the window is shown):
    q / ESC  quit
    s        save a snapshot
    r        toggle recording
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2


def parse_args():
    p = argparse.ArgumentParser(description="Live webcam motion/person detection.")
    p.add_argument("--camera", type=int, default=0, help="camera index (default 0 = /dev/video0)")
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--min-area", type=int, default=1500, help="min contour area to count as motion")
    p.add_argument("--threshold", type=int, default=25, help="background subtractor sensitivity (lower = more sensitive)")
    p.add_argument("--detect-people", action="store_true", help="also run HOG person detection")
    p.add_argument("--record", action="store_true", help="auto-record clips while motion is detected")
    p.add_argument("--cooldown", type=float, default=3.0, help="seconds to keep recording after motion stops")
    p.add_argument("--output", default="captures", help="folder for snapshots and recordings")
    p.add_argument("--no-display", action="store_true", help="run without a window (headless, Ctrl+C to stop)")
    return p.parse_args()


def open_camera(index, width, height):
    backend = cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        sys.exit(
            f"Could not open camera {index}. On Linux check: ls /dev/video*, "
            "and that your user is in the 'video' group (see README)."
        )
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    args = parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = open_camera(args.camera, args.width, args.height)
    subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=args.threshold, detectShadows=True)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    hog = None
    if args.detect_people:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    writer = None
    recording = args.record
    last_motion = 0.0
    people = []
    frame_no = 0
    fps, t_prev = 0.0, time.time()
    warmup = 30  # frames used to learn the background

    print("Running. Press q/ESC in the window (or Ctrl+C) to quit.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame from camera.")
                break
            frame_no += 1

            # --- motion detection ---
            blur = cv2.GaussianBlur(frame, (21, 21), 0)
            mask = subtractor.apply(blur)
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)  # drop shadows
            mask = cv2.dilate(cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel), kernel, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion = False
            if frame_no > warmup:
                for c in contours:
                    if cv2.contourArea(c) < args.min_area:
                        continue
                    motion = True
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if motion:
                last_motion = time.time()

            # --- optional person detection (every 3rd frame, downscaled) ---
            if hog is not None and frame_no % 3 == 0:
                scale = 480 / frame.shape[1]
                small = cv2.resize(frame, None, fx=scale, fy=scale)
                rects, _ = hog.detectMultiScale(small, winStride=(8, 8), padding=(8, 8), scale=1.05)
                people = [(int(x / scale), int(y / scale), int(w / scale), int(h / scale)) for x, y, w, h in rects]
            for x, y, w, h in people:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, "person", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            # --- recording (auto: only while motion + cooldown; manual toggle: always) ---
            if args.record:
                should_write = recording and (time.time() - last_motion < args.cooldown)
            else:
                should_write = recording
            if should_write and writer is None:
                path = out_dir / f"clip_{stamp()}.mp4"
                writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20.0,
                                         (frame.shape[1], frame.shape[0]))
                print(f"Recording -> {path}")
            elif not should_write and writer is not None:
                writer.release()
                writer = None
                print("Recording stopped.")

            # --- overlay ---
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - t_prev, 1e-6))
            t_prev = now
            status = "MOTION" if motion else "idle"
            cv2.putText(frame, f"{status}  {fps:.0f} FPS{'  REC' if writer else ''}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if motion else (200, 200, 200), 2)
            cv2.putText(frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if writer is not None:
                writer.write(frame)

            if not args.no_display:
                try:
                    cv2.imshow("Live Motion Cam", frame)
                except cv2.error:
                    sys.exit("No display available. Re-run with --no-display (and --record).")
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    snap = out_dir / f"snap_{stamp()}.jpg"
                    cv2.imwrite(str(snap), frame)
                    print(f"Saved {snap}")
                if key == ord("r"):
                    recording = not recording
    except KeyboardInterrupt:
        pass
    finally:
        if writer is not None:
            writer.release()
        cap.release()
        cv2.destroyAllWindows()
        print("Bye.")


if __name__ == "__main__":
    main()
