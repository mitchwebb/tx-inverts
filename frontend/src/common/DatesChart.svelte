<script lang="ts">
    import {
        Chart,
        type ChartDataset,
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        TimeScale,
        Title,
        Legend,
        Tooltip,
    } from 'chart.js';
    import 'chartjs-adapter-date-fns'; // required for time scale

    Chart.register(
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        TimeScale,
        Title,
        Legend,
        Tooltip
    );

    type DatesChartProps = {
        data: ChartDataset<'line', Record<string, number>[]>[];
        title: string;
        legendPosition: 'bottom' | 'top' | 'right' | 'left';
        chartID: string;
        min: string | undefined;
        max: string | undefined;
    };

    const { data, title, legendPosition, chartID, min, max }: DatesChartProps =
        $props();

    let chartEl: HTMLCanvasElement;
    let chartInstance:
        | Chart<'line', Record<string, number>[], string>
        | undefined;

    $effect(() => {
        if (!chartEl) return;

        chartInstance?.destroy();

        chartInstance = new Chart<'line', Record<string, number>[], string>(
            chartEl,
            {
                type: 'line',
                data: {
                    datasets: data,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'time',
                            min: min,
                            max: max,
                            time: {
                                unit: 'month',
                                tooltipFormat: 'MMM yyyy',
                            },
                            ticks: {
                                color: getComputedStyle(chartEl).color,
                            },
                        },
                        y: {
                            ticks: {
                                color: getComputedStyle(chartEl).color,
                            },
                        },
                    },
                    plugins: {
                        legend: {
                            position: legendPosition,
                            labels: {
                                color: getComputedStyle(chartEl).color,
                                boxWidth: 10,
                                boxHeight: 10,
                                usePointStyle: true,
                                textAlign: 'left',
                            },
                        },
                        title: {
                            display: true,
                            text: title,
                            color: getComputedStyle(chartEl).color,
                            font: {
                                weight: 500,
                            },
                        },
                    },
                },
            }
        );

        console.log(getComputedStyle(chartEl).color);

        return () => {
            chartInstance?.destroy();
        };
    });
</script>

<div class="canvas-wrapper">
    <canvas bind:this={chartEl} id={chartID}></canvas>
</div>

<style>
    .canvas-wrapper {
        position: relative;
        width: 100%;
        min-width: 0;
        height: 200px;
        box-sizing: border-box;
    }
    .canvas-wrapper canvas {
        display: block;
    }
</style>
