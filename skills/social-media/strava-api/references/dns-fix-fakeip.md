# DNS 修复：绕过 OpenClash fake-ip

当 OpenClash 旁路由下线后，本机 DNS 被劫持到 fake-ip 导致 HTTPS 全部失败。
通过 NetworkManager 直接指定 DNS 修复：

```bash
nmcli con mod enp4s0 ipv4.dns "8.8.8.8 223.5.5.5"
nmcli con mod enp4s0 ipv4.ignore-auto-dns yes
nmcli con down enp4s0 && sleep 1 && nmcli con up enp4s0
```

## 各服务直连状态

| 服务 | 状态 |
|------|:----:|
| Strava API | ✅ 直连可用（Cloudflare CDN） |
| GitHub | ✅ 直连可用 |
| Open-Meteo | ✅ 直连可用 |
| 百度/必应 | ✅ 正常 |
| Wikipedia/Google/DuckDuckGo | ❌ 被墙，仍需代理 |
