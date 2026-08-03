---
name: linux-proxy
description: "Install and configure Clash Meta / Mihomo proxy on Linux (Arch/fnOS/Debian) — Bettbox or mihomo-bin, subscription, DNS fix, LAN sharing, systemd, browser & FN-OS Chromium proxy, remote host config, dashboard panel. Use when user asks to set up proxy, share proxy with LAN, fix DNS hijack, or configure proxy on a remote/fnOS host."
platforms: [linux]
---

# Linux 代理配置（Clash Meta / Mihomo，含 fnOS）

在 Linux（Arch / fnOS / Debian）上配置 Clash Meta 代理：安装、订阅、DNS 修复、LAN 共享、systemd 自启、浏览器（含飞牛 Chromium）代理、远程主机、Dashboard 面板。

## 触发条件
- 在 Linux 上设置代理/VPN
- 修复 DNS 劫持（OpenClash fake-ip 等）
- 与局域网设备共享代理（手机/Windows）
- 安装 Bettbox / mihomo / Clash
- 在远程主机 / fnOS 上配置代理

---

## 1. 安装代理客户端

### Option A: Bettbox (GUI, 需 Xfce/GNOME/KDE)
```bash
sudo pacman -S libayatana-appindicator   # 运行时依赖, 必须先装
yay -S bettbox-bin
```
- **Pitfalls**: `libayatana-appindicator` 是 PKGBUILD 构建时检查的运行时依赖；Bettbox 是 Flutter，headless/SSH-only 环境跑不了；BettboxCore 被杀不会自动重启（需 GUI 里 toggle off/on）

### Option B: mihomo-bin (CLI, headless 友好)
```bash
yay -S mihomo-bin
```
配置 `/etc/mihomo/config.yaml`，`sudo systemctl enable --now mihomo`

---

## 2. 配置订阅
**Bettbox GUI**: Settings → Profiles → Add → 粘贴订阅 URL → Update → 开代理
**mihomo-bin**: 订阅 YAML 放 `/etc/mihomo/config.yaml`（或 `~/.config/mihomo/config.yaml`）

---

## 3. 修复 DNS（若被 OpenClash fake-ip 劫持）
```bash
cat /etc/resolv.conf; resolvectl status
nmcli con mod <iface> ipv4.dns "8.8.8.8 223.5.5.5"
nmcli con mod <iface> ipv4.ignore-auto-dns yes
nmcli con down <iface> && sleep 1 && nmcli con up <iface>
```
> DNS 修复不能解锁 Google/Wikipedia（GFW 封锁，非 DNS 封锁），仍需代理。

---

## 4. 静态 IP（可选）
```bash
nmcli con mod <iface> ipv4.method manual \
  ipv4.addresses 192.168.31.x/24 ipv4.gateway 192.168.31.1 ipv4.dns "8.8.8.8 223.5.5.5"
nmcli con down <iface> && nmcli con up <iface>
```

---

## 5. LAN 共享
Bettbox 默认只 `127.0.0.1:7890`，开 LAN：
1. GUI: Settings → Allow LAN access → On
2. 或改 profile YAML `~/.local/share/com.appshub.bettbox/profiles/<id>.yaml` 加 `bind-address: "0.0.0.0"`
3. 重启代理

验证端口监听所有接口：
```bash
ss -tlnp | grep 7890   # 期望 LISTEN ... *:7890
```

### 防火墙 bypass（LAN 仍不通时）
Bettbox profile 若开了防火墙，需放行或加 skip-auth：
```yaml
skip-auth-prefixes: [127.0.0.1/8, '::1/128', 192.168.31.0/24]
```

---

## 6. 验证连通
```bash
curl -x http://127.0.0.1:7890 -s --max-time 10 https://www.google.com -o /dev/null -w "%{http_code}\n"
# 期望 Google→302, Wikipedia→301/200
```

---

## 7. LAN 设备代理
| 设备 | 配置 |
|---|---|
| Windows | 设置 → 网络 → 代理 → 手动 → `host:7890` |
| 浏览器 | SwitchyOmega → 新 profile → `host:7890` |
| iOS 手动 | Wi-Fi → HTTP 代理 → 手动 → `host:7890`（仅尊重系统代理的应用）|
| iOS 最佳 | Stash/Shadowrocket/Sing-box 导入订阅 URL（独立于 Arch，全系统）|

> **iOS 不支持把 HTTP/SOCKS5 代理加为 VPN 配置**（内置 VPN 只支持 IKEv2/IPSec/L2TP）。用代理 App。

---

## 8. 远程主机代理（SSH）
当代理在 Arch、另一台主机（如 FN-NAS/飞牛）要用：
```bash
# 系统级 /etc/environment
ssh user@remote 'printf "%s\n" "http_proxy=http://PROXY_IP:7890" | sudo -S tee -a /etc/environment && \
  printf "%s\n" "https_proxy=http://PROXY_IP:7890" | sudo -S tee -a /etc/environment && \
  printf "%s\n" "no_proxy=localhost,127.0.0.1,192.168.31.*" | sudo -S tee -a /etc/environment'
```
**Pitfalls**:
- 密码含 `*!@$` 会破坏 shell 引号——用 `printf "%s\n" 'password' | sudo -S ...` 而非 `echo`
- `/etc/environment` 由 PAM 在登录时读取；后台服务（Docker/systemd）需单独配
- SSH_ASKPASS: `DISPLAY=:0 SSH_ASKPASS=/path/to/pass-script setsid ssh ...`

---

## 9. 浏览器 / fnOS Chromium 代理
Chrome 在 Linux 常忽略系统代理，必须用命令行参数。
### 标准 Chrome
```bash
google-chrome-stable --proxy-server=http://PROXY_IP:7890 --proxy-bypass-list=localhost;127.0.0.1;192.168.*
```
### 容器化 Chrome（FN-NOS flygo-browser）
设 `$CHROMIUM_EXTRA_ARGS`（app 的 env.sh 优先，`/etc/environment` 对 app center 服务可能不生效）：
```bash
echo 'export CHROMIUM_EXTRA_ARGS="--proxy-server=http://PROXY_IP:7890 --proxy-bypass-list=localhost;127.0.0.1;192.168.*"' | sudo tee -a /path/to/env.sh
```
### 直接改启动脚本
```bash
find /vol*/@appcenter/ -name "start.sh" 2>/dev/null | grep browser
sudo sed -i '/--start-maximized/a\    --proxy-server=http://PROXY_IP:7890' /path/to/start.sh
```
**Pitfalls**:
- ⚠️ **不加尾部反斜杠 `\`**，否则破坏 shell 脚本导致 Chrome 起不来
- 无 `--proxy-bypass-list` 时 Chrome 访问本地服务可能 SSL 挂起 → 黑屏
- App 卷可能属于系统用户（非 root），sudo 可能失败
- 改脚本后从 FN-OS UI 重启 app 生效；部分 app 重启会重生成脚本 → 优先 CHROMIUM_EXTRA_ARGS
- 系统级代理开启后 app center UI 转圈：`no_proxy` 加 `,.local,fnos.local`

---

## 10. systemd 自启
### mihomo 用户服务（推荐，单用户）
```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/mihomo.service << 'EOF'
[Unit]
Description=Mihomo Proxy Daemon
After=network.target
[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -d %h/.config/mihomo
Restart=on-abort
RestartSec=5
LimitNOFILE=65535
[Install]
WantedBy=default.target
EOF
systemctl --user enable --now mihomo
loginctl enable-linger   # headless 无桌面自启
```
### Bettbox autostart（Xfce GUI）
```ini
[Desktop Entry]
Type=Application
Name=Bettbox
Exec=bash -c "sleep 5 && /usr/share/Bettbox/Bettbox"
StartupNotify=false
Terminal=false
X-GNOME-Autostart-enabled=true
```
> 不要用 systemd 管 BettboxCore——它立即退出（需 tray app）。

### 配置迁移（Bettbox → mihomo CLI）
```bash
mihomo -t -d ~/.config/mihomo    # 1. 测试现有配置
pkill Bettbox; pkill BettboxCore; sleep 2   # 2. 停 Bettbox
systemctl --user start mihomo     # 3. 启动 mihomo
curl -s --proxy http://127.0.0.1:7890 -o /dev/null -w "%{http_code}" https://www.google.com  # 4. 验证
rm ~/.config/autostart/Bettbox.desktop  # 5. 移除 Bettbox 自启
```

---

## 11. Hermes 网关代理 env
网关 systemd 服务需要代理 env 连外部 API：
```bash
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
cat > ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf << 'EOF'
[Service]
Environment="http_proxy=http://127.0.0.1:7890"
Environment="https_proxy=http://127.0.0.1:7890"
Environment="no_proxy=localhost,127.0.0.1,192.168.31.*,open.feishu.cn,msg-frontier.feishu.cn,*.feishu.cn,ilinkai.weixin.qq.com,*.weixin.qq.com"
EOF
systemctl --user daemon-reload
```
> **中国服务（飞书/微信）应 bypass 代理**——本地可直连，代理挂时避免连接问题。

---

## 12. Dashboard / 外部控制器（REST API）
mihomo 外部控制器（REST API）可接面板：
```bash
# config.yaml 加
external-controller: 0.0.0.0:9090
# 开 LAN 访问
# 安装 MetaCubeXD 面板 (fnOS app) 或 web 面板连 9090
```

---

## 13. 认证管理
Bettbox profile 可能配了 authentication（LAN 用户要输用户名密码）：
```bash
grep -A2 "authentication" ~/.local/share/com.appshub.bettbox/profiles/*.yaml
```
要 LAN 免认证：加 `skip-auth-prefixes` 或删掉 `authentication` 行，重启代理。

---

## 14. 升级 Bettbox（手动 .deb）
```bash
cd /tmp && ar x ~/Downloads/Bettbox-<ver>-linux-amd64.deb
sudo tar --zstd -xf data.tar.zst
sudo pkill -9 Bettbox; sudo pkill -9 BettboxCore; sleep 2   # 先杀进程
sudo cp /tmp/usr/share/Bettbox/Bettbox /usr/share/Bettbox/Bettbox
sudo cp /tmp/usr/share/Bettbox/BettboxCore /usr/share/Bettbox/BettboxCore
```
> `Text file busy` = BettboxCore 还占着二进制，先杀再拷。

---

## 15. 排障
| 症状 | 原因 | 修复 |
|---|---|---|
| Google 超时, Baidu 正常 | GFW 封锁 | 代理没跑或端口没绑 0.0.0.0 |
| `ss` 显示 `127.0.0.1:7890` | allow-lan 未开 | GUI 开 LAN 或加 `bind-address: "0.0.0.0"` |
| BettboxCore 被杀不重启 | GUI 不自动重启 core | GUI toggle off/on |
| yay 构建成功安装失败 | sudo 弹窗被拦 | `sudo pacman -U <pkg.tar.zst>` 手动装 |
| `Text file busy` | core 锁二进制 | 先 `pkill BettboxCore` 再拷 |
| Python urllib 仍被墙 | Python 未设代理 | curl --proxy 验证, 或代码设 ProxyHandler |
| mihomo 在跑但代理不通 | 节点卡住 | 换节点 / 重启 mihomo |
