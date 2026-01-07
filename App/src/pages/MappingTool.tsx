import React, { useState, useCallback } from 'react';
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
  const [isProcessing, setIsProcessing] = useState(false);
  
  // DEBUG: Log bei jedem Render
  console.log('[MappingTool] Render - Groups:', state.groups.length);

  const addGroup = useCallback(() => {
    setState(prev => {
      const newGroup: Group = {
        id: `group-${Date.now()}`,
        groupNumber: prev.groups.length + 1,
        name: `Gruppe ${prev.groups.length + 1}`,
        positions: [],
      };
      return { ...prev, groups: [...prev.groups, newGroup] };
    });
  }, []);

  const updateGroup = useCallback((groupId: string, updatedGroup: Group) => {
    setState(prev => ({
      ...prev,
      groups: prev.groups.map(g => g.id === groupId ? updatedGroup : g),
    }));
  }, []);

  const deleteGroup = useCallback((groupId: string) => {
    setState(prev => ({
      ...prev,
      groups: prev.groups.filter(g => g.id !== groupId),
    }));
  }, []);

  const exportJSON = async () => {
    try {
      // Zeige visuelles Feedback
      const button = document.activeElement as HTMLButtonElement;
      if (button) button.disabled = true;
      
      // Generiere JSON asynchron
      await new Promise(resolve => setTimeout(resolve, 0));
      const mappingJSON = convertToMappingJSON(state);
      
      await new Promise(resolve => setTimeout(resolve, 0));
      const blob = new Blob([JSON.stringify(mappingJSON, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mapping_${state.family || 'unnamed'}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      if (button) button.disabled = false;
    } catch (error) {
      console.error('Fehler beim Exportieren:', error);
    }
  };

  const importJSON = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    
    // Sofort UI updaten
    await new Promise(resolve => setTimeout(resolve, 0));

    try {
      const text = await file.text();
      await new Promise(resolve => setTimeout(resolve, 10));
      
      const json = JSON.parse(text);
      await new Promise(resolve => setTimeout(resolve, 10));
      
      // Zeige sofort State mit nur Family
      setState({ family: json.filter_criteria.family || '', groups: [], globalGroupMappings: [] });
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Konvertiere in Chunks
      const importedState = await convertFromMappingJSONAsync(json);
      setState(importedState);
    } catch (error) {
      console.error('Fehler beim Importieren:', error);
    } finally {
      setIsProcessing(false);
      event.target.value = '';
    }
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

          {/* Import Button */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bestehendes Mapping importieren
            </label>
            {isProcessing ? (
              <div className="text-sm text-blue-600">Verarbeite JSON...</div>
            ) : (
              <input
                type="file"
                accept=".json"
                onChange={importJSON}
                disabled={isProcessing}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  disabled:opacity-50"
              />
            )}
            <p className="text-xs text-gray-500 mt-1">
              Laden Sie ein bestehendes mapping.json, um es zu bearbeiten
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
            onUpdate={globalGroupMappings => setState(prev => ({ ...prev, globalGroupMappings }))}
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
  // Generiere alle Kombinationen für group_position (nur für Gruppen mit Codes)
  const groupsWithCodes = state.groups.filter(g => g.positions.some(p => p.codes.length > 0));
  const combinations = generateCombinationsForPreview(groupsWithCodes);
  const groupPositionString = combinations.join('|');

  // Auto-generiere Pattern basierend auf Positionsstruktur (nur für Gruppen mit Codes)
  const pattern = generatePattern(groupsWithCodes);

  // Erstelle group_mappings (gruppiere Codes mit gleicher Position)
  const positionMap = new Map<string, { codes: any[], labels: any[], strict?: boolean }>(); // Key: "group:position:end_position"
  
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
        
        // Erstelle key für Position (ohne Code)
        const posKey = `${group.groupNumber}:${currentTypecodePos}:${endPos}`;
        
        // Gruppiere Codes mit gleicher Position
        if (!positionMap.has(posKey)) {
          positionMap.set(posKey, {
            codes: [],
            labels: [],
            ...(group.strict && { strict: true }),
          });
        }
        
        const posGroup = positionMap.get(posKey)!;
        
        // Füge Code hinzu (nur wenn noch nicht vorhanden)
        if (!posGroup.codes.includes(code.value)) {
          posGroup.codes.push(code.value);
          posGroup.labels.push(
            code.pictures.length > 0 || code.links.length > 0
              ? {
                  text: code.labelDe,
                  ...(code.pictures.length > 0 && { pictures: code.pictures }),
                  ...(code.links.length > 0 && { links: code.links }),
                }
              : code.labelDe
          );
        }
        
        // Rekursion für nächste Position
        collectCodePositions(posIndex + 1, currentTypecodePos + codeLength);
      }
    };
    
    collectCodePositions(0, 1);
  }
  
  // Konvertiere Map zu Array
  const groupMappings = Array.from(positionMap.entries()).map(([key, data]) => {
    const [group, position, end_position] = key.split(':').map(Number);
    return {
      group,
      position,
      end_position,
      codes: data.codes,
      labels: data.labels,
      ...(data.strict && { strict: true }),
    };
  });

  // Erstelle name_mappings (nur Gruppen mit groupName)
  const nameMappings = state.groups
    .filter(group => group.groupName && group.groupName.trim())
    .map(group => ({
      level: group.groupNumber + 1, // Gruppe 1 = Level 2
      name: group.groupName!,
    }));

  // Erstelle special_mappings (nur Gruppen mit specialMapping)
  const specialMappings = state.groups
    .filter(group => group.specialMapping && (
      group.specialMapping.positionRange || 
      group.specialMapping.allowed ||
      (group.specialMapping.labelsDe && group.specialMapping.labelsDe.length > 0) ||
      (group.specialMapping.labelsEn && group.specialMapping.labelsEn.length > 0) ||
      (group.specialMapping.pictures && group.specialMapping.pictures.length > 0) ||
      (group.specialMapping.links && group.specialMapping.links.length > 0)
    ))
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
 * Konvertiert mapping.json zurück zum Editor-State (ASYNCHRON in Chunks)
 */
async function convertFromMappingJSONAsync(json: MappingJSON): Promise<MappingEditorState> {
  const family = json.filter_criteria.family;
  const timestamp = Date.now();
  
  // CHUNK 1: Erstelle Gruppen-Skelett
  const groupsMap = new Map<number, Group>();
  for (const mapping of json.group_mappings) {
    if (!groupsMap.has(mapping.group)) {
      groupsMap.set(mapping.group, {
        id: `group-${mapping.group}`,
        groupNumber: mapping.group,
        name: `Gruppe ${mapping.group}`,
        positions: [],
      });
    }
  }
  
  // UI Pause
  await new Promise(resolve => setTimeout(resolve, 0));
  
  // CHUNK 2: Füge Metadaten hinzu (name_mappings, special_mappings, strict)
  if (json.name_mappings) {
    for (const nameMapping of json.name_mappings) {
      const groupNum = nameMapping.level - 1;
      const group = groupsMap.get(groupNum);
      if (group) group.groupName = nameMapping.name;
    }
  }
  
  if (json.special_mappings) {
    for (const specialMapping of json.special_mappings) {
      const group = groupsMap.get(specialMapping.group);
      if (group) {
        group.specialMapping = {
          positionRange: specialMapping.position,
          allowed: specialMapping.allowed,
          labelsDe: specialMapping.labels,
          labelsEn: specialMapping['labels-en'],
          pictures: specialMapping.pictures,
          links: specialMapping.links,
        };
      }
    }
  }
  
  for (const mapping of json.group_mappings) {
    if (mapping.strict) {
      const group = groupsMap.get(mapping.group);
      if (group) group.strict = true;
    }
  }
  
  // UI Pause
  await new Promise(resolve => setTimeout(resolve, 0));
  
  // CHUNK 3: Gruppiere Mappings nach Gruppe
  const groupMappingsMap = new Map<number, typeof json.group_mappings>();
  for (const mapping of json.group_mappings) {
    if (!groupMappingsMap.has(mapping.group)) {
      groupMappingsMap.set(mapping.group, []);
    }
    groupMappingsMap.get(mapping.group)!.push(mapping);
  }
  
  // UI Pause
  await new Promise(resolve => setTimeout(resolve, 0));
  
  // CHUNK 4: Rekonstruiere Positionen (batch-weise pro Gruppe)
  let processedGroups = 0;
  for (const [groupNum, mappings] of groupMappingsMap) {
    const group = groupsMap.get(groupNum)!;
    const positionsMap = new Map<number, Map<string, any[]>>();
    
    // Vereinfachte Rekonstruktion: Gruppiere nach position+end_position
    for (const mapping of mappings) {
      const posKey = `${mapping.position}:${mapping.end_position}`;
      
      if (!positionsMap.has(0)) positionsMap.set(0, new Map());
      const posMap = positionsMap.get(0)!;
      if (!posMap.has(posKey)) posMap.set(posKey, []);
      
      // Batch: Füge alle Codes hinzu
      const codeArray = posMap.get(posKey)!;
      for (let i = 0; i < mapping.codes.length; i++) {
        const code = mapping.codes[i];
        const label = mapping.labels[i];
        codeArray.push({
          id: `code-${timestamp}-${groupNum}-${codeArray.length}`,
          value: code,
          labelDe: typeof label === 'string' ? label : label.text,
          labelEn: '',
          pictures: typeof label === 'object' && label.pictures ? label.pictures : [],
          links: typeof label === 'object' && label.links ? label.links : [],
        });
      }
    }
    
    // Erstelle Positionen
    let posIndex = 0;
    for (const codesMap of positionsMap.values()) {
      for (const codes of codesMap.values()) {
        group.positions.push({
          id: `position-${timestamp}-${groupNum}-${posIndex}`,
          positionIndex: posIndex++,
          codes: codes,
        });
      }
    }
    
    // Pause alle 5 Gruppen
    processedGroups++;
    if (processedGroups % 5 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
  
  // CHUNK 5: Global Group Mappings
  const globalGroupMappings = (json.global_group_mappings || []).map((gm, idx) => ({
    id: `global-${timestamp}-${idx}`,
    group: gm.group,
    append: gm.append,
  }));
  
  return {
    family,
    groups: Array.from(groupsMap.values()).sort((a, b) => a.groupNumber - b.groupNumber),
    globalGroupMappings,
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