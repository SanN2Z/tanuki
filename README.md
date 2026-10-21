# tanuki · 伪装小日本

供本机 agent 使用的日本环境配置与检测流程。先询问设备用途和任务模式，再选择对应步骤。

| 用途 | 从零配置 | 检测现有环境 |
|---|---|---|
| 个人电脑 | 出口接入、实际应用代理、地区/浏览器配置、验收 | 查应用旁路、DNS/IPv6/UDP/WebRTC、进程继承与地区信息差异 |
| 中转机 / Mac mini | 管理入口、内网、下游代理或转发、常驻服务、端到端验收 | 分别查管理链、下游转发、机上应用及故障回退 |

中转机还会确认：只做 SSH/frp 跳板、给其他设备提供上网出口，还是自己运行 Claude/浏览器。兼用设备分别检查，纯转发机不套用个人桌面的语言和时区要求。

## 安装与调用

下载 [dist/tanuki.zip](dist/tanuki.zip)，解压后将整个 tanuki 目录放到：

- Codex：~/.codex/skills/
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

## 工作流文件

- [用途与中转机流程](references/roles.md)
- [检测流程](references/detection.md)
- [裸机启动与暂停续接](references/bootstrap.md)
- [VPS / 家宽接入](references/network-setup.md)
- [校园网与管理连接](references/campus.md)
- [检测面](references/surfaces.md)、[平台操作](references/platforms.md)、[验收](references/acceptance.md)

包内提供配置模板、Python 只读采集器和无界面的浏览器探针。节点、账号、运行报告、备份和下载工具均保留在使用者本机，不属于技能分发包。

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
