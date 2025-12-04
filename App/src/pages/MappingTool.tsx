import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MappingEditorState, Group, MappingJSON } from '../types/mapping';
import { GroupEditor } from '../components/mapping/GroupEditor';
import { LivePreview } from '../components/mapping/LivePreview';
import { GlobalGroupMappingEditor } from '../components/mapping/GlobalGroupMappingEditor';
import { generateCombinationsForPreview } from '../utils/combinationGenerator';

export const MappingTool: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<MappingEditorState>({
    family: '',
    groups: [],
    globalGroupMappings: [],
  });

  const addGroup = () => {
    const newGroup: Group = {
      id: `group-${Date.now()}`,
      groupNumber: state.groups.length + 1,
      name: `Gruppe ${state.groups.length + 1}`,
      positions: [],
    };
    setState(prev => ({ ...prev, groups: [...prev.groups, newGroup] }));
  };

  const updateGroup = (groupId: string, updatedGroup: Group) => {
    setState(prev => ({
      ...prev,
      groups: prev.groups.map(g => g.id === groupId ? updatedGroup : g),
    }));
  };

  const deleteGroup = (groupId: string) => {
    setState(prev => ({
      ...prev,
      groups: prev.groups.filter(g => g.id !== groupId),
    }));
  };

  const exportJSON = () => {
    const mappingJSON = convertToMappingJSON(state);
    const blob = new Blob([JSON.stringify(mappingJSON, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mapping_${state.family || 'unnamed'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Visual Mapping Tool
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Erstellen Sie filter_criteria und group_mappings grafisch
              </p>
            </div>
            <button
              onClick={() => navigate('/admin')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              ← Zurück
            </button>
          </div>
          
          {/* Produktfamilie */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Produktfamilie
            </label>
            <input
              type="text"
              value={state.family}
              onChange={e => setState(prev => ({ ...prev, family: e.target.value }))}
              placeholder="z.B. BES"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Pattern wird automatisch basierend auf den Positionen generiert
            </p>
          </div>
        </div>

        {/* Gruppen */}
        <div className="space-y-4 mb-6">
          {state.groups.map(group => (
            <GroupEditor
              key={group.id}
              group={group}
              onUpdate={updatedGroup => updateGroup(group.id, updatedGroup)}
              onDelete={() => deleteGroup(group.id)}
            />
          ))}
        </div>

        {/* Neue Gruppe Button */}
        <button
          onClick={addGroup}
          className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-500 transition-colors mb-6"
        >
          + Neue Gruppe
        </button>

        {/* Global Group Mappings */}
        <div className="mb-6">
          <GlobalGroupMappingEditor
            mappings={state.globalGroupMappings}
            onUpdate={globalGroupMappings => setState({ ...state, globalGroupMappings })}
          />
        </div>

        {/* Live Preview */}
        <LivePreview groups={state.groups} />

        {/* Export Button */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <button
            onClick={exportJSON}
            disabled={!state.family || state.groups.length === 0}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
          >
            Als JSON exportieren
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Konvertiert Editor-State zu mapping.json Format
 */
function convertToMappingJSON(state: MappingEditorState): MappingJSON {
  // Generiere alle Kombinationen für group_position
  const combinations = generateCombinationsForPreview(state.groups);
  const groupPositionString = combinations.join('|');

  // Auto-generiere Pattern basierend auf Positionsstruktur
  const pattern = generatePattern(state.groups);

  // Erstelle group_mappings (neue relative Format)
  // Sammle alle einzigartigen Code-Position-Kombinationen (keine Duplikate)
  const mappingSet = new Map<string, any>(); // Key: "group:position:end_position:code"
  
  for (const group of state.groups) {
    // Sortiere Positionen nach Index
    const sortedPositions = [...group.positions].sort((a, b) => a.positionIndex - b.positionIndex);
    
    // Generiere für jeden Code-Pfad die möglichen Positionen
    const collectCodePositions = (posIndex: number, currentTypecodePos: number) => {
      if (posIndex >= sortedPositions.length) {
        return;
      }
      
      const position = sortedPositions[posIndex];
      
      // Für jeden Code in dieser Position
      for (const code of position.codes) {
        const codeLength = code.value.length;
        const endPos = currentTypecodePos + codeLength - 1;
        
        // Erstelle unique key
        const key = `${group.groupNumber}:${currentTypecodePos}:${endPos}:${code.value}`;
        
        // Nur hinzufügen, wenn noch nicht vorhanden
        if (!mappingSet.has(key)) {
          const mapping: any = {
            group: group.groupNumber,
            position: currentTypecodePos,
            end_position: endPos,  // IMMER setzen, auch bei Länge 1!
            codes: [code.value],
            labels: [
              code.pictures.length > 0 || code.links.length > 0
                ? {
                    text: code.labelDe,
                    ...(code.pictures.length > 0 && { pictures: code.pictures }),
                    ...(code.links.length > 0 && { links: code.links }),
                  }
                : code.labelDe,
            ],
          };
          
          // Füge strict von der Gruppe hinzu, wenn aktiviert
          if (group.strict) {
            mapping.strict = true;
          }
          
          mappingSet.set(key, mapping);
        }
        
        // Rekursion für nächste Position
        collectCodePositions(posIndex + 1, currentTypecodePos + codeLength);
      }
    };
    
    collectCodePositions(0, 1);
  }
  
  // Konvertiere Map zu Array
  const groupMappings = Array.from(mappingSet.values());

  // Erstelle name_mappings (nur Gruppen mit groupName)
  const nameMappings = state.groups
    .filter(group => group.groupName && group.groupName.trim())
    .map(group => ({
      level: group.groupNumber + 1, // Gruppe 1 = Level 2
      name: group.groupName!,
    }));

  // Erstelle special_mappings (nur Gruppen mit specialMapping)
  const specialMappings = state.groups
    .filter(group => group.specialMapping && 
      (group.specialMapping.positionRange || group.specialMapping.allowed))
    .map(group => {
      const mapping: any = { group: group.groupNumber };
      if (group.specialMapping!.positionRange) {
        mapping.position = group.specialMapping!.positionRange;
      }
      if (group.specialMapping!.allowed) {
        mapping.allowed = group.specialMapping!.allowed;
      }
      // Labels
      if (group.specialMapping!.labelsDe && group.specialMapping!.labelsDe.length > 0) {
        mapping.labels = group.specialMapping!.labelsDe;
      }
      if (group.specialMapping!.labelsEn && group.specialMapping!.labelsEn.length > 0) {
        mapping['labels-en'] = group.specialMapping!.labelsEn;
      }
      // Pictures & Links
      if (group.specialMapping!.pictures && group.specialMapping!.pictures.length > 0) {
        mapping.pictures = group.specialMapping!.pictures;
      }
      if (group.specialMapping!.links && group.specialMapping!.links.length > 0) {
        mapping.links = group.specialMapping!.links;
      }
      return mapping;
    });

  return {
    filter_criteria: {
      family: state.family,
      pattern,
      group_position: groupPositionString,
    },
    group_mappings: groupMappings,
    ...(nameMappings.length > 0 && { name_mappings: nameMappings }),
    ...(specialMappings.length > 0 && { special_mappings: specialMappings }),
    ...(state.globalGroupMappings.length > 0 && {
      global_group_mappings: state.globalGroupMappings
        .filter(m => m.group && m.group.length > 0) // Nur mit Namen
        .map(m => {
          const mapping: any = { group: m.group };
          if (m.append) mapping.append = true;
          return mapping;
        }),
    }),
    metadata: {
      created: new Date().toISOString(),
      created_by: 'admin', // TODO: Get from auth context
      tool_version: '1.0',
    },
  };
}

/**
 * Generiert Pattern basierend auf möglichen Gruppen-Längen
 * Neues Format: "1:2|3|4,2:4|5"
 * Bedeutung: Gruppe 1 muss Länge 2, 3 oder 4 haben; Gruppe 2 muss Länge 4 oder 5 haben
 */
function generatePattern(groups: Group[]): string {
  if (groups.length === 0) return '';

  const groupPatterns: string[] = [];

  for (const group of groups) {
    // Berechne alle möglichen Längen für diese Gruppe
    const possibleLengths = calculateGroupLengths(group);
    
    if (possibleLengths.size > 0) {
      const lengthsStr = Array.from(possibleLengths).sort((a, b) => a - b).join('|');
      groupPatterns.push(`${group.groupNumber}:${lengthsStr}`);
    }
  }

  return groupPatterns.join(',');
}

/**
 * Berechnet alle möglichen Längen für eine Gruppe basierend auf Code-Kombinationen
 * Beispiel: Position 1 hat [a, ab], Position 2 hat [c, cd]
 * Ergibt: ac (2), acd (3), abc (3), abcd (4) → Längen: [2, 3, 4]
 */
function calculateGroupLengths(group: Group): Set<number> {
  const lengths = new Set<number>();
  
  if (group.positions.length === 0) return lengths;

  // Sortiere Positionen nach Index
  const sortedPositions = [...group.positions].sort((a, b) => a.positionIndex - b.positionIndex);

  // Rekursiv alle Kombinationen durchgehen und Längen sammeln
  const calculateRecursive = (positionIndex: number, currentLength: number) => {
    if (positionIndex >= sortedPositions.length) {
      lengths.add(currentLength);
      return;
    }

    const position = sortedPositions[positionIndex];
    
    for (const code of position.codes) {
      calculateRecursive(positionIndex + 1, currentLength + code.value.length);
    }
  };

  calculateRecursive(0, 0);
  return lengths;
}
