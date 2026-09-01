// Helper functions for dealing with our big, flat, taxaTree

import type { TaxonNodeType } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';

// Create nested visible notes for render (dependent on the list of ranks we're currently allowing to show)
export function getVisibleNodes(
    flatMap: Map<string, TaxonNodeType>,
    openSet: Set<string>,
    allowedRanks: Set<TaxonomicRank>
): TaxonNodeType[] {
    const visible: TaxonNodeType[] = [];
    const childrenByParent = getNestedTree(flatMap);

    function addChildren(parentID: string, effectiveParentID: string | null) {
        // Collect every node that appear at this level
        const promoted: TaxonNodeType[] = [];

        for (const child of childrenByParent[parentID] || []) {
            if (allowedRanks.has(child.taxon_rank)) {
                promoted.push({
                    ...child,
                    effective_parent_id: effectiveParentID,
                });
            } else {
                collectPromotedChildren(
                    child.taxon_id,
                    effectiveParentID,
                    promoted
                );
            }
        }

        // Sort nodes alphabetically, putting nulls at the end
        function sortNodes(nodes: TaxonNodeType[]): TaxonNodeType[] {
            return nodes.sort((a, b) => {
                if (a.canonical_name == null) return 1;
                if (b.canonical_name == null) return -1;

                return a.canonical_name.localeCompare(
                    b.canonical_name,
                    undefined,
                    { sensitivity: 'base' }
                );
            });
        }

        // Now sort visible nodes
        for (const child of sortNodes(promoted)) {
            visible.push(child);
            if (openSet.has(child.taxon_id)) {
                addChildren(child.taxon_id, child.taxon_id);
            }
        }

        function collectPromotedChildren(
            parentID: string,
            effectiveParentID: string | null,
            result: TaxonNodeType[]
        ) {
            for (const child of childrenByParent[parentID] || []) {
                if (allowedRanks.has(child.taxon_rank)) {
                    result.push({
                        ...child,
                        effective_parent_id: effectiveParentID,
                    });
                } else {
                    collectPromotedChildren(
                        child.taxon_id,
                        effectiveParentID,
                        result
                    );
                }
            }
        }
    }

    // Start from the root(s)
    addChildren('__root__', null);
    return visible;
}

// Take flatMap of TaxonNodeType[] and created a nested tree using parent_name_usage_id
export function getNestedTree(
    flatMap: Map<string, TaxonNodeType>
): Record<string, TaxonNodeType[]> {
    const childrenByParent: Record<string, TaxonNodeType[]> = {};

    // Group nodes by parent_id
    for (const node of flatMap.values()) {
        // Get parentID from parent_name_usage_id column
        let parentID = node.parent_name_usage_id;

        // If there is no parentID, or the parentID isn't present in our tree, mark the parentID as 'root'
        parentID = parentID && flatMap.has(parentID) ? parentID : '__root__';

        if (!childrenByParent[parentID]) {
            childrenByParent[parentID] = [];
        }
        childrenByParent[parentID].push(node);
    }

    return childrenByParent;
}

export function getAllChildrenNodes(
    flatList: Map<string, TaxonNodeType>,
    parentID: string
): TaxonNodeType[] {
    const result: TaxonNodeType[] = [];
    const childrenByParent = getNestedTree(flatList);

    function dfs(id: string) {
        const children = childrenByParent[id] || [];
        for (const child of children) {
            result.push(child);
            dfs(child.taxon_id);
        }
    }

    dfs(parentID);

    return result;
}
