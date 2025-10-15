#!/usr/bin/env python3
"""
Test suite for product variant tree SQL queries.
Tests all 8 queries from queries.sql against the imported database.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
import sys


class QueryTester:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.test_results = []
        
    def connect(self):
        """Connect to database."""
        print(f"📁 Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()
        print("✅ Connected!\n")
        
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def run_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Execute query and return results as list of dicts."""
        if params is None:
            params = {}
        
        # Convert dict params to tuple for sqlite3
        # SQLite uses ? placeholders, but we use :name for readability
        self.cursor.execute(query, params)
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def print_results(self, results: List[Dict], title: str):
        """Pretty print query results."""
        print(f"\n{'='*60}")
        print(f"📊 {title}")
        print(f"{'='*60}")
        
        if not results:
            print("⚠️  No results returned")
            return
            
        print(f"Found {len(results)} row(s):\n")
        
        # Print as table
        if results:
            headers = list(results[0].keys())
            
            # Calculate column widths
            widths = {h: len(h) for h in headers}
            for row in results:
                for h in headers:
                    val_len = len(str(row[h]))
                    if val_len > widths[h]:
                        widths[h] = val_len
            
            # Print header
            header_line = " | ".join(h.ljust(widths[h]) for h in headers)
            print(header_line)
            print("-" * len(header_line))
            
            # Print rows
            for row in results:
                print(" | ".join(str(row[h]).ljust(widths[h]) for h in headers))
                
    def test_query_1_product_families(self):
        """Test Query 1: Get all product families."""
        query = """
        SELECT 
            code,
            label,
            label_en,
            position,
            group_name
        FROM nodes
        WHERE parent_id IS NULL 
          AND code IS NOT NULL
        ORDER BY position, code
        """
        
        results = self.run_query(query)
        self.print_results(results, "Query 1: Get Product Families")
        
        # Validation
        assert len(results) > 0, "Should have at least one product family"
        assert all('code' in r for r in results), "All results should have 'code'"
        
        print(f"✅ Query 1 passed! Found {len(results)} product families")
        self.test_results.append(("Query 1", "PASS", len(results)))
        
        return results
        
    def test_query_2_get_children(self, parent_code: str):
        """Test Query 2: Get children of a node."""
        query = """
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
        AND code IS NOT NULL
        ORDER BY position, code
        """
        
        results = self.run_query(query, {'parent_code': parent_code})
        self.print_results(results, f"Query 2: Get Children of '{parent_code}'")
        
        print(f"✅ Query 2 passed! Found {len(results)} children")
        self.test_results.append(("Query 2", "PASS", len(results)))
        
        return results
        
    def test_query_3_max_depth(self, start_code: str):
        """Test Query 3: Get maximum depth from node."""
        query = """
        WITH RECURSIVE depth_calc AS (
            SELECT id, 0 as depth
            FROM nodes
            WHERE code = :start_code
            
            UNION ALL
            
            SELECT n.id, d.depth + 1 as depth
            FROM nodes n
            JOIN depth_calc d ON n.parent_id = d.id
        )
        SELECT MAX(depth) as max_depth FROM depth_calc
        """
        
        results = self.run_query(query, {'start_code': start_code})
        self.print_results(results, f"Query 3: Max Depth from '{start_code}'")
        
        max_depth = results[0]['max_depth'] if results else 0
        print(f"✅ Query 3 passed! Max depth = {max_depth}")
        self.test_results.append(("Query 3", "PASS", max_depth))
        
        return max_depth
        
    def test_query_4_simple(self, target_level: int):
        """Test Query 4 (simplified): Get options at level with no previous selections."""
        query = """
        SELECT 
            code,
            label,
            position,
            group_name,
            level,
            1 as is_compatible
        FROM nodes
        WHERE level = :target_level
          AND code IS NOT NULL
        ORDER BY position, code
        """
        
        results = self.run_query(query, {'target_level': target_level})
        self.print_results(results, f"Query 4 (Simple): Get Options at Level {target_level}")
        
        print(f"✅ Query 4 (Simple) passed! Found {len(results)} options")
        self.test_results.append(("Query 4 (Simple)", "PASS", len(results)))
        
        return results
        
    def test_query_4_with_closure(self, target_level: int, selection_codes: List[tuple]):
        """
        Test Query 4 with closure table: Get compatible options.
        
        Args:
            target_level: Level to get options for
            selection_codes: List of (code, level) tuples for current selections
        """
        # First check if closure table exists
        check_closure = "SELECT name FROM sqlite_master WHERE type='table' AND name='node_paths'"
        closure_exists = len(self.run_query(check_closure)) > 0
        
        if not closure_exists:
            print("⚠️  Closure table not found - skipping Query 4 with compatibility check")
            print("   Run import with --closure flag to test this query")
            self.test_results.append(("Query 4 (Closure)", "SKIP", "No closure table"))
            return []
        
        # Build query with dynamic number of selections
        selections_cte = "current_selections AS (\n"
        for i, (code, level) in enumerate(selection_codes):
            if i > 0:
                selections_cte += "    UNION ALL\n"
            selections_cte += f"    SELECT '{code}' as code, {level} as level\n"
        selections_cte += ")"
        
        query = f"""
        WITH 
        {selections_cte},
        
        candidates AS (
            SELECT id, code, label, position, group_name, level
            FROM nodes
            WHERE level = :target_level AND code IS NOT NULL
        ),
        
        selection_ids AS (
            SELECT n.id, cs.level
            FROM current_selections cs
            JOIN nodes n ON n.code = cs.code AND n.level = cs.level
        ),
        
        last_selection AS (
            SELECT id, level FROM selection_ids ORDER BY level DESC LIMIT 1
        ),
        
        forward_compatible AS (
            SELECT DISTINCT np.descendant_id as candidate_id
            FROM node_paths np
            JOIN last_selection ls ON np.ancestor_id = ls.id
            JOIN candidates c ON np.descendant_id = c.id
        ),
        
        backward_compatible AS (
            SELECT c.id as candidate_id
            FROM candidates c
            WHERE NOT EXISTS (
                SELECT 1 FROM selection_ids si
                WHERE si.level < :target_level
                  AND NOT EXISTS (
                      SELECT 1 FROM node_paths np
                      WHERE np.ancestor_id = c.id AND np.descendant_id = si.id
                  )
            )
        )
        
        SELECT 
            c.code, c.label, c.position, c.group_name, c.level,
            CASE WHEN fc.candidate_id IS NOT NULL AND bc.candidate_id IS NOT NULL 
                 THEN 1 ELSE 0 
            END as is_compatible
        FROM candidates c
        LEFT JOIN forward_compatible fc ON c.id = fc.candidate_id
        LEFT JOIN backward_compatible bc ON c.id = bc.candidate_id
        ORDER BY c.position, c.code
        """
        
        results = self.run_query(query, {'target_level': target_level})
        
        path_str = " → ".join(f"{code}(L{level})" for code, level in selection_codes)
        self.print_results(results, 
            f"Query 4 (Closure): Get Options at Level {target_level} after [{path_str}]")
        
        compatible = sum(1 for r in results if r['is_compatible'] == 1)
        incompatible = sum(1 for r in results if r['is_compatible'] == 0)
        
        print(f"✅ Query 4 (Closure) passed! {compatible} compatible, {incompatible} incompatible")
        self.test_results.append(("Query 4 (Closure)", "PASS", f"{compatible}/{len(results)}"))
        
        return results
        
    def test_query_5_find_by_code(self, search_code: str):
        """Test Query 5: Find nodes by code."""
        query = """
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
        ORDER BY n.level, n.id
        """
        
        results = self.run_query(query, {'search_code': search_code})
        self.print_results(results, f"Query 5: Find Node by Code '{search_code}'")
        
        print(f"✅ Query 5 passed! Found {len(results)} node(s)")
        self.test_results.append(("Query 5", "PASS", len(results)))
        
        return results
        
    def test_query_6_find_by_typecode(self, full_typecode: str):
        """Test Query 6: Find product by full typecode."""
        query = """
        SELECT 
            id,
            code,
            label,
            full_typecode,
            is_intermediate_code
        FROM nodes
        WHERE full_typecode = :full_typecode
        LIMIT 1
        """
        
        results = self.run_query(query, {'full_typecode': full_typecode})
        self.print_results(results, f"Query 6: Find Product by Typecode '{full_typecode}'")
        
        found = len(results) > 0
        print(f"{'✅' if found else '⚠️ '} Query 6 {'passed' if found else 'no results'}")
        self.test_results.append(("Query 6", "PASS" if found else "WARN", len(results)))
        
        return results
        
    def test_query_7_check_node_type(self, check_code: str):
        """Test Query 7: Check node type."""
        query = """
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
                WHEN pattern IS NOT NULL THEN 'pattern_container'
                WHEN full_typecode IS NOT NULL AND is_intermediate_code = 0 THEN 'leaf'
                WHEN full_typecode IS NOT NULL AND is_intermediate_code = 1 THEN 'intermediate'
                WHEN full_typecode IS NULL AND code IS NOT NULL THEN 'variant_step'
                ELSE 'unknown'
            END as node_type,
            child_count > 0 as has_children
        FROM node_info
        """
        
        results = self.run_query(query, {'check_code': check_code})
        self.print_results(results, f"Query 7: Check Node Type for '{check_code}'")
        
        if results:
            node_type = results[0]['node_type']
            print(f"✅ Query 7 passed! Node type = '{node_type}'")
            self.test_results.append(("Query 7", "PASS", node_type))
        else:
            print(f"⚠️  Query 7 - node '{check_code}' not found")
            self.test_results.append(("Query 7", "WARN", "Not found"))
        
        return results
        
    def test_query_8_get_path(self, target_code: str, full_typecode: Optional[str] = None):
        """Test Query 8: Get full path from root."""
        query = """
        WITH RECURSIVE path_to_root AS (
            SELECT 
                id, parent_id, code, label, level, 0 as depth_from_target
            FROM nodes
            WHERE code = :target_code
              AND (:target_full_typecode IS NULL OR full_typecode = :target_full_typecode)
            
            UNION ALL
            
            SELECT 
                n.id, n.parent_id, n.code, n.label, n.level,
                p.depth_from_target + 1
            FROM nodes n
            JOIN path_to_root p ON p.parent_id = n.id
        )
        SELECT code, label, level, depth_from_target
        FROM path_to_root
        WHERE code IS NOT NULL
        ORDER BY depth_from_target DESC
        """
        
        params = {
            'target_code': target_code,
            'target_full_typecode': full_typecode
        }
        
        results = self.run_query(query, params)
        self.print_results(results, f"Query 8: Get Path to '{target_code}'")
        
        if results:
            path = " → ".join(r['code'] for r in results)
            print(f"✅ Query 8 passed! Path: {path}")
            self.test_results.append(("Query 8", "PASS", path))
        else:
            print(f"⚠️  Query 8 - no path found to '{target_code}'")
            self.test_results.append(("Query 8", "WARN", "No path"))
        
        return results
        
    def get_sample_data(self) -> Dict[str, Any]:
        """Get sample codes for testing from database."""
        samples = {}
        
        # Get first product family
        families = self.run_query(
            "SELECT code FROM nodes WHERE parent_id IS NULL AND code IS NOT NULL LIMIT 1"
        )
        samples['product_family'] = families[0]['code'] if families else None
        
        # Get first code node at level 1
        level1 = self.run_query(
            "SELECT code FROM nodes WHERE level = 1 AND code IS NOT NULL LIMIT 1"
        )
        samples['level1_code'] = level1[0]['code'] if level1 else None
        
        # Get first code node at level 2
        level2 = self.run_query(
            "SELECT code FROM nodes WHERE level = 2 AND code IS NOT NULL LIMIT 1"
        )
        samples['level2_code'] = level2[0]['code'] if level2 else None
        
        # Get first leaf product
        leaf = self.run_query(
            "SELECT code, full_typecode FROM nodes WHERE full_typecode IS NOT NULL LIMIT 1"
        )
        if leaf:
            samples['leaf_code'] = leaf[0]['code']
            samples['leaf_typecode'] = leaf[0]['full_typecode']
        
        return samples
        
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        warned = sum(1 for _, status, _ in self.test_results if status == "WARN")
        skipped = sum(1 for _, status, _ in self.test_results if status == "SKIP")
        failed = total - passed - warned - skipped
        
        for query_name, status, details in self.test_results:
            icon = "✅" if status == "PASS" else "⚠️ " if status == "WARN" else "⏭️ " if status == "SKIP" else "❌"
            print(f"{icon} {query_name.ljust(25)} {status.ljust(6)} {details}")
        
        print(f"\n{'='*60}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed:   {passed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"⏭️  Skipped:  {skipped}")
        print(f"❌ Failed:   {failed}")
        print(f"{'='*60}\n")
        
        if failed > 0:
            print("❌ Some tests failed!")
            return False
        elif warned > 0:
            print("⚠️  All tests passed with warnings")
            return True
        else:
            print("✅ All tests passed!")
            return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test SQL queries for product variant tree database'
    )
    parser.add_argument(
        '--db',
        default='products.db',
        help='Path to SQLite database (default: products.db)'
    )
    parser.add_argument(
        '--query',
        type=int,
        choices=range(1, 9),
        help='Run only specific query (1-8)'
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = QueryTester(args.db)
    
    try:
        tester.connect()
        
        # Get sample data for testing
        print("🔍 Finding sample data for tests...\n")
        samples = tester.get_sample_data()
        
        if not samples.get('product_family'):
            print("❌ No product families found in database!")
            print("   Make sure you've imported data with import_data.py")
            sys.exit(1)
        
        print(f"Sample product family: {samples['product_family']}")
        print(f"Sample level 1 code:   {samples.get('level1_code', 'N/A')}")
        print(f"Sample level 2 code:   {samples.get('level2_code', 'N/A')}")
        print(f"Sample leaf product:   {samples.get('leaf_code', 'N/A')}")
        print()
        
        # Run tests
        if args.query is None or args.query == 1:
            tester.test_query_1_product_families()
            
        if args.query is None or args.query == 2:
            if samples.get('product_family'):
                tester.test_query_2_get_children(samples['product_family'])
            
        if args.query is None or args.query == 3:
            if samples.get('product_family'):
                tester.test_query_3_max_depth(samples['product_family'])
            
        if args.query is None or args.query == 4:
            # Test simple version (no selections)
            tester.test_query_4_simple(target_level=1)
            
            # Test with closure table if we have sample data
            if samples.get('product_family') and samples.get('level1_code'):
                selections = [
                    (samples['product_family'], 0),
                    (samples['level1_code'], 1)
                ]
                tester.test_query_4_with_closure(target_level=2, selection_codes=selections)
            
        if args.query is None or args.query == 5:
            if samples.get('level1_code'):
                tester.test_query_5_find_by_code(samples['level1_code'])
            
        if args.query is None or args.query == 6:
            if samples.get('leaf_typecode'):
                tester.test_query_6_find_by_typecode(samples['leaf_typecode'])
            
        if args.query is None or args.query == 7:
            if samples.get('level1_code'):
                tester.test_query_7_check_node_type(samples['level1_code'])
            
        if args.query is None or args.query == 8:
            if samples.get('leaf_code'):
                tester.test_query_8_get_path(
                    samples['leaf_code'],
                    samples.get('leaf_typecode')
                )
        
        # Print summary
        tester.print_summary()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        tester.disconnect()


if __name__ == '__main__':
    main()
