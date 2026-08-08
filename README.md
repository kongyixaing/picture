# Picture & Videos

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.0.1-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/python-3.14-orange.svg" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
</p>

<p align="center">
  <strong>图片视频分享社区 · 虚拟小镇地图</strong>
</p>

<p align="center">
  <a href="https://github.com/kongyixaing/picture/releases">📥 下载</a> ·
  <a href="#功能特性">功能</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#配置说明">配置</a> ·
  <a href="#开发者">开发者</a>
</p>

---

## 📥 下载安装

### 最新版本: v0.0.1

点击下方链接下载适合您系统的安装包：

| 平台 | 安装包 | 大小 | 说明 |
|------|--------|------|------|
| <img src="https://img.shields.io/badge/Windows-10%2F11-0078D4.svg?logo=windows&logoColor=white" width="15"> **Windows x64** | [下载 .zip](https://github.com/kongyixaing/picture/releases/download/v0.0.1/PictureAndVideos-v0.0.1-windows-x64.zip) | ~50MB | 解压后双击运行 |
| <img src="https://img.shields.io/badge/Linux-x64-FCC624.svg?logo=linux&logoColor=black" width="15"> **Linux x64** | [下载 .tar.gz](https://github.com/kongyixaing/picture/releases/download/v0.0.1/PictureAndVideos-v0.0.1-linux-x64.tar.gz) | ~50MB | 解压后执行 `./PictureAndVideos` |
| <img src="https://img.shields.io/badge/macOS-Apple%20Silicon-555555.svg?logo=apple&logoColor=white" width="15"> **macOS ARM64** | [下载 .tar.gz](https://github.com/kongyixaing/picture/releases/download/v0.0.1/PictureAndVideos-v0.0.1-macos-arm64.tar.gz) | ~50MB | 解压后执行 `./PictureAndVideos` |
| <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white" width="15"> **Docker** | [查看说明](#docker部署) | - | 适合服务器部署 |

### 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 7 / Ubuntu 18.04 / macOS 10.14 | Windows 10 / Ubuntu 20.04 / macOS 12+ |
| 内存 | 2 GB | 4 GB+ |
| 磁盘 | 200 MB | 500 MB+ |
| 浏览器 | Chrome / Firefox / Edge 最新版 | Chrome 最新版 |
| 网络 | 需要互联网连接（首次使用） | 稳定宽带 |

### 安装步骤

#### Windows

1. 下载 `PictureAndVideos-v0.0.1-windows-x64.zip`
2. 右键解压到任意目录（如 `C:\PictureAndVideos`）
3. 双击 `PictureAndVideos.exe` 启动
4. 浏览器会自动打开 `http://localhost:5001`
5. 默认管理员账户：`admin` / `admin123`
6. ⚠️ 首次登录后请立即修改密码！

#### Linux

```bash
# 1. 下载并解压
wget https://github.com/kongyixaing/picture/releases/download/v0.0.1/PictureAndVideos-v0.0.1-linux-x64.tar.gz
tar -xzf PictureAndVideos-v0.0.1-linux-x64.tar.gz
cd PictureAndVideos

# 2. 添加执行权限
chmod +x PictureAndVideos

# 3. 启动服务
./PictureAndVideos
# 访问 http://localhost:5001
```

**注册为系统服务（可选）：**
```bash
# 创建服务文件
sudo tee /etc/systemd/system/picture.service << 'EOF'
[Unit]
Description=Picture & Videos Service
After=network.target

[Service]
Type=simple
User=picture
WorkingDirectory=/opt/PictureAndVideos
ExecStart=/opt/PictureAndVideos/PictureAndVideos
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable picture
sudo systemctl start picture
```

#### macOS

```bash
# 1. 下载并解压
curl -O https://github.com/kongyixaing/picture/releases/download/v0.0.1/PictureAndVideos-v0.0.1-macos-arm64.tar.gz
tar -xzf PictureAndVideos-v0.0.1-macos-arm64.tar.gz
cd PictureAndVideos

# 2. 添加执行权限
chmod +x PictureAndVideos

# 3. 启动
./PictureAndVideos
```

⚠️ macOS 首次运行可能提示安全警告：
- 打开 **系统设置 → 隐私与安全性**
- 点击 "仍要运行" 按钮
- 或在终端执行：`xattr -d com.apple.quarantine PictureAndVideos`

## 🐳 Docker 部署

```bash
# 拉取镜像（如果需要）
# docker pull picture:latest

# 运行容器
docker run -d \
  --name picture \
  -p 5001:5001 \
  -v ./data:/app/data \
  -v ./uploads:/app/static/uploads \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  picture:latest

# 查看日志
docker logs -f picture

# 停止服务
docker stop picture
docker rm picture
```

## ✨ 功能特性

### 核心功能
- 🖼️ **图片分享** - 支持上传和浏览图片（PNG、JPG、GIF、BMP、WebP）
- 🎬 **视频分享** - 支持上传视频并在线播放（MP4、AVI、MOV、MKV 等）
- 🔄 **视频转码** - 自动将视频转换为 Web 兼容格式
- 💬 **即时通讯** - 支持私聊和群聊功能
- 👥 **好友系统** - 添加好友、好友申请、好友管理

### 管理功能
- ✅ **内容审核** - 管理员审核用户上传的图片和视频
- 👤 **用户管理** - 管理员管理用户账号
- 📋 **申请管理** - 审核新用户注册申请
- 🔨 **封禁管理** - 查看封禁记录和解封
- 💾 **数据备份** - 自动备份所有数据，支持一键恢复

### 小镇地图（可通过 config.json 开启）
- 🏛️ **中心广场** - 像素风格的小镇中心
- 🏠 **租地建房** - 用户可以租用地块并建造自己的房屋
- 🌍 **世界地图** - 在地图上自由探索，访问其他用户的房屋
- ⭐ **积分系统** - 积分可用于租地、建房
- 🚧 **预留用地** - 功能建筑预留位置

## 🛠️ 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| 后端 | Python 3.14 + Flask | Web 框架 |
| 前端 | HTML5 + CSS3 + JavaScript | Canvas API 绘制地图 |
| 存储 | JSON 文件 | 轻量级数据存储 |
| 打包 | PyInstaller | 跨平台打包 |
| 加密 | cryptography | 数据加密 |
| 视频 | imageio-ffmpeg | 视频转码处理 |

## 📁 项目结构

```
picture/
├── pic_app.py          # 主应用入口
├── pic_models.py       # 数据模型（用户、图片、评论等）
├── land_system.py      # 小镇地图系统
├── world_map.py        # 世界地图/玩家位置
├── backup.py           # 备份系统
├── file_crypto.py      # 文件加密
├── video_converter.py  # 视频转码
├── build.py            # 跨平台打包脚本
├── pic_app.spec        # PyInstaller 配置（Windows）
├── pic_app_unix.spec   # PyInstaller 配置（Linux/macOS）
├── config.json         # 功能开关配置
├── templates/          # HTML 模板
├── static/             # 静态资源
└── .github/workflows/  # GitHub Actions CI/CD
```

## 🚀 快速开始

### 从源码运行（开发者）

```bash
# 克隆仓库
git clone https://github.com/kongyixaing/picture.git
cd picture

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install flask cryptography imageio-ffmpeg

# 运行应用
python pic_app.py
```

访问 `http://localhost:5001`

### 从源码打包

```bash
# 安装打包依赖
pip install pyinstaller

# 使用跨平台打包脚本
python build.py                    # 自动检测当前平台
python build.py --platform windows  # 指定平台
python build.py --release 1.0.0    # 指定版本号

# 打包产物在 release/ 目录
```

## ⚙️ 配置说明

### 功能开关

编辑 `config.json` 控制功能开关：

```json
{
    "map_enabled": true
}
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `map_enabled` | boolean | `false` | 开启/关闭小镇地图功能 |

> 💡 修改 `config.json` 后会自动生效，无需重启服务。

### 管理员账户

首次启动后自动创建管理员账户：
- 用户名: `admin`
- 默认密码: `admin123`

⚠️ 请登录后立即修改密码！

### 数据目录

首次运行会在程序目录下创建以下文件夹：

```
picture/
├── data/              # 数据库和加密密钥
├── backups/           # 自动备份文件
├── static/uploads/    # 用户上传的图片和视频
└── user/              # 用户数据
```

## 📝 API 接口

| 接口 | 方法 | 说明 | 需要登录 |
|------|------|------|----------|
| `/pic` | GET | 首页 | 否 |
| `/pic/login` | GET/POST | 登录 | 否 |
| `/pic/apply` | GET/POST | 申请账号 | 否 |
| `/pic/world` | GET | 小镇地图 | 是 |
| `/pic/upload` | GET/POST | 上传图片/视频 | 是 |
| `/pic/profile` | GET | 个人资料 | 是 |
| `/pic/groups` | GET | 群聊列表 | 是 |
| `/pic/friends` | GET | 好友列表 | 是 |
| `/pic/my/house` | GET | 我的房屋 | 是 |
| `/pic/admin/users` | GET | 用户管理 | 管理员 |
| `/pic/admin/review` | GET | 内容审核 | 管理员 |
| `/pic/land/<id>/rent` | POST | 租用地块 | 是 |
| `/pic/land/<id>/build` | POST | 建造房屋 | 是 |

## 🤝 常见问题

**Q: 忘记管理员密码怎么办？**
A: 删除 `data/` 目录下的用户数据，重启应用即可重置。

**Q: 如何备份数据？**
A: 系统会自动备份到 `backups/` 目录。管理员也可以在"管理中心 → 数据备份"手动备份。

**Q: 如何开启小镇地图？**
A: 编辑 `config.json`，将 `map_enabled` 设为 `true`。

**Q: 支持哪些图片格式？**
A: PNG、JPG/JPEG、GIF、BMP、WebP。

**Q: 支持哪些视频格式？**
A: MP4、AVI、MOV、WMV、FLV、MKV。上传后会自动转换为 Web 兼容格式。

**Q: 如何删除上传的内容？**
A: 管理员可以在"管理中心 → 内容审核"中审核和删除内容。

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- Flask - 轻量级 Python Web 框架
- PyInstaller - 跨平台打包工具
- imageio-ffmpeg - 视频处理库
- cryptography - Python 加密库

## 📞 联系方式

- GitHub: https://github.com/kongyixaing/picture
- 问题反馈: [Issues](https://github.com/kongyixaing/picture/issues)

## 📦 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解完整版本更新记录。

### 最新版本: v0.0.1

**发布日期**: 2026-08-08

**新增功能**:
- ✨ 图片分享和浏览
- ✨ 视频分享和在线播放
- ✨ 视频自动转码
- ✨ 即时通讯（私聊/群聊）
- ✨ 好友系统
- ✨ 内容审核
- ✨ 用户管理
- ✨ 小镇地图（可配置开关）
- ✨ 积分系统
- ✨ 房屋建造
- ✨ 自动数据备份
- ✨ 跨平台打包支持
