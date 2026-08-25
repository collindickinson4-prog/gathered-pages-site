// Newsletter signup — posts to Kit (formerly ConvertKit).
//
// The form posts here, this function talks to Kit. Set KIT_FORM_ID in Vercel's
// environment variables (and in .env for local `vercel dev`). No API key is
// needed: this is the same endpoint Kit's own embedded forms post to, and it
// is the only one that honours the form's double opt-in, so the reader gets
// the confirmation email before they are on the list.
//
// Kit answers 200 whether it worked or not, so the body's status is what
// decides, not the HTTP code.

const ENDPOINT = 'https://app.convertkit.com/forms/{form}/subscriptions';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function readBody(req) {
  if (!req.body) return {};
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch (e) { return {}; }
  }
  return req.body;
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const formId = process.env.KIT_FORM_ID;
  if (!formId) {
    console.error('Kit credentials missing: set KIT_FORM_ID.');
    return res.status(500).json({ error: 'The signup form is not configured yet. Please email jamie@gatheredpages.org.' });
  }

  const body = readBody(req);

  // Bots fill hidden fields; people do not.
  if (body.company) return res.status(200).json({ ok: true });

  const email = String(body.email || '').trim().toLowerCase();
  const firstName = String(body.first_name || '').trim().slice(0, 80);

  if (!EMAIL.test(email) || email.length > 254) {
    return res.status(400).json({ error: 'That email address does not look right.' });
  }

  try {
    const response = await fetch(ENDPOINT.replace('{form}', formId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ email_address: email, first_name: firstName || undefined })
    });

    const text = await response.text();
    let result = {};
    try { result = JSON.parse(text); } catch (e) { /* handled below */ }

    if (!response.ok || result.status !== 'success') {
      console.error('Kit rejected the signup:', response.status, text.slice(0, 400));
      return res.status(502).json({ error: 'We could not reach our email service. Please try again in a moment.' });
    }

    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Kit request failed:', error);
    return res.status(502).json({ error: 'We could not reach our email service. Please try again in a moment.' });
  }
};
