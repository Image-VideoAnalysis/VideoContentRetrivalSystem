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
import requests
from dotenv import load_dotenv

load_dotenv()

# DRES infos
DRES_BASE_URL = "https://vbs.videobrowsing.org/api/v2"
USERNAME = os.getenv("DRES_USERNAME")
PASSWORD = os.getenv("DRES_PASSWORD")

# DRES session 
session = {
    "token": None,
    "evaluationId": None,
    "taskName": None,
}

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
img_filename_to_metadata = {}
image_paths = []

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

metadata_dir = os.getenv("METADATA_DIR")
keyframes_dir = os.getenv("KEYFRAMES_DIR")
keyframes_abs_dir = os.path.abspath(keyframes_dir) 

# Serve the keyframes at /keyframes
app.mount("/keyframes", StaticFiles(directory=keyframes_abs_dir), name="keyframes")

# --- Pydantic Response Models ---
class VideoMetadata(BaseModel):
    video_id: str
    shot: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    keyframe_path: str

class Shot(BaseModel):
    shot: int
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

class Submission(BaseModel):
    mediaItemName: str
    start: int
    end: int

def load_image_paths():
    """Loads all image paths from the keyframes directory."""
    img_paths = []
    for root, dirs, files in os.walk(keyframes_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_paths.append(os.path.join(root, file))

    img_paths.sort(key=lambda x: x.lower())

    print(f"Loaded {len(img_paths)} image paths entries")
    return img_paths

def load_metadata():
    """Loads and aggregates metadata from all JSON files in the metadata directory."""
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
    return metadata


def load_img_filename_metadata_map(metadata):
    """Creates a mapping from keyframe filenames to their metadata."""
    global img_filename_to_metadata
    for mt in metadata:
        filename = os.path.basename(mt["keyframe_path"])
        img_filename_to_metadata[filename] = mt


@app.on_event("startup")
def load_resources():
    """Load all necessary resources on application startup."""
    global image_paths
    
    print("Loading resources...")

    print(f"Username: {USERNAME}")
    
    print(f"CLIP model loaded on {device}")    
    print(f"Faiss index loaded with {index.ntotal} vectors")
    
    image_paths = load_image_paths()
    metadata = load_metadata()

    load_img_filename_metadata_map(metadata)


def encode_text(text_queries: List[str]) -> np.ndarray:
    """Encodes a list of text queries into feature vectors using CLIP."""
    print("Encoding text query...")
    text_tokens = clip.tokenize(text_queries).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text_tokens)
        text_features = torch.nn.functional.normalize(text_features, p=2, dim=1)
    return text_features.cpu().numpy().astype('float32')


def query_index(search_index, query_features: np.ndarray, top_k: int = 10) -> List[List[dict]]:
    """Queries the Faiss index with the given feature vectors."""
    try:
        print(f"Querying index for top {top_k} results...")
        distances, indices = search_index.search(query_features.astype(np.float32), top_k)
        
        results = []
        for i in range(len(query_features)):
            query_results = []
            for rank, (idx, score) in enumerate(zip(indices[i], distances[i])):
                if idx != -1 and idx < len(image_paths):
                    img_path = image_paths[idx]
                    filename = os.path.basename(img_path)
                    meta = img_filename_to_metadata.get(filename)
                    
                    if meta:
                        try:
                            video_metadata = VideoMetadata(**meta)
                            query_results.append({
                                'image_path': video_metadata.keyframe_path,
                                'score': float(score),
                                'metadata': video_metadata,
                                'index': int(idx)
                            })
                        except Exception as e:
                            print(f"Error creating VideoMetadata for index {idx}: {e}")
            results.append(query_results)
        
        return results
    except Exception as e:
        print(f"Error querying index: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying index: {str(e)}")


@app.get("/search", response_model=SearchResponse)
def search_images(
    query: str = Query(..., description="Text query to search for similar images"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Search for images similar to the text query."""
    if not clip_model or not index:
        raise HTTPException(status_code=503, detail="Models not loaded yet")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        query_features = encode_text([query])
        search_results = query_index(index, query_features, top_k)
        
        formatted_results = [SearchResult(**res) for res in search_results[0]] if search_results else []
        
        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def get_evaluation_list():
    """Fetches the list of evaluations from DRES."""
    response = requests.get(f"{DRES_BASE_URL}/client/evaluation/list?session={session['token']}")

    if response.status_code != 200:
        print("Fetching evaluation list failed:", response.text)
        return
    
    data = response.json()
    if data:
        # Assuming the first evaluation and first task template are the correct ones
        eval_id = data[0].get("id")
        eval_name = data[0].get("taskTemplates")[0].get("name")
        session["evaluationId"] = eval_id
        session["taskName"] = eval_name
        print(f"Set evaluationId to {eval_id} and taskName to {eval_name}")


@app.post("/login")
def login():
    """Logs into the DRES system to get a session token."""
    body = {"username": USERNAME, "password": PASSWORD}
    try:
        response = requests.post(f"{DRES_BASE_URL}/login", json=body)
        response.raise_for_status()
        
        data = response.json()
        session_id = data.get("sessionId")
        session["token"] = session_id
        print("DRES login successful. Session ID:", session_id)
        get_evaluation_list()
        return {"status": "success", "sessionId": session_id}
    except requests.RequestException as e:
        print(f"DRES login failed: {e}")
        raise HTTPException(status_code=500, detail=f"DRES login failed: {e}")
    


def dres_submit(text: str=None, mediaItemName: str=None, mediaItemCollName: str="IVADL", start: int=32210, end: int=32210):
    """Submits results to the DRES system."""
    if not session["token"] or not session["evaluationId"]:
        raise HTTPException(status_code=400, detail="Not logged into DRES or evaluation not set.")

    body_result = {
    "answerSets": [
        {
        "taskId": None,
        "taskName": session["taskName"],
        "answers": [
            {
            "text": None,
            "mediaItemName": mediaItemName,
            "mediaItemCollectionName": "IVADL",
            "start": start,
            "end": end
            }
        ]
        }
    ]
    }
    response = requests.post(f"{DRES_BASE_URL}/submit/{session['evaluationId']}?session={session["token"]}", json=body_result)

    print("STATUS", response.status_code)    
    print("Response: ", response.text)
    return response.json()

@app.post("/submit")
def submit(submission: Submission):
    print("Received submission:", submission)

    submit_res = dres_submit(
        mediaItemName=submission.mediaItemName,
        start=submission.start,
        end=submission.end
    )

    print("SUBMIT RES: ", submit_res)

    if not submit_res.get("status"):
        raise HTTPException(status_code=500, detail=submit_res["description"])
    
    return submit_res


@app.get("/metadata/{filename}", response_model=VideoMetadata)
def get_metadata_by_filename(filename: str):
    """Get metadata for a specific keyframe by its filename."""
    meta = img_filename_to_metadata.get(filename)
    if not meta:
        raise HTTPException(status_code=404, detail="Metadata for filename not found")
    
    try:
        return VideoMetadata(**meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing metadata: {str(e)}")


@app.get("/stats")
def get_stats():
    """Get statistics about the loaded dataset."""
    if not img_filename_to_metadata:
        raise HTTPException(status_code=404, detail="No metadata loaded")
    
    video_ids = set(meta['video_id'] for meta in img_filename_to_metadata.values() if 'video_id' in meta)
    total_shots = len({ (meta['video_id'], meta['shot']) for meta in img_filename_to_metadata.values() })
    
    return {
        "total_videos": len(video_ids),
        "total_shots": total_shots,
        "total_keyframes": len(image_paths),
        "video_ids": sorted(list(video_ids))
    }

@app.get("/videos/{video_name}/shots", response_model=List[Shot])
def get_video_shots(video_name: str):
    """
    Given a video name, returns the list of all shots 
    with their respective starting and ending times and keyframe path.
    """
    if not img_filename_to_metadata:
        raise HTTPException(status_code=503, detail="Metadata not loaded yet")

    shots = {}
    for meta in img_filename_to_metadata.values():
        if meta.get('video_id') == video_name:
            shot_id = meta.get('shot')
            # Use a dictionary to automatically handle one keyframe per shot
            if shot_id is not None and shot_id not in shots:
                shots[shot_id] = {
                    "shot": shot_id,
                    "start_time": meta.get('start_time'),
                    "end_time": meta.get('end_time'),
                    "keyframe_path": meta.get('keyframe_path')
                }
    
    if not shots:
        raise HTTPException(status_code=404, detail=f"Video '{video_name}' not found or has no shots.")
        
    # Sort shots by the shot number
    sorted_shots = sorted(shots.values(), key=lambda x: x['shot'])
    
    return sorted_shots


@app.get("/health")
def health_check():
    """Check the health of the server."""
    return {
        "status": "healthy",
        "models_loaded": clip_model is not None and index is not None,
        "device": device,
        "index_size": index.ntotal if index else 0,
        "metadata_loaded": len(img_filename_to_metadata) > 0
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
