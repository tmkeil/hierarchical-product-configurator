import React from 'react';
import { Group } from '../../types/mapping';
import { generateCombinationsForPreview } from '../../utils/combinationGenerator';

interface LivePreviewProps {
  groups: Group[];
}

export const LivePreview: React.FC<LivePreviewProps> = ({ groups }) => {
  const combinations = generateCombinationsForPreview(groups);
  const combinationCount = combinations.length;

  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-lg">Live Vorschau</h3>
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
    </div>
  );
};
