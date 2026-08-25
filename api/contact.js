// Contact form — emails the message to Jamie.
//
// The page used to post to a mailto: address, which opened the visitor's own
// mail app, made the browser warn that the submission was insecure, and lost
// the message entirely for anyone without desktop mail configured. The form
// now posts here and this function sends the mail.
//
// Set RESEND_API_KEY and RESEND_FROM in Vercel's environment variables (and in
// .env for local `vercel dev`). CONTACT_TO is optional and defaults to Jamie.
//
// Like the rest of api/, this calls the REST API with fetch rather than a
// package, so the site keeps its no-dependencies, no-build-step promise.

const EMAIL_ENDPOINT = 'https://api.resend.com/emails';
const DEFAULT_TO = 'jamie@gatheredpages.org';

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// What the form offers. Anything else is somebody poking at the endpoint.
const TOPICS = [
  'Hosting a book club',
  'Introducing you to a group',
  'I make something you should see',
  'Donating or fundraising',
  'Press or partnership',
  'Something else'
];

function readBody(req) {
  if (!req.body) return {};
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch (e) { return {}; }
  }
  return req.body;
}

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// The message arrives as typed. Paragraph breaks are kept; everything else is
// escaped, because this text is written by a stranger and read in a mail client.
function messageHtml(text) {
  return escapeHtml(text)
    .split(/\n{2,}/)
    .map(function (para) { return '<p>' + para.replace(/\n/g, '<br>') + '</p>'; })
    .join('\n');
}

function render(fields) {
  return [
    '<div style="font:15px/1.6 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#23272e">',
    '<p style="margin:0 0 4px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#4a5568">',
    'From the contact form',
    '</p>',
    '<h2 style="margin:0 0 18px;font-size:19px;color:#16294d">' + escapeHtml(fields.topic) + '</h2>',
    '<table cellpadding="0" cellspacing="0" style="margin:0 0 18px;font-size:15px">',
    '<tr><td style="padding:2px 14px 2px 0;color:#4a5568">Name</td><td>' + escapeHtml(fields.name) + '</td></tr>',
    '<tr><td style="padding:2px 14px 2px 0;color:#4a5568">Email</td><td><a href="mailto:' + escapeHtml(fields.email) + '">' + escapeHtml(fields.email) + '</a></td></tr>',
    '</table>',
    '<div style="border-left:3px solid #e15d2a;padding:2px 0 2px 14px">',
    messageHtml(fields.message),
    '</div>',
    '<p style="margin:22px 0 0;font-size:13px;color:#4a5568">Reply to this email and it goes straight to ' + escapeHtml(fields.name) + '.</p>',
    '</div>'
  ].join('\n');
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM;
  const to = process.env.CONTACT_TO || DEFAULT_TO;

  if (!apiKey || !from) {
    console.error('Resend credentials missing: set RESEND_API_KEY and RESEND_FROM.');
    return res.status(500).json({ error: 'The contact form is not configured yet. Please write to ' + DEFAULT_TO + '.' });
  }

  const body = readBody(req);

  // Bots fill hidden fields; people do not.
  if (body.company) return res.status(200).json({ ok: true });

  const name = String(body.name || '').trim().slice(0, 120);
  const email = String(body.email || '').trim().toLowerCase();
  const message = String(body.message || '').trim().slice(0, 5000);
  const topic = TOPICS.indexOf(String(body.topic || '')) !== -1 ? String(body.topic) : 'Something else';

  if (!name) return res.status(400).json({ error: 'Please tell us your name.' });
  if (!EMAIL.test(email) || email.length > 254) {
    return res.status(400).json({ error: 'That email address does not look right.' });
  }
  if (!message) return res.status(400).json({ error: 'Please write a message.' });

  try {
    const response = await fetch(EMAIL_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: from,
        to: [to],
        // So hitting reply in the inbox answers the person who wrote in.
        reply_to: email,
        subject: topic + ' — ' + name,
        html: render({ topic: topic, name: name, email: email, message: message })
      })
    });

    const result = await response.json().catch(function () { return {}; });

    if (!response.ok) {
      console.error('Resend rejected the message:', response.status, JSON.stringify(result.message || result.error || result).slice(0, 400));
      return res.status(502).json({ error: 'We could not send that just now. Please write to ' + DEFAULT_TO + '.' });
    }

    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Resend request failed:', error);
    return res.status(502).json({ error: 'We could not send that just now. Please write to ' + DEFAULT_TO + '.' });
  }
};
