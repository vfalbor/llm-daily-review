// src/hn/poster.js
// Logs into Hacker News and posts a top-level comment on an item thread.

import * as cheerio from 'cheerio';
import { log } from '../utils/logger.js';

const HN_BASE = 'https://news.ycombinator.com';

export async function postHNComment(hnUrl, commentText) {
  const username = process.env.HN_USERNAME;
  const password = process.env.HN_PASSWORD;

  if (!username || !password) throw new Error('HN_USERNAME or HN_PASSWORD not set in .env');

  // Step 1: Login — get session cookie
  const loginRes = await fetch(`${HN_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ acct: username, pw: password, goto: 'news' }),
    redirect: 'manual',
  });

  const rawCookies = loginRes.headers.getSetCookie
    ? loginRes.headers.getSetCookie()
    : [loginRes.headers.get('set-cookie')].filter(Boolean);

  if (loginRes.status === 429) throw new Error('HN login rate-limited (429) — wait a few minutes and retry.');
  if (!rawCookies.length) throw new Error('HN login failed — no cookie returned. Check credentials.');

  const cookieHeader = rawCookies.map(c => c.split(';')[0]).join('; ');

  // Verify we have a user cookie (not just an empty session)
  if (!cookieHeader.includes('user=')) throw new Error('HN login failed — user cookie missing.');

  log.info(`HN login OK as ${username}`);

  // Step 2: Fetch the item page to extract the comment form HMAC
  const itemRes = await fetch(hnUrl, {
    headers: { Cookie: cookieHeader },
  });

  if (!itemRes.ok) throw new Error(`Could not load HN item page: ${itemRes.status}`);

  const html = await itemRes.text();
  const $ = cheerio.load(html);

  // The top-level reply form is the first comment form on the page
  const hmac   = $('input[name="hmac"]').first().val();
  const parent = $('input[name="parent"]').first().val();

  if (!hmac || !parent) throw new Error('Could not find comment form fields (hmac/parent) on item page.');

  // Step 3: Post the comment
  const commentRes = await fetch(`${HN_BASE}/comment`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Cookie: cookieHeader,
    },
    body: new URLSearchParams({ parent, text: commentText, hmac }),
    redirect: 'manual',
  });

  // HN returns 302 to the item on success, 200 with error page on failure
  if (commentRes.status !== 302) {
    const body = await commentRes.text();
    const errMsg = cheerio.load(body)('body').text().slice(0, 200);
    throw new Error(`Comment post failed (status ${commentRes.status}): ${errMsg}`);
  }

  log.info(`HN comment posted on ${hnUrl} (parent=${parent})`);
  return { parent, hn_url: hnUrl };
}
