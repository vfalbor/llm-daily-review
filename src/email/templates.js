// src/email/templates.js
// Renders HTML + plain-text email bodies for daily and weekly newsletters.

export function renderDailyEmail({ date, apps_tested, apps_skipped_dedup = 0 }) {
  const dateFormatted = new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  const appCards = apps_tested.map(app => {
    const scores = app.scores || {};
    const badge = { 'strong-candidate': '#16a34a', 'worth-watching': '#d97706', 'niche': '#6b7280', 'skip': '#dc2626' };
    const badgeColor = badge[app.recommendation] || '#6b7280';
    const badgeLabel = { 'strong-candidate': 'Strong candidate', 'worth-watching': 'Worth watching', 'niche': 'Niche', 'skip': 'Skip' }[app.recommendation] || app.recommendation;

    const top3 = Object.entries(scores)
      .sort((a, b) => (b[1].score ?? 0) - (a[1].score ?? 0))
      .slice(0, 3)
      .map(([k, v]) => `${criterionLabel(k)}: <strong>${v.score}/10</strong>`)
      .join(' · ');

    return `
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;border:1px solid #e4e2da;border-radius:10px;overflow:hidden;background:#fff">
  <tr><td style="padding:16px 20px">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <a href="${app.url}" style="font-size:16px;font-weight:600;color:#1a1a18;text-decoration:none">${app.title || app.app_name}</a>
          <br>
          <span style="display:inline-block;margin-top:6px;font-size:11px;background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:20px">${app.app_type || 'llm-tool'}</span>
          <span style="display:inline-block;margin-top:6px;font-size:11px;background:${badgeColor}22;color:${badgeColor};padding:2px 8px;border-radius:20px;margin-left:4px">${badgeLabel}</span>
        </td>
        <td align="right" style="font-size:28px;font-weight:700;color:#1a1a18;white-space:nowrap">${app.total_score}<span style="font-size:14px;color:#9a9891;font-weight:400">/70</span></td>
      </tr>
    </table>
    <p style="margin:12px 0 8px;font-size:14px;color:#6b6a65;line-height:1.6">${app.summary || ''}</p>
    <p style="margin:0;font-size:12px;color:#9a9891">${top3}</p>
  </td></tr>
</table>`;
  }).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#fafaf8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 16px">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">

  <!-- Header -->
  <tr><td style="padding:24px 0 20px">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td><span style="font-size:16px;font-weight:700;color:#1a1a18">● LLM Daily Review</span></td>
      <td align="right"><span style="font-size:12px;color:#9a9891">${dateFormatted}</span></td>
    </tr></table>
    <hr style="border:none;border-top:1px solid #e4e2da;margin:16px 0 0">
  </td></tr>

  <!-- Intro -->
  <tr><td style="padding:0 0 20px">
    <p style="margin:0;font-size:15px;color:#1a1a18">
      We tested <strong>${apps_tested.length} LLM app${apps_tested.length !== 1 ? 's' : ''}</strong> from today's Hacker News front page.
      ${apps_skipped_dedup > 0 ? `${apps_skipped_dedup} already tested previously were skipped.` : ''}
    </p>
  </td></tr>

  <!-- App cards -->
  <tr><td>${appCards || '<p style="color:#9a9891;font-size:14px">No new LLM apps found today.</p>'}</td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 0 0;border-top:1px solid #e4e2da;margin-top:24px">
    <p style="margin:0 0 8px;font-size:12px;color:#9a9891">
      You're receiving this because you subscribed at tokenstree.com.
      <a href="https://tokenstree.com/unsubscribe?token={{TOKEN}}" style="color:#9a9891">Unsubscribe</a>
    </p>
    <p style="margin:0;font-size:12px;color:#c4c2ba">
      Sent from info@tokenstree.com — if this landed in spam, please mark it as safe.
      Source code: <a href="https://github.com/tokenstree/llm-daily-review" style="color:#9a9891">github.com/tokenstree/llm-daily-review</a>
    </p>
  </td></tr>

</table>
</td></tr></table>
</body></html>`;

  const text = `LLM Daily Review — ${dateFormatted}

We tested ${apps_tested.length} LLM app(s) today.

${apps_tested.map(a => `${a.title || a.app_name} — ${a.total_score}/70 (${a.recommendation})\n${a.url}\n${a.summary}\n`).join('\n')}

Unsubscribe: https://tokenstree.com/unsubscribe?token={{TOKEN}}
Source: https://github.com/tokenstree/llm-daily-review`;

  return {
    subject: `[LLM Daily] ${apps_tested.length} new app${apps_tested.length !== 1 ? 's' : ''} tested — ${new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}`,
    html,
    text,
  };
}

export function renderWeeklyEmail({ week, top5, honorable_mentions, week_summary, total_apps_tested_week }) {
  const top5Cards = (top5 || []).map((app, i) => `
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;border:1px solid #e4e2da;border-radius:10px;overflow:hidden;background:#fff">
  <tr><td style="padding:4px 20px;background:#2563eb">
    <span style="font-size:12px;font-weight:600;color:#fff">#${i + 1} — ${criterionLabel(app.standout_criterion)}</span>
  </td></tr>
  <tr><td style="padding:16px 20px">
    <a href="${app.url || app.app_url || '#'}" style="font-size:16px;font-weight:600;color:#1a1a18;text-decoration:none">${app.app_name}</a>
    <p style="margin:10px 0 0;font-size:14px;color:#6b6a65;line-height:1.6">${app.why_top5 || ''}</p>
    <p style="margin:10px 0 0;font-size:12px;color:#9a9891">Total score: <strong>${app.total_score}/70</strong></p>
  </td></tr>
</table>`).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#fafaf8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 16px">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">

  <tr><td style="padding:24px 0 20px">
    <span style="font-size:16px;font-weight:700;color:#1a1a18">● LLM Week in Review</span>
    <span style="float:right;font-size:12px;color:#9a9891">${week}</span>
    <hr style="border:none;border-top:1px solid #e4e2da;margin:16px 0 0">
  </td></tr>

  <tr><td style="padding:0 0 24px">
    <p style="margin:0;font-size:15px;color:#1a1a18;line-height:1.7">${week_summary || ''}</p>
    <p style="margin:12px 0 0;font-size:13px;color:#9a9891">Apps tested this week: <strong>${total_apps_tested_week}</strong></p>
  </td></tr>

  <tr><td><h2 style="margin:0 0 16px;font-size:16px;font-weight:600;color:#1a1a18">Top 5 this week</h2>
    ${top5Cards}
  </td></tr>

  ${honorable_mentions?.length ? `<tr><td style="padding:16px 0 0">
    <p style="margin:0;font-size:13px;color:#9a9891"><strong>Honorable mentions:</strong> ${honorable_mentions.join(', ')}</p>
  </td></tr>` : ''}

  <tr><td style="padding:24px 0 0;border-top:1px solid #e4e2da">
    <p style="margin:0 0 8px;font-size:12px;color:#9a9891">
      <a href="https://tokenstree.com/unsubscribe?token={{TOKEN}}" style="color:#9a9891">Unsubscribe</a> ·
      <a href="https://github.com/tokenstree/llm-daily-review" style="color:#9a9891">GitHub</a>
    </p>
    <p style="margin:0;font-size:12px;color:#c4c2ba">Sent from info@tokenstree.com — check spam if not in inbox.</p>
  </td></tr>

</table></td></tr></table>
</body></html>`;

  const text = `LLM Week in Review — ${week}\n\n${week_summary}\n\nApps tested: ${total_apps_tested_week}\n\nTop 5:\n${(top5 || []).map((a, i) => `${i + 1}. ${a.app_name} (${a.total_score}/70)\n   ${a.why_top5}`).join('\n\n')}\n\nUnsubscribe: https://tokenstree.com/unsubscribe?token={{TOKEN}}`;

  return {
    subject: `[LLM Weekly] Top 5 LLM apps — ${week}`,
    html,
    text,
  };
}

function criterionLabel(key) {
  const labels = {
    novelty: 'Novelty', system_requirements: 'System requirements',
    current_relevance: 'Relevance', differentiation: 'Differentiation',
    community: 'Community', ease_of_use: 'Ease of use',
    ease_of_integration: 'Integration',
  };
  return labels[key] || key;
}
