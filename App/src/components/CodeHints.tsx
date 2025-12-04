import React, { useEffect, useState } from 'react';

interface CodeHint {
  position: number;
  character: string;
  title: string;
  label_de: string;
  label_en: string;
  matched: boolean;
}

interface CodeHintsProps {
  nodeId: number | null;
  partialCode: string;
  className?: string;
}

/**
 * CodeHints Component
 * Displays character-by-character hints for product codes
 * Shows what each segment means based on the parent node's structure
 */
export const CodeHints: React.FC<CodeHintsProps> = ({ nodeId, partialCode, className = '' }) => {
  const [hints, setHints] = useState<CodeHint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nodeId || !partialCode) {
      setHints([]);
      return;
    }

    const fetchHints = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(
          `http://localhost:8000/api/code-hints/${nodeId}/${encodeURIComponent(partialCode)}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch code hints');
        }
        
        const data = await response.json();
        setHints(data.hints || []);
      } catch (err) {
        console.error('Error fetching code hints:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setHints([]);
      } finally {
        setLoading(false);
      }
    };

    // Debounce to avoid too many requests
    const timeoutId = setTimeout(fetchHints, 150);
    return () => clearTimeout(timeoutId);
  }, [nodeId, partialCode]);

  if (!nodeId || !partialCode) {
    return null;
  }

  if (loading && hints.length === 0) {
    return (
      <div className={`text-xs text-gray-400 italic ${className}`}>
        Lade Code-Struktur...
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-xs text-red-500 ${className}`}>
        Code-Hints nicht verfügbar
      </div>
    );
  }

  if (hints.length === 0) {
    return null;
  }

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
      <div className="flex items-center gap-2 mb-2">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-xs font-semibold text-blue-800">
          Code-Struktur ({partialCode.length} von {hints[hints.length - 1]?.position || '?'} Zeichen)
        </span>
      </div>
      
      <div className="space-y-1.5">
        {hints.map((hint, idx) => (
          <div 
            key={idx}
            className={`flex items-center gap-2 text-xs rounded px-2 py-1.5 transition-colors ${
              hint.matched 
                ? 'bg-green-100 border border-green-300' 
                : 'bg-white border border-gray-200'
            }`}
          >
            {/* Matched Indicator */}
            <div className="flex-shrink-0 w-5 text-center">
              {hint.matched ? (
                <span className="text-green-600 font-bold">✓</span>
              ) : (
                <span className="text-gray-400">○</span>
              )}
            </div>
            
            {/* Position */}
            <div className="flex-shrink-0 w-8 text-gray-500 font-mono text-[10px]">
              Pos {hint.position}
            </div>
            
            {/* Code Segment */}
            <div className={`flex-shrink-0 font-mono font-bold ${
              hint.matched ? 'text-green-700' : 'text-gray-600'
            }`}>
              {hint.character}
            </div>
            
            {/* Title */}
            <div className="flex-shrink-0 text-gray-700 font-medium min-w-[80px]">
              {hint.title}:
            </div>
            
            {/* Label */}
            <div className={`flex-1 ${
              hint.matched ? 'text-gray-800' : 'text-gray-600'
            }`}>
              {hint.label_de}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-2 pt-2 border-t border-blue-200 text-[10px] text-blue-700">
        💡 Tippe weiter, um die nächsten Segmente zu sehen
      </div>
    </div>
  );
};
