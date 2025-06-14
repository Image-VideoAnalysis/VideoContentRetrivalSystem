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

metadata_dir = "../../SBDresults/metadata/"
keyframes_dir = "../../SBDresults/keyframes"
keyframes_abs_dir = os.path.abspath(keyframes_dir) 

# Serve the keyframes at `/keyframes`
app.mount("/keyframes", StaticFiles(directory=keyframes_abs_dir), name="keyframes")

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


def load_image_paths():
    img_paths = []
    for root, dirs, files in os.walk(keyframes_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_paths.append(root + "/" + file)
    
    print(f"Loaded {len(img_paths)} image paths entries")
    return img_paths

def load_metadata():
    # Load metadata from all JSON files in the folder
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
    global img_filename_to_metadata
    for mt in metadata:
        filename = os.path.basename(mt["keyframe_path"])
        img_filename_to_metadata[filename] = mt


@app.on_event("startup")
def load_resources():
    global image_paths
    
    print("Loading resources...")

    print(f"Username: {USERNAME}")
    
    print(f"CLIP model loaded on {device}")    
    print(f"Faiss index loaded with {index.ntotal} vectors")
    
    image_paths = load_image_paths()
    metadata = load_metadata()

    load_img_filename_metadata_map(metadata)


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
                if idx != -1 and idx < len(image_paths):  # Valid index and within metadata bounds
                    img_path = image_paths[idx]
                    print("img_path: ", img_path)

                    filename = os.path.basename(img_path)
                    print("FILENAME: ", filename)

                    meta = img_filename_to_metadata[filename]
                    print("meta: ", meta)
                    
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
        print(e)
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


def get_evaluation_list():
    response = requests.get(f"{DRES_BASE_URL}/client/evaluation/list?session={session["token"]}")

    print("STATUS CODE: ", response.status_code)
    if response.status_code != 200:
        print("Evaluation list failed")
        return None
    
    data = json.loads(response.text)
    print("DATA: ", response.text)

    # take the first element (for the competition, the correct evaluation name should be IVADL2025)
    eval_id = data[0].get("id")
    eval_name = data[0].get("taskTemplates")[0]
    session["evaluationId"] = eval_id
    session["taskName"] = eval_name

@app.post("/login")
def login():
    body = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(f"{DRES_BASE_URL}/login", json=body)
    
    if response.status_code != 200:
        print("Login failed:", response.json())
        return None
    
    data = json.loads(response.text) 
    session_id = data.get("sessionId")
    print("SESSION: ", session_id)
    session["token"] = session_id
    get_evaluation_list()


def dres_submit(text: str=None, mediaItemName: str=None, mediaItemCollName: str="IVADL", start: int=10, end: int=100):
    body_result = {
        "answerSets": [
            {
            "taskId": None,
            "taskName": "KISV Test 01",
            "answers": [
                {
                "text": text,
                "mediaItemName": mediaItemName,
                "mediaItemCollectionName": mediaItemCollName,
                "start": start,
                "end": end
                }
            ]
            }
        ]
    }

    response = requests.post(f"{DRES_BASE_URL}/submit/{session['evaluationId']}?session={session["token"]}", json=body_result)

    print("STATUS", response.status_code)
    if response.status_code != 200:
        print("Submission failed:", response.text)
        return None
    
    print("Response: ", response.text)

@app.post("/submit")
def submit():
    dres_submit(mediaItemName="00001")


# get video metadata by image filename
@app.get("/metadata/{filename}")
def get_metadata(filename: str):
    # Get metadata for a specific index
    if not img_filename_to_metadata[filename]:
        raise HTTPException(status_code=404, detail="Index not found")
    
    meta = img_filename_to_metadata[filename]
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


# check the server status
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": clip_model is not None and index is not None,
        "device": device,
        "index_size": index.ntotal if index else 0,
        "metadata_loaded": len(img_filename_to_metadata) > 0
    }

# get data stats like total videos, total shots, total keyframes, video ids
@app.get("/stats")
def get_stats():
    if not img_filename_to_metadata:
        return {"error": "No metadata loaded"}
    
    video_ids = set()
    total_shots = 0
    total_duration = 0.0
    
    for meta in img_filename_to_metadata.values():
        if 'video_id' in meta:
            video_ids.add(meta['video_id'])
        if 'shot' in meta:
            total_shots += 1
        if 'start_time' in meta and 'end_time' in meta:
            total_duration += meta['end_time'] - meta['start_time']
    
    return {
        "total_videos": len(video_ids),
        "total_shots": total_shots,
        "total_keyframes": len(img_filename_to_metadata),
        "total_duration_seconds": round(total_duration, 2),
        "average_shot_duration": round(total_duration / total_shots, 2) if total_shots > 0 else 0,
        "video_ids": sorted(list(video_ids))
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)