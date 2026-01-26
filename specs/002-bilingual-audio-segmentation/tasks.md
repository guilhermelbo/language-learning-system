# Tasks: Bilingual Audio Segmentation

**Date**: 2026-01-25
**Author**: Gemini

This document breaks down the implementation plan for the Bilingual Audio Segmentation feature into actionable tasks.

## Backend

- [ ] **Task 1: Update Dependencies**
  - Add `langdetect` and `nltk` to the `backend/requirements.txt` file.

- [ ] **Task 2: Create Segmentation Service**
  - Create a new file: `backend/src/domain/services/segmentation_service.py`.
  - Implement a `Segmenter` class or functions to perform language detection and text segmentation.
  - The service should take a string of text and return a list of `Segment` data objects (`{text: string, lang: string}`).
  - Use `nltk.sent_tokenize` for sentence splitting and `langdetect.detect` for language identification.

- [ ] **Task 3: Integrate Segmentation Service**
  - In `backend/src/application/use_cases.py`, import and use the new segmentation service.
  - After receiving the response from the LLM, pass the text to the segmentation service.
  - The use case must now handle a list of segments instead of a single block of text.

- [ ] **Task 4: Implement Multi-Segment TTS**
  - In the use case, iterate through the list of segments returned by the segmentation service.
  - For each segment, call the TTS service (`tts_service.py`) to generate an audio file. The call must specify the correct language.
  - The TTS service will need to save each audio file with a unique name.

- [ ] **Task 5: Implement Audio File Serving**
  - In the FastAPI application (`main.py`), configure a directory to serve static files (e.g., `/tmp/audio`). This is where the TTS service will save the audio segments.
  - The API response will contain the relative URLs to these files (e.g., `/audio/segment_xyz.mp3`).

- [ ] **Task 6: Update API Response Model**
  - Update the Pydantic models for the API response in `backend/src/domain/response_entities.py` to match the new contract defined in `data-model.md` (including `segments` and `audio_urls`).

## Frontend

- [ ] **Task 7: Update API Response Type**
  - In the frontend, update the TypeScript type/interface for the `AIResponse` to include `segments: Segment[]` and `audio_urls: string[]`.

- [ ] **Task 8: Implement Sequential Audio Playback**
  - In the `ChatInterface.tsx` component (or a dedicated audio component), implement the logic to handle the `audio_urls` array.
  - Create a function that plays the audio from each URL in the array, one after the other.
  - Use the HTML5 `<audio>` element or a library like `howler.js` to manage playback.
  - Ensure the UI correctly reflects the audio state (e.g., playing, loading, finished).

- [ ] **Task 9: Update Bilingual Message Display**
  - Modify the `BilingualMessage.tsx` component to optionally accept and render the `segments` array, which could be used for highlighting text as it's spoken in the future. For now, it can continue to display the full `ai_text`.

## Testing

- [ ] **Task 10: Create Backend Unit Tests**
  - Create `backend/tests/test_segmentation_service.py`.
  - Write unit tests for the segmentation service, covering:
    - Simple bilingual text.
    - Text with multiple language switches.
    - Monolingual text (should produce a single segment).
    - Edge cases like empty strings or very short text.

- [ ] **Task 11: Create Backend Integration Test**
  - Update or create an integration test for the `/conversation` endpoint.
  - The test should send a bilingual prompt and assert that the response JSON has the correct structure (`segments` and `audio_urls`).

- [ ] **Task 12: Manual End-to-End Testing**
  - Follow the steps in `quickstart.md` to run the system.
  - Test with various bilingual inputs and confirm that the audio plays back correctly with proper pronunciation for each segment.
