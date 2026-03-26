<!--
    @component
    - Default Texas Inverts body layout
    - Has main body on left and sidebar on right
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Sidebar from '../components/Sidebar/Sidebar.svelte';

    type DefaultPageProps = {
        showSidebar?: boolean;
        children: Snippet;
    };

    const { children, showSidebar = true }: DefaultPageProps = $props();
</script>

<div class="page-wrapper">
    <div class="body-wrapper">
        {@render children?.()}
    </div>
    {#if showSidebar}
        <div id="default-sidebar-wrapper">
            <Sidebar />
        </div>
    {/if}
</div>

<style>
    #default-sidebar-wrapper {
        position: relative;
    }
    .page-wrapper {
        height: 100%;
        width: 100%;
        background-color: var(--container-back);
        display: flex;
        box-sizing: border-box;
        gap: 0.5rem;
        padding: 0.5rem;
    }
    .body-wrapper {
        height: 100%;
        min-width: 300px;
        flex-grow: 1;
        flex-shrink: 1;
        box-sizing: border-box;
        overflow: auto;
        border-radius: 3px;
        border: 1px solid var(--border);
    }
</style>
