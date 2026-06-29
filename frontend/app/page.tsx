"use client";

import React, { useState, useEffect, useCallback } from "react";
import { ChatInterface, Message } from "../components/ChatInterface";
import { VoiceButton } from "../components/VoiceButton";
import { OmniStatusBadge } from "../components/OmniStatusBadge";
import { PronunciationEvent } from "../components/PronunciationEventCard";
import { Sparkles, Settings, Globe } from "lucide-react";

type VoiceMode = "standard" | "omni";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Standard mode state
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Omni mode state
  const [voiceMode, setVoiceMode] = useState<VoiceMode>("standard");
  const [omniConversationId, setOmniConversationId] = useState<string | null>(null);
  const [omniEnabled, setOmniEnabled] = useState(false);
  const [omniModelLoaded, setOmniModelLoaded] = useState(false);
  const [omniToast, setOmniToast] = useState<string | null>(null);

  // Check omni availability on mount
  useEffect(() => {
    const checkOmni = async () => {
      try {
        const res = await fetch(`${API_BASE}/conversation/omni/status`);
        if (res.ok) {
          const data = await res.json();
          setOmniEnabled(data.omni_enabled === true);
          setOmniModelLoaded(data.model_loaded === true);
        }
      } catch {
        setOmniEnabled(false);
      }
    };
    checkOmni();
  }, []);

  const showToast = useCallback((msg: string) => {
    setOmniToast(msg);
    setTimeout(() => setOmniToast(null), 5000);
  }, []);

  // --- Standard voice handler ---
  const handleRecordingComplete = async (blob: Blob) => {
    if (voiceMode === "omni") {
      return handleOmniRecordingComplete(blob);
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      if (conversationId) {
        formData.append("conversation_id", conversationId);
      }

      const response = await fetch(`${API_BASE}/conversation/speech`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("API call failed");
      const data = await response.json();

      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: data.user_text, id: Math.random().toString() },
        { role: "assistant", content: data.ai_text, id: Math.random().toString() },
      ]);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.play().catch((e) => console.error("Audio playback failed:", e));
      }
    } catch (err) {
      console.error("Error sending audio to backend:", err);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: "Simulação de fala (Backend Offline)", id: Math.random().toString() },
        {
          role: "assistant",
          content: "Olá! Notei que o backend está offline. Configure o servidor FastAPI para processar áudio.",
          id: Math.random().toString(),
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // --- Omni voice handler ---
  const handleOmniRecordingComplete = async (blob: Blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      if (omniConversationId) {
        formData.append("conversation_id", omniConversationId);
      }

      const response = await fetch(`${API_BASE}/conversation/omni/speech`, {
        method: "POST",
        body: formData,
      });

      if (response.status === 503) {
        showToast("Voice Tutor mode is currently unavailable. Standard mode is still active.");
        setVoiceMode("standard");
        return;
      }
      if (!response.ok) throw new Error(`Omni API error: ${response.status}`);

      const data = await response.json();

      // Carry conversation ID forward
      if (data.conversation_id) {
        setOmniConversationId(data.conversation_id);
      }

      const pronunciationEvents: PronunciationEvent[] = data.pronunciation_events ?? [];

      setMessages((prev) => [
        ...prev,
        { role: "user", content: data.user_text || "…", id: Math.random().toString() },
        {
          role: "assistant",
          content: data.ai_text,
          id: Math.random().toString(),
          pronunciationEvents: pronunciationEvents.length > 0 ? pronunciationEvents : undefined,
        },
      ]);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.play().catch((e) => console.error("Omni audio playback failed:", e));
      }
    } catch (err) {
      console.error("Omni voice error:", err);
      showToast("Voice Tutor mode is currently unavailable. Standard mode is still active.");
      // Do NOT clear omniConversationId — allows retry if service recovers
    } finally {
      setIsProcessing(false);
    }
  };

  // --- Text handler (standard mode only) ---
  const handleTextInput = async (text: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE}/conversation/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, conversation_id: conversationId }),
      });

      if (!response.ok) throw new Error("API call failed");
      const data = await response.json();

      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: data.user_text, id: Math.random().toString() },
        { role: "assistant", content: data.ai_text, id: Math.random().toString() },
      ]);

      const playAudio = (b64: string) =>
        new Promise<void>((resolve) => {
          const audio = new Audio(`data:audio/wav;base64,${b64}`);
          audio.onended = () => resolve();
          audio.play().catch(() => resolve());
        });

      if (data.user_audio_base64) await playAudio(data.user_audio_base64);
      if (data.audio_base64) await playAudio(data.audio_base64);
    } catch (err) {
      console.error("Error sending text:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="flex flex-col h-screen max-h-screen">
      {/* Toast notification */}
      {omniToast && (
        <div
          className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl text-sm text-white shadow-lg"
          style={{ background: "rgba(30,30,40,0.95)", border: "1px solid rgba(255,255,255,0.1)" }}
          role="alert"
        >
          {omniToast}
        </div>
      )}

      {/* Header */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-gray-500 bg-clip-text text-transparent">
            LingoAI <span className="text-xs font-normal text-indigo-400 ml-1">Beta</span>
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {voiceMode === "omni" && <OmniStatusBadge modelLoaded={omniModelLoaded} />}
          <button className="p-2 rounded-full hover:bg-white/5 transition-colors text-gray-400 hover:text-white">
            <Globe className="w-5 h-5" />
          </button>
          <button className="p-2 rounded-full hover:bg-white/5 transition-colors text-gray-400 hover:text-white">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <ChatInterface messages={messages} />

      {/* Footer / Controls */}
      <footer className="p-8 border-t border-white/5 bg-black/20 backdrop-blur-md">
        <div className="max-w-2xl mx-auto flex flex-col items-center gap-6">

          {/* Mode selector — only shown when omni is available */}
          {omniEnabled && (
            <div
              className="flex items-center gap-1 p-1 rounded-full"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
              role="group"
              aria-label="Modo de voz"
            >
              {(["standard", "omni"] as VoiceMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setVoiceMode(mode)}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all ${
                    voiceMode === mode
                      ? "bg-indigo-600 text-white"
                      : "text-gray-400 hover:text-white"
                  }`}
                  aria-pressed={voiceMode === mode}
                >
                  {mode === "standard" ? "Padrão" : "Voice Tutor"}
                </button>
              ))}
            </div>
          )}

          {/* Text Input (standard mode only) */}
          {voiceMode === "standard" && (
            <div className="w-full relative">
              <input
                type="text"
                placeholder="Digite sua mensagem..."
                className="w-full bg-white/5 border border-white/10 rounded-full px-6 py-4 pr-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all font-light"
                onKeyDown={async (e) => {
                  if (e.key === "Enter" && e.currentTarget.value.trim() && !isProcessing) {
                    const text = e.currentTarget.value.trim();
                    e.currentTarget.value = "";
                    await handleTextInput(text);
                  }
                }}
                disabled={isProcessing}
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                {isProcessing && (
                  <div className="animate-spin w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full" />
                )}
              </div>
            </div>
          )}

          {voiceMode === "standard" && (
            <div className="flex items-center gap-4">
              <div className="h-px flex-1 bg-white/10 w-32" />
              <span className="text-xs text-gray-500 uppercase tracking-widest font-medium">OU FALE</span>
              <div className="h-px flex-1 bg-white/10 w-32" />
            </div>
          )}

          <VoiceButton
            onRecordingComplete={handleRecordingComplete}
            isProcessing={isProcessing}
          />

          {voiceMode === "omni" && (
            <p className="text-xs text-gray-500 text-center">
              Voice Tutor analisa sua pronúncia em tempo real
            </p>
          )}
        </div>
      </footer>
    </main>
  );
}
