/* ============================================================
   api.js —— 后端接口封装 + 通用小工具
   ============================================================ */
(function (global) {
  'use strict';

  var base = (document.querySelector('meta[name="wp-base"]') || {}).content || '';
  base = base.replace(/\/$/, '');

  function url(path) {
    path = String(path || '');
    if (/^(https?:|blob:|data:)/i.test(path)) return path;
    return base + (path.charAt(0) === '/' ? path : '/' + path);
  }

  function download(path, filename) {
    return fetch(url(path)).then(function (res) {
      if (!res.ok) throw new Error('下载失败（HTTP ' + res.status + '）');
      return res.blob();
    }).then(function (blob) {
      var objectUrl = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(objectUrl); }, 60000);
    });
  }

  async function request(method, path, body, isForm) {
    var opt = { method: method, headers: {} };
    if (isForm) {
      opt.body = body;
    } else if (body !== undefined && body !== null) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    var res;
    try {
      res = await fetch(url(path), opt);
    } catch (e) {
      var neterr = new Error('网络不通');
      neterr.network = true;
      throw neterr;
    }
    var text = await res.text();
    var data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error('服务器返回了非 JSON 内容（HTTP ' + res.status + '）');
    }
    if (!res.ok || data.ok === false) {
      // 家庭版：登录失效 / 还没改初始密码，统一跳转，页面不用各自处理（也不弹错误）
      if (data.code === 'login_required' && global.AuthUI) { AuthUI.go('login.html', true); return new Promise(function () {}); }
      if (data.code === 'password_change_required' && global.AuthUI) { AuthUI.go('change-password.html', true); return new Promise(function () {}); }
      var err = new Error(data.error || ('请求失败（HTTP ' + res.status + '）'));
      err.code = data.code || '';
      err.status = res.status;
      throw err;
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
    path: url,
    download: download,
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
