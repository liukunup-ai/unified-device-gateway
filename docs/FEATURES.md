# Unified Device Gateway (UDG) 功能规划

## 概述

UDG 是一个统一设备网关，通过 HTTP、gRPC、MCP 三种协议控制 iOS、Android、Serial 设备。

---

## 一、CLI 命令

### 1.1 已实现

| 命令 | 说明 | 示例 |
|------|------|------|
| `udg start` | 启动服务 | `udg start` |
| `udg version` | 显示版本 | `udg version` |
| `udg token show` | 显示当前 Token | `udg token show` |
| `udg token rotate` | 轮换 Token | `udg token rotate` |
| `udg device list` | 列出设备 | `udg device list` |

### 1.2 规划中

| 命令 | 说明 | 优先级 |
|------|------|--------|
| `udg device add <type>` | 添加设备 | P1 |
| `udg device remove <id>` | 移除设备 | P1 |
| `udg device connect <id>` | 连接设备 | P1 |
| `udg device disconnect <id>` | 断开设备 | P1 |
| `udg device exec <id> <cmd>` | 在设备上执行命令 | P1 |
| `udg device screenshot <id>` | 截图 | P2 |
| `udg config set <key> <value>` | 设置配置 | P2 |
| `udg config get <key>` | 获取配置 | P2 |
| `udg serve --http <port> --grpc <port>` | 指定端口启动 | P3 |
| `udg health` | 健康检查 | P3 |

---

## 二、HTTP API

### 2.1 已实现

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/health` | GET | 健康检查 | 否 |
| `/health/ready` | GET | 就绪检查 | 否 |
| `/health/live` | GET | 存活检查 | 否 |
| `/metrics` | GET | Prometheus 指标 | 否 |
| `/routes` | GET | 查看所有路由 | 否 |
| `/devices` | GET | 列出设备 | Bearer Token |
| `/execute` | POST | 执行命令 | Bearer Token |
| `/mcp` | SSE | MCP 协议端点 | 否 |

### 2.2 规划中

| 端点 | 方法 | 说明 | 认证 | 优先级 |
|------|------|------|------|--------|
| `/devices` | POST | 添加设备 | Bearer Token | P1 |
| `/devices/{id}` | DELETE | 删除设备 | Bearer Token | P1 |
| `/devices/{id}/connect` | POST | 连接设备 | Bearer Token | P1 |
| `/devices/{id}/disconnect` | POST | 断开设备 | Bearer Token | P1 |
| `/devices/{id}/screenshot` | GET | 截图 | Bearer Token | P2 |
| `/devices/{id}/execute` | POST | 单设备执行命令 | Bearer Token | P1 |
| `/devices/scan` | POST | 扫描设备 | Bearer Token | P2 |
| `/config` | GET | 获取配置 | Bearer Token | P2 |
| `/config` | PUT | 更新配置 | Bearer Token | P3 |
| `/tokens` | POST | 创建 Token | Bearer Token | P3 |
| `/tokens` | GET | 列出 Token | Bearer Token | P3 |
| `/tokens/{id}` | DELETE | 删除 Token | Bearer Token | P3 |

---

## 三、gRPC API

### 3.1 已实现

| 服务 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `DeviceGateway` | `ListDevices` | 列出设备 | 骨架 (返回空) |
| `DeviceGateway` | `Execute` | 执行命令 | 骨架 (返回空) |

### 3.2 规划中

| 服务 | 方法 | 说明 | 优先级 |
|------|------|------|--------|
| `DeviceGateway` | `GetDevice` | 获取设备详情 | P1 |
| `DeviceGateway` | `ConnectDevice` | 连接设备 | P1 |
| `DeviceGateway` | `DisconnectDevice` | 断开设备 | P1 |
| `DeviceGateway` | `AddDevice` | 添加设备 | P1 |
| `DeviceGateway` | `RemoveDevice` | 删除设备 | P1 |
| `DeviceGateway` | `Screenshot` | 截图 | P2 |
| `DeviceGateway` | `InstallApp` | 安装应用 | P2 |
| `DeviceGateway` | `UninstallApp` | 卸载应用 | P2 |
| `DeviceGateway` | `StartApp` | 启动应用 | P2 |
| `DeviceGateway` | `StopApp` | 停止应用 | P2 |
| `DeviceGateway` | `ListApps` | 列出已安装应用 | P2 |
| `DeviceGateway` | `GetDeviceProperties` | 获取设备属性 | P3 |
| `DeviceGateway` | `StreamScreen` | 屏幕流 | P3 |

---

## 四、MCP (Model Context Protocol)

### 4.1 已实现

#### Tools

| 工具 | 参数 | 说明 |
|------|------|------|
| `list_devices` | 无 | 列出所有设备 |
| `get_device_info` | `device_id: str` | 获取设备详情 |
| `execute_command` | `device_id`, `command`, `timeout` | 执行 shell 命令 |
| `screenshot` | `device_id: str` | 截图 |

#### Resources

| 资源 URI | 说明 |
|----------|------|
| `device://list` | 设备列表 JSON |
| `device://{device_id}` | 单个设备详情 |

### 4.2 规划中

#### Tools

| 工具 | 参数 | 说明 | 优先级 |
|------|------|------|--------|
| `connect_device` | `device_id: str` | 连接设备 | P1 |
| `disconnect_device` | `device_id: str` | 断开设备 | P1 |
| `add_device` | `type`, `params` | 添加设备 | P1 |
| `remove_device` | `device_id: str` | 删除设备 | P1 |
| `install_app` | `device_id`, `path` | 安装应用 | P2 |
| `uninstall_app` | `device_id`, `bundle_id` | 卸载应用 | P2 |
| `start_app` | `device_id`, `bundle_id` | 启动应用 | P2 |
| `stop_app` | `device_id`, `bundle_id` | 停止应用 | P2 |
| `list_apps` | `device_id: str` | 列出已安装应用 | P2 |
| `get_device_screen` | `device_id: str` | 获取屏幕流 | P3 |
| `press_button` | `device_id`, `button` | 按键 | P2 |
| `input_text` | `device_id`, `text` | 输入文本 | P2 |
| `swipe` | `device_id`, `start_x`, `start_y`, `end_x`, `end_y` | 滑动 | P2 |

#### Resources

| 资源 URI | 说明 | 优先级 |
|----------|------|--------|
| `device://{device_id}/screen` | 设备屏幕截图 | P2 |
| `device://{device_id}/apps` | 已安装应用列表 | P2 |
| `device://{device_id}/properties` | 设备属性 | P3 |
| `system://info` | 系统信息 | P3 |

#### Prompts

| Prompt | 说明 | 优先级 |
|--------|------|--------|
| `device-control` | 设备控制对话模板 | P3 |
| `screen-automation` | 屏幕自动化模板 | P3 |

---

## 五、设备命令

### 5.1 Android (adb)

| 命令 | 参数 | 说明 | 状态 |
|------|------|------|------|
| `shell` | `cmd: str` | 执行 shell 命令 | ✅ |
| `uiautomator` | `method: str`, `cmd: str` | UiAutomator 操作 | ✅ |
| `screenshot` | 无 | 截图 | ✅ |
| `install` | `path: str` | 安装 APK | ✅ |

#### 规划中

| 命令 | 参数 | 说明 | 优先级 |
|------|------|------|--------|
| `start_activity` | `package`, `activity` | 启动 Activity | P2 |
| `stop_app` | `package: str` | 停止应用 | P2 |
| `clear_app` | `package: str` | 清除应用数据 | P2 |
| `push` | `local_path`, `remote_path` | 推送文件 | P2 |
| `pull` | `remote_path`, `local_path` | 拉取文件 | P2 |
| `input_text` | `text: str` | 输入文本 | P2 |
| `tap` | `x: int`, `y: int` | 点击坐标 | P2 |
| `swipe` | `start_x`, `start_y`, `end_x`, `end_y` | 滑动 | P2 |
| `press_key` | `keycode: int` | 按键 | P2 |
| `dump_ui` | 无 | 获取 UI 层次结构 | P2 |
| `get_clipboard` | 无 | 获取剪贴板 | P3 |
| `set_clipboard` | `text: str` | 设置剪贴板 | P3 |

### 5.2 iOS (tidevice/WDA)

| 命令 | 参数 | 说明 | 状态 |
|------|------|------|------|
| `shell` | `cmd: str` | 执行命令 | ✅ |
| `wda_command` | `method`, `path`, `body` | WDA 命令 | ✅ |
| `screenshot` | 无 | 截图 | ✅ |
| `install` | `path: str` | 安装应用 | ✅ |

#### 规划中

| 命令 | 参数 | 说明 | 优先级 |
|------|------|------|--------|
| `start_wda` | `port: int` | 启动 WDA | P2 |
| `stop_wda` | 无 | 停止 WDA | P2 |
| `start_app` | `bundle_id: str` | 启动应用 | P2 |
| `stop_app` | `bundle_id: str` | 停止应用 | P2 |
| `list_apps` | 无 | 列出已安装应用 | P2 |
| `install_wda` | 无 | 安装 WDA | P3 |
| `touch` | `x: int`, `y: int` | 点击 | P2 |
| `swipe` | `start_x`, `start_y`, `end_x`, `end_y` | 滑动 | P2 |
| `input_text` | `text: str` | 输入文本 | P2 |
| `press_button` | `button: str` | 按键 (home/back) | P2 |

### 5.3 Serial

| 命令 | 参数 | 说明 | 状态 |
|------|------|------|------|
| `write` | `data: str` | 写入数据 | 骨架 |
| `read` | `length: int` | 读取数据 | 骨架 |

#### 规划中

| 命令 | 参数 | 说明 | 优先级 |
|------|------|------|--------|
| `read_line` | 无 | 读取一行 | P2 |
| `set_baudrate` | `rate: int` | 设置波特率 | P2 |
| `flush` | 无 | 刷新缓冲区 | P3 |

---

## 六、配置项

### 6.1 已支持

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UDG_HTTP_PORT` | 8080 | HTTP 端口 |
| `UDG_GRPC_PORT` | 50000 | gRPC 端口 |
| `UDG_TOKEN` | 自动生成 | 认证 Token |
| `UDG_MAX_CONNECTIONS` | 50 | 最大连接数 |
| `UDG_COMMAND_TIMEOUT_MS` | 60000 | 命令超时 (毫秒) |
| `UDG_DEVICE_SCAN_INTERVAL` | 60 | 设备扫描间隔 (秒) |
| `UDG_REDIS_URL` | None | Redis URL (可选) |
| `UDG_LOG_LEVEL` | INFO | 日志级别 |
| `UDG_LOG_PATH` | `~/.udg/logs/udg.log` | 日志路径 |
| `UDG_TOKEN_FILE` | `~/.udg/token` | Token 文件路径 |

### 6.2 规划中

| 变量 | 默认值 | 说明 | 优先级 |
|------|--------|------|--------|
| `UDG_DEVICE_SCAN_ENABLE` | true | 是否自动扫描设备 | P2 |
| `UDG_HTTP_HOST` | 0.0.0.0 | HTTP 监听地址 | P2 |
| `UDG_AUTH_ENABLE` | true | 是否启用认证 | P3 |
| `UDG_METRICS_ENABLE` | true | 是否启用指标 | P3 |
| `UDG_TLS_ENABLE` | false | 是否启用 TLS | P3 |
| `UDG_TLS_CERT` | None | TLS 证书路径 | P3 |
| `UDG_TLS_KEY` | None | TLS 密钥路径 | P3 |

---

## 七、协议支持矩阵

| 功能 | HTTP | gRPC | MCP |
|------|------|------|-----|
| 健康检查 | ✅ | - | - |
| 列出设备 | ✅ | ✅ | ✅ |
| 获取设备信息 | ✅ | 规划中 | ✅ |
| 执行命令 | ✅ | ✅ | ✅ |
| 截图 | 规划中 | 规划中 | ✅ |
| 添加设备 | 规划中 | 规划中 | 规划中 |
| 删除设备 | 规划中 | 规划中 | 规划中 |
| 连接设备 | 规划中 | 规划中 | 规划中 |
| 断开设备 | 规划中 | 规划中 | 规划中 |
| 安装应用 | 规划中 | 规划中 | 规划中 |

---

## 八、优先级说明

| 优先级 | 说明 |
|--------|------|
| P1 | 高优先级，必须实现 |
| P2 | 中优先级，应该实现 |
| P3 | 低优先级，可以后续实现 |

---

## 九、里程碑

### v0.1.0 (当前版本)

- [x] HTTP REST API 基础端点
- [x] gRPC 服务骨架
- [x] MCP 工具 (list_devices, execute_command, screenshot)
- [x] Token 认证
- [x] Android 设备支持 (shell, screenshot, install)
- [x] iOS 设备支持 (shell, screenshot, install)
- [x] CLI 基础命令

### v0.2.0

- [ ] 完整的 gRPC 实现
- [ ] 设备连接/断开功能
- [ ] 添加/删除设备 API
- [ ] MCP connect/disconnect/add/remove 工具
- [ ] 设备扫描功能

### v0.3.0

- [ ] 应用管理 (安装/卸载/启动/停止)
- [ ] UI 自动化基础 (tap, swipe, input_text)
- [ ] UI 层次结构获取 (dump)
- [ ] Serial 设备完整支持

### v0.4.0

- [ ] TLS 支持
- [ ] 多 Token 管理
- [ ] Redis 集成
- [ ] WebSocket 屏幕流
- [ ] 远程设备支持
