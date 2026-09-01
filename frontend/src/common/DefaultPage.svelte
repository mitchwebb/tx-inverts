<!--
    @component
    - Default Texas Inverts body layout
    - Has main body on left and sidebar on right
-->
<script lang="ts">
    import type { Snippet } from 'svelte';
    import Sidebar from '../components/Sidebar/Sidebar.svelte';
    import { isNarrowView } from '../contexts/device';
    import { getActiveTaxaContext } from '../contexts/activeTaxaContext';
    type DefaultPageProps = {
        overlay?: boolean;
        showSidebar?: boolean;
        children: Snippet;
    };

    const {
        children,
        overlay = false,
        showSidebar = true,
    }: DefaultPageProps = $props();

    const taxaContext = getActiveTaxaContext();
</script>

<div class="page-wrapper" class:overlay>
    <div class="page-contents">
        <div class="body-wrapper">
            {@render children?.()}
        </div>
        {#if showSidebar && !$isNarrowView}
            <div id="default-sidebar-positioner">
                <div id="default-sidebar-wrapper">
                    <Sidebar activeTaxa={taxaContext.taxa.items} />
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    #default-sidebar-positioner {
        align-items: flex-start;
        flex: 1 1 325px;
        height: 100%;
        display: flex;
        flex-direction: column;
        max-width: 325px;
    }
    .page-wrapper.overlay #default-sidebar-wrapper {
        background-color: var(--container-back);
        padding: 0.5rem;
        border-radius: 3px;
        width: 100%;
    }
    #default-sidebar-wrapper {
        position: relative;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        max-height: 100%;
        height: fit-content;
    }
    .page-wrapper {
        height: 100%;
        width: 100%;
        background-color: var(--container-back);
        display: grid;
        grid-template-rows: auto;
        overflow: hidden;
        box-sizing: border-box;
    }
    .page-wrapper.overlay {
        background-color: transparent;
    }
    .body-wrapper {
        height: 100%;
        flex: 1 1 800px;
        box-sizing: border-box;
        overflow: auto;
        border-radius: 3px;
        border: 1px solid var(--border);
        position: relative;
    }
    .page-wrapper.overlay .body-wrapper {
        border: none;
    }
    .page-contents {
        /* height: 100%; */
        display: flex;
        grid-column: 1;
        overflow: hidden;
        gap: 0.5rem;
        padding: 0.5rem;
    }
</style>
