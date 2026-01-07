const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔨 Building Backend mit PyInstaller...\n');

// Erstelle resources Verzeichnis falls nicht vorhanden
const resourcesDir = path.join(__dirname, 'resources');
if (!fs.existsSync(resourcesDir)) {
  fs.mkdirSync(resourcesDir, { recursive: true });
}

['backend', 'frontend', 'database'].forEach(dir => {
  const targetDir = path.join(resourcesDir, dir);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
});

// PyInstaller ausführen mit venv-win
const venvPython = path.join(__dirname, '..', 'venv-win', 'Scripts', 'python.exe');
const pyinstaller = spawn(venvPython, [
  '-m',
  'PyInstaller',
  '--clean',
  '--noconfirm',
  'backend.spec'
], {
  cwd: __dirname,
  shell: true,
  stdio: 'inherit'
});

pyinstaller.on('close', (code) => {
  if (code !== 0) {
    console.error(`\n❌ PyInstaller fehlgeschlagen mit Code ${code}`);
    process.exit(1);
  }

  console.log('\n✅ Backend gebaut!\n');
  
  // Kopiere backend.exe zu resources/backend/
  const backendExe = path.join(__dirname, 'dist', 'backend.exe');
  const targetPath = path.join(resourcesDir, 'backend', 'backend.exe');
  
  if (fs.existsSync(backendExe)) {
    fs.copyFileSync(backendExe, targetPath);
    console.log('✅ backend.exe kopiert nach resources/backend/\n');
  } else {
    console.error('❌ backend.exe nicht gefunden in dist/\n');
    process.exit(1);
  }

  // Kopiere Datenbank
  const dbSource = path.join(__dirname, '..', 'database', 'variantenbaum.db');
  const dbTarget = path.join(resourcesDir, 'database', 'variantenbaum.db');
  
  if (fs.existsSync(dbSource)) {
    fs.copyFileSync(dbSource, dbTarget);
    console.log('✅ variantenbaum.db kopiert nach resources/database/\n');
  } else {
    console.warn('⚠️  variantenbaum.db nicht gefunden - vergiss nicht die DB zu erstellen!\n');
  }

  // Kopiere uploads/ Ordner falls vorhanden
  const uploadsSource = path.join(__dirname, '..', 'database', 'uploads');
  const uploadsTarget = path.join(resourcesDir, 'database', 'uploads');
  
  if (fs.existsSync(uploadsSource)) {
    if (!fs.existsSync(uploadsTarget)) {
      fs.mkdirSync(uploadsTarget, { recursive: true });
    }
    
    // Kopiere alle Dateien aus uploads/
    const files = fs.readdirSync(uploadsSource);
    files.forEach(file => {
      const src = path.join(uploadsSource, file);
      const dest = path.join(uploadsTarget, file);
      if (fs.statSync(src).isFile()) {
        fs.copyFileSync(src, dest);
      }
    });
    console.log(`✅ ${files.length} Dateien aus uploads/ kopiert\n`);
  }

  console.log('🎉 Backend Build abgeschlossen!\n');
  console.log('Nächster Schritt: npm run build:frontend\n');
});

pyinstaller.on('error', (error) => {
  console.error('❌ Fehler beim Starten von PyInstaller:', error);
  console.error('\nStelle sicher dass PyInstaller installiert ist:');
  console.error('  pip install pyinstaller\n');
  process.exit(1);
});
