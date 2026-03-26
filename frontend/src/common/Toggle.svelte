<!--
    @component
    - General toggle input element
    - Outputs 'checked' state on change
-->
<script lang="ts">
    type ToggleProps = {
        handler: (checked: boolean) => void;
        checked: boolean;
        onColor?: string;
        offColor?: string;
    };

    let {
        handler,
        checked,
        onColor = 'darkgreen',
        offColor = 'darkred',
    }: ToggleProps = $props();

    let internalChecked = $derived(checked);

    function handleClick() {
        internalChecked = !internalChecked;
        handler(internalChecked);
    }
</script>

<!-- TODO: fix this aria-label -->
<button onclick={handleClick} aria-label="toggle">
    <svg
        viewBox="0 3 24 19"
        fill="none"
        stroke-width="1"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="feather feather-toggle"
    >
        <rect
            x="1"
            y="5"
            width="22"
            height="14"
            rx="7"
            ry="7"
            style:fill={internalChecked ? onColor : offColor}
        ></rect>
        <circle cx={internalChecked ? '16' : '8'} cy="12" r="4"></circle>
    </svg>
</button>

<style>
    button {
        background-color: transparent;
        padding: 0;
        height: 100%;
        outline: none;
        border: none;
    }
    svg {
        width: 100%;
        height: 100%;
        display: block;
        stroke: inherit;
    }
    svg circle {
        fill: var(--container-highlight);
    }
    svg rect {
        fill: var(--container-mid);
    }
    svg circle {
        transition: cx 0.2s ease;
    }
</style>
