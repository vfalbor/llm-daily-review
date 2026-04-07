// src/orchestrator/run.js
// Entry point. Called by cron at 15:00 daily.
// Coordinates all skills in sequence.

import { scrapeHN } from '../scraper/hn.js';
import { filterLLMApps } from '../filter/llm-filter.js';
import { checkDedup, markTested } from '../db/database.js';
import { runInContainer } from '../tester/container-runner.js';
import { scoreApp } from '../scorer/scorer.js';
import { generateDailyReport } from '../reporter/daily-report.js';
import { sendNewsletter } from '../email/mailer.js';
import { runWeeklyTop5 } from '../scorer/weekly-top5.js';
import { uploadToGitHub, uploadScores } from '../github/uploader.js';
import { log } from '../utils/logger.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dir = path.dirname(fileURLToPath(import.meta.url));
const LOCK_FILE = path.join(__dir, '../../data/run.lock');

function acquireLock() {
  if (fs.existsSync(LOCK_FILE)) {
    const pid = fs.readFileSync(LOCK_FILE, 'utf8').trim();
    // Check if that process is still alive
    try { process.kill(parseInt(pid), 0); return false; } catch { /* stale lock */ }
  }
  fs.writeFileSync(LOCK_FILE, String(process.pid));
  return true;
}

function releaseLock() {
  try { fs.unlinkSync(LOCK_FILE); } catch {}
}

async function main() {
  if (!acquireLock()) {
    log.warn('Another run is already in progress — aborting to avoid duplicate sends');
    process.exit(0);
  }
  process.on('exit', releaseLock);
  process.on('SIGINT', () => { releaseLock(); process.exit(1); });
  process.on('SIGTERM', () => { releaseLock(); process.exit(1); });

  const runDate = new Date().toISOString().split('T')[0];
  const dayOfWeek = new Date().getDay(); // 5 = Friday

  log.info(`=== LLM Daily Review — ${runDate} ===`);

  // Step 1: Scrape HN
  log.info('Scraping Hacker News...');
  const items = await scrapeHN({ max_items: 30 });
  log.info(`Fetched ${items.length} items`);

  // Step 2: Filter LLM-related apps
  log.info('Identifying LLM-related apps...');
  const candidates = await filterLLMApps(items);
  log.info(`Found ${candidates.length} LLM-related candidates`);

  // Step 3: Dedup — skip already-tested apps
  const newApps = await checkDedup(candidates);
  log.info(`${newApps.length} new apps to test (${candidates.length - newApps.length} skipped — already tested)`);

  const dailyResults = [];

  // Step 4: Test + score each app
  for (const app of newApps) {
    log.info(`Testing: ${app.title}`);
    try {
      // Run in isolated Docker container
      const testResults = await runInContainer(app);

      // Upload container logs + test script to GitHub
      await uploadToGitHub(app, testResults);

      // Score the app
      const scored = await scoreApp(app, testResults);

      // Upload scores.json to GitHub
      await uploadScores(app, scored, runDate);

      // Save to DB
      scored.title = app.title;  // preserve original HN title for GitHub slug
      await markTested(app, scored);
      dailyResults.push(scored);

      log.info(`  Scored: ${scored.total_score}/100 — ${scored.recommendation} (tests: ${testResults.tests_passed}/${testResults.tests_total} passed)`);
    } catch (err) {
      log.error(`  Failed to test ${app.title}: ${err.message}`);
    }
  }

  // Step 5: Generate daily report
  const skippedCount = candidates.length - newApps.length;
  log.info('Generating daily report...');
  const report = await generateDailyReport(runDate, dailyResults, { skipped: skippedCount });

  // Step 6: Send daily newsletter
  log.info('Sending daily newsletter...');
  await sendNewsletter({ edition: 'daily', date: runDate, apps_tested: dailyResults });

  // Step 7: If Friday, run weekly Top 5
  if (dayOfWeek === 5) {
    log.info('Friday — generating weekly Top 5...');
    const top5 = await runWeeklyTop5();
    await sendNewsletter({ edition: 'weekly', ...top5 });
  }

  log.info(`=== Run complete. Tested: ${dailyResults.length} apps ===`);
}

main().catch(err => {
  console.error('Orchestrator fatal error:', err);
  process.exit(1);
});
