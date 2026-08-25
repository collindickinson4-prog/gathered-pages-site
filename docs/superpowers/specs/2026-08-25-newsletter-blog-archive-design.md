# Newsletter blog archive

Design, 2026-08-25.

## The problem

Issues of *The Monthly Gathering* exist only in Kit and in subscribers'
inboxes. `newsletter.html` carries a placeholder promising an archive — *"Once
it goes out it will live here"* — that nothing fulfils. Someone who arrives at
the site cannot read a single letter, and Jamie has no way to link to one.

## Goals

A public archive at `/blog`, in the site's own design, that fills itself when
Jamie sends an issue. One extra decision per send, no code, no deploy.

## Non-goals

Comments, categories, tags, search, pagination, RSS. Authoring on the site —
Kit stays the place letters are written. Backfilling issues sent before this
ships; there are none.

## Decisions

| Decision | Choice | Who |
|---|---|---|
| What appears publicly | Only broadcasts where Kit's `public` flag is true, set by the **Add to your Newsletter site** checkbox on the send screen | Collin |
| Section name | "Blog", despite the site's voice calling them letters everywhere else | Collin |
| How pages are produced | Serverless rendering from the Kit API, edge-cached | Collin |
| Nav placement | Main nav, after What's In The Box | Collin |
| Index rows | Date and subject only | Collin |

The name is worth restating because it is a deliberate departure: every other
surface — `newsletter.html`, the email footer, the welcome letter — says
*letters*. "Blog" appears only in navigation and page headings, so reversing it
later is a find-and-replace, not a rebuild.

## Architecture

### Routing

`vercel.json` rewrites `/blog` and `/blog/:slug` to a single function,
`api/blog.js`. `trailingSlash` is already false, so no redirect dance.

Issue URLs are `/blog/<id>-<slug>`: the Kit broadcast id followed by a slug
derived from the subject. The id is what the function resolves; the slug is
decorative. This means a URL survives Jamie editing a subject line after
sending, so a link shared anywhere keeps working.

### Page shell

Header, nav and footer are duplicated across all 14 static pages. The function
must not become a fifteenth copy in JavaScript, where nobody maintaining this
site would think to look.

`site/blog-shell.html` holds the real chrome — including "Blog" in the nav,
since it is a fifteenth copy of that markup — with two markers,
`<!--BLOG_TITLE-->` and `<!--BLOG_BODY-->`. The function reads it once per cold
start and substitutes. `vercel.json` declares it explicitly so the bundler
includes it:

```json
"functions": { "api/blog.js": { "includeFiles": "site/blog-shell.html" } }
```

Without `includeFiles` the file is not traced into the function bundle, because
the path is built at runtime. This is the single most likely thing to fail
first, and the implementation plan proves it before anything else is built.

### Data

`GET https://api.kit.com/v4/broadcasts`, authenticated with `KIT_API_KEY`
(already set in all three Vercel environments). Kept if `public` is true **and**
the broadcast has been sent. Sorted by `published_at`, newest first. Only
`id`, `subject`, `published_at` and `content` are read. `preview_text` and
`thumbnail_url` are deliberately ignored, because the index shows date and
subject only.

The sent-state test is deliberately unspecified here. No broadcast has ever been
sent from this account, so the value of `status` on a completed broadcast has
not been observed. Guessing it would put an unverified assumption at the centre
of the filter. It gets pinned against Jamie's first real send.

### Cleaning Kit's HTML

`content` arrives as body-only HTML — no unsubscribe link, no footer, no email
chrome — containing `p`, `a`, `em`, `strong`, Kit's layout tables, and a
`<style data-no-inline>` block.

Before rendering: drop `<style>` and `<script>` elements, `on*` attributes and
tracking pixels; unwrap the layout tables; keep the content tags. The result
goes in a `.letter` container and inherits the site stylesheet, so a letter on
the site reads as part of the site rather than an email pasted into a page.

Jamie is a trusted author, so removing scripts is about presentation more than
defence. It is nearly free, so it happens regardless.

### Caching and failure

`Cache-Control: public, s-maxage=300, stale-while-revalidate=86400`. An issue
appears within about five minutes of the box being ticked, and Vercel serves the
last good copy for a day if Kit stops answering.

The only real failure is a cold cache during a Kit outage. Then `/blog` renders
the shell with a short notice that the letters are briefly unavailable, plus the
signup link; an issue URL returns 503 in the same shell. An unknown id returns
404 in the same shell. No stack trace ever reaches a visitor, and the function
logs the underlying error for us.

### Site changes

"Blog" is added to the main nav on all 14 pages by script, after What's In The
Box. The *"The first letter is on its way"* notice on `newsletter.html` becomes
a link across to `/blog`. `/blog` joins `sitemap.xml`; individual issues do not,
since the set changes without a deploy.

## Files

| File | Change |
|---|---|
| `api/blog.js` | New. Fetch, filter, sanitize, render. |
| `site/blog-shell.html` | New. Chrome plus two markers. |
| `vercel.json` | Rewrites and `includeFiles`. |
| `site/*.html` (14) | "Blog" in the main nav. |
| `site/newsletter.html` | Placeholder becomes a link. |
| `site/sitemap.xml` | Add `/blog`. |
| `site/assets/css/style.css` | `.letter` rules for archive content. |

## Unverified assumptions

1. **The sent-broadcast shape.** Only a draft has been observed. `status` and
   `public` on a completed broadcast are unconfirmed.
2. **`includeFiles` behaviour** on this project's `outputDirectory: site` layout.
3. **Kit API rate limits** on the free Newsletter plan. Edge caching should keep
   requests to roughly one per five minutes, but the ceiling is unknown.

Each is proven or corrected during implementation, not assumed away.

## Verification

Local: run the function against the existing draft with the sent filter relaxed,
confirming fetch, sanitize and render.

Production, after deploy: `/blog` returns 200 and lists nothing, because nothing
is public yet. Then Jamie sends her first issue with the box ticked, and the
same URL lists it, its own URL renders it, and the rendered content matches what
subscribers received.

The feature is not "done" until that last check passes against a real send.
