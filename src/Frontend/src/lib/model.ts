

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

// Interface for the HealthCheck endpoint response
export interface HealthCheckResponse {
    status: string;
    models_loaded: boolean;
    device: string;
    index_size: number;
    metadata_loaded: boolean;
}

// Interface for the VideoShots endpoint response
export interface VideoShotsResponse {
    video_id: string;
    total_shots: number;
    shots: VideoMetadata[];
}

// Interface for the Stats endpoint response
export interface StatsResponse {
    total_videos?: number; // Optional as it might return error
    total_shots?: number;
    total_keyframes?: number;
    total_duration_seconds?: number;
    average_shot_duration?: number;
    video_ids?: string[];
    error?: string; // For the case where no metadata is loaded
}
