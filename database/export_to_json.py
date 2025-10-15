#!/usr/bin/env python3
"""
Export Database to Variantenbaum JSON

Konvertiert die SQLite Database zurück in das hierarchische JSON-Format,
das ursprünglich verwendet wurde.

Format:
- Nodes mit 'pattern' Feld → Pattern Container (kein 'code', nur 'pattern' und 'children')
- Nodes mit 'code' → Normale Nodes mit allen Feldern
- Rekursive Struktur über parent_id Beziehungen

Usage:
    python export_to_json.py [output_file.json]
    
    Default output: variantenbaum_export.json
"""

import sqlite3
import json
import sys
from typing import Dict, List, Any, Optional


def get_db_connection(db_path: str = "variantenbaum.db") -> sqlite3.Connection:
    """Verbinde mit SQLite Database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def build_node_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Konvertiert eine DB Row 1:1 in ein Node Dictionary im JSON-Format.
    
    WICHTIG: Übernimmt Werte DIREKT aus der DB!
    - Wenn Wert NULL ist → Feld wird nicht ins JSON geschrieben
    - Reihenfolge der Felder: children, code/pattern, name, label, label-en, position, is_intermediate_code, full_typecode, group
    """
    from collections import OrderedDict
    node = OrderedDict()
    
    # WICHTIG: children kommt IMMER ZUERST!
    node['children'] = []  # Wird später gefüllt
    
    # Pattern Container?
    if row['pattern'] is not None:
        node['pattern'] = row['pattern']
        node['position'] = row['position']
        node['name'] = row['name'] if row['name'] else ""
    else:
        # Normaler Node
        if row['code']:
            node['code'] = row['code']
        
        node['name'] = row['name'] if row['name'] else ""
        node['label'] = row['label'] if row['label'] else ""
        node['label-en'] = row['label_en'] if row['label_en'] else ""  # Bindestrich!
        node['position'] = row['position']
        
        # is_intermediate_code: Nur hinzufügen wenn in DB gesetzt (nicht NULL)
        # UND nur bei Nodes mit Code
        if row['code'] and row['is_intermediate_code'] is not None:
            node['is_intermediate_code'] = bool(row['is_intermediate_code'])
        
        # full_typecode: Nur wenn in DB gesetzt (nicht NULL)
        if row['full_typecode'] is not None:
            node['full_typecode'] = row['full_typecode']
        
        # group: Nur wenn in DB gesetzt (nicht NULL)
        if row['group_name'] is not None:
            node['group'] = row['group_name']
    
    return node


# KEINE zusätzliche Logik mehr nötig!
# Alle Daten kommen direkt aus der Datenbank.


def build_tree_recursive(conn: sqlite3.Connection, parent_id: Optional[int]) -> List[Dict[str, Any]]:
    """
    Baut rekursiv den Baum auf.
    
    Args:
        conn: Database Connection
        parent_id: ID des Parent-Nodes (None für Root-Nodes)
    
    Returns:
        Liste von Child-Nodes
    """
    # Hole alle direkten Kinder
    if parent_id is None:
        cursor = conn.execute("""
            SELECT * FROM nodes 
            WHERE parent_id IS NULL 
            ORDER BY position, id
        """)
    else:
        cursor = conn.execute("""
            SELECT * FROM nodes 
            WHERE parent_id = ? 
            ORDER BY position, id
        """, (parent_id,))
    
    children = []
    for row in cursor:
        node = build_node_dict(row)
        
        # Rekursiv Kinder holen
        node['children'] = build_tree_recursive(conn, row['id'])
        
        # WICHTIG: is_intermediate_code nur behalten wenn Node Kinder hat!
        if not node['children'] and 'is_intermediate_code' in node:
            del node['is_intermediate_code']
        
        children.append(node)
    
    return children


def export_database_to_json(db_path: str = "variantenbaum.db", output_file: str = "variantenbaum_export.json"):
    """
    Hauptfunktion: Exportiert die gesamte Database zu JSON.
    
    Args:
        db_path: Pfad zur SQLite Database
        output_file: Pfad für Output JSON
    """
    print(f"📖 Lese Database: {db_path}")
    conn = get_db_connection(db_path)
    
    try:
        # Zähle Nodes
        total_nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        print(f"   Gefunden: {total_nodes} nodes")
        
        # Baue Baum auf (starte mit Root-Nodes, parent_id = NULL)
        print("🌳 Baue hierarchischen Baum...")
        root_children = build_tree_recursive(conn, parent_id=None)
        
        # Erstelle Root-Node mit "code": "root" (wie im Original!)
        # WICHTIG: Reihenfolge: children, dann code
        from collections import OrderedDict
        root = OrderedDict()
        root['children'] = root_children
        root['code'] = 'root'
        
        # FERTIG! Alle Daten kommen direkt aus der DB, keine weitere Verarbeitung nötig!
        
        # Schreibe JSON
        print(f"💾 Schreibe JSON: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(root, f, indent=2, ensure_ascii=False)
        
        # Statistiken
        def count_nodes(node):
            count = 1 if ('code' in node or 'pattern' in node) else 0
            for child in node.get('children', []):
                count += count_nodes(child)
            return count
        
        exported_count = count_nodes(root)
        print(f"✅ Erfolgreich! {exported_count} nodes exportiert")
        print(f"   Output: {output_file}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "variantenbaum_export.json"
    export_database_to_json(output_file=output_file)
