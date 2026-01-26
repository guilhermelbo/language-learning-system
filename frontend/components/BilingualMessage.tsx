"use client";

import React from 'react';

interface Segment {
  text: string;
  lang: string;
}

interface BilingualMessageProps {
  segments: Segment[];
}

/**
 * Displays bilingual content with visual separation between languages.
 * Shows Portuguese segments with a blue theme and English segments with green.
 */
export const BilingualMessage: React.FC<BilingualMessageProps> = ({ segments }) => {
  const ptSegments = segments.filter(s => s.lang === 'pt');
  const enSegments = segments.filter(s => s.lang === 'en');

  // If only one language, just show it without the language labels
  if (ptSegments.length === 0 || enSegments.length === 0) {
    return (
      <p className="leading-relaxed">
        {segments.map(s => s.text).join(' ')}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {/* Portuguese Section */}
      {ptSegments.length > 0 && (
        <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/20">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">🇧🇷</span>
            <span className="text-xs text-blue-400 font-medium uppercase tracking-wide">
              Português
            </span>
          </div>
          <p className="text-gray-100 leading-relaxed">
            {ptSegments.map(s => s.text).join(' ')}
          </p>
        </div>
      )}

      {/* English Section */}
      {enSegments.length > 0 && (
        <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">🇬🇧</span>
            <span className="text-xs text-green-400 font-medium uppercase tracking-wide">
              English
            </span>
          </div>
          <p className="text-gray-100 leading-relaxed">
            {enSegments.map(s => s.text).join(' ')}
          </p>
        </div>
      )}
    </div>
  );
};
