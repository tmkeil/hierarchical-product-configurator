import React from 'react';
import { Group, Position } from '../../types/mapping';
import { PositionEditor } from './PositionEditor';
import { SpecialMappingEditor } from './SpecialMappingEditor';

interface GroupEditorProps {
  group: Group;
  onUpdate: (group: Group) => void;
  onDelete: () => void;
}

export const GroupEditor: React.FC<GroupEditorProps> = ({ group, onUpdate, onDelete }) => {
  const addPosition = () => {
    const newPosition = {
      id: `position-${Date.now()}`,
      positionIndex: group.positions.length,
      codes: [],
    };
    onUpdate({ ...group, positions: [...group.positions, newPosition] });
  };

  const updatePosition = (positionId: string, updatedPosition: any) => {
    onUpdate({
      ...group,
      positions: group.positions.map(p => p.id === positionId ? updatedPosition : p),
    });
  };

  const deletePosition = (positionId: string) => {
    onUpdate({
      ...group,
      positions: group.positions.filter(p => p.id !== positionId),
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={group.name}
              onChange={e => onUpdate({ ...group, name: e.target.value })}
              placeholder="Gruppen-Titel"
              className="text-lg font-semibold border-none focus:ring-2 focus:ring-blue-500 px-2 py-1 rounded"
            />
            <span className="text-sm text-gray-500">
              (Gruppe {group.groupNumber})
            </span>
          </div>
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-700 px-3 py-1 rounded hover:bg-red-50"
            title="Gruppe löschen"
          >
            🗑️
          </button>
        </div>
        
        {/* Optional: Name Mapping */}
        <div className="mb-2">
          <label className="text-sm text-gray-600">
            Name (optional, für name_mappings):
          </label>
          <input
            type="text"
            value={group.groupName || ''}
            onChange={e => onUpdate({ ...group, groupName: e.target.value || undefined })}
            placeholder="z.B. Gehäuse"
            className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent mt-1"
          />
        </div>

        {/* Strict Mode Checkbox */}
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded p-2">
          <input
            type="checkbox"
            id={`strict-${group.id}`}
            checked={group.strict || false}
            onChange={e => onUpdate({ ...group, strict: e.target.checked })}
            className="mt-0.5"
          />
          <label htmlFor={`strict-${group.id}`} className="text-xs text-gray-700 cursor-pointer">
            <strong>Strict Mode:</strong> Nur die definierten Codes dieser Gruppe sind erlaubt. 
            Wenn deaktiviert, werden auch andere Werte akzeptiert (z.B. für optionale Varianten).
          </label>
        </div>

        {/* Special Mapping */}
        <SpecialMappingEditor group={group} onUpdate={onUpdate} />
      </div>

      {/* Positionen */}
      <div className="p-4 space-y-3">
        {group.positions.map(position => (
          <PositionEditor
            key={position.id}
            position={position}
            onUpdate={(updatedPosition: Position) => updatePosition(position.id, updatedPosition)}
            onDelete={() => deletePosition(position.id)}
          />
        ))}

        {/* Neue Position Button */}
        <button
          onClick={addPosition}
          className="w-full py-2 border border-dashed border-gray-300 rounded text-gray-600 hover:border-blue-500 hover:text-blue-500 text-sm"
        >
          + Position hinzufügen
        </button>
      </div>
    </div>
  );
};
