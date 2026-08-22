import { expect, test } from '@playwright/test'
import { registerTenant } from './helpers.js'

test('audit log records tenant registration, role, and user changes', async ({ page }) => {
  await registerTenant(page)

  await page.click('nav >> text=Roles')
  await page.waitForSelector('text=System')
  await page.click('button:has-text("New role")')
  const createRoleForm = page.locator('form').filter({ has: page.locator('button:has-text("Create role")') })
  await createRoleForm.getByRole('textbox', { name: 'Role name' }).fill('Auditable Role')
  await createRoleForm.locator('button:has-text("Create role")').click()
  await page.waitForSelector('text=Auditable Role')

  await page.click('nav >> text=Audit log')
  await page.waitForSelector('text=Audit log')

  await expect(page.locator('tr', { hasText: 'tenant.registered' })).toBeVisible()
  await expect(page.locator('tr', { hasText: 'role.created' }).filter({ hasText: 'Auditable Role' })).toBeVisible()
})
