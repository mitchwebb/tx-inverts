<!--
    @component
    - Button with a number display for active filters
-->
<script lang="ts">
    import FiltersIcon from '../assets/FiltersIcon.svelte';

    type FiltersButtonProps = {
        open: boolean;
        count: number;
        handler: (e: MouseEvent) => void;
    };
    const { open, count, handler }: FiltersButtonProps = $props();
</script>

<div class="counted-button-wrapper">
    <button
        class={['counted-button', 'button', { open }]}
        aria-label={`${count} filters active`}
        onclick={handler}
    >
        <div class="icon">
            <FiltersIcon />
        </div>
        <span> Filters </span>
    </button>
    {#if count > 0}
        <div class="count-indicator">
            {count}
        </div>
    {/if}
</div>

<style>
    .counted-button.open {
        background-color: var(--container-back);
        box-shadow: inset 0 2px 5px var(--container-shadow);
    }
    .counted-button-wrapper {
        height: 100%;
        width: 100%;
        position: relative;
        display: flex;
        align-items: center;
    }
    .counted-button {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        padding: 0 0.5rem;
        height: 100%;
        box-sizing: border-box;
        border: 1px solid var(--border);
        width: 100%;
    }
    .count-indicator {
        background-color: var(--accent-color);
        width: 1.3rem;
        height: 1.1rem;
        border-radius: 0.5rem;
        position: absolute;
        top: 0;
        right: 0;
        transform: translate(25%, -25%);
        font-size: 0.8rem;
        color: black;
        font-weight: 550;
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
