const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../assets/mechanism-walkthrough.html'), 'utf8');
const model = html.match(/<script id="mechanism-model">([\s\S]*?)<\/script>/)[1];
const controller = html.match(/<script id="mechanism-controller">([\s\S]*?)<\/script>/)[1];
const context = vm.createContext({});
vm.runInContext(model, context);
const simulate = settings => JSON.parse(JSON.stringify(context.simulate(settings)));

// Verify syntax of the shipped controller without claiming browser execution.
new vm.Script(controller);

test('late old result is rejected with the guard and admitted without it', () => {
  const guarded = simulate({guard:true, delay:700});
  const unguarded = simulate({guard:false, delay:700});
  assert.equal(guarded.find(e => e.kind === 'old').action, 'rejected');
  assert.equal(unguarded.find(e => e.kind === 'old').action, 'accepted');
  assert.deepEqual(guarded.at(-1).queue, [8]);
  assert.deepEqual(unguarded.at(-1).queue, [7, 8]);
});

test('early result is admitted, then cleared at interruption under either policy', () => {
  for (const guard of [true,false]) {
    const events = simulate({guard,delay:300});
    assert.deepEqual(events.map(e => e.kind), ['start','old','interrupt','new']);
    assert.deepEqual(events[1].queue, [7]);
    assert.deepEqual(events[2].queue, []);
    assert.deepEqual(events.at(-1).queue, [8]);
  }
});

test('equal timestamps process interruption first, as disclosed in the example', () => {
  for (const guard of [true,false]) {
    const events = simulate({guard,delay:400});
    assert.deepEqual(events.map(e => e.kind), ['start','interrupt','old','new']);
    assert.equal(events[2].action, guard ? 'rejected' : 'accepted');
  }
});

test('the guard never leaves a stale generation queued across the supported delay range', () => {
  for (let delay=100; delay<=900; delay++) {
    const events = simulate({guard:true,delay});
    for (const event of events) assert.ok(event.queue.every(g => g === event.generation));
    assert.deepEqual(events.at(-1).queue, [8]);
  }
});

test('old queue snapshots are independent of later transitions and later runs', () => {
  const first = context.simulate({guard:false,delay:700});
  assert.equal(JSON.stringify(first[2].queue), '[7]');
  first[2].queue.push(99);
  assert.equal(JSON.stringify(first.at(-1).queue), '[7,8]');
  assert.deepEqual(simulate({guard:true,delay:700}).at(-1).queue, [8]);
});

test('invalid model settings are rejected rather than silently changing the scenario', () => {
  for (const delay of [0,99,901,NaN,Infinity,200.5,'700']) {
    assert.throws(() => simulate({guard:true,delay}));
  }
  assert.throws(() => simulate({guard:'on',delay:700}));
});

// Small DOM/timer doubles exercise the shipped controller. They do not render HTML
// or establish browser/visual QA; that remains a separate Chrome check.
function mountController() {
  function element() {
    return {
      value:'', textContent:'', hidden:true, disabled:false, children:[], attributes:{}, listeners:{},
      setAttribute(name,value) { this.attributes[name] = value; },
      append(...children) { this.children.push(...children); },
      replaceChildren(...children) { this.children = children; },
      addEventListener(name,handler) { this.listeners[name] = handler; }
    };
  }
  const ids = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(match => [match[1],element()]));
  const region = element(), timers = new Map(); let serial = 0;
  ids.get('guard').value = 'on'; ids.get('arrival').value = '700';
  const docListeners = {}, windowListeners = {};
  const document = {
    hidden:false,
    getElementById(id) { assert.ok(ids.has(id), `Missing HTML element ${id}`); return ids.get(id); },
    createElement:element, createElementNS:element, createTextNode:text => ({textContent:text}),
    querySelectorAll:() => [region],
    addEventListener:(name,handler) => {docListeners[name] = handler;}
  };
  const sandbox = vm.createContext({document, window:{addEventListener:(name,handler) => {windowListeners[name] = handler;}},
    setInterval:callback => {const id=++serial; timers.set(id,callback); return id;},
    clearInterval:id => timers.delete(id)});
  vm.runInContext(model, sandbox); vm.runInContext(controller, sandbox);
  return {
    ids, region, timers, document,
    fire(id,event='click',value) {if (value !== undefined) ids.get(id).value=value; ids.get(id).listeners[event]();},
    tick() {for (const callback of [...timers.values()]) callback();},
    hide() {document.hidden=true; docListeners.visibilitychange();},
    print() {windowListeners.beforeprint();}
  };
}

test('controller opens on the complete result and keeps navigation state synchronized', () => {
  const ui=mountController();
  assert.equal(ui.region.hidden, false);
  assert.equal(ui.ids.get('progress').textContent, '事件 4 / 4');
  assert.equal(ui.ids.get('queue').textContent, '第 8 轮');
  assert.equal(ui.ids.get('next').disabled, true);
  ui.fire('reset');
  assert.equal(ui.ids.get('generation').textContent, '7');
  assert.equal(ui.ids.get('queue').textContent, '空');
  assert.equal(ui.ids.get('previous').disabled, true);
  ui.fire('next');
  assert.equal(ui.ids.get('generation').textContent, '8');
  assert.match(ui.ids.get('event-caption').textContent, /400 ms/);
  ui.fire('step','input','2');
  assert.match(ui.ids.get('event-caption').textContent, /拒绝入队/);
  ui.fire('guard','change','off');
  assert.equal(ui.ids.get('queue').textContent, '第 7 轮');
  assert.match(ui.ids.get('event-caption').textContent, /直接入队/);
});

test('parameter changes update comparison and stop an in-flight replay', () => {
  const ui=mountController();
  ui.fire('play'); assert.equal(ui.timers.size,1);
  ui.tick(); assert.equal(ui.ids.get('progress').textContent,'事件 2 / 4');
  ui.fire('arrival','input','300');
  assert.equal(ui.timers.size,0);
  assert.equal(ui.ids.get('play').textContent,'播放');
  assert.equal(ui.ids.get('guarded-outcome').textContent,'先入队，后被清空');
  assert.equal(ui.ids.get('unguarded-queue').textContent,'第 8 轮');
  ui.fire('arrival','input','400');
  assert.equal(ui.ids.get('guarded-outcome').textContent,'旧结果被拒绝 ×');
  assert.equal(ui.ids.get('unguarded-queue').textContent,'第 7 轮 → 第 8 轮');
});

test('play, pause, completion, hiding, and printing leave no stray timers', () => {
  const ui=mountController();
  assert.equal(ui.timers.size,0);
  ui.fire('play'); ui.fire('play'); assert.equal(ui.timers.size,0);
  ui.fire('play'); ui.tick(); ui.tick(); ui.tick();
  assert.equal(ui.ids.get('progress').textContent,'事件 4 / 4');
  assert.equal(ui.timers.size,0);
  ui.fire('play'); assert.equal(ui.ids.get('progress').textContent,'事件 1 / 4');
  ui.hide(); assert.equal(ui.timers.size,0);
  ui.fire('play'); ui.print(); assert.equal(ui.timers.size,0);
});
