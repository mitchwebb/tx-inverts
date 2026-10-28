<!-- Simple stylized combination of common name, authorship, and provisional taxon info -->
<!-- Determines color based on invasives/dubious taxon conditions -->
<!-- Fallback to scientificName value if no common name provided (doesn't preserve formatting)-->

<script lang="ts">
    import type { TaxonInfo } from '../types/api';
    import { isItalicizedRank } from '../util/taxa';
    import ProvisionallyAcceptedTip from './ProvisionallyAcceptedTip.svelte';

    // Require these specfic keys from TaxonInfo, but allow other types to be passed in
    type NameAndAuthorshipSubset = Pick<
        TaxonInfo,
        | 'canonicalName'
        | 'taxonomicStatus'
        | 'uSInvasive'
        | 'scientificNameAuthorship'
        | 'taxonRank'
        | 'scientificName'
    >;

    type NameAndAuthorshipType = {
        info: NameAndAuthorshipSubset;
    };
    const { info }: NameAndAuthorshipType = $props();

    const italicized = $derived(isItalicizedRank(info.taxonRank));
</script>

<span
    class="taxon-name-and-authorship"
    class:dubious-taxon={info?.taxonomicStatus !== 'accepted'}
    class:invasive-taxon={info?.uSInvasive}
>
    {#if info.canonicalName}
        <span class={[{ italicized }]}>
            {info.canonicalName}
        </span>
        <span class="taxon-authorship thin"
            >{info.scientificNameAuthorship ?? null}
        </span>
    <!-- If no canonicalName, fall back to dirty scientificName -->
    {:else}
        <span>
            {info.scientificName}
        </span>
    {/if}
    {#if info.taxonomicStatus == 'provisionally accepted'}
        <ProvisionallyAcceptedTip />
    {/if}
</span>

<style>
    .taxon-name-and-authorship {
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
