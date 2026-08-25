# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Plain static HTML/CSS/JS, hand-built, no build step. Chosen by the user so the
site can be hosted cheaply (GoDaddy, Netlify, Cloudflare Pages) and handed to a
non-developer later. Site source lives in `site/`.

## Users

Four distinct visitors arrive at gatheredpages.org, and the site has to route
each one in seconds:

1. **A convener** — an activities director at a senior center, a program
   director at a women's shelter, a school librarian, a nurse manager, a reentry
   coordinator. She already gathers women. She is overloaded. She wants to know
   what she has to do, and the answer is "almost nothing."
2. **A donor or supporter** — someone who read the founder's story or saw an
   Instagram post and wants to help. She needs one obvious action.
3. **A woman who wants to join a club** — she found the site looking for
   community and needs to know whether there is a way in.
4. **A partner maker or bookstore** — a woman-owned business wondering how to
   be part of the ecosystem.

## Product Purpose

Gathered Pages Collective connects women through the power of shared stories,
creating spaces where every woman can find connection, belonging, and the
confidence to grow.

The mechanism is the **Book Club in a Box** — a complete, turnkey book club kit
delivered at no cost to the participating organization. Each kit holds a book,
a journal and pen from women-owned makers, a printed art card by a featured
woman artist, a welcome letter, and a facilitator guide with discussion
questions. The partner organization gathers the women. Gathered Pages provides
everything else.

Success is a woman in a shelter, a recovery program, a senior center, a
classroom, or a reentry program sitting in a circle with a book in her hands
and other women who will listen.

## Positioning

Two things a neighboring nonprofit could not truthfully copy:

1. **Turnkey, at zero cost to the partner.** The pitch to a convener is "we
   hand you everything; you bring the women." Not a grant, not a curriculum, not
   a training — a physical box that arrives ready.
2. **The whole supply chain is women.** Books by women authors wherever
   possible. Journals from women artists. Pens from Ruff House Print Shop.
   Books bought from women-owned independent bookstores. Every dollar spent
   reinforces the ecosystem the mission is trying to strengthen. This is
   described internally as "investing in the ecosystem we hope to strengthen,"
   not as a preference.

## Operating Context

- **Legal status:** Colorado nonprofit corporation, incorporated 6/10/2026.
  EIN 42-3092238. 501(c)(3) status **approved.** Gifts may be described as
  tax-deductible to the extent allowed by law.
- **Program models, in sequence:** donated boxes to partner organizations
  (now); paid "buy a box, give a box" boxes as the funding engine (on
  approval); virtual application-based clubs (once one facilitator playbook is
  proven). Only the donated model is live today.
- **Delivery:** first Colorado groups are hand-delivered. Shipping later.
- **Kit contents:** one book, one journal, one pen, an art card, a welcome
  letter, a facilitator guide, a bookmark. Ten kits nest in one kraft carton
  for a facilitator.
- **Board:** Tiffany Anderson, Amber Story, Crystal Gippe. Founder: Jamie
  Dickinson — lawyer, yoga instructor, mother, wife; splits time between
  Colorado and Nebraska.
- **Contact:** jamie@gatheredpages.org. Instagram @GatheredPagesCollective.
- **Beta phase:** three pilot groups are being recruited (Centennial Elementary
  teachers, Women's Center for Advancement staff, Omaha Public Library staff).
  No completed programs, no participant testimonials, no impact numbers exist
  yet.

## Capabilities and Constraints

- Static site, hosted on Vercel. No CMS, no database, no build step. The only
  server-side code is a handful of functions under `api/`, each one calling a
  REST API with `fetch`.
- **Stripe** takes the donations, live since 25 August 2026. Gifts are one-time,
  monthly or annual, at $25 / $50 / $100 / $250 / $500 or an amount the donor
  types, from $5 to $10,000. Card details never touch the site; Stripe hosts
  the checkout page.
- **Resend** sends the contact form and the year-end giving statements, from
  the verified subdomain `send.gatheredpages.org`. **Kit** holds the newsletter
  list.
- Pages: Home, About, How It Works, Meet Our Founder, Meet The Board, Partner
  With Us, What's In The Box, Women-Owned Partners, Contact, Donate, Newsletter,
  and the two thank-you pages people land on after giving or subscribing.
- **Undecided product facts, not to be invented:** box price for the paid tier
  (the $650 group purchase is written but not open); number of women served;
  launch dates; named partner organizations that have not agreed publicly.

## Brand Commitments

Binding. Taken from `Gathered_Pages_Brand_Guide_2.pdf`.

- **Name:** Gathered Pages Collective. "COLLECTIVE" is set in caps with wide
  letter-spacing.
- **Logo:** an open book cradling three poppies, navy and orange, over the
  wordmark. Files in `source/Gathered Pages Shared Folder/Logo/`. Do not
  recolor, restyle, stretch, or retype it. Minimum 130px wide on screen. Keep
  clear space equal to the height of the book mark. The book-and-poppy mark may
  stand alone as a favicon or avatar.
- **Palette:** Navy `#16294D` (primary), Poppy Orange `#E15D2A` (primary), Sage
  Green `#708058` (secondary), Warm Cream `#F5F1E8` (neutral/bg), Kraft
  `#C6A56B` (neutral), Ink `#2A2E33` (text), deepest navy `#0C2454` for poppy
  centers and outlines. Navy and orange are the heart of the brand.
- **Typography:** Cormorant Garamond for display and headlines. Lato for body
  and labels. Both Google Fonts.
- **Motif:** the open book and the poppy. Poppies in orange, sprigs in sage,
  hand-drawn in feel, simple.
- **Voice:** warm, hopeful, personal, dignified. We speak to women as friends,
  never as "the needy." Short, heartfelt sentences. The word "underserved" is
  deliberately avoided in the mission.
- **Taglines:** "Stories connect us." · "Connecting women through shared
  stories, one box at a time." · "Books create conversation. Conversation
  creates connection. Connection creates hope."
- **Materials the brand lives on:** kraft, twine, paper crinkle, recycled,
  plastic-free. No gloss, no plastic.
- **Visual reference the user pinned:** the UNICEF Australia homepage — a
  full-bleed photographic hero, a headline set very large over it, and a single
  high-contrast donate button. The donate button must be orange and visible on
  every page at every scroll position.
- **Hard constraint from the user:** generated imagery must contain **no
  people**.

## Evidence on Hand

Real, usable:

- Founder's essay, first person, ~800 words — `Website/Meet Our Founder.docx`.
- Mission statement and full "Our Story" narrative — `Business Plan.docx`.
- Six named values with written definitions — partner one-pager and Tiff's notes.
- Four "ways to support" with written copy — partner one-pager.
- Eight women-owned businesses with real bios and real URLs —
  `Notes/Artist Bios.docx`.
- ~50 curated book titles grouped by category — `The Boxes/The Books.docx`.
- Twelve sourced book quotes about women, belonging, and connection —
  `Notes/Favorite Book Quotes.docx`.
- Kit photography/mockup — `The Boxes/Kit Concept.png`.
- Logo in PNG, JPG, EPS, AI — `Logo/`.
- Brand guide PDF — `The Boxes/Gathered_Pages_Brand_Guide_2.pdf`.

Absent, and must not be fabricated: participant testimonials, photos of real
participants, number of women or groups served, dollars raised, named partner
organizations, press coverage, staff beyond the founder and three board members,
board member bios (drafted but not in the shared folder).

## Product Principles

1. **Turnkey is the whole pitch.** Every page aimed at a convener must reduce
   her perceived work, not describe our program.
2. **Route four visitors in five seconds.** A convener, a donor, a woman who
   wants to join, and a maker each need their own obvious door from the
   homepage.
3. **Dignity over pity.** Women are the subject, never the case study. No
   before-and-after framing, no "the needy," no charity-appeal guilt.
4. **Say only what is true today.** No impact numbers, no testimonials.
   Tax-deductibility may be stated now that 501(c)(3) is approved. Being early
   is part of the story; pretending not to be is not.
5. **The ecosystem is the product.** Every woman-owned maker, bookstore, and
   author named on the site is both a credit we owe and a reason someone else
   shares us.

## Accessibility & Inclusion

The audience skews toward women in senior centers and recovery and shelter
settings, often reading on older phones over slow connections, sometimes on a
facility's shared desktop. Targets: WCAG AA contrast throughout, real focus
states, 16px minimum body text, full keyboard operability, no motion that
cannot be reduced, and a page weight that loads on a bad connection.
