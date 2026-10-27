import { writable } from 'svelte/store';
import type { BackboneNode } from '../types/api';

export const taxaTree = writable<Map<string, BackboneNode> | null>(null);
