// metricsContext.ts
import { getContext, setContext } from 'svelte';

export const metricsStateKey = 'metrics';

export type MetricsParams = {
    aOOResolution: '1km2' | '4km2';
};

export const initialMetricsState: MetricsParams = {
    aOOResolution: '4km2',
};

export function setMetricsContext(metricsState: MetricsParams): void {
    setContext(metricsStateKey, metricsState);
}

export function getMetricsContext(): MetricsParams {
    return getContext(metricsStateKey);
}
