<script lang="ts">
    import { loading, images, error } from "$lib/stores";
    import { writable } from "svelte/store";
    import { fly, slide } from 'svelte/transition';

    // Store for currently selected video segment
    const selectedVideo = writable<{ video_id: string; start_time: number; end_time: number } | null>(null);

    $: videoKey = $selectedVideo
    ? `${$selectedVideo.video_id}_${$selectedVideo.start_time}_${$selectedVideo.end_time}`
    : null;

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
                    <video controls autoplay width="100%">
                        <track kind="captions" />
                        <source
                            src={`/videos/V3C1_200/${$selectedVideo.video_id}.mp4#t=${$selectedVideo.start_time},${$selectedVideo.end_time}`}
                            type="video/mp4"
                        />
                        Your browser does not support the video tag.
                    </video>
                {/key}
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
    /* When a video is selected, the container becomes a row, placing the player and list side-by-side */
    .video-selected {
        flex-direction: row;
        gap: 24px;
        align-items: flex-start;
    }

    .video-selected .video-player-wrapper {
        flex: 1 1 70%; /* Player takes up most of the space */
        position: sticky;
        top: 1rem;
    }

    .video-selected .thumbnails-container {
        flex: 1 1 30%; /* Thumbnails take the remaining space */
        max-width: 420px; /* Max width for the sidebar */
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
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
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
    
    /* When video is selected, thumbnail grid becomes a vertical list */
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

    /* Card styling for the list view (when video is selected) */
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
        width: 160px; /* Fixed width for list view image */
        flex-shrink: 0;
        margin-right: 12px;
    }
    
    .card-body {
        padding: 0.75rem 0.25rem;
    }

    /* When in list view, padding is adjusted */
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
        /* On smaller screens, stack player and list vertically */
        .video-selected {
            flex-direction: column;
            gap: 24px;
        }
        .video-selected .video-player-wrapper {
            position: static; /* Unstick the player */
        }
        .video-selected .thumbnails-container {
            max-width: none; /* Allow list to take full width */
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
