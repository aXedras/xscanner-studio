import { expect, test } from '@playwright/test'

test('user can sign in and reaches authenticated app shell', async ({ page }) => {
  let hasSession = false

  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session: hasSession
          ? {
              id: 'user-1',
              email: 'max@example.com',
              user_metadata: { display_name: 'Max Mustermann' },
            }
          : null,
      }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    hasSession = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ hasSession: true }),
    })
  })

  await page.route('**/api/v1/extractions/status-counts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('secret-password')
  await page.locator('form button[type="submit"]').click()

  await expect(page.getByRole('button', { name: 'Abmelden' })).toBeVisible()
  await expect(page.getByText('Willkommen zurück! 👋')).toBeVisible()
})

test('user sees error and stays on login with wrong password', async ({ page }) => {
  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ session: null }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        error: {
          code: 'AUTH_INVALID_CREDENTIALS',
          message: 'Invalid login credentials',
        },
      }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('wrong-password')
  await page.locator('form button[type="submit"]').click()

  await expect(page.getByText('Nicht autorisiert. Bitte melde dich erneut an.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Abmelden' })).toHaveCount(0)
  await expect(page.locator('input[type="email"]')).toBeVisible()
})

test('user can log out from authenticated app shell', async ({ page }) => {
  let hasSession = false
  let signOutCalls = 0

  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session: hasSession
          ? {
              id: 'user-1',
              email: 'max@example.com',
              user_metadata: { display_name: 'Max Mustermann' },
            }
          : null,
      }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    hasSession = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ hasSession: true }),
    })
  })

  await page.route('**/api/v1/auth/sign-out', async route => {
    signOutCalls += 1
    hasSession = false
    await route.fulfill({
      status: 204,
    })
  })

  await page.route('**/api/v1/extractions/status-counts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('secret-password')
  await page.locator('form button[type="submit"]').click()

  const logoutButton = page.getByRole('button', { name: 'Abmelden' })
  await expect(logoutButton).toBeVisible()

  await logoutButton.click()

  await expect(page.locator('input[type="email"]')).toBeVisible()
  await expect(page.locator('input[type="password"]')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Abmelden' })).toHaveCount(0)
  expect(signOutCalls).toBe(1)
})

test('user can toggle appearance and language in authenticated shell', async ({ page }) => {
  let hasSession = false

  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session: hasSession
          ? {
              id: 'user-1',
              email: 'max@example.com',
              user_metadata: { display_name: 'Max Mustermann' },
            }
          : null,
      }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    hasSession = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ hasSession: true }),
    })
  })

  await page.route('**/api/v1/extractions/status-counts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('secret-password')
  await page.locator('form button[type="submit"]').click()

  const themeToggle = page.getByRole('button', { name: 'Toggle theme' })
  await expect(themeToggle).toBeVisible()

  const htmlClassBefore = await page.locator('html').getAttribute('class')
  await themeToggle.click()
  const htmlClassAfter = await page.locator('html').getAttribute('class')
  expect(htmlClassAfter).not.toBe(htmlClassBefore)

  const languageToggle = page.getByRole('button', { name: /Switch language to (EN|DE)/ })
  await languageToggle.click()

  await expect(page.getByRole('link', { name: 'Shipments' })).toBeVisible()
})

test('selected theme persists after reload', async ({ page }) => {
  let hasSession = false

  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session: hasSession
          ? {
              id: 'user-1',
              email: 'max@example.com',
              user_metadata: { display_name: 'Max Mustermann' },
            }
          : null,
      }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    hasSession = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ hasSession: true }),
    })
  })

  await page.route('**/api/v1/extractions/status-counts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('secret-password')
  await page.locator('form button[type="submit"]').click()

  const themeToggle = page.getByRole('button', { name: 'Toggle theme' })
  await expect(themeToggle).toBeVisible()

  const html = page.locator('html')
  const classBefore = await html.getAttribute('class')
  await themeToggle.click()
  const classAfterToggle = await html.getAttribute('class')
  expect(classAfterToggle).not.toBe(classBefore)

  await page.reload()

  await expect(page.getByRole('button', { name: 'Toggle theme' })).toBeVisible()
  const classAfterReload = await html.getAttribute('class')
  expect(classAfterReload).toBe(classAfterToggle)
})

test('selected language persists after reload', async ({ page }) => {
  let hasSession = false

  await page.route('**/api/v1/auth/session', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session: hasSession
          ? {
              id: 'user-1',
              email: 'max@example.com',
              user_metadata: { display_name: 'Max Mustermann' },
            }
          : null,
      }),
    })
  })

  await page.route('**/api/v1/auth/sign-in', async route => {
    hasSession = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ hasSession: true }),
    })
  })

  await page.route('**/api/v1/extractions/status-counts**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 }),
    })
  })

  await page.goto('/')

  await page.locator('input[type="email"]').fill('max@example.com')
  await page.locator('input[type="password"]').fill('secret-password')
  await page.locator('form button[type="submit"]').click()

  const languageToggle = page.getByRole('button', { name: /Switch language to (EN|DE)/ })
  await expect(languageToggle).toBeVisible()

  const switchLabel = (await languageToggle.getAttribute('aria-label')) ?? ''
  const switchesToEnglish = switchLabel.includes('EN')
  await languageToggle.click()

  if (switchesToEnglish) {
    await expect(page.getByRole('link', { name: 'Shipments' })).toBeVisible()
  } else {
    await expect(page.getByRole('link', { name: 'Orders' })).toBeVisible()
  }

  await page.reload()

  if (switchesToEnglish) {
    await expect(page.getByRole('link', { name: 'Shipments' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Switch language to DE' })).toBeVisible()
  } else {
    await expect(page.getByRole('link', { name: 'Orders' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Switch language to EN' })).toBeVisible()
  }
})
