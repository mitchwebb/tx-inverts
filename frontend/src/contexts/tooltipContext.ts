import { getContext, setContext, type Component, type Snippet } from 'svelte';

export const tooltipStateKey = 'tooltip';

export type TooltipState = {
    visible: boolean;
    content: string | Snippet | null;
    target: HTMLElement | null;
    backgroundColor: string | null;
};

export const initialTooltipState: TooltipState = {
    visible: false,
    content: null,
    target: null,
    backgroundColor: null,
};

export function setTooltipContext(tooltipState: TooltipState) {
    setContext(tooltipStateKey, tooltipState);
}

export function getTooltipContext(): TooltipState {
    return getContext(tooltipStateKey) as TooltipState;
}
