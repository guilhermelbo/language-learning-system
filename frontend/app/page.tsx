"use client";

import React, { useState } from 'react';
import { ChatInterface } from '../components/ChatInterface';
import { VoiceButton } from '../components/VoiceButton';
import { Sparkles, Settings, Globe } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const handleRecordingComplete = async (blob: Blob) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', blob, 'recording.webm');
      if (conversationId) {
        formData.append('conversation_id', conversationId);
      }

      // TODO: Replace with actual backend URL
      const response = await fetch('http://localhost:8000/conversation/speech', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("API call failed");

      const data = await response.json();

      setConversationId(data.conversation_id);
      setMessages(prev => [
        ...prev,
        { role: 'user', content: data.user_text, id: Math.random().toString() },
        { role: 'assistant', content: data.ai_text, id: Math.random().toString() }
      ]);

      // Handle audio playback if needed
      // const audioResponse = await fetch(`http://localhost:8000/audio/${data.audio_id}`);
      // ...

    } catch (err) {
      console.error("Error sending audio to backend:", err);
      // Fallback/Mock for testing UI without backend
      setMessages(prev => [
        ...prev,
        { role: 'user', content: "Simulação de fala (Backend Offline)", id: Math.random().toString() },
        { role: 'assistant', content: "Olá! Notei que o backend está offline. Configure o servidor FastAPI para processar áudio.", id: Math.random().toString() }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="flex flex-col h-screen max-h-screen">
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
        <div className="max-w-2xl mx-auto">
          <VoiceButton
            onRecordingComplete={handleRecordingComplete}
            isProcessing={isProcessing}
          />
        </div>
      </footer>
    </main>
  );
}
