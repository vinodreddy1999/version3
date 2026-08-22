import type { Page } from '@playwright/test'

export function randomSlug(): string {
  return Math.random().toString(36).slice(2, 10)
}

export interface RegisteredTenant {
  slug: string
  adminEmail: string
  adminPassword: string
}

/** Registers a fresh tenant + admin user via the UI and leaves the page on the dashboard. */
export async function registerTenant(page: Page): Promise<RegisteredTenant> {
  const slug = `acme-${randomSlug()}`
  const adminEmail = `ada-${randomSlug()}@example.com`
  const adminPassword = 'SuperSecret123!'

  await page.goto('/login')
  await page.click('text=New organization')
  const form = page.locator('form').filter({ hasText: 'Create organization' })
  await form.locator('input').nth(0).fill(`Acme ${slug}`)
  await form.locator('input').nth(1).fill(slug)
  await form.locator('input').nth(2).fill('Ada Admin')
  await form.locator('input').nth(3).fill(adminEmail)
  await form.locator('input').nth(4).fill(adminPassword)
  await form.locator('button[type=submit]').click()
  await page.waitForURL('/')
  await page.waitForSelector('text=Dashboard')

  return { slug, adminEmail, adminPassword }
}

/** Creates a company + plant via the Organization page and selects the plant in the top bar. */
export async function setUpCompanyAndPlant(page: Page): Promise<void> {
  await page.click('nav >> text=Organization')
  await page.waitForSelector('text=Companies')

  const companyForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).first()
  await companyForm.locator('input').nth(0).fill('Acme East')
  await companyForm.locator('input').nth(1).fill('ACME-E')
  await companyForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("Acme East")')

  const plantForm = page.locator('form').filter({ has: page.locator('button:has-text("Add")') }).nth(1)
  await plantForm.locator('select').selectOption({ label: 'Acme East' })
  await plantForm.locator('input').nth(0).fill('Plant 1')
  await plantForm.locator('input').nth(1).fill('P1')
  await plantForm.locator('button:has-text("Add")').click()
  await page.waitForSelector('td:has-text("Plant 1")')

  await page.selectOption('header select', { label: 'Plant 1' })
}
