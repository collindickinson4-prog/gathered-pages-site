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
