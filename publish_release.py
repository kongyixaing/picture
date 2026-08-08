#!/usr/bin/env python3
"""
GitHub Release 一键发布脚本

功能:
  1. 自动检测打包产物
  2. 创建 GitHub Release
  3. 上传所有平台的安装包
  4. 生成 Release Notes

Usage:
  # 方式1: 通过环境变量设置 Token
  set GITHUB_TOKEN=your_token_here
  python publish_release.py --version 0.0.1

  # 方式2: 通过命令行参数
  python publish_release.py --version 0.0.1 --token your_token_here

  # 方式3: 交互式输入
  python publish_release.py --version 0.0.1 --interactive
"""
import os
import sys
import json
import time
import hashlib
import argparse
import mimetypes
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


GITHUB_API = 'https://api.github.com'
REPO = 'kongyixaing/picture'


def get_token(args_token=None, interactive=False):
    """获取 GitHub Token"""
    token = args_token or os.environ.get('GITHUB_TOKEN', '')
    if token:
        return token
    
    if interactive:
        print('\n' + '='*50)
        print('GitHub Token 获取方式:')
        print('1. 访问 https://github.com/settings/tokens')
        print('2. 点击 "Generate new token (classic)"')
        print('3. 勾选 "repo" 权限')
        print('4. 复制 Token')
        print('='*50)
        token = input('\n请输入你的 GitHub Token: ').strip()
        if token:
            return token
    
    print('\n❌ 错误: 未设置 GitHub Token')
    print('\n设置方式:')
    print('  Windows CMD: set GITHUB_TOKEN=your_token')
    print('  PowerShell:  $env:GITHUB_TOKEN="your_token"')
    print('  Python:      python publish_release.py --token your_token')
    print('  交互模式:   python publish_release.py --interactive')
    sys.exit(1)


def github_request(method, endpoint, token, data=None, headers=None):
    """发送 GitHub API 请求"""
    url = f'{GITHUB_API}{endpoint}'
    hdrs = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PictureAndVideos-Publisher',
    }
    if headers:
        hdrs.update(headers)
    
    body = json.dumps(data).encode('utf-8') if data else None
    req = Request(url, data=body, headers=hdrs, method=method)
    
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        try:
            error_data = json.loads(error_body)
            msg = error_data.get('message', str(e))
        except:
            msg = str(e)
        print(f'  ❌ API 错误: {msg}')
        if 'rate limit' in msg.lower():
            print('  💡 提示: API 调用频率过高，请稍后再试')
        return None
    except URLError as e:
        print(f'  ❌ 网络错误: {e.reason}')
        return None


def create_release(version, token):
    """创建 GitHub Release"""
    tag = f'v{version}'
    
    print(f'\n📦 创建 Release: {tag}')
    
    # 检查 tag 是否存在
    existing = github_request('GET', f'/repos/{REPO}/git/refs/tags/{tag}', token)
    if existing is None:
        # tag 可能不存在，先创建
        print(f'  创建 tag {tag}...')
        # 获取最新 commit
        commits = github_request('GET', f'/repos/{REPO}/commits?per_page=1', token)
        if commits:
            sha = commits[0]['sha']
            github_request('POST', f'/repos/{REPO}/git/refs', token, {
                'ref': f'refs/tags/{tag}',
                'sha': sha
            })
    
    # 检查现有 Release
    releases = github_request('GET', f'/repos/{REPO}/releases', token)
    if releases:
        for r in releases:
            if r['tag_name'] == tag:
                print(f'  ⚠️ Release {tag} 已存在，ID: {r["id"]}')
                return r['id']
    
    # 生成 Release Notes
    body = generate_release_notes(version)
    
    # 创建 Release
    data = {
        'tag_name': tag,
        'name': f'Picture & Videos v{version}',
        'body': body,
        'draft': False,
        'prerelease': False,
        'generate_release_notes': False,
    }
    
    result = github_request('POST', f'/repos/{REPO}/releases', token, data)
    if result:
        print(f'  ✅ Release 创建成功!')
        print(f'  🔗 URL: {result["html_url"]}')
        return result['id']
    return None


UPLOAD_API = 'https://uploads.github.com'


def upload_asset(release_id, file_path, token):
    """上传文件到 Release
    
    直接使用 release_id 构造上传 URL，避免重新查询 releases 列表。
    """
    filename = os.path.basename(file_path)
    size = os.path.getsize(file_path)
    
    print(f'  📤 上传: {filename} ({size/1024/1024:.1f} MB)')
    
    # 检查是否已存在同名 asset，如存在先删除
    existing = github_request('GET', f'/repos/{REPO}/releases/{release_id}', token)
    if existing and existing.get('assets'):
        for asset in existing['assets']:
            if asset['name'] == filename:
                print(f'  🗑️  删除已存在的旧文件: {filename}')
                github_request('DELETE', f'/repos/{REPO}/releases/assets/{asset["id"]}', token)
                break
    
    # 直接构造上传 URL
    upload_url = f'{UPLOAD_API}/repos/{REPO}/releases/{release_id}/assets?name={filename}'
    
    # 读取文件
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 上传文件
    if file_path.endswith('.zip'):
        mime_type = 'application/zip'
    elif file_path.endswith('.tar.gz'):
        mime_type = 'application/gzip'
    else:
        mime_type = 'application/octet-stream'
    
    hdrs = {
        'Authorization': f'token {token}',
        'Content-Type': mime_type,
        'Content-Length': str(size),
        'User-Agent': 'PictureAndVideos-Publisher',
    }
    
    req = Request(upload_url, data=content, headers=hdrs, method='POST')
    
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f'  ✅ 上传成功!')
            if result.get('browser_download_url'):
                print(f'  🔗 {result["browser_download_url"]}')
            return True
    except HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        print(f'  ❌ 上传失败: {e.code} - {error_body[:200]}')
        return False


def find_build_artifacts(version=None):
    """查找构建产物
    
    只返回 release/ 目录下与版本号匹配的压缩包，
    避免上传无关的 exe 或 ffmpeg 文件。
    """
    artifacts = []
    release_dir = 'release'
    
    if not os.path.exists(release_dir):
        return artifacts
    
    for f in sorted(os.listdir(release_dir)):
        # 只接受 .zip 和 .tar.gz 压缩包
        if not f.endswith(('.zip', '.tar.gz')):
            continue
        # 如果指定了版本号，只返回匹配的文件
        if version:
            tag = f'v{version}'
            if tag not in f:
                continue
        artifacts.append(os.path.join(release_dir, f))
    
    return artifacts


def generate_release_notes(version):
    """生成 Release Notes"""
    return f'''## Picture & Videos v{version}

### 🎉 发布说明

这是 Picture & Videos 的 **{version}** 版本发布。

### 📥 下载链接

请查看右侧的附件下载适合您系统的安装包。

| 平台 | 文件 |
|------|------|
| Windows x64 | PictureAndVideos-v{version}-windows-x64.zip |
| Linux x64 | PictureAndVideos-v{version}-linux-x64.tar.gz |
| macOS ARM64 | PictureAndVideos-v{version}-macos-arm64.tar.gz |

### 💻 系统要求

- **Windows**: Windows 7/8/10/11 (64位)，至少 2GB 内存
- **Linux**: Ubuntu 18.04+ / CentOS 7+，至少 2GB 内存
- **macOS**: macOS 10.14+，Apple Silicon / Intel

### ✨ 主要功能

- 🖼️ 图片分享 - 支持多种图片格式上传和浏览
- 🎬 视频分享 - 视频上传、转码和在线播放
- 💬 即时通讯 - 私聊和群聊功能
- 👥 好友系统 - 添加好友和管理
- 🏛️ 小镇地图 - 像素风格虚拟小镇（可配置开启）
- ✅ 管理后台 - 内容审核和用户管理
- 💾 数据备份 - 自动备份和恢复

### 🚀 快速开始

**Windows:**
```
解压 .zip 文件，双击 PictureAndVideos.exe 启动
访问 http://localhost:5001
```

**Linux/macOS:**
```bash
tar -xzf PictureAndVideos-v{version}-linux-x64.tar.gz
chmod +x PictureAndVideos
./PictureAndVideos
```

### 🔐 首次使用

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

⚠️ 请登录后立即修改密码！

### 📚 更多信息

- 📖 [README](https://github.com/{REPO}/blob/main/README.md)
- 📝 [更新日志](https://github.com/{REPO}/blob/main/CHANGELOG.md)
- 🐛 [问题反馈](https://github.com/{REPO}/issues)
'''


def main():
    parser = argparse.ArgumentParser(
        description='GitHub Release 一键发布脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python publish_release.py --version 0.0.1 --token ghp_xxxx
  python publish_release.py --version 1.0.0 --interactive
  set GITHUB_TOKEN=ghp_xxxx && python publish_release.py --version 0.0.1
        '''
    )
    parser.add_argument('--version', required=True, help='版本号，如 0.0.1')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式输入 Token')
    parser.add_argument('--skip-upload', action='store_true', help='跳过文件上传')
    args = parser.parse_args()
    
    version = args.version
    
    print(f'''
╔══════════════════════════════════════════════╗
║  Picture & Videos - GitHub Release Publisher ║
╚══════════════════════════════════════════════╝

版本: {version}
仓库: https://github.com/{REPO}
''')
    
    # 获取 Token
    token = get_token(args.token, args.interactive)
    if not token:
        sys.exit(1)
    
    print(f'✅ Token 已获取')
    
    # 验证 Token
    user = github_request('GET', '/user', token)
    if user:
        print(f'✅ 已登录: {user["login"]}')
    else:
        print('❌ Token 无效')
        sys.exit(1)
    
    # 查找构建产物（只返回匹配当前版本的文件）
    artifacts = find_build_artifacts(version)
    print(f'\n📁 找到 {len(artifacts)} 个构建产物:')
    for a in artifacts:
        size = os.path.getsize(a) / 1024 / 1024
        print(f'   • {os.path.basename(a)} ({size:.1f} MB)')
    
    # 创建 Release
    release_id = create_release(version, token)
    if not release_id:
        print('❌ 创建 Release 失败')
        sys.exit(1)
    
    # 上传文件
    if artifacts and not args.skip_upload:
        print(f'\n📤 开始上传 {len(artifacts)} 个文件...')
        for artifact in artifacts:
            upload_asset(release_id, artifact, token)
            time.sleep(0.5)  # 避免 API 限流
    elif args.skip_upload:
        print('\n⏭️ 已跳过文件上传')
    
    # 完成
    tag = f'v{version}'
    print(f'''
╔══════════════════════════════════════════════╗
║  ✅ 发布完成!                                ║
╚══════════════════════════════════════════════╝

🔗 Release URL: https://github.com/{REPO}/releases/tag/{tag}

💡 后续步骤:
  1. 访问 Release 页面确认内容
  2. 如果需要，手动添加 Linux/macOS 版本的安装包
  3. 通知用户新版本已发布
  4. 更新 CHANGELOG.md（如需要）
''')


if __name__ == '__main__':
    main()
