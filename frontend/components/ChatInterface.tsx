"use client";

import React, { useEffect, useRef } from 'react';

interface Message {
    role: 'user' | 'assistant';
    content: str;
    id: string;
}

interface ChatInterfaceProps {
    messages: Message[];
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages }) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div
            ref={scrollRef}
            className="flex-1 w-full max-w-2xl mx-auto overflow-y-auto px-4 py-8 custom-scrollbar space-y-6"
        >
            {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50">
                    <div className="w-20 h-20 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                        <span className="text-4xl text-indigo-400 font-bold">L</span>
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Bem-vindo ao LingoAI</h2>
                        <p className="text-gray-400">Comece uma conversa agora para praticar seu inglês.</p>
                    </div>
                </div>
            )}

            {messages.map((msg) => (
                <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
                >
                    <div className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-lg ${msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-tr-none'
                            : 'glass-card text-gray-100 rounded-tl-none'
                        }`}>
                        <p className="text-sm font-bold mb-1 opacity-50 uppercase tracking-tighter">
                            {msg.role === 'user' ? 'Você' : 'Tutor IA'}
                        </p>
                        <p className="leading-relaxed">{msg.content}</p>
                    </div>
                </div>
            ))}
        </div>
    );
};
