<script>
    import { fetchVideos } from "$lib/stores";

  let query = "";

  let itemsPerPage = 10;

  const submit = () => {
      console.log("Searching keyframes for:", query);
      // Call the function to fetch keyframes based on the query
      fetchVideos(query, itemsPerPage);
  };

</script>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
  <a class="navbar-brand" href="/">CBVR System</a>
  <div class="collapse navbar-collapse">
    <form class="d-flex ms-auto" on:submit|preventDefault={submit}>
      <select class="form-select me-2" bind:value={itemsPerPage} style="width: auto;">
        <option value="10">10</option>
        <option value="20">20</option>
        <option value="30">30</option>
        <option value="50">50</option>
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
