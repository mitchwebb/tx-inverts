<script lang="ts">
    import { getActiveTaxonContext } from '../../contexts/activeTaxonContext';
    import { taxaTree } from '../../contexts/TaxaTree';
    import { type TaxonNodeType } from '../../types/api';
    import { isItalicizedRank } from '../../util/taxa';
    import InvasiveIcon from '../../common/InvasiveIcon.svelte';
    import NSCircle from '../../common/NSCircle.svelte';
    import MagnifyIcon from '../../assets/MagnifyIcon.svelte';
    import { getAllChildrenNodes } from '../../util/taxonNodes';
    import { capitalizeWords } from '../../util/textHelpers';
    import { getFiltersContext } from '../../contexts/filtersContext';
    import DefaultPage from '../../common/DefaultPage.svelte';
    import VirtualizedTable from '../../common/VirtualizedTable.svelte';

    const taxonContext = getActiveTaxonContext();
    const filtersContext = getFiltersContext();

    let filteredTaxa: TaxonNodeType[] = $state([]);

    // Define headers/sort-keys for virtualized rankings table
    const tableHeaders = $derived([
        {
            label: 'Rank',
            sortKey: filtersContext.includeINat
                ? 'ns_rank_state'
                : 'ns_rank_state_no_inat',
        },
        { label: 'Name', sortKey: 'canonical_name' },
        { label: 'Class', sortKey: 'class' },
        { label: 'Order', sortKey: 'order' },
        { label: 'Family', sortKey: 'family' },
        { label: 'Taxon Rank', sortKey: 'taxon_rank' },
    ]);

    function setActiveTaxon(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;

        const targetID = target.dataset.taxonId;

        if (!targetID || !parseInt(targetID)) return;

        taxonContext.taxonID = parseInt(targetID);
    }

    // Filter taxa by filteredTaxonID
    $effect(() => {
        let filterID = filtersContext.filteredTaxonID || 1; // Filter to Animalia if no active filter
        if ($taxaTree && filterID) {
            const childrenTaxa = getAllChildrenNodes($taxaTree, filterID);
            const parentNode = $taxaTree.find(
                (node) => node.taxon_id === filterID
            );

            // If filteredTaxonID is explicitly set, grab the canonicalName here
            if (filtersContext.filteredTaxonID && parentNode) {
                filtersContext.filteredCanonicalName =
                    parentNode.canonical_name;
            } else {
                filtersContext.filteredCanonicalName = null;
            }

            let activeRanks = filtersContext.nSRanks;

            let newTaxa = [
                ...(parentNode ? [parentNode] : []), // include parent first
                ...childrenTaxa,
            ].filter((taxonNode) => ['species'].includes(taxonNode.taxon_rank)); // Filter to just species TODO: maybe subspecies?

            // Determine which rank we need (for filtering)
            const relevantRank: Partial<keyof TaxonNodeType> =
                filtersContext.includeINat
                    ? 'ns_rank_state'
                    : 'ns_rank_state_no_inat';

            // Filter by selected ranks
            if (activeRanks?.length) {
                newTaxa = newTaxa.filter((taxonNode) =>
                    activeRanks.includes(taxonNode[relevantRank])
                );
            }

            filteredTaxa = newTaxa;
        }
    });
</script>

<DefaultPage showSidebar={true}>
    <div id="rankings-page-body">
        <div class="virtual-list-wrapper">
            {#if filteredTaxa.length}
                <VirtualizedTable
                    items={[...filteredTaxa]}
                    rowHeight={30}
                    headers={tableHeaders}
                    activeValue={taxonContext.taxonID}
                    indexCol={'taxon_id'}
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
                                        level="S"
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
                                        taxonContext.taxonID == taxon.taxon_id
                                            ? 'active'
                                            : null
                                    }
                                `}
                                onclick={setActiveTaxon}
                                data-taxon-id={taxon.taxon_id.toString()}
                            >
                                <MagnifyIcon />
                            </button>
                        </div>
                        <div class="taxon-rank-label">
                            {taxon.class}
                        </div>
                        <div class="taxon-rank-label">
                            {taxon.order}
                        </div>
                        <div class="taxon-rank-label">
                            {taxon.family}
                        </div>
                        <div class="taxon-rank-label">
                            {capitalizeWords(taxon.taxon_rank)}
                        </div>
                    {/snippet}
                </VirtualizedTable>
            {:else}
                <div class="no-species-error">
                    No valid rankings found for selected taxon
                </div>
            {/if}
        </div>
    </div>
</DefaultPage>

<style>
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
        color: goldenrod;
        /* display: flex;
        justify-content: center; */
    }
    .taxon-name-wrapper {
        text-align: left;
        flex-grow: 1;
        display: flex;
        justify-content: start;
    }
    .virtual-list-wrapper {
        height: 100%;
        width: 100%;
    }
    #rankings-page-body {
        height: 100%;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        background-color: var(--container-back);
        border-radius: 3px;
        justify-content: baseline;
        border: 1px solid var(--border);
        box-shadow: inset 0px 1px 10px var(--container-shadow);
        transition: all 0.1 ease-in-out;
        box-sizing: border-box;
        gap: 0.25rem;
        color: var(--text-default);
        overflow-y: hidden;
    }
    .taxon-label {
        height: 1.5rem;
        display: flex;
        gap: 0.5rem;
    }
    .invasive > * {
        color: goldenrod;
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
