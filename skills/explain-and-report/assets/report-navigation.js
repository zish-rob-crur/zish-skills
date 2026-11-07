/* Progressive reading navigation; static links and article content work without JS. */
(function () {
  'use strict';

  function readingState({ top, bottom, viewportHeight, offset, sectionTops }) {
    const distance = bottom - top - (viewportHeight - offset);
    const atEnd = bottom <= viewportHeight + 1;
    const fraction = atEnd ? 1 : distance > 0 ? (offset - top) / distance : 0;
    const progress = Math.round(100 * Math.max(0, Math.min(1, fraction)));
    let active = -1;
    sectionTops.forEach((position, index) => {
      if (position <= offset + 1) active = index;
    });
    if (atEnd && sectionTops.length) active = sectionTops.length - 1;
    return { progress, active };
  }

  function initReadingNavigation(doc, win) {
    const report = doc.querySelector('.report');
    if (!report || report.classList.contains('navigation-ready')) return false;
    const main = report.querySelector('main#main');
    const rail = report.querySelector('.reading-rail');
    const outline = report.querySelector('details.report-outline');
    const nav = outline && outline.querySelector('nav');
    const summary = outline && outline.querySelector('summary');
    const progress = rail && rail.querySelector('[data-reading-progress]');
    const value = progress && progress.querySelector('[data-reading-value]');
    const bar = progress && progress.querySelector('[data-reading-bar]');
    if (!main || !rail || !outline || !nav || !summary || !progress || !value || !bar) return false;

    const entries = Array.from(nav.querySelectorAll('a[href^="#"]')).flatMap(link => {
      let target;
      try { target = doc.getElementById(decodeURIComponent(link.getAttribute('href').slice(1))); }
      catch (_) { return []; }
      return target && main.contains(target) ? [{ link, target }] : [];
    }).sort((a, b) => {
      const position = a.target.compareDocumentPosition(b.target);
      return position & 2 ? 1 : position & 4 ? -1 : 0;
    });
    if (!entries.length) return false;

    const wide = win.matchMedia('(min-width: 1440px)');
    let queued = false;

    function refresh() {
      // Both the sidebar and floating outline leave the top of the article clear.
      const offset = 24;
      doc.documentElement.style.setProperty('--reading-offset', `${offset}px`);
      const visible = entries.filter(entry => entry.target.getClientRects().length);
      const rect = main.getBoundingClientRect();
      const state = readingState({
        top: rect.top, bottom: rect.bottom, viewportHeight: win.innerHeight, offset,
        sectionTops: visible.map(entry => entry.target.getBoundingClientRect().top)
      });
      bar.value = state.progress;
      value.textContent = `${state.progress}%`;
      const active = visible[state.active];
      entries.forEach(entry => {
        if (entry === active) entry.link.setAttribute('aria-current', 'location');
        else entry.link.removeAttribute('aria-current');
      });
    }

    function schedule() {
      if (queued) return;
      queued = true;
      win.requestAnimationFrame(() => { queued = false; refresh(); });
    }

    function setMode() { outline.open = wide.matches; refresh(); }

    nav.addEventListener('click', event => {
      if (wide.matches || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
          (event.button != null && event.button !== 0)) return;
      const link = event.target.closest && event.target.closest('a');
      if (entries.some(entry => entry.link === link)) {
        outline.open = false;
        // Update the scroll offset before the browser follows the ordinary hash link.
        refresh();
      }
    });
    outline.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !outline.open) return;
      outline.open = false;
      if (nav.contains(doc.activeElement)) summary.focus();
      event.preventDefault();
      refresh();
    });
    doc.addEventListener('pointerdown', event => {
      if (!wide.matches && outline.open && !rail.contains(event.target)) {
        outline.open = false;
        refresh();
      }
    });
    outline.addEventListener('toggle', schedule);
    wide.addEventListener('change', setMode);
    win.addEventListener('scroll', schedule, { passive: true });
    for (const event of ['resize', 'hashchange', 'pageshow', 'load']) win.addEventListener(event, schedule);
    if (win.ResizeObserver) {
      const observer = new win.ResizeObserver(schedule);
      observer.observe(main);
      observer.observe(rail);
    }
    if (doc.fonts) doc.fonts.ready.then(schedule);

    report.classList.add('navigation-ready');
    progress.hidden = false;
    setMode();
    schedule();
    return true;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { readingState, initReadingNavigation };
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initReadingNavigation(document, window), { once: true });
  } else {
    initReadingNavigation(document, window);
  }
}());
