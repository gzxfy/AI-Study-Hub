import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';

test('a signed-in student can reopen a saved note after reloading', async ({ page }) => {
  const baseUrl = process.env.STUDYHUB_E2E_URL;
  test.skip(!baseUrl, 'Set STUDYHUB_E2E_URL to a running test instance.');

  const username = `student-${randomUUID()}`;
  const email = `${username}@example.com`;
  const password = 'BrowserTest1!';
  const title = 'Browser study note';
  const content = 'A note saved through the React form.';

  await page.goto(new URL('/register', baseUrl).href);
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Confirm password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Create account' }).click();

  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();

  await page.getByRole('link', { name: 'Create note', exact: true }).click();
  await page.getByLabel('Title', { exact: true }).fill(title);
  await page.getByLabel('Content', { exact: true }).fill(content);
  await page.getByRole('button', { name: 'Save note' }).click();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();

  await page.goto(new URL('/app/notes', baseUrl).href);
  await page.reload();
  await page.getByRole('link', { name: new RegExp(`^${title}`) }).click();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
  await expect(page.getByText(content, { exact: true })).toBeVisible();
});
