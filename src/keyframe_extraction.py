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

# Constants
MIN_KEYFRAME_DENSITY = 1 / 10  # at least 1 keyframe every 10 sec
FALLBACK_INTERVAL_SEC = 5 # read frame every 5 sec
# End of constants

# tries to extract frames in this order: target, target+1, target-1, target+2, target-2, ...
def fetch_nearest_decodable_frame(cap: cv2.VideoCapture,
                                  target: int,
                                  start: int,
                                  end: int,
                                  max_probe: int = 15) -> tuple[bool, np.ndarray]:
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



def process_video(video_path: str, 
                  keyframe_dir: str, 
                  model: TransNetV2,  
                  CLIP_model, processor, 
                  fallback_enabled: bool = False,):
    try:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        segment_metadata = []
        video_keyframe_dir = os.path.join(keyframe_dir, video_name)
        os.makedirs(video_keyframe_dir, exist_ok=True)
        
        # Calling TransNet for shot boundary detection
        with torch.no_grad():
            shots = np.array(predict_video(video_path, model))
            
        # OpenCV video handle
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps
        print()
        print(f"Processing {video_name}: {frame_count} frames, {len(shots)} shots detected.")
        actual_density = len(shots) / duration_sec
        
        if fallback_enabled and actual_density < MIN_KEYFRAME_DENSITY: # fallback if keyframe density is too low
            
            print(f" Low keyframe density ({actual_density:.4f} keyframes/sec). Triggering fallback...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            interval_frames = int(FALLBACK_INTERVAL_SEC * fps)
            fallback_imgs   = []   
            fallback_frames = [] 
            
            # select frames every FALLBACK_INTERVAL_SEC seconds
            for frame_idx in range(0, frame_count, interval_frames):
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    # keep going if problems reading
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                fallback_imgs.append(img)  
                fallback_frames.append(frame_idx)

            # clustering phase of fallback: create clusters from keyframes and, for each, 
            # extract one (representative) keyframe
            
            # using CLIP to get embedding of each "fallback" keyframe
            inputs = processor(images=fallback_imgs, return_tensors="pt", padding=True)
            with torch.no_grad():
                feats = CLIP_model.get_image_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            embeddings = feats.cpu().numpy().astype('float32')
            
            # clustering with DBSCAN using cosine similarity
            labels = DBSCAN(eps=0.1, min_samples=1, metric='cosine').fit_predict(embeddings)
            # skip noise/outliers
            unique_lbls = [l for l in set(labels) if l != -1] 
            repr_idx = []               

            # iterate each cluster
            for lbl in unique_lbls:
                idx   = np.where(labels == lbl)[0]  
                embs  = embeddings[idx]               

                # find centroid 
                centroid = embs.mean(axis=0, keepdims=True)
                centroid /= np.linalg.norm(centroid, axis=1, keepdims=True)

                # find keyframe more similar to centroid
                sims = (embs @ centroid.T).ravel()
                best_local = idx[sims.argmax()]
                repr_idx.append(best_local)

            repr_idx.extend(np.where(labels == -1)[0])
            
            idx = 0
            # save results
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
                
        else: # normal flow
            
            # Iterate over every shot boundary pair
            for idx, (start_frame, end_frame) in enumerate(shots):     
                
                # using middle frame as keyframe
                mid_frame = int(start_frame + ((end_frame - start_frame) // 2))
                
                # Skip if TransNet produced an out-of-range index
                if mid_frame >= frame_count:
                    print(f"mid-frame {mid_frame} beyond EOF")
                    continue
                
                # Find the middle frame and read it
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                
                # try first to extract middle frame, move around it if there are problems
                ret, frame = fetch_nearest_decodable_frame(
                                cap, target=mid_frame,
                                start=start_frame, end=end_frame)
                
                if not ret:
                    print(f"Could not grab any frame in shot {idx}")
                    continue
                
                # converting BGR to RGB to ensure correct colors
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Output file name:  <video>_<shot_idx>.jpg
                fname = f"{video_name}_{idx}.jpg"
                fpath = os.path.join(video_keyframe_dir, fname)
                img.save(fpath, quality=95)

                # per-shot metadata
                segment_metadata.append({
                    "video_id": video_name,
                    "shot": idx,
                    "start_frame": int(start_frame),
                    "end_frame": int(end_frame),
                    "start_time": float(start_frame / fps),
                    "end_time": float(end_frame   / fps),
                    "keyframe_path": fpath,
                })
        cap.release()

    except Exception as e:
        print(f"Error while analyzing {os.path.splitext(os.path.basename(video_path))[0]} with error: {e}")
    return segment_metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video preprocessing: shot detection and keyframe extraction")
    parser.add_argument("-i", required=True, help="Path to input video file or directory of videos")
    parser.add_argument("-o", default="output", help="Directory to store output segments and keyframes")
    parser.add_argument("-fl", default=True, help="Boolean to enable fallback time-based keyframe sampling if density is too low")
    args = parser.parse_args()
    input_path = args.input
    

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
        
        #Iterate on all videos in the directory
        for fname in os.listdir(input_path):
            
            if fname.lower().endswith(".mp4"):
                video_path = os.path.join(input_path, fname)
                #Extract keyframes for single video
                segment_metadata = process_video(video_path, keyframe_path, model, CLIP_model, processor, args.fallback)
                
                video_name = os.path.splitext(fname)[0]
                meta_file  = os.path.join(metadata_path, f"{video_name}.json")
                with open(meta_file, "w") as f:
                    json.dump(segment_metadata, f, indent=2)
                    
    else: # processing a file and not a directory of videos
        
        segment_metadata = process_video(args.input, keyframe_path, model, CLIP_model, processor, args.fallback)
        video_name = os.path.splitext(os.path.basename(input_path))[0]
        meta_file = os.path.join(metadata_path, f"{video_name}.json")
        
        with open(meta_file, 'w') as f:
            json.dump(segment_metadata, f, indent=2)