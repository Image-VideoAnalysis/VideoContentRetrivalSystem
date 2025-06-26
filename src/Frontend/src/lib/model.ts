
 // Define a type for the image data displayed in the gallery
 export interface GalleryImage {
      url: string;
      alt: string;
      title: string;
      video_id: string;
      start_time: string;
      end_time: string;
  }

// Interface for VideoMetadata, mirroring the FastAPI model
export interface VideoMetadata {
    video_id: string;
    shot: number;
    start_frame: number;
    end_frame: number;
    start_time: number;
    end_time: number;
    keyframe_path: string;
}

// Interface for a single SearchResult item
export interface SearchResult {
    image_path: string;
    score: number;
    index: number;
    metadata: VideoMetadata | null; // Optional metadata
}

// Interface for the overall SearchResponse
export interface SearchResponse {
    query: string;
    results: SearchResult[];
    total_results: number;
}


export interface Evaluation {
    id: string;
    name: string;
}
