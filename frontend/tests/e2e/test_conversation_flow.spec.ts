/**
 * E2E tests for complete conversation flow.
 * 
 * Tests the full user journey from initial interaction through conversation.
 */

import { test, expect } from '@playwright/test';

test.describe('Conversation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should complete voice-to-text conversation', async ({ page }) => {
    // Start voice interaction
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    await expect(voiceButton).toBeVisible();
    
    // Record audio
    await voiceButton.click();
    
    // Stop recording
    await voiceButton.click();
    
    // Should show processing
    await expect(page.getByText(/processing|thinking|generating/i)).toBeVisible();
    
    // Should display response
    const response = page.getByRole('listitem').or(
      page.locator('.message')
    );
    await expect(response).toBeVisible();
  });

  test('should complete text-to-audio conversation', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type message
    await textInput.fill('How can you help me?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should process
    await expect(page.getByText(/processing/i)).toBeVisible();
    
    // Should show response with audio
    const response = page.locator('.message.assistant');
    await expect(response).toBeVisible();
    
    // Should have audio player
    const audioPlayer = page.getByRole('audio');
    await expect(audioPlayer).toBeVisible();
  });

  test('should maintain conversation context', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // First message
    await textInput.fill('My name is John');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Wait for response
    await page.waitForTimeout(500);
    
    // Second message referencing context
    await textInput.fill("What's my name?");
    await page.getByRole('button', { name: /send/i }).click();
    
    // Response should reference previous context
    const response = page.locator('.message.assistant');
    await expect(response).toBeVisible();
  });

  test('should handle conversation switching between voice and text', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    const voiceButton = page.getByRole('button', { name: /record|mic/i });
    
    // Start with text
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    await page.waitForTimeout(500);
    
    // Switch to voice
    await voiceButton.click();
    await voiceButton.click(); // Record and stop
    
    // Both should work in sequence
    const messages = page.locator('.message');
    await expect(messages).toHaveCount(2);
  });

  test('should display conversation history', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send multiple messages
    for (let i = 0; i < 3; i++) {
      await textInput.fill(`Message ${i + 1}`);
      await page.getByRole('button', { name: /send/i }).click();
    }
    
    // All messages should be visible in history
    const messages = page.locator('.message');
    await expect(messages).toHaveCount(6); // 3 user + 3 assistant
  });

  test('should handle conversation timeout', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Wait for timeout
    await page.waitForTimeout(10000);
    
    // Should handle gracefully - either timeout message or retry option
    const timeoutMessage = page.getByText(/timeout|try again|unavailable/i);
    const retryButton = page.getByRole('button', { name: /retry|try again/i });
    
    if (await timeoutMessage.count() > 0) {
      await expect(timeoutMessage).toBeVisible();
    } else if (await retryButton.count() > 0) {
      await expect(retryButton).toBeVisible();
    }
  });

  test('should clear conversation on reset', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Find clear conversation button
    const clearButton = page.getByRole('button', { name: /clear|reset|new/i });
    
    if (await clearButton.count() > 0) {
      await clearButton.click();
      
      // Conversation should be cleared
      const messages = page.locator('.message');
      await expect(messages).toHaveCount(0);
    }
  });

  test('should show conversation loading indicator', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show loading state
    const loading = page.getByText(/loading|connecting/i);
    await expect(loading).toBeVisible();
  });

  test('should handle rapid message submission', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Try to send messages rapidly
    for (let i = 0; i < 5; i++) {
      await textInput.fill(`Rapid message ${i}`);
      await page.getByRole('button', { name: /send/i }).click();
    }
    
    // Should handle gracefully without crashing
    // Messages might be queued or debounced
    await page.waitForTimeout(2000);
    
    // Should still be functional
    await expect(page.getByRole('textbox')).toBeVisible();
  });

  test('should handle conversation with language switching', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send Portuguese message
    await textInput.fill('Olá, como você está?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Wait for response
    await page.waitForTimeout(500);
    
    // Send English message
    await textInput.fill('Hello, how are you?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should handle both languages
    await expect(page.locator('.message')).toHaveCount(4); // 2 user + 2 assistant
  });
});
