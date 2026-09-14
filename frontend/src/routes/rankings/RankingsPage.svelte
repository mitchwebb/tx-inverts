<script lang="ts">
    import {
        getActiveTaxaContext,
        initialTaxonState,
    } from '../../contexts/activeTaxaContext';
    import { taxaTree } from '../../contexts/TaxaTree';
    import { type TaxonInfo } from '../../types/api';
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
    import NameAndAuthorship from '../../common/NameAndAuthorship.svelte';
    import type { Snippet } from 'svelte';

    const taxaContext = getActiveTaxaContext();
    const filtersContext = getFiltersContext();
    const modalContext = getModalContext();
    const rankingsContext = getRankingsContext();

    // All taxa return from current filters, to be shown in list
    let filteredTaxaNodes: TaxonInfo[] = $state([]);

    const ranksLoading: boolean = $derived(
        rankingsContext.ranksLoading || !$taxaTree
    );

    type TableHeaderType = {
        label: string | Snippet;
        info?: string;
        sortKey: keyof TaxonInfo;
    };

    // Define headers/sort-keys for virtualized rankings table
    const tableHeaders: TableHeaderType[] = $derived([
        {
            label: iNatLabel,
            info: 'The rankings in this column use a 4km² grid cell, minimum collection year of 1800, and maximum 1000m uncertainty radius. Aside from toggling iNaturalist data, they do not respond to further filtering.',
            sortKey: filtersContext.includeINat
                ? 'nSRankState'
                : 'nSRankStateNoINat',
        },
        { label: 'Name', sortKey: 'canonicalName' },
        { label: 'Class', sortKey: 'class' },
        { label: 'Order', sortKey: 'order' },
        { label: 'Family', sortKey: 'family' },
        { label: 'Genus', sortKey: 'genericName' },
    ]);

    function handleTaxonSelect(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;
        const targetID = target.dataset.taxonId;

        if (!targetID) return;

        const targetInt = targetID;

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
    let scrollToTaxonID: string | undefined | null = $state();

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
                filterTaxaIDs = ['N'];
                break;
            // If only one active taxonID
            case 1: {
                // If taxon is species or subspecies, skip filtering but scroll to taxon
                const taxon = $taxaTree.get(taxaContext.taxa.ids[0]);
                if (
                    !taxon ||
                    ['species', 'subspecies'].includes(taxon.taxonRank || '')
                ) {
                    filterTaxaIDs = ['N'];
                    scrollToTaxonID = taxon?.taxonID;
                    break;
                }
                // Else, filter to taxa
                filterTaxaIDs = [taxon.taxonID];
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
                    filterTaxaIDs = ['N'];
                    scrollToTaxonID = taxaContext.taxa.ids.slice(-1)[0];
                    break;
                }
                // Else, filter to taxa
                filterTaxaIDs = taxaContext.taxa.ids;
                // If any taxa are species/subspecies, scroll to latest (last in list)
                for (const taxonID of taxaContext.taxa.ids) {
                    const taxonRank = $taxaTree.get(taxonID)?.taxonRank;
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
        const relevantRank: Partial<keyof TaxonInfo> =
            filtersContext.includeINat ? 'nSRankState' : 'nSRankStateNoINat';

        const filteredMap = new Map<string, TaxonInfo>();

        for (const taxonID of filterTaxaIDs.map(String)) {
            const parentNode = $taxaTree.get(taxonID);

            if (!parentNode) continue;

            filteredMap.set(parentNode.taxonID, parentNode);

            const children = getAllChildrenNodes($taxaTree, taxonID);
            for (const child of children) {
                filteredMap.set(child.taxonID, child);
            }
        }

        // Get new taxa nodes from filteredMap (only species)
        let newTaxa = Array.from(filteredMap.values()).filter(
            (taxonNode) => taxonNode.taxonRank === 'species'
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
                qualifiedSet.has(taxonNode.taxonID)
            );
        }

        filteredTaxaNodes = newTaxa;

        // Send ids to context to have a running list of table taxa
        rankingsContext.visibleTaxonIDs = newTaxa.map((taxon) => taxon.taxonID);
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
                    No valid species found for active filters
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
                        'canonicalName'}
                    defaultAscending={rankingsContext.sortAscending}
                >
                    {#snippet row(taxon: TaxonInfo)}
                        {@const nSRank =
                            filtersContext.includeINat !== false
                                ? taxon.nSRankState
                                : taxon.nSRankStateNoINat}
                        {@const taxonID = taxon.taxonID}
                        {@const activeTaxa = taxaContext.taxa}
                        {@const activeTaxaIDs = taxaContext.taxa.ids}
                        {@const nextColor = taxaContext.getNextColor()}
                        <div class="taxon-icon-wrapper centered">
                            {#if taxon.uSInvasive}
                                <div class="invasive-icon taxon-icon icon">
                                    <InvasiveIcon />
                                </div>
                            {:else if taxon.nSRankState}
                                <div class="rank-circle taxon-icon icon">
                                    <NSCircle
                                        active={true}
                                        rank={nSRank}
                                        level="s"
                                    />
                                </div>
                            {/if}
                        </div>
                        <div
                            class="taxon-name-wrapper left-align"
                            class:invasive-taxon={taxon.uSInvasive}
                            class:dubious-taxon={taxon.taxonomicStatus !==
                                'accepted'}
                        >
                            <div class="name-and-authorship">
                                <NameAndAuthorship info={taxon} />
                            </div>

                            <button
                                class="taxon-select-icon icon"
                                class:active={activeTaxaIDs.some(
                                    (activeID) => activeID == taxonID
                                )}
                                style:color={activeTaxa.get(taxonID)
                                    ? activeTaxa.get(taxonID)?.color
                                    : nextColor}
                                onclick={handleTaxonSelect}
                                data-taxon-id={taxonID}
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
                            {taxon.genericName}
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
    .name-and-authorship {
        overflow: clip;
        flex-grow: 0;
        min-width: 0;
        text-overflow: ellipsis;
    }
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
        text-align: left;
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
    /* Never hide icons when on mobile device */
    @media (hover: none) {
        .taxon-select-icon {
            visibility: visible;
        }
        /* Force a default color for mobile device icon */
        .taxon-select-icon:not(.active) {
            color: var(--text-default) !important;
            opacity: 0.25;
        }
    }
</style>
