<script lang="ts">
    import {
        initialMapState,
        setMapContext,
        type MapState,
    } from '../contexts/mapContext';
    import HeaderBar from '../components/Header/HeaderBar.svelte';
    import {
        EMPTY_NS_VALUES,
        EMPTY_TAXON_INFO,
        getActiveTaxaContext,
        initialActiveTaxaState,
        setActiveTaxaContext,
        type ActiveTaxaState,
        type ActiveTaxon,
    } from '../contexts/activeTaxaContext';
    import Router from './Router.svelte';
    import {
        getRouterContext,
        initialRouterState,
        setRouterContext,
        type RouterState,
    } from '../contexts/routerContext';
    import {
        getCommonNames,
        getNSMetrics,
        getQualifiedTaxa,
        getTaxonInfo,
    } from '../lib/taxa';
    import {
        initialModalState,
        setModalContext,
        type ModalState,
    } from '../contexts/modalContext';
    import Modal from './Modal.svelte';
    import {
        getDatasetCounts,
        getDateCounts,
        getObservationDates,
    } from '../lib/occurrence';
    import {
        getFiltersContext,
        initialFiltersState,
        setFiltersContext,
        type FiltersState,
    } from '../contexts/filtersContext';
    import {
        normalizeAPIResponse,
        NS_VALUES_MAP,
        TAXON_INFO_MAP,
        type NSValues,
        type RegionInfo,
        type TaxonInfo,
    } from '../types/api';
    import {
        initialSidebarState,
        setSidebarContext,
        type SidebarState,
    } from '../contexts/sidebarContext';
    import { untrack } from 'svelte';
    import {
        initialMetricsState,
        setMetricsContext,
        type MetricsParams,
    } from '../contexts/metricsParamsContext';
    import {
        initialRankingsState,
        setRankingsContext,
        type RankingsState,
    } from '../contexts/rankingsContext';
    import { TAXON_COLORS } from '../constants/taxa';
    import { makeIDCollection } from '../util/collection.svelte';
    import { isNarrowView } from '../contexts/device';
    import MobileSidebar from '../components/Sidebar/MobileSidebar.svelte';
    import { getRankAffectingFilterValues } from '../constants/sidebarFilters';

    // Intialize contexts

    // Make taxa collection (easier way of managing our lists of objects reactively)
    const taxaCollection = makeIDCollection<ActiveTaxon, number>(
        (t) => t.taxonID,
        loadTaxonInfo
    );
    const taxaState: ActiveTaxaState = $state(initialActiveTaxaState);

    // Logic for setting next color of active taxon (if all colors are used, will use least used color)
    function getNextTaxonColor(): string {
        const colorCounts = Object.fromEntries(TAXON_COLORS.map((c) => [c, 0]));
        taxaState.taxa.items.forEach((t) => {
            if (t.color in colorCounts) colorCounts[t.color]++;
        });
        return TAXON_COLORS.reduce((least, c) =>
            colorCounts[c] < colorCounts[least] ? c : least
        );
    }

    taxaState.getNextColor = getNextTaxonColor;
    taxaState.taxa = taxaCollection;
    setActiveTaxaContext(taxaState);
    const taxaContext = getActiveTaxaContext();

    const filtersState: FiltersState = $state(initialFiltersState);
    filtersState.regions = makeIDCollection<RegionInfo, string>((c) => c.id);
    setFiltersContext(filtersState);
    const filtersContext = getFiltersContext();

    const mapState: MapState = $state(initialMapState);
    setMapContext(mapState);

    const routerState: RouterState = $state(initialRouterState);
    setRouterContext(routerState);

    const modalState: ModalState = $state(initialModalState);
    setModalContext(modalState);

    const sidebarState: SidebarState = $state(initialSidebarState);
    setSidebarContext(sidebarState);

    const metricsParamsState: MetricsParams = $state(initialMetricsState);
    setMetricsContext(metricsParamsState);

    const rankingsState: RankingsState = $state(initialRankingsState);
    setRankingsContext(rankingsState);

    // Get list of qualified taxonIDs given various filters (for rankings page)
    $effect(() => {
        // Call filters to trigger reactivity
        const regionsIDs = filtersContext.regions.ids;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;
        const datasets = filtersContext.datasets;
        const taxonRank = filtersContext.taxonRank;
        const coordUncertainty = filtersContext.coordUncertainty;
        const includeINat = filtersContext.includeINat;

        untrack(async () => {
            rankingsState.ranksLoading = true;
            const qualifiedTaxa = await getQualifiedTaxa({
                regions: filtersContext.regions,
                dateStart,
                dateEnd,
                datasets,
                taxonRank,
                coordUncertainty,
                includeINat,
            });
            rankingsState.qualifiedTaxonIDs = qualifiedTaxa;
            rankingsState.ranksLoading = false;
        });
    });

    // Retrieve and set taxon info in context
    async function loadTaxonInfo(taxonID: number) {
        const taxon = taxaContext.taxa.get(taxonID);
        if (!taxon || taxon.taxonID === taxon.lastLoadedID) return;

        taxon.taxonLoading = true;
        taxon.taxonError = false;

        // Clear taxonInfo and nSValues in context
        taxon.info = EMPTY_TAXON_INFO;
        taxon.nSValues = EMPTY_NS_VALUES;
        taxon.color = taxaContext.getNextColor();

        try {
            const [rawTaxonInfo, commonNamesResult] = await Promise.all([
                getTaxonInfo(taxonID),
                getCommonNames(taxonID),
            ]);
            const taxonInfo = normalizeAPIResponse<TaxonInfo>(
                rawTaxonInfo,
                TAXON_INFO_MAP
            );
            taxonInfo.commonNames = commonNamesResult?.slice(0, 3) ?? null;
            taxon.info = taxonInfo;
            taxon.lastLoadedID = taxonID;
        } catch {
            taxon.taxonError = true;
        } finally {
            taxon.taxonLoading = false;
        }
    }

    // Get NSValues for all taxa on filters change
    $effect(() => {
        const trackedValues = getRankAffectingFilterValues(filtersContext);

        untrack(() => {
            for (const taxonID of taxaContext.taxa.ids) {
                const taxon = taxaContext.taxa.get(taxonID);
                if (!taxon) continue;
                loadNSValues(taxonID, { ...filtersContext, ...trackedValues });
            }
        });
    });

    // Get NSValues for currently empty taxa on taxonIDs change
    $effect(() => {
        const taxonIDs = taxaContext.taxa.ids;
        const filters = filtersContext;

        untrack(() => {
            for (const taxonID of taxonIDs) {
                const taxon = taxaContext.taxa.get(taxonID);

                // Check to make sure taxon exists and that it doesn't already have values
                // observationCount is the easiest to grab
                if (!taxon || taxon.nSValues.observationCount !== null)
                    continue;

                loadNSValues(taxonID, filters);
            }
        });
    });

    async function loadNSValues(
        taxonID: ActiveTaxaState['taxa']['items'][0]['taxonID'],
        filters: FiltersState
    ) {
        const taxon = taxaContext.taxa.get(taxonID);
        if (!taxon) return;
        taxon.nSValuesLoading = true;
        const abortController = new AbortController();
        try {
            const rawNSResult = await getNSMetrics(
                taxonID,
                filters,
                abortController.signal
            );
            taxon.nSValues = normalizeAPIResponse<NSValues>(
                rawNSResult,
                NS_VALUES_MAP
            );
        } catch (error) {
            console.error(error);
        } finally {
            taxon.nSValuesLoading = false;
        }
    }

    /**
     * Helper function for calling and parsing information
     * from metrics functions for all active taxa, as well
     *
     * @param taxonIDs
     * @param loadingKey
     * @param request
     * @param apply
     */
    function fetchActiveTaxaMetric<T>(
        taxonIDs: number[],
        loadingKey:
            | 'datasetCountsLoading'
            | 'dateRangeLoading'
            | 'dateCountsLoading',
        request: (taxonID: number) => Promise<T>,
        apply: (taxonID: number, result: T) => void
    ) {
        for (const taxonID of taxonIDs) {
            const taxon = taxaContext.taxa.get(taxonID);
            if (taxon) taxon[loadingKey] = true;
        }

        return Promise.all(
            taxonIDs.map(async (taxonID) => {
                try {
                    const result = await request(taxonID);
                    apply(taxonID, result);
                } finally {
                    const taxon = taxaContext.taxa.get(taxonID);
                    if (taxon) taxon[loadingKey] = false;
                }
            })
        );
    }

    // Make empty regions collection to prevent counting regions filtering
    // We're not using this filter our occurrences
    // Note: If we ever do want to filter OCCURRENCE data by region, this will need to be changed.
    const emptyRegions = makeIDCollection<RegionInfo, string>((c) => c.id);

    // Get aggregated datasetCounts for each taxon
    $effect(() => {
        const filters = getRankAffectingFilterValues(filtersContext, [
            'datasets',
        ]);

        const _ = taxaContext.taxa.ids;

        untrack(() =>
            fetchActiveTaxaMetric(
                taxaContext.taxa.ids,
                'datasetCountsLoading',
                (taxonID) =>
                    getDatasetCounts(taxonID, {
                        ...filters,
                        regions: emptyRegions,
                    }),
                (taxonID, counts) => {
                    const taxon = taxaContext.taxa.get(taxonID);
                    if (taxon) taxon.datasetCounts = counts;
                }
            )
        );
    });

    // Get min/max observationDates for each taxon
    $effect(() => {
        const filters = getRankAffectingFilterValues(filtersContext, [
            'dateStart',
            'dateEnd',
        ]);

        const _ = taxaContext.taxa.ids;

        untrack(() =>
            fetchActiveTaxaMetric(
                taxaContext.taxa.ids,
                'dateRangeLoading',
                (taxonID) =>
                    getObservationDates(taxonID, {
                        ...filters,
                        regions: emptyRegions,
                    }),
                (taxonID, range) => {
                    const taxon = taxaContext.taxa.get(taxonID);
                    if (!taxon || !range) return;

                    taxon.dateMin = new Date(range.minDate);
                    taxon.dateMax = new Date(range.maxDate);
                }
            )
        );
    });

    // Get aggregated monthly counts for each taxon
    $effect(() => {
        const filters = getRankAffectingFilterValues(filtersContext, [
            'dateStart',
            'dateEnd',
        ]);

        const _ = taxaContext.taxa.ids;

        untrack(() =>
            fetchActiveTaxaMetric(
                taxaContext.taxa.ids,
                'dateCountsLoading',
                (taxonID) =>
                    getDateCounts(taxonID, {
                        ...filters,
                        regions: emptyRegions,
                    }),
                (taxonID, counts) => {
                    const taxon = taxaContext.taxa.get(taxonID);
                    if (taxon) taxon.dateCounts = counts;
                }
            )
        );
    });
</script>

<div id="layout" class:mobile={$isNarrowView}>
    <Modal />
    <HeaderBar />
    <div id="page-body">
        <Router />
        <!-- TODO: This could be moved now that sidebar is unified -->
        {#if $isNarrowView && !['/about/txinverts', '/about/walkthrough'].includes(routerState.url.pathname)}
            <MobileSidebar />
            <div id="mobile-sidebar-buffer"></div>
        {/if}
    </div>
</div>

<style>
    #mobile-sidebar-buffer {
        height: 55px;
        width: 100%;
        flex-shrink: 0;
        padding: 0.5rem;
        box-sizing: border-box;
    }
    #layout.mobile {
        overflow: hidden;
        height: 100dvh;
    }
    #layout {
        height: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
        width: 100%;
        min-width: 320px;
        background-color: var(--container-shadow);
    }
    #page-body {
        height: 100%;
        overflow: auto;
        box-sizing: border-box;
        flex-grow: 0;
        flex-shrink: 1;
        min-height: 0;
        display: flex;
        flex-direction: column;
    }
</style>
