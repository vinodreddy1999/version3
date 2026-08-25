import { expect, test } from '@playwright/test'
import { randomSlug, registerTenant } from './helpers.js'

test('super admin can impersonate a user and return to their own account', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (e) => consoleErrors.push(e.message))

  await registerTenant(page)

  const clerkEmail = `clerk-${randomSlug()}@example.com`
  const clerkPassword = 'AnotherSecret123!'

  await page.click('nav >> text=Users')
  await page.waitForSelector('text=Invite user')
  await page.click('button:has-text("Invite user")')
  await page.waitForSelector('text=Temporary password')
  const inviteForm = page.locator('form').filter({ hasText: 'Create user' })
  await inviteForm.locator('input').nth(0).fill('Carla Clerk')
  await inviteForm.locator('input').nth(1).fill(clerkEmail)
  await inviteForm.locator('input').nth(2).fill(clerkPassword)
  await page.click('button:has-text("Create user")')
  await page.waitForSelector('text=Carla Clerk')

  const clerkRow = page.locator('tr', { hasText: 'Carla Clerk' })
  await clerkRow.locator('button:has-text("Edit")').click()
  await page.waitForSelector('text=Impersonate this user')

  await page.click('button:has-text("Impersonate")')
  await page.waitForURL('/')
  await page.waitForSelector('text=Dashboard')

  await expect(page.locator('text=Viewing as Carla Clerk')).toBeVisible()
  await expect(page.locator('text=impersonated by Ada Admin')).toBeVisible()
  // The impersonated clerk has no admin permissions, so the Admin nav
  // section — visible to the superuser a moment ago — should be gone.
  await expect(page.locator('nav >> text=Admin')).toHaveCount(0)

  await page.click('button:has-text("Return to admin")')
  await page.waitForSelector('text=Viewing as Carla Clerk', { state: 'detached' })
  await expect(page.locator('nav >> text=Users')).toBeVisible()

  expect(consoleErrors, `Unexpected console/page errors:\n${consoleErrors.join('\n')}`).toEqual([])
})

test('non-superuser cannot see an impersonate option', async ({ page }) => {
  const tenant = await registerTenant(page)

  const clerkEmail = `clerk-${randomSlug()}@example.com`
  const clerkPassword = 'AnotherSecret123!'

  await page.click('nav >> text=Users')
  await page.waitForSelector('text=Invite user')
  await page.click('button:has-text("Invite user")')
  await page.waitForSelector('text=Temporary password')
  const inviteForm = page.locator('form').filter({ hasText: 'Create user' })
  await inviteForm.locator('input').nth(0).fill('Carla Clerk')
  await inviteForm.locator('input').nth(1).fill(clerkEmail)
  await inviteForm.locator('input').nth(2).fill(clerkPassword)
  await page.click('button:has-text("Create user")')
  await page.waitForSelector('text=Carla Clerk')

  // Grant the clerk admin:manage_users directly via a role so they can
  // reach the Users page, then confirm they still don't see Impersonate —
  // that action is gated on is_superuser, not the permission.
  await page.click('nav >> text=Roles')
  await page.waitForSelector('text=System')
  await page.click('button:has-text("New role")')
  const createRoleForm = page.locator('form').filter({ has: page.locator('button:has-text("Create role")') })
  await createRoleForm.getByRole('textbox', { name: 'Role name' }).fill('User Manager')
  await createRoleForm.getByRole('checkbox', { name: 'admin:manage_users' }).click()
  await createRoleForm.locator('button:has-text("Create role")').click()
  await page.waitForSelector('text=User Manager')

  await page.click('nav >> text=Users')
  await page.waitForSelector('text=Carla Clerk')
  const clerkRow = page.locator('tr', { hasText: 'Carla Clerk' })
  await clerkRow.locator('button:has-text("Edit")').click()
  await page.waitForSelector('text=Roles')
  await page.click(`label:has-text("User Manager")`)
  await page.click('button:has-text("Save roles")')
  await page.waitForSelector('text=Save roles', { state: 'detached' })

  await page.click('text=Log out')
  await page.waitForURL('**/login')
  const loginForm = page.locator('form').filter({ has: page.locator('button:has-text("Sign in")') })
  await loginForm.locator('input').nth(0).fill(tenant.slug)
  await loginForm.locator('input').nth(1).fill(clerkEmail)
  await loginForm.locator('input').nth(2).fill(clerkPassword)
  await loginForm.locator('button[type=submit]').click()
  await page.waitForURL('/')
  await page.waitForSelector('text=Dashboard')

  await page.click('nav >> text=Users')
  await page.waitForSelector('text=Invite user')
  const anyRow = page.locator('tbody tr').first()
  await anyRow.locator('button:has-text("Edit")').click()
  await expect(page.locator('text=Impersonate this user')).toHaveCount(0)
})
