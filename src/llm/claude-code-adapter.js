// src/llm/claude-code-adapter.js
// Uses the Claude Code CLI (`claude -p`) as the LLM backend.
// Requires Claude Code installed and authenticated (`claude auth`).
// No API key needed — uses the user's existing Claude Pro subscription.

import { execSync } from 'child_process';

const TIMEOUT_MS = 120_000;
const MAX_PROMPT_CHARS = 30_000;

/**
 * Call Claude via Claude Code CLI.
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @returns {string} raw text response
 */
export async function callClaude(systemPrompt, userPrompt) {
  const combined = systemPrompt
    ? `${systemPrompt}\n\n---\n\n${userPrompt}`
    : userPrompt;

  const truncated = combined.slice(0, MAX_PROMPT_CHARS);

  // Escape single quotes for shell safety
  const escaped = truncated.replace(/'/g, `'"'"'`);

  let output;
  try {
    output = execSync(`claude -p '${escaped}'`, {
      timeout: TIMEOUT_MS,
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024,
    });
  } catch (err) {
    throw new Error(`Claude Code CLI error: ${err.message}`);
  }

  return output.trim();
}
