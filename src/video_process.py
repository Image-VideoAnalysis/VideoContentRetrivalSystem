import os
import subprocess
from TransNetV2.transnet import TransNetV2
import cv2
import argparse



def process_video(video_path: str, output_dir: str):
    """
    Process a single video: detect shots, save shot segments and keyframes.
    Returns a list of metadata dicts for each segment.
    """
    # Determine video ID or name
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_id = video_name  # use filename (without extension) as video_id
    
    # Load TransNet V2 model
    model = TransNetV2()
    print(f"[TransNetV2] Detecting shots in {video_path} ...")
    # Run shot boundary detection
    # model.predict_video returns frame-wise predictions. We use predictions_to_scenes to get segments.
    video_frames, single_frame_predictions, all_frame_predictions = model.predict_video(video_path)
    shots = model.predictions_to_scenes(single_frame_predictions)
    
    # OpenCV video capture for frame extraction
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Prepare output directories
    seg_dir = os.path.join(output_dir, f"{video_id}_segments")
    keyframe_dir = os.path.join(output_dir, f"{video_id}_keyframes")
    os.makedirs(seg_dir, exist_ok=True)
    os.makedirs(keyframe_dir, exist_ok=True)
    
    segment_metadata = []
    for idx, (start_frame, end_frame) in enumerate(shots):
        # Calculate start and end times in seconds
        start_time = start_frame / fps
        end_time = end_frame / fps
        duration = end_time - start_time
        
        # File paths for output segment and keyframe
        segment_file = os.path.join(seg_dir, f"{video_id}_segment_{idx+1}.mp4")
        keyframe_file = os.path.join(keyframe_dir, f"{video_id}_keyframe_{idx+1}.jpg")
        
        # Use FFmpeg to cut the video segment
        # -ss and -to specify start and end; re-encode with H.264 for compatibility
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c:v", "libx264", "-c:a", "aac", "-preset", "veryfast",
            segment_file
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Extract keyframe at midpoint of the shot using OpenCV
        mid_frame = start_frame + (end_frame - start_frame)//2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(keyframe_file, frame)
        else:
            print(f"Warning: Could not extract frame at {mid_frame} for {video_id} shot {idx+1}")
        
        # Record metadata
        segment_metadata.append({
            "video_id": video_id,
            "segment_index": idx+1,
            "start_time": start_time,
            "end_time": end_time,
            "segment_path": os.path.abspath(segment_file),
            "keyframe_path": os.path.abspath(keyframe_file)
        })
    
    cap.release()
    print(f"Processed {len(segment_metadata)} segments for video {video_id}.")
    return segment_metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video preprocessing: shot detection and keyframe extraction")
    parser.add_argument("--input", "-i", required=True, help="Path to input video file or directory of videos")
    parser.add_argument("--output", "-o", default="output", help="Directory to store output segments and keyframes")
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    all_videos_metadata = []
    
    if os.path.isdir(args.input):
        # Process all video files in the directory
        for fname in os.listdir(args.input):
            if fname.lower().endswith((".mp4", ".avi", ".mkv", ".mov")):
                video_path = os.path.join(args.input, fname)
                meta = process_video(video_path, args.output)
                all_videos_metadata.extend(meta)
    else:
        # Process a single video file
        meta = process_video(args.input, args.output)
        all_videos_metadata.extend(meta)
    
    # Save metadata of all segments to a JSON file for reference
    import json
    meta_file = os.path.join(args.output, "segments_metadata.json")
    with open(meta_file, "w") as f:
        json.dump(all_videos_metadata, f, indent=4)
    print(f"Saved segment metadata to {meta_file}")