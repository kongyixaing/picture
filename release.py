#!/usr/bin/env python3
"""
GitHub Release 发布脚本
用于自动创建 GitHub Release 并上传打包文件

Usage:
    python release.py --version 0.0.1
    python release.py --version 0.0.1 --notes "发布说明"
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime


def run_command(cmd, check=True):
    """运行命令并返回输出"""
    print(f'\n执行: {cmd}')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f'错误: {result.stderr}')
        return False
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr and not check:
        print(result.stderr.strip())
    return result.stdout.strip()


def create_github_release(version, notes=''):
    """创建 GitHub Release"""
    tag = f'v{version}'
    repo = 'kongyixaing/picture'
    
    print(f'\n{"="*50}')
    print(f'创建 GitHub Release: {tag}')
    print(f'仓库: https://github.com/{repo}')
    print(f'{"="*50}')
    
    # 检查 tag 是否已存在
    result = subprocess.run(
        ['git', 'tag', '-l', tag],
        capture_output=True, text=True
    )
    existing_tag = result.stdout.strip()
    
    if existing_tag == tag:
        print(f'\n标签 {tag} 已存在')
        response = input('是否继续创建 Release？(y/n): ')
        if response.lower() != 'y':
            print('已取消')
            return False
    
    # 生成发布说明
    if not notes:
        notes = f'''## Picture & Videos v{version}

### 🎉 发布说明

这是 Picture & Videos 的 {version} 版本。

### 📥 下载链接

访问 [GitHub Releases](https://github.com/{repo}/releases) 下载适合您系统的安装包。

### 系统要求
- Windows 7+ / Linux / macOS 10.14+
- 至少 2GB 内存
- Chrome / Firefox / Edge 最新版浏览器

### 新增功能
- 图片和视频分享
- 即时通讯系统
- 好友系统
- 小镇地图（可配置）

更多详情请查看 [CHANGELOG.md](https://github.com/{repo}/blob/main/CHANGELOG.md)。
'''
    
    # 创建 Release
    print(f'\n正在创建 Release...')
    cmd = (
        f'gh release create {tag} '
        f'--repo {repo} '
        f'--title "Picture & Videos v{version}" '
        f'--notes "{notes}" '
        f'--latest'
    )
    
    # 写临时文件存储 notes
    notes_file = f'_release_notes_{tag}.md'
    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write(notes.replace('"', '\\"'))
    
    cmd = (
        f'gh release create {tag} '
        f'--repo {repo} '
        f'--title "Picture & Videos v{version}" '
        f'--notes-file {notes_file} '
        f'--latest'
    )
    
    try:
        result = run_command(cmd)
        os.remove(notes_file)
        if result:
            print(f'\n{"="*50}')
            print(f'✅ Release 创建成功！')
            print(f'链接: https://github.com/{repo}/releases/tag/{tag}')
            print(f'{"="*50}')
            return True
    except Exception as e:
        print(f'\n❌ 创建 Release 失败: {e}')
        if os.path.exists(notes_file):
            os.remove(notes_file)
        print('\n请手动访问: https://github.com/{repo}/releases')
        return False


def main():
    parser = argparse.ArgumentParser(description='GitHub Release 发布脚本')
    parser.add_argument('--version', required=True, help='版本号 (如: 0.0.1)')
    parser.add_argument('--notes', default='', help='发布说明')
    parser.add_argument('--push', action='store_true', help='推送所有更改到远程')
    args = parser.parse_args()
    
    version = args.version
    tag = f'v{version}'
    
    print(f'\nPicture & Videos 发布脚本')
    print(f'版本: {version}')
    print(f'标签: {tag}')
    
    # 如果需要推送
    if args.push:
        print('\n推送更改到远程...')
        run_command('git add -A')
        run_command(f'git commit -m "release: {tag}"')
        run_command('git push origin main')
        run_command(f'git tag -a {tag} -m "release: {tag}"')
        run_command(f'git push origin {tag}')
    
    # 创建 Release
    success = create_github_release(version, args.notes)
    
    if success:
        print('\n下一步:')
        print('1. 在 GitHub Release 页面上传打包文件')
        print('2. 或者配置 GitHub Actions 自动构建和发布')
        print('3. 编写 Release Notes')
        print('4. 发布 Release')


if __name__ == '__main__':
    main()
