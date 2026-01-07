// Preload Script (läuft vor dem Renderer Process)
// Hier können sichere APIs für das Frontend bereitgestellt werden

const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Füge hier bei Bedarf APIs hinzu, z.B.:
  // platform: process.platform
});
