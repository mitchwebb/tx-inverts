import { getContext, setContext } from 'svelte';

export const rankingsStateKey = 'rankings';

// Make type for possible active pages
export type RankingsState = {
    ranksLoading: boolean;
    qualifiedTaxonIDs: number[] | null; // List of ids from backend, filtered using rankings page filters
    currSortKey: string | null;
    sortAscending: boolean | null;
};

export const initialRankingsState: RankingsState = {
    ranksLoading: false,
    qualifiedTaxonIDs: null,
    currSortKey: null,
    sortAscending: null,
};

export function setRankingsContext(rankingsState: RankingsState) {
    setContext(rankingsStateKey, rankingsState);
}

export function getRankingsContext(): RankingsState {
    return getContext(rankingsStateKey) as RankingsState;
}
