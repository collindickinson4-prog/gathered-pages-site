// Donations — creates a Stripe Checkout Session and hands the browser its URL.
//
// The secret key never reaches the browser: the donate page posts a gift key
// here, this function talks to Stripe, and the donor is redirected to Stripe's
// hosted checkout page. Set STRIPE_SECRET_KEY in Vercel's environment
// variables (and in .env for local `vercel dev`).
//
// Like api/subscribe.js this calls the REST API with fetch rather than the
// stripe npm package, so the site keeps its no-dependencies, no-build-step
// promise.
//
// PRICES BELOW: these are Stripe price IDs, not secrets — they are safe in
// the repository. Each one is created in the Stripe dashboard under its
// product (Product -> Pricing -> the price_... shown beside the amount).
// Test-mode and live-mode prices have different IDs. The ones below are the
// LIVE prices, exported from the dashboard on 25 August 2026.

const GIFTS = {
  // Product 1 — One-Time Gift. The amount is left to the donor, so this price
  // is the "customer chooses what to pay" kind and carries no fixed amount.
  onetime:   { price: 'price_1U8LDm172S9w5H39Jerp9pwy',  mode: 'payment',      label: 'One-time gift' },

  // Product 2 — Recurring Gift. One product, four prices, one per interval.
  weekly:    { price: 'price_1U8LI6172S9w5H39rp8CmFnL',  mode: 'subscription', label: 'Recurring gift, weekly' },
  monthly:   { price: 'price_1U8LGy172S9w5H39174R6eQf',  mode: 'subscription', label: 'Recurring gift, monthly' },
  quarterly: { price: 'price_1U8LI6172S9w5H390ZomQu2f',  mode: 'subscription', label: 'Recurring gift, quarterly' },
  yearly:    { price: 'price_1U8LI6172S9w5H39qgDer92K',  mode: 'subscription', label: 'Recurring gift, yearly' },

  // Products 3 and 4 — fixed gifts. Both let the donor give more than one at
  // checkout, so a donor who means to fund three kits does not come back here
  // three times.
  kit:       { price: 'price_1U8LJG172S9w5H39wB4bYrkd',  mode: 'payment',      label: 'One kit for one woman',  quantity: 20 },
  box:       { price: 'price_1U8LLj172S9w5H392bNETU5A',  mode: 'payment',      label: 'A Book Club Box',        quantity: 10 }
};

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
// line_items[0][price]=price_123. This flattens a plain object into that.
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
  const gift = GIFTS[String(body.gift || '')];

  if (!gift) {
    return res.status(400).json({ error: 'We could not tell which gift you meant. Please try again.' });
  }
  if (gift.price.indexOf('price_REPLACE') === 0) {
    console.error('Gift "%s" has no real Stripe price ID yet.', body.gift);
    return res.status(500).json({ error: 'This way of giving is not open yet. Please email jamie@gatheredpages.org.' });
  }

  const origin = siteOrigin(req);
  const params = {
    mode: gift.mode,
    success_url: origin + '/thank-you.html?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: origin + '/donate.html',
    line_items: {
      0: {
        price: gift.price,
        quantity: 1,
        adjustable_quantity: gift.quantity
          ? { enabled: 'true', minimum: 1, maximum: gift.quantity }
          : undefined
      }
    },
    metadata: { gift: body.gift, gift_label: gift.label }
  };

  if (gift.mode === 'payment') {
    // Stripe's own wording: the checkout button reads "Donate", and a customer
    // record is kept so the gift shows against a person in the dashboard.
    params.submit_type = 'donate';
    params.customer_creation = 'always';
    params.payment_intent_data = { description: gift.label + ' \u2014 Gathered Pages Collective' };
  } else {
    params.subscription_data = { metadata: { gift: body.gift } };
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
