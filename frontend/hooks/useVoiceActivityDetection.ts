'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ConversationState =
  | 'idle'
  | 'listening'
  | 'silence_countdown'
  | 'sending'
  | 'tutor_responding'
  | 'playing_audio';

export interface PronunciationEvent {
  word: string;
  error_type: string;
  user_pronunciation: string;
  correct_pronunciation: string;
  correction_attempted: boolean;
  correction_succeeded: boolean | null;
}

export interface TurnResult {
  userText: string;
  aiText: string;
  conversationId: string;
  pronunciationEvents: PronunciationEvent[];
}

export interface UseVADReturn {
  state: ConversationState;
  streamingText: string;
  micError: string | null;
  inactive: boolean;
  start: () => Promise<void>;
  stop: () => void;
  silenceThresholdMs: number;
  setSilenceThresholdMs: (ms: number) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RMS_SILENCE_THRESHOLD = 30; // 0–255 scale from getByteFrequencyData
const MIN_SPEECH_MS = 500;
const VAD_INTERVAL_MS = 100;
const INACTIVITY_TIMEOUT_MS = 30_000;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useVoiceActivityDetection(
  apiBase: string,
  getConversationId: () => string | null,
  language: string,
  onTurnComplete: (result: TurnResult) => void,
): UseVADReturn {
  const [state, setState] = useState<ConversationState>('idle');
  const [streamingText, setStreamingText] = useState('');
  const [micError, setMicError] = useState<string | null>(null);
  const [inactive, setInactive] = useState(false);
  const [silenceThresholdMs, setSilenceThresholdMsState] = useState(2000);

  // Refs — avoid stale closures in callbacks
  const stateRef = useRef<ConversationState>('idle');
  const silenceThresholdRef = useRef(2000);
  const languageRef = useRef(language);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const mimeTypeRef = useRef('');

  const vadIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // VAD counters
  const speechMsRef = useRef(0);
  const silenceMsRef = useRef(0);
  const wasSpeakingRef = useRef(false);
  const stoppingForTurnRef = useRef(false);

  // Audio playback queue
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const doneReceivedRef = useRef(false);

  // Keep refs in sync
  useEffect(() => { silenceThresholdRef.current = silenceThresholdMs; }, [silenceThresholdMs]);
  useEffect(() => { languageRef.current = language; }, [language]);

  const setStateSync = useCallback((s: ConversationState) => {
    stateRef.current = s;
    setState(s);
  }, []);

  // ---------------------------------------------------------------------------
  // Audio playback queue
  // ---------------------------------------------------------------------------

  const playNextAudio = useCallback(() => {
    const ctx = audioCtxRef.current;
    if (!ctx || audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      if (doneReceivedRef.current) {
        setStateSync('listening');
        setInactive(false);
      }
      return;
    }
    isPlayingRef.current = true;
    const source = ctx.createBufferSource();
    source.buffer = audioQueueRef.current.shift()!;
    source.connect(ctx.destination);
    source.onended = playNextAudio;
    source.start();
  }, [setStateSync]);

  const enqueueAudio = useCallback((base64Wav: string) => {
    const ctx = audioCtxRef.current;
    if (!ctx || !base64Wav) return;
    try {
      const binary = atob(base64Wav);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      ctx.decodeAudioData(bytes.buffer.slice(0)).then((buffer) => {
        audioQueueRef.current.push(buffer);
        if (!isPlayingRef.current) {
          setStateSync('playing_audio');
          playNextAudio();
        }
      }).catch(() => { /* degraded — no audio for this sentence */ });
    } catch {
      // ignore base64 decode errors
    }
  }, [playNextAudio, setStateSync]);

  // ---------------------------------------------------------------------------
  // Inactivity guard
  // ---------------------------------------------------------------------------

  const resetInactivity = useCallback(() => {
    if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    setInactive(false);
    inactivityTimerRef.current = setTimeout(() => {
      if (stateRef.current === 'listening') {
        setInactive(true);
        // Stop the loop — user must tap to resume
        if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
      }
    }, INACTIVITY_TIMEOUT_MS);
  }, []);

  // ---------------------------------------------------------------------------
  // SSE consumer
  // ---------------------------------------------------------------------------

  const sendAudio = useCallback(async (blob: Blob) => {
    setStateSync('sending');
    setStreamingText('');
    doneReceivedRef.current = false;
    audioQueueRef.current = [];
    isPlayingRef.current = false;

    const formData = new FormData();
    formData.append('file', blob, 'recording.webm');
    const convId = getConversationId();
    if (convId) formData.append('conversation_id', convId);
    formData.append('language', languageRef.current);

    let accUserText = '';
    let accAiText = '';
    let accPronEvents: PronunciationEvent[] = [];

    try {
      const response = await fetch(`${apiBase}/conversation/omni/speech/stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      setStateSync('tutor_responding');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('event: ')) {
            currentEvent = trimmed.slice(7).trim();
          } else if (trimmed.startsWith('data: ') && currentEvent) {
            try {
              const data = JSON.parse(trimmed.slice(6));
              switch (currentEvent) {
                case 'transcript':
                  accUserText = (data as { user_text?: string }).user_text ?? '';
                  break;
                case 'text_delta':
                  accAiText += (data as { delta?: string }).delta ?? '';
                  setStreamingText(prev => prev + ((data as { delta?: string }).delta ?? ''));
                  break;
                case 'sentence_audio': {
                  const sa = data as { tts_ok?: boolean; audio_base64?: string };
                  if (sa.tts_ok && sa.audio_base64) enqueueAudio(sa.audio_base64);
                  break;
                }
                case 'pronunciation_events':
                  accPronEvents = Array.isArray(data) ? (data as PronunciationEvent[]) : [];
                  break;
                case 'done': {
                  doneReceivedRef.current = true;
                  const conversationId = (data as { conversation_id?: string }).conversation_id ?? '';
                  onTurnComplete({
                    userText: accUserText,
                    aiText: accAiText,
                    conversationId,
                    pronunciationEvents: accPronEvents,
                  });
                  if (!isPlayingRef.current) {
                    setStateSync('listening');
                    resetInactivity();
                  }
                  break;
                }
                case 'error':
                  throw new Error((data as { detail?: string }).detail ?? 'Stream error');
              }
            } catch {
              // ignore individual parse/event errors
            }
            currentEvent = '';
          }
        }
      }
    } catch (err) {
      console.error('[VAD] SSE stream error:', err);
      setStateSync('listening');
      resetInactivity();
    }

    // Restart VAD counters after send completes (mic continues in bg)
    speechMsRef.current = 0;
    silenceMsRef.current = 0;
    wasSpeakingRef.current = false;
    chunksRef.current = [];
  }, [apiBase, getConversationId, onTurnComplete, enqueueAudio, setStateSync, resetInactivity]);

  // ---------------------------------------------------------------------------
  // Recorder factory (creates fresh MediaRecorder on same stream)
  // ---------------------------------------------------------------------------

  const startRecorder = useCallback((stream: MediaStream) => {
    const mimeType = mimeTypeRef.current;
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    mediaRecorderRef.current = recorder;
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      if (!stoppingForTurnRef.current) return; // session-level stop — ignore
      stoppingForTurnRef.current = false;

      const turnChunks = [...chunksRef.current];
      chunksRef.current = [];

      const blob = new Blob(turnChunks, { type: mimeType || 'audio/webm' });

      // Reset VAD counters
      speechMsRef.current = 0;
      silenceMsRef.current = 0;
      wasSpeakingRef.current = false;

      // Restart recorder for next turn (same stream, fresh recorder)
      if (streamRef.current) startRecorder(streamRef.current);

      // Send audio (async fire-and-forget)
      sendAudio(blob);
    };

    recorder.start(100);
  }, [sendAudio]);

  // ---------------------------------------------------------------------------
  // VAD loop
  // ---------------------------------------------------------------------------

  const startVADLoop = useCallback((analyser: AnalyserNode) => {
    if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    vadIntervalRef.current = setInterval(() => {
      const s = stateRef.current;
      if (s !== 'listening' && s !== 'silence_countdown') return;

      analyser.getByteFrequencyData(dataArray);
      const sum = dataArray.reduce((acc, v) => acc + v * v, 0);
      const rms = Math.sqrt(sum / dataArray.length);

      if (rms >= RMS_SILENCE_THRESHOLD) {
        // Speech detected
        speechMsRef.current += VAD_INTERVAL_MS;
        silenceMsRef.current = 0;
        wasSpeakingRef.current = true;
        if (s === 'silence_countdown') setStateSync('listening');
        resetInactivity();
      } else {
        // Silence
        if (wasSpeakingRef.current && speechMsRef.current >= MIN_SPEECH_MS) {
          silenceMsRef.current += VAD_INTERVAL_MS;
          if (s === 'listening') setStateSync('silence_countdown');

          if (silenceMsRef.current >= silenceThresholdRef.current) {
            // Trigger turn
            if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
            stoppingForTurnRef.current = true;
            mediaRecorderRef.current?.stop();
            // VAD loop restarts after sendAudio completes (via new recorder's onstop chain)
            startVADLoop(analyser); // restart to keep monitoring during send
          }
        }
      }
    }, VAD_INTERVAL_MS);
  }, [setStateSync, resetInactivity]);

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  const start = useCallback(async () => {
    setMicError(null);
    setInactive(false);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioCtxRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Detect best mime type
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
      mimeTypeRef.current = mimeTypes.find(t => MediaRecorder.isTypeSupported(t)) ?? '';

      startRecorder(stream);
      setStateSync('listening');
      startVADLoop(analyser);
      resetInactivity();
    } catch (err) {
      const error = err as Error;
      if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
        setMicError('Acesso ao microfone negado. Por favor, habilite nas configurações do navegador.');
      } else if (error.name === 'NotFoundError') {
        setMicError('Nenhum microfone encontrado. Conecte um microfone e tente novamente.');
      } else {
        setMicError(`Erro de microfone: ${error.message}`);
      }
    }
  }, [startRecorder, startVADLoop, setStateSync, resetInactivity]);

  const stop = useCallback(() => {
    if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
    if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);

    stoppingForTurnRef.current = false; // prevent onstop from re-triggering

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }

    audioQueueRef.current = [];
    isPlayingRef.current = false;
    doneReceivedRef.current = false;
    speechMsRef.current = 0;
    silenceMsRef.current = 0;
    wasSpeakingRef.current = false;

    setStreamingText('');
    setStateSync('idle');
  }, [setStateSync]);

  const setSilenceThresholdMs = useCallback((ms: number) => {
    const clamped = Math.max(1000, Math.min(5000, ms));
    silenceThresholdRef.current = clamped;
    setSilenceThresholdMsState(clamped);
  }, []);

  // Cleanup on unmount
  useEffect(() => () => { stop(); }, [stop]);

  return {
    state,
    streamingText,
    micError,
    inactive,
    start,
    stop,
    silenceThresholdMs,
    setSilenceThresholdMs,
  };
}
