import os
import json
import time

LAND_DIR = 'land'
_base_dir = None

PLOT_SIZE = 80
STREET = 40
CELL = PLOT_SIZE + STREET

GRID_COLS = 19
GRID_ROWS = 15

MAP_WIDTH = GRID_COLS * CELL
MAP_HEIGHT = GRID_ROWS * CELL

CENTER_COL = 9
CENTER_ROW = 7

FUNCTIONAL_BUILDINGS = [
    {'name': '画廊馆', 'icon': '🎨', 'route': '/pic/index', 'color': '#87CEEB', 'desc': '浏览图片和视频'},
    {'name': '聊天茶馆', 'icon': '💬', 'route': '/pic/groups', 'color': '#98FB98', 'desc': '群聊和私聊'},
    {'name': '上传工坊', 'icon': '📷', 'route': '/pic/upload', 'color': '#DDA0DD', 'desc': '上传图片和视频'},
    {'name': '好友驿站', 'icon': '🌸', 'route': '/pic/friends', 'color': '#90EE90', 'desc': '好友管理'},
    {'name': '个人小屋', 'icon': '🏠', 'route': '/pic/profile', 'color': '#FFDAB9', 'desc': '个人中心'},
    {'name': '镇公所', 'icon': '⚙️', 'route': '/pic/admin/review', 'color': '#FFB6C1', 'desc': '管理中心'},
]

RENT_PERIOD = 7 * 24 * 3600
BUILD_COST = 10

_layout_cache = None


def init_land_dir(base_dir):
    global _base_dir, LAND_DIR
    _base_dir = base_dir
    LAND_DIR = os.path.join(base_dir, 'land')
    os.makedirs(LAND_DIR, exist_ok=True)


def _read(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.loads(content) if content.strip() else {}
    except Exception:
        return {}


def _write(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _state_path(land_id):
    return os.path.join(LAND_DIR, f'{land_id}.txt')


def _compute_price(col, row):
    dist = max(abs(col - CENTER_COL), abs(row - CENTER_ROW))
    base_price = max(3, 15 - dist)
    return base_price


def _generate_layout():
    layout = []
    land_id = 1

    # Plaza area (4x4 grid cells in center) - not added as land, just empty space
    plaza_rows = [6, 7, 8, 9]
    plaza_cols = [7, 8, 9, 10]
    plaza_positions = set((c, r) for r in plaza_rows for c in plaza_cols)

    # Reserved plots for future features (around plaza) - only keep corners to allow access
    reserved_positions = set()
    reserved_locations = [
        (6, 5), (11, 5),
        (6, 10), (11, 10),
        (5, 6), (5, 9),
        (12, 6), (12, 9),
    ]
    for (col, row) in reserved_locations[:12]:
        reserved_positions.add((col, row))
        layout.append({
            'id': land_id,
            'type': 'reserved',
            'name': '预留用地',
            'icon': '🚧',
            'color': '#9E9E9E',
            'desc': '未开发功能预留',
            'x': col * CELL + STREET,
            'y': row * CELL + STREET,
            'w': PLOT_SIZE,
            'h': PLOT_SIZE,
            'price': 0,
        })
        land_id += 1

    # Functional buildings in a ring around plaza
    func_positions = [
        (3, 3),    # NW
        (15, 3),   # NE
        (3, 11),   # SW
        (15, 11),  # SE
        (0, 7),    # W
        (18, 7),   # E
    ]
    for i, (col, row) in enumerate(func_positions):
        info = FUNCTIONAL_BUILDINGS[i]
        layout.append({
            'id': land_id,
            'type': 'functional',
            'name': info['name'],
            'icon': info['icon'],
            'route': info['route'],
            'color': info['color'],
            'desc': info['desc'],
            'x': col * CELL + STREET,
            'y': row * CELL + STREET,
            'w': PLOT_SIZE,
            'h': PLOT_SIZE,
            'price': 0,
        })
        land_id += 1

    # Rentable plots fill remaining spaces
    occupied = plaza_positions | reserved_positions | set(func_positions)
    for row in range(0, GRID_ROWS):
        for col in range(0, GRID_COLS):
            if (col, row) in occupied:
                continue
            price = _compute_price(col, row)
            layout.append({
                'id': land_id,
                'type': 'rentable',
                'name': '空地',
                'icon': '🌱',
                'color': '#8FBC8F',
                'desc': f'可租用空地（租金 {price} 积分/周）',
                'x': col * CELL + STREET,
                'y': row * CELL + STREET,
                'w': PLOT_SIZE,
                'h': PLOT_SIZE,
                'price': price,
            })
            land_id += 1

    # Add plaza area as a single large area covering full grid cells
    layout.append({
        'id': land_id,
        'type': 'plaza',
        'name': '中心广场',
        'icon': '🏛️',
        'color': '#d4c060',
        'desc': '小镇中心广场',
        'x': plaza_cols[0] * CELL,
        'y': plaza_rows[0] * CELL,
        'w': len(plaza_cols) * CELL,
        'h': len(plaza_rows) * CELL,
        'price': 0,
    })

    return layout


def get_layout():
    global _layout_cache
    if _layout_cache is None:
        _layout_cache = _generate_layout()
    return _layout_cache


def _check_expired(state):
    if not state:
        return state
    if state.get('expiry_time', 0) and time.time() > state.get('expiry_time', 0):
        return {}
    return state


def get_land(land_id):
    for plot in get_layout():
        if plot['id'] == land_id:
            state = _check_expired(_read(_state_path(land_id)))
            merged = dict(plot)
            merged.update(state)
            merged['is_vacant'] = not bool(state)
            return merged
    return None


def get_all_lands():
    layout = get_layout()
    result = []
    for plot in layout:
        state = _check_expired(_read(_state_path(plot['id'])))
        merged = dict(plot)
        merged.update(state)
        merged['is_vacant'] = not bool(state)
        result.append(merged)
    return result


def get_rentable_count():
    return sum(1 for p in get_layout() if p['type'] == 'rentable')


def get_reserved_count():
    return sum(1 for p in get_layout() if p['type'] == 'reserved')


def rent_land(land_id, uid, username):
    land = get_land(land_id)
    if not land or land['type'] != 'rentable':
        return False, '该地块不可租用'
    if not land['is_vacant']:
        return False, '该地块已被租用'
    if get_my_land(uid):
        return False, '您已有一块地，无法再租'
    state = {
        'owner_uid': uid,
        'owner_name': username,
        'rent_time': time.time(),
        'expiry_time': time.time() + RENT_PERIOD,
        'house_level': 0,
        'house_name': '',
        'rent_price': land.get('price', 5),
    }
    _write(_state_path(land_id), state)
    return True, '租地成功'


def build_house(land_id, uid, username, house_name=''):
    land = get_land(land_id)
    if not land:
        return False, '地块不存在'
    state = _read(_state_path(land_id))
    if not state or state.get('owner_uid') != uid:
        return False, '您不拥有该地块'
    state = _check_expired(state)
    if not state:
        return False, '租约已过期，请先续租'
    if state.get('house_level', 0) >= 1:
        return False, '已建有房屋'
    state['house_level'] = 1
    state['house_name'] = house_name or (username + '的小屋')
    _write(_state_path(land_id), state)
    return True, '建房成功'


def renew_rent(land_id, uid):
    land = get_land(land_id)
    if not land:
        return False, '地块不存在'
    state = _read(_state_path(land_id))
    if not state or state.get('owner_uid') != uid:
        return False, '您不拥有该地块'
    base = max(state.get('expiry_time', time.time()), time.time())
    state['expiry_time'] = base + RENT_PERIOD
    state['last_renew'] = time.time()
    _write(_state_path(land_id), state)
    return True, '续租成功'


def get_my_land(uid):
    for plot in get_layout():
        state = _check_expired(_read(_state_path(plot['id'])))
        if state and state.get('owner_uid') == uid:
            merged = dict(plot)
            merged.update(state)
            merged['is_vacant'] = False
            return merged
    return None


def get_land_at(x, y):
    for plot in get_layout():
        if (plot['x'] <= x <= plot['x'] + plot['w'] and
                plot['y'] <= y <= plot['y'] + plot['h']):
            return get_land(plot['id'])
    return None


def cleanup_expired():
    removed = 0
    for plot in get_layout():
        if plot['type'] != 'rentable':
            continue
        state = _read(_state_path(plot['id']))
        if state and state.get('expiry_time', 0) and time.time() > state.get('expiry_time', 0):
            os.remove(_state_path(plot['id']))
            removed += 1
    return removed
