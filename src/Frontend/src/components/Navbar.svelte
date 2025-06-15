<script lang="ts">
    import { fetchVideos, showAlert } from "$lib/stores";
    import { writable } from "svelte/store";

    let query = "";
    let itemsPerPage = 10;
    
    // --- State for Login ---
    const loginStatus = writable<'idle' | 'loading' | 'success' | 'error'>('idle');

    const submit = () => {
        console.log("Searching keyframes for:", query);
        fetchVideos(query, itemsPerPage);
    };

    /**
     * Calls the backend /login endpoint and updates the UI based on the response.
     */
    const login = async () => {
        loginStatus.set('loading');
        try {
            const response = await fetch('http://localhost:8000/login', {
                method: 'POST',
            });

            if (response.ok) {
                console.log("Login successful");
                loginStatus.set('success');
            } else {
                const error = await response.json();
                console.error("Login failed:", error);
                showAlert(error.detail, "danger", 8000);
                loginStatus.set('error');
            }
        } catch (error) {
            console.error("Error during login:", error);
            loginStatus.set('error');
        }
    };
</script>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
    <a class="navbar-brand" href="/">CBVR System</a>
    
    <!-- Login Button and Status Indicator -->
    <div class="login-container">
        <button 
            class="btn btn-outline-light" 
            type="button" 
            on:click={login}
            disabled={$loginStatus === 'loading'}
        >
            {#if $loginStatus === 'loading'}
                Logging in...
            {:else}
                Login
            {/if}
        </button>
        
        {#if $loginStatus === 'success'}
            <span class="login-status-icon success" title="Login successful">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </span>
        {:else if $loginStatus === 'error'}
            <span class="login-status-icon error" title="Login failed">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
            </span>
        {/if}
    </div>

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

<style>
    .login-container {
        display: flex;
        align-items: center;
        gap: 0.5rem; /* Space between button and icon */
        margin-left: 1rem;
    }

    .login-status-icon {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .login-status-icon.success svg {
        color: #28a745; /* Green */
    }

    .login-status-icon.error svg {
        color: #dc3545; /* Red */
    }
</style>
