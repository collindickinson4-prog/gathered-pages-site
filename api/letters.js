// The newsletter archive — past letters, rendered from Kit.
//
// /newsletter is site/newsletter.html with the letter list dropped into its
// <!--LETTERS--> marker; /newsletter/<id>-<slug> renders one letter. Nothing is
// authored here and nothing is deployed when a letter goes out: Kit is the
// source, this reads it.
//
// A broadcast is public when Kit's `public` flag is true AND `status` is
// "completed" (observed on the first real send, 28 August 2026 — a draft
// reports "draft"). Both tests matter: the checkbox can be ticked on a draft.
//
// Because the index is the real newsletter.html, the signup form, the copy and
// the chrome stay ordinary HTML that anyone can edit. A single letter has no
// page of its own to borrow, so its chrome lives in site/letter-shell.html
// rather than becoming a fifteenth copy of the header and footer in
// JavaScript. vercel.json declares both files under includeFiles, because the
// paths are built at runtime and the bundler cannot trace them.

const fs = require('fs');
const path = require('path');

const API = 'https://api.kit.com/v4/broadcasts';

const CACHE = 'public, s-maxage=300, stale-while-revalidate=86400';

const BANNER = '<div class="pagehead__media">\n' +
  '    <img srcset="/assets/img/pressed-poppies-800.jpg 800w, /assets/img/pressed-poppies-1100.jpg 1100w, /assets/img/pressed-poppies.jpg 1600w" sizes="100vw" src="/assets/img/pressed-poppies.jpg" alt="An open herbarium album of pressed orange poppies and sage sprigs mounted on aged cream pages." style="object-position:40% 55%" fetchpriority="high" width="1600" height="1067">\n' +
  '  </div>';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

const files = {};

function file(name) {
  if (files[name] === undefined) {
    files[name] = fs.readFileSync(path.join(process.cwd(), 'site', name), 'utf8');
  }
  return files[name];
}

function esc(value) {
  return String(value === null || value === undefined ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function slugify(subject) {
  return String(subject || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'letter';
}

function readableDate(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  return d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
}

// Kit sends body-only HTML: paragraphs and links wrapped in layout tables,
// with its own <style> block. Keep the words, drop the email plumbing.
function clean(html) {
  let s = String(html || '');
  s = s.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, '');
  s = s.replace(/<img\b[^>]*>/gi, function (tag) {
    return /\b(?:width|height)\s*=\s*["']?1\b/i.test(tag) ? '' : tag;
  });
  s = s.replace(/\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '');
  s = s.replace(/<\/?(?:table|tbody|thead|tfoot|tr|td|th)\b[^>]*>/gi, '');
  // Kit pads the end of a letter with paragraphs of zero-width spaces and
  // line breaks; on the page they read as a hole, not as spacing.
  s = s.replace(/<p\b[^>]*>(?:\s|&nbsp;|&#8203;|\u200b|<br\s*\/?>)*<\/p>/gi, '');
  return s.trim();
}

// The newsletter page, with whatever belongs under "Read the letters".
function newsletterPage(inner) {
  return file('newsletter.html').replace('<!--LETTERS-->', function () { return inner; });
}

// One letter, in the shell that carries the site's chrome.
function letterPage(title, body) {
  return file('letter-shell.html')
    .replace('<!--BLOG_TITLE-->', function () { return esc(title) + ' &#183; Gathered Pages Collective'; })
    .replace('<!--BLOG_BODY-->', function () { return body; });
}

function pagehead(heading, lead) {
  return '<section class="pagehead">\n  ' + BANNER + '\n' +
    '  <div class="wrap">\n' +
    '    <div class="pagehead__inner">\n' +
    '      <p class="breadcrumb"><a href="/index.html">Home</a><span aria-hidden="true">/</span>' +
    '<a href="/newsletter">Newsletter</a></p>\n' +
    '      <h1>' + esc(heading) + '</h1>\n' +
    (lead ? '      <p class="pagehead__lead">' + esc(lead) + '</p>\n' : '') +
    '    </div>\n  </div>\n</section>\n';
}

function section(inner) {
  return '<section class="section">\n  <div class="wrap wrap--mid">\n' +
    inner + '\n  </div>\n</section>\n';
}

function letterList(letters) {
  if (letters.length === 0) {
    return '    <div class="notice mt-6" data-rise>\n' +
      '      <p><strong>The first letter is on its way.</strong></p>\n' +
      '      <p>Once it goes out it will live here, and every issue after it. Sign up above and you will get it the day it is sent.</p>\n' +
      '    </div>';
  }
  const rows = letters.map(function (letter) {
    return '        <div>\n' +
      '          <dt>' + esc(readableDate(letter.published_at)) + '</dt>\n' +
      '          <dd><a href="' + esc(letter.url) + '">' + esc(letter.subject) + '</a></dd>\n' +
      '        </div>';
  }).join('\n');
  return '    <dl class="ledger mt-6" data-rise>\n' + rows + '\n    </dl>';
}

function unavailableNotice() {
  return '    <div class="notice mt-6" data-rise>\n' +
    '      <p><strong>The letters are briefly unavailable.</strong></p>\n' +
    '      <p>Something on our side is not answering. Please try again in a few minutes.</p>\n' +
    '    </div>';
}

function issuePage(letter) {
  const when = readableDate(letter.published_at);
  return letterPage(letter.subject, pagehead(letter.subject, when) +
    section('    <div class="letter">\n' + clean(letter.content) + '\n    </div>\n' +
      '    <div class="mt-7">\n      <hr class="hairline">\n' +
      '      <p class="mt-4 text-soft measure">This letter went to subscribers on ' + esc(when) +
      '. <a href="/newsletter">Read the others and sign up</a> to get the next one by email.' +
      '</p>\n    </div>'));
}

function missingPage(heading, message) {
  return letterPage(heading, pagehead(heading, '') + section(
    '    <div class="notice">\n      <p>' + esc(message) + '</p>\n    </div>\n' +
    '    <p class="mt-6 text-soft measure"><a href="/newsletter">Back to the letters</a></p>'));
}

function issueUrl(broadcast) {
  return '/newsletter/' + broadcast.id + '-' + slugify(broadcast.subject);
}

function isPublished(broadcast) {
  return broadcast && broadcast.public === true && broadcast.status === 'completed';
}

async function kit(url, apiKey) {
  const response = await fetch(url, {
    headers: { 'X-Kit-Api-Key': apiKey, 'Accept': 'application/json' }
  });
  if (!response.ok) {
    const detail = await response.text();
    const error = new Error('Kit answered ' + response.status + ': ' + detail.slice(0, 300));
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function send(res, status, html, cacheable) {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', cacheable ? CACHE : 'no-store');
  return res.status(status).send(html);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.setHeader('Allow', 'GET, HEAD');
    return res.status(405).send('Method not allowed.');
  }

  const apiKey = process.env.KIT_API_KEY;
  if (!apiKey) {
    console.error('Kit credentials missing: set KIT_API_KEY.');
    return send(res, 503, newsletterPage(unavailableNotice()), false);
  }

  const slug = String((req.query && req.query.slug) || '');

  try {
    if (!slug) {
      const data = await kit(API + '?per_page=500', apiKey);
      const letters = (data.broadcasts || [])
        .filter(isPublished)
        .sort(function (a, b) { return new Date(b.published_at) - new Date(a.published_at); })
        .map(function (broadcast) {
          return {
            subject: broadcast.subject,
            published_at: broadcast.published_at,
            url: issueUrl(broadcast)
          };
        });
      return send(res, 200, newsletterPage(letterList(letters)), true);
    }

    // /newsletter/<id>-<slug>: the id is what resolves, the slug is decorative,
    // so a shared link survives Jamie editing a subject line after sending.
    const id = (slug.match(/^(\d+)/) || [])[1];
    if (!id) {
      return send(res, 404, missingPage('Letter not found', 'That letter does not exist. It may have been unpublished, or the link may be wrong.'), false);
    }

    const data = await kit(API + '/' + id, apiKey);
    const broadcast = data.broadcast;
    if (!isPublished(broadcast)) {
      return send(res, 404, missingPage('Letter not found', 'That letter does not exist. It may have been unpublished, or the link may be wrong.'), false);
    }

    return send(res, 200, issuePage(broadcast), true);
  } catch (error) {
    if (error && error.status === 404) {
      return send(res, 404, missingPage('Letter not found', 'That letter does not exist. It may have been unpublished, or the link may be wrong.'), false);
    }
    console.error('Kit request failed:', error);
    if (!slug) return send(res, 503, newsletterPage(unavailableNotice()), false);
    return send(res, 503, missingPage('Letter briefly unavailable', 'We could not reach our email service just now. Please try again in a few minutes.'), false);
  }
};
