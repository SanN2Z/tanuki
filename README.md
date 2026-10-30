# tanuki · 网络环境配置与检测

成员将统一 Prompt 和家宽截图或文本交给本机 Codex，由 tanuki 连续完成环境、Clash 链式代理、浏览器、CLI、防火墙与防泄漏配置和交接。目标国家按分配的家宽资源确定。

## 给成员的入口

1. 管理员通过微信发送 [统一配置 Prompt](docs/member-setup-prompt.txt)，同时附上分配给该成员的家宽截图或文本。
2. 成员将二者交给本机 Codex。Codex 获取仓库、安装完整 skill，读取 [SKILL.md](SKILL.md)，执行 [成员完整配置 SOP](references/member-full-setup.md)。
3. 日常使用阅读 [Claude 使用指南](docs/training-guide.md)，或转发 [PDF](docs/training-guide.pdf)。完成配置后按本机 `START-HERE.md` 启动，按 `RUN.md` 续接和恢复。

已有配置先检测并修复，没有配置再从零准备。成员提供管理员分配的节点文件，并在需要时完成登录、系统授权等交互；Agent 负责具体命令、配置、验证与交接。完成后保留主线路、实际出口、日常启动方式和续接位置。

推荐网络是 **各自已有梯子 → 静态家宽 IP → Claude / Anthropic**：在 Clash Verge 的「订阅 → 全局扩展脚本」中配置家宽节点，以 `dialer-proxy` 指向现有前置节点，并将相关域名分流至家宽。其他网站保留原规则。配置见 [链式代理流程](references/clash-chain.md) 和 [脚本模板](assets/clash-verge-claude-chain.js)。

完整流程由仓库维护，后续复查仍使用同一个入口。具备本机文件与终端能力即可开始，无需成员先手动安装 skill 或准备开发工具。

## 适用场景

| 用途 | 从零配置 | 检测现有环境 |
|---|---|---|
| 个人电脑 | 出口接入、实际应用代理、地区/浏览器配置、验收 | 查应用旁路、DNS/IPv6/UDP/WebRTC、进程继承与地区信息差异 |
| 中转机 / Mac mini | 管理入口、内网、下游代理或转发、常驻服务、端到端验收 | 分别查管理链、下游转发、机上应用及故障回退 |

中转机还会确认：只做 SSH/frp 跳板、给其他设备提供上网出口，还是自己运行 Claude/浏览器。兼用设备分别检查，纯转发机不套用个人桌面的语言和时区要求。

## 可选：安装为 skill

下载 [dist/tanuki.zip](dist/tanuki.zip)，解压后将整个 tanuki 目录放到：

- Codex：~/.agents/skills/
- Claude Code：~/.claude/skills/

在新会话调用 $tanuki 或 /tanuki。其他具备本机终端能力的 agent 可直接读取 [SKILL.md](SKILL.md)。

~~~text
$tanuki
$tanuki 检测这台个人电脑，找出可能的泄露和配置遗漏。
$tanuki 从零配置这台 Mac mini 中转机。
$tanuki 检测并修复，先按实际用途确定检查范围。
~~~

未提供的用途和模式会先询问；已经说明的不会重复问。没有 Python 时先用系统原生命令，不要求预装 Git、Docker 或浏览器 MCP。

## 两种模式

**从零配置：** 盘点 → 选择资源 → 开通 → 隔离试连 → 正式接入 → 修复 → 验收。已有可用出口优先复用。VPS、住宅代理和加密中转按需要选择；购买、白名单、校园认证或系统交互交给用户完成。

**检测：** 默认只读取配置、运行状态和必要的实际连接证据，找出原先未注意到的泄露、旁路与地区信息差异。报告区分已证实问题、有依据的疑点、符合预期和未验证项。明确要求“检测并修复”后，修复有证据的项目。

人工步骤保存到私有工作目录的 RUN.md，补齐条件后继续：

~~~text
$tanuki 继续 <work-dir>/RUN.md
~~~

## Agent 工作流

- [培训入口与成员交接](references/member-onboarding.md)
- [成员完整配置 SOP](references/member-full-setup.md)
- [Clash 全局扩展脚本与静态家宽链式代理](references/clash-chain.md)
- [Claude 应用接入与故障分流](references/claude-usage.md)
- [用途与中转机流程](references/roles.md)
- [检测流程](references/detection.md)
- [裸机启动与暂停续接](references/bootstrap.md)
- [VPS / 家宽接入](references/network-setup.md)
- [校园网与管理连接](references/campus.md)
- [检测面](references/surfaces.md)、[平台操作](references/platforms.md)、[验收](references/acceptance.md)

包内提供配置模板、Python 只读采集器和无界面的浏览器探针。节点、账号、运行报告、备份和下载工具均保留在使用者本机，不属于技能分发包。

采集器默认检查 JP；成员资源为其他国家时传入 `--target-country US` 等实际国家代码。需要核对具体时区时，再传入本机系统格式的 `--target-timezone`。Codex 的个人安装目录见 [官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)。

macOS + Clash/Mihomo TUN 的完整 SOP 可按适用条件接入 [Valdemar-Yu/killswitch](https://github.com/Valdemar-Yu/killswitch) 整机断线保护，安装和恢复沿用原项目说明。

## 验证

采集器测试：

~~~text
python tests/test_collector.py
~~~

使用本机实际内核解析合成模板，不启动代理或修改网络：

~~~text
python tests/check_templates.py --mihomo <mihomo路径> --sing-box <sing-box路径> --output-dir <私有测试目录>
~~~

模板解析通过不能代替目标电脑、真实下游和当前线路的验收。来源和测量边界见 [sources.md](references/sources.md)。

## 更新培训指南

编辑 `docs/training-guide.md`，然后生成 HTML 和 PDF：

~~~text
python -m pip install -r docs/requirements.txt
python docs/build_training_guide.py --pdf
~~~

文档构建需要 Playwright Chromium；已有浏览器可通过 `--browser <可执行文件路径>` 指定。缺少浏览器时运行 `python -m playwright install chromium`。这些依赖仅用于维护培训材料，执行 tanuki 流程无需安装。
