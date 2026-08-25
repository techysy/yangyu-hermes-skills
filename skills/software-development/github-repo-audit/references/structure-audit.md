# 大型多语言项目结构完整性审计脚本（经实测）

来源：对 Hermes agent 代码库（Python + TypeScript monorepo）做\"结构/缺文件/能否运行\"审查。以下脚本均经真实运行验证。

## 1. Python 语法 + 目录树编译

```bash
# 顶层文件逐个编译
python3 -m py_compile run_agent.py cli.py ...主模块...

# 整棵目录树一次编译（更全面），0 = 无语法错误
python3 -c "import compileall; exit(0 if compileall.compile_dir('.', quiet=1, maxlevels=10) else 1)"
```

## 2. Python 导入完整性（AST 扫描）

把 stdlib 之外、又不在本地顶层模块集合里的 import 挑出来做人工复核。

```python
import ast, os, sys
mods = set()
for ent in os.listdir('.'):
    if ent.endswith('.py'): mods.add(ent[:-3])
    elif os.path.isdir(ent) and os.path.exists(os.path.join(ent,'__init__.py')): mods.add(ent)
stdlib = set(sys.stdlib_module_names)
third = set()
for root, dirs, fs in os.walk('.'):
    if any(x in root for x in ('node_modules','.git','.venv','__pycache__','venv','dist','build')): continue
    for f in fs:
        if not f.endswith('.py'): continue
        tree = ast.parse(open(os.path.join(root,f), encoding='utf-8', errors='replace').read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    top = a.name.split('.')[0]
                    if top not in stdlib and top not in mods: third.add(a.name)
            elif isinstance(node, ast.ImportFrom) and node.level==0 and node.module:
                top = node.module.split('.')[0]
                if top not in stdlib and top not in mods: third.add(node.module)
```

**结果解读（关键）**：筛出的\"非本地模块\"大多是 **sys.path 注入的本地脚本** 或 **第三方 SDK 内部子模块**，不是真缺失。验证方式：
1. 在项目树里 `os.walk` 搜该模块名的实际文件（可能藏在 `skills/*/scripts`、`optional-skills/*/scripts`）。
2. 把对应 scripts 目录 `sys.path.insert(0, ...)` 后 `__import__(m)` 实测——能导入就说明完好。

常见 sys.path 注入位置：`skills/**/tests/conftest.py`、`optional-skills/**/scripts/`。

## 3. TypeScript ESM 引用完整性（.js → .ts）

NodeNext 风格下 `import from './foo.js'` 指向磁盘 `foo.ts`。校验相对导入时必须把 `.js` 换成 `.ts/.tsx`，否则误报数百个缺失。

```python
import os, re
def scan(base):
    missing=[]; checked=0
    def resolve(rel):
        for ext in ('.ts','.tsx','.js','.jsx','.d.ts'):
            if os.path.exists(rel+ext): return True
        for ix in ('index.ts','index.tsx'):
            if os.path.isdir(rel) and os.path.exists(os.path.join(rel,ix)): return True
        return False
    for root,dirs,files in os.walk(base):
        if 'node_modules' in root: continue
        for f in files:
            if not f.endswith(('.ts','.tsx')): continue
            src=open(os.path.join(root,f),encoding='utf-8',errors='replace').read()
            for m in re.finditer(r"(?:from|import\s*)\s*['\"]([^'\"]+)['\"]",src):
                spec=m.group(1)
                if not spec.startswith('.'): continue
                checked+=1
                cand=spec[:-3] if spec.endswith('.js') else spec
                rel=os.path.normpath(os.path.join(os.path.dirname(os.path.join(root,f)),cand))
                if not resolve(rel): missing.append((os.path.join(root,f),spec))
    return checked, missing
# 示例：scan('ui-tui/src'); scan('packages/hermes-ink/src')
```

注意 `.d.ts` 也要算作可解析目标（如 `../global.d.ts`）。

## 4. 运行实证（最重要的一层）

静态扫描只能证明\"文件引用闭合\"，真正的\"能否运行\"要靠冒烟测试：
- `./bin --version`、`python3 entry.py --help` → 看 exit code
- 项目自带的 `doctor` / `setup --check` / `self-check` 命令跑一遍，它会汇总缺什么（如 API key、入口点）

## 5. 终端工具 `&` 启发式误判的坑

在 `terminal` 里跑**含 `&` 字符的 heredoc 脚本**（哪怕 `&` 只在字符串字面量里，如 `'__pycache__'`）会被误判为后台任务而拒绝。解决：把脚本 `write_file` 到临时 `.py`，再 `python3 tmp.py` 运行，跑完删掉。

## 输出形态

- 明确分两栏：**代码/结构完整**（项目 OK）vs **环境/依赖缺失**（node_modules、pytest、API key —— 用户自己可装，不算项目缺文件）。
- 用清单 `OK / MISSING` 逐项列出，避免模糊表述。
