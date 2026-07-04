# phonecli

基于坐标的 iOS 手机自动化工具包。使用 WebDriverAgent (WDA) 进行设备控制，
使用 LLM/VLM 进行理解和分类，使用 app map 进行确定性宏回放。

```
┌──────────────┐     subprocess      ┌─────────────────────────────────────┐
│  agent.py    │ ──────────────────→ │  cli.py                             │
│  循环/状态   │                     │  ├── device/  截图, 点击, ...       │
│  宏/VLM      │ ←──── JSON ──────── │  ├── macro/   构建, 运行, 校验     │
│  屏幕识别    │                     │  ├── llm/     任务匹配, XML验证     │
└──────────────┘                     │  └── vlm/     动作, 验证            │
                                     └────────────────┬────────────────────┘
┌──────────────┐                                      │ HTTP
│  daemon.py   │ ─── REPL 循环 ──→                    ▼
│  memory.py   │   多 app map        ┌──────────────────────┐
└──────────────┘                     │  WebDriverAgent       │
                                     │  运行于 iOS 设备      │
┌──────────────────────────────────┐ └──────────────────────┘
│  profile_builder.py              │
│  build_map.py  validate_map.py   │
│  sanitize_map.py                 │
│  五阶段自动构建流水线              │
└──────────────────────────────────┘
```

---

## 1. 环境配置

### 前置依赖

```bash
brew install libimobiledevice
pip install requests openai click pyyaml
```

### 安装 WebDriverAgent

WebDriverAgent (WDA) 是一个 iOS 测试运行器，通过 HTTP API 暴露设备控制能力——
所有操作都建立在它之上。

**第一步：克隆仓库并初始化**

```bash
brew install carthage            # bootstrap.sh 的依赖
git clone https://github.com/appium/WebDriverAgent.git
cd WebDriverAgent
./Scripts/bootstrap.sh
```

**第二步：在 Xcode 中打开**

```bash
open WebDriverAgent.xcodeproj
```

**第三步：配置签名**

`WebDriverAgentLib` 和 `WebDriverAgentRunner` 两个 target 都需要配置签名团队。
如果你没有付费的 Apple Developer 账号，可以使用个人 Apple ID（免费账号即可）：

1. 在 Xcode 中选择 **WebDriverAgentLib** target → **Signing & Capabilities**
2. 勾选 **Automatically manage signing**，选择你的 Team
3. 对 **WebDriverAgentRunner** target 重复上述操作
4. 如果 bundle identifier 冲突，可以修改它（例如在前面加上你的名字：`com.yourname.WebDriverAgentRunner`）

**第四步：构建并运行**

1. 在 Xcode 顶部选择 **WebDriverAgentRunner** scheme
2. 选择你连接的 iOS 设备作为目标
3. 按 **Cmd+U** (Product → Test) 构建并启动 WDA

首次运行时，iOS 会阻止开发者证书。前往 **设置 → 通用 → VPN 与设备管理 → 你的 Apple ID → 信任**，然后重新运行。

**第五步：端口转发**

WDA 在设备上监听。使用 `iproxy` 将其转发到本机：

```bash
brew install libimobiledevice   # 提供 iproxy
iproxy 8100 8100 &
```

**第六步：验证**

```bash
curl http://localhost:8100/status
# → {"value": {"state": "success", ...}, "sessionId": "..."}
```

如果收到包含 `"state": "success"` 的 JSON 响应，说明 WDA 已经就绪。

> **免费账号注意事项**：免费 provisioning profile 的有效期为 7 天。
> 你需要每周在 Xcode 中重新构建 WDA。付费开发者账号不受此限制。

### 配置 LLM/VLM

```bash
# 方案 A: OpenRouter（文字 + 视觉）
export API_KEY="sk-or-v1-..."
export API_BASE="https://openrouter.ai/api/v1"
export MODEL_NAME="qwen/qwen3.7-plus"

# 方案 B: DeepSeek（仅文字，用于构建 map）
export API_KEY="sk-..."
export API_BASE="https://api.deepseek.com/v1"
export MODEL_NAME="deepseek-v4-flash"

# 方案 C: 本地部署
export API_BASE="http://localhost:8002/v1"
export MODEL_NAME="Qwen/Qwen2.5-VL-7B-Instruct"
```

### 快速测试

```bash
python phonecli/cli.py device info
# → {"status": "ok", "width": 402, "height": 874, ...}
```

> 本文档中所有命令均在 **repo 根目录**（包含 `phonecli/` 的目录）下执行。
> 如果你希望先 `cd phonecli` 再运行，请去掉命令路径中的 `phonecli/` 前缀并相应调整输出路径。

---

## 2. 快速上手

> **工作目录**：以下所有命令在 repo 根目录（包含 `phonecli/` 的目录）下运行。
> CLI 的默认输出路径使用 `phonecli/app_maps/` 和 `phonecli/profiles/` 格式。

这个 5 分钟的教程将带你从零开始，跑通第一个手机自动化任务。

### 一次性配置

```bash
# 安装依赖
brew install libimobiledevice
pip install requests openai click pyyaml

# 配置 LLM（以 OpenRouter 为例）
export API_KEY="sk-or-v1-..."
export API_BASE="https://openrouter.ai/api/v1"
export MODEL_NAME="qwen/qwen3.7-plus"
```

按照 [第一章 — 安装 WebDriverAgent](#安装-webdriveragent) 的步骤在你的设备上运行 WDA，然后验证：

```bash
curl http://localhost:8100/status   # 应返回包含 "state": "success" 的 JSON
```

### 构建你的第一个 app map（约 10 分钟）

```bash
python phonecli/cli.py macro auto-build -b com.apple.Preferences -a Settings
```

这会爬取系统设置 app 并生成一个 app map。详见
[第三章 — 构建 app map](#3-构建-app-map)。

### 运行你的第一个任务

```bash
python phonecli/run.py --task "打开飞行模式"
```

Agent 会自动发现所有已构建的 app map，分解任务，回放宏操作，并通过 VLM 验证。

### 接下来

- **[第三章](#3-构建-app-map)**：为更多 app 构建 map
- **[第四章](#4-运行任务)**：单任务模式、交互式 daemon、跨 app 任务
- **[第七章](#7-cli-参考)**：完整 CLI 命令参考

---

## 3. 构建 app map

### 一键构建（推荐）

`auto-build` 命令自动执行全部五个阶段：

```bash
python phonecli/cli.py macro auto-build \
    -b com.apple.mobilecal \
    -a Calendar \
    -o phonecli/app_maps/calendar_map.yaml \
    --classify --enrich --redact
```

### 五阶段流水线

```
阶段 1: 采样 screen_0 → 收集可见元素文本（约 1 分钟）
阶段 2: LLM 生成 app 专属 profile（dynamic_patterns + preserve_navigation）
阶段 3: 使用 profile 进行 BFS 爬取 + LLM 分类 + 语义丰富（主构建过程）
阶段 4: 校验 map 的错误、数据质量和 profile 有效性
阶段 5: 脱敏 — LLM 批量检测并替换个人数据
```

### 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| App map | `phonecli/app_maps/<app>_map.yaml` | 完整导航图（屏幕、元素、宏） |
| Profile | `phonecli/profiles/<App>.yaml` | 动态内容的过滤规则 |
| 检查点 | `.checkpoints/<app>_checkpoint.json` | 断点续传文件（成功后自动删除） |

### 常用 Bundle ID

| App | Bundle ID |
|-----|-----------|
| 系统设置 | `com.apple.Preferences` |
| 日历 | `com.apple.mobilecal` |
| Safari | `com.apple.mobilesafari` |
| 小红书 | `com.xingin.discover` |
| 微博 | `com.sina.weibo` |
| 京东 | `com.jingdong.app.mall` |
| 大众点评 | `com.dianping.dpscope` |
| foodpanda | `com.foodpanda.ios` |
| 音乐 | `com.apple.Music` |

```bash
ideviceinstaller -l   # 列出已安装的 app
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-b, --bundle-id` | *(必填)* | iOS bundle ID |
| `-a, --app-name` | *(必填)* | 可读的 app 名称 |
| `-o, --output` | `phonecli/app_maps/app_map.yaml` | 输出路径 |
| `--max-screens` | `50` | 最大屏幕数量 |
| `--max-depth` | `3` | 最大导航深度 |
| `--scroll-pages` | `3` | 每屏滚动页数 |
| `--classify/--no-classify` | 开启 | LLM 稳定/动态元素分类 |
| `--enrich/--no-enrich` | 开启 | LLM 别名、语义类型、描述 |
| `--redact/--no-redact` | 开启 | 个人隐私信息脱敏 |
| `-c, --checkpoint` | 无 | 启用断点续传 |
| `-r, --resume` | 无 | 从检查点恢复 |

### 中断后恢复

```bash
# 首次运行并启用检查点
python phonecli/cli.py macro auto-build -b com.sina.weibo -a 微博 \
    -c .checkpoints/weibo_checkpoint.json

# 如果被中断（WDA 超时、网络问题等），恢复：
python phonecli/cli.py macro auto-build -b com.sina.weibo -a 微博 \
    -c .checkpoints/weibo_checkpoint.json \
    -r .checkpoints/weibo_checkpoint.json
```

### App Profile 格式

Profile 使用正则表达式过滤动态内容，并通过白名单保留导航元素：

```yaml
app: Calendar
bundle_id: com.apple.mobilecal
dynamic_patterns:
  - '^\d+$'              # 数字（计数、时间戳）
  - '^.{8,}$'            # 长文本（帖子标题、描述）
preserve_navigation:
  - Today
  - Calendars
  - Add
```

### App Map 结构

```yaml
app: Calendar
package: com.apple.mobilecal
screen_w: 402
screen_h: 874
launch_behavior: always_home
common_tasks:
  - Create a new event
  - Check today's schedule
screens:
  - id: screen_0
    description: "月视图，含导航标签"
    elements:
      - text: Today
        center: [0.1667, 0.9405]
        fixed: true
        leads_to: screen_4
        aliases: [current day, now, 今天]
        semantic_type: button
screen_macros:
  screen_0: [force_stop, launch]
  screen_4: [force_stop, launch, tap(67, 822)]
```

### 预置 Map

工具包自带了 8 个 app 的预构建 map：

| App | 屏幕数 | 元素数 | 边数 |
|-----|--------|--------|------|
| 微博 | 50 | 975 | 77 |
| foodpanda | 50 | 957 | 95 |
| Calendar | 50 | 948 | 88 |
| 京东 | 50 | ~700 | ~100 |
| 大众点评 | 50 | 501 | 70 |
| 小红书 | 50 | 405 | 142 |
| 音乐 | 50 | ~500 | ~80 |
| 设置 | 20 | ~200 | ~40 |

---

## 4. 运行任务

### 自动发现

`run.py` 会自动发现 `phonecli/app_maps/*.yaml` 中的所有 map 文件。无需指定
`--app-map` 即可运行：

```bash
python phonecli/run.py --task "打开飞行模式"
```

### 单任务模式

```bash
# 自动发现所有 map
python phonecli/run.py --task "打开飞行模式" --max-rounds 25

# 显式指定 map（单个或多个）
python phonecli/run.py --task "打开 Wi-Fi" \
    --app-map phonecli/app_maps/settings_map.yaml

# 纯 VLM 模式（不使用 map）
python phonecli/run.py --task "查看电量" --no-macro --max-rounds 30
```

### 交互式 Daemon

```bash
# 自动发现所有 map
python phonecli/run.py --interactive

# 显式指定 map（多 app）
python phonecli/run.py --interactive \
    --app-map phonecli/app_maps/settings_map.yaml \
    --app-map phonecli/app_maps/weibo_map.yaml

[phonecli] Task> 打开 Wi-Fi
[Agent] 宏回放完成 → Wi-Fi 已打开

[phonecli] Task> memory
  任务: 5 (成功 5 失败 0)
  操作: op_wifi_on 3次 (平均 8s)
```

### 跨 app 任务

Agent 通过 Planner（`llm plan` 命令）自动分解复杂的跨 app 任务，无需手动干预：

```bash
python phonecli/run.py --task "先小红书搜索，再京东比价，最后备忘录记录" --max-rounds 30
```

Planner 将任务拆分为单 app 子任务，顺序执行。对于未加载 map 的 app，自动跳过
LLM 映射，降级为纯 VLM 模式。

### REPL 命令

| 命令 | 操作 |
|------|------|
| `<任意任务>` | 在设备上执行 |
| `memory` | 查看任务历史和操作统计 |
| `forget` | 清除会话对话记忆 |
| `quit` | 退出 daemon |

---

## 5. Agent 特性

Agent（`agent.py`）通过混合方式编排任务执行：

| 特性 | 说明 |
|------|------|
| **宏路由** | 确定性回放预构建的 app map 操作 |
| **跨 app 感知** | 通过 WDA 检测前台 app，注入 VLM 上下文 |
| **智能宏/VLM 拆分** | 当任务需要搜索/输入时，自动升级为 MACRO_VLM |
| **动作反馈** | 每次动作后像素级对比截图，无变化时警告 VLM |
| **屏幕识别** | 将 XML dump 与 app map 匹配，提供导航目标 |
| **可用 app 列表** | 将已知 app 注入 VLM 上下文，确保 launch() 可靠 |
| **循环检测** | 当同一动作类型重复 3 次且无进展时中止 |
| **VLM 升级** | 连续 3 次 VLM 解析失败后自动注入 home() |
| **任务规划器** | 将跨 app 任务分解为单 app 子任务 |

---

## 6. 评估

```bash
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml --tasks 1,3,5
python phonecli/eval.py --no-macro --max-rounds 30   # 纯 VLM
python phonecli/eval.py --app-map phonecli/app_maps/settings_map.yaml -o results.json
```

---

## 7. CLI 参考

### 设备操作

```bash
python phonecli/cli.py device info
python phonecli/cli.py device screenshot -o /tmp/s.png
python phonecli/cli.py device xml -o /tmp/dump.xml
python phonecli/cli.py device tap 195 420
python phonecli/cli.py device swipe 195 600 195 200
python phonecli/cli.py device text "hello world"
python phonecli/cli.py device launch Settings
python phonecli/cli.py device back
python phonecli/cli.py device home
python phonecli/cli.py device long-press 195 420 -d 3000
```

### 宏操作

```bash
python phonecli/cli.py macro list -m phonecli/app_maps/settings_map.yaml
python phonecli/cli.py macro run -m phonecli/app_maps/settings_map.yaml --op-id op_wifi_on
python phonecli/cli.py macro sample -b com.apple.mobilecal -a Calendar
python phonecli/cli.py macro validate -m phonecli/app_maps/calendar_map.yaml
python phonecli/cli.py macro sanitize -m phonecli/app_maps/calendar_map.yaml
```

### LLM 操作

```bash
# 将任务映射到 app map 操作
python phonecli/cli.py llm map-task -m phonecli/app_maps/settings_map.yaml -t "打开 Wi-Fi"
# 从 XML 无障碍树验证任务是否完成
python phonecli/cli.py llm xml-verify -t "检查 Wi-Fi" --xml-file /tmp/dump.xml
# 将跨 app 任务分解为子任务
python phonecli/cli.py llm plan -t "先小红书搜索，再京东比价" \
    -m phonecli/app_maps/xiaohongshu_map.yaml \
    -m phonecli/app_maps/jd_map.yaml
```

### VLM 操作

```bash
python phonecli/cli.py vlm act -t "打开系统设置" -s /tmp/s.png
python phonecli/cli.py vlm verify -t "Wi-Fi 是否已打开？" -s /tmp/s.png
```

---

## 8. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | `EMPTY` | API 密钥（通用 fallback） |
| `API_BASE` | `http://localhost:8002/v1` | API 地址（通用 fallback） |
| `MODEL_NAME` | `Qwen/Qwen2.5-3B-Instruct` | 模型名称（通用 fallback） |
| `PHONECLI_LLM_API_KEY` | *(fallback)* | 文字 LLM 独立配置 |
| `PHONECLI_LLM_API_BASE` | *(fallback)* | 文字 LLM 端点 |
| `PHONECLI_LLM_MODEL` | *(fallback)* | 文字 LLM 模型 |
| `PHONECLI_VLM_API_KEY` | *(fallback)* | 视觉模型独立配置 |
| `PHONECLI_VLM_API_BASE` | *(fallback)* | 视觉模型端点 |
| `PHONECLI_VLM_MODEL` | *(fallback)* | 视觉模型 |
| `PHONECLI_WDA_URL` | `http://localhost:8100` | WDA 地址 |
| `PHONECLI_TASK_DIR` | `./phonecli_logs` | 日志目录 |

---

## 9. 常见问题

### WDA 无法连接

```bash
curl http://localhost:8100/status
# curl: (7) Failed to connect to localhost port 8100
```

- 检查 `iproxy` 是否在运行：`pgrep iproxy`。如果没有，重启它：`iproxy 8100 8100 &`
- 检查 USB 连接并确保设备已解锁
- 在 Xcode 中重新构建 WDA（Cmd+U）—— 会话可能已断开

### 代码签名过期

如果 Xcode 报告签名错误，你的免费 provisioning profile 可能已过期（7 天限期）。
在 Xcode 中重新打开 WebDriverAgent，前往 **Signing & Capabilities**，
重新启用自动签名。Xcode 将重新生成 profile。

### 运行中途 WDA 会话丢失

```
[WDA] session timed out / no active session
```

WDA 会话可能因不活跃而超时。Agent 会按需创建会话，但长时间暂停可能触发超时。
在 Xcode 中重启 WDA（Cmd+U），然后重新运行。

### iproxy 端口被占用

```
bind: Address already in use
```

杀掉旧的 iproxy 进程：

```bash
pkill iproxy
iproxy 8100 8100 &
```

### VLM 解析失败

```
[Agent] VLM parse failed 3x consecutively — injecting home()
```

VLM 偶尔会返回格式错误的坐标。Agent 在连续 3 次解析失败后会自动注入 `home()`
作为恢复策略。如果频繁发生，请尝试更强大的视觉模型或检查 API 密钥。

### 宏回放导航到错误的屏幕

如果宏导航到了错误的屏幕，说明 app map 可能已经过时（app UI 在构建 map 之后发生了变化）。
重新构建 map：

```bash
python phonecli/cli.py macro auto-build -b <bundle-id> -a <AppName>
```

### LLM 连接错误

```
openai.APIConnectionError / openai.RateLimitError
```

- 验证你的 `API_KEY` 是否有效、`API_BASE` 是否正确
- 检查速率限制或切换到其他服务商
- 对于本地模型，确保 vLLM/Ollama 服务正在运行

---

## 10. 架构

```
phonecli/
├── device.py           基于 WDA 的 iOS 设备操作（截图、点击、滑动、启动 app...）
├── app_map.py          YAML 加载器、屏幕识别、相对坐标宏
├── build_map.py        BFS app 爬虫（LLM 分类、固定/可滚动元素、隐私脱敏）
├── profile_builder.py  五阶段流水线编排（采样 → 生成 profile → 构建）
├── validate_map.py     阶段 4：map 校验（错误、数据质量、profile 有效性）
├── sanitize_map.py     阶段 5：LLM 批量检测并替换个人隐私数据
├── llm_client.py       OpenAI 兼容 API 客户端（文字 + 视觉）
├── prompts.py          所有 LLM/VLM 任务的系统提示词
├── cli.py              Click CLI — 四组命令（device / macro / llm / vlm）
├── agent.py            PhoneAgent 循环（宏路由、VLM、屏幕识别）
├── daemon.py           交互式 REPL 循环（会话复用、多 map）
├── memory.py           DialogueMemory + UserMemory（持久化、支持操作统计）
├── eval.py             批量评估（独立 VLM 裁判）
├── run.py              入口文件（单任务 / 交互模式）
├── app_maps/           预构建 app map（8 个 app）
└── profiles/           App 过滤 profile（8 个 app）
```
