<!-- Styled, reusable AirDatepicker Element for Svelte -->

<script lang="ts">
    import { onMount, untrack } from 'svelte';
    import AirDatepicker, {
        type AirDatepickerOptions,
        type AirDatepickerPositionCallback,
    } from 'air-datepicker';
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

    const positionCalendar: AirDatepickerPositionCallback = ({
        $datepicker,
        $target,
        // $pointer,
        // done,
    }) => {
        const { top, left, height } = $target.getBoundingClientRect();
        const dpHeight = $datepicker.offsetHeight;

        const margin = 10;

        const spaceBelow = window.innerHeight - top - height;
        const spaceAbove = top;
        const showAbove = spaceBelow < dpHeight && spaceAbove > spaceBelow;

        $datepicker.style.left = `${left + window.scrollX}px`;
        $datepicker.style.top = showAbove
            ? `${top + window.scrollY - dpHeight - margin}px`
            : `${top + window.scrollY + height + margin}px`;
    };

    // Sync prop value to selected value
    $effect(() => {
        if (!datepicker) return;
        const current = datepicker.selectedDates[0] ?? null;
        // If no value provided but still currently selected date, clear date
        if (!value && current) {
            datepicker.clear();
        // Else if value is provided (but isn't currently selected), select it
        } else if (value && current?.toDateString() !== new Date(value).toDateString()) {
            datepicker.selectDate(value);
        }
    });

    // Mount Datepicker
    onMount(() => {
        if (inputEl) {
            datepicker = new AirDatepicker(inputEl, {
                locale: localeEn,
                position: positionCalendar,
                ...props,
            });
        }
        return;
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
        z-index: 2000;
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
