#!/usr/bin/env python3
"""
Label-Mapping-Tool für Variantenbäume

Dieses Tool liest Label-Mappings aus einer JSON-Datei und fügt sie automatisch
in den Variantenbaum ein, basierend auf Filter-Kriterien.

Verwendung:
    python label_mapper.py mapping_file.json [--dry-run] [--backup] [--output output.json]
    
Beispiele:
    python label_mapper.py labels_bcc_mounting.json
    python label_mapper.py labels_bcc_mounting.json --dry-run
    python label_mapper.py labels_bcc_mounting.json --backup --output labeled_tree.json
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil
import re
import glob
from schema_search import find_products_by_schema, parse_multiple_schemas, parse_pattern_filter, parse_position_filter, parse_group_start_filter, parse_group_filter, parse_group_position_filter

# Wo das Label-Mapping angewendet wird
JSONFILE = "./baum.json"

def parse_label(label_data):
    """
    Parst ein Label aus String oder erweitertem Objekt-Format.
    
    Args:
        label_data: String oder dict mit {text, pictures, links}
        
    Returns:
        dict: Normalisiertes Label-Objekt {text, pictures, links}
        
    Beispiele:
        "Hydraulik" -> {"text": "Hydraulik", "pictures": [], "links": []}
        {"text": "Hydraulik", "pictures": [...], "links": [...]} -> {"text": "Hydraulik", "pictures": [...], "links": [...]}
    """
    if isinstance(label_data, str):
        return {
            "text": label_data,
            "pictures": [],
            "links": []
        }
    elif isinstance(label_data, dict):
        return {
            "text": label_data.get("text", ""),
            "pictures": label_data.get("pictures", []),
            "links": label_data.get("links", [])
        }
    else:
        raise ValueError(f"Ungültiges Label-Format: {type(label_data)}")

def label_to_string(label_obj):
    """
    Extrahiert nur den Text aus einem Label-Objekt.
    
    Args:
        label_obj: dict mit {text, pictures, links}
        
    Returns:
        str: Label-Text
    """
    return label_obj.get("text", "")
# JSONFILE = "output/variantenbaum.json"
# JSONFILE = "output/variantenbaum_with_dates.json"

def load_mapping_file(mapping_file):
    """
    Lädt eine Label-Mapping-Datei.
    
    Args:
        mapping_file: Pfad zur JSON-Datei mit filter_criteria und code_mappings
        
    Returns:
        dict: Geladene Daten oder None bei Fehlern
        
    Format-Dokumentation:
        Siehe docs/AutoLabeling.md für vollständige JSON-Format-Spezifikation
        
    Kurz-Übersicht:
    {
        "filter_criteria": {
            "family": "BCC",
            "pattern": "1=4", 
            "contains": "M313|M423"
        },
        "code_mappings": [
            {
                "position": 1,
                "codes": ["M313", "M423"],
                "labels": ["Motor 313kW", "Motor 423kW"]
            }
        ],
        "group_mappings": [
            {
                "group": 1,
                "position": 1, 
                "codes": ["M313", "M423"],
                "labels": ["Motor 313kW", "Motor 423kW"]
            }
        ],
        "general_mappings": [
            {
                "codes": ["S4", "PU", "Y"],
                "labels": ["Stecker S4", "PUR-Kabel", "Y-Verteiler"]
            }
        ]
    }
    """
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validiere Struktur
        if 'filter_criteria' not in data:
            print(f"❌ Fehler: 'filter_criteria' fehlt in {mapping_file}")
            return None
        
        # Prüfe ob mindestens code_mappings oder group_mappings vorhanden sind
        if 'code_mappings' not in data:
            data['code_mappings'] = []  # Leere Liste als Standard
        
        if 'group_mappings' not in data:
            data['group_mappings'] = []  # Leere Liste als Standard
        
        if 'global_group_mappings' not in data:
            data['global_group_mappings'] = []  # Leere Liste als Standard
        
        if 'name_mappings' not in data:
            data['name_mappings'] = []  # Leere Liste als Standard
        
        if 'general_mappings' not in data:
            data['general_mappings'] = []  # Leere Liste als Standard
        
        # Validiere dass mindestens ein Mapping-Typ vorhanden ist
        if not data['code_mappings'] and not data['group_mappings'] and not data['global_group_mappings'] and not data['name_mappings'] and not data['general_mappings'] and not data['special_mappings'] and not data['relative_group_mappings']:
            print(f"❌ Fehler: Keine 'code_mappings', 'group_mappings', 'global_group_mappings', 'name_mappings' oder 'general_mappings' gefunden in {mapping_file}")
            return None
        
        return data
    except FileNotFoundError:
        print(f"❌ Fehler: Datei {mapping_file} nicht gefunden!")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim Laden der JSON-Datei: {e}")
        return None
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return None


def parse_filter_criteria(filter_criteria):
    """
    Parst die Filter-Kriterien zu den internen Formaten.
    
    Args:
        filter_criteria: Dictionary mit Filter-Kriterien
        
    Returns:
        dict: Geparste Filter-Parameter für find_products_by_schema
    """
    params = {
        'target_schemas': None,
        'product_family': filter_criteria.get('family'),
        'pattern_rules': None,
        'position_rules': None,
        'group_start_rules': None,
        'group_rules': None,
        'group_count_filter': None,
        'and_mode': filter_criteria.get('and_mode', False),
        'negate_exclude': filter_criteria.get('negate', False),
        'exclude_group_rules': None,
        'group_position_filter': None
    }
    
    # Parse Schema (falls vorhanden)
    if 'schemas' in filter_criteria:
        schemas = filter_criteria['schemas']
        if isinstance(schemas, list):
            params['target_schemas'] = parse_multiple_schemas(schemas)
        else:
            params['target_schemas'] = parse_multiple_schemas([schemas])
    
    # Parse Pattern-Filter
    if 'pattern' in filter_criteria:
        params['pattern_rules'] = parse_pattern_filter(filter_criteria['pattern'])
    
    # Parse Position-Filter
    if 'position' in filter_criteria:
        params['position_rules'] = parse_position_filter(filter_criteria['position'])
    
    # Parse Gruppen-Start-Filter
    if 'group_start' in filter_criteria:
        params['group_start_rules'] = parse_group_start_filter(filter_criteria['group_start'])
    
    # Parse Gruppen-Filter
    if 'group' in filter_criteria:
        params['group_rules'] = parse_group_filter(filter_criteria['group'])
        
    # Parse group_position filter
    if 'group_position' in filter_criteria:
        params['group_position_filter'] = parse_group_position_filter(filter_criteria['group_position'])

    
    # Parse Gruppen-Anzahl-Filter
    if 'group_count' in filter_criteria:
        group_count = filter_criteria['group_count']
        # Konvertiere String zu korrektem Format
        if isinstance(group_count, str):
            # String "2" wird zu {"type": "exact", "value": 2}
            params['group_count_filter'] = {
                "type": "exact",
                "value": int(group_count)
            }
        else:
            # Bereits im richtigen Format (Dictionary)
            params['group_count_filter'] = group_count
    
    return params


def build_group_lookup(group_mappings):
    """
    Erstellt eine Lookup-Tabelle für Code → Group Zuordnungen.
    
    Args:
        group_mappings: Liste von Group-Mapping-Objekten
        
    Returns:
        dict: {position: {code: group}} Struktur
    """
    lookup = {}
    
    for mapping in group_mappings:
        position = mapping.get('position')
        codes = mapping.get('codes', [])
        groups = mapping.get('groups', [])
        
        if not position or not codes or not groups:
            continue
        
        if len(codes) != len(groups):
            print(f"⚠️  Warnung: Codes und Groups haben unterschiedliche Längen bei Position {position}")
            continue
        
        if position not in lookup:
            lookup[position] = {}
        
        for code, group in zip(codes, groups):
            lookup[position][code] = group
    
    return lookup


def build_code_lookup(code_mappings):
    """
    Erstellt eine Lookup-Tabelle für Code → Label Zuordnungen.
    
    Args:
        code_mappings: Liste von Code-Mapping-Objekten
        
    Returns:
        dict: {position: {code: label}} Struktur
    """
    lookup = {}
    
    for mapping in code_mappings:
        # Unterstütze sowohl 'position' als Zahl als auch 'position' als Array
        position_raw = mapping.get('position')
        if isinstance(position_raw, list):
            positions = position_raw
        elif position_raw is not None:
            positions = [position_raw]
        else:
            positions = []
        
        codes = mapping.get('codes', [])
        labels = mapping.get('labels', [])
        labels_en = mapping.get('labels-en', [])
        
        if not positions or not codes or not labels:
            continue
        
        # Prüfe ob labels-en vorhanden und synchron mit labels
        has_english = len(labels_en) > 0 and any(label.strip() for label in labels_en)
        
        if has_english and len(codes) != len(labels_en):
            print(f"⚠️  Warnung: Codes und englische Labels haben unterschiedliche Längen bei Position(en) {positions}")
            # Kürze labels_en auf die Länge von codes
            labels_en = labels_en[:len(codes)] + [''] * (len(codes) - len(labels_en))
        
        if len(codes) != len(labels):
            print(f"⚠️  Warnung: Codes und deutsche Labels haben unterschiedliche Längen bei Position(en) {positions}")
            continue
        
        # Wende die Codes/Labels auf alle angegebenen Positionen an
        for position in positions:
            if position not in lookup:
                lookup[position] = {}
            
            for i, (code, label) in enumerate(zip(codes, labels)):
                label_en = labels_en[i] if has_english and i < len(labels_en) else ''
                lookup[position][code] = {
                    'label': label,
                    'label-en': label_en
                }
    
    return lookup


def extract_code_at_position(full_typecode, code_parts, position):
    """
    Extrahiert den Code an einer bestimmten Position.
    
    Args:
        full_typecode: Vollständiger Produktcode
        code_parts: Code-Teile ohne Produktfamilie
        position: Position (1-basiert)
        
    Returns:
        str: Code an der Position oder None
    """
    try:
        # Für Gruppen-Positionen (Code-Teile)
        if position <= len(code_parts):
            return code_parts[position - 1]
        
        # Für absolute Positionen im vollständigen Code
        # (wird später implementiert falls benötigt)
        return None
    except (IndexError, TypeError):
        return None


def find_node_at_position(tree_data, target_family, target_position, code_at_position):
    """
    Findet den Knoten an einer bestimmten Position im Baum.
    
    ERWEITERTE VERSION: Unterstützt sowohl explizite position-Attribute als auch 
    string-basiertes Position-Matching für flexible Code-Positionen.
    
    Args:
        tree_data: JSON-Baum-Daten
        target_family: Ziel-Produktfamilie (z.B. "BCC")
        target_position: Ziel-Position (1-basiert, z.B. 7 für Position 7)
        code_at_position: Code-Wert an dieser Position (z.B. "A", "C")
        
    Returns:
        list: Liste aller gefundenen Knoten die diesem Code entsprechen
    """
    found_nodes = []
    
    def traverse_for_position(node, current_family=None, path="", depth=0):
        # Behandle Pattern-Knoten und Code-Knoten
        if 'pattern' in node:
            # Pattern-Knoten erhöhen Position nicht, behalten aktuellen Pfad
            current_path = f"{path}-pattern_{node['pattern']}" if path else f"pattern_{node['pattern']}"
        elif 'code' in node:
            current_path = f"{path}-{node['code']}" if path else node['code']
            
            # Bei Tiefe 1: Setze Produktfamilie
            if depth == 1:
                current_family = node['code']
        else:
            current_path = path
        
        # METHODE 1: Explizite position-Attribute (ALTE METHODE - Rückwärts-kompatibel)
        if (current_family == target_family and 
            'code' in node and 
            node['code'].startswith(code_at_position) and
            'position' in node and
            node['position'] == target_position):
            found_nodes.append({
                'node': node,
                'path': current_path,
                'family': current_family,
                'position': node['position'],
                'depth': depth,
                'match_type': 'explicit_position'
            })
        
        # METHODE 2: Position-basiertes Matching mit vorhandenen position-Attributen (NEUE ELEGANTE METHODE)
        elif (current_family == target_family and 
              'code' in node and 
              'position' in node and
              node['position'] <= target_position):  # Knoten muss vor oder an der Zielposition beginnen
            
            # Berechne relative Position innerhalb dieses Knoten-Codes
            node_start_position = node['position']
            relative_position = target_position - node_start_position  # 0-basiert innerhalb des Codes
            node_code = node['code']
            
            # ERWEITERT: Unterstütze sowohl einzelne Zeichen als auch Substrings
            # Prüfe ob der Code lang genug ist
            if relative_position < len(node_code):
                # Versuche Substring-Match ab der relativen Position
                remaining_code = node_code[relative_position:]
                if remaining_code.startswith(code_at_position):
                    found_nodes.append({
                        'node': node,
                        'path': current_path,
                        'family': current_family,
                        'position': target_position,  # Setze die gewünschte Position
                        'depth': depth,
                        'match_type': 'position_based',
                        'full_code': node_code,
                        'node_start_position': node_start_position,
                        'relative_position': relative_position,
                        'matched_substring': code_at_position
                    })
        
        # Rekursiv für alle Children
        for child in node.get('children', []):
            traverse_for_position(child, current_family, current_path, depth + 1)
    
    # Starte Traversierung
    traverse_for_position(tree_data)
    
    # NEUE LOGIK: Wenn wir position-basierte Matches haben, 
    # wähle die spezifischsten (tiefsten) Knoten aus
    if found_nodes:
        # Unterscheide zwischen expliziten und position-basierten Matches
        explicit_matches = [n for n in found_nodes if n['match_type'] == 'explicit_position']
        position_matches = [n for n in found_nodes if n['match_type'] == 'position_based']
        
        # Priorität: Explizite Matches > Position-basierte Matches
        if explicit_matches:
            return explicit_matches
        elif position_matches:
            # Bei position-basierten Matches: Finde die tiefsten/spezifischsten Knoten
            max_depth = max(n['depth'] for n in position_matches)
            deepest_matches = [n for n in position_matches if n['depth'] == max_depth]
            return deepest_matches
    
    return found_nodes


def extract_group_code_at_position(code_parts, group_num, position, end_position=None):
    """
    Extrahiert Code an einer bestimmten Position innerhalb einer Gruppe.
    
    Args:
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002"])
        group_num: Gruppen-Nummer (1-basiert)
        position: Start-Position innerhalb der Gruppe (1-basiert)
        end_position: End-Position innerhalb der Gruppe (optional, für Bereiche)
        
    Returns:
        str: Extrahierter Code oder leerer String wenn nicht verfügbar
    """
    if group_num < 1 or group_num > len(code_parts):
        return ""
    
    group_content = code_parts[group_num - 1]  # 0-basiert
    
    if position < 1 or position > len(group_content):
        return ""
    
    if end_position is None or end_position == -1:
        # Prefix-Matching: Ab Position bis zum Ende
        end_position = len(group_content)
    elif end_position > len(group_content):
        end_position = len(group_content)
    
    # 0-basierte Indizierung für String-Slicing
    start_idx = position - 1
    end_idx = end_position
    
    return group_content[start_idx:end_idx]


def apply_special_mappings(
    tree_data,
    matching_products,
    special_mappings,
    target_family,
    dry_run=False,
    verbose=False
):
    """
    Wendet spezielle Mappings basierend auf Gruppen- und Positionskriterien an.

    special_mappings Einträge unterstützen:
      - group: int (Pflicht)
      - position: "start-end" oder "n" (optional)
      - allowed: "0-9" | "A-Z" | "0-Z" (optional; Zeichenklasse-Constraint)
      - labels: [str, ...] (Pflicht)

    Returns:
        dict: Stats
    """
    stats = {
        'products_processed': 0,
        'labels_applied': 0,
        'labels_updated': 0,
        'groups_processed': set(),
        'nodes_labeled': []
    }

    if not special_mappings:
        return stats

    def _allowed_to_regex(allowed):
        if not allowed:
            return None
        a = allowed.strip().upper()
        if a == "0-9":
            return re.compile(r'^[0-9]+$')
        if a == "A-Z":
            return re.compile(r'^[A-Za-z]+$')
        if a == "0-Z":
            return re.compile(r'^[A-Za-z0-9]+$')
        return None

    for mapping in special_mappings:
        group_num = mapping.get('group')
        position_range = mapping.get('position')
        allowed_chars = mapping.get('allowed')
        labels_raw = mapping.get('labels', [])

        if group_num is None or not labels_raw:
            if verbose:
                print(f"Skipping special mapping (missing group or labels): {mapping}")
            continue

        # Parse labels (unterstützt String und erweiterte Objekte)
        labels = [parse_label(l) for l in labels_raw]

        # Position parsen
        if position_range:
            try:
                parts = [p.strip() for p in position_range.split('-')]
                start_pos = int(parts[0])
                end_pos = int(parts[1]) if len(parts) > 1 else start_pos
                if start_pos <= 0 or (end_pos is not None and end_pos != -1 and end_pos < start_pos):
                    raise ValueError("invalid position range")
            except Exception:
                print(f"⚠️ Ungültiger Positionsbereich '{position_range}' für Gruppe {group_num}")
                continue
        else:
            start_pos = 1
            end_pos = -1  # gesamte Gruppe

        allowed_re = _allowed_to_regex(allowed_chars)

        stats['groups_processed'].add(
            f"{group_num}:{position_range if position_range else ''}:{allowed_chars if allowed_chars else ''}"
        )

        for label in labels:
            # hole Knoten; versuche duplicate-reduction bereits hier (unique_by_full_code=True)
            target_nodes = find_nodes_by_group_position(
                tree_data, target_family, group_num, start_pos, end_pos, "", verbose=False, strict=False, unique_by_full_code=True
            )
            
            print("")

            # Deduplizierung: sichtbare Knoten (node_path) und full_code pro Label
            seen_node_paths = set()
            seen_full_codes_per_label = set()

            for node_info in target_nodes:
                node = node_info.get('node')
                if node is None:
                    continue

                # WICHTIG: Nur Knoten mit 'code' labeln, keine Pattern-Container!
                if 'code' not in node or not node.get('code'):
                    continue

                node_path = node_info.get('path', '')
                full_code = node_info.get('full_code', '') or ''

                # 1) Falls dieser sichtbare Knoten schon gelabelt wurde, skip
                if node_path and node_path in seen_node_paths:
                    continue

                # 2) Falls dieser full_code für dieses Label schon verarbeitet wurde, skip
                if full_code and full_code in seen_full_codes_per_label:
                    continue

                # optional: nur Produkte aus matching_products
                if full_code and matching_products:
                    if not any(p.get('full_typecode', '') == full_code for p in matching_products):
                        if verbose:
                            print(f"❌ Skipping node with full_code '{full_code}': not in matching products")
                        continue

                if verbose:
                    print(f"✅ Node with full_code '{full_code}' is in matching products or no filtering applied (path='{node_path}')")

                code_parts = []
                if full_code:
                    # full_code form: "FAMILY code1-code2-..."
                    parts = full_code.split()
                    if len(parts) >= 2:
                        code_without_family = parts[1]
                        code_parts = code_without_family.split('-')

                # extrahieren: wenn keine position angegeben, but allowed gesetzt -> gesamte Gruppe prüfen
                if (not position_range) and allowed_chars:
                    extracted_code = code_parts[group_num - 1] if group_num <= len(code_parts) else ""
                else:
                    extracted_code = extract_group_code_at_position(code_parts, group_num, start_pos, end_pos)
                    
                print(f"Extracted code at group {group_num}, position {position_range if position_range else 'entire group'}: '{extracted_code}' from full_code '{full_code}'")

                # Allowed-Filter
                if allowed_re is not None:
                    if not extracted_code or not allowed_re.match(extracted_code):
                        # if verbose:
                        #     print(f"Filtered by allowed='{allowed_chars}': '{extracted_code}' (full_code='{full_code}')")
                        print(f"The extracted code '{extracted_code}' does not match the allowed pattern '{allowed_chars}'. Skipping.")
                        continue

                # Alten Label-Wert ermitteln
                old_label = node.get('label', '')

                label_text = label_to_string(label)
                applied = False
                if not dry_run:
                    if old_label and old_label.strip():
                        node['label'] = f"{old_label}\n\n{label_text}"
                        stats['labels_updated'] += 1
                    else:
                        node['label'] = label_text
                        stats['labels_applied'] += 1
                    
                    # Speichere Bilder separat
                    if 'pictures' not in node:
                        node['pictures'] = []
                    node['pictures'].extend(label.get('pictures', []))
                    
                    # Speichere Links separat
                    if 'links' not in node:
                        node['links'] = []
                    node['links'].extend(label.get('links', []))
                    
                    applied = True
                else:
                    # Dry run: nur Statistik simulieren
                    if old_label and old_label.strip():
                        stats['labels_updated'] += 1
                    else:
                        stats['labels_applied'] += 1

                # Statistik-Update: code Feld hinzufügen (extracted_code oder full_code fallback)
                stats['nodes_labeled'].append({
                    'node_path': node_path,
                    'family': target_family,
                    'group': group_num,
                    'position': position_range,
                    'code': extracted_code or full_code,
                    'extracted_code': extracted_code,
                    'old_label': old_label,
                    'new_label': label_text,
                    'pictures': label.get('pictures', []),
                    'links': label.get('links', []),
                    'full_typecode': full_code,
                    'applied': applied,
                    'type': 'special_mapping'
                })
                stats['products_processed'] += 1

                # Markierungen für Deduplizierung
                if node_path:
                    seen_node_paths.add(node_path)
                if full_code:
                    seen_full_codes_per_label.add(full_code)

    return stats

    
def apply_relative_group_mappings(tree_data, matching_products, relative_group_mappings, target_family, dry_run=False, verbose=False):
    """
    Wendet relative Gruppen-Mappings auf die gefundenen Produkte im Baum an.
    
    Args:
        tree_data: JSON-Baum-Daten (werden modifiziert)
        matching_products: Liste der gefundenen Produkte
        relative_group_mappings: Liste von relativen Gruppen-Mapping-Objekten
        target_family: Ziel-Produktfamilie (z.B. "BCC")
        dry_run: Wenn True, werden keine Änderungen gemacht
        
    Returns:
        dict: Statistiken über angewendete Labels
    """
    stats = {
        'products_processed': 0,
        'labels_applied': 0,
        'labels_updated': 0,
        'groups_processed': set(),
        'codes_matched': set(),
        'nodes_labeled': []
    }

    if not relative_group_mappings:
        return stats

    # Erstelle ein Code → Label Mapping für jede Gruppe-Position-Kombination
    group_position_lookup = {}
    for mapping in relative_group_mappings:
        group_num = mapping.get('group')
        position = mapping.get('position')
        end_position = mapping.get('end_position')
        if end_position is None:
            end_position = -1
        codes = mapping.get('codes', [])
        labels_raw = mapping.get('labels', [])
        strict = mapping.get('strict', False)

        if not group_num or not position or not codes or not labels_raw:
            continue
        if len(codes) != len(labels_raw):
            print(f"⚠️  Warnung: Codes und Labels haben unterschiedliche Längen bei Gruppe {group_num}, Position {position}")
            continue

        # Parse labels (unterstützt String und erweiterte Objekte)
        labels = [parse_label(l) for l in labels_raw]

        key = f"{group_num}:{position}:{end_position}:{1 if strict else 0}"
        if key not in group_position_lookup:
            group_position_lookup[key] = {}
        for code, label in zip(codes, labels):
            group_position_lookup[key][code] = label

    # Set, um sicherzustellen, dass pro (node_path, group, position) nur einmal gelabelt wird
    # WICHTIG: Geändert von einfachem seen_node_paths zu detailliertem Tracking,
    # damit mehrere Mappings auf dieselbe Gruppe möglich sind (z.B. Pos 1 und Pos 2)
    seen_node_mappings = set()

    # Für jede Gruppe-Position-Kombination, finde passende Knoten
    for key, code_label_map in group_position_lookup.items():
        group_num, position, end_position, strict_flag = map(int, key.split(':'))
        stats['groups_processed'].add(f"{group_num}:{position}:{strict_flag}")

        for code, label in code_label_map.items():
            target_nodes = find_nodes_by_group_position(
                tree_data, target_family, group_num, position, end_position, code, verbose=False, strict=strict_flag
            )

            # lokale Deduplizierung nach (full_code, node)
            seen_keys = set()
            for node_info in target_nodes:
                dedup_key = (node_info.get('full_code', ''), id(node_info.get('node')))
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                node = node_info['node']
                node_path = node_info.get('path', '')
                full_code = node_info.get('full_code', '')

                # wenn full_code gesetzt ist, nur weitermachen, falls Produkt in matching_products existiert
                if full_code and not any(product.get('full_typecode', '') == full_code for product in matching_products):
                    continue

                # Sicherstellen: Label nur einmal pro (node_path, group, position)
                # Dadurch können mehrere Mappings auf dieselbe Gruppe angewendet werden
                mapping_key = (node_path, group_num, position)
                if mapping_key in seen_node_mappings:
                    continue
                seen_node_mappings.add(mapping_key)

                # alten Label-Wert ermitteln (vor jeder Änderung)
                old_label = node.get('label', '') if node is not None else ''

                if verbose:
                    label_text = label_to_string(label)
                    print(f"Applying label '{label_text}' to node at path: {node_path} (old_label='{old_label}')")

                # Anwenden / Dry-Run unterscheiden
                applied = False
                label_text = label_to_string(label)
                if not dry_run:
                    if old_label and old_label.strip():
                        node['label'] = old_label + '\n\n' + label_text
                        stats['labels_updated'] += 1
                    else:
                        node['label'] = label_text
                        stats['labels_applied'] += 1
                    
                    # Speichere Bilder separat (für spätere DB-Integration)
                    if 'pictures' not in node:
                        node['pictures'] = []
                    node['pictures'].extend(label.get('pictures', []))
                    
                    # Speichere Links separat (für spätere DB-Integration)
                    if 'links' not in node:
                        node['links'] = []
                    node['links'].extend(label.get('links', []))
                    
                    applied = True
                else:
                    # Dry run: nur Statistik simulieren
                    if old_label and old_label.strip():
                        stats['labels_updated'] += 1
                    else:
                        stats['labels_applied'] += 1
                    applied = False

                # Statistik-Update
                stats['codes_matched'].add(f"{group_num}:{position}:{code}")
                stats['nodes_labeled'].append({
                    'node_path': node_path,
                    'family': target_family,
                    'group': group_num,
                    'position': position,
                    'extracted_code': node_info.get('extracted_code', code),
                    'old_label': old_label,
                    'new_label': label_text,
                    'pictures': label.get('pictures', []),
                    'links': label.get('links', []),
                    'full_typecode': full_code,
                    'applied': applied,
                    'type': 'relative_group_mapping'
                })

                stats['products_processed'] += 1

                # Markiere (node_path, group, position) als verarbeitet
                # Dadurch können mehrere Mappings auf dieselbe Gruppe angewendet werden
                # (z.B. Position 1 und Position 2)
                # NICHT mehr: seen_node_paths.add(node_path)

    return stats


def find_nodes_by_group_position(
    tree_data: dict,
    target_family: str,
    group_num: int,
    position: int,
    end_position: int,
    target_code: str,
    verbose: bool = False,
    strict: int = 0,
    unique_by_full_code: bool = True
) -> list[dict]:
    """
    Findet alle Knoten, die an einer bestimmten Gruppe-Position einen bestimmten Code haben.
    Liefert pro passendem Leaf-Pfad ein Ergebnis (auch wenn mehrere Leaves unterhalb eines
    Zwischenknotens existieren).
    strict: exact OR startswith + following char is NOT a letter.
    """
    found_nodes = []

    def build_full_codes_to_leaves(start_node: dict, family: str, path_codes: list[str]) -> list[str]:
        """
        Liefert eine Liste von full_typecode-Strings für alle Leaves unter start_node.
        family ist der Family-Teil (z.B. "BCC"), path_codes enthält den bisherigen Pfad (inkl. start_node falls vorhanden).
        """
        results = []

        def recurse(current, codes_acc):
            # Ergänze aktuellen code wenn vorhanden und nicht 'root'
            cur_code = current.get('code', '')
            new_codes = codes_acc + ([cur_code] if cur_code and cur_code != 'root' else [])
            # Wenn Leaf mit full_typecode vorhanden, verwende diese (höchste Priorität)
            if 'full_typecode' in current and current['full_typecode']:
                results.append(current['full_typecode'])
                return
            # Wenn keine Kinder mehr, baue full_typecode aus accumulated codes
            if not current.get('children'):
                # codes_acc kann die Family schon enthalten; wir wollen "FAMILY code1-code2-..."
                # Stelle sicher, dass family an erster Stelle steht
                usable = [c for c in new_codes if c and c != family]
                if usable:
                    results.append(f"{family} {'-'.join(usable)}")
                else:
                    results.append(family)
                return
            # Sonst rekursiv alle Kinder durchlaufen
            for ch in current.get('children', []):
                recurse(ch, new_codes)

        # Starte Rekursion mit den übergebenen path_codes (ohne 'root')
        start_codes = [c for c in path_codes if c and c != 'root']
        recurse(start_node, start_codes)
        return results
    
    def _strict_matches(extracted: str, target: str) -> bool:
        """
        Strict matching mit verbesserter Logik:
        - Exact match: immer True
        - Prefix match: Nur wenn das folgende Zeichen vom Typ wechselt:
          * Bei Buchstaben: Nächstes Zeichen darf kein Buchstabe sein
          * Bei Ziffern: Nächstes Zeichen darf keine Ziffer sein
          * Bei Mischung: Betrachte letztes Zeichen des Targets
        
        Beispiele:
        - "PA" matched "PAF123" NICHT (F ist Buchstabe, PA endet mit Buchstabe)
        - "PA" matched "PA123" JA (1 ist Ziffer, PA endet mit Buchstabe)
        - "1" matched "12" NICHT (2 ist Ziffer, 1 endet mit Ziffer)
        - "1" matched "1A" JA (A ist Buchstabe, 1 endet mit Ziffer)
        - "12" matched "12G" JA (G ist Buchstabe, 12 endet mit Ziffer)
        """
        if not extracted or not target:
            return False
        if extracted == target:
            return True
        if extracted.startswith(target):
            if len(extracted) > len(target):
                next_char = extracted[len(target)]
                last_target_char = target[-1]
                
                # Bestimme Typ des letzten Zeichens im Target
                if last_target_char.isalpha():
                    # Target endet mit Buchstabe → nächstes Zeichen darf kein Buchstabe sein
                    return not next_char.isalpha()
                elif last_target_char.isdigit():
                    # Target endet mit Ziffer → nächstes Zeichen darf keine Ziffer sein
                    return not next_char.isdigit()
                else:
                    # Target endet mit Sonderzeichen → erlauben (konservativ)
                    return True
        return False

    def traverse_node(node: dict, current_family: str = None, path_codes: list[str] = [], depth: int = 0):
        # Familie bestimmen
        if depth == 1 and 'code' in node:
            current_family = node['code']
        elif 'code' in node and current_family is None and len(node.get('code', '')) <= 4:
            current_family = node['code']

        # Aktuelle Codes-Liste erweitern (ohne root)
        current_code = node.get('code', '')
        new_path_codes = path_codes + ([current_code] if current_code else [])
        new_path_codes = [c for c in new_path_codes if c and c != 'root']

        if verbose:
            print(f"Traversing node at depth {depth}, current_family={current_family}, path_codes={new_path_codes}, strict={strict}")

        if current_family == target_family:
            # Wenn Knoten selbst ein full_typecode hat, benutze nur dieses.
            # Ansonsten generiere alle möglichen full_typecodes bis zu den Leaves unter diesem Knoten.
            candidate_full_codes = []
            if 'full_typecode' in node and node.get('full_typecode'):
                candidate_full_codes = [node['full_typecode']]
            else:
                candidate_full_codes = build_full_codes_to_leaves(node, current_family, new_path_codes)

            for full_code in candidate_full_codes:
                parts = full_code.split()
                if len(parts) < 2:
                    # code_without_family = ''
                    code_parts = []
                else:
                    code_without_family = parts[1]
                    code_parts = code_without_family.split('-')

                # Extrahiere Code an der Position
                extracted_code = extract_group_code_at_position(code_parts, group_num, position, end_position)

                # Prüfe Relevanz für Matching
                should_match = False
                if 'full_typecode' in node:
                    should_match = len(code_parts) == group_num
                else:
                    if group_num <= len(code_parts):
                        # Für Zwischenknoten prüfen wir, ob der aktuelle node.code dem Gruppencode entspricht.
                        # Wenn der aktuelle node selbst nicht den Gruppencode darstellt (z.B. tiefere Ebene),
                        # dann ist dieser Zwischenknoten für diese Gruppe nicht relevant.
                        if current_code:
                            group_code = code_parts[group_num - 1]
                            if current_code == group_code:
                                should_match = True
                        else:
                            # Falls current_code leer (z.B. root), lassen wir es nicht matchen
                            should_match = False

                if verbose:
                    print(f"  full_code={full_code}, should_match={should_match}, extracted_code={extracted_code}")
                    
                # Prüfe should_match immer (auch bei leerem target_code)
                if not should_match:
                    continue
                
                # Prüfe extracted_code nur wenn target_code gesetzt ist
                if target_code and not extracted_code:
                    continue
                
                if strict:
                    matched = _strict_matches(extracted_code, target_code)
                else:
                    if not target_code:  # kein Filter → immer matchen
                        matched = True
                    else:
                        matched = (extracted_code == target_code) or extracted_code.startswith(target_code)                    
                    
                if matched:
                    found_nodes.append({
                        'node': node,
                        'path': '/'.join(new_path_codes),
                        'full_code': full_code,
                        'extracted_code': extracted_code,
                        'match_type': 'exact' if extracted_code == target_code else 'prefix'
                    })

        # Rekursiv für alle Children
        if 'children' in node:
            for child in node['children']:
                traverse_node(child, current_family, new_path_codes, depth + 1)

    traverse_node(tree_data)

    if unique_by_full_code:
        deduped = []
        seen = set()
        for entry in found_nodes:
            full_code = entry.get('full_code', '')
            node_id = id(entry.get('node'))
            key = (full_code, node_id)
            if key not in seen:
                seen.add(key)
                deduped.append(entry)
        return deduped

    return found_nodes


# def find_nodes_by_group_position(
#     tree_data: dict,
#     target_family: str,
#     group_num: int,
#     position: int,
#     end_position: int,
#     target_code: str,
#     verbose: bool = False,
#     strict: int = 0
# ) -> list[dict]:
#     """
#     Findet alle Knoten, die an einer bestimmten Gruppe-Position einen bestimmten Code haben.
#     full_code = komplette Hierarchie bis zum Leaf.
#     extracted_code = nur der relevante Teil für Matching.
#     """
#     found_nodes = []

#     def build_full_code_to_leaf(node: dict, family: str, path_codes: list[str]) -> str:
#         """Erzeugt den vollständigen Typcode bis zum Leaf."""
#         codes = path_codes.copy()
#         # Traverse bis zum Leaf
#         current = node
#         while 'children' in current and current['children']:
#             current = current['children'][0]  # Nimm den ersten Child für den Pfad
#             if 'code' in current:
#                 codes.append(current['code'])
#         return f"{family} {'-'.join(codes[1:])}" if len(codes) > 1 else family

#     def traverse_node(node: dict, current_family: str = None, path_codes: list[str] = [], depth: int = 0):
#         # Familie bestimmen
#         if depth == 1 and 'code' in node:
#             current_family = node['code']
#         elif 'code' in node and current_family is None and len(node.get('code', '')) <= 4:
#             current_family = node['code']

#         # Aktuelle Codes-Liste erweitern (ohne root)
#         current_code = node.get('code', '')
#         new_path_codes = path_codes + ([current_code] if current_code else [])
#         new_path_codes = [c for c in new_path_codes if c and c != 'root']
        
#         print(f"Traversing node at depth {depth}, current_family={current_family}, path_codes={new_path_codes}, strict={strict}")

#         if current_family == target_family:
#             # Vollständiger Code bis zum Leaf
#             full_code = node.get('full_typecode') or build_full_code_to_leaf(node, current_family, new_path_codes)

#             # Teile für Matching
#             parts = full_code.split()
#             if len(parts) >= 2:
#                 code_without_family = parts[1]
#                 code_parts = code_without_family.split('-')

#                 # Extrahiere Code an der Position
#                 extracted_code = extract_group_code_at_position(code_parts, group_num, position, end_position)

#                 # Prüfe Relevanz für Matching
#                 should_match = False
#                 if 'full_typecode' in node:
#                     should_match = len(code_parts) == group_num
#                 else:
#                     if group_num <= len(code_parts):
#                         group_code = code_parts[group_num - 1]
#                         if current_code == group_code:
#                             should_match = True

#                 if verbose:
#                     print(f"should_match={should_match}, extracted_code={extracted_code}, full_code={full_code}")

#                 if should_match and extracted_code and (extracted_code == target_code or extracted_code.startswith(target_code)):
#                     found_nodes.append({
#                         'node': node,
#                         'path': '/'.join(new_path_codes),
#                         'full_code': full_code,  # Jetzt bis zum Leaf
#                         'extracted_code': extracted_code,
#                         'match_type': 'exact' if extracted_code == target_code else 'prefix'
#                     })

#         # Rekursiv für alle Children
#         if 'children' in node:
#             for child in node['children']:
#                 traverse_node(child, current_family, new_path_codes, depth + 1)

#     traverse_node(tree_data)
#     return found_nodes

# def find_nodes_by_group_position(
#     tree_data: dict,
#     target_family: str,
#     group_num: int,
#     position: int,
#     end_position: int,
#     target_code: str,
#     verbose: bool = False
# ) -> list[dict]:
#     """
#     Findet alle Knoten, die an einer bestimmten Gruppe-Position einen bestimmten Code haben.

#     Args:
#         tree_data (dict): JSON-Baum-Daten.
#         target_family (str): Ziel-Produktfamilie.
#         group_num (int): Gruppen-Nummer (1-basiert).
#         position (int): Start-Position innerhalb der Gruppe (1-basiert).
#         end_position (int): End-Position innerhalb der Gruppe (-1 für bis Ende).
#         target_code (str): Gesuchter Code.
#         verbose (bool): Wenn True, werden Debug-Infos ausgegeben.

#     Returns:
#         list[dict]: Liste von Dictionaries mit Infos zu gefundenen Knoten:
#             {
#                 'node': node,
#                 'path': path,
#                 'full_code': str,
#                 'extracted_code': str,
#                 'match_type': 'exact' | 'prefix'
#             }
#     """
#     found_nodes = []

#     def traverse_node(node: dict, current_family: str = None, path: str = "", depth: int = 0):
#         # Familie bestimmen
#         if depth == 1 and 'code' in node:
#             current_family = node['code']
#         elif 'code' in node and current_family is None and len(node.get('code', '')) <= 4:
#             current_family = node['code']

#         # Prüfe nur Knoten der Ziel-Familie
#         if current_family == target_family:
#             node_typecode = None

#             if 'full_typecode' in node:
#                 # Leaf-Knoten: Verwende full_typecode direkt
#                 node_typecode = node['full_typecode']
#             elif 'code' in node and current_family and node['code'] != current_family:
#                 # Zwischenknoten: Rekonstruiere typecode aus Pfad
#                 path_parts = [p for p in path.split('/') if p and p != 'root' and p != current_family]
#                 codes_in_path = [current_family] + path_parts  # Familie + Pfadteile
#                 node_typecode = codes_in_path[0] + ' ' + '-'.join(codes_in_path[1:])

#             if node_typecode:
#                 # Extrahiere Code-Teile (ohne Familie)
#                 parts = node_typecode.split()
#                 if len(parts) >= 2:
#                     code_without_family = parts[1]
#                     code_parts = code_without_family.split('-')

#                     current_code = node.get('code', '')
#                     extracted_code = extract_group_code_at_position(code_parts, group_num, position, end_position)

#                     # Prüfe Relevanz des Knotens für die Gruppe
#                     should_match = False
#                     if 'full_typecode' in node:
#                         should_match = len(code_parts) == group_num
#                     else:
#                         if group_num <= len(code_parts):
#                             group_code = code_parts[group_num - 1]
#                             if current_code == group_code:
#                                 should_match = True

#                     if verbose:
#                         print(f"      should_match: {should_match}, extracted_code: {extracted_code}")

#                     # Match prüfen
#                     if should_match and extracted_code and (extracted_code == target_code or extracted_code.startswith(target_code)):
#                         found_nodes.append({
#                             'node': node,
#                             'path': path,
#                             'full_code': node_typecode,
#                             'extracted_code': extracted_code,
#                             'match_type': 'exact' if extracted_code == target_code else 'prefix'
#                         })
#                         if verbose:
#                             print(f"      MATCH! Adding node {path}")

#         # Rekursiv für alle Children
#         if 'children' in node:
#             for child in node['children']:
#                 child_path = f"{path}/{child.get('code', '')}" if path else child.get('code', '')
#                 traverse_node(child, current_family, child_path, depth + 1)

#     traverse_node(tree_data)
#     return found_nodes


# def find_nodes_by_group_position(tree_data, target_family, group_num, position, end_position, target_code, verbose=False):
#     """
#     Findet alle Knoten, die an einer bestimmten Gruppe-Position einen bestimmten Code haben.
    
#     Args:
#         tree_data: JSON-Baum-Daten
#         target_family: Ziel-Produktfamilie
#         group_num: Gruppen-Nummer (1-basiert)
#         position: Start-Position innerhalb der Gruppe (1-basiert)
#         end_position: End-Position innerhalb der Gruppe
#         target_code: Gesuchter Code
        
#     Returns:
#         list: Liste von {'node': node, 'path': path, 'full_code': code} Dictionaries
#     """
#     found_nodes = []
    
#     def traverse_node(node, current_family=None, path="", depth=0):
#         # Update Familie wenn neuer Familien-Knoten gefunden
#         # DYNAMISCH: Wenn wir auf Depth 1 sind und ein 'code' Attribut haben, ist das die Familie
#         if depth == 1 and 'code' in node:
#             current_family = node['code']
#         # FALLBACK: Erkenne bekannte Familien auch auf anderen Ebenen
#         elif 'code' in node and current_family is None and len(node.get('code', '')) <= 4:
#             # Kurze Codes sind wahrscheinlich Familien (BCC, BES, BNI, etc.)
#             current_family = node['code']
        
#         # Prüfe nur Knoten der Ziel-Familie
#         if current_family == target_family:
#             # Prüfe sowohl Leaf-Knoten (mit full_typecode) als auch Zwischenknoten
#             node_typecode = None
            
#             if 'full_typecode' in node:
#                 # Leaf-Knoten: Verwende full_typecode
#                 node_typecode = node['full_typecode']
#             elif 'code' in node and current_family and node['code'] != current_family:
#                 # Zwischenknoten: Rekonstruiere typecode aus Pfad
#                 path_parts = path.split('/')
#                 codes_in_path = [current_family]
                
#                 for part in path_parts:
#                     if part and part != current_family and part != 'root' and part.strip():
#                         codes_in_path.append(part)
                
#                 codes_in_path.append(node['code'])
                
#                 if len(codes_in_path) >= 2:
#                     node_typecode = codes_in_path[0] + ' ' + '-'.join(codes_in_path[1:])
            
#             if node_typecode:
#                 # Extrahiere Code-Teile (ohne Familie)
#                 parts = node_typecode.split()
#                 if len(parts) >= 2:
#                     code_without_family = parts[1]
#                     code_parts = code_without_family.split('-')
                    
#                     # WICHTIG: Prüfe ob dieser Knoten der relevante Knoten für diese Gruppe ist
#                     current_code = node.get('code', '')
                    
#                     # Extrahiere Code an der Position
#                     extracted_code = extract_group_code_at_position(code_parts, group_num, position, end_position)
                    
#                     # NEUE LOGIK: Nur matchen wenn der Knoten in der relevanten Gruppe ist
#                     should_match = False
                    
#                     if 'full_typecode' in node:
#                         # Leaf-Knoten: Nur wenn er tatsächlich in der gesuchten Gruppe ist
#                         # Ein Leaf-Knoten ist in Gruppe N wenn er genau N Code-Teile hat
#                         if len(code_parts) == group_num:
#                             should_match = True
#                     else:
#                         # Zwischenknoten: Prüfe ob der Knoten für diese Gruppe relevant ist
#                         if group_num <= len(code_parts):
#                             group_code = code_parts[group_num - 1]
                            
#                             # Ein Zwischenknoten ist relevant für Gruppe N wenn:
#                             # Er den Code der Gruppe N repräsentiert (sein current_code == group_code)
#                             if current_code == group_code:
#                                 should_match = True
                    
#                     if verbose:
#                         if not 'full_typecode' in node:
#                             expected_group_code = code_parts[group_num - 1] if group_num <= len(code_parts) else 'N/A'
#                             print(f"      Zwischenknoten: current_code '{current_code}' vs expected group_code '{expected_group_code}'")
#                         print(f"      should_match: {should_match}")
                    
#                     # Match-Prüfung nur wenn der Knoten relevant ist UND extracted_code nicht leer
#                     # KORRIGIERT: extracted_code muss mit target_code beginnen (nicht umgekehrt)
#                     if should_match and extracted_code and (extracted_code == target_code or extracted_code.startswith(target_code)):
#                         found_nodes.append({
#                             'node': node,
#                             'path': path,
#                             'full_code': node_typecode,
#                             'extracted_code': extracted_code,
#                             'match_type': 'exact' if extracted_code == target_code else 'prefix'
#                         })
#                         if verbose:
#                             print(f"      MATCH! ({extracted_code == target_code and 'exact' or 'prefix'})")
#                             print(f"      Adding node {path} to results")
        
#         # Rekursiv für alle Children
#         if 'children' in node:
#             for child in node['children']:
#                 child_path = f"{path}/{child.get('code', '')}" if path else child.get('code', '')
#                 traverse_node(child, current_family, child_path, depth + 1)
    
#     # Starte Traversierung
#     traverse_node(tree_data)
#     return found_nodes


def apply_name_mappings(tree_data, matching_products, name_mappings, target_family, dry_run=False):
    """
    Wendet Name-Mappings auf Knoten basierend auf ihrer Ebene im Baum an.
    KORRIGIERT: Respektiert jetzt die Filter und wendet Namen nur auf gefilterte Produktbäume an.
    
    Args:
        tree_data: JSON-Baum-Daten (werden modifiziert)
        matching_products: Liste der gefundenen Produkte (wird für Filterung verwendet!)
        name_mappings: Liste von Name-Mapping-Objekten
        target_family: Ziel-Produktfamilie (z.B. "BCC")
        dry_run: Wenn True, werden keine Änderungen gemacht
        
    Returns:
        dict: Statistiken über angewendete Namen
    """
    stats = {
        'names_applied': 0,
        'names_updated': 0,
        'levels_processed': set(),
        'nodes_named': []
    }
    
    if not name_mappings:
        return stats

    # Erstelle Set der passenden Produkt-Codes für Filterung
    matching_product_codes = set()
    for product in matching_products:
        if isinstance(product, dict) and 'full_typecode' in product:
            matching_product_codes.add(product['full_typecode'])
        elif isinstance(product, str):
            matching_product_codes.add(product)

    # Für jedes Name-Mapping, finde alle Knoten auf dieser Ebene
    for mapping in name_mappings:
        level = mapping.get('level')
        name = mapping.get('name', '')
        
        if level is None or not name:
            continue
            
        stats['levels_processed'].add(level)
        
        # Finde alle Knoten der Familie auf dieser Ebene, die zu gefilterten Produkten gehören
        def find_and_name_nodes(node, current_family=None, path="", current_level=0, depth=0):
            nodes_named = 0
            
            # Update Familie und Level wenn neuer Familien-Knoten gefunden
            # DYNAMISCH: Wenn wir auf Depth 1 sind und ein 'code' Attribut haben, ist das die Familie
            if depth == 1 and 'code' in node:
                current_family = node['code']
                current_level = 1  # Familie ist Level 1
            # FALLBACK: Erkenne bekannte Familien auch auf anderen Ebenen
            elif 'code' in node and current_family is None and len(node.get('code', '')) <= 4:
                # Kurze Codes sind wahrscheinlich Familien
                current_family = node['code']
                current_level = 1
            elif 'pattern' in node:
                # Pattern-Knoten erhöhen Level nicht
                pass
            else:
                # Normale Code-Knoten erhöhen Level
                current_level += 1
            
            # Wenn wir in der richtigen Familie sind und das richtige Level haben
            if (current_family == target_family and current_level == level):
                
                # WICHTIG: Prüfe ob dieser Knoten zu den gefilterten Produkten gehört
                should_apply_name = False
                
                # Wenn der Knoten einen full_typecode hat, prüfe direkt
                if 'full_typecode' in node and node['full_typecode'] in matching_product_codes:
                    should_apply_name = True
                # Wenn nicht, prüfe ob er Nachkommen hat, die zu gefilterten Produkten gehören
                elif has_matching_descendants(node, matching_product_codes):
                    should_apply_name = True
                
                if should_apply_name:
                    # Namen anwenden
                    if not dry_run:
                        old_name = node.get('name', '')
                        
                        if old_name and old_name.strip():
                            node['name'] = name
                            stats['names_updated'] += 1
                        else:
                            node['name'] = name
                            stats['names_applied'] += 1
                    else:
                        # Dry-Run: Statistik trotzdem berechnen
                        old_name = node.get('name', '')
                        
                        if old_name and old_name.strip():
                            stats['names_updated'] += 1
                        else:
                            stats['names_applied'] += 1
                    
                    # Statistik
                    stats['nodes_named'].append({
                        'node_path': path,
                        'level': level,
                        'family': target_family,
                        'old_name': node.get('name', ''),
                        'new_name': name,
                        'applied': not dry_run,
                        'type': 'name'
                    })
                    
                    nodes_named += 1
            
            # Rekursiv durch Children
            if 'children' in node:
                for child in node['children']:
                    child_path = f"{path}/{child.get('code', '')}" if path else child.get('code', '')
                    nodes_named += find_and_name_nodes(child, current_family, child_path, current_level, depth + 1)
                    
            return nodes_named
        
        def has_matching_descendants(node, matching_codes):
            """Prüft ob ein Knoten Nachkommen hat, die zu den gefilterten Produkten gehören"""
            if 'full_typecode' in node and node['full_typecode'] in matching_codes:
                return True
            
            if 'children' in node:
                for child in node['children']:
                    if has_matching_descendants(child, matching_codes):
                        return True
            
            return False
        
        # Finde und benenne alle passenden Knoten
        find_and_name_nodes(tree_data, depth=0)
    
    return stats


def apply_labels_to_tree(tree_data, matching_products, code_lookup, group_lookup, target_family, dry_run=False):
    """
    Wendet Labels auf die gefundenen Produkte im Baum an.
    
    Args:
        tree_data: JSON-Baum-Daten (werden modifiziert)
        matching_products: Liste der gefundenen Produkte
        code_lookup: Code → Label Lookup-Tabelle
        group_lookup: Code → Group Lookup-Tabelle
        target_family: Ziel-Produktfamilie (z.B. "A", "B", "BCC")
        dry_run: Wenn True, werden keine Änderungen gemacht
        
    Returns:
        dict: Statistiken über angewendete Labels
    """
    stats = {
        'products_processed': 0,
        'labels_applied': 0,
        'labels_updated': 0,
        'groups_applied': 0,
        'groups_updated': 0,
        'positions_processed': set(),
        'codes_matched': set(),
        'products_with_labels': [],
        'nodes_labeled': []
    }
    
    # Für jede Position und jeden Code in den Mappings,
    # finde alle entsprechenden Knoten im Baum der angegebenen Familie
    for position, code_map in code_lookup.items():
        stats['positions_processed'].add(position)
        
        for code, label_data in code_map.items():
            # Finde alle Knoten mit dieser Position und diesem Code in der Ziel-Familie
            target_nodes = find_node_at_position(tree_data, target_family, position, code)
            
            for node_info in target_nodes:
                node = node_info['node']
                node_path = node_info['path']
                
                # Extract labels basierend auf neuer Datenstruktur
                if isinstance(label_data, dict):
                    # Neue Struktur mit separaten deutsch/englisch Labels
                    label_de = label_data.get('label', '')
                    label_en = label_data.get('label-en', '')
                else:
                    # Rückwärts-Kompatibilität: alte Struktur nur mit deutschen Labels
                    label_de = label_data
                    label_en = ''
                
                # Anwenden der Labels (falls nicht dry-run)
                if not dry_run:
                    # Verwende vorhandene label/label-en Felder
                    old_label = node.get('label', '')
                    old_label_en = node.get('label-en', '')
                    
                    # Setze deutsche Labels (anhängen falls vorhanden)
                    if label_de:
                        if old_label and old_label.strip():
                            # print("sidvsdvubsdiuvsidvbsdbvshdbvshdbvsjvbhsdhvbsdhvbjshdvbhsdvjhfvb")
                            # Anhängen mit doppeltem Line Feed
                            node['label'] = old_label + '\n\n' + label_de
                            stats['labels_updated'] += 1
                        else:
                            # print("sidvsdvubsdiuvsidvbsdbvshdbvshdbvsjvbhsdhvbsdhvbjshdvbhsdvjhfvb")
                            # Neues Label setzen
                            node['label'] = label_de
                            stats['labels_applied'] += 1
                    
                    # Setze englische Labels (anhängen falls vorhanden)
                    if label_en:
                        if old_label_en and old_label_en.strip():
                            # Anhängen mit doppeltem Line Feed  
                            node['label-en'] = old_label_en + '\n\n' + label_en
                            stats['labels_updated'] += 1
                        else:
                            # Neues Label setzen
                            node['label-en'] = label_en
                            stats['labels_applied'] += 1
                else:
                    # Dry-Run: Statistik trotzdem berechnen
                    old_label = node.get('label', '')
                    old_label_en = node.get('label-en', '')
                    
                    if label_de:
                        if old_label and old_label.strip():
                            stats['labels_updated'] += 1
                        else:
                            stats['labels_applied'] += 1
                    
                    if label_en:
                        if old_label_en and old_label_en.strip():
                            stats['labels_updated'] += 1
                        else:
                            stats['labels_applied'] += 1
                
                # Statistik
                stats['codes_matched'].add(f"{position}:{code}")
                
                # Bestimme Match-Typ
                match_type = node_info.get('match_type', 'unknown')
                full_code = node_info.get('full_code', node.get('code', ''))
                
                stats['nodes_labeled'].append({
                    'node_path': node_path,
                    'family': target_family,
                    'position': position,
                    'code': code,
                    'node_code': node.get('code', ''),  # Der tatsächliche Node-Code
                    'old_label': node.get('label', ''),
                    'old_label_en': node.get('label-en', ''),
                    'new_label': label_de,
                    'new_label_en': label_en,
                    'full_typecode': node.get('full_typecode', ''),
                    'full_code': full_code,
                    'match_type': match_type,
                    'applied': not dry_run,
                    'type': 'label'
                })
    
    # Für jede Position und jeden Code in den Group-Mappings
    for position, code_map in group_lookup.items():
        stats['positions_processed'].add(position)
        
        for code, group in code_map.items():
            # Finde alle Knoten mit dieser Position und diesem Code in der Ziel-Familie
            target_nodes = find_node_at_position(tree_data, target_family, position, code)
            
            for node_info in target_nodes:
                node = node_info['node']
                node_path = node_info['path']
                
                # Anwenden der Group (falls nicht dry-run)
                if not dry_run:
                    # Verwende vorhandenes group Feld
                    old_group = node.get('group', '')
                    
                    # Setze die Group
                    node['group'] = group
                    
                    if old_group != group:
                        if old_group:
                            stats['groups_updated'] += 1
                        else:
                            stats['groups_applied'] += 1
                
                # Statistik
                stats['codes_matched'].add(f"{position}:{code}")
                stats['nodes_labeled'].append({
                    'node_path': node_path,
                    'family': target_family,
                    'position': position,
                    'code': code,
                    'old_group': node.get('group', ''),
                    'new_group': group,
                    'full_typecode': node.get('full_typecode', ''),
                    'applied': not dry_run,
                    'type': 'group'
                })
    
    # Erstelle Produkt-Liste für Anzeige basierend auf gefundenen Labels
    stats['products_processed'] = len(matching_products)
    for product in matching_products:
        labels_for_product = {}
        full_typecode = product['full_typecode']
        
        # Prüfe ob das Produkt Labels erhält
        for node_info in stats['nodes_labeled']:
            if node_info['full_typecode'] == full_typecode or full_typecode.startswith(node_info['full_typecode']):
                position = node_info['position'] 
                key = f'position_{position}_{node_info["type"]}'
                
                # Extrahiere den tatsächlichen Code des Produkts an dieser Position
                product_code_at_position = "?"
                try:
                    # Verwende den vollständigen Typecode OHNE Familie-Entfernung
                    if position <= len(full_typecode):
                        product_code_at_position = full_typecode[position-1]  # 1-basierte Position
                except:
                    product_code_at_position = node_info.get('node_code', node_info['code'])
                
                # Nur hinzufügen wenn der Mapping-Code mit dem Produktcode übereinstimmt
                # oder wenn es ein Substring-Match ist (für multi-character codes)
                mapping_code = node_info['code']
                if (len(mapping_code) == 1 and product_code_at_position == mapping_code) or \
                   (len(mapping_code) > 1 and product_code_at_position.startswith(mapping_code)):
                
                    if node_info['type'] == 'label':
                        labels_for_product[key] = {
                            'code': product_code_at_position,
                            'mapping_code': mapping_code,
                            'label': node_info['new_label'],
                            'position': position,
                            'type': 'label'
                        }
                    elif node_info['type'] == 'group':
                        labels_for_product[key] = {
                            'code': product_code_at_position,
                            'mapping_code': mapping_code,
                            'group': node_info['new_group'],
                            'position': position,
                            'type': 'group'
                        }
        
        if labels_for_product:
            stats['products_with_labels'].append({
                'full_typecode': full_typecode,
                'code_path': product['code_path'],
                'labels': labels_for_product
            })
    print( f"Angewendete Labels auf {stats['products_processed']} Produkte in Familie '{target_family}'." )
    # Die genauen Produkte:
    print( f"Produkte mit angewendeten Labels: {[p['full_typecode'] for p in stats['products_with_labels']]}" )
    # Die genauen Knoten:
    print( f"Knoten mit angewendeten Labels/Groups: {[n['node_path'] for n in stats['nodes_labeled']]}" )
    
    return stats


def print_mapping_summary(mapping_data):
    """Druckt eine Zusammenfassung der Mapping-Daten."""
    filter_criteria = mapping_data.get('filter_criteria', {})
    code_mappings = mapping_data.get('code_mappings', [])
    group_mappings = mapping_data.get('group_mappings', [])
    metadata = mapping_data.get('metadata', {})
    
    print("=== LABEL-MAPPING KONFIGURATION ===")
    
    # Metadata
    if metadata:
        if 'description' in metadata:
            print(f"Beschreibung: {metadata['description']}")
        if 'version' in metadata:
            print(f"Version: {metadata['version']}")
        if 'created' in metadata:
            print(f"Erstellt: {metadata['created']}")
        print()
    
    # Filter-Kriterien
    print("FILTER-KRITERIEN:")
    for key, value in filter_criteria.items():
        print(f"  {key}: {value}")
    print()
    
    # Code-Mappings
    print("CODE-MAPPINGS:")
    for i, mapping in enumerate(code_mappings, 1):
        position = mapping.get('position', '?')
        codes = mapping.get('codes', [])
        labels = mapping.get('labels', [])
        labels_en = mapping.get('labels-en', [])
        
        has_english = len(labels_en) > 0 and any(label.strip() for label in labels_en)
        
        print(f"  {i}. Position {position}:")
        print(f"     Codes: {len(codes)} ({', '.join(codes[:3])}{'...' if len(codes) > 3 else ''})")
        print(f"     Labels (DE): {len(labels)} Einträge")
        if has_english:
            print(f"     Labels (EN): {len(labels_en)} Einträge")
        
        if labels and len(labels) > 0:
            # Zeige ersten deutschen Label gekürzt
            first_label_raw = labels[0]
            # Parse Label (kann String oder Objekt sein)
            first_label_obj = parse_label(first_label_raw)
            first_label_text = label_to_string(first_label_obj)
            first_label = first_label_text[:100] + "..." if len(first_label_text) > 100 else first_label_text
            first_label_lines = first_label.split('\n')[:2]
            print(f"     Beispiel (DE): {first_label_lines[0]}")
            if len(first_label_lines) > 1:
                print(f"                    {first_label_lines[1]}")
        
        if has_english and labels_en and len(labels_en) > 0:
            # Zeige ersten englischen Label gekürzt
            first_label_en_raw = labels_en[0]
            # Parse Label (kann String oder Objekt sein)
            first_label_en_obj = parse_label(first_label_en_raw)
            first_label_en_text = label_to_string(first_label_en_obj)
            first_label_en = first_label_en_text[:100] + "..." if len(first_label_en_text) > 100 else first_label_en_text
            first_label_en_lines = first_label_en.split('\n')[:2]
            print(f"     Beispiel (EN): {first_label_en_lines[0]}")
            if len(first_label_en_lines) > 1:
                print(f"                    {first_label_en_lines[1]}")
        print()
    
    # Group-Mappings (unterscheide neue und alte)
    if group_mappings:
        relative_mappings = [m for m in group_mappings if 'group' in m and 'labels' in m]
        absolute_mappings = [m for m in group_mappings if 'position' in m and 'groups' in m]
        
        if relative_mappings:
            print("RELATIVE GROUP-MAPPINGS (fuer Labels):")
            for i, mapping in enumerate(relative_mappings, 1):
                group = mapping.get('group', '?')
                position = mapping.get('position', '?')
                end_position = mapping.get('end_position')
                codes = mapping.get('codes', [])
                labels = mapping.get('labels', [])
                
                pos_str = f"{position}" if not end_position or end_position == position else f"{position}-{end_position}"
                print(f"  {i}. Gruppe {group}, Position {pos_str}:")
                print(f"     Codes: {len(codes)} ({', '.join(codes[:3])}{'...' if len(codes) > 3 else ''})")
                print(f"     Labels: {len(labels)} Einträge")
                if labels and len(labels) > 0:
                    # Zeige ersten Label gekürzt
                    first_label_raw = labels[0]
                    # Parse Label (kann String oder Objekt sein)
                    first_label_obj = parse_label(first_label_raw)
                    first_label_text = label_to_string(first_label_obj)
                    first_label = first_label_text[:100] + "..." if len(first_label_text) > 100 else first_label_text
                    first_label_lines = first_label.split('\n')[:2]
                    print(f"     Beispiel: {first_label_lines[0]}")
                    if len(first_label_lines) > 1:
                        print(f"               {first_label_lines[1]}")
                print()
        
        if absolute_mappings:
            print("ABSOLUTE GROUP-MAPPINGS (deprecated, fuer group-Attribut):")
            for i, mapping in enumerate(absolute_mappings, 1):
                position = mapping.get('position', '?')
                codes = mapping.get('codes', [])
                groups = mapping.get('groups', [])
                
                print(f"  {i}. Position {position}:")
                print(f"     Codes: {len(codes)} ({', '.join(codes[:3])}{'...' if len(codes) > 3 else ''})")
                print(f"     Groups: {len(groups)} Einträge")
                if groups and len(groups) > 0:
                    # Zeige ersten Group gekürzt
                    first_group = groups[0][:50] + "..." if len(groups[0]) > 50 else groups[0]
                    print(f"     Beispiel: {first_group}")
                print()
    
    # Global Group-Mappings
    global_group_mappings = mapping_data.get('global_group_mappings', [])
    if global_group_mappings:
        print("GLOBAL GROUP-MAPPINGS:")
        for i, mapping in enumerate(global_group_mappings, 1):
            group = mapping.get('group', '?')
            description = mapping.get('description', 'Keine Beschreibung')
            
            print(f"  {i}. Group: {group}")
            print(f"     Beschreibung: {description}")
            print(f"     Anwendung: Alle gefilterten Produkte")
            print()
    
    # Name-Mappings
    name_mappings = mapping_data.get('name_mappings', [])
    if name_mappings:
        print("NAME-MAPPINGS:")
        for i, mapping in enumerate(name_mappings, 1):
            level = mapping.get('level', '?')
            name = mapping.get('name', '')
            
            print(f"  {i}. Level {level}:")
            print(f"     Name: {name}")
            print(f"     Anwendung: Alle Knoten auf Ebene {level}")
            print()
    
    # Special-Mappings
    special_mappings = mapping_data.get('special_mappings', [])
    if special_mappings:
        print("SPECIAL-MAPPINGS:")
        for i, mapping in enumerate(special_mappings, 1):
            group = mapping.get('group', '?')
            position = mapping.get('position', 'entire group')
            allowed = mapping.get('allowed', '')
            labels_raw = mapping.get('labels', [])
            
            print(f"  {i}. Gruppe {group}, Position {position}:")
            if allowed:
                print(f"     Allowed: {allowed}")
            print(f"     Labels: {len(labels_raw)} Einträge")
            if labels_raw and len(labels_raw) > 0:
                first_label_obj = parse_label(labels_raw[0])
                first_label_text = label_to_string(first_label_obj)
                print(f"     Beispiel: {first_label_text[:80]}...")
                if first_label_obj.get('pictures'):
                    print(f"     Bilder: {len(first_label_obj['pictures'])}")
            print()
    
    # General-Mappings
    general_mappings = mapping_data.get('general_mappings', [])
    if general_mappings:
        print("GENERAL-MAPPINGS:")
        for i, mapping in enumerate(general_mappings, 1):
            codes = mapping.get('codes', [])
            labels_raw = mapping.get('labels', [])
            strict = mapping.get('strict', False)
            
            print(f"  {i}. Codes: {len(codes)} ({', '.join(codes[:3])}{'...' if len(codes) > 3 else ''})")
            print(f"     Labels: {len(labels_raw)} Einträge")
            if strict:
                print(f"     Strict Mode: {strict}")
            if labels_raw and len(labels_raw) > 0:
                first_label_obj = parse_label(labels_raw[0])
                first_label_text = label_to_string(first_label_obj)
                print(f"     Beispiel: {first_label_text[:80]}...")
                if first_label_obj.get('pictures'):
                    print(f"     Bilder: {len(first_label_obj['pictures'])}")
            print()


def print_application_results(stats, dry_run=False):
    """Druckt die Ergebnisse der Label-Anwendung."""
    action = "VORSCHAU" if dry_run else "ANGEWENDET"
    print(f"=== LABELS {action} ===")
    
    print(f"Verarbeitete Produkte: {stats['products_processed']}")
    print(f"Produkte mit Labels: {len(stats['products_with_labels'])}")
    
    if dry_run:
        print(f"Labels würden hinzugefügt werden: {stats['labels_applied']}")
        print(f"Labels würden aktualisiert werden: {stats['labels_updated']}")
        print(f"Groups würden hinzugefügt werden: {stats['groups_applied']}")
        print(f"Groups würden aktualisiert werden: {stats['groups_updated']}")
        if 'global_groups_applied' in stats:
            print(f"Globale Groups würden hinzugefügt werden: {stats['global_groups_applied']}")
            print(f"Globale Groups würden aktualisiert werden: {stats['global_groups_updated']}")
        if 'names_applied' in stats:
            print(f"Namen würden hinzugefügt werden: {stats['names_applied']}")
            print(f"Namen würden aktualisiert werden: {stats['names_updated']}")
    else:
        print(f"Labels hinzugefügt: {stats['labels_applied']}")
        print(f"Labels aktualisiert: {stats['labels_updated']}")
        print(f"Groups hinzugefügt: {stats['groups_applied']}")
        print(f"Groups aktualisiert: {stats['groups_updated']}")
        if 'global_groups_applied' in stats:
            print(f"Globale Groups hinzugefügt: {stats['global_groups_applied']}")
            print(f"Globale Groups aktualisiert: {stats['global_groups_updated']}")
        if 'names_applied' in stats:
            print(f"Namen hinzugefügt: {stats['names_applied']}")
            print(f"Namen aktualisiert: {stats['names_updated']}")
    
    print(f"Verarbeitete Positionen: {len(stats['positions_processed'])}")
    print(f"Gematchte Codes: {len(stats['codes_matched'])}")
    print(f"Gelabelte Knoten: {len(stats.get('nodes_labeled', []))}")
    print()
    
    # Zeige gelabelte Knoten (die tatsächlichen Labels im Baum)
    if 'nodes_labeled' in stats and stats['nodes_labeled']:
        print("GELABELTE KNOTEN IM BAUM:")
        unique_nodes = {}
        for node_info in stats['nodes_labeled']:
            # Handhabe verschiedene Mapping-Typen
            if node_info.get('type') == 'relative_group_mapping':
                # Neue relative group mappings
                key = (node_info['family'], f"G{node_info['group']}P{node_info['position']}", node_info['extracted_code'], node_info['type'])
            elif node_info.get('type') == 'general':
                # General mappings (position-unabhängig)
                key = (node_info['family'], 'GENERAL', node_info['code'], node_info['type'])
            else:
                # Alte code/group mappings
                key = (node_info['family'], node_info.get('position', 'N/A'), node_info['code'], node_info.get('type', 'label'))
            
            if key not in unique_nodes:
                unique_nodes[key] = node_info
        
        # Begrenze auf maximal 50 Beispiele
        max_examples = 50
        total_count = len(unique_nodes)
        
        for i, (key, node_info) in enumerate(unique_nodes.items(), 1):
            if i > max_examples:
                break
                
            family, position_str, code, mapping_type = key
            match_type = node_info.get('match_type', 'unknown')
            match_indicator = {
                'explicit_position': 'ZIEL',   # Explizites position-Attribut
                'position_based': 'POS',      # Position-basiertes Matching (NEUE METHODE)
                'exact': 'ZIEL',              # Exakter Match
                'prefix': 'SUCH',             # Prefix Match
                'unknown': 'FRAGE'
            }.get(match_type, 'FRAGE')
            
            if mapping_type == 'relative_group_mapping':
                print(f"  {i}. {family} {position_str}: '{code}' (relative group) {match_indicator}")
            elif mapping_type == 'general':
                print(f"  {i}. {family} GENERAL: '{code}' (position-unabhängig)")
            else:
                print(f"  {i}. {family} Position {position_str}: '{code}' ({mapping_type}) {match_indicator}")
            
            if node_info.get('full_code'):
                print(f"     Node-Code: {node_info['full_code']}")
            if node_info['full_typecode']:
                print(f"     Beispiel-Produkt: {node_info['full_typecode']}")
            print(f"     Knoten-Pfad: {node_info['node_path']}")
            
            if mapping_type in ['label', 'relative_group_mapping']:
                label_preview = node_info['new_label'][:80] + "..." if len(node_info['new_label']) > 80 else node_info['new_label']
                print(f"     Label (DE): {label_preview.split(chr(10))[0]}")  # Erste Zeile
                
                if node_info.get('new_label_en'):
                    label_en_preview = node_info['new_label_en'][:80] + "..." if len(node_info['new_label_en']) > 80 else node_info['new_label_en']
                    print(f"     Label (EN): {label_en_preview.split(chr(10))[0]}")
                
                if len(unique_nodes) <= 5:  # Zeige Details nur bei wenigen Knoten
                    if node_info.get('old_label'):
                        print(f"     (Ersetzt vorheriges deutsches Label)")
                    else:
                        print(f"     (Neues deutsches Label)")
                    
                    if node_info.get('new_label_en'):
                        if node_info.get('old_label_en'):
                            print(f"     (Ersetzt vorheriges englisches Label)")
                        else:
                            print(f"     (Neues englisches Label)")
                            
            elif mapping_type == 'group':
                group_preview = node_info['new_group'][:50] + "..." if len(node_info['new_group']) > 50 else node_info['new_group']
                print(f"     Group: {group_preview}")
                if len(unique_nodes) <= 5:  # Zeige Details nur bei wenigen Knoten
                    if node_info.get('old_group'):
                        print(f"     (Ersetzt vorherige Group)")
                    else:
                        print(f"     (Neue Group)")
            print()
        
        if total_count > max_examples:
            print(f"     ... und {total_count - max_examples} weitere Knoten")
    
    # Zeige Beispiel-Produkte
    if stats['products_with_labels']:
        print("BEISPIELE DER BETROFFENEN PRODUKTE:")
        max_product_examples = 50
        total_products = len(stats['products_with_labels'])
        
        for i, product in enumerate(stats['products_with_labels'][:max_product_examples], 1):
            print(f"  {i}. {product['full_typecode']}")
            for label_key, label_info in product['labels'].items():
                pos = label_info['position']
                code = label_info['code']
                mapping_type = label_info['type']
                if mapping_type == 'label':
                    print(f"     Position {pos} (Produkt: {code}, via Mapping: {label_info['mapping_code']}) wird gelabelt")
                elif mapping_type == 'group':
                    print(f"     → Position {pos} (Produkt: {code}, via Mapping: {label_info['mapping_code']}) bekommt Group '{label_info['group']}'")
            print()
        
        if total_products > max_product_examples:
            print(f"     ... und {total_products - max_product_examples} weitere Produkte")


def create_backup(file_path):
    """Erstellt ein Backup der JSON-Datei."""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"📁 Backup erstellt: {backup_path}")
    return backup_path


def validate_saved_file(file_path):
    """
    Schnelle Validierung einer gespeicherten JSON-Datei.
    
    Args:
        file_path: Pfad zur JSON-Datei
        
    Returns:
        bool: True wenn gültig, False bei Problemen
    """
    try:
        # Grundlegende JSON-Syntax prüfen
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Grundstruktur prüfen
        if not isinstance(data, dict) or "children" not in data:
            return False
        
        # Stichproben-Test: Prüfe ob mindestens ein Knoten die erwartete Struktur hat
        def check_sample_node(node, depth=0):
            if depth > 3:  # Nicht zu tief gehen
                return True
                
            if not isinstance(node, dict):
                return False
                
            if "children" not in node:
                return False
                
            # Prüfe ein paar Kinder stichprobenartig
            children = node.get("children", [])
            if children and len(children) > 0:
                return check_sample_node(children[0], depth + 1)
            
            return True
        
        return check_sample_node(data)
        
    except Exception:
        return False


def apply_global_group_mappings(tree_data, matching_products, global_group_mappings, target_family, dry_run=False):
    """
    Wendet globale Group-Mappings auf alle Produkte an, die das Filter-Kriterium erfüllen.
    
    Args:
        tree_data: JSON-Baum-Daten
        matching_products: Liste der gefilterten Produkte
        global_group_mappings: Liste von globalen Group-Mapping-Objekten
        target_family: Ziel-Produktfamilie
        dry_run: Ob es ein Dry-Run ist
        
    Returns:
        dict: Statistiken über angewendete globale Groups
    """
    stats = {
        'global_groups_applied': 0,
        'global_groups_updated': 0,
        'nodes_with_global_groups': [],
        'products_processed': len(matching_products)
    }
    
    if not global_group_mappings:
        return stats
    
    # Erstelle Set der passenden Produkt-Codes für schnelle Suche
    matching_product_codes = set()
    for product in matching_products:
        if isinstance(product, dict) and 'full_typecode' in product:
            matching_product_codes.add(product['full_typecode'])
        elif isinstance(product, str):
            matching_product_codes.add(product)
    
    def apply_global_groups_recursive(node, current_family=None, path="", depth=0):
        # Update Familie - DYNAMISCH: Verwende depth 1 Check
        if depth == 1 and 'code' in node:
            current_family = node['code']
        
        # Prüfe ob dieser Knoten zu einem passenden Produkt gehört
        if (current_family == target_family and 
            'full_typecode' in node and 
            node['full_typecode'] in matching_product_codes):
            
            # Wende alle globalen Group-Mappings an
            for global_mapping in global_group_mappings:
                global_group = global_mapping.get('group', '')
                append_mode = global_mapping.get('append', False)
                description = global_mapping.get('description', '')
                
                if global_group:
                    old_group = node.get('group', '')
                    
                    # Anwenden der globalen Group
                    if not dry_run:
                        if append_mode and old_group:
                            # Hänge an bestehende Group an
                            node['group'] = f"{old_group} {global_group}"
                            stats['global_groups_updated'] += 1
                        else:
                            # Setze globale Group
                            node['group'] = global_group
                            if old_group != global_group:
                                if old_group:
                                    stats['global_groups_updated'] += 1
                                else:
                                    stats['global_groups_applied'] += 1
                    
                    # Statistik
                    stats['nodes_with_global_groups'].append({
                        'node_path': path,
                        'family': current_family,
                        'full_typecode': node.get('full_typecode', ''),
                        'old_group': old_group,
                        'new_group': global_group,
                        'description': description,
                        'applied': not dry_run
                    })
        
        # Rekursiv durch Children
        if 'children' in node:
            for i, child in enumerate(node['children']):
                child_path = f"{path}/children[{i}]" if path else f"children[{i}]"
                apply_global_groups_recursive(child, current_family, child_path, depth + 1)
    
    # Starte Anwendung
    apply_global_groups_recursive(tree_data)
    return stats


def apply_general_mappings(tree_data, matching_products, general_mappings, target_family, dry_run=False, verbose=False):
    """
    Wendet General-Mappings an - Labels für Codes die ÜBERALL im Typcode vorkommen können.
    Im Gegensatz zu code_mappings benötigen general_mappings keine Positions-Angabe.

    Args:
        tree_data: JSON-Baum-Daten
        matching_products: Liste der gefilterten Produkte
        general_mappings: Liste von General-Mapping-Objekten mit 'codes' und 'labels'
        target_family: Ziel-Produktfamilie
        dry_run: Ob es ein Dry-Run ist
        verbose: Zeige detaillierte Ausgaben

    Format von general_mappings:
        [
            {
                "codes": ["M313", "M423", "S4"],
                "labels": ["Motor 313kW", "Motor 423kW", "Stecker S4"]
            }
        ]

    Returns:
        dict: Statistiken über angewendete General-Mappings
    """
    stats = {
        'labels_applied': 0,
        'labels_updated': 0,
        'nodes_labeled': [],
        'codes_matched': set(),
        'products_processed': len(matching_products)
    }

    if not general_mappings:
        return stats

    # Baue Code-zu-Label Lookup
    # Jetzt: code_to_label[code] = {'label': label_obj, 'strict': bool}
    code_to_label = {}
    for mapping in general_mappings:
        codes = mapping.get('codes', [])
        labels_raw = mapping.get('labels', [])
        strict_mode = mapping.get('strict', False)

        # Validierung
        if len(codes) != len(labels_raw):
            print(f"⚠️ Warnung: General-Mapping hat ungleiche Anzahl von Codes ({len(codes)}) und Labels ({len(labels_raw)})")
            continue

        # Parse labels (unterstützt String und erweiterte Objekte)
        labels = [parse_label(l) for l in labels_raw]

        for code, label in zip(codes, labels):
            # Überschreiben erlaubt; letzter Eintrag gewinnt
            code_to_label[code] = {'label': label, 'strict': bool(strict_mode)}

    if not code_to_label:
        return stats

    if verbose:
        print(f"  General-Mappings für {len(code_to_label)} Codes")

    # Erstelle Set der passenden Produkt-Codes
    matching_product_codes = set()
    for product in matching_products:
        if isinstance(product, dict) and 'full_typecode' in product:
            matching_product_codes.add(product['full_typecode'])
        elif isinstance(product, str):
            matching_product_codes.add(product)

    def _matches_with_strict_rule(node_code: str, mapping_code: str, strict_flag: bool) -> bool:
        """
        Prüft, ob node_code zum mapping_code passt.
        - Non-strict: exact oder startswith
        - Strict: exact oder startswith + folgendes Zeichen ist kein Buchstabe
        """
        if not node_code or not mapping_code:
            return False
        if node_code == mapping_code:
            return True
        if node_code.startswith(mapping_code):
            if not strict_flag:
                return True
            # strict: nur wenn folgendes Zeichen kein Buchstabe ist
            if len(node_code) > len(mapping_code):
                next_char = node_code[len(mapping_code)]
                return not next_char.isalpha()
        return False

    def apply_general_labels_recursive(node, current_family=None, path="", depth=0):
        """Rekursive Hilfsfunktion zum Anwenden von General-Labels."""
        # Update Familie
        if depth == 1 and 'code' in node:
            current_family = node['code']

        # Prüfe ob dieser Knoten zur Zielfamilie gehört und einen Code hat
        code = node.get('code', '')

        if (current_family == target_family and
            code and
            not code.startswith('pattern_')):

            # Prüfe ob dieser Knoten zu einem gefilterten Produkt gehört
            # Entweder direkt (wenn es ein Produkt ist) oder als Teil des Pfads
            should_apply = False

            if 'full_typecode' in node and node['full_typecode'] in matching_product_codes:
                should_apply = True
            elif has_matching_descendants(node, matching_product_codes):
                should_apply = True

            if should_apply:
                # Prüfe ob der Code in unseren General-Mappings ist (mit strict-Berücksichtigung)
                # Wir müssen alle mapping-codes prüfen, weil strict und prefix-Match relevant sind
                for mapping_code, meta in code_to_label.items():
                    label = meta['label']
                    strict_flag = meta['strict']

                    if _matches_with_strict_rule(code, mapping_code, strict_flag):
                        old_label = node.get('label', '')
                        label_text = label_to_string(label)

                        if not dry_run:
                            node['label'] = label_text
                            
                            # Speichere Bilder separat
                            if 'pictures' not in node:
                                node['pictures'] = []
                            node['pictures'].extend(label.get('pictures', []))
                            
                            # Speichere Links separat
                            if 'links' not in node:
                                node['links'] = []
                            node['links'].extend(label.get('links', []))

                        # Statistik
                        if old_label and old_label.strip() and old_label != label_text:
                            stats['labels_updated'] += 1
                        else:
                            stats['labels_applied'] += 1

                        stats['codes_matched'].add(mapping_code)
                        stats['nodes_labeled'].append({
                            'node_path': path,
                            'family': current_family,
                            'position': 'N/A',  # General-Mappings sind position-unabhängig
                            'code': code,
                            'old_label': old_label,
                            'new_label': label_text,
                            'pictures': label.get('pictures', []),
                            'links': label.get('links', []),
                            'full_typecode': node.get('full_typecode', ''),
                            'applied': not dry_run,
                            'type': 'general'  # Markiere als general mapping
                        })

                        if verbose:
                            print(f"    Code '{mapping_code}' → Label '{label_text}' (Pfad: {path})")
                        # Wenn ein mapping_code matched, sollte das weitere matching für diesen node
                        # optional unterbunden werden. Aktuell brechen wir, damit pro node nur das erste
                        # passende mapping angewendet wird; entferne das `break`, falls mehrere Labels
                        # pro Knoten gewünscht sind.
                        break

        # Rekursiv durch Children
        if 'children' in node:
            for i, child in enumerate(node['children']):
                child_path = f"{path}/children[{i}]" if path else f"children[{i}]"
                apply_general_labels_recursive(child, current_family, child_path, depth + 1)

    # Starte Anwendung
    apply_general_labels_recursive(tree_data)

    if verbose:
        print(f"  Matched Codes: {len(stats['codes_matched'])}/{len(code_to_label)}")
        print(f"  Labels Applied: {stats['labels_applied']}, Updated: {stats['labels_updated']}")

    return stats



def has_matching_descendants(node, matching_product_codes):
    """
    Prüft ob ein Knoten Nachkommen hat, die zu den gefilterten Produkten gehören.
    
    Args:
        node: Der zu prüfende Knoten
        matching_product_codes: Set von Typcode-Strings der gefilterten Produkte
        
    Returns:
        bool: True wenn mindestens ein Nachkomme in matching_product_codes ist
    """
    # Direkter Match
    if 'full_typecode' in node and node['full_typecode'] in matching_product_codes:
        return True
    
    # Prüfe Kinder rekursiv
    for child in node.get('children', []):
        if has_matching_descendants(child, matching_product_codes):
            return True
    
    return False


def inherit_groups_to_children(tree_data, target_family):
    """
    Vererbt Group-Werte von Parent-Nodes an alle Children-Nodes,
    die ebenfalls ein 'group' Attribut haben.
    
    Args:
        tree_data: JSON-Baum-Daten (werden modifiziert)
        target_family: Ziel-Produktfamilie (z.B. "A", "B", "BCC")
        
    Returns:
        dict: Statistiken über vererbte Groups
    """
    stats = {
        'groups_inherited': 0,
        'nodes_updated': 0
    }
    
    def inherit_groups_recursive(node, parent_group=None):
        """Rekursive Hilfsfunktion für Group-Vererbung"""
        current_group = parent_group
        
        # Wenn dieser Node eine eigene Group hat, verwende diese
        if 'group' in node and node['group']:
            current_group = node['group']
        # Wenn dieser Node keine Group hat, aber ein Parent eine hat, vererbe sie
        elif 'group' in node and not node['group'] and parent_group:
            node['group'] = parent_group
            current_group = parent_group
            stats['groups_inherited'] += 1
            stats['nodes_updated'] += 1
        
        # Rekursiv auf alle Children anwenden
        if 'children' in node:
            for child in node['children']:
                inherit_groups_recursive(child, current_group)
        
        # Für Pattern-Nodes
        if isinstance(node, dict) and 'children' in node:
            for child in node['children']:
                if isinstance(child, dict):
                    inherit_groups_recursive(child, current_group)
    
    # Starte die Vererbung nur für die angegebene Familie
    if 'children' in tree_data:
        for family_node in tree_data['children']:
            if family_node.get('code') == target_family:
                inherit_groups_recursive(family_node)
                break
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Wendet Label-Mappings auf Variantenbäume an',
        epilog='''
Beispiele:
  # Einzelnes Mapping
  %(prog)s labels_bcc_mounting.json                    # Wende Labels auf Variantenbaum an
  %(prog)s labels_bcc_mounting.json --dry-run          # Zeige Vorschau ohne Änderungen
  %(prog)s labels_bcc_mounting.json --backup           # Erstelle Backup vor Änderungen
  %(prog)s labels_bcc_mounting.json --output labeled.json  # Speichere in neue Datei
  
  # Batch-Verarbeitung (effizient!)
  %(prog)s --batch mappings/                           # Verarbeite alle Mappings in Verzeichnis
  %(prog)s --batch mappings/ --dry-run                 # Vorschau aller Mappings
  %(prog)s --batch mappings/ --output result.json      # Speichere Ergebnis
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('mapping_file', nargs='?',
                       help='JSON-Datei mit filter_criteria und code_mappings (oder --batch verwenden)')
    parser.add_argument('--batch', '-b',
                       help='Verzeichnis mit mehreren Mapping-Dateien (verarbeitet alle *.json rekursiv)')
    parser.add_argument('--tree-file',
                       help='Pfad zur Variantenbaum-JSON-Datei (Standard: baum.json)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Zeige Vorschau ohne Änderungen zu speichern')
    parser.add_argument('--backup',
                       action='store_true',
                       help='Erstelle Backup der Original-Datei vor Änderungen')
    parser.add_argument('--output', '-o',
                       help='Ausgabe-Datei (Standard: überschreibt Original)')
    parser.add_argument('--with-dates',
                       action='store_true',
                       help='Verwende JSON-Datei mit Datumsangaben')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Zeige detaillierte Ausgaben')
    
    args = parser.parse_args()
    
    # BATCH-MODUS: Verzeichnis mit mehreren Mappings
    if args.batch:
        if not Path(args.batch).is_dir():
            print(f"❌ Fehler: Kein gültiges Verzeichnis: {args.batch}")
            sys.exit(1)
        
        batch_stats = batch_process_mappings(
            mapping_dir=args.batch,
            tree_file=args.tree_file,
            dry_run=args.dry_run,
            backup=args.backup,
            output=args.output,
            verbose=args.verbose
        )
        
        if batch_stats is None:
            sys.exit(1)
        
        sys.exit(0)
    
    # EINZELNER MAPPING-MODUS (wie bisher)
    if not args.mapping_file:
        parser.error("mapping_file ist erforderlich (oder verwende --batch)")
    
    # Lade Mapping-Datei
    mapping_data = load_mapping_file(args.mapping_file)
    if mapping_data is None:
        sys.exit(1)
    
    # Zeige Mapping-Konfiguration
    print_mapping_summary(mapping_data)
    
    # Parse Filter-Kriterien
    filter_criteria = mapping_data['filter_criteria']
    filter_params = parse_filter_criteria(filter_criteria)
    
    # Validiere Filter-Parameter
    if all(v is None for v in [filter_params['target_schemas'], filter_params['group_position_filter'], filter_params['pattern_rules'], 
                              filter_params['position_rules'], filter_params['group_start_rules'], 
                              filter_params['group_rules'], filter_params['group_count_filter']]) and filter_params['product_family'] is None:
        print("❌ Fehler: Keine gültigen Filter-Kriterien gefunden!")
        sys.exit(1)
    
    # Wähle JSON-Datei
    if args.tree_file:
        json_file = args.tree_file
    else:
        # Die Datei an der das Mapping angewendet wird
        json_file = JSONFILE
        # json_file = "output/variantenbaum_with_dates.json" if args.with_dates else "output/variantenbaum.json"
    
    if not Path(json_file).exists():
        print(f"❌ Fehler: Datei {json_file} nicht gefunden!")
        print("Führe zuerst createVariantenBaum.py aus.")
        sys.exit(1)
    
    # Lade Variantenbaum
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden des Variantenbaums: {e}")
        sys.exit(1)
    
    # Finde passende Produkte
    print("SUCHE NACH PASSENDEN PRODUKTEN...")
    
    # BUGFIX: Wenn target_schemas eine leere Liste ist, setze es auf None
    target_schemas_param = filter_params['target_schemas']
    if isinstance(target_schemas_param, list) and len(target_schemas_param) == 0:
        target_schemas_param = None
    
    results = find_products_by_schema(
        tree_data,
        target_schemas=target_schemas_param,
        include_dates=args.with_dates,
        product_family=filter_params['product_family'],
        pattern_rules=filter_params['pattern_rules'],
        group_position_rules=filter_params['group_position_filter'],
        position_rules=filter_params['position_rules'],
        group_start_rules=filter_params['group_start_rules'],
        group_rules=filter_params['group_rules'],
        group_count_config=filter_params['group_count_filter'],
        and_mode=filter_params['and_mode'],
        negate_exclude=filter_params['negate_exclude']
    )
    
    # print(f"aaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbcccccc Gefundene Produkte: {results['match_count']}")
    # Zeige die Produkte an, die den Filter-Kriterien entsprechen
    
    # for product in results['matching_products']:
    #     if isinstance(product, dict) and 'full_typecode' in product:
    #         print(f"  - {product['full_typecode']}")
    #     elif isinstance(product, str):
    #         print(f"  - {product}")
    # zeige alle gefundenen Produkte, wenn verbose
    # print("Gefundene Produkte:")
    # for product in results['matching_products']:
    #     if isinstance(product, dict) and 'full_typecode' in product:
    #         print(f"  - {product['full_typecode']}")
    #     elif isinstance(product, str):
    #         print(f"  - {product}")
    # print()
        
    if results['match_count'] == 0:
        print("KEINE PRODUKTE GEFUNDEN die den Filter-Kriterien entsprechen.")
        sys.exit(1)
    
    # Erstelle Code-Lookup
    code_lookup = build_code_lookup(mapping_data.get('code_mappings', []))
    
    # Zeige die code lookup Zusammenfassung
    # print("\nCODE-LOOKUP ZUSAMMENFASSUNG:")
    # for position, codes in code_lookup.items():
    #     print(f"  Position {position}: {len(codes)} Codes")
    
    # Unterscheide zwischen alten und neuen group_mappings
    group_mappings = mapping_data.get('group_mappings', [])
    relative_group_mappings = []
    absolute_group_mappings = []
    
    # Printe group_mappings Zusammenfassung
    # print("\nGROUP-MAPPINGS ZUSAMMENFASSUNG:")
    # print(f"  Insgesamt: {len(group_mappings)} Mappings")
    # print(f"    - Relative Group-Mappings: {len([m for m in group_mappings if 'group' in m and 'labels' in m])}")
    # print(f"    - Absolute Group-Mappings (deprecated): {len([m for m in group_mappings if 'position' in m and 'groups' in m])}")
    
    # # Zeige mehr über relative und absolute group mappings:
    # print(f"  Relative Group-Mappings Details:")
    # print(f"    - Neue relative group_mappings (mit 'group' und 'labels'): {len([m for m in group_mappings if 'group' in m and 'labels' in m])}")
    # print(f"  Absolute Group-Mappings Details:")
    # print(f"    - Alte absolute group_mappings (mit 'position' und 'groups'): {len([m for m in group_mappings if 'position' in m and 'groups' in m])}")
    
    # Erkenne neue relative group_mappings (haben 'group' und 'labels')
    # vs alte absolute group_mappings (haben 'position' und 'groups')
    for mapping in group_mappings:
        if 'group' in mapping and 'labels' in mapping:
            # Neue relative group_mappings aus schema_search.py
            relative_group_mappings.append(mapping)
        elif 'position' in mapping and 'groups' in mapping:
            # Alte absolute group_mappings (deprecated, nur für Rückwärtskompatibilität)
            absolute_group_mappings.append(mapping)
    
    # Erstelle alte Group-Lookup nur für Rückwärtskompatibilität
    group_lookup = build_group_lookup(absolute_group_mappings) if absolute_group_mappings else {}
    
    global_group_mappings = mapping_data.get('global_group_mappings', [])
    name_mappings = mapping_data.get('name_mappings', [])
    general_mappings = mapping_data.get('general_mappings', [])
    special_mappings = mapping_data.get('special_mappings', [])
    
    if not code_lookup and not relative_group_mappings and not group_lookup and not global_group_mappings and not name_mappings and not general_mappings and not special_mappings:
        print("Keine gueltigen Code-Mappings, Group-Mappings, Global-Group-Mappings, Name-Mappings, General-Mappings oder Special-Mappings gefunden!")
        sys.exit(1)
    
    if args.verbose:
        print("\nCODE-LOOKUP:")
        for position, codes in code_lookup.items():
            print(f"  Position {position}: {len(codes)} Labels")
        
        if relative_group_mappings:
            print("\nRELATIVE GROUP-MAPPINGS:")
            for i, mapping in enumerate(relative_group_mappings, 1):
                group = mapping.get('group', '?')
                position = mapping.get('position', '?')
                codes = mapping.get('codes', [])
                labels = mapping.get('labels', [])
                strict = mapping.get('strict', False)
                print(f"  {i}. Gruppe {group}, Position {position}: {len(codes)} Labels. Mode {'STRICT' if strict else 'NON-STRICT'}")
        
        if group_lookup:
            print("\n👥 ABSOLUTE GROUP-LOOKUP (deprecated):")
            for position, codes in group_lookup.items():
                print(f"  Position {position}: {len(codes)} Groups")
        
        if global_group_mappings:
            print("\nGLOBAL-GROUP-MAPPINGS:")
            for i, mapping in enumerate(global_group_mappings, 1):
                print(f"  {i}. Group: {mapping.get('group', 'N/A')}")
                print(f"     Description: {mapping.get('description', 'N/A')}")
        
        if name_mappings:
            print("\nNAME-MAPPINGS:")
            for i, mapping in enumerate(name_mappings, 1):
                print(f"  {i}. Level: {mapping.get('level', 'N/A')}")
                print(f"     Name: {mapping.get('name', 'N/A')}")
        
        if general_mappings:
            print("\nGENERAL-MAPPINGS:")
            for i, mapping in enumerate(general_mappings, 1):
                codes = mapping.get('codes', [])
                labels = mapping.get('labels', [])
                print(f"  {i}. {len(codes)} Codes (position-unabhängig)")
    
    # Wende Labels an (Code-Mappings)
    print("\nWENDE CODE-LABELS AN...")
    stats = apply_labels_to_tree(tree_data, results['matching_products'], code_lookup, group_lookup, filter_params['product_family'], args.dry_run)
    
    # Wende relative Group-Mappings an (NEUE FUNKTIONALITÄT)
    if relative_group_mappings:
        print("\nWENDE RELATIVE GROUP-MAPPINGS AN...")
        relative_stats = apply_relative_group_mappings(tree_data, results['matching_products'], relative_group_mappings, filter_params['product_family'], args.dry_run, args.verbose)
        
        # Kombiniere Statistiken
        stats['labels_applied'] += relative_stats['labels_applied']
        stats['labels_updated'] += relative_stats['labels_updated']
        stats['nodes_labeled'].extend(relative_stats['nodes_labeled'])
    
    # Wende globale Group-Mappings an
    if global_group_mappings:
        print("\nWENDE GLOBALE GROUP-MAPPINGS AN...")
        global_stats = apply_global_group_mappings(tree_data, results['matching_products'], global_group_mappings, filter_params['product_family'], args.dry_run)
        
        # Integriere globale Statistiken
        stats['global_groups_applied'] = global_stats['global_groups_applied']
        stats['global_groups_updated'] = global_stats['global_groups_updated']
        stats['nodes_with_global_groups'] = global_stats['nodes_with_global_groups']
    
    # Wende Name-Mappings an (NEUE FUNKTIONALITÄT)
    if name_mappings:
        print("\nWENDE NAME-MAPPINGS AN...")
        name_stats = apply_name_mappings(tree_data, results['matching_products'], name_mappings, filter_params['product_family'], args.dry_run)
        
        # Integriere Name-Statistiken
        stats['names_applied'] = name_stats['names_applied']
        stats['names_updated'] = name_stats['names_updated']
        stats['nodes_named'] = name_stats['nodes_named']
    
    # Wende General-Mappings an (NEUE FUNKTIONALITÄT)
    if general_mappings:
        print("\nWENDE GENERAL-MAPPINGS AN...")
        general_stats = apply_general_mappings(tree_data, results['matching_products'], general_mappings, filter_params['product_family'], args.dry_run, args.verbose)
        
        # Kombiniere General-Statistiken mit Haupt-Stats
        stats['labels_applied'] += general_stats['labels_applied']
        stats['labels_updated'] += general_stats['labels_updated']
        stats['nodes_labeled'].extend(general_stats['nodes_labeled'])
        
        if args.verbose:
            print(f"  General-Mappings: {general_stats['labels_applied']} angewendet, {general_stats['labels_updated']} aktualisiert")

    #   "special_mappings": [
    #     {
    #       "group": 2
    #       "position": "3-4", (optional)
    #       "allowed": "0-9", (optional, kann nur angeben werden wenn position angegeben ist)
    #       "labels": ["Stecker S4", "PUR-Kabel", "Y-Verteiler"]
    #     }
    # Wende Special-Mappings an (NEUE FUNKTIONALITÄT)
    if special_mappings:
        print("\nWENDE SPECIAL-MAPPINGS AN...")
        special_stats = apply_special_mappings(tree_data, results['matching_products'], special_mappings, filter_params['product_family'], args.dry_run, args.verbose)
        
        # Kombiniere Special-Statistiken mit Haupt-Stats
        stats['labels_applied'] += special_stats['labels_applied']
        stats['labels_updated'] += special_stats['labels_updated']
        stats['nodes_labeled'].extend(special_stats['nodes_labeled'])
        
        if args.verbose:
            print(f"  Special-Mappings: {special_stats['labels_applied']} angewendet, {special_stats['labels_updated']} aktualisiert")
        
    
    # Vererbe Groups an Children
    if not args.dry_run:
        print("\nVERERBE GROUPS AN CHILDREN...")
        inheritance_stats = inherit_groups_to_children(tree_data, filter_params['product_family'])
        print(f"Groups vererbt: {inheritance_stats['groups_inherited']}")
        print(f"Betroffene Nodes: {inheritance_stats['nodes_updated']}")
    
    # Zeige Ergebnisse
    print_application_results(stats, args.dry_run)
    
    # Speichere Ergebnisse (falls nicht dry-run)
    if not args.dry_run:
        output_file = args.output or json_file
        
        # Erstelle Backup falls gewünscht
        if args.backup and output_file == json_file:
            create_backup(json_file)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Labeled Variantenbaum gespeichert: {output_file}")
            
            # Automatische Validierung nach dem Speichern
            print("🔍 Validiere gespeicherte Datei...")
            if validate_saved_file(output_file):
                print("✅ Validation erfolgreich - Datei ist gültig")
            else:
                print("⚠️  Validation-Warnung - bitte manuell prüfen")
                
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            sys.exit(1)
    else:
        print("INFO: Dry-run Modus: Keine Änderungen gespeichert.")


def find_mapping_files(directory):
    """
    Findet alle JSON-Mapping-Dateien in einem Verzeichnis (rekursiv).
    
    WICHTIG: Sortierung wie in VSCode - Depth-First!
    - Verzeichnisse alphabetisch
    - Dateien in Verzeichnis alphabetisch
    - Rekursiv in Unterverzeichnisse
    
    Beispiel-Reihenfolge:
        mappings/
        ├── 01_base/
        │   ├── file1.json       # 1
        │   ├── file2.json       # 2
        │   └── sub/
        │       ├── file3.json   # 3
        │       └── file4.json   # 4
        └── 02_extended/
            └── file5.json       # 5
    
    Args:
        directory: Pfad zum Verzeichnis
        
    Returns:
        Liste von Pfaden zu Mapping-Dateien (sortiert wie VSCode Tree)
    """
    mapping_files = []
    base_path = Path(directory)
    
    def scan_directory(current_path):
        """Rekursiv scannen in Depth-First Reihenfolge."""
        items = []
        
        # Sammle alle Items im aktuellen Verzeichnis
        try:
            for item in sorted(current_path.iterdir()):
                items.append(item)
        except PermissionError:
            return
        
        # Verarbeite erst Dateien, dann Verzeichnisse (VSCode-Stil)
        # 1. Dateien in diesem Verzeichnis
        for item in items:
            if item.is_file() and item.suffix == '.json':
                # Prüfe ob es eine gültige Mapping-Datei ist
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'filter_criteria' in data:
                            mapping_files.append(str(item))
                except Exception:
                    # Ignoriere ungültige JSON-Dateien
                    pass
        
        # 2. Unterverzeichnisse (rekursiv)
        for item in items:
            if item.is_dir() and not item.name.startswith('.'):
                scan_directory(item)
    
    # Starte Scan
    scan_directory(base_path)
    
    return mapping_files


def batch_process_mappings(mapping_dir, tree_file=None, dry_run=False, backup=False, output=None, verbose=False):
    """
    Verarbeitet alle Mapping-Dateien in einem Verzeichnis sequentiell.
    
    WICHTIG: Lädt den Baum EINMAL und wendet dann alle Mappings nacheinander an!
    Das ist deutlich effizienter als jedes Mapping einzeln auszuführen.
    
    Args:
        mapping_dir: Verzeichnis mit Mapping-Dateien
        tree_file: Pfad zur Variantenbaum-Datei
        dry_run: Keine Änderungen speichern
        backup: Backup erstellen
        output: Ausgabe-Datei
        verbose: Detaillierte Ausgaben
        
    Returns:
        dict: Statistiken über alle Mappings
    """
    print("=" * 80)
    print("BATCH-VERARBEITUNG VON MAPPING-DATEIEN")
    print("=" * 80)
    
    # Finde alle Mapping-Dateien
    mapping_files = find_mapping_files(mapping_dir)
    
    if not mapping_files:
        print(f"❌ Keine Mapping-Dateien gefunden in: {mapping_dir}")
        return None
    
    print(f"📁 Verzeichnis: {mapping_dir}")
    print(f"📄 Gefundene Mapping-Dateien: {len(mapping_files)}")
    for i, mf in enumerate(mapping_files, 1):
        rel_path = Path(mf).relative_to(mapping_dir)
        print(f"   {i}. {rel_path}")
    print()
    
    # Wähle Baum-Datei
    json_file = tree_file or JSONFILE
    
    # Lade Baum EINMAL
    print(f"📦 Lade Variantenbaum: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        print(f"✅ Baum geladen")
    except FileNotFoundError:
        print(f"❌ Fehler: Datei nicht gefunden: {json_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Fehler: Ungültiges JSON in {json_file}: {e}")
        return None
    
    # Erstelle Backup falls gewünscht (nur einmal am Anfang!)
    if backup and not dry_run:
        create_backup(json_file)
    
    # Batch-Statistiken
    batch_stats = {
        'total_mappings': len(mapping_files),
        'successful_mappings': 0,
        'failed_mappings': 0,
        'total_labels_applied': 0,
        'total_labels_updated': 0,
        'total_nodes_labeled': 0,
        'mapping_results': []
    }
    
    # Verarbeite jedes Mapping sequentiell
    print("\n" + "=" * 80)
    print("VERARBEITE MAPPINGS")
    print("=" * 80)
    
    for i, mapping_file in enumerate(mapping_files, 1):
        rel_path = Path(mapping_file).relative_to(mapping_dir)
        print(f"\n[{i}/{len(mapping_files)}] {rel_path}")
        print("-" * 80)
        
        start_time = datetime.now()
        
        try:
            # Lade Mapping
            mapping_data = load_mapping_file(mapping_file)
            if mapping_data is None:
                print(f"⚠️  Überspringe ungültiges Mapping: {rel_path}")
                batch_stats['failed_mappings'] += 1
                continue
            
            # Parse Filter
            filter_criteria = mapping_data['filter_criteria']
            filter_params = parse_filter_criteria(filter_criteria)
            
            # Zeige kurze Zusammenfassung
            family = filter_params.get('product_family', 'N/A')
            print(f"   Familie: {family}")
            
            # Finde passende Produkte
            results = find_products_by_schema(
                tree_data,
                filter_params['product_family'],
                filter_params['target_schemas'],
                filter_params['pattern_rules'],
                filter_params['position_rules'],
                filter_params['group_start_rules'],
                filter_params['group_rules'],
                filter_params['group_position_filter'],
                filter_params['group_count_filter']
            )
            
            print(f"   Passende Produkte: {results['match_count']:,}")
            
            # Wende Mappings an
            stats = {
                'labels_applied': 0,
                'labels_updated': 0,
                'nodes_labeled': [],
                'groups_applied': 0,
                'groups_updated': 0
            }
            
            # Code-Mappings
            code_mappings = mapping_data.get('code_mappings', [])
            if code_mappings:
                code_lookup = build_code_lookup(code_mappings)
                group_lookup = build_group_lookup(code_mappings)
                code_stats = apply_labels_to_tree(tree_data, results['matching_products'], code_lookup, group_lookup, filter_params['product_family'], dry_run)
                stats['labels_applied'] += code_stats['labels_applied']
                stats['labels_updated'] += code_stats['labels_updated']
                stats['nodes_labeled'].extend(code_stats['nodes_labeled'])
            
            # Group-Mappings
            group_mappings = mapping_data.get('group_mappings', [])
            if group_mappings:
                group_stats = apply_relative_group_mappings(tree_data, results['matching_products'], group_mappings, filter_params['product_family'], dry_run, verbose)
                stats['labels_applied'] += group_stats['labels_applied']
                stats['labels_updated'] += group_stats['labels_updated']
                stats['nodes_labeled'].extend(group_stats['nodes_labeled'])
            
            # Special-Mappings
            special_mappings = mapping_data.get('special_mappings', [])
            if special_mappings:
                special_stats = apply_special_mappings(tree_data, results['matching_products'], special_mappings, filter_params['product_family'], dry_run, verbose)
                stats['labels_applied'] += special_stats['labels_applied']
                stats['labels_updated'] += special_stats['labels_updated']
                stats['nodes_labeled'].extend(special_stats['nodes_labeled'])
            
            # General-Mappings
            general_mappings = mapping_data.get('general_mappings', [])
            if general_mappings:
                general_stats = apply_general_mappings(tree_data, results['matching_products'], general_mappings, filter_params['product_family'], dry_run, verbose)
                stats['labels_applied'] += general_stats['labels_applied']
                stats['labels_updated'] += general_stats['labels_updated']
                stats['nodes_labeled'].extend(general_stats['nodes_labeled'])
            
            # Name-Mappings
            name_mappings = mapping_data.get('name_mappings', [])
            if name_mappings:
                name_stats = apply_name_mappings(tree_data, results['matching_products'], name_mappings, filter_params['product_family'], dry_run)
                stats['names_applied'] = name_stats['names_applied']
                stats['names_updated'] = name_stats['names_updated']
            
            # Vererbe Groups
            if not dry_run:
                inheritance_stats = inherit_groups_to_children(tree_data, filter_params['product_family'])
            
            # Zeige Ergebnis
            duration = (datetime.now() - start_time).total_seconds()
            print(f"   ✅ Labels angewendet: {stats['labels_applied']}")
            print(f"   ✅ Labels aktualisiert: {stats['labels_updated']}")
            print(f"   ⏱️  Dauer: {duration:.2f}s")
            
            # Update Batch-Stats
            batch_stats['successful_mappings'] += 1
            batch_stats['total_labels_applied'] += stats['labels_applied']
            batch_stats['total_labels_updated'] += stats['labels_updated']
            batch_stats['total_nodes_labeled'] += len(stats['nodes_labeled'])
            batch_stats['mapping_results'].append({
                'file': str(rel_path),
                'family': family,
                'labels_applied': stats['labels_applied'],
                'labels_updated': stats['labels_updated'],
                'duration': duration
            })
            
        except Exception as e:
            print(f"   ❌ FEHLER: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            batch_stats['failed_mappings'] += 1
    
    # Speichere Ergebnis (nur einmal am Ende!)
    if not dry_run:
        output_file = output or json_file
        
        print("\n" + "=" * 80)
        print("SPEICHERE ERGEBNIS")
        print("=" * 80)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Labeled Variantenbaum gespeichert: {output_file}")
            
            # Validierung
            print("🔍 Validiere gespeicherte Datei...")
            if validate_saved_file(output_file):
                print("✅ Validation erfolgreich")
            else:
                print("⚠️  Validation-Warnung")
                
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            return None
    
    # Zeige Gesamt-Statistik
    print("\n" + "=" * 80)
    print("BATCH-VERARBEITUNG ABGESCHLOSSEN")
    print("=" * 80)
    print(f"Gesamt-Mappings: {batch_stats['total_mappings']}")
    print(f"  ✅ Erfolgreich: {batch_stats['successful_mappings']}")
    print(f"  ❌ Fehlgeschlagen: {batch_stats['failed_mappings']}")
    print(f"\nGesamt-Labels angewendet: {batch_stats['total_labels_applied']:,}")
    print(f"Gesamt-Labels aktualisiert: {batch_stats['total_labels_updated']:,}")
    print(f"Gesamt-Nodes gelabelt: {batch_stats['total_nodes_labeled']:,}")
    
    if batch_stats['mapping_results']:
        print("\nDetails pro Mapping:")
        for result in batch_stats['mapping_results']:
            print(f"  {result['file']}: {result['labels_applied']} angewendet, {result['labels_updated']} aktualisiert ({result['duration']:.2f}s)")
    
    if dry_run:
        print("\nINFO: Dry-run Modus - Keine Änderungen gespeichert.")
    
    print("=" * 80)
    
    return batch_stats


if __name__ == "__main__":
    main()