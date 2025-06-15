#!/usr/bin/env python3
"""
Interactive frame-scrubber for constant-frame-rate video.

* GUI-safe: aborts early if HighGUI is not available
* Robust: copes with videos whose FRAME_COUNT metadata is 0
"""

import cv2
import sys
import os
from pathlib import Path

# ---------------- helpers --------------------------------------------------

def ms_from_frame(idx: int, fps: float) -> float:
    return idx * 1000.0 / fps if fps else 0.0

def draw_overlay(img, text, font_scale=0.7, thickness=2):
    overlay = img.copy()
    h, w = img.shape[:2]
    cv2.rectangle(overlay, (0, h - 40), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)
    cv2.putText(
        img, text, (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255),
        thickness, cv2.LINE_AA)

# --------------- main ------------------------------------------------------

def main(path):
    if not os.path.isfile(path):
        sys.exit(f"File not found: {path}")

    # Fail fast if this OpenCV build has no HighGUI support
    if not hasattr(cv2, "namedWindow"):
        sys.exit("Your OpenCV build lacks GUI support. "
                 "Install opencv-python, not opencv-python-headless.")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit("Could not open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Fallback: count frames manually if metadata is missing
    if total_frames <= 0:
        print("⚠️  Frame count unavailable; counting frames …")
        while True:
            grabbed = cap.grab()
            if not grabbed:
                break
            total_frames += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if total_frames == 0:
        sys.exit("Video appears to contain no frames.")

    win = "Frame selector – press 's' to save, 'Esc' to quit"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)  # keep it simple: no Qt-extras
    cur_idx = 0  # mutable via closure

    def on_trackbar(pos):
        nonlocal cur_idx
        cur_idx = pos
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ok, frame = cap.read()
        if not ok:
            return
        t_ms = ms_from_frame(pos, fps)
        draw_overlay(frame, f"{pos}/{total_frames-1}   {t_ms:.3f} ms")
        cv2.imshow(win, frame)

    max_val = max(1, total_frames - 1)       # never negative or zero
    cv2.createTrackbar("Frame", win, 0, max_val, on_trackbar)
    on_trackbar(0)                            # paint first frame

    while True:
        k = cv2.waitKey(20) & 0xFF
        if k == 27:                           # Esc
            print("No frame selected. Bye.")
            break
        if k == ord('s'):
            ts = ms_from_frame(cur_idx, fps)
            msg = f"Selected frame {cur_idx} at {ts:.3f} ms"
            print(msg)
            Path("selection.txt").write_text(msg + "\n")
            print("Wrote selection.txt")
            break

    cap.release()
    cv2.destroyAllWindows()

# --------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} video.mp4")
    main(sys.argv[1])
