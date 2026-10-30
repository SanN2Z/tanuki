function main(config) {
  const name = "Claude-静态家宽";
  const exit = {
    name, type: "socks5",
    server: "替换为家宽地址", port: 1080,
    username: "替换为用户名", password: "替换为密码",
    "dialer-proxy": "替换为现有固定前置节点名"
  };
  config.proxies = (config.proxies || [])
    .filter(proxy => proxy.name !== name).concat(exit);
  const rules = ["anthropic.com", "claude.ai", "claude.com",
    "claudeusercontent.com", "claudemcpcontent.com"]
    .map(domain => `DOMAIN-SUFFIX,${domain},${name}`);
  config.rules = rules.concat((config.rules || [])
    .filter(rule => !rules.includes(rule)));
  return config;
}
