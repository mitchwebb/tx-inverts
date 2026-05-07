<script lang="ts">
    import { slide } from 'svelte/transition';
    import './header.css';
    import NavbarItem from './NavbarItem.svelte';
    import type { NavItem } from '../../types/nav';

    type MobileNavProps = {
        items: NavItem[];
    };

    const { items }: MobileNavProps = $props();
</script>

<div id="main-nav-foldout" class="nav-item" transition:slide>
    {#each items as navItem (navItem.label)}
        <NavbarItem item={navItem} variant={'mobile'} />
    {/each}
</div>

<style>
    #main-nav-foldout {
        position: absolute;
        top: 100%;
        left: 0;
        z-index: 9998;
        display: flex;
        flex-direction: column;
        background-color: var(--container-mid);
        border-bottom: 1px solid var(--border);
        box-shadow: 0px 3px 6px var(--container-shadow);
        width: 100%;
    }
    :global(#main-nav-foldout .navbar-link) {
        width: 100%;
        padding: 0.5rem 1rem;
        align-items: flex-end;
    }
    :global(#main-nav-foldout .navbar-link:hover) {
        background-color: var(--container-back);
    }
    :global(#main-nav-foldout .navbar-link.active) {
        background-color: var(--container-back);
    }
    :global(#main-nav-foldout .navbar-link.active) {
        border-bottom: none;
    }
</style>
