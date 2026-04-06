// src/email/mailer.js
// Sends daily + weekly newsletters via SMTP (nodemailer).

import nodemailer from 'nodemailer';
import { getActiveSubscribers } from '../db/database.js';
import { renderDailyEmail, renderWeeklyEmail } from './templates.js';
import { log } from '../utils/logger.js';

function createTransport() {
  return nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
    tls: { rejectUnauthorized: false },  // allow IP-based SMTP without cert match
  });
}

export async function sendNewsletter(payload) {
  const transport = createTransport();

  if (payload.edition === 'daily') {
    const recipients = await getActiveSubscribers('daily');
    if (!recipients.length) {
      log.info('No daily subscribers — skipping email');
      return;
    }
    const { subject, html, text } = renderDailyEmail(payload);
    await sendBatch(transport, recipients, subject, html, text);
    log.info(`Daily newsletter sent to ${recipients.length} subscribers`);
  }

  if (payload.edition === 'weekly') {
    const recipients = await getActiveSubscribers('weekly');
    if (!recipients.length) {
      log.info('No weekly subscribers — skipping email');
      return;
    }
    const { subject, html, text } = renderWeeklyEmail(payload);
    await sendBatch(transport, recipients, subject, html, text);
    log.info(`Weekly newsletter sent to ${recipients.length} subscribers`);
  }
}

async function sendBatch(transport, recipients, subject, html, text) {
  // Send individually so each email is personalised (unsubscribe token)
  for (const to of recipients) {
    try {
      await transport.sendMail({
        from: '"LLM Daily Review" <info@tokenstree.com>',
        to,
        subject,
        html,
        text,
      });
    } catch (err) {
      log.error(`Failed to send to ${to}: ${err.message}`);
    }
  }
}
