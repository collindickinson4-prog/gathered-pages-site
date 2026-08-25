// Year-end giving statements.
//
//     node tools/giving_statements.js            the year that just ended
//     node tools/giving_statements.js 2026       a particular year
//
// A donor who gave $25 a month has twelve receipts and no acknowledgement of
// the $300 she actually gave. The IRS wants one written statement per donor
// per year for anyone at $250 or more, and every charity sends one to everyone
// in January because it is the kindest mail a donor gets all year.
//
// Reads every succeeded charge in the year from Stripe, subtracts refunds,
// groups by donor, and writes one print-ready statement per donor plus a CSV
// to check the totals against the books. Nothing is emailed: the files land in
// statements/<year>/ and Jamie sends them herself.
//
// Needs STRIPE_SECRET_KEY, from the environment or from .env in the project
// root. The output holds donor names, emails and amounts, so statements/ is
// gitignored - keep it off shared drives.

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
const PAGE_SIZE = 100;

// ---------------------------------------------------------------- helpers ---

function secretKey() {
  if (process.env.STRIPE_SECRET_KEY) return process.env.STRIPE_SECRET_KEY;
  const envPath = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envPath)) {
    const line = fs.readFileSync(envPath, 'utf8')
      .split(/\r?\n/)
      .find(function (l) { return l.trim().indexOf('STRIPE_SECRET_KEY=') === 0; });
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
  const year = Number(process.argv[2]) || (new Date().getFullYear() - 1);
  if (!(year > 2000 && year < 2200)) {
    console.error('Give a four-digit year, e.g. node tools/giving_statements.js 2026');
    process.exit(1);
  }

  const key = secretKey();
  if (!key) {
    console.error('No STRIPE_SECRET_KEY. Put it in .env or pass it in the environment.');
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
  let total = 0;

  donors.forEach(function (donor) {
    const file = fileNameFor(donor, year);
    fs.writeFileSync(path.join(outDir, file), renderStatement(donor, year), 'utf8');
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

  console.log('');
  console.log('  ' + donors.length + ' donors, ' + money(total) + ' in ' + year);
  console.log('  ' + over250 + ' at $250 or more (the ones the IRS requires this for)');
  console.log('  written to statements/' + year + '/');
  console.log('');
  console.log('Open any file in a browser and print to PDF to send it.');
}

module.exports = {
  groupCharges: groupCharges,
  renderStatement: renderStatement,
  fileNameFor: fileNameFor,
  ACKNOWLEDGEMENT: ACKNOWLEDGEMENT
};

if (require.main === module) {
  main().catch(function (error) {
    console.error('\n' + error.message);
    process.exit(1);
  });
}
