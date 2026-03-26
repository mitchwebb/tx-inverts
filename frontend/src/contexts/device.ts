// stores/device.ts
import { readable } from 'svelte/store';

export const isMobile = readable(false, (set) => {
    const mq = window.matchMedia('(pointer: coarse)');
    set(mq.matches);
    const handler = (e: MediaQueryListEvent) => set(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
});
