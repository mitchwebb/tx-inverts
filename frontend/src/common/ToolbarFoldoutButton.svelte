<!--
    @component
    - Button for map overlay toolbar with foldout contents
-->
<script lang="ts">
    import type { Component, Snippet } from 'svelte';

    type ToolbarFoldoutProps = {
        id: string;
        ButtonLabel: string | Component;
        ariaLabel: string;
        children: Snippet;
    };

    let { id, ButtonLabel, ariaLabel, children }: ToolbarFoldoutProps =
        $props();
    let expanded = $state(false);
</script>

<div {id} class={['foldout-button-wrapper', { expanded }]}>
    <button
        class="foldout-button button"
        aria-label={ariaLabel}
        aria-expanded={expanded}
        onclick={() => (expanded = !expanded)}
    >
        {#if typeof ButtonLabel === 'string'}
            {ButtonLabel}
        {:else}
            <ButtonLabel />
        {/if}
    </button>
    {#if expanded}
        <div class="foldout-content rounded">
            {@render children?.()}
        </div>
    {/if}
</div>

<style>
    .foldout-content {
        background-color: var(--container-mid);
        border: 1px solid var(--container-shadow);
        display: flex;
        flex-direction: column;
        align-self: baseline;
        position: absolute;
        max-height: 400px;
        left: 0;
        top: calc(100% + 2px);
        overflow-y: auto;
    }
    .foldout-button-wrapper {
        /* border: 1px solid var(--container-shadow); */
        border-radius: 3px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 100;
        position: relative;
        height: 1.5rem;
    }
    .foldout-button {
        background-color: var(--container-fore);
        border: 1px solid var(--border);
        color: var(--text-default);
        height: 100%;
        width: max-content;
        padding: 5px 1rem;
        margin: 0;
        flex-shrink: 0;
        box-sizing: border-box;
    }
</style>
