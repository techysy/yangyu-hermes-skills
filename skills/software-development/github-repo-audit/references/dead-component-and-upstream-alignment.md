# 死组件检测与上游对齐修复（2026-08-25 10router 实战）

## 场景

用户报告"使用详情的拓扑图没有了，数据异常"。排查发现 `ProviderTopology.js` 组件文件完好（487 行），但整个 `src/` 无任何文件 import 它——死组件。

根因：此前 git-filter-repo 历史重写（commit 17a41142 "restore runtime files lost in history rewrite"）从备份快照恢复了组件文件，但把它挂进页面的父级 wiring（import + JSX 标签）没有恢复。文件在、渲染链断。

## 检测方法

```bash
# 对疑似组件查全库引用（排除定义处自身）
grep -rn "import.*ComponentName" src/ --include="*.js"
# 结果只有定义文件自己 = 死组件
```

适用信号：历史重写、git-filter-repo、从备份恢复文件的仓库；用户报"某功能消失"但对应文件存在。

## 修复教训：方向不要自创，对齐上游

首次修复自创了数据源——用 `stats.byModel`（历史用过的模型统计）构造拓扑节点。审查时发现与上游设计不符：

| 维度 | 自创方案（错） | 上游方案（对） |
|---|---|---|
| 数据源 | `byModel` 历史模型 | `/api/providers` 活跃连接列表 |
| 节点稳定性 | 随使用漂移 | 只显示当前连接的 provider |
| providers 页开关 | 完全无效 | `topologyVisibility` 设置过滤生效 |
| 免费商家 | 不处理 | noAuth 免费 provider 始终显示 |
| 加载方式 | 静态 import | dynamic import（@xyflow/react 不进共享 bundle） |

正确流程：本地有上游 checkout 时直接 diff 同路径文件的使用方式；否则 `git show <merge-base>:<path>` 看上游接法。按上游恢复数据源 + 渲染位置，再补 fork 特有逻辑。

## 上游参考实现要点（9router UsageStats.js）

```js
// isLLMProvider: serviceKinds 缺省视为 llm
// isTopologyVisible(p, topologyVisibility): false 显式隐藏 / true 显式显示 / 默认 !topologyHiddenByDefault
Promise.all([
  fetch("/api/providers"),      // 活跃连接, isActive===false 剔除, 按 provider 去重
  fetch("/api/provider-nodes"), // 自定义节点名映射
  fetch("/api/settings"),       // topologyVisibility 过滤
])
```

## i18n 缺 key 先查运行时 fallback 再定性

语言包 key 数差异巨大（zh-CN 1421 vs ja/ko/de 各 195）不一定是缺陷：先读运行时加载代码确认是否"缺 key 显示原文"的 by-design fallback（`translationMap[text] || text`）。是 fallback 设计则只影响覆盖度（非中文用户看英文原文），不算 bug；README 宣称多语言支持时才需注明覆盖度。
