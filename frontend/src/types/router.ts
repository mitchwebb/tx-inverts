import type { Provider } from '../constants/mapLegendKeys';
import type { NSRank } from './api';

// export interface RouteParamDefaults {
//     include_inat: boolean | null;
//     taxon_id: number | null;
//     data_provider: Provider | Provider[] | null;
//     ns_rank_state: NSRank | null;
//     taxa_filter: number | null;
// }

// export type URLParam = keyof URLParamMap;

// export type URLParamValue<K extends URLParam> = URLParamMap[K];

export type ParamCodec<T> = {
    toURL(value: T): string[] | null;
    fromURL(values: string[]): T;
};

// Type for relevant router keys to keep in sync
export type SyncedKey<ContextKey, P extends string = string> = {
    param: P;
    codec: ParamCodec<ContextKey>;
};

// Create type to pair synced router keys with their contexts
export type SyncedKeys<Context> = {
    [K in keyof Context]?: SyncedKey<Context[K]>;
};
