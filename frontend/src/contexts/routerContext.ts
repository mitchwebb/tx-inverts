import { getContext, setContext } from 'svelte';

export const routerStateKey = 'router';

export type RouterPath = '/' | '/map' | '/taxa' | '/rankings';

// Make type for possible active pages
export type RouterStateType = {
    url: URL;
    navigate: (pathname: string, replace?: boolean) => void;
};

export const initialRouterState: RouterStateType = {
    url: new URL(window.location.href),
    navigate: () => {},
};

export function setRouterContext(routerState: RouterStateType) {
    setContext(routerStateKey, routerState);
}

export function getRouterContext(): RouterStateType {
    return getContext(routerStateKey) as RouterStateType;
}
