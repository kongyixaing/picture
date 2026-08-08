@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================
echo   Picture & Videos - GitHub Release 发布脚本
echo ====================================================
echo.

REM 检查版本号
if "%1"=="" (
    set /p VERSION="请输入版本号 (如 0.0.1): "
) else (
    set VERSION=%1
)

if "%VERSION%"=="" (
    echo ❌ 未输入版本号
    pause
    exit /b 1
)

echo.
echo 版本: %VERSION%
echo.

REM 检查 Token
if "%GITHUB_TOKEN%"=="" (
    echo ⚠️  未设置 GITHUB_TOKEN 环境变量
    echo.
    echo 请按以下步骤获取 Token:
    echo   1. 访问 https://github.com/settings/tokens
    echo   2. 点击 "Generate new token (classic)"
    echo   3. 勾选 "repo" 权限
    echo   4. 复制 Token
    echo.
    set /p GITHUB_TOKEN="请粘贴你的 GitHub Token: "
    echo.
)

if "%GITHUB_TOKEN%"=="" (
    echo ❌ 未设置 Token，无法发布
    pause
    exit /b 1
)

echo ✅ Token 已设置
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装
    echo 请从 https://www.python.org 下载安装
    pause
    exit /b 1
)

REM 检查 requests 库
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 安装 requests 库...
    pip install requests
)

REM 查找构建产物
echo.
echo 查找构建产物...
set ARTIFACTS=
if exist "release\PictureAndVideos-v%VERSION%-windows-x64.zip" (
    set ARTIFACTS=release\PictureAndVideos-v%VERSION%-windows-x64.zip
    echo   找到: !ARTIFACTS!
) else (
    for %%f in (release\*.zip) do (
        set ARTIFACTS=%%f
        echo   找到: !ARTIFACTS!
    )
)

if "!ARTIFACTS!"=="" (
    echo ❌ 未找到构建产物
    echo 请先运行 build.py 或 build_exe.bat
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   开始发布 %VERSION%
echo ====================================================
echo.

REM 创建 Python 发布脚本
python -c "
import os, json, sys, urllib.request, urllib.error

GITHUB_API = 'https://api.github.com'
REPO = 'kongyixaing/picture'
TOKEN = os.environ.get('GITHUB_TOKEN', '')
VERSION = '%VERSION%'
TAG = f'v{VERSION}'

def gh_request(method, endpoint, data=None, headers=None):
    url = f'{GITHUB_API}{endpoint}'
    hdrs = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PictureAndVideos-Publisher',
    }
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f'  API 错误: {e.code}')
        return None

# 验证 Token
user = gh_request('GET', '/user')
if user:
    print(f'✅ 已登录: {user[\"login\"]}')
else:
    print('❌ Token 无效')
    sys.exit(1)

# 检查 Release 是否存在
releases = gh_request('GET', f'/repos/{REPO}/releases')
existing_id = None
if releases:
    for r in releases:
        if r['tag_name'] == TAG:
            existing_id = r['id']
            print(f'⚠️  Release {TAG} 已存在 (ID: {existing_id})')
            break

if existing_id:
    release_id = existing_id
else:
    # 创建 Release
    print(f'📦 创建 Release: {TAG}')
    body = f'''## Picture & Videos v{VERSION}

### 下载链接

| 平台 | 文件 |
|------|------|
| Windows x64 | PictureAndVideos-v{VERSION}-windows-x64.zip |
| Linux x64 | PictureAndVideos-v{VERSION}-linux-x64.tar.gz |
| macOS ARM64 | PictureAndVideos-v{VERSION}-macos-arm64.tar.gz |

### 系统要求
- Windows 7+ / Linux / macOS 10.14+
- 至少 2GB 内存
- Chrome / Firefox / Edge 最新版

### 功能特性
- 图片和视频分享
- 即时通讯（私聊/群聊）
- 好友系统
- 小镇地图（可配置开关）
- 内容审核和用户管理
- 自动数据备份

### 快速开始
1. 下载安装包
2. 解压到任意目录
3. 双击 PictureAndVideos.exe 启动
4. 访问 http://localhost:5001
5. 默认账户: admin / admin123
'''
    
    result = gh_request('POST', f'/repos/{REPO}/releases', {
        'tag_name': TAG,
        'name': f'Picture & Videos v{VERSION}',
        'body': body,
        'draft': False,
        'prerelease': False,
    })
    if result:
        release_id = result['id']
        print(f'✅ Release 创建成功!')
        print(f'🔗 {result[\"html_url\"]}')
    else:
        print('❌ 创建 Release 失败')
        sys.exit(1)

# 上传文件
artifacts = []
import glob
for pattern in ['release/*.zip', 'release/*.tar.gz']:
    artifacts.extend(glob.glob(pattern))

if artifacts:
    print(f'📤 上传 {len(artifacts)} 个文件...')
    for artifact in artifacts:
        fname = os.path.basename(artifact)
        size = os.path.getsize(artifact)
        print(f'   上传: {fname} ({size/1024/1024:.1f} MB)')
        
        with open(artifact, 'rb') as f:
            content = f.read()
        
        upload_url = f'{GITHUB_API}/repos/{REPO}/releases/{release_id}/assets?name={fname}'
        mime = 'application/zip' if fname.endswith('.zip') else 'application/gzip'
        
        hdrs = {
            'Authorization': f'token {TOKEN}',
            'Content-Type': mime,
            'Content-Length': str(size),
            'User-Agent': 'PictureAndVideos-Publisher',
        }
        
        req = urllib.request.Request(upload_url, data=content, headers=hdrs, method='POST')
        try:
            with urllib.request.urlopen(req) as resp:
                print(f'      ✅ 上传成功')
        except urllib.error.HTTPError as e:
            print(f'      ❌ 上传失败: {e.code}')

print(f'''
====================================================
  ✅ 发布完成!
====================================================

🔗 Release URL: https://github.com/{REPO}/releases/tag/{TAG}
''')
"

echo.
echo ====================================================
echo   完成!
echo ====================================================
echo.
pause
