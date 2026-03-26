import { getContext, setContext } from 'svelte';

export const sidebarStateKey = 'sidebar';

export type SidebarState = {
    visible: boolean;
    foldoutStates: Record<string, boolean>;
    open?: boolean;
};

export const initialSidebarState: SidebarState = {
    visible: false,
    foldoutStates: {},
    open: true,
};

export function setSidebarContext(sidebarState: SidebarState) {
    setContext(sidebarStateKey, sidebarState);
}

export function getSidebarContext(): SidebarState {
    return getContext(sidebarStateKey) as SidebarState;
}
