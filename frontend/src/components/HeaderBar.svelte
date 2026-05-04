<script lang="ts">
    import { slide } from 'svelte/transition';
    import MenuIcon from '../assets/MenuIcon.svelte';
    import { isNarrowView } from '../contexts/device';
    import {
        getRouterContext,
        type RouterPath,
    } from '../contexts/routerContext';
    import { capitalizeWords } from '../util/textHelpers';
    import TaxaSearch from './TaxaSearch.svelte';
    import { onDestroy, onMount } from 'svelte';

    const routerContext = getRouterContext();

    const currPath = $derived(routerContext.url.pathname);

    const navRoutes: RouterPath[] = [
        '/map',
        '/backbone',
        '/rankings',
        '/about',
    ];

    // Handle header bar page navigation
    function handleMenuSelect(e: MouseEvent | KeyboardEvent) {
        if (showMenu) {
            showMenu = false;
        }
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

    let showMenu: boolean = $state(false);

    function handleOutsideMenuClick(e: MouseEvent) {
        if (!showMenu) return;
        const target = e.target as HTMLElement;
        if (
            !target.closest('#main-nav-foldout') &&
            !target.closest('#menu-foldout-button')
        ) {
            showMenu = false;
        }
    }

    onMount(() => document.addEventListener('click', handleOutsideMenuClick));
    onDestroy(() =>
        document.removeEventListener('click', handleOutsideMenuClick)
    );
</script>

<!-- Snippet for click-to-navigate header links -->
{#snippet menuPageLink(path: RouterPath)}
    {@const active = currPath === path}
    <a
        class:active
        class="navbar-link"
        aria-current={active ? 'page' : undefined}
        href={path}
        onclick={handleMenuSelect}
        onkeydown={handleMenuSelect}
    >
        {capitalizeWords(path.slice(1))}
    </a>
{/snippet}

<div id="header-bar-wrapper">
    <header id="header-bar">
        <!-- TODO: Find a more endearing logo -->
        <a class="logo nav-item" href="/">
            <div>TEXAS</div>
            <div>INVERTS</div>
        </a>
        <div id="header-search-bar">
            <TaxaSearch replace={true} />
        </div>

        {#if $isNarrowView}
            <button
                class="menu-foldout-button"
                onclick={(e) => {
                    e.stopPropagation();
                    showMenu = !showMenu;
                }}
            >
                <MenuIcon />
            </button>
        {:else}
            <div id="main-nav" class="nav-item menu-item">
                {#each navRoutes as route, i}
                    <div class="menu-item">
                        {@render menuPageLink(route)}
                    </div>
                {/each}
            </div>
        {/if}
    </header>
    {#if $isNarrowView && showMenu}
        <div id="main-nav-foldout" class="nav-item" transition:slide>
            {#each navRoutes as route, i}
                <div class="foldout-link">
                    {@render menuPageLink(route)}
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .menu-foldout-button {
        background-color: transparent;
        /* padding: 0; */
    }
    #main-nav-foldout {
        position: absolute;
        top: 100%;
        left: 0;
        z-index: 9998;
        display: flex;
        flex-direction: column;
        background-color: var(--container-mid);
        border-bottom: 1px solid var(--border);
        /* box-shadow: 0px 5px 10px 0px var(--container-shadow); */
        width: 100%;
    }
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
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
        padding: 0 1rem;
        cursor: pointer;
    }
    #main-nav .navbar-link {
        height: 100%;
        display: flex;
        align-items: center;
        border-bottom: 3px solid transparent;
    }
    #main-nav .navbar-link.active {
        border-bottom: 3px solid var(--fill-color);
    }
    #main-nav-foldout .navbar-link {
        text-align: left;
        border-left: 3px solid transparent;
        width: 100%;
        padding: 0.5rem 1rem;
    }
    #main-nav-foldout .navbar-link:hover {
        background-color: var(--container-back);
    }
    #main-nav-foldout .navbar-link.active {
        background-color: var(--container-back);
    }
    .navbar-link:hover {
        color: var(--fill-color);
    }
    .menu-item {
        list-style-type: none;
        user-select: none;
        cursor: pointer;
        box-sizing: border-box;
    }
    #main-nav {
        height: 100%;
        flex-grow: 1;
        display: flex;
        margin: 0;
    }
    #header-bar {
        height: 65px;
        flex-shrink: 0;
        background-color: var(--container-fore);
        display: flex;
        align-items: center;
        width: 100%;
        padding: 0rem 1rem;
        gap: 1rem;
        z-index: 100;
        justify-content: space-between;
        position: sticky;
        top: 0;
        box-sizing: border-box;
        overflow: clip;
        border-bottom: solid 1px var(--border);
        box-shadow: 0px 0px 4px var(--container-shadow);
    }
    #header-bar-wrapper {
        position: relative;
        height: fit-content;
        color: var(--text-default);
        box-shadow: 0px 0px 4px var(--container-shadow);
    }
    .logo {
        color: var(--text-default);
        display: flex;
        flex-direction: column;
        padding: 0 0.5rem;
        text-align: left;
    }
    .logo > * {
        font-weight: bold;
        font-size: 1.2rem;
        line-height: 1;
    }
</style>
