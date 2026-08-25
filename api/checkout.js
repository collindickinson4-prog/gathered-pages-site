// Donations — creates a Stripe Checkout Session and hands the browser its URL.
//
// The secret key never reaches the browser: the donate page posts a frequency
// and an amount here, this function talks to Stripe, and the donor is
// redirected to Stripe's hosted checkout page. Set STRIPE_SECRET_KEY in
// Vercel's environment variables (and in .env for local `vercel dev`).
//
// Like api/subscribe.js this calls the REST API with fetch rather than the
// stripe npm package, so the site keeps its no-dependencies, no-build-step
// promise.
//
// The donor picks her own amount, so the session carries an inline price
// rather than a saved one. The product IDs below are the live products the
// gifts are reported against in the dashboard; they are not secrets. A saved
// price would pin us to a fixed amount, which is the one thing this panel is
// built not to do.

const GIFTS = {
  once:    { product: 'prod_V8cSR8adRrkv0L', mode: 'payment',      label: 'One-time gift' },
  monthly: { product: 'prod_V8cWLEx2t9dBfZ', mode: 'subscription', label: 'Monthly gift', interval: 'month' },
  yearly:  { product: 'prod_V8cWLEx2t9dBfZ', mode: 'subscription', label: 'Annual gift',  interval: 'year' }
};

// The panel enforces these too; a request can arrive without going through it.
const MIN_CENTS = 500;
const MAX_CENTS = 1000000;

// The IRS asks a charity to tell the donor, in writing, that she received
// nothing in return for a gift of $250 or more. Stripe's receipt has no footer
// field of its own, so the sentence rides on the payment description, which is
// what the receipt prints as its summary line.
const ACKNOWLEDGEMENT = 'No goods or services were provided in exchange for this contribution. '
  + 'Gathered Pages Collective is a 501(c)(3) tax-exempt organization, EIN 42-3092238.';

const SESSIONS_ENDPOINT = 'https://api.stripe.com/v1/checkout/sessions';
const FALLBACK_SITE = 'https://www.gatheredpages.org';

function readBody(req) {
  if (!req.body) return {};
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch (e) { return {}; }
  }
  return req.body;
}

// Where to send the donor back to. Vercel preview deployments and local
// `vercel dev` have their own origins, so trust the browser's origin when it
// is one of ours and fall back to the live site otherwise.
function siteOrigin(req) {
  if (process.env.SITE_URL) return process.env.SITE_URL.replace(/\/$/, '');
  const origin = String(req.headers.origin || '');
  if (/^https:\/\/[a-z0-9-]+\.vercel\.app$/.test(origin)) return origin;
  if (/^https:\/\/(www\.)?gatheredpages\.org$/.test(origin)) return origin;
  if (/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origin)) return origin;
  return FALLBACK_SITE;
}

// Stripe's API takes form-encoded bodies with bracketed keys, e.g.
// line_items[0][price_data][unit_amount]=5000. This flattens a plain object
// into that.
function encode(params, prefix, pairs) {
  pairs = pairs || [];
  Object.keys(params).forEach(function (key) {
    const value = params[key];
    if (value === undefined || value === null) return;
    const name = prefix ? prefix + '[' + key + ']' : key;
    if (typeof value === 'object') {
      encode(value, name, pairs);
    } else {
      pairs.push(encodeURIComponent(name) + '=' + encodeURIComponent(String(value)));
    }
  });
  return pairs;
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const secretKey = process.env.STRIPE_SECRET_KEY;
  if (!secretKey) {
    console.error('Stripe credentials missing: set STRIPE_SECRET_KEY.');
    return res.status(500).json({ error: 'Online giving is not set up yet. Please email jamie@gatheredpages.org.' });
  }

  const body = readBody(req);
  const gift = GIFTS[String(body.frequency || '')];
  if (!gift) {
    return res.status(400).json({ error: 'We could not tell how often you meant to give. Please try again.' });
  }

  const cents = Math.round(Number(body.amount) * 100);
  if (!isFinite(cents) || cents < MIN_CENTS || cents > MAX_CENTS) {
    return res.status(400).json({ error: 'Please enter an amount between $5 and $10,000.' });
  }

  const origin = siteOrigin(req);
  const params = {
    mode: gift.mode,
    success_url: origin + '/thank-you.html?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: origin + '/donate.html',
    line_items: {
      0: {
        quantity: 1,
        price_data: {
          currency: 'usd',
          product: gift.product,
          unit_amount: cents,
          recurring: gift.interval ? { interval: gift.interval } : undefined
        }
      }
    },
    metadata: { gift: body.frequency, gift_label: gift.label }
  };

  if (gift.mode === 'payment') {
    // Stripe's own wording: the checkout button reads "Donate", and a customer
    // record is kept so the gift shows against a person in the dashboard.
    params.submit_type = 'donate';
    params.customer_creation = 'always';
    params.payment_intent_data = { description: gift.label + ' to Gathered Pages Collective. ' + ACKNOWLEDGEMENT };
  } else {
    params.subscription_data = {
      description: gift.label + ' to Gathered Pages Collective. ' + ACKNOWLEDGEMENT,
      metadata: { gift: body.frequency }
    };
  }

  try {
    const response = await fetch(SESSIONS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + secretKey,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: encode(params).join('&')
    });

    const session = await response.json().catch(function () { return {}; });

    if (!response.ok || !session.url) {
      console.error('Stripe rejected the session:', response.status, JSON.stringify(session.error || session).slice(0, 400));
      return res.status(502).json({ error: 'We could not reach our payment service. Please try again in a moment.' });
    }

    return res.status(200).json({ url: session.url });
  } catch (error) {
    console.error('Stripe request failed:', error);
    return res.status(502).json({ error: 'We could not reach our payment service. Please try again in a moment.' });
  }
};
