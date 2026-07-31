<!--
    @component
    - Virtualized table structure capable of supporting column headers.
-->
<script lang="ts">
    import { onMount, tick, untrack, type Snippet } from 'svelte';
    import ArrowDown from '../assets/ArrowDown.svelte';
    import ArrowUp from '../assets/ArrowUp.svelte';
    import InfoButton from './InfoButton.svelte';

    type VirtualizedTableProps = {
        items: Record<any, any>[];
        rowHeight: number;
        headers: {
            label: string | Snippet;
            info?: string;
            sortKey?: string | null;
        }[];
        row: Snippet<[item: any, index: number]>;
        indexCol?: string | null;
        scrollToID?: number | string | null;
        hideHeader?: boolean;
        overscan?: number;
        defaultSortKey?: (typeof headers)[number]['sortKey'] | null;
        defaultAscending?: boolean | null;
        onSort?: (
            sortKey: (typeof headers)[number]['sortKey'],
            asc: boolean
        ) => void;
    };

    const {
        items,
        rowHeight,
        headers,
        row,
        indexCol = null,
        scrollToID = null,
        hideHeader = false,
        overscan = 5,
        defaultSortKey = headers[0]?.['sortKey'] ?? null,
        defaultAscending = true,
        onSort = () => {},
    }: VirtualizedTableProps = $props();

    let container: HTMLDivElement;
    let header: HTMLDivElement | undefined = $state();

    // Currently active sort key for table
    let currSortKey = $derived<typeof defaultSortKey>(defaultSortKey);
    // Boolean sort direction
    let sortAscending = $derived<boolean>(defaultAscending ?? true);
    // Index of item to scroll to
    let scrollToItemIndex = $state<number | null>(null);
    // Sorted list of items (items passed through sortItems function)
    let sortedItems = $derived(
        sortItems(items, currSortKey, sortAscending ? 'asc' : 'desc')
    );
    // Array of items currently visible in virtual window
    let visibleItems = $state<Record<any, any>[]>([]);

    // Main sorting function for table
    function sortItems<T extends Record<string, any>>(
        array: T[],
        sortKey: keyof T | null | undefined,
        sortDirection: 'asc' | 'desc'
    ) {
        if (!sortKey) return array;

        // Multiplier based on sort direction
        const direction = sortDirection == 'asc' ? 1 : -1;

        const sorted = [...array].sort((a, b) => {
            const A = a[sortKey];
            const B = b[sortKey];

            let result = 0;

            // Put nulls at end
            if (A == null && B == null) result = 0;
            else if (B == null) result = 1;
            else if (A == null) result = -1;
            // Numeric sort
            else if (typeof A === 'number' && typeof B === 'number') {
                result = A - B;
            }

            // String sort
            else if (typeof A === 'string' && typeof B === 'string') {
                result = A.localeCompare(B);
            }

            // Fallback: compare as strings
            else result = String(A).localeCompare(String(B));

            return result * direction;
        });

        return sorted;
    }

    let start = $state(0);
    let end = $state(0);

    let columnCount = $derived(headers.length);
    let columnWidths = $state<string[]>([]);
    let gridTemplateColumns = $derived<string>(
        columnWidths.length
            ? columnWidths.join(' ')
            : 'auto '.repeat(columnCount).trim()
    );

    // Update elements currently visible in virtual table
    function updateVisible() {
        if (!container) return;

        const scrollTop = container.scrollTop;
        const containerHeight = container.clientHeight;

        const perView = Math.ceil(containerHeight / rowHeight);
        start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
        // Using sortedItems is theoretically safer here
        end = Math.min(sortedItems.length, start + perView + overscan * 2);

        visibleItems = sortedItems.slice(start, end);
    }

    // Sort sort button click, assigning sort key and direction
    function handleSortClick(e: MouseEvent) {
        const target = e.target as HTMLElement;
        const sortKey = target?.dataset?.sortKey;
        if (!sortKey) return;

        // If clicking on already selected column, flip order
        if (currSortKey === sortKey) {
            sortAscending = !sortAscending;
            // Else if clicking on new column, set to ascending
        } else {
            sortAscending = true;
        }

        currSortKey = sortKey;

        if (onSort) {
            onSort(sortKey, sortAscending);
        }
    }

    // Handle user resizing table columns
    function resizeColumn(e: PointerEvent) {
        const target = e.target as HTMLElement;
        const targetIndex = target?.dataset?.columnIndex;
        if (targetIndex == null) return;

        let startX = e.clientX;
        let startWidth = target.parentElement!.offsetWidth;

        target.setPointerCapture(e.pointerId);

        function resizeColumn(e: PointerEvent) {
            const dx = e.clientX - startX;
            const newWidth = Math.max(startWidth + dx, 10);
            columnWidths[Number(targetIndex)] = `${newWidth}px`;
        }
        function stopResize() {
            window.removeEventListener('pointermove', resizeColumn);
            window.removeEventListener('pointerup', stopResize);
            window.removeEventListener('pointercancel', stopResize);
        }
        window.addEventListener('pointermove', resizeColumn);
        window.addEventListener('pointerup', stopResize);
        window.addEventListener('pointercancel', stopResize);
    }

    // Attempt to determine reasonable column widths given headers and first row
    // To be used onMount
    async function measureColumnWidths() {
        // Wait for DOM update
        await tick();

        const headerRow = container?.parentElement?.querySelector(
            '.virtualized-table-headers'
        );
        // Grab first row in table
        const firstRow = container?.querySelector('.row');

        if (!headerRow && !firstRow) return;

        // Grab values from headers and first row
        const headerCells = headerRow ? Array.from(headerRow.children) : [];
        const rowCells = firstRow ? Array.from(firstRow.children) : [];

        // Determine number of columns
        const colCount = Math.max(headerCells.length, rowCells.length);

        const widths: string[] = [];
        // Determine max width for each column
        for (let i = 0; i < colCount; i++) {
            let w = 0;
            if (headerCells[i]) {
                w = Math.max(w, headerCells[i].getBoundingClientRect().width);
            }
            if (rowCells[i]) {
                w = Math.max(w, rowCells[i].getBoundingClientRect().width);
            }
            // Push max width for each column as pixel value
            widths.push(`${w}px`);
        }

        // Push these values to columnWidths state
        columnWidths = widths;
    }

    // Scroll virtual list to provided item[indexCol] == scrollToID
    function handleScrollToID() {
        if (!indexCol || !scrollToID || !container) return;

        // If we're already on it, skip it
        if (scrollToItemIndex === scrollToID) return;

        // Find index of active item
        untrack(() => {
            const itemIndex = sortedItems.findIndex((item) => {
                return item[indexCol] == scrollToID;
            });

            // If not found in current list, do nothing
            if (itemIndex === -1) return;

            const position = rowHeight * itemIndex;

            const scrollTop = container.scrollTop;
            const containerHeight = container.clientHeight;

            // If item is already within view, do nothing
            if (position > scrollTop && position < scrollTop + containerHeight)
                return;

            container.scrollTo({ top: Math.max(position - 500, 0) });
            // Else, scroll to active item, placing it at the top of the table
            // Smooth scrolling is jarring with long lists, but it's not the worst thing
            requestAnimationFrame(() => {
                container.scrollTo({ top: position + 8, behavior: 'smooth' });
            });
            scrollToItemIndex = itemIndex;
        });
    }

    // Handle functionality of scrolling the visible window
    function handleVirtualScroll() {
        // Sync header x-axis scroll (if there's a header provided)
        if (header && container) {
            header.scrollLeft = container.scrollLeft;
        }
        // Update visible items
        updateVisible();
    }

    // On mount, update visible items and determine initial column widths
    onMount(() => {
        updateVisible();

        // After creating visible list, determine column widths
        tick().then(() => {
            measureColumnWidths();
        });
    });

    // Update visible rows on any change
    $effect(() => {
        updateVisible();
    });

    $effect(() => {
        if (scrollToID) {
            handleScrollToID();
        }
    });
</script>

<div class="virtual-table-wrapper">
    <div class="x-scroller">
        {#if !hideHeader}
            <div
                class="virtualized-table-headers"
                style:grid-template-columns={gridTemplateColumns}
                bind:this={header}
            >
                {#each headers as header, i (i)}
                    <div
                        class="column-header-wrapper"
                        role="columnheader"
                        aria-sort={header.sortKey
                            ? currSortKey === header.sortKey
                                ? sortAscending
                                    ? 'ascending'
                                    : 'descending'
                                : 'none'
                            : undefined}
                    >
                        <button
                            class="column-header"
                            class:active={currSortKey === header.sortKey}
                            style:cursor={header.sortKey ? 'pointer' : 'auto'}
                            data-sort-key={header.sortKey || null}
                            onclick={handleSortClick}
                        >
                            <div class="header-label-wrapper">
                                <div class="header-label">
                                    {#if typeof header.label === 'string'}
                                        {header.label}
                                    {:else}
                                        {@render header.label()}
                                    {/if}
                                </div>
                                {#if header.info}
                                    <div class="header-info">
                                        <InfoButton type="tooltip" hover={true}>
                                            <div>{header.info}</div>
                                        </InfoButton>
                                    </div>
                                {/if}
                            </div>
                            {#if currSortKey === header.sortKey}
                                <div class="sort-arrow icon">
                                    {#if sortAscending}
                                        <ArrowDown />
                                    {:else}
                                        <ArrowUp />
                                    {/if}
                                </div>
                            {/if}
                        </button>
                        <button
                            data-column-index={i}
                            onpointerdown={resizeColumn}
                            class="resize-handle"
                            aria-label="Resize handle"
                        >
                        </button>
                    </div>
                {/each}
            </div>
        {/if}
        <div
            class="virtual-table"
            bind:this={container}
            onscroll={handleVirtualScroll}
        >
            <div
                class="spacer"
                style:height="{sortedItems.length * rowHeight}px"
            >
                <div class="visible-window" style:top="{start * rowHeight}px">
                    {#each visibleItems as item, i}
                        <div
                            class="row"
                            style:height={`${rowHeight}px`}
                            style:grid-template-columns={gridTemplateColumns}
                        >
                            {@render row(item, i)}
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .column-header.active {
        background-color: var(--container-fore);
    }
    .header-info {
        flex-shrink: 0;
        pointer-events: auto;
    }
    .resize-handle {
        position: absolute;
        width: 20px;
        height: 100%;
        top: 0;
        right: -10px;
        background-color: unset;
        z-index: 100;
        opacity: 0.5;
        margin: unset;
        padding: unset;
        border: unset;
        box-sizing: border-box;
    }
    .resize-handle:hover {
        background-color: var(--container-fore);
        cursor: ew-resize;
    }
    .resize-handle:active {
        cursor: grabbing;
    }
    .header-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        user-select: none;
    }
    .header-label-wrapper {
        overflow: hidden;
        white-space: nowrap;
        display: flex;
        pointer-events: none;
    }
    .sort-arrow {
        height: 1rem;
        width: 1rem;
        margin-left: 0.5rem;
        flex-shrink: 0;
        user-select: none;
        color: var(--fill-color);
    }
    .x-scroller {
        overflow-y: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .virtual-table-wrapper {
        height: 100%;
        position: relative;
        display: flex;
        flex-direction: column;
    }
    .virtual-table {
        position: relative;
        overflow-y: auto;
        height: 100%;
        width: 100%;
        min-width: max-content;
        box-sizing: border-box;
    }
    .virtualized-table-headers {
        display: grid;
        background-color: var(--container-highlight);
        border-bottom: 1px solid var(--container-shadow);
        justify-content: start;
        width: 100%;
        overflow-x: hidden;
        flex-shrink: 0;
        box-sizing: border-box;
        height: fit-content;
    }
    button.column-header {
        margin: unset;
        background-color: unset;
        border-radius: unset;
        color: unset;
    }
    .column-header-wrapper {
        position: relative;
        /* height: 100%; */
        width: 100%;
        box-sizing: border-box;
        border-right: 1px solid var(--container-shadow);
    }
    .column-header {
        display: flex;
        text-align: left;
        font-weight: 600;
        justify-content: space-between;
        box-sizing: border-box;
        align-items: center;
        width: 100%;
        height: 3rem;
        align-items: flex-end;
    }
    .column-header:focus {
        outline: none;
    }
    .column-header:hover {
        background-color: var(--container-fore);
    }
    .header-label,
    .sort-arrow {
        pointer-events: none;
    }
    .column-header:active {
        background-color: var(--container-fore);
    }
    .column-header {
        border: unset;
    }
    .row {
        display: grid;
        text-align: left;
        text-wrap: nowrap;
    }
    :global(.row > *) {
        padding: 0 0.5rem;
        overflow: hidden;
        text-overflow: ellipsis;
        align-self: center;
    }
    .spacer {
        position: relative;
        min-width: max-content;
    }
    .visible-window {
        position: absolute;
        overflow-x: visible;
        left: 0;
    }
    .row:first-child {
        padding-top: 0.5rem;
    }
    .row:last-child {
        padding-bottom: 0.5rem;
    }
</style>
