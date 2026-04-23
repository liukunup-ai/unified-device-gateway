# 统一设备接口重构设计

## 背景

当前实现使用 `execute(command, params, timeout_ms)` 大 switch 语句，违反开闭原则，难以维护和扩展。

## 目标

1. 拆分为独立公开方法，消除 execute() 的 if-elif 链
2. 定义统一接口协议，各平台明确实现
3. 不支持的方法返回 `NOT_SUPPORTED`

## 接口列表（23 个命令）

| # | 方法 | 参数 | 返回 | 说明 |
|---|------|------|------|------|
| 1 | `shell(cmd)` | str | dict | 通用执行 |
| 2 | `screenshot()` | - | dict | 截屏返回 base64 |
| 3 | `install(path)` | str | dict | 安装应用 |
| 4 | `push(local, remote)` | str, str | dict | 推送文件 |
| 5 | `pull(remote, local)` | str, str | dict | 拉取文件 |
| 6 | `list_apps()` | - | dict | 列出应用 |
| 7 | `uninstall(bundle_id)` | str | dict | 卸载应用 |
| 8 | `start_app(bundle_id, ability?)` | str, str? | dict | 启动应用 |
| 9 | `stop_app(bundle_id)` | str | dict | 停止应用 |
| 10 | `get_battery()` | - | dict | 获取电量 |
| 11 | `get_ip()` | - | dict | 获取 IP |
| 12 | `get_current_app()` | - | dict | 获取当前应用 |
| 13 | `tap(x, y)` | int, int | dict | 点击坐标 |
| 14 | `swipe(x1, y1, x2, y2, duration)` | int, int, int, int, int | dict | 滑动 |
| 15 | `press(key)` | str | dict | 按键 (home/back/volup) |
| 16 | `click_by_text(text)` | str | dict | 按文本点击 |
| 17 | `input_text(text)` | str | dict | 输入文本 |
| 18 | `handle_alert(action)` | str | dict | 弹窗 (accept/dismiss) |
| 19 | `screenrecord(path)` | str | dict | 开始录屏 |
| 20 | `stop_screenrecord()` | - | dict | 停止录屏 |
| 21 | `dump_ui()` | - | dict | UI dump XML |
| 22 | `assert_text(text)` | str | dict | 断言文本存在 |
| 23 | `wda_command(params)` | dict | dict | WDA 原始命令 (iOS) |

## 基类默认实现

所有方法默认返回 `NOT_SUPPORTED`：

```python
async def tap(self, x: int, y: int) -> dict:
    return {"status": "error", "error": "NOT_SUPPORTED", "output": None}
```

## 各平台实现

| 方法 | iOS | Android | HarmonyOS |
|------|-----|---------|-----------|
| shell | go-ios shell | adb shell | hdc shell |
| screenshot | go-ios screenshot | adb screencap | hdc shell screencap |
| install | go-ios install | adb install -r | hdc install -r |
| push | go-ios file push | adb push | hdc file send |
| pull | go-ios file pull | adb pull | hdc file recv |
| list_apps | WDA /wda/apps | adb pm list | hdc shell bm dump |
| uninstall | go-ios uninstall | adb uninstall | hdc uninstall |
| start_app | WDA /wda/apps/launch | adb am start | hdc shell aa start |
| stop_app | WDA /wda/apps/terminate | adb am force-stop | hdc shell bm force-stop |
| get_battery | WDA /wda/batteryInfo | adb dumpsys battery | hdc shell hidump -d battery |
| get_ip | go-ios diag --network | adb ifconfig wlan0 | hdc shell ifconfig wlan0 |
| get_current_app | WDA /wda/activeAppInfo | adb dumpsys activity | hdc shell hidump -d top |
| tap | WDA touch | adb input tap | uitest click |
| swipe | WDA touch + wait | adb input swipe | uitest swipe |
| press | NOT_SUPPORTED | adb input keyevent | uitest keyevent |
| click_by_text | WDA /wda/element/text | u2 d(text).click() | uitest -t click |
| input_text | WDA /wda/element/focused/setValue | adb input text | uitest inputtext |
| handle_alert | WDA /wda/alert/accept | u2 d.alert.accept() | uitest -a accept |
| screenrecord | go-ios recordVideo | adb screenrecord | hdc shell screenrecord |
| stop_screenrecord | 终止进程 | 终止进程 | 终止进程 |
| dump_ui | WDA /wda/source | u2 dump_hierarchy | uitest dump |
| assert_text | WDA /wda/element/text/exists | u2 d(text).exists | uitest -t exists |

## 重构步骤

1. 修改 `base.py`:
   - 基类 `BaseDevice` 实现所有 23 个方法，默认返回 `NOT_SUPPORTED`
   - `execute()` 方法简化为直接调用同名方法

2. 修改 `ios.py`:
   - 保留所有现有方法签名
   - 删除 execute() 中的 if-elif 链

3. 修改 `android.py`:
   - 同上

4. 修改 `harmonyos.py`:
   - 同上

5. 更新 `device_scanner.py`:
   - 注册新设备类型

## 预期结果

- `execute()` 方法变成简单的前向调用
- 每个命令独立成公开方法
- 不支持的功能返回 `NOT_SUPPORTED` 而非 `UNKNOWN_COMMAND`
