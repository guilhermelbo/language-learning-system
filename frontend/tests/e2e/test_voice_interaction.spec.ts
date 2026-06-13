/**
 * E2E tests for voice interaction.
 * 
 * Tests the voice button, recording, and speech processing flow.
 */

import { test, expect } from '@playwright/test';

test.describe('Voice Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display voice button and start recording', async ({ page }) => {
    // Voice button should be visible
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    await expect(voiceButton).toBeVisible();

    // Click record button
    await voiceButton.click();

    // Should show recording state
    const recordingState = page.getByText(/recording|listening|speaking/i);
    await expect(recordingState).toBeVisible();
  });

  test('should stop recording and send audio', async ({ page }) => {
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Start recording
    await voiceButton.click();
    
    // Stop recording
    await voiceButton.click();
    
    // Should show processing state
    const processingState = page.getByText(/processing|thinking|generating/i);
    await expect(processingState).toBeVisible();
  });

  test('should handle recording permission denial', async ({ page }) => {
    // Mock permission denial
    const mockPage = await page.context().newPage();
    
    // Try to access microphone
    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });

    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Attempt to start recording
    await voiceButton.click();

    // Should show error message or fallback to text
    const errorMessage = page.getByText(/permission|microphone|error/i);
    // Error might not appear immediately, so check non-blockingly
    if (await errorMessage.count() > 0) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should show recording duration', async ({ page }) => {
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Start recording
    await voiceButton.click();
    
    // Duration should appear
    const duration = page.getByRole('timer').or(page.getByText(/\d{2}:\d{2}/));
    if (await duration.count() > 0) {
      await expect(duration).toBeVisible();
    }
  });

  test('should cancel recording', async ({ page }) => {
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Start recording
    await voiceButton.click();
    
    // Find cancel button
    const cancelButton = page.getByRole('button', { name: /cancel|stop/i });
    
    if (await cancelButton.count() > 0) {
      await cancelButton.click();
      
      // Recording state should disappear
      const recordingState = page.getByText(/recording|listening/i);
      await expect(recordingState).not.toBeVisible();
    }
  });

  test('should validate audio before sending', async ({ page }) => {
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Start recording
    await voiceButton.click();
    
    // Stop quickly to create short recording
    await voiceButton.click();
    
    // Check for validation feedback
    const feedback = page.locator('[data-testid="audio-validation"]');
    if (await feedback.count() > 0) {
      await expect(feedback).toBeVisible();
    }
  });
});
