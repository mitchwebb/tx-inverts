<script lang="ts">
    import { onMount, type Component } from 'svelte';
    import MapPage from './map/MapPage.svelte';
    import {
        getRouterContext,
        type RouterPath,
    } from '../contexts/routerContext';
    import RankingPage from './rankings/RankingsPage.svelte';
    import { routerSyncedKeys } from '../constants/router';
    import {
        getActiveTaxaContext,
        initialTaxonState,
    } from '../contexts/activeTaxaContext';
    import { getRegionInfo } from '../lib/regions';
    import { getFiltersContext } from '../contexts/filtersContext';
    import type { RawRegionInfo, RegionInfo } from '../types/api';
    import BackbonePage from './Backbone/BackbonePage.svelte';
    import AboutPage from './AboutPage.svelte';

    let routerContext = getRouterContext();
    let taxaContext = getActiveTaxaContext();
    let filtersContext = getFiltersContext();

    let PageComponent = $state<null | Component>(null);

    type RouteDefinition = {
        pathname: RouterPath;
        component: Component; // Corresponding page component
        relevantParams: string[];
    };

    // Possible routes and their relevant parameters (and default values)
    // This determines which params to show in the URL (or populate from the URL on page-load)
    export const routeDefinitions: RouteDefinition[] = [
        {
            pathname: '/map',
            component: MapPage,
            relevantParams: ['taxon', 'inat', 'source', 'd1', 'd2'],
        },
        {
            pathname: '/backbone',
            component: BackbonePage,
            relevantParams: ['taxon', 'inat'],
        },
        {
            pathname: '/rankings',
            component: RankingPage,
            relevantParams: ['taxon', 'inat', 'status', 'd1', 'd2', 'region'],
        },
        {
            pathname: '/about',
            component: AboutPage,
            relevantParams: [],
        },
    ];

    function getCurrentRoute(url: URL): RouteDefinition | null {
        for (const route of routeDefinitions) {
            if (route.pathname === url.pathname) return route;
        }
        return null;
    }

    function buildURLFromContext(baseURL: URL) {
        const currentRoute = getCurrentRoute(baseURL);
        if (!currentRoute) return baseURL;

        const { relevantParams } = currentRoute;
        const params = new URLSearchParams();

        for (const { getContext, keys } of Object.values(routerSyncedKeys)) {
            const context = getContext();
            for (const [contextKey, { param, codec }] of Object.entries(keys)) {
                // Get param value
                const value = (context as any)[contextKey];

                // If param is irrelevant, skip it
                if (!relevantParams.includes(param)) continue;

                // Convert to URL string
                const serialized = codec.toURL(value);
                if (!serialized) continue;
                // Add to collected URL params
                params.delete(param);
                for (const v of serialized) params.append(param, v);
            }
        }

        return new URL(
            baseURL.pathname +
                (params.toString() ? `?${params.toString()}` : ''),
            baseURL.origin
        );
    }

    // On mount, populate state from URL
    onMount(() => {
        const url = new URL(window.location.href);
        const currentRoute = getCurrentRoute(url);
        routerContext.url = url;

        // Default to /map if no route matches (including "/")
        if (!currentRoute) {
            const defaultURL = new URL('/map', url.origin);
            routerContext.navigate(defaultURL.toString(), true);
            return;
        }

        const { relevantParams } = currentRoute;

        for (const { getContext, keys } of Object.values(routerSyncedKeys)) {
            const context = getContext();
            for (const [contextKey, { param, codec }] of Object.entries(keys)) {
                // Skip params that are not relevant to requested path
                if (!relevantParams.includes(param)) continue;

                // Else populate relevant params to their corresponding contexts
                const values = url.searchParams.getAll(param);
                if (values.length > 0) {
                    const decoded = codec.fromURL(values);
                    if (decoded != null) {
                        (context as any)[contextKey] = decoded;
                    }
                }
            }
        }

        // Special case for adding taxa based on URL params
        const taxonParams = new Set(
            url.searchParams.getAll('taxon').map(Number).filter(Boolean)
        );
        taxonParams.forEach((id) =>
            taxaContext.taxa.add({
                ...initialTaxonState,
                taxonID: id,
            })
        );

        // Special case for adding regions based on URL params
        const regionParams = new Set(url.searchParams.getAll('region'));
        regionParams.forEach(async (id) => {
            const regionInfo: RegionInfo | null = await getRegionInfo(id);
            if (regionInfo) {
                filtersContext.region.add(regionInfo);
            }
        });

        // Set initial page component
        PageComponent = currentRoute.component;
    });

    // Set initial URL in context for parsing into various contexts
    onMount(() => {});

    // When any routerSyncedKey changes in their respective context, update URL
    // Also, when changing pages, set irrelevant params to null
    $effect(() => {
        const newURL = buildURLFromContext(routerContext.url);
        if (routerContext.url.toString() !== newURL.toString()) {
            routerContext.navigate(newURL.toString(), true);
        }
    });

    function navigate(pathAndSearch: string, replace = false) {
        const newURL = new URL(pathAndSearch, window.location.origin);
        const currentURLStr = routerContext.url.toString();

        if (currentURLStr === newURL.toString()) return;

        if (replace) window.history.replaceState(null, '', newURL.toString());
        else window.history.pushState(null, '', newURL.toString());

        routerContext.url = newURL;
    }

    // Add navigate definition to routerContext
    routerContext.navigate = navigate;

    // When URL changes, parse URL and set layout component
    $effect(() => {
        const route = getCurrentRoute(routerContext.url);
        PageComponent = route?.component ?? null;
    });
</script>

{#if PageComponent}
    <PageComponent />
{:else}
    <div id="page-not-found">Error: Page not found</div>
{/if}

<style>
    #page-not-found {
        text-align: center;
        margin-top: 50px;
        font-size: 2rem;
        color: var(--text-default);
    }
</style>
