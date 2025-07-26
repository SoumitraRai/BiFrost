import express from 'express';
import {
  startSession,
  stopSession,
  getActiveSessions,
  getSettings,
  updateSettings,
  getTrafficLogs,
  getPaymentLogs
} from './proxyController';

const router = express.Router();

// Session routes
router.post('/sessions/start', startSession);
router.post('/sessions/:sessionId/stop', stopSession);
router.get('/sessions/user/:userId', getActiveSessions);

// Settings routes
router.get('/settings/user/:userId', getSettings);
router.put('/settings/user/:userId', updateSettings);

// Traffic log routes
router.get('/logs/session/:sessionId', getTrafficLogs);
router.get('/logs/payments/user/:userId', getPaymentLogs);

export default router;
