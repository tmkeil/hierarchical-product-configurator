# Visual Mapping Tool - Grafischer Mapping-Editor

Web-basiertes Tool zur grafischen Erstellung von `filter_criteria` und `group_mappings`. Ersetzt die manuelle JSON-Bearbeitung durch eine intuitive Benutzeroberfläche.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Workflow & Integration](#workflow--integration)
- [Problem & Lösung](#problem--lösung)
- [Konzepte & Terminologie](#konzepte--terminologie)
- [UI-Mockup](#ui-mockup)
- [Generiertes JSON-Format](#generiertes-json-format)
- [Architektur](#architektur)
- [Implementierungsplan](#implementierungsplan)

---

## Überblick

### Was macht das Visual Mapping Tool?

Ein Web-Interface zur grafischen Erstellung von Mapping-Regeln für `label_mapper.py`. Es generiert:

- **`filter_criteria`** (Gruppen, Positionen, erlaubte Codes)
- **`group_mappings`** (Labels mit Beschreibungen, Bildern, Links)
- **Live-Preview** der `group_position` Syntax
- **JSON-Export** für bestehenden Workflow

**Wichtig:** Das Tool schreibt **NICHT** in die Datenbank, sondern exportiert nur JSON!

### Warum brauchen wir das?

**Aktueller Prozess (Manuell):**
```
1. Öffne mapping.json in Editor
2. Schreibe "1:1=G,2:3=I|1:1=K,2:3=L|..." manuell
3. Hoffe, dass keine Tippfehler drin sind
4. Teste mit label_mapper.py
5. Falls Fehler: Zurück zu Schritt 1
```

**Probleme:**
- ❌ Fehleranfällig (Tippfehler in `group_position`)
- ❌ Schwer zu verstehen (`1:1=G,2:3=I` - was bedeutet das?)
- ❌ Keine Validierung während der Bearbeitung
- ❌ Zeitaufwendig bei vielen Kombinationen

**Mit Visual Tool:**
```
1. Wähle Gruppen/Positionen im UI
2. Ziehe Codes per Drag-&-Drop
3. System generiert "1:1=G,2:3=I|..." automatisch
4. Exportiere JSON
5. Fertig!
```

---

## Workflow & Integration

### Kompletter Datenfluss

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Visual Mapping Tool (Web UI)                             │
│    Grafische Erstellung von Mapping-Regeln                  │
│    ↓                                                         │
│    Output: mapping_BES.json                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. label_mapper.py (Existing Tool)                          │
│    Wendet Mapping-Regeln auf Produktdaten an                │
│    ↓                                                         │
│    Input:  mapping_BES.json + baum.json                     │
│    Output: baum_with_labels.json                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. import_data.py (Existing Tool)                           │
│    Erstellt Datenbank aus JSON                              │
│    ↓                                                         │
│    Input:  baum_with_labels.json                            │
│    Output: variantenbaum.db (inkl. node_labels Tabelle)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CodeHints Component (Frontend)                           │
│    Zeigt Code-Erklärungen während Eingabe                   │
│    ↓                                                         │
│    Liest: node_labels via /api/code-hints                   │
└─────────────────────────────────────────────────────────────┘
```

### Wichtig: Keine Datenbank-Integration!

**Das Visual Mapping Tool:**
- ✅ Generiert **NUR** JSON-Dateien (`mapping_BES.json`)
- ❌ Schreibt **NICHT** direkt in die Datenbank
- ❌ Erzeugt **KEINE** `node_labels` Einträge

**Warum?**
1. **Trennung der Verantwortlichkeiten:**
   - Mapping Tool = Mapping-Regeln erstellen
   - label_mapper = Regeln auf Produktdaten anwenden
   - import_data = Datenbank erstellen

2. **Flexibilität:**
   - Ein Mapping kann auf mehrere `baum.json` angewendet werden
   - Mapping-JSONs können versioniert/geteilt werden

3. **Bestehender Workflow bleibt erhalten:**
   - `label_mapper.py` muss **nicht** angepasst werden
   - `import_data.py` bleibt unverändert

---

## Problem & Lösung

### Das Problem: Manuelle filter_criteria Erstellung

**Beispiel aus deiner `mapping.json`:**

```json
{
  "filter_criteria": {
    "family": "BES",
    "pattern": "1!=1,1!=2,1!=3,1!=4,1!=5,1!=6",
    "group_position": "1:1=G,2:3=I|1:1=K,2:3=I|1:1=M,2:3=I|1:1=Z,2:3=I|1:1=G,2:3=L|1:1=K,2:3=L|1:1=M,2:3=L|1:1=Z,2:3=L|1:1=G,2:3=U|1:1=K,2:3=U|1:1=M,2:3=U|1:1=Z,2:3=U"
  }
}
```

**Was bedeutet `1:1=G,2:3=I`?**
```
1:1=G  →  Gruppe 1, Position 1 = Code "G"
2:3=I  →  Gruppe 2, Position 3 = Code "I"
```

**Problem:** Bei vielen Codes wird der `group_position` String **sehr lang** und **fehleranfällig**!

### Die Lösung: Automatische Kombinationen-Generierung

**Nutzer definiert im Visual Tool:**
- Gruppe 1, Position 1: [G, K, M, Z]  (4 Optionen)
- Gruppe 2, Position 3: [I, L, U]     (3 Optionen)

**Tool berechnet automatisch: 4 × 3 = 12 Kombinationen**

```
1:1=G,2:3=I | 1:1=G,2:3=L | 1:1=G,2:3=U |
1:1=K,2:3=I | 1:1=K,2:3=L | 1:1=K,2:3=U |
1:1=M,2:3=I | 1:1=M,2:3=L | 1:1=M,2:3=U |
1:1=Z,2:3=I | 1:1=Z,2:3=L | 1:1=Z,2:3=U
```

**Alle mit `|` verbunden:**
```
"1:1=G,2:3=I|1:1=G,2:3=L|1:1=G,2:3=U|1:1=K,2:3=I|..."
```

**Vorteil:** Keine Tippfehler, keine vergessenen Kombinationen! ✅

---

## Konzepte & Terminologie

### 1. filter_criteria

**Definition:** Beschreibt, welche Produktcodes zu einer Produktfamilie gehören.

**Struktur:**
```json
{
  "family": "BES",
  "pattern": "1!=1,1!=2",
  "group_position": "1:1=G,2:3=I|..."
}
```

- **family**: Produktfamilie (z.B. "BES")
- **pattern**: Filter für ungültige Codes (`1!=1` = Level 1 darf nicht "1" sein)
- **group_position**: Erlaubte Gruppen/Positionen-Kombinationen

### 2. group_position Syntax

**Format:** `Gruppe:Position=Code,Gruppe:Position=Code|...`

**Beispiele:**
```
"1:1=G,2:3=I"        → Gruppe 1/Pos 1="G" UND Gruppe 2/Pos 3="I"
"1:1=K,2:3=L"        → Gruppe 1/Pos 1="K" UND Gruppe 2/Pos 3="L"
"1:1=G,2:3=I|1:1=K,2:3=L"  → Entweder (G+I) ODER (K+L)
```

**Wichtig:**
- `,` = UND (innerhalb einer Kombination)
- `|` = ODER (zwischen Kombinationen)

### 3. group_mappings

**Definition:** Ordnet Codes ihre Beschreibungen zu.

**Struktur:**
```json
{
  "group": 2,
  "position": 3,
  "codes": ["I", "L", "U"],
  "labels": [
    "Text für I",
    {
      "text": "Text für L",
      "pictures": [{...}],
      "links": [{...}]
    },
    "Text für U"
  ]
}
```

**Wichtig:** Reihenfolge in `codes` und `labels` muss übereinstimmen!

### 4. Gruppen vs. Levels

| **Begriff** | **Bedeutung** | **Wo verwendet?** |
|-------------|---------------|-------------------|
| **Level** | Position im Baum (baum.json) | Produkthierarchie |
| **Gruppe** | Logische Code-Gruppierung | Mapping-Regeln |

**Beispiel:**
- `baum.json`: "Level 1: Bauart", "Level 2: Konfiguration"
- `mapping.json`: "Gruppe 1, Position 1", "Gruppe 2, Position 3"

**Gruppen ≠ Levels!** Die Mapping-Gruppen sind unabhängig von der Baum-Hierarchie.

---

## UI-Mockup

### Hauptansicht (Mapping-Editor)

```
┌──────────────────────────────────────────────────────────────┐
│ Visual Mapping Tool - Mapping-Editor               [Admin]  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Produktfamilie: [BES ▼]              [+ Neue Familie]        │
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Gruppe 1: Basistyp                         [⚙️] [🗑️]    │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │                                                           │ │
│ │ Position 1: Bauart                       [+ Position]    │ │
│ │ ┌───┬───┬───┬───┐                                        │ │
│ │ │ G │ K │ M │ Z │  [+ Code]                              │ │
│ │ └───┴───┴───┴───┘                                        │ │
│ │                                                           │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Gruppe 2: Funktionen                       [⚙️] [🗑️]    │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │                                                           │ │
│ │ Position 3: IO-Link Option                               │ │
│ │ ┌───┬───┬───┐                                            │ │
│ │ │ I │ L │ U │  [+ Code]                                  │ │
│ │ └───┴───┴───┘                                            │ │
│ │                                                           │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│                                            [+ Neue Gruppe]    │
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Live-Preview: group_position                             │ │
│ ├──────────────────────────────────────────────────────────┤ │
│ │ 1:1=G,2:3=I|1:1=G,2:3=L|1:1=G,2:3=U|                     │ │
│ │ 1:1=K,2:3=I|1:1=K,2:3=L|1:1=K,2:3=U|                     │ │
│ │ 1:1=M,2:3=I|1:1=M,2:3=L|1:1=M,2:3=U|                     │ │
│ │ 1:1=Z,2:3=I|1:1=Z,2:3=L|1:1=Z,2:3=U                      │ │
│ │                                                           │ │
│ │ ✅ 12 Kombinationen generiert                            │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│         [Als JSON exportieren]  [Speichern]  [Abbrechen]     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Code-Detail-Dialog (Klick auf "I")

```
┌─────────────────────────────────────────────────────┐
│ Code bearbeiten: "I"                        [✕]     │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Code-Wert:                                           │
│ ┌──────────────────────────────────────────────┐    │
│ │ I                                            │    │
│ └──────────────────────────────────────────────┘    │
│                                                      │
│ Beschreibung (DE):                                   │
│ ┌──────────────────────────────────────────────┐    │
│ │ IO-Link als Nebenfunktion (SIO-Mode)        │    │
│ │ ○ Nur anliegende Spannung: SIO-Mode          │    │
│ │ ○ Bei Kommunikation: IO-Link                 │    │
│ └──────────────────────────────────────────────┘    │
│                                                      │
│ Beschreibung (EN):                                   │
│ ┌──────────────────────────────────────────────┐    │
│ │ IO-Link as secondary function (SIO-Mode)    │    │
│ └──────────────────────────────────────────────┘    │
│                                                      │
│ Bilder:                                              │
│ ┌──────────────────────────────────────────────┐    │
│ │ [📷 /uploads/bes/io-link.png]         [🗑️]  │    │
│ │ [+ Bild hinzufügen]                          │    │
│ └──────────────────────────────────────────────┘    │
│                                                      │
│ Links:                                               │
│ ┌──────────────────────────────────────────────┐    │
│ │ [🔗 IO-Link Datenblatt]               [🗑️]  │    │
│ │ [+ Link hinzufügen]                          │    │
│ └──────────────────────────────────────────────┘    │
│                                                      │
│                      [Speichern]  [Abbrechen]       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Workflow

1. **Familie wählen**: "BES"
2. **Gruppe erstellen**: "Gruppe 1: Basistyp"
3. **Position hinzufügen**: "Position 1"
4. **Codes definieren**: Klicke "+ Code" → Gib "G", "K", "M", "Z" ein
5. **Labels hinzufügen**: Klicke auf Code → Füge Beschreibung/Bilder/Links hinzu
6. **Live-Preview**: Sehe `group_position` sofort
7. **JSON exportieren**: Download `mapping_BES.json`
8. **Verwenden**: `python label_mapper.py mapping_BES.json baum.json`

---

## Generiertes JSON-Format

### Output: mapping_BES.json

```json
{
  "filter_criteria": {
    "family": "BES",
    "pattern": "1!=1,1!=2,1!=3,1!=4,1!=5,1!=6",
    "group_position": "1:1=G,2:3=I|1:1=G,2:3=L|1:1=G,2:3=U|1:1=K,2:3=I|1:1=K,2:3=L|1:1=K,2:3=U|1:1=M,2:3=I|1:1=M,2:3=L|1:1=M,2:3=U|1:1=Z,2:3=I|1:1=Z,2:3=L|1:1=Z,2:3=U"
  },
  "group_mappings": [
    {
      "group": 1,
      "position": 1,
      "codes": ["G", "K", "M", "Z"],
      "labels": [
        "Gewinde",
        "Kunststoff",
        "Metall",
        "Zylinder"
      ]
    },
    {
      "group": 2,
      "position": 3,
      "codes": ["I", "L", "U"],
      "labels": [
        {
          "text": "IO-Link als Nebenfunktion (SIO-Mode)",
          "pictures": [
            {
              "url": "/uploads/bes/io-link.png",
              "description": "IO-Link Schematic"
            }
          ],
          "links": [
            {
              "url": "https://example.com/iolink",
              "description": "IO-Link Datenblatt"
            }
          ]
        },
        "Zusätzlicher PS-Schaltausgang mit IO-Link",
        "Serial Data Output Mode"
      ]
    }
  ],
  "metadata": {
    "created": "2025-12-03T10:30:00Z",
    "created_by": "admin",
    "tool_version": "1.0"
  }
}
```

### Verwendung mit label_mapper.py

```bash
# 1. Exportiere JSON aus Visual Mapping Tool
# → Download: mapping_BES.json

# 2. Wende Mapping auf Produktdaten an
cd database
python label_mapper.py \
  --mapping ../mapping_BES.json \
  --input ../baum.json \
  --output ../baum_with_labels.json

# 3. Erstelle Datenbank
python import_data.py \
  --json ../baum_with_labels.json \
  --db variantenbaum.db \
  --recreate

# 4. Starte Frontend
cd ../App
npm run dev

# → CodeHints funktioniert automatisch!
```

---

## Architektur

### System-Überblick (Reiner JSON-Generator)

```
┌──────────────────────────────────────────────────┐
│  Visual Mapping Tool (Web UI - React)           │
│                                                   │
│  ┌────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  Gruppen/  │  │    Live     │  │   JSON    │ │
│  │ Positionen │→ │   Preview   │→ │  Export   │ │
│  │   Editor   │  │(group_pos.) │  │ (Download)│ │
│  └────────────┘  └─────────────┘  └─────┬─────┘ │
│                                          ↓       │
└──────────────────────────────────────────┼───────┘
                                           │
                                  mapping_BES.json
                                           │
                                           ↓
                            ┌──────────────────────┐
                            │   label_mapper.py    │
                            │   (Existing Tool)    │
                            └──────────┬───────────┘
                                       ↓
                              baum_with_labels.json
                                       ↓
                            ┌──────────────────────┐
                            │   import_data.py     │
                            │   (Existing Tool)    │
                            └──────────┬───────────┘
                                       ↓
                             variantenbaum.db
                          (inkl. node_labels Tabelle)
```

### Technologie-Stack

**Frontend (React):**
- **React 18** + TypeScript
- **React Hook Form** (Formular-Handling)
- **Zod** (Validierung)
- **Tailwind CSS** (Styling)
- **React DnD** (Drag-&-Drop, optional)

**Backend (Minimal):**
- **FastAPI** (für temporäres Speichern von Entwürfen, optional)
- **Oder**: Rein client-seitig (localStorage für Entwürfe)

**Keine Datenbank nötig!** Das Tool ist ein **reiner JSON-Generator**.

---

## Implementierungsplan

### Phase 1: Core UI (Tag 1-2)

**Aufgaben:**
- [ ] Gruppen-Editor (Hinzufügen/Löschen/Umbenennen)
- [ ] Positionen-Editor (Innerhalb Gruppen)
- [ ] Code-Input (Einfache Textfelder)
- [ ] Live-Preview (`group_position` String)
- [ ] JSON-Export (Download-Button)

**Dateien:**
- `App/src/components/mapping/MappingEditor.tsx`
- `App/src/components/mapping/GroupEditor.tsx`
- `App/src/components/mapping/PositionEditor.tsx`
- `App/src/components/mapping/LivePreview.tsx`

**Meilenstein:** Basis-UI funktioniert, kann einfache Mappings erstellen.

### Phase 2: Label-Editor (Tag 3-4)

**Aufgaben:**
- [ ] Code-Detail-Dialog (Beschreibungen DE/EN)
- [ ] Bild-Upload/Verwaltung
- [ ] Link-Verwaltung
- [ ] `group_mappings` Generierung
- [ ] Validierung (Codes != Leer, Labels != Duplikate)

**Dateien:**
- `App/src/components/mapping/CodeDetailDialog.tsx`
- `App/src/components/mapping/ImageUpload.tsx`
- `App/src/components/mapping/LinkEditor.tsx`

**Meilenstein:** Vollständige Mappings mit Bildern/Links möglich.

### Phase 3: Erweiterte Features (Tag 5-6)

**Aufgaben:**
- [ ] Pattern-Editor (`1!=1,1!=2,...`)
- [ ] Drag-&-Drop für Codes (optional)
- [ ] Import bestehender Mappings (JSON-Upload)
- [ ] Validierung gegen baum.json (Prüfe, ob Codes existieren)
- [ ] Kombinations-Vorschau (Wie viele Kombinationen?)

**Dateien:**
- `App/src/components/mapping/PatternEditor.tsx`
- `App/src/utils/mapping-validator.ts`

**Meilenstein:** Tool ist production-ready.

### Phase 4: Testing & Dokumentation (Tag 7-8)

**Aufgaben:**
- [ ] E2E-Tests (Cypress/Playwright)
- [ ] Unit-Tests (Vitest)
- [ ] Benutzer-Handbuch (`USER_GUIDE_MAPPING_TOOL.md`)
- [ ] Video-Tutorial (5-10 Minuten)
- [ ] Integration-Test mit `label_mapper.py`

**Deliverables:**
- `USER_GUIDE_MAPPING_TOOL.md`
- `video_tutorial.mp4`
- Test-Coverage: >80%

---

## FAQ

### Kann ich bestehende mapping.json importieren?

**Ja!** Das Tool bietet einen "Import"-Button:

1. Klicke "Import JSON"
2. Wähle `mapping.json`
3. Tool parst `filter_criteria` und `group_mappings`
4. Zeigt Gruppen/Positionen im Editor
5. Bearbeite grafisch
6. Exportiere aktualisierte Version

### Wie validiere ich, ob Codes im baum.json existieren?

**Option 1: Manuelle Prüfung**
- Lade `baum.json` hoch
- Tool prüft alle Codes in `group_position`
- Zeigt Warnung bei fehlenden Codes

**Option 2: Integration mit label_mapper**
- Exportiere `mapping_BES.json`
- Lasse `label_mapper.py` laufen
- Prüfe Warnings/Errors

### Kann ich Mapping-Regeln versionieren?

**Ja!** Nutze Git:

```bash
# 1. Initialisiere Git-Repo für Mappings
cd mappings/
git init

# 2. Füge Mapping hinzu
git add mapping_BES.json
git commit -m "Initial BES mapping v1.0"

# 3. Bei Änderungen
# ... Bearbeite im Visual Tool ...
git add mapping_BES.json
git commit -m "Added IO-Link L option"

# 4. Zeige Historie
git log --oneline

# 5. Zu alter Version zurück
git checkout abc123 -- mapping_BES.json
```

### Wie groß darf group_position werden?

**Browser-Limits:**
- Moderne Browser: ~1 MB Text in Inputs
- Bei > 10.000 Kombinationen: Nutze Pattern statt explizite Auflistung

**Beispiel:**
```
Gruppe 1: 10 Positionen à 5 Codes = 9.765.625 Kombinationen ❌

Besser: Nutze Constraints in label_mapper statt alles aufzulisten
```

---

## Zusammenfassung

Das **Visual Mapping Tool** vereinfacht die Mapping-Erstellung drastisch:

| **Aspekt** | **Manuell (aktuell)** | **Visual Tool** |
|------------|----------------------|-----------------|
| **Zeit** | ~1-2 Stunden | ~15 Minuten |
| **Fehlerquote** | ~20% (Tippfehler) | ~2% |
| **Validierung** | Keine | Live |
| **Wartbarkeit** | Schwierig | Einfach |
| **Lernkurve** | Steil | Flach |

**Nächste Schritte:**
1. Review dieser README
2. Feedback zu UI-Mockup
3. Phase 1 starten (Core UI)
