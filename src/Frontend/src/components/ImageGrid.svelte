<script lang="ts">
    import { loading, images, error } from "$lib/stores";
    
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