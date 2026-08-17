<!--
    @component
    - Svelte-style input element
    - Accepts number or date type
    - Returns value on change
-->
<script lang="ts">
    type InputProps = {
        customClass?: string | null;
        label?: string;
        value: number | null;
        min?: number | null;
        max?: number | null;
        step?: number | null;
        handler: (val: number | null) => void;
        placeholder?: string | null;
        units?: string | null;
    };

    let {
        customClass = null,
        label = '',
        value = $bindable(),
        min = null,
        max = null,
        step = null,
        handler,
        placeholder = null,
        units = null,
    }: InputProps = $props();

    let val = $derived<number | null>(value ?? null);

    function parseValue(rawValue: string): number | null {
        // If value is an empty string, return null
        return rawValue === '' ? null : Number(rawValue);
    }

    function handleChange(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        const parsed = parseValue(raw);
        handler(parsed);
    }

    $effect(() => {
        val = value ?? null;
    });
</script>

<label class={`input-wrapper ${customClass}`}>
    {label}
    <input
        type="number"
        bind:value={val}
        {min}
        {max}
        {step}
        onchange={handleChange}
        {placeholder}
    />
    <div>
        {#if units}
            <div class="input-suffix">
                {units}
            </div>
        {/if}
    </div>
</label>

<style>
    input {
        color: var(--text-default);
        height: 2.5rem;
        box-sizing: border-box;
        padding: 0 2.5rem 0 0.75rem;
        background-color: var(--container-back);
        border: 1px solid var(--border);
        border-radius: 3px;
        color: var(--text-default);
        padding-right: 4rem;
        max-width: 100%;
    }
    input:focus {
        outline: none;
        border-color: var(--fill-color);
    }
    input[type='number'] {
        -webkit-appearance: textfield;
        -moz-appearance: textfield;
        appearance: textfield;
    }

    input[type='number']::-webkit-inner-spin-button,
    input[type='number']::-webkit-outer-spin-button {
        -webkit-appearance: none;
    }

    .input-wrapper {
        position: relative;
        display: block;
    }

    .input-wrapper,
    .input-wrapper * {
        box-sizing: border-box;
    }

    .input-suffix {
        position: absolute;
        right: 0.75rem;
        top: 50%;
        transform: translateY(-50%);
        pointer-events: none; /* don't block clicks into the input */
        color: var(--text-secondary, var(--text-default));
        font-size: 0.8rem;
        white-space: nowrap;
        max-width: 4rem;
        overflow: hidden;
        text-overflow: ellipsis;
        opacity: 0.6;
        font-weight: 400;
        font-style: italic;
    }

    .increment-buttons {
        position: absolute;
        right: 0.25rem;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }
</style>
