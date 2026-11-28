/* 在线轮次协议与离线有效练习次数的回归测试。 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const WEB = path.join(__dirname, '../../web/js');

async function main() {
  const storage = {}, window = {}, calls = [];
  const sandbox = { window, Promise, Date, Math, JSON,
    localStorage: { getItem: key => storage[key] || null, setItem: (key, value) => { storage[key] = value; } },
    API: {
      post(url, body) { calls.push({ url, body }); return Promise.resolve(body); },
      get() { return Promise.resolve({ recording: { id: 8, status: 'pending' } }); },
      path: url => url, toast() {}
    },
    fetch(url, opts) { calls.push({ url, body: JSON.parse(opts.body) }); return Promise.resolve({ ok: true }); }
  };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(WEB, 'game-adapter-online.js'), 'utf8'), sandbox);
  await window.WPAdapter.begin({ ords: [4], previous_play_token: 'previous' }, { bank_id: 7 });
  assert.equal(calls[0].body.previous_play_token, 'previous');
  assert.equal(calls[0].body.bank_id, 7);
  const report = { score: 80, play_token: 'server-round', rule_version: 4,
    combo_events: [{ ord: 4, eligible: true }], initial_seconds: 20, time_left: 5, bonus_seconds: 1 };
  assert.equal(await window.WPAdapter.save(report, { bank_id: 7 }), true);
  assert.equal(calls[1].body.play_token, 'server-round');
  assert.equal(calls[1].body.combo_events[0].ord, 4);
  assert.equal(calls[1].body.time_left, 5);
  assert.equal((await window.WPAdapter.recording(8)).status, 'pending');
  const before = calls.length;
  let release;
  sandbox.API.post = function (url, body) {
    calls.push({ url, body });
    if (url === '/api/plays/progress') return new Promise(resolve => { release = resolve; });
    return Promise.resolve({});
  };
  const checkpoint = Object.assign({}, report, { detail: [{ ord: 0, wrong: 0, solved: true }] });
  const progress = window.WPAdapter.progress(checkpoint);
  checkpoint.detail[0].wrong = 4;
  const phase = window.WPAdapter.phase(report.play_token, 'recording');
  const saved = window.WPAdapter.save(report, { bank_id: 7 });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls.length, before + 1);
  assert.equal(calls[before].url, '/api/plays/progress');
  assert.ok(calls[before].body.device);
  assert.equal(calls[before].body.detail[0].wrong, 0, '排队时冻结快照，不引用后来变动的状态');
  release({});
  await Promise.all([progress, phase, saved]);
  assert.equal(calls.slice(before).map(call => call.url).join(','),
    '/api/plays/progress,/api/plays/phase,/api/scores');

  vm.runInContext(fs.readFileSync(path.join(WEB, 'game-adapter-offline.js'), 'utf8'), sandbox);
  const adapter = window.WPAdapter, bank = { bank_id: 7, game_type: 'spell' }, meta = { ords: [4, 5] };
  for (let i = 1; i <= 16; i++) {
    const policy = await adapter.begin(meta, bank);
    assert.equal(policy.attempt, i);
    const tier = i <= 5 ? 0 : i <= 10 ? 1 : i <= 15 ? 2 : 3;
    assert.equal(policy.score_factor, [1, .75, .5, .2][tier]);
    assert.equal(policy.time_factor, [1, .8, .6, .4][tier]);
    const count = adapter.history().length;
    const r = { score: 10, play_token: policy.play_token };
    assert.equal(adapter.save(r, bank), true);
    assert.equal(adapter.save(r, bank), true);
    assert.equal(adapter.history().length, count + 1);
  }
  const blank = await adapter.begin(meta, bank);
  adapter.save({ score: 0, play_token: blank.play_token }, bank);
  assert.equal((await adapter.begin(meta, bank)).attempt, 17);
  assert.equal((await adapter.begin({ ords: [5, 4] }, bank)).attempt, 17);
  assert.equal((await adapter.begin({ ords: [9] }, bank)).attempt, 1);
  assert.equal((await adapter.begin(meta, { bank_id: 8 })).attempt, 1);
  console.log('轮次协议、四档递减、白卷与幂等保存全部通过');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
