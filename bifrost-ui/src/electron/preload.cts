const { contextBridge, ipcRenderer } = require('electron');

// Define types for TypeScript
type ValidSendChannel = 'toMain' | 'registerUser' | 'loginUser' | 'logoutUser';
type ValidReceiveChannel = 'fromMain' | 'registrationResponse' | 'loginResponse';
type ValidInvokeChannel = 'getStaticData' | 'checkAuth' | 'register' | 'login';

// Track listener information by channel and an ID for each specific listener
// This allows multiple components to safely register for the same channel
interface ListenerInfo {
  id: number;
  handler: (event: Electron.IpcRendererEvent, ...args: unknown[]) => void;
  wrappedHandler: (event: Electron.IpcRendererEvent, ...args: unknown[]) => void;
}

// Global tracking variables
let nextListenerId = 1;
const channelListeners: Record<string, ListenerInfo[]> = {};

// Debug console functions with prefix for easier filtering
function logDebug(message: string, ...args: any[]) {
  console.log(`[IPC-DEBUG] ${message}`, ...args);
}

function logError(message: string, ...args: any[]) {
  console.error(`[IPC-ERROR] ${message}`, ...args);
}

/**
 * Safe version of removeListener that won't throw if the handler doesn't exist
 */
function safeRemoveListener(channel: string, handler: (...args: any[]) => void) {
  try {
    ipcRenderer.removeListener(channel, handler);
  } catch (error) {
    logError(`Error removing listener for ${channel}:`, error);
  }
}

/**
 * Clean up all listeners for a channel
 */
function removeAllChannelListeners(channel: string) {
  if (channelListeners[channel]) {
    logDebug(`Removing all listeners for channel ${channel}`);
    channelListeners[channel].forEach(info => {
      safeRemoveListener(channel, info.wrappedHandler);
    });
    delete channelListeners[channel];
  }
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', 
  {
    // Send from renderer to main
    send: (channel: ValidSendChannel, data: unknown) => {
      // whitelist channels
      const validChannels: ValidSendChannel[] = ['toMain', 'registerUser', 'loginUser', 'logoutUser'];
      if (validChannels.includes(channel)) {
        try {
          logDebug(`Sending on channel ${channel}:`, data);
          ipcRenderer.send(channel, data);
        } catch (error) {
          logError(`Error sending on channel ${channel}:`, error);
        }
      } else {
        logError(`Invalid send channel: ${channel}`);
      }
    },
    
    // Receive from main process - returns an ID that can be used to remove this specific listener
    receive: (channel: ValidReceiveChannel, func: (...args: unknown[]) => void): number => {
      const validChannels: ValidReceiveChannel[] = ['fromMain', 'registrationResponse', 'loginResponse'];
      if (validChannels.includes(channel)) {
        try {
          logDebug(`Setting up listener for channel: ${channel}`);
          
          // Create a unique ID for this listener
          const listenerId = nextListenerId++;
          
          // Create the wrapper that will call the user's function
          const wrappedHandler = (event: Electron.IpcRendererEvent, ...args: unknown[]) => {
            logDebug(`Event received on channel ${channel}, listener #${listenerId}`);
            try {
              func(...args);
            } catch (error) {
              logError(`Error in listener callback for ${channel}:`, error);
            }
          };
          
          // Initialize the channel listener array if needed
          if (!channelListeners[channel]) {
            channelListeners[channel] = [];
          }
          
          // Add this listener to our tracking
          channelListeners[channel].push({
            id: listenerId,
            handler: func,
            wrappedHandler
          });
          
          // Register the actual listener with Electron
          ipcRenderer.on(channel, wrappedHandler);
          
          logDebug(`Listener #${listenerId} registered for ${channel}. Total listeners: ${ipcRenderer.listenerCount(channel)}`);
          
          // Return the ID so the caller can remove this specific listener later
          return listenerId;
          
        } catch (error) {
          logError(`Error setting up listener for ${channel}:`, error);
          return -1;
        }
      } else {
        logError(`Invalid receive channel: ${channel}`);
        return -1;
      }
    },
    
    // Remove a specific listener by its ID
    removeListener: (channel: string, listenerId: number) => {
      logDebug(`Attempting to remove listener #${listenerId} from ${channel}`);
      
      if (!channelListeners[channel]) {
        logDebug(`No listeners registered for ${channel}`);
        return false;
      }
      
      // Find the listener with this ID
      const index = channelListeners[channel].findIndex(info => info.id === listenerId);
      
      if (index === -1) {
        logDebug(`Listener #${listenerId} not found for ${channel}`);
        return false;
      }
      
      // Get the handler function
      const { wrappedHandler } = channelListeners[channel][index];
      
      // Remove from our tracking
      channelListeners[channel].splice(index, 1);
      
      // If this was the last listener for this channel, clean up the channel
      if (channelListeners[channel].length === 0) {
        delete channelListeners[channel];
      }
      
      // Remove from Electron
      safeRemoveListener(channel, wrappedHandler);
      
      logDebug(`Removed listener #${listenerId} from ${channel}. Remaining listeners: ${ipcRenderer.listenerCount(channel)}`);
      return true;
    },
    
    // Legacy cleanup method for backward compatibility
    cleanup: (channel: string) => {
      logDebug(`Legacy cleanup for channel: ${channel}`);
      removeAllChannelListeners(channel);
    },
    
    // Invoke methods that return values
    invoke: (channel: ValidInvokeChannel, data?: unknown) => {
      const validChannels: ValidInvokeChannel[] = ['getStaticData', 'checkAuth', 'register', 'login'];
      if (validChannels.includes(channel)) {
        try {
          return ipcRenderer.invoke(channel, data);
        } catch (error) {
          console.error(`Error invoking ${channel}:`, error);
          return Promise.reject(error);
        }
      }
      console.warn(`Invalid invoke channel: ${channel}`);
      return Promise.reject(new Error(`Invalid channel: ${channel}`));
    },
    
    // Special direct methods for common operations
    invokeRegister: async (userData: { username: string; password: string; role: string }) => {
      try {
        logDebug('Invoking registration directly', userData);
        const result = await ipcRenderer.invoke('register', userData);
        logDebug('Registration result:', result);
        return result;
      } catch (err) {
        logError('Registration error:', err);
        return { success: false, message: 'Registration failed due to an error' };
      }
    },
    
    // Direct login method
    invokeLogin: async (userData: { username: string; password: string }) => {
      try {
        logDebug('Invoking login directly', userData);
        const result = await ipcRenderer.invoke('login', userData);
        logDebug('Login result:', result);
        return result;
      } catch (err) {
        logError('Login error:', err);
        return { success: false, message: 'Login failed due to an error' };
      }
    }
  }
);

// Make sure to clean up all listeners when the window unloads
window.addEventListener('unload', () => {
  logDebug('Window unloading, removing all IPC listeners');
  
  // Get all channels
  const channels = Object.keys(channelListeners);
  
  // Clean up each channel
  channels.forEach(removeAllChannelListeners);
  
  // Double-check with removeAllListeners for extra safety
  try {
    // This removes all listeners for all channels
    Object.keys(channelListeners).forEach(channel => {
      ipcRenderer.removeAllListeners(channel);
    });
  } catch (error) {
    logError('Error during final cleanup:', error);
  }
});
