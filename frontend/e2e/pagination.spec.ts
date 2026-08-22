import { expect, test } from '@playwright/test'
import { registerTenant, setUpCompanyAndPlant } from './helpers.js'

test('inventory movements list pages through results with real Prev/Next controls', async ({ page }) => {
  test.slow()

  await registerTenant(page)
  await setUpCompanyAndPlant(page)

  await page.click('nav >> text=Inventory')
  await page.waitForSelector('text=Items')
  const itemForm = page.locator('form').first()
  await itemForm.locator('input').nth(0).fill('RM-STEEL')
  await itemForm.locator('input').nth(1).fill('Steel Sheet')
  await itemForm.locator('input').nth(2).fill('KG')
  await itemForm.locator('button:has-text("Add item")').click()
  await page.waitForSelector('td:has-text("RM-STEEL")')

  const movementForm = page.locator('form').filter({ has: page.locator('button:has-text("Post")') })
  for (let i = 0; i < 25; i++) {
    await movementForm.locator('select').first().selectOption({ label: 'RM-STEEL — Steel Sheet' })
    await movementForm.locator('input[type=number]').fill('1')
    await movementForm.locator('button:has-text("Post")').click()
    await page.waitForTimeout(150)
  }

  await expect(page.locator('text=1–20 of 25')).toBeVisible()
  await expect(page.locator('button:has-text("Prev")')).toBeDisabled()
  await expect(page.locator('button:has-text("Next")')).toBeEnabled()

  await page.click('button:has-text("Next")')
  await expect(page.locator('text=21–25 of 25')).toBeVisible()
  await expect(page.locator('button:has-text("Next")')).toBeDisabled()
  await expect(page.locator('button:has-text("Prev")')).toBeEnabled()

  await page.click('button:has-text("Prev")')
  await expect(page.locator('text=1–20 of 25')).toBeVisible()
})
