<script lang="ts">
    import { loading, images, error, showAlert } from "$lib/stores";
    import { writable } from "svelte/store";
    import { fly, slide } from 'svelte/transition';
    import { onDestroy } from 'svelte';

    // --- STATE MANAGEMENT ---

    const selectedVideo = writable<{ video_id: string; start_time: number; end_time: number } | null>(null);
    const videoShots = writable<any[]>([]);
    const shotsLoading = writable(false);
    let videoElement: HTMLVideoElement;

    // --- Submission State ---
    const startTime = writable<number | null>(null);
    const endTime = writable<number | null>(null);
    const submissionStatus = writable<'idle' | 'submitting' | 'success' | 'error'>('idle');


    // --- REACTIVE LOGIC ---

    // This block runs whenever the 'selectedVideo' store changes
    $: {
        if ($selectedVideo) {
            fetchVideoShots($selectedVideo.video_id);
            startTime.set(null);
            endTime.set(null);
            submissionStatus.set('idle');
        } else {
            videoShots.set([]);
        }
    }

    // This key ensures the <video> element is completely re-rendered when the source changes
    $: videoKey = $selectedVideo
    ? `${$selectedVideo.video_id}_${$selectedVideo.start_time}_${$selectedVideo.end_time}`
    : null;
    
    // A computed property to check if submission is possible
    $: canSubmit = $startTime !== null && $endTime !== null && $startTime <= $endTime;

    // --- FUNCTIONS ---

    /**
     * Fetches all shots for a given video ID from the backend API.
     */
    async function fetchVideoShots(videoId: string) {
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

    /**
     * Seeks the main video player to a specific time.
     */
    function seekTo(time: number) {
        if (videoElement) {
            videoElement.currentTime = time;
            videoElement.play();
        }
    }

    /**
     * Handles image loading errors for shot thumbnails.
     */
    function handleImageError(e: Event & { currentTarget: HTMLImageElement }) {
        e.currentTarget.src = 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=Error';
    }
    
    /**
     * Constructs the correct, full URL for a keyframe image.
     */
    function getImageUrl(keyframePath: string): string {
        if (!keyframePath) return 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=No+Path';
        const pathParts = keyframePath.split(/[\/\\]keyframes[\/\\]/);
        const relativePath = pathParts.length > 1 ? pathParts[1] : '';
        if (!relativePath) {
            const fallbackParts = keyframePath.replace(/\\/g, '/').split('/');
            if (fallbackParts.length >= 2) {
                 return `http://localhost:8000/keyframes/${fallbackParts.slice(-2).join('/')}`;
            }
            return 'https://placehold.co/140x79/1e1e1e/aaaaaa?text=Bad+Path';
        }
        return `http://localhost:8000/keyframes/${relativePath.replace(/\\/g, '/')}`;
    }

    // --- Submission Functions ---

    /**
     * Sets the start time for the submission to the video's current time.
     */
    function setStartTime() {
        if (videoElement) {
            startTime.set(videoElement.currentTime);
            submissionStatus.set('idle');
        }
    }
    
    /**
     * Sets the end time for the submission to the video's current time.
     */
    function setEndTime() {
        if (videoElement) {
            endTime.set(videoElement.currentTime);
            submissionStatus.set('idle');
        }
    }

    /**
     * Submits the selected time range to the backend.
     */
    async function submitSelection() {
        if (!canSubmit || !$selectedVideo) return;

        submissionStatus.set('submitting');
        try {
            const response = await fetch('http://localhost:8000/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mediaItemName: $selectedVideo.video_id,
                    start: Math.floor($startTime * 1000),
                    end: Math.floor($endTime * 1000)
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                showAlert(errorData.detail, "danger", 8000);
            }
            
            submissionStatus.set('success');
            setTimeout(() => submissionStatus.set('idle'), 2000);

        } catch (err) {
            console.error('Submission error:', err);
            submissionStatus.set('error');
            setTimeout(() => submissionStatus.set('idle'), 3000);
        }
    }
</script>

<!-- Main container -->
<div class="page-container" class:video-selected={$selectedVideo !== null}>

    <!-- Video Player Wrapper -->
    <div class="video-player-wrapper">
        {#if $selectedVideo}
            <div class="video-player-container" in:fly={{ y: -20, duration: 400, delay: 200 }} out:slide>
                <div class="video-header">
                    <h4>Playing: {$selectedVideo.video_id}</h4>
                    <button class="close-button" on:click={() => selectedVideo.set(null)} title="Close player">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </div>
                
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
                
                <!-- Submission Controls -->
                <div class="submission-controls">
                    <div class="time-selectors">
                        <button class="time-button" on:click={setStartTime}>Set Start</button>
                        <div class="time-display">
                            Start: {$startTime !== null ? $startTime.toFixed(2) + 's' : 'Not set'}
                        </div>
                        <button class="time-button" on:click={setEndTime}>Set End</button>
                         <div class="time-display">
                            End: {$endTime !== null ? $endTime.toFixed(2) + 's' : 'Not set'}
                        </div>
                    </div>
                    <button 
                        class="submit-button"
                        class:submitting={$submissionStatus === 'submitting'}
                        class:success={$submissionStatus === 'success'}
                        class:error={$submissionStatus === 'error'}
                        disabled={!canSubmit || $submissionStatus !== 'idle'}
                        on:click={submitSelection}
                    >
                        {#if $submissionStatus === 'submitting'}
                            Submitting...
                        {:else if $submissionStatus === 'success'}
                            Success!
                        {:else if $submissionStatus === 'error'}
                            Error!
                        {:else}
                            Submit
                        {/if}
                    </button>
                </div>

                <!-- Related Shots Section -->
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
                                    <span class="shot-number">Shot {shot.shot}</span>
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
    <div class="thumbnails-container">
        {#if $loading}
            <p class="message-container loading-message">Loading keyframes...</p>
        {:else if $error}
            <p class="message-container error-message">Error: {$error}</p>
        {:else if $images.length === 0}
            <p class="message-container">No keyframes found. Try adjusting the search query.</p>
        {:else}
            <div class="row">
                {#each $images as img (img.url)}
                    <div class="col">
                        <div class="card h-100" role="button" tabindex="0"
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
        --success-color: #28a745;
        --error-color: #dc3545;
        --shadow-color: rgba(0, 0, 0, 0.3);
    }

    .page-container {
        display: flex;
        flex-direction: column;
        max-width: 1800px;
        margin: 1rem auto;
        padding: 0 1rem;
    }

    /* === YOUTUBE-LIKE LAYOUT ACTIVATION === */
    /* FIX: This is now a fixed-position overlay */
    .page-container.video-selected {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: var(--dark-bg-primary);
        z-index: 1000;
        flex-direction: row;
        gap: 24px;
        padding: 1rem;
        margin: 0;
        box-sizing: border-box;
    }

    .video-selected .video-player-wrapper {
        flex: 1;
        min-width: 0;
        display: flex; /* Use flexbox to manage internal layout */
    }

    .video-selected .thumbnails-container {
        flex: 0 0 420px;
        overflow-y: auto;
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
        display: flex;
        flex-direction: column;
        width: 100%; /* Ensure it fills the wrapper */
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
        width: 100%;
        height: auto;
        /* Allow video to shrink if container is small */
        max-height: 50vh;
    }

    /* === Submission Controls === */
    .submission-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem;
        background-color: var(--dark-bg-tertiary);
        border-top: 1px solid var(--border-color);
        flex-wrap: wrap;
        gap: 1rem;
    }

    .time-selectors {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .time-button {
        background-color: #333;
        color: var(--text-primary);
        border: 1px solid #555;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.2s;
    }

    .time-button:hover {
        background-color: #444;
    }

    .time-display {
        background-color: #222;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-size: 0.9rem;
        color: var(--text-secondary);
        min-width: 100px;
        text-align: center;
    }
    
    .submit-button {
        background-color: var(--accent-color);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.2s, transform 0.1s;
    }

    .submit-button:disabled {
        background-color: #555;
        cursor: not-allowed;
        color: #999;
    }
    
    .submit-button:not(:disabled):hover {
        filter: brightness(1.1);
    }
    .submit-button.submitting {
        background-color: #555;
    }
    .submit-button.success {
        background-color: var(--success-color);
    }
    .submit-button.error {
        background-color: var(--error-color);
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

    /* === Related Shots Styles === */
    .related-shots-container {
        padding: 1rem;
        background-color: var(--dark-bg-tertiary);
        border-top: 1px solid var(--border-color);
        /* Let this area scroll if content overflows */
        overflow-y: auto;
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
        padding-bottom: 0.5rem;
    }

    .shots-grid::-webkit-scrollbar { height: 8px; }
    .shots-grid::-webkit-scrollbar-track { background: var(--dark-bg-secondary); border-radius: 4px; }
    .shots-grid::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
    .shots-grid::-webkit-scrollbar-thumb:hover { background: #777; }

    .shot-thumbnail {
        all: unset;
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

    .shot-thumbnail:hover, .shot-thumbnail:focus-visible { border-color: var(--accent-color); }

    .shot-thumbnail img { width: 100%; height: 100%; object-fit: cover; display: block; }
    
    .shot-number {
        position: absolute;
        top: 4px;
        left: 4px;
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 2px 6px;
        font-size: 0.7rem;
        border-radius: 4px;
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
    .message-container { text-align: center; padding: 2rem; font-size: 1.2rem; color: var(--text-secondary); }
    .error-message { color: #ff8a8a; }
    .loading-message { color: var(--accent-color); }

    /* === RESPONSIVE ADJUSTMENTS === */
    @media (max-width: 992px) {
        .page-container.video-selected {
            position: relative; /* Revert to normal flow on mobile */
            height: auto;
        }
        .video-selected {
            flex-direction: column;
            gap: 24px;
        }
        .video-selected .video-player-wrapper {
            overflow-y: visible;
        }
        .video-selected .thumbnails-container { 
            flex: 1 1 auto;
            max-width: none;
            overflow-y: visible;
        }
    }
    
    @media (max-width: 480px) {
        .row { grid-template-columns: 1fr; }
        .page-container { margin: 0.5rem auto; padding: 0 0.5rem; }
        .submission-controls {
            flex-direction: column;
            align-items: stretch;
        }
        .submit-button {
            width: 100%;
        }
    }
</style>
