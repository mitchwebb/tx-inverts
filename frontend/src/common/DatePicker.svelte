<!-- Styled, reusable AirDatepicker Element for Svelte -->

<script lang="ts">
    import { onMount } from 'svelte';
    import AirDatepicker, { type AirDatepickerOptions } from 'air-datepicker';
    import localeEn from 'air-datepicker/locale/en';
    import 'air-datepicker/air-datepicker.css';

    // TODO: Work on binding typed dates

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

    // Sync prop value to selected value
    $effect(() => {
        console.log(value);
        if (!datepicker) return;
        const current = datepicker.selectedDates[0] ?? null;
        // If no value provided but still currently selected date, clear date
        if (!value && current) {
            console.log('helo');
            datepicker.clear();
            // Else if value is provided (but isn't currently selected), select it
        } else if (
            value &&
            current?.toDateString() !== new Date(value).toDateString()
        ) {
            datepicker.selectDate(value);
        }
    });

    let cleanup: (() => void) | null = null;

    onMount(() => {
        if (!inputEl || !inputEl.parentElement) return;
        datepicker = new AirDatepicker(inputEl, {
            container: inputEl.parentElement,
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
/>

<style>
    :global(#air-datepicker-global-container) {
        z-index: 10000;
    }
    .hidden-input {
        display: none;
    }
    input {
        padding: 0.5rem;
        color: var(--text-default);
        background-color: var(--container-back);
        border: 1px solid var(--border);
        border-radius: 3px;
        min-width: 75px;
    }
    input:focus {
        outline: 1px solid var(--accent-color);
    }
</style>
