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
    import DownloadIcon from '../../assets/DownloadIcon.svelte';
    import { getModalContext } from '../../contexts/modalContext';
    import DownloadTaxaForm from '../../components/DownloadTaxaForm.svelte';
    import LoadingIcon from '../../assets/LoadingIcon.svelte';

    const taxonContext = getActiveTaxonContext();
    const filtersContext = getFiltersContext();
    const modalContext = getModalContext();

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
        // { label: 'Genus', sortKey: 'genus' },
        // { label: 'Taxon Rank', sortKey: 'taxon_rank' },
    ]);

    function setActiveTaxon(e: MouseEvent) {
        const target = e.currentTarget as HTMLElement;
        const targetID = target.dataset.taxonId;

        if (!targetID || !parseInt(targetID)) return;

        taxonContext.taxonID = parseInt(targetID);
    }

    // Filter taxa by filteredTaxa
    $effect(() => {
        // Filter to animalia (all) if not filtered taxa
        let filterTaxa = filtersContext.filteredTaxa || { 1: 'Animalia' };

        if (!$taxaTree) {
            return;
        }

        let activeRanks = filtersContext.nSRanks;

        // Determine which rank we need (for filtering)
        const relevantRank: Partial<keyof TaxonNodeType> =
            filtersContext.includeINat
                ? 'ns_rank_state'
                : 'ns_rank_state_no_inat';

        const taxaMap = new Map<Number, TaxonNodeType>();

        for (const taxonID of Object.keys(filterTaxa).map(Number)) {
            const parentNode = $taxaTree.find(
                (node) => node.taxon_id === taxonID
            );

            if (!parentNode) continue;

            taxaMap.set(parentNode.taxon_id, parentNode);

            const children = getAllChildrenNodes($taxaTree, taxonID);
            for (const child of children) {
                taxaMap.set(child.taxon_id, child);
            }
        }

        let newTaxa = Array.from(taxaMap.values()).filter((taxonNode) =>
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
                        <!-- <div class="taxon-rank-label">
                            {taxon.genus}
                        </div> -->
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
    .rankings-loading {
        margin: 0.5rem;
    }
    #download-rankings-button {
        height: 2.5rem;
        position: absolute;
        right: 0;
        bottom: 0;
        opacity: 0.6;
        transition: opacity ease-in-out 0.1s;
    }
    #download-rankings-button:hover {
        opacity: 1;
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
        color: goldenrod;
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
        position: relative;
    }
    #rankings-page-body {
        height: 100%;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        background-color: var(--container-mid);
        border-radius: 3px;
        justify-content: baseline;
        border: 1px solid var(--border);
        /* box-shadow: inset 0px 1px 10px var(--container-shadow); */
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
