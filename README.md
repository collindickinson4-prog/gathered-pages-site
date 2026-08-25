# Gathered Pages Collective — website

An eleven-page static site for gatheredpages.org. No build step, no dependencies,
no framework. Open `site/index.html` in a browser and it works.

```
site/                     ← this is the whole website. Upload this folder.
  index.html              Home
  about.html              About / our story / values / where we are today
  how-it-works.html       The convener's path, what we provide, FAQ
  the-box.html            What's in the box (interactive seed packets)
  founder.html            Meet Our Founder — Jamie's essay
  partner.html            Partner With Us + application form
  reading-list.html       The candidate reading list
  makers.html             Women-owned makers and bookshops
  donate.html             Ways to give
  contact.html            Contact + form
  404.html                Not-found page (hand-written, not generated)
  robots.txt, sitemap.xml
  assets/
    css/style.css         The whole design system, commented by section
    css/fonts.css         @font-face for the self-hosted fonts
    fonts/                Cormorant Garamond + Lato, .woff2, self-hosted
    js/main.js            Mobile nav, sticky masthead, packet toggles, reveals
    img/                  Logo, kit photography, generated botanical imagery

tools/build_pages.py      Optional. Regenerates the ten generated HTML files so the
                          masthead, footer and <head> stay identical across
                          them. You can ignore it and edit the HTML directly.
tools/check_site.py       Run this after any edit. See "Checking your work".
tools/giving_statements.js  Year-end giving statements. Each January:
                          node tools/giving_statements.js 2026
                          node tools/giving_statements.js 2026 --test=you@example.com
                          node tools/giving_statements.js 2026 --send

PRODUCT.md                Durable product truth: users, positioning, brand
                          commitments, legal status, and the list of facts
                          that must not be invented.
DESIGN.md                 The visual system, recorded from the built site.

source/                   The original shared folder, extracted. Read-only.
```

## Running it locally

```bash
cd site
python -m http.server 8000
# then open http://127.0.0.1:8000
```

Opening `index.html` directly with `file://` also works, but a local server is
closer to how it will behave when hosted.

## Deploying

Upload the **contents of `site/`** to the web root. Nothing needs compiling.
It will work on GoDaddy hosting, Netlify, Cloudflare Pages, GitHub Pages, or
any static host.

If you use Netlify or Cloudflare Pages: no build command, publish directory
`site`.

## Editing content

Two options, both fine:

1. **Edit the HTML directly.** The files are plain and readable. This is the
   right choice for a typo or a paragraph.
2. **Edit `tools/build_pages.py` and run `python tools/build_pages.py`.** All
   the page copy lives in that one file. This is the right choice for anything
   that touches the navigation, the footer, or several pages at once, because
   it guarantees they stay identical.

If you edit the HTML by hand and then run the generator, the generator wins and
your hand edits are lost. Pick one and stay with it. If you would rather never
think about this again, delete `tools/` — nothing at runtime uses it.

## Checking your work

```bash
python tools/check_site.py
```

Exits 0 if the site is sound, 1 if something is broken. It catches the things
that silently break a hand-edited static site: unclosed or mismatched tags,
dead links, anchors pointing at ids that don't exist, missing image files,
images without `alt` or without `width`/`height`, and pages that lost a
required piece of chrome such as the Donate button or the skip link.

Run it after every edit. If you edit HTML by hand, this is the only thing
standing between a stray `</div>` and a broken page.

## Things that are deliberately unfinished

Nothing on the site tells a visitor it is unfinished — every one of these works
today, just in a simpler way than it eventually should.

1. **Donation processor** — `donate.html`. The two giving buttons open an email
   to Jamie. Replace both `mailto:` links with a hosted donation URL once a
   processor is chosen. Givebutter and Zeffy both waive fees for nonprofits;
   Stripe and PayPal also work.
2. **Form delivery** — `partner.html` and `contact.html`. Both forms use
   `action="mailto:jamie@gatheredpages.org"`, which opens the visitor's email
   app with their answers filled in. That works, but it depends on them having
   a mail client set up, so a real form endpoint is better. Sign up for
   Formspree, Netlify Forms or Basin and replace the `action` on both forms.
   Each form already shows the email address as a visible fallback.
3. **Board biographies** — `about.html`. The board is listed by name only,
   because the drafted bios were not cleared for publication.
4. **Colorado charitable solicitation registration.** Most states, Colorado
   included, require a nonprofit to register with the Secretary of State before
   soliciting donations publicly. Worth confirming with Tiffany before the
   donate page goes live. This is a legal question, not a website one.
5. **One title to confirm.** Jamie's book list has an entry reading "Lade
   Tremaine" that could not be matched to a real title, so it was left off the
   reading list. Tell us what it was and it goes back on.

## Accessibility

The site targets WCAG 2.1 AA. Specifically:

- Body text is 17px minimum. Every text/background pair was measured in the
  rendered page at 4.5:1 (3:1 for large display type), and every input, select,
  textarea and button boundary at 3:1 for WCAG 1.4.11. Both audits return zero
  failures across all eleven pages, at desktop and at 320, 360 and 390px.
- Every page has exactly one `<h1>` and no skipped heading levels.
- Every non-logo image carries `srcset` with width steps from 480px to 2400px,
  so a phone downloads phone-sized files. Cold-cache mobile home page: about
  517 KB above the fold on a typical 2x phone, 738 KB on a 3x phone.
- Two colours are derived from the brand palette so white text on them passes:
  `--orange-action` `#C65225` for buttons and `--orange-ink` `#B04419` for small
  orange text on cream. Brand orange `#E15D2A` is still used at display sizes
  and for rules and numerals, where 3:1 applies. The same is true of
  `--sage-deep` `#63734E` as a surface colour under white text.
- Every interactive element has a visible focus ring.
- The mobile navigation and the seed-packet panels are real buttons with
  `aria-expanded` and `aria-controls`.
- The site is fully usable with JavaScript disabled: the reveal animations
  default to visible, and the navigation falls back to the always-expanded list.
- All motion is disabled under `prefers-reduced-motion: reduce`.

If you change a colour, check it. `webaim.org/resources/contrastchecker` is
the quickest way.

## Imagery

- The logo files came from the brand folder and are used unmodified. The site
  only uses `logo-white.png` and the two `icon-*.png` favicons;
  `logo-full.png`, `logo-navy.png`, `mark.png` and `kit-concept.jpg` are kept
  in the folder as web-ready brand assets for social posts and documents.
- The kit photography (`kit-*.jpg`) is cropped from `Kit Concept.png` in the
  shared folder — that is a mockup, not a photograph of a real box. Replace it
  with real photographs as soon as the first cartons are packed.
- The botanical plates and the still lifes (`hero-poppy-field.jpg`,
  `plate-poppy.jpg`, `circle-of-chairs.jpg`, `bookcloth-stack.jpg`,
  `reading-nook.jpg`, `makers-table.jpg`, `poppy-seeds.jpg`,
  `kraft-cartons.jpg`, `pressed-poppies.jpg`, `endpaper.jpg`) are generated,
  and contain no people by design. Swap in real photographs of real cartons and
  real rooms whenever you have them — they will always beat these.
