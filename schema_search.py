#!/usr/bin/env python3
"""
Schema-basierte Produktsuche für Variantenbäume

Dieses Script ermöglicht es, nach Produkten zu suchen, die einem bestimmten Schema entsprechen.
Es durchsucht sowohl Endknoten (Blätter) als auch Zwischenknoten mit is_intermediate_code=true.

Verwendung:
    python schema_search.py [3,3,3,4] [--with-dates] [--details]
    
Beispiele:
    python schema_search.py [3,3,3,4]
    python schema_search.py [3,3,3,4,0] --details
    python schema_search.py [1,4,2] --with-dates --details
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# JSON file in der die Suche durchgeführt wird
# JSONFILE = "output/variantenbaum.json"
JSONFILE = "output/baum.json"


def parse_multiple_schemas(schema_args):
    """
    Parst mehrere Schema-Argumente zu einer Liste von Schema-Objekten.
    
    Args:
        schema_args: Liste von Schema-Strings
        
    Returns:
        list: Liste von Schema-Objekten {'schema': [3,3,3,4], 'is_prefix': False} oder None bei Fehlern
    """
    if not schema_args:
        return None
    
    schemas = []
    for schema_str in schema_args:
        schema_obj = parse_schema(schema_str)
        if schema_obj is None:
            return None
        schemas.append(schema_obj)
    
    return schemas


def parse_schema(schema_str):
    """
    Parst ein Schema-String zu einer Liste von Integers mit optionalem Präfix-Flag.
    
    Args:
        schema_str: String im Format "[3,3,3,4]", "3,3,3,4", "[4,4]:prefix" oder "4,4:prefix"
        
    Returns:
        dict: {'schema': [3,3,3,4], 'is_prefix': False} oder None bei Fehlern
    """
    try:
        # Prüfe auf :prefix Suffix
        is_prefix = False
        if ':prefix' in schema_str:
            schema_str = schema_str.replace(':prefix', '')
            is_prefix = True
        
        # Entferne Klammern und Leerzeichen
        clean_str = schema_str.strip('[]').replace(' ', '')
        
        # Teile am Komma und konvertiere zu int
        parts = [int(x.strip()) for x in clean_str.split(',') if x.strip()]
        
        return {
            'schema': parts,
            'is_prefix': is_prefix
        }
    except (ValueError, AttributeError):
        return None


def parse_pattern_filter(pattern_str):
    """
    Parst einen Pattern-Filter-String zu einer Liste von Regeln.
    
    Args:
        pattern_str: String im Format "1=3,2=4,last=6" oder "1=3-5,3=2" oder "3!=2" (ungleich)
        
    Returns:
        list: Liste von Dictionaries mit Pattern-Regeln oder None bei Fehlern
        
    Beispiele:
        "1=3,2=4" → [{'position': 1, 'min_len': 3, 'max_len': 3, 'negate': False}, {'position': 2, 'min_len': 4, 'max_len': 4, 'negate': False}]
        "1=3-5,last=6" → [{'position': 1, 'min_len': 3, 'max_len': 5, 'negate': False}, {'position': 'last', 'min_len': 6, 'max_len': 6, 'negate': False}]
        "3!=2" → [{'position': 3, 'min_len': 2, 'max_len': 2, 'negate': True}]
        "3!=2-4" → [{'position': 3, 'min_len': 2, 'max_len': 4, 'negate': True}]
    """
    if not pattern_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in pattern_str.split(',') if p.strip()]
        
        for part in parts:
            # Prüfe auf != (ungleich) oder = (gleich)
            negate = False
            if '!=' in part:
                negate = True
                position_str, length_str = part.split('!=', 1)
            elif '=' in part:
                negate = False
                position_str, length_str = part.split('=', 1)
            else:
                continue
                
            position_str = position_str.strip()
            length_str = length_str.strip()
            
            # Parse Position
            if position_str.lower() == 'last':
                position = 'last'
            else:
                position = int(position_str)
                if position < 1:
                    raise ValueError(f"Position muss >= 1 sein, nicht {position}")
            
            # Parse Länge (kann Bereich sein: "3-5" oder einzelner Wert: "4")
            if '-' in length_str:
                min_str, max_str = length_str.split('-', 1)
                min_len = int(min_str.strip())
                max_len = int(max_str.strip())
                if min_len > max_len:
                    raise ValueError(f"Minimale Länge ({min_len}) darf nicht größer sein als maximale Länge ({max_len})")
            else:
                min_len = max_len = int(length_str)
            
            if min_len < 0 or max_len < 0:
                raise ValueError("Längen müssen >= 0 sein")
            
            rules.append({
                'position': position,
                'min_len': min_len,
                'max_len': max_len,
                'negate': negate
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_position_filter(position_str):
    """
    Parst einen Absolute-Position-Filter-String zu einer Liste von Regeln.
    
    Args:
        position_str: String im Format "5=M,11=PX" oder "5=M423,22=PX0334" oder "5=M:prefix"
        
    Returns:
        list: Liste von Dictionaries mit Position-Regeln oder None bei Fehlern
        
    Beispiele:
        "5=M,11=PX" → [{'position': 5, 'value': 'M', 'is_prefix': False}, {'position': 11, 'value': 'PX', 'is_prefix': False}]
        "5=M423" → [{'position': 5, 'value': 'M423', 'is_prefix': False}]
        "5=M:prefix" → [{'position': 5, 'value': 'M', 'is_prefix': True}]
        "5=M:prefix,22=PX0334" → [{'position': 5, 'value': 'M', 'is_prefix': True}, {'position': 22, 'value': 'PX0334', 'is_prefix': False}]
    """
    if not position_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in position_str.split(',') if p.strip()]
        
        for part in parts:
            if '=' not in part:
                continue
                
            position_str_part, value_with_prefix = part.split('=', 1)
            position = int(position_str_part.strip())
            
            # Prüfe auf :prefix Suffix
            is_prefix = False
            if ':prefix' in value_with_prefix:
                value = value_with_prefix.replace(':prefix', '')
                is_prefix = True
            else:
                value = value_with_prefix
            
            value = value.strip()
            
            if position < 1:
                raise ValueError(f"Position muss >= 1 sein, nicht {position}")
            
            if not value:
                raise ValueError("Wert darf nicht leer sein")
            
            rules.append({
                'position': position,
                'value': value,
                'is_prefix': is_prefix
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_group_start_filter(group_start_str):
    """
    Parst einen Gruppen-Start-Position-Filter-String zu einer Liste von Regeln.
    
    Args:
        group_start_str: String im Format "1=5,2=9" oder "1=5"
        
    Returns:
        list: Liste von Dictionaries mit Gruppen-Start-Regeln oder None bei Fehlern
        
    Beispiele:
        "1=5,2=9" → [{'group': 1, 'start_position': 5}, {'group': 2, 'start_position': 9}]
        "1=5" → [{'group': 1, 'start_position': 5}]
    """
    if not group_start_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in group_start_str.split(',') if p.strip()]
        
        for part in parts:
            if '=' not in part:
                continue
                
            group_str, position_str = part.split('=', 1)
            group = int(group_str.strip())
            position = int(position_str.strip())
            
            if group < 1:
                raise ValueError(f"Gruppen-Nummer muss >= 1 sein, nicht {group}")
            
            if position < 1:
                raise ValueError(f"Start-Position muss >= 1 sein, nicht {position}")
            
            rules.append({
                'group': group,
                'start_position': position
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_contains_filter(contains_str):
    """
    Parst einen Contains-Filter-String zu einer Liste von Regeln.
    
    Args:
        contains_str: String im Format "M313" oder "M313,PX" (UND) oder "M314|M111" (ODER) oder "M313:case"
        
    Returns:
        list: Liste von Dictionaries mit Contains-Regeln oder None bei Fehlern
        
    Beispiele:
        "M313" → [{'value': 'M313', 'case_sensitive': False, 'or_group': 0}]
        "M313,PX" → [{'value': 'M313', 'case_sensitive': False, 'or_group': 0}, {'value': 'PX', 'case_sensitive': False, 'or_group': 0}] (UND)
        "M314|M111" → [{'value': 'M314', 'case_sensitive': False, 'or_group': 1}, {'value': 'M111', 'case_sensitive': False, 'or_group': 1}] (ODER)
        "M313,PX|050" → M313 UND (PX ODER 050)
        "M313:case" → [{'value': 'M313', 'case_sensitive': True, 'or_group': 0}]
        
    WICHTIG: 
    - Komma (,) = UND-Verknüpfung
    - Pipe (|) = ODER-Verknüpfung  
    - Kombination: "M313,PX|050" = M313 UND (PX ODER 050)
    """
    if not contains_str:
        return []
    
    try:
        rules = []
        or_group_id = 0
        
        # Erst nach Komma teilen (UND-Gruppen)
        and_parts = [p.strip() for p in contains_str.split(',') if p.strip()]
        
        for and_part in and_parts:
            # Dann jede UND-Gruppe nach Pipe teilen (ODER-Alternativen)
            or_parts = [p.strip() for p in and_part.split('|') if p.strip()]
            
            if len(or_parts) > 1:
                # Mehrere ODER-Alternativen in dieser UND-Gruppe
                or_group_id += 1
                current_or_group = or_group_id
            else:
                # Einzelner Wert (normale UND-Verknüpfung)
                current_or_group = 0
            
            for or_part in or_parts:
                # Parse Case-Sensitivity
                case_sensitive = False
                if ':case' in or_part:
                    or_part = or_part.replace(':case', '')
                    case_sensitive = True
                
                value = or_part.strip()
                
                if not value:
                    raise ValueError("Suchwert darf nicht leer sein")
                
                rules.append({
                    'value': value,
                    'case_sensitive': case_sensitive,
                    'or_group': current_or_group
                })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_group_content_filter(group_content_str):
    """
    Parst einen Gruppen-Inhalt-Filter-String zu einer Liste von Regeln.
    
    Args:
        group_content_str: String im Format "1=M313" oder "1=M:prefix,2=PX" oder "1=M313,3=050"
        
    Returns:
        list: Liste von Dictionaries mit Gruppen-Inhalt-Regeln oder None bei Fehlern
        
    Beispiele:
        "1=M313" → [{'group': 1, 'value': 'M313', 'is_prefix': False}]
        "1=M:prefix" → [{'group': 1, 'value': 'M', 'is_prefix': True}]
        "1=M313,2=PX" → [{'group': 1, 'value': 'M313', 'is_prefix': False}, {'group': 2, 'value': 'PX', 'is_prefix': False}]
        "1=M:prefix,3=050" → [{'group': 1, 'value': 'M', 'is_prefix': True}, {'group': 3, 'value': '050', 'is_prefix': False}]
    """
    if not group_content_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in group_content_str.split(',') if p.strip()]
        
        for part in parts:
            if '=' not in part:
                continue
                
            group_str, value_with_prefix = part.split('=', 1)
            group = int(group_str.strip())
            
            # Prüfe auf :prefix Suffix
            is_prefix = False
            if ':prefix' in value_with_prefix:
                value = value_with_prefix.replace(':prefix', '')
                is_prefix = True
            else:
                value = value_with_prefix
            
            value = value.strip()
            
            if group < 1:
                raise ValueError(f"Gruppen-Nummer muss >= 1 sein, nicht {group}")
            
            if not value:
                raise ValueError("Wert darf nicht leer sein")
            
            rules.append({
                'group': group,
                'value': value,
                'is_prefix': is_prefix
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_exclude_group_filter(exclude_group_str):
    """
    Parst einen Exclude-Gruppen-Filter-String.
    
    Args:
        exclude_group_str: String im Format "1=Z" oder "1=Z:prefix" oder "1=Z,2=ZA123" oder "3=Z:prefix,5=SPECIAL"
        
    Returns:
        list: Liste von Dictionaries mit Exclude-Gruppen-Regeln oder None bei Fehlern
        
    Beispiele:
        "1=Z" → [{'group': 1, 'value': 'Z', 'is_prefix': False}]
        "1=Z:prefix" → [{'group': 1, 'value': 'Z', 'is_prefix': True}] (schließt Z, ZA, ZB123, etc. aus)
        "1=Z,2=SPECIAL" → [{'group': 1, 'value': 'Z', 'is_prefix': False}, {'group': 2, 'value': 'SPECIAL', 'is_prefix': False}]
        "1=Z:prefix,3=X:prefix" → [{'group': 1, 'value': 'Z', 'is_prefix': True}, {'group': 3, 'value': 'X', 'is_prefix': True}]
    """
    if not exclude_group_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in exclude_group_str.split(',') if p.strip()]
        
        for part in parts:
            if '=' not in part:
                continue
                
            group_str, value_with_prefix = part.split('=', 1)
            group = int(group_str.strip())
            
            # Prüfe auf :prefix Suffix
            is_prefix = False
            if ':prefix' in value_with_prefix:
                value = value_with_prefix.replace(':prefix', '')
                is_prefix = True
            else:
                value = value_with_prefix
            
            value = value.strip()
            
            if group < 1:
                raise ValueError(f"Gruppen-Nummer muss >= 1 sein, nicht {group}")
            
            if not value:
                raise ValueError("Exclude-Wert darf nicht leer sein")
            
            rules.append({
                'group': group,
                'value': value,
                'is_prefix': is_prefix
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_exclude_position_filter(exclude_position_str):
    """
    Parst einen Exclude-Position-Filter-String.
    
    Args:
        exclude_position_str: String im Format "5=Z" oder "5=Z:prefix" oder "5=Z,22=SPECIAL" oder "5=ZA123:prefix"
        
    Returns:
        list: Liste von Dictionaries mit Exclude-Position-Regeln oder None bei Fehlern
        
    Beispiele:
        "5=Z" → [{'position': 5, 'value': 'Z', 'is_prefix': False}]
        "5=Z:prefix" → [{'position': 5, 'value': 'Z', 'is_prefix': True}] (schließt Z, ZA, ZB123, etc. aus)
        "5=Z,22=SPECIAL" → [{'position': 5, 'value': 'Z', 'is_prefix': False}, {'position': 22, 'value': 'SPECIAL', 'is_prefix': False}]
        "5=ZA123:prefix,11=X:prefix" → [{'position': 5, 'value': 'ZA123', 'is_prefix': True}, {'position': 11, 'value': 'X', 'is_prefix': True}]
    """
    if not exclude_position_str:
        return []
    
    try:
        rules = []
        parts = [p.strip() for p in exclude_position_str.split(',') if p.strip()]
        
        for part in parts:
            if '=' not in part:
                continue
                
            position_str_part, value_with_prefix = part.split('=', 1)
            position = int(position_str_part.strip())
            
            # Prüfe auf :prefix Suffix
            is_prefix = False
            if ':prefix' in value_with_prefix:
                value = value_with_prefix.replace(':prefix', '')
                is_prefix = True
            else:
                value = value_with_prefix
            
            value = value.strip()
            
            if position < 1:
                raise ValueError(f"Position muss >= 1 sein, nicht {position}")
            
            if not value:
                raise ValueError("Exclude-Wert darf nicht leer sein")
            
            rules.append({
                'position': position,
                'value': value,
                'is_prefix': is_prefix
            })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_exclude_contains_filter(exclude_contains_str):
    """
    Parst einen Exclude-Contains-Filter-String.
    
    Args:
        exclude_contains_str: String im Format "Z" oder "ZA123" oder "Z,SPECIAL" oder "ZA123|ZB456" oder "Z:case"
        
    Returns:
        list: Liste von Dictionaries mit Exclude-Contains-Regeln oder None bei Fehlern
        
    Beispiele:
        "Z" → [{'value': 'Z', 'case_sensitive': False, 'or_group': 0}]
        "ZA123" → [{'value': 'ZA123', 'case_sensitive': False, 'or_group': 0}]
        "Z,SPECIAL" → [{'value': 'Z', 'case_sensitive': False, 'or_group': 0}, {'value': 'SPECIAL', 'case_sensitive': False, 'or_group': 0}] (UND: ausschließen wenn Z UND SPECIAL)
        "ZA123|ZB456" → [{'value': 'ZA123', 'case_sensitive': False, 'or_group': 1}, {'value': 'ZB456', 'case_sensitive': False, 'or_group': 1}] (ODER: ausschließen wenn ZA123 ODER ZB456)
        "Z:case" → [{'value': 'Z', 'case_sensitive': True, 'or_group': 0}]
        
    WICHTIG: 
    - Komma (,) = UND-Verknüpfung (ausschließen wenn ALLE Teile gefunden)
    - Pipe (|) = ODER-Verknüpfung (ausschließen wenn EINER der Teile gefunden)
    """
    if not exclude_contains_str:
        return []
    
    try:
        rules = []
        or_group_id = 0
        
        # Erst nach Komma teilen (UND-Gruppen)
        and_parts = [p.strip() for p in exclude_contains_str.split(',') if p.strip()]
        
        for and_part in and_parts:
            # Dann jede UND-Gruppe nach Pipe teilen (ODER-Alternativen)
            or_parts = [p.strip() for p in and_part.split('|') if p.strip()]
            
            if len(or_parts) > 1:
                # Mehrere ODER-Alternativen in dieser UND-Gruppe
                or_group_id += 1
                current_or_group = or_group_id
            else:
                # Einzelner Wert (normale UND-Verknüpfung)
                current_or_group = 0
            
            for or_part in or_parts:
                # Parse Case-Sensitivity
                case_sensitive = False
                if ':case' in or_part:
                    or_part = or_part.replace(':case', '')
                    case_sensitive = True
                
                value = or_part.strip()
                
                if not value:
                    raise ValueError("Exclude-Suchwert darf nicht leer sein")
                
                rules.append({
                    'value': value,
                    'case_sensitive': case_sensitive,
                    'or_group': current_or_group
                })
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_group_filter(group_str):
    """
    Parst einen Gruppen-Filter-String.
    
    Args:
        group_str: String im Format "Typ1" oder "Typ1,Typ2" oder "BCC=Typ1" oder "BCC=Typ1,BES=Typ2"
        
    Returns:
        dict: Dictionary mit Gruppen-Regeln oder None bei Fehlern
        
    Beispiele:
        "Typ1" → {'default': ['Typ1']}
        "Typ1,Typ2" → {'default': ['Typ1', 'Typ2']} (ODER-Verknüpfung)
        "BCC=Typ1" → {'BCC': ['Typ1']}
        "BCC=Typ1,Typ2" → {'BCC': ['Typ1', 'Typ2']} (ODER-Verknüpfung für BCC)
        "BCC=Typ1,BES=Typ2" → {'BCC': ['Typ1'], 'BES': ['Typ2']}
        "BCC=Typ1,Typ2,BES=Typ3" → {'BCC': ['Typ1', 'Typ2'], 'BES': ['Typ3']}
    """
    if not group_str:
        return {}
    
    try:
        rules = {}
        parts = [p.strip() for p in group_str.split(',') if p.strip()]
        
        current_family = 'default'  # Standard Familie
        
        for part in parts:
            if '=' in part:
                # Format: "FAMILIE=GRUPPE"
                family, group = part.split('=', 1)
                family = family.strip()
                group = group.strip()
                
                if not family or not group:
                    raise ValueError("Produktfamilie und Gruppe dürfen nicht leer sein")
                
                current_family = family
                if current_family not in rules:
                    rules[current_family] = []
                rules[current_family].append(group)
            else:
                # Format: "GRUPPE" - gehört zur aktuellen Familie
                group = part.strip()
                if not group:
                    raise ValueError("Gruppe darf nicht leer sein")
                
                if current_family not in rules:
                    rules[current_family] = []
                rules[current_family].append(group)
        
        return rules
    except (ValueError, AttributeError) as e:
        return None


def parse_group_count_filter(group_count_str):
    """
    Parst einen erweiterten Gruppen-Anzahl-Filter-String.
    
    Args:
        group_count_str: String im Format "3" (exakt), ">3" (mehr als), ">=4" (min), "<5" (weniger als), 
                        "<=3" (max), "2-5" (Bereich), "3,5,7" (mehrere exakte Werte)
        
    Returns:
        dict: Filter-Konfiguration mit 'type', 'value', 'min', 'max', 'values' oder None bei Fehlern
        
    Beispiele:
        "3" → {'type': 'exact', 'value': 3}
        ">3" → {'type': 'greater', 'value': 3}
        ">=4" → {'type': 'greater_equal', 'value': 4}
        "<5" → {'type': 'less', 'value': 5}
        "<=3" → {'type': 'less_equal', 'value': 3}
        "2-5" → {'type': 'range', 'min': 2, 'max': 5}
        "3,5,7" → {'type': 'multiple', 'values': [3, 5, 7]}
    """
    if not group_count_str:
        return None
    
    group_count_str = group_count_str.strip()
    
    try:
        # Prüfe auf Bereich (z.B. "2-5")
        if '-' in group_count_str and not group_count_str.startswith('-'):
            parts = group_count_str.split('-')
            if len(parts) == 2:
                min_val = int(parts[0].strip())
                max_val = int(parts[1].strip())
                if min_val <= max_val and min_val >= 1:
                    return {'type': 'range', 'min': min_val, 'max': max_val}
        
        # Prüfe auf mehrere Werte (z.B. "3,5,7")
        if ',' in group_count_str:
            values = []
            for part in group_count_str.split(','):
                val = int(part.strip())
                if val >= 1:
                    values.append(val)
            if values:
                return {'type': 'multiple', 'values': sorted(list(set(values)))}
        
        # Prüfe auf Vergleichsoperatoren
        if group_count_str.startswith('>='):
            value = int(group_count_str[2:].strip())
            if value >= 1:
                return {'type': 'greater_equal', 'value': value}
        elif group_count_str.startswith('<='):
            value = int(group_count_str[2:].strip())
            if value >= 1:
                return {'type': 'less_equal', 'value': value}
        elif group_count_str.startswith('>'):
            value = int(group_count_str[1:].strip())
            if value >= 0:  # Kann 0 sein für ">0"
                return {'type': 'greater', 'value': value}
        elif group_count_str.startswith('<'):
            value = int(group_count_str[1:].strip())
            if value >= 1:
                return {'type': 'less', 'value': value}
        else:
            # Exakter Wert (z.B. "3")
            value = int(group_count_str)
            if value >= 1:
                return {'type': 'exact', 'value': value}
        
        return None
    except (ValueError, AttributeError) as e:
        return None


def parse_analyze_group_position(analyze_str):
    """
    Parst einen Analyze-Gruppen-Position-String für das Sammeln aller einzigartigen Werte.
    
    Args:
        analyze_str: String im Format "3:1" (Position 1 in Gruppe 3) oder "3:1-2" (Position 1-2 in Gruppe 3)
        
    Returns:
        dict: Analyse-Konfiguration mit 'group', 'start_pos', 'end_pos' oder None bei Fehlern
        
    Beispiele:
        "3:1" → {'group': 3, 'start_pos': 1, 'end_pos': 1}
        "3:1-2" → {'group': 3, 'start_pos': 1, 'end_pos': 2}
    """
    if not analyze_str:
        return None
    
    try:
        if ':' not in analyze_str:
            return None
            
        # Split bei erstem Doppelpunkt: "3:1" → ["3", "1"] oder "3:1-2" → ["3", "1-2"]
        group_str, position_part = analyze_str.split(':', 1)
        group = int(group_str.strip())
        
        if group < 1:
            raise ValueError(f"Gruppen-Nummer muss >= 1 sein, nicht {group}")
        
        position_part = position_part.strip()
        if '-' in position_part:
            # Expliziter Bereich: "1-2"
            start_str, end_str = position_part.split('-', 1)
            start_pos = int(start_str.strip())
            end_pos = int(end_str.strip())
            
            if start_pos > end_pos:
                raise ValueError(f"Start-Position ({start_pos}) darf nicht größer sein als End-Position ({end_pos})")
        else:
            # Einzelne Position: "1"
            start_pos = int(position_part)
            end_pos = start_pos
        
        if start_pos < 1:
            raise ValueError(f"Position muss >= 1 sein, nicht {start_pos}")
        
        return {
            'group': group,
            'start_pos': start_pos,
            'end_pos': end_pos
        }
        
    except ValueError as e:
        print(f"❌ Fehler beim Parsen von '{analyze_str}': {e}")
        return None
    except Exception as e:
        print(f"❌ Unerwarteter Fehler beim Parsen von '{analyze_str}': {e}")
        return None


def parse_group_position_filter(group_position_str):
    """
    Parst einen Gruppen-Position-Filter-String mit OR-Verknüpfung.
    
    Args:
        group_position_str: String im Format "3:1=M" oder "3:2=ABC" oder "3:1=M:prefix" oder "3:2-4=ABC" (expliziter Bereich)
                           Mit '|' für OR-Verknüpfung: "1:2=A|3:1=BD" bedeutet (1:2=A) ODER (3:1=BD)
                           Komma ist weiterhin UND: "1:2=A,2:1=X|3:1=BD" bedeutet (1:2=A UND 2:1=X) ODER (3:1=BD)
        
    Returns:
        list: Liste von Listen mit Gruppen-Position-Regeln (OR-Gruppen) oder None bei Fehlern
              Äußere Liste = OR-Verknüpfung, innere Liste = UND-Verknüpfung
        
    Beispiele:
        "3:1=M" → [[{'group': 3, 'start_pos': 1, 'end_pos': 1, 'value': 'M', 'is_prefix': False}]]
        "3:2=ABC" → [[{'group': 3, 'start_pos': 2, 'end_pos': 4, 'value': 'ABC', 'is_prefix': False}]]
        "3:1=M,5:3=PX" → [[rule1, rule2]] (UND-Verknüpfung)
        "3:1=M|5:3=PX" → [[rule1], [rule2]] (OR-Verknüpfung)
        "1:2=A,2:1=X|3:1=BD" → [[rule1, rule2], [rule3]] (Gruppe1 UND Gruppe2) ODER Gruppe3
    """
    if not group_position_str:
        return []
    
    try:
        # Teile zuerst nach '|' für OR-Verknüpfung
        or_groups = [g.strip() for g in group_position_str.split('|') if g.strip()]
        all_or_groups = []
        
        for or_group in or_groups:
            # Innerhalb jeder OR-Gruppe: Teile nach ',' für UND-Verknüpfung
            and_rules = []
            parts = [p.strip() for p in or_group.split(',') if p.strip()]
            for part in parts:
                if ':' not in part or '=' not in part:
                    continue
                group_str, position_value_part = part.split(':', 1)
                group = int(group_str.strip())
                if group < 1:
                    raise ValueError(f"Gruppen-Nummer muss >= 1 sein, nicht {group}")
                negate = False
                if '!=' in position_value_part:
                    negate = True
                    position_part, value_with_prefix = position_value_part.split('!=', 1)
                elif '=' in position_value_part:
                    negate = False
                    position_part, value_with_prefix = position_value_part.split('=', 1)
                else:
                    continue
                
                position_part = position_part.strip()
                value_with_prefix = value_with_prefix.strip()

                is_prefix = False
                if ':prefix' in value_with_prefix:
                    value = value_with_prefix.replace(':prefix', '')
                    is_prefix = True
                else:
                    value = value_with_prefix
                value = value.strip()
                if not value:
                    raise ValueError("Wert darf nicht leer sein")
                position_part = position_part.strip()
                explicit_range = False
                # Erweiterung: Prüfe auf -1 (letzte Position)
                if position_part == '-1':
                    start_pos = -1
                    end_pos = -1
                elif '-' in position_part:
                    start_str, end_str = position_part.split('-', 1)
                    start_pos = int(start_str.strip())
                    end_pos = int(end_str.strip())
                    explicit_range = True
                    if start_pos > end_pos:
                        raise ValueError(f"Start-Position ({start_pos}) darf nicht größer sein als End-Position ({end_pos})")
                    if end_pos - start_pos + 1 != len(value):
                        raise ValueError(f"Bereich-Länge ({end_pos - start_pos + 1}) muss der Wert-Länge ({len(value)}) entsprechen")
                else:
                    start_pos = int(position_part)
                    end_pos = start_pos + len(value) - 1
                # start_pos kann jetzt auch -1 sein
                rule = {
                    'group': group,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'value': value,
                    'negate': negate,
                    'is_prefix': is_prefix
                }
                if explicit_range:
                    rule['explicit_range'] = True
                and_rules.append(rule)
            
            if and_rules:  # Nur hinzufügen wenn Regeln vorhanden
                all_or_groups.append(and_rules)
        
        return all_or_groups if all_or_groups else []
    except (ValueError, AttributeError) as e:
        return None


def calculate_code_schema(code_parts):
    """
    Berechnet das Schema eines Code-Pfads (ohne die Produktfamilie).
    
    Args:
        code_parts: Liste der Code-Teile (ohne Produktfamilie)
        
    Returns:
        list: Schema als Liste von Längen
    """
    return [len(part) for part in code_parts]


def matches_pattern_filter(schema, pattern_rules):
    """
    Prüft ob ein Schema den Pattern-Filter-Regeln entspricht.
    
    Args:
        schema: Schema als Liste von Längen [3,3,3,4]
        pattern_rules: Liste von Pattern-Regeln
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not pattern_rules:
        return True
    
    for rule in pattern_rules:
        position = rule['position']
        min_len = rule['min_len']
        max_len = rule['max_len']
        negate = rule.get('negate', False)
        
        # Bestimme die tatsächliche Position
        if position == 'last':
            if not schema:  # Leeres Schema
                return False
            actual_position = len(schema) - 1
        else:
            actual_position = position - 1  # Konvertiere zu 0-basiertem Index
        
        # Prüfe ob Position existiert
        if actual_position < 0 or actual_position >= len(schema):
            return False
        
        # Prüfe Länge
        actual_length = schema[actual_position]
        length_matches = min_len <= actual_length <= max_len
        
        # Berücksichtige Negation
        if negate:
            # Bei Negation: Regel ist erfüllt wenn die Länge NICHT im Bereich liegt
            if length_matches:
                return False  # Negierte Regel nicht erfüllt
        else:
            # Bei normaler Regel: Länge muss im Bereich liegen
            if not length_matches:
                return False  # Normale Regel nicht erfüllt
    
    return True


def matches_position_filter(full_typecode, position_rules):
    """
    Prüft ob ein Produktcode den Absolute-Position-Filter-Regeln entspricht.
    
    Args:
        full_typecode: Vollständiger Produktcode (z.B. "BCC M423-0000-2A-002-PX0334-050")
        position_rules: Liste von Position-Regeln mit 'is_prefix' Flag
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not position_rules:
        return True
    
    # Verwende den Code so wie er ist (mit Leerzeichen und Bindestrichen)
    code = full_typecode
    
    for rule in position_rules:
        position = rule['position']
        expected_value = rule['value']
        is_prefix = rule.get('is_prefix', False)
        
        # Konvertiere zu 0-basiertem Index
        start_index = position - 1
        
        if is_prefix:
            # Präfix-Match: Der erwartete Wert muss am Anfang der Position stehen
            end_index = start_index + len(expected_value)
            
            # Prüfe ob Position im Code existiert
            if start_index < 0 or end_index > len(code):
                return False
            
            # Prüfe Präfix an Position
            actual_value = code[start_index:end_index]
            if actual_value != expected_value:
                return False
        else:
            # Exakter Match: Bestimme das Ende basierend auf der nächsten Nicht-Alphanumerischen Zeichen oder String-Ende
            # Oder basierend auf der Länge des erwarteten Werts
            end_index = start_index + len(expected_value)
            
            # Prüfe ob Position im Code existiert
            if start_index < 0 or end_index > len(code):
                return False
            
            # Für exakten Match: Prüfe ob der Wert genau passt UND
            # dass danach ein Trennzeichen kommt (oder String-Ende)
            actual_value = code[start_index:end_index]
            if actual_value != expected_value:
                return False
            
            # Zusätzliche Prüfung für exakten Match: 
            # Nach dem Wert sollte ein Trennzeichen kommen oder das String-Ende
            if end_index < len(code):
                next_char = code[end_index]
                # Erlaubte Trennzeichen: Leerzeichen, Bindestrich, etc.
                if next_char.isalnum():  # Wenn das nächste Zeichen alphanumerisch ist, ist es kein exakter Match
                    return False
    
    return True


def matches_group_start_filter(full_typecode, code_parts, group_start_rules, node_position=None):
    """
    Prüft ob ein Produktcode den Gruppen-Start-Position-Filter-Regeln entspricht.
    
    Args:
        full_typecode: Vollständiger Produktcode (z.B. "BCC M423-0000-2A-002-PX0334-050")
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        group_start_rules: Liste von Gruppen-Start-Regeln
        node_position: Position des aktuellen Knotens im Baum (aus JSON)
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not group_start_rules:
        return True
    
    # Berechne Start-Positionen für jede Gruppe
    group_positions = {}
    
    if node_position is not None and len(code_parts) > 0:
        # Nutze die position aus dem JSON für die letzte Gruppe
        # und berechne rückwärts für die anderen Gruppen
        last_group_index = len(code_parts)
        last_group_position = node_position
        
        # Berechne Positionen rückwärts
        current_position = last_group_position
        for i in range(last_group_index, 0, -1):
            group_positions[i] = current_position
            if i > 1:  # Nicht beim ersten Element
                current_position -= len(code_parts[i-1]) + 1  # -1 für Trennzeichen
    else:
        # Fallback: Berechne Start-Positionen manuell
        # Familie + Leerzeichen + Code-Teile getrennt durch '-'
        family_and_space_length = full_typecode.find(' ') + 1 if ' ' in full_typecode else 0
        
        current_position = family_and_space_length + 1  # +1 für 1-basierte Indexierung
        for i, part in enumerate(code_parts):
            group_positions[i + 1] = current_position  # Gruppe 1, 2, 3, ...
            current_position += len(part) + 1  # +1 für '-' Trennzeichen
    
    # Prüfe alle Regeln
    for rule in group_start_rules:
        group = rule['group']
        expected_position = rule['start_position']
        
        # Prüfe ob Gruppe existiert
        if group not in group_positions:
            return False
        
        # Prüfe Start-Position
        actual_position = group_positions[group]
        if actual_position != expected_position:
            return False
    
    return True


def matches_contains_filter(full_typecode, code_parts, product_family, contains_rules):
    """
    Prüft ob ein Produktcode den Contains-Filter-Regeln entspricht.
    
    Args:
        full_typecode: Vollständiger Produktcode (z.B. "BCC M423-0000-2A-002-PX0334-050")
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        product_family: Produktfamilie (z.B. "BCC")
        contains_rules: Liste von Contains-Regeln mit or_group
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not contains_rules:
        return True
    
    # Suche nur im Code-Teil (ohne Familie, da Familie über -f gefiltert wird)
    search_text = '-'.join(code_parts)
    
    # Gruppiere Regeln nach or_group
    or_groups = {}
    and_rules = []  # or_group = 0
    
    for rule in contains_rules:
        or_group = rule['or_group']
        if or_group == 0:
            and_rules.append(rule)
        else:
            if or_group not in or_groups:
                or_groups[or_group] = []
            or_groups[or_group].append(rule)
    
    # Prüfe UND-Regeln (or_group = 0)
    for rule in and_rules:
        search_value = rule['value']
        case_sensitive = rule['case_sensitive']
        
        # Case-Sensitivity behandeln
        check_text = search_text if case_sensitive else search_text.upper()
        check_value = search_value if case_sensitive else search_value.upper()
        
        if check_value not in check_text:
            return False
    
    # Prüfe ODER-Gruppen (or_group > 0)
    for or_group_id, or_rules in or_groups.items():
        # Mindestens eine Regel in dieser ODER-Gruppe muss erfüllt sein
        group_matched = False
        
        for rule in or_rules:
            search_value = rule['value']
            case_sensitive = rule['case_sensitive']
            
            # Case-Sensitivity behandeln
            check_text = search_text if case_sensitive else search_text.upper()
            check_value = search_value if case_sensitive else search_value.upper()
            
            if check_value in check_text:
                group_matched = True
                break  # Eine Regel in der ODER-Gruppe erfüllt
        
        if not group_matched:
            return False  # Diese ODER-Gruppe nicht erfüllt
    
    return True


def matches_exclude_group_filter(code_parts, exclude_group_rules):
    """
    Prüft ob Code-Teile den Exclude-Gruppen-Filter-Regeln entsprechen.
    
    Args:
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        exclude_group_rules: Liste von Exclude-Gruppen-Regeln mit 'is_prefix' Flag
        
    Returns:
        bool: True wenn das Produkt AUSGESCHLOSSEN werden soll (gefunden in Exclude-Liste)
    """
    if not exclude_group_rules:
        return False  # Keine Exclude-Regeln = nicht ausschließen
    
    for rule in exclude_group_rules:
        group_number = rule['group']
        exclude_value = rule['value']
        is_prefix = rule.get('is_prefix', False)
        
        # Konvertiere zu 0-basiertem Index
        group_index = group_number - 1
        
        # Prüfe ob Gruppe existiert
        if group_index < 0 or group_index >= len(code_parts):
            continue  # Gruppe existiert nicht, diese Regel überspringen
        
        # Hole den tatsächlichen Wert der Gruppe
        actual_value = code_parts[group_index]
        
        if is_prefix:
            # Präfix-Match: Wenn der exclude_value am Anfang der Gruppe steht, ausschließen
            if actual_value.startswith(exclude_value):
                return True  # Produkt soll ausgeschlossen werden
        else:
            # Exakter Match: Wenn der exclude_value exakt der Gruppe entspricht, ausschließen
            if actual_value == exclude_value:
                return True  # Produkt soll ausgeschlossen werden
    
    return False  # Keine Exclude-Regel getroffen = nicht ausschließen


def matches_exclude_position_filter(full_typecode, exclude_position_rules):
    """
    Prüft ob ein Produktcode den Exclude-Position-Filter-Regeln entspricht.
    
    Args:
        full_typecode: Vollständiger Produktcode (z.B. "BCC M423-0000-2A-002-PX0334-050")
        exclude_position_rules: Liste von Exclude-Position-Regeln mit 'is_prefix' Flag
        
    Returns:
        bool: True wenn das Produkt AUSGESCHLOSSEN werden soll (gefunden in Exclude-Liste)
    """
    if not exclude_position_rules:
        return False  # Keine Exclude-Regeln = nicht ausschließen
    
    # Verwende den Code so wie er ist (mit Leerzeichen und Bindestrichen)
    code = full_typecode
    
    for rule in exclude_position_rules:
        position = rule['position']
        exclude_value = rule['value']
        is_prefix = rule.get('is_prefix', False)
        
        # Konvertiere zu 0-basiertem Index
        start_index = position - 1
        
        if is_prefix:
            # Präfix-Match: Der exclude_value darf NICHT am Anfang der Position stehen
            end_index = start_index + len(exclude_value)
            
            # Prüfe ob Position im Code existiert
            if start_index < 0 or end_index > len(code):
                continue  # Position existiert nicht, diese Regel überspringen
            
            # Prüfe Präfix an Position
            actual_value = code[start_index:end_index]
            if actual_value == exclude_value:
                return True  # Produkt soll ausgeschlossen werden
        else:
            # Exakter Match: Der exclude_value darf NICHT exakt an dieser Position stehen
            end_index = start_index + len(exclude_value)
            
            # Prüfe ob Position im Code existiert
            if start_index < 0 or end_index > len(code):
                continue  # Position existiert nicht, diese Regel überspringen
            
            # Für exakten Match: Prüfe ob der Wert genau passt UND
            # dass danach ein Trennzeichen kommt (oder String-Ende)
            actual_value = code[start_index:end_index]
            if actual_value == exclude_value:
                # Zusätzliche Prüfung für exakten Match: 
                # Nach dem Wert sollte ein Trennzeichen kommen oder das String-Ende
                if end_index >= len(code):
                    return True  # String-Ende erreicht = exakter Match
                else:
                    next_char = code[end_index]
                    # Erlaubte Trennzeichen: Leerzeichen, Bindestrich, etc.
                    if not next_char.isalnum():  # Wenn das nächste Zeichen kein alphanumerisches ist, ist es ein exakter Match
                        return True  # Produkt soll ausgeschlossen werden
    
    return False  # Keine Exclude-Regel getroffen = nicht ausschließen


def matches_exclude_contains_filter(full_typecode, code_parts, product_family, exclude_contains_rules):
    """
    Prüft ob ein Produktcode den Exclude-Contains-Filter-Regeln entspricht.
    
    Args:
        full_typecode: Vollständiger Produktcode (z.B. "BCC M423-0000-2A-002-PX0334-050")
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        product_family: Produktfamilie (z.B. "BCC")
        exclude_contains_rules: Liste von Exclude-Contains-Regeln mit or_group
        
    Returns:
        bool: True wenn das Produkt AUSGESCHLOSSEN werden soll (gefunden in Exclude-Liste)
    """
    if not exclude_contains_rules:
        return False  # Keine Exclude-Regeln = nicht ausschließen
    
    # Suche nur im Code-Teil (ohne Familie, da Familie über -f gefiltert wird)
    search_text = '-'.join(code_parts)
    
    # Gruppiere Regeln nach or_group
    or_groups = {}
    and_rules = []  # or_group = 0
    
    for rule in exclude_contains_rules:
        or_group = rule['or_group']
        if or_group == 0:
            and_rules.append(rule)
        else:
            if or_group not in or_groups:
                or_groups[or_group] = []
            or_groups[or_group].append(rule)
    
    # Prüfe UND-Regeln (or_group = 0)
    # ALLE UND-Regeln müssen erfüllt sein, damit ausgeschlossen wird
    all_and_matched = True
    if and_rules:  # Nur prüfen wenn UND-Regeln existieren
        for rule in and_rules:
            search_value = rule['value']
            case_sensitive = rule['case_sensitive']
            
            # Case-Sensitivity behandeln
            check_text = search_text if case_sensitive else search_text.upper()
            check_value = search_value if case_sensitive else search_value.upper()
            
            if check_value not in check_text:
                all_and_matched = False
                break
    
    # Prüfe ODER-Gruppen (or_group > 0)
    # Mindestens eine Regel in jeder ODER-Gruppe muss erfüllt sein
    all_or_groups_matched = True
    if or_groups:  # Nur prüfen wenn ODER-Gruppen existieren
        for or_group_id, or_rules in or_groups.items():
            # Mindestens eine Regel in dieser ODER-Gruppe muss erfüllt sein
            group_matched = False
            
            for rule in or_rules:
                search_value = rule['value']
                case_sensitive = rule['case_sensitive']
                
                # Case-Sensitivity behandeln
                check_text = search_text if case_sensitive else search_text.upper()
                check_value = search_value if case_sensitive else search_value.upper()
                
                if check_value in check_text:
                    group_matched = True
                    break  # Eine Regel in der ODER-Gruppe erfüllt
            
            if not group_matched:
                all_or_groups_matched = False
                break  # Diese ODER-Gruppe nicht erfüllt
    
    # Exclude-Logik: Wenn keine Regeln definiert sind, ist die Gruppe automatisch "erfüllt"
    if not and_rules:
        all_and_matched = True
    if not or_groups:
        all_or_groups_matched = True
    
    # Ausschließen wenn alle Bedingungen erfüllt sind
    return all_and_matched and all_or_groups_matched


def matches_group_position_filter(code_parts, group_position_rules):
    """
    Prüft ob Code-Teile den Gruppen-Position-Filter-Regeln entsprechen.
    
    Args:
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        group_position_rules: Liste von Gruppen-Position-Regeln
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not group_position_rules:
        return True
    
    for rule in group_position_rules:
        group_number = rule['group']
        start_pos = rule['start_pos']
        end_pos = rule['end_pos']
        expected_value = rule['value']
        negate = rule.get('negate', False)
        is_prefix = rule.get('is_prefix', False)
        group_index = group_number - 1        
        
        if group_index < 0 or group_index >= len(code_parts):
            return False  # Gruppe existiert nicht
        group_content = code_parts[group_index]
        # Erweiterung: -1 bedeutet letzte Position
        if start_pos == -1:
            start_idx = len(group_content) - len(expected_value)
            end_idx = len(group_content)
            if start_idx < 0 or end_idx > len(group_content):
                return False
        else:
            start_idx = start_pos - 1
            end_idx = end_pos if end_pos <= len(group_content) else len(group_content)
            if start_idx < 0 or start_idx >= len(group_content):
                return False
            if end_idx > len(group_content):
                # print(f"  ❌ End-Index {end_idx} überschreitet die Länge der Gruppe {group_number} ({len(group_content)}).")
                return False
        actual_value = group_content[start_idx:end_idx]
        if is_prefix:
            if not actual_value.startswith(expected_value) and not negate:
                return False
            if actual_value.startswith(expected_value) and negate:
                return False
        else:
            if actual_value != expected_value and not negate:
                return False
            if actual_value == expected_value and negate:
                return False
    # print("  ✅ Alle Gruppen-Position-Regeln erfüllt.")
    return True


def matches_group_content_filter(code_parts, group_content_rules):
    """
    Prüft ob Code-Teile den Gruppen-Inhalt-Filter-Regeln entsprechen.
    
    Args:
        code_parts: Code-Teile ohne Produktfamilie (z.B. ["M423", "0000", "2A", "002", "PX0334", "050"])
        group_content_rules: Liste von Gruppen-Inhalt-Regeln mit 'is_prefix' Flag
        
    Returns:
        bool: True wenn alle Regeln erfüllt sind
    """
    if not group_content_rules:
        return True
    
    for rule in group_content_rules:
        group_number = rule['group']
        expected_value = rule['value']
        is_prefix = rule.get('is_prefix', False)
        
        # Konvertiere zu 0-basiertem Index
        group_index = group_number - 1
        
        # Prüfe ob Gruppe existiert
        if group_index < 0 or group_index >= len(code_parts):
            return False
        
        # Hole den tatsächlichen Wert der Gruppe
        actual_value = code_parts[group_index]
        
        if is_prefix:
            # Präfix-Match: Der erwartete Wert muss am Anfang der Gruppe stehen
            if not actual_value.startswith(expected_value):
                return False
        else:
            # Exakter Match
            if actual_value != expected_value:
                return False
    
    return True


def matches_extended_group_count_filter(product_schema, group_count_config):
    """
    Prüft ob ein Produkt-Schema dem erweiterten Gruppen-Anzahl-Filter entspricht.
    
    Args:
        product_schema: Schema des Produkts (Liste von Längen)
        group_count_config: Gruppen-Count-Konfiguration von parse_group_count_filter()
        
    Returns:
        bool: True wenn das Schema dem Filter entspricht
    """
    if not group_count_config:
        return True
    
    actual_count = len(product_schema)
    filter_type = group_count_config['type']
    
    if filter_type == 'exact':
        return actual_count == group_count_config['value']
    elif filter_type == 'greater':
        return actual_count > group_count_config['value']
    elif filter_type == 'greater_equal':
        return actual_count >= group_count_config['value']
    elif filter_type == 'less':
        return actual_count < group_count_config['value']
    elif filter_type == 'less_equal':
        return actual_count <= group_count_config['value']
    elif filter_type == 'range':
        return group_count_config['min'] <= actual_count <= group_count_config['max']
    elif filter_type == 'multiple':
        return actual_count in group_count_config['values']
    
    return False


def matches_group_filter(node, product_family, group_rules):
    """
    Prüft ob ein Produktknoten den Gruppen-Filter-Regeln entspricht.
    
    Args:
        node: JSON-Knoten des Produkts
        product_family: Produktfamilie des aktuellen Produkts
        group_rules: Dictionary mit Gruppen-Regeln (jetzt Listen von erlaubten Gruppen)
        
    Returns:
        bool: True wenn die Gruppen-Regeln erfüllt sind
    """
    if not group_rules:
        return True
    
    # Hole das group-Attribut des Knotens
    node_group = node.get('group', '')
    
    # Prüfe familienspezifische Regel zuerst
    if product_family and product_family in group_rules:
        expected_groups = group_rules[product_family]
        # ODER-Verknüpfung: node_group muss in einer der erlaubten Gruppen sein
        return node_group in expected_groups
    
    # Prüfe Default-Regel
    if 'default' in group_rules:
        expected_groups = group_rules['default']
        # ODER-Verknüpfung: node_group muss in einer der erlaubten Gruppen sein
        return node_group in expected_groups
    
    # Keine passende Regel gefunden
    return False


def extract_code_path(node_path):
    """
    Extrahiert den Code-Pfad aus einem vollständigen Pfad (entfernt root und Pattern-Knoten).
    
    Args:
        node_path: Vollständiger Pfad als String "root-FAMILIE-pattern_3-Teil1-pattern_4-Teil2-..."
        
    Returns:
        list: Code-Teile ohne root, Produktfamilie und Pattern-Knoten
    """
    parts = node_path.split('-')
    code_parts = []
    
    for i, part in enumerate(parts):
        # Überspringe root, Pattern-Knoten und die Produktfamilie (Index 1)
        if part != 'root' and not part.startswith('pattern_') and i != 1:
            code_parts.append(part)
    
    return code_parts

def find_products_by_schema(data, target_schemas=None, include_dates=False, product_family=None, prefix_match=False, pattern_rules=None, position_rules=None, group_start_rules=None, group_rules=None, group_count_config=None, contains_rules=None, group_content_rules=None, group_position_rules=None, analyze_group_position=None, exclude_group_rules=None, exclude_position_rules=None, exclude_contains_rules=None, negate_exclude=False, and_mode=False):
    """
    Findet alle Produkte, die einem bestimmten Schema entsprechen.
    
    Args:
        data: JSON-Daten des Variantenbaums
        target_schemas: Gewünschte Schemas als Liste von Schema-Objekten [{'schema': [3,3,3,4], 'is_prefix': False}] (optional wenn pattern_rules verwendet wird)
        include_dates: Ob Datumsangaben in Ergebnissen enthalten sein sollen
        product_family: Optional - beschränke Suche auf diese Produktfamilie
        prefix_match: Wenn True, werden ALLE Schemas als Präfix behandelt (für Rückwärtskompatibilität)
        pattern_rules: Liste von Pattern-Filter-Regeln
        position_rules: Liste von Absolute-Position-Filter-Regeln
        group_start_rules: Liste von Gruppen-Start-Position-Filter-Regeln
        group_rules: Dictionary mit Gruppen-Filter-Regeln
        group_count_config: Gruppen-Anzahl-Filter-Konfiguration (z.B. {'type': 'exact', 'value': 3} oder {'type': 'greater', 'value': 2})
        contains_rules: Liste von Contains-Filter-Regeln
        group_content_rules: Liste von Gruppen-Inhalt-Filter-Regeln
        group_position_rules: Liste von Gruppen-Position-Filter-Regeln
        analyze_group_position: Konfiguration für Gruppen-Position-Analyse (sammelt alle Werte an einer Position)
        exclude_group_rules: Liste von Exclude-Gruppen-Filter-Regeln
        exclude_position_rules: Liste von Exclude-Position-Filter-Regeln
        exclude_contains_rules: Liste von Exclude-Contains-Filter-Regeln
        negate_exclude: Wenn True, wird die Logik aller Filter umgekehrt (finde Produkte die NICHT den Kriterien entsprechen)
        and_mode: Wenn True, müssen ALLE Schemas erfüllt sein (UND-Verknüpfung), sonst reicht eines (ODER-Verknüpfung)
        
    Returns:
        dict: Ergebnisse mit gefundenen Produkten
    """
    # print(f"\n\ngroup position rules: {group_position_rules}\n\n")
    # loope durch die Argumente und printe nur die nicht-None Werte
    # print("Suchparameter:")
    # for arg, value in locals().items():
    #     if value is not None and arg not in ['data', 'matching_products', 'total_products_checked', 'searched_families']:
    #         print(f"  {arg}: {value}")
            
    matching_products = []
    total_products_checked = 0
    searched_families = []
    
    # Kompatibilität: target_schema als einzelnes Schema (alte API)
    if target_schemas is not None and not isinstance(target_schemas, list):
        target_schemas = [{'schema': target_schemas, 'is_prefix': prefix_match}]
    elif target_schemas is not None and len(target_schemas) > 0 and not isinstance(target_schemas[0], dict):
        # Liste von alten Schema-Listen zu neuen Schema-Objekten konvertieren
        target_schemas = [{'schema': schema, 'is_prefix': prefix_match} for schema in target_schemas]
    
    # Erste Phase: Sammle alle verfügbaren Produktfamilien
    def collect_families(node, depth=0):
        # Produktfamilien sind auf Tiefe 1 (erste Code-Ebene)
        if 'code' in node and depth == 1:
            if node['code'] not in searched_families:
                searched_families.append(node['code'])
        
        # Rekursiv für alle Children
        for child in node.get('children', []):
            collect_families(child, depth + 1)
    
    # Sammle zuerst alle Familien
    collect_families(data)
    
    def traverse_node(node, path="", current_family=None, depth=0):
        nonlocal total_products_checked
        
        # Behandle Pattern-Knoten und Code-Knoten unterschiedlich
        if 'pattern' in node:
            # Pattern-Knoten: verwende Pattern-Wert im Pfad, aber überspringe bei Produktsuche
            current_path = f"{path}-pattern_{node['pattern']}" if path else f"pattern_{node['pattern']}"
        elif 'code' in node:
            current_path = f"{path}-{node['code']}" if path else node['code']
            # Bestimme Produktfamilie (erste Code-Ebene - Tiefe 1)
            if depth == 1:
                current_family = node['code']
        else:
            current_path = path
        
        # Wenn Produktfamilien-Filter gesetzt ist, überspringe andere Familien
        skip_family = product_family and current_family and current_family != product_family
        
        # Prüfe nur Knoten mit Code (keine Pattern-Knoten)
        if 'code' in node and not skip_family:
            # Prüfe ob es ein gültiges Produkt ist (Endknoten oder Zwischenknoten mit Excel-Code)
            is_leaf = not node.get('children', [])
            is_intermediate_with_code = node.get('is_intermediate_code', False)
            
            if is_leaf or is_intermediate_with_code:
                total_products_checked += 1
                
                # Extrahiere Code-Pfad (ohne root und Produktfamilie)
                # print(f"\nÜberprüfe Produkt: {current_path}")
                code_parts = extract_code_path(current_path)
                
                if code_parts:
                    # Berechne Schema
                    product_schema = calculate_code_schema(code_parts)
                    
                    # Hole full_typecode für Filter
                    full_typecode = node.get('full_typecode', current_path.replace('-', ' ', 1).replace('-', '-'))
                    
                    # Prüfe Pattern-Filter
                    pattern_matches = True
                    if pattern_rules:
                        pattern_matches = matches_pattern_filter(product_schema, pattern_rules)
                    
                    # Prüfe Absolute-Position-Filter
                    position_matches = True
                    if position_rules:
                        position_matches = matches_position_filter(full_typecode, position_rules)
                    
                    # Prüfe Gruppen-Start-Position-Filter
                    group_start_matches = True
                    if group_start_rules:
                        node_position = node.get('position')
                        group_start_matches = matches_group_start_filter(full_typecode, code_parts, group_start_rules, node_position)
                    
                    # Prüfe Gruppen-Filter
                    group_matches = True
                    if group_rules:
                        group_matches = matches_group_filter(node, current_family, group_rules)
                    
                    # Prüfe Contains-Filter
                    contains_matches = True
                    if contains_rules:
                        contains_matches = matches_contains_filter(full_typecode, code_parts, current_family, contains_rules)
                    
                    # Prüfe Gruppen-Inhalt-Filter
                    group_content_matches = True
                    if group_content_rules:
                        group_content_matches = matches_group_content_filter(code_parts, group_content_rules)
                    
                    # Prüfe Exclude-Filter (wenn eines matcht, Produkt ausschließen)
                    exclude_matches = False
                    if exclude_group_rules:
                        exclude_matches = exclude_matches or matches_exclude_group_filter(code_parts, exclude_group_rules)
                    if not exclude_matches and exclude_position_rules:
                        exclude_matches = exclude_matches or matches_exclude_position_filter(full_typecode, exclude_position_rules)
                    if not exclude_matches and exclude_contains_rules:
                        exclude_matches = exclude_matches or matches_exclude_contains_filter(full_typecode, code_parts, current_family, exclude_contains_rules)
                    
                    # Prüfe erweiterten Gruppen-Anzahl-Filter
                    group_count_matches = True
                    if group_count_config is not None:
                        group_count_matches = matches_extended_group_count_filter(product_schema, group_count_config)
                    
                    # Prüfe Gruppen-Position-Filter mit OR-Verknüpfung
                    group_position_matches = True
                    if group_position_rules:
                        # group_position_rules ist jetzt eine Liste von OR-Gruppen: [[rule1, rule2], [rule3]]
                        # Äußere Liste = OR, innere Liste = UND
                        # Mindestens eine OR-Gruppe muss erfüllt sein
                        or_results = []
                        for or_group in group_position_rules:
                            # Alle Regeln in dieser OR-Gruppe müssen erfüllt sein (UND)
                            and_result = all(matches_group_position_filter(code_parts, [rule]) for rule in or_group)
                            or_results.append(and_result)
                        # Mindestens ein OR-Ergebnis muss True sein
                        group_position_matches = any(or_results) if or_results else True
                    
                    # Vergleiche mit Ziel-Schemas (nur wenn target_schemas angegeben)
                    schema_matches = True  # Standardmäßig True für Pattern-only Suchen
                    matched_schema_objs = []
                    if target_schemas is not None:
                        if and_mode:
                            # UND-Modus: ALLE Schemas müssen erfüllt sein
                            schema_matches = True
                            for schema_obj in target_schemas:
                                target_schema = schema_obj['schema']
                                is_prefix_match = schema_obj['is_prefix']
                                current_match = False
                                
                                if is_prefix_match:
                                    # Präfix-Match: Ziel-Schema muss am Anfang des Produkt-Schemas stehen
                                    if len(product_schema) >= len(target_schema):
                                        if product_schema[:len(target_schema)] == target_schema:
                                            current_match = True
                                            matched_schema_objs.append(schema_obj)
                                else:
                                    # Exakter Match
                                    if product_schema == target_schema:
                                        current_match = True
                                        matched_schema_objs.append(schema_obj)
                                
                                # Bei UND-Modus: Wenn ein Schema nicht erfüllt ist, ist das ganze Produkt ungültig
                                if not current_match:
                                    schema_matches = False
                                    break
                            
                            # Wenn nicht alle Schemas erfüllt sind, leere die matched_schema_objs
                            if not schema_matches:
                                matched_schema_objs = []
                        else:
                            # ODER-Modus: Mindestens ein Schema muss erfüllt sein (bisheriges Verhalten)
                            schema_matches = False
                            for schema_obj in target_schemas:
                                target_schema = schema_obj['schema']
                                is_prefix_match = schema_obj['is_prefix']
                                
                                if is_prefix_match:
                                    # Präfix-Match: Ziel-Schema muss am Anfang des Produkt-Schemas stehen
                                    if len(product_schema) >= len(target_schema):
                                        if product_schema[:len(target_schema)] == target_schema:
                                            schema_matches = True
                                            matched_schema_objs.append(schema_obj)
                                            # Im ODER-Modus: Weiter suchen, um alle passenden Schemas zu sammeln
                                else:
                                    # Exakter Match
                                    if product_schema == target_schema:
                                        schema_matches = True
                                        matched_schema_objs.append(schema_obj)
                                        # Im ODER-Modus: Weiter suchen, um alle passenden Schemas zu sammeln
                    
                    # Kombiniere alle Filter-Bedingungen
                    all_positive_filters_match = (schema_matches and pattern_matches and position_matches and 
                                               group_start_matches and group_matches and contains_matches and 
                                               group_content_matches and group_count_matches and group_position_matches)
                    
                    # Bestimme finale Bedingung basierend auf negate_exclude Flag
                    if negate_exclude:
                        # Negiert: Finde Produkte die NICHT alle positiven Filter erfüllen ODER die Exclude-Kriterien erfüllen
                        final_condition = not all_positive_filters_match or exclude_matches
                    else:
                        # Normal: Alle positiven Filter müssen erfüllt sein UND Exclude-Filter dürfen nicht matchen
                        final_condition = all_positive_filters_match and not exclude_matches
                    
                    if final_condition:
                        product_info = {
                            'full_typecode': full_typecode,
                            'code_path': current_path,
                            'schema': product_schema,
                            'matched_schema_objs': matched_schema_objs,
                            'type': 'leaf' if is_leaf else 'intermediate',
                            'position': node.get('position'),
                            'code_parts': code_parts,
                            'family': current_family
                        }
                        
                        # Füge Datumsangaben hinzu falls gewünscht
                        if include_dates and 'date_info' in node:
                            product_info['date_info'] = node['date_info']
                        
                        matching_products.append(product_info)
        
        # Rekursiv für alle Children (auch Pattern-Knoten durchlaufen)
        # Nur durchlaufen wenn Familie nicht übersprungen wird
        if not skip_family:
            for child in node.get('children', []):
                traverse_node(child, current_path, current_family, depth + 1)
    
    # Starte Traversierung
    traverse_node(data)
    
    return {
        'target_schemas': target_schemas,
        'pattern_rules': pattern_rules,
        'position_rules': position_rules,
        'group_start_rules': group_start_rules,
        'group_rules': group_rules,
        'contains_rules': contains_rules,
        'group_content_rules': group_content_rules,
        'group_position_rules': group_position_rules,
        'analyze_group_position': analyze_group_position,
        'exclude_group_rules': exclude_group_rules,
        'exclude_position_rules': exclude_position_rules,
        'exclude_contains_rules': exclude_contains_rules,
        'negate_exclude': negate_exclude,
        'group_count_config': group_count_config,
        'prefix_match': prefix_match,
        'and_mode': and_mode,
        'product_family_filter': product_family,
        'searched_families': searched_families,
        'matching_products': matching_products,
        'match_count': len(matching_products),
        'total_products_checked': total_products_checked,
        'match_percentage': round(len(matching_products) / total_products_checked * 100, 2) if total_products_checked > 0 else 0
    }


def export_filter_criteria(results, output_file=None):
    """
    Exportiert die verwendeten Filter-Kriterien als JSON für label_mapper.py.
    
    Args:
        results: Ergebnisse von find_products_by_schema
        output_file: Ausgabe-Datei (optional, sonst filter_criteria.json)
        
    Returns:
        str: Pfad der erstellten Datei
    """
    if output_file is None:
        output_file = "filter_criteria.json"
    
    # Erstelle Filter-Kriterien-Struktur
    filter_criteria = {}
    
    # Produktfamilie
    if results.get('product_family_filter'):
        filter_criteria['family'] = results['product_family_filter']
    
    # Schemas
    if results.get('target_schemas'):
        schemas = []
        for schema_obj in results['target_schemas']:
            schema_str = str(schema_obj['schema']).replace(' ', '')
            if schema_obj['is_prefix']:
                schema_str += ':prefix'
            schemas.append(schema_str)
        
        if len(schemas) == 1:
            filter_criteria['schemas'] = schemas[0]
        else:
            filter_criteria['schemas'] = schemas
    
    # Pattern-Filter
    if results.get('pattern_rules'):
        pattern_parts = []
        for rule in results['pattern_rules']:
            pos = "last" if rule['position'] == 'last' else str(rule['position'])
            negate = rule.get('negate', False)
            operator = '!=' if negate else '='
            
            if rule['min_len'] == rule['max_len']:
                pattern_parts.append(f"{pos}{operator}{rule['min_len']}")
            else:
                pattern_parts.append(f"{pos}{operator}{rule['min_len']}-{rule['max_len']}")
        filter_criteria['pattern'] = ','.join(pattern_parts)
    
    # Position-Filter
    if results.get('position_rules'):
        position_parts = []
        for rule in results['position_rules']:
            value_str = rule['value']
            if rule.get('is_prefix', False):
                value_str += ':prefix'
            position_parts.append(f"{rule['position']}={value_str}")
        filter_criteria['position'] = ','.join(position_parts)
    
    # Gruppen-Start-Filter
    if results.get('group_start_rules'):
        group_start_parts = []
        for rule in results['group_start_rules']:
            group_start_parts.append(f"{rule['group']}={rule['start_position']}")
        filter_criteria['group_start'] = ','.join(group_start_parts)
    
    # Gruppen-Filter
    if results.get('group_rules'):
        group_parts = []
        for family, groups in results['group_rules'].items():
            if family == 'default':
                # Für default Familie: einfach alle Gruppen komma-getrennt
                group_parts.extend(groups)
            else:
                # Für spezifische Familie: Familie=Gruppe für jede Gruppe
                for group in groups:
                    group_parts.append(f"{family}={group}")
        filter_criteria['group'] = ','.join(group_parts)
    
    # UND-Modus
    if results.get('and_mode'):
        filter_criteria['and_mode'] = True
    
    # Gruppen-Anzahl-Filter (erweitert)
    if results.get('group_count_config') is not None:
        config = results['group_count_config']
        if config['type'] == 'exact':
            filter_criteria['group_count'] = str(config['value'])
        elif config['type'] == 'greater':
            filter_criteria['group_count'] = f">{config['value']}"
        elif config['type'] == 'greater_equal':
            filter_criteria['group_count'] = f">={config['value']}"
        elif config['type'] == 'less':
            filter_criteria['group_count'] = f"<{config['value']}"
        elif config['type'] == 'less_equal':
            filter_criteria['group_count'] = f"<={config['value']}"
        elif config['type'] == 'range':
            filter_criteria['group_count'] = f"{config['min']}-{config['max']}"
        elif config['type'] == 'multiple':
            filter_criteria['group_count'] = ','.join(map(str, config['values']))
    
    # Contains-Filter
    if results.get('contains_rules'):
        contains_parts = []
        
        # Gruppiere nach or_group
        or_groups = {}
        and_rules = []
        
        for rule in results['contains_rules']:
            or_group = rule['or_group']
            if or_group == 0:
                and_rules.append(rule)
            else:
                if or_group not in or_groups:
                    or_groups[or_group] = []
                or_groups[or_group].append(rule)
        
        # UND-Regeln
        for rule in and_rules:
            value_str = rule['value']
            if rule.get('case_sensitive', False):
                value_str += ':case'
            contains_parts.append(value_str)
        
        # ODER-Gruppen
        for or_group_id, or_rules in or_groups.items():
            or_values = []
            for rule in or_rules:
                value_str = rule['value']
                if rule.get('case_sensitive', False):
                    value_str += ':case'
                or_values.append(value_str)
            contains_parts.append('|'.join(or_values))
        
        filter_criteria['contains'] = ','.join(contains_parts)
    
    # Gruppen-Inhalt-Filter
    if results.get('group_content_rules'):
        group_content_parts = []
        for rule in results['group_content_rules']:
            value_str = rule['value']
            if rule.get('is_prefix', False):
                value_str += ':prefix'
            group_content_parts.append(f"{rule['group']}={value_str}")
        filter_criteria['group_content'] = ','.join(group_content_parts)
    
    # Gruppen-Position-Filter mit OR-Verknüpfung
    if results.get('group_position_rules'):
        or_groups = []
        for or_group in results['group_position_rules']:
            # Jede OR-Gruppe ist eine Liste von AND-Regeln
            and_parts = []
            for rule in or_group:
                is_negate = rule.get('negate', False)
                negate_prefix = '!=' if is_negate else '='
                is_prefix = rule.get('is_prefix', False)
                prefix_text = ":prefix" if is_prefix else ""
                
                if rule.get('explicit_range', False):
                    and_parts.append(f"{rule['group']}:{rule['start_pos']}-{rule['end_pos']}{negate_prefix}{rule['value']}{prefix_text}")
                else:
                    and_parts.append(f"{rule['group']}:{rule['start_pos']}{negate_prefix}{rule['value']}{prefix_text}")
            # AND-Regeln mit Komma verbinden
            or_groups.append(','.join(and_parts))
        # OR-Gruppen mit Pipe verbinden
        filter_criteria['group_position'] = '|'.join(or_groups)
    
    # Exclude-Gruppen-Filter
    if results.get('exclude_group_rules'):
        exclude_group_parts = []
        for rule in results['exclude_group_rules']:
            value_str = rule['value']
            if rule.get('is_prefix', False):
                value_str += ':prefix'
            exclude_group_parts.append(f"{rule['group']}={value_str}")
        filter_criteria['exclude_group'] = ','.join(exclude_group_parts)
    
    # Exclude-Position-Filter
    if results.get('exclude_position_rules'):
        exclude_position_parts = []
        for rule in results['exclude_position_rules']:
            value_str = rule['value']
            if rule.get('is_prefix', False):
                value_str += ':prefix'
            exclude_position_parts.append(f"{rule['position']}={value_str}")
        filter_criteria['exclude_position'] = ','.join(exclude_position_parts)
    
    # Exclude-Contains-Filter
    if results.get('exclude_contains_rules'):
        exclude_contains_parts = []
        
        # Gruppiere nach or_group
        or_groups = {}
        and_rules = []
        
        for rule in results['exclude_contains_rules']:
            or_group = rule['or_group']
            if or_group == 0:
                and_rules.append(rule)
            else:
                if or_group not in or_groups:
                    or_groups[or_group] = []
                or_groups[or_group].append(rule)
        
        # UND-Regeln
        for rule in and_rules:
            value_str = rule['value']
            if rule.get('case_sensitive', False):
                value_str += ':case'
            exclude_contains_parts.append(value_str)
        
        # ODER-Gruppen
        for or_group_id, or_rules in or_groups.items():
            or_values = []
            for rule in or_rules:
                value_str = rule['value']
                if rule.get('case_sensitive', False):
                    value_str += ':case'
                or_values.append(value_str)
            exclude_contains_parts.append('|'.join(or_values))
        
        filter_criteria['exclude_contains'] = ','.join(exclude_contains_parts)
    
    # Negate-Flag
    if results.get('negate_exclude'):
        filter_criteria['negate'] = True
    
    # Erstelle vollständige Struktur für label_mapper.py
    export_data = {
        "filter_criteria": filter_criteria,
        "code_mappings": [
            {
                "position": 1,
                "codes": ["EXAMPLE_CODE"],
                "labels": ["EXAMPLE LABEL - Bitte ersetzen"]
            }
        ],
        "metadata": {
            "description": "Auto-generated filter criteria from schema_search.py",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0",
            "search_results": {
                "match_count": results['match_count'],
                "total_products_checked": results['total_products_checked'],
                "match_percentage": results['match_percentage']
            }
        }
    }
    
    # Generiere automatisch group_mappings basierend auf group_position Filtern oder analyze_group_position
    if results.get('group_position_rules') or results.get('analyze_group_position'):
        group_mappings = []
        
        # Analysiere gefundene Produkte um unique Werte zu sammeln
        position_values = {}  # group_position -> set von unique values
        
        # Bestimme welche Positionen analysiert werden sollen
        positions_to_analyze = []
        
        if results.get('group_position_rules'):
            # Verwende group_position_rules (verschachtelte OR-Struktur)
            for or_group in results['group_position_rules']:
                for rule in or_group:
                    positions_to_analyze.append({
                        'group_num': rule['group'],
                        'start_pos': rule['start_pos'],
                        'end_pos': rule['end_pos'],
                        'source': 'filter'
                    })
        
        if results.get('analyze_group_position'):
            # Verwende analyze_group_position
            analyze_config = results['analyze_group_position']
            positions_to_analyze.append({
                'group_num': analyze_config['group'],
                'start_pos': analyze_config['start_pos'],
                'end_pos': analyze_config['end_pos'],
                'source': 'analyze'
            })
        
        for product in results.get('matching_products', []):
            code_parts = product.get('code_parts', [])
            
            for pos_config in positions_to_analyze:
                group_num = pos_config['group_num']
                start_pos = pos_config['start_pos']
                end_pos = pos_config['end_pos']
                
                # Prüfe ob die Gruppe existiert
                if group_num <= len(code_parts):
                    group_content = code_parts[group_num - 1]  # 0-based index
                    
                    # Extrahiere den Wert an der spezifizierten Position
                    if start_pos <= len(group_content):
                        if end_pos <= len(group_content):
                            extracted_value = group_content[start_pos-1:end_pos]  # 0-based slicing
                            
                            # Erstelle eindeutigen Schlüssel für diese Gruppe-Position-Kombination
                            key = f"group_{group_num}_pos_{start_pos}"
                            if end_pos > start_pos:
                                key += f"_to_{end_pos}"
                            
                            if key not in position_values:
                                position_values[key] = {
                                    'values': set(),
                                    'group_num': group_num,
                                    'start_pos': start_pos,
                                    'end_pos': end_pos,
                                    'source': pos_config['source']
                                }
                            
                            position_values[key]['values'].add(extracted_value)
        
        # Erstelle group_mappings für jede gefundene Position
        for key, data in position_values.items():
            unique_values = sorted(list(data['values']))
            
            # Für analyze_group_position: Zeige alle gefundenen Werte
            # Für group_position_rules: Nur wenn es mehrere verschiedene Werte gibt
            if data['source'] == 'analyze' or len(unique_values) > 1:
                # Erstelle Labels basierend auf den Werten
                if data['end_pos'] > data['start_pos']:
                    labels = [f"Group {data['group_num']} Position {data['start_pos']}-{data['end_pos']} = '{value}'" for value in unique_values]
                else:
                    labels = [f"Group {data['group_num']} Position {data['start_pos']} = '{value}'" for value in unique_values]
                
                group_mapping = {
                    "group": data['group_num'],
                    "position": data['start_pos'],
                    "codes": unique_values,
                    "labels": labels
                }
                
                # Füge end_position hinzu wenn es ein Bereich ist
                if data['end_pos'] > data['start_pos']:
                    group_mapping["end_position"] = data['end_pos']
                
                group_mappings.append(group_mapping)
        
        # Füge group_mappings zum Export hinzu, wenn welche gefunden wurden
        if group_mappings:
            export_data["group_mappings"] = group_mappings
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_file
    except Exception as e:
        print(f"❌ Fehler beim Exportieren: {e}")
        return None


def print_results(results, show_details=False):
    """
    Druckt die Suchergebnisse formatiert aus.
    
    Args:
        results: Ergebnisse von find_products_by_schema
        show_details: Ob Details der gefundenen Produkte angezeigt werden sollen
    """
    print(f"=== SCHEMA-SUCHE ERGEBNISSE ===")
    if results.get('target_schemas'):
        if len(results['target_schemas']) == 1:
            schema_obj = results['target_schemas'][0]
            prefix_suffix = ':prefix' if schema_obj['is_prefix'] else ''
            print(f"Gesuchtes Schema: {schema_obj['schema']}{prefix_suffix}")
        else:
            schema_strs = []
            for schema_obj in results['target_schemas']:
                prefix_suffix = ':prefix' if schema_obj['is_prefix'] else ''
                schema_strs.append(f"{schema_obj['schema']}{prefix_suffix}")
            print(f"Gesuchte Schemas: {', '.join(schema_strs)}")
    if results.get('pattern_rules'):
        pattern_desc = []
        for rule in results['pattern_rules']:
            pos = "letzte" if rule['position'] == 'last' else f"{rule['position']}."
            negate = rule.get('negate', False)
            operator_text = " ≠ " if negate else " = "
            
            if rule['min_len'] == rule['max_len']:
                pattern_desc.append(f"{pos} Gruppe{operator_text}{rule['min_len']}")
            else:
                pattern_desc.append(f"{pos} Gruppe{operator_text}{rule['min_len']}-{rule['max_len']}")
        print(f"Pattern-Filter: {', '.join(pattern_desc)}")
    
    if results.get('position_rules'):
        position_desc = []
        for rule in results['position_rules']:
            if rule.get('is_prefix', False):
                position_desc.append(f"Pos {rule['position']} beginnt mit '{rule['value']}'")
            else:
                position_desc.append(f"Pos {rule['position']} = '{rule['value']}' (exakt)")
        print(f"Position-Filter: {', '.join(position_desc)}")
    
    if results.get('group_start_rules'):
        group_start_desc = []
        for rule in results['group_start_rules']:
            group_start_desc.append(f"Gruppe {rule['group']} startet bei Pos {rule['start_position']}")
        print(f"Gruppen-Start-Filter: {', '.join(group_start_desc)}")
    
    if results.get('group_rules'):
        group_desc = []
        for family, groups in results['group_rules'].items():
            if family == 'default':
                if len(groups) == 1:
                    group_desc.append(f"Gruppe = '{groups[0]}' (alle Familien)")
                else:
                    group_desc.append(f"Gruppe = '{' oder '.join(groups)}' (alle Familien)")
            else:
                if len(groups) == 1:
                    group_desc.append(f"{family} = '{groups[0]}'")
                else:
                    group_desc.append(f"{family} = '{' oder '.join(groups)}'")
        print(f"Gruppen-Filter: {', '.join(group_desc)}")
    
    # Gruppen-Anzahl-Filter (erweitert)
    if results.get('group_count_config') is not None:
        config = results['group_count_config']
        if config['type'] == 'exact':
            count = config['value']
            print(f"Gruppen-Anzahl-Filter: Genau {count} {'Gruppe' if count == 1 else 'Gruppen'}")
        elif config['type'] == 'greater':
            print(f"Gruppen-Anzahl-Filter: Mehr als {config['value']} Gruppen")
        elif config['type'] == 'greater_equal':
            print(f"Gruppen-Anzahl-Filter: {config['value']} oder mehr Gruppen")
        elif config['type'] == 'less':
            print(f"Gruppen-Anzahl-Filter: Weniger als {config['value']} Gruppen")
        elif config['type'] == 'less_equal':
            print(f"Gruppen-Anzahl-Filter: {config['value']} oder weniger Gruppen")
        elif config['type'] == 'range':
            print(f"Gruppen-Anzahl-Filter: Zwischen {config['min']} und {config['max']} Gruppen")
        elif config['type'] == 'multiple':
            values_str = ', '.join(map(str, config['values']))
            print(f"Gruppen-Anzahl-Filter: Genau {values_str} Gruppen")
    
    if results.get('contains_rules'):
        contains_desc = []
        
        # Gruppiere nach or_group für bessere Anzeige
        or_groups = {}
        and_rules = []
        
        for rule in results['contains_rules']:
            or_group = rule['or_group']
            if or_group == 0:
                and_rules.append(rule)
            else:
                if or_group not in or_groups:
                    or_groups[or_group] = []
                or_groups[or_group].append(rule)
        
        # UND-Regeln anzeigen
        for rule in and_rules:
            case_info = " (case-sensitive)" if rule.get('case_sensitive', False) else ""
            contains_desc.append(f"Code enthält '{rule['value']}'{case_info}")
        
        # ODER-Gruppen anzeigen
        for or_group_id, or_rules in or_groups.items():
            or_values = []
            for rule in or_rules:
                case_info = " (case-sensitive)" if rule.get('case_sensitive', False) else ""
                or_values.append(f"'{rule['value']}'{case_info}")
            contains_desc.append(f"Code enthält ({' ODER '.join(or_values)})")
        
        print(f"Contains-Filter: {', '.join(contains_desc)}")
    
    if results.get('group_content_rules'):
        group_content_desc = []
        for rule in results['group_content_rules']:
            if rule.get('is_prefix', False):
                group_content_desc.append(f"Gruppe {rule['group']} beginnt mit '{rule['value']}'")
            else:
                group_content_desc.append(f"Gruppe {rule['group']} = '{rule['value']}' (exakt)")
        print(f"Gruppen-Inhalt-Filter: {', '.join(group_content_desc)}")
    
    if results.get('group_position_rules'):
        group_position_desc = []
        for or_idx, or_group in enumerate(results['group_position_rules']):
            # Jede OR-Gruppe ist eine Liste von AND-Regeln
            and_parts = []
            for rule in or_group:
                negate = rule.get('negate', False)
                is_prefix = rule.get('is_prefix', False)
                operator_text = " ≠ " if negate else " = "
                prefix_text = "beginnt mit " if is_prefix else ""
                if rule.get('explicit_range', False):
                    and_parts.append(f"Gruppe {rule['group']} Position {rule['start_pos']}-{rule['end_pos']} {operator_text} {prefix_text}'{rule['value']}'")
                else:
                    and_parts.append(f"Gruppe {rule['group']} Position {rule['start_pos']} {operator_text} {prefix_text}'{rule['value']}'")
            # Wenn mehr als eine OR-Gruppe existiert, gruppiere mit Klammern
            if len(results['group_position_rules']) > 1:
                group_position_desc.append(f"({' UND '.join(and_parts)})")
            else:
                group_position_desc.extend(and_parts)
        # Verbinde OR-Gruppen mit " ODER "
        print(f"Gruppen-Position-Filter: {' ODER '.join(group_position_desc)}")
    
    if results.get('prefix_match'):
        print(f"Match-Typ: Präfix-Match (findet auch längere Schemas)")
    elif results.get('target_schemas'):
        # Prüfe ob gemischte Match-Typen verwendet werden
        has_prefix = any(s['is_prefix'] for s in results['target_schemas'])
        has_exact = any(not s['is_prefix'] for s in results['target_schemas'])
        
        and_mode = results.get('and_mode', False)
        and_suffix = " (UND-Verknüpfung)" if and_mode else " (ODER-Verknüpfung)"
        
        if has_prefix and has_exact:
            print(f"Match-Typ: Gemischte Matches (exakt + präfix){and_suffix}")
        elif has_prefix:
            print(f"Match-Typ: Präfix-Match{and_suffix}")
        else:
            print(f"Match-Typ: Exakter Match{and_suffix}")
    else:
        print(f"Match-Typ: Filter-basierte Suche")
    if results.get('product_family_filter'):
        print(f"Produktfamilie: {results['product_family_filter']}")
        # Prüfe ob die Familie in den durchsuchten Familien ist
        if results['product_family_filter'] not in results.get('searched_families', []):
            print(f"❌ Produktfamilie '{results['product_family_filter']}' nicht gefunden!")
            print(f"Verfügbare Familien: {', '.join(results.get('searched_families', [])[:10])}")
            return
    else:
        families_found = results.get('searched_families', [])
        if families_found:
            print(f"Durchsuchte Produktfamilien: {len(families_found)} ({', '.join(families_found[:5])}{'...' if len(families_found) > 5 else ''})")
    
    print(f"Gefundene Produkte: {results['match_count']}")
    print(f"Geprüfte Produkte: {results['total_products_checked']}")
    print(f"Trefferquote: {results['match_percentage']}%")
    print()
    
    if results['match_count'] == 0:
        print("❌ Keine Produkte mit diesem Schema gefunden.")
        return
    
    # Gruppiere nach Typ
    leaves = [p for p in results['matching_products'] if p['type'] == 'leaf']
    intermediates = [p for p in results['matching_products'] if p['type'] == 'intermediate']
    
    print(f"📊 Verteilung:")
    print(f"  - Endprodukte (Blätter): {len(leaves)}")
    print(f"  - Zwischenprodukte: {len(intermediates)}")
    print()
    
    if show_details:
        print("📋 DETAILS DER GEFUNDENEN PRODUKTE:")
        print()
        
        if leaves:
            print("🔹 ENDPRODUKTE:")
            for i, product in enumerate(leaves[0:], 1):  # Zeige maximal 10
                print(f"  {i}. {product['full_typecode']}")
                # print(f"     Teile: {' → '.join(product['code_parts'])}")
                if show_details and product.get('matched_schema_objs'):
                    # Zeige alle gematchten Schemas
                    matched_info = []
                    for schema_obj in product['matched_schema_objs']:
                        if schema_obj['is_prefix'] and product['schema'] != schema_obj['schema']:
                            matched_info.append(f"präfix {schema_obj['schema']}")
                        else:
                            matched_info.append(f"exakt {schema_obj['schema']}")
                    if matched_info:
                        print(f"     Schema: {product['schema']} (erfüllt: {', '.join(matched_info)})")
                if 'date_info' in product:
                    date_info = product['date_info']
                    if 'creation_date' in date_info:
                        print(f"     Erstellt: {date_info['creation_date']['earliest']}")
                print()
            
            # if len(leaves) > 10:
            #     print(f"     ... und {len(leaves) - 10} weitere Endprodukte")
            #     print()
        
        if intermediates:
            print("🔹 ZWISCHENPRODUKTE:")
            for i, product in enumerate(intermediates[0:], 1):  # Zeige maximal 5
                print(f"  {i}. {product['full_typecode']}")
                # print(f"     Teile: {' → '.join(product['code_parts'])}")
                if show_details and product.get('matched_schema_objs'):
                    # Zeige alle gematchten Schemas
                    matched_info = []
                    for schema_obj in product['matched_schema_objs']:
                        if schema_obj['is_prefix'] and product['schema'] != schema_obj['schema']:
                            matched_info.append(f"präfix {schema_obj['schema']}")
                        else:
                            matched_info.append(f"exakt {schema_obj['schema']}")
                    if matched_info:
                        print(f"     Schema: {product['schema']} (erfüllt: {', '.join(matched_info)})")
                if 'date_info' in product:
                    date_info = product['date_info']
                    if 'creation_date' in date_info:
                        print(f"     Erstellt: {date_info['creation_date']['earliest']}")
                print()
            
            # if len(intermediates) > 5:
            #     print(f"     ... und {len(intermediates) - 5} weitere Zwischenprodukte")
    else:
        # Zeige nur erste paar Beispiele
        print("📋 BEISPIELE (verwende --details für vollständige Liste):")
        examples = results['matching_products'][:5]
        for i, product in enumerate(examples, 1):
            print(f"  {i}. {product['full_typecode']} ({product['type']})")
        
        if len(results['matching_products']) > 5:
            print(f"     ... und {len(results['matching_products']) - 5} weitere")


def main():
    parser = argparse.ArgumentParser(
        description='Suche nach Produkten mit einem bestimmten Schema im Variantenbaum',
        epilog='''
Beispiele:
  %(prog)s [3,3,3,4]                         # Suche nach Schema [3,3,3,4] (exakt)
  %(prog)s [3,3,3,4] [4,4,3,4]               # Suche nach zwei exakten Schemas (ODER)
  %(prog)s [4,4]:prefix                      # Finde alle Schemas die mit [4,4] beginnen
  %(prog)s [3,3,3,4] [4,4]:prefix            # Exaktes [3,3,3,4] ODER Präfix [4,4]
  %(prog)s [3,3,3,4] [4,4]:prefix --and      # Exaktes [3,3,3,4] UND Präfix [4,4] (beide erforderlich!)
  %(prog)s [4,4]:prefix [4,4,3]:prefix       # ODER: Präfix [4,4] ODER Präfix [4,4,3]
  %(prog)s [4,4]:prefix [4,4,3]:prefix --and # UND: Präfix [4,4] UND Präfix [4,4,3] (beide erforderlich!)
  %(prog)s [3,3]:prefix [4,4]:prefix [5,5]   # ODER: Zwei Prefixe ODER ein exaktes Schema
  %(prog)s [3,3]:prefix [4,4]:prefix [5,5] --and # UND: Alle drei Schemas müssen erfüllt sein
  %(prog)s --pattern "1=3,2=4"               # 1. Gruppe = 3 UND 2. Gruppe = 4 Zeichen
  %(prog)s --position "5=M,11=PX"            # Position 5 = 'M' (exakt) UND Position 11 = 'PX' (exakt)
  %(prog)s --position "5=M423,22=PX0334"     # Längere Strings: Position 5-8='M423', 22-27='PX0334' (exakt)
  %(prog)s --position "5=M:prefix"           # Position 5 beginnt mit 'M' (z.B. M1234, M567, etc.)
  %(prog)s --position "5=M:prefix,11=PX"     # Position 5 Präfix 'M' UND Position 11 exakt 'PX'
  %(prog)s --group-start "1=5,2=9"           # 1. Gruppe startet bei Pos 5, 2. bei Pos 9
  %(prog)s --group "Typ1"                    # Alle Produkte mit group='Typ1'
  %(prog)s --group "BCC=Typ1"                # BCC-Produkte mit group='Typ1'
  %(prog)s --group "BCC=Typ1,BES=Typ2"       # BCC mit 'Typ1' UND BES mit 'Typ2'
  %(prog)s [3,3,3,4] [4,4]:prefix -f BCC --and # Exakt + Präfix nur für BCC-Familie (UND)
  %(prog)s --group-count 3                   # Nur Produkte mit genau 3 Gruppen
  %(prog)s --group-count 2 -f A              # Familie A mit genau 2 Gruppen
  %(prog)s --contains "M313"                 # Code enthält "M313"
  %(prog)s --contains "M314|M111" -f BCC     # BCC-Familie: Code enthält M314 ODER M111
  %(prog)s --contains "M313,PX"              # Code enthält "M313" UND "PX" (beide!)
  %(prog)s --contains "M313,PX|050"          # Code enthält M313 UND (PX ODER 050)
  %(prog)s --contains "M313:case"            # Case-sensitive Suche nach "M313"
  %(prog)s --contains "0334,M423"            # Code enthält sowohl "0334" als auch "M423"
  %(prog)s --group-content "1=M313"          # Gruppe 1 = 'M313' (exakt)
  %(prog)s --group-content "1=M:prefix"      # Gruppe 1 beginnt mit 'M' (z.B. M123, M456, etc.)
  %(prog)s --group-content "1=M:prefix,2=0000" # Gruppe 1 beginnt mit 'M' UND Gruppe 2 = '0000'
  %(prog)s --group-content "1=M313,3=050"    # Gruppe 1 = 'M313' UND Gruppe 3 = '050'
  %(prog)s --pattern "1=4" --group-content "1=M:prefix" -f BCC # 4-stellige erste Gruppe die mit 'M' beginnt
                                             # Vollständiges UND-Beispiel mit allen Filtern
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('schemas', nargs='*',
                       help='Die gesuchten Schemas, z.B. "[3,3,3,4]" "[4,4]:prefix" oder "3,3,3,4" (optional wenn Filter verwendet werden)')
    parser.add_argument('--pattern',
                       help='Pattern-Filter, z.B. "1=3,2=4" (gleich), "1=3-5,last=6" (Bereich), "3!=2" (ungleich), "3!=2-4" (nicht im Bereich)')
    parser.add_argument('--position',
                       help='Absolute Position-Filter, z.B. "5=M,11=PX" (exakt) oder "5=M:prefix" (beginnt mit), "5=M423,22=PX0334" (Position im gesamten Code)')
    parser.add_argument('--group-start',
                       help='Gruppen-Start-Position-Filter, z.B. "1=5,2=9" (Gruppe X startet bei Position Y)')
    parser.add_argument('--group',
                       help='Gruppen-Filter, z.B. "Typ1" (alle), "BCC=Typ1" (nur BCC), "BCC=Typ1,BES=Typ2" (mehrere Familien)')
    parser.add_argument('--group-count',
                       help='Erweiterte Gruppen-Anzahl-Filter, z.B. "3" (exakt), ">3" (mehr als), ">=4" (min), "<5" (weniger als), "<=3" (max), "2-5" (Bereich), "3,5,7" (mehrere)')
    parser.add_argument('--contains',
                       help='Contains-Filter für Code-Teil (ohne Familie), z.B. "M313" (einzeln), "M313,PX" (M313 UND PX), "M314|M111" (M314 ODER M111), "M313,PX|050" (M313 UND (PX ODER 050))')
    parser.add_argument('--group-content',
                       help='Gruppen-Inhalt-Filter, z.B. "1=M313" (Gruppe 1 exakt), "1=M:prefix" (Gruppe 1 beginnt mit M), "1=M313,2=PX" (Gruppe 1=M313 UND Gruppe 2=PX)')
    parser.add_argument('--group-position',
                       help='Gruppen-Position-Filter mit OR-Verknüpfung, z.B. "3:1=M" (einzeln), "3:1=M,4:2=PX" (UND), "3:1=M|5:1=P" (ODER), "1:2=A,2:1=X|3:1=BD" (komplexe OR-UND-Kombination)')
    parser.add_argument('--analyze-group-position',
                       help='Analysiere alle einzigartigen Werte an Gruppen-Position, z.B. "3:1" (alle Werte an Gruppe 3 Position 1), "3:1-2" (alle 2-Zeichen-Werte ab Position 1)')
    parser.add_argument('--exclude-group',
                       help='Exclude-Gruppen-Filter, z.B. "1=Z" (schließe aus wenn Gruppe 1 = Z), "1=Z:prefix" (schließe aus wenn Gruppe 1 beginnt mit Z)')
    parser.add_argument('--exclude-position',
                       help='Exclude-Position-Filter, z.B. "5=Z" (schließe aus wenn Position 5 = Z), "5=Z:prefix" (schließe aus wenn Position 5 beginnt mit Z)')
    parser.add_argument('--exclude-contains',
                       help='Exclude-Contains-Filter, z.B. "Z" (schließe aus wenn Z im Code), "Z&custom" (UND), "Z|special" (ODER in Gruppe 1)')
    parser.add_argument('--family', '-f',
                       help='Beschränke Suche auf diese Produktfamilie (z.B. BNI, BES, BOH)')
    parser.add_argument('--prefix', '-p',
                       action='store_true',
                       help='Präfix-Match: Finde auch Produkte mit längeren Schemas, die das gesuchte Schema als Präfix haben')
    parser.add_argument('--and',
                       action='store_true',
                       dest='and_mode',
                       help='UND-Verknüpfung: ALLE angegebenen Schemas müssen erfüllt sein (Standard: ODER-Verknüpfung)')
    parser.add_argument('--negate',
                       action='store_true',
                       help='Negiere alle Filter: Kehrt die Logik aller Filter um (finde Produkte die NICHT den Kriterien entsprechen)')
    parser.add_argument('--with-dates', 
                       action='store_true',
                       help='Verwende JSON-Datei mit Datumsangaben')
    parser.add_argument('--details', 
                       action='store_true',
                       help='Zeige detaillierte Informationen zu den gefundenen Produkten')
    parser.add_argument('--export-filter', 
                       help='Exportiere Filter-Kriterien als JSON für label_mapper.py (z.B. --export-filter filter_bcc.json)')
    
    args = parser.parse_args()
    
    # Parse Schemas (optional wenn --pattern verwendet wird)
    target_schemas = None
    if args.schemas:
        target_schemas = parse_multiple_schemas(args.schemas)
        if target_schemas is None:
            print("❌ Fehler: Ungültiges Schema-Format!")
            print("Verwende Format: [3,3,3,4] oder 3,3,3,4")
            print("Für Präfix-Match: [4,4]:prefix")
            print("Mehrere Schemas: [3,3,3,4] [4,4]:prefix [2,2,2]")
            sys.exit(1)
    
    # Parse Pattern-Filter
    pattern_rules = None
    if args.pattern:
        pattern_rules = parse_pattern_filter(args.pattern)
        if pattern_rules is None:
            print("❌ Fehler: Ungültiges Pattern-Format!")
            print("Verwende Format: '1=3,2=4' oder '1=3-5,last=6'")
            print("Beispiele:")
            print("  1=3       → 1. Gruppe = 3 Zeichen")
            print("  1=3-5     → 1. Gruppe = 3-5 Zeichen") 
            print("  last=6    → Letzte Gruppe = 6 Zeichen")
            print("  1=3,2=4   → 1. Gruppe = 3 UND 2. Gruppe = 4")
            sys.exit(1)
    
    # Parse Position-Filter
    position_rules = None
    if args.position:
        position_rules = parse_position_filter(args.position)
        if position_rules is None:
            print("❌ Fehler: Ungültiges Position-Format!")
            print("Verwende Format: '5=M,11=PX' oder '5=M423' oder '5=M:prefix'")
            print("Beispiele:")
            print("  5=M       → Position 5 im Code = 'M' (exakt)")
            print("  5=M:prefix → Position 5 im Code beginnt mit 'M' (z.B. M1234)")
            print("  5=M423    → Position 5-8 im Code = 'M423' (exakt)")
            print("  5=M,11=PX → Position 5 = 'M' (exakt) UND Position 11 = 'PX' (exakt)")
            print("  5=M:prefix,11=PX → Position 5 beginnt mit 'M' UND Position 11 = 'PX'")
            print("  5=M423,22=PX0334 → Mehrere längere Strings (exakt)")
            sys.exit(1)
    
    # Parse Gruppen-Start-Filter
    group_start_rules = None
    if args.group_start:
        group_start_rules = parse_group_start_filter(args.group_start)
        if group_start_rules is None:
            print("❌ Fehler: Ungültiges Gruppen-Start-Format!")
            print("Verwende Format: '1=5,2=9' oder '1=5'")
            print("Beispiele:")
            print("  1=5       → 1. Gruppe startet bei Position 5")
            print("  1=5,2=9   → 1. Gruppe bei Pos 5, 2. Gruppe bei Pos 9")
            sys.exit(1)
    
    # Parse Gruppen-Filter
    group_rules = None
    if args.group:
        group_rules = parse_group_filter(args.group)
        if group_rules is None:
            print("❌ Fehler: Ungültiges Gruppen-Format!")
            print("Verwende Format: 'Typ1' oder 'BCC=Typ1' oder 'BCC=Typ1,BES=Typ2'")
            print("Beispiele:")
            print("  Typ1          → Alle Produkte mit group='Typ1'")
            print("  BCC=Typ1      → Nur BCC-Produkte mit group='Typ1'")
            print("  BCC=Typ1,BES=Typ2 → BCC mit 'Typ1' UND BES mit 'Typ2'")
            sys.exit(1)
    
    # Parse Contains-Filter
    contains_rules = None
    if args.contains:
        contains_rules = parse_contains_filter(args.contains)
        if contains_rules is None:
            print("❌ Fehler: Ungültiges Contains-Format!")
            print("Verwende Format: 'M313' oder 'M314|M111' oder 'M313,PX|050'")
            print("Beispiele:")
            print("  M313          → Code enthält 'M313'")
            print("  M314|M111     → Code enthält 'M314' ODER 'M111'")
            print("  M313,PX       → Code enthält 'M313' UND 'PX'")
            print("  M313,PX|050   → Code enthält 'M313' UND ('PX' ODER '050')")
            print("  M313:case     → Case-sensitive Suche nach 'M313'")
            print("  0334,M423     → Code enthält sowohl '0334' als auch 'M423'")
            print()
            print("Syntax:")
            print("  , (Komma) = UND-Verknüpfung")
            print("  | (Pipe)  = ODER-Verknüpfung")
            print("  Familie wird über -f BCC gefiltert (nicht über contains!)")
            sys.exit(1)
    
    # Parse Gruppen-Inhalt-Filter
    group_content_rules = None
    if args.group_content:
        group_content_rules = parse_group_content_filter(args.group_content)
        if group_content_rules is None:
            print("❌ Fehler: Ungültiges Gruppen-Inhalt-Format!")
            print("Verwende Format: '1=M313' oder '1=M:prefix' oder '1=M313,2=PX'")
            print("Beispiele:")
            print("  1=M313        → Gruppe 1 = 'M313' (exakt)")
            print("  1=M:prefix    → Gruppe 1 beginnt mit 'M' (z.B. M123, M456)")
            print("  2=PX          → Gruppe 2 = 'PX' (exakt)")
            print("  1=M:prefix,3=050 → Gruppe 1 beginnt mit 'M' UND Gruppe 3 = '050'")
            print("  1=M313,2=0000 → Gruppe 1 = 'M313' UND Gruppe 2 = '0000'")
            print()
            print("Hinweis: Gruppen sind die Code-Teile nach der Produktfamilie")
            print("Beispiel: BCC M423-0000-2A-002 → Gruppe 1='M423', Gruppe 2='0000', etc.")
            sys.exit(1)
    
    # Parse Gruppen-Position-Filter
    group_position_rules = None
    if hasattr(args, 'group_position') and args.group_position:
        group_position_rules = parse_group_position_filter(args.group_position)
        if group_position_rules is None:
            print("❌ Fehler: Ungültiges Gruppen-Position-Format!")
            print("Verwende Format: '3:1=M' oder '3:2=ABC' oder '3:1-3=M42' oder '3:1!=M42'")
            print("Beispiele:")
            print("  3:1=M         → In Gruppe 3 an Position 1 = 'M' (automatische Länge)")
            print("  3:2=ABC       → In Gruppe 3 an Position 2 = 'ABC' (automatische Länge)")
            print("  3:1-3=M42     → In Gruppe 3 von Position 1-3 = 'M42' (explizite Länge)")
            print("  3:1=M,4:2=PX  → Gruppe 3 Position 1='M' UND Gruppe 4 Position 2='PX'")
            print("  3:1=M|5:1=P   → Gruppe 3 Position 1='M' ODER Gruppe 5 Position 1='P'")
            print("  1:2=A,2:1=X|3:1=BD → (Gruppe 1 Pos 2='A' UND Gruppe 2 Pos 1='X') ODER (Gruppe 3 Pos 1='BD')")
            print("  3:1!=M42      → In Gruppe 3 an Position 1 ≠ 'M42' (Negation)")
            print()
            print("Hinweis: Relative Positionierung innerhalb von Gruppen")
            print("  | (Pipe)  = ODER-Verknüpfung zwischen Bedingungsgruppen")
            print("  , (Komma) = UND-Verknüpfung innerhalb einer Bedingungsgruppe")
            print("Beispiel: BCC M423-0000-2A-002 → Gruppe 3='2A', Position 1='2', Position 2='A'")
            sys.exit(1)
    
    # Parse Analyze-Gruppen-Position
    analyze_group_position = None
    if hasattr(args, 'analyze_group_position') and args.analyze_group_position:
        analyze_group_position = parse_analyze_group_position(args.analyze_group_position)
        if analyze_group_position is None:
            print("❌ Fehler: Ungültiges Analyze-Gruppen-Position-Format!")
            print("Verwende Format: '3:1' oder '3:1-2'")
            print("Beispiele:")
            print("  3:1           → Analysiere alle Werte an Gruppe 3 Position 1")
            print("  3:1-2         → Analysiere alle 2-Zeichen-Werte ab Gruppe 3 Position 1")
            print("  4:2           → Analysiere alle Werte an Gruppe 4 Position 2")
            print()
            print("Hinweis: Sammelt alle einzigartigen Werte an der Position für group_mappings")
            sys.exit(1)
    
    # Parse Exclude-Filter
    exclude_group_rules = None
    if args.exclude_group:
        exclude_group_rules = parse_exclude_group_filter(args.exclude_group)
        if exclude_group_rules is None:
            print("❌ Fehler: Ungültiges Exclude-Gruppen-Format!")
            print("Verwende Format: '1=Z' oder '1=Z:prefix' oder '1=Z,2=CUSTOM'")
            sys.exit(1)
    
    exclude_position_rules = None
    if args.exclude_position:
        exclude_position_rules = parse_exclude_position_filter(args.exclude_position)
        if exclude_position_rules is None:
            print("❌ Fehler: Ungültiges Exclude-Position-Format!")
            print("Verwende Format: '5=Z' oder '10=CUSTOM:prefix'")
            sys.exit(1)
    
    exclude_contains_rules = None
    if args.exclude_contains:
        exclude_contains_rules = parse_exclude_contains_filter(args.exclude_contains)
        if exclude_contains_rules is None:
            print("❌ Fehler: Ungültiges Exclude-Contains-Format!")
            print("Verwende Format: 'Z' oder 'Z&custom' oder 'Z|special'")
            sys.exit(1)
    
    # Parse erweiterten Group-Count-Filter
    group_count_config = None
    if args.group_count:
        group_count_config = parse_group_count_filter(args.group_count)
        if group_count_config is None:
            print("❌ Fehler: Ungültiges Gruppen-Anzahl-Format!")
            print("Verwende Format:")
            print("  '3'       → Exakt 3 Gruppen")
            print("  '>3'      → Mehr als 3 Gruppen")
            print("  '>=4'     → 4 oder mehr Gruppen")
            print("  '<5'      → Weniger als 5 Gruppen")
            print("  '<=3'     → 3 oder weniger Gruppen")
            print("  '2-5'     → Zwischen 2 und 5 Gruppen")
            print("  '3,5,7'   → Genau 3, 5 oder 7 Gruppen")
            sys.exit(1)
    
    # Validierung: Mindestens ein Filter erforderlich (außer wenn nur Familie-Filter)
    if (target_schemas is None and pattern_rules is None and 
        position_rules is None and group_start_rules is None and group_rules is None
        and contains_rules is None and group_content_rules is None and group_position_rules is None and args.family is None and group_count_config is None
        and exclude_group_rules is None and exclude_position_rules is None and exclude_contains_rules is None
        and analyze_group_position is None):
        print("❌ Fehler: Mindestens ein Filter muss angegeben werden!")
        print("Beispiele:")
        print("  py schema_search.py [3,3,3,4]")
        print("  py schema_search.py [3,3,3,4] [4,4]:prefix")
        print("  py schema_search.py --pattern '1=3,2=4'")
        print("  py schema_search.py --position '5=M'")
        print("  py schema_search.py --group-start '1=5'")
        print("  py schema_search.py --group 'Typ1'")
        print("  py schema_search.py --group-count 3")
        print("  py schema_search.py --contains 'M313'")
        print("  py schema_search.py --contains 'M314|M111' -f BCC")
        print("  py schema_search.py --contains 'M313,PX|050'")
        print("  py schema_search.py --group-content '1=M313'")
        print("  py schema_search.py --group-content '1=M:prefix,2=0000'")
        print("  py schema_search.py --exclude-group '1=Z'")
        print("  py schema_search.py --exclude-position '5=Z:prefix'")
        print("  py schema_search.py --exclude-contains 'Z|CUSTOM'")
        print("  py schema_search.py --exclude-group '1=Z:prefix' --negate  # Nur die mit Z am Anfang")
        print("  py schema_search.py --exclude-contains 'Z00' --negate -f BCC  # Nur BCC mit Z00")
        print("  py schema_search.py -f BCC  # Alle BCC-Produkte")
        sys.exit(1)
    
    # Wähle JSON-Datei in der die Suche durchgeführt wird
    json_file = JSONFILE
    # json_file = "output/variantenbaum_with_dates.json" if args.with_dates else "output/variantenbaum.json"
    
    if not Path(json_file).exists():
        print(f"❌ Fehler: Datei {json_file} nicht gefunden!")
        print("Führe zuerst createVariantenBaum.py aus.")
        sys.exit(1)
    
    # Lade JSON-Daten
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden der JSON-Datei: {e}")
        sys.exit(1)
    
    # Führe Suche durch
    results = find_products_by_schema(data, target_schemas, args.with_dates, args.family, args.prefix, 
                                    pattern_rules, position_rules, group_start_rules, group_rules, group_count_config,
                                    contains_rules, group_content_rules, group_position_rules, analyze_group_position, exclude_group_rules, exclude_position_rules, exclude_contains_rules, args.negate, args.and_mode)
    
    # Zeige Ergebnisse
    print_results(results, args.details)
    
    # Exportiere Filter-Kriterien falls gewünscht
    if args.export_filter:
        export_file = export_filter_criteria(results, args.export_filter)
        if export_file:
            print(f"\n📤 Filter-Kriterien exportiert: {export_file}")
            print(f"Verwende mit: python label_mapper.py {export_file}")


if __name__ == "__main__":
    main()