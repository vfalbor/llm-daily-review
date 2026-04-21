// src/scripts/resend-today.js
// Resends today's daily email with the latest template (including news digest).
// Usage: node --env-file=.env src/scripts/resend-today.js

import { getDayApps, saveDailyNews } from '../db/database.js';
import { scrapeHN } from '../scraper/hn.js';
import { summarizeNewsItems } from '../summarizer/hn-news-summary.js';
import { sendNewsletter } from '../email/mailer.js';
import { log } from '../utils/logger.js';

const runDate = new Date().toISOString().split('T')[0];

log.info(`Resending daily email for ${runDate}...`);

const apps = getDayApps(runDate);
log.info(`Loaded ${apps.length} apps from DB for ${runDate}`);

log.info('Scraping HN for news digest...');
const items = await scrapeHN({ max_items: 30 });
log.info(`Fetched ${items.length} HN items`);

log.info('Generating news summary via Groq...');
const newsSummary = await summarizeNewsItems(items, 6);
log.info(`News digest: ${newsSummary.length} items`);
newsSummary.forEach(n => log.info(`  [${n.points}pts] ${n.title}`));

saveDailyNews(runDate, newsSummary);
log.info('News saved to DB');

log.info('Sending newsletter...');
await sendNewsletter({
  edition: 'daily',
  date: runDate,
  apps_tested: apps,
  apps_skipped_dedup: 0,
  news_summary: newsSummary,
});

log.info('Done.');
