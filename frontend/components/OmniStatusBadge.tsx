"use client";

import React from "react";

interface OmniStatusBadgeProps {
  modelLoaded: boolean;
}

export const OmniStatusBadge: React.FC<OmniStatusBadgeProps> = ({ modelLoaded }) => {
  return (
    <div
      className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
      style={{
        background: modelLoaded ? "rgba(99, 102, 241, 0.15)" : "rgba(255, 255, 255, 0.05)",
        border: `1px solid ${modelLoaded ? "rgba(99, 102, 241, 0.4)" : "rgba(255,255,255,0.1)"}`,
      }}
    >
      {modelLoaded ? (
        <>
          <span
            className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"
            aria-hidden="true"
          />
          <span className="text-indigo-300">Voice Tutor Active</span>
        </>
      ) : (
        <>
          <span
            className="w-1.5 h-1.5 rounded-full bg-yellow-500"
            aria-hidden="true"
          />
          <span className="text-yellow-300">Loading model…</span>
        </>
      )}
    </div>
  );
};
