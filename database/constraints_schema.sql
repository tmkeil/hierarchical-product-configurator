-- ============================================================================
-- CONSTRAINTS SCHEMA - Code Validation Rules
-- ============================================================================
-- Defines rules that restrict which codes can be used on specific levels
-- based on previous selections (pattern matching, prefix rules, etc.)
-- ============================================================================

-- ============================================================================
-- TABLE: constraints
-- ============================================================================
-- Main constraint definition for a specific level
-- ============================================================================

CREATE TABLE IF NOT EXISTS constraints (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Target level for this constraint
    level INTEGER NOT NULL,
    
    -- Rule mode
    mode TEXT NOT NULL CHECK(mode IN ('allow', 'deny')),
    -- 'allow': Only listed codes are permitted (whitelist)
    -- 'deny': Listed codes are forbidden (blacklist)
    
    -- Human-readable description
    description TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_constraints_level ON constraints(level);


-- ============================================================================
-- TABLE: constraint_conditions
-- ============================================================================
-- Conditions that must be met for a constraint to apply
-- All conditions are AND-ed together
-- ============================================================================

CREATE TABLE IF NOT EXISTS constraint_conditions (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Parent constraint
    constraint_id INTEGER NOT NULL,
    
    -- Condition type
    condition_type TEXT NOT NULL CHECK(condition_type IN ('pattern', 'prefix', 'exact_code')),
    -- 'pattern': Code length match (e.g., "4-6" or "5")
    -- 'prefix': Code starts with specific prefix (e.g., "C")
    -- 'exact_code': Exact code match (e.g., "ABC123")
    
    -- Which level does this condition check?
    target_level INTEGER NOT NULL,
    
    -- Condition value
    value TEXT NOT NULL,
    -- Examples:
    --   pattern: "4-6", "5", "3-10"
    --   prefix: "C", "AB", "XYZ"
    --   exact_code: "ABC123", "C010"
    
    -- Constraints
    FOREIGN KEY (constraint_id) REFERENCES constraints(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conditions_constraint ON constraint_conditions(constraint_id);


-- ============================================================================
-- TABLE: constraint_codes
-- ============================================================================
-- Codes that are allowed/denied by this constraint
-- Supports both single codes and ranges
-- ============================================================================

CREATE TABLE IF NOT EXISTS constraint_codes (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Parent constraint
    constraint_id INTEGER NOT NULL,
    
    -- Code type
    code_type TEXT NOT NULL CHECK(code_type IN ('single', 'range')),
    -- 'single': Single code (e.g., "C010")
    -- 'range': Code range (e.g., "C010-C020", "A-Z", "PS001-PS999")
    
    -- Code value
    code_value TEXT NOT NULL,
    -- Examples:
    --   single: "C010", "ABC", "XYZ123"
    --   range: "C010-C020", "A-X", "0-Z", "Z0-ZZ", "PS001-PS999"
    
    -- Constraints
    FOREIGN KEY (constraint_id) REFERENCES constraints(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_codes_constraint ON constraint_codes(constraint_id);


-- ============================================================================
-- EXAMPLE CONSTRAINTS
-- ============================================================================

-- Example 1: "If Level 1 starts with 'C' AND Level 2 has pattern 4-6,
--             then only codes C010-C020 are allowed on Level 3"
-- 
-- INSERT INTO constraints (level, mode, description) VALUES
--   (3, 'allow', 'Only C010-C020 for C-family with short Level 2 codes');
-- 
-- INSERT INTO constraint_conditions (constraint_id, condition_type, target_level, value) VALUES
--   (1, 'prefix', 1, 'C'),
--   (1, 'pattern', 2, '4-6');
-- 
-- INSERT INTO constraint_codes (constraint_id, code_type, code_value) VALUES
--   (1, 'range', 'C010-C020');


-- Example 2: "If Level 1 is exactly 'KDC', deny codes starting with 'X' on Level 2"
-- 
-- INSERT INTO constraints (level, mode, description) VALUES
--   (2, 'deny', 'No X-codes for KDC family');
-- 
-- INSERT INTO constraint_conditions (constraint_id, condition_type, target_level, value) VALUES
--   (2, 'exact_code', 1, 'KDC');
-- 
-- INSERT INTO constraint_codes (constraint_id, code_type, code_value) VALUES
--   (2, 'single', 'X1'),
--   (2, 'single', 'X2'),
--   (2, 'range', 'X10-X99');


-- ============================================================================
-- NOTES
-- ============================================================================
--
-- Range Format Examples:
--   Numeric with prefix: C010-C020 (C010, C011, ..., C020)
--   Alphabetic: A-X (A, B, C, ..., X)
--   Alphanumeric: 0-Z (0, 1, ..., 9, A, ..., Z)
--   Complex: Z0-ZZ (Z0, Z1, ..., Z9, ZA, ..., ZZ)
--   Long prefix: PS001-PS999 (PS001, PS002, ..., PS999)
--
-- Condition Evaluation:
--   All conditions for a constraint are AND-ed together
--   Multiple constraints on the same level are OR-ed together
--   If NO constraints match, code is allowed by default
--
-- Mode Logic:
--   'allow' mode: Code must be in constraint_codes list
--   'deny' mode: Code must NOT be in constraint_codes list
--
-- ============================================================================
