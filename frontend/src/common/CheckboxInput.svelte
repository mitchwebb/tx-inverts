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
        e.stopPropagation();
        const target = e.target as HTMLInputElement;
        handler?.({
            name,
            value,
            checked: target.checked,
        });
    }
</script>

<label class={`container ${customClass}`}>
    <!-- Normal checkbox (hidden if custom icon provided) -->
    <input
        {checked}
        {name}
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
    {:else}
        <span class="checkmark"></span>
    {/if}
    <!-- Label content snippet (provided as child) -->
    {#if children}
        <span class="label-content">
            {@render children?.()}
        </span>
    {/if}
</label>

<style>
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
        color: var(--accent-color);
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
    .checkbox-label input {
        padding: 0;
    }
    .container {
        display: flex;
        gap: 0.5rem;
        cursor: pointer;
        display: flex;
        position: relative;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    .container input {
        position: relative;
        opacity: 0;
        cursor: pointer;
        height: 1rem;
        width: 1rem;
    }
    .checkmark {
        position: absolute;
        top: 0;
        left: 0;
        height: 1rem;
        width: 1rem;
        background-color: var(--container-back);
        border: 1px solid var(--border);
    }
    .container:hover input ~ .checkmark {
        background-color: var(--container-mid);
    }
    .container input:checked ~ .checkmark {
        background-color: var(--accent-color);
    }
    .checkmark:after {
        content: '';
        position: absolute;
        display: none;
    }
    .container input:checked ~ .checkmark:after {
        display: block;
    }
    .container .checkmark:after {
        left: 0.35rem;
        top: 0.1rem;
        width: 0.2rem;
        height: 0.5rem;
        border: solid black;
        border-width: 0 3px 3px 0;
        -webkit-transform: rotate(45deg);
        -ms-transform: rotate(45deg);
        transform: rotate(45deg);
    }
</style>
