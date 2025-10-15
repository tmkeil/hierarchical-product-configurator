-- =====================================================
-- Product Variant Tree - SQL Queries
-- =====================================================
-- This file contains all 8 queries from PROJECT_DOCUMENTATION.md
-- translated to SQL with performance optimizations.
--
-- Usage:
--   sqlite3 products.db < queries.sql
--   OR run individual queries in your application
--
-- Note: Replace :parameter placeholders with actual values
-- =====================================================

-- =====================================================
-- QUERY 1: Get All Product Families
-- =====================================================
-- Returns root nodes (product families) that user can choose from initially.
-- Pattern containers are automatically excluded since they don't have a code.
--
-- Example result:
-- code | label              | label_en           | position | group_name
-- -----|--------------------|--------------------|----------|------------
-- XPRO5| Extended Platform  | Extended Platform  | 0        | Base
-- ENG7 | Engine Config      | Engine Config      | 1        | Base
-- TR4X | Transmission       | Transmission       | 2        | Base
--
-- Performance: O(1) - simple index scan on parent_id
-- =====================================================

SELECT 
    code,
    label,
    label_en,
    position,
    group_name
FROM nodes
WHERE parent_id IS NULL 
  AND code IS NOT NULL  -- Ensures only real product families, not pattern containers
ORDER BY position, code;


-- =====================================================
-- QUERY 2: Get Children of Node
-- =====================================================
-- Returns direct children of a specific node (one level down only).
-- Skips pattern containers automatically via code IS NOT NULL filter.
--
-- Parameters:
--   :parent_code - The code of the parent node (e.g., 'XPRO5')
--
-- Example: Get children of XPRO5
-- code  | label           | name            | position | full_typecode | is_intermediate
-- ------|-----------------|-----------------|----------|---------------|----------------
-- ENG7  | Engine Config   | engine_config   | 0        | NULL          | 0
-- TR4X  | Transmission    | transmission    | 1        | NULL          | 0
--
-- Performance: O(log n) - uses idx_nodes_parent index
-- =====================================================

SELECT 
    code,
    label,
    name,
    position,
    full_typecode,
    is_intermediate_code
FROM nodes
WHERE parent_id = (
    SELECT id FROM nodes WHERE code = :parent_code LIMIT 1
)
AND code IS NOT NULL  -- Skip pattern containers
ORDER BY position, code;


-- =====================================================
-- QUERY 3: Get Maximum Depth from Node
-- =====================================================
-- Calculates maximum depth reachable from a given node.
-- Uses recursive CTE to traverse the tree downward.
--
-- Parameters:
--   :start_code - The code of the starting node (e.g., 'XPRO5')
--
-- Example: Max depth from XPRO5 = 4 means user can make 4 more selections
--
-- Performance: 
--   - Recursive CTE: O(n) for subtree traversal
--   - With closure table: O(1) using MAX(depth) on pre-computed paths
--
-- Note: This uses the recursive approach. For better performance with
-- large datasets, use the closure table version below.
-- =====================================================

-- Option A: Recursive CTE (works without closure table)
WITH RECURSIVE depth_calc AS (
    -- Base case: Start at the specified node with depth 0
    SELECT 
        id, 
        0 as depth
    FROM nodes
    WHERE code = :start_code
    
    UNION ALL
    
    -- Recursive case: Find all children and increment depth
    SELECT 
        n.id, 
        d.depth + 1 as depth
    FROM nodes n
    JOIN depth_calc d ON n.parent_id = d.id
)
SELECT MAX(depth) as max_depth 
FROM depth_calc;

-- Option B: Using Closure Table (MUCH faster for large datasets)
-- Requires --closure flag during import
-- Performance: O(1) - single index lookup
/*
SELECT MAX(depth) as max_depth
FROM node_paths
WHERE ancestor_id = (
    SELECT id FROM nodes WHERE code = :start_code LIMIT 1
);
*/


-- =====================================================
-- QUERY 4: Get Available Options for Level (COMPLEX)
-- =====================================================
-- This is the MOST COMPLEX query - it returns all valid options for
-- a specific level, considering the user's current path and validating
-- bidirectional compatibility.
--
-- Algorithm (translated from variantenbaum.ts):
-- 1. Get all nodes at target level
-- 2. For each node, check if path exists from last selection to this node (forward)
-- 3. For each node, check if path exists from this node to all previous selections (backward)
-- 4. Mark node as compatible only if BOTH checks pass
--
-- Parameters:
--   :target_level      - The level user is selecting at (e.g., 2)
--   :current_path_json - JSON array of current selections, e.g. '[{"code":"XPRO5","level":0},{"code":"ENG7","level":1}]'
--
-- Example Scenario:
--   User selected: XPRO5 (level 0), ENG7 (level 1)
--   Target level: 2
--   
-- Result:
-- code  | label        | position | group_name | level | is_compatible
-- ------|--------------|----------|------------|-------|---------------
-- TR4X  | Transmission | 0        | Drivetrain | 2     | 1
-- WRAP5 | Wrapper      | 1        | Optional   | 2     | 0  (incompatible)
--
-- Performance Notes:
-- - WITHOUT closure table: ~1-3 seconds for 2M nodes (many recursive CTEs)
-- - WITH closure table: ~10-100ms for 2M nodes (pre-computed paths)
--
-- =====================================================

-- IMPORTANT: SQLite does NOT have native JSON array parsing functions
-- like PostgreSQL's json_array_elements(). There are TWO approaches:

-- =====================================================
-- APPROACH A: Multiple Individual Parameters (Recommended for SQLite)
-- =====================================================
-- Instead of JSON, pass each selection as separate parameters:
--   :selection_0_code, :selection_0_level
--   :selection_1_code, :selection_1_level
--   etc.
--
-- This works well for up to ~10 levels (typical product trees)

-- Example for 2 previous selections (XPRO5 at level 0, ENG7 at level 1):
WITH 
-- Parse current path from parameters
current_selections AS (
    SELECT :selection_0_code as code, :selection_0_level as level
    UNION ALL
    SELECT :selection_1_code as code, :selection_1_level as level
    -- Add more UNION ALL for deeper paths
),

-- Get all candidate nodes at target level
candidates AS (
    SELECT 
        id,
        code,
        label,
        position,
        group_name,
        level
    FROM nodes
    WHERE level = :target_level
      AND code IS NOT NULL  -- Skip pattern containers
),

-- Get IDs of current selections for path checking
selection_ids AS (
    SELECT n.id, cs.level
    FROM current_selections cs
    JOIN nodes n ON n.code = cs.code AND n.level = cs.level
),

-- Find last selection (highest level in current path)
last_selection AS (
    SELECT id, level
    FROM selection_ids
    ORDER BY level DESC
    LIMIT 1
),

-- FORWARD CHECK: Can we reach candidate from last selection?
-- (Uses closure table if available, otherwise recursive CTE)
forward_compatible AS (
    SELECT DISTINCT np.descendant_id as candidate_id
    FROM node_paths np
    JOIN last_selection ls ON np.ancestor_id = ls.id
    JOIN candidates c ON np.descendant_id = c.id
    -- If no closure table, comment above and use recursive CTE:
    /*
    WITH RECURSIVE forward_path AS (
        SELECT id FROM last_selection
        UNION ALL
        SELECT n.id FROM nodes n JOIN forward_path fp ON n.parent_id = fp.id
    )
    SELECT DISTINCT fp.id as candidate_id
    FROM forward_path fp
    JOIN candidates c ON fp.id = c.id
    */
),

-- BACKWARD CHECK: Can candidate reach ALL previous selections?
-- This is the critical "no gaps" check
backward_compatible AS (
    SELECT c.id as candidate_id
    FROM candidates c
    WHERE NOT EXISTS (
        -- Check if there's ANY previous selection NOT reachable from candidate
        SELECT 1
        FROM selection_ids si
        WHERE si.level < :target_level  -- Only check selections BEFORE target level
          AND NOT EXISTS (
              -- Try to find path from candidate to this selection
              SELECT 1
              FROM node_paths np
              WHERE np.ancestor_id = c.id
                AND np.descendant_id = si.id
              -- If no closure table, use recursive CTE:
              /*
              WITH RECURSIVE backward_path AS (
                  SELECT id FROM nodes WHERE id = c.id
                  UNION ALL
                  SELECT n.id FROM nodes n JOIN backward_path bp ON n.parent_id = bp.id
              )
              SELECT 1 FROM backward_path WHERE id = si.id
              */
          )
    )
)

-- Final result: Combine forward and backward compatibility
SELECT 
    c.code,
    c.label,
    c.position,
    c.group_name,
    c.level,
    CASE 
        WHEN fc.candidate_id IS NOT NULL AND bc.candidate_id IS NOT NULL 
        THEN 1 
        ELSE 0 
    END as is_compatible
FROM candidates c
LEFT JOIN forward_compatible fc ON c.id = fc.candidate_id
LEFT JOIN backward_compatible bc ON c.id = bc.candidate_id
ORDER BY c.position, c.code;


-- =====================================================
-- APPROACH B: Using JSON Extension (Requires json1 extension)
-- =====================================================
-- SQLite has json1 extension (enabled by default since 3.38.0)
-- This allows parsing JSON arrays directly:

/*
WITH 
-- Parse JSON array into rows
current_selections AS (
    SELECT 
        json_extract(value, '$.code') as code,
        json_extract(value, '$.level') as level
    FROM json_each(:current_path_json)
),
-- ... rest same as Approach A ...
*/


-- =====================================================
-- SIMPLIFIED VERSION: No Previous Selections
-- =====================================================
-- When user hasn't made any selections yet (initial state),
-- ALL options at level 0 are compatible.

SELECT 
    code,
    label,
    position,
    group_name,
    level,
    1 as is_compatible  -- All compatible when no constraints
FROM nodes
WHERE level = :target_level
  AND code IS NOT NULL
ORDER BY position, code;


-- =====================================================
-- QUERY 5: Find Node by Code
-- =====================================================
-- Finds all nodes matching a specific code.
-- Can return MULTIPLE results because same code may appear
-- in different branches (e.g., "ENG7" might exist under multiple parents).
--
-- Parameters:
--   :search_code - The code to search for (e.g., 'ENG7')
--
-- Example Result:
-- id  | code | label         | level | full_typecode | parent_code
-- ----|------|---------------|-------|---------------|-------------
-- 12  | ENG7 | Engine Config | 1     | NULL          | XPRO5
-- 34  | ENG7 | Engine Config | 1     | NULL          | TR4X
--
-- Performance: O(log n) - uses idx_nodes_code index
-- =====================================================

SELECT 
    n.id,
    n.code,
    n.label,
    n.level,
    n.full_typecode,
    p.code as parent_code,
    p.label as parent_label
FROM nodes n
LEFT JOIN nodes p ON n.parent_id = p.id
WHERE n.code = :search_code
ORDER BY n.level, n.id;


-- =====================================================
-- QUERY 6: Find Product by Full Typecode
-- =====================================================
-- Finds a SINGLE final product by its complete typecode string.
-- Returns exactly ONE result (or none if typecode doesn't exist).
--
-- Parameters:
--   :full_typecode - The complete typecode (e.g., 'XPRO5 ENG7 TR4X')
--
-- Example Result:
-- id  | code | label        | full_typecode       | is_intermediate
-- ----|------|--------------|---------------------|----------------
-- 89  | TR4X | Transmission | XPRO5 ENG7 TR4X    | 0
--
-- Performance: O(log n) - uses idx_nodes_typecode index
-- =====================================================

SELECT 
    id,
    code,
    label,
    full_typecode,
    is_intermediate_code
FROM nodes
WHERE full_typecode = :full_typecode
LIMIT 1;


-- =====================================================
-- QUERY 7: Check Node Type
-- =====================================================
-- Determines the type of a node based on its properties and children.
--
-- Node Types:
--   - 'leaf': Final product (has full_typecode, is_intermediate_code = 0, no children)
--   - 'intermediate': Intermediate product (has full_typecode, is_intermediate_code = 1)
--   - 'variant_step': Configuration step (no full_typecode, has code, has children)
--   - 'pattern_container': UI grouping (has pattern, no code)
--
-- Parameters:
--   :check_code - The code to check (e.g., 'ENG7')
--
-- Example Result:
-- code | label         | node_type     | has_children
-- -----|---------------|---------------|-------------
-- ENG7 | Engine Config | variant_step  | 1
--
-- Performance: O(log n) for node lookup + O(1) for type determination
-- =====================================================

WITH node_info AS (
    SELECT 
        code,
        label,
        full_typecode,
        is_intermediate_code,
        pattern,
        (SELECT COUNT(*) FROM nodes WHERE parent_id = n.id) as child_count
    FROM nodes n
    WHERE code = :check_code
    LIMIT 1
)
SELECT 
    code,
    label,
    CASE
        -- Pattern container: has pattern, no code
        WHEN pattern IS NOT NULL THEN 'pattern_container'
        
        -- Leaf product: has full typecode and is NOT intermediate
        WHEN full_typecode IS NOT NULL AND is_intermediate_code = 0 THEN 'leaf'
        
        -- Intermediate product: has full typecode and IS intermediate
        WHEN full_typecode IS NOT NULL AND is_intermediate_code = 1 THEN 'intermediate'
        
        -- Variant step: has code but no full typecode (configuration step)
        WHEN full_typecode IS NULL AND code IS NOT NULL THEN 'variant_step'
        
        ELSE 'unknown'
    END as node_type,
    child_count > 0 as has_children
FROM node_info;


-- =====================================================
-- QUERY 8: Get Full Path from Root to Node
-- =====================================================
-- Returns the complete path from root (product family) to a specific node.
-- Useful for breadcrumbs, displaying selection history, or debugging.
--
-- Parameters:
--   :target_code       - The code of the target node (e.g., 'WRAP5')
--   :target_full_typecode (optional) - Full typecode for disambiguation
--
-- Example Result:
-- code  | label              | level | depth_from_target
-- ------|-----------------------|-------|------------------
-- XPRO5 | Extended Platform     | 0     | 3
-- ENG7  | Engine Config         | 1     | 2
-- TR4X  | Transmission          | 2     | 1
-- WRAP5 | Wrapper               | 3     | 0
--
-- Performance:
--   - Recursive CTE: O(h) where h = height from target to root (~4-5 typically)
--   - With closure table: O(1) - single query
-- =====================================================

-- Option A: Recursive CTE (works without closure table)
WITH RECURSIVE path_to_root AS (
    -- Base case: Start at target node
    SELECT 
        id,
        parent_id,
        code,
        label,
        level,
        0 as depth_from_target
    FROM nodes
    WHERE code = :target_code
      -- If multiple nodes with same code exist, disambiguate with typecode:
      AND (:target_full_typecode IS NULL OR full_typecode = :target_full_typecode)
    
    UNION ALL
    
    -- Recursive case: Walk up to parent
    SELECT 
        n.id,
        n.parent_id,
        n.code,
        n.label,
        n.level,
        p.depth_from_target + 1
    FROM nodes n
    JOIN path_to_root p ON p.parent_id = n.id
)
SELECT 
    code,
    label,
    level,
    depth_from_target
FROM path_to_root
WHERE code IS NOT NULL  -- Skip any pattern containers in path
ORDER BY depth_from_target DESC;  -- Root first, target last


-- Option B: Using Closure Table (faster for large datasets)
/*
WITH target_node AS (
    SELECT id FROM nodes 
    WHERE code = :target_code 
      AND (:target_full_typecode IS NULL OR full_typecode = :target_full_typecode)
    LIMIT 1
)
SELECT 
    n.code,
    n.label,
    n.level,
    np.depth
FROM node_paths np
JOIN nodes n ON np.ancestor_id = n.id
JOIN target_node t ON np.descendant_id = t.id
WHERE n.code IS NOT NULL  -- Skip pattern containers
ORDER BY np.depth DESC;  -- Root first
*/


-- =====================================================
-- BONUS: Helper Queries
-- =====================================================

-- Get Statistics
SELECT 
    COUNT(*) as total_nodes,
    COUNT(CASE WHEN parent_id IS NULL THEN 1 END) as product_families,
    COUNT(CASE WHEN pattern IS NOT NULL THEN 1 END) as pattern_containers,
    COUNT(CASE WHEN code IS NOT NULL THEN 1 END) as code_nodes,
    COUNT(CASE WHEN full_typecode IS NOT NULL AND is_intermediate_code = 0 THEN 1 END) as leaf_products,
    COUNT(CASE WHEN full_typecode IS NOT NULL AND is_intermediate_code = 1 THEN 1 END) as intermediate_products,
    MIN(level) as min_level,
    MAX(level) as max_level
FROM nodes;

-- Get Tree Structure Summary
SELECT 
    level,
    COUNT(*) as node_count,
    COUNT(CASE WHEN pattern IS NOT NULL THEN 1 END) as patterns,
    COUNT(CASE WHEN code IS NOT NULL THEN 1 END) as codes,
    COUNT(CASE WHEN full_typecode IS NOT NULL THEN 1 END) as products
FROM nodes
GROUP BY level
ORDER BY level;

-- Find Orphaned Nodes (should be empty if tree is valid)
SELECT 
    id,
    code,
    parent_id,
    'Orphaned node - parent does not exist' as issue
FROM nodes
WHERE parent_id IS NOT NULL
  AND parent_id NOT IN (SELECT id FROM nodes);

-- Check Closure Table Integrity (if using closure table)
SELECT 
    COUNT(*) as total_paths,
    COUNT(CASE WHEN depth = 0 THEN 1 END) as self_references,
    MAX(depth) as max_depth
FROM node_paths;
