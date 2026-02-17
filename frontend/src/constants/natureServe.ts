// Key for NatureServe values and colors
// TODO: We may want to separate these and move it to the db

export const nSRankKey = [
    { rank: 'X', color: '#000000', description: 'Presumed Extinct' },
    { rank: 'H', color: '#cd3030', description: 'Possibly Extinct' },
    { rank: '1', color: '#cd3030', description: 'Critically Imperiled' },
    { rank: '2', color: '#cd6630', description: 'Imperiled' },
    { rank: '3', color: '#cd9a00', description: 'Vulnerable' },
    { rank: '4', color: '#006666', description: 'Apparently Secure' },
    { rank: '5', color: '#006666', description: 'Secure' },
    { rank: 'U', color: '#b3b3b3', description: 'Unrankable' },
] as const;

export const nSRanks = nSRankKey.map((rankItem) => rankItem.rank);

export const nSDescriptions = nSRankKey.map((rankItem) => rankItem.description);
