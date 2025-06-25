<script>
    import Alert from '../components/Alert.svelte';
    import Navbar from '../components/Navbar.svelte';

    export let title = "Content-Based Video Retrieval";

</script>

<Navbar />

<Alert />

<main>
  <slot />
</main>

<footer class="text-center py-3 border-top mt-5">
</footer>


<style>
  :global(body) {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  header, footer {
    background-color: #1f1f1f;
    color: #f1f1f1;
  }

  main {
    padding: 1.5rem;
  }

  a, .nav-link {
    color: #f1f1f1;
    text-decoration: none;
  }

  a:hover {
    color: #cccccc;
  }

  .card {
    background-color: #1e1e1e;
    border: 1px solid #2c2c2c;
    color: #e0e0e0;
  }

  .card:hover {
    background-color: #2a2a2a;
  }

  .navbar {
    background-color: #1a1a1a;
  }

  .btn-dark {
    background-color: #333;
    border-color: #444;
  }

  .btn-dark:hover {
    background-color: #444;
  }
</style>
