<script lang="ts">
    import { loading, images, error } from "$lib/stores";
    import { writable } from "svelte/store";
    import { fly, slide } from 'svelte/transition';

    // --- STATE MANAGEMENT ---

    // Store for the currently selected video to play
    const selectedVideo = writable<{ video_id: string; start_time: number; end_time: number } | null>(null);

    // New: Store for the shots of the currently playing video
    const videoShots = writable<any[]>([]); // Added type for better safety
    const shotsLoading = writable(false);
    
    // New: A reference to the HTML <video> element to control it directly
    let videoElement: HTMLVideoElement;

    // --- REACTIVE LOGIC ---

    // This block runs whenever the 'selectedVideo' store changes
    $: if ($selectedVideo) {
        // When a new video is selected, fetch its shots
        fetchVideoShots($selectedVideo.video_id);
    } else {
        // When the player is closed, clear the list of shots
        videoShots.set([]);
    }

    // This key ensures the <video> element is completely re-rendered when the source changes,
    // avoiding issues with the browser not updating the source correctly.
    $: videoKey = $selectedVideo
    ? `${$selectedVideo.video_id}_${$selectedVideo.start_time}_${$selectedVideo.end_time}`
    : null;

    // --- FUNCTIONS ---

    /**
     * Fetches all shots for a given video ID from the backend API.
     * @param {string} videoId - The ID of the video to fetch shots for.
     */
    async function fetchVideoShots(videoId: string) {
        shotsLoading.set(true);
        try {
            // Call the new endpoint you created
            const response = await fetch(`http://localhost:8000/videos/${videoId}/shots`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            videoShots.set(data);
        } catch (err) {
            console.error("Failed to fetch video shots:", err);
            videoShots.set([]); // Clear shots on error
        } finally {
            shotsLoading.set(false);
        }
    }

    /**
     * Seeks the main video player to a specific time.
     * @param {number} time - The time in seconds to seek to.
     */
    function seekTo(time: number) {
        if (videoElement) {
            videoElement.currentTime = time;
            videoElement.play(); // Optional: automatically play after seeking
        }
    }

    /**
     * FIX: Handles image loading errors for shot thumbnails.
     * Replaces the broken image source with a placeholder.
     * @param {Event} e - The error event.
     */
    function handleImageError(e: Event & { currentTarget: HTMLImageElement }) {
        e.currentTarget.src = 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=Error';
    }

    /**
     * FIX: Constructs the correct, full URL for a keyframe image.
     * The backend provides an absolute file path, but we need a URL relative
     * to the '/keyframes' static route.
     * @param {string} keyframePath - The full file path from the backend.
     */
    function getImageUrl(keyframePath: string): string {
        if (!keyframePath) {
            return 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=No+Path';
        }
        // Use a regular expression to split by either /keyframes/ or \keyframes\ (for Windows paths)
        const pathParts = keyframePath.split(/[\/\\]keyframes[\/\\]/);
        const relativePath = pathParts.length > 1 ? pathParts[1] : '';

        if (!relativePath) {
            // As a fallback, try to get the last two parts of the path (e.g., video_id/frame.jpg)
            const fallbackParts = keyframePath.replace(/\\/g, '/').split('/');
            if (fallbackParts.length >= 2) {
                 return `http://localhost:8000/keyframes/${fallbackParts.slice(-2).join('/')}`;
            }
            return 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=Bad+Path';
        }

        return `http://localhost:8000/keyframes/${relativePath.replace(/\\/g, '/')}`;
    }
</script>

<!--
  Main container.
  The 'video-selected' class is dynamically added when a video is active.
  This class triggers the layout change from a full-page grid to a player-and-sidebar view.
-->
<div class="page-container" class:video-selected={$selectedVideo !== null}>

    <!-- Video Player Wrapper -->
    <div class="video-player-wrapper">
        {#if $selectedVideo}
            <!-- The 'in:fly' transition makes the player appear smoothly from the top. -->
            <div class="video-player-container" in:fly={{ y: -20, duration: 400, delay: 200 }} out:slide>
                <div class="video-header">
                    <h4>Playing: {$selectedVideo.video_id}</h4>
                    <!-- A stylish close button to clear the selected video -->
                    <button class="close-button" on:click={() => selectedVideo.set(null)} title="Close player">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </div>
                 <!-- The #key block ensures the video element is re-created when the source changes -->
                {#key videoKey}
                    <video controls autoplay width="100%" bind:this={videoElement}>
                        <track kind="captions" />
                        <source
                            src={`/videos/V3C1_200/${$selectedVideo.video_id}.mp4#t=${$selectedVideo.start_time},${$selectedVideo.end_time}`}
                            type="video/mp4"
                        />
                        Your browser does not support the video tag.
                    </video>
                {/key}

                <!-- === NEW: Related Shots Section === -->
                <div class="related-shots-container">
                    {#if $shotsLoading}
                        <p class="shots-message">Loading shots...</p>
                    {:else if $videoShots.length > 0}
                        <h5>Shots in this video</h5>
                        <div class="shots-grid">
                            {#each $videoShots as shot (shot.keyframe_path)}
                                <button class="shot-thumbnail" on:click={() => seekTo(shot.start_time)} title="Go to shot at {shot.start_time.toFixed(2)}s">
                                    <img 
                                        src={getImageUrl(shot.keyframe_path)} 
                                        alt={`Shot ${shot.shot}`}
                                        on:error={handleImageError}
                                    />
                                    <span class="shot-time">{shot.start_time.toFixed(2)}s</span>
                                </button>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
    </div>

    <!-- Thumbnails Container -->
    <!-- This container holds the grid of video thumbnails. Its layout adapts based on the 'video-selected' class on the parent. -->
    <div class="thumbnails-container">
        {#if $loading}
            <p class="message-container loading-message">Loading keyframes...</p>
        {:else if $error}
            <p class="message-container error-message">Error: {$error}</p>
        {:else if $images.length === 0}
            <p class="message-container">No keyframes found. Try adjusting the search query.</p>
        {:else}
            <!-- This 'row' div is the direct container for the cards, switching between grid and list-item styles -->
            <div class="row">
                {#each $images as img (img.url)}
                    <div class="col">
                        <div
                            class="card h-100"
                            role="button"
                            tabindex="0"
                            on:click={() => selectedVideo.set({
                                video_id: img.video_id,
                                start_time: img.start_time,
                                end_time: img.end_time
                            })}
                            on:keydown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    selectedVideo.set({
                                        video_id: img.video_id,
                                        start_time: img.start_time,
                                        end_time: img.end_time
                                    });
                                }
                            }}
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
</div>

<style>
    :root {
        --dark-bg-primary: #121212;
        --dark-bg-secondary: #1e1e1e;
        --dark-bg-tertiary: #2a2a2a;
        --border-color: #3a3a3a;
        --text-primary: #f1f1f1;
        --text-secondary: #aaaaaa;
        --accent-color: #3ea6ff;
        --shadow-color: rgba(0, 0, 0, 0.3);
    }

    .page-container {
        display: flex;
        flex-direction: column;
        max-width: 1800px;
        margin: 1rem auto;
        padding: 0 1rem;
        transition: all 0.5s ease-in-out;
    }

    /* === YOUTUBE-LIKE LAYOUT ACTIVATION === */
    .video-selected {
        flex-direction: row;
        gap: 24px;
        align-items: flex-start;
    }

    .video-selected .video-player-wrapper {
        flex: 1 1 70%;
        position: sticky;
        top: 1rem;
        /* FIX: Prevent the wrapper from growing taller than the screen */
        max-height: calc(100vh - 2rem);
        overflow-y: auto; /* Allow scrolling for the shot list if needed */
    }

    .video-selected .thumbnails-container {
        flex: 1 1 30%;
        max-width: 420px;
    }

    /* === VIDEO PLAYER === */
    .video-player-wrapper {
        transition: all 0.5s ease-in-out;
    }
    .video-player-container {
        background-color: var(--dark-bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        overflow: hidden;
    }
    .video-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem;
    }
    .video-header h4 {
        color: var(--text-primary);
        margin: 0;
        font-weight: 500;
    }
    video {
        display: block;
        background-color: #000;
        /* FIX: Ensure video scales correctly within its container */
        width: 100%;
        height: auto;
    }

    /* === CLOSE BUTTON === */
    .close-button {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background-color 0.2s ease, color 0.2s ease;
    }
    .close-button:hover {
        background-color: var(--dark-bg-tertiary);
        color: var(--text-primary);
    }
    .close-button svg {
        width: 20px;
        height: 20px;
    }


    /* === THUMBNAILS === */
    .thumbnails-container {
        width: 100%;
        transition: all 0.5s ease-in-out;
    }
    .row {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
        transition: all 0.5s ease-in-out;
    }
    
    .video-selected .row {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .card {
        background-color: transparent;
        color: var(--text-primary);
        border: none;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        transition: background-color 0.3s ease;
    }

    .card:hover {
        background-color: var(--dark-bg-secondary);
    }

    .video-selected .card {
        flex-direction: row;
        align-items: center;
    }

    .card-img-top {
        width: 100%;
        aspect-ratio: 16 / 9;
        object-fit: cover;
        background-color: var(--dark-bg-secondary);
        border-radius: 8px;
        transition: border-radius 0.3s ease;
    }
    
    .video-selected .card-img-top {
        width: 160px;
        flex-shrink: 0;
        margin-right: 12px;
    }
    
    .card-body {
        padding: 0.75rem 0.25rem;
    }

    .video-selected .card-body {
        padding: 0;
    }

    .card-title {
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
        color: var(--text-primary);
    }

    .card-text {
        font-size: 0.8rem;
        line-height: 1.4;
        color: var(--text-secondary);
    }

    /* === NEW: Related Shots Styles === */
    .related-shots-container {
        padding: 1rem;
        background-color: var(--dark-bg-tertiary);
        border-top: 1px solid var(--border-color);
    }

    .related-shots-container h5 {
        margin: 0 0 0.75rem 0;
        font-weight: 500;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    .shots-message {
        font-size: 0.9rem;
        color: var(--text-secondary);
        padding: 0.5rem 0;
    }

    .shots-grid {
        display: flex;
        gap: 0.75rem;
        overflow-x: auto;
        padding-bottom: 0.5rem; /* For scrollbar spacing */
    }

    .shots-grid::-webkit-scrollbar {
        height: 8px;
    }
    .shots-grid::-webkit-scrollbar-track {
        background: var(--dark-bg-secondary);
        border-radius: 4px;
    }
    .shots-grid::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 4px;
    }
    .shots-grid::-webkit-scrollbar-thumb:hover {
        background: #777;
    }

    .shot-thumbnail {
        all: unset; /* Reset button styles */
        box-sizing: border-box;
        display: block;
        position: relative;
        flex-shrink: 0;
        width: 140px;
        aspect-ratio: 16 / 9;
        border-radius: 6px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        transition: border-color 0.2s ease;
        background-color: var(--dark-bg-secondary);
    }

    .shot-thumbnail:hover, .shot-thumbnail:focus-visible {
        border-color: var(--accent-color);
    }

    .shot-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .shot-time {
        position: absolute;
        bottom: 4px;
        right: 4px;
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 2px 6px;
        font-size: 0.7rem;
        border-radius: 4px;
    }


    /* === MESSAGES === */
    .message-container {
        text-align: center;
        padding: 2rem;
        font-size: 1.2rem;
        color: var(--text-secondary);
    }
    .error-message {
        color: #ff8a8a;
    }
    .loading-message {
        color: var(--accent-color);
    }

    /* === RESPONSIVE ADJUSTMENTS === */
    @media (max-width: 992px) {
        .video-selected {
            flex-direction: column;
            gap: 24px;
        }
        .video-selected .video-player-wrapper {
            position: static;
            max-height: none; /* Remove max-height for stacked layout */
        }
        .video-selected .thumbnails-container {
            max-width: none;
        }
    }
    
    @media (max-width: 480px) {
        .row {
            grid-template-columns: 1fr;
        }
        .page-container {
            margin: 0.5rem auto;
            padding: 0 0.5rem;
        }
    }
</style>
