# 映射表

- adb 命令参考 adb.txt
- go-ios 命令参考 ios.txt
- hdc 命令参考 hdc.txt (HarmonyOS)

前置条件：
- go-ios需要提前执行`ios tunnel start --userspace`启动隧道
- hdc需要提前执行`hdc connect`连接HarmonyOS设备

## 表

### 1. 基础设备与文件管理

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **列出设备** | `udg list` | `GET /devices` | `ListDevices` | `list_devices` | `ios list` | - | `adb devices` | - | `hdc list targets` | - |
| **推送文件** | `udg push <local> <remote>` | `POST /push`<br>`{ "local": "a.txt", "remote": "/data/" }` | `PushFile` | `push_file` | `ios file push --bundle_id=xxx` | *(无)* | `adb push` | `d.push(local, remote)` | `hdc file send` | *(无)* |
| **拉取文件** | `udg pull <remote> <local>` | `POST /pull`<br>`{ "remote": "/data/a.txt" }` | `PullFile` | `pull_file` | `ios file pull --bundle_id=xxx` | *(无)* | `adb pull` | `d.pull(remote, local)` | `hdc file recv` | *(无)* |

### 2. 应用生命周期管理

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **列出应用** | `udg apps` | `GET /apps` | `ListApps` | `list_apps` | `ios apps` | `GET /wda/apps` | `adb shell pm list packages` | `d.app_list()` | `hdc shell bm dump -a` | *(无)* |
| **安装应用** | `udg install <path>` | `POST /install`<br>`{ "path": "/tmp/app.ipa" }` | `InstallApp` | `install_app` | `ios install` | *(无)* | `adb install -r` | `d.app_install("/path/to.apk")` | `hdc install -r` | *(无)* |
| **卸载应用** | `udg uninstall <pkg>` | `POST /uninstall`<br>`{ "bundle_id": "com.xx" }` | `UninstallApp` | `uninstall_app` | `ios uninstall` | *(无)* | `adb uninstall` | `d.app_uninstall("com.xx")` | `hdc uninstall` | *(无)* |
| **启动应用** | `udg launch <pkg>` | `POST /launch`<br>`{ "bundle_id": "com.xx" }` | `LaunchApp` | `launch_app` | *(go-ios无直接启动)* | `POST /wda/apps/launch`<br>`{"bundleId":"com.xx"}` | `adb shell am start -n pkg/act` | `d.app_start("com.xx")` | `hdc shell aa start -d` | *(无)* |
| **停止应用** | `udg stop <pkg>` | `POST /stop`<br>`{ "bundle_id": "com.xx" }` | `StopApp` | `stop_app` | *(无)* | `POST /wda/apps/terminate` | `adb shell am force-stop` | `d.app_stop("com.xx")` | `hdc shell bm force-stop` | *(无)* |

### 3. 设备信息获取

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **获取电量** | `udg battery` | `GET /battery` | `GetBattery` | `get_battery` | `ios diag --battery` | `GET /wda/batteryInfo` | `adb shell dumpsys battery` | `d.battery.info()` | `hdc shell hidump -d battery` | *(无)* |
| **获取IP地址** | `udg ip` | `GET /ip` | `GetIP` | `get_ip` | `ios diag --network` | `GET /wda/device/info` | `adb shell ifconfig wlan0` | `d.info.display['width']` *(需组合netifaces)* | `hdc shell ifconfig wlan0` | *(无)* |
| **获取当前应用** | `udg current-app` | `GET /current-app` | `GetCurrentApp` | `get_current_app` | *(无)* | `GET /wda/activeAppInfo` | `adb shell dumpsys activity` | `d.app_current()` | `hdc shell hidump -d top -a` | *(无)* |

### 4. 基础交互 (点击/滑动/按键)

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **点击** | `udg tap <x> <y>` | `POST /tap`<br>`{"x":100,"y":200}` | `Tap` | `tap` | *(无)* | `POST /wda/touch/perform`<br>`{"actions":[{"action":"tap","options":{"x":100,"y":200}}]}` | `adb shell input tap 100 200` | `d.click(x, y)` | `hdc shell input tap` | `uitest -t click` |
| **滑动** | `udg swipe <x1> <y1> <x2> <y2>` | `POST /swipe`<br>`{"fromX":0,"fromY":100,"toX":0,"toY":500,"duration":0.5}` | `Swipe` | `swipe` | *(无)* | `POST /wda/touch/perform`<br>`{"actions":[{"action":"press","options":{"x":0,"y":100}},{"action":"wait","options":{"ms":500}},{"action":"moveTo","options":{"x":0,"y":500}}]}` | `adb shell input swipe 0 100 0 500` | `d.swipe(x1, y1, x2, y2, duration)` | `hdc shell input swipe` | `uitest -t swipe` |
| **按键** | `udg press <key>`<br>(home/back/volup) | `POST /press`<br>`{"key":"home"}` | `Press` | `press` | *(无)* | `POST /wda/touch/perform` | `adb shell input keyevent KEYCODE_HOME` | `d.press("home")` | `hdc shell input keyevent` | *(无)* |

### 5. UI 元素交互 (按钮/输入/弹窗)

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **按钮** | `udg click-text <text>` | `POST /click-by-text`<br>`{"text":"提交"}` | `ClickByText` | `click_text` | *(无)* | `POST /wda/element/text`<br>`{"text":"提交"}` | *(adb无法直接按文本)* | `d.click(text="提交")` | *(无)* | `uitest -t text -a click` |
| **输入** | `udg input <text>` | `POST /input`<br>`{"text":"hello"}` | `Input` | `input_text` | *(无)* | `POST /wda/element/focused/setValue` | `adb shell input text "hello"` | `d.send_keys("hello")` | `hdc shell input text` | *(无)* |
| **弹窗** | `udg alert <action>`<br>(accept/dismiss) | `POST /alert`<br>`{"action":"accept"}` | `Alert` | `handle_alert` | *(无)* | `POST /wda/alert/accept`<br>`POST /wda/alert/dismiss` | *(adb无法处理弹窗)* | `d.alert.accept()` / `d.alert.dismiss()` | *(无)* | `uitest -a accept/dismiss` |

### 6. 屏幕录制与调试

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **截屏** | `udg screenshot [path]` | `GET /screenshot` | `Screenshot` | `screenshot` | `ios screenshot` | `GET /wda/screenshot` | `adb exec-out screencap -p` | `d.screenshot("screen.png")` | `hdc shell screencap -p` | *(无)* |
| **录屏** | `udg record [path]` | `POST /record/start`<br>`POST /record/stop` | `StartRecord`<br>`StopRecord` | `start_record` | `ios recordVideo --output=xxx.mp4` | *(WDA不支持录屏)* | `adb shell screenrecord /sdcard/demo.mp4` | *(u2不支持录屏)* | `hdc shell screenrecord` | *(无)* |
| **UI dump** | `udg ui dump` | `GET /ui/xml` | `DumpUI` | `dump_ui` | *(无)* | `GET /wda/source` | *(adb无直接dump)* | `d.dump_hierarchy()` | *(无)* | `uitest -a dump` |
| **断言** | `udg assert-text <text>` | `POST /assert/text`<br>`{"expected":"登录"}` | `AssertText` | `assert_text` | *(无)* | `POST /wda/element/text/exists` | *(无)* | `d(text="登录").wait(timeout=5)` | *(无)* | `uitest -t text -a exists` |

### 7. 串口通信 (仅限物理串口/ADB over serial)

*注：iOS 和 WDA 通常不支持通用串口操作，这一般是针对嵌入式设备或特定硬件。*

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **串口写入** | `udg write <port> <data>` | `POST /serial/write`<br>`{"port":"/dev/ttyS0","data":"AT\r"}` | `WriteSerial` | `serial_write` | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* |
| **串口读出** | `udg read <port> <bytes>` | `POST /serial/read`<br>`{"port":"/dev/ttyS0","bytes":1024}` | `ReadSerial` | `serial_read` | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* |
| **设置串口参数** | `udg config-serial <port> <baud>` | `POST /serial/config`<br>`{"port":"/dev/ttyS0","baud":115200}` | `SetSerialConfig` | `serial_set_config` | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* |
| **获取串口参数** | `udg get-serial <port>` | `GET /serial/config?port=...` | `GetSerialConfig` | `serial_get_config` | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* |
| **设置串口回调** | `udg serial-callback <url>` | `POST /serial/callback`<br>`{"port":"/dev/ttyS0","callback_url":"http://..."}` | `RegisterSerialCallback` | `serial_set_callback` | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* | *(不支持)* |

### 8. 通用与扩展

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) | HarmonyOS(hdc) | HarmonyOS(hiDriver) |
|------|------|------|------|------|------|------|------|------|------|------|
| **通用执行** | `udg exec <cmd>` | `POST /exec`<br>`{"command":"ls -la"}` | `ExecuteCommand` | `execute` | *(通过 `ios shell` 有限支持)* | *(WDA无shell)* | `adb shell <cmd>` | `d.shell("ls -la")` | `hdc shell <cmd>` | *(无)* |

### 关键修正说明 (相比原表)：

1.  **iOS IP地址**：原表写 `/wda/batteryInfo`，这是错误的。实际应为 `GET /wda/device/info` 或 `ios diag --network`。
2.  **iOS 启动/停止应用**：原表在 `go-ios` 列留空，WDA 列正确。`go-ios` 本身没有直接 launch 命令，通常需要配合 `devicectl` 或 libimobiledevice。
3.  **按钮/输入/弹窗**：原表中 iOS 部分全部错误地指向了 `/wda/touch/perform`（手势操作）。这些应该使用 WDA 的元素交互接口（如 `/wda/element` 系列）。
4.  **串口部分**：iOS (Lightning 转串口需要特定 MFI 芯片) 和 Android (除非是 rooted 或特定硬件) 默认都不支持标准串口操作。**这一列通常仅适用于嵌入式 Linux 或 PC 主机直连物理串口**。如果你需要针对 Android 的 USB 转串口外设，通常需要通过 NDK 或 JNI 单独实现，不在 adb/u2 的标准能力范围内。
5.  **断言**：原生工具链中几乎没有自带 "assert" 命令，这通常是测试框架（如 Pytest, JUnit）的工作。设计中改为 `assert-text` 这种具体行为。
6.  **HarmonyOS ui dump/click_by_text/assert_text**：使用 `uitest` 命令通过 hiDriver 调用，而非 hdc 直连。
7.  **HarmonyOS alert**：使用 `uitest -a accept/dismiss` 处理弹窗。
8.  **iOS alert**：正确实现为 `POST /wda/alert/accept` 和 `POST /wda/alert/dismiss`。

### 建议的 API 路径规范化 (RESTful)：

- 使用复数名词：`/devices`, `/apps`
- 使用具体资源：`/devices/{udid}/battery`
- 异步操作（如录屏、长按）：返回 `202 Accepted` + `Location` 头指向任务状态 API。
- 对于 MCP (Model Context Protocol)，建议使用标准 `tools/call` 格式，其中 `name` 对应上述 `list_devices` 等，`arguments` 为 JSON 参数。

## 其他

```bash
# 版本
udg version

# 帮助
udg help

# 运行
udg start

# 状态
udg status

# 查看 token
cat ~/.udg/token

# 轮换 token
udg token rotate
```

参数设置支持

-d <id> 或 --device <id> 或 --device=<id> 不指定设备时，默认使用列表中的第一个
