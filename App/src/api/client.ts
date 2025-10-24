/**
 * API Client für Variantenbaum Backend
 * 
 * Ersetzt die 730 Zeilen Tree-Traversal Logik in variantenbaum.ts
 * mit einfachen API Calls gegen die Closure Table.
 */

// API Base URL aus Environment Variable (Vite)
// VITE_API_BASE_URL sollte nur die Base URL sein (z.B. http://localhost:8000)
// /api wird hier angehängt
const API_BASE = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api`;

// ============================================================
// Auth Token Management
// ============================================================

const TOKEN_KEY = 'auth_token';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ============================================================
// Types (wie Backend Pydantic Models)
// ============================================================

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface Node {
  id?: number;  // Node ID from database
  code: string | null;
  label?: string | null;
  label_en?: string | null;
  name?: string | null;  // Name-Attribut für Beschreibung
  level: number;
  position: number;
  group_name?: string | null;
  pattern?: number | null;
  pictures?: NodePicture[];  // Bilder für diesen Node
  links?: NodeLink[];  // Links für diesen Node
}

export interface NodePicture {
  url: string;
  description?: string | null;
  uploaded_at: string;
}

export interface NodeLink {
  url: string;
  title: string;
  description?: string | null;
  added_at?: string;
}

export interface AvailableOption {
  id?: number;  // Primäre Node ID (erste gefundene)
  ids?: number[];  // ALLE Node IDs mit diesem Code (für Multi-Pfad-Kompatibilität!)
  code: string;
  label?: string | null;
  label_en?: string | null;
  name?: string | null;  // Name-Attribut für Beschreibung
  group_name?: string | null;  // Group-Name-Attribut
  level: number;
  position: number;
  is_compatible: boolean;
  parent_pattern?: number | null;  // Für Gruppierung nach Branch/Pattern
  pictures?: NodePicture[];  // Bilder für diese Option
  links?: NodeLink[];  // Links für diese Option
}

export interface Selection {
  code: string;
  level: number;
  id?: number;  // Primäre Node ID (deprecated - verwende ids!)
  ids?: number[];  // ALLE Node IDs mit diesem Code (für Multi-Pfad-Kompatibilität!)
}

export interface OptionsRequest {
  target_level: number;
  previous_selections: Selection[];
  group_filter?: string | null;
}

export interface PathNode {
  code: string;
  label?: string | null;
  label_en?: string | null;
  level: number;
  depth: number;
}

export interface NodeCheckResult {
  exists: boolean;
  code?: string | null;
  label?: string | null;
  label_en?: string | null;
  level?: number | null;
  families: string[];
  is_complete_product?: boolean;
  product_type?: string;
}

export interface CodePathSegment {
  level: number;
  code: string;
  name?: string | null;
  label?: string | null;
  label_en?: string | null;
  position_start?: number | null;
  position_end?: number | null;
  group_name?: string | null;
  pictures?: NodePicture[];  // Bilder für dieses Segment
  links?: NodeLink[];  // Links für dieses Segment
}

export interface TypecodeDecodeResult {
  exists: boolean;
  original_input: string;
  normalized_code?: string | null;
  is_complete_product: boolean;
  product_type: string;
  path_segments: CodePathSegment[];
  full_typecode?: string | null;
  families: string[];
  group_name?: string | null;  // Produktattribut (von erster Produktfamilie)
}

export interface HealthResponse {
  status: string;
  database: string;
  total_nodes: number;
  total_paths: number;
}

// ============================================================
// Constraint Types
// ============================================================

export interface ConstraintCondition {
  id?: number;
  condition_type: 'pattern' | 'prefix' | 'exact_code';
  target_level: number;
  value: string;
}

export interface ConstraintCode {
  id?: number;
  code_type: 'single' | 'range';
  code_value: string;
}

export interface Constraint {
  id?: number;
  level: number;
  mode: 'allow' | 'deny';
  description?: string | null;
  conditions: ConstraintCondition[];
  codes: ConstraintCode[];
  created_at?: string;
  updated_at?: string;
}

export interface CreateConstraintRequest {
  level: number;
  mode: 'allow' | 'deny';
  description?: string | null;
  conditions: ConstraintCondition[];
  codes: ConstraintCode[];
}

export interface ConstraintValidationResult {
  is_valid: boolean;
  violated_constraints: Constraint[];
  message?: string | null;
}

// ============================================================
// Helper Functions
// ============================================================

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // JWT Token aus localStorage holen (falls vorhanden)
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  
  // Authorization Header hinzufügen wenn Token vorhanden
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    // 401 Unauthorized -> Token ist invalid/abgelaufen, redirect zu Login
    if (response.status === 401) {
      removeAuthToken();
      // Frontend wird durch Auth Context Provider automatisch zu /login redirecten
    }
    
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    console.error('API Error Details:', error);
    throw new Error(JSON.stringify(error.detail || error));
  }

  return response.json();
}

// ============================================================
// AUTH API Functions
// ============================================================

/**
 * POST /api/auth/login
 * 
 * Login mit Username/Password
 */
export async function login(username: string, password: string): Promise<Token> {
  const response = await fetchApi<Token>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  
  // Token in localStorage speichern
  setAuthToken(response.access_token);
  
  return response;
}

/**
 * POST /api/auth/logout
 * 
 * Logout (entfernt Token aus localStorage)
 */
export async function logout(): Promise<void> {
  try {
    // Backend informieren (für evtl. Token-Blacklisting)
    await fetchApi('/auth/logout', { method: 'POST' });
  } finally {
    // Token immer entfernen, auch bei Fehler
    removeAuthToken();
  }
}

/**
 * GET /api/auth/me
 * 
 * Holt Infos über aktuell eingeloggten User
 */
export async function getCurrentUser(): Promise<User> {
  return fetchApi<User>('/auth/me');
}

/**
 * POST /api/auth/change-password
 * 
 * Ändert Passwort des eingeloggten Users
 */
export async function changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
    }),
  });
}

// ============================================================
// API Functions
// ============================================================

/**
 * GET /api/product-families
 * 
 * Ersetzt: getProductFamilies() in variantenbaum.ts
 */
export async function fetchProductFamilies(): Promise<Node[]> {
  return fetchApi<Node[]>('/product-families');
}

/**
 * GET /api/product-families/{family_code}/groups
 * 
 * Holt alle verfügbaren group_names für eine Produktfamilie
 */
export async function fetchFamilyGroups(familyCode: string): Promise<string[]> {
  return fetchApi<string[]>(`/product-families/${familyCode}/groups`);
}

/**
 * GET /api/product-families/{family_code}/groups/{group_name}/max-level
 * 
 * Gibt die maximale Level-Tiefe für eine bestimmte Group zurück
 */
export async function fetchGroupMaxLevel(familyCode: string, groupName: string): Promise<{ max_level: number }> {
  return fetchApi<{ max_level: number }>(`/product-families/${familyCode}/groups/${groupName}/max-level`);
}

/**
 * GET /api/nodes/suggest-codes
 * 
 * Schlägt Codes vor basierend auf Partial-Match
 */
export async function suggestCodes(partial: string, familyCode: string, level: number, limit: number = 10): Promise<{ suggestions: string[] }> {
  const params = new URLSearchParams({
    partial,
    family_code: familyCode,
    level: level.toString(),
    limit: limit.toString()
  });
  return fetchApi<{ suggestions: string[] }>(`/nodes/suggest-codes?${params}`);
}

/**
 * GET /api/nodes/check-code-exists
 * 
 * Prüft ob ein Code bereits existiert
 */
export async function checkCodeExists(
  code: string,
  familyCode: string,
  level: number,
  parentId?: number
): Promise<{ exists: boolean }> {
  const params = new URLSearchParams({
    code,
    family_code: familyCode,
    level: level.toString()
  });
  
  if (parentId !== undefined) {
    params.append('parent_id', parentId.toString());
  }
  
  return fetchApi<{ exists: boolean }>(`/nodes/check-code-exists?${params}`);
}

/**
 * GET /api/nodes/{code}/children
 * 
 * Ersetzt: Tree-Traversal für direkte Kinder
 */
export async function fetchChildren(parentCode: string): Promise<Node[]> {
  return fetchApi<Node[]>(`/nodes/${parentCode}/children`);
}

/**
 * GET /api/nodes/{code}/max-depth
 */
export async function fetchMaxDepth(nodeCode: string): Promise<{ max_depth: number }> {
  return fetchApi<{ max_depth: number }>(`/nodes/${nodeCode}/max-depth`);
}

/**
 * GET /api/nodes/{code}/max-level
 * 
 * **WICHTIG für UI!** Gibt maximale LEVEL (User-Selections) zurück,
 * nicht DEPTH (Tree-Hops). Pattern Container werden nicht gezählt.
 */
export async function fetchMaxLevel(nodeCode: string, familyCode?: string): Promise<{ max_level: number }> {
  const url = familyCode 
    ? `/nodes/${nodeCode}/max-level?family_code=${familyCode}`
    : `/nodes/${nodeCode}/max-level`;
  return fetchApi<{ max_level: number }>(url);
}

/**
 * POST /api/options
 * 
 * **WICHTIGSTER API CALL!**
 * 
 * Ersetzt die gesamte Kompatibilitäts-Logik:
 * - getAvailableOptionsForLevel()
 * - testBidirectionalCompatibility()
 * - testPathCompatibility()
 * - findAllNodesAtLevel()
 * - canReachLaterSelectionsFromNode()
 * - findCodeFromNodeAtLevel()
 * - testMultiLevelPathExists()
 * - und 10+ weitere Funktionen!
 * 
 * Performance: ~10-50ms (statt mehrere Sekunden mit Rekursion!)
 */
export async function fetchAvailableOptions(
  targetLevel: number,
  previousSelections: Selection[],
  groupFilter?: string | null
): Promise<AvailableOption[]> {
  return fetchApi<AvailableOption[]>('/options', {
    method: 'POST',
    body: JSON.stringify({
      target_level: targetLevel,
      previous_selections: previousSelections,
      group_filter: groupFilter || null,
    }),
  });
}

/**
 * GET /api/nodes/{code}
 */
export async function fetchNode(code: string): Promise<Node> {
  return fetchApi<Node>(`/nodes/${code}`);
}

/**
 * GET /api/nodes/{code}/path
 */
export async function fetchNodePath(code: string): Promise<PathNode[]> {
  return fetchApi<PathNode[]>(`/nodes/${code}/path`);
}

/**
 * GET /api/health
 */
export async function fetchHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/health');
}

/**
 * GET /api/nodes/check/{code}
 */
export async function checkNodeCode(code: string): Promise<NodeCheckResult> {
  return fetchApi<NodeCheckResult>(`/nodes/check/${code}`);
}

/**
 * GET /api/nodes/decode/{code}
 */
export async function decodeTypecode(code: string): Promise<TypecodeDecodeResult> {
  return fetchApi<TypecodeDecodeResult>(`/nodes/decode/${code}`);
}

/**
 * GET /api/nodes/search
 * 
 * Erweiterte Suche mit verschiedenen Filtern
 */
export interface AdvancedSearchFilters {
  pattern?: number;      // Codelänge
  prefix?: string;       // Code beginnt mit
  postfix?: string;      // Code endet mit
  label?: string;        // Suche in Labels
  family?: string;       // Produktfamilie
}

export interface AdvancedSearchResult {
  level: number;
  count: number;
  filters_applied: AdvancedSearchFilters;
  options: AvailableOption[];
}

export async function advancedSearch(
  level: number,
  filters: AdvancedSearchFilters
): Promise<AdvancedSearchResult> {
  const params = new URLSearchParams({ level: level.toString() });
  
  if (filters.pattern !== undefined) params.append('pattern', filters.pattern.toString());
  if (filters.prefix) params.append('prefix', filters.prefix);
  if (filters.postfix) params.append('postfix', filters.postfix);
  if (filters.label) params.append('label', filters.label);
  if (filters.family) params.append('family', filters.family);
  
  return fetchApi<AdvancedSearchResult>(`/nodes/search?${params.toString()}`);
}

/**
 * PUT /api/nodes/{node_id}
 * Update node attributes
 */
export interface UpdateNodeData {
  code?: string;
  name?: string;
  label?: string;
  label_en?: string;
  group_name?: string;
}

export interface UpdateNodeResponse {
  success: boolean;
  message: string;
}

export async function updateNode(
  nodeId: number,
  data: UpdateNodeData
): Promise<UpdateNodeResponse> {
  const response = await fetch(`${API_BASE}/nodes/${nodeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update node');
  }
  
  return response.json();
}

/**
 * POST /api/nodes/bulk-filter
 * Filter nodes based on multiple criteria
 */
export interface BulkFilterRequest {
  level: number;
  family_code: string;
  code?: string;
  code_prefix?: string;
  code_content?: {
    position?: number;  // Optional: Wenn nicht angegeben, wird im gesamten Code gesucht
    value: string;
  };
  group_name?: string;
  name?: string;
  pattern?: string;  // Codelänge: exakt ("3") oder Range ("2-4")
  // Erweiterte Filter für kompatibel/inkompatibel Splits
  parent_level_patterns?: Record<number, {length: string; type: '' | 'alphabetic' | 'numeric' | 'alphanumeric'}>;  // {level: {length: "3" | "2-4", type: "numeric"}}
  parent_level_options?: Record<number, string[]>;  // {level: ["ABC", "DEF"]} - Nur exakte Codes!
  allowed_pattern?: {
    from: number;
    to?: number;
    allowed: 'alphabetic' | 'numeric' | 'alphanumeric';
  };
}

export interface BulkFilterResponse {
  nodes: AvailableOption[];
  count: number;
}

export async function bulkFilterNodes(
  filters: BulkFilterRequest
): Promise<BulkFilterResponse> {
  return fetchApi<BulkFilterResponse>('/nodes/bulk-filter', {
    method: 'POST',
    body: JSON.stringify(filters),
  });
}

/**
 * PUT /api/nodes/bulk-update
 * Update multiple nodes at once
 */
export interface BulkUpdateRequest {
  node_ids: number[];
  updates: {
    name?: string;
    label?: string;
    label_en?: string;
    group_name?: string;
    // Append-Felder (fügen Werte hinzu statt zu ersetzen)
    append_name?: string;
    append_label?: string;
    append_label_en?: string;
    append_group_name?: string;
  };
}

export interface BulkUpdateResponse {
  success: boolean;
  updated_count: number;
  message: string;
}

export async function bulkUpdateNodes(
  data: BulkUpdateRequest
): Promise<BulkUpdateResponse> {
  return fetchApi<BulkUpdateResponse>('/nodes/bulk-update', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * GET /api/nodes/by-code/{code}/level/{level}/ids
 * Holt ALLE Node-IDs mit einem Code auf einem Level (unabhängig von Kompatibilität).
 */
export interface AllNodeIdsResponse {
  code: string;
  level: number;
  ids: number[];
  count: number;
}

export async function getAllNodeIdsByCodeLevel(
  code: string,
  level: number
): Promise<AllNodeIdsResponse> {
  return fetchApi<AllNodeIdsResponse>(
    `/nodes/by-code/${encodeURIComponent(code)}/level/${level}/ids`
  );
}

/**
 * POST /api/nodes/by-path/find-id
 * Findet die spezifische Node-ID für einen Code basierend auf dem Parent-Pfad
 */
export interface FindNodeIdByPathResponse {
  found: boolean;
  node_id: number | null;
  node?: {
    id: number;
    code: string;
    label?: string | null;
    label_en?: string | null;
    name?: string | null;
    level: number;
    position: number;
    group_name?: string | null;
  };
  message?: string;
}

export async function findNodeIdByPath(
  code: string,
  level: number,
  familyCode: string,
  parentCodes: string[]
): Promise<FindNodeIdByPathResponse> {
  return fetchApi<FindNodeIdByPathResponse>('/nodes/by-path/find-id', {
    method: 'POST',
    body: JSON.stringify({
      code,
      level,
      family_code: familyCode,
      parent_codes: parentCodes
    }),
  });
}

// ============================================================
// Constraint API Functions
// ============================================================

/**
 * GET /api/constraints/level/{level}
 * Holt alle Constraints für ein Level
 */
export async function fetchConstraintsForLevel(level: number): Promise<Constraint[]> {
  return fetchApi<Constraint[]>(`/constraints/level/${level}`);
}

/**
 * POST /api/constraints
 * Erstellt eine neue Constraint
 */
export async function createConstraint(request: CreateConstraintRequest): Promise<Constraint> {
  return fetchApi<Constraint>('/constraints', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * PUT /api/constraints/{id}
 * Aktualisiert eine Constraint
 */
export async function updateConstraint(id: number, request: CreateConstraintRequest): Promise<Constraint> {
  return fetchApi<Constraint>(`/constraints/${id}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * DELETE /api/constraints/{id}
 * Löscht eine Constraint
 */
export async function deleteConstraint(id: number): Promise<{ success: boolean; message: string }> {
  return fetchApi<{ success: boolean; message: string }>(`/constraints/${id}`, {
    method: 'DELETE',
  });
}

/**
 * POST /api/constraints/validate
 * Validiert einen Code gegen Constraints
 */
export async function validateCodeAgainstConstraints(
  code: string,
  level: number,
  previousSelections: Record<number, string>
): Promise<ConstraintValidationResult> {
  return fetchApi<ConstraintValidationResult>('/constraints/validate', {
    method: 'POST',
    body: JSON.stringify({
      code,
      level,
      previous_selections: previousSelections,
    }),
  });
}
