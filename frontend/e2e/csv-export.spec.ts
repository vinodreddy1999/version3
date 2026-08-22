import { expect, test } from '@playwright/test'
import { registerTenant, setUpCompanyAndPlant } from './helpers.js'

test('inventory items export button downloads a CSV', async ({ page }) => {
  await registerTenant(page)
  await setUpCompanyAndPlant(page)

  await page.click('nav >> text=Inventory')
  await page.waitForSelector('text=Items')

  const itemForm = page.locator('form').filter({ has: page.locator('button:has-text("Add item")') })
  await itemForm.locator('input').nth(0).fill('SMOKE-E2E')
  await itemForm.locator('input').nth(1).fill('Smoke Item')
  await itemForm.locator('button:has-text("Add item")').click()
  await page.waitForSelector('td:has-text("SMOKE-E2E")')

  const downloadPromise = page.waitForEvent('download')
  await page.click('button:has-text("Export CSV")')
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('inventory_items.csv')

  const path = await download.path()
  const fs = await import('node:fs')
  const content = fs.readFileSync(path!, 'utf-8')
  expect(content).toContain('SKU,Name,Type,UoM,Reorder Point,Active')
  expect(content).toContain('SMOKE-E2E')
})
