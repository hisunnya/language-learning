/* ============================================================
   api.js —— 后端接口封装 + 通用小工具
   ============================================================ */
(function (global) {
  'use strict';

  function url(path) {
    return path.charAt(0) === '/' ? path : '/' + path;
  }

  async function request(method, path, body, isForm) {
    var opt = { method: method, headers: {} };
    if (isForm) {
      opt.body = body;
    } else if (body !== undefined && body !== null) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    var res = await fetch(url(path), opt);
    var text = await res.text();
    var data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error('服务器返回了非 JSON 内容（HTTP ' + res.status + '）');
    }
    if (!res.ok || data.ok === false) {
      throw new Error(data.error || ('请求失败（HTTP ' + res.status + '）'));
    }
    return data;
  }

  var toastTimer = null;
  function toast(msg, ms) {
    var t = document.getElementById('toast');
    if (!t) { alert(msg); return; }
    t.textContent = msg;
    t.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('on'); }, ms || 2600);
  }

  function showMsg(el, text, kind) {
    if (!el) return;
    el.className = 'msg on ' + (kind || 'info');
    el.textContent = text;
    if (kind === 'ok' || kind === 'err') {
      setTimeout(function () { el.classList.remove('on'); }, 6000);
    }
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fmtTime(ts) {
    if (!ts) return '';
    var d = new Date(ts);
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  global.API = {
    get: function (p) { return request('GET', p); },
    post: function (p, body) { return request('POST', p, body); },
    del: function (p) { return request('DELETE', p); },
    upload: function (p, formData) { return request('POST', p, formData, true); },
    toast: toast,
    msg: showMsg,
    esc: esc,
    fmtTime: fmtTime
  };
})(window);
