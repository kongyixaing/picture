# Picture & Videos 图片视频分享社区

一个基于 Python Flask 的图片和视频分享与社交平台，支持用户上传、浏览、评论、好友、群聊等功能，并内置一个像素风格的小镇地图，用户可以在小镇上租地、建房，打造自己的数字家园。

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

### 小镇地图（可通过 config.json 开启）
- 🏛️ **中心广场** - 像素风格的小镇中心
- 🏠 **租地建房** - 用户可以租用地块并建造自己的房屋
- 🌍 **世界地图** - 在地图上自由探索，访问其他用户的房屋
- ⭐ **积分系统** - 积分可用于租地、建房
- 🔑 **预留用地** - 功能建筑预留位置

## 🛠️ 技术栈

- **后端**: Python 3.14 + Flask
- **前端**: 原生 HTML5 + CSS3 + JavaScript (Canvas API)
- **数据库**: JSON 文件存储（轻量级）
- **打包**: PyInstaller
- **加密**: cryptography (数据加密)
- **视频处理**: imageio-ffmpeg

## 📁 项目结构

```
picture/
├── pic_app.py          # 主应用入口
├── pic_models.py       # 数据模型
├── land_system.py      # 小镇地图系统
├── world_map.py        # 世界地图/玩家位置
├── backup.py           # 备份系统
├── fetch_backup.py     # 备份定时任务
├── file_crypto.py      # 文件加密
├── video_converter.py  # 视频转码
├── pic_app.spec        # PyInstaller 配置
├── installer.iss       # Inno Setup 安装器配置
├── config.json         # 功能开关配置
├── templates/          # HTML 模板
│   ├── pic_base.html       # 基础布局
│   ├── pic_index.html      # 首页
│   ├── pic_world.html      # 小镇地图
│   ├── pic_house.html      # 房屋详情
│   └── ...
├── static/             # 静态资源
│   ├── pic_style.css       # 样式表
│   └── uploads/            # 用户上传文件
└── build_exe.bat       # 打包脚本
```

## 🚀 快速开始

### 开发模式运行

```bash
# 安装依赖
pip install flask cryptography imageio-ffmpeg

# 运行应用
python pic_app.py
```

访问 http://localhost:5001

### 打包成可执行文件

```bash
# 运行打包脚本
build_exe.bat

# 输出在 dist/PictureAndVideos/
```

### 创建安装程序

```bash
# 运行安装包打包脚本
build_installer.bat
```

## ⚙️ 配置说明

### 功能开关

编辑 `config.json` 控制功能开关：

```json
{
    "map_enabled": true
}
```

- `map_enabled`: 开启/关闭小镇地图功能（默认 `false`）

### 管理员账户

首次启动后自动创建管理员账户：
- 用户名: `admin`
- 默认密码: `admin123`

请登录后立即修改密码。

## 📝 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/pic` | GET | 首页 |
| `/pic/world` | GET | 小镇地图（需登录） |
| `/pic/login` | GET/POST | 登录 |
| `/pic/logout` | GET | 登出 |
| `/pic/upload` | GET/POST | 上传图片/视频 |
| `/pic/profile` | GET | 个人资料 |
| `/pic/groups` | GET | 群聊列表 |
| `/pic/friends` | GET | 好友列表 |
| `/pic/admin/users` | GET | 用户管理（管理员） |
| `/pic/admin/review` | GET | 内容审核（管理员） |
| `/pic/land/<id>/rent` | POST | 租用地块 |
| `/pic/land/<id>/build` | POST | 建造房屋 |

## 📄 许可证

本项目仅供学习和个人使用。

## 📦 版本历史

### v0.0.1 (2026-08-08)
- 🎉 首个正式版本
- ✅ 图片和视频分享功能
- ✅ 即时通讯系统（私聊/群聊）
- ✅ 好友系统
- ✅ 内容审核和用户管理
- ✅ 小镇地图功能（可配置开关）
- ✅ 积分系统和房屋建造
- ✅ 自动数据备份
- ✅ 视频自动转码
