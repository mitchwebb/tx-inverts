import { getContext, setContext } from 'svelte';

export const rankingsStateKey = 'rankings';

// Make type for possible active pages
export type RankingsState = {
    ranksLoading: boolean;
    // List of ids from backend, filtered using rankings page filters
    // This currently disregards ranks/parent taxa filters, which are applied later
    qualifiedTaxonIDs: string[] | null;
    currSortKey: string | null;
    sortAscending: boolean | null;
    // List of taxonIDs currently visible in table, used for downloads
    visibleTaxonIDs: string[];
};

export const initialRankingsState: RankingsState = {
    ranksLoading: false,
    qualifiedTaxonIDs: null,
    currSortKey: null,
    sortAscending: null,
    visibleTaxonIDs: [],
};

export function setRankingsContext(rankingsState: RankingsState) {
    setContext(rankingsStateKey, rankingsState);
}

export function getRankingsContext(): RankingsState {
    return getContext(rankingsStateKey) as RankingsState;
}
