# 映射表

- adb 命令参考 adb.txt
- go-ios 命令参考 ios.txt

前置条件：go-ios需要提前执行`ios tunnel start --userspace`启动隧道。

## 表

| 功能 | CLI | HTTP | gRPC | MCP | iOS(go-ios) | iOS(WDA) | Android(adb) | Android(uiautomator2) |
|------|------|------|------|------|------|------|------|------|
| 列出设备 | `udg list` | `GET /devices` | `ListDevices` | `list_devices` | `ios list` | - | `adb devices` | - |
| 推送文件 | `udg push <local> <remote>` | `POST /push` | `PushFile` | `push_file` | `ios file push` | - | `adb push` | - |
| 拉取文件 | `udg pull <remote> <local>` | `POST /pull` | `PullFile` | `pull_file` | `ios file pull` | - | `adb pull` | - |
| 列出应用 | `udg apps` | `GET /apps` | `ListApps` | `list_apps` | `ios apps` | `/wda/apps` | `adb shell pm list packages` | - |
| 安装应用 | `udg install <path>` | `POST /install` | `InstallApp` | `install_app` | `ios install` | - | `adb install -r` | - |
| 卸载应用 | `udg uninstall <pkg>` | `POST /uninstall` | `UninstallApp` | `uninstall_app` | `ios uninstall` | - | `adb uninstall` | - |
| 启动应用 | `udg launch <pkg>` | `POST /launch` | `LaunchApp` | `launch_app` | - | `/wda/apps/launch` | `am start` | - |
| 停止应用 | `udg stop <pkg>` | `POST /stop` | `StopApp` | `stop_app` | - | `/wda/apps/terminate` | `am force-stop` | - |
| 获取电量 | `udg battery` | `GET /battery` | `GetBattery` | `get_battery` | - | `/wda/batteryInfo` | `dumpsys battery` | - |
| 获取IP地址 | `udg ip` | `GET /ip` | `GetIP` | `get_ip` | - | `/wda/batteryInfo` | `dumpsys battery` | - |
| 获取当前应用 | `udg current app <id>` | `GET /current/app` | `GetCurrentApp` | `get_current_app` | - | `/wda/activeElementInfo` | `dumpsys activity` | - |
| 点击 | `udg tap <x> <y>` | `POST /tap` | `Tap` | `tap` | - | `/wda/touch/perform` | `input tap` | `d.click(x, y)` |
| 滑动 | `udg swipe <x1> <y1> <x2> <y2> <duration>` | `POST /swipe` | `Swipe` | `swipe` | - | `/wda/touch/perform` | `input swipe` | `d.swipe(x1, y1, x2, y2, duration)` |
| 按键 | `udg press <key>` | `POST /press` | `Press` | `press` | - | `/wda/touch/perform` | `input swipe` | `d.press("home")` |
| 按钮 | `udg click <text>` | `POST /click` | `Click` | `click` | - | `/wda/touch/perform` | `input swipe` | `d.click("ok")` |
| 输入 | `udg input <text>` | `POST /input` | `Input` | `input` | - | `/wda/touch/perform` | `input swipe` | `d.input("home")` |
| 弹窗 | `udg alert <text>` | `POST /alert` | `Alert` | `alert` | - | `/wda/touch/perform` | `input swipe` | `d.alert("submit")` |
| 截屏 | `udg screenshot <id>` | `GET /screenshot` | `Screenshot` | `screenshot` | `c.screenshot('screen.png')` | - | `screencap` | `d.screenshot("screen.png")` |
| 录屏 | `udg record [path]` | `POST /record` | `StartRecord` | `start_record` | `ios recordVideo` | - | `screenrecord` | - |
| 断言 | `udg assert <id>` | `POST /assert` | `Assert` | `assert` | - | - | - | - |
| UI dump | `udg ui dump <id>` | `POST /execute` | `Execute` | `execute_command` | - | - | - | `uiautomator dump` |
| 通用 | `udg execute <id>` | `POST /execute` | `Execute` | `execute` | - | - | - | - |

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

# 轮换 token
udg token rotate
```

参数设置支持

-d <id> 或 --device <id> 或 --device=<id> 不指定设备时，默认使用列表中的第一个
