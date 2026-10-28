<script lang="ts">
    import type { ParkSuggestion } from "../../../types/api";

    const {name, altPropName, owner}: ParkSuggestion = $props();
</script>

<div class="park-suggestion-row">
    <span class="prop-name">{name}</span>
    <div class="alt-prop-text">
        {#if altPropName && altPropName.trim()}
            <span class="alt-prop-name thin">{altPropName}</span>
        {/if}
        <span class="park-owner thin">{owner}</span>
    </div>
</div>

<style>
</style>