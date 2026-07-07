import { test } from '@playwright/test';

// Test for pulling up mobile browser for manual testing
test('test browser', async ({ page }) => {
    // point this to wherever you want
    await page.goto('http://localhost:5173/');

    // keep browser open
    await page.pause();
});
