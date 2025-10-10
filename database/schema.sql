-- ============================================================================
-- PRODUCT VARIANT TREE - DATABASE SCHEMA
-- ============================================================================
-- SQLite Schema (Azure SQL Server compatible)
-- Created for hierarchical product configurator with 2M+ variants
-- ============================================================================

-- ============================================================================
-- TABLE: nodes
-- ============================================================================
-- Stores all nodes in the variant tree (Product Families, Pattern Containers,
-- Code Nodes, Leaf Nodes, Intermediate Nodes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS nodes (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Hierarchy
    parent_id INTEGER,
    level INTEGER NOT NULL,  -- Depth from root (0 = Product Family)
    
    -- Node identification
    code TEXT,  -- NULL for Pattern Containers!
    name TEXT NOT NULL,  -- Category name (e.g., "Engine Type", "Color")
    
    -- Display labels
    label TEXT NOT NULL,  -- German description (e.g., "V8 Turbo", "Rot")
    label_en TEXT,  -- English description (optional)
    
    -- Position in final typecode
    position INTEGER NOT NULL,  -- Character position in full typecode
    
    -- Pattern Container attributes
    pattern INTEGER,  -- String length (only for Pattern Containers)
    
    -- Product identification
    full_typecode TEXT,  -- Complete product code (only for Leaves/Intermediates)
    is_intermediate_code BOOLEAN DEFAULT 0,  -- Has both typecode AND children?
    
    -- Grouping
    group_name TEXT,  -- Cross-branch grouping (e.g., "Performance", "Standard")
    
    -- Pictures (JSON array with image metadata)
    pictures TEXT DEFAULT '[]',  -- JSON: [{"url": "...", "description": "...", "uploaded_at": "..."}]
    
    -- Links (JSON array with external links)
    links TEXT DEFAULT '[]',  -- JSON: [{"url": "...", "title": "...", "description": "...", "added_at": "..."}]
    
    -- Constraints
    FOREIGN KEY (parent_id) REFERENCES nodes(id) ON DELETE CASCADE,
    
    -- Ensure either code OR pattern is set (not both)
    CHECK (
        (code IS NOT NULL AND pattern IS NULL) OR
        (code IS NULL AND pattern IS NOT NULL) OR
        (parent_id IS NULL)  -- Root node can have both NULL
    )
);

-- ============================================================================
-- INDEXES for nodes
-- ============================================================================

-- For Query 2: Get children of a node
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);

-- For Query 5: Find node by code
CREATE INDEX IF NOT EXISTS idx_nodes_code ON nodes(code) WHERE code IS NOT NULL;

-- For Query 6: Find product by full_typecode
CREATE INDEX IF NOT EXISTS idx_nodes_typecode ON nodes(full_typecode) WHERE full_typecode IS NOT NULL;

-- For Query 4: Get nodes at specific level
CREATE INDEX IF NOT EXISTS idx_nodes_level ON nodes(level);

-- Composite index for performance
CREATE INDEX IF NOT EXISTS idx_nodes_level_code ON nodes(level, code) WHERE code IS NOT NULL;


-- ============================================================================
-- TABLE: node_dates (OPTIONAL)
-- ============================================================================
-- Stores product lifecycle data (creation/modification dates)
-- Separated for cleaner schema (date_info is optional in JSON)
-- ============================================================================

CREATE TABLE IF NOT EXISTS node_dates (
    node_id INTEGER PRIMARY KEY,
    
    -- Usage statistics
    typecode_count INTEGER,  -- Number of products using this code
    
    -- Creation dates
    creation_earliest TEXT,  -- ISO 8601 format: YYYY-MM-DD
    creation_latest TEXT,
    
    -- Modification dates
    modification_earliest TEXT,
    modification_latest TEXT,
    
    -- Constraints
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);


-- ============================================================================
-- TABLE: node_paths (CLOSURE TABLE - OPTIONAL)
-- ============================================================================
-- Pre-computed transitive closure for fast hierarchical queries
-- Only needed if using Option A (Closure Table approach)
-- Storage: ~1-2 GB for 2M variants (28M relationships)
-- Performance: Instant lookups for Query 4
-- ============================================================================

CREATE TABLE IF NOT EXISTS node_paths (
    ancestor_id INTEGER NOT NULL,
    descendant_id INTEGER NOT NULL,
    depth INTEGER NOT NULL,  -- Number of levels between ancestor and descendant
    
    -- Composite primary key
    PRIMARY KEY (ancestor_id, descendant_id),
    
    -- Foreign keys
    FOREIGN KEY (ancestor_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (descendant_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES for node_paths
-- ============================================================================

-- For backward compatibility checks (Query 4)
CREATE INDEX IF NOT EXISTS idx_paths_descendant ON node_paths(descendant_id);

-- For depth-based queries
CREATE INDEX IF NOT EXISTS idx_paths_depth ON node_paths(depth);


-- ============================================================================
-- TRIGGERS (For automatic Closure Table maintenance)
-- ============================================================================
-- Only needed if using Closure Table + allowing INSERT/DELETE operations
-- Can be omitted if data is read-only after initial import
-- ============================================================================

-- Trigger: Insert new paths when a node is added
CREATE TRIGGER IF NOT EXISTS trg_node_insert
AFTER INSERT ON nodes
FOR EACH ROW
WHEN NEW.parent_id IS NOT NULL
BEGIN
    -- Insert self-reference
    INSERT INTO node_paths (ancestor_id, descendant_id, depth)
    VALUES (NEW.id, NEW.id, 0);
    
    -- Insert paths through parent
    INSERT INTO node_paths (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, NEW.id, depth + 1
    FROM node_paths
    WHERE descendant_id = NEW.parent_id;
END;

-- Trigger: Delete all paths when a node is deleted
CREATE TRIGGER IF NOT EXISTS trg_node_delete
BEFORE DELETE ON nodes
FOR EACH ROW
BEGIN
    -- Delete all paths involving this node
    DELETE FROM node_paths
    WHERE ancestor_id = OLD.id OR descendant_id = OLD.id;
END;


-- ============================================================================
-- VIEWS (Helper views for common queries)
-- ============================================================================

-- View: All product families (Query 1)
CREATE VIEW IF NOT EXISTS v_product_families AS
SELECT id, code, label, label_en, position, group_name
FROM nodes
WHERE parent_id IS NULL AND code IS NOT NULL
ORDER BY code;

-- View: All leaf products (final products without children)
CREATE VIEW IF NOT EXISTS v_leaf_products AS
SELECT id, code, full_typecode, label, label_en
FROM nodes
WHERE full_typecode IS NOT NULL
  AND is_intermediate_code = 0
ORDER BY full_typecode;

-- View: All intermediate products (products with variants)
CREATE VIEW IF NOT EXISTS v_intermediate_products AS
SELECT id, code, full_typecode, label, label_en
FROM nodes
WHERE full_typecode IS NOT NULL
  AND is_intermediate_code = 1
ORDER BY full_typecode;


-- ============================================================================
-- COMMENTS & DOCUMENTATION
-- ============================================================================

-- Schema Design Notes:
-- 
-- 1. LEVEL CALCULATION:
--    - Level 0 = Product Family (root)
--    - Level 1+ = Selection steps
--    - Pattern Containers DO NOT count as levels (they're organizational)
--    - Level is calculated during import based on tree depth
--
-- 2. PATTERN CONTAINERS:
--    - Have `pattern` set, `code` is NULL
--    - Not selectable by users
--    - Organizational only (group codes by length)
--
-- 3. INTERMEDIATE CODES:
--    - Have both `full_typecode` AND children
--    - Represent products that can be ordered as-is OR customized further
--
-- 4. CLOSURE TABLE (node_paths):
--    - Optional but HIGHLY RECOMMENDED for 2M+ records
--    - Stores ALL ancestor-descendant relationships
--    - Example: If A→B→C→D exists, stores:
--      * A→A (depth=0), A→B (depth=1), A→C (depth=2), A→D (depth=3)
--      * B→B (depth=0), B→C (depth=1), B→D (depth=2)
--      * C→C (depth=0), C→D (depth=1)
--      * D→D (depth=0)
--    - Enables instant path existence checks for Query 4
--
-- 5. PERFORMANCE OPTIMIZATION:
--    - Indexes on parent_id, code, level for fast queries
--    - Closure table for O(1) path lookups (vs O(n) recursive)
--    - Triggers maintain closure table automatically on INSERT/DELETE
--
-- 6. AZURE SQL SERVER COMPATIBILITY:
--    - Change AUTOINCREMENT to IDENTITY(1,1)
--    - Change BOOLEAN to BIT
--    - Change TEXT to NVARCHAR(MAX) or appropriate size
--    - Triggers syntax may need adjustment
--
-- ============================================================================

-- ============================================================================
-- TABLE: users
-- ============================================================================
-- User accounts für Authentication (Admins & normale Users)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT 1,
    must_change_password BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes für Users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
