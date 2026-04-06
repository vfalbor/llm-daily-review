// src/web/server.js
// Express server: serves the web UI and JSON API.

import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';
import {
  getDayApps,
  getCalendarDays,
  addSubscriber,
  unsubscribe,
} from '../db/database.js';

const __dir = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// Serve static UI
app.use(express.static(path.join(__dir)));

// API: calendar data for a month
app.get('/api/calendar', (req, res) => {
  const { year, month } = req.query;
  if (!year || !month) return res.status(400).json({ error: 'year and month required' });
  const data = getCalendarDays(parseInt(year), parseInt(month));
  res.json(data);
});

// API: results for a specific date
app.get('/api/results', (req, res) => {
  const { date } = req.query;
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return res.status(400).json({ error: 'date required (YYYY-MM-DD)' });
  }
  const apps = getDayApps(date);
  res.json(apps);
});

// API: subscribe to newsletter
app.post('/api/subscribe', (req, res) => {
  const { email, edition } = req.body;
  if (!email || !edition) return res.status(400).json({ error: 'email and edition required' });
  if (!['daily', 'weekly', 'both'].includes(edition)) {
    return res.status(400).json({ error: 'invalid edition' });
  }
  const token = crypto.randomBytes(20).toString('hex');
  try {
    addSubscriber({ email, edition, token });
    // TODO: send confirmation email
    res.json({ ok: true });
  } catch (err) {
    if (err.message.includes('UNIQUE')) {
      res.json({ ok: true, note: 'already subscribed' });
    } else {
      res.status(500).json({ error: 'subscription failed' });
    }
  }
});

// Unsubscribe
app.get('/unsubscribe', (req, res) => {
  const { token } = req.query;
  if (!token) return res.status(400).send('Invalid unsubscribe link');
  unsubscribe(token);
  res.send('<html><body style="font-family:sans-serif;padding:40px"><h2>Unsubscribed</h2><p>You have been removed from the mailing list.</p></body></html>');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`LLM Daily Review running on http://localhost:${PORT}`);
});

export default app;
