<!--
    @component
    - Universal tooltip for site.
    - Relies on tooltipContext to store/read positioning and content.
-->
<script lang="ts">
    import { getTooltipContext } from '../contexts/tooltipContext';
    import { getTextColor } from '../util/colors';
    import { getCSSValue } from '../util/theme';

    const tooltipContext = getTooltipContext();

    let tooltip: HTMLElement;

    let left = $state(0);
    let top = $state(0);

    // Place tooltip above target (false) or below (true)
    let verticalFlip: boolean = $state(false);
    // Allows tooltip pointer to follow target
    let arrowAdjustment = $state(0);

    // Padding between target object and tooltip
    const padding = 10;

    // Set fallback for default backgroundColor
    let backgroundColor = $derived(
        tooltipContext.backgroundColor ??
            getCSSValue('#theme-wrapper', '--tooltip-background')
    );

    // Close tooltip on click off
    function handleDocumentClick(event: MouseEvent) {
        const clickedNode = event.target as Node;
        // Only close if click is outside both tooltip and target
        if (
            !tooltip?.contains(clickedNode) &&
            !tooltipContext.target?.contains(clickedNode)
        ) {
            tooltipContext.visible = false;
        }
    }

    // Update tooltip position on resize
    function updatePosition() {
        const target = tooltipContext.target;
        if (!tooltipContext.visible || !target || !tooltip) return;

        const tooltipRect = tooltip.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();

        const absoluteLeft =
            targetRect.left + targetRect.width / 2 - tooltipRect.width / 2;
        const absoluteTop = targetRect.top - tooltipRect.height - padding;

        // Determine if tooltip needs to be flipped to be below the target
        verticalFlip = absoluteTop < padding;
        top = verticalFlip ? targetRect.bottom + padding : absoluteTop;

        // Determine x placement of tooltip based on page boundaries
        left = Math.min(
            Math.max(padding, absoluteLeft),
            window.innerWidth - (tooltipRect.width + padding)
        );

        // Apply tooltip arrow placement
        arrowAdjustment = left - absoluteLeft;
    }

    // Close tooltip on scroll
    function handleScroll() {
        tooltipContext.visible = false;
    }

    // Attach/remove event listeners based on visibility
    $effect(() => {
        if (!tooltipContext.visible) return;

        updatePosition();
        window.addEventListener('click', handleDocumentClick);
        window.addEventListener('scroll', handleScroll, true);
        window.addEventListener('resize', updatePosition);

        return () => {
            window.removeEventListener('click', handleDocumentClick);
            window.removeEventListener('scroll', handleScroll, true);
            window.removeEventListener('resize', updatePosition);
        };
    });

    // Set text color based on background value
    let textColor = $derived(getTextColor(backgroundColor || null));
</script>

<div
    bind:this={tooltip}
    id="tooltip-wrapper"
    class="rounded"
    style:visibility={tooltipContext.visible ? 'visible' : 'hidden'}
    style:left={`${left}px`}
    style:top={`${top}px`}
    style:background-color={backgroundColor}
    style:color={textColor}
    role="tooltip"
    aria-hidden={!tooltipContext.visible}
>
    <div class="tooltip-content">
        {@html tooltipContext.content}
    </div>
    <div
        class="tooltip-arrow {verticalFlip ? 'flipped' : ''}"
        style:border-top-color={verticalFlip
            ? 'transparent'
            : (backgroundColor ?? null)}
        style:border-bottom-color={verticalFlip
            ? (backgroundColor ?? null)
            : 'transparent'}
        style:top={verticalFlip ? 'unset' : '100%'}
        style:bottom={verticalFlip ? '100%' : 'unset'}
        style:left={`max(50% - ${arrowAdjustment}px, ${padding}px)`}
    ></div>
</div>

<style>
    .tooltip-content {
        padding: 0.5rem 0.25rem;
    }
    #tooltip-wrapper {
        position: fixed;
        z-index: 9999;
        max-width: 200px;
        user-select: none;
        padding: 0.25rem;
        background-color: var(--border);
        font-size: 0.9rem;
    }
    .tooltip-arrow {
        content: ' ';
        position: absolute;
        margin-left: -8px;
        border-width: 8px;
        border-style: solid;
        border-left-color: transparent;
        border-right-color: transparent;
        border-top-color: var(--border);
        border-bottom-color: var(--border);
    }
</style>
