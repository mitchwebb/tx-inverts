<script lang="ts">
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import { nSRankKey } from '../../constants/natureServe';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import type { NSRank } from '../../types/api';

    const filtersContext = getFiltersContext();

    function handleRankSelect(payload: CheckboxPayload) {
        // Get list of currently selected ranks
        let currRanks = filtersContext.nSRanks || [];
        const value = payload.value as NSRank;

        currRanks = payload.checked
            ? [...new Set([...currRanks, value])] // If checked, add provided and dedupe list
            : currRanks.filter((rank) => rank !== value); // Remove provider if unchecked

        // Set new list in state
        filtersContext.nSRanks = currRanks;
    }
</script>

<div
    class="conservation-rank-filter filters-section"
    class:active={!!filtersContext.nSRanks?.length}
>
    <div class="filters-section-header">Conservation Rank</div>
    <div class="filters-section-content">
        {#each nSRankKey as rankItem}
            <CheckboxInput
                value={rankItem.rank.toUpperCase()}
                name={rankItem.description}
                handler={handleRankSelect}
                checked={!!filtersContext.nSRanks?.includes(rankItem.rank)}
            >
                <span
                    >{rankItem.rank.toUpperCase()} ({rankItem.description})</span
                >
            </CheckboxInput>
        {/each}
    </div>
</div>

<style>
    .conservation-rank-filter {
        display: flex;
        flex-direction: column;
        align-items: left;
        white-space: nowrap;
    }
</style>
