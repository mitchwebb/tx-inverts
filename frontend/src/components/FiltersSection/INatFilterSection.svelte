<script lang="ts">
    import InfoButton from '../../common/InfoButton.svelte';
    import Toggle from '../../common/Toggle.svelte';
    import { getFiltersContext } from '../../contexts/filtersContext';

    type INatFilterProps = {
        label?: string;
    }

    const {label='Include iNat Data'}: INatFilterProps = $props();

    const filtersContext = getFiltersContext();

    const active = $derived(filtersContext.includeINat);

    function handleINatToggle(toggled: boolean) {
        filtersContext.includeINat = toggled;
    }
</script>

<div id="inat-filters-section" class="filters-section" class:active={!filtersContext.includeINat}>
    <div id="inat-filter-section-header" class="filters-section-header">
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
                    checked={active}
                    onColor="darkgreen"
                    offColor="darkred"
                />
            </div>
            <span class="inat-label">{label}</span>
        </div>
    </div>
</div>

<style>
    #inat-filter-section-header {
        display: flex;
        gap: .25rem;
    }
    .inat-toggle-wrapper {
        display: flex;
        gap: 0.5rem;
        justify-content: left;
        align-items: center;
    }
    .inat-toggle {
        height: 1.5rem;
        width: 1.5rem;
        stroke: var(--text-default);
    }
    .inat-label {
        text-align: left;
        /* white-space: nowrap; */
    }
</style>
