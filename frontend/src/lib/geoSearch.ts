import type {
    CountySuggestion,
    ParkSuggestion,
    RawCountySuggestion,
    RawParkSuggestion,
} from '../types/api';

/**
 * Helper to map raw county suggestion results into useable CountySuggestion objects
 * To be used in GeoSearch component
 * @param {RawCountySuggestion} json - Raw county json containing "id" and "county" keys
 */
export function parseCounties(json: RawCountySuggestion[]): CountySuggestion[] {
    return json.map((suggestion) => {
        return {
            id: suggestion.id,
            name: suggestion.county,
            regionType: 'county',
        };
    });
}

/**
 * Helper to map raw parks suggestion results into useable ParkSuggestion objects
 * To be used in GeoSearch component
 * @param {RawParkSuggestion} json - Raw park json containing "id" "prop_name", "alt_prop_name", "prop_class", and "owner" keys
 */
export function parseParks(json: RawParkSuggestion[]): ParkSuggestion[] {
    return json.map((result: RawParkSuggestion) => {
        return {
            id: result.id,
            name: result.prop_name,
            altPropName: result.alt_prop_name,
            propClass: result.prop_class,
            owner: result.owner,
            regionType: 'park',
        };
    });
}
