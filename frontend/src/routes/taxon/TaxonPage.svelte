<script lang="ts">
    import { type TaxonNodeType } from '../../types/api';
    import { taxaTree } from '../../contexts/TaxaTree';
    import { getActiveTaxaContext, initialTaxonState } from '../../contexts/activeTaxaContext';
    import NSCircle from '../../common/NSCircle.svelte';
    import ChevronDown from '../../assets/ChevronDown.svelte';
    import ChevronRight from '../../assets/ChevronRight.svelte';
    import { tick } from 'svelte';
    import MagnifyIcon from '../../assets/MagnifyIcon.svelte';
    import { capitalizeWords } from '../../util/textHelpers';
    import { isItalicizedRank } from '../../util/taxa';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import { getVisibleNodes } from '../../util/taxonNodes';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DefaultPage from '../../common/DefaultPage.svelte';
    import type { TaxonomicRank } from '../../types/taxa';

    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();

    const rankColumns: TaxonomicRank[] = [
        'kingdom',
        'phylum',
        'class',
        'order',
        'family',
        'genus',
        'species',
        'subspecies',
    ];

    let gridCols = $state(
        `repeat(${rankColumns.length}, minmax(max-content, 1fr)`
    );

    let openNodes: Set<number> = $state.raw(new Set([1]));

    // Minimum pixel movement to count as dragging
    const minMoveThreshold = 5;
    let isDragging: boolean = $state.raw(false);

    let initialTaxonOpened: boolean = $state(false);

    let visibleNodes: TaxonNodeType[] = $state.raw([]);

    function handleNodeClick(e: MouseEvent | KeyboardEvent) {
        // Ignore clicks while dragging
        if (isDragging) {
            isDragging = false;
            return;
        }

        const target = e.currentTarget as HTMLElement;

        if (!target || !target.id) return;

        const taxonID = parseInt(target.id);
        const set = new Set(openNodes);
        const isOpen = set.has(taxonID);

        if (isOpen) {
            set.delete(taxonID);
        } else {
            set.add(taxonID);
        }

        openNodes = set;

        const targetTaxonID = target.id;
        moveToTaxon(targetTaxonID);
    }

    function setActiveTaxon(e: MouseEvent) {
        e.stopPropagation();

        // Ignore clicks while dragging
        if (isDragging) {
            isDragging = false;
            return;
        }

        const target = e.currentTarget as HTMLElement;
        const parentNode = target.parentNode as HTMLElement;

        if (!target || !parentNode || !parentNode.id) return;

        const targetInt = parseInt(parentNode.id);

        // If taxon is already selected, deselect it
        if (taxaContext.taxa.ids.includes(targetInt)) {
            taxaContext.taxa.remove(targetInt);
            // Otherwise, select it
        } else {
            taxaContext.taxa.add({
                ...initialTaxonState,
                taxonID: targetInt
            });
        }
    }

    function openTaxon(taxonID: TaxonNodeType['taxon_id']) {
        if (openNodes.has(taxonID)) return; // already open, do nothing

        const set = new Set(openNodes);
        let currentID = taxonID;

        while (currentID) {
            set.add(currentID);
            const currentNode = $taxaTree?.get(currentID);
            if (!currentNode || !currentNode.parent_name_usage_id) break;
            currentID = currentNode.parent_name_usage_id;
        }
        openNodes = set;

        moveToTaxon(taxonID);
    }

    // Function to slide taxonomic tree window to selected taxon
    async function moveToTaxon(targetID: TaxonNodeType['taxon_id'] | string) {
        await tick();

        const idString = targetID.toString();
        // Assuming taxonID is a string or number matching the div id
        const el = document.getElementById(idString);
        if (el) {
            const nodeRect = el.getBoundingClientRect();
            // Find position of node in scrollable container
            const container = document.getElementById('taxon-page-body');
            const containerRect = container?.getBoundingClientRect();

            if (!containerRect || !container) return;

            const nodeWidth = nodeRect.width;

            // Get click offset relative to container and convert to scroll offset
            const offsetTop = nodeRect.top - containerRect.top;
            const scrollOffsetTop = offsetTop + container.scrollTop;

            const offsetLeft =
                nodeRect.left + nodeWidth / 2 - containerRect.left;
            const scrollOffsetLeft = offsetLeft + container.scrollLeft;

            // Scroll so the element is centered in container
            container.scrollTo({
                top: scrollOffsetTop - containerRect.height / 2,
                left: scrollOffsetLeft - containerRect.width / 2,
                behavior: 'smooth',
            });
        }
    }

    function handleWindowDrag(e: MouseEvent) {
        const container = document.getElementById('taxon-page-body');

        if (!e.currentTarget || !container) return;

        isDragging = false;

        const origin = {
            x: e.clientX,
            y: e.clientY,
        };

        e.preventDefault();

        const originalScroll = {
            top: container?.scrollTop,
            left: container?.scrollLeft,
        };

        function dragToScroll(e: MouseEvent) {
            const coordChange = {
                x: e.clientX - origin.x,
                y: e.clientY - origin.y,
            };

            if (
                !isDragging &&
                (Math.abs(coordChange.x) > minMoveThreshold ||
                    Math.abs(coordChange.y) > minMoveThreshold)
            ) {
                isDragging = true;
            }

            container?.scrollTo({
                top: originalScroll.top - coordChange.y,
                left: originalScroll.left - coordChange.x,
            });
        }

        function endWindowDrag() {
            // isDragging = false;
            window.removeEventListener('mousemove', dragToScroll);
            window.removeEventListener('mouseup', endWindowDrag);
        }

        window.addEventListener('mouseup', endWindowDrag);
        window.addEventListener('mousemove', dragToScroll);
    }

    // Determine if passed taxonID is a parent node in the taxaTree
    function taxonIsParent(id: number): boolean {
        if (!$taxaTree) return false;
        for (const node of $taxaTree.values()) {
            if (node.parent_name_usage_id === id) return true;
        }
        return false;
    }

    // Parse visible nodes tree every render based on dependencies
    $effect(() => {
        if ($taxaTree) {
            visibleNodes = getVisibleNodes($taxaTree, openNodes);
        }
    });

    // If a new activeTaxonID is set or if the page was just loaded, open it in the tree
    $effect(() => {
        const lastAddedID = taxaContext.taxa.ids.slice(-1)[0];
        if (lastAddedID && $taxaTree) {
            openTaxon(lastAddedID);
        }
    });

    // Check for active taxon node and scroll to it
    $effect(() => {
        const lastAddedTaxonID = taxaContext.taxa.ids.slice(-1)[0];
        if (
            lastAddedTaxonID &&
            !initialTaxonOpened &&
            visibleNodes.length > 0
        ) {
            const activeNodeExists = visibleNodes.some(
                (node) => node.taxon_id === lastAddedTaxonID
            );

            if (activeNodeExists) {
                moveToTaxon(lastAddedTaxonID);
                initialTaxonOpened = true; // Prevents this from running again.
            }
        }
    });
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<DefaultPage>
    <div
        id="taxon-page-body"
        role="application"
        class={[{ loading: !$taxaTree }]}
        tabindex="0"
        aria-label="Taxon navigation viewport"
        style:grid-template-columns={gridCols}
        onmousedown={handleWindowDrag}
        onkeydown={null}
    >
        {#each rankColumns as rank, i}
            <!-- Flag last header for styling -->
            {@const last = i == rankColumns.length - 1}
            <div
                class="taxon-rank-header grid-item"
                class:last
                style:grid-column={i + 1}
            >
                {capitalizeWords(rank)}
            </div>
        {/each}
        {#if !$taxaTree}
            <div id="taxa-loading-icon" class="icon">
                <LoadingIcon />
            </div>
        {/if}
        {#if $taxaTree}
            {#each visibleNodes as node, i}
                <!-- Find parent node index -->
                {@const parentIndex = visibleNodes.findIndex(
                    (n) => n.taxon_id === node.parent_name_usage_id
                )}
                <!-- Make sure parent node was found, then get rank index -->
                {@const parentCol =
                    parentIndex >= 0
                        ? rankColumns.indexOf(
                              visibleNodes[parentIndex].taxon_rank
                          ) + 1
                        : null}
                <!-- Get current column -->
                {@const nodeCol = rankColumns.indexOf(node.taxon_rank) + 1}
                <!-- Find offset between current and parent -->
                {@const offset = parentCol !== null ? nodeCol - parentCol : 0}
                <!-- Determine if we need a horizontal line -->
                {@const showHorizontalLine = offset > 0}
                <!-- Check if node has children -->
                {@const hasChildren = taxonIsParent(node.taxon_id)}
                {@const nsRank =
                    filtersContext.includeINat !== false
                        ? node.ns_rank_state
                        : node.ns_rank_state_no_inat}
                {@const italicized = isItalicizedRank(node.taxon_rank)}
                {@const nextColor = taxaContext.getNextColor()}

                <div
                    role="button"
                    tabindex="0"
                    id={node.taxon_id.toString()}
                    class="taxon-node-wrapper"
                    style:grid-column={nodeCol}
                    style:grid-row={i + 2}
                    onclick={handleNodeClick}
                    onkeypress={handleNodeClick}
                >
                    <button
                        class={[
                            'taxon-node-label',
                            `${hasChildren ? 'branch' : 'leaf'}`,
                            { invasive: node.us_invasive },
                        ]}
                    >
                        {#if node.us_invasive}
                            <div class="invasive-icon taxon-icon icon">
                                <InvasiveIcon />
                            </div>
                        {:else if node.ns_rank_state && node.taxon_rank == 'species'}
                            <div class="rank-circle taxon-icon icon">
                                <NSCircle
                                    active={true}
                                    rank={nsRank}
                                    level="s"
                                />
                            </div>
                        {/if}
                        {#if hasChildren}
                            <div class="taxon-chevron icon">
                                {#if openNodes.has(node.taxon_id)}
                                    <ChevronDown />
                                {:else}
                                    <ChevronRight />
                                {/if}
                            </div>
                        {/if}
                        <span class="taxon-name">
                            <span class={[{ italicized }]}>
                                {node.canonical_name}
                            </span>
                            <span class="taxon-authorship"
                                >{node.scientific_name_authorship ?? null}
                            </span>
                        </span>
                    </button>
                    <button
                        class="taxon-select-icon icon"
                        class:active={taxaContext.taxa.ids.some(
                            (taxonID) => taxonID == node.taxon_id
                        )}
                        style:color={taxaContext.taxa.get(node.taxon_id)
                            ? taxaContext.taxa.get(node.taxon_id)?.color
                            : nextColor}
                        onclick={setActiveTaxon}
                    >
                        <MagnifyIcon />
                    </button>
                </div>
                {#if showHorizontalLine}
                    <span
                        class="horizontal-line"
                        style:grid-column={`${parentCol} / span ${offset}`}
                        style:grid-row={i + 2}
                    >
                    </span>
                {/if}

                {@const showVerticalLine = parentIndex >= 0}

                {#if showVerticalLine}
                    {@const siblings = visibleNodes.filter(
                        (n) =>
                            n.parent_name_usage_id === node.parent_name_usage_id
                    )}
                    {@const isLastChild =
                        siblings.length &&
                        siblings[siblings.length - 1].taxon_id ===
                            node.taxon_id}
                    {#if isLastChild}
                        <div
                            class="vertical-line"
                            style:grid-column={parentCol}
                            style:grid-row={`${parentIndex + 3} / span ${i - parentIndex}`}
                        ></div>
                    {/if}
                {/if}
            {/each}
            <!-- Filler row to provide padding at bottom of selection area -->
            <div
                class="filler-row"
                style:grid-row={visibleNodes.length + 2}
                style:grid-column={1 / -1}
            ></div>
        {/if}
    </div>
</DefaultPage>

<style>
    .taxon-icon {
        margin-left: 0.5rem;
    }
    .invasive > * {
        color: var(--accent-color);
    }
    #taxa-loading-icon {
        padding: 0.5rem;
        color: var(--fill-color);
    }
    #taxon-page-body.loading {
        cursor: wait;
    }
    .filler-row {
        height: 1.5rem;
    }
    .taxon-select-icon {
        /* color: transparent; */
        background: transparent;
        padding: 0rem;
        margin-left: 0.5rem;
        flex-shrink: 0;
        visibility: hidden;
    }
    .taxon-node-wrapper:hover > .taxon-select-icon,
    .taxon-select-icon.active {
        visibility: visible;
    }
    .spacer-row {
        height: 1rem;
    }
    .taxon-authorship {
        font-weight: 200;
    }
    .taxon-chevron {
        flex-shrink: 0;
    }
    .taxon-node-label {
        position: relative;
        background-color: transparent;
        width: fit-content;
        color: var(--text-default);
        border: none;
        padding: 0;
        text-align: left;
        display: flex;
        align-items: center;
        white-space: nowrap;
        padding-top: 4px;
    }
    .taxon-node-label.active {
        font-weight: bold;
    }
    .taxon-node-wrapper {
        padding-right: 1rem;
        display: flex;
        align-items: center;
        position: relative;
    }
    .vertical-line {
        border-left: 1px solid var(--border);
    }
    .vertical-line,
    .horizontal-line {
        margin-left: calc(0.5rem + 3px);
        margin-bottom: calc(0.5rem + 3px);
    }
    .horizontal-line {
        border-bottom: 1px solid var(--border);
    }
    .taxon-rank-header {
        position: sticky;
        top: 0;
        z-index: 2;
        color: var(--text-default);
        text-align: left;
        background-color: var(--container-highlight);
        padding: 1rem 0.5rem 0.5rem 0.5rem;
        border-bottom: 1px solid var(--container-shadow);
        font-weight: 600;
        user-select: none;
    }
    .taxon-rank-header:not(.last) {
        border-right: 1px solid var(--container-shadow);
    }
    #taxon-page-body {
        height: 100%;
        display: grid;
        background-color: var(--container-mid);
        grid-auto-rows: max-content;
        border-radius: 3px;
        justify-content: baseline;
        transition: all 0.1 ease-in-out;
        cursor: grab;
        box-sizing: border-box;
        overflow: auto;
    }
    .leaf .taxon-name {
        padding-left: 0.5rem;
        vertical-align: middle;
    }

    .taxon-name > * {
        vertical-align: middle;
    }
</style>
