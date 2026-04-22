// Keys for map features in ['name: color'] format for MapBox styling
export type Color = string;

// Level 3 Ecoregions Key
export const l3EcoregionsLegend = {
    propName: 'US_L3NAME',
    colorMap: {
        'Western Gulf Coastal Plain': '#def1ef',
        'High Plains': '#ffec97',
        'Edwards Plateau': '#c2e1b6',
        'South Central Plains': '#9bb3b1',
        'Chihuahuan Deserts': '#f8bbb7',
        'Texas Blackland Prairies': '#be8c62',
        'Arizona/New Mexico Mountains': '#c4e3c5',
        'Central Great Plains': '#fde9cf',
        'Southwestern Tablelands': '#f1c8bb',
        'Cross Timbers': '#94ab83',
        'East Central Texas Plains': '#f7c82b',
        'Southern Texas Plains': '#fbc7a2',
    },
} as const;
export type L3Ecoregion = keyof typeof l3EcoregionsLegend.colorMap;
export const l3EcoregionsColorStops = Object.entries(
    l3EcoregionsLegend.colorMap
) as [string, string][];

// Level 4 Ecoregions Key
// Note: Floodplains and low terraces occur in multiple L3 Regions, so we must keep the prefixes
export const l4EcoregionsLegend = {
    propName: 'L4_KEY',
    colorMap: {
        '23a  Chihuahuan Desert Slopes': '#f0f7e4',
        '23b  Madrean Lower Montane Woodlands': '#c4e3c5',
        '24a  Chihuahuan Basins and Playas': '#fcefeb',
        '24b  Chihuahuan Desert Grasslands': '#fce3db',
        '24c  Low Mountains and Bajadas': '#fbd9cf',
        '24d  Chihuahuan Montane Woodlands': '#f8bbb7',
        '24e  Stockton Plateau': '#f2c8ba',
        '24f  Rio Grande Floodplain': '#de9a85',
        '25b  Rolling Sand Plains': '#ffface',
        '25e  Canadian/Cimarron High Plains': '#ffe7ad',
        '25i  Llano Estacado': '#fff3c2',
        '25j  Shinnery Sands': '#ffec97',
        '25k  Arid Llano Estacado': '#fff8d3',
        '26a  Canadian/Cimarron Breaks': '#f1c8bb',
        '26b  Flat Tablelands and Valleys': '#f6d9cf',
        '26c  Caprock Canyons, Badlands, and Breaks': '#f0b6a2',
        '26d  Semiarid Canadian Breaks': '#f2d4c5',
        '27h  Red Prairie': '#fde1c1',
        '27i  Broken Red Plains': '#fde9cf',
        '27j  Limestone Plains': '#fef0d4',
        '29b  Eastern Cross Timbers': '#94ab83',
        '29c  Western Cross Timbers': '#c0c589',
        '29d  Grand Prairie': '#c9cbaa',
        '29e  Limestone Cut Plain': '#d4d3af',
        '29f  Carbonate Cross Timbers': '#a0b07e',
        '30a  Edwards Plateau Woodland': '#d5eacf',
        '30b  Llano Uplift': '#c2e1b6',
        '30c  Balcones Canyonlands': '#a2d4a6',
        '30d  Semiarid Edwards Plateau': '#deeed6',
        '31a  Northern Nueces Alluvial Plains': '#fcdcc8',
        '31b  Semiarid Edwards Bajada': '#fdeddd',
        '31c  Texas-Tamaulipan Thornscrub': '#fde6d3',
        '31d  Rio Grande Floodplain and Terraces': '#fbc7a2',
        '32a  Northern Blackland Prairie': '#c2997d',
        '32b  Southern Blackland/Fayette Prairie': '#d0af9d',
        '32c  Floodplains and Low Terraces': '#be8c62',
        '33a  Northern Post Oak Savanna': '#f5e19a',
        '33b  Southern Post Oak Savanna': '#ffdd75',
        '33c  San Antonio Prairie': '#e1a934',
        '33d  Northern Prairie Outliers': '#f7c82b',
        '33e  Bastrop Lost Pines': '#dfca3a',
        '33f  Floodplains and Low Terraces': '#f2c85e',
        '34a  Northern Humid Gulf Coastal Prairies': '#cadde1',
        '34b  Southern Subhumid Gulf Coastal Prairies': '#def1ef',
        '34c  Floodplains and Low Terraces': '#afcccf',
        '34d  Coastal Sand Plain': '#d4e3d7',
        '34e  Lower Rio Grande Valley': '#bfd6d3',
        '34f  Lower Rio Grande Alluvial Floodplain': '#89babe',
        '34g  Texas-Louisiana Coastal Marshes': '#7597a2',
        '34h  Mid-Coast Barrier Islands and Coastal Marshes': '#7cabbc',
        '34i  Laguna Madre Barrier Islands and Coastal Marshes': '#7f9b94',
        '35a  Tertiary Uplands': '#ccd7cc',
        '35b  Floodplains and Low Terraces': '#7cb4b1',
        '35c  Pleistocene Fluvial Terraces': '#d3dedc',
        '35e  Southern Tertiary Uplands': '#a1c5ac',
        '35f  Flatwoods': '#bad6c3',
        '35g  Red River Bottomlands': '#9bb3b1',
    },
} as const;
export type L4Ecoregion = keyof typeof l4EcoregionsLegend.colorMap;
export const l4EcoregionsColorStops = Object.entries(
    l4EcoregionsLegend.colorMap
) as [L4Ecoregion, string][];

// Map of L4 Ecoregions to L3 Ecoregions
export const ecoregionsMap: Record<
    L3Ecoregion,
    Partial<Record<L4Ecoregion, string>>
> = {
    'Arizona/New Mexico Mountains': {
        '23a  Chihuahuan Desert Slopes': '#f0f7e4',
        '23b  Madrean Lower Montane Woodlands': '#c4e3c5',
    },
    'Chihuahuan Deserts': {
        '24a  Chihuahuan Basins and Playas': '#fcefeb',
        '24b  Chihuahuan Desert Grasslands': '#fce3db',
        '24c  Low Mountains and Bajadas': '#fbd9cf',
        '24d  Chihuahuan Montane Woodlands': '#f8bbb7',
        '24e  Stockton Plateau': '#f2c8ba',
        '24f  Rio Grande Floodplain': '#de9a85',
    },
    'High Plains': {
        '25b  Rolling Sand Plains': '#ffface',
        '25e  Canadian/Cimarron High Plains': '#ffe7ad',
        '25i  Llano Estacado': '#fff3c2',
        '25j  Shinnery Sands': '#ffec97',
        '25k  Arid Llano Estacado': '#fff8d3',
    },
    'Southwestern Tablelands': {
        '26a  Canadian/Cimarron Breaks': '#f1c8bb',
        '26b  Flat Tablelands and Valleys': '#f6d9cf',
        '26c  Caprock Canyons, Badlands, and Breaks': '#f0b6a2',
        '26d  Semiarid Canadian Breaks': '#f2d4c5',
    },
    'Central Great Plains': {
        '27h  Red Prairie': '#fde1c1',
        '27i  Broken Red Plains': '#fde9cf',
        '27j  Limestone Plains': '#fef0d4',
    },
    'Cross Timbers': {
        '29b  Eastern Cross Timbers': '#94ab83',
        '29c  Western Cross Timbers': '#c0c589',
        '29d  Grand Prairie': '#c9cbaa',
        '29e  Limestone Cut Plain': '#d4d3af',
        '29f  Carbonate Cross Timbers': '#a0b07e',
    },
    'Edwards Plateau': {
        '30a  Edwards Plateau Woodland': '#d5eacf',
        '30b  Llano Uplift': '#c2e1b6',
        '30c  Balcones Canyonlands': '#a2d4a6',
        '30d  Semiarid Edwards Plateau': '#deeed6',
    },
    'Southern Texas Plains': {
        '31a  Northern Nueces Alluvial Plains': '#fcdcc8',
        '31b  Semiarid Edwards Bajada': '#fdeddd',
        '31c  Texas-Tamaulipan Thornscrub': '#fde6d3',
        '31d  Rio Grande Floodplain and Terraces': '#fbc7a2',
    },
    'Texas Blackland Prairies': {
        '32a  Northern Blackland Prairie': '#c2997d',
        '32b  Southern Blackland/Fayette Prairie': '#d0af9d',
        '32c  Floodplains and Low Terraces': '#be8c62',
    },
    'East Central Texas Plains': {
        '33a  Northern Post Oak Savanna': '#f5e19a',
        '33b  Southern Post Oak Savanna': '#ffdd75',
        '33c  San Antonio Prairie': '#e1a934',
        '33d  Northern Prairie Outliers': '#f7c82b',
        '33e  Bastrop Lost Pines': '#dfca3a',
        '33f  Floodplains and Low Terraces': '#f2c85e',
    },
    'Western Gulf Coastal Plain': {
        '34a  Northern Humid Gulf Coastal Prairies': '#cadde1',
        '34b  Southern Subhumid Gulf Coastal Prairies': '#def1ef',
        '34c  Floodplains and Low Terraces': '#afcccf',
        '34d  Coastal Sand Plain': '#d4e3d7',
        '34e  Lower Rio Grande Valley': '#bfd6d3',
        '34f  Lower Rio Grande Alluvial Floodplain': '#89babe',
        '34g  Texas-Louisiana Coastal Marshes': '#7597a2',
        '34h  Mid-Coast Barrier Islands and Coastal Marshes': '#7cabbc',
        '34i  Laguna Madre Barrier Islands and Coastal Marshes': '#7f9b94',
    },
    'South Central Plains': {
        '35a  Tertiary Uplands': '#ccd7cc',
        '35b  Floodplains and Low Terraces': '#7cb4b1',
        '35c  Pleistocene Fluvial Terraces': '#d3dedc',
        '35e  Southern Tertiary Uplands': '#a1c5ac',
        '35f  Flatwoods': '#bad6c3',
        '35g  Red River Bottomlands': '#9bb3b1',
    },
} as const;

// Texas Parks Property Type Key
export const texasParksLegend = {
    propName: 'LegendClass',
    colorMap: {
        Federal: '#FF0000',
        'Districts & Authorities': '#FF7744',
        'City & Municipal': '#FFFF00',
        'Private & Other': '#00FF00',
        State: '#0000FF',
        County: '#BB33FF',
    },
} as const;
export type TexasParkClassification = keyof typeof texasParksLegend.colorMap;
export const TexasParksColorStops = Object.entries(
    texasParksLegend.colorMap
) as [string, string][];

// Layer feature properties used by map legends
export type LegendFeatureProperty =
    | typeof l4EcoregionsLegend.propName
    | typeof l3EcoregionsLegend.propName
    | typeof texasParksLegend.propName;

// Layer feature property values used by map legends
export type LegendFeatureValue =
    | L3Ecoregion
    | L4Ecoregion
    | TexasParkClassification;

// type HoverablePropertyDef = {
//     propName: LegendFeatureProperty;
//     source: MapLayerSource;
//     sourceLayer: MapSourceLayer;
// };
