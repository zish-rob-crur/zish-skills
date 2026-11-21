const test = require('node:test');
const assert = require('node:assert/strict');
const { readingState, initReadingNavigation } = require('../assets/report-navigation.js');

test('progress uses the article boundaries, including deep entry, its end, and short articles', () => {
  const state = changes => readingState({top:100, bottom:2100, viewportHeight:800, offset:24, sectionTops:[300,1000,1800], ...changes});
  assert.deepEqual(state(), {progress:0, active:-1});
  assert.deepEqual(state({top:-588,bottom:1412,sectionTops:[-388,312,1112]}), {progress:50,active:0});
  assert.deepEqual(state({top:-1300,bottom:700,sectionTops:[-1100,-400,400]}), {progress:100,active:2});
  assert.deepEqual(state({top:100,bottom:500,sectionTops:[200,350]}), {progress:100,active:1});
  assert.equal(state({top:-588,bottom:2412,sectionTops:[-388,312,1112]}).progress, 28);
});

// These doubles run the shipped controller and its events, without claiming rendered QA.
function mount({scroll = 0, innerWidth = 1440, invalid = false, observer = true, withExtras = false} = {}) {
  const pending = [], listeners = new Map(), observed = [], timers = new Map();
  let timerId = 0, resizeCallback;
  const document = {
    activeElement:null, listeners:new Map(),
    addEventListener(name,handler) { this.listeners.set(name,handler); },
    documentElement:{
      attributes:{},
      style:{values:{},setProperty(k,v){this.values[k]=v;}},
      setAttribute(k,v){this.attributes[k]=v;},
      getAttribute(k){return this.attributes[k];},
      removeAttribute(k){delete this.attributes[k];}
    }
  };
  const window = {
    innerHeight:800, innerWidth, scroll,
    addEventListener(name, handler) { listeners.set(name, handler); },
    requestAnimationFrame(handler) { pending.push(handler); },
    setTimeout(handler) { const id = ++timerId; timers.set(id, handler); return id; },
    clearTimeout(id) { timers.delete(id); }
  };
  function element(tagName = 'DIV') {
    const classSet = new Set();
    return {
      tagName, textContent:'', className:'', style:{},
      listeners:new Map(), attributes:{}, children:[], hidden:false, open:false,
      classList:{
        add(c){classSet.add(c);},
        remove(c){classSet.delete(c);},
        contains(c){return classSet.has(c);},
        toggle(c, force){const on = force === undefined ? !classSet.has(c) : Boolean(force); if(on) classSet.add(c); else classSet.delete(c); return on;}
      },
      addEventListener(name,handler) { this.listeners.set(name,handler); },
      setAttribute(name,value) { this.attributes[name]=value; },
      removeAttribute(name) { delete this.attributes[name]; },
      getAttribute(name) { return this.attributes[name]; },
      appendChild(child) { this.children.push(child); child.parentNode = this; return child; },
      replaceChildren(...children) { this.children = children; },
      cloneNode(deep) {
        const copy = element(this.tagName);
        copy.textContent = this.textContent;
        copy.className = this.className;
        copy.open = this.open;
        copy.attributes = {...this.attributes};
        if (deep) copy.children = this.children.map(ch => ch.cloneNode ? ch.cloneNode(true) : ch);
        return copy;
      },
      contains(child) { return this===child || this.children.some(node=>node.contains && node.contains(child)); },
      focus() { document.activeElement=this; },
      closest(name) { return name==='a' && this.isLink ? this : null; }
    };
  }
  const outline=element(), nav=element(), summary=element(), rail=element(), progress=element(), value=element(), bar=element(), main=element(), report=element();
  const themeToggle = withExtras ? element('BUTTON') : null;
  const citeLink = withExtras ? element('A') : null;
  const tipNode = withExtras ? element('SPAN') : null;
  const drawerTrigger = withExtras ? element('A') : null;
  const drawerDetails = withExtras ? element('DETAILS') : null;
  const dt = withExtras ? element('DT') : null;
  const dd = withExtras ? element('DD') : null;
  const tableScroll = withExtras ? element('DIV') : null;
  const table = withExtras ? element('TABLE') : null;
  const thA = withExtras ? element('TH') : null;
  const thB = withExtras ? element('TH') : null;
  const agentTrace = withExtras ? element('DIV') : null;
  const traceBtnAll = withExtras ? element('BUTTON') : null;
  const traceBtn1 = withExtras ? element('BUTTON') : null;
  const traceBtn2 = withExtras ? element('BUTTON') : null;
  const traceStage1 = withExtras ? element('DIV') : null;
  const traceStage2 = withExtras ? element('DIV') : null;
  const meterMainFill = withExtras ? element('DIV') : null;
  const meterMainText = withExtras ? element('SPAN') : null;
  const meterSubFill = withExtras ? element('DIV') : null;
  const meterSubGhost = withExtras ? element('DIV') : null;
  const meterSubText = withExtras ? element('SPAN') : null;
  if (withExtras) {
    document.body = element('BODY');
    document.createElement = tag => element(tag.toUpperCase());
    tableScroll.classList.add('table-scroll');
    const thead = element('THEAD');
    const tr = element('TR');
    thA.textContent = 'Col A';
    thB.textContent = 'Col B';
    thA.getBoundingClientRect = () => ({width: 200});
    thB.getBoundingClientRect = () => ({width: 200});
    tr.appendChild(thA);
    tr.appendChild(thB);
    thead.appendChild(tr);
    table.appendChild(thead);
    tableScroll.appendChild(table);
    thead.querySelector = sel => sel === 'tr' ? tr : null;
    table.querySelector = sel => sel === 'thead' ? thead : null;
    citeLink.isLink = true;
    citeLink.attributes.href = '#C1';
    citeLink.getBoundingClientRect = () => ({top: 200, left: 120, height: 20});
    tipNode.attributes['data-tip-title'] = 'Stage 1';
    tipNode.attributes['data-tip-body'] = 'Milestone note.';
    tipNode.getBoundingClientRect = () => ({top: 300, left: 200, height: 24});
    drawerTrigger.isLink = true;
    drawerTrigger.attributes.href = '#art-detail';
    drawerTrigger.attributes['data-drawer-target'] = 'art-detail';
    drawerTrigger.attributes['data-drawer-title'] = 'Detail Spec';
    drawerTrigger.attributes['data-drawer-wide'] = 'true';
    drawerDetails.attributes.id = 'art-detail';
    drawerDetails.open = false;
    const innerSpan = element('SPAN');
    innerSpan.attributes.id = 'nested-id';
    innerSpan.textContent = 'Spec body';
    drawerDetails.children = [innerSpan];
    dt.textContent = 'C1';
    const code = element('CODE'); code.textContent = 'spec.txt';
    const para = element('P'); para.textContent = 'Requirement details.';
    dd.querySelector = sel => sel === 'code' ? code : null;
    dd.querySelectorAll = sel => sel === 'p' ? [para] : [];
    dt.nextElementSibling = dd;
    main.querySelectorAll = sel => {
      if (sel === 'a[href^="#"]') return [citeLink];
      if (sel === '[data-tip-title]') return [tipNode];
      return [];
    };
    report.querySelectorAll = sel => {
      if (sel === '[data-drawer-target]') return [drawerTrigger];
      if (sel === 'table') return [table];
      if (sel === '[data-agent-trace]') return [agentTrace];
      return [];
    };
    traceBtnAll.attributes['data-trace-step'] = 'all';
    traceBtnAll.attributes['data-main-pct'] = '6';
    traceBtnAll.attributes['data-main-label'] = '+600 chars';
    traceBtnAll.attributes['data-sub-pct'] = '0';
    traceBtnAll.attributes['data-sub-ghost-pct'] = '92';
    traceBtnAll.attributes['data-sub-label'] = 'peak 35k -> 0';
    traceBtn1.attributes['data-trace-step'] = '1';
    traceBtn1.attributes['data-main-pct'] = '0';
    traceBtn1.attributes['data-main-label'] = '0';
    traceBtn1.attributes['data-sub-pct'] = '90';
    traceBtn1.attributes['data-sub-ghost-pct'] = '0';
    traceBtn1.attributes['data-sub-label'] = '35k tok';
    traceBtn2.attributes['data-trace-step'] = '2';
    traceBtn2.attributes['data-main-pct'] = '6';
    traceBtn2.attributes['data-main-label'] = '+600 chars';
    traceBtn2.attributes['data-sub-pct'] = '0';
    traceBtn2.attributes['data-sub-ghost-pct'] = '90';
    traceBtn2.attributes['data-sub-label'] = 'released';
    traceStage1.attributes['data-step'] = '1';
    traceStage2.attributes['data-step'] = '2';
    agentTrace.querySelectorAll = sel => {
      if (sel === '[data-trace-step]') return [traceBtnAll, traceBtn1, traceBtn2];
      if (sel === '.trace-stage[data-step]') return [traceStage1, traceStage2];
      return [];
    };
    agentTrace.querySelector = sel => ({
      '[data-meter-main-fill]': meterMainFill,
      '[data-meter-main-text]': meterMainText,
      '[data-meter-sub-fill]': meterSubFill,
      '[data-meter-sub-ghost]': meterSubGhost,
      '[data-meter-sub-text]': meterSubText
    })[sel] || null;
  }
  outline.open=true; outline.children=[summary,nav];
  rail.children=[outline,progress]; progress.children=[value,bar];
  progress.hidden=true;
  progress.querySelector = selector => ({'[data-reading-value]':value,'[data-reading-bar]':bar})[selector];
  rail.querySelector = selector => selector==='[data-reading-progress]' ? progress : null;
  rail.getBoundingClientRect = () => ({height:outline.open ? 180 : 44});
  outline.querySelector = selector => ({nav,summary})[selector];
  report.classList = {values:new Set(),add(name){this.values.add(name);},contains(name){return this.values.has(name);}};
  report.querySelector = selector => ({'main#main':main,'.reading-rail':rail,'details.report-outline':outline,'[data-theme-toggle]':themeToggle})[selector];
  document.querySelector = selector => selector==='.report' ? report : null;
  const sections=[300,1000,1800].map((top,index) => {
    const node=element(); node.top=top;node.visible=true;node.order=index;
    node.getBoundingClientRect=()=>({top:node.top-window.scroll,height:100});
    node.getClientRects=()=>node.visible ? [{}] : [];
    node.compareDocumentPosition=other=>node.order===other.order ? 0 : node.order<other.order ? 4 : 2;
    return node;
  });
  main.children=sections;
  main.height=2000;
  main.getBoundingClientRect=()=>({top:100-window.scroll,bottom:100+main.height-window.scroll});
  const links=sections.map((target,index)=>{
    const link=element();link.isLink=true;link.attributes.href=`#part-${index}`;return link;
  });
  // Deliberately reverse the menu order: active tracking must follow document order.
  nav.children=links;
  nav.querySelectorAll=()=>[...links].reverse();
  document.getElementById=id=>{
    if (invalid) return null;
    if (withExtras && id === 'C1') return dt;
    if (withExtras && id === 'art-detail') return drawerDetails;
    return sections[Number(id.replace('part-',''))] || null;
  };
  if (observer) window.ResizeObserver=class {
    constructor(callback){resizeCallback=callback;}
    observe(node){observed.push(node);}
  };
  const mounted=initReadingNavigation(document,window);
  function flush() { for (const task of pending.splice(0)) task(); }
  function runTimers() { for (const [id, fn] of [...timers.entries()]) { timers.delete(id); fn(); } }
  function event(target,name,data={}) {
    const e={target,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},...data};
    target.listeners.get(name)(e);return e;
  }
  return {document,window,report,outline,nav,summary,rail,progress,value,bar,main,links,sections,pending,timers,observed,mounted,themeToggle,citeLink,tipNode,drawerTrigger,drawerDetails,tableScroll,table,thA,thB,agentTrace,traceBtnAll,traceBtn1,traceBtn2,traceStage1,traceStage2,meterMainFill,meterMainText,meterSubFill,meterSubGhost,meterSubText,flush,runTimers,event,
    fire(name, e){listeners.get(name)(e);},resizeContent(){resizeCallback();},
    offset(){return document.documentElement.style.values['--reading-offset'];}};
}

test('valid markup initializes as collapsed bottom-left floating TOC; malformed targets leave static fallback intact', () => {
  const ui=mount();
  assert.equal(ui.mounted,true);assert.equal(ui.progress.hidden,false);assert.equal(ui.outline.open,false);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),undefined);
  assert.equal(ui.report.classList.contains('navigation-ready'),true);
  assert.equal(ui.offset(),'24px');assert.equal(ui.bar.value,0);assert.equal(ui.value.textContent,'0%');
  assert.equal(initReadingNavigation(ui.document,ui.window),false);
  const bad=mount({invalid:true});
  assert.equal(bad.mounted,false);assert.equal(bad.progress.hidden,true);assert.equal(bad.outline.open,true);
  assert.equal(bad.report.classList.contains('navigation-ready'),false);assert.equal(bad.pending.length,0);
});

test('scroll is frame-throttled, highlights the current section, and reaches 100 before the footer', () => {
  const ui=mount();ui.flush();
  ui.window.scroll=1000;
  ui.fire('scroll');ui.fire('scroll');ui.fire('scroll');assert.equal(ui.pending.length,1);
  ui.flush();
  assert.equal(ui.links[1].attributes['aria-current'],'location');
  assert.equal(ui.links[0].attributes['aria-current'],undefined);assert.equal(ui.links[2].attributes['aria-current'],undefined);
  assert.equal(ui.document.activeElement,null);
  ui.window.scroll=1400;ui.fire('scroll');ui.flush();
  assert.equal(ui.value.textContent,'100%');assert.equal(ui.bar.value,100);
  assert.equal(ui.links[2].attributes['aria-current'],'location');
});

test('deep entry, history restoration, resize and content reflow update progress without changing focus', () => {
  const ui=mount({scroll:688});ui.flush();
  assert.equal(ui.value.textContent,'50%');assert.equal(ui.links[0].attributes['aria-current'],'location');
  assert.deepEqual(ui.observed,[ui.main,ui.rail]);
  ui.main.height=3000;ui.resizeContent();ui.flush();assert.equal(ui.value.textContent,'28%');
  ui.window.scroll=1600;ui.fire('pageshow');ui.flush();assert.equal(ui.links[1].attributes['aria-current'],'location');
  ui.window.innerHeight=1100;ui.fire('resize');ui.flush();assert.equal(ui.bar.value,79);
  assert.equal(ui.document.activeElement,null);
});

test('floating TOC supports hover-to-preview, click-to-pin, link navigation, and Escape focus restore', () => {
  const ui=mount();ui.flush();
  assert.equal(ui.outline.open,false);

  // Hover opens preview; leaving schedules close unless re-entered
  ui.event(ui.rail,'mouseenter');
  assert.equal(ui.outline.open,true);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),undefined);
  ui.event(ui.rail,'mouseleave');
  assert.equal(ui.timers.size,1);
  ui.event(ui.rail,'mouseenter');
  assert.equal(ui.timers.size,0);
  assert.equal(ui.outline.open,true);

  // Clicking a link while unpinned closes preview without preventing hash navigation
  const click=ui.event(ui.nav,'click',{target:ui.links[1],button:0});
  assert.equal(click.defaultPrevented,false);
  assert.equal(ui.outline.open,false);

  // Hover then click summary pins it open across mouseleave and desktop link clicks
  ui.event(ui.rail,'mouseenter');
  const pinClick=ui.event(ui.summary,'click');
  assert.equal(pinClick.defaultPrevented,true);
  assert.equal(ui.outline.open,true);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),'true');
  ui.event(ui.rail,'mouseleave');
  ui.runTimers();
  assert.equal(ui.outline.open,true);
  ui.event(ui.nav,'click',{target:ui.links[1],button:0});
  assert.equal(ui.outline.open,true);

  // On narrow screens (<760px), clicking a link closes even if previously opened via summary tap
  ui.window.innerWidth=390;
  ui.event(ui.nav,'click',{target:ui.links[1],button:0});
  assert.equal(ui.outline.open,false);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),undefined);

  // Escape unpins, closes, and restores focus to summary
  ui.window.innerWidth=1440;
  ui.event(ui.summary,'click');
  assert.equal(ui.outline.open,true);
  ui.document.activeElement=ui.links[1];
  const escape=ui.event(ui.outline,'keydown',{key:'Escape'});
  assert.equal(escape.defaultPrevented,true);
  assert.equal(ui.outline.open,false);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),undefined);
  assert.equal(ui.document.activeElement,ui.summary);
});

test('opening the floating directory does not change reading progress or the active section', () => {
  const ui=mount({scroll:688});ui.flush();
  const initial={progress:ui.bar.value, active:ui.links.map(link=>link.attributes['aria-current'])};
  assert.equal(initial.progress,50);
  ui.event(ui.rail,'mouseenter');ui.flush();
  assert.equal(ui.offset(),'24px');
  assert.deepEqual({progress:ui.bar.value,active:ui.links.map(link=>link.attributes['aria-current'])},initial);
  ui.resizeContent();ui.flush();
  assert.equal(ui.bar.value,initial.progress);
  ui.event(ui.rail,'mouseleave');ui.runTimers();ui.flush();
  assert.deepEqual({progress:ui.bar.value,active:ui.links.map(link=>link.attributes['aria-current'])},initial);
});

test('outside pointer unpins and closes floating directory without stealing focus or blocking pointer', () => {
  const ui=mount({scroll:688});ui.flush();
  ui.event(ui.summary,'click');
  assert.equal(ui.outline.open,true);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),'true');
  ui.event(ui.document,'pointerdown',{target:ui.summary});assert.equal(ui.outline.open,true);
  ui.event(ui.document,'pointerdown',{target:ui.bar});assert.equal(ui.outline.open,true);
  ui.document.activeElement=ui.sections[0];
  const outside=ui.event(ui.document,'pointerdown',{target:ui.main});
  assert.equal(outside.defaultPrevented,false);assert.equal(ui.outline.open,false);
  assert.equal(ui.rail.getAttribute('data-toc-pinned'),undefined);
  assert.equal(ui.document.activeElement,ui.sections[0]);assert.equal(ui.bar.value,50);
});

test('hidden targets are not highlighted and ordinary resize works without ResizeObserver', () => {
  const ui=mount({scroll:1000,observer:false});ui.flush();
  assert.equal(ui.links[1].attributes['aria-current'],'location');
  ui.sections[1].visible=false;ui.fire('resize');ui.flush();
  assert.equal(ui.links[0].attributes['aria-current'],'location');
  assert.equal(ui.links[1].attributes['aria-current'],undefined);
});

test('theme toggle, citation popovers, and data-tip-title popovers enhance reading cleanly', () => {
  const ui=mount({withExtras:true});ui.flush();
  assert.equal(ui.themeToggle.getAttribute('aria-pressed'), 'false');
  ui.event(ui.themeToggle, 'click');
  assert.equal(ui.document.documentElement.getAttribute('data-theme'), 'light');
  assert.equal(ui.themeToggle.getAttribute('aria-pressed'), 'true');
  ui.event(ui.themeToggle, 'click');
  assert.equal(ui.document.documentElement.getAttribute('data-theme'), undefined);

  const popover = ui.document.body.children[0];
  assert.equal(popover.hidden, true);
  ui.event(ui.citeLink, 'mouseenter');
  assert.equal(popover.hidden, false);
  assert.equal(popover.children[0].textContent, '证据 C1 · spec.txt');
  assert.equal(popover.children[1].textContent, 'Requirement details.');
  ui.event(ui.citeLink, 'mouseleave');
  assert.equal(popover.hidden, true);

  ui.event(ui.tipNode, 'focus');
  assert.equal(popover.hidden, false);
  assert.equal(popover.children[0].textContent, 'Stage 1');
  assert.equal(popover.children[1].textContent, 'Milestone note.');
  ui.event(ui.tipNode, 'blur');
  assert.equal(popover.hidden, true);
});

test('floating detail drawer supports hover-to-preview, click-to-pin toggle, id stripping, and Escape close', () => {
  const ui=mount({withExtras:true});ui.flush();
  const drawer = ui.document.body.children[1];
  assert.equal(drawer.className, 'explorer-float-drawer');
  assert.equal(drawer.hidden, true);

  // Hover opens in preview mode; leaving schedules close
  ui.event(ui.drawerTrigger, 'mouseenter');
  assert.equal(drawer.hidden, false);
  assert.equal(drawer.classList.contains('is-compare-mode'), true);
  assert.equal(drawer.classList.contains('is-pinned'), false);
  const bar = drawer.children[0];
  const badge = bar.children[0].children[0];
  const titleEl = bar.children[0].children[1];
  const body = drawer.children[1];
  assert.equal(badge.textContent, '预览模式');
  assert.equal(titleEl.textContent, 'Detail Spec');
  const clonedDetails = body.children[0];
  assert.equal(clonedDetails.open, true);
  assert.equal(clonedDetails.getAttribute('id'), undefined);
  assert.equal(clonedDetails.children[0].getAttribute('id'), undefined);

  ui.event(ui.drawerTrigger, 'mouseleave');
  ui.runTimers();
  assert.equal(drawer.hidden, true);

  // First click pins; second click on same trigger closes & unpins
  const click1 = ui.event(ui.drawerTrigger, 'click', {button:0});
  assert.equal(click1.defaultPrevented, true);
  assert.equal(drawer.hidden, false);
  assert.equal(drawer.classList.contains('is-pinned'), true);
  assert.equal(badge.textContent, '已固定');
  assert.equal(ui.drawerTrigger.classList.contains('is-active-pill'), true);

  ui.event(ui.drawerTrigger, 'click', {button:0});
  assert.equal(drawer.hidden, true);
  assert.equal(ui.drawerTrigger.classList.contains('is-active-pill'), false);

  // Re-open pinned and close via Escape
  ui.event(ui.drawerTrigger, 'click', {button:0});
  assert.equal(drawer.hidden, false);
  ui.event(ui.document, 'keydown', {key:'Escape'});
  assert.equal(drawer.hidden, true);
  assert.equal(drawer.classList.contains('is-pinned'), false);
});

test('table column resizers support pointer drag width adjustment and double-click reset', () => {
  const ui = mount({withExtras:true}); ui.flush();
  const handleA = ui.thA.children[0];
  assert.equal(handleA.className, 'col-resizer');
  assert.equal(ui.thA.classList.contains('has-col-resizer'), true);

  let stopped = false;
  ui.event(handleA, 'pointerdown', {
    button: 0,
    clientX: 200,
    stopPropagation() { stopped = true; }
  });
  assert.equal(stopped, true);
  assert.equal(ui.table.style.tableLayout, 'fixed');
  assert.equal(ui.tableScroll.classList.contains('has-resized-table'), true);
  assert.equal(ui.document.documentElement.getAttribute('data-col-resizing'), 'true');

  ui.fire('pointermove', {clientX: 320});
  assert.equal(ui.thA.style.width, '320px');
  assert.equal(ui.table.style.width, '520px');

  ui.fire('pointerup');
  assert.equal(ui.document.documentElement.getAttribute('data-col-resizing'), undefined);
  assert.equal(handleA.classList.contains('is-dragging'), false);

  ui.event(handleA, 'dblclick');
  assert.equal(ui.thA.style.width, '');
  assert.equal(ui.table.style.tableLayout, '');
  assert.equal(ui.table.style.width, '');
  assert.equal(ui.table.classList.contains('is-col-resized'), false);
  assert.equal(ui.tableScroll.classList.contains('has-resized-table'), false);
});

test('agent trace stepper highlights swimlane rows, updates context meters, and toggles back to all', () => {
  const ui = mount({withExtras:true}); ui.flush();
  assert.equal(ui.agentTrace.getAttribute('data-active-step'), 'all');
  assert.equal(ui.meterMainFill.style.width, '6%');
  assert.equal(ui.meterSubGhost.style.width, '92%');
  assert.equal(ui.traceStage1.classList.contains('is-dimmed'), false);

  ui.event(ui.traceBtn1, 'click');
  assert.equal(ui.agentTrace.getAttribute('data-active-step'), '1');
  assert.equal(ui.traceBtn1.getAttribute('aria-pressed'), 'true');
  assert.equal(ui.traceStage1.classList.contains('is-active'), true);
  assert.equal(ui.traceStage2.classList.contains('is-dimmed'), true);
  assert.equal(ui.meterSubFill.style.width, '90%');
  assert.equal(ui.meterSubText.textContent, '35k tok');

  ui.event(ui.traceBtn1, 'keydown', {key:'ArrowRight'});
  assert.equal(ui.document.activeElement, ui.traceBtn2);
  assert.equal(ui.agentTrace.getAttribute('data-active-step'), '2');
  assert.equal(ui.meterSubFill.style.width, '0%');
  assert.equal(ui.meterSubGhost.style.width, '90%');

  // Clicking the already active stage row returns to the full overview
  ui.event(ui.traceStage2, 'click', {target: ui.traceStage2});
  assert.equal(ui.agentTrace.getAttribute('data-active-step'), 'all');
  assert.equal(ui.traceStage1.classList.contains('is-dimmed'), false);
  assert.equal(ui.traceStage2.classList.contains('is-active'), false);
});
