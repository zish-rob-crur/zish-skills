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

  function initThemeToggle(doc, report) {
    const toggle = report.querySelector('[data-theme-toggle]');
    if (!toggle || !doc.documentElement || typeof doc.documentElement.setAttribute !== 'function') return;
    function syncLabel() {
      const isLight = doc.documentElement.getAttribute && doc.documentElement.getAttribute('data-theme') === 'light';
      toggle.setAttribute('aria-pressed', isLight ? 'true' : 'false');
      toggle.textContent = isLight ? '☾ 深色阅读' : '☀ 浅色纸张';
    }
    syncLabel();
    toggle.addEventListener('click', () => {
      const current = doc.documentElement.getAttribute && doc.documentElement.getAttribute('data-theme');
      if (current === 'light') {
        if (doc.documentElement.removeAttribute) doc.documentElement.removeAttribute('data-theme');
      } else {
        doc.documentElement.setAttribute('data-theme', 'light');
      }
      syncLabel();
    });
  }

  function initCitationPreviews(doc, win, report, main) {
    if (typeof main.querySelectorAll !== 'function' || typeof doc.createElement !== 'function' || !doc.body) return;
    const citeLinks = Array.from(main.querySelectorAll('a[href^="#"]')).flatMap(link => {
      let id;
      try { id = decodeURIComponent(link.getAttribute('href').slice(1)); }
      catch (_) { return []; }
      const target = id && doc.getElementById(id);
      if (!target || target.tagName !== 'DT') return [];
      const dd = target.nextElementSibling;
      if (!dd || dd.tagName !== 'DD') return [];
      const code = dd.querySelector && dd.querySelector('code');
      const sourceText = code ? ` · ${code.textContent}` : '';
      const bodyText = Array.from(dd.querySelectorAll ? dd.querySelectorAll('p') : [])
        .map(p => p.textContent).join(' ') || dd.textContent;
      return [{ el: link, title: `证据 ${target.textContent}${sourceText}`, body: bodyText }];
    });
    const tipNodes = Array.from(main.querySelectorAll('[data-tip-title]')).flatMap(el => {
      const title = el.getAttribute('data-tip-title');
      const body = el.getAttribute('data-tip-body') || '';
      return title ? [{ el, title, body }] : [];
    });
    const items = [...citeLinks, ...tipNodes];
    if (!items.length) return;

    const popover = doc.createElement('div');
    popover.className = 'cite-popover';
    popover.setAttribute('role', 'tooltip');
    popover.hidden = true;
    doc.body.appendChild(popover);

    function show({ el, title, body }) {
      if (popover.replaceChildren) popover.replaceChildren();
      else popover.textContent = '';
      const heading = doc.createElement('strong');
      heading.textContent = title;
      popover.appendChild(heading);
      if (body) {
        const para = doc.createElement('p');
        para.textContent = body;
        popover.appendChild(para);
      }
      popover.hidden = false;
      const rect = el.getBoundingClientRect();
      const vw = win.innerWidth || 1280;
      const vh = win.innerHeight || 800;
      const left = Math.min(Math.max(16, rect.left), vw - 396);
      const top = Math.min(Math.max(12, rect.top + (rect.height || 20) + 10), vh - 140);
      if (popover.style) {
        popover.style.top = `${top}px`;
        popover.style.left = `${Math.max(16, left)}px`;
      }
    }

    function hide() { popover.hidden = true; }

    items.forEach(item => {
      item.el.addEventListener('mouseenter', () => show(item));
      item.el.addEventListener('mouseleave', hide);
      item.el.addEventListener('focus', () => show(item));
      item.el.addEventListener('blur', hide);
    });
    win.addEventListener('scroll', hide, { passive: true });
  }

  function initFloatDrawer(doc, win, report, scheduleTimer, cancelTimer) {
    if (typeof report.querySelectorAll !== 'function' || typeof doc.createElement !== 'function' || !doc.body) return;
    const rawTriggers = Array.from(report.querySelectorAll('[data-drawer-target]'));
    const triggers = rawTriggers.filter(el => {
      const id = el.getAttribute && el.getAttribute('data-drawer-target');
      return id && doc.getElementById(id);
    });
    if (!triggers.length) return;

    const drawer = doc.createElement('aside');
    drawer.className = 'explorer-float-drawer';
    drawer.setAttribute('aria-label', '明细检视窗');
    drawer.hidden = true;

    const bar = doc.createElement('div');
    bar.className = 'explorer-float-bar';
    const left = doc.createElement('div');
    left.className = 'float-bar-left';
    const badge = doc.createElement('span');
    badge.className = 'float-mode-badge';
    badge.textContent = '预览模式';
    const titleEl = doc.createElement('strong');
    titleEl.className = 'float-title';
    left.appendChild(badge);
    left.appendChild(titleEl);

    const actions = doc.createElement('div');
    actions.className = 'float-bar-actions';
    const pinBtn = doc.createElement('button');
    pinBtn.type = 'button';
    pinBtn.className = 'float-action-btn';
    pinBtn.setAttribute('data-drawer-pin', '');
    pinBtn.textContent = '固定窗口';
    const jumpBtn = doc.createElement('button');
    jumpBtn.type = 'button';
    jumpBtn.className = 'float-action-btn';
    jumpBtn.setAttribute('data-drawer-jump', '');
    jumpBtn.textContent = '定位原文';
    const closeBtn = doc.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'float-action-btn';
    closeBtn.setAttribute('data-drawer-close', '');
    closeBtn.textContent = '关闭';
    actions.appendChild(pinBtn);
    actions.appendChild(jumpBtn);
    actions.appendChild(closeBtn);
    bar.appendChild(left);
    bar.appendChild(actions);

    const body = doc.createElement('div');
    body.className = 'explorer-float-body';
    drawer.appendChild(bar);
    drawer.appendChild(body);
    doc.body.appendChild(drawer);

    let activeId = null;
    let drawerPinned = false;
    let drawerTimer = null;

    function clearDrawerTimer() {
      if (drawerTimer !== null) {
        cancelTimer(drawerTimer);
        drawerTimer = null;
      }
    }

    function stripIds(node) {
      if (!node || typeof node !== 'object') return;
      if (node.removeAttribute) node.removeAttribute('id');
      if (node.children) Array.from(node.children).forEach(stripIds);
    }

    function renderTarget(trigger, target) {
      if (body.replaceChildren) body.replaceChildren();
      else body.textContent = '';
      if (typeof target.cloneNode === 'function') {
        const clone = target.cloneNode(true);
        stripIds(clone);
        if (clone.tagName === 'DETAILS') clone.open = true;
        if (target.tagName === 'DT' && target.nextElementSibling && target.nextElementSibling.tagName === 'DD' &&
            typeof target.nextElementSibling.cloneNode === 'function') {
          const dl = doc.createElement('dl');
          dl.className = 'evidence-list';
          const dtClone = clone;
          const ddClone = target.nextElementSibling.cloneNode(true);
          stripIds(ddClone);
          dl.appendChild(dtClone);
          dl.appendChild(ddClone);
          body.appendChild(dl);
        } else {
          body.appendChild(clone);
        }
      } else {
        const p = doc.createElement('p');
        p.textContent = target.textContent || '';
        body.appendChild(p);
      }
      const title = (trigger.getAttribute('data-drawer-title') || trigger.textContent || activeId || '').trim();
      titleEl.textContent = title;
      const isCompare = trigger.getAttribute('data-drawer-wide') === 'true';
      if (drawer.classList) {
        drawer.classList.toggle('is-compare-mode', isCompare);
        drawer.classList.toggle('is-pinned', drawerPinned);
      }
    }

    function syncDrawerState() {
      badge.textContent = drawerPinned ? '已固定' : '预览模式';
      pinBtn.setAttribute('aria-pressed', drawerPinned ? 'true' : 'false');
      pinBtn.textContent = drawerPinned ? '取消固定' : '固定窗口';
      if (drawer.classList) drawer.classList.toggle('is-pinned', drawerPinned);
      if (drawerPinned) drawer.setAttribute('data-drawer-pinned', 'true');
      else drawer.removeAttribute('data-drawer-pinned');
      triggers.forEach(el => {
        const active = !drawer.hidden && el.getAttribute('data-drawer-target') === activeId;
        if (el.classList) el.classList.toggle('is-active-pill', active);
      });
    }

    function openDrawer(trigger, pinNow) {
      const id = trigger.getAttribute('data-drawer-target');
      const target = id && doc.getElementById(id);
      if (!target) return;
      clearDrawerTimer();
      activeId = id;
      if (pinNow) drawerPinned = true;
      renderTarget(trigger, target);
      drawer.hidden = false;
      syncDrawerState();
    }

    function closeDrawer() {
      clearDrawerTimer();
      drawerPinned = false;
      activeId = null;
      drawer.hidden = true;
      syncDrawerState();
    }

    function scheduleDrawerClose() {
      clearDrawerTimer();
      if (drawerPinned) return;
      drawerTimer = scheduleTimer(() => {
        drawerTimer = null;
        if (!drawerPinned) closeDrawer();
      }, 240);
    }

    triggers.forEach(trigger => {
      trigger.addEventListener('mouseenter', () => {
        clearDrawerTimer();
        if (!drawerPinned) openDrawer(trigger, false);
      });
      trigger.addEventListener('mouseleave', scheduleDrawerClose);
      trigger.addEventListener('click', event => {
        if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
            (event.button != null && event.button !== 0)) return;
        event.preventDefault();
        const id = trigger.getAttribute('data-drawer-target');
        if (drawerPinned && !drawer.hidden && activeId === id) {
          closeDrawer();
          return;
        }
        openDrawer(trigger, true);
      });
    });

    drawer.addEventListener('mouseenter', clearDrawerTimer);
    drawer.addEventListener('mouseleave', scheduleDrawerClose);
    pinBtn.addEventListener('click', () => {
      drawerPinned = !drawerPinned;
      syncDrawerState();
    });
    closeBtn.addEventListener('click', closeDrawer);
    jumpBtn.addEventListener('click', () => {
      const id = activeId;
      const target = id && doc.getElementById(id);
      closeDrawer();
      if (!target) return;
      let cur = target;
      while (cur) {
        if (cur.tagName === 'DETAILS') cur.open = true;
        cur = cur.parentNode;
      }
      if (typeof target.scrollIntoView === 'function') {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else if (win.location && id) {
        win.location.hash = `#${id}`;
      }
    });
    doc.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !drawer.hidden) {
        closeDrawer();
      }
    });
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

    const scheduleTimer = (win && win.setTimeout) ? win.setTimeout.bind(win) : setTimeout;
    const cancelTimer = (win && win.clearTimeout) ? win.clearTimeout.bind(win) : clearTimeout;
    let queued = false;
    let pinned = false;
    let hoverTimer = null;

    function clearHoverTimer() {
      if (hoverTimer !== null) {
        cancelTimer(hoverTimer);
        hoverTimer = null;
      }
    }

    function syncPinned() {
      if (pinned) rail.setAttribute('data-toc-pinned', 'true');
      else rail.removeAttribute('data-toc-pinned');
    }

    function refresh() {
      // The bottom-left floating TOC leaves the top of the article clear.
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

    rail.addEventListener('mouseenter', () => {
      clearHoverTimer();
      outline.open = true;
      refresh();
    });
    rail.addEventListener('mouseleave', () => {
      clearHoverTimer();
      if (pinned) return;
      hoverTimer = scheduleTimer(() => {
        hoverTimer = null;
        if (!pinned) {
          outline.open = false;
          refresh();
        }
      }, 220);
    });
    summary.addEventListener('click', event => {
      event.preventDefault();
      clearHoverTimer();
      pinned = !pinned;
      outline.open = pinned;
      syncPinned();
      refresh();
    });
    nav.addEventListener('click', event => {
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
          (event.button != null && event.button !== 0)) return;
      const link = event.target.closest && event.target.closest('a');
      if (entries.some(entry => entry.link === link)) {
        clearHoverTimer();
        if (!pinned || (win.innerWidth || 1280) < 760) {
          pinned = false;
          outline.open = false;
          syncPinned();
        }
        // Update the scroll offset before the browser follows the ordinary hash link.
        refresh();
      }
    });
    outline.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !outline.open) return;
      clearHoverTimer();
      pinned = false;
      outline.open = false;
      syncPinned();
      if (nav.contains(doc.activeElement)) summary.focus();
      event.preventDefault();
      refresh();
    });
    doc.addEventListener('pointerdown', event => {
      if (outline.open && !rail.contains(event.target)) {
        clearHoverTimer();
        pinned = false;
        outline.open = false;
        syncPinned();
        refresh();
      }
    });
    outline.addEventListener('toggle', schedule);
    win.addEventListener('scroll', schedule, { passive: true });
    win.addEventListener('resize', () => {
      if (!pinned) outline.open = false;
      schedule();
    });
    for (const event of ['hashchange', 'pageshow', 'load']) win.addEventListener(event, schedule);
    if (win.ResizeObserver) {
      const observer = new win.ResizeObserver(schedule);
      observer.observe(main);
      observer.observe(rail);
    }
    if (doc.fonts) doc.fonts.ready.then(schedule);

    initThemeToggle(doc, report);
    initCitationPreviews(doc, win, report, main);
    initFloatDrawer(doc, win, report, scheduleTimer, cancelTimer);

    report.classList.add('navigation-ready');
    progress.hidden = false;
    outline.open = false;
    syncPinned();
    refresh();
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
