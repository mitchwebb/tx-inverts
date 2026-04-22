export type ParamCodec<T> = {
    toURL(value: T): string[] | null;
    fromURL(values: string[]): T | null | undefined;
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
