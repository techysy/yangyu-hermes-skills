#!/usr/bin/env python3
"""GitHub 仓库发布一致性审查辅助脚本.

用法:
  python3 audit_repo.py <repo_or_dir> [<zip_or_crx> ...]

对给定仓库目录执行:
  1. 版本号一致性 (manifest/package.json vs README/CHANGELOG)
  2. Chrome MV3 扩展 _locales/*/messages.json 语言包 key 差集
  3. 发布 zip/crx 与源码内容一致性 (可选, 传入 zip 路径)
  4. 检查 zip 路径分隔符 (反斜杠 = 无法被 Chrome 加载)
  5. LICENSE 文件存在性
  6. .gitignore 是否忽略 *.zip/*.crx/*.JPG
  7. Chrome MV3 专项: host_permissions 与实际 fetch() 域名差集

零依赖 (stdlib only). 打印审计报告, 非零退出码 = 发现严重问题.
"""
import json
import os
import re
import sys
import zipfile
import difflib


def norm(p):
    return p.replace('\\', '/')


# 构建产物/依赖目录: 找版本文件时跳过
SKIP_DIRS = ('.git', 'node_modules', 'old', 'dist', 'build', 'out', '.next',
             '.next-cli-build', '.turbo', '.cache', 'release', 'releases',
             'release_packages', 'coverage', '.venv', 'venv', '__pycache__')


def find_under(d, name):
    """在目录下递归找某个文件 (不进入构建/依赖目录)."""
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        if name in files:
            return os.path.join(root, name)
    return None


def find_all_under(d, name):
    """在目录下递归找全部同名文件 (不进入构建/依赖目录)."""
    hits = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        if name in files:
            hits.append(os.path.join(root, name))
    return hits


def version_field(path):
    """读取 manifest.json / package.json 的 version 字段."""
    try:
        with open(path) as f:
            return json.load(f).get('version')
    except Exception:
        return None


# ── 文档版本提取: 噪音过滤 + 版本语义上下文, 拿不准返回 None (宁可不报也不误报) ──
_DOC_NOISE_RE = re.compile(
    r'https?://|localhost|127\.0\.0\.1|Keep a Changelog|Semantic Versioning',
    re.IGNORECASE)
_DOC_BADGE_RE = re.compile(
    # 徽章只认带版本语义的: badge/v1.2.3 / badge/app-v1.2.3 / badge/version-1.2.3
    # (label 无 v 前缀的如 badge/fnOS-1.1.31xx 是"系统要求"徽章, 不是版本声明 → 不认)
    r'badge/(?:[a-z0-9]+[-_])?v(\d+\.\d+\.\d+(?:\.\d+)?)(?![\w.])'
    r'|badge/version[-_]?v?(\d+\.\d+\.\d+(?:\.\d+)?)(?![\w.])',
    re.IGNORECASE)
_DOC_HEADING_RE = re.compile(r'^\s*#{1,6}\s*\[?v?(\d+\.\d+\.\d+(?:\.\d+)?)\]?')
_DOC_LABEL_RE = re.compile(
    r'(?:当前版本|版本号|版本|version)\s*\**\s*[:：]?\s*v?(\d+\.\d+\.\d+(?:\.\d+)?)',
    re.IGNORECASE)
_DOC_BRACKET_RE = re.compile(r'\[v?(\d+\.\d+\.\d+(?:\.\d+)?)\]')


def _plausible_version(v):
    """排除日期误提取 (如 2026.10.12) —— 大版本号不可能是年份."""
    try:
        return int(v.split('.')[0]) < 1900
    except ValueError:
        return False


def _looks_like_ipv4(v):
    """4 段且每段 <=255 视为 IP (127.0.0.1), 用于裸 [ ] 上下文兜底."""
    parts = v.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def extract_doc_version(txt):
    """从 README/CHANGELOG 提取文档'声称的当前版本'.

    只认带版本语义的上下文: 徽章 badge/x.y.z、标题 ## [1.0.0]/# v1.0.0、
    版本标签 **版本**: 1.0.0、链接文本 [1.0.0]。
    跳过 URL 行与 Keep a Changelog/Semantic Versioning 规范引用;
    拿不准返回 None —— 调用方应跳过比对而不是报不一致。
    """
    for raw in txt[:20000].splitlines():
        line = raw.strip()
        if not line:
            continue
        # 1) 徽章 (含 URL 的行也要认; badge/version-1.0.0-blue)
        m = _DOC_BADGE_RE.search(line)
        v = (m.group(1) or m.group(2)) if m else None
        if v and _plausible_version(v):
            return v
        # 2) 裸链接文本: [1.0.0](...); [127.0.0.1] 之类 IP 兜底排除
        #    (放在噪音过滤之前 —— "见 [1.0.0](http://...)" 是合法版本声明;
        #    [http://127.0.0.1] 内容以 http 开头, 本就匹配不上)
        m = _DOC_BRACKET_RE.search(line)
        if m and _plausible_version(m.group(1)) and not _looks_like_ipv4(m.group(1)):
            return m.group(1)
        # 3) 版本标签 (语义词强约束, 结构上不怕 URL 噪音):
        #    **版本**: 1.0.0 / 当前版本 1.0.0 / version: 1.0.0
        m = _DOC_LABEL_RE.search(line)
        if m and _plausible_version(m.group(1)):
            return m.group(1)
        # 4) 噪音行: URL/本地地址/规范引用 —— 其余模式一律跳过
        if _DOC_NOISE_RE.search(line):
            continue
        # 5) 标题行: 严格开头 ## [1.0.0] / # v0.5.99
        m = _DOC_HEADING_RE.match(line)
        if m and _plausible_version(m.group(1)):
            return m.group(1)
        # 6) 宽松标题: # 9Router v0.5.99 for fnOS —— 标题内任意 v?x.y.z
        if re.match(r'^\s*#{1,6}\s', line):
            rest = re.sub(r'^\s*#{1,6}\s*', '', line)
            m = re.search(r'(?<![\d.])v?(\d+\.\d+\.\d+(?:\.\d+)?)(?![\d.])', rest)
            if m and _plausible_version(m.group(1)) and not _looks_like_ipv4(m.group(1)):
                return m.group(1)
    return None


def pick_version_source(repo):
    """按显式权威优先级挑出版本基准, 返回 (path, 全部候选路径列表).

    优先级: ui/package.json > 根 package.json > 其余 package.json > manifest.json;
    例外: Chrome 扩展 manifest (含 manifest_version) 始终权威。
    """
    manifest = find_under(repo, 'manifest.json')
    pkgs = sorted(find_all_under(repo, 'package.json'),
                  key=lambda p: _pkg_rank(repo, p))

    is_chrome_ext = False
    if manifest:
        try:
            with open(manifest) as f:
                is_chrome_ext = 'manifest_version' in json.load(f)
        except Exception:
            pass

    vfile = None
    if is_chrome_ext:
        vfile = manifest
    if not vfile:
        vfile = next((p for p in pkgs if version_field(p)), None)
    if not vfile and manifest:
        vfile = manifest

    all_srcs = []
    if vfile:
        all_srcs.append(vfile)
    for p in [manifest] if manifest else []:
        if p not in all_srcs:
            all_srcs.append(p)
    for p in pkgs:
        if p not in all_srcs:
            all_srcs.append(p)
    return vfile, all_srcs


def _pkg_rank(repo, p):
    """package.json 显式优先级: ui/ > 根 > 其余 (不依赖 walk 顺序)."""
    rel = norm(os.path.relpath(os.path.dirname(p), repo))
    if rel == 'ui':
        return (0, '')
    if rel == '.':
        return (1, '')
    return (2, rel)


def extract_fetch_hosts(repo):
    """从 .js 文件中提取 fetch() 使用的所有域名."""
    hosts = set()
    url_pattern = re.compile(r'["\'](https?://[^"\']+)["\']')
    for root, dirs, files in os.walk(repo):
        dirs[:] = [x for x in dirs if x not in ('.git', 'node_modules', 'old')]
        for fn in files:
            if not fn.endswith('.js'):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
            for url in url_pattern.findall(content):
                try:
                    host = url.split('://', 1)[1].split('/', 1)[0]
                    # 去掉端口
                    host = host.split(':', 1)[0]
                    hosts.add(host)
                except Exception:
                    pass
    return hosts


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    repo = sys.argv[1]
    zips = sys.argv[2:]
    problems = []

    print(f"== 审查仓库: {repo} ==")

    # 1. 版本号一致性
    # 源文件按显式优先级挑基准 (ui/package.json > 根 > 其余 > manifest;
    # Chrome 扩展 manifest 始终权威), 并把全部版本源打印出来供人工复核
    manifest = find_under(repo, 'manifest.json')
    vfile, all_srcs = pick_version_source(repo)
    source_version = None
    if vfile:
        source_version = version_field(vfile)
        for p in all_srcs:
            v = version_field(p)
            rel = norm(os.path.relpath(p, repo))
            if v is None:
                print(f"[版本字段] {rel}: (无 version 字段)")
                continue
            mark = " (基准)" if p == vfile else ""
            print(f"[版本字段] {rel}: {v}{mark}")
        # 从 README / CHANGELOG 提取声称的版本 (只认语义上下文, 拿不准跳过)
        if source_version:
            for doc in ('README.md', 'CHANGELOG.md'):
                p = os.path.join(repo, doc)
                if not os.path.exists(p):
                    continue
                try:
                    with open(p, encoding='utf-8', errors='ignore') as f:
                        txt = f.read()
                except Exception:
                    continue
                claimed = extract_doc_version(txt)
                if claimed is None:
                    print(f"[版本字段] {doc}: 未检出明确版本声明, 跳过比对")
                    continue
                print(f"[版本字段] {doc}: {claimed}")
                # 段数不同 = 不同版本体系 (如 4 位测试包 0.5.55.2 vs 3 位 0.5.55),
                # 没把握不报 —— 只比同段数的版本
                if len(claimed.split('.')) != len(source_version.split('.')):
                    print(f"[版本字段] {doc}: {claimed} 与源 {source_version} 段数不同, 视为不同版本体系, 跳过比对")
                    continue
                if claimed != source_version:
                    problems.append(f"[版本不一致] {doc} 声称 {claimed}, 但 {norm(os.path.relpath(vfile, repo))} 是 {source_version}")
        else:
            print(f"[版本字段] {norm(os.path.relpath(vfile, repo))} 无 version 字段, 跳过文档比对")
    else:
        print("[版本字段] 未找到 manifest.json / package.json")

    # 2. i18n 语言包 key 差集 (Chrome MV3)
    locales = os.path.join(repo, '_locales')
    if os.path.isdir(locales):
        keysets = {}
        for lang in sorted(os.listdir(locales)):
            p = os.path.join(locales, lang, 'messages.json')
            if not os.path.exists(p):
                continue
            with open(p) as f:
                keysets[lang] = set(json.load(f).keys())
        if keysets:
            base = keysets.get('en') or next(iter(keysets.values()))
            for lang, keys in keysets.items():
                missing = base - keys
                if missing:
                    problems.append(f"[i18n] {lang} 缺 {len(missing)} 个 key: {sorted(missing)}")
            print(f"[i18n] 检查 {len(keysets)} 个语言包")

    # 7. Chrome MV3 host_permissions 与 fetch() 域名差集
    if manifest:
        try:
            with open(manifest) as f:
                manifest_data = json.load(f)
            declared_hosts = set()
            for pattern in manifest_data.get('host_permissions', []):
                # 简化处理: 去掉 /* 取基础域名
                host = pattern.replace('https://', '').replace('http://', '').replace('/*', '').strip('/')
                if host:
                    declared_hosts.add(host)
            
            fetch_hosts = extract_fetch_hosts(repo)
            # 过滤掉本地/相对路径
            external_hosts = {h for h in fetch_hosts if not h.startswith(('localhost', '127.', 'chrome-extension'))}
            # 差集: 在 fetch 中使用但未在 host_permissions 中明确声明
            missing_hosts = set()
            for fh in external_hosts:
                # 检查是否有匹配的 host_permissions
                matched = any(fh == dh or fh.endswith('.' + dh) for dh in declared_hosts)
                if not matched:
                    missing_hosts.add(fh)
            
            if missing_hosts:
                problems.append(f"[MV3 host_permissions] fetch() 使用的域名未在 manifest 声明: {sorted(missing_hosts)}")
            print(f"[MV3] 检查 host_permissions 与 {len(external_hosts)} 个外部 fetch 域名")
        except Exception as e:
            print(f"[MV3] 无法解析 manifest: {e}")

    # 3-4. 发布 zip 与源码一致性 + 路径分隔符
    for zpath in zips:
        if not os.path.exists(zpath):
            print(f"[zip] 跳过不存在的: {zpath}")
            continue
        try:
            z = zipfile.ZipFile(zpath)
        except Exception as e:
            problems.append(f"[zip] {os.path.basename(zpath)} 无法打开: {e}")
            continue
        names = [n for n in z.namelist() if not n.endswith('/')]
        # 反斜杠路径检测
        bs = [n for n in names if '\\' in n]
        if bs:
            problems.append(f"[zip] {os.path.basename(zpath)} 含反斜杠路径 {len(bs)} 条 (Chrome 无法加载 unpacked 扩展)")
        # 版本字段
        for n in names:
            if norm(n).endswith('manifest.json'):
                try:
                    zv = json.loads(z.read(n).decode('utf-8')).get('version')
                    print(f"[zip] {os.path.basename(zpath)} manifest version: {zv}")
                    if source_version and zv and zv != source_version:
                        problems.append(f"[zip] {os.path.basename(zpath)} 版本 {zv} ≠ 源码 {source_version}")
                except Exception:
                    pass
        # 与源码内容比对 (对 js/html/css/json)
        for n in names:
            ext = os.path.splitext(n)[1].lower()
            if ext not in ('.js', '.html', '.css', '.json'):
                continue
            rel = norm(n)
            srcp = os.path.join(repo, rel)
            if not os.path.exists(srcp):
                continue
            with open(srcp, encoding='utf-8', errors='ignore') as f:
                src_lines = f.read().splitlines()
            z_lines = z.read(n).decode('utf-8', errors='ignore').splitlines()
            if len(src_lines) != len(z_lines):
                diff = list(difflib.unified_diff(src_lines, z_lines, lineterm='', n=0))
                problems.append(f"[zip] {os.path.basename(zpath)} 内 {rel} 与源码不一致 (源码{len(src_lines)}行 vs 产物{len(z_lines)}行, 差{len(diff)}行)")

    # 5. LICENSE
    if not any(os.path.exists(os.path.join(repo, l)) for l in ('LICENSE', 'LICENSE.md', 'LICENSE.txt')):
        problems.append("[license] 根目录无 LICENSE 文件 (检查 README 是否声称了 license)")

    # 6. .gitignore
    gi = os.path.join(repo, '.gitignore')
    if os.path.exists(gi):
        with open(gi) as f:
            gic = f.read()
        for art in ('*.zip', '*.crx', '*.JPG', 'releases/'):
            if art not in gic:
                print(f"[gitignore] 未忽略 {art}")

    print("\n== 审计结果 ==")
    if problems:
        print(f"发现 {len(problems)} 个问题:")
        for p in problems:
            print("  ❌ " + p)
        return 1
    print("  ✅ 未发现严重问题")
    return 0


if __name__ == '__main__':
    sys.exit(main())
