import { expect, test } from '@playwright/test'
import { inviteUser, randomSlug, registerTenant } from './helpers.js'

test('custom role + invited user get exactly the granted permissions in the UI', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (e) => consoleErrors.push(e.message))

  const tenant = await registerTenant(page)

  await page.waitForSelector('text=Admin')
  await page.click('nav >> text=Roles')
  await page.waitForSelector('text=System')

  await page.click('button:has-text("New role")')
  await page.waitForSelector('text=Role name')
  const createRoleForm = page.locator('form').filter({ has: page.locator('button:has-text("Create role")') })
  await createRoleForm.getByRole('textbox', { name: 'Role name' }).fill('Warehouse Clerk')
  await createRoleForm.getByRole('checkbox', { name: 'inventory:read' }).click()
  await createRoleForm.getByRole('checkbox', { name: 'warehouse:write' }).click()
  await createRoleForm.locator('button:has-text("Create role")').click()
  await page.waitForSelector('text=Warehouse Clerk')

  const clerkEmail = `clerk-${randomSlug()}@example.com`
  const clerkPassword = 'AnotherSecret123!'

  await inviteUser(page, 'Carla Clerk', clerkEmail, clerkPassword, 'Warehouse Clerk')

  await page.click('text=Log out')
  await page.waitForURL('**/login')
  const loginForm = page.locator('form').filter({ has: page.locator('button:has-text("Sign in")') })
  await loginForm.locator('input').nth(0).fill(tenant.slug)
  await loginForm.locator('input').nth(1).fill(clerkEmail)
  await loginForm.locator('input').nth(2).fill(clerkPassword)
  await loginForm.locator('button[type=submit]').click()
  await page.waitForURL('/')
  await page.waitForSelector('text=Dashboard')

  await expect(page.locator('text=Admin')).toHaveCount(0)

  await page.goto('/admin/users')
  await page.waitForURL('/')

  expect(consoleErrors, `Unexpected console/page errors:\n${consoleErrors.join('\n')}`).toEqual([])
})
