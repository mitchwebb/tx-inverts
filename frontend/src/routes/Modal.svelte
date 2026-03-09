<!-- A dialog component could be used instead-->
<!-- But this feels more Svelte-ish and legacy-capable -->

<script lang="ts">
    import { fade } from 'svelte/transition';
    import XIcon from '../assets/XIcon.svelte';
    import { getModalContext } from '../contexts/modalContext';

    const modalContext = getModalContext();

    function handleKeyPress(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            handleModalClose();
        }
    }

    function handleModalClose() {
        if (modalContext.visible) {
            modalContext.visible = false;
        }
    }

    function focus(el: HTMLElement) {
        el.focus();
    }

    $effect(() => {
        $inspect(typeof modalContext.content);
    });
</script>

{#if modalContext.visible}
    <div id="modal">
        <div
            id="modal-overlay"
            onclick={handleModalClose}
            aria-hidden="true"
            transition:fade={{ duration: 50 }}
        ></div>
        <div id="modal-content-positioner">
            <div
                use:focus
                id="modal-content-wrapper"
                aria-modal="true"
                role="dialog"
                tabindex="0"
                onclick={(e) => e.stopPropagation()}
                onkeydown={handleKeyPress}
            >
                <div id="modal-content">
                    {#if typeof modalContext.content === 'string'}
                        <div class="modal-string">
                            {@html modalContext.content}
                        </div>
                    {:else}
                        {@const Component = modalContext.content}
                        <Component />
                    {/if}
                </div>
                <button
                    id="modal-close-button"
                    class="button"
                    onclick={handleModalClose}
                >
                    <XIcon />
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    #modal {
        position: fixed;
        inset: 0;
        z-index: 1000;
    }

    #modal-overlay {
        position: absolute;
        inset: 0;
        background-color: var(--container-shadow);
        opacity: 0.75;
    }

    #modal-close-button {
        position: absolute;
        top: 0.25rem;
        right: 0.25rem;
        color: var(--text-default);
        cursor: pointer;
        padding: 0;
        border: none;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1003;
        height: 1.5rem;
    }

    #modal-content-positioner {
        position: absolute;
        display: flex;
        justify-content: center;
        align-items: center;
        inset: 0;
        z-index: 1001;
        pointer-events: none;
        height: 100%;
        width: 100%;
    }

    #modal-content-wrapper {
        position: relative;
        display: flex;
        flex-direction: column; /* stack content vertically */
        background-color: var(--container-back);
        border-radius: 4px;
        min-width: 100px;
        max-width: 80dvw;
        min-height: 2rem;
        max-height: 95dvh; /* constrain to viewport */
        outline: 1px solid var(--border);
        pointer-events: auto;
        z-index: 1002;
        box-sizing: border-box;
        overflow: hidden; /* keep scroll inside wrapper */
        padding: 1.75rem;
    }

    #modal-content {
        flex: 1 1 auto; /* grow to wrapper height */
        overflow-y: auto; /* scroll if content is tall */
        width: 100%;
        display: block; /* remove flex centering to prevent clipping */
        color: var(--text-default);
        box-sizing: border-box;
    }

    .modal-string {
        padding: 0.5rem 1.5rem;
    }
</style>
