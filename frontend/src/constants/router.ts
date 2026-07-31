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
import type { NSRank, RegionInfo } from '../types/api';
import type { URLParamCodec, SyncedKeys } from '../types/router';
import {
    booleanURLCodec,
    dateURLCodec,
    collectionObjectURLCodec,
    stringArrayURLCodec,
    stringURLCodec,
    numberArrayURLCodec,
    numberURLCodec,
} from '../util/router';
import type { TaxonomicRank } from '../types/taxa';
import type { makeIDCollection } from '../util/collection.svelte';

export function makeSyncedKeys<
    Context,
    const T extends SyncedKeys<Context> = SyncedKeys<Context>,
>(obj: T): T {
    return obj;
}

export type RouterSyncedKey =
    | 'inat'
    | 'dataset'
    | 'status'
    | 'rank'
    | 'd1'
    | 'd2'
    | 'region'
    | 'uncertainty'
    | 'taxon';

// Collect all context keys synced with router URL params and match them with their contexts and codecs
// This is used to set contexts from URL params and vice-versa
export const routerSyncedKeys = {
    filters: {
        getContext: getFiltersContext,
        keys: makeSyncedKeys<FiltersState>({
            includeINat: { param: 'inat', codec: booleanURLCodec(true) },
            datasets: {
                param: 'dataset',
                codec: stringArrayURLCodec() as URLParamCodec<string[]>,
            },
            nSRanks: {
                param: 'status',
                codec: stringArrayURLCodec() as URLParamCodec<NSRank[]>,
            },
            taxonRank: {
                param: 'rank',
                codec: stringURLCodec() as URLParamCodec<TaxonomicRank | null>,
            },
            dateStart: {
                param: 'd1',
                codec: dateURLCodec(),
            },
            dateEnd: {
                param: 'd2',
                codec: dateURLCodec(),
            },
            regions: {
                param: 'region',
                codec: collectionObjectURLCodec() as URLParamCodec<
                    ReturnType<typeof makeIDCollection<RegionInfo, string>>
                >,
            },
            coordUncertainty: {
                param: 'uncertainty',
                codec: numberURLCodec() as URLParamCodec<number>,
            },
        }),
    },

    // Special case of setting active taxa in state from URL
    taxon: {
        getContext: getActiveTaxaContext,
        keys: makeSyncedKeys<ActiveTaxaState>({
            taxa: {
                param: 'taxon',
                codec: collectionObjectURLCodec() as URLParamCodec<
                    ReturnType<typeof makeIDCollection<ActiveTaxon, number>>
                >,
            },
        }),
    },

    map: {
        getContext: getMapContext,
        keys: makeSyncedKeys<MapState>({}),
    },
} as const;
