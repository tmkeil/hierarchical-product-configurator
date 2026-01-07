# Electron Desktop App - Build-Anleitung

Diese Anleitung zeigt, wie du aus der Webanwendung eine eigenständige Windows `.exe` erstellen kannst.

## Voraussetzungen

### 1. Software installieren

**Auf deinem Entwicklungs-PC (Windows):**

```bash
# Node.js und npm (falls noch nicht installiert)
# Download: https://nodejs.org/

# PyInstaller für Backend-Bundling
pip install pyinstaller

# Electron Dependencies installieren
cd electron
npm install
```

### 2. Datenbank vorbereiten

Die `.exe` wird die aktuelle Datenbank bündeln. Stelle sicher, dass sie aktuell ist:

```bash
cd database

# Neue Datenbank erstellen mit aktuellen Produktdaten
python import_data.py --json ../baum.json --db variantenbaum.db --recreate --closure
```

## Build-Prozess

### Alle Schritte auf einmal (empfohlen):

```bash
cd electron
npm run build:win
```

Das führt automatisch aus:
1. ✅ Backend → `backend.exe` (mit PyInstaller)
2. ✅ Frontend → Produktions-Build (mit Vite)
3. ✅ Electron → Windows Installer `.exe` (mit electron-builder)

**Dauer:** ~5-10 Minuten (beim ersten Mal länger)

**Ergebnis:** `electron/dist/Produktkonfigurator-Setup-1.0.0.exe`

---

### Schritte einzeln (nur bei Problemen):

#### Schritt 1: Backend bundlen

```bash
cd electron
npm run build:backend
```

**Was passiert:**
- PyInstaller erstellt `backend.exe` aus `api.py`
- Alle Python-Dependencies werden eingebunden (FastAPI, Uvicorn, SQLite, etc.)
- `backend.exe` wird nach `resources/backend/` kopiert
- `variantenbaum.db` wird nach `resources/database/` kopiert
- `uploads/` Ordner wird kopiert (falls vorhanden)

**Ergebnis:** `electron/resources/backend/backend.exe` (~70-100 MB)

#### Schritt 2: Frontend bundlen

```bash
npm run build:frontend
```

**Was passiert:**
- Vite erstellt Produktions-Build von React-App
- Optimiert und minifiziert alle Assets
- `App/dist/` wird nach `resources/frontend/` kopiert

**Ergebnis:** `electron/resources/frontend/` mit `index.html`, `assets/`, etc.

#### Schritt 3: Electron App packen

```bash
npm run build:win
```

**Was passiert:**
- electron-builder erstellt Windows Installer
- Bündelt: `main.js`, `resources/`, Node.js, Chromium
- Erstellt NSIS-Installer (Setup.exe)

**Ergebnis:** `electron/dist/Produktkonfigurator-Setup-1.0.0.exe` (~150-200 MB)

---

## Die fertige .exe testen

```bash
# Installer ausführen
cd electron/dist
./Produktkonfigurator-Setup-1.0.0.exe

# Installiert nach: C:/Program Files/Produktkonfigurator/
# Desktop-Verknüpfung wird erstellt
```

**Was passiert beim ersten Start:**
1. Backend startet im Hintergrund (`backend.exe`)
2. SQLite-Datenbank wird geladen (aus Installation)
3. Uploads-Ordner wird erstellt in: `C:/Users/Username/AppData/Roaming/produktkonfigurator/uploads/`
4. Electron-Fenster öffnet sich mit der App
5. Login-Seite erscheint

**Login-Daten:**
- Username: `admin`
- Passwort: `ChangeMe123!`

---

## Neue Version erstellen (Update)

Wenn du Änderungen gemacht hast (neue Features, neue Produktdaten):

### 1. Version-Nummer erhöhen

```bash
cd electron

# In package.json:
# "version": "1.0.0"  →  "version": "1.1.0"
```

### 2. Datenbank aktualisieren (falls nötig)

```bash
cd database
python import_data.py --json ../baum_neu.json --db variantenbaum.db --recreate --closure
```

### 3. Neu bauen

```bash
cd electron
npm run build:win
```

**Ergebnis:** `Produktkonfigurator-Setup-1.1.0.exe`

### 4. An User verteilen

Die User müssen:
1. Alte Version deinstallieren (oder einfach überschreiben)
2. Neue Setup.exe herunterladen
3. Installieren → Fertig!

**Hinweis:** User-Daten gehen NICHT verloren, da sie in `AppData/Roaming/` liegen (außer bei Deinstallation mit "Daten löschen").

---

## Verzeichnisstruktur

```
electron/
├── package.json              # Electron Dependencies & Build-Config
├── main.js                   # Electron Main Process (startet Backend)
├── preload.js                # Preload Script (Security)
├── loading.html              # Loading Screen
├── backend.spec              # PyInstaller Config für Backend
├── build-backend.js          # Backend Build-Script
├── build-frontend.js         # Frontend Build-Script (aktuell ungenutzt, in package.json direkt)
├── assets/
│   └── icon.ico              # App-Icon (TODO: erstellen)
├── resources/                # Wird von Build-Scripts befüllt
│   ├── backend/
│   │   └── backend.exe       # Gebündeltes FastAPI Backend
│   ├── frontend/
│   │   ├── index.html
│   │   └── assets/           # React Production Build
│   └── database/
│       ├── variantenbaum.db  # SQLite Datenbank
│       └── uploads/          # Bestehende Bilder
└── dist/                     # Build Output
    └── Produktkonfigurator-Setup-1.0.0.exe
```

---

## Troubleshooting

### Backend startet nicht

**Problem:** `backend.exe` fehlt oder startet nicht

**Lösung:**
```bash
# PyInstaller neu installieren
pip install --upgrade pyinstaller

# Backend manuell testen
cd electron
pyinstaller --clean backend.spec

# backend.exe direkt ausführen
cd dist
./backend.exe
```

### Frontend wird nicht angezeigt

**Problem:** Weißer Bildschirm nach Backend-Start

**Lösung:**
```bash
# Frontend manuell neu bauen
cd App
npm run build

# Prüfe ob dist/ Ordner erstellt wurde
ls dist/

# Kopiere manuell nach electron/resources/frontend/
```

### Große Dateigröße

**Problem:** `.exe` ist >300 MB

**Das ist normal:**
- Backend: ~70-100 MB (Python + Dependencies)
- Frontend: ~10-20 MB (React + Assets)
- Electron: ~100-150 MB (Chromium + Node.js)

**Optimierung (optional):**
```bash
# UPX Kompression aktivieren (in backend.spec)
upx=True  # Reduziert um ~30-40%
```

### "App kann nicht gestartet werden" bei Usern

**Problem:** Windows Smart Screen Warnung

**Grund:** App ist nicht signiert (kein Code-Signing-Zertifikat)

**Lösung für User:**
1. Rechtsklick auf `.exe` → "Eigenschaften"
2. Unten: ☑️ "Zulassen" → OK
3. Dann normal starten

**Langfristige Lösung:** Code-Signing-Zertifikat kaufen (~€300/Jahr)

---

## Development Mode (lokales Testen)

Für schnelles Testen ohne Build:

```bash
# Terminal 1: Backend starten
cd database
python api.py

# Terminal 2: Frontend starten
cd App
npm run dev

# Terminal 3: Electron starten (lädt lokale Server)
cd electron
npm start
```

Electron lädt dann `http://localhost:5173` (Frontend) und `http://localhost:8000` (Backend).

---

## Icon erstellen (TODO)

Die App braucht noch ein Icon:

```bash
# Icon-Datei erstellen: electron/assets/icon.ico
# Format: .ico (Windows)
# Größen: 16x16, 32x32, 64x64, 128x128, 256x256

# Kostenloses Tool: https://www.img2go.com/convert-to-ico
```

Dann in `package.json` bereits konfiguriert:
```json
"build": {
  "win": {
    "icon": "assets/icon.ico"
  }
}
```

---

## Zusammenfassung

**Für neue .exe erstellen:**
```bash
cd electron
npm run build:win
# → electron/dist/Produktkonfigurator-Setup-1.0.0.exe
```

**Für User:**
- Eine `.exe` herunterladen
- Installieren
- Starten
- Login mit `admin` / `ChangeMe123!`

Fertig! 🎉
