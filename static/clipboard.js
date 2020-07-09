const RespStatus = {
  success: 0,
  fail: 1,
  error: 2,
};
var updateInterval;
Vue.use(VueClipboard);
var vm = new Vue({
  el: "#app",
  data: function () {
    return {
      clipboard: "",
      updateTime: 0,
      readonly: false,
      upToDate: false,
      lockStatus: false,
      lock_owner: "",
      online_users_num: 0,
    };
  },
  created() {
    this.polling();
  },
  computed: {
    upToDateStyle: function () {
      let cs = "";
      if (this.upToDate) {
        cs = "el-icon-check el-button--success";
      } else {
        cs = "el-icon-loading el-button--warning";
      }
      return cs.concat(" button-disable");
    },
    lockStatusStyle: function () {
      let cs = "";
      if (this.lockStatus) {
        cs = "el-icon-lock el-button--success";
      } else if (this.lock_owner) {
        cs = "el-icon-lock el-button--danger";
      } else {
        cs = "el-icon-unlock el-button--info";
      }
      return cs.concat(" button-disable");
    },
  },
  watch: {
    clipboard: function () {
      this.upToDate = false;
      if (this.lockStatus) {
        this.putClipboard();
      }
    },
  },
  methods: {
    onDelete() {
      if (this.lockStatus) {
        this.clipboard = "";
      } else {
        this.topMessage("请先点击文本框获得写入权限", "error");
      }
    },
    onCopy() {
      this.topMessage("复制成功", "success", "copy-message", true);
    },
    onError() {
      this.topMessage("复制失败", "error", "copy-message", true);
    },
    topMessage(message, type, customClass, center, duration) {
      type = type || "success";
      center = center || false;
      duration = duration || 2000;
      customClass = customClass || "message";
      this.$message({
        message: message,
        type: type,
        center: center,
        duration: duration,
        customClass: customClass,
      });
    },
    onFocus(event) {
      this.readonly = true;
      this.acquireLock(event);
    },
    onBlur() {
      setTimeout(() => {
        this.releaseLock();
      }, 200);
    },
    putClipboard() {
      let data = new FormData();
      data.append("data", this.clipboard);
      axios
        .post("./clipboard", data)
        .then((response) => {
          // console.log(response);
          if (response.data.status == RespStatus.success) {
            // 剪切板最后上传时间再过500ms，更新状态
            if (updateInterval) {
              clearInterval(updateInterval);
            }
            updateInterval = setTimeout(() => {
              this.upToDate = true;
            }, 500);
          } else {
            console.log("upload clipboard failed");
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
    heartbeat() {
      axios
        .post("./heartbeat")
        .then((response) => {
          this.lock_owner = response.data.lock_owner;
          this.online_users_num = response.data.online_users_num;
          // 未获得锁，就会刷新剪切板
          if (!this.lockStatus) {
            if (!this.upToDate) {
              this.upToDate = true;
            }

            this.clipboard = response.data.clipboard;
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
    polling() {
      this.heartbeat();
      setInterval(() => {
        this.heartbeat();
      }, 500);
    },
    acquireLock(event) {
      axios
        .get("./acquire_lock")
        .then((response) => {
          if (response.data.status == RespStatus.success) {
            console.log("acquire lock successed");
            this.lockStatus = true;
            this.readonly = false;
            flag_blur = false;
          } else if (response.data.status == RespStatus.fail) {
            console.log("acquire lock failed");
            this.topMessage("有人在编辑哦", "warning");
            event.srcElement.blur();
          } else {
            console.log("acquire lock error");
            this.topMessage("发生错误，请刷新网页", "error");
            event.srcElement.blur();
          }
        })
        .catch((error) => {
          console.log(error);
          this.topMessage("似乎是网络错误", "error");
          event.srcElement.blur();
        });
    },
    releaseLock() {
      if (!this.lockStatus) {
        return;
      }
      axios
        .get("./release_lock")
        .then((response) => {
          if (response.data.status == RespStatus.success) {
            console.log("release lock successed");
            // lock_owner需要通过轮询更新，这里提前清空lock_owner。
            // 自己释放锁后就不会出现“其他人正在编辑”的情况
            this.lock_owner = "";
            this.lockStatus = false;
          } else {
            console.log("release lock failed");
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
  },
});
