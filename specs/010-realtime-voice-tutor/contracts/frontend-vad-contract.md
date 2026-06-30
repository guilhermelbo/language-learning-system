# Contract: Frontend Voice Activity Detection (VAD) Component

## Component: `useVoiceActivityDetection` hook

React hook that manages the full microphone → silence-detection → send → playback loop.

## Interface

```typescript
interface SilenceConfig {
  silenceThresholdMs: number;  // default: 2000, range: 1000–5000
  minSpeechMs: number;         // default: 500, fixed
}

type ConversationState =
  | "idle"
  | "listening"
  | "silence_countdown"
  | "sending"
  | "tutor_responding"
  | "playing_audio";

interface UseVADResult {
  state: ConversationState;
  start: () => Promise<void>;       // activates mic, begins loop
  stop: () => void;                 // deactivates mic, stops loop
  config: SilenceConfig;
  setConfig: (c: Partial<SilenceConfig>) => void;
}

function useVoiceActivityDetection(
  onAudioReady: (blob: Blob) => Promise<void>,  // called when a turn is ready to send
  config?: Partial<SilenceConfig>
): UseVADResult;
```

## State Transition Rules

| From | To | Trigger |
|------|-----|---------|
| `idle` | `listening` | `start()` called |
| `listening` | `silence_countdown` | RMS drops below threshold for first interval |
| `silence_countdown` | `listening` | RMS rises above threshold (user resumes speaking) |
| `silence_countdown` | `sending` | Countdown elapsed + min speech duration met |
| `sending` | `tutor_responding` | SSE stream first event received |
| `tutor_responding` | `playing_audio` | First `sentence_audio` event received |
| `playing_audio` | `listening` | `done` event received AND audio queue empty |
| any | `idle` | `stop()` called |
| `listening` | `idle` | 30s inactivity (no speech detected) |

## VAD Algorithm

1. `getUserMedia({ audio: true })` → `AudioContext` → `AnalyserNode` (FFT size: 2048)
2. Every 100ms: call `analyser.getByteFrequencyData(dataArray)`, compute RMS = sqrt(mean(dataArray²))
3. Silence condition: RMS < 30 (on 0–255 scale)
4. Speech detected: RMS ≥ 30 for at least `minSpeechMs` continuously
5. Silence triggered: RMS < 30 for at least `silenceThresholdMs` after speech detected
6. `MediaRecorder` runs concurrently, accumulates chunks via `ondataavailable`
7. On silence trigger: `recorder.stop()` → collect final blob → call `onAudioReady(blob)`

## Audio Playback Contract

The hook manages an internal audio queue:
- `sentence_audio` events → decode base64 WAV → `AudioBuffer` → enqueue
- Queue plays sequentially: next sentence starts when `AudioBufferSourceNode.onended` fires
- While playing: mic stays muted (state = `playing_audio`)
- Queue empty + `done` received → mic re-enabled (state = `listening`)

## Visual State Indicators

| State | Required UI |
|-------|-------------|
| `idle` | "Tap to start" or inactive |
| `listening` | Animated mic icon, audio waveform visualization |
| `silence_countdown` | Countdown ring or bar (fills over threshold duration) |
| `sending` | Spinner or "Sending…" |
| `tutor_responding` | Streaming text appears word by word |
| `playing_audio` | Tutor avatar or waveform animating |
