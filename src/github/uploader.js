// src/github/uploader.js
// Uploads container test logs to a GitHub release or repo directory.
// Each app run gets its own folder: results/{date}/{app-slug}/
// After upload, local temp files are deleted to free disk space.

import { Octokit } from '@octokit/rest';
import fs from 'fs';
import path from 'path';
import { log } from '../utils/logger.js';

const OWNER = process.env.GITHUB_OWNER || 'tokenstree';
const REPO = process.env.GITHUB_REPO || 'llm-daily-review';

function getOctokit() {
  return new Octokit({ auth: process.env.GITHUB_TOKEN });
}

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);
}

export async function uploadToGitHub(app, testResults) {
  if (!process.env.GITHUB_TOKEN) {
    log.warn('GITHUB_TOKEN not set — skipping GitHub upload');
    return;
  }

  const octokit = getOctokit();
  const date = new Date().toISOString().split('T')[0];
  const slug = slugify(app.title || 'unknown-app');
  const basePath = `results/${date}/${slug}`;

  // Files to upload from the temp log directory
  const files = {
    'stdout.txt': path.join(testResults.log_dir, 'stdout.txt'),
    'stderr.txt': path.join(testResults.log_dir, 'stderr.txt'),
    'app-meta.json': null, // generated inline
    'scores.json': null,   // generated inline
  };

  const uploads = [];

  for (const [filename, filepath] of Object.entries(files)) {
    let content;

    if (filename === 'app-meta.json') {
      content = Buffer.from(JSON.stringify({ app, test_results: testResults }, null, 2)).toString('base64');
    } else if (filename === 'scores.json') {
      // Scores are added after scoring; skip here, orchestrator calls a second upload
      continue;
    } else if (filepath && fs.existsSync(filepath)) {
      content = fs.readFileSync(filepath).toString('base64');
    } else {
      continue;
    }

    try {
      // Check if file already exists (to get SHA for update)
      let sha;
      try {
        const existing = await octokit.repos.getContent({
          owner: OWNER, repo: REPO,
          path: `${basePath}/${filename}`,
        });
        sha = existing.data.sha;
      } catch { /* file doesn't exist yet */ }

      await octokit.repos.createOrUpdateFileContents({
        owner: OWNER, repo: REPO,
        path: `${basePath}/${filename}`,
        message: `test: add ${filename} for ${slug} (${date})`,
        content,
        sha,
      });

      uploads.push(filename);
    } catch (err) {
      log.error(`GitHub upload failed for ${filename}: ${err.message}`);
    }
  }

  log.info(`Uploaded to GitHub: ${basePath}/ [${uploads.join(', ')}]`);

  // Clean up local temp files to free disk space
  try {
    fs.rmSync(testResults.log_dir, { recursive: true, force: true });
    log.info(`Cleaned up local temp dir: ${testResults.log_dir}`);
  } catch (err) {
    log.warn(`Could not delete temp dir: ${err.message}`);
  }
}

export async function uploadScores(app, scored, date) {
  if (!process.env.GITHUB_TOKEN) return;

  const octokit = getOctokit();
  const slug = slugify(app.title || 'unknown-app');
  const filePath = `results/${date}/${slug}/scores.json`;

  const content = Buffer.from(JSON.stringify(scored, null, 2)).toString('base64');

  try {
    let sha;
    try {
      const existing = await octokit.repos.getContent({ owner: OWNER, repo: REPO, path: filePath });
      sha = existing.data.sha;
    } catch {}

    await octokit.repos.createOrUpdateFileContents({
      owner: OWNER, repo: REPO, path: filePath,
      message: `score: ${slug} — ${scored.total_score}/70 (${date})`,
      content, sha,
    });
  } catch (err) {
    log.error(`GitHub score upload failed: ${err.message}`);
  }
}
