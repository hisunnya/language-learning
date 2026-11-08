const audio = require('./utils/audio.js');
const config = require('./config.js');

App({
  globalData: {
    selection: null
  },

  onLaunch: function () {
    // 语音位置在 config.js 里配；没配就不启用，界面不显示 🔊，游戏照常玩
    audio.configure({ cloudPrefix: config.audioCloudPrefix, base: config.audioBase });
    this.globalData.selection = wx.getStorageSync('wp_last_selection') || null;
  }
});
