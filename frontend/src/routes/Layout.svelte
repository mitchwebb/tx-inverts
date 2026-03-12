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
        getActiveTaxonContext,
        initialTaxonState,
        setActiveTaxonContext,
        type ActiveTaxonState,
    } from '../contexts/activeTaxonContext';
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
        type RawTaxonInfo,
        type TaxonInfo,
    } from '../types/api';
    import {
        initialSidebarState,
        setSidebarContext,
        type SidebarState,
    } from '../contexts/sidebarContext';
    import { onMount } from 'svelte';
    import {
        initialMetricsState,
        setMetricsContext,
        type MetricsParams,
    } from '../contexts/metricsParamsContext';
    import type { Provider, ProviderCode } from '../constants/mapLegendKeys';

    // Intialize contexts
    const taxonState: ActiveTaxonState = $state(initialTaxonState);
    setActiveTaxonContext(taxonState);
    const taxonContext = getActiveTaxonContext();

    const filtersState: FiltersState = $state(initialFiltersState);
    setFiltersContext(filtersState);
    const filtersContext = getFiltersContext();

    const mapState: MapState = $state(initialMapState);
    setMapContext(mapState);

    const routerState: RouterState = $state(initialRouterState);
    setRouterContext(routerState);
    const routerContext = getRouterContext();

    const modalState: ModalState = $state(initialModalState);
    setModalContext(modalState);

    const sidebarState: SidebarState = $state(initialSidebarState);
    setSidebarContext(sidebarState);

    const metricsParamsState: MetricsParams = $state(initialMetricsState);
    setMetricsContext(metricsParamsState);

    // Set initial URL in context for parsing into various contexts
    onMount(() => {
        const url = new URL(window.location.href);
        routerContext.url = url;
    });

    // Retrieve and set taxon info in context (on activeTaxonID changes)
    $effect(() => {
        const activeTaxonID = taxonContext.taxonID;
        if (activeTaxonID && activeTaxonID !== taxonContext.lastLoadedID) {
            taxonContext.taxonLoading = true;
            taxonContext.taxonError = false;

            // Clear taxonInfo and nSValues in context
            taxonContext.taxonInfo = EMPTY_TAXON_INFO;
            taxonContext.nSValues = EMPTY_NS_VALUES;

            // Wrap in async IIFE
            (async () => {
                try {
                    const taxonInfoPromise: Promise<RawTaxonInfo> =
                        getTaxonInfo(activeTaxonID);
                    const commonNamesPromise = getCommonNames(activeTaxonID);

                    const [rawTaxonInfo, commonNamesResult] = await Promise.all(
                        [taxonInfoPromise, commonNamesPromise]
                    );

                    const taxonInfo = normalizeAPIResponse<TaxonInfo>(
                        rawTaxonInfo,
                        TAXON_INFO_MAP
                    );

                    taxonInfo.commonNames = commonNamesResult
                        ? commonNamesResult.slice(0, 3)
                        : null;

                    taxonContext.taxonInfo = taxonInfo;

                    taxonContext.lastLoadedID = activeTaxonID;
                } catch (error) {
                    taxonContext.taxonError = true;
                } finally {
                    taxonContext.taxonLoading = false;
                }
            })();
        } else if (!activeTaxonID) {
            taxonContext.taxonInfo = EMPTY_TAXON_INFO;
        }
    });

    // Get NatureServe values from server on new taxon or filters change
    $effect(() => {
        const activeTaxonID = taxonContext.taxonID;
        const includeINat = filtersContext.includeINat !== false;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;
        const dataProviders = filtersContext.dataProviders;

        taxonContext.nSValuesLoading = true;

        if (activeTaxonID) {
            (async () => {
                try {
                    const rawNSResult = await getNSMetrics(
                        activeTaxonID,
                        includeINat,
                        dateStart,
                        dateEnd,
                        dataProviders
                    );
                    const nSValues = normalizeAPIResponse<NSValues>(
                        rawNSResult,
                        NS_VALUES_MAP
                    );
                    taxonContext.nSValues = nSValues;
                } catch (error) {
                    console.error(error);
                } finally {
                    taxonContext.nSValuesLoading = false;
                }
            })();
        }
    });

    // Get institution counts in context (on activeTaxonID and select filter changes)
    $effect(() => {
        const activeTaxonID = taxonContext.taxonID;
        const includeINat = filtersContext.includeINat !== false;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;

        if (activeTaxonID) {
            taxonContext.observationMetricsLoading = true;

            (async () => {
                try {
                    // Run both async calls concurrently
                    const [providerCounts, dateRange] = await Promise.all([
                        getProviderCounts(
                            activeTaxonID,
                            includeINat,
                            dateStart,
                            dateEnd
                        ),
                        getObservationDates(activeTaxonID, includeINat),
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
                    taxonContext.providerCounts = providerCounts;

                    if (dateRange) {
                        taxonContext.dateMin = dateRange?.minDate;
                        taxonContext.dateMax = dateRange?.maxDate;
                    }
                } catch (error) {
                    console.error(error);
                } finally {
                    taxonContext.observationMetricsLoading = false;
                }
            })();
        } else {
            taxonContext.dateMin = null;
            taxonContext.dateMax = null;
            taxonContext.providerCounts = null;
        }
    });

    // // On taxa filter change, set in state
    // $effect(() => {
    // 	const taxaFilter = routerContext.url.searchParams.get('taxa_filter')
    // 	if (!taxaFilter) return;
    // 	taxonContext.filteredTaxonID = parseInt(taxaFilter);
    // })
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
        min-width: min(1000px, 100%);
        display: flex;
        flex-direction: column;
        position: relative;
    }
    #page-body {
        height: 100%;
        overflow: auto;
    }
</style>
