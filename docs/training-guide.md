# Claude 使用指南

**日常以 Claude Code CLI 为主，从网络配置到完成任务。**

Claude Code CLI 在终端中使用，可以直接读取项目文件、修改代码、运行命令并继续之前的任务。日常工作放在 CLI；首次登录、账单和账号管理按提示使用浏览器。

## 01 开始前，先把环境配好

本手册按以下顺序使用：**网络与出口 → CLI 代理 → 安装登录 → 日常任务 → 命令与用量 → 维护排障**。Windows 使用 PowerShell；macOS / Linux 使用系统终端。命令与安装方式按 2026 年 10 月 29 日的官方文档整理。

准备好管理员分配的节点或家宽配置、自己获授权的 Claude 账号，以及能在目标电脑读文件、执行命令的 Agent。配置还没拿到时，说明“尚未分配”。

### 需要自建 VPS 时，从官方入口购买

| 商家 | 注册 / 购买入口 | 套餐与价格 |
|---|---|---|
| LightNode | [官网](https://www.lightnode.com/) · [控制台](https://console.lightnode.com/) | [东京 VPS](https://go.lightnode.com/tokyo-vps) |
| Vultr | [官网](https://www.vultr.com/) · [控制台](https://my.vultr.com/) | [价格页](https://www.vultr.com/pricing/) |
| Akamai / Linode | [注册与登录](https://login.linode.com/) | [价格页](https://www.akamai.com/cloud/pricing/) |

购买前确认地区、Linux 系统、独立 IPv4、月流量和计费规则；付款后把服务器信息的本地文件位置交给 Agent 部署。VPS 通常提供机房 IP，住宅 / 家宽出口按对应资源另行选择。具体价格与库存以购买页面为准。

### 把下面整段交给本机 Agent

```text
请获取 https://github.com/SanN2Z/tanuki，读取 SKILL.md 并执行。
这台电脑用于个人日常工作，主要用 Claude Code CLI，同时需要浏览器完成登录。
已有配置先检测并修复，没有配置从零准备；优先复用管理员分配的资源。
请检查实际出口、CLI 的代理继承、官方客户端安装和认证方式，完成必要的已授权安装与可逆配置。
保留正在使用的代理和远程连接；涉及活动线路、系统代理、TUN 或防火墙切换时，先准备方案与回退，再让我确认。
完成后给我主线路、实际出口、CLI 启动方法、恢复方法和 RUN.md 位置。
```

当前 Claude 尚不能联网时，用另一个已经可用的本机 Agent，或请管理员先完成网络接入。只有普通网页聊天窗口时，需要把操作交给有本机执行权限的 Agent。

项目地址：<https://github.com/SanN2Z/tanuki>。GitHub 暂时无法访问时，由管理员传入完整仓库 ZIP，再让 Agent 读取其中的 `SKILL.md` 继续。

<div class="page-break"></div>

## 02 网络安全：确认实际走哪条出口

典型链路是：**你的电脑 → 本地代理客户端 → 管理员分配的固定出口 → Claude**。直达出口不稳定时，才按方案增加中转；最终出口仍使用管理员确认的资源。

### 先弄懂四个词

| 名称 | 实际含义 |
|---|---|
| 节点 | 代理客户端中的连接配置；名称不等于真实出口 |
| 出口 IP | Claude 实际看到的网络来源地址，以测量结果为准 |
| HTTP / mixed 端口 | CLI 接入本地代理的入口，与最终出口 IP 不同 |
| TUN / 断线保护 | 分别负责流量接管与故障时的连接行为，覆盖范围要验证 |

### 请 Agent 验证这几件事

| 验证对象 | 你应拿到的结果 |
|---|---|
| 实际出口 | 当前线路、出口地址、地区与测量时间 |
| Claude Code | 真实 CLI 进程使用的代理及目标请求路径 |
| 登录浏览器 | 登录所用浏览器的连接正常，路径符合方案 |
| 相关网络路径 | 所需 DNS、IPv6、UDP / WebRTC 按实际设备检查 |
| 故障回退 | 认可出口失效时按既定方案失败或回退，保持管理连接 |

浏览器能打开网页、单次 IP 查询成功，只说明对应请求通过。CLI、WSL、容器和 SSH 远端要按各自实际运行位置确认。

### 配好后保存一张交接卡

```text
主线路 / 备用方案：
实际出口与测量时间：
本地 HTTP / mixed 端口：
CLI 日常启动方式：
配置、备份、恢复方法和 RUN.md 位置：
```

时区、浏览器语言和其他差异交给 Agent 按实际用途判断，保留需要的中文输入法、字体和工作软件。具体方法见仓库的 [检测流程](../references/detection.md)。

<div class="page-break"></div>

## 03 让 Claude Code CLI 使用代理

**本地代理已启动，不代表 CLI 一定使用了它。** 先让 Agent 确认真实的 HTTP / mixed 监听地址。下面的 `7890` 只是示例，执行前替换为交接卡中的实际端口。

### 先在当前终端接入

Windows PowerShell：

```powershell
$env:HTTPS_PROXY = 'http://127.0.0.1:7890'
$env:HTTP_PROXY = $env:HTTPS_PROXY
claude
```

macOS / Linux：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY="$HTTPS_PROXY"
claude
```

这些变量作用于当前终端及它新启动的子进程。已经运行的 Claude Code 会话不会自动继承之后修改的终端变量；从配置好的终端启动新会话。

### 日常使用时，由 Agent 合并持久配置

独立运行的 CLI 可在用户级 `~/.claude/settings.json` 的 `env` 中配置代理。下面是需要合并的片段，端口仍须换成实际值：

```json
{
  "env": {
    "HTTPS_PROXY": "http://127.0.0.1:7890",
    "HTTP_PROXY": "http://127.0.0.1:7890"
  }
}
```

已有配置保留，由 Agent 合并 `env`。已有代理变量、`NO_PROXY` 或自定义网关时，让它核对生效顺序；小写代理变量可能优先于大写变量。Claude Code 需要 HTTP(S) 入口，不能仅填 SOCKS 地址。

最后在真实 CLI 中发一条简短请求确认可用，并由 Agent 核对连接路径。相关语义见 [官方网络配置](https://code.claude.com/docs/en/network-config)。

<div class="page-break"></div>

## 04 安装 CLI、登录并确认账号

### 第一步：安装官方 Claude Code

已能正常运行 `claude` 时，沿用现有安装。新装用户在对应系统的终端执行：

Windows PowerShell：

```powershell
irm https://claude.ai/install.ps1 | iex
```

macOS / Linux / WSL：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

安装完成后打开新的终端，检查版本。下载失败或提示找不到命令时，把完整报错交给 Agent，按 [官方安装说明](https://code.claude.com/docs/en/setup) 处理网络或 PATH。

```text
claude --version
```

### 第二步：在终端发起官方登录

```text
claude auth login
claude auth status --text
```

按提示在浏览器完成登录，再回到终端。首次直接运行 `claude` 也可触发登录；已登录且账号正确时，可以跳过重新登录。[官方认证说明](https://code.claude.com/docs/en/authentication)

### 第三步：确认计费来源

| 来源 | 应核对的内容 |
|---|---|
| Claude 订阅账号 | 登录的是本人账号，套餐与额度符合分配情况 |
| API / Console | 用量按对应 API 账户计费，查看 Console 账单 |
| 团队或其他接入 | 按组织给出的账号、模型与计费方式使用 |

存在 `ANTHROPIC_API_KEY`、旧网关或其他认证配置时，请 Agent 核对有效认证方式。能发出请求不等于正在消耗订阅额度。登录状态和终端命令见 [CLI 参考](https://code.claude.com/docs/en/cli-reference)。

<div class="page-break"></div>

## 05 每天怎么开始一个任务

**先进入工作目录，再启动 Claude。** 已有项目时，在它的目录中打开终端；初次练习可以建立一个专用目录。

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\work\claude-demo" -Force | Out-Null
Set-Location "$env:USERPROFILE\work\claude-demo"
claude
```

macOS / Linux：

```bash
mkdir -p ~/work/claude-demo
cd ~/work/claude-demo
claude
```

进入后用中文直接提需求。**`cd`、`claude` 在系统终端输入；自然语言和 `/usage` 等斜杠命令在 Claude 输入框里输入。**

### 第一次先认识目录

```text
先查看当前目录，说明项目用途、主要文件和已有运行方式。
只阅读和解释，先不要修改文件；缺少资料时明确告诉我。
```

### 然后交付一个范围明确的小任务

```text
请为当前项目补充一份入门说明，保存为 QUICKSTART.md。
内容包括用途、目录结构、启动方法和一个可操作示例。
以现有文件为依据，无法确认的启动方法列为待补充。
```

Claude 请求文件或命令权限时，核对目标路径和动作是否属于这次任务。完成后打开结果；代码任务查看改动与相关验证结果。后续任务在同一目录继续。

流程示例见 [官方快速入门](https://code.claude.com/docs/en/quickstart) 与 [常用工作流](https://code.claude.com/docs/en/common-workflows)。

<div class="page-break"></div>

## 06 怎样让 Claude 把事情做完整

把**目标、材料、范围、交付文件和完成标准**说清楚。大任务先讨论方案，范围明确后让它执行；常规小任务可以直接交付。

### 修改代码

```text
目标：修复我刚才提供的报错。
请先定位相关代码和触发条件，再做必要修改。
范围：围绕这次问题处理，遵循项目已有约定。
完成后说明改了什么，并运行能验证该问题的检查。
```

### 整理资料或撰写说明

```text
请阅读当前目录下我指定的资料，整理成一份中文说明。
先说明资料覆盖什么，再按主题归纳要点。
输出到 notes/summary.md，保留可追溯的文件或页码信息。
无法读取或没有依据的内容，请列为待补充。
```

### 处理数据

```text
请分析我指定的 CSV，先解释字段、单位和数据范围。
按我给出的目标完成计算，把结果与可复用脚本保存到 results/。
说明缺失数据、使用的假设，以及主要结论对应的计算。
```

### 收到结果后怎么继续

需要调整时直接说明具体差异，例如“保留现有结构，把第三段写得更具体”，或“报错仍在，复现步骤是……”。任务跑偏时打断并重述目标。工具报错时让它解释原因，再针对失败点继续。

较大的代码改动可先用 `/plan` 讨论方案，执行后用 `/diff` 查看变更。任务交付以可打开的文件、实际输出或相关检查为依据。

参考：[任务组织](https://code.claude.com/docs/en/common-workflows)、[提示与上下文实践](https://code.claude.com/docs/en/best-practices)、[命令说明](https://code.claude.com/docs/en/commands)。

<div class="page-break"></div>

## 07 CLI 常用命令速查

### 在系统终端输入

| 命令 | 用途 |
|---|---|
| `claude` | 在当前工作目录开始交互会话 |
| `claude -c` | 继续当前目录最近的会话 |
| `claude -r` | 选择历史会话继续 |
| `claude -p "总结 README.md"` | 执行一次请求并退出，适合简短任务 |
| `claude auth status --text` | 查看登录状态 |
| `claude update` | 手动更新 CLI |

### 在 Claude 会话中输入

| 命令 | 用途 |
|---|---|
| `/help` | 查看帮助；输入 `/` 查看当前可用命令 |
| `/status` | 查看当前会话的配置状态 |
| `/usage` | 查看套餐用量和会话统计 |
| `/model` | 查看并选择当前账号可用的模型 |
| `/plan` | 在较大任务前进入计划模式 |
| `/context` | 查看上下文占用情况 |
| `/compact` | 压缩会话上下文，保留摘要继续 |
| `/clear` | 清空当前会话上下文，开始新任务 |
| `/resume` | 选择并恢复历史会话 |
| `/diff` | 查看当前文件改动 |
| `/permissions` | 查看与调整操作权限 |

**打断与退出：** `Ctrl+C` 可以打断正在执行的操作。空闲时首次按会清空输入，再次按退出。多行输入按当前终端显示的换行提示操作。

命令与可用功能以本机 `/` 菜单为准。来源：[CLI 参考](https://code.claude.com/docs/en/cli-reference)、[会话命令](https://code.claude.com/docs/en/commands)、[交互快捷键](https://code.claude.com/docs/en/interactive-mode)。

<div class="page-break"></div>

## 08 模型、上下文和额度怎么管理

### 模型按任务选择

先使用账号提供的默认模型。需要切换时打开 `/model`：可用的 Sonnet 适合多数日常任务，Opus 用于较复杂的推理任务，Haiku 可用于简单、快速的处理。具体可用模型与名称由账号及接入方式决定。[官方模型配置](https://code.claude.com/docs/en/model-config)

### 同一任务继续，无关任务分开

同一项目、同一目标继续原会话；新的独立目标用 `/clear` 或新会话。对话很长时先用 `/context` 查看占用，必要时用 `/compact` 整理。

```text
请总结当前任务：已完成什么、改了哪些文件、采用了哪些关键决定、
还有哪些未完成事项，以及继续时的第一步。
保存到 notes/handoff.md，供下次会话读取。
```

下次回到原项目目录，用 `claude -c` 继续；有多份任务时用 `claude -r` 选择对应会话。项目交接文件用于跨会话接续，网络配置进度仍保存在 tanuki 的私有 `RUN.md` 中。[会话接续](https://code.claude.com/docs/en/common-workflows)

### `/usage` 中几种数字分别看

| 显示内容 | 应如何理解 |
|---|---|
| 套餐额度条 / 重置时间 | 查看当前账号可用额度，按窗口安排任务 |
| 会话 token | 当前会话处理量，与上下文长度、读入内容等有关 |
| 会话美元估算 | 由用量估算；订阅用户结合套餐及额外用量设置理解 |
| API / 额外用量账单 | 以实际计费账户和官方账单为准 |

先限定相关文件、明确完成标准，避免反复重读大量无关资料。复杂任务拆成有交付结果的阶段。上下文整理用于减少后续负担，套餐额度按服务端窗口恢复。需要额外付费用量时先了解对应预算设置。

来源：[官方用量与费用说明](https://code.claude.com/docs/en/costs)、[上下文实践](https://code.claude.com/docs/en/best-practices)。

<div class="page-break"></div>

## 09 把项目习惯和重复流程留下来

### `CLAUDE.md` 保存项目约定

在项目中用 `/init` 生成起点，再确认实际运行命令和工作习惯。已有文件时保留其内容，补充 Claude 无法仅从代码推断的约定。

```markdown
# 项目约定
- 默认用中文沟通。
- 先阅读 README 和相关目录，再处理当前任务。
- 输出文件放在项目约定的目录，沿用现有命名与格式。
- 代码改动完成后运行能验证该改动的检查。
```

项目约定写入 `CLAUDE.md`；代理凭据、节点订阅等私有内容留在指定的私有配置中。[官方项目记忆说明](https://code.claude.com/docs/en/memory)

### 以后在 CLI 直接调用 tanuki

首次可以把 GitHub 地址直接交给 Agent。需要快捷调用时，让它安装完整 skill：

```text
请将 https://github.com/SanN2Z/tanuki 的完整 skill 安装到
~/.claude/skills/tanuki/，保留 SKILL.md、references、scripts 和 assets。
本次只安装流程，确认安装位置；网络配置按后续请求执行。
```

在新会话中调用：

```text
/tanuki 检测这台个人电脑的 Claude Code 网络环境，先只读定位问题。
```

需要继续配置时，把 Agent 交接的实际 `RUN.md` 路径告诉它；沿用原记录，从未完成位置继续。具备本机执行能力的其他 Agent 也可以直接读取仓库 `SKILL.md`。

skill 保存重复操作流程；`CLAUDE.md` 保存当前项目习惯。安装位置见 [官方 skills 文档](https://code.claude.com/docs/en/skills)，成员接入方式见 [仓库流程](../references/member-onboarding.md)。

<div class="page-break"></div>

## 10 故障处理、维护与账号使用边界

### 按提示分开处理

| 现象 | 先做什么 |
|---|---|
| 安装后找不到 `claude` | 打开新终端，交给 Agent 检查安装结果与 PATH |
| 浏览器能用，CLI 超时 | 查 HTTP(S) 代理、环境继承、执行位置和实际路径 |
| CLI 提示未登录 | 查看 `claude auth status --text`，按官方流程重新登录 |
| 明确提示额度耗尽 | 查看 `/usage` 的窗口和恢复时间，安排继续任务 |
| 403、认证或连接错误 | 保存完整提示，分别检查认证、服务状态和网络 |
| 明确提示账号停用 | 按官方通知和申诉入口处理 |
| 代理退出后无法联网 | 按交接卡检查代理及断线保护，使用预先准备的恢复方法 |

### 把报修信息交给 Agent

```text
请按 https://github.com/SanN2Z/tanuki 排查，先只读定位。
设备、系统、CLI 版本与当前网络：……
开始时间、操作步骤、完整报错：……
其他网页能否访问，代理是否正在运行：……
上次交接或 RUN.md 的本地位置：……
请说明原因、证据、修复办法和当前需要我做的一步。
```

平时保持已验证的线路和设置；按管理员资料登记续费。换设备、换网络或升级客户端后复查受影响的部分。手机、WSL、容器和远端的 Claude 分别验证。

### 网络配置与“防封”的边界

CLI 是日常工作方式，不提供免封能力。固定出口、实际请求验证和断线保护用于减少配置遗漏；第三方检测分数不能代表封号概率。个人账号按本人使用要求管理，多人使用采用各自账号或组织席位，服务地区和使用方式遵守平台规则。

指南与 GitHub 地址可以转发。节点二维码、订阅、密码和账号令牌只交给指定维护者，保留在私有位置。

官方入口：[服务状态](https://status.claude.com/) · [账号申诉](https://support.claude.com/en/articles/8241253-safeguards-warnings-and-appeals) · [账号条款](https://www.anthropic.com/legal/consumer-terms) · [支持地区](https://www.anthropic.com/legal/supported-regions)。
