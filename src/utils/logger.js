// src/utils/logger.js
// Minimal structured logger. Writes to stdout and to data/cron.log.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dir = path.dirname(fileURLToPath(import.meta.url));
const LOG_FILE = path.join(__dir, '../../data/run.log');

function write(level, msg) {
  const line = `[${new Date().toISOString()}] [${level}] ${msg}`;
  console[level === 'ERROR' ? 'error' : 'log'](line);
  try {
    fs.appendFileSync(LOG_FILE, line + '\n');
  } catch { /* non-fatal */ }
}

export const log = {
  info: msg => write('INFO', msg),
  warn: msg => write('WARN', msg),
  error: msg => write('ERROR', msg),
};
