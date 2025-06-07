<script>
  export let onSearch;
  let query = "";

  const submit = () => {
    if (query.trim().length > 0) {
      onSearch(query);
    }
  };
</script>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
  <a class="navbar-brand" href="/">CBVR System</a>
  <div class="collapse navbar-collapse">
    <form class="d-flex ms-auto" on:submit|preventDefault={submit}>
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
