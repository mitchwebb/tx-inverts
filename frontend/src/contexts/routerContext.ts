import { getContext, setContext } from 'svelte';

export const routerStateKey = 'router';

export type RouterPath = '/' | '/map' | '/backbone' | '/rankings';

// Make type for possible active pages
export type RouterState = {
    url: URL;
    navigate: (pathname: string, replace?: boolean) => void;
};

export const initialRouterState: RouterState = {
    url: new URL(window.location.href),
    navigate: () => {},
};

export function setRouterContext(routerState: RouterState) {
    setContext(routerStateKey, routerState);
}

export function getRouterContext(): RouterState {
    return getContext(routerStateKey) as RouterState;
}
