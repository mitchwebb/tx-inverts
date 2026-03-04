<script lang="ts">
    import { onMount, type Snippet } from 'svelte';
    import DownloadWithProgress from '../common/DownloadWithProgress.svelte';
    import type { EstimateMetrics } from '../types/api';
    import { getHumanReadableBytes } from '../util/bytes';
    import LoadingIcon from '../assets/LoadingIcon.svelte';

    type DownloadFormProps = {
        header: string;
        requestHandler: (estimate: boolean, onProgress?: (received: number) => void) => Promise<any>;
        children?: Snippet;
    }

    const { header, requestHandler, children }: DownloadFormProps = $props();

    let estimateSize: number | null = $state(null);
    let rowCount: number | null = $state(null);
    let loadingEstimate: boolean = $state(true);
    let bytesReceived: number | null = $state(null);

    let downloadDisabled: boolean = $derived(rowCount == 0 || estimateSize == null || loadingEstimate);

    // Consider download to be 'large' if is exceeds 50 MB
    let largeFile: boolean = $derived(!!estimateSize && estimateSize > (50 * 1024 * 1024))

    async function handleDownload() {
        await requestHandler(false, (r) => { bytesReceived = r });
        bytesReceived = null;
    }

    $effect(() => {
        (async () => {
            loadingEstimate = true;
            estimateSize = null;
            rowCount = null;
            const estimateMetrics: EstimateMetrics = await requestHandler(true) as EstimateMetrics;
            estimateSize = estimateMetrics.sizeEstimate
            rowCount = estimateMetrics.rowCount
            loadingEstimate = false;
        })()
    })

</script>

<div id="download-form-wrapper">
    <div id="download-form-header">
        <span class='header'> {header} </span>
    </div>
    <div id="download-form-content">
        {@render children?.()}
    </div>
    <div class='button-and-metrics-wrapper'>
        {#if estimateSize !== null && rowCount !== null}
            <div class="download-metrics thin">
                <span>Total Records: {rowCount.toLocaleString()}</span>
                <span class:large-file={largeFile}>File Estimate: {getHumanReadableBytes(estimateSize)}</span>
            </div>
            <DownloadWithProgress 
                label="Download"
                downloadHandler={handleDownload} 
                disabled={downloadDisabled}
                fileSize={estimateSize} 
                bytesReceived={bytesReceived} />
        {:else if loadingEstimate}
            <div id="download-loading-icon" class="icon">
                <LoadingIcon/>
            </div>
        {/if}
    </div>
</div>

<style>
    .large-file {
        color: red;
    }
    #download-loading-icon {
        margin: .5rem;
    }
    #download-form-content {
        overflow-y: auto;
        flex: 1;
        min-height: 0;
        min-width: 500px;
    }
    .button-and-metrics-wrapper {
        display: flex;
        gap: 1rem;
        flex-shrink: 0;
        justify-content: right;
        align-items: center;
        height: 50px;
    }
    .download-metrics {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        font-size: 1rem;
    }
    #download-form-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-width: 200px;
        max-height: 80dvh;
    }
</style>