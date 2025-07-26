import { Request, Response } from 'express';
import {
  createProxySession,
  endProxySession,
  getActiveSessionsByUserId,
  getProxySettingsByUserId,
  createOrUpdateProxySettings,
  getSessionTrafficLogs,
  getPaymentTrafficLogs,
  ProxySettings
} from './proxyModel';

// Session management
export async function startSession(req: Request, res: Response) {
  try {
    const { userId, ipAddress } = req.body;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const sessionId = await createProxySession({
      user_id: userId,
      ip_address: ipAddress,
      status: 'Active'
    });
    
    res.json({ 
      message: 'Proxy session started successfully.',
      sessionId 
    });
  } catch (error) {
    console.error('Failed to start proxy session:', error);
    res.status(500).json({ message: 'Failed to start proxy session.' });
  }
}

export async function stopSession(req: Request, res: Response) {
  try {
    const { sessionId } = req.params;
    
    if (!sessionId) {
      return res.status(400).json({ message: 'Session ID is required.' });
    }
    
    await endProxySession(parseInt(sessionId));
    res.json({ message: 'Proxy session ended successfully.' });
  } catch (error) {
    console.error('Failed to end proxy session:', error);
    res.status(500).json({ message: 'Failed to end proxy session.' });
  }
}

export async function getActiveSessions(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const sessions = await getActiveSessionsByUserId(parseInt(userId));
    res.json(sessions);
  } catch (error) {
    console.error('Failed to fetch active sessions:', error);
    res.status(500).json({ message: 'Failed to fetch active sessions.' });
  }
}

// Settings management
export async function getSettings(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const settings = await getProxySettingsByUserId(parseInt(userId));
    
    if (!settings) {
      // Return default settings if not found
      return res.json({
        user_id: parseInt(userId),
        enable_payment_filter: true,
        auto_approval: false,
        brave_certificate_installed: false
      });
    }
    
    res.json(settings);
  } catch (error) {
    console.error('Failed to fetch proxy settings:', error);
    res.status(500).json({ message: 'Failed to fetch proxy settings.' });
  }
}

export async function updateSettings(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    const { enablePaymentFilter, autoApproval, braveCertificateInstalled } = req.body;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const settings: ProxySettings = {
      user_id: parseInt(userId),
      enable_payment_filter: enablePaymentFilter !== undefined ? enablePaymentFilter : true,
      auto_approval: autoApproval !== undefined ? autoApproval : false,
      brave_certificate_installed: braveCertificateInstalled !== undefined ? braveCertificateInstalled : false
    };
    
    await createOrUpdateProxySettings(settings);
    res.json({ 
      message: 'Proxy settings updated successfully.',
      settings 
    });
  } catch (error) {
    console.error('Failed to update proxy settings:', error);
    res.status(500).json({ message: 'Failed to update proxy settings.' });
  }
}

// Traffic logs
export async function getTrafficLogs(req: Request, res: Response) {
  try {
    const { sessionId } = req.params;
    
    if (!sessionId) {
      return res.status(400).json({ message: 'Session ID is required.' });
    }
    
    const logs = await getSessionTrafficLogs(parseInt(sessionId));
    res.json(logs);
  } catch (error) {
    console.error('Failed to fetch traffic logs:', error);
    res.status(500).json({ message: 'Failed to fetch traffic logs.' });
  }
}

export async function getPaymentLogs(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 50;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const logs = await getPaymentTrafficLogs(parseInt(userId), limit);
    res.json(logs);
  } catch (error) {
    console.error('Failed to fetch payment logs:', error);
    res.status(500).json({ message: 'Failed to fetch payment logs.' });
  }
}
