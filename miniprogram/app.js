App({
  globalData: {
    selection: null
  },

  onLaunch: function () {
    this.globalData.selection = wx.getStorageSync('wp_last_selection') || null;
  }
});
