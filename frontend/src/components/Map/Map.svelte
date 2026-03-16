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
        allMapLayerIDs,
        allMapLayers,
        layerGroups,
        observationsLayer,
        observationsLayerSource,
        type LayerBundle,
        type LayerGroupID,
        type MapLayerID,
        type MapLayerSource,
        type MapSourceLayer,
    } from '../../lib/map/mapLayers';
    import { getMapHoverContext } from '../../contexts/mapHoverContext';
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import { buildTooltipSections } from '../../lib/map/mapTooltips';
    import {
        clearTargetFeatures,
        handleLegendHover,
    } from '../../lib/map/mapFeatures';

    // ---------------------------------------------
    // Contexts & reactive state
    // ---------------------------------------------

    let map: mapboxgl.Map;

    // Get contexts
    const mapContext = getMapContext();
    const taxonContext = getActiveTaxonContext();
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

    mapContext.isLayerGroupActive = function (groupID: LayerGroupID) {
        const layerIDs = layerGroups[groupID];
        return layerIDs.every((id) => mapContext.activeLayers.includes(id));
    };

    // Create layer hide/show functionality
    mapContext.setLayerVisibility = function (
        layerOrGroupID: MapLayerID | LayerGroupID,
        visible: boolean,
        opacityOnly: boolean = false // if True, will preserve layer and set opacity to 0
    ) {
        // If a group is added, always parse it into
        const layerIDs = layerGroups[layerOrGroupID as LayerGroupID] || [
            layerOrGroupID,
        ];
        for (const id of layerIDs) {
            const layer = map.getLayer(id);
            if (!layer) continue;
            // If opacityOnly is True, change only the opacity of the layer,
            // leaving it on the map to avoid refetching data
            if (opacityOnly) {
                switch (layer.type) {
                    case 'fill':
                        map.setPaintProperty(
                            id,
                            'fill-opacity',
                            visible ? 0.6 : 0
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

    $effect(() => {
        map = new mapboxgl.Map({
            accessToken: MAPBOX_TOKEN,
            container: 'map',
            style: 'mapbox://styles/mapbox/outdoors-v11',
            // Offset for the map's starting center
            center: [center[0] + 3, center[1]],
            zoom: 4.7,
            cooperativeGestures: true,
        });

        map.on('load', () => {
            mapReady = true;
            map.dragRotate.disable();
            // Iterate through allMapLayers and add them to the map
            for (const layerBundle of allMapLayers as LayerBundle[]) {
                // Skip deferred layers
                if (layerBundle.deferred === true) {
                    continue;
                }
                map.addSource(layerBundle.id, layerBundle.source);
                layerBundle.layers.forEach((layer) => {
                    map.addLayer(layer);
                });
            }

            // After all layers are added:
            for (const layerID of allMapLayerIDs) {
                const isVisible = mapContext.activeLayers.includes(layerID);
                mapContext.setLayerVisibility(layerID, isVisible, false);
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
                    layers: allMapLayerIDs.filter((id) => map.getLayer(id)),
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

                        // TODO: This is very hard-coded and suspect, but I want to
                        // disable L3-ecoregion hovering map-side, while allowing it via the legend
                        if (feature.source !== 'l3-ecoregions') {
                            map.setFeatureState(hoveredFeature, {
                                hover: true,
                            });
                        }
                        // Keep track of hovered features in order to clear them
                        hoveredFeatures.push(hoveredFeature);
                        hoveredFeatureInfo.push({
                            source: feature.source as MapLayerSource,
                            sourceLayer: feature.sourceLayer as MapSourceLayer,
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
                    layers: allMapLayerIDs.filter((id) => map.getLayer(id)),
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
                    const layerId = feature.layer?.id as MapLayerID | undefined;
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

            // Monitor layer events to trigger loading behavior
            map.on('sourcedata', (e) => {
                if (e.sourceId === observationsLayerSource.id) {
                    if (!e.isSourceLoaded) {
                        mapContext.loading = true;
                    } else if (e.isSourceLoaded) {
                        mapContext.loading = false;
                    }
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

    const tileLayers = [...observationsLayer.layers];

    // Function for redrawing observations tiles layer
    function setupTileLayers() {
        if (!map) return;

        tileLayers.forEach((layer) => {
            if (!map.getLayer(layer.id)) {
                map.addLayer(layer);
            }
        });
    }

    // Update select map layers which depend on activeSpecies changes
    $effect(() => {
        // Kick off reactivity based on activeSpecies
        const taxonID = taxonContext.taxonID;
        const taxonRank = taxonContext?.taxonInfo.taxonRank;
        const includeINat = filtersContext.includeINat;
        const dataProviders = filtersContext?.dataProviders?.length
            ? filtersContext.dataProviders
            : null;
        const dateStart = filtersContext.dateStart;
        const dateEnd = filtersContext.dateEnd;

        const ready = mapReady;

        if (!map || !taxonID || !ready) return;

        let cancelled = false;

        async function updateLayers() {
            try {
                tileLayers.forEach((layer) => {
                    if (map.getLayer(layer.id)) map.removeLayer(layer.id);
                });

                if (map.getSource(observationsLayerSource.id)) {
                    map.removeSource(observationsLayerSource.id);
                }

                const origin = window.location.origin;

                // Add new tile source with updated species ID
                map.addSource(observationsLayerSource.id, {
                    ...observationsLayerSource.source,
                    tiles: [
                        `${origin}/server/occurrence/tiles/${includeINat}/${taxonID}/${taxonRank}/${dataProviders}/${dateStart}/${dateEnd}/{z}/{x}/{y}.mvt`,
                    ],
                } as mapboxgl.VectorSourceSpecification);

                // Add tile layers again
                setupTileLayers();

                async function getRangeExtentGeom() {
                    // Fetch range extent data
                    const rangeExtentURL =
                        '/server/natureserve/get_range_extent_geom';

                    const response = await fetch(rangeExtentURL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            taxon_ids: taxonID,
                            include_inat: includeINat,
                            date_start: dateStart,
                            date_end: dateEnd,
                            data_providers: dataProviders,
                        }),
                    });

                    if (!response.ok) {
                        // This is triggered for 404/500 etc.
                        const errData = await response.json();
                        console.error(
                            'Error:',
                            response.status,
                            errData.detail
                        );
                        return;
                    }

                    const json = await response.json();

                    if (cancelled) return;

                    const result = json.result;

                    mapContext.rangeExtentGeom = result.range_extent_geom;

                    const sourceID = 'range-extent';
                    const source = map.getSource(sourceID);
                    if (source && 'setData' in source) {
                        (source as mapboxgl.GeoJSONSource).setData(
                            result.range_extent_geom ?? {
                                type: 'FeatureCollection',
                                features: [],
                            }
                        );
                    }
                }

                getRangeExtentGeom();
            } catch (error) {
                console.error('Failed to update map layers:', error);
            }
        }

        updateLayers();

        return () => {
            cancelled = true;
        };
    });

    // React to hovered feature state changes from outside map component
    $effect(() => {
        console.log(mapContext.activeLayers);
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

    /* Mapbox tooltip restyle */
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
