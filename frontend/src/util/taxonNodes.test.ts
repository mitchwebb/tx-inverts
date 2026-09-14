import { beforeEach, describe, expect, test } from 'vitest';
import type { TaxonInfo, TaxonNodeType } from '../types/api';
import {
    getAllChildrenNodes,
    getNestedTree,
    getVisibleNodes,
} from './taxonNodes';
import type { TaxonomicRank } from '../types/taxa';

// Tree structure:
// root (1)
// ├── child A (2)
// │   ├── grandchild A1 (4)
// │   └── grandchild A2 (5)
// └── child B (3)  <- dead end

const makeNode = (
    id: string,
    parent: string | null,
    taxonRank: TaxonomicRank
): TaxonNodeType =>
    ({
        taxonID: id,
        parentNameUsageID: parent,
        taxonRank: taxonRank,
    }) as TaxonNodeType;

let flatMap: Map<string, TaxonNodeType>;

beforeEach(() => {
    flatMap = new Map([
        ['1', makeNode('1', null, 'kingdom')],
        ['2', makeNode('2', '1', 'phylum')],
        ['3', makeNode('3', '1', 'class')],
        ['4', makeNode('4', '2', 'order')],
        ['5', makeNode('5', '2', 'family')],
    ]);
});

describe('test getNestedTree functionality', () => {
    test('something', () => {
        const tree = getNestedTree(flatMap);
        const correctNest = {
            // Base node
            __root__: [
                {
                    parentNameUsageID: null,
                    taxonID: '1',
                    taxonRank: 'kingdom',
                },
            ],
            '1': [
                {
                    parentNameUsageID: '1',
                    taxonID: '2',
                    taxonRank: 'phylum',
                },
                {
                    parentNameUsageID: '1',
                    taxonID: '3',
                    taxonRank: 'class',
                },
            ],
            '2': [
                {
                    parentNameUsageID: '2',
                    taxonID: '4',
                    taxonRank: 'order',
                },
                {
                    parentNameUsageID: '2',
                    taxonID: '5',
                    taxonRank: 'family',
                },
            ],
        };
        expect(tree).toEqual(correctNest);
    });

    test('dead end node has no children', () => {
        const tree = getNestedTree(flatMap);
        expect(tree[3]).toBeUndefined();
    });
});

describe('test getAllChildrenNodes functionality', () => {
    test('basic node retrieval', () => {
        const childrenNodes = getAllChildrenNodes(flatMap, '2');
        const expectedChildren = [
            {
                parentNameUsageID: '2',
                taxonID: '4',
                taxonRank: 'order',
            },
            {
                parentNameUsageID: '2',
                taxonID: '5',
                taxonRank: 'family',
            },
        ];
        expect(childrenNodes).toEqual(expectedChildren);
    });

    test('dead end returns empty', () => {
        expect(getAllChildrenNodes(flatMap, '3')).toHaveLength(0);
    });

    test('returns full subtree from root', () => {
        const result = getAllChildrenNodes(flatMap, '1');
        expect(result).toHaveLength(4);
    });
});

const allowedRanks: TaxonomicRank[] = [
    'kingdom',
    'phylum',
    'class',
    'order',
    'family',
    'tribe',
    'genus',
    'species',
    'subspecies',
];

describe('test getVisibleNodes functionality', () => {
    test('no visible nodes defaults to -1 (roots)', () => {
        const visibleNodes = getVisibleNodes(
            flatMap,
            new Set(),
            new Set(allowedRanks)
        );
        expect(visibleNodes.map((n) => n.taxonID)).toEqual(['1']);
    });
    test('gets basic chain', () => {
        const visibleNodes = getVisibleNodes(
            flatMap,
            new Set(['1', '2']),
            new Set(allowedRanks)
        );
        expect(visibleNodes.map((n) => n.taxonID)).toEqual(
            expect.arrayContaining(['1', '2', '3', '4', '5'])
        );
    });
    test('opens children when parent in openSet', () => {
        const visible = getVisibleNodes(
            flatMap,
            new Set(['1']),
            new Set(allowedRanks)
        );
        expect(visible.map((n) => n.taxonID)).toEqual(
            expect.arrayContaining(['2', '1', '3'])
        );
    });
    test("doesn't include open children when parent isn't open", () => {
        const visible = getVisibleNodes(
            flatMap,
            new Set(['2']),
            new Set(allowedRanks)
        );
        expect(visible.map((n) => n.taxonID)).toEqual(
            expect.arrayContaining(['1'])
        );
    });
});
