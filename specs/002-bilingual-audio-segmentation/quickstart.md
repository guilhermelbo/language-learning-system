# Quickstart: Testing Bilingual Audio Segmentation

**Date**: 2026-01-25
**Author**: Gemini

## 1. Objective

This document provides instructions for developers to test the implementation of the bilingual audio segmentation feature. It outlines how to run the necessary services and how to make a request to the updated API endpoint.

## 2. Prerequisites

- The `backend` service must be running.
- The `tts` (Text-to-Speech) AI service from `ai_services/tts` must be running, as the backend will call it to generate audio files.
- The backend must be configured with the correct endpoint for the TTS service.
- An environment with `curl` and `jq` (for pretty-printing JSON) is recommended for testing.

## 3. Running the Services

From the repository root, start the required services using Docker Compose:

```bash
docker-compose up -d backend tts
```

This command will build and start the `backend` and `tts` services in detached mode.

## 4. Making a Test Request

Use the following `curl` command to send a POST request to the `/conversation` endpoint. The body contains a phrase that will elicit a mixed-language response.

```bash
curl -X POST http://localhost:8000/conversation \
-H "Content-Type: application/json" \
-d 
'{'
  "text": "me ensine como usar a expressão get off"
}'
```

*Note: The port `8000` assumes the default configuration for the FastAPI backend.*

## 5. Expected Response

The API should return a JSON object with a `200 OK` status. The structure of the response should match the `AIResponse` schema defined in the API contract.

**Example Successful Response:**

```json
{
  "user_text": "me ensine como usar a expressão get off",
  "ai_text": "A expressão 'get off' pode ser usada para dizer a alguém para sair. Por exemplo: 'Get off the stage!' significa 'Saia do palco!'.",
  "segments": [
    {
      "text": "A expressão 'get off' pode ser usada para dizer a alguém para sair.",
      "lang": "pt"
    },
    {
      "text": "Por exemplo: 'Get off the stage!'",
      "lang": "en"
    },
    {
      "text": " significa 'Saia do palco!'.",
      "lang": "pt"
    }
  ],
  "audio_urls": [
    "/audio/segment_01.mp3",
    "/audio/segment_02.mp3",
    "/audio/segment_03.mp3"
  ],
  "conversation_id": "8c7f76a7-02e4-4a25-82d2-56a394e3c9af"
}
```

## 6. Verification Steps

1.  **Check the `segments` array**: Verify that the `ai_text` has been correctly split into segments with the appropriate `lang` tag.
2.  **Check the `audio_urls` array**: Ensure the number of URLs matches the number of segments.
3.  **Access an audio URL**: Try to access one of the returned URLs (e.g., `http://localhost:8000/audio/segment_01.mp3`). You should be able to download or play the corresponding audio clip.
4.  **Listen to the audio**: Listen to the audio from each URL to confirm that it is pronounced in the correct language as specified by the `lang` tag.

