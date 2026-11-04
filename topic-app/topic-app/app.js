// 主应用逻辑

// ====== 状态 ======
const STORAGE_KEYS = {
  usedIds: 'tp_used_ids',
  restoredIds: 'tp_restored_ids',
  history: 'tp_history',
  points: 'tp_points',
  theme: 'tp_theme',
};

const POINTS = {
  endDiscussion: 10,
  viewHint: 2,
  startBonus: 30,
};

const THEMES = {
  warm: '暖棕',
  forest: '森绿',
  mist: '雾蓝',
};

const state = {
  topics: [],
  categories: [],
  currentTopic: null,
  hintShown: false,
  currentCategory: '__all__',
  theme: 'warm',
};

// ====== 存储 ======
const storage = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      return v === null ? fallback : JSON.parse(v);
    } catch { return fallback; }
  },
  set(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  },
};

// ====== 工具：将 hint 字符串拆成列表 ======
function parseHint(hint) {
  // hint 格式："参考方向：\n- xxx\n- xxx\n- xxx"
  const lines = hint.split('\n').map(s => s.trim()).filter(Boolean);
  // 找到第一个"参考方向："行，后面以 "- " 开头的是列表项
  const items = [];
  let inList = false;
  for (const line of lines) {
    if (line.startsWith('参考方向')) {
      inList = true;
      continue;
    }
    if (inList && (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('· '))) {
      items.push(line.slice(2).trim());
    }
  }
  return items;
}

// ====== 初始化 ======
async function init() {
  // 加载数据
  const mod = await import('./topics.js');
  state.topics = mod.TOPICS;
  state.categories = mod.CATEGORIES;

  // 初始化积分
  if (storage.get(STORAGE_KEYS.points, null) === null) {
    storage.set(STORAGE_KEYS.points, POINTS.startBonus);
  }

  // 初始化主题
  state.theme = storage.get(STORAGE_KEYS.theme, 'warm');
  applyTheme(state.theme);

  // 渲染
  renderCategoryChips();
  renderPoints();
  renderThemeOptions();
  bindEvents();
  renderHistory();
  showEmptyState();
}

function showEmptyState() {
  document.getElementById('topicEmpty').style.display = 'flex';
  document.getElementById('topicResult').style.display = 'none';
}

// ====== 主题切换 ======
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  state.theme = theme;
  storage.set(STORAGE_KEYS.theme, theme);
}

function renderThemeOptions() {
  document.querySelectorAll('.theme-option').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.theme === state.theme);
  });
}

function toggleThemePicker(force) {
  const picker = document.getElementById('themePicker');
  const willShow = force ?? !picker.classList.contains('show');
  picker.classList.toggle('show', willShow);
}

// ====== 分类 chips ======
function renderCategoryChips() {
  const wrap = document.getElementById('categoryChips');
  const all = ['__all__', ...state.categories];
  wrap.innerHTML = '';
  all.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'chip' + (cat === state.currentCategory ? ' active' : '');
    btn.textContent = cat === '__all__' ? '全部' : cat;
    btn.dataset.cat = cat;
    btn.addEventListener('click', () => {
      state.currentCategory = cat;
      renderCategoryChips();
    });
    wrap.appendChild(btn);
  });
}

// ====== 积分 ======
function getPoints() { return storage.get(STORAGE_KEYS.points, 0); }
function addPoints(n) {
  const cur = getPoints();
  storage.set(STORAGE_KEYS.points, cur + n);
  renderPoints();
  showPointsModal(n);
}
function spendPoints(n) {
  if (getPoints() < n) return false;
  storage.set(STORAGE_KEYS.points, getPoints() - n);
  renderPoints();
  return true;
}
function renderPoints() {
  document.getElementById('pointsValue').textContent = getPoints();
}

// ====== 抽话题 ======
function pickTopic() {
  const usedIds = new Set(storage.get(STORAGE_KEYS.usedIds, []));
  const restoredIds = new Set(storage.get(STORAGE_KEYS.restoredIds, []));

  const pool = state.topics.filter(t => {
    if (state.currentCategory !== '__all__' && t.category !== state.currentCategory) return false;
    if (usedIds.has(t.id) && !restoredIds.has(t.id)) return false;
    return true;
  });

  if (pool.length === 0) {
    showToast(state.currentCategory === '__all__'
      ? '太棒了！所有话题都讨论过啦 🎉'
      : '这个分类下没有新话题了，换一个分类试试');
    return;
  }

  const restoredPool = pool.filter(t => restoredIds.has(t.id));
  const finalPool = restoredPool.length > 0 ? restoredPool : pool;
  const picked = finalPool[Math.floor(Math.random() * finalPool.length)];

  usedIds.add(picked.id);
  restoredIds.delete(picked.id);
  storage.set(STORAGE_KEYS.usedIds, [...usedIds]);
  storage.set(STORAGE_KEYS.restoredIds, [...restoredIds]);

  state.currentTopic = picked;
  state.hintShown = false;
  renderCurrentTopic();
}

function renderCurrentTopic() {
  const empty = document.getElementById('topicEmpty');
  const result = document.getElementById('topicResult');

  empty.style.display = 'none';
  result.style.display = 'flex';

  document.getElementById('topicCategory').textContent = state.currentTopic.category;
  document.getElementById('topicText').textContent = state.currentTopic.topic;

  // 用列表渲染参考方向
  const hintItems = parseHint(state.currentTopic.hint);
  const list = document.getElementById('topicHintList');
  list.innerHTML = hintItems.map(s => `<li>${escapeHtml(s)}</li>`).join('');

  // 重置 hint 状态
  document.getElementById('topicHint').classList.remove('show');
  document.getElementById('btnViewHint').disabled = false;
  document.getElementById('btnViewHint').textContent = `查看方向 (-${POINTS.viewHint}积分)`;

  // 动画
  const card = document.getElementById('topicResult');
  card.classList.remove('show-result');
  void card.offsetWidth;
  card.classList.add('show-result');
}

function viewHint() {
  if (state.hintShown) return;
  if (state.currentTopic === null) {
    showToast('先抽一个话题吧');
    return;
  }
  if (!spendPoints(POINTS.viewHint)) {
    showToast(`积分不够啦，先去完成讨论赚积分吧～`);
    return;
  }
  state.hintShown = true;
  document.getElementById('topicHint').classList.add('show');
  document.getElementById('btnViewHint').disabled = true;
  document.getElementById('btnViewHint').textContent = '已查看方向';
}

function skipTopic() {
  if (!state.currentTopic) return pickTopic();
  const usedIds = new Set(storage.get(STORAGE_KEYS.usedIds, []));
  usedIds.delete(state.currentTopic.id);
  storage.set(STORAGE_KEYS.usedIds, [...usedIds]);
  pickTopic();
}

function endDiscussion() {
  if (!state.currentTopic) {
    showToast('还没有正在讨论的话题');
    return;
  }
  const history = storage.get(STORAGE_KEYS.history, []);
  const viewedHint = state.hintShown;
  let pointsEarned = POINTS.endDiscussion;
  if (viewedHint) {
    pointsEarned = Math.max(2, POINTS.endDiscussion - POINTS.viewHint);
  }
  history.unshift({
    id: state.currentTopic.id,
    topic: state.currentTopic.topic,
    category: state.currentTopic.category,
    hint: state.currentTopic.hint,
    hintViewed: viewedHint,
    pointsEarned,
    date: new Date().toISOString(),
  });
  storage.set(STORAGE_KEYS.history, history);
  addPoints(pointsEarned);
  renderHistory();
}

// ====== 历史页面 ======
function renderHistory() {
  const history = storage.get(STORAGE_KEYS.history, []);
  const usedIds = storage.get(STORAGE_KEYS.usedIds, []);
  const list = document.getElementById('historyList');
  const empty = document.getElementById('historyEmpty');

  document.getElementById('statTotal').textContent = history.length;
  document.getElementById('statRemaining').textContent = state.topics.length - usedIds.length;
  document.getElementById('statTotalPoints').textContent = history.reduce((s, h) => s + h.pointsEarned, 0);

  if (history.length === 0) {
    list.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';

  list.innerHTML = history.map((h, i) => {
    const items = parseHint(h.hint);
    return `
    <div class="history-item" data-idx="${i}">
      <div class="history-content">
        <div class="history-meta">
          <span class="history-date">${formatDate(h.date)}</span>
          <span class="history-cat">${h.category}</span>
          <span class="history-points">+${h.pointsEarned} 积分</span>
          ${h.hintViewed ? '<span class="history-cat viewed">看过方向</span>' : ''}
        </div>
        <div class="history-topic">${escapeHtml(h.topic)}</div>
        <div class="history-hint"><ul>${items.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul></div>
      </div>
      <div class="history-actions">
        <button class="btn btn-ghost btn-sm" data-action="restore" data-idx="${i}">放回话题库</button>
      </div>
    </div>
  `;
  }).join('');

  list.querySelectorAll('[data-action="restore"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx);
      restoreTopic(idx);
    });
  });
}

function restoreTopic(idx) {
  const history = storage.get(STORAGE_KEYS.history, []);
  const item = history[idx];
  if (!item) return;
  const usedIds = new Set(storage.get(STORAGE_KEYS.usedIds, []));
  usedIds.delete(item.id);
  storage.set(STORAGE_KEYS.usedIds, [...usedIds]);
  const restoredIds = new Set(storage.get(STORAGE_KEYS.restoredIds, []));
  restoredIds.add(item.id);
  storage.set(STORAGE_KEYS.restoredIds, [...restoredIds]);
  history.splice(idx, 1);
  storage.set(STORAGE_KEYS.history, history);
  renderHistory();
  showToast('已放回话题库，下次抽到它的概率会更高');
}

// ====== 工具 ======
function formatDate(iso) {
  const d = new Date(iso);
  const pad = n => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
}

let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2400);
}

function showPointsModal(n) {
  const modal = document.getElementById('pointsModal');
  document.getElementById('pointsModalTitle').textContent = '讨论完成！';
  document.getElementById('pointsModalBody').innerHTML = `
    <div class="modal-points">+${n}</div>
    <div>积分</div>
    <div style="margin-top:14px;font-size:13px;">当前累计：<b>${getPoints()}</b> 积分</div>
  `;
  modal.classList.add('show');
  setTimeout(() => modal.classList.remove('show'), 1800);
}

// ====== 事件绑定 ======
function bindEvents() {
  document.getElementById('btnDraw').addEventListener('click', pickTopic);
  document.getElementById('btnViewHint').addEventListener('click', viewHint);
  document.getElementById('btnSkip').addEventListener('click', skipTopic);
  document.getElementById('btnEnd').addEventListener('click', endDiscussion);

  // Tab 切换
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      document.getElementById('view' + capitalize(tab.dataset.view)).classList.add('active');
    });
  });

  // 主题按钮
  document.getElementById('themeBtn').addEventListener('click', e => {
    e.stopPropagation();
    toggleThemePicker();
  });
  document.querySelectorAll('.theme-option').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      applyTheme(btn.dataset.theme);
      renderThemeOptions();
      toggleThemePicker(false);
    });
  });
  // 点别处关闭主题选择
  document.addEventListener('click', () => toggleThemePicker(false));

  // 点击积分卡：弹出积分说明
  document.getElementById('pointsCard').addEventListener('click', () => {
    document.getElementById('pointsModalTitle').textContent = '积分说明';
    document.getElementById('pointsModalBody').innerHTML = `
      <div style="text-align:left;line-height:2;">
        <div>✓ 完成一次讨论（未看方向）：<b>+${POINTS.endDiscussion} 积分</b></div>
        <div>✓ 完成一次讨论（看过方向）：<b>+${Math.max(2, POINTS.endDiscussion - POINTS.viewHint)} 积分</b></div>
        <div>💡 查看参考方向：<b>-${POINTS.viewHint} 积分</b></div>
        <div>🎁 初始赠送：<b>${POINTS.startBonus} 积分</b></div>
        <hr style="margin:14px 0;border:none;border-top:1px solid var(--border);">
        <div style="text-align:center;font-size:13px;color:var(--ink-soft);">当前：<b style="color:var(--primary-dark);">${getPoints()}</b> 积分</div>
      </div>
    `;
    document.getElementById('pointsModal').classList.add('show');
  });

  // 关闭 modal
  document.querySelectorAll('[data-close]').forEach(el => {
    el.addEventListener('click', () => el.closest('.modal-mask').classList.remove('show'));
  });

  // 键盘快捷键：空格抽话题
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.code === 'Space') {
      e.preventDefault();
      pickTopic();
    }
  });
}

function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ====== 启动 ======
init().catch(err => {
  console.error(err);
  showToast('数据加载失败：' + err.message);
});
