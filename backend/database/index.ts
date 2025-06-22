import express from 'express';
import cors from 'cors';
import userRoutes from './userRoutes';
import 'dotenv/config';

const app = express();
app.use(cors());
app.use(express.json());
app.use('/api', userRoutes); 

app.listen(3001, () => {
  console.log('Server running on port 3001');
});