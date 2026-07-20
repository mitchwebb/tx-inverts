<script lang="ts">
    import { getRouterContext } from '../../contexts/routerContext';
    import type { NavItem } from '../../types/nav';
    import NavbarDropdown from './NavbarDropdown.svelte';
    import './header.css';

    type NavItemProps = {
        item: NavItem;
        variant: 'desktop' | 'mobile';
    };

    const { item, variant }: NavItemProps = $props();

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

    const routerContext = getRouterContext();
    const currPath = $derived(routerContext.url.pathname);
</script>

<div class="menu-item navbar-item">
    <!-- Single item -->
    {#if !item.children || !item.children.length}
        {@const active = currPath === item.href}
        <a
            class:active
            class="navbar-link"
            aria-current={active ? 'page' : undefined}
            href={item.href}
            onclick={handleMenuSelect}
            onkeydown={handleMenuSelect}
        >
            {item.label}
        </a>
        <!-- Dropdown item -->
    {:else if item.children}
        {#if variant === 'desktop'}
            <NavbarDropdown {item} />
        {:else if variant === 'mobile'}
            {#each item.children as child (child.label)}
                {@const active = currPath === child.href}
                <a
                    class:active
                    class="navbar-link mobile-navbar-link"
                    aria-current={active ? 'page' : undefined}
                    href={child.href}
                    onclick={handleMenuSelect}
                    onkeydown={handleMenuSelect}
                >
                    {child.label}
                </a>
            {/each}
        {/if}
    {/if}
</div>

<style>
    .mobile-navbar-link {
        padding: 0;
        height: 2.5rem;
    }
    .mobile-navbar-link {
        text-align: left;
    }
    .navbar-item {
        position: relative;
    }
</style>
