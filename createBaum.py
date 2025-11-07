import pandas as pd
from anytree import Node
import json
from pathlib import Path
import re
import os

INPUT_XLSX = "data.xlsx"

COL_TYPECODE = "TypeCode"
COL_CREATIONDATE = "CreationDate"
COL_MODIFICATIONDATE = "ModificationDate"

INCLUDE_DATES = False

def normalize_token(tok: str) -> str:
    if tok is None:
        return None
    
    t = str(tok)
    
    t = t.upper()
    return t if t else None

def parse_date_format(date_str: str):
    
    if not date_str or date_str == '0' or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    try:
        if len(date_str) == 7:
            day = int(date_str[0])
            month = int(date_str[1:3])
            year = int(date_str[3:])
        elif len(date_str) == 8:
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:])
        else:
            return None
        
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1990 <= year <= 2030):
            return None
        
        return {
            'original': date_str,
            'formatted': f"{day:02d}.{month:02d}.{year}",
            'iso': f"{year}-{month:02d}-{day:02d}",
            'year': year,
            'month': month,
            'day': day,
            'timestamp': year * 10000 + month * 100 + day
        }
        
    except (ValueError, IndexError):
        return None
    
    
def split_typecode(code: str):
    if not code or pd.isna(code):
        return []
    
    code_str = str(code).strip()
    if not code_str:
        return []
    
    dalimiter_pattern = r'_{2,}|[-\s]+|(?<=\w)_(?=\w)'
    
    parts = re.split(dalimiter_pattern, code_str)
    
    normalized_parts = []
    for part in parts:
        norm_part = normalize_token(part)
        if norm_part:
            normalized_parts.append(norm_part)
            
    return normalized_parts


def calculate_group_arrangement(sequence, max_len):
    group_lengths = [len(item) for item in sequence]

    group_lengths += [0] * (max_len - len(group_lengths))
    return group_lengths


def analyse_schema_by_product_family(typecodes):
    
    product_fammilies = {}
    
    for code in typecodes:
        parts = split_typecode(code)
        if len(parts) >= 2:
            product_family = parts[0]
            rest_parts = parts[1:]
            
            if product_family not in product_fammilies:
                product_fammilies[product_family] = []
                
            product_fammilies[product_family].append(rest_parts)
            
    family_schemas = {}
    for family, sequences in product_fammilies.items():
        max_len = max(len(seq) for seq in sequences) if sequences else 0
        
        schemas = []
        for sequence in sequences:
            schema = calculate_group_arrangement(sequence, max_len)
            schemas.append(tuple(schema))
            
        unique_schemas = list(set(schemas))
        
        family_schemas[family] = {
            'max_length': max_len,
            'schemas': unique_schemas,
            'schema_count': len(unique_schemas)
        }

    return family_schemas


def build_anytree(typecodes, creation_dates=None, modification_dates=None):
    root = Node("root")
    
    family_schemas = analyse_schema_by_product_family(typecodes)
    
    for code in typecodes:
        parts = split_typecode(code)
        
        if len(parts) < 2:
            continue
        
        prefix = parts[0]
        rest = parts[1:]
        
        max_len = family_schemas.get(prefix, {}).get('max_length', len(rest))
        schema = calculate_group_arrangement(rest, max_len)

        current_node = next((child for child in root.children if child.name == prefix), None)

        if current_node is None:
            current_node = Node(prefix, parent=root)
            current_node.group_name = ""
            current_node.position = 1
            current_node.node_type = "product_family"

            if creation_dates is not None or modification_dates is not None:
                current_node.creation_dates = []
                current_node.modification_dates = []
                current_node.typecode_count = 0
                
        if creation_dates and code in creation_dates:
            if not hasattr(current_node, 'creation_dates'):
                current_node.creation_dates = []
            current_node.creation_dates.append(creation_dates[code])
            
        if modification_dates and code in modification_dates:
            if not hasattr(current_node, 'modification_dates'):
                current_node.modification_dates = []
            current_node.modification_dates.append(modification_dates[code])
            
        if hasattr(current_node, 'typecode_count'):
            current_node.typecode_count += 1
            
        current_position = current_node.position + len(current_node.name) + 1
        
        for i, (part, length) in enumerate(zip(rest, schema)):
            if length == 0:
                break

            actual_part_length = len(part)
            
            pattern_node = next((child for child in current_node.children
                                 if getattr(child, 'is_pattern', False) and child.pattern_length == actual_part_length and child.pattern_position == i), None)
            
            if pattern_node is None:
                pattern_node = Node(f"len_{actual_part_length}", parent=current_node)
                pattern_node.group_name = ""
                pattern_node.is_pattern = True
                pattern_node.pattern_length = actual_part_length
                pattern_node.pattern_position = i
                pattern_node.position = current_position
                
                if creation_dates is not None or modification_dates is not None:
                    pattern_node.creation_dates = []
                    pattern_node.modification_dates = []
                    pattern_node.typecode_count = 0
                
            if creation_dates and code in creation_dates:
                if not hasattr(pattern_node, 'creation_dates'):
                    pattern_node.creation_dates = []
                pattern_node.creation_dates.append(creation_dates[code])

            if modification_dates and code in modification_dates:
                if not hasattr(pattern_node, 'modification_dates'):
                    pattern_node.modification_dates = []
                pattern_node.modification_dates.append(modification_dates[code])

            if hasattr(pattern_node, 'typecode_count'):
                pattern_node.typecode_count += 1
                
            part_node = next((child for child in pattern_node.children if child.name == part), None)
            if part_node is None:
                part_node = Node(part, parent=pattern_node)
                part_node.group_name = ""
                part_node.position = current_position
                part_node.node_type = "code_part"
                
                if creation_dates is not None or modification_dates is not None:
                    part_node.creation_dates = []
                    part_node.modification_dates = []
                    part_node.typecode_count = 0
                    
            if creation_dates and code in creation_dates:
                if not hasattr(part_node, 'creation_dates'):
                    part_node.creation_dates = []
                part_node.creation_dates.append(creation_dates[code])

            if modification_dates and code in modification_dates:
                if not hasattr(part_node, 'modification_dates'):
                    part_node.modification_dates = []
                part_node.modification_dates.append(modification_dates[code])

            if hasattr(part_node, 'typecode_count'):
                part_node.typecode_count += 1
            current_node = part_node
            current_position = current_node.position + len(current_node.name) + 1
            
    return root



def construct_full_typecode(node):
    
    path = []
    current = node
    while current.parent is not None:
        if current.name != "root":
            if not getattr(current, 'is_pattern', False):
                path.insert(0, current.name)
        current = current.parent
        
    if len(path) < 2:
        return None
    
    first_level = path[0]
    rest = path[1:]
    
    if rest:
        return f"{first_level} {'-'.join(rest)}"
    else:
        return first_level
    
    
    
def node_to_dict(node, excel_codes_set=None, include_dates=False):
    path = []
    current = node
    while current is not None and current.parent is not None:
        if current.name != "root":
            if not getattr(current, 'is_pattern', False):
                path.insert(0, current.name)
        current = current.parent

        if current is node:
            break
        
    is_intermediate_code = False
    if len(path) >= 2 and excel_codes_set:
        normalized_path = "-".join(path)
        is_intermediate_code = normalized_path in excel_codes_set
        
    result = {
        "children": [node_to_dict(child, excel_codes_set, include_dates) for child in node.children] if node.children else []
    }
    
    if getattr(node, 'is_pattern', False):
        result["pattern"] = node.pattern_length
        result["position"] = node.position
        result["name"] = getattr(node, 'group_name', "")
        
    else:
        result["code"] = node.name
        
        if node.name != "root":
            result["name"] = getattr(node, 'group_name', "")
            # result["code"] = node.name  # Add the actual code from node.name
            
        if node.name != "root":
            result["label"] = ""
            result["label-en"] = ""

        if node.name != "root" and hasattr(node, 'position'):
            result["position"] = node.position
            
    if node.children and node.name != "root" and not getattr(node, 'is_pattern', False):
        result["is_intermediate_code"] = is_intermediate_code
        
    if node.name != "root" and not getattr(node, 'is_pattern', False):
        is_leaf = not node.children
        is_intermediate_with_code = node.children and is_intermediate_code
        if is_leaf or is_intermediate_with_code:
            full_typecode = construct_full_typecode(node)
            if full_typecode:
                result["full_typecode"] = full_typecode
                result["group"] = ""
                
    if include_dates and hasattr(node, 'creation_dates') and node.name != "root":
        creation_dates = getattr(node, 'creation_dates', [])
        modification_dates = getattr(node, 'modification_dates', [])
        typecode_count = getattr(node, 'typecode_count', 0)
        
        if creation_dates or modification_dates or typecode_count > 0:
            date_info = {}
            
            if typecode_count > 0:
                date_info['typecode_count'] = typecode_count
                
            if creation_dates:
                valid_creation_dates = [d for d in creation_dates if d is not None]
                if valid_creation_dates:
                    sorted_dates = sorted(valid_creation_dates, key=lambda x: x['timestamp'])
                    date_info['creation_date'] = {
                        'earliest': sorted_dates[0]['formatted'],
                        'latest': sorted_dates[-1]['formatted']
                    }
                    
            if modification_dates:
                valid_modification_dates = [d for d in modification_dates if d is not None]
                if valid_modification_dates:
                    sorted_dates = sorted(valid_modification_dates, key=lambda x: x['timestamp'])
                    date_info['modification_date'] = {
                        'earliest': sorted_dates[0]['formatted'],
                        'latest': sorted_dates[-1]['formatted']
                    }

            if date_info:
                result['date_info'] = date_info

    return result


def main():
    df = pd.read_excel(INPUT_XLSX, dtype=str)
    df = df.drop_duplicates(subset=[COL_TYPECODE])
    
    typecodes = df[COL_TYPECODE].dropna().tolist()
    
    creation_dates = None
    modification_dates = None
    
    if INCLUDE_DATES:
        creation_dates = {}
        modification_dates = {}
        
        for idx, row in df.iterrows():
            typecode = row[COL_TYPECODE]
            if pd.notna(typecode):
                creation_date_str = row.get(COL_CREATIONDATE)
                if pd.notna(creation_date_str):
                    parsed_creation = parse_date_format(str(creation_date_str))
                    if parsed_creation:
                        creation_dates[typecode] = parsed_creation
                        
                modification_date_str = row.get(COL_MODIFICATIONDATE)
                if pd.notna(modification_date_str):
                    parsed_modification = parse_date_format(str(modification_date_str))
                    if parsed_modification:
                        modification_dates[typecode] = parsed_modification

    root = build_anytree(typecodes, creation_dates, modification_dates)
    
    normalized_excel_codes = set()
    for code in typecodes:
        parts = split_typecode(code)
        if len(parts) >= 2:
            normalized_code = "-".join(parts)
            normalized_excel_codes.add(normalized_code)
            
    json_data = node_to_dict(root, normalized_excel_codes, INCLUDE_DATES)
    
    output_filename = "baum.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        
if __name__ == "__main__":
    main()