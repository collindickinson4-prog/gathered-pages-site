# -*- coding: utf-8 -*-
"""
Gathered Pages Collective — static site check.

    python tools/check_site.py

Exits 0 if the site is sound, 1 if anything is broken. Run it after editing
any page. It checks the things that silently break a hand-edited static site:
unbalanced tags, dead links and anchors, missing image files, images without
alt text, and pages that lost a required piece of chrome.
"""

import io
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

problems = []
notes = []


def fail(page, msg):
    problems.append("%s: %s" % (page, msg))


class Balance(HTMLParser):
    """Catches unclosed and mismatched elements — the classic hand-edit break."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append("stray </%s> at line %d" % (tag, self.getpos()[0]))
            return
        open_tag, line = self.stack.pop()
        if open_tag != tag:
            self.errors.append(
                "</%s> at line %d closes <%s> opened at line %d"
                % (tag, self.getpos()[0], open_tag, line)
            )


def check_page(name, src):
    # --- structure -------------------------------------------------------
    b = Balance()
    b.feed(src)
    for e in b.errors:
        fail(name, e)
    for tag, line in b.stack:
        fail(name, "<%s> opened at line %d is never closed" % (tag, line))

    # --- required chrome -------------------------------------------------
    if '<html lang="en">' not in src:
        fail(name, 'missing <html lang="en">')
    if not re.search(r"<title>[^<]+</title>", src):
        fail(name, "missing or empty <title>")
    if not re.search(r'<meta name="description" content="[^"]{20,}"', src):
        fail(name, "missing or too-short meta description")

    h1s = re.findall(r"<h1[ >]", src)
    if len(h1s) != 1:
        fail(name, "expected exactly one <h1>, found %d" % len(h1s))

    if 'class="skip"' not in src:
        fail(name, "missing skip-to-content link")
    if '<main id="main">' not in src:
        fail(name, "missing <main id=\"main\">")
    if src.count('class="btn btn--donate" href="donate.html"') < 1:
        fail(name, "the masthead Donate Now button is missing")
    if 'href="index.html"' not in src:
        fail(name, "no link back to the home page")

    # --- images ----------------------------------------------------------
    for m in re.finditer(r"<img\b[^>]*>", src):
        tag = m.group(0)
        line = src[: m.start()].count("\n") + 1
        if 'alt="' not in tag:
            fail(name, "line %d: <img> without alt" % line)
        elif re.search(r'alt="\s*"', tag) and "aria-hidden" not in tag:
            fail(name, "line %d: <img> with empty alt and no aria-hidden" % line)
        if "width=" not in tag or "height=" not in tag:
            fail(name, "line %d: <img> without width/height (causes layout shift)" % line)

    # --- leftover template placeholders ----------------------------------
    for m in re.finditer(r"\{[a-z_]+\}", src):
        fail(name, "unreplaced template placeholder %s" % m.group(0))

    # --- links, anchors, assets -----------------------------------------
    ids = set(re.findall(r'id="([^"]+)"', src))

    for m in re.finditer(r'(?:href|src)="([^"]+)"', src):
        target = m.group(1)
        line = src[: m.start()].count("\n") + 1
        if target.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
            continue
        if target.startswith("#"):
            if len(target) > 1 and target[1:] not in ids:
                fail(name, "line %d: #%s does not exist on this page" % (line, target[1:]))
            continue
        path, _, frag = target.partition("#")
        full = os.path.join(SITE, path.replace("/", os.sep))
        if not os.path.exists(full):
            fail(name, "line %d: %s does not exist" % (line, target))
        elif frag and path.endswith(".html"):
            tgt = io.open(full, encoding="utf-8").read()
            if frag not in set(re.findall(r'id="([^"]+)"', tgt)):
                fail(name, "line %d: %s has no element with id=%s" % (line, path, frag))

    for m in re.finditer(r'srcset="([^"]+)"', src):
        for part in m.group(1).split(","):
            url = part.strip().split(" ")[0]
            if url and not os.path.exists(os.path.join(SITE, url.replace("/", os.sep))):
                fail(name, "srcset references missing file %s" % url)


def main():
    pages = sorted(f for f in os.listdir(SITE) if f.endswith(".html"))
    if not pages:
        print("No HTML found in site/")
        return 1

    for name in pages:
        check_page(name, io.open(os.path.join(SITE, name), encoding="utf-8").read())

    # --- stylesheet asset references -------------------------------------
    css_path = os.path.join(SITE, "assets", "css")
    for css_name in os.listdir(css_path):
        if not css_name.endswith(".css"):
            continue
        css = io.open(os.path.join(css_path, css_name), encoding="utf-8").read()
        for m in re.finditer(r'url\(["\']?([^"\')]+)["\']?\)', css):
            u = m.group(1)
            if u.startswith(("http", "data:")):
                continue
            full = os.path.normpath(os.path.join(css_path, u.replace("/", os.sep)))
            if not os.path.exists(full):
                fail("assets/css/" + css_name, "url(%s) does not resolve" % u)

    # --- launch blockers, reported but not failures ----------------------
    for name in pages:
        src = io.open(os.path.join(SITE, name), encoding="utf-8").read()
        if "YOUR_FORM_ID" in src:
            notes.append("%s: form still posts to the YOUR_FORM_ID placeholder" % name)
        if 'class="todo' in src:
            notes.append("%s: has a visible pre-launch TODO box" % name)

    print("Checked %d pages in site/\n" % len(pages))

    if notes:
        print("Pre-launch reminders (not failures):")
        for n in notes:
            print("  - " + n)
        print()

    if problems:
        print("FAILED - %d problem(s):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1

    print("PASSED - structure, links, anchors, assets and image attributes are sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
