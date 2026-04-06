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

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.3-70b-versatile';

// Criterion weights from the skill definition
const WEIGHTS = {
  novelty: 1.4,
  current_relevance: 1.3,
  differentiation: 1.3,
  ease_of_use: 1.0,
  ease_of_integration: 1.0,
  community: 0.8,
  system_requirements: 0.7,
};

export async function runWeeklyTop5() {
  // Determine Monday–Friday window of current week
  const now = new Date();
  const friday = new Date(now);
  const monday = new Date(now);
  monday.setDate(now.getDate() - now.getDay() + 1);
  monday.setHours(0, 0, 0, 0);
  friday.setHours(23, 59, 59, 999);

  const weekStart = monday.toISOString();
  const weekEnd = friday.toISOString();
  const weekLabel = getISOWeek(monday);

  log.info(`Weekly Top 5: pulling apps from ${weekStart} to ${weekEnd}`);

  const allApps = getWeekApps(weekStart, weekEnd);
  log.info(`Week total: ${allApps.length} apps`);

  // Step 1: Eligibility filter
  const eligible = allApps.filter(app => {
    if (app.recommendation === 'skip') return false;
    const scores = app.scores || {};
    if ((scores.ease_of_use?.score ?? 0) < 4) return false;
    if ((app.total_score ?? 0) < 35) return false;
    return true;
  });

  // Step 2: Weighted ranking
  const ranked = eligible.map(app => {
    const scores = app.scores || {};
    const weighted = Object.entries(WEIGHTS).reduce((sum, [key, weight]) => {
      return sum + (scores[key]?.score ?? 0) * weight;
    }, 0);
    return { ...app, weighted_total: weighted };
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
    .filter(a => (a.total_score ?? 0) >= 45)
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

  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 2048,
      messages: [
        {
          role: 'system',
          content: 'You are the editor of a weekly LLM tools digest. Write concise, concrete, non-hype justifications. Return ONLY valid JSON, no markdown fences.'
        },
        { role: 'user', content: prompt }
      ],
    }),
  });

  if (!res.ok) throw new Error(`Groq API error in top5 enrichment: ${res.status} ${await res.text()}`);
  const data = await res.json();
  const text = data.choices[0].message.content.trim().replace(/^```json\n?|```$/g, '');
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
