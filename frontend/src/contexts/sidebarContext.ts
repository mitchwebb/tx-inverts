import { getContext, setContext } from 'svelte';
import type { SidebarFilter } from '../constants/sidebarFilters';

export const sidebarStateKey = 'sidebar';

export type SidebarStateType = {
    visibleFilters: SidebarFilter[];
    width: number;
    visible: boolean;
};

export const initialSidebarState: SidebarStateType = {
    visibleFilters: [],
    width: 350,
    visible: false,
};

export function setSidebarContext(sidebarState: SidebarStateType) {
    setContext(sidebarStateKey, sidebarState);
}

export function getSidebarContext(): SidebarStateType {
    return getContext(sidebarStateKey) as SidebarStateType;
}
