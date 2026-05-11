<script lang="ts">
    import { onMount, untrack } from 'svelte';
    import GrabLine from '../../assets/GrabLine.svelte';
    import Sidebar from './Sidebar.svelte';
    import { getActiveTaxaContext } from '../../contexts/activeTaxaContext';

    const taxaContext = getActiveTaxaContext();

    let wrapper: HTMLElement;
    let isOpen = $state(false);
    let isDragging = $state(false);
    let startY = $state(0);
    let currentY = $state(0);
    let screenHeight = $state(0);
    let samples: { y: number; t: number }[] = $state([]);

    const FLICK_VELOCITY = 0.5; // px/ms
    const POSITION_THRESHOLD = 0.4; // 40% of screen
    const MIN_PEEK = 60;

    // TODO: Fix this hard-code
    // Leave some room for the header
    const MAX_TOP = 70;

    onMount(() => {
        screenHeight = window.innerHeight;
        closeSheet();
    });

    function openSheet() {
        isOpen = true;
        wrapper.style.transition =
            'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)';
        wrapper.style.transform = `translateY(${MAX_TOP}px)`;
    }

    function closeSheet() {
        isOpen = false;
        wrapper.style.transition =
            'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)';
        wrapper.style.transform = `translateY(calc(100% - ${MIN_PEEK}px))`;
    }

    function onPointerDown(e: PointerEvent) {
        startY = e.clientY;
        currentY = e.clientY;
        samples = [{ y: e.clientY, t: Date.now() }];
        // Don't commit to dragging yet — wait to see if it's a scroll or a drag
    }

    function onPointerMove(e: PointerEvent) {
        currentY = e.clientY;
        const now = Date.now();
        samples.push({ y: currentY, t: now });
        samples = samples.filter((s) => s.t > now - 100);

        const rawDelta = currentY - startY;

        if (!isDragging) {
            // Only hijack the gesture if:
            // - moving downward while open (closing gesture), OR
            // - moving upward while closed (opening gesture)
            // - and the scrollable content is at the top
            const scrollEl = wrapper.querySelector(
                '.sidebar-scroll'
            ) as HTMLElement;
            const atTop = !scrollEl || scrollEl.scrollTop === 0;

            const tryingToClose = isOpen && rawDelta > 8;
            const tryingToOpen = !isOpen && rawDelta < -8;

            if (
                tryingToClose ||
                tryingToOpen ||
                (isOpen && atTop && rawDelta > 0)
            ) {
                isDragging = true;
                wrapper.style.transition = 'none';
                (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
            } else {
                return; // Scroll
            }
        }
        const baseY = isOpen ? MAX_TOP : screenHeight - MIN_PEEK;

        let delta: number;
        if (isOpen) {
            // Dragging down: allow freely
            // Dragging past top: rubber-band
            delta = rawDelta < MAX_TOP ? rawDelta * 0.15 : rawDelta;
        } else {
            // Dragging up: allow freely
            // Dragging past bottom: rubber-band
            const maxUp = screenHeight - MIN_PEEK;
            delta =
                rawDelta < -maxUp
                    ? -maxUp + (rawDelta + maxUp) * 0.15
                    : rawDelta > MAX_TOP
                      ? rawDelta * 0.15
                      : rawDelta;
        }

        // Clamp so it never goes below MIN_PEEK
        const newY = Math.max(
            0,
            Math.min(screenHeight - MIN_PEEK, baseY + delta)
        );
        wrapper.style.transform = `translateY(${newY}px)`;
    }

    function onPointerUp() {
        if (!isDragging) return;
        isDragging = false;

        const oldest = samples[0];
        const newest = samples[samples.length - 1];
        const velocity =
            oldest && newest && oldest !== newest
                ? (newest.y - oldest.y) / (newest.t - oldest.t)
                : 0;

        const delta = currentY - startY;
        const flicked = Math.abs(velocity) > FLICK_VELOCITY;

        if (isOpen) {
            const shouldClose = flicked
                ? velocity > 0
                : delta > screenHeight * POSITION_THRESHOLD;
            shouldClose ? closeSheet() : openSheet();
        } else {
            const shouldOpen = flicked
                ? velocity < 0
                : delta < -(screenHeight * POSITION_THRESHOLD);
            shouldOpen ? openSheet() : closeSheet();
        }
    }

    let bouncing = $state(false);

    // Bounce sidebar on taxa changes
    $effect(() => {
        const activeTaxa = taxaContext.taxa.items;

        untrack(() => {
            if (!activeTaxa || !wrapper || isOpen) return;
            bouncing = true;
            setTimeout(() => {
                bouncing = false;
            }, 500);
        });
    });
</script>

<div
    id="mobile-sidebar-wrapper"
    class:bouncing
    bind:this={wrapper}
    role="dialog"
    aria-modal={isOpen}
    tabindex="-1"
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    onpointerup={onPointerUp}
    onpointercancel={onPointerUp}
>
    <button
        id="mobile-sidebar-tab"
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
        aria-expanded={isOpen}
        onclick={() => (isOpen ? closeSheet() : openSheet())}
    >
        <div id="mobile-sidebar-button">
            <GrabLine />
        </div>
    </button>
    <Sidebar activeTaxa={taxaContext.taxa.items} />
</div>

<style>
    #mobile-sidebar-wrapper {
        position: absolute;
        left: 0;
        bottom: 0;
        width: 100%;
        height: 100dvh;
        box-sizing: border-box;
        padding: 0.5rem;
        background-color: var(--container-fore);
        border-top-right-radius: 0.5rem;
        border-top-left-radius: 0.5rem;
        border-top: 1px solid var(--border);
        display: flex;
        flex-direction: column;
        align-items: center;
        will-change: transform;
        z-index: 900;
        touch-action: none;
        overscroll-behavior: none;
    }

    #mobile-sidebar-tab {
        color: var(--text-default);
        height: 0.75rem;
        width: 3rem;
        background-color: var(--container-fore);
        border: none;
        cursor: grab;
        touch-action: none;
        flex-shrink: 0;
        position: absolute;
        left: calc(50% - 1.5rem);
        bottom: 100%;
        border: 1px solid var(--border);
        border-bottom: none;
        border-top-right-radius: 3px;
        border-top-left-radius: 3px;
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
        padding: 0;
        padding-top: 0.2rem;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    #mobile-sidebar-tab:active {
        cursor: grabbing;
    }

    #mobile-sidebar-button {
        color: var(--text-default);
        width: 2.5rem;
        padding: 0 0.5rem;
        background-color: transparent;
        box-sizing: border-box;
    }

    .bouncing {
        animation: sidebar-bounce 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
    }

    /* Global allows us to use this name inline */
    @keyframes sidebar-bounce {
        0% {
            transform: translateY(calc(100% - 60px));
        }
        30% {
            transform: translateY(calc(100% - 90px));
        }
        50% {
            transform: translateY(calc(100% - 60px));
        }
        70% {
            transform: translateY(calc(100% - 78px));
        }
        85% {
            transform: translateY(calc(100% - 60px));
        }
        93% {
            transform: translateY(calc(100% - 68px));
        }
        100% {
            transform: translateY(calc(100% - 60px));
        }
    }
</style>
