// stores/device.ts
import { readable } from 'svelte/store';

export const isMobile = readable(false, (set) => {
    const mq = window.matchMedia('(pointer: coarse)');
    set(mq.matches);
    const handler = (e: MediaQueryListEvent) => set(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
});

export const isNarrowView = readable(false, (set) => {
    if (typeof window === 'undefined') return; // SSR guard

    const mq = window.matchMedia('(max-width: 640px)');
    set(mq.matches);

    const handler = (e: MediaQueryListEvent) => set(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
});
