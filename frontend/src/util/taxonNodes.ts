// Helper functions for dealing with our big, flat, taxaTree

import type { TaxonNodeType } from '../types/api';

// Create nested visible notes for render
export function getVisibleNodes(
    flatList: TaxonNodeType[],
    openSet: Set<number>
): TaxonNodeType[] {
    const visible: TaxonNodeType[] = [];
    const childrenByParent = getNestedTree(flatList);

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

export function getNestedTree(flatList: TaxonNodeType[]) {
    const childrenByParent: Record<number, TaxonNodeType[]> = {};

    // Group nodes by parent_id
    for (const node of flatList) {
        if (!childrenByParent[node.parent_name_usage_id ?? -1]) {
            childrenByParent[node.parent_name_usage_id ?? -1] = [];
        }
        childrenByParent[node.parent_name_usage_id ?? -1].push(node);
    }
    return childrenByParent;
}

export function getAllChildrenNodes(
    flatList: TaxonNodeType[],
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
