# Gathered Pages Collective — website

A fourteen-page static site for gatheredpages.org. No build step, no dependencies,
no framework. One page, /newsletter, is finished by a function that reads the
sent letters from Kit; the rest are plain HTML. Open `site/index.html` in a browser and it works. The pages under
`api/` are serverless functions Vercel runs; everything else is plain HTML.

```
site/                     ← this is the whole website. Upload this folder.
  index.html              Home
  about.html              About / our story / values / where we are today
  how-it-works.html       The convener's path, what we provide, FAQ
  the-box.html            What's in the box (interactive seed packets)
  founder.html            Meet Our Founder — Jamie's essay
  board.html              Meet The Board
  partner.html            Partner With Us + application form
  makers.html             Women-owned makers and bookshops
  donate.html             Ways to give + the Stripe giving panel
  thank-you.html          Where Stripe returns a donor after a gift
  newsletter.html         Newsletter signup, and the archive of sent letters.
                          Served at /newsletter by api/letters.js, which fills
                          its <!--LETTERS--> marker. Everything else on the page
                          is ordinary HTML; edit it as you would any other page.
  newsletter-thank-you.html  Where the signup form lands
  contact.html            Contact + form
  404.html                Not-found page
  letter-shell.html       Header, nav and footer for a single letter. Not a page:
                          api/letters.js fills its <!--BLOG_TITLE--> and
                          <!--BLOG_BODY--> markers.
  robots.txt, sitemap.xml
  assets/
    css/style.css         The whole design system, commented by section
    css/fonts.css         @font-face for the self-hosted fonts
    fonts/                Cormorant Garamond + Lato, .woff2, self-hosted
    js/main.js            Mobile nav, sticky masthead, packet toggles, reveals
    img/                  Logo, kit photography, generated botanical imagery

api/checkout.js           Creates a Stripe Checkout Session for a gift.
api/stripe-webhook.js     Records completed gifts.
api/contact.js            Emails the contact form to Jamie.
api/subscribe.js          Adds a newsletter signup to Kit.
api/letters.js            Renders /newsletter and /newsletter/<id>-<slug> from
                          Kit's broadcasts. A letter appears within about five
                          minutes of Jamie ticking "Add to your Newsletter site"
                          before sending. No deploy needed.

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

That server does not run the functions, so `/newsletter` and the forms are dead
under it. For those, `vercel dev` from the repo root, with the values from `.env`.

## Deploying

Upload the **contents of `site/`** to the web root. Nothing needs compiling.
It will work on GoDaddy hosting, Netlify, Cloudflare Pages, GitHub Pages, or
any static host.

If you use Netlify or Cloudflare Pages: no build command, publish directory
`site`.

## Editing content

Edit the HTML directly. The files are plain and readable, and each page owns
its own masthead and footer.

There used to be a generator, `tools/build_pages.py`, that rebuilt every page
from one Python file. It was removed once the pages had been hand-edited past
what it knew: it still held the pre-August copy and described the 501(c)(3) as
pending, so running it would have reverted the site and republished a false
tax claim. It is in the git history if it is ever wanted.

The cost of that choice is that shared chrome — the masthead, the footer, the
`<head>` — has to be changed in each page. `tools/check_site.py` catches a page
that lost a required piece of it.

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
  failures across every page, at desktop and at 320, 360 and 390px.
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
