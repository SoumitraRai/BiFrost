CREATE DATABASE IF NOT EXISTS bifrost_db;
USE bifrost_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role ENUM('Admin', 'Client') NOT NULL,
  email VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proxy_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  end_time TIMESTAMP NULL,
  ip_address VARCHAR(45),
  status ENUM('Active', 'Ended', 'Failed') NOT NULL DEFAULT 'Active',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS proxy_settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  enable_payment_filter BOOLEAN DEFAULT TRUE,
  auto_approval BOOLEAN DEFAULT FALSE,
  brave_certificate_installed BOOLEAN DEFAULT FALSE,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS traffic_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_id INT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  url VARCHAR(2048),
  method VARCHAR(10),
  status_code INT,
  content_type VARCHAR(100),
  size INT,
  is_payment_related BOOLEAN DEFAULT FALSE,
  is_approved BOOLEAN,
  FOREIGN KEY (session_id) REFERENCES proxy_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  date DATE NOT NULL,
  requests_count INT DEFAULT 0,
  blocked_payments_count INT DEFAULT 0,
  approved_payments_count INT DEFAULT 0,
  data_transferred BIGINT DEFAULT 0, -- in bytes
  UNIQUE KEY (user_id, date),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);