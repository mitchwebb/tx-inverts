<script lang="ts">
    import { TAXON_COLORS } from '../constants/taxa';

    const groupOnePoints: [number, number][] = [
        [20, 20],
        [25, 30],
    ];

    const groupTwoPoints: [number, number][] = [
        [170, 30],
        [160, 20],
        [170, 15],
        [180, 25],
    ];

    const groupThreePoints: [number, number][] = [
        [100, 80],
        [80, 70],
        [90, 60],
    ];

    const groups = [groupOnePoints, groupTwoPoints, groupThreePoints];
</script>

<div class="occurrences-svg">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120" width="100%">
        {#each groups as groupPoints, i}
            <!-- Large points (background) -->
            {#each groupPoints as point}
                <circle
                    class="separation-radius"
                    fill={TAXON_COLORS[i]}
                    r="15"
                    cx={point[0]}
                    cy={point[1]}
                ></circle>
            {/each}
            <!-- Small points (foreground) -->
            {#each groupPoints as point}
                <circle
                    class="observation-point"
                    fill="black"
                    r="4"
                    cx={point[0]}
                    cy={point[1]}
                ></circle>
            {/each}
            {@const xCenter =
                groupPoints.reduce((acc, curr) => acc + curr[0], 0) /
                groupPoints.length}
            {@const yMax = groupPoints.reduce(
                (acc, curr) => Math.max(acc, curr[1]),
                0
            )}
            <text fill={TAXON_COLORS[i]} y={yMax + 35} x={xCenter}>
                {i + 1}
            </text>
        {/each}
    </svg>
</div>

<style>
    .occurrences-svg {
        width: 200px;
        position: relative;
    }
    svg {
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 2px;
        transition: all 0.1s ease-in-out;
    }
    circle {
        transition:
            cx 0.5s ease-in-out,
            cy 0.5s ease-in-out;
    }
    text {
        font-size: 16px;
        text-anchor: middle;
        /* stroke-width: 0.5; */
        /* stroke: var(--border); */
    }
</style>
