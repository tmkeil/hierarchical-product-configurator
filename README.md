# Produktschlüsselkonfigurator

Ein hierarchischer Produktkonfigurator für Typcode-basierte Produktvarianten mit integrierter Benutzerverwaltung und Authentifizierung.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Technologie-Stack](#technologie-stack)
- [Entwicklung & Maintenance](#entwicklung--maintenance)
- [Desktop-App für Windows](#desktop-app-für-windows)
- [Lokale Installation & Testen](#lokale-installation--testen)
  - [Datenbank-Wartung](#datenbank-wartung)
- [Datenbankschema & Architektur](#datenbankschema--architektur)
- [Produktionsreife Deployment](#produktionsreife-deployment)
  - [Image Storage Strategie](#image-storage-strategie)
- [API-Dokumentation](#api-dokumentation)

---

## Überblick

### Was macht diese Anwendung?

Der Produktschlüsselkonfigurator ist ein Web-basiertes Tool zur Konfiguration von Produktvarianten in einem hierarchischen Typcode-System. Die Anwendung ermöglicht:

- **Hierarchische Produktnavigation**: Auswahl von Produktfamilien, Gruppen und spezifischen Optionen auf verschiedenen Ebenen
- **Typcode-Validierung**: Automatische Prüfung von Produktcodes gegen definierte Constraints und Regeln
- **Produktschlüssel-Dekodierung**: Auflösung von bestehenden Typecodes zu lesbaren Produktbeschreibungen
- **Benutzerverwaltung**: Rollenbasierte Zugriffskontrolle (Admin/User) mit JWT-Authentifizierung
- **Multi-Sprach-Support**: Produktinformationen in Deutsch und Englisch

### Hauptfunktionen

1. **Produktkonfigurator**:
   - Schrittweise Auswahl durch Produkthierarchie (Family → Group → Levels)
   - Dynamische Filterung verfügbarer Optionen basierend auf vorherigen Auswahlen
   - **Produktverfügbarkeit**: Nachfolgeprodukte für auslaufende Optionen
   - Visuelle Darstellung mit Bildern und technischen Informationen
   - Export der Konfiguration als Produktschlüssel

2. **Typcode-Dekodierung**:
   - Eingabe eines **beliebigen** Produktcodes (vollständig oder Teilcode)
   - Automatische Auflösung zu Produktfamilie, Gruppe und allen Ebenen
   - Funktioniert auch für Codes beliebiger Level (nicht nur finale Produkte)
   - Anzeige vollständiger Produktinformationen mit Hierarchie-Pfad

3. **Schema-Visualisierung**:
   - Interaktive Visualisierung der Typcode-Struktur
   - Sub-Segment-Definitionen für detaillierte Code-Aufschlüsselung
   - Zeigt Bedeutung einzelner Zeichen im Produktcode (z.B. "Position 0-1: Bereich, Position 1-3: Steckergröße")
   - Admin: Erstellen und Bearbeiten von Sub-Segment-Definitionen

4. **Excel Export**:
   - Export von Produktfamilien nach Excel
   - Alle Code-Ebenen dokumentiert (nicht nur finale Produkte)
   - Automatische Deduplizierung identischer Codes
   - Separate "Gemeinsame Codes"-Tabelle für gruppen-übergreifende Codes
   - Gruppiert nach Produktgruppen mit vollständigen Labels

5. **Produktlebenszyklus-Verwaltung**:
   - **Successor-Verwaltung**: Erstellen und Verwalten von Nachfolgeprodukten für auslaufende Artikel
   - Ankündigungs- und Abkündigungsdaten festlegen
   - Kommentare für Kunden (Deutsch/Englisch)
   - Visuelle Warnung im Produktkonfigurator bei auslaufenden Produkten
   - Automatische Verlinkung zu Nachfolgeprodukten

6. **KMAT-Referenzen**:
   - Zuordnung von KMAT-Nummern zu Produktoptionen
   - Mehrere KMAT-Referenzen pro Produkt möglich
   - Anzeige im Produktkonfigurator während der Auswahl

7. **Admin-Panel**:
   - Benutzerverwaltung (Erstellen, Anzeigen von Benutzern)
   - Rollenzuweisung (Admin/User)
   - Passwort-Management
   - **Produktdaten-Management**: Löschen von Produktfamilien und Nodes
   - Übersicht über alle Systembenutzer

---

## Technologie-Stack

### Backend
- **FastAPI** (Python): REST API mit automatischer OpenAPI-Dokumentation
- **SQLite**: Lokale Datenbank mit Closure Table für hierarchische Abfragen
- **JWT Authentication**: Token-basierte Authentifizierung mit bcrypt-Passwort-Hashing
- **Uvicorn**: ASGI-Server für asynchrone Request-Verarbeitung

### Frontend
- **React 18** + **TypeScript**: Typsichere UI-Entwicklung
- **React Router**: Client-seitiges Routing
- **React Query**: Effizientes Data-Fetching und Caching
- **Tailwind CSS**: Utility-First CSS Framework
- **Vite**: Schneller Build-Prozess und HMR

### Datenbank-Design
- **Closure Table Pattern**: Vorberechnete Pfade für O(1) Hierarchie-Abfragen
- **Node-basierte Struktur**: Jeder Produktknoten mit Code, Labels, Bildern, Links
- **Constraint-System**: Regelbasierte Validierung von Produktkombinationen

## Entwicklung & Maintenance

**Entwicklungszeit:** 3 Monate (~25.000 Zeilen Code mit Copilot).

Die Codezeilen sind das Ergebnis der eigentlichen Arbeit: Architektur-Entscheidungen (Dependency Injection, Closure Table Pattern), Design des hierarchischen Datenmodells, Analyse kontext-abhängiger Code-Bedeutungen und manuelle Erstellung von Mapping-Regeln. Copilot unterstützte bei der Umsetzung und Best Practices.

### Projektstruktur

Das Projekt besteht aus drei Komponenten mit unterschiedlichen Entwicklungszyklen:

**1. Webanwendung - 7 Wochen**

Features wurden iterativ erweitert, sobald neue Use Cases während der Entwicklung sichtbar wurden.\
Die Architektur ermöglicht einen nahtlosen Wechsel zwischen SQLite (Entwicklung) und PostgreSQL/Azure SQL (Produktion) durch Dependency Injection.

**Features:**
- **FastAPI REST API** mit JWT-Auth, Benutzerverwaltung, Constraint-Validierung
- **React Frontend** mit hierarchischem Produktnavigator, Admin Panel, Typcode-Dekodierung
- **Komplexer Produktkonfigurator**: 
  - Dynamische Kompatibilität zwischen Produktoptionen (Forward/Backward Compatibility Checks)
  - Nutzer können Optionen in beliebiger Reihenfolge wählen → System validiert automatisch machbare Kombinationen
  - Details zur Kompatibilitäts-Logik: Siehe [`PROJECT_DOCUMENTATION.md`](App/PROJECT_DOCUMENTATION.md) (Query 4 Algorithmus)
- **Erweiterte Features**:
  - Schema-Visualisierung mit Sub-Segment-Definitionen
  - Excel Export für Produktfamilien
  - Produktlebenszyklus-Verwaltung (Successors)
  - KMAT-Referenzen Management

**Umfang:**
- **~17.000 Zeilen Code** (TypeScript + Python)
- **Frontend:** ~8.500 Zeilen React/TypeScript (App.tsx: ~7.300 Zeilen)
- **Backend:** ~8.000 Zeilen FastAPI/Python
- **25+ REST API Endpoints**

**2. Python-Scripts für Datenvorbereitung - 4 Wochen**

Entwickelt in einem iterativen Prozess, da neue Anforderungen erst nach Analyse der Datenquellen erkennbar wurden.

Die größte Herausforderung war die Entwicklung einer JSON-Struktur, die alle Produktvarianten hierarchisch abbildet und gleichzeitig Labels (Beschreibungen) automatisch den richtigen Code-Segmenten zuordnet. Erschwerend kam hinzu, dass derselbe Code je nach Produktfamilie unterschiedliche Bedeutungen haben kann. Ein "A" kann in einer Familie "Aluminium", in einer anderen "Automatik" bedeuten.

**Entwickelte Tools:**
- **`createBaum.py`**: Konvertiert Excel-Typcodes zu JSON-Baumstruktur
- **`schema_search.py`**: Filtert relevante Produkte aus der Baumstruktur für die Label-Zuordnung (2689 Zeilen)
- **`label_mapper.py`**: Ordnet Labels automatisch zu Code-Segmenten mit kontext-spezifischen Regeln (3042 Zeilen)

**3. Visual Mapping Tool & Electron Desktop App - 1 Woche**

**Visual Mapping Tool:**
Historisch wurden Mapping-Regeln manuell in komplexen JSON-Strukturen definiert (`filter_criteria`, `group_position`). Das **Visual Mapping Tool** ersetzt diesen manuellen Prozess durch eine grafische Oberfläche.

**Motivation:**
- Manuelle JSON-Erstellung fehleranfällig und zeitaufwendig
- Komplexe Syntax schwer zu verstehen für neue Bearbeiter
- Keine Validierung während der Erstellung

**Lösung:**
- Web-basiertes UI zur Definition von Code-Schemas
- Drag-&-Drop für Code-Segmente
- Automatische Generierung von `filter_criteria` und `node_labels`
- Live-Preview der resultierenden JSON-Struktur

**Electron Desktop App:**
- Standalone Windows .exe für einfache Distribution
- Kein Python/Node.js Setup für Endnutzer erforderlich
- Embedded SQLite Datenbank
- PyInstaller für Backend-Bundling
- electron-builder für Installer-Erstellung
- Siehe Sektion "Desktop-App für Windows" für Details

→ **Detaillierte Dokumentation**: Siehe [`README_MAPPING.md`](README_MAPPING.md)

## Desktop-App für Windows

Die Anwendung kann als **eigenständige Windows `.exe`** verteilt werden.

### Vorteile

- ✅ **Keine Installation** von Python/Node.js nötig
- ✅ **Keine Terminal-Befehle** oder Entwickler-Setup
- ✅ **SQLite-Datenbank eingebunden** mit allen Produktdaten
- ✅ **Gleiche Funktionen** wie Webanwendung (Login, Produktkonfigurator, Admin-Panel)
- ✅ **Offline-fähig** (keine Cloud/Internet nötig)

### Für Entwickler: .exe erstellen

**Voraussetzungen:**

1. **Node.js 18+** und **npm** installiert
2. **Python 3.10+ mit venv-win**: Separates Virtual Environment für Windows-PyInstaller

**Schritt 1: Windows Virtual Environment erstellen (einmalig)**

PyInstaller für Windows muss in einem separaten `venv-win` laufen:

```bash
# Im Projekt-Root:
python3 -m venv venv-win

# Aktivieren (Windows):
venv-win\Scripts\activate

# Dependencies installieren:
pip install -r requirements.txt
pip install pyinstaller

# Deaktivieren:
deactivate
```

**Hinweis:** `venv-win` muss existieren, aber nicht aktiviert sein beim Build. Das Build-Script verwendet automatisch `venv-win/Scripts/python.exe`.

**Schritt 2: Electron Dependencies installieren (einmalig)**

```bash
cd electron
npm install
```

**Schritt 3: Build ausführen**

```bash
# Kompletter Build (Backend + Frontend + Installer):
npm run build:win

# Oder manuell Schritt für Schritt:
npm run build:backend   # Baut backend.exe mit PyInstaller
npm run build:frontend  # Baut React App mit Vite
npx electron-builder --win  # Erstellt Installer

# Ergebnis: electron/dist/Produktkonfigurator-Setup-1.0.0.exe (~150-200 MB)
```

**Was passiert beim Build?**

1. **build:backend** (build-backend.js):
   - Verwendet PyInstaller mit `venv-win/Scripts/python.exe`
   - Bundelt FastAPI + SQLite + alle Dependencies
   - Erstellt `electron/resources/backend/backend.exe`
   - Kopiert Datenbank nach `electron/resources/database/`

2. **build:frontend** (build-frontend.js):
   - Baut React App mit Vite (`npm run build` in App/)
   - Kopiert Build nach `electron/resources/frontend/`

3. **electron-builder**:
   - Packt Electron + Backend + Frontend + Datenbank
   - Erstellt Windows-Installer (.exe)
   - Konfiguration: `electron/package.json` → `build` Sektion

### Für Anwender: Installation

1. **`Produktkonfigurator-Setup-1.0.0.exe`** herunterladen
2. Installieren
3. **Produktkonfigurator** starten
4. Login mit: `admin` / `ChangeMe123!`

---

## Datenvorbereitung & Workflow

Das Repo enthält eine `baum.json`, die für das lokale Testen bereits verwendet werden kann.\
Dieser Teil beschreibt nur, wie die Datei erstellt wird, die die vollständige Produkthierarchie enthält.

#### Ausgangslage

Die Produktdaten stammen aus heterogenen Quellen:
- **Excel-Dateien**: Alle Produkttypcodes
- **Word/Excel-Dateien**: Produktbeschreibungen (Labels) in unterschiedlichen Formaten und Strukturierungen

#### Workflow

**1. Baumstruktur erstellen (`createBaum.py`)**
- Liest Excel-Dateien mit allen Produkttypcodes
- Baut hierarchische JSON-Struktur
- Ausgabe: `baum.json` **ohne** Labels/Beschreibungen zu den Codesegments

**2. Mapping-Regeln extrahieren (`schema_search.py`)**
- Analysiert Word/Excel-Dateien mit Produktbeschreibungen
- Identifiziert verschiedene Dokumentationsformate
- Extrahiert Zuordnungsregeln zwischen Codes und Labels

**3. Labels zuordnen (`label_mapper.py`)**
- Verwendet Mapping-Regeln aus `schema_search.py`
- Fügt Beschreibungen zu Codesegments hinzu

**Problem**: Derselbe Code kann auf einem Level in verschiedenen Kontexten unterschiedliche Bedeutungen haben.

**Beispiel**:
- Code `"A"` auf Level 2 in Familie `"FX"` → "Aluminium"
- Code `"A"` auf Level 2 in Familie `"GY"` → "Automatik"

**Lösung**: Kontext-spezifische Regeln definieren:
- Produktfamilie
- Parent-Codes (vorherige Auswahlen)
- Position im Baum

**Kontinuierliche Verbesserung**: Da die Quelldokumente sehr unterschiedlich strukturiert sind, werden `label_mapper` und `schema_search` iterativ erweitert, um alle Edge Cases abzudecken.

## Lokale Installation & Testen

### Voraussetzungen

- **Python 3.10+**
- **Node.js 18+** und **npm**
- **Git**

### Schritt 1: Repository klonen

```bash
git clone <repository-url> repo
cd repo
```

### Schritt 2: Python Virtual Environment erstellen

Eine virtuelle Umgebung isoliert die Python-Dependencies dieses Projekts von anderen Python-Installationen auf deinem System.

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
# Auf Linux/Mac:
source venv/bin/activate
# Auf Windows:
venv\Scripts\activate

```

### Schritt 3: Backend-Dependencies installieren

```bash
# Alle Python-Packages aus requirements.txt installieren
pip install -r requirements.txt
```

### Schritt 4: Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei im Root-Verzeichnis:

```bash
# .env Datei im Root-Verzeichnis erstellen auf Linux/Mac:
cat > .env << EOF
# JWT Authentication
JWT_SECRET=dein-super-geheimes-jwt-secret-min-32-zeichen-lang
JWT_EXPIRATION_MINUTES=60

# Initial Admin User (wird beim ersten Start erstellt)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=ChangeMe123!

# API Configuration
API_BASE_URL=http://localhost:8000
EOF
```

```powershell
# Auf Windows (PowerShell):
@"
# .env Datei im Root-Verzeichnis erstellen auf Windows (PowerShell):
# JWT Authentication
JWT_SECRET=dein-super-geheimes-jwt-secret-min-32-zeichen-lang
JWT_EXPIRATION_MINUTES=60

# Initial Admin User (wird beim ersten Start erstellt)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=ChangeMe123!

# API Configuration
API_BASE_URL=http://localhost:8000
"@ | Out-File -Encoding UTF8 .env
```

### Schritt 5: Datenbank erstellen

> **💡 Vollständige Command-Referenz**: Siehe [`database/IMPORT_EXPORT_GUIDE.md`](database/IMPORT_EXPORT_GUIDE.md)

#### Aktuell (SQLite):

```bash
cd database

# Datenbank erstellen mit Closure Table für Performance
python import_data.py --json ../baum.json --db variantenbaum.db --recreate --closure
```

**Was passiert hier?**
- Erstellt Datenbank-Schema aus `schema.sql`
- Importiert Produkthierarchie aus `baum.json`
- **Erstellt automatisch Admin-User** (Username/Passwort aus `.env`)
- Berechnet Closure Table für schnelle Hierarchie-Queries

**Wichtig**: `database/uploads/` Verzeichnis wird für hochgeladene Bilder genutzt (Nutzer können im Frontend Bilder zu Knoten hochladen).

#### Nach PostgreSQL-Umstellung (lokal testen mit Docker):

```bash
# 1. PostgreSQL lokal starten (einmalig - läuft dann im Hintergrund)
docker run -d \
  --name produktkonf-db \
  -e POSTGRES_PASSWORD=testpassword \
  -e POSTGRES_DB=produktkonfigurator \
  -p 5432:5432 \
  postgres:15

# 2. Datenbank erstellen (Verbindung zu lokalem Docker PostgreSQL)
cd database
python import_data.py \
  --json ../baum.json \
  --db "postgresql://postgres:testpassword@localhost:5432/produktkonfigurator" \
  --recreate \
  --closure
```

**Hinweis**:\
Stoppen mit `docker stop produktkonf-db`, erneut starten mit `docker start produktkonf-db`.

### Schritt 6: Backend starten

```bash
cd database

# Backend-Server starten (in der virtuellen Umgebung)
uvicorn api:app --reload --port 8000
```

**Was passiert hier?**

- **`uvicorn`**: ASGI-Server startet die FastAPI-Anwendung
- **`api:app`**: Lädt das `app` Objekt aus der `api.py` Datei
- **`--reload`**: Automatischer Neustart bei Code-Änderungen (nur für Entwicklung!)
- **`--port 8000`**: Server läuft auf http://localhost:8000

### Schritt 7: Frontend-Dependencies installieren

Zweite Terminal-Session öffnen (virtuelle Umgebung nicht nötig):
```bash
cd App

# Node.js Dependencies installieren
npm install
```

**Was passiert hier?**
- npm liest `package.json` und `package-lock.json`
- Installiert React, TypeScript, Vite, Tailwind CSS und alle Frontend-Dependencies
- Erstellt `node_modules/` Verzeichnis

### Schritt 8: Frontend starten

```bash
# In zweitem Terminal wieder die virtuelle Umgebung aktivieren
source ../venv/bin/activate  # Auf Linux/Mac
venv\Scripts\activate        # Auf Windows

cd App

# Development Server starten
npm run dev
```

**Was passiert hier?**
- **Vite Dev Server** startet auf http://localhost:5173
- Hot Module Replacement (HMR) ermöglicht sofortige Code-Updates
- TypeScript-Kompilierung im Watch-Mode

### Schritt 9: Anwendung im Browser testen

1. **Browser öffnen**: Navigiere zu **http://localhost:5173**

2. **Login**: 
   - Username: `admin`
   - Password: `ChangeMe123!`

3. **Funktionen testen**:
   - ✅ **Produktkonfigurator**: Wähle Produktfamilie → Gruppe → Optionen
   - ✅ **Typcode-Dekodierung**: Klicke "🔍 Produktcode Checker" und gib einen Code ein
   - ✅ **Admin Panel**: Klicke "Admin Panel" → Benutzer verwalten
   - ✅ **Passwort ändern**: Klicke "Change Password"

**Wie funktioniert die Authentifizierung?**
- **Login**: Backend generiert JWT-Token (gültig 60 Minuten)
- **Token-Speicherung**: Im Browser LocalStorage (siehe `App/src/contexts/AuthContext.tsx`)
- **API-Requests**: Token wird bei jedem Fetch im `Authorization`-Header mitgeschickt
- **Backend-Prüfung**: Jeder API-Endpoint validiert Token (siehe `database/auth.py`)

4. **API-Dokumentation**:\
http://localhost:8000/docs

### Datenbank-Wartung

> **📋 Alle Import/Export/Merge Commands**: Siehe [`database/IMPORT_EXPORT_GUIDE.md`](database/IMPORT_EXPORT_GUIDE.md)

**Mehrere Variantenbäume zusammenführen (Merge)**

Wenn zusätzliche Produktfamilien aus einer neuen `baum.json` in eine bestehende Datenbank importieren werden sollen, ohne die bestehende Datenbank zu überschreiben:

```bash
cd database

# Sicheres Merge: Behält alle existierenden Daten (Bilder, Labels, Links)
python merge_data.py \
  --current-db variantenbaum.db \
  --new-json ../baum_neu.json

# Optional: Dry-run (zeigt nur Änderungen an, führt nichts aus)
python merge_data.py \
  --current-db variantenbaum.db \
  --new-json ../baum_neu.json \
  --dry-run
```

**Was passiert beim Merge?**
1. 💾 Exportiert aktuelle DB zu JSON (mit allen Daten: Bilder, Links, Labels)
2. 🔀 Merged mit neuen Produktschlüsseln aus `baum_neu.json`
3. 📦 Erstellt Backup: `variantenbaum.db.backup_TIMESTAMP`
4. ♻️ Importiert gemergtes JSON in neue DB (Closure Table neu berechnet)
5. 👤 Benutzer bleiben unverändert

## Datenbankschema & Architektur

### Datenbank-Struktur

**1. `users` - Benutzerverwaltung**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT 1,
    must_change_password BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. `nodes` - Produkthierarchie**
```sql
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_type TEXT CHECK(node_type IN ('family', 'group', 'node')),
    level INTEGER,
    code TEXT,
    label TEXT,
    label_en TEXT,
    pictures TEXT,  -- JSON Array
    links TEXT,     -- JSON Array
    parent_id INTEGER,
    family_code TEXT,
    group_code TEXT,
    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);
```

**3. `node_closure` - Closure Table für Performance**
```sql
CREATE TABLE node_closure (
    ancestor_id INTEGER NOT NULL,
    descendant_id INTEGER NOT NULL,
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id),
    FOREIGN KEY (ancestor_id) REFERENCES nodes(id),
    FOREIGN KEY (descendant_id) REFERENCES nodes(id)
);
```

**Vorteile der Closure Tabelle:**
- **O(1) Hierarchie-Abfragen**: "Alle Kinder eines Knotens" ohne Rekursion
- **Schnelle Pfad-Queries**: "Ist X ein Nachfahre von Y?" mit einem JOIN
- **Vorberechnete Tiefen**: Direkt verfügbar ohne Traversierung

**4. `constraints` - Produktregeln & Validierung**
```sql
CREATE TABLE constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL,
    family_code TEXT NOT NULL,
    conditions TEXT NOT NULL,  -- JSON Array: [{level, code}]
    allowed_codes TEXT NOT NULL, -- JSON Array: [code1, code2, ...]
    description TEXT
);
```

**5. `product_successors` - Nachfolgeprodukte**
```sql
CREATE TABLE product_successors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id INTEGER NOT NULL,
    target_node_id INTEGER,
    announcement_date TEXT,
    discontinuation_date TEXT,
    comment TEXT,
    comment_en TEXT,
    FOREIGN KEY (source_node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES nodes(id) ON DELETE SET NULL
);
```

**Verwendung:**
- Markiert auslaufende Produkte (Abkündigungsdatum)
- Verlinkt zu Nachfolgeprodukten
- Frontend zeigt gelbe Warnung bei abgekündigten Optionen

### Datenimport-Prozess

Das `import_data.py` Script führt folgende Schritte aus:

1. **JSON Parsing**: Liest hierarchische Produktstruktur
2. **Level-Berechnung**: Überspringt "Pattern Container", zählt nur echte Code-Nodes
3. **Node-Import**: Speichert Produktfamilien, Gruppen und Nodes
4. **Closure Table Build**: Berechnet alle Ancestor-Descendant Beziehungen

**Beispiel-Hierarchie**:
```
Family: ABC
  ├─ Group: ABC1
  │   ├─ Level 1: Pattern Container
  │   │   ├─ Node: A (Level 1)
  │   │   └─ Node: B (Level 1)
  │   ├─ Level 2: Pattern Container
  │   │   ├─ Node: 1 (Level 2)
  │   │   └─ Node: 2 (Level 2)
```

### API-Architektur

**Backend-Struktur**:
```
database/
├── api.py              # FastAPI Application, REST Endpoints
├── auth.py             # JWT Authentication, Password Hashing
├── schema.sql          # Datenbank-Schema Definition
└── import_data.py      # JSON → SQLite Import Script
```

**Frontend-Struktur**:
```
App/src/
├── main.tsx                    # Entry Point
├── App.tsx                     # Main Application Component
├── api/client.ts               # API Client, Type Definitions
├── contexts/AuthContext.tsx    # Authentication State Management
├── pages/
│   ├── LoginPage.tsx           # Login UI
│   └── AdminPanel.tsx          # User Management UI
└── components/
    ├── ProtectedRoute.tsx      # Route Guards
    └── ChangePasswordModal.tsx # Password Change Dialog
```

## Produktionsreife Deployment

### Unterschiede: Lokal vs. Produktion

| | Lokal (Testen) | Produktion |
|--------|----------------|------------|
| **Datenbank** | SQLite (lokale Datei) | PostgreSQL / Azure SQL |
| **Umgebungsvariablen** | `.env` Datei | Azure Key Vault |
| **Backend** | `uvicorn --reload` | Docker Container |
| **Frontend** | Vite Dev Server | Statische Files |



### Anpassungen für PostgreSQL/Azure SQL

#### 1. Code-Änderungen in `api.py`

**Datenbank-Connection:**
```python
# Von SQLite:
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    # ...

# Zu PostgreSQL (mit SSL/TLS):
import psycopg2
def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")  # oder aus Key Vault
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')  # ← Erzwingt SSL
    # ...

# Zu Azure SQL (SSL im Connection String):
import pyodbc
def get_db():
    # Connection String mit Encryption:
    # "DRIVER={ODBC Driver 17};SERVER=...;DATABASE=...;UID=...;PWD=...;Encrypt=yes;TrustServerCertificate=no"
    DATABASE_URL = os.getenv("DATABASE_URL")  # oder aus Key Vault
    conn = pyodbc.connect(DATABASE_URL)
    # ...
```

**SQL-Platzhalter ändern (alle Queries):**
```python
# SQLite verwendet ?
cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))

# PostgreSQL verwendet %s
cursor.execute("SELECT * FROM nodes WHERE id = %s", (node_id,))

# Azure SQL bleibt bei ?
cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
```

**CORS-Konfiguration:**
```python
# Aktuell (lokal):
origins = ["http://localhost:5173"]

# Produktion:
origins = [
    "https://deine-frontend-domain.azurestaticapps.net",
    "https://www.deine-domain.com"
]
```

#### 2. Schema-Anpassungen in `schema.sql`

```sql
-- SQLite:
id INTEGER PRIMARY KEY AUTOINCREMENT

-- PostgreSQL:
id SERIAL PRIMARY KEY

-- Azure SQL:
id INT IDENTITY(1,1) PRIMARY KEY
```

#### 3. Frontend URL-Anpassung in `App/src/api/client.ts`

```typescript
// Aktuell (lokal):
const API_BASE_URL = 'http://localhost:8000';

// Produktion - Option 1 (hardcoded):
const API_BASE_URL = 'https://dein-backend.azurewebsites.net';

// Produktion - Option 2
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

**Wenn Option 2**: Erstelle `App/.env.production`:
```bash
VITE_API_BASE_URL=https://dein-backend.azurewebsites.net
```

`VITE_API_BASE_URL` ist **kein Secret** und kann ins Repo committed werden.

### Azure Key Vault Integration (Backend Secrets)

**Was kommt in Azure Key Vault?**
- `jwt-secret` (JWT Secret für Token-Signierung)
- `database-url` (PostgreSQL/Azure SQL Connection String mit Passwort!)

**Was NICHT?**
- `VITE_API_BASE_URL` (Frontend-URL, kein Secret)
- `KEY_VAULT_URL` (URL zum Key Vault selbst, kein Secret)

**Code-Änderung in `api.py`:**

```python
# Aktuell (lokal mit .env):
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///variantenbaum.db")

# Produktion (mit Azure Key Vault):
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault URL aus Environment
key_vault_url = os.getenv("KEY_VAULT_URL")

credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)

# Secrets aus Key Vault holen
JWT_SECRET = client.get_secret("jwt-secret").value
DATABASE_URL = client.get_secret("database-url").value
```

### Image Storage Strategie

**Entwicklung (aktuell für lokales Testen):**

*Backend (api.py):*
```python
# POST /api/upload Endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile):
    # Speichert Datei lokal
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Gibt relativen Pfad zurück
    return {"path": f"/uploads/{file.filename}"}
```
- Bilder werden lokal im `database/uploads/` Verzeichnis gespeichert
- Datenbank speichert relative Pfade: `/uploads/product.jpg`

*Frontend:*
```typescript
// Upload (aus App.tsx)
const formData = new FormData();
formData.append('file', file);
const response = await fetch('/api/upload', { method: 'POST', body: formData });
const { path } = await response.json();  // "/uploads/product.jpg"

// Anzeige
<img src={`${API_BASE_URL}${node.pictures[0]}`} />
// Ergibt: http://localhost:8000/uploads/product.jpg
```

**Produktion (Azure Blob Storage):**

**Voraussetzung: Azure Storage Account erstellen (Admins)**

```bash
# 1. Azure Storage Account erstellen
az storage account create \
  --name produktkonfigurator \
  --resource-group ihre-resource-group \
  --location westeurope \
  --sku Standard_LRS

# 2. Container "uploads" erstellen
az storage container create \
  --name uploads \
  --account-name produktkonfigurator \
  --public-access off  # Nicht öffentlich zugänglich

# 3. Connection String abrufen (kommt in Key Vault)
az storage account show-connection-string \
  --name produktkonfigurator \
  --resource-group ihre-resource-group
# Ergebnis:
# "DefaultEndpointsProtocol=https;AccountName=produktkonfigurator;AccountKey=...;EndpointSuffix=core.windows.net"
```

**Azure Blob Storage URL-Struktur:**
```
https://{storage_account_name}.blob.core.windows.net/{container}/{blob_name}
```

**Schritt 2: Connection String im Key Vault speichern**

Der Connection String aus Schritt 1 muss als Secret im Azure Key Vault gespeichert werden:

```bash
# Connection String im Key Vault speichern
az keyvault secret set \
  --vault-name ihr-key-vault \
  --name AZURE-STORAGE-CONNECTION-STRING \
  --value "DefaultEndpointsProtocol=https;AccountName=produktkonfigurator;AccountKey=...;EndpointSuffix=core.windows.net"
```

**Wichtig:** Der API-Container muss Zugriff auf dieses Secret haben (wie bei `DATABASE_URL` auch).

**Schritt 3: Automatische Azure Blob Storage Erkennung**

Der Backend-Code **erkennt automatisch**, ob Azure Blob Storage verwendet werden soll:

**Code in `api.py` (bereits implementiert):**
```python
# 1. Conditional Import (try/except für optionale Azure SDK)
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# 2. Automatische Umgebungserkennung beim App-Start
blob_service: Optional[BlobServiceClient] = None
if AZURE_AVAILABLE and os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
    blob_service = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )
    print("✅ Azure Blob Storage aktiviert")
else:
    print("ℹ️  Lokaler File Storage (uploads/) wird genutzt")

# 3. Upload Endpoint mit automatischer Speicherort-Wahl
@app.post("/api/upload")
async def upload_file(file: UploadFile):
    if blob_service:
        # PRODUKTION: Upload zu Azure Blob Storage
        blob_client = blob_service.get_blob_client(
            container="uploads",
            blob=file.filename
        )
        blob_client.upload_blob(await file.read())
        azure_url = blob_client.url
        return {"path": azure_url}  # Absolute URL
    else:
        # ENTWICKLUNG: Upload zu lokalem uploads/ Ordner
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"path": f"/uploads/{file.filename}"}  # Relative URL
```

**Wie funktioniert die automatische Erkennung?**

1. **Lokal (Entwicklung):**
   - `AZURE_STORAGE_CONNECTION_STRING` nicht gesetzt
   - → `blob_service = None`
   - → Upload nutzt `uploads/` Ordner
   - → Gibt relative URLs zurück: `/uploads/file.jpg`

2. **Produktion (Azure Container):**
   - `AZURE_STORAGE_CONNECTION_STRING` aus Key Vault geladen
   - → `blob_service = BlobServiceClient(...)`
   - → Upload nutzt Azure Blob Storage
   - → Gibt absolute URLs zurück: `https://storage.blob.core.windows.net/uploads/file.jpg`

**Dependencies:**
- Werden in Production automatisch im Docker Image installiert (siehe Dockerfile)

**Schritt 4: Frontend-Code anpassen**
```typescript
// Upload: KEINE Änderung (weiterhin über POST /api/upload)
const formData = new FormData();
formData.append('file', file);
const response = await fetch('/api/upload', { method: 'POST', body: formData });
const { path } = await response.json();  
// Jetzt: "https://storage.blob.core.windows.net/uploads/product.jpg"

// Anzeige: Funktioniert jetzt mit absoluten URLs
<img src={node.pictures[0]} />
// Kein ${API_BASE_URL} Prefix mehr!
```

**Schritt 5: Migration existierender Bilder (einmaliges Script)**
```python
# Alle lokalen Bilder zu Azure hochladen + Datenbank-Pfade updaten
import sqlite3
from azure.storage.blob import BlobServiceClient

# Azure Connection String aus Key Vault
blob_service = BlobServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
conn = sqlite3.connect("variantenbaum.db")

for file in os.listdir("uploads/"):
    # 1. Upload zu Azure Blob Storage
    with open(f"uploads/{file}", "rb") as data:
        blob_client = blob_service.get_blob_client("uploads", file)
        blob_client.upload_blob(data)
        azure_url = blob_client.url
        # Beispiel: "https://storage.blob.core.windows.net/uploads/file.jpg"
    
    # 2. DB updaten: Relativer Pfad → Absolute Azure URL
    # Vorher: /uploads/file.jpg
    # Nachher: https://storage.blob.core.windows.net/uploads/file.jpg
    conn.execute(
        "UPDATE nodes SET pictures = replace(pictures, ?, ?) WHERE pictures LIKE ?",
        (f'/uploads/{file}', azure_url, f'%{file}%')
    )
conn.commit()
```

**Wichtig**: 
- Datenbank-Struktur (`pictures` als TEXT) unterstützt beide Varianten
- Kein Breaking Change: Lokal und Azure funktionieren gleichzeitig (während Migration)

### Build & Deployment

**Production-Deployment besteht aus zwei Phasen:**

**Phase 1: Infrastruktur vorbereiten**

Erstelle Azure-Ressourcen via Terraform/Bicep oder Azure Portal:
- Azure Storage Account + Container "uploads"
- Azure SQL Database
- Azure Container Apps (Backend)
- Azure Static Web Apps (Frontend)
- Azure Key Vault mit Secrets:
  - `database-url` (PostgreSQL/Azure SQL Connection String)
  - `jwt-secret` (JWT Secret für Token-Signierung)
  - `AZURE-STORAGE-CONNECTION-STRING` (Blob Storage Connection String)

**Phase 2: Pipeline Deployment**

Pipeline `azure-pipelines.yml` übernimmt Build & Deployment:
- **Frontend**: `npm run build` → Statische Files zu Azure Static Web Apps
- **Backend**: `docker build` → Container Image zu Azure Container Apps
  - Dockerfile installiert alle Dependencies aus `requirements.txt` (inkl. `azure-storage-blob`)
  - Container lädt Secrets aus Key Vault (via Azure Managed Identity)
  - Code erkennt, ob `AZURE_STORAGE_CONNECTION_STRING` gesetzt ist und nutzt dann Azure Blob Storage

## API-Dokumentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
