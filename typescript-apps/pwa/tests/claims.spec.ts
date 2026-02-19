import { test, expect } from '@playwright/test';

test('Admin Claims Management Flow', async ({ page }) => {
    page.on('console', msg => console.log(`PAGE CONSOLE: ${msg.text()}`));
    page.on('pageerror', exception => console.log(`PAGE ERROR: ${exception}`));

    // 1. Login as Admin first
    await page.goto('/admin');
    await expect(page.getByRole('heading', { name: 'Wali Admin' })).toBeVisible();

    await page.getByPlaceholder('admin@wali.com').fill('admin@wali.com');
    await page.getByPlaceholder('••••••••').fill('admin123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    // Wait for dashboard redirect
    await expect(page).toHaveURL(/\/admin\/dash/);

    // 2. Navigate to Claims page
    await page.getByRole('link', { name: 'Claims' }).click();
    await expect(page).toHaveURL(/\/admin\/claims/);

    // 3. Verify Claims page loads with header
    await expect(page.getByText('Gestion des Claims')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Suivi et approbation des demandes d\'indemnisation')).toBeVisible();

    // 4. Check stats cards are visible
    await expect(page.getByText('Soumis')).toBeVisible();
    await expect(page.getByText('Examen')).toBeVisible();
    await expect(page.getByText('Payés')).toBeVisible();
    await expect(page.getByText('Rejetés')).toBeVisible();

    // 5. Test tab filtering
    const tabs = ['TOUS', 'DÉPOSÉS', 'EXAMEN', 'APPROUVÉS', 'REJETÉS', 'PAYÉS'];
    for (const tab of tabs) {
        await page.getByRole('tab', { name: tab }).click();
        await page.waitForTimeout(300);
        
        // Check that the table or empty state is visible
        const hasTable = await page.locator('table tbody tr').count() > 0;
        const hasEmptyState = await page.getByText('AUCUN CLAIM TROUVÉ').isVisible();
        expect(hasTable || hasEmptyState).toBeTruthy();
    }

    // 6. Test search functionality
    const searchInput = page.getByPlaceholder('RECHERCHER ID / USER...');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('CLM-2024');
    await page.waitForTimeout(500);
    
    // Clear search
    await searchInput.clear();

    // 7. Test refresh button
    await page.getByRole('button', { name: 'RefreshCw' }).click();
    await expect(page.locator('table')).toBeVisible();

    // 8. Verify export button exists
    await expect(page.getByText('EXPORTER CSV')).toBeVisible();
});

test('Claims page shows mock data warning when API fails', async ({ page }) => {
    // Block the API request to simulate failure
    await page.route('**/api/v1/partners/*/incidents/admin/all', route => route.abort());

    // Login
    await page.goto('/admin');
    await page.getByPlaceholder('admin@wali.com').fill('admin@wali.com');
    await page.getByPlaceholder('••••••••').fill('admin123');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await page.waitForURL(/\/admin\/dash/);
    await page.goto('/admin/claims');

    // Check for mock data warning
    await expect(page.getByText('Mode démonstration')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Données simulées affichées')).toBeVisible();
});
