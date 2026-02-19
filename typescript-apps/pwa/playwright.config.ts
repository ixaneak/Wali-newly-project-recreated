import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    // Mobile Chrome (Pixel 5)
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    // Mobile Safari (iPhone 13)
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 13'] },
    },
    // Desktop Chrome (for admin dashboard mostly)
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120000,
  },
});
