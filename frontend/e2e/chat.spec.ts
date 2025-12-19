import { test, expect } from '@playwright/test';

test.describe('Chat SSE', () => {
  test('short math returns quickly and appears in chat', async ({ page, baseURL }) => {
    // Use environment-provided test credentials or defaults
    const username = process.env.TEST_USER || 'demo_user';
    const password = process.env.TEST_PASS || 'demo_pass';

    // Navigate to login
    await page.goto(baseURL! + '/login');

    // Fill login form
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');

    // Wait for navigation to chat
    await page.waitForURL('**/chat', { timeout: 10000 });

    // Send a short math query via UI
    await page.fill('textarea[name="message"]', 'What is 2+2?');
    await page.click('button.send-button');

    // Wait for the concise reply to appear in the messages list
    await expect(page.locator('.messages .message:last-child .text')).toContainText('4', { timeout: 8000 });
  });
});
