<script lang="ts">
    import { onDestroy, onMount } from 'svelte';
    import { getRouterContext } from '../../contexts/routerContext';
    import type { NavItem } from '../../types/nav';
    import ChevronDown from '../../assets/ChevronDown.svelte';
    import './header.css';

    type NavDropdownProps = {
        item: NavItem;
    };

    const { item }: NavDropdownProps = $props();

    const routerContext = getRouterContext();
    const currPath = $derived(routerContext.url.pathname);

    // Handle header bar page navigation
    function handleMenuSelect(e: MouseEvent | KeyboardEvent) {
        if (dropdownOpen) {
            dropdownOpen = false;
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

    let dropdownOpen = $state(false);

    function handleDropdown() {
        dropdownOpen = !dropdownOpen;
    }

    function handleOutsideDropdownClick(e: MouseEvent) {
        if (!dropdownOpen) return;
        const target = e.target as HTMLElement;
        if (!target.closest('.navbar-dropdown-button')) {
            dropdownOpen = false;
        }
    }

    // Determine if any children are selected
    const parentActive = $derived(
        item.children?.map((child) => child.href).includes(currPath)
    );

    onMount(() =>
        document.addEventListener('click', handleOutsideDropdownClick)
    );
    onDestroy(() =>
        document.removeEventListener('click', handleOutsideDropdownClick)
    );
</script>

<div class="navbar-link" class:active={parentActive}>
    <button class="navbar-dropdown-button" onclick={handleDropdown}>
        <div>{item.label}</div>
        <div class="icon navbar-icon"><ChevronDown /></div>
    </button>
</div>

{#if dropdownOpen}
    <div id={`${item.label}-dropdown`} class="navbar-dropdown">
        {#each item.children as dropdownItem}
            {@const childActive = dropdownItem.href === currPath}
            <a
                class:active={childActive}
                class="dropdown-item navbar-link"
                aria-current={childActive ? 'page' : undefined}
                href={dropdownItem.href}
                onclick={handleMenuSelect}
                onkeydown={handleMenuSelect}
            >
                {dropdownItem.label}
            </a>
        {/each}
    </div>
{/if}

<style>
    .dropdown-item {
        text-align: left;
    }
    .navbar-icon {
        height: 1rem;
        width: 1rem;
    }
    .navbar-dropdown {
        position: absolute;
        top: calc(100% - 5px);
        background-color: var(--container-mid);
        border: 1px solid var(--border);
        min-width: 150px;
        display: flex;
        flex-direction: column;
        justify-content: left;
        align-items: start;
        box-shadow: 0px 3px 6px var(--container-shadow);
        border-radius: 3px;
    }
    .navbar-dropdown .navbar-link {
        padding: 0.5rem 1rem;
        white-space: nowrap;
        align-items: flex-start;
    }
    .navbar-dropdown .navbar-link.active {
        background-color: var(--container-back);
    }
    .navbar-dropdown .navbar-link.active {
        border-bottom: none;
    }
    .navbar-dropdown-button {
        all: unset;
        height: 100%;
        background-color: transparent;
        cursor: pointer;
        position: relative;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        flex-wrap: nowrap;
        gap: 0.25rem;
    }
</style>
