<script>
    import { alertVisible, alertColor, alertMessage } from "$lib/stores";
	import { fade } from "svelte/transition";
    
    function closeAlert() {
      alertVisible.set(false);
    }


</script>
  
{#if $alertVisible}
    <div class="overlay" transition:fade={{ duration: 300 }}>
        <div class="alert alert-{$alertColor} alert-dismissible fade show" role="alert">
            {$alertMessage}
            <button type="button" class="btn-close" aria-label="Close" on:click={closeAlert}></button>
        </div>
    </div>
{/if}

<style>
.overlay {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1050;
    min-width: 300px;
    max-width: 500px;
}
</style>
  