// src/llm/index.js
// LLM provider router. Switch via LLM_PROVIDER env var:
//   LLM_PROVIDER=groq          → Groq API (free, requires GROQ_API_KEY)
//   LLM_PROVIDER=claude-code   → Claude Code CLI (requires `claude` installed + auth)

import { callGroq } from './groq-adapter.js';
import { callClaude } from './claude-code-adapter.js';

const PROVIDER = process.env.LLM_PROVIDER || 'groq';

/**
 * Unified LLM call. Returns raw text string.
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @param {number} maxTokens
 */
export async function llmCall(systemPrompt, userPrompt, maxTokens = 4096) {
  if (PROVIDER === 'claude-code') {
    return callClaude(systemPrompt, userPrompt);
  }
  return callGroq(systemPrompt, userPrompt, maxTokens);
}

export { PROVIDER };
