// src/summarizer/hn-news-summary.js
// Takes raw HN items and generates a brief daily news digest.
// Filters out pure app/tool posts (those go to the app review section).
// Uses LLM to write a one-liner "why this matters" per item.

import { llmCall, GROQ_MODEL_FAST } from '../llm/index.js';
import { log } from '../utils/logger.js';

const SYSTEM_PROMPT = `You are a concise tech news analyst. Given a list of Hacker News items,
write a one-sentence summary (max 20 words) for each explaining why it matters to a developer or tech founder.
Be direct. No hype words. Focus on the practical implication or the interesting finding.
Return valid JSON only.`;

/**
 * Generate a ranked news digest from raw HN items.
 * Excludes items that look like pure tool/library launches (those are handled by the app reviewer).
 * @param {Array} items - raw scraped HN items with {title, url, hn_url, points, comments}
 * @param {number} maxItems - max news items to include (default 6)
 * @returns {Array} [{title, url, hn_url, points, comments, summary}]
 */
export async function summarizeNewsItems(items, maxItems = 6) {
  if (!items?.length) return [];

  // Sort by points descending, take top 15 candidates
  const sorted = [...items]
    .filter(i => i.title && i.url)
    .sort((a, b) => (b.points || 0) - (a.points || 0))
    .slice(0, 15);

  // Filter out obvious tool launches (Show HN: with a GitHub URL or similar)
  const newsItems = sorted.filter(item => {
    const t = item.title.toLowerCase();
    const isShowHN = t.startsWith('show hn:');
    const isAskHN = t.startsWith('ask hn:');
    const isGitHub = item.url.includes('github.com') || item.url.includes('gitlab.com');
    const isPkg = item.url.includes('pypi.org') || item.url.includes('npmjs.com') || item.url.includes('crates.io');
    // Keep Ask HN (discussion), keep non-tool Show HNs, exclude pure repo launches
    if (isShowHN && (isGitHub || isPkg)) return false;
    return true;
  }).slice(0, 10);

  if (!newsItems.length) return [];

  const prompt = `These are today's top Hacker News items by score. Write a one-sentence summary for each.

Items:
${newsItems.map((item, i) => `${i + 1}. [${item.points} pts] "${item.title}" — ${item.url}`).join('\n')}

Return JSON array:
[
  {"index": 1, "summary": "Why this matters in one sentence."},
  ...
]

Only include items worth reading. Skip if boring or clearly off-topic. Return up to ${maxItems} items.`;

  let summaries = [];
  try {
    const raw = await llmCall(SYSTEM_PROMPT, prompt, 1024, GROQ_MODEL_FAST);
    const match = raw.match(/\[[\s\S]*\]/);
    if (match) summaries = JSON.parse(match[0]);
  } catch (err) {
    log.warn(`News summary LLM failed: ${err.message} — falling back to top items without summaries`);
    return newsItems.slice(0, maxItems).map(item => ({ ...item, summary: '' }));
  }

  // Merge summaries back into items
  return summaries
    .slice(0, maxItems)
    .map(s => {
      const item = newsItems[s.index - 1];
      if (!item) return null;
      return { ...item, summary: s.summary || '' };
    })
    .filter(Boolean);
}
