# 文档资产与架构图维护

## 架构图 assets/architecture.svg（2026-08-24 新增）

- **形态**：纯内联 SVG，不是 HTML 包装 —— GitHub README 的 `![]()` 直接渲染，无需转 PNG
- **设计系统**：slate-950 (`#020617`) 底 + 40px 网格 pattern、JetBrains Mono、语义配色（hook 注入层 rose `#fb7185` / 核心运行时 emerald `#34d399` / cardkit cyan `#22d3ee` / 外部服务 amber `#fbbf24` / cron 路径橙 `#fb923c`）、双矩形遮罩（先画不透明 `#0f172a` 再画半透明色块）防箭头透底
- **内容**：全链路 Gateway → AST hook 层(14 hooks) → StreamCardController → streaming/ → cardkit/ → 飞书 CardKit v2.0 API → 用户端卡片；cron 推送路径与 CardKit 失败回落虚线单独标注
- **验证闭环（每次改图必做）**：
  ```bash
  rsvg-convert -w 1380 assets/architecture.svg -o /tmp/check.png
  ```
  渲染后做视觉检查：① 文字不溢出方框 ② 箭头起止点正确 ③ 图例位于所有边界框之外
- **README 插入位置**：中英两版均为「核心特性表」之后、「快速安装」之前，小节名 🏗️ 架构总览 / Architecture；alt text 写完整链路描述而非一句概括
- **提交三件套**：svg + README.md + README.en.md 一起 commit

## 同步检查清单

1. 改 SKILL.md（任一拷贝）→ `cp` 同步另一份 → git 提交推送（见 SKILL.md「文档双源同步」节）
2. 改配置默认值 → 同步 `tests/test_config.py` 断言 + `docs/CONFIGURATION.md` + `docs/TROUBLESHOOTING.md`（既有约定）
3. 发 Release 时确认附件包含最新 `hermes-fry-cards-skill.md`
