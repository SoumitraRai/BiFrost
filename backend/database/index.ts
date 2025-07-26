import express from 'express';
import cors from 'cors';
import userRoutes from './userRoutes';
import proxyRoutes from './proxyRoutes';
import statsRoutes from './statsRoutes';
import 'dotenv/config';

// Create Express app
const app = express();

// Configure CORS
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// Health check endpoint for easier debugging
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK' });
});

// Set up routes
app.use('/api/auth', userRoutes);
app.use('/api/proxy', proxyRoutes);
app.use('/api/stats', statsRoutes);

// Start the server
const server = app.listen(3001, () => {
  console.log('Server running on port 3001');
});

// Add error handling
server.on('error', (error: any) => {
  if (error.code === 'EADDRINUSE') {
    console.error('Port 3001 is already in use. Please free up the port and try again.');
  } else {
    console.error('Server error:', error);
  }
}); 