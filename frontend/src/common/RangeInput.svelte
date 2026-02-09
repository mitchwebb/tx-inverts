<!--
    @component
    - Svelte-style range input element
    - Accepts number or date types
    - Returns (start, end) values on change
-->
<script lang="ts">
    type RangeInputProps = {
        type: 'number' | 'date';
        customClass?: string | null;
        label?: string;
        startValue: string | number | null;
        endValue: string | number | null;
        min?: string | number | null;
        max?: string | number | null;
        step?: number | null;
        handler: (start: string | null, end: string | null) => void;
    };

    let {
        type,
        customClass = null,
        label = '',
        startValue = null,
        endValue = null,
        min = null,
        max = null,
        step = null,
        handler,
    }: RangeInputProps = $props();

    let start = $derived<string | null>(
        startValue != null ? String(startValue) : null
    );

    let end = $derived<string | null>(
        endValue != null ? String(endValue) : null
    );

    // Safe compare function for dates/numbers
    function compare(a: string, b: string) {
        return type === 'number' ? Number(a) - Number(b) : a.localeCompare(b);
    }

    function parseValue(value: string | null) {
        // If value is an empty string, return null
        return value === '' ? null : value;
    }

    function handleStartChange(e: Event) {
        const value = (e.target as HTMLInputElement).value;
        start = parseValue(value);
        // Set end equal to start if new start overlaps
        if (end !== null && start !== null && compare(start, end) > 0)
            end = start;
        handler(start, end);
    }

    function handleEndChange(e: Event) {
        const value = (e.target as HTMLInputElement).value;
        end = parseValue(value);
        // Set start equal to end if new end overlaps
        if (start !== null && end !== null && compare(start, end) > 0)
            start = end;
        handler(start, end);
    }
</script>

<label class={`range-wrapper ${customClass}`}>
    {label}
    <input
        {type}
        bind:value={start}
        {min}
        {max}
        {step}
        onchange={handleStartChange}
    />
    <span> to </span>
    <input
        {type}
        bind:value={end}
        {min}
        {max}
        {step}
        onchange={handleEndChange}
    />
</label>

<style>
    .range-wrapper {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    input {
        color: var(--text-default);
    }
    input:focus {
        outline: none;
        border-color: var(--fill-color);
    }
</style>
