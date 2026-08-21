# -*- coding: utf-8 -*-
"""
Gathered Pages Collective — page generator.

The shipped website in ../site is plain, dependency-free HTML. This script
exists only so the masthead, footer and <head> stay byte-identical across all
ten pages. Edit the content here, run `python tools/build_pages.py`, and the
HTML files are rewritten.

You can also just edit the .html files directly — nothing at runtime depends
on this script. If you do, either keep this file in sync or delete it.
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

SITE_URL = "https://www.gatheredpages.org"
EMAIL = "jamie@gatheredpages.org"
INSTAGRAM = "https://www.instagram.com/gatheredpagescollective/"

# --------------------------------------------------------------------------
# Authored icon set — one stroke weight (1.4), round caps, 24px box.
# --------------------------------------------------------------------------

ICONS = {
    "arrow": '<path d="M4 12h15m0 0-5.5-5.5M19 12l-5.5 5.5"/>',
    "book": '<path d="M12 6.8C10.4 5.4 8.4 4.7 5.6 4.7c-.7 0-1.1.4-1.1 1v11.5c0 .6.4 1 1.1 1 2.8 0 4.8.7 6.4 2.1 1.6-1.4 3.6-2.1 6.4-2.1.7 0 1.1-.4 1.1-1V5.7c0-.6-.4-1-1.1-1-2.8 0-4.8.7-6.4 2.1Zm0 0v13.5"/>',
    "journal": '<path d="M7.5 3.5h11a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1h-11m0-17a3 3 0 0 0 0 6h1m-1-6v17m0 0a3 3 0 0 1 0-6h1m4-5.5h4"/>',
    "pen": '<path d="m5 19 1-4L16.4 4.6a1.9 1.9 0 0 1 2.7 0l.3.3a1.9 1.9 0 0 1 0 2.7L9 18l-4 1Zm10.6-13.2 2.6 2.6"/>',
    "card": '<path d="M4.2 4.5h15.6a.7.7 0 0 1 .7.7v13.6a.7.7 0 0 1-.7.7H4.2a.7.7 0 0 1-.7-.7V5.2a.7.7 0 0 1 .7-.7Z"/><path d="M12 16.6v-3.3"/><path d="M12 13.3a2.9 2.9 0 1 1 0-5.8 2.9 2.9 0 0 1 0 5.8Z"/>',
    "guide": '<path d="M6 3.5h9.5L20 8v12.5H6zm9.5 0V8H20M9 12h8m-8 3.5h8m-8-7h3"/>',
    "sprig": '<path d="M12 21V7m0 0c0-2 1.4-3.5 3.5-4 .3 2.4-1 4-3.5 4Zm0 3.5c-2.5 0-3.8-1.6-3.5-4C10.6 7 12 8.5 12 10.5Zm0 4.5c2.5 0 3.8-1.6 3.5-4-2.1.5-3.5 2-3.5 4Z"/>',
    "poppy": '<path d="M12 21v-8m0 0c-2.3 0-4-1.6-4-3.6C8 7 9.8 5 12 3c2.2 2 4 4 4 6.4 0 2-1.7 3.6-4 3.6Zm0 3c-1.6-.8-3.2-.7-4.4.3m4.4 1.4c1.6-.8 3.2-.7 4.4.3"/>',
    "envelope": '<path d="M3.5 7.5h17v11h-17zm0 0 8.5 6 8.5-6"/>',
    "seed": '<path d="M12 3.5c3 2.4 4.5 5 4.5 7.8A4.5 4.5 0 0 1 12 15.8a4.5 4.5 0 0 1-4.5-4.5C7.5 8.5 9 5.9 12 3.5Zm0 12.3V20.5"/>',
    "hands": '<path d="M4 12.5v4a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4v-4m-16 0 3-3m13 3-3-3m-10-6v6m4-8v8m4-6v6"/>',
}


def icon(name, cls="", size=None):
    body = ICONS[name]
    attrs = ' class="%s"' % cls if cls else ""
    style = ' width="%s" height="%s"' % (size, size) if size else ""
    return (
        '<svg%s%s viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">%s</svg>' % (attrs, style, body)
    )


ARROW = icon("arrow")

# --------------------------------------------------------------------------
# Shared chrome
# --------------------------------------------------------------------------

PRIMARY_NAV = [
    ("about.html", "About"),
    ("how-it-works.html", "How It Works"),
    ("the-box.html", "What&#8217;s In The Box"),
    ("reading-list.html", "Reading List"),
    ("partner.html", "Partner With Us"),
]

UTILITY_NAV = [
    ("founder.html", "Meet Our Founder"),
    ("makers.html", "Our Makers"),
    ("contact.html", "Contact"),
]

MOBILE_ONLY_NAV = UTILITY_NAV


def head(page):
    title = page["title"]
    full_title = title if page["slug"] == "index" else "%s &#183; Gathered Pages Collective" % title
    if page["slug"] == "index":
        full_title = "Gathered Pages Collective &#183; Book clubs for women who need them"
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}/{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Gathered Pages Collective">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/{canon}">
<meta property="og:image" content="{site}/assets/img/og-card.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#16294D">
<link rel="icon" href="assets/img/icon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="assets/img/icon-180.png">
<link rel="preload" as="font" type="font/woff2" href="assets/fonts/CormorantGaramond-500-latin.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="assets/fonts/Lato-400-latin.woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<!--
  DIRECTION CONTRACT — Gathered Pages Collective
  THESIS: A book club you can order, that arrives in a box. Built as an
    illustrated seed catalog, refusing the cream-ground charity landing page
    with soft photographs of hands holding books.
  OWN-WORLD: Deep navy lithographic ground carrying cream specimen plates;
    poppy orange as the bloom, sage as foliage, kraft as paper stock. Hairline
    rules, dot leaders, ruled ledger rows, double-ruled plate frames,
    decimal-leading-zero sowing steps, tracked Lato column heads over
    Cormorant Garamond display.
  STORY: A convener learns in one viewport that a complete book club arrives
    free and she only has to gather the women; a donor sees exactly what a
    gift buys; both reach an orange action that never leaves the screen.
  FIRST VIEWPORT: Full-bleed navy poppy plate, display headline bottom-left at
    up to 6rem, lead beneath, orange Donate Now beside an outlined partner
    action, sticky masthead carrying the same orange button.
  FORM: Illustrated seed catalog — candidate 4 of the grounded list; seed
    key ed6a03ae.
  FINISH: unreviewed and undocumented is unfinished; this build ends with the
    finish review, the verdict, and DESIGN.md
-->
<a class="skip" href="#main">Skip to content</a>
""".format(
        full_title=full_title,
        desc=page["desc"],
        site=SITE_URL,
        canon="" if page["slug"] == "index" else page["slug"] + ".html",
        ogtitle=title if page["slug"] != "index" else "Gathered Pages Collective",
    )


def masthead(slug):
    def link(href, label, current):
        aria = ' aria-current="page"' if current else ""
        return '<a href="%s"%s>%s</a>' % (href, aria, label)

    util = "\n        ".join(
        link(h, l, slug == h.replace(".html", "")) for h, l in UTILITY_NAV
    )
    primary = "\n        ".join(
        link(h, l, slug == h.replace(".html", "")) for h, l in PRIMARY_NAV
    )
    mobile_extra = "\n        ".join(
        '<a href="%s" class="nav-mobile-only"%s>%s</a>'
        % (h, ' aria-current="page"' if slug == h.replace(".html", "") else "", l)
        for h, l in MOBILE_ONLY_NAV
    )

    return """<div class="utility-strip">
  <div class="wrap utility-strip__inner">
    <nav class="utility-nav" aria-label="Secondary">
        {util}
    </nav>
  </div>
</div>

<header class="masthead">
  <div class="wrap masthead__inner">
    <a class="brand" href="index.html">
      <img src="assets/img/logo-white.png" width="400" height="312" alt="Gathered Pages Collective &#8212; home">
    </a>

    <nav class="primary-nav" id="site-nav" aria-label="Primary">
        {primary}
        {mobile_extra}
    </nav>

    <a class="btn btn--donate" href="donate.html">Donate Now</a>

    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="site-nav">
      <span class="nav-toggle__bars" aria-hidden="true"><span></span><span></span><span></span></span>
      <span class="nav-toggle__text">Menu</span>
    </button>
  </div>
</header>

<main id="main">
""".format(util=util, primary=primary, mobile_extra=mobile_extra)


FOOTER = """</main>

<footer class="footer">
  <div class="wrap">
    <div class="footer__top">
      <div class="footer__brand">
        <img src="assets/img/logo-white.png" width="400" height="312" alt="Gathered Pages Collective">
        <p class="footer__tagline">Stories connect us. Conversations strengthen us. Community transforms us.</p>
      </div>

      <nav aria-label="About the organization">
        <p class="footer__head">The organization</p>
        <ul>
          <li><a href="about.html">About us</a></li>
          <li><a href="founder.html">Meet our founder</a></li>
          <li><a href="makers.html">Women-owned makers</a></li>
          <li><a href="contact.html">Contact</a></li>
        </ul>
      </nav>

      <nav aria-label="About the program">
        <p class="footer__head">The program</p>
        <ul>
          <li><a href="how-it-works.html">How it works</a></li>
          <li><a href="the-box.html">What&#8217;s in the box</a></li>
          <li><a href="reading-list.html">Our reading list</a></li>
          <li><a href="partner.html">Host a book club</a></li>
        </ul>
      </nav>

      <nav aria-label="Ways to get involved">
        <p class="footer__head">Get involved</p>
        <ul>
          <li><a href="donate.html">Donate</a></li>
          <li><a href="partner.html">Partner with us</a></li>
          <li><a href="contact.html#introduce">Introduce us to a group</a></li>
          <li><a href="{instagram}" rel="noopener">Instagram</a></li>
        </ul>
      </nav>
    </div>

    <div class="footer__bottom">
      <p>Gathered Pages Collective is a Colorado nonprofit corporation, incorporated 10 June 2026. EIN 42-3092238. Our application for 501(c)(3) tax-exempt status is pending; gifts are not yet tax-deductible.</p>
      <p>&#169; 2026 Gathered Pages Collective &#183; <a href="mailto:{email}">{email}</a></p>
    </div>
  </div>
</footer>

<script src="assets/js/main.js" defer></script>
</body>
</html>
""".format(instagram=INSTAGRAM, email=EMAIL)


_IMG_DIR = os.path.join(SITE, "assets", "img")


def _image_set(filename):
    """srcset + intrinsic size for an image, from the variants actually on disk.

    A variant is `name-<width>.jpg` beside `name.jpg`. Returns the srcset
    string and the full-size image's real pixel dimensions, so the reserved
    space is always the right shape.
    """
    base, ext = os.path.splitext(filename)
    widths = []
    for f in os.listdir(_IMG_DIR):
        m = re.match(re.escape(base) + r"-(\d+)" + re.escape(ext) + r"$", f)
        if m:
            widths.append(int(m.group(1)))
    full = os.path.join(_IMG_DIR, filename)
    with open(full, "rb") as fh:
        iw, ih = _jpeg_size(fh.read())
    widths = sorted(widths) + [iw]
    parts = []
    for w in widths:
        name = filename if w == iw else "%s-%d%s" % (base, w, ext)
        parts.append("assets/img/%s %dw" % (name, w))
    return ", ".join(parts), iw, ih


def _jpeg_size(data):
    """Read a JPEG's dimensions without pulling in an image library."""
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = (data[i + 5] << 8) + data[i + 6]
            w = (data[i + 7] << 8) + data[i + 8]
            return w, h
        i += 2 + (data[i + 2] << 8) + data[i + 3]
    raise ValueError("not a JPEG")


def pagehead(h1, lead, img, alt, crumb=None, pos="50% 50%"):
    crumbs = ""
    if crumb:
        crumbs = (
            '<p class="breadcrumb"><a href="index.html">Home</a>'
            '<span aria-hidden="true">/</span>%s</p>' % crumb
        )
    base = img.rsplit(".", 1)[0]
    srcset, iw, ih = _image_set(img)

    return """<section class="pagehead">
  <div class="pagehead__media">
    <img srcset="{srcset}" sizes="100vw" src="assets/img/{img}" alt="{alt}" style="object-position:{pos}" fetchpriority="high" width="{iw}" height="{ih}">
  </div>
  <div class="wrap">
    <div class="pagehead__inner">
      {crumbs}
      <h1>{h1}</h1>
      <p class="pagehead__lead">{lead}</p>
    </div>
  </div>
</section>
""".format(img=img, alt=alt, pos=pos, crumbs=crumbs, h1=h1, lead=lead,
               srcset=srcset, iw=iw, ih=ih)


# --------------------------------------------------------------------------
# Shared content blocks
# --------------------------------------------------------------------------

CLOSING_CTA = """<section class="section section--ink">
  <div class="wrap">
    <div class="statement-grid">
      <div data-rise>
        <p class="statement">Every box begins a conversation. <em>Help us send the next one.</em></p>
      </div>
      <div data-rise>
        <p class="text-soft">A gift covers a book by a woman author, a journal and pen from a woman-owned maker, an art card, and the guide that lets a facilitator run the whole club without training. If you would rather give your time than your money, introduce us to a group.</p>
        <div class="btn-row">
          <a class="btn btn--donate" href="donate.html">Donate Now</a>
          <a class="btn btn--outline" href="partner.html">Bring a club to your group</a>
        </div>
      </div>
    </div>
  </div>
</section>
"""


def values_block(navy=True):
    values = [
        ("Connection", "Meaningful relationships begin with shared stories. We create space for women to gather, listen, and support one another."),
        ("Belonging", "Every woman deserves to feel welcomed, valued, and seen, and to show up authentically knowing she belongs."),
        ("Stories that inspire", "Stories broaden perspectives and spark growth. We curate books that challenge, encourage, and connect us."),
        ("Women supporting women", "From the authors we read to the businesses we partner with, we celebrate and invest in women at every step."),
        ("Access", "Community and learning shouldn&#8217;t depend on circumstance. We remove barriers so more women can read together."),
        ("Community", "Lasting change happens through relationships, when women share experiences and celebrate each other&#8217;s wins."),
    ]
    rows = "\n".join(
        "      <div><dt>%s</dt><dd>%s</dd></div>" % (name, text) for name, text in values
    )
    return """<div class="ledger">
{rows}
    </div>""".format(rows=rows)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

PAGES = []


def page(slug, title, desc, body):
    PAGES.append({"slug": slug, "title": title, "desc": desc, "body": body})


# ---------------------------------------------------------------- home ----

page(
    "index",
    "Gathered Pages Collective",
    "Gathered Pages Collective sends complete book clubs — book, journal, pen and discussion guide — free to shelters, recovery programs, senior centers and schools serving women. You gather the women. We handle the rest.",
    """<section class="hero">
  <div class="hero__media">
    <img src="assets/img/hero-poppy-field.jpg"
         srcset="assets/img/hero-poppy-field-800.jpg 800w, assets/img/hero-poppy-field-1000.jpg 1000w, assets/img/hero-poppy-field-1400.jpg 1400w, assets/img/hero-poppy-field.jpg 2400w"
         sizes="100vw" width="2400" height="1029" fetchpriority="high"
         alt="A field of orange poppies drawn in the manner of an antique seed catalog plate, printed on deep navy.">
  </div>
  <div class="wrap hero__inner">
    <div class="hero__body">
      <h1 class="hero__title">Send a book club<br>to a woman who<br><em>needs one.</em></h1>
      <p class="hero__lead">We send complete book club kits &#8212; the book, a journal and pen from women-owned makers, and a guide that runs the conversation &#8212; free to the organizations that already gather women. You bring the women. We handle the rest.</p>
      <div class="btn-row">
        <a class="btn btn--donate" href="donate.html">Donate Now</a>
        <a class="btn btn--outline" href="partner.html">Bring a club to your group</a>
      </div>
      <div class="hero__foot">
        <p>Gathered Pages Collective is a Colorado nonprofit connecting women through shared stories. Our first pilot clubs are being placed now.</p>
      </div>
    </div>
  </div>
</section>





<section class="section section--tight section--navy">
  <div class="wrap">
    <div class="section-intro mb-6" data-rise>
      <p class="label label--orange">Get involved</p>
      <h2>Two ways to take part</h2>
      <p>Send a box to a woman who needs one, or pull up a chair and read alongside her.</p>
    </div>
    <div class="doors doors--two">
      <a class="door" href="donate.html" data-rise>
        <div class="door__figure"><img srcset="assets/img/kit-box-700.jpg 700w, assets/img/kit-box-1000.jpg 1000w, assets/img/kit-box.jpg 1400w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 45vw" src="assets/img/kit-box.jpg" width="1400" height="948" loading="lazy" alt="A kraft box open on a table, the belly-banded kit inside resting in paper crinkle."></div>
        <h3>Donate to a woman in need</h3>
        <p>A gift buys one complete box &#8212; the book, the journal and pen, the art card and the guide &#8212; for a woman in a shelter, a recovery program or transitional housing. It costs her nothing.</p>
        <span class="door__more">Ways to give """ + ARROW + """</span>
      </a>

      <a class="door" href="contact.html" data-rise>
        <div class="door__figure"><img srcset="assets/img/reading-nook-600.jpg 600w, assets/img/reading-nook-900.jpg 900w, assets/img/reading-nook.jpg 1100w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 45vw" src="assets/img/reading-nook.jpg" width="1100" height="1375" loading="lazy" alt="A worn armchair, a stack of hardbacks, a mug of tea and three poppies in a jar under lamplight."></div>
        <h3>Join a virtual book club</h3>
        <p>Receive your own personal box and join a facilitator-led virtual book club with other women who share your story &#8212; connect from anywhere in the country.</p>
        <span class="door__more">Join a virtual club """ + ARROW + """</span>
      </a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>
        <div class="section-intro">
          <h2>What arrives</h2>
          <p>One kit per woman, nested in paper crinkle inside a kraft carton, tied with twine. Ten kits go to a facilitator; she hands them out. Nothing in it is plastic, and nothing in it was bought from a business that isn&#8217;t worth supporting.</p>
        </div>
        <dl class="ledger mt-5">
          <div><dt>The book</dt><dd>Chosen for the group, by a woman author wherever possible, bought from a woman-owned independent bookshop.</dd></div>
          <div><dt>Journal &amp; pen</dt><dd>From women artists and makers &#8212; the poppy and mountain journal covers, and the gel pens from Ruff House Print Shop in Lawrence, Kansas.</dd></div>
          <div><dt>The art card</dt><dd>A printed card by a featured woman artist. Frameable, hers to keep, and a credit the artist can point to.</dd></div>
          <div><dt>The guide</dt><dd>A facilitator welcome and printed discussion questions, so leading the conversation takes no training and no prep.</dd></div>
        </dl>
        <div class="btn-row">
          <a class="btn btn--navy" href="the-box.html">Open the box</a>
        </div>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/kit-carton-700.jpg 700w, assets/img/kit-carton-1000.jpg 1000w, assets/img/kit-carton.jpg 1200w" sizes="(max-width: 900px) calc(100vw - 4rem), 45vw" src="assets/img/kit-carton.jpg" width="1200" height="1591" loading="lazy" alt="An open kraft carton holding ten belly-banded kits in paper crinkle, a Facilitator Welcome card resting on top.">
        <figcaption class="plate-caption">The facilitator carton, opened. Ten kits, one welcome card, no assembly.</figcaption>
      </figure>
    </div>
  </div>
</section>



<section class="section">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>
        <div class="section-intro">
          <h2>Every dollar stays with women</h2>
          <p>We read books by women. We buy journals from women artists, pens from a woman-owned letterpress, and books from women-owned independent bookshops. It is not a preference. It is the point.</p>
        </div>
        <p class="mt-4 text-soft measure">A woman writes the book. A woman prints the pen. A woman runs the shop we buy it from. A woman opens the box. That is the ecosystem we are trying to strengthen, and we would rather build it than describe it.</p>
        <div class="btn-row">
          <a class="btn btn--outline" href="makers.html">Meet the makers</a>
        </div>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/makers-table-800.jpg 800w, assets/img/makers-table-1100.jpg 1100w, assets/img/makers-table.jpg 1600w" sizes="(max-width: 900px) calc(100vw - 4rem), 45vw" src="assets/img/makers-table.jpg" width="1600" height="1067" loading="lazy" alt="A maker&#8217;s worktable: poppy-covered journals, sage gel pens, jute twine, kraft hang-tags and a letterpress card.">
        <figcaption class="plate-caption">The goods we buy, from the women who make them.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section section--navy">
  <div class="wrap">
    <div class="split">
      <figure class="figure plate split__figure-first" data-rise>
        <img srcset="assets/img/jamie-dickinson-600.jpg 600w, assets/img/jamie-dickinson-900.jpg 900w, assets/img/jamie-dickinson.jpg 1097w" sizes="(max-width: 900px) calc(100vw - 4rem), 42vw" src="assets/img/jamie-dickinson.jpg" width="1097" height="1536" loading="lazy" alt="Jamie Dickinson, founder of Gathered Pages Collective.">
      </figure>
      <div data-rise>
        <div class="section-intro">
          <h2>Meet our founder</h2>
        </div>
        <p class="lead mt-4">&#8220;In one particularly challenging chapter of my life, reading helped me recognize truths I had been avoiding and ultimately gave me the courage to make hard decisions that changed the trajectory of my life.&#8221;</p>
        <p class="mt-4 text-soft">Jamie Dickinson is a lawyer, a yoga instructor, a mother and a wife who has never been able to imagine her life without books. Gathered Pages Collective grew out of what she found when she started sharing them.</p>
        <div class="btn-row">
          <a class="btn btn--cream" href="founder.html">Read Jamie&#8217;s story</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--sage">
  <div class="wrap">
    <div class="section-intro mb-6" data-rise>
      <h2>Meet the board</h2>
      <p>Three women who agreed to build this with our founder. No paid staff &#8212; this is all of us.</p>
    </div>
    <div class="people">
      <div class="person" data-rise>
        <figure class="figure plate">
          <img src="assets/img/board-tiffany-anderson.jpg" width="452" height="565" loading="lazy" alt="Tiffany Anderson.">
        </figure>
        <h3>Tiffany Anderson</h3>
        <p class="label">Board member</p>
      </div>

      <div class="person" data-rise>
        <figure class="figure plate">
          <img srcset="assets/img/board-amber-story-400.jpg 400w, assets/img/board-amber-story.jpg 800w" sizes="(max-width: 520px) calc(100vw - 4.5rem), (max-width: 860px) 45vw, 30vw" src="assets/img/board-amber-story.jpg" width="800" height="1000" loading="lazy" alt="Amber Story.">
        </figure>
        <h3>Amber Story</h3>
        <p class="label">Board member</p>
      </div>

      <div class="person" data-rise>
        <figure class="figure plate">
          <img src="assets/img/board-crystal-gippe.jpg" width="365" height="456" loading="lazy" alt="Crystal Gippe.">
        </figure>
        <h3>Crystal Gippe</h3>
        <p class="label">Board member</p>
      </div>
    </div>

    <p class="doors__aside" data-rise>Jamie Dickinson founded Gathered Pages Collective and serves alongside them. <a href="about.html">More about who we are</a>.</p>
  </div>
</section>



<section class="section section--warm">
  <div class="wrap">
    <div class="split split--wide-text">
      <figure class="figure plate plate--book split__figure-first" data-rise>
        <img src="assets/img/theo-of-golden.jpg" width="362" height="552" loading="lazy" alt="The jacket of Theo of Golden by Allen Levi: a single feather on a pale ground.">
      </figure>
      <div data-rise>
        <div class="section-intro">
          <p class="label label--orange">This month&#8217;s selection</p>
          <h2>Theo of Golden</h2>
          <p>Allen Levi &#183; our first selection</p>
        </div>
        <p class="mt-4 text-soft measure">A quietly moving #1 New York Times bestseller about an enigmatic visitor who arrives in the riverside town of Golden and, through small acts of attention and kindness, changes the lives of everyone he meets. It is a story about connection, belonging and the beauty of being truly seen &#8212; the very heart of what every Gathered Pages book club is about.</p>
        <div class="btn-row">
          <a class="btn btn--navy" href="reading-list.html">See the reading list</a>
          <a class="btn btn--outline" href="https://www.instagram.com/gatheredpagescollective/" rel="noopener">Follow along on Instagram</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-intro mb-6" data-rise>
      <p class="label label--orange">Supporting women in business</p>
      <h2>Our artists and journals</h2>
      <p>Every item in our boxes is purchased from a women-owned business. Meet the artists whose work fills each one, and the bookshop the books come from.</p>
    </div>
    <div class="doors">
      <a class="door" href="https://sunshineandlaurelart.com/" rel="noopener" data-rise>
        <div class="door__figure"><img srcset="assets/img/artist-rebekah-600.jpg 600w, assets/img/artist-rebekah.jpg 750w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 30vw" src="assets/img/artist-rebekah.jpg" width="750" height="989" loading="lazy" alt="An acrylic landscape by Rebekah Hayden: snow-covered mountains above a still lake at sunrise."></div>
        <h3>Rebekah Hayden</h3>
        <p>Sunshine and Laurel Art &#8212; a Colorado landscape artist creating expressive acrylic paintings inspired by the beauty of nature. Twelve of her journals are in our stock.</p>
        <span class="door__more">Visit Sunshine and Laurel Art """ + ARROW + """</span>
      </a>

      <a class="door" href="https://www.etsy.com/shop/GinkgoByLaura" rel="noopener" data-rise>
        <div class="door__figure"><img src="assets/img/artist-laura.jpg" width="600" height="600" loading="lazy" alt="Illustrated botanical cards by Laura: poppies, a zinnia, a sunflower and a daisy in bright ink."></div>
        <h3>Laura</h3>
        <p>Ginkgo by Laura &#8212; a biologist and gardener creating nature-inspired illustrated cards and the journals in every box. Fifteen of hers are in our stock.</p>
        <span class="door__more">Shop Ginkgo by Laura """ + ARROW + """</span>
      </a>

      <a class="door" href="https://www.nextchapterbooksandgifts.com/" rel="noopener" data-rise>
        <div class="door__figure"><img src="assets/img/shop-next-chapter.jpg" width="515" height="388" loading="lazy" alt="The Next Chapter bookshop: a white brick storefront with a carved wooden sign and books in the window."></div>
        <h3>The Next Chapter</h3>
        <p>Books and literary gifts, women-owned. Established in 2019 by Shelly Mutum on a fifty-year family legacy of bookselling, and a community hub in its own right.</p>
        <span class="door__more">Visit The Next Chapter """ + ARROW + """</span>
      </a>
    </div>

    <p class="doors__aside" data-rise>We are finalizing partnerships with more women-owned businesses. <a href="makers.html">See all women-owned makers and bookshops</a> we buy from today.</p>
  </div>
</section>



""" + CLOSING_CTA,
)

# --------------------------------------------------------------- about ----

page(
    "about",
    "About Gathered Pages Collective",
    "Our mission, our values, our board and exactly where we are today. Gathered Pages Collective connects women through the power of shared stories.",
    pagehead(
        "Stories connect us.",
        "Gathered Pages Collective connects women through the power of shared stories, creating spaces where every woman can find connection, belonging, and the confidence to grow.",
        "pressed-poppies.jpg",
        "An open herbarium album of pressed orange poppies and sage sprigs mounted on aged cream pages.",
        "<span>About</span>",
        "60% 45%",
    )
    + """<section class="section">
  <div class="wrap wrap--mid">
    <div class="prose prose--wrap" data-rise>
      <h2>Our story</h2>
      <figure class="figure plate figure--float">
        <img srcset="assets/img/read-queen-books-600.jpg 600w, assets/img/read-queen-books-900.jpg 900w, assets/img/read-queen-books.jpg 1500w" sizes="(max-width: 640px) calc(100vw - 4rem), 20rem" src="assets/img/read-queen-books.jpg" width="1500" height="1540" loading="lazy" alt="Jamie Dickinson outside The Read Queen bookstore and cafe, holding two hardbacks, a filing box of books at her feet.">
      </figure>
      <p>At Gathered Pages Collective, we believe stories have the power to bring women together.</p>
      <p>Reading a great book is meaningful, but sharing that experience with others is transformative. Through honest conversation and shared perspectives, women find connection, encouragement, and the reminder that they are not alone.</p>
      <p>Unfortunately, those opportunities aren&#8217;t equally available to everyone.</p>
      <p>Women navigating financial hardship, domestic violence, illness, recovery, grief, single parenthood, incarceration, caregiving responsibilities, or other major life transitions often experience profound isolation. Research consistently shows that meaningful relationships and a sense of belonging are essential to resilience and well-being, yet many women lack access to affordable, welcoming communities where they can simply gather, reflect, and connect.</p>
      <p>That&#8217;s where Gathered Pages Collective comes in.</p>
      <p>We create opportunities for women to experience the connection and belonging that come from reading together. By partnering with shelters, recovery programs, transitional housing organizations, correctional facilities, community nonprofits, and other trusted organizations, we provide thoughtfully curated book club experiences at no cost to participants.</p>
      <p>Every decision we make reflects our belief in women supporting women. We intentionally feature books written by women wherever possible, partner with women-owned businesses to create the journals and gifts included in our experiences, and invest in female entrepreneurs whose work aligns with our mission. In doing so, we create a ripple effect &#8212; supporting women as storytellers, business owners, community leaders, and readers.</p>
      <p>We know a book alone doesn&#8217;t change a life. But a conversation can. A community can. A woman who feels seen, heard, and connected can.</p>
      <p>Because stories don&#8217;t just help us understand the world &#8212; they help us find one another.</p>
    </div>


  </div>
</section>

<section class="section section--navy">
  <div class="wrap">
    <div class="statement-grid">
      <div data-rise>
        <p class="statement">Stories connect us. Conversations strengthen us. <em>Community transforms us.</em></p>
      </div>
      <div data-rise>
        <p class="text-soft">Our mission is broad and welcoming on purpose. Our values are where we say out loud how we intend to keep it &#8212; why we look for women authors first, why the journal in the box came from a woman&#8217;s studio, and why none of it costs the women who receive it anything.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap wrap--mid">
    <div class="section-intro" data-rise>
      <h2>What we value</h2>
      <p>Six commitments, and each one is a decision we have already had to make.</p>
    </div>
    <div class="mt-6" data-rise>
      """
    + values_block()
    + """
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>
        <div class="section-intro">
          <h2>Where we are today</h2>
          <p>We would rather tell you exactly what is true than imply more than there is.</p>
        </div>
        <dl class="ledger mt-5">
          <div><dt>Incorporated</dt><dd>Gathered Pages Collective was incorporated as a Colorado nonprofit corporation on <strong>10 June 2026</strong>. Our EIN is <strong>42-3092238</strong>.</dd></div>
          <div><dt>Tax status</dt><dd>Our application for <strong>501(c)(3)</strong> recognition has been submitted and is pending with the IRS. Until it is granted, gifts to Gathered Pages Collective are not tax-deductible, and we will not tell you otherwise.</dd></div>
          <div><dt>Program</dt><dd>We are placing our <strong>first pilot clubs</strong> now, deliberately small and deliberately local, so the facilitator experience is right before we scale it.</dd></div>
          <div><dt>Team</dt><dd>One founder, three board members, and a growing list of women-owned businesses we buy from. No paid staff.</dd></div>
          <div><dt>Impact</dt><dd>We have no participant numbers to quote yet. When we do, they will be real ones.</dd></div>
        </dl>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/kraft-cartons-800.jpg 800w, assets/img/kraft-cartons-1100.jpg 1100w, assets/img/kraft-cartons.jpg 1600w" sizes="(max-width: 900px) calc(100vw - 4rem), 45vw" src="assets/img/kraft-cartons.jpg" width="1600" height="1067" loading="lazy" alt="Kraft cartons tied with twine stacked by a doorway, a sprig of orange poppies laid across the top box.">
        <figcaption class="plate-caption">Cartons waiting by the door. Our first deliveries are hand-carried.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section section--ink">
  <div class="wrap wrap--mid">
    <div class="section-intro" data-rise>
      <h2>Our board</h2>
      <p>Three women who agreed to build this with our founder.</p>
    </div>
    <ul class="catalog mt-6" data-rise>
      <li><span class="entry-title">Tiffany Anderson</span><span class="entry-leader"></span><span class="entry-note">Board member</span></li>
      <li><span class="entry-title">Amber Story</span><span class="entry-leader"></span><span class="entry-note">Board member</span></li>
      <li><span class="entry-title">Crystal Gippe</span><span class="entry-leader"></span><span class="entry-note">Board member</span></li>
      <li><span class="entry-title">Jamie Dickinson</span><span class="entry-leader"></span><span class="entry-note">Founder</span></li>
    </ul>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# -------------------------------------------------------- how it works ----

page(
    "how-it-works",
    "How It Works",
    "What hosting a Gathered Pages book club actually asks of you: a short conversation, a book choice, and a room. We provide everything else at no cost.",
    pagehead(
        "You gather the women.<br>We handle the rest.",
        "Hosting a Gathered Pages book club costs your organization nothing and asks almost nothing of you. Here is the whole process, start to finish.",
        "circle-of-chairs.jpg",
        "A circle of mismatched chairs in a sunlit community room, a book and tied journal waiting on each seat.",
        "<span>How it works</span>",
        "50% 60%",
    )
    + """<section class="section">
  <div class="wrap">
    <div class="section-intro" data-rise>
      <h2>The process</h2>
      <p>Five steps. Four of them are ours.</p>
    </div>
    <div class="steps steps--narrow mt-6">
      <div class="step" data-rise>
        <div class="step__body">
          <h3>Tell us about your group</h3>
          <p>Fill in the short form on the partner page, or just email us. We want to know roughly how many women, what they are navigating, and whether you can gather them once or regularly. There is no application to write and no budget to submit.</p>
        </div>
      </div>
      <div class="step" data-rise>
        <div class="step__body">
          <h3>A short conversation</h3>
          <p>Fifteen minutes on the phone or over coffee. We are trying to understand your group well enough to choose the right book, and to make sure a book club is genuinely useful to them rather than one more thing on your desk.</p>
        </div>
      </div>
      <div class="step" data-rise>
        <div class="step__body">
          <h3>We bring three books; you choose one</h3>
          <p>We come back with three titles chosen for your group and a paragraph on why each one is on the list. You know these women better than we do, so the choice is yours. If none of them fit, say so and we will go again.</p>
        </div>
      </div>
      <div class="step" data-rise>
        <div class="step__body">
          <h3>The carton arrives</h3>
          <p>One kraft carton holding ten complete kits, each one banded and ready to hand over. In Colorado we deliver it ourselves. Everything inside is yours &#8212; the books do not come back.</p>
        </div>
      </div>
      <div class="step" data-rise>
        <div class="step__body">
          <h3>You open the guide and ask the first question</h3>
          <p>The facilitator guide gives you a welcome to read, discussion questions for each section of the book, and reflection prompts for the journals. You do not need to have read the book first, and you do not need training.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--navy">
  <div class="wrap">
    <div class="split">
      <div data-rise>
        <div class="section-intro">
          <h2>What we provide</h2>
          <p>Everything in the carton, at no cost to your organization or to the women in your group.</p>
        </div>
        <dl class="ledger mt-5">
          <div><dt>Books</dt><dd>One copy per woman, hers to keep.</dd></div>
          <div><dt>Journals &amp; pens</dt><dd>One of each per woman, from women-owned makers.</dd></div>
          <div><dt>Art card</dt><dd>A printed card by a featured woman artist.</dd></div>
          <div><dt>Facilitator guide</dt><dd>Welcome script, discussion questions, journal prompts.</dd></div>
          <div><dt>Delivery</dt><dd>Hand-delivered locally in Colorado, shipped elsewhere.</dd></div>
          <div><dt>Someone to ask</dt><dd>A person you can email when something comes up.</dd></div>
        </dl>
      </div>
      <div data-rise>
        <div class="section-intro">
          <h2>What you provide</h2>
          <p>The part we cannot do from here.</p>
        </div>
        <dl class="ledger mt-5">
          <div><dt>The women</dt><dd>A group of roughly ten who would want this.</dd></div>
          <div><dt>A room</dt><dd>Any room. A rec room, a staff room, a day room, a library corner.</dd></div>
          <div><dt>A time</dt><dd>Whatever cadence works &#8212; once, monthly, or the length of a program.</dd></div>
          <div><dt>An hour</dt><dd>Roughly, per meeting, to hold the conversation.</dd></div>
          <div><dt>Honest feedback</dt><dd>Tell us what worked and what did not. Our early groups are shaping this.</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap wrap--mid">
    <div class="section-intro" data-rise>
      <h2>Questions we get asked</h2>
    </div>
    <dl class="ledger ledger--qa mt-6" data-rise>
      <div><dt>What does it cost?</dt><dd>Nothing. Not to your organization, and not to the women who receive a kit. The program is funded by donations and, in time, by paid boxes bought by people who can afford them.</dd></div>
      <div><dt>Do we give the books back?</dt><dd>No. The book, the journal, the pen and the art card belong to the woman who receives them.</dd></div>
      <div><dt>Do I need to have read the book?</dt><dd>It helps, but the guide is written so you can lead the conversation either way.</dd></div>
      <div><dt>What if my group is bigger or smaller than ten?</dt><dd>Tell us. Ten is our standard carton, not a rule.</dd></div>
      <div><dt>Can the group meet only once?</dt><dd>Yes. A single gathering is a real book club. Many of our partner settings cannot commit to a series, and that is fine.</dd></div>
      <div><dt>Are you outside Colorado?</dt><dd>Colorado and Nebraska are where our founder splits her time, so those are easiest first. Ask anyway &#8212; shipping is a cost, not an obstacle.</dd></div>
      <div><dt>Some of the material is emotionally heavy. Is that a problem?</dt><dd>Books raise things. We are not a therapy service and we do not pretend to be, and our facilitator agreement says so plainly. We choose titles with your group in mind and you always have final say on the book.</dd></div>
      <div><dt>How long does it take to get a carton?</dt><dd>We are placing our first pilot clubs now, so the honest answer is: talk to us and we will give you a real date rather than a guess.</dd></div>
    </dl>
    <div class="btn-row">
      <a class="btn btn--navy" href="partner.html">Apply to host a club</a>
      <a class="btn btn--outline" href="the-box.html">See what&#8217;s in the box</a>
    </div>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# ------------------------------------------------------------- the box ----

PACKETS = [
    ("book", "The book", "One copy per woman, chosen for the group and hers to keep. By a woman author wherever possible, bought from a woman-owned independent bookshop rather than from a warehouse.",
     "Sowing: the group reads at whatever pace suits them. Our guide is written in sections so a group that gets halfway still has a real conversation."),
    ("journal", "The journal", "From a woman artist &#8212; the poppy and mountain covers are the first two. It is bound with the pen in a kraft belly band so it travels as a set.",
     "Sowing: the reflection prompts in the guide are written for these pages. Nobody ever has to read theirs out loud."),
    ("pen", "The pen", "A gel pen from Ruff House Print Shop, a letterpress studio and paperie in Lawrence, Kansas, run by Jill Shephard.",
     "Sowing: a small thing, deliberately. A pen that is nicer than it needs to be is the part people notice."),
    ("card", "The art card", "A printed card featuring a woman artist we are highlighting that season. Frameable, hers to keep, and a credit the artist can point her own audience toward.",
     "Sowing: the featured artist rotates. It is the cheapest way we have found to put real money and real attention into a working artist&#8217;s hands."),
    ("envelope", "The welcome letter", "A short letter from our founder, sitting on top so it is the first thing you see. One paragraph about why this box exists.",
     "Sowing: it is not a flyer and it does not ask for anything. It says she belongs here, which is the whole point of the box."),
    ("guide", "The facilitator guide", "A welcome to read aloud, discussion questions for each part of the book, and journal prompts. Written so the conversation runs without training or prep.",
     "Sowing: one printed Facilitator Welcome card sits on top of the carton explaining how to hand the kits out. That is the entire onboarding."),
]


def packets_markup():
    out = []
    for i, (ic, name, front, back) in enumerate(PACKETS):
        pid = "packet-back-%d" % (i + 1)
        out.append(
            """      <div class="packet-cell">
        <button class="packet" type="button" data-packet aria-expanded="false" aria-controls="{pid}">
          {icon}
          <h3>{name}</h3>
          <p>{front}</p>
          <span class="packet__flip">Sowing instructions <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 9 7 7 7-7"/></svg></span>
        </button>
        <div class="packet__back" id="{pid}"><div><p>{back}</p></div></div>
      </div>""".format(pid=pid, icon=icon(ic, cls="packet__icon"), name=name, front=front, back=back)
        )
    return "\n".join(out)


page(
    "the-box",
    "What’s In The Box",
    "A book, a journal, a pen, an art card, a welcome letter and a facilitator guide — one kit per woman, ten kits per carton, all sourced from women-owned makers.",
    pagehead(
        "What&#8217;s in the box",
        "One kit per woman: a book, a journal, a pen, an art card, a letter and the guide that runs the conversation. Ten kits nest in a kraft carton and go to one facilitator.",
        "kit-carton.jpg",
        "An open kraft carton holding ten belly-banded book club kits nested in paper crinkle.",
        "<span>What&#8217;s in the box</span>",
        "50% 50%",
    )
    + """<section class="section">
  <div class="wrap">
    <div class="split split--wide-figure">
      <div data-rise>
        <div class="section-intro">
          <h2>One kit, one woman</h2>
          <p>We designed a single kit sized for one person rather than a group box. Ten of them nest inside a plain kraft carton for a facilitator, and the same kit ships on its own when it needs to.</p>
        </div>
        <p class="mt-4 text-soft measure">Everything is paper: kraft carton, paper crinkle, paper tape, jute twine, a sticker seal to break. No plastic wrap, no bubble, no gloss. It is cheaper, it is recyclable, and it is honest about what this organization is.</p>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/kit-box-700.jpg 700w, assets/img/kit-box-1000.jpg 1000w, assets/img/kit-box.jpg 1400w" sizes="(max-width: 900px) calc(100vw - 4rem), 45vw" src="assets/img/kit-box.jpg" width="1400" height="948" loading="lazy" alt="A closed kraft mailer box with a cream Gathered Pages sticker on the lid and a smaller one on the side.">
        <figcaption class="plate-caption">Sealed and labelled. The sticker breaking is the reveal.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section section--navy section--flush-top">
  <div class="wrap">
    <div class="ruled-head mt-7" data-rise>
      <span class="label label--orange">Contents</span>
      <span class="label">Select any item for its sowing instructions</span>
    </div>
    <div class="packets" data-rise>
"""
    + packets_markup()
    + """
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="split">
      <figure class="figure plate split__figure-first" data-rise>
        <img srcset="assets/img/kit-contents-700.jpg 700w, assets/img/kit-contents-1000.jpg 1000w, assets/img/kit-contents.jpg 1400w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 30vw" src="assets/img/kit-contents.jpg" width="1400" height="946" loading="lazy" alt="A single kit laid out: a navy hardback, a poppy journal banded with a sage pen, a welcome card and a poppy art card.">
        <figcaption class="plate-caption">One woman&#8217;s kit, unpacked.</figcaption>
      </figure>
      <div data-rise>
        <div class="section-intro">
          <h2>The order she opens it in</h2>
          <p>The sequence is the design. It is what turns a box of things into someone having thought about you.</p>
        </div>
        <ol class="mt-5 measure text-soft">
          <li>The welcome letter, sitting on top.</li>
          <li>The book, banded so opening it feels deliberate.</li>
          <li>The journal and pen, tied together as a set.</li>
          <li>The art card, tucked alongside &#8212; the thing she keeps longest.</li>
          <li>A small card with the first meeting details.</li>
        </ol>
      </div>
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap wrap--mid">
    <div class="section-intro" data-rise>
      <h2>What a kit costs us</h2>
      <p>Not an estimate. These are the prices on our own receipts so far, for the thirty books, thirty-seven journals and sixteen pens we have bought.</p>
    </div>
    <dl class="ledger mt-6" data-rise>
      <div><dt>Book</dt><dd>$20.20 &#8211; $21.85 &#183; The Read Queen, thirty copies bought so far</dd></div>
      <div><dt>Journal</dt><dd>$7.30 &#8211; $20.27 &#183; three artists, three prices, each paid in full</dd></div>
      <div><dt>Pen</dt><dd>$6.75 &#183; Ruff House Print Shop, bought by the case</dd></div>
      <div><dt>Bookmark &amp; pin</dt><dd>The Towne Witch and Magnifique Hearts &#183; per-unit cost depends on the run</dd></div>
      <div><dt>Box &amp; paper</dt><dd>Kraft carton, belly band, art card, welcome letter, seal and crinkle</dd></div>
      <div><dt>Per woman</dt><dd><strong>About $40 &#8211; $55 all in.</strong> A ten-woman group is therefore roughly $400 &#8211; $550. Shipping would add $6 &#8211; $9 a box, which is exactly why our first Colorado groups get their cartons hand-delivered.</dd></div>
    </dl>
    <div class="btn-row">
      <a class="btn btn--donate" href="donate.html">Fund a kit</a>
      <a class="btn btn--outline" href="makers.html">See who we buy from</a>
    </div>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# ------------------------------------------------------------- founder ----

page(
    "founder",
    "Meet Our Founder",
    "Jamie Dickinson on her mother reading aloud, on reading through a hard chapter of her own life, and on why Gathered Pages Collective exists.",
    pagehead(
        "Meet our founder",
        "Jamie Dickinson on her mother reading aloud, on the books that got her through a hard chapter, and on the thing she eventually realized she valued most.",
        "reading-nook.jpg",
        "A worn armchair beside a table with a stack of hardbacks, a mug of tea and three poppies in a jar under lamplight.",
        "<span>Meet our founder</span>",
        "62% 50%",
    )
    + """<section class="section">
  <div class="wrap wrap--mid">
    <div class="prose" data-rise>
      <p class="lead">Hi, I&#8217;m Jamie Dickinson, founder of Gathered Pages Collective.</p>
      <p>I&#8217;ve always believed that books do more than tell stories &#8212; they help us understand ourselves, connect with others, and sometimes find the courage to change our lives.</p>
      <p>My love of reading began with my mom. Growing up, she read to my brother and me every night, instilling in us not only a love of books but a curiosity about the world and the people in it. Those evenings planted the seeds for a lifelong passion that continues to shape my life today. In many ways, books have become a language we still share. Although we now live more than 2,000 miles apart, not a week goes by without a conversation about what we&#8217;re reading. Those discussions have strengthened our relationship across the years and the miles, reminding me that stories have a unique way of bringing people together.</p>
      <p>People often ask me how I find time to read. As a busy lawyer, yoga instructor, mom, and wife, I understand why they ask. Life is full, schedules are demanding, and there never seem to be enough hours in the day. The truth is that I can&#8217;t imagine navigating my life without books. Reading is the one thing that helps me quiet my constantly whirling mind and truly relax. It creates space to reflect, learn, dream, and simply breathe.</p>
    </div>
  </div>
</section>

<section class="section section--navy section--tight">
  <div class="wrap wrap--mid">
    <figure class="quote quote--wide" data-rise>
      <p>&#8220;In one particularly challenging chapter of my life, reading helped me recognize truths I had been avoiding and ultimately gave me the courage to make hard decisions that changed the trajectory of my life.&#8221;</p>
    </figure>
  </div>
</section>

<section class="section">
  <div class="wrap wrap--mid">
    <div class="prose" data-rise>
      <p>The idea for Gathered Pages Collective grew from my own experience with reading and the profound impact it has had on my life. Throughout the years, books have been my teachers, my companions, and often my source of clarity during difficult seasons. In one particularly challenging chapter of my life, reading helped me recognize truths I had been avoiding and ultimately gave me the courage to make hard decisions that changed the trajectory of my life. Through the stories and experiences of others, I found perspective, strength, and hope for a different future.</p>
      <p>That experience reinforced something I had always believed: stories have power. They remind us that we are not alone. They help us see possibilities we may not have considered and give us the confidence to take the next step in our own journey.</p>
      <p>But reading has given me more than personal growth &#8212; it has given me community. Some of the most meaningful conversations I&#8217;ve had, the deepest connections I&#8217;ve formed, and the greatest lessons I&#8217;ve learned have come from sharing books with others.</p>
      <p>Because I split my time between two states and am rarely in one place for long, building and maintaining community can be challenging. Yet books have provided a constant foundation. No matter where I am, discussing stories with other women creates connection, belonging, and understanding. Those conversations have become an anchor in my life, helping me build relationships that support and sustain me through every season.</p>
      <p>Over time, I realized that what I valued most wasn&#8217;t simply reading books &#8212; it was sharing them. The discussions, the laughter, the vulnerability, and the friendships that grew from a shared story often became just as meaningful as the books themselves.</p>
      <p>That realisation became the inspiration for Gathered Pages Collective.</p>
      <p>Our mission is simple: to connect women through shared stories by providing free book club experiences to women seeking connection, belonging, and community. Through thoughtfully curated Book Clubs in a Box, we create opportunities for meaningful conversation, personal growth, friendship, and hope.</p>
      <p>Reading is important to me because it has shaped who I am. It has challenged me, comforted me, inspired me, and helped me navigate some of life&#8217;s most difficult decisions. Every book offers an opportunity to see the world &#8212; and ourselves &#8212; a little differently.</p>
      <p>My hope is that every woman who participates in a Gathered Pages Collective book club experiences what I have experienced through reading: the comfort of being understood, the courage that comes from hearing another woman&#8217;s story, and the strength that comes from knowing you are not alone.</p>
    </div>

    <div class="mt-7" data-rise>
      <hr class="hairline">
      <p class="mt-4 text-soft measure">Jamie Dickinson is the founder of Gathered Pages Collective. She is a lawyer and a yoga instructor, splits her time between Colorado and Nebraska, and would like to know what you are reading.</p>
      <div class="btn-row">
        <a class="btn btn--navy" href="contact.html">Write to Jamie</a>
        <a class="btn btn--outline" href="about.html">About the organization</a>
      </div>
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap">
    <div class="quote-band">
      <figure class="quote" data-rise>
        <p>&#8220;There&#8217;s power in allowing yourself to be known and heard, in owning your unique story, in using your authentic voice.&#8221;</p>
        <figcaption>Michelle Obama, <cite>Becoming</cite></figcaption>
      </figure>
      <div data-rise>
        <p class="text-soft">A shelf of lines we keep coming back to sits behind the reading list &#8212; the books we are considering, and why.</p>
        <a class="xref" href="reading-list.html">The reading list """ + ARROW + """</a>
      </div>
    </div>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# ------------------------------------------------------------- partner ----

page(
    "partner",
    "Partner With Us",
    "Apply to host a free Gathered Pages book club. We provide the books, journals, pens and discussion guide at no cost. You bring the women.",
    pagehead(
        "Bring a book club<br>to the women you serve.",
        "We provide everything at no cost to your organization: a thoughtfully chosen book, journals and pens from women-owned businesses, and a simple guide to lead the conversation. You bring the women.",
        "kraft-cartons.jpg",
        "Kraft cartons tied with twine stacked by a doorway, a sprig of orange poppies laid across the top box.",
        "<span>Partner with us</span>",
        "55% 50%",
    )
    + """<section class="section">
  <div class="wrap">
    <div class="section-intro" data-rise>
      <h2>Who we are looking for</h2>
      <p>We are not looking for a group of women. We are looking for the person who already gathers them and would take a complete program off the shelf if someone handed it to her.</p>
    </div>
    <dl class="ledger mt-6" data-rise>
      <div><dt>Shelters</dt><dd>Domestic violence and women&#8217;s shelters &#8212; the program or activities director, or a case manager. Healing and community is the exact mission, and residents often have time.</dd></div>
      <div><dt>Recovery</dt><dd>Recovery and mental health programs &#8212; a program director or group therapist. Shared reading is a connective, low-pressure group activity.</dd></div>
      <div><dt>Senior living</dt><dd>Senior centers and assisted living &#8212; the activities coordinator. Reading clubs cut isolation and staff love ready-made programming.</dd></div>
      <div><dt>Schools</dt><dd>Teachers, school librarians, PTA leads. Teacher book clubs as self-care, or mother groups. Emotional labor is the job nobody funds.</dd></div>
      <div><dt>Hospitals</dt><dd>Nurse managers, chaplains, patient experience leads. Nurses and first responders carry other people&#8217;s worst days and rarely get anything poured back.</dd></div>
      <div><dt>Reentry</dt><dd>Reentry program coordinators and prison education liaisons.</dd></div>
      <div><dt>Libraries</dt><dd>Adult services and outreach librarians &#8212; you already host clubs and you already know which groups are underserved.</dd></div>
      <div><dt>Community groups</dt><dd>Women&#8217;s ministry leaders, community center directors, military family readiness and spouse-group coordinators, refugee and immigrant women&#8217;s services.</dd></div>
    </dl>
    <p class="mt-5 text-soft measure">If you are reading this and thinking &#8220;that is almost us,&#8221; it is us. Write anyway.</p>
  </div>
</section>

<section class="section section--navy">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>
        <div class="section-intro">
          <h2>What we ask of you</h2>
          <p>Short version: a room, an hour, and roughly ten women.</p>
        </div>
        <p class="mt-4 text-soft measure">There is no cost, no match, no reporting requirement, and no grant to administer. We do ask you to sign a one-page facilitator agreement covering the practical things &#8212; that you will hand the materials to the women they are for, that the discussion questions and structure remain ours, that some books raise personal or emotional material and we are not providing therapy or crisis services, and that we may ask you for feedback to make the next box better.</p>
        <p class="mt-4 text-soft measure">Our early groups are shaping this program rather than receiving a finished product, and we will say that to you plainly rather than pretend otherwise.</p>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/bookcloth-stack-800.jpg 800w, assets/img/bookcloth-stack-1100.jpg 1100w, assets/img/bookcloth-stack.jpg 1600w" sizes="(max-width: 900px) calc(100vw - 4rem), 45vw" src="assets/img/bookcloth-stack.jpg" width="1600" height="1067" loading="lazy" alt="A fan of cloth-bound hardbacks in navy, sage, kraft and burnt orange on kraft paper with dried poppy pods and twine.">
        <figcaption class="plate-caption">Ten copies, one group, no cost.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section" id="apply">
  <div class="wrap wrap--mid">
    <div class="section-intro" data-rise>
      <h2>Apply to host a club</h2>
      <p>Six fields. We read every one of these ourselves.</p>
    </div>


    <form class="form mt-6" action="mailto:jamie@gatheredpages.org" method="post" enctype="text/plain" data-rise>
      <div class="field-row">
        <div class="field">
          <label for="p-name">Your name</label>
          <input id="p-name" name="name" type="text" autocomplete="name" required>
        </div>
        <div class="field">
          <label for="p-role">Your role</label>
          <input id="p-role" name="role" type="text" placeholder="Activities coordinator" required>
        </div>
      </div>

      <div class="field-row">
        <div class="field">
          <label for="p-org">Organization</label>
          <input id="p-org" name="organization" type="text" required>
        </div>
        <div class="field">
          <label for="p-city">City &amp; state</label>
          <input id="p-city" name="location" type="text" required>
        </div>
      </div>

      <div class="field-row">
        <div class="field">
          <label for="p-email">Email</label>
          <input id="p-email" name="email" type="email" autocomplete="email" required>
        </div>
        <div class="field">
          <label for="p-size">How many women, roughly?</label>
          <input id="p-size" name="group_size" type="text" inputmode="numeric" placeholder="10">
        </div>
      </div>

      <div class="field">
        <label for="p-about">Tell us about your group</label>
        <textarea id="p-about" name="about" placeholder="Who they are, what they are navigating, and how often you could gather them."></textarea>
        <p class="field-hint">Please don&#8217;t include names or identifying details of the women in your group.</p>
      </div>

      <div class="btn-row btn-row--flush">
        <button class="btn btn--navy" type="submit">Send this to Jamie</button>
        <a class="btn btn--outline" href="mailto:{email}?subject=Hosting%20a%20Gathered%20Pages%20book%20club">Email instead</a>
      </div>
      <p class="field-hint">This opens your email app with your answers filled in. If nothing happens, write to <a href="mailto:{email}">{email}</a> instead.</p>
    </form>
  </div>
</section>

<section class="section section--warm section--tight">
  <div class="wrap wrap--mid">
    <div class="notice" data-rise>
      <p><strong>Not the right fit, but you know someone?</strong></p>
      <p>The single most useful thing anyone does for us is an introduction. If you know a shelter, a recovery program, a senior center or a staff room that would want this, <a href="contact.html#introduce">tell us about them</a> and we will make the approach.</p>
    </div>
  </div>
</section>

""".replace("{email}", EMAIL)
    + CLOSING_CTA,
)

# -------------------------------------------------------- reading list ----

READING = [
    (
        "Books that hold a group together",
        "Warm, generous novels that give a circle of strangers something to say to each other in the first hour.",
        [
            ("Theo of Golden", "Allen Levi"),
            ("The Correspondent", "Virginia Evans"),
            ("My Friends", "Fredrik Backman"),
            ("The Covenant of Water", "Abraham Verghese"),
            ("Horse", "Geraldine Brooks"),
            ("West with Giraffes", "Lynda Rutledge"),
            ("A Man Called Ove", "Fredrik Backman"),
            ("The Midnight Library", "Matt Haig"),
            ("The Great Believers", "Rebecca Makkai"),
            ("Cutting for Stone", "Abraham Verghese"),
            ("Water for Elephants", "Sara Gruen"),
            ("Go as a River", "Shelley Read"),
        ],
    ),
    (
        "Women writing women",
        "Where we look first. A book by a woman, about women, put into the hands of ten women, is the whole thesis in one object.",
        [
            ("Happy Land", "Dolen Perkins-Valdez"),
            ("The Lion Women of Tehran", "Marjan Kamali"),
            ("Lady Tan&#8217;s Circle of Women", "Lisa See"),
            ("The Island of Sea Women", "Lisa See"),
            ("First Ladies", "Marie Benedict &amp; Victoria Christopher Murray"),
            ("The Women", "Kristin Hannah"),
            ("The Great Alone", "Kristin Hannah"),
            ("Black Cake", "Charmaine Wilkerson"),
            ("The Frozen River", "Ariel Lawhon"),
            ("The Wind Knows My Name", "Isabel Allende"),
            ("Atmosphere", "Taylor Jenkins Reid"),
            ("How to Read a Book", "Monica Wood"),
            ("The One Hundred Years of Lenni and Margot", "Marianne Cronin"),
            ("Lessons in Chemistry", "Bonnie Garmus"),
            ("The Dictionary of Lost Words", "Pip Williams"),
            ("Great Circle", "Maggie Shipstead"),
            ("The Secrets of Midwives", "Sally Hepworth"),
            ("The Giver of Stars", "Jojo Moyes"),
        ],
    ),
    (
        "Heavier, and worth it",
        "For groups that have said they want the harder conversation. We never place one of these without asking the facilitator first.",
        [
            ("Tilt", "Emma Pattee"),
            ("The Names", "Florence Knapp"),
            ("Wild Dark Shore", "Charlotte McConaghy"),
            ("The God of the Woods", "Liz Moore"),
            ("James", "Percival Everett"),
            ("Demon Copperhead", "Barbara Kingsolver"),
            ("American Dirt", "Jeanine Cummins"),
            ("The Power of One", "Bryce Courtenay"),
        ],
    ),
    (
        "Rest, and looking after yourself",
        "Short, kind books for groups whose members are running on empty &#8212; nurses, carers, teachers, new mothers.",
        [
            ("Wintering", "Katherine May"),
            ("Thirty Things I Love About Myself", "Radhika Sanghani"),
            ("The Gifts of Imperfection", "Bren&#233; Brown"),
            ("Braving the Wilderness", "Bren&#233; Brown"),
            ("All About Love", "bell hooks"),
        ],
    ),
    (
        "True stories",
        "Memoir and narrative non-fiction. Often the fastest route to a group talking about themselves.",
        [
            ("Finding Me", "Viola Davis"),
            ("Educated", "Tara Westover"),
            ("Becoming", "Michelle Obama"),
            ("Awake", "Jen Hatmaker"),
            ("Fast Girls", "Elise Hooper"),
            ("The Glass Castle", "Jeannette Walls"),
            ("Eat, Pray, Love", "Elizabeth Gilbert"),
            ("Untamed", "Glennon Doyle"),
        ],
    ),
    (
        "The world we are handing on",
        "Climate and place, for groups who would rather look outward than inward.",
        [
            ("The Light Pirate", "Lily Brooks-Dalton"),
            ("Migrations", "Charlotte McConaghy"),
        ],
    ),
]


def reading_markup():
    out = []
    for heading, blurb, items in READING:
        rows = "\n".join(
            '        <li><span class="entry-title">%s</span><span class="entry-leader"></span><span class="entry-note">%s</span></li>'
            % (t, a)
            for t, a in items
        )
        out.append(
            """    <div class="mt-7" data-rise>
      <h3>{heading}</h3>
      <p class="text-soft measure mt-3">{blurb}</p>
      <ul class="catalog mt-5">
{rows}
      </ul>
    </div>""".format(heading=heading, blurb=blurb, rows=rows)
        )
    return "\n\n".join(out)


page(
    "reading-list",
    "Our Reading List",
    "The titles Gathered Pages Collective is considering for its boxes, grouped by what a group needs — books that hold a circle together, women writing women, memoir, rest, and the harder conversation.",
    pagehead(
        "The reading list",
        "Not a canon. A working list of titles we are considering, grouped by what a particular group of women might need from an hour together.",
        "bookcloth-stack.jpg",
        "A fan of cloth-bound hardbacks in navy, sage, kraft and burnt orange on kraft paper with dried poppy pods.",
        "<span>Reading list</span>",
        "50% 45%",
    )
    + """<section class="section">
  <div class="wrap wrap--mid">
    <div class="section-intro mb-5" data-rise>
      <h2>Titles under consideration</h2>
    </div>

    <div class="notice" data-rise>
      <p><strong>How to read this list.</strong> These are titles under consideration, not a fixed catalog. Every group gets three options chosen for them, with a paragraph on why each one is on the shortlist, and the facilitator picks. A title appearing here is not a promise that it will be in your carton.</p>
    </div>

"""
    + reading_markup()
    + """

    <div class="mt-7" data-rise>
      <hr class="hairline">
      <div class="mt-5">
        <h3>How a book gets chosen</h3>
        <p class="text-soft measure mt-3">One question comes first: will this give ten women in a room something honest to say to each other? After that we look for a woman author, a book we can buy from a woman-owned bookshop, a length a busy group can actually finish, and subject matter that suits what this particular group is carrying. The facilitator has the final say, always.</p>
        <div class="btn-row">
          <a class="btn btn--navy" href="partner.html">Choose a book for your group</a>
          <a class="btn btn--outline" href="makers.html">Where we buy books</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--navy section--tight">
  <div class="wrap">
    <div class="quote-band">
      <figure class="quote" data-rise>
        <p>&#8220;I am a reader. I am intelligent. I have something to contribute.&#8221;</p>
        <figcaption>Harriet&#8217;s opening line at every meeting in <cite>How to Read a Book</cite>, Monica Wood</figcaption>
      </figure>
      <div data-rise>
        <p class="text-soft">It is the line we would put on the inside of every carton lid if there were room. A book club is not charity handed down. It is ten women agreeing that what each of them thinks is worth hearing.</p>
      </div>
    </div>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# --------------------------------------------------------------- makers ----

MAKERS_IN_BOX = [
    (
        "The Read Queen",
        "Lafayette, Colorado",
        "Founded by friends Deirdre and Barbra, an independent bookstore and coffee shop in a century-old building, and a community hub dedicated to keeping local bookselling alive. Every book we have bought so far &#8212; thirty copies and counting &#8212; came off their shelves, and so did our first ten journals.",
        "https://thereadqueen.com",
        "thereadqueen.com",
    ),
    (
        "Ruff House Print Shop",
        "Lawrence, Kansas",
        "Jill Shephard runs a letterpress studio and boutique paperie making paper goods and stationery, grown out of her own entrepreneurial vision and her love of design. The gel pens in every kit are hers.",
        "https://www.ruffhouseprintshop.com",
        "ruffhouseprintshop.com",
    ),
    (
        "Sunshine and Laurel Art",
        "Colorado",
        "Rebekah is a landscape artist whose expressive acrylic paintings blend realism with texture. Inspired by the beauty of nature, her work invites you to slow down and reconnect with the world around you. Twelve of her journals are in our stock.",
        "https://sunshineandlaurelart.com/",
        "sunshineandlaurelart.com",
    ),
    (
        "Ginkgo by Laura",
        "Etsy",
        "Laura is a biologist and gardener who draws colorful botanicals inspired by traditional fraktur folk art &#8212; a whimsical blend of botanical illustration and fantastical color. Fifteen of her journals are in our stock.",
        "https://www.etsy.com/shop/GinkgoByLaura",
        "etsy.com/shop/GinkgoByLaura",
    ),
    (
        "The Towne Witch",
        "Etsy",
        "Cassandra makes handmade pieces with a touch of enchantment &#8212; nature and mystical aesthetics, crafted into meaningful treasures with a whimsical flair. She made the bookmarks.",
        "https://www.etsy.com/shop/TowneWitch",
        "etsy.com/shop/TowneWitch",
    ),
    (
        "Magnifique Hearts",
        "South Boston, Massachusetts",
        "Elegant, affordable jewelry and accessories from a business dedicated to women&#8217;s empowerment, with a portion of sales benefiting She&#8217;s the First. Ours are the stickers and the pins.",
        "https://www.instagram.com/magnifiquehearts/",
        "@magnifiquehearts",
    ),
]

MAKERS_LOVED = [
    (
        "Book Club Society",
        "Omaha, Nebraska",
        "Michelle and Megan built a dedicated space for book clubs, spontaneous visits and relaxed reading &#8212; part bookshop, part gathering spot, and the answer to &#8220;where should we go for book club?&#8221;",
        "https://www.thebookclubsociety.com",
        "thebookclubsociety.com",
    ),
    (
        "The Next Chapter",
        "Omaha, Nebraska",
        "Established in 2019 by Shelly Mutum, a woman-owned independent bookstore built on a fifty-year family legacy of bookselling, and a community hub in its own right.",
        "https://www.nextchapterbooksandgifts.com/",
        "nextchapterbooksandgifts.com",
    ),
]


MAKER_TMPL = """      <div class="maker">
        <div>
          <h3>{name}</h3>
          <p class="label">{place}</p>
        </div>
        <p>{blurb}</p>
        <a class="xref maker__link" href="{url}" rel="noopener">{label} {arrow}</a>
      </div>"""


def makers_markup(items):
    return "\n".join(
        MAKER_TMPL.format(
            name=name, place=place, blurb=blurb, url=url, label=label, arrow=ARROW
        )
        for name, place, blurb, url, label in items
    )


page(
    "makers",
    "Women-Owned Makers",
    "The women-owned businesses whose goods go into a Gathered Pages box, and the bookshops, artists and makers we love and buy from.",
    pagehead(
        "The women we buy from",
        "A book by a woman, printed on a pen made by a woman, sold by a woman who owns her shop. We would rather build that ecosystem than describe it.",
        "makers-table.jpg",
        "A worktable of poppy-covered journals, sage gel pens, jute twine, kraft hang-tags and a letterpress card.",
        "<span>Our makers</span>",
        "50% 55%",
    )
    + """<section class="section">
  <div class="wrap">
    <div class="section-intro" data-rise>
      <h2>In the box today</h2>
      <p>Six women-owned businesses we have already paid, for goods sitting in our stock right now. Every one of them is a line on our expense log.</p>
    </div>
    <div class="makers mt-6" data-rise>
"""
    + makers_markup(MAKERS_IN_BOX)
    + """
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap">
    <div class="section-intro" data-rise>
      <h2>Women-owned bookshops we love</h2>
      <p>Two more shops whose work fits what we are trying to do, and who we are working toward. Worth your money whether or not you ever open one of our boxes.</p>
    </div>
    <div class="makers mt-6" data-rise>
"""
    + makers_markup(MAKERS_LOVED)
    + """
    </div>
  </div>
</section>

<section class="section section--navy">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>
        <div class="section-intro">
          <h2>Make something we should be buying?</h2>
          <p>We are always looking for women artists who make journals, printers and paper goods makers, and independent bookshops we can order from.</p>
        </div>
        <p class="mt-4 text-soft measure">Featured artists are credited on the printed art card that goes into every kit, named on this page, and tagged wherever we post about that box. If you make journals, cards, bookmarks, small goods or artwork, we would like to see it.</p>
        <div class="btn-row">
          <a class="btn btn--cream" href="contact.html#makers">Send us your work</a>
        </div>
      </div>
      <figure class="figure plate" data-rise>
        <img srcset="assets/img/plate-poppy-480.jpg 480w, assets/img/plate-poppy.jpg 880w" sizes="(max-width: 900px) 100vw, 40vw" src="assets/img/plate-poppy.jpg" width="880" height="1173" loading="lazy" alt="A botanical specimen plate of a single corn poppy with a bud, a seed pod and sage foliage, on aged cream paper.">
        <figcaption class="plate-caption">The kind of thing that ends up on an art card.</figcaption>
      </figure>
    </div>
  </div>
</section>

"""
    + CLOSING_CTA,
)

# --------------------------------------------------------------- donate ----

page(
    "donate",
    "Donate",
    "Give once or monthly to put books, journals and pens from women-owned makers into the hands of women who need connection. Our 501(c)(3) application is pending.",
    pagehead(
        "Every box begins<br>a conversation.",
        "A gift buys a book by a woman author, a journal and pen from a woman-owned maker, an art card, and the guide that lets any facilitator run the whole club. Then it buys nine more.",
        "poppy-seeds.jpg",
        "A kraft seed envelope spilling poppy seed across a navy painted board, three dried seed pods and a coil of twine alongside.",
        "<span>Donate</span>",
        "45% 50%",
    )
    + """<section class="section">
  <div class="wrap wrap--mid">
    <div class="notice" data-rise>
      <p><strong>Please read this before you give.</strong></p>
      <p>Gathered Pages Collective is a Colorado nonprofit corporation, incorporated 10 June 2026, EIN 42-3092238. Our application for 501(c)(3) recognition has been submitted and is <strong>pending</strong> with the IRS. Until it is granted we cannot tell you your gift is tax-deductible, and we are not going to imply it. If deductibility matters to you, wait for us &#8212; we will say so here the day it lands.</p>
    </div>

  </div>
</section>

<section class="section section--navy section--flush-top">
  <div class="wrap">
    <div class="ruled-head mt-7" data-rise>
      <span class="label label--orange">What a gift buys</span>
      <span class="label">Planning ranges, per woman</span>
    </div>
    <dl class="ledger" data-rise>
      <div><dt>A pen</dt><dd>$6.75 &#183; A gel pen from Ruff House Print Shop, and the small pleasure of writing with something nicer than you expected.</dd></div>
      <div><dt>A journal</dt><dd>$7.30 &#8211; $20.27 &#183; The spread is real: the journals come from three different women artists, and we pay each of them her price.</dd></div>
      <div><dt>A book</dt><dd>$20.20 &#8211; $21.85 &#183; Bought at near retail from a woman-owned bookshop rather than wholesale from a warehouse.</dd></div>
      <div><dt>One woman&#8217;s kit</dt><dd>About $40 &#8211; $55 &#183; The book, the journal and the pen, plus the art card, bookmark, letter and packaging around them.</dd></div>
      <div><dt>A whole club</dt><dd>About $400 &#8211; $550 &#183; Ten kits, one carton, one facilitator, one group of women who did not know each other last month.</dd></div>
    </dl>
    <div class="btn-row" data-rise>
      <a class="btn btn--donate" href="mailto:jamie@gatheredpages.org?subject=I%20would%20like%20to%20give%20to%20Gathered%20Pages">Give once</a>
      <a class="btn btn--outline" href="mailto:jamie@gatheredpages.org?subject=I%20would%20like%20to%20give%20monthly%20to%20Gathered%20Pages">Give monthly</a>
    </div>
    <p class="mt-4 text-soft fine">These are prices we have actually paid, taken from our own expense log &#8212; not giving tiers. Give any amount; nothing is too small.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-intro" data-rise>
      <h2>Other ways to help</h2>
      <p>Money is the fastest, but it is not the only useful thing you have.</p>
    </div>
    <div class="doors mt-6">
      <a class="door" href="contact.html#introduce" data-rise>
        <div class="door__figure"><img srcset="assets/img/circle-of-chairs-600.jpg 600w, assets/img/circle-of-chairs-900.jpg 900w, assets/img/circle-of-chairs-1100.jpg 1100w, assets/img/circle-of-chairs.jpg 1800w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 30vw" src="assets/img/circle-of-chairs.jpg" width="1800" height="1012" loading="lazy" alt="A circle of chairs waiting in a community room."></div>
        <h3>Introduce us</h3>
        <p>Know a shelter, recovery program, senior center or staff room serving women? An introduction is worth more to us than a check.</p>
        <span class="door__more">Make an introduction """ + ARROW + """</span>
      </a>
      <a class="door" href="partner.html" data-rise>
        <div class="door__figure"><img srcset="assets/img/kraft-cartons-800.jpg 800w, assets/img/kraft-cartons-1100.jpg 1100w, assets/img/kraft-cartons.jpg 1600w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 30vw" src="assets/img/kraft-cartons.jpg" width="1600" height="1067" loading="lazy" alt="Kraft cartons tied with twine waiting by a doorway."></div>
        <h3>Host a club</h3>
        <p>If you run or work with a group of women yourself, apply to host. We provide everything; you gather them.</p>
        <span class="door__more">Apply to host """ + ARROW + """</span>
      </a>
      <a class="door" href="makers.html" data-rise>
        <div class="door__figure"><img srcset="assets/img/makers-table-800.jpg 800w, assets/img/makers-table-1100.jpg 1100w, assets/img/makers-table.jpg 1600w" sizes="(max-width: 900px) calc(100vw - 4.5rem), 30vw" src="assets/img/makers-table.jpg" width="1600" height="1067" loading="lazy" alt="Journals, pens, twine and kraft tags on a maker&#8217;s worktable."></div>
        <h3>Buy from our makers</h3>
        <p>Every business on our makers page is women-owned and worth your money whether or not it ever comes through us.</p>
        <span class="door__more">See the makers """ + ARROW + """</span>
      </a>
    </div>
  </div>
</section>

<section class="section section--warm">
  <div class="wrap">
    <div class="quote-band">
      <figure class="quote" data-rise>
        <p>&#8220;Women survive by holding one another up.&#8221;</p>
        <figcaption>Lisa See, <cite>The Island of Sea Women</cite></figcaption>
      </figure>
      <div data-rise>
        <p class="text-soft">If you would rather talk to a person before giving, our founder reads every message herself.</p>
        <a class="xref" href="contact.html">Write to Jamie """ + ARROW + """</a>
      </div>
    </div>
  </div>
</section>
""",
)

# -------------------------------------------------------------- contact ----

page(
    "contact",
    "Contact",
    "Write to Gathered Pages Collective — to host a club, to introduce us to a group, to show us your work, or just to tell us what you are reading.",
    pagehead(
        "Get in touch",
        "One founder reads all of this. Tell us which of these you are and we will answer properly.",
        "pressed-poppies.jpg",
        "An open herbarium album of pressed orange poppies and sage sprigs mounted on aged cream pages.",
        "<span>Contact</span>",
        "40% 55%",
    )
    + """<section class="section">
  <div class="wrap">
    <div class="split split--wide-text">
      <div data-rise>

        <div class="section-intro mb-5">
          <h2>Send a message</h2>
        </div>

        <form class="form" action="mailto:jamie@gatheredpages.org" method="post" enctype="text/plain">
          <div class="field">
            <label for="c-topic">What is this about?</label>
            <select id="c-topic" name="topic">
              <option>Hosting a book club</option>
              <option>Introducing you to a group</option>
              <option>I make something you should see</option>
              <option>Donating or fundraising</option>
              <option>Press or partnership</option>
              <option>Something else</option>
            </select>
          </div>

          <div class="field-row">
            <div class="field">
              <label for="c-name">Your name</label>
              <input id="c-name" name="name" type="text" autocomplete="name" required>
            </div>
            <div class="field">
              <label for="c-email">Email</label>
              <input id="c-email" name="email" type="email" autocomplete="email" required>
            </div>
          </div>

          <div class="field">
            <label for="c-message">Message</label>
            <textarea id="c-message" name="message" required></textarea>
          </div>

          <div class="btn-row btn-row--flush">
            <button class="btn btn--navy" type="submit">Send</button>
            <a class="btn btn--outline" href="mailto:{email}">Email directly</a>
          </div>
          <p class="field-hint">This opens your email app with your message filled in. If nothing happens, write to <a href="mailto:{email}">{email}</a> instead.</p>
        </form>
      </div>

      <div data-rise>
        <dl class="ledger">
          <div><dt>Email</dt><dd><a href="mailto:{email}">{email}</a></dd></div>
          <div><dt>Instagram</dt><dd><a href="{instagram}" rel="noopener">@gatheredpagescollective</a></dd></div>
          <div><dt>Where we are</dt><dd>Colorado, and Nebraska about half the time.</dd></div>
          <div><dt>Legal</dt><dd>Gathered Pages Collective, a Colorado nonprofit corporation. EIN 42-3092238. 501(c)(3) application pending.</dd></div>
        </dl>

        <div class="mt-6" id="introduce">
          <h3>Introducing us to a group</h3>
          <p class="text-soft measure mt-3">Tell us the organization, the city, and the name of the person who actually convenes the women &#8212; the activities coordinator, the program director, the librarian. We will make the approach ourselves, and we will mention you sent us unless you would rather we didn&#8217;t.</p>
        </div>

        <div class="mt-6" id="makers">
          <h3>If you make things</h3>
          <p class="text-soft measure mt-3">Send a link and a sentence about what you make. We buy journals, pens, cards, bookmarks and small paper goods, and we feature one woman artist per box on a printed art card she can point her own audience toward.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section--navy section--tight">
  <div class="wrap">
    <div class="statement-grid">
      <div data-rise>
        <p class="statement">Or simply tell us <em>what you&#8217;re reading.</em></p>
      </div>
      <div data-rise>
        <p class="text-soft">Genuinely. Half of what ends up on our reading list arrived that way, and the fastest way to be useful to a book club organization is to recommend a book.</p>
        <div class="btn-row">
          <a class="btn btn--cream" href="reading-list.html">See what&#8217;s on the list</a>
        </div>
      </div>
    </div>
  </div>
</section>
""".replace("{email}", EMAIL).replace("{instagram}", INSTAGRAM),
)

# --------------------------------------------------------------------------
# Write
# --------------------------------------------------------------------------

def build():
    os.makedirs(SITE, exist_ok=True)
    for p in PAGES:
        html = head(p) + masthead(p["slug"]) + p["body"] + FOOTER
        # collapse accidental blank runs
        html = re.sub(r"\n{3,}", "\n\n", html)
        path = os.path.join(SITE, p["slug"] + ".html")
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("wrote", os.path.basename(path), len(html) // 1024, "KB")

    # robots + sitemap
    with io.open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)

    urls = "\n".join(
        "  <url><loc>%s/%s</loc></url>"
        % (SITE_URL, "" if p["slug"] == "index" else p["slug"] + ".html")
        for p in PAGES
    )
    with io.open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % urls
        )
    print("wrote robots.txt, sitemap.xml")


if __name__ == "__main__":
    build()
