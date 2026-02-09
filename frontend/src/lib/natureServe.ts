/**
 * Calculates NatureServe-type state rank based on minimum necessary data (as of right now)
 * Derived from NatureServe's assessment calculator
 *
 * @param occurrences - An integer representing the number of occurrences of a taxon
 * @param rangeExtent - An integer representing a taxon's range extent in km2 (currently)
 * @param areaOfOccupancy - An integer representing a taxon's AOO in 4km2 bins
 * @returns zeroRangeRank - The taxon's state-level conservation rank, as derived from these minimum params
 */

import type { NSRank } from '../types/api';

export function calculateNSRank(
    occurrences: number,
    rangeExtent: number,
    areaOfOccupancy: number
): NSRank {
    // If all values are 0, species is data deficient
    // NatureServe doesn't actually have this ranking. This would be presumed extinct
    if (occurrences == 0 && rangeExtent == 0 && areaOfOccupancy == 0) {
        return 'U';
    }
    // According to IUCN, rangeExtent should be AT LEAST equal to areaOfOccupancy
    if (rangeExtent < areaOfOccupancy) {
        rangeExtent = areaOfOccupancy;
    }

    // If one of these values exists, all of them must at this point
    if (occurrences == 0 || rangeExtent == 0 || areaOfOccupancy == 0) {
        return 'U';
    }

    let points = 0.0;
    let threeAverageScore = 0;

    if (occurrences == 0) {
        // NatureServe Z Value
        points += 0.0;
    } else if (0 < occurrences && occurrences <= 5) {
        // NatureServe A Value
        points += 0.0;
    } else if (5 < occurrences && occurrences <= 20) {
        // NatureServe B Value
        points += 1.38;
    } else if (20 < occurrences && occurrences <= 80) {
        // NatureServe C Value
        points += 2.75;
    } else if (80 < occurrences && occurrences <= 300) {
        // NatureServe D Value
        points += 4.13;
    } else if (300 < occurrences) {
        // NatureServe E Value
        points += 5.5;
    }

    // These point values are doubled, as NatureServe gives them a weight of 2
    if (areaOfOccupancy == 0) {
        // NatureServe Z Value
        points += 0.0 * 2;
    } else if (0 < areaOfOccupancy && areaOfOccupancy <= 1) {
        // NatureServe A Value
        points += 0.0 * 2;
    } else if (1 < areaOfOccupancy && areaOfOccupancy <= 2) {
        // NatureServe B Value
        points += 0.69 * 2;
    } else if (2 < areaOfOccupancy && areaOfOccupancy <= 5) {
        // NatureServe C Value
        points += 1.38 * 2;
    } else if (5 < areaOfOccupancy && areaOfOccupancy <= 25) {
        // NatureServe D Value
        points += 2.06 * 2;
    } else if (25 < areaOfOccupancy && areaOfOccupancy <= 125) {
        // NatureServe E Value
        points += 2.75 * 2;
    } else if (125 < areaOfOccupancy && areaOfOccupancy <= 500) {
        // NatureServe F Value
        points += 3.44 * 2;
    } else if (500 < areaOfOccupancy && areaOfOccupancy <= 2500) {
        // NatureServe G Value
        points += 4.13 * 2;
    } else if (2500 < areaOfOccupancy && areaOfOccupancy <= 12500) {
        // NatureServe H Value
        points += 4.81 * 2;
    } else if (12500 < areaOfOccupancy) {
        // NatureServe I Value
        points += 5.5 * 2;
    }

    if (rangeExtent == 0) {
        // NatureServe Z Value
        points += 0.0;
    } else if (0 < rangeExtent && rangeExtent <= 100) {
        // NatureServe A Value
        points += 0.0;
    } else if (100 < rangeExtent && rangeExtent <= 250) {
        // NatureServe B Value
        points += 0.79;
    } else if (250 < rangeExtent && rangeExtent <= 1000) {
        // NatureServe C Value
        points += 1.57;
    } else if (1000 < rangeExtent && rangeExtent <= 5000) {
        // NatureServe D Value
        points += 2.36;
    } else if (5000 < rangeExtent && rangeExtent <= 20000) {
        // NatureServe E Value
        points += 3.14;
    } else if (20000 < rangeExtent && rangeExtent <= 200000) {
        // NatureServe F Value
        points += 3.93;
    } else if (200000 < rangeExtent && rangeExtent <= 2500000) {
        // NatureServe G Value
        points += 4.71;
    } else if (2500000 < rangeExtent) {
        // NatureServe H Value
        points += 5.5;
    }

    threeAverageScore = points / 4;

    // This is terminology taken from NatureServe ranking calculator
    // In this case, 'range' refers to the difference between low/high
    // ranking estimates.
    // With our parameters, there is no estimate range, hence 'zero_range'
    let zeroRangeRank: NSRank = 'U';

    if (threeAverageScore <= 1.5) {
        zeroRangeRank = '1';
    } else if (threeAverageScore <= 2.5) {
        zeroRangeRank = '2';
    } else if (threeAverageScore <= 3.5) {
        zeroRangeRank = '3';
    } else if (threeAverageScore <= 4.5) {
        zeroRangeRank = '4';
    } else if (threeAverageScore > 4.5) {
        zeroRangeRank = '5';
    }

    return zeroRangeRank;
}
