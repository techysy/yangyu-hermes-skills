---
name: readme-structure
description: "开源项目 README 结构规范 — 主版中文 + README.en.md 英文版，按读者分层，排障拆独立文档，用户价值优先。Use when writing, restructuring, or reviewing a README for any open-source project (GitHub repo)."
version: 1.0.0
platforms: [linux, macos]
---

# 开源项目 README 结构规范

> 用户对公开开源仓库 README 有清晰的结构偏好。教训来源：重构 9router-fnos README 时被纠正"现在感觉什么都有什么都不清晰"。

## 触发条件

- 写/重写/审查任何开源项目的 README
- 中英双语文档的组织
- 排障/踩坑内容从主文档拆分

## 核心规则

### 1. 中英分离（不是逐段重复）

**主 README 用中文**，另建 `README.en.md` 英文版（像海外项目的 `zh` 版本反过来）。

```markdown
<!-- README.md 顶部放语言切换链接 -->
- [English README](./README.en.md)

<!-- README.en.md 顶部同理链回 -->
- [中文 README](./README.md)
```

**否决的方案**：
- ❌ 中英每段各写一遍（冗长、抓不住重点）
- ❌ 纯中文 + 英文标注

### 2. 按读者分层，主线清晰

主 README 只服务"安装者"，一条主线：

```
这是什么 → 功能亮点 → 快速安装 → 使用说明 → 本项目增强 → 从源码构建 → License
```

不要混入：运维排障、开发者踩坑、历史修复记录。

### 3. 排障拆到独立文档

README 里只放一行指针：

```markdown
## 🐛 问题排查
构建/安装/运行的常见问题与修复，见 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。
```

详细排障步骤收敛到 `TROUBLESHOOTING.md`（呼应"排障独立模块"偏好）。

### 4. 用户价值优先

- **功能亮点**用表格/要点展示用户关心的核心价值（"一个端点连所有 AI""自动 fallback"），不堆技术细节
- 先讲"能做什么"，再讲"怎么用"

### 5. 中英不重复

同一内容只写一次，不中英各写一段。

### 6. 保留可执行命令而非解释

安装/构建步骤直接给命令（含必要的 PATH export 注释），符合用户"一条命令 + 注释"偏好。

## 反面实例（教训）

9router-fnos README 原问题：
- 中英逐段重复 → 冗长
- Cloudflare 修复大段排障混进主 README → 普通用户被开发者内容淹没
- 踩坑记录（cp -r 漏 .next-cli-build）混排 → 目标读者不清

重构后主 README 一条主线（是什么→怎么装→怎么用→有什么增强），排障收敛到 TROUBLESHOOTING.md。

## 验证清单

- [ ] 主 README 是中文，含语言切换链接到 README.en.md
- [ ] README.en.md 英文版存在，链回中文
- [ ] 章节顺序：是什么 → 功能亮点 → 快速安装 → 使用说明 → 本项目增强 → 构建 → License
- [ ] 排障内容不在主 README，只留指向 TROUBLESHOOTING.md 的指针
- [ ] 功能亮点用表格/要点，用户价值优先
- [ ] 安装/构建给可执行命令，不中英重复
