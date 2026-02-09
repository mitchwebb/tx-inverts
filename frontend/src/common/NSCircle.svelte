<!--
    @component
    - NatureServe-style conservation ranking bubble
    - Relies on nSRankKey for color values
-->
<script lang="ts">
    import { nSRankKey } from '../constants/natureServe';
    import type { NSLevel, NSRank } from '../types/api';
    import { getTextColor } from '../util/colors';

    type CircleProps = {
        active: boolean;
        level: NSLevel;
        rank: NSRank;
    };

    let { active, level, rank }: CircleProps = $props();

    type NSRankKeyItem = (typeof nSRankKey)[number];

    class UnknownNSRankError extends Error {
        constructor(rank: string | null) {
            super(`Unknown NatureServe rank: "${rank}"`);
            this.name = 'UnknownNSRankError';
        }
    }

    // Get rank attributes from key
    const { color, description } = $derived.by<NSRankKeyItem>(() => {
        const rankProps = nSRankKey.find((row) => row.rank === rank);
        if (!rankProps) throw new UnknownNSRankError(rank);
        return rankProps;
    });
</script>

<svg
    class="ns-circle"
    height="24"
    width="24"
    viewBox="0 0 24 24"
    preserveAspectRatio="xMidYMid meet"
>
    <g>
        <circle
            r={11.5}
            cx={12}
            cy={12}
            fill={active ? 'var(--fill-color)' : 'none'}
        />
        <circle r={10.5} cx={12} cy={12} fill={active ? color : 'grey'}>
            <title>{description}</title>
        </circle>
        <text
            class="ranking-text"
            text-anchor="middle"
            dominant-baseline="central"
            dx={12}
            dy={12}
            font-size={11}
            fill={getTextColor(active ? color : 'grey')}
        >
            {level.toUpperCase()}{rank?.toUpperCase()}
        </text>
    </g>
</svg>

<style>
    .ns-circle {
        height: 100%;
        width: 100%;
        display: block;
    }
    .ranking-text {
        pointer-events: none;
    }
</style>
