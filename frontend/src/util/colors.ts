/**
 * Determines whether black or white text will be more legible on a given background color.
 *
 * Uses the standard relative luminance formula:
 *   0.299 * R + 0.587 * G + 0.114 * B
 * to assess whether the background is "light" or "dark."
 *
 * @param bgColor - A valid rgb, hex, or hsl string
 * @returns 'rgb(0, 0, 0)' for 'light' backgrounds, 'rgb(255, 255, 255)' for 'dark' ones
 */
export function getTextColor(
    bgColor: string | null,
    defaultLight: string = 'rgb(255, 255, 555)',
    defaultDark: string = 'rgb(0, 0, 0)'
): string {
    let r = 0,
        g = 0,
        b = 0;

    if (bgColor) {
        const parsedHex = stringToHex(bgColor);

        // If hex, convert to RGB
        if (parsedHex) {
            const parsedRGB = hexToRGB(bgColor);
            const colorStart = parsedRGB.indexOf('(');
            const colorEnd = bgColor.indexOf(')');
            [r, g, b] = bgColor
                .slice(colorStart + 1, colorEnd) // Get inner string
                .split(',') // Split on commas
                .map((v: string) => parseInt(v.trim())); // Trim spaces (if needed) and parse to int
        }
    }

    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;

    return luminance > 128 ? defaultDark : defaultLight;
}

/**
 * Given 6 digit hex code ('#ffffff'), parse to RGB
 *
 * @param hexString - A 6-digit hex color string
 * @returns An RGB string (e.g. 'rgb(56, 234, 34)') or default value ('rgb(0, 0, 0)')
 */
export function hexToRGB(hexString: string) {
    let r = 0,
        g = 0,
        b = 0;

    // Check if 7-digit hex
    if (hexString.length == 7) {
        r = parseInt(hexString.slice(1, 3), 16);
        g = parseInt(hexString.slice(3, 5), 16);
        b = parseInt(hexString.slice(5, 7), 16);
    }

    return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Little bit of a hack to parse CSS strings by creating a component without mounting it
 * and reading the hex value from the component
 *
 * @param colorString - A valid RGB, hsl, or hex string
 * @returns Parsed color string
 */
export function stringToHex(colorString: string) {
    var ctx = document.createElement('canvas').getContext('2d');
    if (ctx) {
        ctx.fillStyle = colorString;
    }
    return ctx?.fillStyle;
}
