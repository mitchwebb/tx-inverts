import { getContext, setContext } from 'svelte';

export const sidebarStateKey = 'sidebar';

export type SidebarState = {
    width: number;
    visible: boolean;
};

export const initialSidebarState: SidebarState = {
    width: 350,
    visible: false,
};

export function setSidebarContext(sidebarState: SidebarState) {
    setContext(sidebarStateKey, sidebarState);
}

export function getSidebarContext(): SidebarState {
    return getContext(sidebarStateKey) as SidebarState;
}
