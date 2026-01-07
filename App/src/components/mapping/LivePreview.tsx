import React, { useState } from 'react';
import { Group } from '../../types/mapping';
import { generateCombinationsForPreview } from '../../utils/combinationGenerator';

interface LivePreviewProps {
  groups: Group[];
}

export const LivePreview: React.FC<LivePreviewProps> = ({ groups }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [combinations, setCombinations] = useState<string[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);
  
  // DEBUG: Log bei jedem Render
  console.log('[LivePreview] Render - Groups:', groups.length, 'Expanded:', isExpanded);

  const calculatePreview = async () => {
    setIsCalculating(true);
    
    // Gib UI Zeit zum Update
    await new Promise(resolve => setTimeout(resolve, 0));
    
    try {
      const groupsWithCodes = groups.filter(g => g.positions.some(p => p.codes.length > 0));
      if (groupsWithCodes.length === 0) {
        setCombinations([]);
        setIsExpanded(true);
        setIsCalculating(false);
        return;
      }
      
      // Schätze Anzahl Kombinationen
      let estimatedCount = 1;
      for (const group of groupsWithCodes) {
        const groupCombos = group.positions.reduce((acc, pos) => acc * Math.max(pos.codes.length, 1), 1);
        estimatedCount *= groupCombos;
        if (estimatedCount > 10000) {
          setCombinations([`[Zu viele Kombinationen (≈${estimatedCount.toLocaleString()}) - Export verwenden]`]);
          setIsExpanded(true);
          setIsCalculating(false);
          return;
        }
      }
      
      // Berechne in Chunks
      await new Promise(resolve => setTimeout(resolve, 0));
      const result = generateCombinationsForPreview(groupsWithCodes);
      setCombinations(result);
      setIsExpanded(true);
    } catch (error) {
      setCombinations(['[Fehler bei Berechnung]']);
    } finally {
      setIsCalculating(false);
    }
  };
  
  const combinationCount = combinations.length;

  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-lg">Live Vorschau</h3>
        {!isExpanded ? (
          <button
            onClick={calculatePreview}
            disabled={isCalculating || groups.length === 0}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isCalculating ? 'Berechne...' : 'Vorschau anzeigen'}
          </button>
        ) : (
          <button
            onClick={() => setIsExpanded(false)}
            className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
          >
            Schließen
          </button>
        )}
      </div>

      {!isExpanded && (
        <div className="text-sm text-gray-500 text-center py-4">
          Klicken Sie auf "Vorschau anzeigen" um die Kombinationen zu berechnen
        </div>
      )}

      {isExpanded && (
        <>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">
              {combinationCount} {combinationCount === 1 ? 'Kombination' : 'Kombinationen'}
            </span>
          </div>

          {/* group_position String */}
          <div>
            <div className="text-xs font-medium text-gray-500 mb-1">group_position:</div>
            {combinationCount === 0 ? (
              <div className="text-sm text-gray-400 italic px-3 py-2">
                Keine Kombinationen vorhanden. Fügen Sie Gruppen, Positionen und Codes hinzu.
              </div>
            ) : (
              <div className="font-mono text-sm bg-gray-100 px-3 py-2 rounded border border-gray-200 max-h-48 overflow-y-auto">
                {combinations.join('|')}
              </div>
            )}
          </div>

          {/* Statistics */}
          {combinationCount > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="text-xs text-gray-600">
                <div className="flex justify-between mb-1">
                  <span>Gruppen:</span>
                  <span className="font-medium">{groups.length}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>Positionen gesamt:</span>
                  <span className="font-medium">
                    {groups.reduce((sum, g) => sum + g.positions.length, 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Codes gesamt:</span>
                  <span className="font-medium">
                    {groups.reduce(
                      (sum, g) => sum + g.positions.reduce((pSum, p) => pSum + p.codes.length, 0),
                      0
                    )}
                  </span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
