<script lang="ts">
    import type { CheckboxPayload } from '../../common/CheckboxInput.svelte';
    import CheckboxInput from '../../common/CheckboxInput.svelte';
    import InfoButton from '../../common/InfoButton.svelte';
    import { nSRankKey } from '../../constants/natureServe';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import type { NSRank } from '../../types/api';
    import { toggleArrayValue } from '../../util/toggleArrayValue';

    const filtersContext = getFiltersContext();

    function handleRankSelect(payload: CheckboxPayload) {
        // Get list of currently selected ranks
        let currRanks = filtersContext.nSRanks || [];
        const value = payload.value as NSRank;

        // Set new list in state
        filtersContext.nSRanks = toggleArrayValue(
            currRanks,
            value,
            payload.checked
        );
    }
</script>

<div
    class="conservation-rank-filter filters-section"
    class:active={!!filtersContext.nSRanks?.length}
>
    <div class="filters-section-header">
        <span>Conservation Ranks</span>
        &nbsp
        <InfoButton
            hover={true}
            type="tooltip"
            htmlContent="This filter uses preliminary ranks determined using unfiltered data from our database"
        />
    </div>
    <div class="filters-section-content rank-filter-list">
        {#each nSRankKey as rankItem}
            <CheckboxInput
                value={rankItem.rank.toUpperCase()}
                name={rankItem.description}
                handler={handleRankSelect}
                checked={!!filtersContext.nSRanks?.includes(rankItem.rank)}
            >
                <span class="rank-filter-label"
                    >{rankItem.rank.toUpperCase()} ({rankItem.description})</span
                >
            </CheckboxInput>
        {/each}
    </div>
</div>

<style>
    .rank-filter-list {
        display: flex;
        flex-direction: column;
        align-items: left;
        white-space: nowrap;
        width: fit-content;
        gap: 0.25rem;
    }
    .rank-filter-label {
        width: fit-content;
    }
</style>
