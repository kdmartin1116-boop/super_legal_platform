import { test, expect } from '@playwright/test';

test.describe('Document Generation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/);
  });

  test('should generate contract document', async ({ page }) => {
    await page.goto('/generation');
    
    // Select contract type
    await page.selectOption('select[name="documentType"]', 'contract');
    
    // Fill contract details
    await page.fill('input[name="party1"]', 'Company A');
    await page.fill('input[name="party2"]', 'Company B');
    await page.fill('textarea[name="terms"]', 'Software development services for 6 months');
    await page.selectOption('select[name="jurisdiction"]', 'New York');
    
    // Generate document
    await page.click('button:has-text("Generate Document")');
    
    // Wait for generation to complete
    await expect(page.locator('text=Document generated successfully')).toBeVisible({ timeout: 15000 });
    
    // Should show generated document
    await expect(page.locator('.generated-document')).toBeVisible();
  });

  test('should customize document template', async ({ page }) => {
    await page.goto('/generation/templates');
    
    // Select NDA template
    await page.click('.template-card:has-text("NDA")');
    
    // Customize template
    await page.fill('input[name="companyName"]', 'Tech Corp');
    await page.fill('input[name="effectivePeriod"]', '2 years');
    await page.selectOption('select[name="governingLaw"]', 'California');
    
    // Generate from template
    await page.click('button:has-text("Generate from Template")');
    
    // Should show customized document
    await expect(page.locator('.generated-document')).toContainText('Tech Corp');
    await expect(page.locator('.generated-document')).toContainText('2 years');
  });

  test('should save generated document', async ({ page }) => {
    await page.goto('/generation');
    
    // Generate a simple document first
    await page.selectOption('select[name="documentType"]', 'letter');
    await page.fill('textarea[name="content"]', 'This is a test legal letter');
    await page.click('button:has-text("Generate Document")');
    
    // Wait for generation
    await page.waitForSelector('.generated-document');
    
    // Save document
    await page.click('button:has-text("Save Document")');
    
    // Should show save confirmation
    await expect(page.locator('text=Document saved successfully')).toBeVisible();
  });
});