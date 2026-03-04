import { expect, test } from '@playwright/test'

test('app boots and shows auth entry', async ({ page }) => {
  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ session: null }),
    })
  })

  await page.goto('/')

  await expect(page.locator('input[type="email"]')).toBeVisible()
  await expect(page.locator('input[type="password"]')).toBeVisible()
})
