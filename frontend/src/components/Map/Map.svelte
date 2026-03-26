<!--
    @component
    - The main map component for the site (using mapbox)
    - This component is a bear, but there is a lot of internally-important map logic
-->
<script module lang="ts">
    const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
</script>

<script lang="ts">
    import * as mapboxgl from 'mapbox-gl';
    import {
        getMapContext,
        type HoveredFeatureInfo,
    } from '../../contexts/mapContext';
    import {
        createObservationsBundle,
        createRangeExtentBundle,
        staticMapLayerIDs,
        staticMapLayers,
        type LayerBundle,
        type StaticLayerGroupID,
    } from '../../lib/map/mapLayers';
    import { getMapHoverContext } from '../../contexts/mapHoverContext';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import {
        getFiltersContext,
        type FiltersState,
    } from '../../contexts/filtersContext';
    import { buildTooltipSections } from '../../lib/map/mapTooltips';
    import {
        clearTargetFeatures,
        handleLegendHover,
    } from '../../lib/map/mapFeatures';
    import { onMount, untrack } from 'svelte';
    import { isMobile } from '../../contexts/device';

    // ---------------------------------------------
    // Contexts & reactive state
    // ---------------------------------------------

    let map: mapboxgl.Map;

    // Get contexts
    const mapContext = getMapContext();
    const taxaContext = getActiveTaxaContext();
    const mapHoverContext = getMapHoverContext();
    const filtersContext = getFiltersContext();

    // Keep track of whether or not map has been loaded
    let mapReady = $state(false);
    // Keep track of whether or not observations are being loaded
    let observationsLoading = $state(false);

    let hoveredFeatures: mapboxgl.FeatureSelector[] = [];
    let selectedFeatures: mapboxgl.GeoJSONFeature[] = [];

    // Logical center of the map (Texas)
    let center: mapboxgl.LngLatLike = $state([-100.0, 31.3]);

    // ---------------------------------------------
    // Layer visibility & management
    // ---------------------------------------------

    // Check layerGroups for
    mapContext.isLayerGroupActive = function (groupID: string) {
        const layerIDs = mapContext.layerGroups[groupID as StaticLayerGroupID];
        if (layerIDs) {
            return layerIDs.every((id) => mapContext.activeLayers.includes(id));
        }
        // For dynamic layer groups, check the single ID directly
        return mapContext.activeLayers.includes(groupID);
    };

    // Create layer hide/show functionality
    mapContext.setLayerVisibility = function (
        layerOrGroupID: string,
        visible: boolean,
        opacityOnly: boolean = false // if True, will preserve layer and set opacity to 0
    ) {
        // If a group is added, always parse it into
        const layerIDs = mapContext.layerGroups[
            layerOrGroupID as StaticLayerGroupID
        ] ?? [layerOrGroupID];
        for (const id of layerIDs) {
            const layer = map.getLayer(id);
            if (!layer) continue;
            // If opacityOnly is True, change only the opacity of the layer,
            // leaving it on the map to avoid refetching data
            if (opacityOnly) {
                switch (layer.type) {
                    case 'fill':
                        map.setLayoutProperty(
                            id,
                            'visibility',
                            visible ? 'visible' : 'none'
                        );
                        break;
                    case 'line':
                        map.setPaintProperty(
                            id,
                            'line-opacity',
                            visible ? 1 : 0
                        );
                        break;
                    case 'circle':
                        map.setPaintProperty(
                            id,
                            'circle-opacity',
                            visible ? 1 : 0
                        );
                        break;
                    default:
                        map.setLayoutProperty(
                            id,
                            'visibility',
                            visible ? 'visible' : 'none'
                        );
                        break;
                }
            } else {
                map.setLayoutProperty(
                    id,
                    'visibility',
                    visible ? 'visible' : 'none'
                );
            }
        }
    };

    // ---------------------------------------------
    // Tooltip management
    // ---------------------------------------------

    // Add mouse handlers, tooltips, etc...
    let tooltip = new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: false,
    });

    function clearTooltip() {
        clearTargetFeatures(map, selectedFeatures, 'selected');
        tooltip.remove();
        tooltip = new mapboxgl.Popup({
            closeButton: true,
            closeOnClick: false,
        });
    }

    // ---------------------------------------------
    // Map initialization & onLoad
    // ---------------------------------------------

    // Helper to get list of all active layer ids
    function getAllActiveLayerIDs() {
        return [
            ...staticMapLayerIDs,
            ...Object.values(mapContext.taxonLayers).flatMap((t) => t.layerIDs),
        ];
    }

    $effect(() => {
        map = new mapboxgl.Map({
            accessToken: MAPBOX_TOKEN,
            container: 'map',
            style: 'mapbox://styles/mapbox/outdoors-v11',
            // Offset for the map's starting center
            center: [center[0] + 3, center[1]],
            zoom: 4.7,
            cooperativeGestures: $isMobile ? true : false,
        });

        map.on('load', () => {
            mapReady = true;
            map.dragRotate.disable();
            // Iterate through staticMapLayers and add them to the map
            for (const layerBundle of staticMapLayers as LayerBundle[]) {
                map.addSource(layerBundle.id, layerBundle.source);
                layerBundle.layers.forEach((layer) => {
                    map.addLayer(layer);
                });
            }

            // Set visibility of static layers
            for (const layerID of staticMapLayerIDs) {
                const isVisible = mapContext.activeLayers.includes(layerID);
                mapContext.setLayerVisibility(layerID, isVisible, false);
            }

            // Add dynamic layers (if IDs already in context)
            // This reloads ALL taxonLayers, which isn't the most
            // efficient thing in the world. But is it an issue in earnest?
            for (const taxonID of taxaContext.taxonIDs) {
                if (taxonID in mapContext.taxonLayers) {
                    mapContext.taxonLayers[taxonID].loaded = false;
                }
                setupTaxonLayers(taxonID);
            }

            // ---------------------------------------------
            // Mouse movement and hover handling
            // ---------------------------------------------

            // Logic for handling hover states
            map.on('mousemove', (e) => {
                // Get coords for latlng display
                const coordinates = map!.unproject(e.point);

                mapHoverContext.lnglat = [
                    coordinates.lng.toFixed(2),
                    coordinates.lat.toFixed(2),
                ];

                clearTargetFeatures(map, hoveredFeatures, 'hover');

                // Get features from featureLayers that currently exist
                let features = map!.queryRenderedFeatures(e.point, {
                    layers: getAllActiveLayerIDs().filter((id) =>
                        map.getLayer(id)
                    ),
                });

                // If we're hovering on an observation point, ONLY focus on the point
                const observationPoints = features.filter(
                    (feature) => feature.sourceLayer === 'observations-circles'
                );

                if (observationPoints.length) {
                    features = observationPoints;
                }

                const hoveredFeatureInfo: HoveredFeatureInfo[] = [];

                // If layer features are found at cursor
                if (features.length) {
                    // Set cursor to pointer
                    map.getCanvas().style.cursor = 'pointer';

                    // Set new hovered features for map hover effects
                    for (const feature of features) {
                        if (!feature.source || !feature.id) continue;

                        const hoveredFeature = {
                            source: feature.source,
                            sourceLayer: feature.sourceLayer!,
                            id: feature.id,
                        };

                        // This is a hard-coded way to disable L3-ecoregion
                        // hovering map-side, while allowing it via the legend
                        if (feature.source !== 'l3-ecoregions') {
                            map.setFeatureState(hoveredFeature, {
                                hover: true,
                            });
                        }
                        // Keep track of hovered features in order to clear them
                        hoveredFeatures.push(hoveredFeature);
                        hoveredFeatureInfo.push({
                            source: feature.source,
                            sourceLayer: feature.sourceLayer ?? '',
                            id: feature.id,
                            properties: feature.properties ?? {},
                        });
                    }
                    // Else if no features found at cursor
                } else {
                    // Set cursor back to grab
                    map.getCanvas().style.cursor = 'grab';
                }

                mapContext.hoveredFeatures = hoveredFeatureInfo.length
                    ? hoveredFeatureInfo
                    : null;
            });

            // ---------------------------------------------
            // Mouse click and tooltip handling
            // ---------------------------------------------

            // Logic for handling select states and tooltips
            map.on('click', (e) => {
                const coordinates = map!.unproject(e.point);

                clearTooltip();

                let features = map!.queryRenderedFeatures(e.point, {
                    layers: getAllActiveLayerIDs().filter((id) =>
                        map.getLayer(id)
                    ),
                });

                clearTargetFeatures(map, selectedFeatures, 'selected');

                // If we're selecting an observation point, ONLY focus on the point
                const observationPoints = features.filter(
                    (feature) => feature?.layer?.id === 'observations-circles'
                );

                if (observationPoints.length) {
                    features = observationPoints;
                }

                // Iterate through selected features to set mouseover display data
                for (const feature of features) {
                    const layerId = feature.layer?.id as string | undefined;
                    if (!layerId || !feature.source || !feature.id) continue;

                    // Set new selected features for map hover effects
                    const selectedFeature = {
                        source: feature.source,
                        sourceLayer: feature.sourceLayer,
                        id: feature.id,
                        properties: feature.properties,
                    } as mapboxgl.GeoJSONFeature;

                    map.setFeatureState(selectedFeature, { selected: true });
                    selectedFeatures.push(selectedFeature);
                }

                const tooltipHTML = buildTooltipSections(selectedFeatures);

                // Set tooltip content and position
                if (tooltipHTML) {
                    tooltip
                        .setLngLat(coordinates)
                        .setHTML(
                            `<div class='tooltip-content'>
                                ${tooltipHTML}
                            </div>
                            `
                        )
                        .addTo(map!);
                }
            });

            // Monitor taxon layer events to trigger loading behavior
            map.on('sourcedata', (e) => {
                if (e.sourceId?.startsWith('observations-tiles-')) {
                    mapContext.loading = !e.isSourceLoaded;
                }
            });

            // Cleanup function on destroy
            return () => {
                // window.removeEventListener('resize', updateMapOffset);
                map?.remove();
                mapReady = false;
            };
        });
    });

    // ---------------------------------------------
    // Reactive layer updates (filters, taxon changes)
    // ---------------------------------------------

    // Get range extent geometry per-taxon
    // This needs to be done when observations change (from filtering)
    async function fetchRangeExtentGeom(taxonID: number) {
        const includeINat = filtersContext.includeINat;
        const dataProviders = filtersContext.dataProviders?.length
            ? filtersContext.dataProviders
            : null;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;

        const response = await fetch(
            '/server/natureserve/get_range_extent_geom',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    taxon_ids: taxonID,
                    include_inat: includeINat,
                    date_start: dateStart,
                    date_end: dateEnd,
                    data_providers: dataProviders,
                }),
            }
        );

        if (!response.ok) {
            const errData = await response.json();
            console.error('Error:', response.status, errData.detail);
            return;
        }

        const json = await response.json();
        const result = json.result;
        mapContext.taxonLayers[taxonID].rangeExtentGeom =
            result.range_extent_geom;

        const source = map.getSource(`range-extent-${taxonID}`);
        if (source && 'setData' in source) {
            (source as mapboxgl.GeoJSONSource).setData(
                result.range_extent_geom ?? {
                    type: 'FeatureCollection',
                    features: [],
                }
            );
        }
    }

    // Set up each taxon layer bundle
    async function setupTaxonLayers(taxonID: number) {
        const color = taxaContext.taxa[taxonID].color;
        const includeINat = filtersContext.includeINat;
        const dataProviders = filtersContext.dataProviders?.length
            ? filtersContext.dataProviders
            : null;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;

        if (!mapContext.taxonLayers[taxonID]) {
            mapContext.taxonLayers[taxonID] = {
                color: taxaContext.taxa[taxonID].color,
                loaded: false,
                layerIDs: [],
                rangeExtentGeom: null,
                areaOfOccupancyGeom: null,
            };
        }

        const obsBundle = createObservationsBundle(taxonID, color);
        const rangeBundle = createRangeExtentBundle(taxonID, color);

        // Add observation source with tile URL
        map.addSource(obsBundle.id, {
            ...obsBundle.source,
            tiles: [
                `${window.location.origin}/server/occurrence/tiles/${includeINat}/${taxonID}/${dataProviders}/${dateStart}/${dateEnd}/{z}/{x}/{y}.mvt`,
            ],
        });
        obsBundle.layers.forEach((layer) => map.addLayer(layer));

        // Add range extent source
        map.addSource(rangeBundle.id, rangeBundle.source);
        rangeBundle.layers.forEach((layer) => map.addLayer(layer));

        // Populate layerIDs on taxonLayers
        mapContext.taxonLayers[taxonID].layerIDs = [
            ...obsBundle.layers.map((l) => l.id),
            ...rangeBundle.layers.map((l) => l.id),
        ];

        // Register dynamic layer groups
        mapContext.layerGroups[`observations-layer-group-${taxonID}`] =
            obsBundle.layers.map((l) => l.id);
        mapContext.layerGroups[`range-extent-layer-group-${taxonID}`] =
            rangeBundle.layers.map((l) => l.id);

        // Add to activeLayers
        mapContext.activeLayers = [
            ...mapContext.activeLayers,
            ...mapContext.taxonLayers[taxonID].layerIDs,
        ];

        // Fetch range extent geom
        await fetchRangeExtentGeom(taxonID);

        mapContext.taxonLayers[taxonID].loaded = true;
    }

    // Update select map layers which depend on activeSpecies changes
    $effect(() => {
        const includeINat = filtersContext.includeINat;
        const dataProviders = filtersContext?.dataProviders?.length
            ? filtersContext.dataProviders
            : null;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;
        if (!map || !mapReady) return;

        let cancelled = false;

        untrack(() => {
            for (const taxonID of Object.keys(mapContext.taxonLayers).map(
                Number
            )) {
                // Make sure taxon exists and is loaded
                if (!mapContext.taxonLayers[taxonID].loaded) continue;
                const taxon = taxaContext.taxa[taxonID];
                if (!taxon) continue; // taxon was removed

                const sourceID = `observations-tiles-${taxonID}`;
                const source = map.getSource(
                    sourceID
                ) as mapboxgl.VectorTileSource;
                if (source) {
                    source.setTiles([
                        `${window.location.origin}/server/occurrence/tiles/${includeINat}/${taxonID}/${dataProviders}/${dateStart}/${dateEnd}/{z}/{x}/{y}.mvt`,
                    ]);
                }
                fetchRangeExtentGeom(taxonID);
            }
        });

        return () => {
            cancelled = true;
        };
    });

    // Add and remove taxaLayers when they are toggled in context
    $effect(() => {
        const currentIDs = new Set(taxaContext.taxonIDs);
        if (!mapReady) return;

        untrack(() => {
            // Add new layers
            for (const taxonID of currentIDs) {
                if (!(taxonID in mapContext.taxonLayers)) {
                    mapContext.taxonLayers[taxonID] = {
                        color: taxaContext.taxa[taxonID].color,
                        loaded: false,
                        layerIDs: [],
                        rangeExtentGeom: null,
                        areaOfOccupancyGeom: null,
                    };
                    setupTaxonLayers(taxonID);
                }
            }
            // Remove old layers
            for (const taxonID of Object.keys(mapContext.taxonLayers).map(
                Number
            )) {
                if (!currentIDs.has(taxonID)) {
                    const layerIDs = mapContext.taxonLayers[taxonID].layerIDs;
                    layerIDs.forEach((id) => {
                        if (map.getLayer(id)) map.removeLayer(id);
                    });
                    if (map.getSource(`observations-tiles-${taxonID}`))
                        map.removeSource(`observations-tiles-${taxonID}`);
                    if (map.getSource(`range-extent-${taxonID}`))
                        map.removeSource(`range-extent-${taxonID}`);
                    delete mapContext.layerGroups[
                        `observations-layer-group-${taxonID}`
                    ];
                    delete mapContext.layerGroups[
                        `range-extent-layer-group-${taxonID}`
                    ];
                    delete mapContext.taxonLayers[taxonID];
                    mapContext.activeLayers = mapContext.activeLayers.filter(
                        (id) => !layerIDs.includes(id)
                    );
                }
            }
        });
    });

    // React to hovered feature state changes from outside map component
    $effect(() => {
        const hoveredLegendInfo = mapContext.hoveredLegendInfo;
        if (!hoveredLegendInfo) return;

        clearTargetFeatures(map, hoveredFeatures, 'hover');

        handleLegendHover(map, hoveredFeatures, hoveredLegendInfo);
    });
</script>

<svelte:head>
    <link
        href="https://api.mapbox.com/mapbox-gl-js/v2.9.2/mapbox-gl.css"
        rel="stylesheet"
    />
</svelte:head>

<div id="map_box">
    <div id="map" class={[{ observationsLoading }]}></div>
</div>

<style>
    #map {
        height: 100%;
        width: 100%;
        position: absolute;
        box-sizing: border-box;
    }
    #map_box {
        height: 100%;
        width: 100%;
        position: absolute;
        top: 0;
        box-sizing: border-box;
    }

    /*  */
    /* Mapbox restyle */
    /*  */
    :global(.tooltip-section ul) {
        margin: 0 0 0 1rem;
        padding: 0;
        list-style: none;
    }
    :global(.tooltip-section a) {
        color: var(--fill-color);
    }
    :global(.mapboxgl-popup-content) > div {
        transform: translateZ(0);
    }
    :global(.tooltip-section-header) {
        font-weight: bold;
    }
    :global(.mapboxgl-popup-content) {
        background-color: rgba(55, 55, 55, 0.9) !important;
        color: var(--text-default) !important;
        border: var(--border) !important;
        text-align: left;
        width: fit-content;
        padding: 1rem !important;
        /* margin: 0.75rem 0.75rem !important; */
    }
    :global(.mapboxgl-popup-content > .mapboxgl-popup-close-button) {
        color: var(--text-default) !important;
        font-size: 1rem;
        position: absolute !important;
        padding: 5px 10px !important;
    }
    :global(.mapboxgl-popup-close-button:hover span) {
        opacity: 0.9;
        background-color: transparent !important;
    }
    :global(.tooltip-content) {
        max-height: 200px;
        overflow-y: auto;
        overflow-x: hidden;
    }
    :global(.tooltip-content .tooltip-section:not(:last-child)) {
        margin-bottom: 0.5rem;
    }
    :global(.mapboxgl-popup-anchor-top .mapboxgl-popup-tip) {
        border-bottom-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-top-left .mapboxgl-popup-tip) {
        border-bottom-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-top-right .mapboxgl-popup-tip) {
        border-bottom-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-bottom-left .mapboxgl-popup-tip) {
        border-top-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-bottom-right .mapboxgl-popup-tip) {
        border-top-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-bottom .mapboxgl-popup-tip) {
        border-top-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-right .mapboxgl-popup-tip) {
        border-left-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup-anchor-left .mapboxgl-popup-tip) {
        border-right-color: var(--container-back) !important;
        opacity: 0.9 !important;
    }
    :global(.mapboxgl-popup) {
        max-width: 400px !important;
    }
    :global(.mapboxgl-popup-content) {
        position: relative !important;
        background: transparent !important;
    }
    :global(.mapboxgl-popup-content::before) {
        content: '' !important;
        position: absolute !important;
        inset: 0 !important;
        background: var(--container-back) !important;
        opacity: 0.9 !important;
        pointer-events: none !important;
        z-index: 0 !important;
    }
    :global(.mapboxgl-popup-content > *) {
        position: relative !important;
        z-index: 1 !important; /* ensure content sits above overlay */
    }
</style>
