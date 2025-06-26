
import type { GalleryImage, SearchResult } from "$lib/model";
import { writable, type Writable } from 'svelte/store';
import { searchImages } from "$lib/api";


// Writable stores for reactive state management
export const images: Writable<GalleryImage[]> = writable([]);
export const loading: Writable<boolean> = writable(true); // Set to true initially as we'll fetch on mount
export const error: Writable<string | null> = writable(null);

export let alertMessage = writable('');
export let alertColor = writable('danger');
export let alertVisible = writable(false);

// --- Submission State ---
export const startTime = writable<number | null>(null);
export const endTime = writable<number | null>(null);
export const submissionStatus = writable<'idle' | 'submitting' | 'success' | 'error'>('idle');

export const selectedVideo = writable<{ video_id: string; start_time: number; end_time: number } | null>(null);
export const videoShots = writable<any[]>([]);
export const shotsLoading = writable(false);

export function showAlert(message = "", color = 'danger', duration = 5000) {
    alertMessage.set(message);
    alertColor.set(color);
    alertVisible.set(true);

    setTimeout(() => {
    alertVisible.set(false);
    }, duration);
}


/**
 * Function to fetch initial video keyframes.
 * Uses the searchImages API with a generic query to get a default set of results.
 */
export async function fetchVideos(query: string = "guitar", top_k: number = 10): Promise<void> {
    loading.set(true); // Indicate loading state
    error.set(null); // Clear any previous errors

    try {
        // Perform a search for a generic query to get some initial keyframes
        // You can change "video" to something more specific or adjust topK
        const response = await searchImages(query, top_k); // Fetch up to 20 keyframes

        if (response.results && response.results.length > 0) {
            console.log("results:", response.results)
            // Map the SearchResult from the API to the GalleryImage format
            const mappedImages: GalleryImage[] = response.results.map((result: SearchResult) => ({
                url: result.image_path,
                alt: `Keyframe from Video ${result.metadata?.video_id || 'N/A'} Shot ${result.metadata?.shot || 'N/A'}`,
                title: `Video ${result.metadata?.video_id || 'N/A'} - Shot ${result.metadata?.shot || 'N/A'}`,
                video_id: result.metadata?.video_id || 'N/A',
                start_time: (result.metadata?.start_time || 0).toFixed(2),
                end_time: (result.metadata?.end_time || 0).toFixed(2)
            }));
            images.set(mappedImages);
        } else {
            images.set([]);
        }
    } catch (err: any) {
        console.error("Failed to fetch initial videos:", err);
        error.set(err.message || "Could not load initial video keyframes.");
    } finally {
        loading.set(false);
    }
}

