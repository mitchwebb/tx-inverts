<script lang="ts">
    import {
        getRouterContext,
        type RouterPath,
    } from '../contexts/routerContext';
    import { capitalizeWords } from '../util/textHelpers';
    import TaxaSearch from './TaxaSearch.svelte';

    const routerContext = getRouterContext();

    const currPath = $derived(routerContext.url.pathname);

    const navRoutes: RouterPath[] = ['/map', '/backbone', '/rankings'];

    // Handle header bar page navigation
    function handleMenuSelect(e: MouseEvent | KeyboardEvent) {
        // If it's a keyboard event, only respond to Enter or Space
        if (e instanceof KeyboardEvent) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
        }

        // Prevent full reloading (normal navigation)
        e.preventDefault();

        const target = e.currentTarget as HTMLAnchorElement;
        const pathname = target.getAttribute('href');

        if (!pathname) return;

        // Navigate to page (ignoring same-page clicks)
        if (pathname !== window.location.pathname) {
            routerContext.navigate(pathname, true);
        }
    }
</script>

<!-- Snippet for click-to-navigate header links -->
{#snippet menuPageLink(path: RouterPath)}
    {@const active = currPath === path}
    <li class:active>
        <a
            class="navbar-link"
            aria-current={active ? 'page' : undefined}
            href={path}
            onclick={handleMenuSelect}
            onkeydown={handleMenuSelect}
        >
            {capitalizeWords(path.slice(1))}
        </a>
    </li>
{/snippet}

<header id="header-bar">
    <!-- TODO: Find a more endearing logo -->
    <a class="logo nav-item" href="/">
        <div>TEXAS</div>
        <div>INVERTS</div>
    </a>
    <div id="header-search-bar">
        <TaxaSearch replace={true} />
    </div>

    <ul id="main-nav" class="nav-item">
        {#each navRoutes as route, i}
            {@render menuPageLink(route)}
        {/each}
    </ul>
</header>

<style>
    #header-search-bar {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
        max-width: 350px;
    }
    .navbar-link {
        all: unset;
        height: 100%;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-decoration: none;
    }
    #main-nav li {
        list-style-type: none;
        height: 100%;
        display: flex;
        align-items: center;
        user-select: none;
        cursor: pointer;
        border-bottom: 3px solid transparent;
        padding: 0 1rem;
        box-sizing: border-box;
    }
    #main-nav li:hover {
        color: var(--fill-color);
    }
    #main-nav li.active {
        border-bottom: 3px solid var(--fill-color);
    }
    #main-nav.nav-item {
        padding: 0;
    }
    #main-nav {
        height: 100%;
        flex-grow: 1;
        display: flex;
        margin: 0;
    }
    #header-bar {
        flex-shrink: 0;
        height: 65px;
        background-color: var(--container-fore);
        display: flex;
        align-items: center;
        width: fit-content;
        min-width: 100%;
        padding: 0 2rem;
        gap: 2rem;
        z-index: 100;
        color: var(--text-default);
        box-shadow: 0px 0px 4px var(--container-shadow);
        justify-content: space-between;
        position: sticky;
        top: 0;
        box-sizing: border-box;
    }
    .logo {
        color: var(--text-default);
        display: flex;
        flex-direction: column;
    }
    .logo > * {
        font-weight: bold;
        font-size: 1.2rem;
        line-height: 1;
    }
</style>
