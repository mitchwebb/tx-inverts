<script lang="ts">
    import EyeOff from '../../assets/EyeOff.svelte';
    import EyeOn from '../../assets/EyeOn.svelte';
    import NSScale from '../../common/NSScale.svelte';
    import { getMapContext } from '../../contexts/mapContext';
    import {
        type ActiveTaxon,
    } from '../../contexts/activeTaxaContext';
    import { nSRankKey } from '../../constants/natureServe';
    import { handleLayerToggle } from '../../util/handleMapLayerToggle';
    import NSCircle from '../../common/NSCircle.svelte';
    import { getRouterContext } from '../../contexts/routerContext';
    import { toLocaleRounded } from '../../util/textHelpers';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import CheckboxInput, {
        type CheckboxPayload,
    } from '../../common/CheckboxInput.svelte';
    import InfoButton from '../../common/InfoButton.svelte';
    import { countActiveFilters } from '../../lib/filters.svelte';
    import { calculateNSRank } from '../../lib/natureServe';
    import { getMetricsContext } from '../../contexts/metricsParamsContext';
    import Dropdown from '../../common/Dropdown.svelte';
    import Foldout from '../../common/Foldout.svelte';
    import { getSidebarContext } from '../../contexts/sidebarContext';

    type NSSectionProps = {
        activeTaxon: ActiveTaxon;
        defaultOpen?: boolean;
    };

    const { activeTaxon, defaultOpen = false }: NSSectionProps = $props();

    const mapContext = getMapContext();

    // Assertion is safe, since this section will only receive active taxa
    const nSValues = $derived(activeTaxon.nSValues);

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
            ? nSValues?.areaOfOccupancy4Km2Bins
            : nSValues?.areaOfOccupancy1Km2Bins
    );

    // Update nSRankLocal on nSValue changes
    const localRank = $derived(deriveLocalRank());

    // As long as we're not using it anywhere else, the local nSRank can live
    // in this component
    function deriveLocalRank() {
        if (
            activeTaxon &&
            activeTaxon.info.taxonRank &&
            ['species', 'subspecies'].includes(activeTaxon.info.taxonRank)
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
                ? activeTaxon.info.nSRankDB
                : activeTaxon.info.nSRankDBNoINat)
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

    function aOOGridHandler(value: string) {
        const gridSize = value as typeof metricsContext.aOOResolution;
        metricsContext.aOOResolution = gridSize;
    }

    function layerToggleHandler(payload: CheckboxPayload) {
        const layerID = payload.value;
        const layerVisible = payload.checked as boolean;
        handleLayerToggle(mapContext, { layerID, layerVisible });
    }

    const sidebarContext = getSidebarContext();

    function handleSidebarFoldout(id: string | undefined, open: boolean) {
        if (!id) return;
        sidebarContext.foldoutStates[id] = open;
    }
</script>

<Foldout
    id={`${activeTaxon.taxonID}-ns-section`}
    defaultOpen={sidebarContext.foldoutStates[
        `${activeTaxon.taxonID}-ns-section`
    ] || defaultOpen}
    label="Conservation Values"
    isLoading={activeTaxon.nSValuesLoading}
    customClass="ns-section-wrapper"
    openCallback={handleSidebarFoldout}
    bannerText={filtersActive ? 'Using Filtered Data' : undefined}
>
    {#snippet closedDisplay()}
        {#if rank && !activeTaxon.info.usInvasive}
            <div>
                <NSCircle
                    activeFilters={filtersActive}
                    active={true}
                    level="s"
                    rank={rank ? rank : 'u'}
                />
            </div>
        {/if}
    {/snippet}
    <div class="ns-section">
        {#if rank && !activeTaxon.info.usInvasive}
            <div id="rank-text" class="centered-text">
                <span>
                    {nSRankKey.find((item) => item.rank === rank)?.description}
                </span>
                <div class="info-button">
                    <InfoButton type="tooltip" hover={true}>
                        <div>
                            The rankings made on this site are programmatically
                            derived using public data. These are preliminary
                            rankings meant for exploration and do not represent
                            official rankings.
                        </div>
                    </InfoButton>
                </div>
            </div>
            <div class="rank-scale">
                <NSScale level="s" activeRank={rank} />
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
            {#if nSValues.numberOfOccurrences != null}
                <div id="occurrences-section" class="ns-metric-row">
                    <div id="occurrences-text">
                        <span>Occurrences:</span>
                        <span class="thin">
                            {nSValues.numberOfOccurrences.toLocaleString()}
                            <InfoButton hover={true} type="tooltip">
                                <div>
                                    For this tool, occurrences are populations
                                    separated by at least 1km.
                                </div>
                            </InfoButton>
                        </span>
                    </div>
                </div>
            {/if}
            <div id="observations-section" class="ns-metric-row">
                {#if nSValues.observationCount != null}
                    <div id="observations-text">
                        <span>Individual Observations:</span>
                        <span class="thin">
                            {nSValues.observationCount.toLocaleString()}
                        </span>
                    </div>
                    {#if isMapPage}
                        <div class="ns-checkbox">
                            <CheckboxInput
                                customClass="space-between"
                                name="observations-checkbox"
                                value={`observations-layer-group-${activeTaxon.taxonID}`}
                                handler={layerToggleHandler}
                                checked={mapContext.isLayerGroupActive(
                                    `observations-layer-group-${activeTaxon.taxonID}`
                                )}
                                checkboxIcon={eyeIcon}
                            />
                        </div>
                    {/if}
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
                        <div class="ns-checkbox">
                            <CheckboxInput
                                customClass="space-between"
                                name="extent-checkbox"
                                value={`range-extent-layer-group-${activeTaxon.taxonID}`}
                                handler={layerToggleHandler}
                                checked={mapContext.isLayerGroupActive(
                                    `range-extent-layer-group-${activeTaxon.taxonID}`
                                )}
                                checkboxIcon={eyeIcon}
                            />
                        </div>
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
                            <Dropdown
                                options={[
                                    { value: '1km2', label: '1km2' },
                                    { value: '4km2', label: '4km2' },
                                ]}
                                selected={aOOGridSize}
                                onChange={aOOGridHandler}
                            />
                            Grid
                        </span>
                    </div>
                {/if}
            </div>
        </div>
    </div>
</Foldout>

<style>
    #ns-metrics-section {
        display: flex;
        flex-direction: column;
        /* gap: 0.25rem; */
    }
    #aoo-text {
        display: flex;
        justify-content: space-between;
        width: 100%;
        line-break: unset;
        flex-wrap: wrap;
        column-gap: 0.5rem;
        align-items: center;
    }
    #aoo-grid-select-wrapper {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        white-space: nowrap;
    }
    :global(.ns-section-wrapper > .sidebar-foldout-content) {
        padding: 0;
    }
    .ns-section {
        position: relative;
        text-align: left;
        display: flex;
        flex-direction: column;
    }
    .ns-metric-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 1.5rem;
        width: 100%;
    }
    .ns-checkbox {
        display: flex;
        align-items: center;
    }
    :global(.ns-metric-row .input-item-wrapper) {
        display: flex;
        justify-content: center;
    }
    #rank-text {
        margin-bottom: 0.5rem;
        display: flex;
        gap: 0.25rem;
        justify-content: center;
        font-size: 1.2rem;
    }
    .rank-scale {
        display: flex;
        justify-content: center;
        margin-bottom: 0.5rem;
    }
</style>
