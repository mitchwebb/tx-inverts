<script lang="ts">
    import type { CountySuggestion } from "../../../types/api";
    const {name}: CountySuggestion = $props();
</script>

<div class="county-suggestion-row">
    {name}
</div>

<style>
</style>