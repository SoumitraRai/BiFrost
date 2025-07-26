import { db } from './connection';
import { ResultSetHeader, RowDataPacket } from 'mysql2';

export interface ProxySession {
  id?: number;
  user_id: number;
  start_time?: Date;
  end_time?: Date | null;
  ip_address?: string;
  status: 'Active' | 'Ended' | 'Failed';
}

export interface ProxySettings {
  id?: number;
  user_id: number;
  enable_payment_filter: boolean;
  auto_approval: boolean;
  brave_certificate_installed: boolean;
  last_updated?: Date;
}

export interface TrafficLog {
  id?: number;
  session_id: number;
  timestamp?: Date;
  url: string;
  method: string;
  status_code: number;
  content_type: string;
  size: number;
  is_payment_related: boolean;
  is_approved: boolean | null;
}

// Proxy Session methods
export async function createProxySession(session: ProxySession): Promise<number> {
  const [result] = await db.query<ResultSetHeader>(
    'INSERT INTO proxy_sessions (user_id, ip_address, status) VALUES (?, ?, ?)',
    [session.user_id, session.ip_address || null, session.status]
  );
  return result.insertId;
}

export async function endProxySession(sessionId: number): Promise<void> {
  await db.query(
    'UPDATE proxy_sessions SET end_time = CURRENT_TIMESTAMP, status = "Ended" WHERE id = ? AND status = "Active"',
    [sessionId]
  );
}

export async function getActiveSessionsByUserId(userId: number): Promise<ProxySession[]> {
  const [rows] = await db.query<RowDataPacket[]>(
    'SELECT * FROM proxy_sessions WHERE user_id = ? AND status = "Active"',
    [userId]
  );
  return rows as ProxySession[];
}

// Proxy Settings methods
export async function getProxySettingsByUserId(userId: number): Promise<ProxySettings | null> {
  const [rows] = await db.query<RowDataPacket[]>(
    'SELECT * FROM proxy_settings WHERE user_id = ?',
    [userId]
  );
  return rows.length > 0 ? rows[0] as ProxySettings : null;
}

export async function createOrUpdateProxySettings(settings: ProxySettings): Promise<void> {
  await db.query(
    `INSERT INTO proxy_settings 
      (user_id, enable_payment_filter, auto_approval, brave_certificate_installed) 
     VALUES (?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE 
      enable_payment_filter = VALUES(enable_payment_filter),
      auto_approval = VALUES(auto_approval),
      brave_certificate_installed = VALUES(brave_certificate_installed)`,
    [
      settings.user_id, 
      settings.enable_payment_filter, 
      settings.auto_approval, 
      settings.brave_certificate_installed
    ]
  );
}

// Traffic Log methods
export async function addTrafficLog(log: TrafficLog): Promise<number> {
  const [result] = await db.query<ResultSetHeader>(
    `INSERT INTO traffic_logs 
      (session_id, url, method, status_code, content_type, size, is_payment_related, is_approved) 
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      log.session_id,
      log.url,
      log.method,
      log.status_code,
      log.content_type,
      log.size,
      log.is_payment_related,
      log.is_approved
    ]
  );
  return result.insertId;
}

export async function getSessionTrafficLogs(sessionId: number): Promise<TrafficLog[]> {
  const [rows] = await db.query<RowDataPacket[]>(
    'SELECT * FROM traffic_logs WHERE session_id = ? ORDER BY timestamp DESC',
    [sessionId]
  );
  return rows as TrafficLog[];
}

export async function getPaymentTrafficLogs(userId: number, limit: number = 50): Promise<TrafficLog[]> {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT t.* FROM traffic_logs t
     JOIN proxy_sessions s ON t.session_id = s.id
     WHERE s.user_id = ? AND t.is_payment_related = TRUE
     ORDER BY t.timestamp DESC
     LIMIT ?`,
    [userId, limit]
  );
  return rows as TrafficLog[];
}
