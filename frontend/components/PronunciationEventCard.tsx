"use client";

import React from "react";

export interface PronunciationEvent {
  word: string;
  error_type: "vowel" | "consonant" | "stress" | "intonation" | "other";
  user_pronunciation: string;
  correct_pronunciation: string;
  correction_attempted: boolean;
  correction_succeeded: boolean | null;
}

interface PronunciationEventCardProps {
  event: PronunciationEvent;
}

const ERROR_LABELS: Record<string, string> = {
  vowel: "Vogal",
  consonant: "Consoante",
  stress: "Acento",
  intonation: "Entonação",
  other: "Pronúncia",
};

const drillStatus = (event: PronunciationEvent): { label: string; color: string } => {
  if (!event.correction_attempted) {
    return { label: "Aguardando repetição", color: "text-yellow-400" };
  }
  if (event.correction_succeeded === true) {
    return { label: "Correto!", color: "text-green-400" };
  }
  if (event.correction_succeeded === false) {
    return { label: "Continue praticando", color: "text-orange-400" };
  }
  return { label: "", color: "" };
};

export const PronunciationEventCard: React.FC<PronunciationEventCardProps> = ({ event }) => {
  const status = drillStatus(event);

  return (
    <div
      className="rounded-xl px-4 py-3 text-sm"
      style={{
        background: "rgba(239, 68, 68, 0.08)",
        border: "1px solid rgba(239, 68, 68, 0.25)",
      }}
      role="region"
      aria-label={`Pronúncia: ${event.word}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="px-2 py-0.5 rounded-full text-xs font-medium"
          style={{
            background: "rgba(239, 68, 68, 0.2)",
            color: "#fca5a5",
          }}
        >
          {ERROR_LABELS[event.error_type] ?? "Pronúncia"}
        </span>
        <span className="font-semibold text-white">"{event.word}"</span>
        {status.label && (
          <span className={`ml-auto text-xs ${status.color}`}>{status.label}</span>
        )}
      </div>

      <div className="flex flex-col gap-1 text-xs text-gray-300">
        {event.user_pronunciation && (
          <div>
            <span className="text-gray-500 mr-1">Você disse:</span>
            <span className="font-mono">{event.user_pronunciation}</span>
          </div>
        )}
        <div>
          <span className="text-gray-500 mr-1">Correto:</span>
          <span className="font-mono text-green-300">{event.correct_pronunciation}</span>
        </div>
      </div>
    </div>
  );
};
