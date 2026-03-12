<script lang="ts">
</script>

<svg
    class="loading-icon"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
>
    <path d="M22,12c0,5.5-4.5,10-10,10S2,17.5,2,12S6.5,2,12,2" />
</svg>

<style>
    svg {
        display: block;
        /* width: 100%; */
        height: 100%;
        animation: rotation linear 1s infinite;
    }

    @keyframes rotation {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
</style>
