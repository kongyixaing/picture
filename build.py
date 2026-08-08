#!/usr/bin/env python3
"""跨平台打包脚本 - Build script for all platforms

Usage:
    python build.py            # 自动检测当前平台并打包
    python build.py --platform windows  # 指定平台
    python build.py --release 0.0.1     # 指定版本号
"""
import os
import sys
import shutil
import platform
import subprocess
import argparse
from datetime import datetime

VERSION = '0.0.1'
APP_NAME = 'PictureAndVideos'
SUPPORTED_PLATFORMS = ['windows', 'linux', 'macos']


def get_platform():
    system = platform.system().lower()
    if 'windows' in system:
        return 'windows'
    elif 'linux' in system:
        return 'linux'
    elif 'darwin' in system:
        return 'macos'
    return system


def get_platform_info():
    system = platform.system()
    machine = platform.machine()
    
    if system == 'Windows':
        if machine == 'AMD64':
            return 'windows-x64'
        elif machine == 'ARM64':
            return 'windows-arm64'
        return 'windows-x86'
    elif system == 'Linux':
        if machine == 'x86_64':
            return 'linux-x64'
        elif machine == 'aarch64':
            return 'linux-arm64'
        return 'linux-x64'
    elif system == 'Darwin':
        if machine == 'arm64':
            return 'macos-arm64'
        return 'macos-x64'
    return f'{system.lower()}-{machine}'


def check_dependencies():
    print('检查依赖...')
    try:
        import PyInstaller
        print(f'  PyInstaller {PyInstaller.__version__} ✓')
    except ImportError:
        print('  安装 PyInstaller...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    try:
        import imageio_ffmpeg
        print(f'  imageio-ffmpeg ✓')
    except ImportError:
        print('  安装 imageio-ffmpeg...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'imageio-ffmpeg'])
    
    print('  依赖检查完成 ✓')


def clean_build():
    """清理之前的构建"""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f'  清理 {dir_name}/')


def build_executable(platform_name):
    """使用 PyInstaller 打包可执行文件"""
    print(f'\n使用 PyInstaller 打包 {APP_NAME}...')
    
    spec_file = 'pic_app.spec'
    if platform_name == 'windows':
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            spec_file, '--clean', '--noconfirm'
        ])
    else:
        # Linux/macOS 需要调整 spec 文件中的名称
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            spec_file, '--clean', '--noconfirm',
            '--name', APP_NAME.lower()
        ])


def create_archive(platform_name, version):
    """创建压缩包"""
    dist_dir = 'dist'
    archive_dir = 'release'
    
    if not os.path.exists(dist_dir):
        print('错误: dist 目录不存在，打包可能失败')
        return None
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    platform_tag = get_platform_info()
    
    # 确定压缩包格式
    if platform_name == 'windows':
        archive_name = f'{APP_NAME}-v{version}-{platform_tag}.zip'
        archive_path = os.path.join(archive_dir, archive_name)
        shutil.make_archive(
            os.path.join(archive_dir, f'{APP_NAME}-v{version}-{platform_tag}'),
            'zip', dist_dir
        )
    else:
        archive_name = f'{APP_NAME}-v{version}-{platform_tag}.tar.gz'
        archive_path = os.path.join(archive_dir, archive_name)
        # 使用 tar.gz
        import tarfile
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(dist_dir, arcname=f'{APP_NAME}-v{version}')
    
    print(f'  压缩包已创建: {archive_path}')
    return archive_path


def create_readme_release(platform_name, version, archive_path):
    """创建发布说明"""
    release_dir = 'release'
    readme_path = os.path.join(release_dir, f'{APP_NAME}-v{version}-{get_platform_info()}-README.txt')
    
    content = f'''{APP_NAME} v{version} - 安装说明
========================================

平台: {get_platform_info()}
版本: {version}
日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

一、系统要求
------------
{get_system_requirements(platform_name)}

二、安装步骤
------------
{get_install_steps(platform_name)}

三、启动应用
------------
{get_startup_steps(platform_name)}

四、功能特性
------------
• 图片分享 - 支持上传和浏览多种格式图片
• 视频分享 - 支持上传和在线播放
• 视频转码 - 自动转换为 Web 兼容格式
• 即时通讯 - 私聊和群聊
• 好友系统 - 添加好友和管理
• 小镇地图 - 像素风格的虚拟小镇（可配置）
• 内容审核 - 管理员审核系统

五、常见问题
------------
Q: 如何修改管理员密码？
A: 登录后进入个人设置修改密码。

Q: 数据存储在哪里？
A: 数据存储在程序目录下的 data/ 文件夹中。

Q: 如何开启小镇地图？
A: 编辑 config.json，将 map_enabled 设为 true。

六、技术支持
------------
GitHub: https://github.com/kongyixaing/picture
版本: v{version}
'''
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'  安装说明已创建: {readme_path}')


def get_system_requirements(platform_name):
    if platform_name == 'windows':
        return '''• Windows 7/8/10/11 (64位)
• 至少 2GB 内存
• 至少 200MB 可用磁盘空间
• 无需安装 Python'''
    elif platform_name == 'linux':
        return '''• Ubuntu 18.04 / CentOS 7 / Debian 10 或更高版本
• 至少 2GB 内存
• 至少 200MB 可用磁盘空间
• 无需安装 Python'''
    elif platform_name == 'macos':
        return '''• macOS 10.14 (Mojave) 或更高版本
• 至少 2GB 内存
• 至少 200MB 可用磁盘空间
• 无需安装 Python'''
    return '请查看官方文档'


def get_install_steps(platform_name):
    if platform_name == 'windows':
        return '''1. 解压 PictureAndVideos-v{version}-windows-x64.zip 到任意目录
2. 双击 PictureAndVideos.exe 启动
3. 首次启动会自动创建管理员账户

或者使用安装程序:
1. 运行 PictureAndVideos-Setup.exe
2. 按照安装向导完成安装'''
    elif platform_name == 'linux':
        return '''1. 解压 tar.gz: tar -xzf PictureAndVideos-v{version}-linux-x64.tar.gz
2. 进入解压目录: cd PictureAndVideos-v{version}
3. 添加执行权限: chmod +x PictureAndVideos
4. 启动应用: ./PictureAndVideos
5. 首次启动会自动创建管理员账户

（可选）注册为系统服务:
sudo cp picture.service /etc/systemd/system/
sudo systemctl enable picture
sudo systemctl start picture'''
    elif platform_name == 'macos':
        return '''1. 解压 tar.gz: tar -xzf PictureAndVideos-v{version}-macos-*.tar.gz
2. 进入解压目录: cd PictureAndVideos-v{version}
3. 添加执行权限: chmod +x PictureAndVideos
4. 启动应用: ./PictureAndVideos
5. 首次启动会自动创建管理员账户

注意: macOS 可能会提示安全警告，请在系统设置中允许运行。'''
    return '请查看官方文档'


def get_startup_steps(platform_name):
    if platform_name == 'windows':
        return '''1. 双击 PictureAndVideos.exe
2. 浏览器会自动打开 http://localhost:5001
3. 如果没有自动打开，请手动访问 http://localhost:5001
4. 默认管理员账户: admin / admin123
5. 首次登录后请立即修改密码'''
    elif platform_name in ('linux', 'macos'):
        return '''1. 运行 ./PictureAndVideos
2. 打开浏览器访问 http://localhost:5001
3. 默认管理员账户: admin / admin123
4. 首次登录后请立即修改密码
5. 按 Ctrl+C 停止服务'''
    return '请查看官方文档'


def create_checksum(archive_path):
    """创建文件校验和"""
    import hashlib
    
    checksums = {}
    for algo in ['md5', 'sha256']:
        hash_obj = hashlib.new(algo)
        with open(archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        checksums[algo] = hash_obj.hexdigest()
    
    checksum_path = archive_path + '.sha256'
    with open(checksum_path, 'w') as f:
        f.write(f'{checksums["sha256"]}  {os.path.basename(archive_path)}\n')
    
    print(f'  校验和: sha256={checksums["sha256"][:16]}...')
    return checksums


def main():
    parser = argparse.ArgumentParser(description='跨平台打包脚本')
    parser.add_argument('--platform', choices=SUPPORTED_PLATFORMS,
                        help='指定打包平台 (默认: 自动检测)')
    parser.add_argument('--release', default=VERSION,
                        help=f'版本号 (默认: {VERSION})')
    parser.add_argument('--clean', action='store_true',
                        help='清理之前的构建')
    args = parser.parse_args()
    
    version = args.release
    platform_name = args.platform or get_platform()
    platform_tag = get_platform_info()
    
    print(f'''
============================================
  {APP_NAME} v{version} 打包脚本
  平台: {platform_tag}
============================================
''')
    
    if args.clean:
        print('清理构建...')
        clean_build()
    
    check_dependencies()
    clean_build()
    build_executable(platform_name)
    
    print('\n创建发布包...')
    archive_path = create_archive(platform_name, version)
    
    if archive_path:
        create_readme_release(platform_name, version, archive_path)
        create_checksum(archive_path)
        
        print(f'''
============================================
  打包完成!
============================================

发布文件:
  压缩包: {archive_path}
  安装说明: release/{APP_NAME}-v{version}-{platform_tag}-README.txt
  校验和: {archive_path}.sha256

上传到 GitHub:
  1. 在 GitHub Releases 页面创建新 Release
  2. 上传上面的压缩包
  3. 粘贴 README.txt 内容到 Release 说明
  4. 发布 Release

详细说明: https://github.com/kongyixaing/picture
''')


if __name__ == '__main__':
    main()
