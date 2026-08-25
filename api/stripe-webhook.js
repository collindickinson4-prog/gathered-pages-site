// Stripe webhook — records completed gifts.
//
// Point a Stripe webhook endpoint at https://www.gatheredpages.org/api/stripe-webhook
// and subscribe it to checkout.session.completed.
//
// This deliberately does not trust the posted body. Vercel's Node runtime
// parses the request body before we see it, and Stripe's signature can only be
// checked against the exact raw bytes, so instead of half-checking a signature
// we take nothing from the request but the session ID and then read that
// session back from Stripe with our own secret key. Everything logged below
// therefore came from Stripe over an authenticated connection.
//
// The donor's receipt is sent by Stripe itself, not from here. Turn it on once
// in the dashboard: Settings -> Business -> Customer emails -> "Successful
// payments" (and "Subscription payments" for recurring gifts).

const SESSION_ENDPOINT = 'https://api.stripe.com/v1/checkout/sessions/';

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

  const secretKey = process.env.STRIPE_SECRET_KEY;
  if (!secretKey) {
    console.error('Stripe credentials missing: set STRIPE_SECRET_KEY.');
    return res.status(500).json({ received: false });
  }

  const event = readBody(req);

  // Stripe retries anything that is not a 2xx, so acknowledge the events we do
  // not act on rather than failing them.
  if (event.type !== 'checkout.session.completed') {
    return res.status(200).json({ received: true, ignored: event.type || null });
  }

  const sessionId = String((event.data && event.data.object && event.data.object.id) || '');
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId)) {
    console.error('checkout.session.completed arrived without a usable session ID.');
    return res.status(200).json({ received: true });
  }

  try {
    const response = await fetch(SESSION_ENDPOINT + sessionId + '?expand[]=line_items', {
      headers: { 'Authorization': 'Bearer ' + secretKey }
    });
    const session = await response.json().catch(function () { return {}; });

    if (!response.ok) {
      console.error('Could not read session %s back from Stripe:', sessionId, response.status);
      return res.status(200).json({ received: true });
    }

    if (session.payment_status !== 'paid' && session.status !== 'complete') {
      console.log('Gift session %s completed without payment (%s).', sessionId, session.payment_status);
      return res.status(200).json({ received: true });
    }

    const details = session.customer_details || {};
    const metadata = session.metadata || {};
    const amount = ((session.amount_total || 0) / 100).toFixed(2);

    console.log(
      'Gift received: %s %s %s from %s (%s) — session %s',
      amount,
      String(session.currency || 'usd').toUpperCase(),
      metadata.gift_label || metadata.gift || session.mode,
      details.name || 'name not given',
      details.email || 'email not given',
      sessionId
    );

    return res.status(200).json({ received: true });
  } catch (error) {
    console.error('Stripe request failed:', error);
    return res.status(200).json({ received: true });
  }
};
