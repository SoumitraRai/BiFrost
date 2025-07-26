import mysql from 'mysql2/promise';

export const db = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'sr',
  password: process.env.DB_PASSWORD || 'sr',
  database: process.env.DB_NAME || 'bifrost_db',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});