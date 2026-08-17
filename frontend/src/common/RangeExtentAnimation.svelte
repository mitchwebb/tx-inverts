<script lang="ts">
    import { onDestroy, onMount } from 'svelte';
    import { TAXON_COLORS } from '../constants/taxa';

    let interval: NodeJS.Timeout;

    const height = 100;
    const width = 200;
    const center = [width / 2, height / 2];

    const pointsCount = 5;

    // Generate outer points (counter-clockwise)
    let outerPoints: [number, number][] = $state([]);

    // Generate inner points
    let innerPoints: [number, number][] = $state([]);

    function generatePoints() {
        // Each point
        for (let i = 0; i < pointsCount; i++) {
            const angle =
                (360 / pointsCount) * Math.random() + (360 / pointsCount) * i;
            const radians = (angle * Math.PI) / 180;
            // Place points, making room for stroke width
            const dx = ((width - 10) / 2) * Math.cos(-radians);
            const dy = ((height - 10) / 2) * Math.sin(-radians);
            innerPoints[i] = [
                dx * Math.random() + center[0],
                dy * Math.random() + center[1],
            ];
            outerPoints[i] = [dx + center[0], dy + center[1]];
        }
    }

    onMount(() => {
        generatePoints();
        interval = setInterval(() => {
            generatePoints();
        }, 2000);
    });

    onDestroy(() => {
        // Clear the interval when component is destroyed
        clearInterval(interval);
    });

    // Generate inner points
</script>

<div class="range-extent-svg">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100" width="100%">
        {#each outerPoints as point, i (i)}
            <circle r="4" cx={point[0]} cy={point[1]} fill={TAXON_COLORS[0]}
            ></circle>
        {/each}
        {#each innerPoints as point, i (i)}
            <circle r="4" cx={point[0]} cy={point[1]} fill={TAXON_COLORS[0]}
            ></circle>
        {/each}
    </svg>
    <div
        class="blob"
        style:background-color={TAXON_COLORS[0]}
        style="clip-path: polygon({outerPoints
            .map((p) => `${p[0]}px ${p[1]}px`)
            .join(', ')})"
    ></div>
</div>

<style>
    .range-extent-svg {
        width: 200px;
        position: relative;
    }
    svg {
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 2px;
        transition: all 0.5s ease-in-out;
    }
    circle {
        transition:
            cx 0.5s ease-in-out,
            cy 0.5s ease-in-out;
    }
    .blob {
        position: absolute;
        top: 0;
        width: 200px;
        height: 100px;
        transition: all 0.5s ease-in-out;
        opacity: 0.2;
    }
</style>
