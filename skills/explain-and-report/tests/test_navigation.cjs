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
function mount({wide = false, scroll = 0, invalid = false, observer = true} = {}) {
  const pending = [], listeners = new Map(), observed = [];
  let resizeCallback;
  const document = {
    activeElement:null, listeners:new Map(),
    addEventListener(name,handler) { this.listeners.set(name,handler); },
    documentElement:{style:{values:{},setProperty(k,v){this.values[k]=v;}}}
  };
  const window = {
    innerHeight:800, scroll,
    addEventListener(name, handler) { listeners.set(name, handler); },
    requestAnimationFrame(handler) { pending.push(handler); }
  };
  function element() {
    return {
      listeners:new Map(), attributes:{}, children:[], hidden:false,
      addEventListener(name,handler) { this.listeners.set(name,handler); },
      setAttribute(name,value) { this.attributes[name]=value; },
      removeAttribute(name) { delete this.attributes[name]; },
      getAttribute(name) { return this.attributes[name]; },
      contains(child) { return this===child || this.children.some(node=>node.contains(child)); },
      focus() { document.activeElement=this; },
      closest(name) { return name==='a' && this.isLink ? this : null; }
    };
  }
  const outline=element(), nav=element(), summary=element(), rail=element(), progress=element(), value=element(), bar=element(), main=element(), report=element();
  outline.open=true; outline.children=[summary,nav];
  rail.children=[outline,progress]; progress.children=[value,bar];
  progress.hidden=true;
  progress.querySelector = selector => ({'[data-reading-value]':value,'[data-reading-bar]':bar})[selector];
  rail.querySelector = selector => selector==='[data-reading-progress]' ? progress : null;
  rail.getBoundingClientRect = () => ({height:outline.open ? 180 : 48});
  outline.querySelector = selector => ({nav,summary})[selector];
  report.classList = {values:new Set(),add(name){this.values.add(name);},contains(name){return this.values.has(name);}};
  report.querySelector = selector => ({'main#main':main,'.reading-rail':rail,'details.report-outline':outline})[selector];
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
  document.getElementById=id=>invalid ? null : sections[Number(id.replace('part-',''))] || null;
  const media={matches:wide,addEventListener(name,handler){this.change=handler;}};
  window.matchMedia=query=>{assert.equal(query,'(min-width: 1440px)');return media;};
  if (observer) window.ResizeObserver=class {
    constructor(callback){resizeCallback=callback;}
    observe(node){observed.push(node);}
  };
  const mounted=initReadingNavigation(document,window);
  function flush() { for (const task of pending.splice(0)) task(); }
  function event(target,name,data={}) {
    const e={target,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},...data};
    target.listeners.get(name)(e);return e;
  }
  return {document,window,report,outline,nav,summary,rail,progress,value,bar,main,links,sections,media,pending,observed,mounted,flush,event,
    fire(name){listeners.get(name)();},resizeContent(){resizeCallback();},
    setWide(matches){media.matches=matches;media.change();},
    offset(){return document.documentElement.style.values['--reading-offset'];}};
}

test('valid markup is enhanced once; malformed targets leave the static fallback intact', () => {
  const ui=mount();
  assert.equal(ui.mounted,true);assert.equal(ui.progress.hidden,false);assert.equal(ui.outline.open,false);
  assert.equal(ui.report.classList.contains('navigation-ready'),true);
  assert.equal(ui.offset(),'24px');assert.equal(ui.bar.value,0);assert.equal(ui.value.textContent,'0%');
  assert.equal(initReadingNavigation(ui.document,ui.window),false);
  const bad=mount({invalid:true});
  assert.equal(bad.mounted,false);assert.equal(bad.progress.hidden,true);assert.equal(bad.outline.open,true);
  assert.equal(bad.report.classList.contains('navigation-ready'),false);assert.equal(bad.pending.length,0);
});

test('scroll is frame-throttled, highlights the current section, and reaches 100 before the footer', () => {
  const ui=mount({wide:true});ui.flush();
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
  const ui=mount({wide:true,scroll:688});ui.flush();
  assert.equal(ui.value.textContent,'50%');assert.equal(ui.links[0].attributes['aria-current'],'location');
  assert.deepEqual(ui.observed,[ui.main,ui.rail]);
  ui.main.height=3000;ui.resizeContent();ui.flush();assert.equal(ui.value.textContent,'28%');
  ui.window.scroll=1600;ui.fire('pageshow');ui.flush();assert.equal(ui.links[1].attributes['aria-current'],'location');
  ui.window.innerHeight=1100;ui.fire('resize');ui.flush();assert.equal(ui.bar.value,79);
  assert.equal(ui.document.activeElement,null);
});

test('responsive menu preserves native links and a stable inset, and Escape restores summary focus', () => {
  const ui=mount({wide:true});assert.equal(ui.outline.open,true);assert.equal(ui.offset(),'24px');
  ui.setWide(false);assert.equal(ui.outline.open,false);assert.equal(ui.offset(),'24px');
  ui.outline.open=true;ui.event(ui.outline,'toggle');ui.flush();assert.equal(ui.offset(),'24px');
  const click=ui.event(ui.nav,'click',{target:ui.links[1],button:0});
  assert.equal(click.defaultPrevented,false);assert.equal(ui.outline.open,false);assert.equal(ui.offset(),'24px');
  ui.outline.open=true;
  ui.event(ui.nav,'click',{target:ui.links[1],ctrlKey:true,button:0});assert.equal(ui.outline.open,true);
  ui.document.activeElement=ui.links[1];
  const escape=ui.event(ui.outline,'keydown',{key:'Escape'});
  assert.equal(escape.defaultPrevented,true);assert.equal(ui.outline.open,false);assert.equal(ui.document.activeElement,ui.summary);
  ui.setWide(true);assert.equal(ui.outline.open,true);assert.equal(ui.offset(),'24px');
});

test('opening the floating directory does not change reading progress or the active section', () => {
  const ui=mount({scroll:688});ui.flush();
  const initial={progress:ui.bar.value, active:ui.links.map(link=>link.attributes['aria-current'])};
  assert.equal(initial.progress,50);
  ui.outline.open=true;ui.event(ui.outline,'toggle');ui.flush();
  assert.equal(ui.offset(),'24px');
  assert.deepEqual({progress:ui.bar.value,active:ui.links.map(link=>link.attributes['aria-current'])},initial);
  ui.resizeContent();ui.flush();
  assert.equal(ui.bar.value,initial.progress);
  ui.outline.open=false;ui.event(ui.outline,'toggle');ui.flush();
  assert.deepEqual({progress:ui.bar.value,active:ui.links.map(link=>link.attributes['aria-current'])},initial);
});

test('outside pointer closes only the floating directory without stealing focus or blocking the pointer', () => {
  const ui=mount({scroll:688});ui.flush();ui.outline.open=true;
  ui.event(ui.document,'pointerdown',{target:ui.summary});assert.equal(ui.outline.open,true);
  ui.event(ui.document,'pointerdown',{target:ui.bar});assert.equal(ui.outline.open,true);
  ui.document.activeElement=ui.sections[0];
  const outside=ui.event(ui.document,'pointerdown',{target:ui.main});
  assert.equal(outside.defaultPrevented,false);assert.equal(ui.outline.open,false);
  assert.equal(ui.document.activeElement,ui.sections[0]);assert.equal(ui.bar.value,50);
  ui.setWide(true);
  ui.event(ui.document,'pointerdown',{target:ui.main});assert.equal(ui.outline.open,true);
});

test('hidden targets are not highlighted and ordinary resize works without ResizeObserver', () => {
  const ui=mount({wide:true,scroll:1000,observer:false});ui.flush();
  assert.equal(ui.links[1].attributes['aria-current'],'location');
  ui.sections[1].visible=false;ui.fire('resize');ui.flush();
  assert.equal(ui.links[0].attributes['aria-current'],'location');
  assert.equal(ui.links[1].attributes['aria-current'],undefined);
});
