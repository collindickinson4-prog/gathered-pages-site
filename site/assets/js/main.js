/* Gathered Pages Collective — progressive enhancement only.
   Every page works with this file removed. */

(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- Mobile navigation ------------------------------------------------ */

  var toggle = document.querySelector('[data-nav-toggle]');
  var nav = document.getElementById('site-nav');

  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      nav.setAttribute('data-open', String(open));
      document.body.classList.toggle('is-nav-open', open);
      var label = toggle.querySelector('.nav-toggle__text');
      if (label) label.textContent = open ? 'Close' : 'Menu';
    };

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });

    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) setOpen(false);
    });
  }

  /* ---- Masthead compacts once you are past the first screenful ---------- */

  var masthead = document.querySelector('.masthead');

  if (masthead) {
    var compact = false;
    var syncMasthead = function () {
      var next = window.scrollY > 140;
      if (next === compact) return;
      compact = next;
      masthead.classList.toggle('is-compact', compact);
    };
    syncMasthead();
    window.addEventListener('scroll', syncMasthead, { passive: true });
  }

  /* ---- Seed packets: front / back --------------------------------------- */

  Array.prototype.forEach.call(
    document.querySelectorAll('[data-packet]'),
    function (button) {
      var back = document.getElementById(button.getAttribute('aria-controls'));
      if (!back) return;
      button.addEventListener('click', function () {
        var open = button.getAttribute('aria-expanded') === 'true';
        button.setAttribute('aria-expanded', String(!open));
        back.setAttribute('data-open', String(!open));
      });
    }
  );

  /* ---- One authored reveal, once, on the way in ------------------------- */

  var risers = document.querySelectorAll('[data-rise]');

  if (!risers.length) return;

  if (reduced || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(risers, function (el) { el.classList.add('is-in'); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var group = entry.target.parentElement
        ? Array.prototype.filter.call(entry.target.parentElement.children, function (c) {
            return c.hasAttribute && c.hasAttribute('data-rise');
          })
        : [];
      var index = group.indexOf(entry.target);
      entry.target.style.setProperty('--rise-delay', (index > 0 ? Math.min(index, 5) * 0.07 : 0) + 's');
      entry.target.classList.add('is-in');
      observer.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

  Array.prototype.forEach.call(risers, function (el) { observer.observe(el); });
})();

/* Newsletter signup. Posts to /api/subscribe, which holds the Kit credentials
   server-side. Without JavaScript the form does nothing, so the status line
   tells the reader to email instead. */
(function () {
  var forms = document.querySelectorAll('[data-newsletter]');
  if (!forms.length) return;

  Array.prototype.forEach.call(forms, function (form) {
    var status = form.querySelector('[data-newsletter-status]');
    var button = form.querySelector('button[type="submit"]');
    var buttonText = button ? button.textContent : '';

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (form.dataset.sending === 'true') return;

      var data = new FormData(form);
      var payload = {
        email: (data.get('email') || '').toString().trim(),
        first_name: (data.get('first_name') || '').toString().trim(),
        company: (data.get('company') || '').toString()
      };

      form.dataset.sending = 'true';
      if (button) { button.disabled = true; button.textContent = 'Signing you up\u2026'; }
      if (status) { status.textContent = ''; status.classList.remove('is-error', 'is-done'); }

      fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (response) {
          return response.json().catch(function () { return {}; }).then(function (body) {
            return { ok: response.ok, body: body };
          });
        })
        .then(function (result) {
          if (result.ok) {
            form.reset();
            if (status) {
              status.textContent = 'You are on the list…';
              status.classList.add('is-done');
            }
            window.location.href = 'newsletter-thank-you.html';
          } else if (status) {
            status.textContent = result.body.error || 'Something went wrong. Please email jamie@gatheredpages.org.';
            status.classList.add('is-error');
          }
        })
        .catch(function () {
          if (status) {
            status.textContent = 'Something went wrong. Please email jamie@gatheredpages.org.';
            status.classList.add('is-error');
          }
        })
        .then(function () {
          form.dataset.sending = 'false';
          if (button) { button.disabled = false; button.textContent = buttonText; }
        });
    });
  });
})();

/* Giving panel — frequency, amount, one action. The choice is assembled here
   and sent to /api/checkout, which asks Stripe for a Checkout Session and
   sends back its URL. Nothing about a card is ever typed on this site. */
(function () {
  var panel = document.querySelector('[data-give-panel]');
  if (!panel) return;

  var tabs = panel.querySelectorAll('[data-frequency]');
  var tiles = panel.querySelectorAll('[data-amount]');
  var other = panel.querySelector('[data-give-other]');
  var otherInput = panel.querySelector('[data-give-other-input]');
  var submit = panel.querySelector('[data-give-submit]');
  var status = panel.querySelector('[data-give-status]');

  var SUFFIX = { once: '', monthly: ' monthly', yearly: ' a year' };
  var MIN = 5;
  var MAX = 10000;

  var frequency = 'once';
  var choice = '50';

  function amount() {
    if (choice !== 'other') return Number(choice);
    var typed = Number((otherInput.value || '').replace(/[^0-9.]/g, ''));
    return typed > 0 ? Math.round(typed * 100) / 100 : 0;
  }

  function press(nodes, node) {
    Array.prototype.forEach.call(nodes, function (n) {
      n.setAttribute('aria-pressed', String(n === node));
    });
  }

  function relabel() {
    var value = amount();
    var money = value ? '$' + (value % 1 ? value.toFixed(2) : value) : '';
    submit.textContent = 'Give' + (money ? ' ' + money : '') + SUFFIX[frequency];
  }

  function clearStatus() {
    if (!status) return;
    status.textContent = '';
    status.classList.remove('is-error', 'is-done');
  }

  function fail(message) {
    if (!status) return;
    status.textContent = message;
    status.classList.remove('is-done');
    status.classList.add('is-error');
  }

  Array.prototype.forEach.call(tabs, function (tab) {
    tab.addEventListener('click', function () {
      frequency = tab.dataset.frequency;
      press(tabs, tab);
      clearStatus();
      relabel();
    });
  });

  Array.prototype.forEach.call(tiles, function (tile) {
    tile.addEventListener('click', function () {
      choice = tile.dataset.amount;
      press(tiles, tile);
      other.hidden = choice !== 'other';
      if (choice === 'other') otherInput.focus();
      clearStatus();
      relabel();
    });
  });

  otherInput.addEventListener('input', function () {
    clearStatus();
    relabel();
  });

  submit.addEventListener('click', function () {
    if (submit.dataset.sending === 'true') return;

    var value = amount();
    if (!value) return fail('Please choose or enter an amount.');
    if (value < MIN) return fail('The smallest gift we can take online is $' + MIN + '.');
    if (value > MAX) return fail('For gifts over $' + MAX.toLocaleString() + ', please email jamie@gatheredpages.org.');

    var buttonText = submit.textContent;
    submit.dataset.sending = 'true';
    submit.disabled = true;
    submit.textContent = 'Taking you to checkout…';
    clearStatus();

    function restore() {
      submit.dataset.sending = 'false';
      submit.disabled = false;
      submit.textContent = buttonText;
    }

    fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frequency: frequency, amount: value })
    })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (result.ok && result.body.url) {
          window.location.href = result.body.url;
          return;
        }
        fail(result.body.error || 'Something went wrong. Please email jamie@gatheredpages.org.');
        restore();
      })
      .catch(function () {
        fail('Something went wrong. Please email jamie@gatheredpages.org.');
        restore();
      });
  });

  relabel();
})();

/* Contact form — posts the message to /api/contact, which mails it to Jamie.
   The form used to open the visitor's own mail app, which warned about an
   insecure submission and lost the message for anyone without desktop mail. */
(function () {
  var form = document.querySelector('[data-contact]');
  if (!form) return;

  var status = form.querySelector('[data-contact-status]');
  var button = form.querySelector('button[type="submit"]');
  var buttonText = button ? button.textContent : '';

  function say(message, kind) {
    if (!status) return;
    status.textContent = message;
    status.classList.remove('is-error', 'is-done');
    if (kind) status.classList.add(kind);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (form.dataset.sending === 'true') return;

    var data = new FormData(form);
    var payload = {
      topic: (data.get('topic') || '').toString(),
      name: (data.get('name') || '').toString().trim(),
      email: (data.get('email') || '').toString().trim(),
      message: (data.get('message') || '').toString().trim(),
      company: (data.get('company') || '').toString()
    };

    if (!payload.name) return say('Please tell us your name.', 'is-error');
    if (!payload.email) return say('Please add your email so we can write back.', 'is-error');
    if (!payload.message) return say('Please write a message.', 'is-error');

    form.dataset.sending = 'true';
    if (button) { button.disabled = true; button.textContent = 'Sending\u2026'; }
    say('');

    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (result.ok) {
          form.reset();
          say('Thank you \u2014 your message is with Jamie. She answers everything herself, usually within a few days.', 'is-done');
        } else {
          say(result.body.error || 'Something went wrong. Please write to jamie@gatheredpages.org.', 'is-error');
        }
      })
      .catch(function () {
        say('Something went wrong. Please write to jamie@gatheredpages.org.', 'is-error');
      })
      .then(function () {
        form.dataset.sending = 'false';
        if (button) { button.disabled = false; button.textContent = buttonText; }
      });
  });
})();
