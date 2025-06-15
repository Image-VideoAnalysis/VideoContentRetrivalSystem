#!/usr/bin/env python3
"""
print_fps.py  –  Print the nominal frame-rate of a video.

Usage:
    python print_fps.py <video_file>
"""

import sys
import cv2

def main(path: str) -> None:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit(f"Error: could not open {path!r}")

    fps = cap.get(cv2.CAP_PROP_FPS)        # float
    if not fps or fps <= 0:
        sys.exit("Warning: FPS not present or invalid in file metadata.")

    print(f"{path}: {fps:.3f} fps")
    cap.release()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python print_fps.py <video_file>")
    main(sys.argv[1])
