<script lang="ts">
    import {
        initialMapState,
        setMapContext,
        type MapStateType,
    } from '../contexts/mapContext';
    import HeaderBar from '../components/HeaderBar.svelte';
    import {
        EMPTY_TAXON_INFO,
        getActiveTaxonContext,
        initialTaxonState,
        setActiveTaxonContext,
        type ActiveTaxonStateType,
    } from '../contexts/activeTaxonContext';
    import Router from './Router.svelte';
    import {
        getRouterContext,
        initialRouterState,
        setRouterContext,
        type RouterStateType,
    } from '../contexts/routerContext';
    import { getCommonNames, getNSValues, getTaxonInfo } from '../lib/taxa';
    import {
        initialModalState,
        setModalContext,
        type ModalStateType,
    } from '../contexts/modalContext';
    import Modal from './Modal.svelte';
    import { getObservationDates, getProviderCounts } from '../lib/occurrence';
    import {
        getFiltersContext,
        initialFiltersState,
        setFiltersContext,
        type FiltersStateType,
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
        type SidebarStateType,
    } from '../contexts/sidebarContext';
    import { onMount } from 'svelte';
    import { calculateNSRank } from '../lib/natureServe';

    // Intialize contexts
    const taxonState: ActiveTaxonStateType = $state(initialTaxonState);
    setActiveTaxonContext(taxonState);
    const taxonContext = getActiveTaxonContext();

    const filtersState: FiltersStateType = $state(initialFiltersState);
    setFiltersContext(filtersState);
    const filtersContext = getFiltersContext();

    const mapState: MapStateType = $state(initialMapState);
    setMapContext(mapState);

    const routerState: RouterStateType = $state(initialRouterState);
    setRouterContext(routerState);
    const routerContext = getRouterContext();

    const modalState: ModalStateType = $state(initialModalState);
    setModalContext(modalState);

    const sidebarState: SidebarStateType = $state(initialSidebarState);
    setSidebarContext(sidebarState);

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

    // Get NatureServe values on new taxon or filters change
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
                    const rawNSResult = await getNSValues(
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

    // Update nSRankLocal on nSValue changes
    $effect(() => {
        if (
            taxonContext.taxonInfo.taxonRank &&
            ['species', 'subspecies'].includes(taxonContext.taxonInfo.taxonRank)
        ) {
            const {
                areaOfOccupancy4Km2Bins,
                numberOfOccurrences,
                rangeExtentKm2,
            } = taxonContext.nSValues;
            if (
                areaOfOccupancy4Km2Bins !== null &&
                numberOfOccurrences !== null &&
                rangeExtentKm2 !== null
            ) {
                const localRank = calculateNSRank(
                    numberOfOccurrences,
                    rangeExtentKm2,
                    areaOfOccupancy4Km2Bins
                );
                taxonContext.taxonInfo.nSRankLocal = localRank;
            } else {
                taxonContext.taxonInfo.nSRankLocal = null;
            }
        } else {
            taxonContext.taxonInfo.nSRankLocal = null;
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
        min-width: 1000px;
        display: flex;
        flex-direction: column;
        position: relative;
    }
    #page-body {
        height: 100%;
        overflow: auto;
    }
</style>
