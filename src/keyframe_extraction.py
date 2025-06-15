import os
from PIL import Image
import numpy as np
import torch
from TransNetV2.transnet import TransNetV2
import cv2
import json
import argparse
from TransNetV2.inference import predict_video
from transformers import CLIPProcessor, CLIPModel
from sklearn.cluster import DBSCAN
import faiss

def fetch_nearest_decodable_frame(cap: cv2.VideoCapture,
                                  target: int,
                                  start: int,
                                  end: int,
                                  max_probe: int = 15) -> tuple[bool, np.ndarray]:
    """
    Try to grab `target` first.  If it fails, probe ±1, ±2, … up to `max_probe`
    frames (clamped to [start, end]) and return the first decodable frame.

    Returns (success_flag, frame_bgr).
    """
    
    # order: target, target+1, target-1, target+2, target-2, ...
    offsets = [0]
    for d in range(1, max_probe + 1):
        offsets.extend([d, -d])

    for off in offsets:
        probe = int(np.clip(target + off, start, end))
        cap.set(cv2.CAP_PROP_POS_FRAMES, probe)
        ok, frm = cap.read()
        if ok:
            return True, frm
    return False, None



def process_video(video_path: str, keyframe_dir: str, model: TransNetV2,  CLIP_model, processor, fallback_enabled: bool = False,):
    """
    Detect shots in `video_path`, extract one key-frame per shot,
    fallback to time-based sampling if keyframe density is too low,
    store them under  keyframe_dir/<video_name>/,
    and return a list of dictionaries with metadata.
    """
    predicted_fallback_keyframes = []
    
    try:
        # Derive a simple ID for the video (file name without suffix)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        # list of metadata that will be returned
        segment_metadata = []
        
        # Creating a per-video directory
        video_keyframe_dir = os.path.join(keyframe_dir, video_name)
        os.makedirs(video_keyframe_dir, exist_ok=True)
        
        # TransNetV2 returns an (N, 2) array of [start_frame, end_frame] for every detected shot
        with torch.no_grad():
            shots = np.array(predict_video(video_path, model))
            
        # OpenCV video handle, used to grab individual frames
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
    
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps
        print()
        print(f"Processing {video_name}: {frame_count} frames, {len(shots)} shots detected.")

            
        # Fallback if keyframe density is too low
        MIN_KEYFRAME_DENSITY = 1 / 10  # at least 1 every 20 sec
        FALLBACK_INTERVAL_SEC = 5
        actual_density = len(shots) / duration_sec
        
        if fallback_enabled and actual_density < MIN_KEYFRAME_DENSITY:
            print(f" Low keyframe density ({actual_density:.4f} keyframes/sec). Triggering fallback...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            interval_frames = int(FALLBACK_INTERVAL_SEC * fps)
            fallback_imgs   = []   # PIL images
            fallback_frames = []   # corresponding frame numbers
            
            for frame_idx in range(0, frame_count, interval_frames):
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                fallback_imgs.append(img)  
                fallback_frames.append(frame_idx)
        
            inputs = processor(images=fallback_imgs, return_tensors="pt", padding=True)
            with torch.no_grad():
                feats = CLIP_model.get_image_features(**inputs)
            # Normalize to unit length (L2)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            embeddings = feats.cpu().numpy().astype('float32')
            
            labels = DBSCAN(eps=0.1, min_samples=1, metric='cosine').fit_predict(embeddings)
            
            unique_lbls = [l for l in set(labels) if l != -1] # skip noise/outliers
            repr_idx = []                       # indices of the chosen key-frames

            for lbl in unique_lbls:
                idx   = np.where(labels == lbl)[0]    # frames in this cluster
                embs  = embeddings[idx]               # shape (m, 512)

                # cluster centroid (mean of unit vectors, still ≈ unit length)
                centroid = embs.mean(axis=0, keepdims=True)
                centroid /= np.linalg.norm(centroid, axis=1, keepdims=True)

                # cosine similarities to the centroid  (dot product because all unit-norm)
                sims = (embs @ centroid.T).ravel()

                best_local = idx[sims.argmax()]       # medoid index in the *global* list
                repr_idx.append(best_local)

            repr_idx.extend(np.where(labels == -1)[0])
            
            idx = 0
            for local_i in repr_idx:
                img = fallback_imgs[local_i]
                fr_no = fallback_frames[local_i]

                name  = f"{video_name}_fb_{fr_no}.jpg"
                path  = os.path.join(video_keyframe_dir, name)
                img.save(path, quality=95)

                segment_metadata.append({
                    "video_id"    : video_name,
                    "shot"        : idx,
                    "start_frame" : fr_no,
                    "end_frame"   : fr_no,
                    "start_time"  : fr_no / fps,
                    "end_time"    : fr_no / fps,
                    "keyframe_path": path,
                })
                idx+=1
        else:
            # Iterate over every shot boundary pair
            for idx, (start_frame, end_frame) in enumerate(shots):     
                
                # Rigth now using middle frame as keyframe, could be improved
                mid_frame = int(start_frame + ((end_frame - start_frame) // 2))
                
                # Skip if TransNetV2 produced an out-of-range index
                if mid_frame >= frame_count:
                    print(f"⚠️  mid-frame {mid_frame} beyond EOF – skipped")
                    continue
                
                # Find the middle frame and read it
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                
                # Try mid-frame first; fall back if necessary
                ret, frame = fetch_nearest_decodable_frame(
                                cap, target=mid_frame,
                                start=start_frame, end=end_frame)
                
                #  fallback: step back 1 frame once
                if not ret and mid_frame > start_frame:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame - 1)
                    ret, frame = cap.read()
                    
                if not ret:
                    print(f"⚠️  Could not grab any frame in shot {idx}")
                    continue

                
                # From OpenCV to RGB to PIL.Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Output file name:  <video>_<shot_idx>.jpg
                fname = f"{video_name}_{idx}.jpg"
                fpath = os.path.join(video_keyframe_dir, fname)
                img.save(fpath, quality=95)

                # Assemble per-shot metadata
                segment_metadata.append({
                    "video_id": video_name,
                    "shot": idx,
                    "start_frame": int(start_frame),
                    "end_frame": int(end_frame),
                    "start_time": float(start_frame / fps),
                    "end_time": float(end_frame   / fps),
                    "keyframe_path": fpath,
                })
        # Free the video file handle
        cap.release()

    except Exception as e:
        print(f"Error while analyzing {os.path.splitext(os.path.basename(video_path))[0]} with error: {e}")
    return segment_metadata


if __name__ == "__main__":
    # CLI arguments
    #   -i / --input   : video file or directory containing *.mp4
    #   -o / --output  : root folder for key-frames & metadata
    #   -fl/ --fallback : extract keyframes with a time-based subsampling
    parser = argparse.ArgumentParser(description="Video preprocessing: shot detection and keyframe extraction")
    parser.add_argument("--input", "-i", required=True, help="Path to input video file or directory of videos")
    parser.add_argument("--output", "-o", default="output", help="Directory to store output segments and keyframes")
    parser.add_argument("--fallback", "-fl", default=True, help="Boolean to enable fallback time-based keyframe sampling if density is too low")
    args = parser.parse_args()
    
    input_path = args.input
    
    # Output folder structure:
    #   <output>/keyframes/ will contains per-video sub-folders
    #   <output>/metadata/  will contains per-video JSON files
    metadata_path = os.path.join(args.output, "metadata")
    keyframe_path = os.path.join(args.output, "keyframes")
    os.makedirs(metadata_path, exist_ok=True)
    os.makedirs(keyframe_path, exist_ok=True)
    
    #Loading TransNet in eval mode
    model = TransNetV2()
    state_dict = torch.load("TransNetV2/transnetv2-pytorch-weights.pth")
    model.load_state_dict(state_dict)
    model.eval()
    
    CLIP_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    

    if os.path.isdir(input_path):
        for fname in os.listdir(input_path):
            if fname.lower().endswith(".mp4"):
                video_path = os.path.join(input_path, fname)
                segment_metadata = process_video(video_path, keyframe_path, model, CLIP_model, processor, args.fallback)
                
                # Write per-video metadata JSON
                video_name = os.path.splitext(fname)[0]
                meta_file  = os.path.join(metadata_path, f"{video_name}.json")
                with open(meta_file, "w") as f:
                    json.dump(segment_metadata, f, indent=2)
    else:
        segment_metadata = process_video(args.input, keyframe_path, model, CLIP_model, processor, args.fallback)
        video_name = os.path.splitext(os.path.basename(input_path))[0]
        meta_file = os.path.join(metadata_path, f"{video_name}.json")
        
        with open(meta_file, 'w') as f:
            json.dump(segment_metadata, f, indent=2)