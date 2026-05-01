<!--
    @component
    - NatureServe-style conservation rank chart
    - Requires level and rank of evaluated species
-->
<script lang="ts">
    import NSCircle from './NSCircle.svelte';
    import { nSRankKey } from '../constants/natureServe';
    import type { NSLevel, NSRank } from '../types/api';

    type NSScaleProps = {
        level: NSLevel;
        activeRank?: NSRank;
    };

    let { level, activeRank = null }: NSScaleProps = $props();

    const fullRanking = $derived(`${level}${activeRank}`);
</script>

<div class="nature-serve-scale">
    {#each nSRankKey as { rank }}
        <!-- Element is active if fullRanking is equal to current rank -->
        {@const active = fullRanking == `${level}${rank}` || !activeRank}
        <NSCircle {active} {level} {rank} />
    {/each}
</div>

<style>
    .nature-serve-scale {
        width: 100%;
        max-width: 350px;
        display: flex;
        flex-wrap: nowrap;
        align-items: center;
        justify-content: center;

        /* Height depends on width of each circle */
        height: auto;
        aspect-ratio: auto; /* Let children define height */
    }
</style>
