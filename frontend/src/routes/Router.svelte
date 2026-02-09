<script lang="ts">
    import { onMount, type Component } from 'svelte';
    import MapPage from './map/MapPage.svelte';
    import { getRouterContext } from '../contexts/routerContext';
    import TaxonPage from './taxon/TaxonPage.svelte';
    import RankingPage from './rankings/RankingsPage.svelte';
    import { routerSyncedKeys } from '../constants/router';

    let routerContext = getRouterContext();

    let PageComponent = $state<null | Component>(null);

    type RouteDefinition = {
        pathname: string;
        component: Component; // Corresponding page component
        relevantParams: string[];
    };

    // Possible routes and their relevant parameters (and default values)
    // TODO: Figure out type protection on relevantParams—refer to constants/router.ts for now
    export const routeDefinitions: RouteDefinition[] = [
        {
            pathname: '/map',
            component: MapPage,
            relevantParams: ['taxon', 'inat', 'source', 'd1', 'd2'],
        },
        {
            pathname: '/taxa',
            component: TaxonPage,
            relevantParams: ['taxon', 'inat'],
        },
        {
            pathname: '/rankings',
            component: RankingPage,
            relevantParams: ['taxon', 'inat', 'filter_taxon', 'status'],
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
                // If param is irrelevant, set to null
                // TODO: Is there anything dangerous about this?
                // TODO: It implies all params CAN be null. Should this be true?
                if (!relevantParams.includes(param)) {
                    (context as any)[contextKey] = null;
                }
                const value = (context as any)[contextKey];
                const serialized = codec.toURL(value);
                if (!serialized) continue;
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
        const url = routerContext.url;
        const currentRoute = getCurrentRoute(url);

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
                    (context as any)[contextKey] = codec.fromURL(values);
                }
            }
        }

        // Set initial page component
        PageComponent = currentRoute.component;
    });

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
        font-size: 24px;
        color: var(--text-default);
    }
</style>
