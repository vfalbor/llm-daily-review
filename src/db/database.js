// src/db/database.js
// SQLite-based persistence: dedup, scores, subscribers.

import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __dir = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dir, '../../data/review.db');

let db;

function getDb() {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    migrate(db);
  }
  return db;
}

function migrate(db) {
  // Add hn_points/hn_comments to existing DBs that predate this migration
  for (const col of ['hn_points INTEGER DEFAULT 0', 'hn_comments INTEGER DEFAULT 0']) {
    try { db.exec(`ALTER TABLE tested_apps ADD COLUMN ${col}`); } catch {}
  }

  db.exec(`
    CREATE TABLE IF NOT EXISTS tested_apps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      url TEXT UNIQUE NOT NULL,
      title TEXT NOT NULL,
      tested_at TEXT NOT NULL,
      total_score INTEGER,
      recommendation TEXT,
      scores_json TEXT,
      report_json TEXT,
      hn_points INTEGER DEFAULT 0,
      hn_comments INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS subscribers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      edition TEXT NOT NULL CHECK(edition IN ('daily','weekly','both')),
      token TEXT UNIQUE NOT NULL,
      confirmed INTEGER DEFAULT 0,
      subscribed_at TEXT NOT NULL,
      unsubscribed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS daily_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_date TEXT UNIQUE NOT NULL,
      apps_found INTEGER,
      apps_tested INTEGER,
      apps_skipped INTEGER,
      report_md TEXT,
      created_at TEXT NOT NULL
    );
  `);
}

// Returns items NOT already in the DB
export function checkDedup(candidates) {
  const db = getDb();
  const stmt = db.prepare('SELECT 1 FROM tested_apps WHERE url = ?');
  return candidates.filter(c => !stmt.get(c.url));
}

export function markTested(app, scored) {
  const db = getDb();
  db.prepare(`
    INSERT OR IGNORE INTO tested_apps
      (url, title, tested_at, total_score, recommendation, scores_json, report_json, hn_points, hn_comments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    app.url,
    app.title,
    new Date().toISOString(),
    scored.total_score,
    scored.recommendation,
    JSON.stringify(scored.scores),
    JSON.stringify(scored),
    app.points ?? 0,
    app.comments ?? 0
  );
}

export function getWeekApps(weekStart, weekEnd) {
  const db = getDb();
  return db.prepare(`
    SELECT * FROM tested_apps
    WHERE tested_at >= ? AND tested_at <= ?
    ORDER BY total_score DESC
  `).all(weekStart, weekEnd).map(row => ({
    ...row,
    scores: JSON.parse(row.scores_json),
    report: JSON.parse(row.report_json),
  }));
}

export function getDayApps(date) {
  const db = getDb();
  const start = `${date}T00:00:00Z`;
  const end = `${date}T23:59:59Z`;
  return db.prepare(`
    SELECT * FROM tested_apps WHERE tested_at >= ? AND tested_at <= ?
  `).all(start, end).map(row => ({
    ...row,
    scores: JSON.parse(row.scores_json),
    report: JSON.parse(row.report_json),
  }));
}

export function addSubscriber({ email, edition, token }) {
  const db = getDb();
  db.prepare(`
    INSERT OR IGNORE INTO subscribers (email, edition, token, confirmed, subscribed_at)
    VALUES (?, ?, ?, 1, ?)
  `).run(email, edition, token, new Date().toISOString());
}

export function getSubscriberToken(email) {
  const db = getDb();
  const row = db.prepare('SELECT token FROM subscribers WHERE email = ? AND unsubscribed_at IS NULL').get(email);
  return row?.token || null;
}

export function unsubscribe(token) {
  const db = getDb();
  db.prepare(`
    UPDATE subscribers SET unsubscribed_at = ? WHERE token = ?
  `).run(new Date().toISOString(), token);
}

export function getActiveSubscribers(edition) {
  const db = getDb();
  return db.prepare(`
    SELECT email FROM subscribers
    WHERE (edition = ? OR edition = 'both')
    AND confirmed = 1
    AND unsubscribed_at IS NULL
  `).all(edition).map(r => r.email);
}

export function saveDailyRun(date, stats, reportMd) {
  const db = getDb();
  db.prepare(`
    INSERT OR REPLACE INTO daily_runs
      (run_date, apps_found, apps_tested, apps_skipped, report_md, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(date, stats.found, stats.tested, stats.skipped, reportMd, new Date().toISOString());
}

export function getCalendarDays(year, month) {
  const db = getDb();
  return db.prepare(`
    SELECT run_date, apps_tested FROM daily_runs
    WHERE run_date LIKE ?
    ORDER BY run_date
  `).all(`${year}-${String(month).padStart(2, '0')}%`);
}
