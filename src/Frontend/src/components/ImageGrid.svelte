<script lang="ts">
    import { onMount } from 'svelte';
    import { get, writable, type Writable } from 'svelte/store';
    import { searchImages } from '$lib/api'; // Adjust path if necessary
    import type { SearchResult } from '$lib/model'; // Import the type for SearchResult

    // Define a type for the image data displayed in the gallery
    interface GalleryImage {
        url: string;
        alt: string;
        title: string;
        video_id: string;
        start_time: string; // Changed to string for display consistency
        end_time: string;   // Changed to string for display consistency
    }

    // Writable stores for reactive state management
    const images: Writable<GalleryImage[]> = writable([]);
    const loading: Writable<boolean> = writable(true); // Set to true initially as we'll fetch on mount
    const error: Writable<string | null> = writable(null);

    /**
     * Function to fetch initial video keyframes.
     * Uses the searchImages API with a generic query to get a default set of results.
     */
    async function fetchInitialVideos(): Promise<void> {
        loading.set(true); // Indicate loading state
        error.set(null); // Clear any previous errors

        try {
            // Perform a search for a generic query to get some initial keyframes
            // You can change "video" to something more specific or adjust topK
            const response = await searchImages("guitar", 20); // Fetch up to 20 keyframes

            if (response.results && response.results.length > 0) {
                // Map the SearchResult from the API to the GalleryImage format
                const mappedImages: GalleryImage[] = response.results.map((result: SearchResult) => ({
                    url: result.image_path,
                    alt: `Keyframe from Video ${result.metadata?.video_id || 'N/A'} Shot ${result.metadata?.shot || 'N/A'}`,
                    title: `Video ${result.metadata?.video_id || 'N/A'} - Shot ${result.metadata?.shot || 'N/A'}`,
                    video_id: result.metadata?.video_id || 'N/A',
                    // Format times to 2 decimal places for display
                    start_time: (result.metadata?.start_time || 0).toFixed(2),
                    end_time: (result.metadata?.end_time || 0).toFixed(2)
                }));
                images.set(mappedImages); // Update the store with fetched images
                console.log("images: ", $images.title)
            } else {
                images.set([]); // No results found
            }
        } catch (err: any) {
            console.error("Failed to fetch initial videos:", err);
            error.set(err.message || "Could not load initial video keyframes.");
        } finally {
            loading.set(false); // End loading state
        }
    }

    // Call the fetch function when the component is mounted to the DOM
    onMount(() => {
        fetchInitialVideos();
    });
</script>

<div class="container my-4">
    {#if $loading}
        <p class="message-container loading-message">Loading keyframes...</p>
    {:else if $error}
        <p class="message-container error-message">Error: {$error}</p>
    {:else if $images.length === 0}
        <p class="message-container">No keyframes found. Try adjusting the search query or check the backend.</p>
    {:else}
        <div class="row">
            {#each $images as img (img.url)} <!-- Use img.url as a unique key for iteration -->
                <div class="col">
                    <div
                        class="card h-100 shadow-sm"
                        role="button"
                        tabindex="0"
                        on:click={() => console.log('Card clicked:', img.title)}
                        on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') console.log('Card activated:', img.title); }}
                    >
                        <img
                            src={img.url || 'img_placeholder.png'}
                            class="card-img-top"
                            alt={img.alt}
                        />
                        <div class="card-body">
                            <h5 class="card-title">{img.title}</h5>
                            <p class="card-text">
                                Video ID: <strong>{img.video_id}</strong><br />
                                Time: {img.start_time}s - {img.end_time}s
                            </p>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    /* Styling for the container and grid layout */
    .container {
        max-width: 1200px;
        margin: 2rem auto;
        padding: 0 1rem;
    }

    .row {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); /* Responsive grid */
        gap: 1.5rem; /* Gap between grid items */
    }

    /* Styling for individual cards */
    .card {
        background-color: #1e1e1e; /* Dark background for the card */
        color: #e0e0e0; /* Light text color */
        border: 1px solid #2a2a2a; /* Subtle border */
        border-radius: 8px; /* Rounded corners */
        overflow: hidden; /* Ensures content respects border-radius */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Soft shadow for depth */
        transition: background-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease; /* Smooth transitions */
        cursor: pointer;
        display: flex; /* Flexbox for consistent height */
        flex-direction: column;
    }

    .card:hover {
        background-color: #2a2a2a; /* Slightly lighter on hover */
        transform: translateY(-5px) scale(1.02); /* Lift and slightly enlarge on hover */
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3); /* Enhanced shadow on hover */
    }

    .card-img-top {
        width: 100%;
        height: 180px; /* Fixed height for consistent image size */
        object-fit: cover; /* Cover the area while maintaining aspect ratio */
        border-bottom: 1px solid #3a3a3a; /* Separator for image and body */
        background-color: #333; /* Placeholder background for images */
    }

    .card-body {
        padding: 1rem;
        display: flex;
        flex-direction: column;
        flex-grow: 1; /* Allows body to expand and push content down */
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #f8f8f8; /* Slightly brighter title color */
    }

    .card-text {
        font-size: 0.9rem;
        line-height: 1.4;
        color: #b0b0b0; /* Subtler text color */
        margin-bottom: 0.5rem;
    }

    .card-text strong {
        color: #ffffff; /* Highlight strong text */
    }

    /* Messages for loading, error, and no content */
    .message-container {
        text-align: center;
        padding: 2rem;
        font-size: 1.2rem;
        color: #b0b0b0;
    }

    .error-message {
        color: #dc3545;
        background-color: #3a1c1c;
        border: 1px solid #6c2323;
        padding: 1rem;
        border-radius: 8px;
    }

    .loading-message {
        color: #007bff;
    }

    /* Responsive adjustments for smaller screens */
    @media (max-width: 768px) {
        .row {
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
        }
        .card-img-top {
            height: 150px;
        }
    }

    @media (max-width: 480px) {
        .row {
            grid-template-columns: 1fr; /* Single column on very small screens */
        }
        .container {
            padding: 0 0.5rem;
        }
    }
</style>