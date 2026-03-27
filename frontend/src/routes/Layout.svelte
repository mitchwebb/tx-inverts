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
        initialTaxonState,
        setActiveTaxaContext,
        type ActiveTaxaState,
    } from '../contexts/activeTaxaContext';
    import Router from './Router.svelte';
    import {
        getRouterContext,
        initialRouterState,
        setRouterContext,
        type RouterState,
    } from '../contexts/routerContext';
    import { getCommonNames, getNSMetrics, getTaxonInfo } from '../lib/taxa';
    import {
        initialModalState,
        setModalContext,
        type ModalState,
    } from '../contexts/modalContext';
    import Modal from './Modal.svelte';
    import { getObservationDates, getProviderCounts } from '../lib/occurrence';
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
        type TaxonInfo,
    } from '../types/api';
    import {
        initialSidebarState,
        setSidebarContext,
        type SidebarState,
    } from '../contexts/sidebarContext';
    import { onMount, untrack } from 'svelte';
    import {
        initialMetricsState,
        setMetricsContext,
        type MetricsParams,
    } from '../contexts/metricsParamsContext';
    import { type Provider } from '../constants/mapLegendKeys';
    import {
        initialRankingsState,
        setRankingsContext,
        type RankingsState,
    } from '../contexts/rankingsContext';
    import { TAXON_COLORS } from '../constants/taxa';

    // Intialize contexts
    const taxaState: ActiveTaxaState = $state(initialActiveTaxaState);
    setActiveTaxaContext(taxaState);

    // Logic for setting next color of active taxon (if all colors are used, will use least used color)
    function getNextTaxonColor(): string {
        const colorCounts = Object.fromEntries(TAXON_COLORS.map((c) => [c, 0]));
        Object.values(taxaState.taxa).forEach((t) => {
            if (t.color in colorCounts) colorCounts[t.color]++;
        });
        return TAXON_COLORS.reduce((least, c) =>
            colorCounts[c] < colorCounts[least] ? c : least
        );
    }

    function addActiveTaxon(taxonID: number, append = false) {
        if (taxaState.taxa[taxonID]) return;
        // If append is false, replace the latest taxon
        if (!append) {
            // Get latest taxonID in context
            const lastID = taxaState.taxonIDs.slice(-1)[0];
            if (lastID !== undefined) {
                delete taxaState.taxa[lastID];
                taxaState.taxonIDs.pop();
            }
        }
        taxaState.taxa[taxonID] = {
            ...initialTaxonState,
            taxonID,
            color: getNextTaxonColor(),
        };
        taxaState.taxonIDs = [...taxaState.taxonIDs, taxonID];
        loadTaxonInfo(taxonID);
    }
    function removeActiveTaxon(taxonID: number) {
        delete taxaState.taxa[taxonID];
        taxaState.taxonIDs = taxaState.taxonIDs.filter((id) => id !== taxonID);
    }
    function clearTaxa() {
        taxaContext.taxa = initialActiveTaxaState.taxa;
        taxaContext.taxonIDs = initialActiveTaxaState.taxonIDs;
    }
    taxaState.add = addActiveTaxon;
    taxaState.remove = removeActiveTaxon;
    taxaState.clear = clearTaxa;
    taxaState.getNextColor = getNextTaxonColor;
    const taxaContext = getActiveTaxaContext();

    const filtersState: FiltersState = $state(initialFiltersState);
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

    // Retrieve and set taxon info in context
    async function loadTaxonInfo(taxonID: number) {
        const taxon = taxaContext.taxa[taxonID];
        if (!taxon || taxon.taxonID === taxon.lastLoadedID) return;

        taxon.taxonLoading = true;
        taxon.taxonError = false;

        // Clear taxonInfo and nSValues in context
        taxon.info = EMPTY_TAXON_INFO;
        taxon.nSValues = EMPTY_NS_VALUES;

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
        const dataProviders = filtersContext.dataProviders;

        untrack(() => {
            for (const taxonID of taxaContext.taxonIDs) {
                const taxon = taxaContext.taxa[taxonID];
                if (!taxon) continue;
                loadNSValues(
                    taxonID,
                    includeINat,
                    dateStart,
                    dateEnd,
                    dataProviders
                );
            }
        });
    });

    // Get NSValues for currently empty taxa on taxonIDs change
    $effect(() => {
        const taxonIDs = taxaContext.taxonIDs;

        untrack(() => {
            for (const taxonID of taxonIDs) {
                const taxon = taxaContext.taxa[taxonID];
                // Check to make sure taxon exists and that it doesn't already have values
                if (!taxon || taxon.nSValues.numberOfOccurrences !== null)
                    continue;
                const includeINat = filtersContext.includeINat !== false;
                const dateStart = filtersContext.dateStart;
                const dateEnd = filtersContext.dateEnd;
                const dataProviders = filtersContext.dataProviders;
                loadNSValues(
                    taxonID,
                    includeINat,
                    dateStart,
                    dateEnd,
                    dataProviders
                );
            }
        });
    });

    async function loadNSValues(
        taxonID: number,
        includeINat: boolean,
        dateStart: Date | null,
        dateEnd: Date | null,
        dataProviders: Provider[]
    ) {
        const taxon = taxaContext.taxa[taxonID];
        if (!taxon) return;
        taxon.nSValuesLoading = true;
        const abortController = new AbortController();
        try {
            const rawNSResult = await getNSMetrics(
                taxonID,
                includeINat,
                dateStart,
                dateEnd,
                dataProviders,
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

        for (const taxonID of Object.keys(taxaContext.taxa).map(Number)) {
            const taxon = taxaContext.taxa[taxonID];
            taxon.observationMetricsLoading = true;

            (async () => {
                try {
                    // Run both async calls concurrently
                    const [providerCounts, dateRange] = await Promise.all([
                        getProviderCounts(
                            taxonID,
                            includeINat,
                            dateStart,
                            dateEnd
                        ),
                        getObservationDates(taxonID, includeINat),
                    ]);
                    // If publishers are already selected, but they do not have this taxon,
                    // make sure to include them in the provider counts with a value of 0
                    if (filtersContext.dataProviders && providerCounts) {
                        const existingProviders = new Set(
                            Object.keys(providerCounts)
                        );
                        for (const provider of filtersContext.dataProviders) {
                            if (!existingProviders.has(provider)) {
                                providerCounts[provider] = 0;
                            }
                        }
                    }
                    taxon.providerCounts = providerCounts;

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
</script>

<div id="layout">
    <Modal />
    <HeaderBar />
    <div id="page-body">
        <Router />
    </div>
</div>

<style>
    #layout {
        height: 100%;
        min-height: 500px;
        /* min-width: fit-content; */
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: auto;
        width: 100%;
        min-width: 800px;
    }
    #page-body {
        height: 100%;
        /* min-height: 500px; */
        overflow: auto;
    }
</style>
