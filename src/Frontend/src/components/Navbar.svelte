<script>
    import { fetchVideos } from "$lib/stores";

  let query = "";

  let searchType = 'keyframe';

  const submit = () => {
    if (searchType === 'keyframe') {
      // Logic for searching keyframes
      console.log("Searching keyframes for:", query);
      // Call the function to fetch keyframes based on the query
      fetchVideos(query);
    } else {
      // Logic for searching videos
      console.log("Searching videos for:", query);
      // Call the function to fetch videos based on the query
      fetchVideos(query);
    }
  };

</script>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
  <a class="navbar-brand" href="/">CBVR System</a>
  <div class="collapse navbar-collapse">
    <form class="d-flex ms-auto" on:submit|preventDefault={submit}>
      <select class="form-select me-2" bind:value={searchType} style="width: auto;">
        <option value="keyframe">Keyframes</option>
        <option value="video">Video</option>
      </select>
      <input
        class="form-control me-2"
        type="search"
        placeholder="Search scenes..."
        aria-label="Search"
        bind:value={query}
      />
      <button class="btn btn-outline-light" type="submit">Search</button>
    </form>
  </div>
</nav>
