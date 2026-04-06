// src/enricher/hn-sentiment.js
// Fetches HN comments for a post and analyzes overall sentiment via LLM.
// Returns a structured sentiment score (1-10) with justification.

import { llmCall, GROQ_MODEL_FAST } from '../llm/index.js';
import { log } from '../utils/logger.js';

const ALGOLIA_HN_API = 'https://hn.algolia.com/api/v1/items';
const MAX_COMMENTS = 30;       // top-level + nested, capped for token budget
const MAX_COMMENT_CHARS = 300; // truncate each comment to keep prompt small

// ── Fetch comments from HN Algolia API ──────────────────────────────────────

function extractHNItemId(hnUrl) {
  if (!hnUrl) return null;
  const m = hnUrl.match(/item\?id=(\d+)/);
  return m ? m[1] : null;
}

function flattenComments(node, result = [], depth = 0) {
  if (!node.children) return result;
  for (const child of node.children) {
    if (child.text && result.length < MAX_COMMENTS) {
      // Strip HTML tags from comment text
      const clean = child.text
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, MAX_COMMENT_CHARS);
      if (clean.length > 10) {
        result.push({ text: clean, author: child.author || 'anon', depth });
      }
    }
    if (result.length < MAX_COMMENTS) {
      flattenComments(child, result, depth + 1);
    }
  }
  return result;
}

async function fetchHNComments(hnUrl) {
  const itemId = extractHNItemId(hnUrl);
  if (!itemId) return null;

  try {
    const res = await fetch(`${ALGOLIA_HN_API}/${itemId}`, {
      signal: AbortSignal.timeout(8000),
      headers: { 'User-Agent': 'HNReviewer/1.0' },
    });
    if (!res.ok) return null;
    const data = await res.json();

    const comments = flattenComments(data);
    return {
      total_comments: data.children?.length || 0,
      points: data.points || 0,
      fetched_comments: comments,
    };
  } catch (err) {
    log.warn(`Failed to fetch HN comments for ${hnUrl}: ${err.message}`);
    return null;
  }
}

// ── Sentiment analysis via LLM ──────────────────────────────────────────────

async function analyzeSentiment(app, commentData) {
  const commentBlock = commentData.fetched_comments
    .map((c, i) => `[${i + 1}] (${c.author}): ${c.text}`)
    .join('\n');

  const systemPrompt = `You are an expert at analyzing Hacker News comment sentiment for developer tools and projects.
Analyze the comments and return a JSON object with:
- score: integer 1-10 (1=very negative, 5=neutral/mixed, 10=overwhelmingly positive)
- positive_signals: array of 1-3 short strings summarizing positive themes
- negative_signals: array of 1-3 short strings summarizing negative themes
- justification: 1-2 sentence summary citing specific comment themes

Scoring guide:
- 1-2: Hostile reception, major concerns about security/ethics/quality
- 3-4: Mostly negative, significant skepticism or criticism
- 5: Mixed or neutral, balanced pros and cons
- 6-7: Generally positive with some constructive criticism
- 8-9: Very positive, excitement and praise with minor nitpicks
- 10: Universally acclaimed, no significant criticism

If there are very few comments (<3), lean toward 5 (neutral) with justification noting insufficient data.
Return ONLY valid JSON, no markdown fences.`;

  const userPrompt = `Analyze the HN comment sentiment for this project:

Title: ${app.title}
Type: ${app.app_type || 'unknown'}
HN Points: ${commentData.points}
Total comments: ${commentData.total_comments}
Fetched comments (${commentData.fetched_comments.length}):

${commentBlock}`;

  try {
    const raw = await llmCall(systemPrompt, userPrompt, 512, GROQ_MODEL_FAST);
    const parsed = JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
    // Clamp score to 1-10
    parsed.score = Math.max(1, Math.min(10, parsed.score || 5));
    return parsed;
  } catch (err) {
    log.warn(`Sentiment analysis failed for "${app.title}": ${err.message}`);
    return null;
  }
}

// ── Main entry ──────────────────────────────────────────────────────────────

export async function analyzeHNSentiment(app) {
  const hnUrl = app.hn_url;
  if (!hnUrl) {
    return { score: null, reason: 'no_hn_url' };
  }

  const commentData = await fetchHNComments(hnUrl);
  if (!commentData || commentData.fetched_comments.length === 0) {
    return { score: null, reason: 'no_comments' };
  }

  // Too few comments for meaningful analysis — return neutral with note
  if (commentData.fetched_comments.length < 3) {
    return {
      score: 5,
      positive_signals: [],
      negative_signals: [],
      justification: `Only ${commentData.fetched_comments.length} comment(s) found — insufficient for meaningful sentiment analysis, defaulting to neutral.`,
      comment_count: commentData.fetched_comments.length,
      hn_points: commentData.points,
    };
  }

  const sentiment = await analyzeSentiment(app, commentData);
  if (!sentiment) {
    return { score: null, reason: 'analysis_failed' };
  }

  return {
    ...sentiment,
    comment_count: commentData.fetched_comments.length,
    hn_points: commentData.points,
  };
}

// ── Format for scorer prompt ────────────────────────────────────────────────

export function formatSentimentForScorer(sentiment) {
  if (!sentiment || sentiment.score === null) {
    return '### HN Comment Sentiment\n- No sentiment data available (no comments or analysis failed)';
  }

  const lines = ['### HN Comment Sentiment'];
  lines.push(`- Sentiment score: ${sentiment.score}/10`);
  lines.push(`- HN points: ${sentiment.hn_points || 'unknown'}`);
  lines.push(`- Comments analyzed: ${sentiment.comment_count || 0}`);

  if (sentiment.positive_signals?.length) {
    lines.push(`- Positive signals: ${sentiment.positive_signals.join('; ')}`);
  }
  if (sentiment.negative_signals?.length) {
    lines.push(`- Negative signals: ${sentiment.negative_signals.join('; ')}`);
  }
  if (sentiment.justification) {
    lines.push(`- Summary: ${sentiment.justification}`);
  }

  return lines.join('\n');
}
