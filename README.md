# Produktschlüsselkonfigurator

Ein hierarchischer Produktkonfigurator für Typcode-basierte Produktvarianten mit integrierter Benutzerverwaltung und Authentifizierung.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Technologie-Stack](#technologie-stack)
- [Entwicklung & Maintenance](#entwicklung--maintenance)
- [Lokale Installation & Testen](#lokale-installation--testen)
- [Datenbankschema & Architektur](#datenbankschema--architektur)
- [Produktionsreife Deployment](#produktionsreife-deployment)
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
   - Visuelle Darstellung mit Bildern und technischen Informationen
   - Export der Konfiguration als Produktschlüssel

2. **Typcode-Dekodierung**:
   - Eingabe eines bestehenden Produktschlüssels
   - Automatische Auflösung zu Produktfamilie, Gruppe und allen Ebenen
   - Anzeige vollständiger Produktinformationen

3. **Admin-Panel**:
   - Benutzerverwaltung (Erstellen, Anzeigen von Benutzern)
   - Rollenzuweisung (Admin/User)
   - Passwort-Management
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

**Entwicklungszeit:** 2 Monate (~19.000 Zeilen Code mit Copilot).

Die Codezeilen sind das Ergebnis der eigentlichen Arbeit: Architektur-Entscheidungen (Dependency Injection, Closure Table Pattern), Design des hierarchischen Datenmodells, Analyse kontext-abhängiger Code-Bedeutungen und manuelle Erstellung von Mapping-Regeln. Copilot unterstützte bei der Umsetzung und Best Practices.

### Projektstruktur

Das Projekt besteht aus zwei Komponenten mit unterschiedlichen Entwicklungszyklen:

**1. Webanwendung - 3 Wochen**

Features wurden iterativ erweitert, sobald neue Use Cases während der Entwicklung sichtbar wurden.\
Die Architektur ermöglicht einen nahtlosen Wechsel zwischen SQLite (Entwicklung) und PostgreSQL/Azure SQL (Produktion) durch Dependency Injection.

**Features:**
- **FastAPI REST API** mit JWT-Auth, Benutzerverwaltung, Constraint-Validierung
- **React Frontend** mit hierarchischem Produktnavigator, Admin Panel, Typcode-Dekodierung
- **Komplexer Produktkonfigurator**: 
  - Dynamische Kompatibilität zwischen Produktoptionen (Forward/Backward Compatibility Checks)
  - Nutzer können Optionen in beliebiger Reihenfolge wählen → System validiert automatisch machbare Kombinationen
  - Details zur Kompatibilitäts-Logik: Siehe [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) (Query 4 Algorithmus)

**Umfang:**
- **~13.000 Zeilen Code** (TypeScript + Python)
- **Frontend:** ~6.500 Zeilen React/TypeScript
- **Backend:** ~6.000 Zeilen FastAPI/Python
- **15+ REST API Endpoints**

**2. Python-Scripts für Datenvorbereitung - 4 Wochen**

Entwickelt in einem iterativen Prozess, da neue Anforderungen erst nach Analyse der Datenquellen erkennbar wurden.

Die größte Herausforderung war die Entwicklung einer JSON-Struktur, die alle Produktvarianten hierarchisch abbildet und gleichzeitig Labels (Beschreibungen) automatisch den richtigen Code-Segmenten zuordnet. Erschwerend kam hinzu, dass derselbe Code je nach Produktfamilie unterschiedliche Bedeutungen haben kann. Ein "A" kann in einer Familie "Aluminium", in einer anderen "Automatik" bedeuten.

**Entwickelte Tools:**
- **`createBaum.py`**: Konvertiert Excel-Typcodes zu JSON-Baumstruktur
- **`schema_search.py`**: Filtert relevante Produkte aus der Baumstruktur für die Label-Zuordnung (2689 Zeilen)
- **`label_mapper.py`**: Ordnet Labels automatisch zu Code-Segmenten mit kontext-spezifischen Regeln (3042 Zeilen)

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

### Build & Deployment

**Pipeline `azure-pipelines.yml` übernimmt:**
- **Frontend**: `npm run build` erstellt statische Files in `App/dist/` → Deployment zu Azure Static Web Apps
- **Backend**: Docker Image wird gebaut aus `database/Dockerfile` → Deployment zu Azure Container Apps

## API-Dokumentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
