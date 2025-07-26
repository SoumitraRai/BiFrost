import express from 'express';
import {
  recordStats,
  getUserDailyStats,
  getUserMonthlyStats
} from './statsController';

const router = express.Router();

// Stats routes
router.post('/record', recordStats);
router.get('/daily/:userId', getUserDailyStats);
router.get('/monthly/:userId', getUserMonthlyStats);

export default router;
