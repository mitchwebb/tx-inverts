import { writable } from 'svelte/store';
import type { TaxonNodeType } from '../types/api';

export const taxaTree = writable<TaxonNodeType[] | null>(null);
