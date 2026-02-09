<!--
    @component
    - Universal link icon
    - Uses href and target props to populate <a> element
-->
<script lang="ts">
    import LinkIcon from '../assets/LinkIcon.svelte';

    type LinkButtonProps = {
        href: string;
        ariaLabel?: string;
        target?: string;
    };
    const {
        href,
        ariaLabel = 'Open link',
        target = '_self',
    }: LinkButtonProps = $props();
</script>

<a
    class="link-button"
    {href}
    {target}
    aria-label={ariaLabel}
    rel={target === '_blank' ? 'noopener noreferrer' : undefined}
>
    <LinkIcon />
</a>

<style>
    a {
        color: unset;
    }
</style>
