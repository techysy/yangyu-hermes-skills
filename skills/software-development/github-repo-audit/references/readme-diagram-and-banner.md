# README 架构图与徽章去重（GitHub 渲染踩坑）

来源：完善 deepseek-harness-fnos README 时发现的两类问题。

## 1. 含中文的架构图：别用闭合框线 ASCII

**问题**：README 代码块里用闭合框线 ASCII 画架构图（`┌─...─┐` + `│` 竖边框），只要含**中文**，在 GitHub 等宽字体下就会错位破框——中文字符是**双字节宽度**，每行含中文数量不同，导致框的右边界 `┐`/`┘`/`│` 对不齐。

**验证方法**（脚本看每行右边界列）：
```python
import unicodedata
def dw(s):  # CJK 计 2 格
    return sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in s)
# 比较每行的 dw() —— 闭合框要求所有行显示宽度一致，中文多就必然不一致
```

**正确做法**：用**树形前缀连线**，每行只用 `│`/`├─`/`└─` 作为结构线 + 缩进对齐。结构线是纯 ASCII 制表符天然等宽，中文只出现在说明文字里，不破坏对齐：

```text
fnOS（飞牛私有云）
│
├─ 访问入口（三选一）
│  ├─ ① 桌面图标（iframe）
│  │     └─ http://127.0.0.1:28000
│  └─ ② 局域网 / Tailscale
│        └─ http://<NAS_IP>:28000
│
└─ dsh web（0.0.0.0:28000）
   └─ --trusted-host 放行（browser-trust 围栏）
```

**规则**：纯英文/纯 ASCII 用闭合框线没问题；一旦混中文就切树形。

## 2. 顶部徽章（badge）与项目链接去重

README 顶部有徽章条（如 `upstream-v0.1.0`、`fnOS v0.1.0`、`offline` 三个 shields，各自带链接）时：
- **不要**再单独列 `- **上游项目**: [repo](...)` 和 `- **飞牛打包版**: [repo](...)` 两行列表——徽章已携带相同链接 + 版本信息，是冗余。
- 若需保留上游引用，把它**并进简介句**：

```markdown
DeepSeek Harness（dsh）— DeepSeek 官方 agent 框架的浏览器 UI，打包成飞牛 fnOS 应用。
基于上游 [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)（v0.1.0-rc.6）。
```

## 3. 包装项目 README 的双协议

打包/适配上游项目的仓库，README 底部要有：
- 本仓库 LICENSE（打包层，归打包者）
- **上游协议小节**：引用上游仓库 + 照抄其 LICENSE（`gh api repos/<owner>/<repo> --jq '.license'` 确认），并用一句版权归属说明区分"打包层归我 / 上游代码归原作者"。
