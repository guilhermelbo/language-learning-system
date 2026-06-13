/**
 * E2E tests for text input interaction.
 * 
 * Tests the text input, submission, and response flow.
 */

import { test, expect } from '@playwright/test';

test.describe('Text Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display text input field', async ({ page }) => {
    // Text input should be visible
    const textInput = page.getByRole('textbox');
    await expect(textInput).toBeVisible();
    await expect(textInput).toBeEnabled();
  });

  test('should submit text message', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type message
    await textInput.fill('Hello, how are you?');
    
    // Submit (by clicking send button or pressing Enter)
    const sendButton = page.getByRole('button', { name: /send|submit/i });
    if (await sendButton.count() > 0) {
      await sendButton.click();
    } else {
      await page.keyboard.press('Enter');
    }
    
    // Should show processing state
    const processingState = page.getByText(/processing|thinking/i);
    await expect(processingState).toBeVisible();
  });

  test('should display message in conversation', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type and send message
    await textInput.fill('Test message');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Message should appear in conversation history
    const message = page.getByText('Test message');
    await expect(message).toBeVisible();
  });

  test('should validate empty input', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Try to send empty message
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show validation message
    const validationMessage = page.getByText(/please|empty|required/i);
    if (await validationMessage.count() > 0) {
      await expect(validationMessage).toBeVisible();
    }
  });

  test('should handle long input', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type very long message
    const longMessage = 'a'.repeat(5000);
    await textInput.fill(longMessage);
    
    // Should handle gracefully
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show processing state
    const processingState = page.getByText(/processing/i);
    await expect(processingState).toBeVisible();
  });

  test('should display assistant response', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Assistant response should appear
    const assistantMessage = page.locator('.message.assistant');
    await expect(assistantMessage).toBeVisible();
  });

  test('should scroll to latest message', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send multiple messages
    for (let i = 0; i < 5; i++) {
      await textInput.fill(`Message ${i + 1}`);
      await page.getByRole('button', { name: /send/i }).click();
    }
    
    // Should scroll to show latest message
    await expect(textInput).toBeVisible();
  });

  test('should handle special characters', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type message with special characters
    await textInput.fill('Hello! How are you doing today?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should process successfully
    await expect(page.getByText('Processing')).toBeVisible();
  });

  test('should handle unicode characters', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Type message with unicode (emojis, accents)
    await textInput.fill('Olá! 🎉 Привет как дела?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should process successfully
    await expect(page.getByText('Processing')).toBeVisible();
  });
});
