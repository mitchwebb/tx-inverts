<script lang="ts">
    import EyeOff from '../../assets/EyeOff.svelte';
    import EyeOn from '../../assets/EyeOn.svelte';
    import NSScale from '../../common/NSScale.svelte';
    import { getMapContext } from '../../contexts/mapContext';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { nSRankKey } from '../../constants/natureServe';
    import { handleLayerToggle } from '../../util/handleMapLayerToggle';
    import NSCircle from '../../common/NSCircle.svelte';
    import SidebarFoldout from './SidebarFoldout.svelte';
    import { getRouterContext } from '../../contexts/routerContext';
    import { toLocaleRounded } from '../../util/textHelpers';
    import Toggle from '../../common/Toggle.svelte';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import CheckboxInput, {
        type CheckboxPayload,
    } from '../../common/CheckboxInput.svelte';
    import {
        layerGroups,
        type LayerGroupID,
        type MapLayerID,
    } from '../../lib/map/mapLayers';
    import InfoButton from '../../common/InfoButton.svelte';
    import { countActiveFilters } from '../../lib/filters.svelte';
    import { calculateNSRank } from '../../lib/natureServe';
    import { getMetricsContext } from '../../contexts/metricsParamsContext';

    const mapContext = getMapContext();

    const taxonContext = getActiveTaxonContext();
    const taxonInfo = $derived(taxonContext.taxonInfo);
    const nSValues = $derived(taxonContext.nSValues);

    const filtersContext = getFiltersContext();
    const routerContext = getRouterContext();
    const metricsContext = getMetricsContext();

    // Determine if there are any active observations filters affecting the ranking
    const filtersActive = $derived.by(() => {
        const count = countActiveFilters(filtersContext, 'observations');
        return count > 0;
    });

    const isMapPage: boolean = $derived(routerContext.url.pathname === '/map');

    let aOOGridSize = $derived(metricsContext.aOOResolution);

    let aOOValue = $derived(
        metricsContext.aOOResolution == '4km2'
            ? nSValues.areaOfOccupancy4Km2Bins
            : nSValues.areaOfOccupancy1Km2Bins
    );

    // Update nSRankLocal on nSValue changes
    const localRank = $derived(deriveLocalRank());

    // As long as we're not using it anywhere else, the local nSRank can live
    // in this component
    function deriveLocalRank() {
        if (
            taxonContext.taxonInfo.taxonRank &&
            ['species', 'subspecies'].includes(taxonContext.taxonInfo.taxonRank)
        ) {
            if (
                aOOValue !== null &&
                nSValues.numberOfOccurrences !== null &&
                nSValues.rangeExtentKm2 !== null
            ) {
                const localRank = calculateNSRank(
                    nSValues.numberOfOccurrences,
                    nSValues.rangeExtentKm2,
                    aOOValue
                );
                return localRank;
            } else {
                return null;
            }
        } else {
            return null;
        }
    }

    // Determine conservation rank of current taxonID
    // Default to locally calculated rank, then to rank stored on database
    const rank = $derived(
        localRank ||
            (filtersContext.includeINat
                ? taxonInfo.nSRankDB
                : taxonInfo.nSRankDBNoINat)
    );

    // According to IUCN, rangeExtent should be at LEAST areaOfOccupancy,
    // as areaOfOccupancy is defined to be an area within rangeExtent
    const adjusted_range_extent = $derived.by(() => {
        const range = nSValues.rangeExtentKm2;
        const aooBins = nSValues.areaOfOccupancy4Km2Bins;
        if (range == null || aooBins == null) {
            return null;
            // If both values exist make AOO at least rangeExtent
        } else {
            const aooKm2 = aooBins * 4;
            return range < aooKm2 ? aooKm2 : range;
        }
    });

    function aOOGridHandler(e: Event) {
        const target = e.target as HTMLSelectElement;
        const gridSize = target.value as '1km2' | '4km2';
        metricsContext.aOOResolution = gridSize;
    }

    function layerToggleHandler(payload: CheckboxPayload) {
        const layerID = payload.value as MapLayerID | LayerGroupID;
        const layerVisible = payload.checked as boolean;
        handleLayerToggle(mapContext, { layerID, layerVisible });
    }

    function handleINatToggle(toggled: boolean) {
        filtersContext.includeINat = toggled;
    }
</script>

<SidebarFoldout
    defaultOpen={true}
    label="Conservation Values"
    isLoading={taxonContext.nSValuesLoading}
    customClass="ns-section-wrapper"
>
    {#snippet closedDisplay()}
        {#if rank && !taxonInfo.usInvasive}
            <NSCircle active={true} level="s" rank={rank ? rank : 'u'} />
        {/if}
    {/snippet}
    {#if filtersActive}
        <div id="filter-warning">Filters Applied to Data</div>
    {/if}
    <div class="ns-section">
        {#if rank && !taxonInfo.usInvasive}
            <div id="rank-text" class="centered-text subheader">
                <span
                    >{nSRankKey.find((item) => item.rank === rank)
                        ?.description}</span
                >
                <div class="info-button">
                    <InfoButton
                        type="tooltip"
                        hover={true}
                        htmlContent={'<div>The rankings made on this site are programmatically derived using public data. These are preliminary rankings meant for exploration and do not represent official rankings made by experts.</div>'}
                    />
                </div>
            </div>
            <div class="rank-scale">
                <NSScale level="s" {rank} />
            </div>
        {/if}

        <!-- On the map page, we give the ability to toggle layers -->
        {#snippet eyeIcon(checked: boolean)}
            {#if isMapPage}
                <div class="inline-icon icon">
                    {#if checked}
                        <EyeOn />
                    {:else}
                        <EyeOff />
                    {/if}
                </div>
            {/if}
        {/snippet}

        <div id="ns-metrics-section">
            <div id="occurrences-section" class="ns-metric-row">
                {#if nSValues.numberOfOccurrences}
                    <div id="occurrences-text">
                        <span>Occurrences:</span>
                        <span class="thin">
                            {nSValues.numberOfOccurrences.toLocaleString()}
                        </span>
                    </div>
                    {#if isMapPage}
                        <CheckboxInput
                            customClass="space-between"
                            name="observations-checkbox"
                            value="observations-layer-group"
                            handler={layerToggleHandler}
                            checked={mapContext.isLayerGroupActive(
                                'observations-layer-group'
                            )}
                            checkboxIcon={eyeIcon}
                        />
                    {/if}
                {/if}
            </div>
            <div id="observations-section" class="ns-metric-row">
                {#if nSValues.observationCount}
                    <div id="observations-text">
                        <span>Individual Observations:</span>
                        <span class="thin">
                            {nSValues.observationCount.toLocaleString()}
                        </span>
                    </div>
                {/if}
            </div>
            <div id="range-extent-section" class="ns-metric-row">
                {#if adjusted_range_extent != null}
                    <div id="range-extent-text">
                        <span> Range Extent: </span>
                        <span class="thin">
                            {toLocaleRounded(adjusted_range_extent, 2)}
                            km<sup>2</sup>
                        </span>
                    </div>
                    {#if isMapPage}
                        <CheckboxInput
                            customClass="space-between"
                            name="extent-checkbox"
                            value="range-extent-layer-group"
                            handler={layerToggleHandler}
                            checked={layerGroups[
                                'range-extent-layer-group'
                            ].every((id) =>
                                mapContext.activeLayers.includes(id)
                            )}
                            checkboxIcon={eyeIcon}
                        />
                    {/if}
                {/if}
            </div>
            <div id="aoo-section" class="ns-metric-row">
                {#if nSValues.areaOfOccupancy4Km2Bins != null}
                    <div id="aoo-text">
                        <span>
                            <span>Area of Occupancy:</span>
                            <span class="thin">
                                {aOOValue}
                            </span>
                        </span>
                        <span id="aoo-grid-select-wrapper">
                            <select
                                id="aoo-grid-select"
                                onchange={aOOGridHandler}
                            >
                                <option
                                    value="1km2"
                                    selected={aOOGridSize == '1km2'}
                                >
                                    1km2
                                </option>
                                <option
                                    value="4km2"
                                    selected={aOOGridSize == '4km2'}
                                >
                                    4km2
                                </option>
                            </select>
                            Grid Cells
                        </span>
                    </div>
                {/if}
            </div>
            <div class="inat-toggle-section ns-metric-row">
                <span>Include iNat Data</span>
                <div class="inat-toggle icon">
                    <Toggle
                        handler={handleINatToggle}
                        checked={filtersContext.includeINat !== false}
                        onColor="darkgreen"
                        offColor="darkred"
                    />
                </div>
            </div>
        </div>
    </div>
</SidebarFoldout>

<style>
    #aoo-text {
        display: flex;
        justify-content: space-between;
        width: 100%;
        line-break: unset;
        flex-wrap: wrap;
        column-gap: 0.5rem;
    }
    #aoo-grid-select-wrapper {
        white-space: nowrap;
    }
    #aoo-grid-select {
        color: var(--text-default);
    }
    :global(.ns-section-wrapper > .sidebar-foldout-content) {
        padding: 0;
    }
    #filter-warning {
        background-color: goldenrod;
        color: black;
        height: 1rem;
        font-size: 0.75rem;
    }
    .inat-toggle-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
        white-space: nowrap;
    }
    .ns-section {
        position: relative;
        text-align: left;
        display: flex;
        flex-direction: column;
        padding: 0.75rem;
    }
    .ns-metric-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    :global(.ns-metric-row .input-item-wrapper) {
        display: flex;
        justify-content: center;
    }
    .inat-toggle {
        flex-grow: 0;
        flex-shrink: 0;
        display: block;
        stroke: var(--text-default);
    }
    #rank-text {
        margin-bottom: 0.5rem;
        display: flex;
        gap: 0.25rem;
        justify-content: center;
    }
    .rank-scale {
        margin-bottom: 0.5rem;
    }
</style>
