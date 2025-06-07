<script>
  import Navbar from '../components/Navbar.svelte';
  // import ResultsTable from './components/ResultsTable.svelte';
  import { search } from '../lib/api.ts';

  let results = [];

  async function handleSearch(query) {
    try {
      results = await search(query);
    } catch (e) {
      console.error(e);
      alert("Search failed. Try again.");
    }
  }
</script>

<Navbar onSearch={handleSearch} />
