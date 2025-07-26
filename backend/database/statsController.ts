import { Request, Response } from 'express';
import { updateDailyStats, getDailyStats, getMonthlyStats } from './statsModel';

export async function recordStats(req: Request, res: Response) {
  try {
    const { 
      userId, 
      requestsCount,
      blockedPaymentsCount,
      approvedPaymentsCount,
      dataTransferred 
    } = req.body;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    await updateDailyStats({
      user_id: userId,
      requests_count: requestsCount || 0,
      blocked_payments_count: blockedPaymentsCount || 0,
      approved_payments_count: approvedPaymentsCount || 0,
      data_transferred: dataTransferred || 0
    });
    
    res.json({ message: 'Stats recorded successfully.' });
  } catch (error) {
    console.error('Failed to record stats:', error);
    res.status(500).json({ message: 'Failed to record stats.' });
  }
}

export async function getUserDailyStats(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    const days = req.query.days ? parseInt(req.query.days as string) : 7;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const stats = await getDailyStats(parseInt(userId), days);
    res.json(stats);
  } catch (error) {
    console.error('Failed to fetch user stats:', error);
    res.status(500).json({ message: 'Failed to fetch user stats.' });
  }
}

export async function getUserMonthlyStats(req: Request, res: Response) {
  try {
    const { userId } = req.params;
    
    if (!userId) {
      return res.status(400).json({ message: 'User ID is required.' });
    }
    
    const stats = await getMonthlyStats(parseInt(userId));
    res.json(stats);
  } catch (error) {
    console.error('Failed to fetch user monthly stats:', error);
    res.status(500).json({ message: 'Failed to fetch user monthly stats.' });
  }
}
