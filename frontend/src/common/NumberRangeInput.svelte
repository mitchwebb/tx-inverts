<!--
    @component
    - Svelte-style range input element
    - Accepts number or date types
    - Returns (start, end) values on change
-->
<script lang="ts">
    import BasicNumberInput from "./BasicNumberInput.svelte";

    type RangeInputProps = {
        customClass?: string | null;
        label?: string;
        startValue: number | null;
        endValue: number | null;
        min?: number | null;
        max?: number | null;
        step?: number | null;
        handler: (start: number | null, end: number | null) => void;
    };

    let {
        customClass = null,
        label = '',
        startValue = null,
        endValue = null,
        min = null,
        max = null,
        step = null,
        handler,
    }: RangeInputProps = $props();

    let start = $derived<number | null>(
        startValue != null ? startValue : null
    );

    let end = $derived<number | null>(
        endValue != null ? endValue : null
    );

    // Safe compare function for dates/numbers
    function compare(a: number, b: number) {
        return a - b;
    }

    function handleStartChange(value: number | null) {
        // Set end equal to start if new start overlaps
        if (end !== null && value !== null && compare(value, end) > 0)
            end = start;
        handler(start, end);
    }

    function handleEndChange(value: number | null) {
        // Set start equal to end if new end overlaps
        if (start !== null && value !== null && compare(start, value) > 0)
            start = end;
        handler(start, end);
    }
</script>

<label class={`range-wrapper ${customClass}`}>
    {label}
    <BasicNumberInput
        bind:value={start}
        {min}
        {max}
        {step}
        handler={handleStartChange}
    />
    <span> to </span>
    <BasicNumberInput
        bind:value={end}
        {min}
        {max}
        {step}
        handler={handleEndChange}
    />
</label>

<style>
    .range-wrapper {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
</style>
