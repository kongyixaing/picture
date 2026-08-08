import sys
import traceback

print("Python version:", sys.version)
print()

try:
    print("Checking flask...")
    from flask import Flask
    print("Flask imported successfully")
except Exception as e:
    print("Flask import error:", e)
    traceback.print_exc()
    sys.exit(1)

print()

try:
    print("Checking imageio-ffmpeg...")
    import imageio_ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    print("imageio-ffmpeg available, ffmpeg at:", ffmpeg_path)
except Exception as e:
    print("imageio-ffmpeg import warning:", e)
    print("  Video conversion will be unavailable.")
    print("  To enable, run: pip install imageio-ffmpeg")
    print("  Or install ffmpeg system-wide and make sure it's on PATH.")

print()

try:
    print("Checking pic_models...")
    from pic_models import PicUser, Picture, UPLOAD_DIR
    print("pic_models imported successfully")
    print("UPLOAD_DIR:", UPLOAD_DIR)
except Exception as e:
    print("pic_models import error:", e)
    traceback.print_exc()
    sys.exit(1)

print()

try:
    print("Checking video_converter...")
    from video_converter import convert_to_h264, is_h264, probe_video, get_ffmpeg_path
    print("video_converter imported successfully")
    print("FFmpeg path:", get_ffmpeg_path())
except Exception as e:
    print("video_converter import error:", e)
    traceback.print_exc()
    sys.exit(1)

print()

try:
    print("Checking file_crypto...")
    import file_crypto
    file_crypto.init_crypto('.')
    if file_crypto.is_crypto_enabled():
        print("file_crypto imported successfully, encryption enabled")
    else:
        print("file_crypto imported, encryption disabled (cryptography library not available)")
except Exception as e:
    print("file_crypto import warning:", e)
    print("  File encryption will be unavailable.")
    print("  To enable, run: pip install cryptography")

print()

try:
    print("Checking pic_app...")
    import pic_app
    print("pic_app imported successfully")
    print("App is ready to run on port 5001")
except Exception as e:
    print("pic_app import error:", e)
    traceback.print_exc()
    sys.exit(1)

print()

try:
    print("Checking backup module...")
    import backup
    backup.init_backup('.')
    print("backup module loaded successfully")
    print("Backup directory:", backup.BACKUP_DIR)
    print("Auto backup interval:", backup.AUTO_BACKUP_INTERVAL_DAYS, "days")
except Exception as e:
    print("backup module warning:", e)
    print("  Auto backup feature will be unavailable.")

print()
print("All checks passed!")
