// src/hn/post-weekly-comment.js
// Runs at 15:30 every Friday (via cron).
// Reads the pending top-1 app saved by the orchestrator, generates a natural
// HN comment with the LLM, and posts it to the item thread.

import { readFileSync, unlinkSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { postHNComment } from './poster.js';
import { llmCall } from '../llm/index.js';
import { log } from '../utils/logger.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const PENDING_FILE = join(__dir, '../../data/pending-hn-comment.json');

async function generateComment(app) {
  const prompt = `Write a SHORT Hacker News comment (2–3 sentences) announcing that this project ranked #1 in the weekly LLM Daily Review top-5 on tokenstree.eu.

Project: ${app.app_name}
Why it ranked #1 this week: ${app.why_top5}
Standout criterion: ${app.standout_criterion}
Score: ${app.total_score}/100

Rules:
- Mention it ranked #1 in the weekly top-5 at tokenstree.eu this week
- Reference ONE specific reason from "why it ranked #1"
- Include the portal URL: https://tokenstree.eu
- Sound natural, not promotional
- Do NOT use hashtags or generic praise
- Plain text only, no markdown
- Maximum 3 sentences`;

  return llmCall(
    'You write brief, genuine Hacker News comments announcing weekly rankings.',
    prompt,
    256
  );
}

async function main() {
  let pending;
  try {
    pending = JSON.parse(readFileSync(PENDING_FILE, 'utf8'));
  } catch {
    log.warn('No pending HN comment file found — nothing to post.');
    process.exit(0);
  }

  log.info(`Posting HN comment for: ${pending.app_name} → ${pending.hn_url}`);

  const commentText = await generateComment(pending);
  log.info(`Generated comment: ${commentText}`);

  await postHNComment(pending.hn_url, commentText);

  // Clean up so we don't accidentally re-post
  unlinkSync(PENDING_FILE);
  log.info('Done. Pending file removed.');
}

main().catch(err => {
  log.error(`HN comment post failed: ${err.message}`);
  process.exit(1);
});
