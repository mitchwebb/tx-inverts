import { getMapContext, type MapState } from '../contexts/mapContext';
import {
    getActiveTaxaContext,
    type ActiveTaxaState,
} from '../contexts/activeTaxaContext';
import {
    getFiltersContext,
    type FiltersState,
} from '../contexts/filtersContext';
import type { NSRank } from '../types/api';
import type { ParamCodec, SyncedKeys } from '../types/router';
import {
    booleanCodec,
    dateCodec,
    iDObjectCodec,
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
            datasets: {
                param: 'dataset',
                codec: stringArrayCodec() as ParamCodec<string[]>,
            },
            nSRanks: {
                param: 'status',
                codec: stringArrayCodec() as ParamCodec<NSRank[]>,
            },
            taxonRank: {
                param: 'rank',
                codec: stringCodec() as ParamCodec<TaxonomicRank | null>,
            },
            dateStart: { param: 'd1', codec: dateCodec() },
            dateEnd: { param: 'd2', codec: dateCodec() },
            region: {
                param: 'region',
                codec: iDObjectCodec(),
            },
        }),
    },

    // Special case of setting active taxa in state from URL
    taxon: {
        getContext: getActiveTaxaContext,
        keys: makeSyncedKeys<ActiveTaxaState>({
            taxa: {
                param: 'taxon',
                codec: iDObjectCodec(),
            },
        }),
    },

    map: {
        getContext: getMapContext,
        keys: makeSyncedKeys<MapState>({}),
    },
} as const;
