import { expect, test } from '@playwright/test';

test('agent looks up an order, proposes a ticket, and supervisor approves it', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Demo identity').selectOption('agent');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await page.getByRole('button', { name: /Track an order/ }).click();
  await expect(page.getByText(/Order ORD-10021 is in transit/)).toBeVisible();
  await page.getByPlaceholder('Ask about an order…').fill('Open a support ticket for delayed delivery on ORD-10021');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByText(/prepared this support ticket for review/i)).toBeVisible();

  await page.getByRole('button', { name: /Demo Support Agent/ }).click();
  await page.getByLabel('Demo identity').selectOption('supervisor');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: /Action review/ }).click();
  await expect(page.getByRole('heading', { name: /Support request for ORD-10021/ })).toBeVisible();
  await page.getByRole('button', { name: 'Approve and create ticket' }).click();
  await expect(page.getByRole('status').getByText('Ticket created after supervisor approval.')).toBeVisible();
  await expect(page.getByText('No pending actions. New ticket proposals will appear here.')).toBeVisible();
});
