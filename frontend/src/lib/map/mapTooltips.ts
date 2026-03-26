import { isValidURL } from '../../util/isValidURL';
import { toLocaleRounded } from '../../util/textHelpers';
import type { GeoJsonProperties } from 'geojson';

export type MapHoverField = {
    label: string; // Label for UI display
    property: string; // Property corresponding to layer data
    transform?: (value: any, properties: GeoJsonProperties) => string; // Necessary transform for data display
};

export type MapHoverSection = {
    sectionLabel: string; // Label for display section ('Parks')
    fields: MapHoverField[];
};

// Tooltip fields that should be captured and displayed based on mouseover position
export const targetFeatureFieldsMap: Partial<Record<string, MapHoverSection>> =
    {
        'tx_eco_l4-1joalj': {
            sectionLabel: 'Ecoregion',
            fields: [
                { label: 'L3', property: 'US_L3NAME' },
                { label: 'L4', property: 'US_L4NAME' },
            ],
        },
        texas_parks: {
            sectionLabel: 'Park',
            fields: [
                { label: 'Name', property: 'ManagerPropName' },
                { label: 'Property Type', property: 'LegendClass' },
                {
                    label: 'Acreage',
                    property: 'AcresCalc',
                    transform: (v: unknown) =>
                        typeof v === 'number'
                            ? `${toLocaleRounded(v, 2)} acres`
                            : '',
                },
            ],
        },
        'tx_counties-25946r': {
            sectionLabel: 'County',
            fields: [{ label: '', property: 'COUNTY' }],
        },
        'observations-circles': {
            sectionLabel: 'Observation',
            fields: [
                { label: '', property: 'accepted_scientific_name' },
                {
                    label: 'Date',
                    property: 'collection_start_date',
                    transform: (v: string, props: GeoJsonProperties) => {
                        let start_date = v ? new Date(v) : null;
                        let date_string = null;

                        if (start_date) {
                            date_string = start_date.toLocaleDateString();
                        }

                        if (props) {
                            let end_date = props.collection_end_date
                                ? new Date(props.collection_end_date)
                                : null;
                            if (
                                end_date &&
                                end_date.getDate() != start_date?.getDate()
                            ) {
                                date_string += ` - ${end_date.toLocaleDateString()}`;
                            }
                        }
                        return `<span>${date_string}</span>`;
                    },
                },
                { label: 'Institution', property: 'institution_code' },
                {
                    label: '',
                    property: 'gbif_id',
                    transform: (v: string) => {
                        if (
                            isValidURL(`https://www.gbif.org/occurrence/${v}`)
                        ) {
                            return `
                            <a 
                                aria-label='Link to original occurrence record' 
                                target='none'
                                href=https://www.gbif.org/occurrence/${v}>https://www.gbif.org/occurrence/${v}
                            </a>`;
                        } else {
                            return `GBIF ID: ${v}`;
                        }
                    },
                },
            ],
        },
    };

export function buildTooltipSections(
    features: mapboxgl.GeoJSONFeature[]
): string {
    const sections: string[] = [];

    // Eliminate duplicate features (sometimes caused by multiple layers with the same source)
    const dedupedFeatures = features.filter((feature, index, self) => {
        return (
            index ===
            self.findIndex(
                (f) => f.source === feature.source && f.id === feature.id
            )
        );
    });

    for (const feature of dedupedFeatures) {
        const sourceID = feature.source as string | undefined;
        if (!sourceID) continue;

        const sourceLayer = feature.sourceLayer;
        if (!sourceLayer) continue;

        const targetFieldsMap = targetFeatureFieldsMap[sourceLayer];
        if (!targetFieldsMap) continue;

        const { sectionLabel, fields } = targetFieldsMap;

        const sectionRows = fields
            .map(({ label, property, transform }) => {
                const props = feature.properties || {};
                const raw = props[property];
                const value =
                    raw != null
                        ? transform
                            ? transform(raw, props)
                            : raw
                        : 'Unknown';
                const labelText = label ? `${label}: ` : '';
                return `<li>${labelText}${value}</li>`;
            })
            .join('');

        sections.push(`
                        <div class="tooltip-section">
                            <div class="tooltip-section-header">${sectionLabel}:</div>
                            <ul>${sectionRows}</ul>
                        </div>
                    `);
    }
    return sections.join('');
}
