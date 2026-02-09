import { getContext, setContext, type Snippet } from 'svelte';

export const tooltipStateKey = 'tooltip';

export type TooltipStateType = {
    visible: boolean;
    content: string | Snippet | null;
    target: HTMLElement | null;
    backgroundColor: string | null;
};

export const initialTooltipState: TooltipStateType = {
    visible: false,
    content: null,
    target: null,
    backgroundColor: null,
};

export function setTooltipContext(tooltipState: TooltipStateType) {
    setContext(tooltipStateKey, tooltipState);
}

export function getTooltipContext(): TooltipStateType {
    return getContext(tooltipStateKey) as TooltipStateType;
}
