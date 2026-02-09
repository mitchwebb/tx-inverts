<script lang="ts">
    import InfoButton from '../../common/InfoButton.svelte';
    import Toggle from '../../common/Toggle.svelte';
    import { getFiltersContext } from '../../contexts/filtersContext';

    const filtersContext = getFiltersContext();

    function handleINatToggle(toggled: boolean) {
        filtersContext.includeINat = toggled;
    }
</script>

<div class="filters-section" class:active={!filtersContext.includeINat}>
    <div id="inat-filters-section" class="filters-section-header">
        <span>iNaturalist</span>
        <InfoButton
            type="tooltip"
            htmlContent="<span>By default, our site includes iNaturalist Research Grade Observations in our preliminary conservation rankings. These may be toggled on or off as desired.</span>"
            hover={true}
        />
    </div>
    <div class="filters-section-content">
        <div class="inat-toggle-wrapper">
            <div class="inat-toggle">
                <Toggle
                    handler={handleINatToggle}
                    checked={filtersContext.includeINat !== false}
                    onColor="darkgreen"
                    offColor="darkred"
                />
            </div>
            <span class="sidebar-header-text">iNaturalist Data</span>
        </div>
    </div>
</div>

<style>
    #inat-filters-section {
        display: flex;
        gap: 0.25rem;
    }
    .inat-toggle-wrapper {
        display: flex;
        gap: 0.5rem;
        justify-content: left;
    }
    .inat-toggle {
        height: 1.5rem;
        stroke: var(--text-default);
    }
</style>
