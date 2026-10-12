#!/usr/bin/env python3
"""Read Chrome's Goofish cookies on macOS and import over Docker stdin."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

DOMAINS = ('goofish.com', 'taobao.com')

IMPORT_CODE = '''
import json, os, sys, tempfile
from pathlib import Path
from goofish_cli.core.crypto import encrypt_cookies
from goofish_cli.core.session import resolve_cookie_path
records = json.load(sys.stdin)
flat = {r['name']: r['value'] for r in records}
if not all(flat.get(k) for k in ('unb', '_m_h5_tk')):
    raise SystemExit(2)
path = resolve_cookie_path()
path.parent.mkdir(parents=True, exist_ok=True)
fd, name = tempfile.mkstemp(prefix='.cookie-import-', dir=path.parent)
try:
    with os.fdopen(fd, 'wb') as f:
        f.write(encrypt_cookies(records))
    os.replace(name, path)
finally:
    if os.path.exists(name):
        os.unlink(name)
print('encrypted-import-ok')
'''


def validate_records(records):
    out, seen = [], set()
    for record in records:
        host = record.get('domain', '').lstrip('.').lower()
        if not any(host == d or host.endswith('.' + d) for d in DOMAINS):
            continue
        if not record.get('name') or not record.get('value'):
            continue
        key = (record['name'], record['domain'], record.get('path') or '/')
        if key not in seen:
            seen.add(key)
            out.append(dict(name=key[0], value=record['value'], domain=key[1], path=key[2]))
    flat = {r['name']: r['value'] for r in out}
    if not all(flat.get(k) for k in ('unb', '_m_h5_tk')):
        raise ValueError('缺少闲鱼登录态')
    return out


def status_valid(output):
    try:
        return json.loads(output).get('valid') is True
    except (ValueError, AttributeError):
        return False


def read_chrome(profile=None):
    import browser_cookie3
    root = Path.home() / 'Library/Application Support/Google/Chrome'
    profiles = [root / profile] if profile else [root / 'Default', *sorted(root.glob('Profile *'))]
    found_database = False
    for folder in profiles:
        for database in (folder / 'Cookies', folder / 'Network/Cookies'):
            if not database.is_file():
                continue
            found_database = True
            try:
                records = []
                for domain in DOMAINS:
                    jar = browser_cookie3.chrome(cookie_file=str(database), domain_name=domain)
                    records.extend(
                        dict(name=c.name, value=c.value, domain=c.domain, path=c.path or '/')
                        for c in jar if c.expires is None or c.expires > time.time()
                    )
                return validate_records(records)
            except Exception:
                continue
    if not found_database:
        raise ValueError('没有找到 Chrome Cookie 数据库。请先打开 Chrome，并登录闲鱼。')
    raise ValueError('未读取到完整闲鱼登录态。请在 Chrome 登录 www.goofish.com；如出现钥匙串提示，请允许访问。仍失败时，请彻底退出 Chrome 后重试。')


def main():
    parser = argparse.ArgumentParser(description='从 Mac Chrome 一键导入闲鱼登录态到 Docker')
    parser.add_argument('--profile', help='指定 Chrome 配置目录，例如 Default 或 Profile 1')
    parser.add_argument('--container', default='goofish-cli', help='目标容器名称')
    parser.add_argument('--check-only', action='store_true', help='仅检查 Docker，不读取 Cookie')
    args = parser.parse_args()
    docker = shutil.which('docker')
    if not docker:
        raise ValueError('没有找到 Docker。请启动 Docker Desktop 后重试。')
    state = subprocess.run([docker, 'inspect', '--format', '{{.State.Running}}', args.container], capture_output=True, text=True, timeout=20)
    if state.returncode or state.stdout.strip() != 'true':
        raise ValueError('目标容器没有运行。请先启动 Docker Desktop 和 goofish-cli 容器。')
    if args.check_only:
        print('Docker 容器正在运行，可以导入。')
        return 0
    print('正在读取 Chrome 闲鱼登录态。如弹出钥匙串提示，请允许访问。', flush=True)
    records = read_chrome(args.profile)
    result = subprocess.run([docker, 'exec', '-i', args.container, 'python', '-c', IMPORT_CODE], input=json.dumps(records), capture_output=True, text=True, timeout=30)
    if result.returncode or 'encrypted-import-ok' not in result.stdout:
        raise ValueError('容器写入失败。请检查容器状态和数据卷权限。')
    print('Cookie 已加密导入，正在验证闲鱼登录状态……', flush=True)
    status = subprocess.run([docker, 'exec', args.container, 'goofish', 'auth', 'status', '--format', 'json'], capture_output=True, text=True, timeout=90)
    if status.returncode == 0 and status_valid(status.stdout):
        print('成功：闲鱼登录有效，现在可以使用 Docker 中的 goofish 命令。')
        return 0
    print('Cookie 已导入，但闲鱼未确认登录有效。请在 Chrome 重新登录后，再运行本脚本。')
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        print('操作超时。若已显示 Cookie 导入成功，可稍后运行 docker exec goofish-cli goofish auth status 再检查。', file=sys.stderr)
        sys.exit(2)
    except (ValueError, ImportError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
