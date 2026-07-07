// Helper functions for dealing with our big, flat, taxaTree

import type { TaxonNodeType } from '../types/api';

// Create nested visible notes for render
export function getVisibleNodes(
    flatMap: Map<number, TaxonNodeType>,
    openSet: Set<number>
): TaxonNodeType[] {
    const visible: TaxonNodeType[] = [];
    const childrenByParent = getNestedTree(flatMap);

    function addChildren(parent_id: number | null) {
        for (const child of childrenByParent[parent_id ?? -1] || []) {
            visible.push(child);
            if (openSet.has(child.taxon_id)) {
                addChildren(child.taxon_id);
            }
        }
    }

    // Start from the root(s)
    addChildren(null);
    return visible;
}

// Take flatMap of TaxonNodeType[] and created a nested tree using parent_name_usage_id
export function getNestedTree(
    flatMap: Map<number, TaxonNodeType>
): Record<number, TaxonNodeType[]> {
    const childrenByParent: Record<number, TaxonNodeType[]> = {};

    // Group nodes by parent_id
    for (const node of flatMap.values()) {
        const parentID = node.parent_name_usage_id ?? -1;
        if (!childrenByParent[parentID]) {
            childrenByParent[parentID] = [];
        }
        childrenByParent[parentID].push(node);
    }
    return childrenByParent;
}

export function getAllChildrenNodes(
    flatList: Map<number, TaxonNodeType>,
    parentID: number
): TaxonNodeType[] {
    const result: TaxonNodeType[] = [];
    const childrenByParent = getNestedTree(flatList);

    function dfs(id: number) {
        const children = childrenByParent[id] || [];
        for (const child of children) {
            result.push(child);
            dfs(child.taxon_id);
        }
    }

    dfs(parentID);

    return result;
}
