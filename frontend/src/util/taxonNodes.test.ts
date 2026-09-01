import { beforeEach, describe, expect, test } from 'vitest';
import type { TaxonNodeType } from '../types/api';
import {
    getAllChildrenNodes,
    getNestedTree,
    getVisibleNodes,
} from './taxonNodes';

// Tree structure:
// root (1)
// ├── child A (2)
// │   ├── grandchild A1 (4)
// │   └── grandchild A2 (5)
// └── child B (3)  <- dead end

const makeNode = (id: string, parent: string | null): TaxonNodeType =>
    ({
        taxon_id: id,
        parent_name_usage_id: parent,
    }) as TaxonNodeType;

let flatMap: Map<string, TaxonNodeType>;

beforeEach(() => {
    flatMap = new Map([
        ['1', makeNode('1', null)],
        ['2', makeNode('2', '1')],
        ['3', makeNode('3', '1')],
        ['4', makeNode('4', '2')],
        ['5', makeNode('5', '2')],
    ]);
});

describe('test getNestedTree functionality', () => {
    test('something', () => {
        const tree = getNestedTree(flatMap);
        const correctNest = {
            // Base node
            '-1': [
                {
                    parent_name_usage_id: null,
                    taxon_id: 1,
                },
            ],
            '1': [
                {
                    parent_name_usage_id: 1,
                    taxon_id: 2,
                },
                {
                    parent_name_usage_id: 1,
                    taxon_id: 3,
                },
            ],
            '2': [
                {
                    parent_name_usage_id: 2,
                    taxon_id: 4,
                },
                {
                    parent_name_usage_id: 2,
                    taxon_id: 5,
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
                parent_name_usage_id: 2,
                taxon_id: '4',
            },
            {
                parent_name_usage_id: 2,
                taxon_id: '5',
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

describe('test getVisibleNodes functionality', () => {
    test('no visible nodes defaults to -1 (roots)', () => {
        const visibleNodes = getVisibleNodes(flatMap, new Set());
        expect(visibleNodes.map((n) => n.taxon_id)).toEqual([1]);
    });
    test('gets basic chain', () => {
        const visibleNodes = getVisibleNodes(flatMap, new Set(['1', '2']));
        expect(visibleNodes.map((n) => n.taxon_id)).toEqual(
            expect.arrayContaining([1, 2, 3, 4, 5])
        );
    });
    test('opens children when parent in openSet', () => {
        const visible = getVisibleNodes(flatMap, new Set(['1']));
        expect(visible.map((n) => n.taxon_id)).toEqual(
            expect.arrayContaining([2, 1, 3])
        );
    });
    test("doesn't include open children when parent isn't open", () => {
        const visible = getVisibleNodes(flatMap, new Set(['2']));
        expect(visible.map((n) => n.taxon_id)).toEqual(
            expect.arrayContaining([1])
        );
    });
});
