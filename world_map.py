import time
import threading

MAP_WIDTH = 2000
MAP_HEIGHT = 1500

TILE_SIZE = 40


def set_map_bounds(width, height):
    global MAP_WIDTH, MAP_HEIGHT
    MAP_WIDTH = width
    MAP_HEIGHT = height

ZONES = {
    'gallery': {
        'name': '画廊区',
        'x': 800, 'y': 400,
        'width': 400, 'height': 300,
        'color': '#87CEEB',
        'route': '/pic/index',
        'description': '浏览图片和视频',
        'icon': '🎨'
    },
    'chat': {
        'name': '聊天广场',
        'x': 300, 'y': 700,
        'width': 350, 'height': 250,
        'color': '#98FB98',
        'route': '/pic/groups',
        'description': '群聊和私聊',
        'icon': '💬'
    },
    'profile': {
        'name': '个人小屋',
        'x': 1500, 'y': 200,
        'width': 300, 'height': 250,
        'color': '#FFDAB9',
        'route': '/pic/profile',
        'description': '个人中心',
        'icon': '🏠'
    },
    'upload': {
        'name': '创作工坊',
        'x': 1400, 'y': 1000,
        'width': 350, 'height': 250,
        'color': '#DDA0DD',
        'route': '/pic/upload',
        'description': '上传图片和视频',
        'icon': '📷'
    },
    'admin': {
        'name': '管理中心',
        'x': 100, 'y': 100,
        'width': 250, 'height': 200,
        'color': '#FFB6C1',
        'route': '/pic/admin/review',
        'description': '管理员专用',
        'icon': '⚙️'
    },
    'friends': {
        'name': '好友花园',
        'x': 500, 'y': 200,
        'width': 280, 'height': 250,
        'color': '#90EE90',
        'route': '/pic/friends',
        'description': '好友管理',
        'icon': '🌸'
    }
}

PLAYER_COLORS = [
    '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
    '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA',
    '#FF9F1C', '#2EC4B6', '#E71D36', '#001219'
]

_online_players = {}
_lock = threading.Lock()


def get_player_color(uid):
    idx = hash(uid) % len(PLAYER_COLORS)
    return PLAYER_COLORS[idx]


def update_player_position(uid, x, y):
    with _lock:
        _online_players[uid] = {
            'uid': uid,
            'x': x,
            'y': y,
            'timestamp': time.time(),
            'color': get_player_color(uid)
        }


def get_player_position(uid):
    with _lock:
        return _online_players.get(uid)


def get_all_players():
    with _lock:
        now = time.time()
        players = []
        for uid, data in list(_online_players.items()):
            if now - data['timestamp'] > 300:
                del _online_players[uid]
            else:
                players.append(data)
        return players


def get_zone_at(x, y):
    for zone_id, zone in ZONES.items():
        if (zone['x'] <= x <= zone['x'] + zone['width'] and
                zone['y'] <= y <= zone['y'] + zone['height']):
            return zone_id, zone
    return None, None


def get_zone_info(zone_id):
    return ZONES.get(zone_id)


def get_map_bounds():
    return MAP_WIDTH, MAP_HEIGHT


def cleanup_offline_players():
    with _lock:
        now = time.time()
        to_remove = []
        for uid, data in _online_players.items():
            if now - data['timestamp'] > 300:
                to_remove.append(uid)
        for uid in to_remove:
            del _online_players[uid]
    return len(to_remove)


def get_online_count():
    with _lock:
        now = time.time()
        count = 0
        for data in _online_players.values():
            if now - data['timestamp'] <= 300:
                count += 1
        return count
