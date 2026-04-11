// src/scorer/weekly-top5.js
// Runs every Friday: pulls the week's scored apps from DB,
// applies the weighted ranking from the weekly-top5 skill, and returns top 5.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { getWeekApps } from '../db/database.js';
import { log } from '../utils/logger.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(
  join(__dir, '../../skills/weekly-top5/SKILL.md'), 'utf8'
);

import { llmCall } from '../llm/index.js';

// Criterion weights for 12-criteria scoring
// hn_sentiment: LLM-derived score (0–10) based on comment tone, sentiment, etc.
// hn_points: raw HN upvotes normalised to 0–10 against the week's maximum
const WEIGHTS = {
  hn_sentiment:        1.2,
  hn_points:           1.1,
  novelty:             1.4,
  current_relevance:   1.3,
  differentiation:     1.3,
  performance:         1.2,
  ease_of_use:         1.0,
  ease_of_integration: 1.0,
  documentation:       0.9,
  maturity:            0.9,
  community:           0.8,
  system_requirements: 0.7,
};

export async function runWeeklyTop5() {
  // Window: last 7 days ending now (covers Sat+Sun of previous week through Friday)
  const now = new Date();
  const weekEnd = new Date(now);
  weekEnd.setHours(23, 59, 59, 999);
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - 6);
  weekStart.setHours(0, 0, 0, 0);

  const weekLabel = getISOWeek(weekStart);

  log.info(`Weekly Top 5: pulling apps from ${weekStart} to ${weekEnd}`);

  const allApps = getWeekApps(weekStart, weekEnd);
  log.info(`Week total: ${allApps.length} apps`);

  // Step 1: Eligibility filter
  const eligible = allApps.filter(app => {
    if (app.recommendation === 'skip') return false;
    const scores = app.scores || {};
    if ((scores.ease_of_use?.score ?? 0) < 4) return false;
    if ((app.total_score ?? 0) < 50) return false; // 50/100 minimum
    return true;
  });

  // Step 2: Weighted ranking
  // Normalise raw HN points to 0–10 against the week's maximum
  const maxPoints = Math.max(1, ...eligible.map(a => a.hn_points ?? 0));
  const ranked = eligible.map(app => {
    const scores = app.scores || {};
    const hnPointsScore = ((app.hn_points ?? 0) / maxPoints) * 10;
    const weighted = Object.entries(WEIGHTS).reduce((sum, [key, weight]) => {
      const raw = key === 'hn_points' ? hnPointsScore : (scores[key]?.score ?? 0);
      return sum + raw * weight;
    }, 0);
    return { ...app, weighted_total: weighted, hn_points_score: hnPointsScore };
  }).sort((a, b) => b.weighted_total - a.weighted_total);

  // Step 3: Diversity bonus — penalise duplicate app types
  const seenTypes = {};
  const diversified = ranked.map((app, i) => {
    const type = app.app_type || 'unknown';
    if (seenTypes[type]) {
      return { ...app, weighted_total: app.weighted_total * 0.95 };
    }
    seenTypes[type] = true;
    return app;
  }).sort((a, b) => b.weighted_total - a.weighted_total);

  // Step 4: Top 5 + honorable mentions
  const top5 = diversified.slice(0, 5);
  const honorableMentions = diversified
    .slice(5, 8)
    .filter(a => (a.total_score ?? 0) >= 65)
    .map(a => a.title || a.app_name);

  // Step 5: Use Claude to write the justifications and week summary
  const enriched = await enrichWithJustifications(top5, honorableMentions, allApps, weekLabel);

  return {
    week: weekLabel,
    generated_at: new Date().toISOString(),
    top5: enriched.top5,
    honorable_mentions: honorableMentions,
    week_summary: enriched.week_summary,
    total_apps_tested_week: allApps.length,
  };
}

async function enrichWithJustifications(top5, mentions, allApps, weekLabel) {
  const prompt = `${SKILL_MD}

---

Write justifications and a week summary for the following Top 5 ranked apps.

TOP 5 (in order):
${top5.map((a, i) => `${i + 1}. ${a.title || a.app_name} — total:${a.total_score}, weighted:${a.weighted_total?.toFixed(1)}, type:${a.app_type}`).join('\n')}

ALL APPS TESTED THIS WEEK (${allApps.length} total):
${allApps.map(a => `- ${a.title || a.app_name} (${a.app_type}, score:${a.total_score})`).join('\n')}

HONORABLE MENTIONS: ${mentions.join(', ') || 'none'}

Return JSON with shape:
{
  "top5": [
    { "rank": 1, "app_name": "...", "why_top5": "...", "standout_criterion": "..." },
    ...
  ],
  "week_summary": "..."
}
Return ONLY valid JSON.`;

  const raw = await llmCall(
    'You are the editor of a weekly LLM tools digest. Write concise, concrete, non-hype justifications. Return ONLY valid JSON, no markdown fences.',
    prompt,
    2048
  );
  const text = raw.replace(/^```json\n?|```$/g, '');
  const enriched = JSON.parse(text);

  // Merge original score data back in
  enriched.top5 = enriched.top5.map((e, i) => ({
    ...top5[i],
    ...e,
    scores_snapshot: top5[i].scores,
  }));

  return enriched;
}

function getISOWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}
