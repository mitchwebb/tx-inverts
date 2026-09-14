<!-- Simple stylized combination of common name, authorship, and provisional taxon info -->
<!-- Determines color based on invasives/dubious taxon conditions -->

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
    <span class={[{ italicized }]}>
        {info.canonicalName}
    </span>
    <span class="taxon-authorship"
        >{info.scientificNameAuthorship ?? null}
    </span>
    {#if info.taxonomicStatus == 'provisionally accepted'}
        <ProvisionallyAcceptedTip />
    {/if}
</span>

<style>
</style>
