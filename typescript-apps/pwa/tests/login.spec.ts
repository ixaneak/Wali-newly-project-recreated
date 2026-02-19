import { test, expect } from '@playwright/test';
import * as fs from 'fs';

test('User Login Flow (Phone + OTP)', async ({ page }) => {
    // Increase timeout for this test
    test.setTimeout(120000);

    page.on('console', msg => console.log(`PAGE CONSOLE: ${msg.text()}`));
    page.on('pageerror', exception => console.log(`PAGE ERROR: ${exception}`));

    // 1. Go to Login Page with Test Mode enabled
    await page.goto('/login?testMode=true', { waitUntil: 'domcontentloaded', timeout: 60000 });

    // Debug: Dump content immediately after load
    const content = await page.content();
    fs.writeFileSync('page_dump_debug.html', content);
    console.log('Dumped page content to page_dump_debug.html');

    // Diagnostic checks
    const loading = page.getByText('Loading...');
    if (await loading.isVisible()) {
        console.log('PAGE STATUS: STUCK LOADING');
    } else {
        console.log('PAGE STATUS: Loading indicator NOT visible (Good)');
    }

    const phoneInput = page.locator('input[type="tel"]');

    // Check visibility properties
    const isVisible = await phoneInput.isVisible();
    console.log(`Phone Input isVisible: ${isVisible}`);

    if (!isVisible) {
        // Log why
        const box = await phoneInput.boundingBox();
        console.log(`Phone Input BoundingBox: ${JSON.stringify(box)}`);
        // Check opacity/styles
        const opacity = await phoneInput.evaluate(el => window.getComputedStyle(el).opacity);
        const display = await phoneInput.evaluate(el => window.getComputedStyle(el).display);
        const visibility = await phoneInput.evaluate(el => window.getComputedStyle(el).visibility);
        console.log(`Phone Input Styles - Opacity: ${opacity}, Display: ${display}, Visibility: ${visibility}`);
    }

    // Explicit wait for visibility with long timeout
    // await expect(phoneInput).toBeVisible({ timeout: 30000 });

    // 2. Enter Phone Number
    await phoneInput.fill('0707070707', { force: true });
    await page.getByRole('button', { name: /Recevoir le code/i }).click();

    // 3. Verify OTP Page Load
    await expect(page).toHaveURL(/\/verify-otp/);
    await expect(page.getByText('Code de vérification', { exact: false })).toBeVisible({ timeout: 30000 });
});
