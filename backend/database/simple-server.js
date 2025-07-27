const express = require('express');
const cors = require('cors');
const mysql = require('mysql2');

// Create a simple express server
const app = express();
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json());

// Create a direct database connection
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'admin',
  database: 'bifrost_db'
});

// Connect to database
connection.connect(err => {
  if (err) {
    console.error('Failed to connect to MySQL:', err);
    return;
  }
  console.log('Connected to MySQL database');
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK' });
});

// Register endpoint
app.post('/api/auth/register', (req, res) => {
  console.log('Registration request received:', req.body);
  const { username, password, role } = req.body;
  
  if (!username || !password || !role) {
    return res.status(400).json({ message: 'All fields are required.' });
  }
  
  // Check if user exists
  connection.query(
    'SELECT * FROM users WHERE username = ?',
    [username],
    (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ message: 'Database error.' });
      }
      
      if (results.length > 0) {
        return res.status(400).json({ message: 'Username already exists.' });
      }
      
      // Create new user
      connection.query(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        [username, password, role],
        (err) => {
          if (err) {
            console.error('Insert error:', err);
            return res.status(500).json({ message: 'Failed to register user.' });
          }
          
          console.log('User registered successfully');
          res.json({ message: 'Registered successfully.' });
        }
      );
    }
  );
});

// Login endpoint
app.post('/api/auth/login', (req, res) => {
  console.log('Login request received:', req.body);
  const { username, password } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ message: 'Username and password are required.' });
  }
  
  connection.query(
    'SELECT * FROM users WHERE username = ? AND password = ?',
    [username, password],
    (err, results) => {
      if (err) {
        console.error('Login error:', err);
        return res.status(500).json({ message: 'Database error.' });
      }
      
      if (results.length === 0) {
        return res.status(401).json({ message: 'Invalid username or password.' });
      }
      
      console.log('User logged in successfully');
      res.json({ message: 'Login successful.', role: results[0].role });
    }
  );
});

// Start the server
const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Simple server running on port ${PORT}`);
});
