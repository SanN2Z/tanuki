# Clash Verge：现有梯子连接静态家宽

用于个人电脑的 Claude Code 与登录浏览器。推荐链路：应用 → 本机 Clash → 用户现有梯子前置节点 → 静态家宽 → Claude / Anthropic。其他业务保留原订阅规则。复用已有线路，使用 Clash Verge 的全局扩展脚本与 Mihomo 的 `dialer-proxy`。

## 资源与来源

从获授权的本地文件读取家宽协议、地址、端口、认证与到期信息；核对现有订阅、前置节点、规则模式、全局扩展脚本及最终生成配置。家宽尚未分配时按 B2 续接。需要自购时可给出 [米芽静态代理入口](https://miyaip.com/dashboard/staticProxy)，是否购买及套餐由使用者决定。

部分产品最多同时连接 2 台设备；计数与释放规则由供应商确认。校园网可能切换公网来源 IP；采用链式代理后，供应商通常看到前置节点的公网 IP。切换前置或自动选路同样可能改变来源，旧来源未释放时可能占用名额。白名单应填写实际到达家宽端点的来源，不能直接抄校园公网 IP。保持一个稳定前置节点，并依据供应商规则处理切换。

## 合并到全局扩展脚本

1. 使用当前通用订阅，打开「订阅 → 全局扩展脚本（Script）」。读取并备份已有脚本；将 [脚本模板](../assets/clash-verge-claude-chain.js) 的逻辑合并到现有 `main(config)`，返回合并后的对象。已有复杂脚本时保留其功能，按最终配置消解覆盖关系。
2. 示例为 SOCKS5。填写真实服务器、端口与认证；HTTP / HTTPS 按供应商实际协议及 TLS 能力修改。IP 白名单认证时去掉 `username` 和 `password`。凭据只写入本次私有配置。
3. `dialer-proxy` 写在家宽节点上，值是已存在的前置节点或代理组的准确名称。推荐现有的固定前置节点；若选组，确认成员不包含家宽节点或指回它的组。家宽是最终出口，前置只负责连接家宽端点。
4. 将 `anthropic.com`、`claude.ai`、`claude.com`、`claudeusercontent.com`、`claudemcpcontent.com` 的 `DOMAIN-SUFFIX` 规则放在原有宽泛规则之前，目标为家宽节点。覆盖核心 API、登录与所需内容域名；GitHub、npm、WebFetch 目标及其他第三方请求沿用原规则，必要时按实际业务补充。
5. 全局脚本会应用于不同订阅，切换订阅后前置名称仍须有效；需按订阅区分时使用 `main(config, profileName)`。保留原订阅节点、代理组、DNS 与无关分流。规则模式才能按这些规则选择出口；全局脚本的「全局」不是运行模式。

## 验证与接入

先在私有候选配置中合并并由实际 Mihomo 内核解析。离线解析不发请求。需要网络试连时，沿用 B3 的独立目录、空闲回环端口和关闭 TUN 的隔离实例；只使用用户提供的资源，不改活动客户端，不终止或重启现有 Clash Verge / Mihomo。

对真实 Claude API 和登录请求，核对最终配置中的规则顺序、命中规则与包含家宽及前置的实际连接链。出口 IP 可在隔离候选中增加临时精确查询域名规则，强制走家宽节点再查询，完成后撤掉这条测试规则。普通查 IP 网站按原规则可能走前置，不能用它的结果断言 Claude 的最终出口。代理节点的延迟测试成功也不能替代目标请求。

按本次授权应用已验证的脚本，沿用客户端支持的保存/应用方式；保留原件及恢复方法。已有订阅级扩展可能覆盖全局脚本结果，订阅更新与切换后核对最终配置。CLAUDE CLI 接入本机 HTTP / mixed 端口，不能把远端家宽的 SOCKS5 地址直接填进 `HTTPS_PROXY`。完成一条实际 CLI 请求和登录浏览器路径验证，再交接前置节点、家宽出口、监听端口、时间、私有脚本及 `RUN.md` 位置。

家宽不可用时目标业务连接失败；不要在家宽策略里加入 `DIRECT` 或普通前置作为自动回退。校园认证和现有管理连接按原方案保留。

## 官方依据

- [Mihomo dialer-proxy](https://wiki.metacubex.one/config/proxies/dialer-proxy/)：家宽节点通过所选前置建立连接。
- [Clash Verge 全局扩展脚本](https://www.clashverge.dev/guide/script.html)：`main(config)`、`profileName` 和规则前置合并。
- [Claude Code 网络配置](https://code.claude.com/docs/en/network-config)：HTTP(S) 代理入口，以及 API、认证和内容域名的用途。
