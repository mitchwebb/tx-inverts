// Some GeoJSON types (avoiding a dependency)

export type GeoJSONPolygon = {
    type: 'Polygon';
    coordinates: number[][][]; // Array of LinearRings, each LinearRing is an array of positions [lng, lat]
};

export type GeoJSONMultiPolygon = {
    type: 'MultiPolygon';
    coordinates: number[][][][]; // Array of polygons
};
