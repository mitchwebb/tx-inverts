<!-- Small tooltip for a 'provisionally accepted' taxon warning -->
<script lang="ts">
    import InfoButton from './InfoButton.svelte';
</script>

<InfoButton type="tooltip" hover={true}>
    <span>
        A "provisionally accepted" status marks a taxon where more information
        is required to be certain of its validity. These taxa are frequently
        fixed in Catalogue of Life updates.
    </span>
</InfoButton>

<style></style>
