<!--
    @component
    - Icon to mark invasive species
    - Triggers tooltip on hover
-->
<script lang="ts">
    import { onDestroy } from 'svelte';
    import AlertTriangle from '../assets/AlertTriangle.svelte';
    import { getTooltipContext } from '../contexts/tooltipContext';

    const tooltipContext = getTooltipContext();

    let invasiveIcon: HTMLButtonElement;

    function handleMouseEnter() {
        if (!invasiveIcon) return;
        tooltipContext.content =
            'This species has been identified as invasive within the United States';
        tooltipContext.visible = true;
        tooltipContext.target = invasiveIcon;
        // tooltipContext.backgroundColor = 'goldenrod';
    }

    function handleMouseExit() {
        tooltipContext.visible = false;
        tooltipContext.content = null;
        tooltipContext.backgroundColor = null;
        tooltipContext.target = null;
    }

    onDestroy(() => {
        handleMouseExit();
    });
</script>

<button
    class="invasive-tooltip-wrapper"
    aria-label="Invasive species information"
    onmouseenter={handleMouseEnter}
    onmouseleave={handleMouseExit}
    onfocus={handleMouseEnter}
    onblur={handleMouseExit}
    bind:this={invasiveIcon}
>
    <div>
        <AlertTriangle />
    </div>
</button>

<style>
    .invasive-tooltip-wrapper {
        cursor: pointer;
        height: 100%;
        width: 100%;
        margin: 0;
        padding: 0;
        background-color: transparent;
        color: var(--accent-color);
        border: none;
    }
</style>
