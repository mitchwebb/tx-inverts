<script lang="ts">
    type DropdownProps = {
        options: { value: string; label: string }[];
        selected: string;
        onChange: (value: string) => void;
    };

    const { options, selected, onChange }: DropdownProps = $props();

    function handleChange(event: Event) {
        const target = event.target as HTMLSelectElement;
        onChange(target.value);
    }
</script>

<div class="custom-select">
    <select onchange={handleChange}>
        {#each options as option}
            <option value={option.value} selected={selected === option.value}>
                {option.value}
            </option>
        {/each}
    </select>
</div>

<style>
    .custom-select {
        position: relative;
    }
    .custom-select select {
        -webkit-appearance: none;
        background-color: var(--container-back);
        color: var(--text-default);
        border: 1px solid var(--border);
        border-radius: 3px;
        cursor: pointer;
        padding: 0.25rem;
        padding-right: 1.5rem;
    }

    .custom-select option {
        cursor: pointer;
    }

    .custom-select:hover {
        background-color: var(--container-shadow);
    }

    .custom-select::after {
        content: '';
        position: absolute;
        right: calc(0.25rem + 2px);
        top: 50%;
        transform: translateY(-50%);
        pointer-events: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid var(--text-default);
    }
</style>
