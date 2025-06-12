<script lang="ts">
    import { fetchVideos } from '$lib/stores';
  import ImageGrid from '../components/ImageGrid.svelte';
  import { onMount } from 'svelte';

  // Call the fetch function when the component is mounted to the DOM
  onMount(() => {
      fetchVideos();
  });

</script>

<ImageGrid/>

