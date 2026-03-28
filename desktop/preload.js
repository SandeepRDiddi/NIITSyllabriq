const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("desktopInfo", {
  mode: "electron"
});
