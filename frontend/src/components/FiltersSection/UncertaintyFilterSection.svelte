<script lang="ts">
    import { getFiltersContext } from '../../contexts/filtersContext';
    import BasicInput from '../../common/BasicNumberInput.svelte';
    import InfoButton from '../../common/InfoButton.svelte';

    type DateFilterProps = {
        header?: string;
    };

    const { header = 'Coord Uncertainty Limit' }: DateFilterProps = $props();

    const filtersContext = getFiltersContext();

    function handleChange(value: number | null) {
        filtersContext.coordUncertainty = value ?? null;
    }

    let limitUncertainty = $derived<boolean>(
        !!filtersContext?.coordUncertainty
    );
</script>

<div
    class="uncertainty-filter-section filters-section"
    class:active={filtersContext.coordUncertainty != null}
>
    <div class="filters-section-header">
        <span class="header-text-wrapper">
            {header}
            <InfoButton type="tooltip" hover>
                <span
                    >Some observation data include a coordinate uncertainty
                    range, which defines a radius around the provided
                    coordinates in which the record may exist. Data with high
                    uncertainty may be unreliable for calculating rankings.</span
                >
            </InfoButton>
        </span>
    </div>
    <div class="filters-section-content">
        <div class="uncertainty-filter-wrapper">
            <div class="uncertainty-content-wrapper">
                <ul
                    class="uncertainty-limit-wrapper"
                    class:disabled={limitUncertainty}
                >
                    <div class="uncertainty-limit-input-wrapper">
                        <BasicInput
                            min={0}
                            bind:value={filtersContext.coordUncertainty}
                            handler={handleChange}
                            placeholder={'No Limit'}
                            units={'meters'}
                        />
                    </div>
                </ul>
            </div>
        </div>
    </div>
</div>

<style>
    .uncertainty-filter-section {
        height: fit-content;
        flex-basis: 33%;
    }
    .header-text-wrapper {
        display: flex;
        flex-wrap: nowrap;
        white-space: nowrap;
        gap: 0.25rem;
    }
    .uncertainty-limit-wrapper {
        margin-left: 1rem;
    }
    .uncertainty-limit-input-wrapper {
        max-width: 250px;
    }
    .uncertainty-content-wrapper ul {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        padding: 0;
        margin: 0;
        height: 2.5rem;
        max-width: 100%;
    }
    .filters-section-header {
        width: 100%;
        display: flex;
        gap: 1rem;
    }
    .uncertainty-content-wrapper {
        min-width: 25px;
        font-size: 0.8rem;
        display: flex;
        flex-direction: column;
    }
    .uncertainty-filter-wrapper {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        position: relative;
        width: 100%;
    }
</style>
