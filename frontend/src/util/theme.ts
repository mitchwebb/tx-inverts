/**
 * Simple helper to retrieve CSS variable values
 *
 * @param themeElement - Selector string for relevant element with access to vars
 * @param cssVarString - Desired CSS variable value string
 * @returns CSS variable value || undefined
 */
export function getCSSValue(selector: string, cssVarString: string) {
    const themeWrapper = document.querySelector(selector);
    let value;
    if (themeWrapper) {
        const themes = getComputedStyle(themeWrapper);
        value = themes.getPropertyValue(cssVarString);
    }
    return value;
}
