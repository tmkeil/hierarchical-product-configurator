import React from 'react';
import { GlobalGroupMapping } from '../../types/mapping';

interface GlobalGroupMappingEditorProps {
  mappings: GlobalGroupMapping[];
  onUpdate: (mappings: GlobalGroupMapping[]) => void;
}

export const GlobalGroupMappingEditor: React.FC<GlobalGroupMappingEditorProps> = ({
  mappings,
  onUpdate,
}) => {
  const addMapping = () => {
    const newMapping: GlobalGroupMapping = {
      id: `global-${Date.now()}`,
      group: '',
      append: false,
    };
    onUpdate([...mappings, newMapping]);
  };

  const updateMapping = (id: string, updated: GlobalGroupMapping) => {
    onUpdate(mappings.map(m => (m.id === id ? updated : m)));
  };

  const deleteMapping = (id: string) => {
    onUpdate(mappings.filter(m => m.id !== id));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Global Group Mappings</h3>
        <button
          onClick={addMapping}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
        >
          + Mapping hinzufügen
        </button>
      </div>

      {/* Info Box */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-gray-700">
        <p className="font-semibold mb-1">ℹ️ Global Group Mappings</p>
        <p>
          Referenziert eine Gruppe aus den <strong>filter_criteria</strong>. 
          Die Codes/Labels werden automatisch übernommen. 
          <strong>Append</strong> fügt die Daten hinzu, statt sie zu überschreiben.
        </p>
      </div>

      {/* Mappings List */}
      <div className="space-y-3">
        {mappings.length === 0 ? (
          <div className="text-center py-8 text-gray-400 border border-dashed border-gray-300 rounded">
            Keine Global Group Mappings definiert
          </div>
        ) : (
          mappings.map(mapping => (
            <div
              key={mapping.id}
              className="border border-gray-300 rounded p-3 bg-gray-50"
            >
              <div className="flex items-start gap-3">
                {/* Group Name Input */}
                <div className="flex-1">
                  <label className="text-xs text-gray-600 mb-1 block">
                    Gruppen-Name (Referenz)
                  </label>
                  <input
                    type="text"
                    value={mapping.group}
                    onChange={e =>
                      updateMapping(mapping.id, { ...mapping, group: e.target.value })
                    }
                    placeholder="z.B. Cordset, Gehäuse, ..."
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                {/* Append Checkbox */}
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id={`append-${mapping.id}`}
                    checked={mapping.append || false}
                    onChange={e =>
                      updateMapping(mapping.id, { ...mapping, append: e.target.checked })
                    }
                    className="rounded"
                  />
                  <label
                    htmlFor={`append-${mapping.id}`}
                    className="text-sm text-gray-700 cursor-pointer whitespace-nowrap"
                  >
                    Append
                  </label>
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => deleteMapping(mapping.id)}
                  className="text-red-600 hover:text-red-700 pt-6"
                  title="Mapping löschen"
                >
                  🗑️
                </button>
              </div>

              {/* Append Explanation */}
              {mapping.append && (
                <div className="mt-2 text-xs text-gray-600 bg-yellow-50 border border-yellow-200 rounded p-2">
                  <strong>Append-Modus:</strong> Daten werden hinzugefügt, nicht überschrieben.
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};