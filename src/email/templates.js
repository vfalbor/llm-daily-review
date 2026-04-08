// src/email/templates.js
// Renders HTML + plain-text email bodies for daily and weekly newsletters.

const GITHUB_RESULTS_BASE = 'https://github.com/vfalbor/llm-daily-review/tree/main/results';

function escHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function criterionLabel(key) {
  const labels = {
    hn_sentiment: 'HN Sentiment', novelty: 'Novelty', system_requirements: 'System req.',
    current_relevance: 'Relevance', differentiation: 'Differentiation',
    community: 'Community', ease_of_use: 'Ease of use',
    ease_of_integration: 'Integration', documentation: 'Docs',
    maturity: 'Maturity', performance: 'Performance',
  };
  return labels[key] || key;
}

function scoreBar(score, max = 10) {
  const pct = Math.round((score / max) * 100);
  const color = score >= 7 ? '#16a34a' : score >= 5 ? '#d97706' : '#dc2626';
  return `<div style="height:4px;background:#e4e2da;border-radius:2px;margin-top:3px">
    <div style="height:4px;width:${pct}%;background:${color};border-radius:2px"></div>
  </div>`;
}

function domainEmoji(domain) {
  const map = {
    'llm-ai': '🤖', 'devtool': '🔧', 'database': '🗄️', 'infrastructure': '⚙️',
    'language': '📝', 'security': '🔒', 'data': '📊', 'web': '🌐',
    'mobile': '📱', 'hardware': '🔌', 'research': '🔬', 'game': '🎮',
  };
  return map[domain] || '📦';
}

export function renderDailyEmail({ date, apps_tested, apps_skipped_dedup = 0 }) {
  const dateFormatted = new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  // Stats summary
  const byRec = { 'strong-candidate': 0, 'worth-watching': 0, 'niche': 0, 'skip': 0 };
  apps_tested.forEach(a => { if (byRec[a.recommendation] !== undefined) byRec[a.recommendation]++; });
  const topScore = apps_tested.length ? Math.max(...apps_tested.map(a => a.total_score || 0)) : 0;
  const avgScore = apps_tested.length
    ? Math.round(apps_tested.reduce((s, a) => s + (a.total_score || 0), 0) / apps_tested.length)
    : 0;

  // Domains covered
  const domains = [...new Set(apps_tested.map(a => (a.report || a).domain).filter(Boolean))];

  const appCards = apps_tested
    .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
    .map(app => {
      const scores   = app.scores || {};
      const report   = app.report || app;
      const badgeColor = { 'strong-candidate': '#16a34a', 'worth-watching': '#d97706', 'niche': '#6b7280', 'skip': '#dc2626' }[app.recommendation] || '#6b7280';
      const badgeLabel = { 'strong-candidate': '⭐ Strong candidate', 'worth-watching': '👀 Worth watching', 'niche': '🔍 Niche', 'skip': '⏭ Skip' }[app.recommendation] || app.recommendation;

      const toolUrl  = report.app_url || report.tool_url || app.url || '#';
      const hnUrl    = report.hn_url;
      const domain   = report.domain || '';
      const appType  = report.app_type || app.app_type || '';
      const ghSlug   = (app.title || app.report?.app_name || app.app_name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);
      const ghLink   = `${GITHUB_RESULTS_BASE}/${date}/${ghSlug}`;

      // Test results
      const testsTotal  = report.enriched?.tests_total ?? 0;
      const testsPassed = report.enriched?.tests_passed ?? 0;
      const testBar = testsTotal > 0
        ? `Tests: <strong>${testsPassed}/${testsTotal} passed</strong>`
        : 'No automated tests ran';

      // Benchmarks from scores enriched
      const benchmarks = (report.enriched?.benchmark_notes || '')
        .split('\n').filter(Boolean)
        .map(l => l.replace('BENCHMARK:', '').replace(/:/g, ': '))
        .slice(0, 3);

      // All 10 criteria
      const allCriteria = [
        'hn_sentiment','novelty','system_requirements','current_relevance','differentiation',
        'community','ease_of_use','ease_of_integration','documentation','maturity','performance',
      ];
      const criteriaRows = allCriteria.map(key => {
        const s    = scores[key]?.score ?? '—';
        const just = scores[key]?.justification || '';
        const num  = typeof s === 'number' ? s : 0;
        return `<tr>
          <td style="padding:4px 8px 4px 0;font-size:12px;color:#6b6a65;width:130px;vertical-align:top">${criterionLabel(key)}</td>
          <td style="padding:4px 0;width:36px;text-align:right;font-size:12px;font-weight:600;color:#1a1a18;vertical-align:top">${s}/10</td>
          <td style="padding:4px 0 4px 10px;font-size:11px;color:#9a9891;vertical-align:top">${escHtml(just.slice(0, 120))}${just.length > 120 ? '…' : ''}</td>
        </tr>`;
      }).join('');

      return `
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;border:1px solid #e4e2da;border-radius:10px;overflow:hidden;background:#fff">
  <!-- App header -->
  <tr><td style="padding:16px 20px 12px">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="vertical-align:top">
        <div style="font-size:16px;font-weight:600;margin-bottom:5px">
          <a href="${escHtml(toolUrl)}" style="color:#1a1a18;text-decoration:none">${escHtml(app.report?.app_name || app.app_name || app.title)}</a>
          ${hnUrl ? `&nbsp;<a href="${escHtml(hnUrl)}" style="font-size:11px;color:#FF6600;text-decoration:none;font-weight:500">▲ HN</a>` : ''}
        </div>
        <div>
          ${domain ? `<span style="display:inline-block;font-size:11px;background:#f0f4ff;color:#2563eb;padding:2px 7px;border-radius:20px;margin-right:4px">${domainEmoji(domain)} ${escHtml(domain)}</span>` : ''}
          ${appType ? `<span style="display:inline-block;font-size:11px;background:#f3f4f6;color:#6b7280;padding:2px 7px;border-radius:20px;margin-right:4px">${escHtml(appType)}</span>` : ''}
          <span style="display:inline-block;font-size:11px;background:${badgeColor}22;color:${badgeColor};padding:2px 7px;border-radius:20px;font-weight:600">${badgeLabel}</span>
        </div>
      </td>
      <td align="right" style="vertical-align:top;white-space:nowrap;padding-left:12px">
        <div style="font-size:30px;font-weight:700;color:#1a1a18;line-height:1">${app.total_score ?? '—'}<span style="font-size:13px;color:#9a9891;font-weight:400">/100</span></div>
      </td>
    </tr></table>
  </td></tr>

  <!-- Summary -->
  ${report.summary || app.summary ? `<tr><td style="padding:0 20px 12px">
    <p style="margin:0;font-size:13px;color:#44423d;line-height:1.6">${escHtml(report.summary || app.summary)}</p>
  </td></tr>` : ''}

  <!-- Test results + benchmarks -->
  <tr><td style="padding:0 20px 12px;border-top:1px solid #f0ede6">
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px"><tr>
      <td style="vertical-align:top;width:50%">
        <div style="font-size:11px;font-weight:600;color:#9a9891;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">QA Tests</div>
        <div style="font-size:12px;color:#1a1a18">${testBar}</div>
        <div style="margin-top:4px">
          <a href="${ghLink}" style="font-size:11px;color:#2563eb;text-decoration:none">→ View test artifacts on GitHub</a>
        </div>
      </td>
      <td style="vertical-align:top;padding-left:16px;width:50%">
        <div style="font-size:11px;font-weight:600;color:#9a9891;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">Benchmarks</div>
        ${benchmarks.length
          ? benchmarks.map(b => `<div style="font-size:12px;color:#1a1a18;margin-bottom:2px">📊 ${b}</div>`).join('')
          : '<div style="font-size:12px;color:#9a9891">No benchmark data</div>'
        }
      </td>
    </tr></table>
  </td></tr>

  <!-- Scores breakdown -->
  <tr><td style="padding:0 20px 14px;border-top:1px solid #f0ede6">
    <div style="font-size:11px;font-weight:600;color:#9a9891;text-transform:uppercase;letter-spacing:.5px;margin:10px 0 8px">Score breakdown</div>
    <table width="100%" cellpadding="0" cellspacing="0">${criteriaRows}</table>
  </td></tr>
</table>`;
    }).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#fafaf8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 16px">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%">

  <!-- Header -->
  <tr><td style="padding:24px 0 20px">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td><span style="font-size:16px;font-weight:700;color:#1a1a18">● TokensTree Daily Review</span></td>
      <td align="right"><span style="font-size:12px;color:#9a9891">${dateFormatted}</span></td>
    </tr></table>
    <hr style="border:none;border-top:1px solid #e4e2da;margin:14px 0 0">
  </td></tr>

  <!-- Stats bar -->
  <tr><td style="padding:0 0 20px">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #e4e2da;border-radius:10px;padding:14px 20px"><tr>
      <td style="text-align:center;border-right:1px solid #e4e2da;padding-right:16px">
        <div style="font-size:22px;font-weight:700;color:#1a1a18">${apps_tested.length}</div>
        <div style="font-size:11px;color:#9a9891">apps tested</div>
      </td>
      <td style="text-align:center;border-right:1px solid #e4e2da;padding:0 16px">
        <div style="font-size:22px;font-weight:700;color:#1a1a18">${avgScore}</div>
        <div style="font-size:11px;color:#9a9891">avg score /100</div>
      </td>
      <td style="text-align:center;border-right:1px solid #e4e2da;padding:0 16px">
        <div style="font-size:22px;font-weight:700;color:#d97706">${byRec['worth-watching'] + byRec['strong-candidate']}</div>
        <div style="font-size:11px;color:#9a9891">worth watching</div>
      </td>
      <td style="text-align:center;padding-left:16px">
        <div style="font-size:22px;font-weight:700;color:#6b7280">${apps_skipped_dedup}</div>
        <div style="font-size:11px;color:#9a9891">already known</div>
      </td>
    </tr></table>
    ${domains.length ? `<p style="margin:10px 0 0;font-size:12px;color:#9a9891">Domains today: ${domains.map(d => `${domainEmoji(d)} ${d}`).join(' · ')}</p>` : ''}
  </td></tr>

  <!-- App cards -->
  <tr><td>${appCards || '<p style="color:#9a9891;font-size:14px">No new apps found today.</p>'}</td></tr>

  <!-- Score legend -->
  <tr><td style="padding:0 0 20px">
    <table cellpadding="0" cellspacing="0"><tr>
      <td style="font-size:11px;color:#9a9891;padding-right:12px">Score legend:</td>
      <td style="font-size:11px;color:#16a34a;padding-right:10px">■ ≥70 strong</td>
      <td style="font-size:11px;color:#d97706;padding-right:10px">■ 50–69 worth watching</td>
      <td style="font-size:11px;color:#6b7280;padding-right:10px">■ 35–49 niche</td>
      <td style="font-size:11px;color:#dc2626">■ &lt;35 skip</td>
    </tr></table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:16px 0 0;border-top:1px solid #e4e2da">
    <p style="margin:0 0 6px;font-size:12px;color:#9a9891">
      You're receiving this because you subscribed at <a href="https://tokenstree.com" style="color:#2563eb">tokenstree.com</a>.
      <a href="https://tokenstree.com/unsubscribe?token={{TOKEN}}" style="color:#9a9891;margin-left:8px">Unsubscribe</a>
    </p>
    <p style="margin:0;font-size:11px;color:#c4c2ba">
      Sent from info@tokenstree.com — if this landed in spam, please mark it safe.
    </p>
  </td></tr>

</table>
</td></tr></table>
</body></html>`;

  const text = `TokensTree Daily Review — ${dateFormatted}

${apps_tested.length} apps tested today | avg score: ${avgScore}/100 | ${byRec['worth-watching'] + byRec['strong-candidate']} worth watching | ${apps_skipped_dedup} skipped (already known)

${apps_tested
  .sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
  .map(a => {
    const r = a.report || {};
    const t = r.enriched?.tests_passed ?? 0;
    const tot = r.enriched?.tests_total ?? 0;
    return [
      `${a.total_score}/100 [${a.recommendation}] ${a.title || a.app_name}`,
      `  Domain: ${r.domain || '?'} | Type: ${r.app_type || '?'}`,
      `  ${r.summary || a.summary || ''}`,
      `  Tests: ${tot > 0 ? `${t}/${tot} passed` : 'n/a'}`,
      `  URL: ${r.tool_url || r.app_url || a.url}`,
      `  Artifacts: ${GITHUB_RESULTS_BASE}/${date}/${(a.title || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60)}`,
    ].join('\n');
  }).join('\n\n')}

All results: ${GITHUB_RESULTS_BASE}/${date}
Unsubscribe: https://tokenstree.com/unsubscribe?token={{TOKEN}}`;

  const worthy = apps_tested.filter(a => ['strong-candidate','worth-watching'].includes(a.recommendation));
  const subject = worthy.length
    ? `[HN Daily] ${worthy.map(a => a.title?.split(':')[0] || a.app_name).slice(0,2).join(', ')} and ${apps_tested.length - worthy.length} more — ${new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}`
    : `[HN Daily] ${apps_tested.length} apps reviewed — ${new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}`;

  return { subject, html, text };
}

export function renderWeeklyEmail({ week, top5, honorable_mentions, week_summary, total_apps_tested_week }) {
  const top5Cards = (top5 || []).map((app, i) => `
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;border:1px solid #e4e2da;border-radius:10px;overflow:hidden;background:#fff">
  <tr><td style="padding:4px 20px;background:#2563eb">
    <span style="font-size:12px;font-weight:600;color:#fff">#${i + 1} — Standout: ${criterionLabel(app.standout_criterion)}</span>
  </td></tr>
  <tr><td style="padding:16px 20px">
    <a href="${escHtml(app.url || app.app_url || '#')}" style="font-size:16px;font-weight:600;color:#1a1a18;text-decoration:none">${escHtml(app.app_name)}</a>
    <p style="margin:10px 0 0;font-size:13px;color:#6b6a65;line-height:1.6">${escHtml(app.why_top5 || '')}</p>
    <p style="margin:10px 0 0;font-size:12px;color:#9a9891">Total score: <strong>${app.total_score}/100</strong></p>
  </td></tr>
</table>`).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#fafaf8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 16px">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%">
  <tr><td style="padding:24px 0 20px">
    <span style="font-size:16px;font-weight:700;color:#1a1a18">● TokensTree Week in Review</span>
    <span style="float:right;font-size:12px;color:#9a9891">${week}</span>
    <hr style="border:none;border-top:1px solid #e4e2da;margin:14px 0 0">
  </td></tr>
  <tr><td style="padding:0 0 24px">
    <p style="margin:0;font-size:14px;color:#1a1a18;line-height:1.7">${escHtml(week_summary || '')}</p>
    <p style="margin:10px 0 0;font-size:12px;color:#9a9891">Apps reviewed this week: <strong>${total_apps_tested_week}</strong></p>
  </td></tr>
  <tr><td><h2 style="margin:0 0 16px;font-size:15px;font-weight:600;color:#1a1a18">Top 5 this week</h2>${top5Cards}</td></tr>
  ${honorable_mentions?.length ? `<tr><td style="padding:12px 0">
    <p style="margin:0;font-size:12px;color:#9a9891"><strong>Honorable mentions:</strong> ${honorable_mentions.map(m => escHtml(m)).join(', ')}</p>
  </td></tr>` : ''}
  <tr><td style="padding:20px 0 0;border-top:1px solid #e4e2da">
    <p style="margin:0;font-size:12px;color:#9a9891">
      <a href="https://tokenstree.com/unsubscribe?token={{TOKEN}}" style="color:#9a9891">Unsubscribe</a> ·
      <a href="https://github.com/vfalbor/llm-daily-review" style="color:#9a9891">GitHub</a>
    </p>
  </td></tr>
</table></td></tr></table>
</body></html>`;

  const text = `TokensTree Week in Review — ${week}\n\n${week_summary}\n\nApps reviewed: ${total_apps_tested_week}\n\nTop 5:\n${(top5 || []).map((a, i) => `${i + 1}. ${a.app_name} (${a.total_score}/100)\n   ${a.why_top5}`).join('\n\n')}\n\nUnsubscribe: https://tokenstree.com/unsubscribe?token={{TOKEN}}`;

  return {
    subject: `[HN Weekly] Top 5 apps this week — ${week}`,
    html,
    text,
  };
}
