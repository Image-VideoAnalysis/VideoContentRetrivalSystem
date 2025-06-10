// src/services/api.ts

import type {
    VideoMetadata,
    SearchResult,
    SearchResponse,
    HealthCheckResponse,
    VideoShotsResponse,
    StatsResponse
} from './model'; // Assuming 'model.ts' is where your interfaces are now located.

const API_BASE_URL: string = 'http://localhost:8000'; // Replace with your backend URL if different



function adjustKeyframePath(originalPath: string): string {
    if (originalPath.startsWith('./SBDresults/keyframes/')) {
        // Only extract the part after the original keyframe base
        const relativePath = originalPath.replace('./SBDresults/keyframes/', '');
        // Return new path via backend proxy
        return `${API_BASE_URL}/keyframes/${relativePath}`;
    }
    return originalPath;
}


/**
 * Searches for images similar to the given text query.
 * @param query The text query to search for.
 * @param topK The number of top results to return (default: 10).
 * @returns A Promise that resolves to a SearchResponse object.
 * @throws An error if the API call fails.
 */
export async function searchImages(query: string, topK: number = 10): Promise<SearchResponse> {
    try {
        const response: Response = await fetch(`${API_BASE_URL}/search?query=${encodeURIComponent(query)}&top_k=${topK}`);
        if (!response.ok) {
            const errorData: { detail?: string } = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch search results');
        }
        const data: SearchResponse = await response.json();

        // Adjust keyframe paths in the search results
        data.results = data.results.map(result => ({
            ...result,
            metadata: result.metadata ? {
                ...result.metadata,
                keyframe_path: adjustKeyframePath(result.metadata.keyframe_path)
            } : null,
            // Assuming image_path also needs adjustment and has a similar structure
            // and often refers to the same keyframe path
            image_path: adjustKeyframePath(result.image_path)
        }));

        return data;
    } catch (error: any) {
        console.error('Error searching images:', error);
        throw error;
    }
}

/**
 * Retrieves metadata for a specific index.
 * @param indexId The ID of the index to retrieve metadata for.
 * @returns A Promise that resolves to a VideoMetadata object.
 * @throws An error if the API call fails or index is not found.
 */
export async function getMetadata(indexId: number): Promise<VideoMetadata> {
    try {
        const response: Response = await fetch(`${API_BASE_URL}/metadata/${indexId}`);
        if (!response.ok) {
            const errorData: { detail?: string } = await response.json();
            throw new Error(errorData.detail || `Failed to fetch metadata for index ${indexId}`);
        }
        const data: VideoMetadata = await response.json();

        // Adjust keyframe path for the single metadata object
        data.keyframe_path = adjustKeyframePath(data.keyframe_path);

        return data;
    } catch (error: any) {
        console.error(`Error fetching metadata for index ${indexId}:`, error);
        throw error;
    }
}

/**
 * Retrieves all shots for a specific video ID.
 * @param videoId The ID of the video to retrieve shots for.
 * @returns A Promise that resolves to a VideoShotsResponse object.
 * @throws An error if the API call fails or video ID is not found.
 */
export async function getVideoShots(videoId: string): Promise<VideoShotsResponse> {
    try {
        const response: Response = await fetch(`${API_BASE_URL}/videos/${videoId}`);
        if (!response.ok) {
            const errorData: { detail?: string } = await response.json();
            throw new Error(errorData.detail || `Failed to fetch shots for video ${videoId}`);
        }
        const data: VideoShotsResponse = await response.json();

        // Adjust keyframe paths for each shot in the response
        data.shots = data.shots.map(shot => ({
            ...shot,
            keyframe_path: adjustKeyframePath(shot.keyframe_path)
        }));

        return data;
    } catch (error: any) {
        console.error(`Error fetching video shots for ${videoId}:`, error);
        throw error;
    }
}

/**
 * Performs a health check on the backend server.
 * @returns A Promise that resolves to a HealthCheckResponse object.
 * @throws An error if the API call fails.
 */
export async function getHealthCheck(): Promise<HealthCheckResponse> {
    try {
        const response: Response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            const errorData: { detail?: string } = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch health status');
        }
        return await response.json();
    } catch (error: any) {
        console.error('Error fetching health status:', error);
        throw error;
    }
}

/**
 * Retrieves statistics about the loaded data.
 * @returns A Promise that resolves to a StatsResponse object.
 * @throws An error if the API call fails.
 */
export async function getStats(): Promise<StatsResponse> {
    try {
        const response: Response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) {
            const errorData: { detail?: string } = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch stats');
        }
        return await response.json();
    } catch (error: any) {
        console.error('Error fetching stats:', error);
        throw error;
    }
}
