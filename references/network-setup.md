# 网络接入：已有出口、VPS 与家宽

本文件用于配置模式或已授权的检测后修复。先确定最终出口，再配置传输路径。模板用于独立回环试连，全部从 TUN 关闭开始；只有 B3 通过才激活。中转机向下游提供服务还需执行 roles.md 的接入步骤，不能只交付回环监听。部署、认证和验收信息保存在用户 <work-dir>。

## 已有出口

读取用户指定的私有配置，提取所需节点和既定链路。检查实际协议、客户端内核和运行生成配置；不扫描作者机器上的节点作为备用资源。已有端点有效时直接进入隔离试连。

记录当前规则模式、组选择、全局脚本、配置扩展、最终运行配置和连接链。客户端脚本可能给新节点增加 dialer-proxy 或替换出口，原 YAML 正确并不保证生效结果正确。

## VPS 分支

默认适配用户可管理的日本 Linux/systemd VPS，服务端 sing-box，客户端 Mihomo，VLESS + REALITY + Vision over TCP。其他已有可用协议可以复用，不强制迁移。

1. 通过既有 SSH 别名或用户确认的主机身份连接授权主机。核对系统、架构、时钟、端口、已有服务、资源和防火墙；主机身份不明或没有登录方式时回 B2。ssh-keyscan 的结果需独立确认，不能当成身份验证。
2. 使用 sing-box 当前官方软件源/发行版安装与系统匹配的版本；记录实际版本与来源。已经安装就复用。官网：[安装](https://sing-box.sagernet.org/installation/package-manager/)、[VLESS](https://sing-box.sagernet.org/configuration/inbound/vless/)、[TLS/REALITY](https://sing-box.sagernet.org/configuration/shared/tls/)。
3. 选择空闲 TCP 端口。模板使用 9443，只有实际网络支持时才沿用；若校园网需要已验证可用的 443 且端口空闲，可改成 443，同时更新服务端、客户端、云安全组与主机防火墙。
4. 从该 VPS 测候选 REALITY 握手目标的 TLS、SNI 与证书。例如 openssl s_client -connect <host>:443 -servername <host> -tls1_3 -verify_return_error。目标 hostname 由测试选择，随后必须通过真正的 REALITY 客户端握手。
5. 在私有目录生成新凭据；每个设备使用独立 UUID。保存输出到权限受限文件，避免终端/聊天打印：
   
   ~~~sh
   umask 077
   sing-box generate reality-keypair > reality-keys.private.txt
   sing-box generate uuid > client01-uuid.private.txt
   openssl rand -hex 4 > short-id.private.txt
   ~~~

6. 用 assets/server-reality.template.json 渲染服务端，用 assets/client-reality.template.yaml 渲染客户端。agent 用 JSON/YAML 序列化或正确的字符串转义填写值，不能把含引号的密码直接文本拼接。所有模板占位符都必须替换。
7. 服务端执行 sing-box check -c <server.json>；本机执行 mihomo -t -d <isolated-dir> -f <client.yaml>。通过后才部署。
8. 新服务器上使用 assets/tanuki-exit.service.template 创建独立服务；填实际 sing-box 路径和配置绝对路径。配置可放 /etc/tanuki-exit/server.json，目录 0700、配置 0600，单元放 /etc/systemd/system/tanuki-exit.service。已有同名服务/目录时先确认归属，不覆盖。官方安装包若自带运行服务，先确认监听状态，不另起冲突监听。
9. 在用户已授权的主机和云安全组只增加所需 TCP 入站，保留 SSH 与其他规则。然后 systemctl daemon-reload、systemctl enable --now tanuki-exit；检查 is-active、监听端口和必要的脱敏 journal。仅放行 TCP 外层端口不等于 UDP 功能已验证。
10. 从目标电脑隔离试连。云端部署成功而电脑握手失败时留在 B3，不启动 TUN。

需要停用本次新服务时用 systemctl disable --now tanuki-exit，撤销本次新增入站规则；保留配置与备份以便恢复。更换已有服务配置应恢复其原件并验证，再按授权重载对应服务。共享 VPS 上生成每设备凭据，撤销一个设备只删除对应 UUID，不动其他设备。

## 家宽 / ISP 分支

用户明确选择住宅出口时，它就是最终出口。先确认是供应商的代理服务，还是本人日本家宽上的网关。

**供应商代理：**

1. 读取本次私有 endpoint 文件。核对国家、协议、主机、端口、认证方法、有效期、允许的来源、会话粘性和 UDP 支持。
2. SOCKS5 起步可用 assets/client-residential.template.yaml；HTTP/HTTPS 按供应商实际协议修改。模板 tls:false 表示普通 SOCKS5，不因商品名写“HTTPS”就打开 TLS。仅当端口确实支持且证书验证通过时启用相应 TLS 配置。
3. IP 白名单必须对应实际向住宅端点发起连接的来源。直连是本地网络公网；经 VPS 中转通常是 VPS 公网。先确定连接链，再让用户在后台更新，更新后重试一次。
4. 端点主机的 bootstrap DNS 与应用 DNS 分开。遇到 NXDOMAIN、SERVFAIL、异常固定答案或超时，结合供应商文档和目标网络查询定位；不把某次短 TTL 结果固化为永久 hosts。
5. 直连可用且符合用户第一跳要求时无需 VPS。普通 SOCKS5 第一跳没有加密；若需要加密第一跳，使用供应商实际提供的 TLS 入口，或已授权的加密中转。缺中转资源则回 B2。
6. 服务端拒绝 CONNECT 不能仅凭 TCP 已连接就断定校园网封锁，也不能仅凭一个错误码断定白名单问题。结合授权/到期状态、供应商拒绝信息与协议握手判断。

**自有日本家宽网关：**

已有 WireGuard、Tailscale、OpenVPN 或代理入口时优先复用其官方客户端。在网关所在网络测得 JP 出口后，单独在使用电脑验证。若家宽处于 CGNAT 且没有现成可达入口，明确公网/现有穿透服务这个缺项，交用户开通；不假定路由器端口转发一定有效。

**需要中转时：**

- VPS 是最终出口：电脑 → 可达中转入口 → 用户 VPS → 网站。
- 住宅是最终出口：电脑 → 加密入口/VPS → 日本住宅代理 → 网站。
- Mihomo 的 dialer-proxy 放在最终出口节点上，指向拨号入口；最终出口仍由该节点决定。组只选择本次认可的最终出口，不把中转裸节点或 DIRECT 加入故障回退。
- 实际 HTTP 出口必须吻合最终节点，不能仅看组名。住宅白名单也随此连接链判断。

见官方 [dialer-proxy](https://wiki.metacubex.one/en/config/proxies/dialer-proxy/) 与 [SOCKS](https://wiki.metacubex.one/en/config/proxies/socks/)。

## 模板输入

| 模板 | 必填字段 |
|---|---|
| server-reality.template.json | CLIENT_UUID、REALITY_PRIVATE_KEY、SHORT_ID、HANDSHAKE_HOST；端口与客户端同步 |
| client-reality.template.yaml | VPS_ADDRESS、CLIENT_UUID、REALITY_PUBLIC_KEY、SHORT_ID、HANDSHAKE_HOST、BOOTSTRAP_DNS；核对端口 |
| client-residential.template.yaml | RESIDENTIAL_HOST、RESIDENTIAL_USER、RESIDENTIAL_PASSWORD、BOOTSTRAP_DNS；核对端口、TLS、认证和 UDP |
| tanuki-exit.service.template | SING_BOX_BIN、SERVER_CONFIG，均为该服务器绝对路径 |

BOOTSTRAP_DNS 填当前网络实测可用的解析器 IP；不要把测试实例自己的 DNS 监听地址填作上游。模板固定的 17890 / 11053 只是建议本地端口，使用前查占用并调整；不抢占已有监听。住宅若使用 IP 白名单且没有账号认证，去掉 username/password。

模板客户端开启独立本地 DNS，使用真实地址解析以便验证上游；默认保留 IPv6 查询能力。它们没有接管系统解析器，因此“本地 DNS 监听通过”不是“整机 DNS 已接管”。后续按校园网需求调整，不为各平台重复复制整份配置。

## 隔离试连与失败定位

1. 实际内核解析全部渲染文件。独立数据目录，TUN 关闭、controller 关闭、只监听回环；进程启动记录 PID。Windows Start-Process 使用隐藏窗口。
2. 若已有 TUN，查看代理端点的实际路由；必要时给隔离节点指定已确认的出站接口以测目标物理网络。没有这一证据时标为“经现有网络路径测试”，不能宣称裸机直连已验收。
3. 通过新回环端口访问两家 IP 服务。用 curl.exe/curl --proxy http://127.0.0.1:<port> --noproxy "" --max-time 10 <URL> 只对这个受控代理测试排除 NO_PROXY 干扰；没有修改全局变量或强制公网直连。国家不一致时保留各来源。
4. 向 127.0.0.1:<dns-port> 发送实际 DNS 查询，Windows 可用 nslookup -port=<dns-port> <域名> 127.0.0.1，macOS/Linux 可用 dig @127.0.0.1 -p <dns-port> <域名>。目标域名还要通过代理成功进行证书验证的 HTTPS；fake-IP 或缓存答案不能单独证明上游正常。
5. 从目标应用或受控工具验证需要的 UDP/WebRTC。HTTP 查询通过不能证明 UDP 或 IPv6，未用到的项目注明不适用。
6. 出口组应在最终出口不可达时失败。可在隔离配置副本中把本次最终出口端口改为已确认无监听的端口，检查默认/受保护请求失败、无 DIRECT 成功；只停止自己创建的测试进程，保留工作中的代理。
7. 原配置正常试连与失效配置分别记录。销毁自己创建的实例前保存脱敏证据，清理 PID，进入 B4。

按失败层停止：

| 证据 | 下一步 |
|---|---|
| DNS 名称无法解析 | 查 bootstrap、认证门户、实际 DNS 路径 |
| TCP 超时/拒绝 | 查端口、监听、两层防火墙、目标网络可达性 |
| TCP 通但 REALITY/TLS 失败 | 核对 UUID、公钥/短 ID、SNI、flow、时钟和两端版本；只比较私有值，不回显 |
| 代理认证/CONNECT 被拒绝 | 查账号状态、白名单与服务商协议支持 |
| 代理连通但 HTTP 不是预期出口 | 查 dialer-proxy 方向、脚本重写、组选择与实际连接链 |
| HTTP 正常但 DNS/UDP 失败 | 分别测对应协议，修正该路径，不用全局 DIRECT 掩盖 |

同一配置在另一网络可用只提供对照，不能直接证明校园路径的具体拦截机制。完成一轮针对性定位后，有明确改动再复测；无新条件则保存阻塞和下一步。
