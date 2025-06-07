<script>
    // Esempio di elenco di immagini (puoi sostituire con i tuoi dati)
    export let images = [
        "https://via.placeholder.com/300",
        "https://via.placeholder.com/300",
        "https://via.placeholder.com/300",
        // Aggiungi altre immagini qui
    ];
</script>

<style>
    .image-grid {
        display: flex;
        flex-wrap: wrap;
        margin: -15px;
    }

    .image-grid-item {
        width: calc(25% - 30px);
        margin: 15px;
        box-sizing: border-box;
    }
</style>

<div class="container">
    <div class="row image-grid">
        {#each images as image, index}
            <div class="col-md-3 image-grid-item">
                <img src={image} class="img-fluid" />
            </div>
        {/each}
    </div>
</div>