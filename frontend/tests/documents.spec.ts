import { test, expect } from '@playwright/test';

test.describe('Document Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/);
  });

  test('should upload document successfully', async ({ page }) => {
    await page.goto('/documents');
    
    // Click upload button
    await page.click('text=Upload Document');
    
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/sample-contract.pdf');
    
    // Submit upload
    await page.click('button:has-text("Upload")');
    
    // Should show success message
    await expect(page.locator('text=Document uploaded successfully')).toBeVisible();
  });

  test('should process uploaded document', async ({ page }) => {
    await page.goto('/documents');
    
    // Assuming document is already uploaded, click on first document
    await page.click('.document-item:first-child');
    
    // Click process button
    await page.click('text=Process Document');
    
    // Wait for processing to complete
    await expect(page.locator('text=Processing complete')).toBeVisible({ timeout: 30000 });
    
    // Should show analysis results
    await expect(page.locator('.analysis-results')).toBeVisible();
  });

  test('should search documents', async ({ page }) => {
    await page.goto('/documents');
    
    // Enter search term
    await page.fill('input[placeholder*="Search"]', 'contract');
    await page.press('input[placeholder*="Search"]', 'Enter');
    
    // Should show filtered results
    await expect(page.locator('.document-item')).toHaveCount({ min: 1 });
  });
});