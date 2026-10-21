# 平台采集与调整

先按 SKILL.md 确认用途与模式。检测模式只执行采集与查询；配置或已授权的检测后修复才执行调整。地区和浏览器设置只作用于实际运行目标应用的上下文，纯转发机不套用个人桌面目标。修改前记录原值与恢复方法，路径与端口以实测为准。

## Windows

使用 -NoProfile 避免提示符插件干扰，同时注明它可能与交互终端的代理环境不同。

~~~powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Get-TimeZone
Get-Culture
Get-UICulture
Get-WinHomeLocation
Get-WinUserLanguageList
Get-ItemProperty 'HKCU:/Software/Microsoft/Windows/CurrentVersion/Internet Settings' |
    Select-Object ProxyEnable,ProxyServer,AutoConfigURL
netsh winhttp show proxy
Get-NetRoute -DestinationPrefix '0.0.0.0/0'
Get-NetRoute -DestinationPrefix '::/0'
Get-DnsClientServerAddress
~~~

权限不足时可用 route.exe print、netsh interface ipv4 show dnsservers、netsh interface ipv6 show dnsservers 取证，或通过系统/代理软件界面查看。WinHTTP、系统代理、环境代理和 TUN 是不同层。

已授权的日本地区设置：

~~~powershell
Set-TimeZone -Id 'Tokyo Standard Time'
Set-Culture -CultureInfo 'ja-JP'
Set-WinHomeLocation -GeoId 122
~~~

这些命令不改变网络出口。语言列表和输入法在“时间和语言”中调整，保留必要输入法。UI 语言、非 Unicode 区域设置可能涉及组件安装和重启，不自动修改。

常见代理运行配置：

~~~text
%APPDATA%/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
%APPDATA%/io.github.clash-verge-rev.clash-verge-rev/verge.yaml
%USERPROFILE%/.config/mihomo/config.yaml
%USERPROFILE%/.config/clash/config.yaml
~~~

仅读取必要的 TUN、DNS、规则和策略组片段，隐藏 secret、订阅 URL、密码、私钥。优先从软件界面确认运行配置和连接链，不能假定 config.yaml 总是最终配置。

## macOS

~~~sh
date '+%Z %z'
readlink /etc/localtime
defaults read -g AppleLocale
defaults read -g AppleLanguages
scutil --proxy
scutil --dns
route -n get default
netstat -rn -f inet6
~~~

地区与时区通过系统设置调整。只改浏览器时无需改全系统 UI；既有进程在适当时机重新启动后取证。不因检测而提权修改 VPN 或网络扩展。

## Linux、WSL、容器

~~~sh
date '+%Z %z'
readlink /etc/localtime
locale
timedatectl status
ip -4 route show default
ip -6 route show default
resolvectl status
cat /etc/resolv.conf
~~~

部分容器没有 systemd、ip 或 resolvectl，使用已有配置与应用实测，不安装整套服务。TZ=Asia/Tokyo 和 LANG=ja_JP.UTF-8 仅对继承变量且支持它的进程生效；对应 locale 必须实际存在。Docker daemon、WSL 与 SSH 远端分别核对。

## 浏览器与请求

1. 在平常的浏览器配置执行 scripts/browser_probe.js，需要日文优先时调整浏览器语言顺序，再看实际 Accept-Language。
2. 通过实际站点 Network 面板看必要请求头、远程地址和协议，不导出含会话的 HAR。
3. 对照 WebRTC 公网候选与 HTTP 出口。发现未代理 UDP 后检查 TUN 覆盖或现有 WebRTC 隐私策略，重测并说明可能影响通话。
4. 站点定位权限单独核对；探针默认不请求坐标。
5. 新测试配置可用 --user-data-dir 隔离，但不代表原配置。--lang 不能单独证明请求头、JS locale 和时区一致。

## 网络实测补充

通过实际路径各测一次：

~~~text
curl --max-time 8 https://ipapi.co/json/
curl --max-time 8 https://ipinfo.io/json
curl --max-time 8 https://api.ipify.org?format=json
curl --max-time 8 https://api6.ipify.org?format=json
~~~

Windows 使用 curl.exe 避免 PowerShell 别名。前两项用于国家/ASN 交叉证据，后两项用于地址族专用出口；HTTP 代理客户端的地址族与代理出站应分开描述。

不要为对照清空全部代理变量或关闭 VPN。无代理变量仍可能经过 TUN；强制直连会影响活跃连接。失效回退通过现有日志或已授权维护测试确认。

Claude 目标域名以当前官方说明和实际连接为准，单个检测网站不能证明应用全部连接路径。

## 首次接入实际应用

先按 network-setup.md 完成独立端口试连，再选择覆盖方式。客户端启动程序、服务助手和实际内核路径分别记录。

### 仅指定 CLI / 应用

把实际本地 HTTP 代理端口传给新启动的目标进程，不先覆盖整机变量。PowerShell 示例：

~~~powershell
$env:HTTPS_PROXY = 'http://127.0.0.1:<实际端口>'
$env:HTTP_PROXY = $env:HTTPS_PROXY
~~~

POSIX shell 可对单次启动设置 HTTP_PROXY/HTTPS_PROXY。先保存原值，检查 NO_PROXY、大写/小写变量和程序自己的配置；Claude Code 的 HTTP 代理入口可连接 Mihomo mixed-port，即使 Mihomo 上游是 SOCKS5，也不是让 Claude 直接使用 SOCKS。

用户需要持续使用时，再写入该应用支持的启动环境；IDE 从旧父进程启动可能保留旧变量，需要按实际进程继承验证。运行中的登录会话不为试验批量退出。

### 桌面系统代理

Windows/macOS 的代理客户端通过其支持的系统代理选项接入；Linux 桌面使用其桌面环境的网络代理设置。先记录旧值，导入本次私有配置并读取最终生成配置，再在已授权范围内切换。

系统代理通常覆盖遵循代理设置的应用；用连接证据确认浏览器/CLI/Desktop，各应用不必同时采用相同接入方式。不支持的应用转入 TUN 或应用单独配置。

### 全机 TUN

在通过试连的配置副本上启用 TUN，使用当前 [Mihomo TUN 文档](https://wiki.metacubex.one/en/config/inbound/tun/) 和实际平台能力：

1. 确认需要覆盖的 IPv4/IPv6、UDP 和应用范围；填写 enable、stack、auto-route、auto-detect-interface 及所需 DNS hijack。macOS 设备名按内核要求用空闲 utun 名称，Windows/Linux 按本机可用名称；不要照抄作者接口。
2. 按 campus.md 加入实际必要的管理/内网排除，核对 strict-route 对当前平台和既有网络的影响。代理端点的底层拨号必须独立可达。
3. IPv6 的 DNS 回答、TUN 地址/捕获路由、上游出口是三个条件。需要全机 IPv6 覆盖时逐一建立证据；ipv6:true 或 dns.ipv6:false 都不能单独证明已接管。上游确实不支持时，把可行的范围或受限影响交用户判断，不静默全局禁用。
4. 开启劫持前核对 DNS listen 已生效；启用后测试系统解析、代理上游与校园例外。应用 DoH 不一定经过端口 53。
5. 桌面使用现有客户端的服务模式/网络权限；无桌面 Linux 使用为本次配置准备的 systemd 服务。macOS 专用常驻网关仅在用户需要时建立 LaunchDaemon，普通桌面无需迁移成守护进程。
6. 对需要交互的系统权限给出真实弹窗/操作位置。配置助手批准、TUN 建立与业务验证分别记录，不把“已授予权限”当作出口验收。
7. 激活后核对实际默认路由、目标连接和管理连接；保存到能跨应用重载保持的配置层。重启验收只在可中断时执行。

Windows 用 route print / Get-NetRoute；macOS 用 route -n get <目标地址>；Linux 用 ip route get <目标地址> 与相应 IPv6 命令。实际连接日志比全局开关更能证明应用走向。
