<script lang="ts">
</script>

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 420" width="100%">
    <!-- Clip paths to separate pyramid sections -->
    <defs>
        <clipPath id="cp0"
            ><rect x="0" y="35" width="680" height="47" /></clipPath
        >
        <clipPath id="cp1"
            ><rect x="0" y="86" width="680" height="47" /></clipPath
        >
        <clipPath id="cp2"
            ><rect x="0" y="137" width="680" height="47" /></clipPath
        >
        <clipPath id="cp3"
            ><rect x="0" y="188" width="680" height="47" /></clipPath
        >
        <clipPath id="cp4"
            ><rect x="0" y="239" width="680" height="47" /></clipPath
        >
        <clipPath id="cp5"
            ><rect x="0" y="290" width="680" height="47" /></clipPath
        >
        <clipPath id="cp6"
            ><rect x="0" y="341" width="680" height="47" /></clipPath
        >
    </defs>

    <!-- Kingdom -->
    <polygon
        points="80,33 600,33 562,84 118,84"
        fill="#bf360c"
        clip-path="url(#cp0)"
    />
    <!-- Phylum -->
    <polygon
        points="118,84 562,84 525,135 155,135"
        fill="#f57f17"
        clip-path="url(#cp1)"
    />
    <!-- Class -->
    <polygon
        points="155,135 525,135 488,186 192,186"
        fill="#ebb520"
        clip-path="url(#cp2)"
    />
    <!-- Order -->
    <polygon
        points="192,186 488,186 451,237 229,237"
        fill="#2e7d32"
        clip-path="url(#cp3)"
    />
    <!-- Family -->
    <polygon
        points="229,237 451,237 414,288 266,288"
        fill="#1565c0"
        clip-path="url(#cp4)"
    />
    <!-- Genus -->
    <polygon
        points="266,288 414,288 377,339 303,339"
        fill="#4a148c"
        clip-path="url(#cp5)"
    />
    <!-- Species -->
    <polygon
        points="303,339 377,339 340,390"
        fill="#880e4f"
        clip-path="url(#cp6)"
    />

    <!-- Section Labels and Lines -->
    <g class="text-and-lines">
        <line x1="600" x2="605" y1="84" y2="84"></line>
        <text x="615" y="84">Kingdom</text>
        <line x1="562" x2="605" y1="135" y2="135"></line>
        <text x="615" y="135">Phylum</text>
        <line x1="525" x2="605" y1="186" y2="186"></line>
        <text x="615" y="186">Class</text>
        <line x1="488" x2="605" y1="237" y2="237"></line>
        <text x="615" y="237">Order</text>
        <line x1="451" x2="605" y1="288" y2="288"></line>
        <text x="615" y="288">Family</text>
        <line x1="414" x2="605" y1="339" y2="339"></line>
        <text x="615" y="339">Genus</text>
        <line x1="377" x2="605" y1="392" y2="392"></line>
        <text x="615" y="392">Species</text>
    </g>
</svg>

<style>
    svg {
        stroke-linecap: round;
        stroke-linejoin: round;
        display: block;
        height: 100%;
    }
    .text-and-lines {
        /* Translate labels to center of row */
        transform: translate(0, calc(((-51px / 2) + 0.75rem)));
    }
    .text-and-lines line {
        /* Translate line to center of text */
        transform: translate(0, -0.75rem);
    }
    text {
        font-size: 1.5rem;
        fill: var(--text-default);
    }
    line {
        stroke-width: 2px;
        stroke: var(--border);
    }
</style>
