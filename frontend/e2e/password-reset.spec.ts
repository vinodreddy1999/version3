import { expect, test } from '@playwright/test'
import { registerTenant } from './helpers.js'

test('forgot password form shows the generic success message', async ({ page }) => {
  const tenant = await registerTenant(page)
  await page.click('text=Log out')
  await page.waitForURL('**/login')

  await page.click('text=Forgot password?')
  await page.waitForSelector('text=Send reset link')
  const form = page.locator('form').filter({ has: page.locator('button:has-text("Send reset link")') })
  await form.locator('input').nth(0).fill(tenant.slug)
  await form.locator('input').nth(1).fill(tenant.adminEmail)
  await form.locator('button:has-text("Send reset link")').click()

  await expect(page.locator('text=reset link has been sent')).toBeVisible()
})

test('reset password page without a token shows a clear error', async ({ page }) => {
  await page.goto('/reset-password')
  await expect(page.locator('text=missing its token')).toBeVisible()
})

test('reset password page rejects a bogus token with a real backend error', async ({ page }) => {
  await page.goto('/reset-password?token=not-a-real-token')
  await page.fill('input[type=password] >> nth=0', 'BrandNewPass123!')
  await page.fill('input[type=password] >> nth=1', 'BrandNewPass123!')
  await page.click('button:has-text("Update password")')
  await expect(page.locator('text=invalid or expired')).toBeVisible()
})

test('reset password page validates matching passwords client-side', async ({ page }) => {
  await page.goto('/reset-password?token=whatever')
  await page.fill('input[type=password] >> nth=0', 'BrandNewPass123!')
  await page.fill('input[type=password] >> nth=1', 'SomethingElse456!')
  await page.click('button:has-text("Update password")')
  await expect(page.locator('text=do not match')).toBeVisible()
})
