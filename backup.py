import os
import zipfile
import time
import threading
import shutil
from datetime import datetime, timedelta

LOG_FILE = None


def _log(message):
    if LOG_FILE is None:
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {message}\n')
    except Exception:
        pass


BACKUP_DIR = None
_base_dir = None
_last_backup_time = 0
_backup_thread = None
_running = False
AUTO_BACKUP_INTERVAL_DAYS = 7


def init_backup(base_dir):
    global BACKUP_DIR, _base_dir, LOG_FILE
    _base_dir = base_dir
    BACKUP_DIR = os.path.join(base_dir, 'backups')
    LOG_FILE = os.path.join(BACKUP_DIR, 'backup.log')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    _load_last_backup_time()
    _log('Backup system initialized')
    return True


def _load_last_backup_time():
    global _last_backup_time
    info_file = os.path.join(BACKUP_DIR, '.last_backup')
    if os.path.exists(info_file):
        try:
            with open(info_file, 'r') as f:
                _last_backup_time = float(f.read().strip())
        except Exception:
            _last_backup_time = 0


def _save_last_backup_time(ts):
    global _last_backup_time
    _last_backup_time = ts
    info_file = os.path.join(BACKUP_DIR, '.last_backup')
    try:
        with open(info_file, 'w') as f:
            f.write(str(ts))
    except Exception:
        pass


def get_last_backup_time():
    return _last_backup_time


def _should_auto_backup():
    if _last_backup_time == 0:
        return True
    elapsed = time.time() - _last_backup_time
    return elapsed >= AUTO_BACKUP_INTERVAL_DAYS * 24 * 3600


def create_backup(backup_name=None):
    if not _base_dir:
        return None, '备份系统未初始化'

    if backup_name is None:
        backup_name = f'backup_{time.strftime("%Y%m%d_%H%M%S")}'

    backup_filename = f'{backup_name}.zip'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    dirs_to_backup = [
        'user',
        'picture',
        'comments',
        'BanRecord',
        'groupchat',
        'videos',
        'data',
        'logs',
    ]

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dir_name in dirs_to_backup:
                dir_path = os.path.join(_base_dir, dir_name)
                if os.path.exists(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, _base_dir)
                            zf.write(file_path, arcname)

            uploads_path = os.path.join(_base_dir, 'static', 'uploads')
            if os.path.exists(uploads_path):
                for root, dirs, files in os.walk(uploads_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, _base_dir)
                        zf.write(file_path, arcname)

        ts = time.time()
        _save_last_backup_time(ts)

        size = os.path.getsize(backup_path)
        _log(f'Backup created: {backup_filename}, size: {_format_size(size)}')
        return {
            'filename': backup_filename,
            'path': backup_path,
            'size': size,
            'time': ts,
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
        }, None
    except Exception as e:
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass
        _log(f'Backup failed: {str(e)}')
        return None, str(e)


def list_backups():
    if not BACKUP_DIR or not os.path.exists(BACKUP_DIR):
        return []
    backups = []
    for fname in os.listdir(BACKUP_DIR):
        if fname.endswith('.zip'):
            fpath = os.path.join(BACKUP_DIR, fname)
            try:
                stat = os.stat(fpath)
                backups.append({
                    'filename': fname,
                    'size': stat.st_size,
                    'time': stat.st_mtime,
                    'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                })
            except Exception:
                pass
    backups.sort(key=lambda x: x['time'], reverse=True)
    return backups


def delete_backup(filename):
    if not BACKUP_DIR:
        return False
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    if not filename.endswith('.zip'):
        return False
    fpath = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(fpath) and os.path.isfile(fpath):
        try:
            os.remove(fpath)
            return True
        except Exception:
            return False
    return False


def get_backup_path(filename):
    if not BACKUP_DIR:
        return None
    if '..' in filename or '/' in filename or '\\' in filename:
        return None
    if not filename.endswith('.zip'):
        return None
    fpath = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(fpath) and os.path.isfile(fpath):
        return fpath
    return None


def _auto_backup_loop():
    global _running
    _running = True
    _log('Auto backup thread started')
    while _running:
        try:
            if _should_auto_backup():
                _log('Performing weekly auto backup...')
                result, err = create_backup()
                if result:
                    _log(f'Auto backup completed: {result["filename"]} ({_format_size(result["size"])})')
                    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Auto backup completed: {result["filename"]}')
                else:
                    _log(f'Auto backup failed: {err}')
                    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Auto backup failed: {err}')
        except Exception as e:
            _log(f'Auto backup error: {str(e)}')
            print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Auto backup error: {e}')

        for _ in range(3600):
            if not _running:
                break
            time.sleep(1)


def start_auto_backup():
    global _backup_thread
    if _backup_thread and _backup_thread.is_alive():
        return False
    _backup_thread = threading.Thread(target=_auto_backup_loop, daemon=True)
    _backup_thread.start()
    return True


def stop_auto_backup():
    global _running
    _running = False


def _format_size(size):
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    elif size < 1024 * 1024 * 1024:
        return f'{size / (1024 * 1024):.1f} MB'
    else:
        return f'{size / (1024 * 1024 * 1024):.2f} GB'


def format_size(size):
    return _format_size(size)
