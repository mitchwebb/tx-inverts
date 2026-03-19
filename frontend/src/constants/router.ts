import { getMapContext, type MapState } from '../contexts/mapContext';
import {
    getActiveTaxaContext,
    type ActiveTaxaState,
    type ActiveTaxon,
} from '../contexts/activeTaxaContext';
import {
    getFiltersContext,
    type FiltersState,
} from '../contexts/filtersContext';
import type { NSRank } from '../types/api';
import type { Provider } from './mapLegendKeys';
import type { ParamCodec, SyncedKeys } from '../types/router';
import {
    booleanCodec,
    numberArrayCodec,
    numberCodec,
    stringArrayCodec,
    stringCodec,
} from '../util/router';
import type { TaxonomicRank } from '../types/taxa';

export function makeSyncedKeys<
    Context,
    const T extends SyncedKeys<Context> = SyncedKeys<Context>,
>(obj: T): T {
    return obj;
}

// Collect all context keys synced with router URL params and match them with their contexts and codecs
// This is used to set contexts from URL params and vice-versa
export const routerSyncedKeys = {
    filters: {
        getContext: getFiltersContext,
        keys: makeSyncedKeys<FiltersState>({
            includeINat: { param: 'inat', codec: booleanCodec(true) },
            dataProviders: {
                param: 'source',
                codec: stringArrayCodec() as ParamCodec<Provider[] | null>,
            },
            nSRanks: {
                param: 'status',
                codec: stringArrayCodec() as ParamCodec<NSRank[] | null>,
            },
            taxonRank: {
                param: 'rank',
                codec: stringCodec() as ParamCodec<TaxonomicRank | null>,
            },
            dateStart: { param: 'd1', codec: stringCodec() },
            dateEnd: { param: 'd2', codec: stringCodec() },
        }),
    },

    taxon: {
        getContext: getActiveTaxaContext,
        keys: makeSyncedKeys<ActiveTaxaState>({
            taxonIDs: { param: 'taxon', codec: numberArrayCodec() },
        }),
    },

    map: {
        getContext: getMapContext,
        keys: makeSyncedKeys<MapState>({}),
    },
} as const;
