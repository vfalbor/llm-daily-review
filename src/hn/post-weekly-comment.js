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
  const prompt = `You are a developer who just discovered a useful open-source tool on Hacker News.
Write a SHORT comment (2–3 sentences) for the HN thread of this tool.

Tool: ${app.app_name}
Why it stands out this week: ${app.why_top5}
Standout criterion: ${app.standout_criterion}

Rules:
- Sound like a genuine developer, first-person ("I tried this", "been looking for", etc.)
- Reference ONE specific technical detail from the "why it stands out" text
- Do NOT use marketing language, hashtags, or generic praise like "great project"
- Do NOT mention rankings, newsletters, or automated systems
- Plain text only, no markdown
- Maximum 3 sentences`;

  return llmCall(
    'You are a developer writing a brief, genuine comment on Hacker News.',
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
