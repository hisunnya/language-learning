/* ============================================================
   wechat.js —— 微信内置浏览器的兼容处理（只在 UA 里有 MicroMessenger 时由 module-header.js 加载）
   ------------------------------------------------------------
   1. <html> 加 is-wechat，样式要区分时用。
   2. 安卓微信有自己的「字体大小」设置，会把网页文字整体放大、把版面撑坏：
      调 WeixinJSBridge 的 setFontSizeCallback 让它别管。
   3. 微信里点下载没有反应（blob / 文件下载被拦）：声明了 <body data-wx-download> 的页面
      （导出名单、初始密码、离线页）顶部显示一条可关闭的提示，告诉老师点右上角「···」→「在浏览器打开」。
   纯 ES5，不依赖别的脚本。
   ============================================================ */
(function (global) {
  'use strict';

  var TIP = {
    zh: '在微信里无法下载文件。请点右上角「···」，选择「在默认浏览器打开」后再操作。',
    en: 'Files cannot be downloaded inside WeChat. Tap “···” at the top right and choose “Open in browser”.'
  };
  var CLOSE = { zh: '知道了', en: 'Got it' };
  var DISMISS_KEY = 'wx_download_tip_closed';

  function isWeChat(ua) { return /MicroMessenger/i.test(ua || ''); }

  function currentLang(doc) {
    var l = (doc.documentElement.getAttribute('lang') || '').toLowerCase();
    return l.indexOf('en') === 0 ? 'en' : 'zh';
  }

  /* 让微信别按它的字号设置缩放页面（官方桥接口，微信安卓有效，iOS 上无害） */
  function keepFontSize(win) {
    function apply() {
      try {
        win.WeixinJSBridge.invoke('setFontSizeCallback', { fontSize: 0 });
        win.WeixinJSBridge.on('menu:setfont', function () {
          win.WeixinJSBridge.invoke('setFontSizeCallback', { fontSize: 0 });
        });
      } catch (e) { /* 桥不在就算了 */ }
    }
    if (typeof win.WeixinJSBridge === 'object' && win.WeixinJSBridge && win.WeixinJSBridge.invoke) apply();
    else win.document.addEventListener('WeixinJSBridgeReady', apply, false);
  }

  function dismissed(win) {
    try { return win.sessionStorage.getItem(DISMISS_KEY) === '1'; } catch (e) { return false; }
  }

  function showDownloadTip(win) {
    var doc = win.document;
    if (!doc.body || !doc.body.hasAttribute('data-wx-download') || dismissed(win) || doc.getElementById('wxDownloadTip')) return null;
    var bar = doc.createElement('div');
    bar.id = 'wxDownloadTip';
    bar.setAttribute('role', 'status');
    bar.style.cssText = 'position:relative;z-index:50;margin:0 0 10px;padding:10px 12px;background:#fff3cd;color:#664d03;' +
      'border:1px solid #ffe69c;border-radius:10px;font-size:14px;line-height:1.5;';
    var text = doc.createElement('span');
    var button = doc.createElement('button');
    button.type = 'button';
    button.style.cssText = 'margin-left:10px;padding:4px 12px;border:1px solid #d6a800;background:#fff;color:#664d03;border-radius:8px;font-size:14px;';
    function paint() {
      var l = currentLang(doc);
      text.textContent = TIP[l];
      button.textContent = CLOSE[l];
    }
    paint();
    win.addEventListener('portal-lang-change', paint);
    button.addEventListener('click', function () {
      try { win.sessionStorage.setItem(DISMISS_KEY, '1'); } catch (e) { /* 存不了就算了，下次还会提示 */ }
      if (bar.parentNode) bar.parentNode.removeChild(bar);
    });
    bar.appendChild(text);
    bar.appendChild(button);
    doc.body.insertBefore(bar, doc.body.firstChild);
    return bar;
  }

  function start(win) {
    var ua = (win.navigator && win.navigator.userAgent) || '';
    if (!isWeChat(ua)) return false;
    win.document.documentElement.className += ' is-wechat';
    keepFontSize(win);
    if (win.document.body) showDownloadTip(win);
    else win.document.addEventListener('DOMContentLoaded', function () { showDownloadTip(win); });
    return true;
  }

  var api = { isWeChat: isWeChat, start: start, showDownloadTip: showDownloadTip, keepFontSize: keepFontSize };
  if (global.document) start(global);
  global.WPWeChat = api;
})(typeof window !== 'undefined' ? window : this);
