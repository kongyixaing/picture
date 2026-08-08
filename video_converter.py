import os
import sys
import subprocess
import threading
import time
import shutil


def _get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def _get_ffmpeg():
    if getattr(sys, 'frozen', False):
        try:
            bundled = _get_resource_path(os.path.join('imageio_ffmpeg', 'binaries'))
            for f in os.listdir(bundled):
                if f.startswith('ffmpeg') and (f.endswith('.exe') or f == 'ffmpeg'):
                    return os.path.join(bundled, f)
        except Exception:
            pass

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        return system_ffmpeg

    return None


FFMPEG_PATH = _get_ffmpeg()
FFMPEG_AVAILABLE = FFMPEG_PATH is not None

CONVERT_DIR = 'static/converted'
_convert_dir_initialized = False


def init_convert_dir(base_dir):
    global CONVERT_DIR, _convert_dir_initialized
    CONVERT_DIR = os.path.join(base_dir, 'static', 'converted')
    os.makedirs(CONVERT_DIR, exist_ok=True)
    _convert_dir_initialized = True


_convert_tasks = {}


def get_ffmpeg_path():
    return FFMPEG_PATH


def is_ffmpeg_available():
    return FFMPEG_AVAILABLE


def probe_video(input_path):
    if not FFMPEG_AVAILABLE:
        return {}
    cmd = [
        FFMPEG_PATH, '-i', input_path, '-hide_banner'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stderr
        
        info = {}
        
        import re
        codec_match = re.search(r'Video:\s+(\S+)', output)
        if codec_match:
            info['codec_name'] = codec_match.group(1)
        
        res_match = re.search(r'(\d{2,5})x(\d{2,5})', output)
        if res_match:
            info['width'] = int(res_match.group(1))
            info['height'] = int(res_match.group(2))
        
        dur_match = re.search(r'Duration:\s+(\d+):(\d+):(\d+\.\d+)', output)
        if dur_match:
            h = int(dur_match.group(1))
            m = int(dur_match.group(2))
            s = float(dur_match.group(3))
            info['duration'] = str(h * 3600 + m * 60 + s)
        
        bitrate_match = re.search(r'bitrate:\s+(\d+)\s+kb/s', output)
        if bitrate_match:
            info['bit_rate'] = str(int(bitrate_match.group(1)) * 1000)
        
        return info
    except Exception:
        pass
    return {}


def is_h264(input_path):
    info = probe_video(input_path)
    return info.get('codec_name') == 'h264'


def convert_to_h264(input_path, output_path=None, crf=23, preset='medium', progress_callback=None):
    if not FFMPEG_AVAILABLE:
        return False, 'FFmpeg 不可用，请安装 imageio-ffmpeg 或系统 ffmpeg'
    if not os.path.exists(input_path):
        return False, '输入文件不存在'

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f'{base}_h264.mp4'

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    cmd = [
        FFMPEG_PATH, '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', preset,
        '-crf', str(crf),
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        total_duration = None
        info = probe_video(input_path)
        if info and info.get('duration'):
            total_duration = float(info['duration'])

        for line in process.stdout:
            if progress_callback and total_duration:
                if 'time=' in line:
                    try:
                        time_str = line.split('time=')[1].split(' ')[0]
                        h, m, s = time_str.split(':')
                        current = int(h) * 3600 + int(m) * 60 + float(s)
                        progress = min(100, int(current / total_duration * 100))
                        progress_callback(progress)
                    except Exception:
                        pass

        process.wait()

        if process.returncode == 0 and os.path.exists(output_path):
            if progress_callback:
                progress_callback(100)
            return True, output_path
        else:
            return False, f'转码失败，退出码: {process.returncode}'

    except Exception as e:
        return False, str(e)


def start_convert_task(task_id, input_path, output_path=None, crf=23, preset='medium'):
    task = {
        'id': task_id,
        'status': 'processing',
        'progress': 0,
        'input_path': input_path,
        'output_path': output_path,
        'result': None,
        'error': None,
        'start_time': time.time()
    }
    _convert_tasks[task_id] = task

    def progress_callback(progress):
        task['progress'] = progress

    def run():
        success, result = convert_to_h264(
            input_path, output_path, crf, preset,
            progress_callback=progress_callback
        )
        if success:
            task['status'] = 'completed'
            task['output_path'] = result
            task['result'] = result
        else:
            task['status'] = 'failed'
            task['error'] = result
        task['end_time'] = time.time()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return task


def get_task_status(task_id):
    return _convert_tasks.get(task_id)


def cleanup_old_tasks(max_age=3600):
    now = time.time()
    old_ids = []
    for tid, task in _convert_tasks.items():
        if task.get('end_time') and now - task['end_time'] > max_age:
            old_ids.append(tid)
    for tid in old_ids:
        del _convert_tasks[tid]


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('用法: python video_converter.py <input_file> [output_file] [crf] [preset]')
        print('示例: python video_converter.py input.mp4 output_h264.mp4 23 medium')
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    crf = int(sys.argv[3]) if len(sys.argv) > 3 else 23
    preset = sys.argv[4] if len(sys.argv) > 4 else 'medium'

    print(f'FFmpeg 路径: {FFMPEG_PATH}')
    print(f'输入文件: {input_file}')

    if is_h264(input_file):
        print('视频已经是 H.264 编码')
    else:
        print('视频不是 H.264 编码，开始转码...')

    def show_progress(p):
        print(f'\r转码进度: {p}%', end='', flush=True)

    success, result = convert_to_h264(input_file, output_file, crf, preset, show_progress)
    print()

    if success:
        print(f'转码成功! 输出文件: {result}')
    else:
        print(f'转码失败: {result}')
