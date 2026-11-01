import { test, expect } from '@playwright/test';

test.describe('Nirikshan Regulatory Scrutiny Flow', () => {
  test('Smoke Test: Login, Applicant Portal, and Officer Scrutiny Console', async ({ page }) => {
    // 1. Visit Login Page
    await page.goto('/login');
    await expect(page).toHaveTitle(/Nirikshan \(निरीक्षण\)/);
    await expect(page.locator('text=Nirikshan')).toBeVisible();
    await expect(page.locator('text=(निरीक्षण)')).toBeVisible();

    // 2. Click Quick Login as Applicant
    const applicantBtn = page.locator('button:has-text("Applicant Portal")');
    await expect(applicantBtn).toBeVisible();
    await applicantBtn.click();

    // 3. Verify Applicant Portal rendered
    await expect(page).toHaveURL(/.*applicant/);
    await expect(page.locator('text=Pre-Submission Self-Assessment')).toBeVisible();
    await expect(page.locator('text=Upload Documents & Live Pipeline')).toBeVisible();
    await expect(page.locator('text=Rectification & Deficiency Thread')).toBeVisible();

    // 4. Test Pre-Submission Self Assessment rules
    await expect(page.locator('text=Minimum Campus Land Area')).toBeVisible();
    await expect(page.locator('text=Cadre Distribution Ratio (1:2:6)')).toBeVisible();

    // 5. Switch to Rectification Tab
    await page.click('button:has-text("Rectification & Deficiency Thread")');
    await expect(page.locator('text=Pending Deficiencies')).toBeVisible();

    // 6. Switch to Officer Console
    await page.click('button:has-text("Officer Scrutiny Console")');
    await expect(page).toHaveURL(/.*officer/);
    await expect(page.locator('text=AICTE Scrutiny Officer Console')).toBeVisible();

    // 7. Verify Officer Console Tabs
    await expect(page.locator('button:has-text("Document Viewer (pdf.js)")')).toBeVisible();
    await expect(page.locator('button:has-text("Revision Time Machine")')).toBeVisible();
    await expect(page.locator('button:has-text("Integrity Network")')).toBeVisible();
    await expect(page.locator('button:has-text("Geotag Map")')).toBeVisible();
    await expect(page.locator('button:has-text("Trust Ladder & Findings")')).toBeVisible();
    await expect(page.locator('button:has-text("\"Ask Why\" Assistant")')).toBeVisible();
    await expect(page.locator('button:has-text("Deficiency Letter Generator")')).toBeVisible();

    // 8. Test Revision Time Machine
    await page.click('button:has-text("Revision Time Machine")');
    await expect(page.locator('text=Document Diff Highlights')).toBeVisible();

    // 9. Test Geotag Map
    await page.click('button:has-text("Geotag Map")');
    await expect(page.locator('text=Geotag Physical Verification Map')).toBeVisible();

    // 10. Test Deficiency Letter Generator
    await page.click('button:has-text("Deficiency Letter Generator")');
    await expect(page.locator('text=ALL INDIA COUNCIL FOR TECHNICAL EDUCATION')).toBeVisible();
    await expect(page.locator('text=FORMAL DEFICIENCY OBSERVATION NOTICE')).toBeVisible();

    // 11. Test Bilingual Toggle
    const langBtn = page.locator('button[title="Toggle English / हिंदी"]');
    await langBtn.click();
    await expect(page.locator('text=निरीक्षण')).toBeVisible();
  });
});
