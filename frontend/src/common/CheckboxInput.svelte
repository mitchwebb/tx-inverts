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
        checked: boolean;
        e: Event;
    };

    type CheckboxInputProps = {
        name: string;
        value: string;
        handler: (payload: CheckboxPayload) => void;
        checked: boolean;
        children?: Snippet;
        checkboxIcon?: Snippet<[checked: boolean]>;
        customClass?: string;
        labelPosition?: 'left' | 'right';
    };

    let {
        name,
        value,
        handler,
        checked,
        children,
        checkboxIcon,
        customClass,
        labelPosition = 'right',
    }: CheckboxInputProps = $props();

    function handleChange(e: Event) {
        const target = e.target as HTMLInputElement;
        handler?.({
            name,
            value,
            checked: target.checked,
            e,
        });
    }
</script>

<label class={`checkbox-container ${customClass}`}>
    <!-- Normal checkbox (hidden if custom icon provided) -->
    <div class="checkbox-icon-wrapper">
        <input
            {checked}
            {name}
            onclick={(e) => e.stopPropagation()}
            type="checkbox"
            class:hidden-checkbox={!!checkboxIcon}
            onchange={handleChange}
            value={String(value)}
        />

        {#if labelPosition === 'right'}
            <!-- Custom checkbox UI (optional) -->
            {#if checkboxIcon}
                <div class="custom-checkbox">
                    {@render checkboxIcon(checked!)}
                </div>
            {:else}
                <span class="default-checkmark"></span>
            {/if}
        {/if}
    </div>

    <!-- Label content snippet (provided as child) -->
    {#if children}
        <div class="label-content">
            {@render children?.()}
        </div>
    {/if}

    {#if labelPosition === 'left'}
        <!-- Custom checkbox UI (optional) -->
        {#if checkboxIcon}
            <div class="custom-checkbox">
                {@render checkboxIcon(checked!)}
            </div>
        {:else}
            <span class="default-checkmark"></span>
        {/if}
    {/if}
</label>

<style>
    .label-content {
        width: 100%;
        text-align: left;
        display: inline;
        align-self: baseline;
    }
    .checkbox-icon-wrapper {
        position: relative;
        flex-shrink: 0;
        height: 1rem;
        width: 1rem;
        padding: 0;
        margin: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: var(--accent-color);
        transition: color 0.2s ease;
        z-index: 1;
        box-sizing: border-box;
    }
    .checkbox-icon-wrapper:hover {
        cursor: pointer;
    }
    .hidden-checkbox {
        position: absolute;
        opacity: 0;
        width: 1.5rem;
        height: 1.5rem;
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
    .checkbox-container {
        gap: 0.5rem;
        display: inline-flex;
        width: 100%;
        position: relative;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        vertical-align: middle;
        align-items: center;
    }
    .checkbox-container input {
        cursor: pointer;
        position: relative;
        opacity: 0;
        height: 100%;
        width: 100%;
        padding: 0;
        margin: 0;
    }
    .default-checkmark {
        cursor: pointer;
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 100%;
        background-color: var(--container-back);
        border: 1px solid var(--border);
        box-sizing: border-box;
        padding: 0;
        margin: 0;
        align-self: baseline;
    }
    .checkbox-container:hover
        .checkbox-icon-wrapper
        input:not(:checked)
        ~ .default-checkmark {
        background-color: var(--container-mid);
    }

    .checkbox-icon-wrapper input:checked ~ .default-checkmark {
        background-color: var(--accent-color);
    }
    input:checked ~ .default-checkmark:after {
        content: '✓';
        color: black;
        font-weight: bold;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
