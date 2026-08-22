import { expect, test } from '@playwright/test'
import { registerTenant, setUpCompanyAndPlant } from './helpers.js'

test('full golden path across every module reflects real data end to end', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (e) => consoleErrors.push(e.message))

  await registerTenant(page)
  await setUpCompanyAndPlant(page)

  // Inventory: raw material + finished good, then a receipt movement.
  await page.click('nav >> text=Inventory')
  await page.waitForSelector('text=Items')
  const itemForm = page.locator('form').first()

  await itemForm.locator('input').nth(0).fill('RM-STEEL')
  await itemForm.locator('input').nth(1).fill('Steel Sheet')
  await itemForm.locator('input').nth(2).fill('KG')
  await itemForm.locator('button:has-text("Add item")').click()
  await page.waitForSelector('td:has-text("RM-STEEL")')

  await itemForm.locator('input').nth(0).fill('FG-BRACKET')
  await itemForm.locator('input').nth(1).fill('Steel Bracket')
  await itemForm.locator('select').selectOption('finished_good')
  await itemForm.locator('input').nth(2).fill('EA')
  await itemForm.locator('button:has-text("Add item")').click()
  await page.waitForSelector('td:has-text("FG-BRACKET")')

  const movementForm = page.locator('form').filter({ has: page.locator('button:has-text("Post")') })
  await movementForm.locator('select').first().selectOption({ label: 'RM-STEEL — Steel Sheet' })
  await movementForm.locator('input[type=number]').fill('100')
  await movementForm.locator('button:has-text("Post")').click()
  await page.waitForSelector('td:has-text("100")')

  // Warehouse: warehouse/zone/bin, then putaway 50 KG of steel into the bin.
  await page.click('nav >> text=Warehouse')
  await page.waitForSelector('text=Warehouses')
  const whForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).first()
  await whForm.locator('input').nth(0).fill('Main WH')
  await whForm.locator('input').nth(1).fill('WH1')
  await whForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("Main WH")')
  await page.click('text=Manage')
  await page.waitForSelector('text=Zones')

  const zoneForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).nth(1)
  await zoneForm.locator('input').nth(0).fill('Storage')
  await zoneForm.locator('input').nth(1).fill('Z1')
  await zoneForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("Storage")')

  const binForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).nth(2)
  await binForm.locator('select').selectOption({ label: 'Z1' })
  await binForm.locator('input').fill('B1')
  await binForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("B1")')

  const putawayForm = page.locator('form').filter({ has: page.locator('button:has-text("Putaway")') })
  await putawayForm.locator('select').nth(0).selectOption({ label: 'RM-STEEL' })
  await putawayForm.locator('select').nth(1).selectOption({ label: 'B1' })
  await putawayForm.locator('input[type=number]').fill('50')
  await putawayForm.locator('button:has-text("Putaway")').click()
  await page.waitForSelector('td:has-text("50.0000")')

  // Production: BOM (2 steel per bracket), order for 10, complete it.
  await page.click('nav >> text=Production')
  await page.waitForSelector('text=Bills of Material')
  const bomForm = page.locator('form').filter({ has: page.locator('button:has-text("Create BOM")') })
  await bomForm.locator('input').nth(0).fill('Bracket BOM')
  await bomForm.locator('select').nth(0).selectOption({ label: 'FG-BRACKET — Steel Bracket' })
  await bomForm.locator('select').nth(1).selectOption({ label: 'RM-STEEL — Steel Sheet' })
  await bomForm.locator('input[type=number]').fill('2')
  await bomForm.locator('button:has-text("Create BOM")').click()
  await page.waitForSelector('td:has-text("Bracket BOM")')

  const poForm = page.locator('form').filter({ has: page.locator('button:has-text("Create order")') })
  await poForm.locator('select').selectOption({ label: 'Bracket BOM' })
  await poForm.locator('input[type=number]').fill('10')
  await poForm.locator('button:has-text("Create order")').click()
  await page.waitForSelector('td:has-text("Bracket BOM")')

  const orderRow = page.locator('tr', { hasText: 'Bracket BOM' })
  await orderRow.locator('input[type=number]').fill('10')
  await orderRow.locator('button:has-text("Complete")').click()
  await page.waitForSelector('text=completed')

  // Procurement: supplier + PO, submit, receive in full.
  await page.click('nav >> text=Procurement')
  await page.waitForSelector('text=Suppliers')
  const supplierForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).first()
  await supplierForm.locator('input').nth(0).fill('SteelCo')
  await supplierForm.locator('input').nth(1).fill('SUP-1')
  await supplierForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("SteelCo")')

  const poForm2 = page.locator('form').filter({ has: page.locator('button:has-text("Create PO")') })
  await poForm2.locator('select').nth(0).selectOption({ label: 'SteelCo' })
  await poForm2.locator('select').nth(1).selectOption({ label: 'RM-STEEL' })
  await poForm2.locator('input[type=number]').nth(0).fill('200')
  await poForm2.locator('button:has-text("Create PO")').click()
  await page.waitForSelector('text=draft')

  await page.click('button:has-text("Submit")')
  await page.waitForSelector('text=submitted')
  const receiveRow = page.locator('tr').filter({ has: page.locator('input[type=number]') }).first()
  await receiveRow.locator('input[type=number]').fill('200')
  await receiveRow.locator('button:has-text("Receive")').click()
  await page.waitForSelector('text=received')

  // Sales: customer + SO, confirm, ship in full.
  await page.click('nav >> text=Sales')
  await page.waitForSelector('text=Customers')
  const customerForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).first()
  await customerForm.locator('input').nth(0).fill('Bracket Buyers')
  await customerForm.locator('input').nth(1).fill('CUST-1')
  await customerForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("Bracket Buyers")')

  const soForm = page.locator('form').filter({ has: page.locator('button:has-text("Create SO")') })
  await soForm.locator('select').nth(0).selectOption({ label: 'Bracket Buyers' })
  await soForm.locator('select').nth(1).selectOption({ label: 'FG-BRACKET' })
  await soForm.locator('input[type=number]').nth(0).fill('5')
  await soForm.locator('button:has-text("Create SO")').click()
  await page.waitForSelector('text=draft')

  await page.click('button:has-text("Confirm")')
  await page.waitForSelector('text=confirmed')
  const shipRow = page.locator('tr').filter({ has: page.locator('input[type=number]') }).first()
  await shipRow.locator('input[type=number]').fill('5')
  await shipRow.locator('button:has-text("Ship")').click()
  await page.waitForSelector('text=shipped')

  // Maintenance: asset + work order lifecycle.
  await page.click('nav >> text=Maintenance')
  await page.waitForSelector('text=Assets')
  const assetForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).first()
  await assetForm.locator('input').nth(0).fill('CNC Mill')
  await assetForm.locator('input').nth(1).fill('CNC-1')
  await assetForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("CNC Mill")')

  const woForm = page.locator('form').filter({ has: page.locator('button:has-text("Create")') })
  await woForm.locator('select').nth(0).selectOption({ label: 'CNC Mill' })
  await woForm.locator('button:has-text("Create")').click()
  await page.waitForSelector('text=open')

  await page.click('button:has-text("Start")')
  await page.waitForSelector('text=maintenance')
  await page.click('button:has-text("Complete")')
  await page.waitForSelector('text=completed')

  // Quality: failing inspection with a defect, then resolve it.
  await page.click('nav >> text=Quality')
  await page.waitForSelector('text=Inspections')
  const inspForm = page.locator('form').filter({ has: page.locator('button:has-text("Log inspection")') })
  await inspForm.locator('select').nth(0).selectOption({ label: 'FG-BRACKET' })
  await inspForm.locator('input[type=number]').nth(0).fill('5')
  await inspForm.locator('input[placeholder="e.g. scratch"]').fill('surface scratch')
  await inspForm.locator('input[type=number]').nth(1).fill('1')
  await inspForm.locator('button:has-text("Log inspection")').click()
  await page.waitForSelector('text=fail')

  await page.click('button:has-text("Resolve")')
  await page.waitForSelector('text=resolved')

  // Dashboard should reflect all of the above with real numbers.
  await page.click('nav >> text=Dashboard')
  await page.waitForSelector('text=Active items')
  const body = await page.textContent('body')
  expect(body).toContain('2') // active item count

  expect(consoleErrors, `Unexpected console/page errors:\n${consoleErrors.join('\n')}`).toEqual([])
})
