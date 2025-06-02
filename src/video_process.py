import os
import subprocess
from PIL import Image, ImageTk
from TransNetV2.transnet import TransNetV2
import cv2
import json
import argparse
from TransNetV2.inference import predict_video

def extract_frame(video_path, frame_idx):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)

def process_video(video_path: str, keyframe_dir: str, model: TransNetV2):
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    shots = predict_video(video_path, model)
    segment_metadata = []
    
    for idx, (start_frame, end_frame) in enumerate(shots):
    
        mid_frame = start_frame + (end_frame - start_frame) // 2
        img = extract_frame(video_path, mid_frame)
        if img is None:
            print(f"⚠️  Could not grab frame {mid_frame}")
            continue

        fname = f"{video_name}_{idx}.jpg"
        fpath = os.path.join(keyframe_dir, fname)
        img.save(fpath, "JPEG", quality=90)
        
        segment_metadata.append({
            "video_id": video_name,
            "segment_index": idx,
            "start_frame": int(start_frame),
            "end_frame": int(end_frame),
            "keyframe_path": fpath,
        })

    return segment_metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video preprocessing: shot detection and keyframe extraction")
    parser.add_argument("--input", "-i", required=True, help="Path to input video file or directory of videos")
    parser.add_argument("--output", "-o", default="output", help="Directory to store output segments and keyframes")
    args = parser.parse_args()
        
    metadata_path = os.path.join(args.output, "metadata")
    keyframe_path = os.path.join(args.output, "keyframes")
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(keyframe_path, exist_ok=True)
    model = TransNetV2()

    all_meta = []

    if os.path.isdir(args.input):
        for fname in os.listdir(args.input):
            if fname.lower().endswith(".mp4"):
                vp = os.path.join(args.input, fname)
                all_meta.extend(process_video(vp, keyframe_path, model))
    else:
        all_meta.extend(process_video(args.input, keyframe_path, model))

    # dump once
    with open(os.path.join(metadata_path, "predictions.json"), "w") as f:
        json.dump(all_meta, f, indent=2)