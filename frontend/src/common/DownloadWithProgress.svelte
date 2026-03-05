<script lang="ts">
    import LoadingIcon from '../assets/LoadingIcon.svelte';

    type DownloadWithEstimateProps = {
        label: string;
        loadingEstimate?: boolean;
        disabled: boolean;
        downloadHandler: () => void;
        fileSize?: number | null;
        bytesReceived?: number | null;
    };

    const {
        label,
        loadingEstimate = false,
        disabled = false,
        downloadHandler,
        fileSize = null,
        bytesReceived = null,
    }: DownloadWithEstimateProps = $props();

    function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        const data = new FormData(event.target as HTMLFormElement);
        // Exit on dubious activity
        if (data.get('email_confirm')) return;
        else downloadHandler();
    }
</script>

<div class="download-item-wrapper" class:disabled>
    <form onsubmit={handleSubmit}>
        <!-- Catch some dubious activity -->
        <input
            style="display:none"
            type="text"
            name="email_confirm"
            tabindex="-1"
            autocomplete="off"
        />
    </form>
    <button class="download-button" type="submit">
        <span class="button-label-wrapper">
            {#if loadingEstimate}
                <div class="icon">
                    <LoadingIcon />
                </div>
                <!-- <span> Loading </span> -->
            {:else}
                {label}
            {/if}
        </span>
        {#if bytesReceived && fileSize}
            <div
                class="loading-bar"
                style:width={`${(bytesReceived / fileSize) * 100}%`}
            ></div>
        {/if}
    </button>
</div>

<style>
    .button-label-wrapper {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    .loading-bar {
        background-color: var(--fill-color);
        position: absolute;
        left: 0;
        top: calc(100% - 3px);
        height: 3px;
        /* opacity: 50%; */
        border-radius: 1px;
    }
    .download-item-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
    }
    .download-button {
        border: 1px solid var(--border);
        position: relative;
    }
    .disabled {
        opacity: 0.75;
    }
    .download-item-wrapper.disabled {
        cursor: wait;
    }
    .download-item-wrapper.disabled button {
        pointer-events: none;
    }
    .button-label-wrapper .icon {
        height: 1.2rem;
    }
</style>
