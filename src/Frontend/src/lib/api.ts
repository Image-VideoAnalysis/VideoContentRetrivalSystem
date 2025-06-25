
import { videoShots, shotsLoading } from './stores';
import type {
    SearchResponse} from './model';

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
 * Fetches all shots for a given video ID from the backend API.
 */
export async function fetchVideoShots(videoId: string) {
    shotsLoading.set(true);
    try {
        const response = await fetch(`http://localhost:8000/videos/${videoId}/shots`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        videoShots.set(data);
    } catch (err) {
        console.error("Failed to fetch video shots:", err);
        videoShots.set([]);
    } finally {
        shotsLoading.set(false);
    }
}
