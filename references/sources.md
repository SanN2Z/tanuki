# 来源与证据边界

查阅日期：2026-10-21。涉及当前客户端和代理软件语义时，对照正在使用的版本。

## 参考项目

[LinXiaoTao/FuckClaude](https://github.com/LinXiaoTao/FuckClaude) 的 [signals.ts](https://github.com/LinXiaoTao/FuckClaude/blob/master/src/config/signals.ts) 提供时区、语言、字体、设备、Intl 和 WebRTC 的候选检测思路。其评分属于该项目自定义的评估方式，不代表 Anthropic 官方规则。本技能独立实现采集，没有复制上游代码、评分或素材。

上游 README 的日期/Unicode 标记叙述属于特定版本逆向报告。没有当前版本直接证据时，不用于断言本机行为。浏览器扫描不能替代原生客户端或远端网络测量。

## 官方与标准资料

- [Claude Code 网络配置](https://code.claude.com/docs/en/network-config)：HTTP(S) 代理、变量优先级、SOCKS 支持与证书配置；不自动外推到 Desktop 全部连接。
- [Mihomo TUN](https://wiki.metacubex.one/en/config/inbound/tun/) 与 [DNS](https://wiki.metacubex.one/en/config/dns/)：路由、接管与上游解析，配置值需与运行状态结合。
- [MDN navigator.languages](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/languages) 与 [Accept-Language](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Language)：JS 语言列表与实际 HTTP 头分别取证。
- [Chrome UA-CH](https://developer.chrome.com/docs/privacy-security/user-agent-client-hints) 与 [高熵信息 API](https://developer.mozilla.org/en-US/docs/Web/API/NavigatorUAData/getHighEntropyValues)：传统 UA 之外还有独立接口，支持和权限有差异。
- [MDN ICE 类型](https://developer.mozilla.org/en-US/docs/Web/API/RTCIceCandidate/type)：host、srflx、prflx、relay 需结合路径解释。
- [MDN 地理定位](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)：安全上下文与授权约束；定位与时区是不同信号。
- [Khronos WebGL renderer 扩展](https://registry.khronos.org/webgl/extensions/WEBGL_debug_renderer_info/)：图形信息接口，字段用于描述运行环境。
- [W3C 浏览器指纹指引](https://www.w3.org/TR/fingerprinting-guidance/)：可关联浏览器特征与测量边界，不是地区概率模型。
- [Microsoft 用户语言列表](https://learn.microsoft.com/en-us/powershell/module/international/set-winuserlanguagelist)：修改会涉及输入法等设置，不能为检测替换整份列表。
- [ipapi 开发说明](https://ipapi.co/developers/) 与 [IPinfo API](https://ipinfo.io/developers/core-api)：IP 数据库观测；字段和匿名调用可用性会变化，失败保留未验证。

- [Microsoft 地区 ID](https://learn.microsoft.com/en-us/windows/win32/intl/table-of-geographical-locations)：Japan 的 GeoID 为 122。
- [ipify 官方说明](https://www.ipify.org/)：IPv4 与 IPv6 专用查询接口。
- [RFC 7239](https://www.rfc-editor.org/info/rfc7239/)：代理转发的原始连接信息可能通过 Forwarded 暴露，是否出现需要实际请求证据。
- [IANA IPv4 特殊用途地址](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml)：198.18.0.0/15 是非公网基准测试范围，不当作公网 ICE 地址。

## 证据用语

“已测得”需当前上下文直接输出；“配置为”指文件或设置值；“可能”用于尚待实测的路径差异。节点名称、厂商品牌、字体和语言不能独立证明所在地。

## 裸机网络流程的参考

下面是设计来源，接收者运行时无需这些本地项目：

- c-pool 的 MAC_GATEWAY_VPS_PLAN_20261021.md、MAC_GATEWAY_VPS_REPORT_20261021.md：将服务部署、配置解析、目标设备实际握手和正式接管分开验收。
- c-pool 的 MAC_NETWORK_DIAG_BRIEF_20261021.md、MAC_FRP_UU_REPORT_20261021.md：管理链路的内核路由、TUN 排除、按实际进程/域名分流，以及持久配置验证。
- owned-vps-egress-kit 的 deployment / verification 说明：本人资源、每设备凭据、独立端口试连和出口失效验证。
- residential-exit-setup：供应商认证、来源白名单、端点 bootstrap DNS、住宅最终出口与第一跳传输的区分。

通用流程和模板保存在本技能内，未包含上述项目的服务器、个人路径、账号、订阅或运行配置。模板与资料按当前实际内核复核，不继承具体校园、机器或供应商的固定参数。

新增官方来源：

- [sing-box 安装](https://sing-box.sagernet.org/installation/package-manager/)、[VLESS 入站](https://sing-box.sagernet.org/configuration/inbound/vless/)、[TLS/REALITY](https://sing-box.sagernet.org/configuration/shared/tls/) 与 [路由规则](https://sing-box.sagernet.org/configuration/route/rule/)：服务端模板与部署接口。
- [Mihomo VLESS](https://wiki.metacubex.one/en/config/proxies/vless/)、[SOCKS](https://wiki.metacubex.one/en/config/proxies/socks/) 与 [dialer-proxy](https://wiki.metacubex.one/en/config/proxies/dialer-proxy/)：客户端协议和连接链方向。
- [Clash Verge Rev 官方发行](https://github.com/clash-verge-rev/clash-verge-rev/releases) 与 [Mihomo 官方发行](https://github.com/MetaCubeX/mihomo/releases)：按当前平台与内核版本选包。
- [Python 官方下载](https://www.python.org/downloads/)：可选批量采集工具的运行环境。
- [Microsoft nslookup 端口](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/nslookup-set-port)：查询独立测试 DNS 监听。

- [Mihomo 通用配置](https://wiki.metacubex.one/en/config/general/)：下游接入的绑定地址、允许范围与代理认证。
- [Apple launchd](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)：系统守护任务与登录用户任务的生命周期。
