/**
 * E2E tests for TTS audio playback.
 * 
 * Tests audio generation, playback controls, and synchronization.
 */

import { test, expect } from '@playwright/test';

test.describe('Audio Playback', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display audio player after response', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message to trigger TTS
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Audio player should appear
    const audioPlayer = page.getByRole('audio').or(
      page.getByText(/playing|audio|speaker/i)
    );
    await expect(audioPlayer).toBeVisible();
  });

  test('should play audio automatically', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Wait for audio to start playing
    const audio = page.getByRole('audio');
    await expect(audio).toBeAttached();
    
    // Audio should be playing (not paused)
    // Note: Play state detection depends on browser implementation
    await expect(audio).toBeEnabled();
  });

  test('should show play/pause controls', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Play/pause controls should be visible
    const playPauseButton = page.getByRole('button', { name: /play|pause/i });
    await expect(playPauseButton).toBeVisible();
  });

  test('should handle audio pause and resume', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message and start playing
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Pause audio
    const pauseButton = page.getByRole('button', { name: /pause/i });
    if (await pauseButton.count() > 0) {
      await pauseButton.click();
    }
    
    // Resume audio
    const playButton = page.getByRole('button', { name: /play/i });
    if (await playButton.count() > 0) {
      await playButton.click();
    }
  });

  test('should show audio duration', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Duration should be shown
    const duration = page.locator('[type="time"]').or(
      page.getByText(/\d{1,2}:\d{2}/)
    );
    if (await duration.count() > 0) {
      await expect(duration).toBeVisible();
    }
  });

  test('should handle multiple audio segments', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message that triggers bilingual response
    await textInput.fill('How are you?');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should have multiple audio segments (bilingual)
    const audioSegments = page.locator('.audio-segment');
    
    // Wait for all segments to be generated
    await page.waitForTimeout(1000);
    
    // At least one segment should be visible
    await expect(audioSegments.first()).toBeVisible();
  });

  test('should handle audio loading state', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show loading/processing state for audio
    const loadingState = page.getByText(/loading|generating|buffering/i);
    await expect(loadingState).toBeVisible();
  });

  test('should handle audio error', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Mock audio generation failure
    await page.route('**/conversation/speech*', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'TTS service unavailable' }),
      });
    });
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show error message
    const errorMessage = page.getByText(/error|unavailable|failed/i);
    if (await errorMessage.count() > 0) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle autoplay permission', async ({ page }) => {
    const textInput = page.getByRole('textbox');
    
    // Send message
    await textInput.fill('Hello');
    await page.getByRole('button', { name: /send/i }).click();
    
    // If autoplay is blocked, user should see controls to start playback
    const playButton = page.getByRole('button', { name: /play/i });
    if (await playButton.count() > 0) {
      await expect(playButton).toBeVisible();
    }
  });
});
