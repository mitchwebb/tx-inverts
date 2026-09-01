import { writable } from 'svelte/store';
import type { TaxonNodeType } from '../types/api';

export const taxaTree = writable<Map<string, TaxonNodeType> | null>(null);
