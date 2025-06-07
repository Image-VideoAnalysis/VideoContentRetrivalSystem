from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import clip
import faiss
import json
import numpy as np
import uvicorn
from typing import List

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global objects
clip_model = None
preprocess = None
index = None
metadata = []
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model, index, and metadata
@app.on_event("startup")
def load_resources():
    # global clip_model, preprocess, index, metadata

    # Load CLIP model
    clip_model, preprocess = clip.load("ViT-B/32", device=device)

    # Load Faiss index
    # index = faiss.read_index("path/to/faiss_index.index")

    # Load metadata
    with open("../../SBDresults/metadata/", "r") as f:
        metadata = json.load(f)

class Shot(BaseModel):
    video_id: str
    start_time: float
    end_time: float
    keyframe_path: str
    score: float

@app.get("/search", response_model=List[Shot])
def search(query: str = Query(..., min_length=1)):
    # global clip_model, index, metadata

    # Encode query
    text = clip.tokenize([query]).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    # Search
    text_np = text_features.cpu().numpy().astype("float32")
    scores, indices = index.search(text_np, k=10)

    # Build response
    results = []
    for score, idx in zip(scores[0], indices[0]):
        data = metadata[idx]
        results.append(Shot(
            video_id=data["video_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            thumbnail_url=data["thumbnail_url"],
            score=float(score)
        ))
    return results

class SubmitRequest(BaseModel):
    video_id: str
    timestamp: float

# submit results to DRES
@app.post("/submit")
def submit_result(payload: SubmitRequest):
    pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
