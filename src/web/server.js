// src/web/server.js
// Express server: serves the web UI and JSON API.

import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';
import fs from 'fs';
import {
  getDayApps,
  getCalendarDays,
  addSubscriber,
  unsubscribe,
  getWeeklyTop5,
  getRecentApps,
} from '../db/database.js';

const __dir = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());

// SEO: Serve index.html with server-side injected recent results for Google crawling
const INDEX_HTML_PATH = path.join(__dir, 'index.html');
app.get('/', (req, res) => {
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  try {
    const html = fs.readFileSync(INDEX_HTML_PATH, 'utf-8');
    const apps = getRecentApps(30);

    const BADGE = { 'strong': '⭐ Strong candidate', 'worth-watching': '👀 Worth watching', 'niche': '🔍 Niche', 'skip': '⏭ Skip' };
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

    const rows = apps.map(a => {
      const d = (a.tested_at || '').slice(0, 10);
      const badge = BADGE[a.recommendation] || a.recommendation;
      return `<tr><td>${esc(d)}</td><td><a href="${esc(a.url)}" rel="noopener">${esc(a.title)}</a></td><td>${esc(a.total_score)}/100</td><td>${esc(badge)}</td></tr>`;
    }).join('\n');

    const seoBlock = `
<!-- SEO: pre-rendered recent results for search engine crawlers -->
<section id="seo-recent" aria-label="Recent LLM app reviews" style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;">
  <h2>Recent LLM App Reviews from Hacker News</h2>
  <p>Latest AI tool evaluations — tested daily in Docker containers and scored across 11 criteria.</p>
  <table>
    <thead><tr><th>Date</th><th>App</th><th>Score</th><th>Recommendation</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
</section>`;

    const patched = html.replace('</body>', seoBlock + '\n</body>');
    res.type('html').send(patched);
  } catch (_) {
    res.sendFile(INDEX_HTML_PATH);
  }
});

// Serve static UI — no-cache so browser always gets latest index.html
app.use(express.static(path.join(__dir), {
  etag: false,
  lastModified: false,
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    }
  },
}));

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

// API: weekly top 5 (latest or by week param e.g. ?week=2026-W15)
app.get('/api/weekly-top5', (req, res) => {
  const result = getWeeklyTop5(req.query.week || null);
  if (!result) return res.status(404).json({ error: 'No weekly top 5 found' });
  res.json(result);
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

// SEO: robots.txt
app.get('/robots.txt', (req, res) => {
  res.type('text/plain');
  res.send([
    'User-agent: *',
    'Allow: /',
    'Disallow: /api/',
    '',
    'Sitemap: https://tokenstree.eu/sitemap.xml',
    '',
    '# LLM-friendly context file',
    'LLMs-txt: https://tokenstree.eu/llms.txt',
  ].join('\n'));
});

// SEO: sitemap.xml — homepage + newsletter index + individual articles
app.get('/sitemap.xml', (req, res) => {
  const BASE = 'https://tokenstree.eu';
  const today = new Date().toISOString().split('T')[0];

  // Discover newsletter articles dynamically
  const newsletterDir = path.join(__dir, 'newsletter');
  let articleUrls = [];
  try {
    const files = fs.readdirSync(newsletterDir);
    articleUrls = files
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .map(f => `<url><loc>${BASE}/newsletter/${f}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>`);
  } catch (_) { /* newsletter dir may not exist */ }

  const urls = [
    `<url><loc>${BASE}/</loc><lastmod>${today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>`,
    `<url><loc>${BASE}/newsletter/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>`,
    ...articleUrls,
  ];

  res.type('application/xml');
  res.send(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>`);
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
