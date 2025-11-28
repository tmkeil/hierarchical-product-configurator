# Product Variant Tree - Database Schema Project

## What This Is

A hierarchical product configurator where users select options at each level to build a final product code.

**Current:** React frontend + JSON file  
**Goal:** SQLite database (Azure SQL compatible) to handle 2M+ records

**Example product code:**
```
XPRO5 ENG7-TR4X-89-WRAP5-55-ZZ99
  │     │    │    │   (each segment = one selection level)
  └─ Product Family
```

---

## JSON Structure


### Key Attributes

```javascript
{
  "code": "ENG7",              // Product code segment
  "name": "Engine Type",       // Category/segment name (e.g., "Color", "Connection", "Cylinders")
  "position": 7,               // Character position in final typecode
  "pattern": 4,                // String length (containers only)
  "label": "V8 Turbo",         // Specific description of this option
  "group": "Performance",      // Cross-branch grouping (same group can span different branches)
  "full_typecode": "A ENG7-X", // Complete code (leaves/intermediates only)
  "is_intermediate_code": true,// Has variants but is also a product
  "children": [...],           // Child nodes
  "date_info": {               // Optional: Product lifecycle data
    "typecode_count": 5,       // Number of products using this code
    "creation_date": {
      "earliest": "08.03.1997",
      "latest": "01.12.2024"
    },
    "modification_date": {
      "earliest": "08.03.1997",
      "latest": "15.10.2025"
    }
  }
}
```

**Important distinction:**
- `name` = Segment category (what type of choice this is: "Color", "Connection Type", "Cylinder Count")
- `label` = Specific option description (what this particular option is: "Red", "M12 Connector", "4 Cylinders")
- `group` = Logical grouping across branches (e.g., "Performance", "Standard", "Economy" - can span different parent branches within same product family)

**Node Types:**
- **Product Family** - Root product lines, has `code`
- **Pattern Container** - Groups codes by length, has `pattern`, NO `code`
- **Code Node** - Selectable option with `code`, `label`, `position`
- **Leaf Node** - Final product with `full_typecode`, no children
- **Intermediate Node** - Product that also has variants (`full_typecode` + children)

### Example Structure

```
XPRO5 ENG7-TR4X-89-WRAP5-55-ZZ99
  │     │    │    │   │     │   └─ Level 6 (position 29 in final code)
  │     │    │    │   │     └───── Level 5 (position 26)
  │     │    │    │   └─────────── Level 4 (position 20)
  │     │    │    └──────────────── Level 3 (position 17)
  │     │    └───────────────────── Level 2 (position 12)
  │     └────────────────────────── Level 1 (position 7)
  └──────────────────────────────── Product Family (position 1)
```

**Level numbering:** 
- Level 1 = first choice after product family
- Level 2 = second choice, etc.
- `level_number` in queries = which step in the configuration (1, 2, 3, 4...)

---

### How Levels Work

Each level shows ALL nodes at that depth in the tree, regardless of which branch they're in. The frontend then filters for compatibility based on previous selections.

```
Example Tree:

Product Family: CAR
├─ Level 1: ENGINE-A (pos 5)
│  ├─ Level 2: TRANS-X (pos 13)
│  │  ├─ Level 3: INTERIOR-RED (pos 22)
│  │  └─ Level 3: INTERIOR-BLUE (pos 22)
│  └─ Level 2: TRANS-Y (pos 13)
│     └─ Level 3: INTERIOR-GREEN (pos 22)
└─ Level 1: ENGINE-B (pos 5)
   └─ Level 2: TRANS-Z (pos 13)
      ├─ Level 3: INTERIOR-BLACK (pos 22)
      └─ Level 3: INTERIOR-WHITE (pos 22)

Level 1 dropdown shows:
  ✓ ENGINE-A
  ✓ ENGINE-B

User selects: ENGINE-A

Level 2 dropdown shows:
  ✓ TRANS-X  ← compatible (child of ENGINE-A)
  ✓ TRANS-Y  ← compatible (child of ENGINE-A)
  ✗ TRANS-Z  ← NOT compatible (belongs to ENGINE-B branch)

User selects: TRANS-X

Level 3 dropdown shows:
  ✓ INTERIOR-RED    ← compatible (child of TRANS-X)
  ✓ INTERIOR-BLUE   ← compatible (child of TRANS-X)
  ✗ INTERIOR-GREEN  ← NOT compatible (belongs to TRANS-Y branch)
  ✗ INTERIOR-BLACK  ← NOT compatible (belongs to ENGINE-B branch)
  ✗ INTERIOR-WHITE  ← NOT compatible (belongs to ENGINE-B branch)
```

**Query 3 should return:** ALL options at that level (both ✓ and ✗), with a flag/attribute indicating which are compatible with previous selections. The frontend can then display them grouped (compatible first, incompatible grayed out).

---

### Pattern Containers

Pattern containers group codes by their length. They are organizational nodes with NO `code` attribute.

```
Example with Pattern Containers:

Product Family: PUMP
└─ Level 1: MOTOR-A (pos 6)
   ├─ [Pattern Container: pattern=4, pos=14]  ← Groups all 4-character codes
   │  ├─ Level 2: SEAL (code, pos 14)
   │  └─ Level 2: BOLT (code, pos 14)
   └─ [Pattern Container: pattern=6, pos=14]  ← Groups all 6-character codes
      ├─ Level 2: WASHER (code, pos 14)
      └─ Level 2: GASKET (code, pos 14)

Final product codes:
- PUMP MOTOR-A-SEAL    (4-char option)
- PUMP MOTOR-A-BOLT    (4-char option)
- PUMP MOTOR-A-WASHER  (6-char option)
- PUMP MOTOR-A-GASKET  (6-char option)
```

**Important for queries:**
- Pattern containers are NOT selectable (they have no `code`)
- When getting children (Query 2), you can skip pattern containers and return only the actual code nodes
- Pattern containers help organize the tree but are invisible to the user

---

### Intermediate Codes

Some nodes are BOTH a complete product AND have further variants (children).

```
Example with Intermediate Codes:

Product Family: SENSOR
└─ Level 1: BASE-A (pos 8)
   ├─ Level 2: CABLE-SHORT (pos 16)  ← is_intermediate_code: true
   │  │                                 full_typecode: "SENSOR BASE-A-CABLE-SHORT"
   │  │                                 ↑ This is a COMPLETE product you can order
   │  ├─ Level 3: CONNECTOR-M12 (pos 25)
   │  │  └─ full_typecode: "SENSOR BASE-A-CABLE-SHORT-CONNECTOR-M12"
   │  └─ Level 3: CONNECTOR-M8 (pos 25)
   │     └─ full_typecode: "SENSOR BASE-A-CABLE-SHORT-CONNECTOR-M8"
   └─ Level 2: CABLE-LONG (pos 16)   ← is_intermediate_code: false
      └─ full_typecode: "SENSOR BASE-A-CABLE-LONG"
         (no children, so NOT intermediate)

In this example:
- "SENSOR BASE-A-CABLE-SHORT" is a valid product (can be ordered as-is)
- BUT it also has children (you can add connectors to customize it further)
- "SENSOR BASE-A-CABLE-LONG" is also a valid product but has NO further options
```

**Important for queries:**
- Intermediate codes have BOTH `full_typecode` AND `children`
- Regular leaf nodes have `full_typecode` but NO children
- Regular variant steps have children but NO `full_typecode`

---

## 🔍 Required Queries

The database must support these 8 queries efficiently (optimized for 2M+ records):

**Query 1: Get all product families**
```
Input: None
Output: All Level 1 nodes that have a `code` attribute
Example: [{code: "XPRO5", label: "...", position: 1, ...}, ...]
```

**Query 2: Get children of a specific node**
```
Input: parent_code (e.g., "XPRO5")
Output: Array of DIRECT child node objects (one level down only, NOT grandchildren)

"Children" = immediate descendants only (not recursive)
Example: If XPRO5 has children [ENG7, ENG8], and ENG7 has children [TR4X, TR5Y],
         Query 2 for "XPRO5" returns only [ENG7, ENG8], NOT [ENG7, ENG8, TR4X, TR5Y]

Return all attributes for each child: code, name, label, position, group, 
full_typecode, is_intermediate_code, pattern (if applicable)

Two variants needed:
  a) Get ALL direct children (including pattern containers that have no `code`)
  b) Get only direct CODE nodes (skip pattern containers - nodes with `pattern` but no `code`)

Use case: When user selects an option, show next level choices.
```

**Query 3: Get maximum depth from a node**
```
Input: parent_code (e.g., "ENG7")
Output: Integer - maximum number of levels below this node

Example: If ENG7 → TR4X → RED → FINISH (3 levels deep)
         and ENG7 → TR5Y → BLUE (2 levels deep)
         Return: 3 (the deepest path)

Use case: Frontend dynamically shows/hides dropdown fields based on depth.

IMPORTANT - This query is called on EVERY selection change:

Scenario 1: User selects product family "XPRO5" (has 7 levels total)
  - Query 3 input: "XPRO5"
  - Output: 7
  - Frontend: Show 7 dropdown fields

Scenario 2: User then selects level 1 option "ENG7" (has only 2 more levels)
  - Query 3 input: "ENG7"
  - Output: 2
  - Frontend: Hide dropdowns 4-7 (only show dropdowns 1, 2, 3)

Scenario 3: User changes level 1 to "ENG8" (has 15 more levels)
  - Query 3 input: "ENG8"
  - Output: 15
  - Frontend: Show dropdowns 1-16 (1 + 15 more levels)

Scenario 4: User directly selects level 7 (skipping 1-6)
  - Query 3 input: level 7's parent_code
  - Output: X (depth below level 7)
  - Frontend: Show dropdowns 8 to 7+X
  - Frontend also calls Query 4 for levels 1-6 to update compatibility

This query must be FAST (called on every selection change).
```

**Query 4: Get available options for a level** ⚠️ MOST COMPLEX QUERY

---

### COMPLETE EXAMPLE: User jumps to level 7 directly

**Scenario:** User selects product family "XPRO5", then DIRECTLY selects level 7 option "WRAP5" (skipping levels 1-6).

**Tree structure:**
```
XPRO5 (product family)
├─ ENG7 (level 1)
│  ├─ TR4X (level 2)
│  │  └─ RED (level 3)
│  │     └─ ... → WRAP5 (level 7) ✓ Valid path exists!
│  └─ TR5Y (level 2)
│     └─ BLUE (level 3)
│        └─ ... → ZZAA (level 7) ✗ Different path
└─ ENG8 (level 1)
   └─ TRBB (level 2)
      └─ ... → WRAP5 (level 7) ✓ Another valid path to WRAP5!
```

**Query 4 is called to fill level 2 dropdown:**

**Input:**
```javascript
{
  product_family_code: "XPRO5",
  level_number: 2,
  previous_selections: [{level: 7, code: "WRAP5"}]
}
```

**Expected Output:**
```javascript
[
  {
    code: "TR4X",
    label: "Transmission Type A",
    is_compatible: true,     // ✓ Path exists: XPRO5 → ENG7 → TR4X → ... → WRAP5
    parent_code: "ENG7"
  },
  {
    code: "TR5Y", 
    label: "Transmission Type B",
    is_compatible: false,    // ✗ No path: TR5Y leads to ZZAA, not WRAP5
    parent_code: "ENG7"
  },
  {
    code: "TRBB",
    label: "Transmission Type C", 
    is_compatible: true,     // ✓ Path exists: XPRO5 → ENG8 → TRBB → ... → WRAP5
    parent_code: "ENG8"
  }
]
```

**What the database must check for EACH level 2 option:**
1. **Forward check:** Can we reach this option from XPRO5? (Yes, all level 2 options are reachable)
2. **Backward check:** Can we reach WRAP5 (level 7) from this option? 
   - TR4X → ... → WRAP5? **YES** ✓
   - TR5Y → ... → WRAP5? **NO** ✗ (TR5Y leads to ZZAA instead)
   - TRBB → ... → WRAP5? **YES** ✓
3. **Result:** is_compatible = forward_check AND backward_check

---

### 📝 Query Specification

**Input:**
```javascript
{
  product_family_code: string,    // e.g., "XPRO5"
  level_number: integer,          // Which dropdown to fill (1, 2, 3, ...)
  previous_selections: [          // Array of ALL user selections so far
    {level: integer, code: string},
    {level: integer, code: string},
    ...
  ]
}
```

**Output:**
```javascript
[
  {
    code: string,                  // Node's code
    label: string,                 // Display text
    name: string,                  // Category name
    position: integer,             // Position in final typecode
    group: string,                 // Grouping category
    full_typecode: string | null,  // Complete product code (if leaf/intermediate)
    is_intermediate_code: boolean, // Has both typecode and children?
    is_compatible: boolean,        // ⚠️ DATABASE MUST CALCULATE THIS
    parent_code: string            // Immediate parent's code
  },
  ...
]
```

---

### 🔍 COMPATIBILITY ALGORITHM (is_compatible calculation)

**The core challenge:** Determine if an option at level X is compatible with ALL previous selections (both before AND after level X).

**Rules:**

**1. SPECIAL CASE - First level with no selections:**
   ```
   If level_number = 1 AND previous_selections = []
   → ALL options have is_compatible = true
   ```

**2. FORWARD COMPATIBILITY:**
   Build path from product_family through all previous selections (sorted by level) to this option.
   ```
   Example: previous_selections = [{level: 1, code: "ENG7"}]
            Testing level 2 option "TR4X"
            
   Check: Does path exist? XPRO5 → ENG7 → TR4X
   - YES → forward compatible ✓
   - NO  → forward incompatible ✗
   ```

**3. BACKWARD COMPATIBILITY (for gaps):**
   If previous_selections contains levels AFTER level_number, check if those are reachable.
   ```
   Example: previous_selections = [{level: 7, code: "WRAP5"}]
            Testing level 2 option "TR4X"
            
   Check: Does path exist? TR4X → ... → WRAP5
   - YES → backward compatible ✓
   - NO  → backward incompatible ✗
   ```

**4. GAP HANDLING:**
   Selections can have gaps (e.g., levels 1, 3, 7 selected, but not 2, 4, 5, 6).
   Must find ANY valid path connecting all selections in order.
   ```
   Example: previous_selections = [{level: 1, code: "ENG7"}, {level: 7, code: "WRAP5"}]
            Testing level 3 option "RED"
            
   Check: Does path exist? XPRO5 → ENG7 → ? → RED → ? → WRAP5
   - Must skip intermediate levels (2, 4, 5, 6) when traversing
   - Pattern containers don't count as levels (skip them)
   ```

**5. PATTERN CONTAINER HANDLING:**
   Nodes with `pattern` but no `code` are organizational only.
   ```
   Tree:
     ENG7 (level 1)
     └─ [Pattern: 4] ← NOT a level, skip this
        ├─ TR4X (level 2) ← This is level 2, not level 3
        └─ TR5Y (level 2)
   ```

**6. FINAL CALCULATION:**
   ```
   is_compatible = forward_compatible AND backward_compatible
   ```

---

### 💡 IMPLEMENTATION ALGORITHM (Step-by-Step)

**Step 1:** Collect all nodes at `level_number`
- Traverse tree from `product_family_code`
- Count only nodes with `code` attribute as levels
- Skip pattern containers (nodes with `pattern` but no `code`)

**Step 2:** For each collected node, calculate `is_compatible`:

**a) If level_number = 1 AND previous_selections is empty:**
   - `is_compatible = true` (done)

**b) Otherwise, do FORWARD CHECK:**
   - Sort previous_selections by level (ascending)
   - Filter selections where level < level_number
   - Check if path exists: product_family → selection[0] → selection[1] → ... → this_node
   - Use breadth-first search (BFS) to handle gaps between levels
   - Result: `forward_compatible = true/false`

**c) Do BACKWARD CHECK (if needed):**
   - Filter selections where level > level_number
   - For each later selection:
     * Check if path exists: this_node → ... → later_selection
     * Use BFS to traverse descendants
   - If ALL later selections are reachable: `backward_compatible = true`
   - Otherwise: `backward_compatible = false`

**d) Calculate final result:**
   - `is_compatible = forward_compatible AND backward_compatible`

**Step 3:** Find `parent_code` for each node:
- Traverse from product_family to this node
- Return code of immediate parent (skip pattern containers)

**Step 4:** Return all nodes with their attributes

---

### 📚 IMPLEMENTATION NOTES

**Two implementation approaches:**

**Option A: Closure Table (Recommended for production)**
- Pre-compute all ancestor-descendant relationships in a separate `node_paths` table
- Storage: ~1-2 GB for 2M variants (28M relationships)
- Performance: Instant lookups (milliseconds) via indexed table
- Complexity: Requires maintaining closure table when tree changes

**Option B: Recursive CTEs (Simpler alternative)**
- Use `WITH RECURSIVE` queries in SQLite/SQL Server
- Storage: No additional tables needed
- Performance: Slower for deep trees, but fine for <100k records
- Complexity: Easier to implement and maintain

**Recommendation:** Start with Option B (recursive CTEs). Migrate to Option A (closure table) if Query 4 performance becomes an issue during testing.

**Performance note:** This query is called on every dropdown interaction, so optimization is important.

---

**Query 5: Find node(s) by code**

---

**Query 5: Find node(s) by code**
```
Input: code (e.g., "ENG7")
Output: Array of ALL nodes with this code (can be multiple if code appears in different branches)

Each result includes:
  - All node attributes
  - Full path from root: e.g., ["XPRO5", "ENG7"] or ["YPRO2", "ENG7"]
  
Note: Same code can exist in multiple branches. This query finds all occurrences.

Use case: Search/debugging, or checking if a code exists at all.
For frontend navigation, use Query 4 or Query 9 instead (they know the context/path).
```

**Query 6: Find product by full_typecode**
```
Input: full_typecode (e.g., "XPRO5 ENG7-TR4X")
Output: The final node representing this product
```

**Query 7: Check node type**
```
Input: node_id or code
Output: Is it a leaf? (no children)
        Is it intermediate? (has full_typecode AND children)
        Is it just a variant step? (no full_typecode)
```

**Query 8: Get full path from root to node**
```
Input: node_id or full_typecode
Output: Array of all parent nodes from root to this node
Example: [XPRO5, ENG7, TR4X] for "XPRO5 ENG7-TR4X"
```
```
Input: node_id or full_typecode
Output: Array of all parent nodes from root to this node
Example: [XPRO5, ENG7, TR4X] for "XPRO5 ENG7-TR4X"
```

---

## Frontend Query Orchestration (for context)

**Important:** The database only implements the 8 queries above. The frontend orchestrates them
to handle complex user interactions.

**Example: User jumps directly to level 7 (skipping levels 1-6)**

When user selects level 7 option "WRAP5", the frontend will:

1. Call Query 4 multiple times to update ALL dropdowns:
   ```
   Query 4 (level=1, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 1
   Query 4 (level=2, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 2
   Query 4 (level=3, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 3
   Query 4 (level=4, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 4
   Query 4 (level=5, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 5
   Query 4 (level=6, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 6
   Query 4 (level=8, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 8
   Query 4 (level=9, selections=[{level: 7, code: "WRAP5"}])  → Update dropdown 9
   ... etc
   ```
   Each query returns options with `is_compatible` flag. Frontend shows:
   - Compatible options as enabled (clickable)
   - Incompatible options as grayed out (visible but disabled)

2. Call Query 3 to show/hide dropdowns:
   ```
   Query 3 (parent_code="WRAP5")  → Returns max depth below WRAP5
   ```
   If depth = 3, frontend shows dropdowns 8, 9, 10 (levels after 7)
   If depth = 0, frontend hides all dropdowns after level 7

3. Frontend handles automatic reset of incompatible selections:
   - If user previously selected level 2 = "TR4X"
   - And "TR4X" is now incompatible with level 7 = "WRAP5"
   - Frontend automatically resets level 2 selection
   - This logic is in the frontend, NOT in the database