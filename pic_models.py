import os
import json
import hashlib
import time
import uuid
from datetime import datetime

USER_DIR = 'user'
PICTURE_DIR = 'picture'
COMMENTS_DIR = 'comments'
BAN_RECORD_DIR = 'BanRecord'
GROUPCHAT_DIR = 'groupchat'
VIDEO_DIR = 'videos'
APPLICATION_DIR = 'data/applications'
UPLOAD_DIR = 'static/uploads'
LOG_DIR = 'logs'

_base_dir = None
BLOCKED_IPS_FILE = 'data/blocked_ips.txt'


def init_data_dirs(base_dir):
    global _base_dir, USER_DIR, PICTURE_DIR, COMMENTS_DIR, BAN_RECORD_DIR
    global GROUPCHAT_DIR, VIDEO_DIR, APPLICATION_DIR, UPLOAD_DIR, BLOCKED_IPS_FILE, LOG_DIR
    _base_dir = base_dir
    USER_DIR = os.path.join(base_dir, 'user')
    PICTURE_DIR = os.path.join(base_dir, 'picture')
    COMMENTS_DIR = os.path.join(base_dir, 'comments')
    BAN_RECORD_DIR = os.path.join(base_dir, 'BanRecord')
    GROUPCHAT_DIR = os.path.join(base_dir, 'groupchat')
    VIDEO_DIR = os.path.join(base_dir, 'videos')
    APPLICATION_DIR = os.path.join(base_dir, 'data', 'applications')
    UPLOAD_DIR = os.path.join(base_dir, 'static', 'uploads')
    BLOCKED_IPS_FILE = os.path.join(base_dir, 'data', 'blocked_ips.txt')
    LOG_DIR = os.path.join(base_dir, 'logs')
    os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
    for d in [USER_DIR, PICTURE_DIR, COMMENTS_DIR, BAN_RECORD_DIR,
              GROUPCHAT_DIR, VIDEO_DIR, APPLICATION_DIR, UPLOAD_DIR, LOG_DIR]:
        os.makedirs(d, exist_ok=True)
    _init_grant_record_dir(base_dir)
    _init_red_packet_dir(base_dir)


def _read_txt_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.loads(content) if content.strip() else {}
    except:
        return {}


def _write_txt_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _safe_listdir(directory):
    if not os.path.exists(directory):
        return []
    try:
        return os.listdir(directory)
    except:
        return []


def _get_next_id(directory, prefix=''):
    max_id = 0
    if not os.path.exists(directory):
        return 1
    for fname in _safe_listdir(directory):
        if fname.endswith('.txt'):
            try:
                name = fname[:-4]
                if prefix:
                    name = name.replace(prefix, '')
                num = int(name)
                if num > max_id:
                    max_id = num
            except:
                pass
    return max_id + 1


# ==================== User Model ====================
class PicUser:
    @staticmethod
    def generate_uid():
        return 'U' + str(int(time.time() * 1000)) + str(uuid.uuid4().hex[:6]).upper()

    @staticmethod
    def create(username, password, role='user', email='', phone=''):
        if PicUser.get_by_username(username):
            return None
        uid = PicUser.generate_uid()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_data = {
            'uid': uid,
            'username': username,
            'password': password_hash,
            'role': role,
            'email': email,
            'phone': phone,
            'status': 'active',
            'ban_end_time': 0,
            'created_at': time.time(),
            'points': 0,
            'uploaded_pictures': 0,
            'uploaded_videos': 0,
            'friends': [],
            'friend_requests': [],
            'groups': [],
            'private_chats': {},
            'ban_history': [],
            'points_history': []
        }
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user_data)
        return uid

    @staticmethod
    def get_by_uid(uid):
        path = os.path.join(USER_DIR, f'{uid}.txt')
        data = _read_txt_file(path)
        return data if data else None

    @staticmethod
    def get_by_username(username):
        for fname in _safe_listdir(USER_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(USER_DIR, fname))
                if data.get('username') == username:
                    return data
        return None

    @staticmethod
    def authenticate(identifier, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for fname in _safe_listdir(USER_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(USER_DIR, fname))
                if not data:
                    continue
                if data.get('status') == 'banned' and data.get('ban_end_time', 0) > time.time():
                    continue
                username = data.get('username', '')
                email = data.get('email', '')
                phone = data.get('phone', '')
                if (username == identifier or email == identifier or phone == identifier) \
                        and data.get('password') == password_hash:
                    return data
        return None

    @staticmethod
    def update(uid, **kwargs):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        user.update(kwargs)
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def delete(uid):
        path = os.path.join(USER_DIR, f'{uid}.txt')
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    @staticmethod
    def get_all():
        users = []
        for fname in _safe_listdir(USER_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(USER_DIR, fname))
                if data:
                    users.append(data)
        return users

    @staticmethod
    def change_password(uid, old_password, new_password):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if user.get('password') != old_hash:
            return False
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user['password'] = new_hash
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def ban_user(uid, minutes, reason, applicant='admin'):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        ban_end = time.time() + minutes * 60
        user['status'] = 'banned'
        user['ban_end_time'] = ban_end
        ban_record = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'user': user.get('username'),
            'uid': uid,
            'reason': reason,
            'applicant': applicant,
            'duration_minutes': minutes
        }
        user['ban_history'].append(ban_record)
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)

        ban_id = _get_next_id(BAN_RECORD_DIR)
        ban_record['ban_id'] = ban_id
        _write_txt_file(os.path.join(BAN_RECORD_DIR, f'{ban_id}.txt'), ban_record)

        return True

    @staticmethod
    def unban_user(uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        user['status'] = 'active'
        user['ban_end_time'] = 0
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def get_points(uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return 0
        return user.get('points', 0)

    @staticmethod
    def add_points(uid, amount, reason='', operator=''):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        if amount < 0:
            return False
        user['points'] = user.get('points', 0) + amount
        record = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'type': 'add',
            'amount': amount,
            'reason': reason,
            'operator': operator,
            'balance_after': user['points']
        }
        user.setdefault('points_history', []).append(record)
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def deduct_points(uid, amount, reason=''):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        if amount < 0:
            return False
        current = user.get('points', 0)
        if current < amount:
            return False
        user['points'] = current - amount
        record = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'type': 'deduct',
            'amount': amount,
            'reason': reason,
            'balance_after': user['points']
        }
        user.setdefault('points_history', []).append(record)
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def transfer_points(from_uid, to_uid, amount, reason=''):
        if amount <= 0:
            return False
        from_user = PicUser.get_by_uid(from_uid)
        to_user = PicUser.get_by_uid(to_uid)
        if not from_user or not to_user:
            return False
        if from_user.get('points', 0) < amount:
            return False
        from_user['points'] = from_user.get('points', 0) - amount
        to_user['points'] = to_user.get('points', 0) + amount
        from_record = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'type': 'transfer_out',
            'amount': amount,
            'reason': reason,
            'counterparty': to_user.get('username', ''),
            'balance_after': from_user['points']
        }
        to_record = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'type': 'transfer_in',
            'amount': amount,
            'reason': reason,
            'counterparty': from_user.get('username', ''),
            'balance_after': to_user['points']
        }
        from_user.setdefault('points_history', []).append(from_record)
        to_user.setdefault('points_history', []).append(to_record)
        _write_txt_file(os.path.join(USER_DIR, f'{from_uid}.txt'), from_user)
        _write_txt_file(os.path.join(USER_DIR, f'{to_uid}.txt'), to_user)
        return True

    @staticmethod
    def get_points_history(uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return []
        history = user.get('points_history', [])
        history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return history

    @staticmethod
    def is_banned(uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        if user.get('status') == 'banned':
            if user.get('ban_end_time', 0) > time.time():
                return True
            else:
                PicUser.unban_user(uid)
                return False
        return False

    @staticmethod
    def send_friend_request(from_uid, to_uid):
        from_user = PicUser.get_by_uid(from_uid)
        to_user = PicUser.get_by_uid(to_uid)
        if not from_user or not to_user:
            return False
        if from_uid in [f.get('uid') for f in to_user.get('friends', [])]:
            return False
        if from_uid in [r.get('from_uid') for r in to_user.get('friend_requests', [])]:
            return False
        request = {
            'from_uid': from_uid,
            'from_username': from_user.get('username'),
            'timestamp': time.time()
        }
        to_user.setdefault('friend_requests', []).append(request)
        _write_txt_file(os.path.join(USER_DIR, f'{to_uid}.txt'), to_user)
        return True

    @staticmethod
    def accept_friend_request(uid, from_uid):
        user = PicUser.get_by_uid(uid)
        from_user = PicUser.get_by_uid(from_uid)
        if not user or not from_user:
            return False
        requests = user.get('friend_requests', [])
        new_requests = [r for r in requests if r.get('from_uid') != from_uid]
        user['friend_requests'] = new_requests

        friend_info = {'uid': from_uid, 'username': from_user.get('username')}
        if from_uid not in [f.get('uid') for f in user.get('friends', [])]:
            user.setdefault('friends', []).append(friend_info)
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)

        my_info = {'uid': uid, 'username': user.get('username')}
        if uid not in [f.get('uid') for f in from_user.get('friends', [])]:
            from_user.setdefault('friends', []).append(my_info)
        _write_txt_file(os.path.join(USER_DIR, f'{from_uid}.txt'), from_user)
        return True

    @staticmethod
    def reject_friend_request(uid, from_uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        user['friend_requests'] = [r for r in user.get('friend_requests', [])
                                    if r.get('from_uid') != from_uid]
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        return True

    @staticmethod
    def remove_friend(uid, friend_uid):
        user = PicUser.get_by_uid(uid)
        friend_user = PicUser.get_by_uid(friend_uid)
        if not user or not friend_user:
            return False
        user['friends'] = [f for f in user.get('friends', []) if f.get('uid') != friend_uid]
        friend_user['friends'] = [f for f in friend_user.get('friends', []) if f.get('uid') != uid]
        _write_txt_file(os.path.join(USER_DIR, f'{uid}.txt'), user)
        _write_txt_file(os.path.join(USER_DIR, f'{friend_uid}.txt'), friend_user)
        return True


# ==================== Admin Points Grant Record ====================
GRANT_RECORD_DIR = None


def _init_grant_record_dir(base_dir):
    global GRANT_RECORD_DIR
    GRANT_RECORD_DIR = os.path.join(base_dir, 'data', 'grant_records')
    os.makedirs(GRANT_RECORD_DIR, exist_ok=True)


def get_admin_today_grant_count(admin_uid):
    if not GRANT_RECORD_DIR:
        return 0
    today = time.strftime('%Y-%m-%d')
    count = 0
    for fname in _safe_listdir(GRANT_RECORD_DIR):
        if fname.endswith('.txt') and fname.startswith(f'{admin_uid}_{today}_'):
            count += 1
    return count


def record_admin_grant(admin_uid, target_uid, amount, reason=''):
    if not GRANT_RECORD_DIR:
        return False
    today = time.strftime('%Y-%m-%d')
    ts = int(time.time() * 1000)
    record = {
        'admin_uid': admin_uid,
        'target_uid': target_uid,
        'amount': amount,
        'reason': reason,
        'timestamp': time.time(),
        'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    filename = f'{admin_uid}_{today}_{ts}.txt'
    _write_txt_file(os.path.join(GRANT_RECORD_DIR, filename), record)
    return True


# ==================== Picture Model ====================
class Picture:
    @staticmethod
    def get_next_id():
        return _get_next_id(PICTURE_DIR)

    @staticmethod
    def upload(uploader_uid, uploader_name, title, description, filename, is_video=False):
        pid = Picture.get_next_id()
        pic_data = {
            'id': pid,
            'title': title,
            'description': description,
            'filename': filename,
            'uploader_uid': uploader_uid,
            'uploader_name': uploader_name,
            'is_video': is_video,
            'status': 'pending',
            'upload_time': time.time(),
            'rating_sum': 0,
            'rating_count': 0,
            'comment_count': 0,
            'download_points': 0,
            'download_count': 0,
            'downloaders': []
        }
        _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic_data)
        if not is_video:
            user = PicUser.get_by_uid(uploader_uid)
            if user:
                PicUser.update(uploader_uid, uploaded_pictures=user.get('uploaded_pictures', 0) + 1)
        else:
            user = PicUser.get_by_uid(uploader_uid)
            if user:
                PicUser.update(uploader_uid, uploaded_videos=user.get('uploaded_videos', 0) + 1)
        return pid

    @staticmethod
    def get_by_id(pid):
        path = os.path.join(PICTURE_DIR, f'{pid}.txt')
        data = _read_txt_file(path)
        return data if data else None

    @staticmethod
    def get_all_approved():
        pics = []
        for fname in _safe_listdir(PICTURE_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(PICTURE_DIR, fname))
                if data and data.get('status') == 'approved':
                    pics.append(data)
        pics.sort(key=lambda x: x.get('upload_time', 0), reverse=True)
        return pics

    @staticmethod
    def get_approved_by_uploader(uploader_uid):
        pics = []
        for fname in _safe_listdir(PICTURE_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(PICTURE_DIR, fname))
                if data and data.get('status') == 'approved' and data.get('uploader_uid') == uploader_uid:
                    pics.append(data)
        pics.sort(key=lambda x: x.get('upload_time', 0), reverse=True)
        return pics

    @staticmethod
    def get_all_pending():
        pics = []
        for fname in _safe_listdir(PICTURE_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(PICTURE_DIR, fname))
                if data and data.get('status') == 'pending':
                    pics.append(data)
        pics.sort(key=lambda x: x.get('upload_time', 0), reverse=True)
        return pics

    @staticmethod
    def update(pid, **kwargs):
        pic = Picture.get_by_id(pid)
        if not pic:
            return False
        pic.update(kwargs)
        _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic)
        return True

    @staticmethod
    def delete(pid):
        pic = Picture.get_by_id(pid)
        if pic:
            filepath = os.path.join(UPLOAD_DIR, pic.get('filename', ''))
            if os.path.exists(filepath):
                os.remove(filepath)
        path = os.path.join(PICTURE_DIR, f'{pid}.txt')
        if os.path.exists(path):
            os.remove(path)
        comment_file = os.path.join(COMMENTS_DIR, f'pic_{pid}')
        page = 1
        while True:
            cf = f'{comment_file}_page{page}.txt'
            if os.path.exists(cf):
                os.remove(cf)
                page += 1
            else:
                break
        return True

    @staticmethod
    def approve(pid, download_points=0):
        pic = Picture.get_by_id(pid)
        if pic:
            pic['status'] = 'approved'
            pic['download_points'] = download_points
            _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic)
            return True
        return False

    @staticmethod
    def set_download_points(pid, points):
        pic = Picture.get_by_id(pid)
        if not pic:
            return False
        pic['download_points'] = max(0, int(points))
        _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic)
        return True

    @staticmethod
    def record_download(pid, user_uid):
        pic = Picture.get_by_id(pid)
        if not pic:
            return False
        downloaders = pic.get('downloaders', [])
        if user_uid not in downloaders:
            downloaders.append(user_uid)
            pic['downloaders'] = downloaders
        pic['download_count'] = pic.get('download_count', 0) + 1
        _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic)
        return True

    @staticmethod
    def has_downloaded(pid, user_uid):
        pic = Picture.get_by_id(pid)
        if not pic:
            return False
        return user_uid in pic.get('downloaders', [])

    @staticmethod
    def reject(pid):
        pic = Picture.get_by_id(pid)
        if pic:
            filepath = os.path.join(UPLOAD_DIR, pic.get('filename', ''))
            if os.path.exists(filepath):
                os.remove(filepath)
        return Picture.update(pid, status='rejected')

    @staticmethod
    def add_rating(pid, rating):
        pic = Picture.get_by_id(pid)
        if not pic:
            return False
        pic['rating_sum'] = pic.get('rating_sum', 0) + rating
        pic['rating_count'] = pic.get('rating_count', 0) + 1
        _write_txt_file(os.path.join(PICTURE_DIR, f'{pid}.txt'), pic)
        return True

    @staticmethod
    def get_average_rating(pid):
        pic = Picture.get_by_id(pid)
        if not pic or pic.get('rating_count', 0) == 0:
            return 0
        return round(pic['rating_sum'] / pic['rating_count'], 1)


# ==================== Comment Model ====================
class Comment:
    @staticmethod
    def _get_comment_file(pic_id, page):
        return os.path.join(COMMENTS_DIR, f'pic_{pic_id}_page{page}.txt')

    @staticmethod
    def _get_page_for_new(pic_id):
        page = 1
        while True:
            cf = Comment._get_comment_file(pic_id, page)
            if not os.path.exists(cf):
                return page
            comments = _read_txt_file(cf).get('comments', [])
            if len(comments) < 50:
                return page
            page += 1

    @staticmethod
    def add(pic_id, user_uid, username, content, rating=0):
        page = Comment._get_page_for_new(pic_id)
        cf = Comment._get_comment_file(pic_id, page)
        data = _read_txt_file(cf)
        if not data:
            data = {'pic_id': pic_id, 'page': page, 'comments': []}
        comments = data.get('comments', [])
        cid = int(time.time() * 1000) + len(comments)
        comment = {
            'id': cid,
            'pic_id': pic_id,
            'user_uid': user_uid,
            'username': username,
            'content': content,
            'rating': rating,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        comments.append(comment)
        data['comments'] = comments
        _write_txt_file(cf, data)

        pic = Picture.get_by_id(pic_id)
        if pic:
            Picture.update(pic_id, comment_count=pic.get('comment_count', 0) + 1)
            if rating > 0:
                Picture.add_rating(pic_id, rating)
        return cid

    @staticmethod
    def get_by_pic(pic_id, page=1):
        cf = Comment._get_comment_file(pic_id, page)
        data = _read_txt_file(cf)
        return data.get('comments', []) if data else []

    @staticmethod
    def get_total_pages(pic_id):
        page = 0
        while True:
            cf = Comment._get_comment_file(pic_id, page + 1)
            if os.path.exists(cf):
                page += 1
            else:
                break
        return page if page > 0 else 1

    @staticmethod
    def delete(comment_id, pic_id=None):
        if pic_id:
            pages_to_check = list(range(1, Comment.get_total_pages(pic_id) + 1))
        else:
            pages_to_check = []
            for fname in _safe_listdir(COMMENTS_DIR):
                if fname.startswith('pic_') and fname.endswith('.txt'):
                    parts = fname.replace('pic_', '').replace('.txt', '').split('_page')
                    if len(parts) == 2:
                        try:
                            pid = int(parts[0])
                            pg = int(parts[1])
                            pages_to_check.append((pid, pg))
                        except:
                            pass

        for item in pages_to_check:
            if pic_id:
                pid = pic_id
                pg = item
            else:
                pid, pg = item
            cf = Comment._get_comment_file(pid, pg)
            data = _read_txt_file(cf)
            if not data:
                continue
            comments = data.get('comments', [])
            new_comments = [c for c in comments if c.get('id') != comment_id]
            if len(new_comments) != len(comments):
                data['comments'] = new_comments
                _write_txt_file(cf, data)
                pic = Picture.get_by_id(pid)
                if pic:
                    Picture.update(pid, comment_count=max(0, pic.get('comment_count', 1) - 1))
                return True
        return False

    @staticmethod
    def delete_all_by_user(user_uid):
        deleted = 0
        for fname in _safe_listdir(COMMENTS_DIR):
            if fname.startswith('pic_') and fname.endswith('.txt'):
                path = os.path.join(COMMENTS_DIR, fname)
                data = _read_txt_file(path)
                if not data:
                    continue
                comments = data.get('comments', [])
                new_comments = [c for c in comments if c.get('user_uid') != user_uid]
                removed = len(comments) - len(new_comments)
                if removed > 0:
                    data['comments'] = new_comments
                    _write_txt_file(path, data)
                    pic_id = data.get('pic_id')
                    if pic_id:
                        pic = Picture.get_by_id(pic_id)
                        if pic:
                            Picture.update(pic_id, comment_count=max(0, pic.get('comment_count', 0) - removed))
                    deleted += removed
        return deleted


# ==================== Application Model ====================
class Application:
    @staticmethod
    def create(ip, username, password, email=''):
        apps = Application.get_all()
        recent = [a for a in apps if a.get('ip') == ip
                  and time.time() - a.get('timestamp', 0) < 60]
        if recent:
            return None, '同一IP申请间隔至少1分钟'
        if Application.is_ip_blocked(ip):
            return None, '该IP已被禁止申请'
        if PicUser.get_by_username(username):
            return None, '用户名已存在'

        aid = _get_next_id(APPLICATION_DIR)
        app_data = {
            'id': aid,
            'ip': ip,
            'username': username,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'email': email,
            'status': 'pending',
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        _write_txt_file(os.path.join(APPLICATION_DIR, f'{aid}.txt'), app_data)
        return aid, None

    @staticmethod
    def get_all():
        apps = []
        if not os.path.exists(APPLICATION_DIR):
            return apps
        for fname in _safe_listdir(APPLICATION_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(APPLICATION_DIR, fname))
                if data:
                    apps.append(data)
        apps.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return apps

    @staticmethod
    def get_pending():
        return [a for a in Application.get_all() if a.get('status') == 'pending']

    @staticmethod
    def approve(aid):
        path = os.path.join(APPLICATION_DIR, f'{aid}.txt')
        data = _read_txt_file(path)
        if not data:
            return False
        data['status'] = 'approved'
        _write_txt_file(path, data)
        uid = PicUser.create(
            username=data['username'],
            password='',
            role='user',
            email=data.get('email', '')
        )
        if uid:
            user_path = os.path.join(USER_DIR, f'{uid}.txt')
            user_data = _read_txt_file(user_path)
            user_data['password'] = data['password']
            _write_txt_file(user_path, user_data)
        return True

    @staticmethod
    def reject(aid):
        path = os.path.join(APPLICATION_DIR, f'{aid}.txt')
        data = _read_txt_file(path)
        if not data:
            return False
        data['status'] = 'rejected'
        _write_txt_file(path, data)
        return True

    @staticmethod
    def is_ip_blocked(ip):
        data = _read_txt_file(BLOCKED_IPS_FILE)
        blocked = data.get('blocked_ips', [])
        return ip in blocked

    @staticmethod
    def block_ip(ip):
        data = _read_txt_file(BLOCKED_IPS_FILE)
        if not data:
            data = {'blocked_ips': []}
        if ip not in data.get('blocked_ips', []):
            data.setdefault('blocked_ips', []).append(ip)
        _write_txt_file(BLOCKED_IPS_FILE, data)
        return True

    @staticmethod
    def unblock_ip(ip):
        data = _read_txt_file(BLOCKED_IPS_FILE)
        if not data:
            return False
        data['blocked_ips'] = [i for i in data.get('blocked_ips', []) if i != ip]
        _write_txt_file(BLOCKED_IPS_FILE, data)
        return True

    @staticmethod
    def get_blocked_ips():
        data = _read_txt_file(BLOCKED_IPS_FILE)
        return data.get('blocked_ips', []) if data else []


# ==================== Group Chat Model ====================
class GroupChat:
    @staticmethod
    def get_next_id():
        return _get_next_id(GROUPCHAT_DIR)

    @staticmethod
    def create(creator_uid, creator_name, name):
        gid = GroupChat.get_next_id()
        group_data = {
            'id': gid,
            'name': name,
            'creator_uid': creator_uid,
            'creator_name': creator_name,
            'members': [{'uid': creator_uid, 'username': creator_name}],
            'created_at': time.time(),
            'messages': [],
            'invitations': []
        }
        _write_txt_file(os.path.join(GROUPCHAT_DIR, f'{gid}.txt'), group_data)

        creator = PicUser.get_by_uid(creator_uid)
        if creator:
            groups = creator.get('groups', [])
            groups.append({'gid': gid, 'name': name})
            PicUser.update(creator_uid, groups=groups)
        return gid

    @staticmethod
    def get_by_id(gid):
        path = os.path.join(GROUPCHAT_DIR, f'{gid}.txt')
        data = _read_txt_file(path)
        return data if data else None

    @staticmethod
    def get_user_groups(uid):
        groups = []
        for fname in _safe_listdir(GROUPCHAT_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(GROUPCHAT_DIR, fname))
                if data:
                    members = [m.get('uid') for m in data.get('members', [])]
                    if uid in members:
                        groups.append(data)
        return groups

    @staticmethod
    def invite(gid, inviter_uid, target_uid):
        group = GroupChat.get_by_id(gid)
        target = PicUser.get_by_uid(target_uid)
        if not group or not target:
            return False
        if group.get('creator_uid') != inviter_uid:
            return False
        members = [m.get('uid') for m in group.get('members', [])]
        if target_uid in members:
            return False

        invitation = {
            'gid': gid,
            'group_name': group.get('name'),
            'inviter_uid': inviter_uid,
            'inviter_name': group.get('creator_name'),
            'timestamp': time.time()
        }
        invitations = target.get('groups', [])
        target_groups = [g for g in invitations if isinstance(g, dict) and g.get('invitation')]
        target_groups.append(invitation)

        all_groups = [g for g in invitations if isinstance(g, dict) and 'gid' in g and 'invitation' not in g]
        all_groups.extend([g for g in invitations if isinstance(g, dict) and g.get('invitation')])
        all_groups.append(invitation)

        PicUser.update(target_uid, groups=all_groups)
        return True

    @staticmethod
    def accept_invitation(gid, uid):
        group = GroupChat.get_by_id(gid)
        user = PicUser.get_by_uid(uid)
        if not group or not user:
            return False
        members = [m.get('uid') for m in group.get('members', [])]
        if uid not in members:
            group.setdefault('members', []).append({'uid': uid, 'username': user.get('username')})
            _write_txt_file(os.path.join(GROUPCHAT_DIR, f'{gid}.txt'), group)

        user_groups = user.get('groups', [])
        new_groups = []
        for g in user_groups:
            if isinstance(g, dict) and g.get('gid') == gid and 'invitation' in (g.get('invitation') or ''):
                continue
            new_groups.append(g)
        has_group = any(isinstance(g, dict) and g.get('gid') == gid and 'invitation' not in str(g.get('invitation', '')) for g in new_groups)
        if not has_group:
            new_groups.append({'gid': gid, 'name': group.get('name')})
        PicUser.update(uid, groups=new_groups)
        return True

    @staticmethod
    def send_message(gid, sender_uid, sender_name, content):
        group = GroupChat.get_by_id(gid)
        if not group:
            return False
        members = [m.get('uid') for m in group.get('members', [])]
        if sender_uid not in members:
            return False
        msg = {
            'id': int(time.time() * 1000),
            'sender_uid': sender_uid,
            'sender_name': sender_name,
            'content': content,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        group.setdefault('messages', []).append(msg)
        _write_txt_file(os.path.join(GROUPCHAT_DIR, f'{gid}.txt'), group)
        return True

    @staticmethod
    def send_red_packet_msg(gid, sender_uid, sender_name, rpid, rp_type, total_amount,
                            total_count=1, remark='', target_name=''):
        group = GroupChat.get_by_id(gid)
        if not group:
            return False
        members = [m.get('uid') for m in group.get('members', [])]
        if sender_uid not in members:
            return False

        if rp_type == 'single':
            content = f'🧧 专属红包给 {target_name}'
        elif rp_type == 'password':
            content = f'🧧 口令红包 - {remark if remark else "点击输入口令领取"}'
        else:
            content = f'🧧 拼手气红包 - {remark if remark else "恭喜发财，大吉大利"}'

        msg = {
            'id': int(time.time() * 1000),
            'sender_uid': sender_uid,
            'sender_name': sender_name,
            'content': content,
            'type': 'red_packet',
            'rpid': rpid,
            'rp_type': rp_type,
            'total_amount': total_amount,
            'total_count': total_count,
            'remark': remark,
            'target_name': target_name,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        group.setdefault('messages', []).append(msg)
        _write_txt_file(os.path.join(GROUPCHAT_DIR, f'{gid}.txt'), group)
        return True

    @staticmethod
    def delete_group(gid, deleter_uid):
        group = GroupChat.get_by_id(gid)
        if not group:
            return False
        if group.get('creator_uid') != deleter_uid:
            return False
        for member in group.get('members', []):
            uid = member.get('uid')
            user = PicUser.get_by_uid(uid)
            if user:
                groups = user.get('groups', [])
                new_groups = [g for g in groups if not (isinstance(g, dict) and g.get('gid') == gid)]
                PicUser.update(uid, groups=new_groups)
        path = os.path.join(GROUPCHAT_DIR, f'{gid}.txt')
        if os.path.exists(path):
            os.remove(path)
        return True


# ==================== Private Chat Model ====================
class PrivateChat:
    @staticmethod
    def _get_chat_key(uid1, uid2):
        uids = sorted([uid1, uid2])
        return f'{uids[0]}_{uids[1]}'

    @staticmethod
    def send_message(from_uid, from_name, to_uid, content):
        from_user = PicUser.get_by_uid(from_uid)
        to_user = PicUser.get_by_uid(to_uid)
        if not from_user or not to_user:
            return False
        friends = [f.get('uid') for f in from_user.get('friends', [])]
        if to_uid not in friends:
            return False

        chat_key = PrivateChat._get_chat_key(from_uid, to_uid)
        msg = {
            'id': int(time.time() * 1000),
            'from_uid': from_uid,
            'from_name': from_name,
            'to_uid': to_uid,
            'content': content,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S'),
            'read': False
        }

        from_chats = from_user.get('private_chats', {})
        if chat_key not in from_chats:
            from_chats[chat_key] = {'messages': [], 'other_uid': to_uid, 'other_name': to_user.get('username')}
        from_chats[chat_key].setdefault('messages', []).append(msg)
        PicUser.update(from_uid, private_chats=from_chats)

        to_chats = to_user.get('private_chats', {})
        if chat_key not in to_chats:
            to_chats[chat_key] = {'messages': [], 'other_uid': from_uid, 'other_name': from_user.get('username')}
        to_chats[chat_key].setdefault('messages', []).append(msg)
        PicUser.update(to_uid, private_chats=to_chats)

        return True

    @staticmethod
    def get_messages(uid, other_uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return []
        chat_key = PrivateChat._get_chat_key(uid, other_uid)
        chats = user.get('private_chats', {})
        return chats.get(chat_key, {}).get('messages', [])

    @staticmethod
    def mark_read(uid, other_uid):
        user = PicUser.get_by_uid(uid)
        if not user:
            return False
        chat_key = PrivateChat._get_chat_key(uid, other_uid)
        chats = user.get('private_chats', {})
        if chat_key in chats:
            for msg in chats[chat_key].get('messages', []):
                if msg.get('to_uid') == uid:
                    msg['read'] = True
            PicUser.update(uid, private_chats=chats)
        return True

    @staticmethod
    def send_points(from_uid, from_name, to_uid, amount, remark=''):
        if amount <= 0:
            return False, '金额必须大于0'
        from_user = PicUser.get_by_uid(from_uid)
        to_user = PicUser.get_by_uid(to_uid)
        if not from_user or not to_user:
            return False, '用户不存在'
        friends = [f.get('uid') for f in from_user.get('friends', [])]
        if to_uid not in friends:
            return False, '只能给好友转账'
        if from_user.get('points', 0) < amount:
            return False, '积分不足'

        if not PicUser.transfer_points(from_uid, to_uid, amount,
                                       reason=f'私信转账{(" - " + remark) if remark else ""}'):
            return False, '转账失败'

        chat_key = PrivateChat._get_chat_key(from_uid, to_uid)
        msg = {
            'id': int(time.time() * 1000),
            'from_uid': from_uid,
            'from_name': from_name,
            'to_uid': to_uid,
            'content': f'[积分转账] {amount} 积分{(" - " + remark) if remark else ""}',
            'type': 'points_transfer',
            'points_amount': amount,
            'remark': remark,
            'timestamp': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S'),
            'read': False
        }

        from_chats = from_user.get('private_chats', {})
        if chat_key not in from_chats:
            from_chats[chat_key] = {'messages': [], 'other_uid': to_uid, 'other_name': to_user.get('username')}
        from_chats[chat_key].setdefault('messages', []).append(msg)
        PicUser.update(from_uid, private_chats=from_chats)

        to_chats = to_user.get('private_chats', {})
        if chat_key not in to_chats:
            to_chats[chat_key] = {'messages': [], 'other_uid': from_uid, 'other_name': from_user.get('username')}
        to_chats[chat_key].setdefault('messages', []).append(msg)
        PicUser.update(to_uid, private_chats=to_chats)

        return True, '转账成功'


# ==================== Red Packet Model ====================
RED_PACKET_DIR = None


def _init_red_packet_dir(base_dir):
    global RED_PACKET_DIR
    RED_PACKET_DIR = os.path.join(base_dir, 'data', 'red_packets')
    os.makedirs(RED_PACKET_DIR, exist_ok=True)


class RedPacket:
    @staticmethod
    def _get_next_id():
        return _get_next_id(RED_PACKET_DIR, prefix='rp_')

    @staticmethod
    def create(gid, sender_uid, sender_name, rp_type, total_amount,
               total_count=1, password='', remark='', target_uid='', target_name=''):
        if total_amount <= 0:
            return None, '金额必须大于0'
        if total_count < 1:
            total_count = 1
        if rp_type == 'single':
            total_count = 1

        sender = PicUser.get_by_uid(sender_uid)
        if not sender:
            return None, '用户不存在'
        if sender.get('points', 0) < total_amount:
            return None, '积分不足'

        if not PicUser.deduct_points(sender_uid, total_amount,
                                      reason=f'发群红包 {gid}{(" - " + remark) if remark else ""}'):
            return None, '扣款失败'

        rpid = RedPacket._get_next_id()
        rp_data = {
            'id': rpid,
            'gid': gid,
            'sender_uid': sender_uid,
            'sender_name': sender_name,
            'type': rp_type,
            'total_amount': total_amount,
            'total_count': total_count,
            'remaining_amount': total_amount,
            'remaining_count': total_count,
            'password': password,
            'remark': remark,
            'target_uid': target_uid,
            'target_name': target_name,
            'grabbers': [],
            'created_at': time.time(),
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        _write_txt_file(os.path.join(RED_PACKET_DIR, f'rp_{rpid}.txt'), rp_data)
        return rpid, None

    @staticmethod
    def get_by_id(rpid):
        path = os.path.join(RED_PACKET_DIR, f'rp_{rpid}.txt')
        data = _read_txt_file(path)
        return data if data else None

    @staticmethod
    def grab(rpid, grabber_uid, grabber_name, password=''):
        rp = RedPacket.get_by_id(rpid)
        if not rp:
            return False, '红包不存在', 0
        if rp.get('remaining_count', 0) <= 0 or rp.get('remaining_amount', 0) <= 0:
            return False, '红包已被抢完', 0

        grabber_uids = [g.get('uid') for g in rp.get('grabbers', [])]
        if grabber_uid in grabber_uids:
            return False, '您已经抢过这个红包了', 0

        rp_type = rp.get('type', 'lucky')

        if rp_type == 'single':
            if rp.get('target_uid') and rp['target_uid'] != grabber_uid:
                return False, '这是专属红包，您不能领取', 0
            amount = rp.get('total_amount', 0)
        elif rp_type == 'password':
            if rp.get('password') and rp['password'] != password:
                return False, '口令不正确', 0
            amount = RedPacket._calc_lucky_amount(rp)
        else:
            amount = RedPacket._calc_lucky_amount(rp)

        if amount <= 0:
            return False, '红包已被抢完', 0

        PicUser.add_points(grabber_uid, amount,
                           reason=f'抢群红包 {rpid}{(" - " + rp.get("remark", "")) if rp.get("remark") else ""}',
                           operator=rp.get('sender_name', ''))

        rp['remaining_amount'] = rp.get('remaining_amount', 0) - amount
        rp['remaining_count'] = rp.get('remaining_count', 0) - 1
        grab_record = {
            'uid': grabber_uid,
            'name': grabber_name,
            'amount': amount,
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time()
        }
        rp.setdefault('grabbers', []).append(grab_record)
        _write_txt_file(os.path.join(RED_PACKET_DIR, f'rp_{rpid}.txt'), rp)

        return True, '领取成功', amount

    @staticmethod
    def _calc_lucky_amount(rp):
        remaining = rp.get('remaining_amount', 0)
        count = rp.get('remaining_count', 0)
        if count <= 0:
            return 0
        if count == 1:
            return remaining
        import random
        max_amount = remaining - (count - 1)
        if max_amount < 1:
            return 1
        amount = random.randint(1, max_amount)
        return amount


# ==================== Ban Request Model ====================
class BanRequest:
    @staticmethod
    def get_all():
        records = []
        for fname in _safe_listdir(BAN_RECORD_DIR):
            if fname.endswith('.txt'):
                data = _read_txt_file(os.path.join(BAN_RECORD_DIR, fname))
                if data:
                    records.append(data)
        records.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return records


# ==================== User Action Log ====================
class UserActionLog:
    @staticmethod
    def _get_log_file(uid):
        date_str = datetime.now().strftime('%Y%m%d')
        return os.path.join(LOG_DIR, f'{uid}_{date_str}.log')

    @staticmethod
    def log(uid, username, action, detail='', ip=''):
        try:
            log_file = UserActionLog._get_log_file(uid)
            time_str = time.strftime('%Y-%m-%d %H:%M:%S')
            log_line = f'[{time_str}] [{username}] [{action}] {detail}'
            if ip:
                log_line += f' (IP: {ip})'
            log_line += '\n'
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            return True
        except Exception as e:
            print(f'Log write error: {e}')
            return False

    @staticmethod
    def get_user_logs(uid, date_str=None):
        if date_str:
            log_file = os.path.join(LOG_DIR, f'{uid}_{date_str}.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ''
        logs = []
        for fname in _safe_listdir(LOG_DIR):
            if fname.startswith(f'{uid}_') and fname.endswith('.log'):
                log_file = os.path.join(LOG_DIR, fname)
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    date = fname.replace(f'{uid}_', '').replace('.log', '')
                    logs.append({'date': date, 'content': content})
        logs.sort(key=lambda x: x['date'], reverse=True)
        return logs

    @staticmethod
    def get_all_log_dates(uid):
        dates = []
        for fname in _safe_listdir(LOG_DIR):
            if fname.startswith(f'{uid}_') and fname.endswith('.log'):
                date = fname.replace(f'{uid}_', '').replace('.log', '')
                dates.append(date)
        dates.sort(reverse=True)
        return dates
