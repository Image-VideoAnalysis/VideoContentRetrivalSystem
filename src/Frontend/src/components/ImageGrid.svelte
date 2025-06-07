<script>
  export let images = [];
  
</script>


<div class="container my-4">
  <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
    {#each images as img}
      <div class="col">
        <div
          class="card h-100 shadow-sm"
          style="cursor: pointer;"
        >
          <img src={img.url} class="card-img-top" alt={img.alt || "Keyframe"} />
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
</div>

<style>
  .card {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #2a2a2a;
    transition: background-color 0.2s, transform 0.2s;
  }

  .card:hover {
    background-color: #2a2a2a;
    transform: scale(1.02);
  }

  .card-img-top {
    object-fit: cover;
    max-height: 180px;
  }
</style>