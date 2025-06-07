<script>
    import ImageGrid from '../components/ImageGrid.svelte';

    // Esempio di elenco di immagini (puoi sostituire con i tuoi dati)
    let images = [
        "https://via.placeholder.com/300",
        "https://via.placeholder.com/300",
        "https://via.placeholder.com/300",
        // Aggiungi altre immagini qui
    ];
</script>

    <!-- Utilizzo del componente ImageGrid -->
    <ImageGrid images={images} />

<style>
/* Aggiungi qui lo stile generale dell'applicazione */
body {
    font-family: Arial, sans-serif;
    padding: 20px;
}
</style>