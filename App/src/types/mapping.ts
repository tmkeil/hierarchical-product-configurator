/**
 * TypeScript Interfaces für Visual Mapping Tool
 * Entspricht dem Format in mapping.json
 */

export interface FilterCriteria {
  family: string;
  pattern: string;
  group_position: string;
}

export interface GroupMapping {
  group: number;
  position: number;
  codes: string[];
  labels: (string | LabelWithMedia)[];
  strict?: boolean;
}

export interface LabelWithMedia {
  text: string;
  pictures?: Picture[];
  links?: Link[];
}

export interface Picture {
  url: string;
  description: string;
}

export interface Link {
  url: string;
  description: string;
}

export interface NameMapping {
  level: number;
  name: string;
}

export interface SpecialMapping {
  group: number;
  position?: string;
  allowed?: string;
  labels?: string[];
  'labels-en'?: string[];
  pictures?: Picture[];
  links?: Link[];
}

export interface GlobalGroupMapping {
  id: string;
  group: string; // Gruppen-Name (Referenz auf filter_criteria)
  append?: boolean;
}

export interface MappingMetadata {
  created: string;
  created_by: string;
  tool_version: string;
}

export interface MappingJSON {
  filter_criteria: FilterCriteria;
  group_mappings: GroupMapping[];
  name_mappings?: NameMapping[];
  special_mappings?: SpecialMapping[];
  global_group_mappings?: Array<{ group: string; append?: boolean }>; // Export-Format
  metadata: MappingMetadata;
}

/**
 * Internal Types für Visual Editor State
 */

export interface Position {
  id: string;
  positionIndex: number; // Reihenfolge: 0, 1, 2, ... (nicht die Typecode-Position!)
  codes: Code[];
}

export interface Code {
  id: string;
  value: string;
  labelDe: string;
  labelEn?: string;
  pictures: Picture[];
  links: Link[];
}

export interface Group {
  id: string;
  groupNumber: number;
  name: string;
  groupName?: string; // Optional: Name für name_mappings
  strict?: boolean; // Strict Mode für alle Positionen dieser Gruppe
  positions: Position[];
  specialMapping?: {
    positionRange?: string; // z.B. "3-6"
    allowed?: string; // z.B. "1-4", "0-Z", "A-Z"
    labelsDe?: string[];
    labelsEn?: string[];
    pictures?: Picture[];
    links?: Link[];
  };
}

export interface MappingEditorState {
  family: string;
  groups: Group[];
  globalGroupMappings: GlobalGroupMapping[];
}
