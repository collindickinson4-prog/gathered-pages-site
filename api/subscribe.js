// Newsletter signup — posts to Kit (formerly ConvertKit).
//
// The API key never reaches the browser: the form posts here, this function
// talks to Kit. Set KIT_API_KEY and KIT_FORM_ID in Vercel's environment
// variables (and in .env for local `vercel dev`).
//
// Kit has two live API generations and the key you generate decides which one
// works. V4 keys (kit_...) authenticate with an X-Kit-Api-Key header; older V3
// keys go in the request body. We try V4 first and fall back to V3 when Kit
// rejects the key, so either kind of key works without a code change.

const V4_ENDPOINT = 'https://api.kit.com/v4/forms/{form}/subscribers';
const V3_ENDPOINT = 'https://api.convertkit.com/v3/forms/{form}/subscribe';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function readBody(req) {
  if (!req.body) return {};
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch (e) { return {}; }
  }
  return req.body;
}

async function subscribeV4(apiKey, formId, email, firstName) {
  const response = await fetch(V4_ENDPOINT.replace('{form}', formId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Kit-Api-Key': apiKey },
    body: JSON.stringify({ email_address: email, first_name: firstName || undefined })
  });
  return { ok: response.ok, status: response.status, text: await response.text() };
}

async function subscribeV3(apiKey, formId, email, firstName) {
  const response = await fetch(V3_ENDPOINT.replace('{form}', formId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey, email: email, first_name: firstName || undefined })
  });
  return { ok: response.ok, status: response.status, text: await response.text() };
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const apiKey = process.env.KIT_API_KEY;
  const formId = process.env.KIT_FORM_ID;
  if (!apiKey || !formId) {
    console.error('Kit credentials missing: set KIT_API_KEY and KIT_FORM_ID.');
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
    let result = await subscribeV4(apiKey, formId, email, firstName);

    if (!result.ok && [401, 403, 404].includes(result.status)) {
      result = await subscribeV3(apiKey, formId, email, firstName);
    }

    if (!result.ok) {
      console.error('Kit rejected the signup:', result.status, result.text.slice(0, 400));
      return res.status(502).json({ error: 'We could not reach our email service. Please try again in a moment.' });
    }

    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Kit request failed:', error);
    return res.status(502).json({ error: 'We could not reach our email service. Please try again in a moment.' });
  }
};
