// Helper functions for dealing with our big, flat, taxaTree

import type { BackboneNode } from '../types/api';
import type { TaxonomicRank } from '../types/taxa';

// Create nested visible notes for render (dependent on the list of ranks we're currently allowing to show)
export function getVisibleNodes(
    flatMap: Map<string, BackboneNode>,
    openSet: Set<string>,
    allowedRanks: Set<TaxonomicRank>
): BackboneNode[] {
    const visible: BackboneNode[] = [];
    const childrenByParent = getNestedTree(flatMap);

    function addChildren(parentID: string, effectiveParentID: string | null) {
        // Collect every node that appear at this level
        const promoted: BackboneNode[] = [];

        for (const child of childrenByParent[parentID] || []) {
            if (child.taxonRank !== null && allowedRanks.has(child.taxonRank)) {
                promoted.push({
                    ...child,
                    effectiveParentID: effectiveParentID,
                });
            } else {
                collectPromotedChildren(
                    child.taxonID,
                    effectiveParentID,
                    promoted
                );
            }
        }

        // Sort nodes alphabetically, putting nulls at the end
        function sortNodes(nodes: BackboneNode[]): BackboneNode[] {
            return nodes.sort((a, b) => {
                const aName = a.canonicalName ?? a.scientificName;
                const bName = b.canonicalName ?? b.scientificName;
                if (aName == null) return 1;
                if (bName == null) return -1;

                return aName.localeCompare(bName, undefined, {
                    sensitivity: 'base',
                });
            });
        }

        // Now sort visible nodes
        for (const child of sortNodes(promoted)) {
            visible.push(child);
            if (openSet.has(child.taxonID)) {
                addChildren(child.taxonID, child.taxonID);
            }
        }

        function collectPromotedChildren(
            parentID: string,
            effectiveParentID: string | null,
            result: BackboneNode[]
        ) {
            for (const child of childrenByParent[parentID] || []) {
                if (
                    child.taxonRank !== null &&
                    allowedRanks.has(child.taxonRank)
                ) {
                    result.push({
                        ...child,
                        effectiveParentID: effectiveParentID,
                    });
                } else {
                    collectPromotedChildren(
                        child.taxonID,
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

// Take flatMap of BackboneNode[] and created a nested tree using parent_name_usage_id
export function getNestedTree(
    flatMap: Map<string, BackboneNode>
): Record<string, BackboneNode[]> {
    const childrenByParent: Record<string, BackboneNode[]> = {};

    // Group nodes by parent_id
    for (const node of flatMap.values()) {
        // Get parentID from parent_name_usage_id column
        let parentID = node.parentNameUsageID;

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
    flatList: Map<string, BackboneNode>,
    parentID: string
): BackboneNode[] {
    const result: BackboneNode[] = [];
    const childrenByParent = getNestedTree(flatList);

    function dfs(id: string) {
        const children = childrenByParent[id] || [];
        for (const child of children) {
            result.push(child);
            dfs(child.taxonID);
        }
    }

    dfs(parentID);

    return result;
}
