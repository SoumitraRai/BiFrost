import { Request, Response } from 'express';
import { findUserByUsername, createUser, findUserByCredentials } from './userModel';

export async function registerUser(req: Request, res: Response) {
  const { username, password, role } = req.body;
  if (!username || !password || !role) {
    return res.status(400).json({ message: 'All fields are required.' });
  }
  const user = await findUserByUsername(username);
  if (user) {
    return res.status(400).json({ message: 'Username already exists.' });
  }
  await createUser(username, password, role);
  res.json({ message: 'Registered successfully.' });
}

export async function loginUser(req: Request, res: Response) {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: 'Username and password are required.' });
  }
  const user = await findUserByCredentials(username, password);
  if (!user) {
    return res.status(401).json({ message: 'Invalid username or password.' });
  }
  res.json({ message: 'Login successful.', role: user.role });
}