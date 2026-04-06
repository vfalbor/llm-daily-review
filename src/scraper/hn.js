// src/scraper/hn.js
// Fetches and parses Hacker News front page.
// Returns top N items without following "More".

import * as cheerio from 'cheerio';

const HN_URL = 'https://news.ycombinator.com/';
const USER_AGENT = 'llm-daily-review/1.0 (+https://github.com/tokenstree/llm-daily-review)';

export async function scrapeHN({ max_items = 30 } = {}) {
  const res = await fetch(HN_URL, {
    headers: { 'User-Agent': USER_AGENT },
    signal: AbortSignal.timeout(15_000),
  });

  if (!res.ok) throw new Error(`HN fetch failed: ${res.status}`);

  const html = await res.text();
  const $ = cheerio.load(html);
  const items = [];

  // HN rows come in pairs: .athing (title row) + next sibling (subtext row)
  $('.athing').each((i, el) => {
    if (items.length >= max_items) return false;

    const $el = $(el);
    const rank = parseInt($el.find('.rank').text(), 10);
    const titleEl = $el.find('.titleline > a').first();
    const title = titleEl.text().trim();
    let url = titleEl.attr('href') || '';

    // Internal HN items (Ask HN, Show HN) have relative URLs
    if (url.startsWith('item?id=')) url = HN_URL + url;

    const hnItemId = $el.attr('id');
    const hn_url = `https://news.ycombinator.com/item?id=${hnItemId}`;

    // Subtext row is the next sibling
    const subtext = $el.next('.athing').length ? null : $el.next();
    const points = subtext ? parseInt($(subtext).find('.score').text(), 10) || 0 : 0;
    const comments = subtext
      ? parseInt($(subtext).find('a').last().text(), 10) || 0
      : 0;
    const author = subtext ? $(subtext).find('.hnuser').text() : '';
    const age = subtext ? $(subtext).find('.age').attr('title') || '' : '';

    if (!title || !url) return;

    items.push({
      rank,
      title,
      url: cleanUrl(url),
      hn_url,
      points,
      comments,
      author,
      age,
      scraped_at: new Date().toISOString(),
    });
  });

  return items;
}

function cleanUrl(url) {
  try {
    const u = new URL(url);
    // Strip common tracking params
    ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'fbclid'].forEach(p =>
      u.searchParams.delete(p)
    );
    return u.toString();
  } catch {
    return url;
  }
}
