"use client";

import React, { useState } from 'react';
import { ChatInterface } from '../components/ChatInterface';
import { VoiceButton } from '../components/VoiceButton';
import { Sparkles, Settings, Globe } from 'lucide-react';

interface Segment {
  text: string;
  lang: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
  segments?: Segment[];
}

interface APIResponse {
  user_text: string;
  ai_text: string;
  segments: Segment[];
  conversation_id: string;
  audio_urls?: string[];
  user_audio_base64?: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const playAudioSequence = (urls: string[]): Promise<void> => {
    return new Promise((resolve) => {
      if (!urls || urls.length === 0) {
        resolve();
        return;
      }
      
      const playNext = (index: number) => {
        if (index >= urls.length) {
          resolve();
          return;
        }
        
        const fullUrl = `http://localhost:8000${urls[index]}`;
        const audio = new Audio(fullUrl);
        
        audio.onended = () => {
          playNext(index + 1);
        };
        
        audio.onerror = (e) => {
          console.error("Audio playback failed for:", fullUrl, e);
          playNext(index + 1); 
        };
        
        audio.play().catch(e => {
          console.error("Audio playback failed to start for:", fullUrl, e);
          playNext(index + 1);
        });
      };
      
      playNext(0);
    });
  };

  const playBase64Audio = (base64Audio: string): Promise<void> => {
    return new Promise((resolve) => {
      if (!base64Audio) {
        resolve();
        return;
      }
      const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
      audio.onended = () => resolve();
      audio.onerror = (e) => {
        console.error("Base64 audio playback failed:", e);
        resolve();
      };
      audio.play().catch(e => {
        console.error("Base64 audio playback failed to start:", e);
        resolve();
      });
    });
  };

  const handleRecordingComplete = async (blob: Blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'recording.webm');
      if (conversationId) {
        formData.append('conversation_id', conversationId);
      }

      const response = await fetch('http://localhost:8000/conversation/speech', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("API call failed");

      const data: APIResponse = await response.json();

      setConversationId(data.conversation_id);
      setMessages(prev => [
        ...prev,
        { role: 'user', content: data.user_text, id: Math.random().toString() },
        { role: 'assistant', content: data.ai_text, id: Math.random().toString(), segments: data.segments }
      ]);

      await playAudioSequence(data.audio_urls || []);

    } catch (err) {
      console.error("Error sending audio to backend:", err);
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
        <div className="max-w-2xl mx-auto flex flex-col items-center gap-6">

          {/* Text Input */}
          <div className="w-full relative">
            <input
              type="text"
              placeholder="Digite sua mensagem..."
              className="w-full bg-white/5 border border-white/10 rounded-full px-6 py-4 pr-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all font-light"
              onKeyDown={async (e) => {
                if (e.key === 'Enter' && e.currentTarget.value.trim() && !isProcessing) {
                  const text = e.currentTarget.value.trim();
                  e.currentTarget.value = '';
                  setIsProcessing(true);

                  try {
                    const response = await fetch('http://localhost:8000/conversation/text', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        text,
                        conversation_id: conversationId
                      }),
                    });

                    if (!response.ok) throw new Error("API call failed");

                    const data: APIResponse = await response.json();

                    setConversationId(data.conversation_id);
                    setMessages(prev => [
                      ...prev,
                      { role: 'user', content: data.user_text, id: Math.random().toString() },
                      { role: 'assistant', content: data.ai_text, id: Math.random().toString(), segments: data.segments }
                    ]);
                    
                    if (data.user_audio_base64) {
                      await playBase64Audio(data.user_audio_base64);
                    }

                    if (data.audio_urls) {
                      await playAudioSequence(data.audio_urls);
                    }
                  } catch (err) {
                    console.error("Error sending text:", err);
                  } finally {
                    setIsProcessing(false);
                  }
                }
              }}
              disabled={isProcessing}
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              {isProcessing && <div className="animate-spin w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full"></div>}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-white/10 w-32"></div>
            <span className="text-xs text-gray-500 uppercase tracking-widest font-medium">OU FALE</span>
            <div className="h-px flex-1 bg-white/10 w-32"></div>
          </div>

          <VoiceButton
            onRecordingComplete={handleRecordingComplete}
            isProcessing={isProcessing}
          />
        </div>
      </footer>
    </main>
  );
}
