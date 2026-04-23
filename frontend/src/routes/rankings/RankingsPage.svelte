<script lang="ts">
    import {
        getActiveTaxaContext,
        initialTaxonState,
    } from '../../contexts/activeTaxaContext';
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
    import { openModal } from '../../lib/modal.svelte';

    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();
    const modalContext = getModalContext();
    const rankingsContext = getRankingsContext();

    // All taxa return from current filters, to be shown in list
    let filteredTaxaNodes: TaxonNodeType[] = $state([]);

    const ranksLoading: boolean = $derived(
        rankingsContext.ranksLoading || !$taxaTree
    );

    // Define headers/sort-keys for virtualized rankings table
    const tableHeaders = $derived([
        {
            label: iNatLabel,
            info: 'The rankings in this column are precalculated using a 4km2 grid cell. Aside from toggling iNaturalist data, they do not respond to further filtering, and instead reflect all available data.',
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

        const targetInt = parseInt(targetID);

        // If taxon is already selected, deselect it
        if (taxaContext.taxa.ids.includes(targetInt)) {
            taxaContext.taxa.remove(targetInt);
            // Otherwise, select it
        } else {
            taxaContext.taxa.add({
                ...initialTaxonState,
                taxonID: targetInt,
            });
        }
    }

    // Active taxon id to scroll table to (has to be species or subspecies id)
    let scrollToTaxonID: number | undefined | null = $state();

    // Filter taxa to currently active taxa
    $effect(() => {
        // If taxaTree isn't loaded, end
        if (!$taxaTree) {
            return;
        }

        // Get list of qualified taxa from data/region filtering
        const qualifiedTaxonIDs = rankingsContext.qualifiedTaxonIDs;

        // If there are no qualified taxa, show nothing
        if (qualifiedTaxonIDs && !qualifiedTaxonIDs.length) {
            filteredTaxaNodes = [];
            return;
        }

        // List of taxonIDs to filter list to
        let filterTaxaIDs;
        scrollToTaxonID = null;

        // Behavior for
        switch (taxaContext.taxa.ids.length) {
            // If no active taxonIDs, filter to Animalia
            case 0:
                filterTaxaIDs = [1];
                break;
            // If only one active taxonID
            case 1: {
                // If taxon is species or subspecies, skip filtering but scroll to taxon
                const taxon = $taxaTree.get(taxaContext.taxa.ids[0]);
                if (
                    !taxon ||
                    ['species', 'subspecies'].includes(taxon.taxon_rank)
                ) {
                    filterTaxaIDs = [1];
                    scrollToTaxonID = taxon?.taxon_id;
                    break;
                }
                // Else, filter to taxa
                filterTaxaIDs = [taxon.taxon_id];
                break;
            }
            // If more than one active taxonID
            default: {
                // If they're all species or subspecies, skip filtering
                if (
                    taxaContext.taxa.ids.every((taxonID) => {
                        return ['species', 'subspecies', null].includes(
                            taxaContext?.taxa.get(taxonID)?.info?.taxonRank ||
                                null
                        );
                    })
                ) {
                    filterTaxaIDs = [1];
                    scrollToTaxonID = taxaContext.taxa.ids.slice(-1)[0];
                    break;
                }
                // Else, filter to taxa
                filterTaxaIDs = taxaContext.taxa.ids;
                // If any taxa are species/subspecies, scroll to latest (last in list)
                for (const taxonID of taxaContext.taxa.ids) {
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

        // Get new taxa nodes from filtereMap (only species)
        let newTaxa = Array.from(filteredMap.values()).filter((taxonNode) =>
            ['species'].includes(taxonNode.taxon_rank)
        );

        // Filter to activeRanks
        if (activeRanks?.length) {
            newTaxa = newTaxa.filter((taxonNode) =>
                activeRanks.includes(taxonNode[relevantRank])
            );
        }

        // Filter to taxa retrieved using date/region filters
        if (qualifiedTaxonIDs) {
            const qualifiedSet = new Set(qualifiedTaxonIDs);
            newTaxa = newTaxa.filter((taxonNode) =>
                qualifiedSet.has(taxonNode.taxon_id)
            );
        }

        filteredTaxaNodes = newTaxa;

        // Send ids to context to have a running list of table taxa
        rankingsContext.visibleTaxonIDs = newTaxa.map(
            (taxon) => taxon.taxon_id
        );
    });

    function handleDownloadButton() {
        openModal(modalContext, downloadTaxaForm);
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

{#snippet downloadTaxaForm()}
    <DownloadTaxaForm />
{/snippet}

{#snippet iNatLabel()}
    {#if filtersContext.includeINat}
        <span>Raw Rank</span>
    {:else}
        <div id="rank-header-no-inat">
            <span>Raw Rank</span>
            <span id="no-inat-tag"> Excl. iNat </span>
        </div>
    {/if}
{/snippet}

<DefaultPage showSidebar={true}>
    <div id="rankings-page-body">
        <div class="virtual-list-wrapper" class:loading-blink={ranksLoading}>
            {#if ranksLoading}
                <div class="icon rankings-loading">
                    <LoadingIcon />
                </div>
            {:else if !filteredTaxaNodes.length}
                <div class="no-species-error">
                    No valid rankings found for selected taxon
                </div>
            {:else if filteredTaxaNodes.length}
                <VirtualizedTable
                    items={[...filteredTaxaNodes]}
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
                        {@const taxonID = taxon.taxon_id}
                        {@const activeTaxa = taxaContext.taxa}
                        {@const activeTaxaIDs = taxaContext.taxa.ids}
                        {@const nextColor = taxaContext.getNextColor()}
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
                                class="taxon-select-icon icon"
                                class:active={activeTaxaIDs.some(
                                    (activeID) => activeID == taxonID
                                )}
                                style:color={activeTaxa.get(taxonID)
                                    ? activeTaxa.get(taxonID)?.color
                                    : nextColor}
                                onclick={handleTaxonSelect}
                                data-taxon-id={taxonID.toString()}
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
    #rank-header-no-inat {
        display: flex;
        flex-direction: column;
        font-size: 0.9rem;
    }
    #no-inat-tag {
        font-size: 0.75rem;
        font-style: italic;
        font-weight: 500;
    }
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
    .centered {
        text-align: center;
        justify-self: center;
    }
    .taxon-icon-wrapper {
        color: var(--accent-color);
    }
    .taxon-name-wrapper {
        text-align: left;
        flex-grow: 1;
        display: flex;
        justify-content: space-between;
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
    .invasive > * {
        color: var(--accent-color);
    }
    .taxon-select-icon {
        color: transparent;
        background: transparent;
        padding: 0rem;
        margin-left: 0.5rem;
        flex-shrink: 0;
        visibility: hidden;
    }
    .taxon-name-wrapper:hover .taxon-select-icon,
    .taxon-select-icon.active {
        visibility: visible;
    }
    .taxon-name {
        text-overflow: ellipsis;
        overflow: hidden;
    }
    .taxon-authorship {
        font-weight: 200;
    }
</style>
