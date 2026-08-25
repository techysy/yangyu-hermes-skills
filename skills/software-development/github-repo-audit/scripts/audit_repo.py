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


def find_under(d, name):
    """在目录下递归找某个文件 (不进入 .git)."""
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in ('.git', 'node_modules', 'old')]
        if name in files:
            return os.path.join(root, name)
    return None


def version_field(path):
    """读取 manifest.json / package.json 的 version 字段."""
    try:
        with open(path) as f:
            return json.load(f).get('version')
    except Exception:
        return None


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
    manifest = find_under(repo, 'manifest.json')
    pkgjson = find_under(repo, 'package.json')
    vfile = manifest or pkgjson
    source_version = None
    if vfile:
        source_version = version_field(vfile)
        print(f"[版本字段] {os.path.relpath(vfile, repo)}: {source_version}")
        # 从 README / CHANGELOG 提取声称的版本
        for doc in ('README.md', 'CHANGELOG.md'):
            p = os.path.join(repo, doc)
            if not os.path.exists(p):
                continue
            with open(p) as f:
                txt = f.read()
            m = re.search(r'v?(\d+\.\d+\.\d+(?:\.\d+)?)', txt[:2000])
            if m and source_version and m.group(1) != source_version:
                problems.append(f"[版本不一致] {doc} 声称 {m.group(1)}, 但 {os.path.basename(vfile)} 是 {source_version}")
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
