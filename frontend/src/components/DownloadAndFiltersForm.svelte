<script lang="ts">
    import { onMount, type Snippet } from 'svelte';
    import DownloadWithProgress from '../common/DownloadWithProgress.svelte';
    import type { EstimateMetrics } from '../types/api';
    import { getHumanReadableBytes } from '../util/bytes';
    import LoadingIcon from '../assets/LoadingIcon.svelte';

    const TURNSTILE_KEY = import.meta.env.VITE_TURNSTILE_KEY;

    type DownloadFormProps = {
        header?: string;
        requestHandler: (
            getEstimate: boolean,
            token?: string | null,
            onProgress?: (received: number) => void
        ) => Promise<any>;
        children?: Snippet;
    };

    const { header, requestHandler, children }: DownloadFormProps = $props();

    let estimateSize: number | null = $state(null);
    let rowCount: number | null = $state(null);
    let loadingEstimate: boolean = $state(true);
    let bytesReceived: number | null = $state(null);
    let turnstileToken: string | null = $state(null);

    let downloadDisabled: boolean = $derived(
        rowCount == 0 ||
            estimateSize == null ||
            loadingEstimate ||
            !turnstileToken
    );

    // Consider download to be 'large' if is exceeds 50 MB
    let largeFile: boolean = $derived(
        !!estimateSize && estimateSize > 50 * 1024 * 1024
    );

    async function handleDownload() {
        downloadDisabled = true;
        await requestHandler(false, turnstileToken, (r) => {
            bytesReceived = r;
        });
        downloadDisabled = false;
        bytesReceived = null;
    }

    $effect(() => {
        (async () => {
            loadingEstimate = true;
            estimateSize = null;
            rowCount = null;
            const estimateMetrics: EstimateMetrics = (await requestHandler(
                true
            )) as EstimateMetrics;
            if (!estimateMetrics) {
                loadingEstimate = false;
                rowCount = null;
                estimateSize = null;
                return;
            }
            estimateSize = estimateMetrics.sizeEstimate;
            rowCount = estimateMetrics.rowCount;
            loadingEstimate = false;
        })();
    });

    onMount(() => {
        turnstile.render('#turnstile-widget', {
            sitekey: TURNSTILE_KEY,
            theme: 'dark',
            size: 'normal',
            callback: function (token: string) {
                turnstileToken = token;
            },
        });
    });
</script>

<div id="download-form-wrapper">
    {#if header}
        <h3 id="download-form-header">
            {header}
        </h3>
    {/if}
    <div id="download-form-content">
        {@render children?.()}
    </div>
    <div class="download-section-wrapper">
        <div id="turnstile-widget"></div>
        <div class="button-and-metrics-wrapper">
            {#if estimateSize !== null && rowCount !== null}
                <div class="download-metrics thin">
                    <span>Total Records: {rowCount.toLocaleString()}</span>
                    <span class:large-file={largeFile}
                        >File Estimate: {getHumanReadableBytes(
                            estimateSize
                        )}</span
                    >
                </div>
                <DownloadWithProgress
                    label="Download"
                    downloadHandler={handleDownload}
                    disabled={downloadDisabled || !turnstileToken}
                    fileSize={estimateSize}
                    {bytesReceived}
                />
            {:else if loadingEstimate}
                <span class="thin"> Getting Estimate </span>
                <div id="download-loading-icon" class="icon">
                    <LoadingIcon />
                </div>
            {:else if estimateSize == null && rowCount == null}
                <div class="retrieval-failed-message">
                    Download Retrieval Failed
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    .download-section-wrapper {
        display: flex;
        justify-content: space-between;
        height: 65px;
        margin-top: 0.5rem;
    }
    #turnstile-widget {
        display: flex;
        justify-content: left;
    }
    .retrieval-failed-message {
        margin: 0 0.5rem;
    }
    .large-file {
        color: red;
    }
    #download-loading-icon {
        margin: 0.5rem;
    }
    #download-form-content {
        overflow-y: auto;
        flex: 1;
        min-height: 0;
        width: 100%;
        flex-wrap: wrap;
    }
    .button-and-metrics-wrapper {
        display: flex;
        gap: 1rem;
        flex-shrink: 0;
        justify-content: right;
        align-items: flex-start;
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
        min-width: 200px;
        width: 90dvw;
        max-width: 800px;
    }
</style>
