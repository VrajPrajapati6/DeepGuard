/**
 * Electron Main Process
 * Creates and manages the application window.
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#0a0e27',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    frame: true,
    titleBarStyle: 'default',
    icon: path.join(__dirname, 'public', 'icon.png')
  });

  // Load the app
  const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, 'build', 'index.html')}`;
  mainWindow.loadURL(startUrl);

  // Open DevTools in development
  if (process.env.ELECTRON_START_URL) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
