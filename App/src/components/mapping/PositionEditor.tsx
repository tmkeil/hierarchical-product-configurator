import React, { useState } from 'react';
import { Position, Code } from '../../types/mapping';
import { CodeDetailModal } from './CodeDetailModal';

interface PositionEditorProps {
  position: Position;
  onUpdate: (position: Position) => void;
  onDelete: () => void;
}

export const PositionEditor: React.FC<PositionEditorProps> = ({
  position,
  onUpdate,
  onDelete,
}) => {
  const [newCodeValue, setNewCodeValue] = useState('');
  const [selectedCode, setSelectedCode] = useState<Code | null>(null);

  const addCode = () => {
    if (!newCodeValue.trim()) return;

    const newCode: Code = {
      id: `code-${Date.now()}`,
      value: newCodeValue.trim(),
      labelDe: '',
      labelEn: '',
      pictures: [],
      links: [],
    };

    onUpdate({
      ...position,
      codes: [...position.codes, newCode],
    });
    setNewCodeValue('');
  };

  const updateCode = (codeId: string, updatedCode: Code) => {
    onUpdate({
      ...position,
      codes: position.codes.map(c => c.id === codeId ? updatedCode : c),
    });
  };

  const deleteCode = (codeId: string) => {
    onUpdate({
      ...position,
      codes: position.codes.filter(c => c.id !== codeId),
    });
  };

  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">
          Position #{position.positionIndex + 1}
        </span>
        <button
          onClick={onDelete}
          className="text-red-600 hover:text-red-700 text-sm"
          title="Position löschen"
        >
          ✕
        </button>
      </div>

      {/* Codes */}
      <div className="mb-3">
        <div className="flex flex-wrap gap-2">
          {position.codes.map(code => (
            <div
              key={code.id}
              className="inline-flex items-center gap-2 bg-white border border-gray-300 rounded px-3 py-1.5 group hover:border-blue-500 transition-colors cursor-pointer"
              onClick={() => setSelectedCode(code)}
              title="Klicken zum Bearbeiten"
            >
              <span className="font-mono text-sm font-semibold">{code.value}</span>
              <span className="text-sm text-gray-600 max-w-[150px] truncate">
                {code.labelDe || 'Keine Beschreibung'}
              </span>
              {(code.pictures.length > 0 || code.links.length > 0) && (
                <span className="text-xs text-blue-600">
                  {code.pictures.length > 0 && `🖼️${code.pictures.length}`}
                  {code.links.length > 0 && `🔗${code.links.length}`}
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteCode(code.id);
                }}
                className="text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        {position.codes.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            💡 Klicken Sie auf einen Code, um Beschreibungen, Bilder und Links hinzuzufügen
          </p>
        )}
      </div>

      {/* Code hinzufügen */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newCodeValue}
          onChange={e => setNewCodeValue(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && addCode()}
          placeholder="Code-Wert (z.B. G, K, M)"
          className="flex-1 text-sm px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          onClick={addCode}
          disabled={!newCodeValue.trim()}
          className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          + Code
        </button>
      </div>

      {/* Code Detail Modal */}
      {selectedCode && (
        <CodeDetailModal
          code={selectedCode}
          onSave={(updatedCode) => {
            updateCode(selectedCode.id, updatedCode);
            setSelectedCode(null);
          }}
          onClose={() => setSelectedCode(null)}
        />
      )}
    </div>
  );
};
