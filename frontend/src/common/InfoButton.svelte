<!--
    @component
    - Info button for page
    - Relies on tooltipContext for functionality
    - Can be used to trigger tooltip or modal messages
-->
<script lang="ts">
    import { onDestroy, type Component, type Snippet } from 'svelte';
    import InfoIcon from '../assets/InfoIcon.svelte';
    import { getModalContext } from '../contexts/modalContext';
    import { getTooltipContext } from '../contexts/tooltipContext';
    import { openModal } from '../lib/modal.svelte';

    let infoButton: HTMLElement;

    type InfoButtonProps = {
        type: 'modal' | 'tooltip';
        children: Snippet;
        hover?: boolean; // If tooltip and hover, tooltip activates on hover
    };

    let { type = 'modal', children, hover = false }: InfoButtonProps = $props();

    const tooltipContext = getTooltipContext();
    const modalContext = getModalContext();

    function handleMouseEnter() {
        if (infoButton && type === 'tooltip' && hover) {
            showTooltip();
        }
    }

    function handleMouseExit() {
        if (type !== 'tooltip' || !hover) return;

        tooltipContext.visible = false;
        tooltipContext.content = null;
        tooltipContext.target = null;
    }

    function showTooltip() {
        tooltipContext.content = children;
        tooltipContext.target = infoButton;
        tooltipContext.visible = true;
    }

    onDestroy(() => {
        handleMouseExit();
    });

    // Handle click functionality
    function handleInfoClick() {
        if (type === 'modal') {
            openModal(modalContext, children);
        } else if (type === 'tooltip' && infoButton && !hover) {
            showTooltip();
        }
    }
</script>

<button
    class="info-icon-wrapper"
    aria-label="Info button"
    bind:this={infoButton}
    onclick={handleInfoClick}
    onfocus={handleMouseEnter}
    onblur={handleMouseExit}
    onmouseenter={handleMouseEnter}
    onmouseleave={handleMouseExit}
>
    <InfoIcon />
</button>

<style>
    .info-icon-wrapper {
        cursor: pointer;
        position: relative;
        z-index: 1;
        height: 0.9rem;
        padding: 0;
        background-color: transparent;
        border: none;
        color: var(--text-default);
    }
</style>
