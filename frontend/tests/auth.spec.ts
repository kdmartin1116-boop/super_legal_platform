import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should allow user registration and login', async ({ page }) => {
    await page.goto('/');
    
    // Click register button
    await page.click('text=Register');
    
    // Fill registration form
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="fullName"]', 'Test User');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');
    
    // Submit registration
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard or show success message
    await expect(page).toHaveURL(/dashboard|success/);
  });

  test('should show error for invalid login', async ({ page }) => {
    await page.goto('/login');
    
    // Fill with invalid credentials
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'wrong');
    
    // Submit login
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });

  test('should logout user successfully', async ({ page }) => {
    // First login with valid credentials
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL(/dashboard/);
    
    // Click logout
    await page.click('text=Logout');
    
    // Should redirect to login page
    await expect(page).toHaveURL(/login|\/$/);
  });
});