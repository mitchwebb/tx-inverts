<!--
    @component
    - Basic Svelte checkbox input item
    - Accepts customIcon to replace textbox
    - Handler returns { name: string, value: string, checked: boolean }
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    export type CheckboxPayload = {
        name: string;
        value: string;
        checked?: boolean;
    };

    type CheckboxInputProps = {
        name: string;
        value: string;
        handler: (payload: CheckboxPayload) => void;
        checked: boolean;
        children?: Snippet;
        checkboxIcon?: Snippet<[checked: boolean]>;
        customClass?: string;
    };

    let {
        name,
        value,
        handler,
        checked,
        children,
        checkboxIcon,
        customClass,
    }: CheckboxInputProps = $props();

    function handleChange(e: Event) {
        const target = e.target as HTMLInputElement;
        handler?.({
            name,
            value,
            checked: target.checked,
        });
    }
</script>

<label class={`checkbox-label ${customClass}`}>
    <!-- Normal checkbox (hidden if custom icon provided) -->
    <input
        {checked}
        {name}
        onclick={(e) => e.stopPropagation()}
        type="checkbox"
        class:hidden-checkbox={checkboxIcon}
        onchange={handleChange}
        value={String(value)}
    />
    <!-- Custom checkbox UI (optional) -->
    {#if checkboxIcon}
        <span class="checkbox-icon icon">
            {@render checkboxIcon(checked!)}
        </span>
    {/if}
    <!-- Label content snippet (provided as child) -->
    {#if children}
        <span class="label-content">
            {@render children?.()}
        </span>
    {/if}
</label>

<style>
    .checkbox-label {
        display: flex;
        gap: 0.5rem;
        cursor: pointer;
    }
    .label-content {
        width: 100%;
        min-width: 0;
        text-align: left;
    }
    .checkbox-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        pointer-events: none; /* allow clicks to pass through to the hidden checkbox */
        color: var(--fill-color);
        transition: color 0.2s ease;
        z-index: 1;
    }
    .checkbox-icon:hover {
        cursor: pointer;
    }
    .hidden-checkbox {
        position: absolute;
        opacity: 0;
        width: 1em;
        height: 1em;
        margin: 0;
        padding: 0;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        z-index: 5;
        display: none;
    }
</style>
