'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Mic, MicOff, Brain, Volume2, AlertCircle } from 'lucide-react';
import {
  useVoiceActivityDetection,
  TurnResult,
  ConversationState,
} from '../hooks/useVoiceActivityDetection';
import { PronunciationEvent } from './PronunciationEventCard';
import { PronunciationEventCard } from './PronunciationEventCard';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ConversationMessage {
  id: string;
  userText: string;
  aiText: string;
  pronunciationEvents: PronunciationEvent[];
}

interface VoiceTutorLiveProps {
  conversationId: string | null;
  onConversationIdChange: (id: string | null) => void;
  language?: string;
  onSwitchToStandard?: () => void;
}

// ---------------------------------------------------------------------------
// State Badge
// ---------------------------------------------------------------------------

const STATE_CONFIG: Record<ConversationState, { label: string; color: string; icon: React.ReactNode; pulse: boolean }> = {
  idle: { label: 'Idle', color: 'rgba(255,255,255,0.08)', icon: <MicOff className="w-4 h-4 text-gray-400" />, pulse: false },
  listening: { label: 'Listening…', color: 'rgba(99,102,241,0.2)', icon: <Mic className="w-4 h-4 text-indigo-400" />, pulse: true },
  silence_countdown: { label: 'Detected pause…', color: 'rgba(250,204,21,0.15)', icon: <Mic className="w-4 h-4 text-yellow-400" />, pulse: true },
  sending: { label: 'Sending…', color: 'rgba(99,102,241,0.15)', icon: <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />, pulse: false },
  tutor_responding: { label: 'Tutor thinking…', color: 'rgba(99,102,241,0.15)', icon: <Brain className="w-4 h-4 text-indigo-300" />, pulse: true },
  playing_audio: { label: 'Tutor speaking…', color: 'rgba(34,197,94,0.15)', icon: <Volume2 className="w-4 h-4 text-green-400" />, pulse: true },
};

function StateBadge({ state }: { state: ConversationState }) {
  const cfg = STATE_CONFIG[state];
  return (
    <div
      className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300"
      style={{ background: cfg.color, border: '1px solid rgba(255,255,255,0.08)' }}
    >
      <span className={cfg.pulse ? 'animate-pulse' : ''}>{cfg.icon}</span>
      <span className="text-gray-200">{cfg.label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Silence Threshold Control (T014)
// ---------------------------------------------------------------------------

function SilenceThresholdControl({ value, onChange }: { value: number; onChange: (ms: number) => void }) {
  const seconds = value / 1000;
  return (
    <div className="flex items-center gap-3 text-xs text-gray-500">
      <span className="whitespace-nowrap">Silence: {seconds.toFixed(1)}s</span>
      <input
        type="range"
        min={1000}
        max={5000}
        step={500}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-24 accent-indigo-500"
        aria-label="Silence threshold"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Message Bubble
// ---------------------------------------------------------------------------

function MessagePair({ msg }: { msg: ConversationMessage }) {
  return (
    <div className="flex flex-col gap-2">
      {msg.userText && (
        <div className="flex justify-end">
          <div
            className="max-w-xs px-4 py-2 rounded-2xl rounded-tr-sm text-sm text-white"
            style={{ background: 'rgba(99,102,241,0.3)', border: '1px solid rgba(99,102,241,0.2)' }}
          >
            {msg.userText}
          </div>
        </div>
      )}
      <div className="flex justify-start">
        <div
          className="max-w-sm px-4 py-2 rounded-2xl rounded-tl-sm text-sm text-gray-100"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          {msg.aiText}
        </div>
      </div>
      {msg.pronunciationEvents.length > 0 && (
        <div className="flex flex-col gap-1 mt-1">
          {msg.pronunciationEvents.map((ev, i) => (
            <PronunciationEventCard key={i} event={ev} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component (T010 + T013 + T015 + T018)
// ---------------------------------------------------------------------------

export function VoiceTutorLive({
  conversationId,
  onConversationIdChange,
  language = 'en-US',
  onSwitchToStandard,
}: VoiceTutorLiveProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const conversationIdRef = useRef<string | null>(conversationId);
  conversationIdRef.current = conversationId;

  const getConversationId = useCallback(() => conversationIdRef.current, []);

  const handleTurnComplete = useCallback(
    (result: TurnResult) => {
      if (result.conversationId) {
        onConversationIdChange(result.conversationId);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2),
          userText: result.userText,
          aiText: result.aiText,
          pronunciationEvents: result.pronunciationEvents,
        },
      ]);
    },
    [onConversationIdChange],
  );

  const {
    state,
    streamingText,
    micError,
    inactive,
    start,
    stop,
    silenceThresholdMs,
    setSilenceThresholdMs,
  } = useVoiceActivityDetection(API_BASE, getConversationId, language, handleTurnComplete);

  const isActive = state !== 'idle';

  return (
    <div className="flex flex-col items-center gap-4 w-full">

      {/* Mic error (T018) */}
      {micError && (
        <div
          className="w-full max-w-sm rounded-xl p-4 flex flex-col gap-2"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}
        >
          <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {micError}
          </div>
          {onSwitchToStandard && (
            <button
              onClick={onSwitchToStandard}
              className="text-xs text-gray-400 hover:text-white underline underline-offset-2 self-start"
            >
              Switch to Standard Mode
            </button>
          )}
        </div>
      )}

      {/* Conversation history */}
      {messages.length > 0 && (
        <div className="w-full max-w-sm flex flex-col gap-4 max-h-64 overflow-y-auto pr-1">
          {messages.map((msg) => (
            <MessagePair key={msg.id} msg={msg} />
          ))}

          {/* Streaming text bubble (T013) */}
          {(state === 'tutor_responding' || state === 'playing_audio') && streamingText && (
            <div className="flex justify-start">
              <div
                className="max-w-sm px-4 py-2 rounded-2xl rounded-tl-sm text-sm text-gray-100"
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
              >
                {streamingText}
                <span className="inline-block w-0.5 h-3.5 ml-0.5 bg-gray-300 animate-pulse align-middle" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Streaming text when no history yet (T013) */}
      {messages.length === 0 && streamingText && (
        <div
          className="w-full max-w-sm px-4 py-2 rounded-2xl text-sm text-gray-100"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          {streamingText}
          <span className="inline-block w-0.5 h-3.5 ml-0.5 bg-gray-300 animate-pulse align-middle" />
        </div>
      )}

      {/* State badge */}
      <StateBadge state={state} />

      {/* Inactivity pill (T018) */}
      {inactive && (
        <button
          onClick={start}
          className="px-4 py-1.5 rounded-full text-xs font-medium text-white transition-all hover:opacity-80"
          style={{ background: 'rgba(99,102,241,0.3)', border: '1px solid rgba(99,102,241,0.4)' }}
        >
          Tap to continue
        </button>
      )}

      {/* Start / Stop button */}
      {!inactive && (
        <button
          onClick={isActive ? stop : start}
          disabled={!!micError}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
            isActive
              ? 'bg-red-500/80 hover:bg-red-500 shadow-lg shadow-red-500/25'
              : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-500/25'
          } disabled:opacity-40 disabled:cursor-not-allowed`}
          aria-label={isActive ? 'Stop conversation' : 'Start conversation'}
        >
          {isActive ? (
            <div className="w-5 h-5 rounded-sm bg-white" />
          ) : (
            <Mic className="w-6 h-6 text-white" />
          )}
        </button>
      )}

      {/* Silence threshold slider (T015) */}
      {(state === 'idle' || state === 'listening' || state === 'silence_countdown') && (
        <SilenceThresholdControl
          value={silenceThresholdMs}
          onChange={setSilenceThresholdMs}
        />
      )}
    </div>
  );
}
