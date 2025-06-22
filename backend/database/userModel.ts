import { db } from './connection';
import { RowDataPacket } from 'mysql2';

export async function findUserByUsername(username: string) {
  const [rows] = await db.query('SELECT * FROM users WHERE username = ?', [username]);
  return Array.isArray(rows) && rows.length > 0 ? rows[0] : null;
}

export async function createUser(username: string, password: string, role: string) {
  await db.query('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [username, password, role]);
}

export async function findUserByCredentials(username: string, password: string) {
  const [rows] = await db.query<RowDataPacket[]>(
    'SELECT * FROM users WHERE username = ? AND password = ?',
    [username, password]
  );
  return rows.length > 0 ? rows[0] as any : null;
}