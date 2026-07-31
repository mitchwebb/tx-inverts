<!-- Styled, reusable AirDatepicker Element for Svelte -->

<script lang="ts">
    import { onMount } from 'svelte';
    import AirDatepicker, { type AirDatepickerOptions } from 'air-datepicker';
    import localeEn from 'air-datepicker/locale/en';
    import 'air-datepicker/air-datepicker.css';

    let inputEl: HTMLInputElement;

    export type AirDatepickerPayload = {
        date: Date | Date[];
        formattedDate: string | string[];
        datepicker: AirDatepicker;
    };

    type DatePickerProps = {
        id: string;
        hiddenInput?: boolean;
        placeholder?: string;
        value?: string | Date | null;
    } & AirDatepickerOptions;

    const {
        id,
        hiddenInput = false,
        placeholder = '',
        value,
        ...props
    }: DatePickerProps = $props();

    let datepicker: AirDatepicker | null = $state(null);
    let inputValue = $state('');

    function handleInput(e: Event) {
        inputValue = (e.target as HTMLInputElement).value;
    }

    function commitInput() {
        if (!datepicker) return;

        const parsed = new Date(inputValue);

        if (!inputValue) {
            datepicker.clear();
            return;
        }

        if (!isNaN(parsed.getTime())) {
            datepicker.selectDate(parsed);
        } else {
            // invalid -> reset to picker value
            const current = datepicker.selectedDates[0];
            inputValue = current ? current.toLocaleDateString() : '';
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            e.preventDefault();
            commitInput();
            (e.target as HTMLInputElement).blur();
        }
    }

    function handleBlur() {
        setTimeout(() => {
            const active = document.activeElement;

            // if focus is inside calendar → ignore
            if (datepicker?.visible) return;

            commitInput();
        }, 0);
    }

    // Sync prop value to selected value
    $effect(() => {
        if (!datepicker) return;

        if (value == null) {
            inputValue = '';
            return;
        }

        const d = new Date(value);

        if (!isNaN(d.getTime())) {
            inputValue = d.toLocaleDateString();
        }
    });

    let cleanup: (() => void) | null = null;

    onMount(() => {
        if (!inputEl) return;
        datepicker = new AirDatepicker(inputEl, {
            locale: localeEn,
            ...props,
        });

        return cleanup;
    });
</script>

<input
    {id}
    class:hidden-input={hiddenInput}
    bind:this={inputEl}
    class="datepicker"
    {placeholder}
    value={inputValue}
    oninput={handleInput}
    onblur={handleBlur}
    onkeydown={handleKeydown}
/>

<style>
    :global(#air-datepicker-global-container) {
        z-index: 10000;
    }
    .hidden-input {
        display: none;
    }
    input {
        padding: 0 0.75rem;
        color: var(--text-default);
        background-color: var(--container-back);
        border: 1px solid var(--border);
        border-radius: 3px;
        min-width: 75px;
        font-size: .8rem;
    }
    input:focus {
        outline: 1px solid var(--accent-color);
    }
</style>
