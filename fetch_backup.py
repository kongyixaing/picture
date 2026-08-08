import os
import sys
import json
import time
import shutil
import argparse
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: requests module not found. Please install it: pip install requests")
    sys.exit(1)


DEFAULT_CONFIG = {
    'server_url': 'http://localhost:5001',
    'token': '',
    'local_backup_dir': os.path.join(os.path.expanduser('~'), 'pic_backups'),
    'keep_backups': 4,
    'timeout': 300,
    'verify_ssl': False
}


def load_config(config_file):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                custom = json.load(f)
                config.update(custom)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
    return config


def save_config(config_file, config):
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {config_file}")
    except Exception as e:
        print(f"Error: Failed to save config: {e}")


def get_latest_backup(config):
    url = f"{config['server_url']}/pic/api/backup/latest"
    headers = {'X-Backup-Token': config['token']}
    try:
        response = requests.get(url, headers=headers, timeout=config['timeout'],
                                verify=config['verify_ssl'])
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("No backups available on server")
            return None
        elif response.status_code == 403:
            print("Error: Invalid backup token")
            return None
        else:
            print(f"Error: Server returned {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: Failed to connect to server: {e}")
        return None


def download_backup(config, backup_info):
    url = f"{config['server_url']}/pic/api/backup/download/{backup_info['filename']}"
    headers = {'X-Backup-Token': config['token']}
    local_path = os.path.join(config['local_backup_dir'], backup_info['filename'])

    if os.path.exists(local_path):
        local_size = os.path.getsize(local_path)
        if local_size == backup_info['size']:
            print(f"Local backup is already up-to-date: {backup_info['filename']}")
            return True

    os.makedirs(config['local_backup_dir'], exist_ok=True)

    print(f"Downloading backup: {backup_info['filename']} ({format_size(backup_info['size'])})")
    try:
        response = requests.get(url, headers=headers, timeout=config['timeout'],
                                verify=config['verify_ssl'], stream=True)
        if response.status_code != 200:
            print(f"Error: Download failed with status {response.status_code}")
            return False

        downloaded = 0
        with open(local_path + '.tmp', 'wb') as f:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (1024 * 1024) == 0:
                        print(f"  Downloaded: {format_size(downloaded)}")

        if os.path.exists(local_path):
            os.remove(local_path)
        os.rename(local_path + '.tmp', local_path)

        print(f"Download completed: {local_path}")
        return True
    except Exception as e:
        print(f"Error: Download failed: {e}")
        if os.path.exists(local_path + '.tmp'):
            try:
                os.remove(local_path + '.tmp')
            except Exception:
                pass
        return False


def clean_old_backups(config):
    if not os.path.exists(config['local_backup_dir']):
        return

    backups = []
    for fname in os.listdir(config['local_backup_dir']):
        if fname.endswith('.zip'):
            fpath = os.path.join(config['local_backup_dir'], fname)
            try:
                stat = os.stat(fpath)
                backups.append((fname, stat.st_mtime, fpath))
            except Exception:
                pass

    backups.sort(key=lambda x: x[1], reverse=True)

    if len(backups) > config['keep_backups']:
        to_delete = backups[config['keep_backups']:]
        print(f"\nCleaning old backups (keeping {config['keep_backups']} latest)...")
        for fname, mtime, fpath in to_delete:
            try:
                os.remove(fpath)
                print(f"  Deleted: {fname}")
            except Exception as e:
                print(f"  Failed to delete {fname}: {e}")


def format_size(size):
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    elif size < 1024 * 1024 * 1024:
        return f'{size / (1024 * 1024):.1f} MB'
    else:
        return f'{size / (1024 * 1024 * 1024):.2f} GB'


def main():
    parser = argparse.ArgumentParser(description='自动下载服务器备份到本机')
    parser.add_argument('--config', default='fetch_backup_config.json',
                        help='配置文件路径')
    parser.add_argument('--init', action='store_true',
                        help='初始化配置文件')
    parser.add_argument('--list', action='store_true',
                        help='列出服务器上的备份')
    args = parser.parse_args()

    config = load_config(args.config)

    if args.init:
        print("Initializing configuration file...")
        print("\n请编辑配置文件并填写以下信息：")
        print(f"  server_url: 服务器地址（如 http://your-server:5001）")
        print(f"  token: 从服务器 data/backup_token.txt 获取的备份API令牌")
        print(f"  local_backup_dir: 本机备份存放目录")
        save_config(args.config, config)
        return

    if not config['token']:
        print("Error: token is not set in config file")
        print("Please run with --init to create config file")
        return

    if args.list:
        url = f"{config['server_url']}/pic/api/backup/list"
        headers = {'X-Backup-Token': config['token']}
        try:
            response = requests.get(url, headers=headers, timeout=config['timeout'],
                                    verify=config['verify_ssl'])
            if response.status_code == 200:
                backups = response.json()
                print(f"Server backups ({len(backups)}):")
                for b in backups:
                    print(f"  {b['filename']} - {format_size(b['size'])} - {b['time_str']}")
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for latest backup...")
    backup_info = get_latest_backup(config)

    if backup_info:
        download_backup(config, backup_info)
        clean_old_backups(config)
    else:
        print("No backup to download")


if __name__ == '__main__':
    main()
