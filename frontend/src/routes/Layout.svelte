<script lang="ts">
    import {
        initialMapState,
        setMapContext,
        type MapState,
    } from '../contexts/mapContext';
    import HeaderBar from '../components/HeaderBar.svelte';
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
    import { getObservationDates, getDatasetCounts } from '../lib/occurrence';
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
    filtersState.region = makeIDCollection<RegionInfo, string>((c) => c.id);
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
        const regionIDs = filtersContext.region.ids;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;
        const datasets = filtersContext.datasets;

        untrack(async () => {
            rankingsState.ranksLoading = true;
            const qualifiedTaxa = await getQualifiedTaxa(
                dateStart,
                dateEnd,
                datasets,
                regionIDs
            );
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
        const includeINat = filtersContext.includeINat !== false;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;
        const datasets = filtersContext.datasets;

        untrack(() => {
            for (const taxonID of taxaContext.taxa.ids) {
                const taxon = taxaContext.taxa.get(taxonID);
                if (!taxon) continue;
                loadNSValues(
                    taxonID,
                    includeINat,
                    dateStart,
                    dateEnd,
                    datasets
                );
            }
        });
    });

    // Get NSValues for currently empty taxa on taxonIDs change
    $effect(() => {
        const taxonIDs = taxaContext.taxa.ids;

        untrack(() => {
            for (const taxonID of taxonIDs) {
                const taxon = taxaContext.taxa.get(taxonID);
                // Check to make sure taxon exists and that it doesn't already have values
                if (!taxon || taxon.nSValues.numberOfOccurrences !== null)
                    continue;
                const includeINat = filtersContext.includeINat !== false;
                const dateStart = filtersContext.dateStart;
                const dateEnd = filtersContext.dateEnd;
                const datasets = filtersContext.datasets;
                loadNSValues(
                    taxonID,
                    includeINat,
                    dateStart,
                    dateEnd,
                    datasets
                );
            }
        });
    });

    async function loadNSValues(
        taxonID: number,
        includeINat: FiltersState['includeINat'],
        dateStart: FiltersState['dateStart'],
        dateEnd: FiltersState['dateEnd'],
        datasets: FiltersState['datasets']
    ) {
        const taxon = taxaContext.taxa.get(taxonID);
        if (!taxon) return;
        taxon.nSValuesLoading = true;
        const abortController = new AbortController();
        try {
            const rawNSResult = await getNSMetrics(
                taxonID,
                includeINat,
                dateStart,
                dateEnd,
                datasets,
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

    // Get institution counts in context (on activeTaxonID and select filter changes)
    $effect(() => {
        const includeINat = filtersContext.includeINat !== false;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;

        for (const taxonID of taxaContext.taxa.ids) {
            const taxon = taxaContext.taxa.get(taxonID);
            if (!taxon) return;

            taxon.observationMetricsLoading = true;

            (async () => {
                try {
                    // Run both async calls concurrently
                    const [datasetCounts, dateRange] = await Promise.all([
                        getDatasetCounts(
                            taxonID,
                            includeINat,
                            dateStart,
                            dateEnd
                        ),
                        getObservationDates(taxonID, includeINat),
                    ]);
                    // If publishers are already selected, but they do not have this taxon,
                    // make sure to include them in the dataset counts with a value of 0
                    if (filtersContext.datasets && datasetCounts) {
                        const existingDatasets = new Set(
                            Object.keys(datasetCounts)
                        );
                        for (const dataset of filtersContext.datasets) {
                            if (!existingDatasets.has(dataset)) {
                                datasetCounts[dataset] = 0;
                            }
                        }
                    }
                    taxon.datasetCounts = datasetCounts;

                    if (dateRange) {
                        taxon.dateMin = new Date(dateRange?.minDate);
                        taxon.dateMax = new Date(dateRange?.maxDate);
                    }
                } catch (error) {
                    console.error(error);
                } finally {
                    taxon.observationMetricsLoading = false;
                }
            })();
        }
    });

    // Derive filterTaxonIDs from taxaContext.taxa ABOVE species rank
    $effect(() => {
        filtersContext.filterTaxonIDs = taxaContext.taxa.ids.filter((id) => {
            const taxon = taxaContext.taxa.get(id);
            const taxonRank = taxon?.info.taxonRank;
            return taxonRank && !['species', 'subspecies'].includes(taxonRank);
        });
    });
</script>

<div id="layout" class:mobile={$isNarrowView}>
    <Modal />
    <HeaderBar />
    <div id="page-body">
        <Router />
        {#if $isNarrowView && routerState.url.pathname !== '/about'}
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
        /* overflow: auto; */
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
