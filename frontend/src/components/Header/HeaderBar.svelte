<script lang="ts">
    import { isNarrowView } from '../../contexts/device';
    import TaxaSearch from '../TaxaSearch.svelte';
    import MobileNavbarFoldout from './MobileNavbarFoldout.svelte';
    import MenuIcon from '../../assets/MenuIcon.svelte';
    import { getRouterContext } from '../../contexts/routerContext';
    import type { NavItem } from '../../types/nav';
    import NavbarItem from './NavbarItem.svelte';
    import './header.css';

    const NAV_ITEMS: NavItem[] = [
        { label: 'Map', href: '/map' },
        { label: 'Backbone', href: '/backbone' },
        { label: 'Rankings', href: '/rankings' },
        {
            label: 'About',
            href: '/about/txinverts',
            children: [
                { label: 'Texas Inverts', href: '/about/txinverts' },
                { label: 'Walkthrough', href: '/about/walkthrough' },
            ],
        },
    ];

    const routerContext = getRouterContext();

    let showMenu: boolean = $state(false);

    // If searching for taxa on a page without the sidebar, swap to map page
    function handleTaxonSearch() {
        if (!document.querySelector('#sidebar')) {
            routerContext.navigate('/map');
        }
    }

    $effect(() => {
        const currPath = routerContext.url.pathname;
        if (currPath) {
            showMenu = false;
        }
    });
</script>

<div id="header-bar-wrapper">
    <header id="header-bar">
        <a id="navbar-logo-wrapper" class="logo" href="/">
            <img
                id="logo-text"
                alt="Texas Inverts"
                src="/static/nav_logo_just_text.png"
            />
        </a>
        <div id="header-search-bar">
            <TaxaSearch replace={true} onSelect={handleTaxonSearch} />
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
            <div id="main-nav" class="nav-item">
                {#each NAV_ITEMS as navItem}
                    <NavbarItem item={navItem} variant={'desktop'} />
                {/each}
            </div>
        {/if}
    </header>
    {#if $isNarrowView && showMenu}
        <MobileNavbarFoldout items={NAV_ITEMS} />
    {/if}
</div>

<style>
    #logo-text {
        display: flex;
        flex-direction: column;
        justify-content: center;
        filter: brightness(0) saturate(100%) invert(82%) sepia(17%)
            saturate(360%) hue-rotate(3deg) brightness(94%) contrast(88%);
        height: 40px;
    }
    #navbar-logo-wrapper {
        display: flex;
        justify-content: center;
        gap: 0.25rem;
        align-items: center;
        margin: 0 0.25rem;
    }
    .menu-foldout-button {
        background-color: transparent;
    }
    #header-search-bar {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
        max-width: 350px;
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
        z-index: 101;
        justify-content: space-between;
        position: sticky;
        top: 0;
        box-sizing: border-box;
        border-bottom: solid 1px var(--border);
        box-shadow: 0px 0px 3px var(--container-shadow);
    }
    #header-bar-wrapper {
        position: relative;
        height: fit-content;
        color: var(--text-default);
        box-shadow: 0px 0px 3px var(--container-shadow);
    }
    .logo {
        color: var(--text-default);
        display: flex;
        /* flex-direction: column; */
        /* padding: 0 0.5rem; */
        text-align: left;
    }
    .logo > * {
        font-weight: bold;
        font-size: 1.2rem;
        line-height: 1;
    }
</style>
