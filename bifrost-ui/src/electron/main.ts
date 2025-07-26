import { app, BrowserWindow, ipcMain } from 'electron';
import { getPreloadPath, getUIPath } from './pathResolver.js';
// Import fetch for ESM
import fetch from 'node-fetch';

// Store reference to main window to prevent garbage collection
let mainWindow: BrowserWindow | null = null;

// Create the browser window.
function createMainWindow() {
  // Destroy any existing window first to prevent duplicate handlers
  if (mainWindow) {
    // First remove all IPC handlers related to this window
    console.log('Destroying existing window, cleaning up first');
    
    // Remove IPC handlers before destroying the window
    try {
      if (mainWindow.webContents) {
        console.log('Removing any lingering listeners');
        // Use a safe approach to avoid errors if the window is already being destroyed
        mainWindow.removeAllListeners();
      }
    } catch (error) {
      console.error('Error cleaning up window:', error);
    }
    
    try {
      mainWindow.destroy();
    } catch (error) {
      console.error('Error destroying window:', error);
    }
    
    mainWindow = null;
  }

  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false, // For security reasons
      contextIsolation: true, // Protect against prototype pollution
      preload: getPreloadPath(), // Use the preload script
      // Enable sandbox mode for renderer processes
      sandbox: true,
      // Remote module is disabled by default in newer Electron versions
      // Additional security options
      webSecurity: true,
    },
  });
  
  const windowId = mainWindow.id;
  console.log(`Created new window with ID ${windowId}`);

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    console.log('Loading dev URL');
    mainWindow.loadURL('http://localhost:5123').catch(error => {
      console.error('Error loading URL:', error);
    });
    
    // Open the DevTools in development mode
    mainWindow.webContents.openDevTools();
  } else {
    console.log('Loading production file');
    mainWindow.loadFile(getUIPath());
  }

  // Setup handler for when the window is about to be closed
  // This runs BEFORE the closed event and gives us a chance to clean up
  mainWindow.on('close', () => {
    console.log(`Window ${windowId} is about to close, preparing cleanup`);
    
    try {
      // Perform additional cleanup here
      // Ensure IPC handlers specific to this window are removed
      // This is now handled by our window tracking system
    } catch (error) {
      console.error('Error during window close cleanup:', error);
    }
  });

  // Handle window being closed
  mainWindow.on('closed', () => {
    console.log(`Window ${windowId} closed, cleaning up resources`);
    mainWindow = null;
  });
  
  // Handle unresponsive window
  mainWindow.on('unresponsive', () => {
    console.log(`Window ${windowId} became unresponsive, attempting recovery`);
    
    try {
      if (mainWindow && !mainWindow.isDestroyed()) {
        // Try to reload the window
        mainWindow.reload();
      }
    } catch (error) {
      console.error('Error recovering unresponsive window:', error);
    }
  });
  
  // Handle window crashes using any to bypass TypeScript limitations
  (mainWindow.webContents as any).on('crashed', () => {
    console.error(`Window ${windowId} renderer process crashed, recreating window`);
    createMainWindow(); // Recreate the window
  });
  
  // Track renderer process termination
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`Window ${windowId} failed to load: ${errorDescription} (${errorCode})`);
  });
  
  return mainWindow;
}

// IPC handlers for user registration and login
function setupIPC() {
  // Define response types
  type ApiResponse = {
    message?: string;
    role?: string;
    [key: string]: any;
  };

  /**
   * Track which windows have which handlers registered to prevent memory leaks
   */
  const handlersByWindow = new Map<number, string[]>();

  /**
   * Register a handler that's tied to a specific window
   */
  function registerWindowHandler(
    window: BrowserWindow, 
    channel: string, 
    handler: (event: Electron.IpcMainEvent, ...args: any[]) => void
  ) {
    // Store the channel name for this window to clean up later
    const windowId = window.id;
    if (!handlersByWindow.has(windowId)) {
      handlersByWindow.set(windowId, []);
    }
    handlersByWindow.get(windowId)?.push(channel);
    
    // Register the handler
    ipcMain.on(channel, handler);
    
    console.log(`Registered handler for ${channel} on window ${windowId}`);
  }

  /**
   * Clean up all handlers for a specific window
   */
  function cleanupWindowHandlers(windowId: number) {
    const channels = handlersByWindow.get(windowId);
    if (!channels) return;
    
    console.log(`Cleaning up ${channels.length} handlers for window ${windowId}`);
    
    // Remove all listeners for this window
    channels.forEach(channel => {
      ipcMain.removeAllListeners(channel);
      console.log(`Removed all listeners for ${channel}`);
    });
    
    // Clear the tracking
    handlersByWindow.delete(windowId);
  }

  // We'll use a different approach for cleanup since the event isn't directly available
  // Instead, we'll track windows and clean up when they're closed
  app.on('browser-window-created', (_event, window) => {
    window.on('closed', () => {
      console.log(`Window ${window.id} closed, cleaning up handlers`);
      cleanupWindowHandlers(window.id);
    });
  });

  // We'll use a single handler to prevent memory leaks
  const registerUserHandler = async (event: Electron.IpcMainEvent, userData: any) => {
    try {
      // Get the sender window
      const window = BrowserWindow.fromWebContents(event.sender);
      if (!window) {
        console.error('Could not identify sender window');
        return;
      }
      
      console.log(`Registration request received from window ${window.id}:`, userData);
      
      // Validate input first to avoid potential issues
      if (!userData.username || !userData.password || !userData.role) {
        console.log('Invalid registration data');
        event.sender.send('registrationResponse', {
          success: false,
          message: 'Missing required fields'
        });
        return;
      }
      
      // Log the request details for debugging
      console.log('Sending registration request to:', 'http://localhost:3001/api/auth/register');
      
      // Set a timeout for the fetch operation
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      
      try {
        const response = await fetch('http://localhost:3001/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
          signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        console.log('Registration response status:', response.status, response.statusText);
        
        // Handle potential JSON parsing errors
        let data: ApiResponse;
        const textResponse = await response.text();
        try {
          data = JSON.parse(textResponse) as ApiResponse;
        } catch (parseError) {
          console.error('Failed to parse JSON response:', textResponse);
          data = { message: 'Invalid response from server' };
        }
        
        console.log('Registration response data:', data);
        
        // Make sure the window still exists before sending a response
        if (!window.isDestroyed()) {
          // Send the response back to the renderer
          event.sender.send('registrationResponse', {
            success: response.ok,
            message: data?.message || 'Registration completed'
          });
          
          console.log('Registration response sent to renderer');
        } else {
          console.log('Window destroyed, not sending response');
        }
      } catch (fetchError: any) {
        clearTimeout(timeout);
        
        if (fetchError.name === 'AbortError') {
          console.error('Registration request timed out');
          
          if (!window.isDestroyed()) {
            event.sender.send('registrationResponse', {
              success: false,
              message: 'Server request timed out'
            });
          }
        } else {
          throw fetchError; // Re-throw to be handled by the outer catch
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      
      try {
        event.sender.send('registrationResponse', {
          success: false,
          message: 'Network or server error'
        });
      } catch (sendError) {
        console.error('Failed to send error response:', sendError);
      }
    }
  };

  // Handle login requests with improved error handling
  const loginUserHandler = async (event: Electron.IpcMainEvent, userData: any) => {
    try {
      // Get the sender window
      const window = BrowserWindow.fromWebContents(event.sender);
      if (!window) {
        console.error('Could not identify sender window');
        return;
      }
      
      // Validate input first
      if (!userData.username || !userData.password) {
        console.log('Invalid login data');
        event.sender.send('loginResponse', {
          success: false,
          message: 'Missing username or password'
        });
        return;
      }

      console.log(`Login request received from window ${window.id} for user:`, userData.username);
      
      // Set a timeout for the fetch operation
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      
      try {
        const response = await fetch('http://localhost:3001/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
          signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        console.log('Login response status:', response.status, response.statusText);
        
        // Handle potential JSON parsing errors
        let data: ApiResponse;
        const textResponse = await response.text();
        try {
          data = JSON.parse(textResponse) as ApiResponse;
        } catch (parseError) {
          console.error('Failed to parse JSON response:', textResponse);
          data = { message: 'Invalid response from server' };
        }

        console.log('Login response data:', data);
        
        // Make sure the window still exists before sending a response
        if (!window.isDestroyed()) {
          event.sender.send('loginResponse', {
            success: response.ok,
            message: data?.message || 'Login successful',
            role: data?.role
          });
          
          console.log('Login response sent to renderer');
        } else {
          console.log('Window destroyed, not sending response');
        }
      } catch (fetchError: any) {
        clearTimeout(timeout);
        
        if (fetchError.name === 'AbortError') {
          console.error('Login request timed out');
          
          if (!window.isDestroyed()) {
            event.sender.send('loginResponse', {
              success: false,
              message: 'Server request timed out'
            });
          }
        } else {
          throw fetchError; // Re-throw to be handled by the outer catch
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      
      try {
        event.sender.send('loginResponse', {
          success: false,
          message: 'Network or server error'
        });
      } catch (sendError) {
        console.error('Failed to send error response:', sendError);
      }
    }
  };

  // Register the handlers for all current and future windows
  BrowserWindow.getAllWindows().forEach(window => {
    registerWindowHandler(window, 'registerUser', registerUserHandler);
    registerWindowHandler(window, 'loginUser', loginUserHandler);
  });
  
  // Also set up handlers for new windows
  app.on('browser-window-created', (_, window) => {
    registerWindowHandler(window, 'registerUser', registerUserHandler);
    registerWindowHandler(window, 'loginUser', loginUserHandler);
  });
}

// Set up invoke handlers for Promise-based IPC
function setupInvokeHandlers() {
  // Keep track of all registered handlers
  const handlers = new Set<string>();
  
  // Registration handler using invoke
  ipcMain.handle('register', async (_event, userData) => {
    try {
      console.log('Registration invoke received:', userData);
      
      if (!userData.username || !userData.password || !userData.role) {
        console.log('Invalid registration data');
        return {
          success: false,
          message: 'Missing required fields'
        };
      }
      
      console.log('Sending registration request to backend');
      
      // Set a timeout for the fetch operation
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      
      try {
        const response = await fetch('http://localhost:3001/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
          signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        console.log('Registration response status:', response.status);
        
        // Handle potential JSON parsing errors
        let data;
        const textResponse = await response.text();
        try {
          data = JSON.parse(textResponse);
        } catch (parseError) {
          console.error('Failed to parse JSON response:', textResponse);
          return { 
            success: false,
            message: 'Invalid response from server'
          };
        }
        
        console.log('Registration response data:', data);
        
        return {
          success: response.ok,
          message: data?.message || 'Registration completed',
          data
        };
      } catch (error) {
        clearTimeout(timeout);
        console.error('Fetch error during registration:', error);
        
        const fetchError = error as { name?: string };
        if (fetchError.name === 'AbortError') {
          return {
            success: false,
            message: 'Request timed out'
          };
        }
        
        return {
          success: false,
          message: 'Network or server error'
        };
      }
    } catch (error) {
      console.error('Registration invoke error:', error);
      return {
        success: false,
        message: 'Error processing registration'
      };
    }
  });
  
  // Login handler using invoke
  ipcMain.handle('login', async (_event, userData) => {
    try {
      console.log('Login invoke received:', userData);
      
      if (!userData.username || !userData.password) {
        console.log('Invalid login data');
        return {
          success: false,
          message: 'Username and password are required'
        };
      }
      
      console.log('Sending login request to backend');
      
      // Set a timeout for the fetch operation
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      
      try {
        const response = await fetch('http://localhost:3001/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
          signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        console.log('Login response status:', response.status);
        
        // Handle potential JSON parsing errors
        let data;
        const textResponse = await response.text();
        console.log('Raw login response:', textResponse);
        
        try {
          data = JSON.parse(textResponse);
        } catch (parseError) {
          console.error('Failed to parse JSON response:', textResponse);
          return { 
            success: false,
            message: 'Invalid response from server'
          };
        }
        
        console.log('Login response data:', data);
        
        return {
          success: response.ok,
          message: data?.message || 'Login completed',
          role: data?.role || '',
          data
        };
      } catch (error) {
        clearTimeout(timeout);
        console.error('Fetch error during login:', error);
        
        const fetchError = error as { name?: string };
        if (fetchError.name === 'AbortError') {
          return {
            success: false,
            message: 'Request timed out'
          };
        }
        
        return {
          success: false,
          message: 'Network or server error'
        };
      }
    } catch (error) {
      console.error('Login invoke error:', error);
      return {
        success: false,
        message: 'Error processing login'
      };
    }
  });
  
  // Add to tracking
  handlers.add('register');
  handlers.add('login');
  
  // Return a cleanup function
  return () => {
    // Remove all handlers on cleanup
    handlers.forEach(channel => {
      try {
        console.log(`Removing IPC handler for ${channel}`);
        ipcMain.removeHandler(channel);
      } catch (e) {
        console.error(`Error removing handler for ${channel}:`, e);
      }
    });
  };
}

// App lifecycle events
app.whenReady().then(() => {
  // Set up exception handling
  process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
    // You might want to show a dialog to the user here
  });

  // Keep track of cleanup functions
  const cleanupFunctions: (() => void)[] = [];

  createMainWindow();
  setupIPC();
  
  // Set up invoke handlers and get cleanup function
  const cleanupInvokeHandlers = setupInvokeHandlers();
  cleanupFunctions.push(cleanupInvokeHandlers);

  app.on('activate', () => {
    // On macOS it's common to re-create a window when the dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
  
  // Proper cleanup before app quits
  app.on('before-quit', () => {
    console.log('App is quitting, performing final cleanup');
    cleanupFunctions.forEach(cleanup => {
      try {
        cleanup();
      } catch (e) {
        console.error('Cleanup error:', e);
      }
    });
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Global cleanup when the app is about to quit
app.on('before-quit', () => {
  console.log('App is quitting, performing final cleanup');
  // Clean up all remaining IPC handlers
  ipcMain.removeAllListeners();
});
