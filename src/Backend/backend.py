from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import clip
import faiss
import json
import numpy as np
import uvicorn
import os
from typing import List, Optional
from fastapi.staticfiles import StaticFiles


app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP model
clip_model, preprocess = clip.load("ViT-L/14", device=device)
# Load Faiss index
index = faiss.read_index("../image_index.faiss")
metadata = []

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

keyframes_dir = os.path.abspath("../../../SBDresults/keyframes")

# Serve the keyframes at `/keyframes`
app.mount("/keyframes", StaticFiles(directory=keyframes_dir), name="keyframes")

# Response models
class VideoMetadata(BaseModel):
    video_id: str
    shot: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    keyframe_path: str

class SearchResult(BaseModel):
    image_path: str
    score: float
    index: int
    metadata: Optional[VideoMetadata] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int

@app.on_event("startup")
def load_resources():
    global metadata  # Fix: make metadata global
    
    print("Loading resources...")
    
    print(f"CLIP model loaded on {device}")    
    print(f"Faiss index loaded with {index.ntotal} vectors")
    
    # Load metadata from all JSON files in the folder
    metadata_dir = "../../../SBDresults/metadata/"
    metadata = []
    
    if os.path.exists(metadata_dir):
        for filename in os.listdir(metadata_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(metadata_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        metadata.extend(data if isinstance(data, list) else [data])
                except json.JSONDecodeError as e:
                    print(f"Error decoding {filename}: {e}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    print(f"Loaded {len(metadata)} metadata entries")

# tokenize text and generate text feature vector with clip 
def encode_text(text_queries):
    print("Encoding text query...")
    text = clip.tokenize(text_queries).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text)
        text_features = torch.nn.functional.normalize(text_features, p=2, dim=1)
    return text_features.cpu().numpy().astype('float32')

# query the FAISS index with encoded features
def query_index(index, query_features, top_k=10):
    try:
        print(f"Querying index for top {top_k} results...")
        D, I = index.search(query_features.astype(np.float32), top_k)
        
        results = []
        for i in range(len(query_features)):
            query_results = []
            for rank, (idx, score) in enumerate(zip(I[i], D[i])):
                if idx != -1 and idx < len(metadata):  # Valid index and within metadata bounds
                    meta = metadata[idx]
                    
                    # extract image path from metadata
                    image_path = meta.get('keyframe_path', f"image_{idx}")
                    
                    # create structured metadata object
                    video_metadata = None
                    if meta and isinstance(meta, dict):
                        try:
                            video_metadata = VideoMetadata(
                                video_id=meta.get('video_id', ''),
                                shot=meta.get('shot', 0),
                                start_frame=meta.get('start_frame', 0),
                                end_frame=meta.get('end_frame', 0),
                                start_time=meta.get('start_time', 0.0),
                                end_time=meta.get('end_time', 0.0),
                                keyframe_path=meta.get('keyframe_path', '')
                            )
                        except Exception as e:
                            print(f"Error creating VideoMetadata for index {idx}: {e}")
                            video_metadata = None
                    
                    query_results.append({
                        'image_path': image_path,
                        'score': float(score),
                        'metadata': video_metadata,
                        'index': int(idx)
                    })
            results.append(query_results)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying index: {str(e)}")


@app.get("/search", response_model=SearchResponse)
def search_images(
    query: str = Query(..., description="Text query to search for similar images"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Search for images similar to the text query"""
    
    if not clip_model or not index:
        raise HTTPException(status_code=503, detail="Models not loaded yet")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Encode the text query
        query_features = encode_text([query])  # Pass as list
        
        # Search the index
        search_results = query_index(index, query_features, top_k)
        
        print(f"Search results found: {len(search_results[0]) if search_results else 0}")

        # Format results for response
        formatted_results = []
        if search_results:
            for result in search_results[0]:  # Take first query results
                formatted_results.append(SearchResult(
                    image_path=result['image_path'],
                    score=result['score'],
                    index=result['index'],
                    metadata=result.get('metadata')
                ))
        
        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# get video metadata by index (FAISS indexes)
# metadata are ordered from the first keyframe of the first video metadata (with index 1) 
@app.get("/metadata/{index_id}")
def get_metadata(index_id: int):
    """Get metadata for a specific index"""
    if index_id < 0 or index_id >= len(metadata):
        raise HTTPException(status_code=404, detail="Index not found")
    
    meta = metadata[index_id]
    try:
        return VideoMetadata(
            video_id=meta.get('video_id', ''),
            shot=meta.get('shot', 0),
            start_frame=meta.get('start_frame', 0),
            end_frame=meta.get('end_frame', 0),
            start_time=meta.get('start_time', 0.0),
            end_time=meta.get('end_time', 0.0),
            keyframe_path=meta.get('keyframe_path', '')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing metadata: {str(e)}")

# get video shots by index (format: 00001)
@app.get("/videos/{video_id}")
def get_video_shots(video_id: str):
    """Get all shots for a specific video"""
    video_shots = [meta for meta in metadata if meta.get('video_id') == video_id]
    
    if not video_shots:
        raise HTTPException(status_code=404, detail=f"No shots found for video {video_id}")
    
    try:
        formatted_shots = []
        for meta in video_shots:
            formatted_shots.append(VideoMetadata(
                video_id=meta.get('video_id', ''),
                shot=meta.get('shot', 0),
                start_frame=meta.get('start_frame', 0),
                end_frame=meta.get('end_frame', 0),
                start_time=meta.get('start_time', 0.0),
                end_time=meta.get('end_time', 0.0),
                keyframe_path=meta.get('keyframe_path', '')
            ))
        
        return {
            "video_id": video_id,
            "total_shots": len(formatted_shots),
            "shots": formatted_shots
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video shots: {str(e)}")

# check the server status
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": clip_model is not None and index is not None,
        "device": device,
        "index_size": index.ntotal if index else 0,
        "metadata_loaded": len(metadata) > 0
    }

# get data stats like total videos, total shots, total keyframes, video ids
@app.get("/stats")
def get_stats():
    if not metadata:
        return {"error": "No metadata loaded"}
    
    video_ids = set()
    total_shots = 0
    total_duration = 0.0
    
    for meta in metadata:
        if 'video_id' in meta:
            video_ids.add(meta['video_id'])
        if 'shot' in meta:
            total_shots += 1
        if 'start_time' in meta and 'end_time' in meta:
            total_duration += meta['end_time'] - meta['start_time']
    
    return {
        "total_videos": len(video_ids),
        "total_shots": total_shots,
        "total_keyframes": len(metadata),
        "total_duration_seconds": round(total_duration, 2),
        "average_shot_duration": round(total_duration / total_shots, 2) if total_shots > 0 else 0,
        "video_ids": sorted(list(video_ids))
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)