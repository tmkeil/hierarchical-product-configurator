# 📋 Datenbank Import/Export Guide

Vollständige Command-Übersicht für alle Import/Export-Operationen.

---

## 🔵 EXPORT

### 1. Produkte exportieren
```bash                                                           (optional kmat)
py export_to_json.py --db variantenbaum.db --output backup.json --include-kmat --kmat-output kmat_references.json
```
✅ Erstellt **2 separate JSON-Dateien**: 
- `backup.json` (Produktdaten)
- Optional `kmat_references.json` (KMAT Referenzen)

### 3. Sub-Segments exportieren
```bash
py export_subsegments.py --db variantenbaum.db --output subsegments.json
```
✅ Sub-Segments müssen **separat** exportiert werden

---

## 🔵 IMPORT (Vollständiger Neuaufbau)

### **Empfohlener Import mit allen Features**
```bash
# recreate: Datenbank reset (Produkte löschen; User, subsegments, kmat und successors behalten)
# closure: Closure Table aufbauen (für Performance)
# kmat-json: KMAT Referenzen importieren (optional)
# subsegments-json: Sub-Segment Definitionen importieren (optional)
py import_data.py \
    --json ../variantenbaum/output/baum.json \
    --db variantenbaum.db \
    --recreate \
    --closure \
    --kmat-json kmat_references.json \
    --subsegments-json subsegments.json
```

### Nur KMAT Referenzen importieren
```bash
py import_kmat_references.py \
    --db variantenbaum.db \
    --json kmat_references.json
```

### Nur Sub-Segments importieren
```bash
python database/import_subsegments.py \
    --db variantenbaum.db \
    --json subsegments.json
```

---

## 🔵 MERGE (Neue Daten hinzufügen)

### Neue Produkte in bestehende DB mergen
```bash
# new-kmat-json (optional): Neue KMAT Referenzen mitimportieren
# output (optional): Custom Output DB Datei
py merge_data.py \
    --current-db variantenbaum.db \
    --new-json neue_produkte.json
    --new-kmat-json neue_kmat.json
    --output merged_database.db
```

---