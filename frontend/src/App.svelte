<script lang="ts">
    import Layout from './routes/Layout.svelte';
    import './app.css';
    import { taxaTree } from './contexts/TaxaTree';
    import { datasets } from './contexts/Datasets';
    import { onMount } from 'svelte';
    import Tooltip from './common/Tooltip.svelte';
    import {
        initialTooltipState,
        setTooltipContext,
    } from './contexts/tooltipContext';
    import { loadBackbone } from './lib/taxa';
    import { loadDatasets } from './lib/occurrence';

    // Load taxaTree and datasets structures on mount
    onMount(() => {
        if (!$taxaTree) {
            loadBackbone();
        }
        if (!$datasets) {
            loadDatasets();
        }
    });

    const tooltipState = $state(initialTooltipState);
    setTooltipContext(tooltipState);
</script>

<div id="theme-wrapper" data-theme={'dark'}>
    <Tooltip />
    <div id="portal-root"></div>
    <Layout />
    <div style:display="none">For Marimba</div>
</div>

<style>
    #theme-wrapper {
        height: 100%;
        width: 100%;
        display: flex;
        flex-direction: column;
    }
</style>
