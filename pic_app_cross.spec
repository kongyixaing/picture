# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import imageio_ffmpeg

block_cipher = None

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)

datas = [
    ('templates', 'templates'),
    ('static/pic_style.css', 'static'),
    (ffmpeg_dir, os.path.join('imageio_ffmpeg', 'binaries')),
    ('world_map.py', '.'),
    ('land_system.py', '.'),
    ('backup.py', '.'),
    ('fetch_backup.py', '.'),
    ('file_crypto.py', '.'),
    ('video_converter.py', '.'),
    ('pic_models.py', '.'),
]

a = Analysis(
    ['pic_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'imageio_ffmpeg',
        'cryptography',
        'cryptography.fernet',
        'cffi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PictureAndVideos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PictureAndVideos',
)
