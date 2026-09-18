import { RANK_ORDER, type TaxonomicRank } from '../types/taxa';

export function sortRankOrder(rankArray: TaxonomicRank[]) {
    rankArray.sort((a, b) => RANK_ORDER.indexOf(a) - RANK_ORDER.indexOf(b));
    return rankArray;
}
