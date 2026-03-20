<script lang="ts">
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';
    import { taxaTree } from '../../contexts/TaxaTree';
    import { type TaxonNodeType } from '../../types/api';
    import { isItalicizedRank } from '../../util/taxa';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import NSCircle from '../../common/NSCircle.svelte';
    import MagnifyIcon from '../../assets/MagnifyIcon.svelte';
    import { getAllChildrenNodes } from '../../util/taxonNodes';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DefaultPage from '../../common/DefaultPage.svelte';
    import VirtualizedTable from '../../common/VirtualizedTable.svelte';
    import DownloadIcon from '../../assets/DownloadIcon.svelte';
    import { getModalContext } from '../../contexts/modalContext';
    import DownloadTaxaForm from '../../components/DownloadTaxaForm.svelte';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';
    import { getRankingsContext } from '../../contexts/rankingsContext';

    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();
    const modalContext = getModalContext();
    const rankingsContext = getRankingsContext();

    // All taxa return from current filters, to be shown in list
    let filteredTaxa: TaxonNodeType[] = $state([]);

    // Define headers/sort-keys for virtualized rankings table
    const tableHeaders = $derived([
        {
            label: `${filtersContext.includeINat ? 'Rank' : 'Rank (no iNat)'}`,
            info: 'The rankings in this column are precalculated using a 4km2 grid cell. Aside from toggling iNaturalist data, they will not respond to further filtering.',
            sortKey: filtersContext.includeINat
                ? 'ns_rank_state'
                : 'ns_rank_state_no_inat',
        },
        { label: 'Name', sortKey: 'canonical_name' },
        { label: 'Class', sortKey: 'class' },
        { label: 'Order', sortKey: 'order' },
        { label: 'Family', sortKey: 'family' },
        { label: 'Genus', sortKey: 'genus' },
        // { label: 'Taxon Rank', sortKey: 'taxon_rank' },
    ]);

    function handleTaxonSelect(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;
        const targetID = target.dataset.taxonId;

        if (!targetID || !parseInt(targetID)) return;

        taxaContext.add(parseInt(targetID));
    }

    // Active taxon id to scroll table to (has to be species or subspecies id)
    let scrollToTaxonID: number | undefined | null = $state();

    // Filter taxa to currently active taxa
    $effect(() => {
        // If taxaTree isn't loaded, end
        if (!$taxaTree) {
            return;
        }

        // List of taxonIDs to filter list to
        let filterTaxaIDs;

        // Behavior for
        switch (taxaContext.taxonIDs.length) {
            // If no active taxonIDs, filter to Animalia
            case 0:
                filterTaxaIDs = [1];
                scrollToTaxonID = null;
                break;
            // If only one active taxonID
            case 1: {
                // If taxon is species or subspecies, skip filtering but scroll to taxon
                const taxon = $taxaTree.get(taxaContext.taxonIDs[0]);
                if (
                    !taxon ||
                    ['species', 'subspecies'].includes(taxon.taxon_rank)
                ) {
                    filterTaxaIDs = [1];
                    scrollToTaxonID = taxon?.taxon_id;
                    break;
                }
                // Else filter to taxon
                else {
                    filterTaxaIDs = [taxon.taxon_id];
                    break;
                }
            }
            // If more than one active taxonID, filter to taxa
            default: {
                filterTaxaIDs = taxaContext.taxonIDs;
                scrollToTaxonID = null;
                // If any taxa are species/subspecies, scroll to latest (last in list)
                for (const taxonID of taxaContext.taxonIDs) {
                    const taxonRank = $taxaTree.get(taxonID)?.taxon_rank;
                    if (
                        taxonRank &&
                        ['species', 'subspecies'].includes(taxonRank)
                    ) {
                        scrollToTaxonID = taxonID;
                    }
                }
            }
        }

        let activeRanks = filtersContext.nSRanks;

        // Determine which rank we need (for filtering)
        const relevantRank: Partial<keyof TaxonNodeType> =
            filtersContext.includeINat
                ? 'ns_rank_state'
                : 'ns_rank_state_no_inat';

        const filteredMap = new Map<number, TaxonNodeType>();

        for (const taxonID of filterTaxaIDs.map(Number)) {
            const parentNode = $taxaTree.get(taxonID);

            if (!parentNode) continue;

            filteredMap.set(parentNode.taxon_id, parentNode);

            const children = getAllChildrenNodes($taxaTree, taxonID);
            for (const child of children) {
                filteredMap.set(child.taxon_id, child);
            }
        }

        let newTaxa = Array.from(filteredMap.values()).filter((taxonNode) =>
            ['species'].includes(taxonNode.taxon_rank)
        );

        if (activeRanks?.length) {
            newTaxa = newTaxa.filter((taxonNode) =>
                activeRanks.includes(taxonNode[relevantRank])
            );
        }

        filteredTaxa = newTaxa;
    });

    function handleDownloadButton() {
        modalContext.visible = true;
        modalContext.content = DownloadTaxaForm;
    }

    // Handle sort form virtualized table (preserving sort across pages)
    function handleSort(sortKey: string | null | undefined, asc: boolean) {
        if (sortKey) {
            rankingsContext.currSortKey = sortKey;
            rankingsContext.sortAscending = asc;
        } else {
            rankingsContext.currSortKey = null;
            rankingsContext.sortAscending = null;
        }
    }
</script>

<DefaultPage showSidebar={true}>
    <div id="rankings-page-body">
        <div class="virtual-list-wrapper">
            {#if !$taxaTree}
                <div class="icon rankings-loading">
                    <LoadingIcon />
                </div>
            {:else if !filteredTaxa.length}
                <div class="no-species-error">
                    No valid rankings found for selected taxon
                </div>
            {:else if filteredTaxa.length}
                <VirtualizedTable
                    items={[...filteredTaxa]}
                    rowHeight={30}
                    headers={tableHeaders}
                    scrollToID={scrollToTaxonID}
                    indexCol={'taxon_id'}
                    onSort={handleSort}
                    defaultSortKey={rankingsContext.currSortKey ||
                        'canonical_name'}
                    defaultAscending={rankingsContext.sortAscending}
                >
                    {#snippet row(taxon: TaxonNodeType)}
                        {@const nsRank =
                            filtersContext.includeINat !== false
                                ? taxon.ns_rank_state
                                : taxon.ns_rank_state_no_inat}
                        {@const italicized = isItalicizedRank(taxon.taxon_rank)}
                        <div class="taxon-icon-wrapper centered">
                            {#if taxon.us_invasive}
                                <div class="invasive-icon taxon-icon icon">
                                    <InvasiveIcon />
                                </div>
                            {:else if taxon.ns_rank_state}
                                <div class="rank-circle taxon-icon icon">
                                    <NSCircle
                                        active={true}
                                        rank={nsRank}
                                        level="s"
                                    />
                                </div>
                            {/if}
                        </div>
                        <div
                            class={[
                                'taxon-name-wrapper',
                                { invasive: taxon.us_invasive },
                                'left-align',
                            ]}
                        >
                            <span class="taxon-name">
                                <span class={[{ italicized }]}>
                                    {taxon.canonical_name}
                                </span>
                                <span class="taxon-authorship"
                                    >{taxon.scientific_name_authorship ?? null}
                                </span>
                            </span>
                            <button
                                class={`
                                    taxon-select-icon 
                                    icon 
                                    ${
                                        taxaContext.taxonIDs.some(
                                            (taxonID) =>
                                                taxonID == taxon.taxon_id
                                        )
                                            ? 'active'
                                            : null
                                    }
                                `}
                                onclick={handleTaxonSelect}
                                data-taxon-id={taxon.taxon_id.toString()}
                            >
                                <MagnifyIcon />
                            </button>
                        </div>
                        <div class="row-text">
                            {taxon.class}
                        </div>
                        <div class="row-text">
                            {taxon.order}
                        </div>
                        <div class="row-text">
                            {taxon.family}
                        </div>
                        <div class="taxon-rank-label">
                            {taxon.genus}
                        </div>
                    {/snippet}
                </VirtualizedTable>
                <button
                    id="download-rankings-button"
                    onclick={handleDownloadButton}
                >
                    <DownloadIcon />
                </button>
            {/if}
        </div>
    </div>
</DefaultPage>

<style>
    .row-text {
        display: flex;
        /* align-items: center; */
    }
    #rankings-page-body:hover #download-rankings-button {
        opacity: 0.6;
    }
    .rankings-loading {
        margin: 0.5rem;
    }
    #download-rankings-button {
        height: 2.5rem;
        position: absolute;
        right: 5px;
        bottom: 5px;
        opacity: 0.4;
        transition: opacity ease-in-out 0.1s;
    }
    #download-rankings-button:hover {
        opacity: 1 !important;
    }
    .no-species-error {
        margin: 1rem;
        opacity: 0.5;
    }
    .taxon-column-name {
        cursor: pointer;
    }
    .centered {
        text-align: center;
        justify-self: center;
    }
    .rankings-body-grid {
        padding: 0.5rem;
        width: fit-content;
    }
    .taxon-icon-wrapper {
        color: var(--accent-color);
    }
    .taxon-name-wrapper {
        text-align: left;
        flex-grow: 1;
        display: flex;
        justify-content: start;
        align-items: center;
    }
    .virtual-list-wrapper {
        height: 100%;
        width: 100%;
        position: relative;
    }
    #rankings-page-body {
        height: 100%;
        flex-grow: 1;
        background-color: var(--container-mid);
        border-radius: 3px;
        transition: all 0.1 ease-in-out;
        box-sizing: border-box;
        color: var(--text-default);
        overflow-y: hidden;
    }
    .taxon-label {
        height: 1.5rem;
        display: flex;
        gap: 0.5rem;
    }
    .invasive > * {
        color: var(--accent-color);
    }
    .filler-row {
        height: 1.5rem;
    }
    .taxon-select-icon {
        color: transparent;
        background: transparent;
        padding: 0.25rem;
        flex-shrink: 0;
    }
    .taxon-name-wrapper:hover .taxon-select-icon,
    .taxon-select-icon.active {
        color: var(--fill-color);
    }
    .taxon-name {
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .spacer-row {
        height: 1rem;
    }
    .taxon-authorship {
        font-weight: 200;
    }
    .taxon-label {
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
    .taxon-label.active {
        font-weight: bold;
    }
    .taxon-label-left {
        line-height: 2rem;
        padding-right: 1rem;
        display: flex;
        align-items: center;
        width: 100%;
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
</style>
