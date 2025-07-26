import { db } from './connection';
import { ResultSetHeader, RowDataPacket } from 'mysql2';

export interface DailyStats {
  id?: number;
  user_id: number;
  date: string; // YYYY-MM-DD format
  requests_count: number;
  blocked_payments_count: number;
  approved_payments_count: number;
  data_transferred: number; // in bytes
}

export async function updateDailyStats(stats: Partial<DailyStats> & { user_id: number }): Promise<void> {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  
  // Prepare the increments with sensible defaults
  const requestsIncrement = stats.requests_count || 0;
  const blockedPaymentsIncrement = stats.blocked_payments_count || 0;
  const approvedPaymentsIncrement = stats.approved_payments_count || 0;
  const dataTransferredIncrement = stats.data_transferred || 0;
  
  await db.query(
    `INSERT INTO stats 
      (user_id, date, requests_count, blocked_payments_count, approved_payments_count, data_transferred) 
     VALUES (?, ?, ?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE 
      requests_count = requests_count + VALUES(requests_count),
      blocked_payments_count = blocked_payments_count + VALUES(blocked_payments_count),
      approved_payments_count = approved_payments_count + VALUES(approved_payments_count),
      data_transferred = data_transferred + VALUES(data_transferred)`,
    [
      stats.user_id,
      stats.date || today,
      requestsIncrement,
      blockedPaymentsIncrement,
      approvedPaymentsIncrement,
      dataTransferredIncrement
    ]
  );
}

export async function getDailyStats(userId: number, days: number = 7): Promise<DailyStats[]> {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT * FROM stats 
     WHERE user_id = ? AND date >= DATE_SUB(CURRENT_DATE, INTERVAL ? DAY) 
     ORDER BY date ASC`,
    [userId, days]
  );
  return rows as DailyStats[];
}

export async function getMonthlyStats(userId: number): Promise<DailyStats[]> {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT 
       DATE_FORMAT(date, '%Y-%m-01') as date,
       SUM(requests_count) as requests_count,
       SUM(blocked_payments_count) as blocked_payments_count,
       SUM(approved_payments_count) as approved_payments_count,
       SUM(data_transferred) as data_transferred
     FROM stats 
     WHERE user_id = ? AND date >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH) 
     GROUP BY DATE_FORMAT(date, '%Y-%m-01')
     ORDER BY date ASC`,
    [userId]
  );
  return rows as DailyStats[];
}
