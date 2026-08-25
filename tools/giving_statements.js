// Year-end giving statements.
//
//     node tools/giving_statements.js                 the year that just ended
//     node tools/giving_statements.js 2026            a particular year
//     node tools/giving_statements.js 2026 --test=me@example.com
//     node tools/giving_statements.js 2026 --send     email every donor
//
// A donor who gave $25 a month has twelve receipts and no acknowledgement of
// the $300 she actually gave. The IRS wants one written statement per donor
// per year for anyone at $250 or more, and every charity sends one to everyone
// in January because it is the kindest mail a donor gets all year.
//
// Reads every succeeded charge in the year from Stripe, subtracts refunds,
// groups by donor, and writes one print-ready statement per donor plus a CSV
// to check the totals against the books. The files land in statements/<year>/.
//
// Sending is a separate, deliberate second run. Look at the numbers first:
// these letters go to real donors and a wrong total is worse than a late one.
// --test sends one real donor's statement to an address of your choosing so
// you can see what lands. --send then mails everyone, recording each address
// in sent.csv as it goes, so a re-run after a failure picks up where it
// stopped instead of mailing anyone twice.
//
// Needs STRIPE_SECRET_KEY, and for sending RESEND_API_KEY and RESEND_FROM,
// from the environment or from .env in the project root. The output holds
// donor names, emails and amounts, so statements/ is gitignored - keep it off
// shared drives.

const fs = require('fs');
const path = require('path');

const ORG = {
  name: 'Gathered Pages Collective',
  address: ['4939 Silver Feather Circle', 'Broomfield, Colorado 80023'],
  ein: '42-3092238',
  email: 'jamie@gatheredpages.org',
  site: 'gatheredpages.org',
  signer: 'Jamie Dickinson',
  signerTitle: 'Founder'
};

// The sentence that makes a gift substantiable. Same wording as the receipts.
const ACKNOWLEDGEMENT =
  'No goods or services were provided in exchange for these contributions. ' +
  ORG.name + ' is a 501(c)(3) tax-exempt organization, EIN ' + ORG.ein + '. ' +
  'Your gifts are tax-deductible to the extent allowed by law.';

const CHARGES_ENDPOINT = 'https://api.stripe.com/v1/charges';
const EMAIL_ENDPOINT = 'https://api.resend.com/emails';
const PAGE_SIZE = 100;

// Resend allows a couple of requests a second on the free plan. A pause
// between letters keeps a hundred donors from tripping the rate limit.
const SEND_PAUSE_MS = 600;

// ---------------------------------------------------------------- helpers ---

// Environment first, then .env in the project root, so the same command works
// on Jamie's machine and in a shell that already has the key exported.
function setting(name) {
  if (process.env[name]) return process.env[name];
  const envPath = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envPath)) {
    const line = fs.readFileSync(envPath, 'utf8')
      .split(/\r?\n/)
      .find(function (l) { return l.trim().indexOf(name + '=') === 0; });
    if (line) return line.split('=').slice(1).join('=').trim().replace(/^["']|["']$/g, '');
  }
  return '';
}

function money(cents) {
  return '$' + (cents / 100).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function dayOf(seconds) {
  const d = new Date(seconds * 1000);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'America/Denver' });
}

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function csvCell(value) {
  const text = String(value == null ? '' : value);
  return /[",\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
}

// A donor is one email address. Stripe keeps the address on the charge itself,
// which survives even when the customer record is later edited or deleted.
function donorKey(charge) {
  const details = charge.billing_details || {};
  const customer = (charge.customer && typeof charge.customer === 'object') ? charge.customer : {};
  const email = (details.email || customer.email || '').trim().toLowerCase();
  return email || ('stripe:' + (charge.customer && charge.customer.id ? charge.customer.id : charge.id));
}

function donorName(charge) {
  const details = charge.billing_details || {};
  const customer = (charge.customer && typeof charge.customer === 'object') ? charge.customer : {};
  return (details.name || customer.name || '').trim();
}

// --------------------------------------------------------------- grouping ---

// Exported so the shape of this can be checked without calling Stripe.
function groupCharges(charges) {
  const donors = new Map();

  charges.forEach(function (charge) {
    if (charge.status !== 'succeeded' || !charge.paid) return;

    // A refunded gift was not a gift. A partly refunded one counts for what
    // the donor actually parted with.
    const net = charge.amount - (charge.amount_refunded || 0);
    if (net <= 0) return;

    const key = donorKey(charge);
    if (!donors.has(key)) {
      donors.set(key, {
        key: key,
        email: key.indexOf('stripe:') === 0 ? '' : key,
        name: donorName(charge),
        gifts: [],
        total: 0
      });
    }

    const donor = donors.get(key);
    if (!donor.name) donor.name = donorName(charge);
    donor.gifts.push({
      date: charge.created,
      amount: net,
      recurring: Boolean(charge.invoice),
      refunded: (charge.amount_refunded || 0) > 0
    });
    donor.total += net;
  });

  const list = Array.from(donors.values());
  list.forEach(function (donor) { donor.gifts.sort(function (a, b) { return a.date - b.date; }); });
  list.sort(function (a, b) { return b.total - a.total; });
  return list;
}

// -------------------------------------------------------------- rendering ---

function renderStatement(donor, year) {
  const rows = donor.gifts.map(function (gift) {
    return '        <tr><td>' + dayOf(gift.date) + '</td><td>' +
      (gift.recurring ? 'Recurring gift' : 'One-time gift') +
      (gift.refunded ? ' (net of refund)' : '') +
      '</td><td class="amount">' + money(gift.amount) + '</td></tr>';
  }).join('\n');

  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<title>' + escapeHtml(year) + ' giving statement &#183; ' + escapeHtml(donor.name || donor.email) + '</title>',
    '<style>',
    '  @page { margin: 0.9in; }',
    '  * { box-sizing: border-box; }',
    '  body {',
    '    margin: 0; padding: 2.5rem;',
    '    font: 11pt/1.6 "Lato", "Helvetica Neue", Helvetica, Arial, sans-serif;',
    '    color: #23272e; background: #fff; max-width: 7.2in;',
    '  }',
    '  h1 { font-family: "Cormorant Garamond", Garamond, "Times New Roman", serif;',
    '       font-size: 26pt; font-weight: 500; letter-spacing: -0.01em; margin: 0 0 0.35rem; }',
    '  .org { font-size: 9.5pt; line-height: 1.5; color: #3f4a5c; }',
    '  .org strong { display: block; font-size: 11pt; color: #16294d; letter-spacing: 0.02em; }',
    '  .rule { border: 0; border-top: 2px solid #16294d; margin: 1.5rem 0; }',
    '  .hair { border: 0; border-top: 1px solid rgba(22,41,77,0.2); margin: 1.25rem 0; }',
    '  .to { margin: 1.5rem 0 0.25rem; font-size: 11pt; }',
    '  .to strong { font-size: 12pt; }',
    '  .lead { margin: 1.25rem 0; }',
    '  table { width: 100%; border-collapse: collapse; margin: 1rem 0 0; }',
    '  th { text-align: left; font-size: 8.5pt; letter-spacing: 0.13em; text-transform: uppercase;',
    '       color: #3f4a5c; border-bottom: 1px solid rgba(22,41,77,0.35); padding: 0 0 0.4rem; }',
    '  td { padding: 0.5rem 0; border-bottom: 1px solid rgba(22,41,77,0.12); vertical-align: top; }',
    '  .amount { text-align: right; white-space: nowrap; }',
    '  tfoot td { border-bottom: 0; border-top: 2px solid #16294d; font-weight: 700; font-size: 12pt; padding-top: 0.6rem; }',
    '  .ack { margin: 1.5rem 0 0; padding: 0.9rem 1.1rem; background: #f5f1e8;',
    '         border-left: 3px solid #c65225; font-size: 10pt; line-height: 1.55; }',
    '  .close { margin-top: 2rem; }',
    '  .sign { margin-top: 2.25rem; font-size: 10.5pt; }',
    '  .sign strong { display: block; }',
    '  .sign span { color: #3f4a5c; }',
    '</style>',
    '</head>',
    '<body>',
    '  <div class="org">',
    '    <strong>' + escapeHtml(ORG.name) + '</strong>',
    '    ' + ORG.address.map(escapeHtml).join('<br>') + '<br>',
    '    ' + escapeHtml(ORG.email) + ' &#183; ' + escapeHtml(ORG.site) + '<br>',
    '    EIN ' + escapeHtml(ORG.ein),
    '  </div>',
    '',
    '  <hr class="rule">',
    '',
    '  <h1>' + escapeHtml(year) + ' Giving Statement</h1>',
    '',
    '  <p class="to"><strong>' + escapeHtml(donor.name || 'Friend of Gathered Pages') + '</strong><br>',
    '  ' + escapeHtml(donor.email) + '</p>',
    '',
    '  <hr class="hair">',
    '',
    '  <p class="lead">Thank you for what you gave in ' + escapeHtml(year) + '. Below is the record of',
    '  your gifts, for your files and for your taxes. Every dollar of it went where you meant it to go',
    '  &#8212; into books, journals and pens bought from women-owned makers, and into the boxes that',
    '  carry them to women who needed a room to sit down in.</p>',
    '',
    '  <table>',
    '    <thead>',
    '      <tr><th>Date</th><th>Gift</th><th class="amount">Amount</th></tr>',
    '    </thead>',
    '    <tbody>',
    rows,
    '    </tbody>',
    '    <tfoot>',
    '      <tr><td colspan="2">Total contributions in ' + escapeHtml(year) + '</td><td class="amount">' + money(donor.total) + '</td></tr>',
    '    </tfoot>',
    '  </table>',
    '',
    '  <p class="ack">' + escapeHtml(ACKNOWLEDGEMENT) + '</p>',
    '',
    '  <p class="close">If anything here looks wrong, write to me directly and I will fix it the same week.</p>',
    '',
    '  <p class="sign">',
    '    With gratitude,<br><br>',
    '    <strong>' + escapeHtml(ORG.signer) + '</strong>',
    '    <span>' + escapeHtml(ORG.signerTitle) + ', ' + escapeHtml(ORG.name) + '</span>',
    '  </p>',
    '</body>',
    '</html>',
    ''
  ].join('\n');
}

function fileNameFor(donor, year) {
  const base = (donor.name || donor.email || donor.key)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'donor';
  return year + '-' + base + '.html';
}

// -------------------------------------------------------------- the post ---

function subjectFor(year) {
  return 'Your ' + year + ' giving statement — ' + ORG.name;
}

// One letter, through Resend. Returns the provider's message id so sent.csv
// records something that can be looked up later.
async function sendStatement(key, from, to, year, html) {
  const response = await fetch(EMAIL_ENDPOINT, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + key,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: from,
      to: [to],
      reply_to: ORG.email,
      subject: subjectFor(year),
      html: html
    })
  });

  const body = await response.json().catch(function () { return {}; });
  if (!response.ok) {
    throw new Error(response.status + ' ' + JSON.stringify(body.message || body.error || body).slice(0, 200));
  }
  return body.id || '';
}

// Who has already been written to this year. A crash halfway through a
// hundred donors must not mean a hundred people get a second letter.
function readSent(dir) {
  const file = path.join(dir, 'sent.csv');
  if (!fs.existsSync(file)) return new Set();
  return new Set(
    fs.readFileSync(file, 'utf8')
      .split(/\r?\n/)
      .slice(1)
      .map(function (line) { return line.split(',')[0].trim().toLowerCase(); })
      .filter(Boolean)
  );
}

function recordSent(dir, email, id) {
  const file = path.join(dir, 'sent.csv');
  if (!fs.existsSync(file)) fs.writeFileSync(file, 'Email,Sent,Message ID\n', 'utf8');
  fs.appendFileSync(file, [email, new Date().toISOString(), id].map(csvCell).join(',') + '\n', 'utf8');
}

function pause(ms) {
  return new Promise(function (resolve) { setTimeout(resolve, ms); });
}

// ----------------------------------------------------------------- stripe ---

async function fetchCharges(key, year) {
  const from = Math.floor(Date.UTC(year, 0, 1) / 1000);
  const to = Math.floor(Date.UTC(year + 1, 0, 1) / 1000) - 1;

  const charges = [];
  let startingAfter = null;

  for (;;) {
    const query = [
      'created[gte]=' + from,
      'created[lte]=' + to,
      'limit=' + PAGE_SIZE,
      'expand[]=data.customer'
    ];
    if (startingAfter) query.push('starting_after=' + startingAfter);

    const response = await fetch(CHARGES_ENDPOINT + '?' + query.join('&'), {
      headers: { 'Authorization': 'Bearer ' + key }
    });
    const page = await response.json();

    if (!response.ok) {
      throw new Error('Stripe said ' + response.status + ': ' + JSON.stringify(page.error || page).slice(0, 300));
    }

    charges.push.apply(charges, page.data);
    process.stdout.write('  read ' + charges.length + ' charges\r');

    if (!page.has_more || !page.data.length) break;
    startingAfter = page.data[page.data.length - 1].id;
  }

  process.stdout.write('\n');
  return charges;
}

// ------------------------------------------------------------------- main ---

async function main() {
  const args = process.argv.slice(2);
  const send = args.indexOf('--send') !== -1;
  const testArg = args.find(function (a) { return a.indexOf('--test=') === 0; });
  const testTo = testArg ? testArg.slice('--test='.length).trim() : '';
  const yearArg = args.find(function (a) { return a.indexOf('--') !== 0; });

  const year = Number(yearArg) || (new Date().getFullYear() - 1);
  if (!(year > 2000 && year < 2200)) {
    console.error('Give a four-digit year, e.g. node tools/giving_statements.js 2026');
    process.exit(1);
  }

  const key = setting('STRIPE_SECRET_KEY');
  if (!key) {
    console.error('No STRIPE_SECRET_KEY. Put it in .env or pass it in the environment.');
    process.exit(1);
  }

  // Fail before reading a year of charges rather than after.
  const mailKey = (send || testTo) ? setting('RESEND_API_KEY') : '';
  const mailFrom = (send || testTo) ? setting('RESEND_FROM') : '';
  if ((send || testTo) && (!mailKey || !mailFrom)) {
    console.error('Sending needs RESEND_API_KEY and RESEND_FROM in .env.');
    console.error('RESEND_FROM looks like: Gathered Pages Collective <jamie@send.gatheredpages.org>');
    process.exit(1);
  }
  if (key.indexOf('sk_test') === 0) {
    console.log('Note: this is a test-mode key, so these are test-mode gifts.\n');
  }

  console.log('Reading ' + year + ' charges from Stripe...');
  const charges = await fetchCharges(key, year);
  const donors = groupCharges(charges);

  if (!donors.length) {
    console.log('No gifts found in ' + year + '. Nothing written.');
    return;
  }

  const outDir = path.join(__dirname, '..', 'statements', String(year));
  fs.mkdirSync(outDir, { recursive: true });

  const index = [['Name', 'Email', 'Gifts', 'Total', 'Needs acknowledgement', 'File']];
  const letters = new Map();
  let total = 0;

  donors.forEach(function (donor) {
    const file = fileNameFor(donor, year);
    const html = renderStatement(donor, year);
    fs.writeFileSync(path.join(outDir, file), html, 'utf8');
    letters.set(donor.key, html);
    total += donor.total;
    index.push([
      donor.name,
      donor.email,
      donor.gifts.length,
      (donor.total / 100).toFixed(2),
      donor.total >= 25000 ? 'yes' : '',
      file
    ]);
  });

  fs.writeFileSync(
    path.join(outDir, 'index.csv'),
    index.map(function (row) { return row.map(csvCell).join(','); }).join('\n') + '\n',
    'utf8'
  );

  const over250 = donors.filter(function (d) { return d.total >= 25000; }).length;
  const reachable = donors.filter(function (d) { return d.email; });
  const unreachable = donors.filter(function (d) { return !d.email; });

  console.log('');
  console.log('  ' + donors.length + ' donors, ' + money(total) + ' in ' + year);
  console.log('  ' + over250 + ' at $250 or more (the ones the IRS requires this for)');
  console.log('  written to statements/' + year + '/');

  // One letter to an address of your choosing, so you see what a donor sees
  // before any donor sees it.
  if (testTo) {
    const sample = reachable[0] || donors[0];
    console.log('');
    console.log('Sending ' + (sample.name || sample.email || 'a sample') + '’s statement to ' + testTo + '...');
    const id = await sendStatement(mailKey, mailFrom, testTo, year, letters.get(sample.key));
    console.log('  sent' + (id ? ' (' + id + ')' : ''));
    console.log('');
    console.log('Look at it. If it reads right, run the same command with --send.');
    return;
  }

  if (!send) {
    console.log('');
    console.log('Nothing has been emailed. Check the totals in index.csv, then:');
    console.log('  node tools/giving_statements.js ' + year + ' --test=you@example.com');
    console.log('  node tools/giving_statements.js ' + year + ' --send');
    return;
  }

  const already = readSent(outDir);
  const queue = reachable.filter(function (d) { return !already.has(d.email); });

  console.log('');
  if (already.size) console.log('  ' + already.size + ' already written to earlier - skipping those');
  console.log('Emailing ' + queue.length + ' donors...');
  console.log('');

  let sent = 0;
  const failed = [];

  for (const donor of queue) {
    try {
      const id = await sendStatement(mailKey, mailFrom, donor.email, year, letters.get(donor.key));
      recordSent(outDir, donor.email, id);
      sent += 1;
      console.log('  ✓ ' + donor.email + '  ' + money(donor.total));
    } catch (error) {
      failed.push({ email: donor.email, why: error.message });
      console.log('  ✗ ' + donor.email + '  ' + error.message);
    }
    await pause(SEND_PAUSE_MS);
  }

  console.log('');
  console.log('  ' + sent + ' sent, ' + failed.length + ' failed');
  if (failed.length) {
    console.log('  Run the same command again - the ones that went out are recorded in');
    console.log('  sent.csv and will be skipped.');
  }
  if (unreachable.length) {
    console.log('');
    console.log('  ' + unreachable.length + ' donors have no email address on file. Their statements are');
    console.log('  in statements/' + year + '/ - print those and post them.');
  }
}

module.exports = {
  groupCharges: groupCharges,
  renderStatement: renderStatement,
  fileNameFor: fileNameFor,
  sendStatement: sendStatement,
  readSent: readSent,
  recordSent: recordSent,
  subjectFor: subjectFor,
  ACKNOWLEDGEMENT: ACKNOWLEDGEMENT
};

if (require.main === module) {
  main().catch(function (error) {
    console.error('\n' + error.message);
    process.exit(1);
  });
}
