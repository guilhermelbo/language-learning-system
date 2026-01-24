"use client";

import React, { useState } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';

interface VoiceButtonProps {
    onRecordingComplete: (blob: Blob) => void;
    isProcessing: boolean;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({ onRecordingComplete, isProcessing }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            const chunks: BlobPart[] = [];

            recorder.ondataavailable = (e) => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                onRecordingComplete(blob);
                stream.getTracks().forEach(track => track.stop());
            };

            recorder.start();
            setMediaRecorder(recorder);
            setIsRecording(true);
        } catch (err) {
            console.error("Failed to start recording:", err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorder) {
            mediaRecorder.stop();
            setIsRecording(false);
        }
    };

    return (
        <div className="flex flex-col items-center gap-4">
            <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording
                        ? 'bg-red-500 hover:bg-red-600 scale-110'
                        : 'bg-indigo-600 hover:bg-indigo-700'
                    } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${isRecording ? 'pulse-red' : ''
                    }`}
                style={isRecording ? { boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.7)' } : undefined}
            >
                {isProcessing ? (
                    <Loader2 className="w-10 h-10 animate-spin text-white" />
                ) : isRecording ? (
                    <Square className="w-10 h-10 text-white fill-current" />
                ) : (
                    <Mic className="w-10 h-10 text-white" />
                )}
            </button>
            <span className="text-sm font-medium text-indigo-300">
                {isProcessing ? 'Processando áudio...' : isRecording ? 'Gravando...' : 'Toque para falar'}
            </span>
        </div>
    );
};
