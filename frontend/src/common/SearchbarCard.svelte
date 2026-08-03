<script lang="ts">
    import type { Snippet } from 'svelte';
    import XIcon from '../assets/XIcon.svelte';

    type SearchCardProps = {
        label: string | Snippet;
        value: string | number;
        handleRemoveCard: (value: string | null) => void;
    };

    const { label, value, handleRemoveCard }: SearchCardProps = $props();

    function removeCard(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;
        const cardValue = target.dataset.cardValue;
        handleRemoveCard(cardValue ?? null);
    }
</script>

<div class="searchbar-card">
    <div class="card-label">
        {#if typeof label === 'string'}
            {label}
        {:else}
            {@render label()}
        {/if}
    </div>
    <button
        class="remove-card-button button"
        data-card-value={value}
        onclick={removeCard}
    >
        <div class="remove-card-icon">
            <XIcon />
        </div>
    </button>
</div>

<style>
    .card-label {
        padding: 0.25rem 0.5rem;
        user-select: none;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        overflow: hidden;
        min-width: 0;
    }
    .remove-card-icon {
        height: 1.5rem;
        pointer-events: none;
    }
    .remove-card-button {
        cursor: pointer;
        padding: 0;
        background-color: var(--container-back);
        border-radius: 3px;
        height: 100%;
        width: 2.25rem;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .searchbar-card {
        display: flex;
        background-color: var(--container-mid);
        cursor: unset;
        justify-content: space-between;
        border: 1px solid var(--border);
        font-size: 0.8rem;
        align-items: center;
        height: 30px;
        border-radius: 3px;
        max-width: 350px;
        width: 100%;
        box-sizing: border-box;
    }
</style>
