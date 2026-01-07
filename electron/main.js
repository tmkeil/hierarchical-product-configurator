const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const isDev = require('electron-is-dev');

let mainWindow;
let backendProcess;

// Pfade basierend auf Development oder Production
const getResourcePath = (relativePath) => {
  if (isDev) {
    return path.join(__dirname, '..', relativePath);
  }
  return path.join(process.resourcesPath, relativePath);
};

const BACKEND_PATH = isDev 
  ? path.join(__dirname, '..', 'database', 'api.py')
  : path.join(process.resourcesPath, 'backend', 'backend.exe');

const FRONTEND_PATH = isDev
  ? 'http://localhost:5173'  // Vite Dev Server
  : `file://${path.join(process.resourcesPath, 'frontend', 'index.html')}`;

const DB_PATH = isDev
  ? path.join(__dirname, '..', 'database', 'variantenbaum.db')
  : path.join(process.resourcesPath, 'database', 'variantenbaum.db');

const UPLOADS_PATH = isDev
  ? path.join(__dirname, '..', 'database', 'uploads')
  : path.join(app.getPath('userData'), 'uploads');

// Backend starten
function startBackend() {
  return new Promise((resolve, reject) => {
    console.log('Starte Backend...');
    console.log('Backend Path:', BACKEND_PATH);
    console.log('DB Path:', DB_PATH);
    console.log('Uploads Path:', UPLOADS_PATH);

    // Erstelle uploads Verzeichnis falls nicht vorhanden
    if (!fs.existsSync(UPLOADS_PATH)) {
      fs.mkdirSync(UPLOADS_PATH, { recursive: true });
    }

    // Environment Variables für Backend
    const env = {
      ...process.env,
      DB_PATH: DB_PATH,
      UPLOADS_DIR: UPLOADS_PATH,
      JWT_SECRET: 'electron-demo-secret-change-in-production',
      JWT_EXPIRATION_MINUTES: '60',
      INITIAL_ADMIN_USERNAME: 'admin',
      INITIAL_ADMIN_PASSWORD: 'ChangeMe123!'
    };

    if (isDev) {
      // Development: Python direkt ausführen
      backendProcess = spawn('python', [BACKEND_PATH], { env });
    } else {
      // Production: Gebundelte backend.exe ausführen
      backendProcess = spawn(BACKEND_PATH, [], { env });
    }
    
    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Backend Start Fehler:', error);
      dialog.showErrorBox(
        'Backend Fehler',
        `Backend konnte nicht gestartet werden:\n${error.message}`
      );
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend Process beendet mit Code: ${code}`);
    });

    // Warte 8 Sekunden damit Backend SICHER bereit ist
    console.log('[Electron] Warte 8 Sekunden auf Backend...');
    setTimeout(() => {
      console.log('[Electron] Backend sollte jetzt bereit sein!');
      resolve();
    }, 8000);
  });
}

// Electron Fenster erstellen
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false // Erst zeigen wenn Backend bereit ist
  });

  // Loading Screen zeigen
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));
  mainWindow.show();

  // Warte 500ms damit Loading Screen sichtbar wird
  setTimeout(() => {
    console.log('[Electron] Lade Frontend...');
    if (isDev) {
      mainWindow.loadURL('http://localhost:5173');  // Vite Dev Server
    } else {
      // Production: Lokale HTML-Dateien laden
      const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
      console.log('[Electron] Frontend Path:', frontendPath);
      mainWindow.loadFile(frontendPath);
    }
  }, 500);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // DevTools immer öffnen (zum Debuggen)
  mainWindow.webContents.openDevTools();
}

// App bereit
app.whenReady().then(async () => {
  try {
    await startBackend();
    createWindow();
  } catch (error) {
    console.error('Startup Fehler:', error);
    dialog.showErrorBox(
      'Startup Fehler',
      `Anwendung konnte nicht gestartet werden:\n${error.message}`
    );
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Alle Fenster geschlossen
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// App wird beendet - Backend Process killen
app.on('will-quit', () => {
  if (backendProcess) {
    console.log('Beende Backend Process...');
    backendProcess.kill();
  }
});

// Cleanup bei Fehler
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  if (backendProcess) {
    backendProcess.kill();
  }
});
