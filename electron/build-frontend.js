const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🎨 Building Frontend...\n');

// Gehe ins App-Verzeichnis und führe npm run build aus
const npmBuild = spawn('npm', ['run', 'build'], {
  cwd: path.join(__dirname, '..', 'App'),
  shell: true,
  stdio: 'inherit',
  env: { ...process.env, ELECTRON_BUILD: 'true' }  // Setze Flag für Electron Build
});

npmBuild.on('close', (code) => {
  if (code !== 0) {
    console.error(`\n❌ Frontend Build fehlgeschlagen mit Code ${code}`);
    process.exit(1);
  }

  console.log('\n✅ Frontend gebaut!\n');

  // Kopiere dist/ zu resources/frontend/
  const distSource = path.join(__dirname, '..', 'App', 'dist');
  const frontendTarget = path.join(__dirname, 'resources', 'frontend');

  if (!fs.existsSync(frontendTarget)) {
    fs.mkdirSync(frontendTarget, { recursive: true });
  }

  // Kopiere alle Dateien rekursiv
  copyRecursive(distSource, frontendTarget);

  console.log('✅ Frontend kopiert nach resources/frontend/\n');
  console.log('🎉 Frontend Build abgeschlossen!\n');
  console.log('Nächster Schritt: npm run build:win\n');
});

npmBuild.on('error', (error) => {
  console.error('❌ Fehler beim Frontend Build:', error);
  process.exit(1);
});

// Hilfsfunktion zum rekursiven Kopieren
function copyRecursive(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();

  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach(childItemName => {
      copyRecursive(
        path.join(src, childItemName),
        path.join(dest, childItemName)
      );
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}
