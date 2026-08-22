import { expect, test } from '@playwright/test'
import { registerTenant, setUpCompanyAndPlant } from './helpers.js'

test('quality inspection attachment upload and download', async ({ page }) => {
  await registerTenant(page)
  await setUpCompanyAndPlant(page)

  await page.click('nav >> text=Inventory')
  await page.waitForSelector('text=Items')
  const itemForm = page.locator('form').filter({ has: page.locator('button:has-text("Add item")') })
  await itemForm.locator('input').nth(0).fill('RM-ATT')
  await itemForm.locator('input').nth(1).fill('Attachable Item')
  await itemForm.locator('button:has-text("Add item")').click()
  await page.waitForSelector('td:has-text("RM-ATT")')

  await page.click('nav >> text=Quality')
  await page.waitForSelector('text=Inspections')
  const inspectionForm = page.locator('form').filter({ has: page.locator('button:has-text("Log inspection")') })
  await inspectionForm.locator('select').first().selectOption({ label: 'RM-ATT' })
  await inspectionForm.locator('input[type=number]').first().fill('5')
  await inspectionForm.locator('button:has-text("Log inspection")').click()
  await page.waitForSelector('span.font-mono:has-text("RM-ATT")')

  await page.click('button:has-text("+ Attach file")')
  await page.setInputFiles('input[type=file]', {
    name: 'inspection-note.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('inspection attachment contents'),
  })
  await page.waitForSelector('button:has-text("inspection-note.txt")')

  const downloadPromise = page.waitForEvent('download')
  await page.click('button:has-text("inspection-note.txt")')
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('inspection-note.txt')

  const path = await download.path()
  const fs = await import('node:fs')
  expect(fs.readFileSync(path!, 'utf-8')).toBe('inspection attachment contents')
})
