from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, Response
from functools import wraps
import os
import sys
import json
import time
import mimetypes
import uuid
import random
from werkzeug.utils import secure_filename


def _get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


BASE_DIR = _get_base_path()
TEMPLATE_DIR = _get_resource_path('templates')
STATIC_DIR = _get_resource_path('static')

import pic_models
import video_converter
import file_crypto
import backup
import world_map
import land_system

pic_models.init_data_dirs(BASE_DIR)
video_converter.init_convert_dir(BASE_DIR)
file_crypto.init_crypto(BASE_DIR)
backup.init_backup(BASE_DIR)
backup.start_auto_backup()
land_system.init_land_dir(BASE_DIR)

PicUser = pic_models.PicUser
Picture = pic_models.Picture
Comment = pic_models.Comment
Application = pic_models.Application
GroupChat = pic_models.GroupChat
PrivateChat = pic_models.PrivateChat
BanRequest = pic_models.BanRequest
UserActionLog = pic_models.UserActionLog

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = 'pic_site_secret_key_2026'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024


@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
    except:
        return str(value)


# ---- Feature config (edit config.json to toggle features) ----
_config_cache = None
_config_mtime = 0


def load_config():
    global _config_cache, _config_mtime
    config_path = os.path.join(BASE_DIR, 'config.json')
    try:
        mtime = os.path.getmtime(config_path)
    except OSError:
        # Auto-create config.json next to the executable so users can edit it
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'map_enabled': False}, f, indent=4, ensure_ascii=False)
            _config_mtime = os.path.getmtime(config_path)
        except Exception:
            pass
        _config_cache = {}
        return _config_cache
    if _config_cache is not None and mtime == _config_mtime:
        return _config_cache
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_cache = json.load(f)
        _config_mtime = mtime
    except Exception:
        _config_cache = {}
    return _config_cache


def is_feature_enabled(name):
    return bool(load_config().get(name, False))


@app.context_processor
def inject_now():
    return {
        'now': time.time,
        'map_enabled': is_feature_enabled('map_enabled'),
    }

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXT = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}


def allowed_file(filename, exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in exts


# Routes guarded by the map feature switch (config.json -> map_enabled)
MAP_ROUTES_PREFIXES = (
    '/pic/world',
    '/pic/api/world',
    '/pic/api/lands',
    '/pic/api/land/',
    '/pic/land/',
    '/pic/house/',
    '/pic/my/house',
)


@app.before_request
def _guard_map_feature():
    if is_feature_enabled('map_enabled'):
        return None
    path = request.path
    for prefix in MAP_ROUTES_PREFIXES:
        if path == prefix.rstrip('/') or path.startswith(prefix):
            return '地图功能未开启。如需开启，请在 config.json 中设置 "map_enabled": true。', 404
    return None


def get_current_user():
    if 'uid' in session:
        user = PicUser.get_by_uid(session['uid'])
        if user and not PicUser.is_banned(session['uid']):
            return user
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('pic_login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return 'Permission denied', 403
        return f(*args, **kwargs)
    return decorated


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') not in ('admin', 'manager'):
            return 'Permission denied', 403
        return f(*args, **kwargs)
    return decorated


def get_client_ip():
    return request.remote_addr or '127.0.0.1'


def init_default_admin():
    admin_user = PicUser.get_by_username('admin')
    if not admin_user:
        PicUser.create('admin', 'admin123', role='admin')
        print('Default admin created: admin / admin123')


# ==================== 首页与图片展示 ====================
@app.route('/pic')
def pic_index():
    user = get_current_user()
    pics = Picture.get_all_approved()
    return render_template('pic_index.html', user=user, pictures=pics)


@app.route('/pic/world')
def pic_world():
    user = get_current_user()
    map_width = land_system.MAP_WIDTH
    map_height = land_system.MAP_HEIGHT
    world_map.set_map_bounds(map_width, map_height)
    start_x, start_y = map_width // 2, map_height // 2
    player_color = '#4ECDC4'
    my_land = None
    if user:
        player_color = world_map.get_player_color(user['uid'])
        pos = world_map.get_player_position(user['uid'])
        if pos:
            start_x, start_y = pos['x'], pos['y']
        my_land = land_system.get_my_land(user['uid'])
    lands = land_system.get_all_lands()
    return render_template('pic_world.html', user=user,
                           map_width=map_width, map_height=map_height,
                           start_x=start_x, start_y=start_y,
                           player_color=player_color, lands=lands,
                           my_land=my_land,
                           build_cost=land_system.BUILD_COST,
                           rent_period_days=land_system.RENT_PERIOD // (24 * 3600))


@app.route('/pic/api/world/position', methods=['POST'])
@login_required
def pic_api_world_position():
    user = get_current_user()
    data = request.get_json()
    x = data.get('x', 1000)
    y = data.get('y', 750)
    world_map.update_player_position(user['uid'], x, y)
    return jsonify({'status': 'ok'})


@app.route('/pic/api/world/players')
def pic_api_world_players():
    players = world_map.get_all_players()
    user = get_current_user()
    if user:
        players = [p for p in players if p['uid'] != user['uid']]
    return jsonify({'players': players, 'count': len(players)})


@app.route('/pic/api/lands')
def pic_api_lands():
    lands = land_system.get_all_lands()
    return jsonify({'lands': lands})


@app.route('/pic/api/land/<int:land_id>')
def pic_api_land_info(land_id):
    land = land_system.get_land(land_id)
    if not land:
        return jsonify({'error': '地块不存在'}), 404
    return jsonify(land)


@app.route('/pic/land/<int:land_id>/rent', methods=['POST'])
@login_required
def pic_land_rent(land_id):
    user = get_current_user()
    land = land_system.get_land(land_id)
    if not land:
        return '地块不存在', 404
    price = land.get('price', 5)
    if not PicUser.deduct_points(user['uid'], price,
                                 reason=f'租用地块 {land_id}'):
        return '积分不足', 403
    ok, msg = land_system.rent_land(land_id, user['uid'], user['username'])
    if not ok:
        PicUser.add_points(user['uid'], price, reason='租地失败退还')
        return msg, 400
    UserActionLog.log(user['uid'], user['username'], '租用地块',
                      f'租用地块 {land_id}，消耗 {price} 积分')
    return redirect(url_for('pic_world'))


@app.route('/pic/land/<int:land_id>/build', methods=['POST'])
@login_required
def pic_land_build(land_id):
    user = get_current_user()
    house_name = request.form.get('house_name', '').strip()
    if not PicUser.deduct_points(user['uid'], land_system.BUILD_COST,
                                 reason=f'在地块 {land_id} 建房'):
        return '积分不足', 403
    ok, msg = land_system.build_house(land_id, user['uid'], user['username'], house_name)
    if not ok:
        PicUser.add_points(user['uid'], land_system.BUILD_COST, reason='建房失败退还')
        return msg, 400
    UserActionLog.log(user['uid'], user['username'], '建造房屋',
                      f'在地块 {land_id} 建造房屋：{house_name or (user["username"] + "的小屋")}')
    return redirect(url_for('pic_house', land_id=land_id))


@app.route('/pic/land/<int:land_id>/renew', methods=['POST'])
@login_required
def pic_land_renew(land_id):
    user = get_current_user()
    land = land_system.get_land(land_id)
    if not land:
        return '地块不存在', 404
    price = land.get('rent_price', land.get('price', 5))
    if not PicUser.deduct_points(user['uid'], price,
                                 reason=f'续租地块 {land_id}'):
        return '积分不足', 403
    ok, msg = land_system.renew_rent(land_id, user['uid'])
    if not ok:
        PicUser.add_points(user['uid'], price, reason='续租失败退还')
        return msg, 400
    UserActionLog.log(user['uid'], user['username'], '续租地块',
                      f'续租地块 {land_id}，消耗 {price} 积分')
    return redirect(url_for('pic_house', land_id=land_id))


@app.route('/pic/house/<int:land_id>')
def pic_house(land_id):
    user = get_current_user()
    land = land_system.get_land(land_id)
    if not land:
        return '地块不存在', 404
    if land.get('is_vacant') or land.get('house_level', 0) < 1:
        return '该地块上还没有房屋', 404
    owner = PicUser.get_by_uid(land.get('owner_uid', ''))
    pictures = Picture.get_approved_by_uploader(land.get('owner_uid', ''))
    is_owner = user and user['uid'] == land.get('owner_uid')
    expiry_time = land.get('expiry_time', 0)
    days_left = max(0, int((expiry_time - time.time()) / (24 * 3600)))
    rent_cost = land.get('rent_price', land.get('price', 5))
    return render_template('pic_house.html', user=user, land=land,
                           owner=owner, pictures=pictures,
                           is_owner=is_owner, days_left=days_left,
                           rent_cost=rent_cost)


@app.route('/pic/my/house')
@login_required
def pic_my_house():
    user = get_current_user()
    my_land = land_system.get_my_land(user['uid'])
    if not my_land:
        return redirect(url_for('pic_world'))
    if my_land.get('house_level', 0) < 1:
        return redirect(url_for('pic_world'))
    return redirect(url_for('pic_house', land_id=my_land['id']))


@app.route('/pic/<int:pic_id>')
def pic_detail(pic_id):
    user = get_current_user()
    pic = Picture.get_by_id(pic_id)
    if not pic:
        return '图片不存在', 404
    if pic.get('status') != 'approved':
        is_owner = user and str(pic.get('uploader_uid')) == str(user.get('uid'))
        is_manager = user and user.get('role') in ('admin', 'manager')
        if not is_owner and not is_manager:
            return '图片不存在', 404
    page = int(request.args.get('page', 1))
    comments = Comment.get_by_pic(pic_id, page)
    total_pages = Comment.get_total_pages(pic_id)
    avg_rating = Picture.get_average_rating(pic_id)

    has_downloaded = False
    if user:
        has_downloaded = Picture.has_downloaded(pic_id, user['uid'])
        user = PicUser.get_by_uid(user['uid'])

    return render_template('pic_detail.html', user=user, pic=pic,
                           comments=comments, page=page,
                           total_pages=total_pages, avg_rating=avg_rating,
                           has_downloaded=has_downloaded)


@app.route('/pic/uploads/<filename>')
def pic_uploaded_file(filename):
    filepath = os.path.join(pic_models.UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return 'File not found', 404

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    is_video = ext in ALLOWED_VIDEO_EXT

    if file_crypto.is_crypto_enabled() and file_crypto.is_file_encrypted(filepath):
        mimetype, _ = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'video/mp4' if is_video else 'image/jpeg'

        range_header = request.headers.get('Range', None)

        decrypted_data = file_crypto.decrypt_file(filepath)
        if decrypted_data is False:
            return 'File corrupted', 500

        file_size = len(decrypted_data)

        if not range_header:
            def generate():
                chunk_size = 64 * 1024
                offset = 0
                while offset < file_size:
                    end = min(offset + chunk_size, file_size)
                    yield decrypted_data[offset:end]
                    offset = end
            response = Response(generate(), mimetype=mimetype)
            response.headers['Content-Length'] = str(file_size)
            response.headers['Accept-Ranges'] = 'bytes'
            return response

        byte1, byte2 = 0, None
        range_header = range_header.strip()
        if range_header.startswith('bytes='):
            range_value = range_header[6:]
            if '-' in range_value:
                byte1_str, byte2_str = range_value.split('-', 1)
                if byte1_str:
                    byte1 = int(byte1_str)
                if byte2_str:
                    byte2 = int(byte2_str)

        if byte1 >= file_size:
            response = Response(status=416)
            response.headers['Content-Range'] = f'bytes */{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            return response

        if byte2 is None or byte2 >= file_size:
            byte2 = file_size - 1

        if byte2 < byte1:
            response = Response(status=416)
            response.headers['Content-Range'] = f'bytes */{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            return response

        length = byte2 - byte1 + 1

        def generate_range():
            chunk_size = 64 * 1024
            offset = byte1
            remaining = length
            while remaining > 0:
                chunk = min(chunk_size, remaining)
                end = offset + chunk
                yield decrypted_data[offset:end]
                offset = end
                remaining -= chunk

        response = Response(generate_range(), mimetype=mimetype, status=206)
        response.headers['Content-Range'] = f'bytes {byte1}-{byte2}/{file_size}'
        response.headers['Content-Length'] = str(length)
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    if is_video:
        return stream_video(filepath)
    return send_from_directory(pic_models.UPLOAD_DIR, filename)


def stream_video(filepath):
    file_size = os.path.getsize(filepath)
    mimetype, _ = mimetypes.guess_type(filepath)
    if not mimetype:
        mimetype = 'video/mp4'

    range_header = request.headers.get('Range', None)
    if not range_header:
        def generate():
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk
        response = Response(generate(), mimetype=mimetype)
        response.headers['Content-Length'] = str(file_size)
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    byte1, byte2 = 0, None
    range_header = range_header.strip()
    if range_header.startswith('bytes='):
        range_value = range_header[6:]
        if '-' in range_value:
            byte1_str, byte2_str = range_value.split('-', 1)
            if byte1_str:
                byte1 = int(byte1_str)
            if byte2_str:
                byte2 = int(byte2_str)

    if byte1 >= file_size:
        response = Response(status=416)
        response.headers['Content-Range'] = f'bytes */{file_size}'
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    if byte2 is None or byte2 >= file_size:
        byte2 = file_size - 1

    if byte2 < byte1:
        response = Response(status=416)
        response.headers['Content-Range'] = f'bytes */{file_size}'
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    length = byte2 - byte1 + 1

    def generate_range():
        with open(filepath, 'rb') as f:
            f.seek(byte1)
            remaining = length
            while remaining > 0:
                chunk_size = min(1024 * 1024, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    response = Response(generate_range(), mimetype=mimetype, status=206)
    response.headers['Content-Range'] = f'bytes {byte1}-{byte2}/{file_size}'
    response.headers['Content-Length'] = str(length)
    response.headers['Accept-Ranges'] = 'bytes'
    return response


# ==================== 登录注册 ====================
@app.route('/pic/login', methods=['GET', 'POST'])
def pic_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '')
        password = request.form.get('password', '')
        user = PicUser.authenticate(identifier, password)
        if user:
            session['uid'] = user['uid']
            session['username'] = user['username']
            session['role'] = user['role']
            UserActionLog.log(user['uid'], user['username'], '登录', '用户登录成功', get_client_ip())
            return redirect(url_for('pic_index'))
        UserActionLog.log('unknown', identifier, '登录失败', f'登录尝试失败，标识符: {identifier}', get_client_ip())
        return render_template('pic_login.html', error='用户名或密码错误')
    return render_template('pic_login.html', error=None)


@app.route('/pic/logout')
def pic_logout():
    user = get_current_user()
    if user:
        UserActionLog.log(user['uid'], user['username'], '登出', '用户登出', get_client_ip())
    session.clear()
    return redirect(url_for('pic_index'))


@app.route('/pic/apply', methods=['GET', 'POST'])
def pic_apply():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        ip = get_client_ip()
        aid, err = Application.create(ip, username, password, email)
        if aid:
            return render_template('pic_apply.html', success='申请已提交，请等待管理员审核')
        return render_template('pic_apply.html', error=err)
    return render_template('pic_apply.html', error=None, success=None)


# ==================== 用户中心 ====================
@app.route('/pic/profile')
@login_required
def pic_profile():
    user = get_current_user()
    return render_template('pic_profile.html', user=user)


@app.route('/pic/change_password', methods=['GET', 'POST'])
@login_required
def pic_change_password():
    user = get_current_user()
    if request.method == 'POST':
        old_pwd = request.form.get('old_password', '')
        new_pwd = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')
        if new_pwd != confirm_pwd:
            return render_template('pic_change_password.html', user=user, error='两次密码不一致')
        if PicUser.change_password(user['uid'], old_pwd, new_pwd):
            UserActionLog.log(user['uid'], user['username'], '修改密码', '用户修改密码成功')
            return redirect(url_for('pic_profile'))
        return render_template('pic_change_password.html', user=user, error='原密码错误')
    return render_template('pic_change_password.html', user=user, error=None)


# ==================== 上传图片/视频 ====================
@app.route('/pic/upload', methods=['GET', 'POST'])
@login_required
def pic_upload():
    user = get_current_user()
    if PicUser.is_banned(user['uid']):
        return '您已被封禁，无法上传', 403

    if request.method == 'POST':
        upload_type = request.form.get('type', 'image')
        title = request.form.get('title', '')
        description = request.form.get('description', '')

        if 'file' not in request.files:
            return render_template('pic_upload.html', user=user, error='没有选择文件')
        file = request.files['file']
        if file.filename == '':
            return render_template('pic_upload.html', user=user, error='没有选择文件')

        if upload_type == 'video':
            exts = ALLOWED_VIDEO_EXT
            is_video = True
        else:
            exts = ALLOWED_IMAGE_EXT
            is_video = False

        if file and allowed_file(file.filename, exts):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f'{int(time.time() * 1000)}_{user["uid"]}.{ext}'
            file_path = os.path.join(pic_models.UPLOAD_DIR, new_filename)
            file.save(file_path)

            if file_crypto.is_crypto_enabled():
                file_crypto.encrypt_file(file_path)

            pid = Picture.upload(
                uploader_uid=user['uid'],
                uploader_name=user['username'],
                title=title,
                description=description,
                filename=new_filename,
                is_video=is_video
            )
            file_type = '视频' if is_video else '图片'
            UserActionLog.log(user['uid'], user['username'], f'上传{file_type}',
                              f'上传{file_type}成功，ID: {pid}，标题: {title}，文件名: {new_filename}')
            return redirect(url_for('pic_detail', pic_id=pid))
        return render_template('pic_upload.html', user=user, error='文件格式不支持')
    return render_template('pic_upload.html', user=user, error=None)


# ==================== 下载 ====================
@app.route('/pic/<int:pic_id>/download', methods=['POST'])
@login_required
def pic_download(pic_id):
    user = get_current_user()
    pic = Picture.get_by_id(pic_id)
    if not pic or pic.get('status') != 'approved':
        return '图片不存在', 404

    filepath = os.path.join(pic_models.UPLOAD_DIR, pic.get('filename', ''))
    if not os.path.exists(filepath):
        return '文件不存在', 404

    download_points = pic.get('download_points', 0)
    has_downloaded = Picture.has_downloaded(pic_id, user['uid'])

    if download_points > 0 and not has_downloaded:
        if not PicUser.deduct_points(user['uid'], download_points,
                                     reason=f'下载图片 {pic_id} ({pic.get("title", "")})'):
            return '积分不足', 403
        uploader_uid = pic.get('uploader_uid')
        if uploader_uid:
            PicUser.add_points(uploader_uid, download_points,
                               reason=f'图片被下载 {pic_id} ({pic.get("title", "")})',
                               operator=user.get('username', ''))

    Picture.record_download(pic_id, user['uid'])
    UserActionLog.log(user['uid'], user['username'], '下载图片',
                      f'下载图片ID {pic_id}，标题: {pic.get("title", "")}，消耗积分: {download_points if not has_downloaded else 0}')

    filename = pic.get('filename', '')

    if file_crypto.is_crypto_enabled() and file_crypto.is_file_encrypted(filepath):
        decrypted = file_crypto.decrypt_file(filepath)
        if decrypted is False:
            return '文件损坏', 500

        def generate():
            chunk_size = 64 * 1024
            offset = 0
            total = len(decrypted)
            while offset < total:
                end = min(offset + chunk_size, total)
                yield decrypted[offset:end]
                offset = end

        response = Response(generate(), mimetype='application/octet-stream')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = str(len(decrypted))
        return response

    return send_from_directory(pic_models.UPLOAD_DIR, filename,
                               as_attachment=True, download_name=filename)


# ==================== 评论与评分 ====================
@app.route('/pic/<int:pic_id>/comment', methods=['POST'])
@login_required
def pic_add_comment(pic_id):
    user = get_current_user()
    if PicUser.is_banned(user['uid']):
        return '您已被封禁，无法评论', 403
    content = request.form.get('content', '')
    rating = int(request.form.get('rating', 0))
    if not content.strip():
        return redirect(url_for('pic_detail', pic_id=pic_id))
    Comment.add(pic_id, user['uid'], user['username'], content, rating)

    if rating > 0:
        pic = Picture.get_by_id(pic_id)
        if pic and pic.get('uploader_uid') and pic.get('uploader_uid') != user['uid']:
            PicUser.add_points(pic['uploader_uid'], rating,
                               reason=f'图片被评分 {pic_id} ({pic.get("title", "")})，评分: {rating}',
                               operator=user.get('username', ''))

    rating_info = f'，评分: {rating}' if rating > 0 else ''
    UserActionLog.log(user['uid'], user['username'], '发表评论',
                      f'在图片ID {pic_id} 发表评论{rating_info}，内容: {content[:50]}...' if len(content) > 50 else f'在图片ID {pic_id} 发表评论{rating_info}，内容: {content}')
    return redirect(url_for('pic_detail', pic_id=pic_id))


@app.route('/pic/comment/<int:comment_id>/delete', methods=['POST'])
@manager_required
def pic_delete_comment(comment_id):
    pic_id = request.form.get('pic_id', type=int)
    Comment.delete(comment_id, pic_id)
    return redirect(request.referrer or url_for('pic_index'))


# ==================== 管理员 - 审核 ====================
@app.route('/pic/admin/review')
@manager_required
def pic_admin_review():
    user = get_current_user()
    pending = Picture.get_all_pending()
    return render_template('pic_admin_review.html', user=user, pictures=pending)


@app.route('/pic/admin/review/<int:pic_id>/approve', methods=['POST'])
@manager_required
def pic_admin_approve(pic_id):
    user = get_current_user()
    pic = Picture.get_by_id(pic_id)
    title = pic.get('title', '') if pic else ''
    download_points = int(request.form.get('download_points', 0))
    download_points = max(0, min(100, download_points))
    Picture.approve(pic_id, download_points=download_points)
    UserActionLog.log(user['uid'], user['username'], '审核通过',
                      f'审核通过图片 ID: {pic_id}，标题: {title}，下载积分: {download_points}')
    return redirect(url_for('pic_admin_review'))


@app.route('/pic/admin/review/<int:pic_id>/reject', methods=['POST'])
@manager_required
def pic_admin_reject(pic_id):
    user = get_current_user()
    pic = Picture.get_by_id(pic_id)
    title = pic.get('title', '') if pic else ''
    Picture.reject(pic_id)
    UserActionLog.log(user['uid'], user['username'], '审核拒绝',
                      f'审核拒绝图片 ID: {pic_id}，标题: {title}')
    return redirect(url_for('pic_admin_review'))


@app.route('/pic/admin/picture/<int:pic_id>/delete', methods=['POST'])
@admin_required
def pic_admin_delete_picture(pic_id):
    user = get_current_user()
    pic = Picture.get_by_id(pic_id)
    title = pic.get('title', '') if pic else ''
    filename = pic.get('filename', '') if pic else ''
    Picture.delete(pic_id)
    UserActionLog.log(user['uid'], user['username'], '删除图片/视频',
                      f'删除图片/视频 ID: {pic_id}，标题: {title}，文件: {filename}')
    return redirect(url_for('pic_index'))


# ==================== Admin - 数据备份 ====================
@app.route('/pic/admin/backup')
@admin_required
def pic_admin_backup():
    user = get_current_user()
    backups = backup.list_backups()
    for b in backups:
        b['size_str'] = backup.format_size(b['size'])
    last_ts = backup.get_last_backup_time()
    last_backup_time = None
    if last_ts > 0:
        import time
        last_backup_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_ts))
    return render_template('pic_admin_backup.html', user=user,
                           backups=backups, last_backup_time=last_backup_time)


@app.route('/pic/admin/backup/create', methods=['POST'])
@admin_required
def pic_admin_backup_create():
    user = get_current_user()
    result, err = backup.create_backup()
    UserActionLog.log(user['uid'], user['username'], '手动备份',
                      f'手动创建备份: {result["filename"] if result else err}')
    if err:
        return redirect(url_for('pic_admin_backup', error=err))
    return redirect(url_for('pic_admin_backup', message='备份创建成功'))


@app.route('/pic/admin/backup/download/<filename>')
@admin_required
def pic_admin_backup_download(filename):
    user = get_current_user()
    fpath = backup.get_backup_path(filename)
    if not fpath:
        return '备份文件不存在', 404
    UserActionLog.log(user['uid'], user['username'], '下载备份',
                      f'下载备份文件: {filename}')
    return send_from_directory(backup.BACKUP_DIR, filename, as_attachment=True)


@app.route('/pic/admin/backup/delete/<filename>', methods=['POST'])
@admin_required
def pic_admin_backup_delete(filename):
    user = get_current_user()
    backup.delete_backup(filename)
    UserActionLog.log(user['uid'], user['username'], '删除备份',
                      f'删除备份文件: {filename}')
    return redirect(url_for('pic_admin_backup'))


BACKUP_API_TOKEN = None


def _get_backup_api_token():
    global BACKUP_API_TOKEN
    if BACKUP_API_TOKEN is None:
        token_file = os.path.join(BASE_DIR, 'data', 'backup_token.txt')
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    BACKUP_API_TOKEN = f.read().strip()
            except Exception:
                pass
        if not BACKUP_API_TOKEN:
            BACKUP_API_TOKEN = ''.join(random.choices(
                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                k=32
            ))
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, 'w') as f:
                f.write(BACKUP_API_TOKEN)
    return BACKUP_API_TOKEN


def _require_backup_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Backup-Token')
        if token != _get_backup_api_token():
            return jsonify({'error': 'Invalid token'}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/pic/api/backup/latest', methods=['GET'])
@_require_backup_token
def pic_api_backup_latest():
    backups = backup.list_backups()
    if not backups:
        return jsonify({'error': 'No backups available'}), 404
    latest = backups[0]
    return jsonify({
        'filename': latest['filename'],
        'size': latest['size'],
        'time': latest['time'],
        'time_str': latest['time_str']
    })


@app.route('/pic/api/backup/download/<filename>', methods=['GET'])
@_require_backup_token
def pic_api_backup_download(filename):
    fpath = backup.get_backup_path(filename)
    if not fpath:
        return jsonify({'error': 'Backup not found'}), 404
    return send_from_directory(backup.BACKUP_DIR, filename, as_attachment=True)


@app.route('/pic/api/backup/list', methods=['GET'])
@_require_backup_token
def pic_api_backup_list():
    backups = backup.list_backups()
    return jsonify(backups)


# ==================== Admin - 用户管理 ====================
@app.route('/pic/admin/users')
@admin_required
def pic_admin_users():
    user = get_current_user()
    users = PicUser.get_all()
    return render_template('pic_admin_users.html', user=user, users=users)


@app.route('/pic/admin/user/add', methods=['GET', 'POST'])
@admin_required
def pic_admin_add_user():
    user = get_current_user()
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')
        email = request.form.get('email', '')
        if role not in ('user', 'manager', 'admin'):
            role = 'user'
        uid = PicUser.create(username, password, role=role, email=email)
        if uid:
            UserActionLog.log(user['uid'], user['username'], '添加用户',
                              f'创建新用户: {username} ({uid})，角色: {role}')
            return redirect(url_for('pic_admin_users'))
        return render_template('pic_admin_add_user.html', user=user, error='用户名已存在')
    return render_template('pic_admin_add_user.html', user=user, error=None)


@app.route('/pic/admin/user/<uid>/delete', methods=['POST'])
@admin_required
def pic_admin_delete_user(uid):
    user = get_current_user()
    deleted_user = PicUser.get_by_uid(uid)
    deleted_name = deleted_user.get('username', uid) if deleted_user else uid
    PicUser.delete(uid)
    UserActionLog.log(user['uid'], user['username'], '删除用户',
                      f'删除用户: {deleted_name} ({uid})')
    return redirect(url_for('pic_admin_users'))


@app.route('/pic/admin/user/<uid>/give_points', methods=['POST'])
@admin_required
def pic_admin_give_points(uid):
    user = get_current_user()
    target_user = PicUser.get_by_uid(uid)
    if not target_user:
        return '用户不存在', 404

    points = int(request.form.get('points', 0))
    reason = request.form.get('reason', '').strip()

    if points <= 0 or points > 10:
        return '积分数量必须在1-10之间', 400

    today_count = pic_models.get_admin_today_grant_count(user['uid'])
    if today_count >= 3:
        return '今日发放次数已达上限（每天最多3次）', 403

    if not PicUser.add_points(uid, points, reason=reason, operator=user.get('username', '')):
        return '发放失败', 500

    pic_models.record_admin_grant(user['uid'], uid, points, reason)
    UserActionLog.log(user['uid'], user['username'], '发放积分',
                      f'给用户 {target_user.get("username", uid)} ({uid}) 发放 {points} 积分，原因: {reason}')
    return redirect(url_for('pic_admin_users'))


# ==================== Admin - 申请管理 ====================
@app.route('/pic/admin/applications')
@admin_required
def pic_admin_applications():
    user = get_current_user()
    apps = Application.get_pending()
    blocked_ips = Application.get_blocked_ips()
    return render_template('pic_admin_applications.html', user=user,
                           applications=apps, blocked_ips=blocked_ips)


@app.route('/pic/admin/application/<int:aid>/approve', methods=['POST'])
@admin_required
def pic_admin_approve_application(aid):
    user = get_current_user()
    app_data = Application.get_all()
    app_info = next((a for a in app_data if a.get('id') == aid), None)
    app_username = app_info.get('username', '') if app_info else ''
    Application.approve(aid)
    UserActionLog.log(user['uid'], user['username'], '审核注册申请',
                      f'通过注册申请 ID: {aid}，用户名: {app_username}')
    return redirect(url_for('pic_admin_applications'))


@app.route('/pic/admin/application/<int:aid>/reject', methods=['POST'])
@admin_required
def pic_admin_reject_application(aid):
    user = get_current_user()
    app_data = Application.get_all()
    app_info = next((a for a in app_data if a.get('id') == aid), None)
    app_username = app_info.get('username', '') if app_info else ''
    Application.reject(aid)
    UserActionLog.log(user['uid'], user['username'], '拒绝注册申请',
                      f'拒绝注册申请 ID: {aid}，用户名: {app_username}')
    return redirect(url_for('pic_admin_applications'))


@app.route('/pic/admin/block_ip', methods=['POST'])
@admin_required
def pic_admin_block_ip():
    ip = request.form.get('ip', '')
    if ip:
        Application.block_ip(ip)
    return redirect(url_for('pic_admin_applications'))


@app.route('/pic/admin/unblock_ip/<ip>', methods=['POST'])
@admin_required
def pic_admin_unblock_ip(ip):
    Application.unblock_ip(ip)
    return redirect(url_for('pic_admin_applications'))


# ==================== 封禁系统 ====================
@app.route('/pic/admin/ban/<uid>', methods=['POST'])
@manager_required
def pic_admin_ban(uid):
    user = get_current_user()
    minutes = int(request.form.get('minutes', 60))
    reason = request.form.get('reason', '')
    pic_id = request.form.get('pic_id', '')
    applicant = 'admin' if user.get('role') == 'admin' else user.get('username')

    PicUser.ban_user(uid, minutes, reason, applicant)
    Comment.delete_all_by_user(uid)
    banned_user = PicUser.get_by_uid(uid)
    banned_name = banned_user.get('username', uid) if banned_user else uid
    UserActionLog.log(user['uid'], user['username'], '封禁用户',
                      f'封禁用户 {banned_name} ({uid})，时长: {minutes}分钟，原因: {reason}')

    if pic_id:
        return redirect(url_for('pic_detail', pic_id=int(pic_id)))
    return redirect(url_for('pic_admin_users'))


@app.route('/pic/admin/unban/<uid>', methods=['POST'])
@manager_required
def pic_admin_unban(uid):
    user = get_current_user()
    PicUser.unban_user(uid)
    unbanned_user = PicUser.get_by_uid(uid)
    unbanned_name = unbanned_user.get('username', uid) if unbanned_user else uid
    UserActionLog.log(user['uid'], user['username'], '解除封禁',
                      f'解除用户 {unbanned_name} ({uid}) 的封禁')
    return redirect(url_for('pic_admin_users'))


@app.route('/pic/ban_records')
@manager_required
def pic_ban_records():
    user = get_current_user()
    records = BanRequest.get_all()
    return render_template('pic_ban_records.html', user=user, records=records)


# ==================== 用户列表 & 好友系统 ====================
@app.route('/pic/users')
@login_required
def pic_users():
    user = get_current_user()
    all_users = PicUser.get_all()
    friend_uids = [f.get('uid') for f in user.get('friends', [])]
    return render_template('pic_users.html', user=user, all_users=all_users,
                           friend_uids=friend_uids)


@app.route('/pic/friends')
@login_required
def pic_friends():
    user = get_current_user()
    friends = user.get('friends', [])
    requests = user.get('friend_requests', [])
    return render_template('pic_friends.html', user=user, friends=friends,
                           requests=requests)


@app.route('/pic/friend/add/<target_uid>', methods=['POST'])
@login_required
def pic_add_friend(target_uid):
    user = get_current_user()
    PicUser.send_friend_request(user['uid'], target_uid)
    target = PicUser.get_by_uid(target_uid)
    target_name = target.get('username', target_uid) if target else target_uid
    UserActionLog.log(user['uid'], user['username'], '发送好友请求', f'向用户 {target_name} ({target_uid}) 发送好友请求')
    return redirect(url_for('pic_users'))


@app.route('/pic/friend/accept/<from_uid>', methods=['POST'])
@login_required
def pic_accept_friend(from_uid):
    user = get_current_user()
    PicUser.accept_friend_request(user['uid'], from_uid)
    from_user = PicUser.get_by_uid(from_uid)
    from_name = from_user.get('username', from_uid) if from_user else from_uid
    UserActionLog.log(user['uid'], user['username'], '接受好友请求', f'接受了 {from_name} ({from_uid}) 的好友请求')
    return redirect(url_for('pic_friends'))


@app.route('/pic/friend/reject/<from_uid>', methods=['POST'])
@login_required
def pic_reject_friend(from_uid):
    user = get_current_user()
    PicUser.reject_friend_request(user['uid'], from_uid)
    from_user = PicUser.get_by_uid(from_uid)
    from_name = from_user.get('username', from_uid) if from_user else from_uid
    UserActionLog.log(user['uid'], user['username'], '拒绝好友请求', f'拒绝了 {from_name} ({from_uid}) 的好友请求')
    return redirect(url_for('pic_friends'))


@app.route('/pic/friend/remove/<friend_uid>', methods=['POST'])
@login_required
def pic_remove_friend(friend_uid):
    user = get_current_user()
    PicUser.remove_friend(user['uid'], friend_uid)
    friend = PicUser.get_by_uid(friend_uid)
    friend_name = friend.get('username', friend_uid) if friend else friend_uid
    UserActionLog.log(user['uid'], user['username'], '删除好友', f'删除了好友 {friend_name} ({friend_uid})')
    return redirect(url_for('pic_friends'))


# ==================== 私聊 ====================
@app.route('/pic/chat/<other_uid>')
@login_required
def pic_private_chat(other_uid):
    user = get_current_user()
    other = PicUser.get_by_uid(other_uid)
    if not other:
        return '用户不存在', 404
    friends = [f.get('uid') for f in user.get('friends', [])]
    if other_uid not in friends:
        return '只能和好友聊天', 403

    messages = PrivateChat.get_messages(user['uid'], other_uid)
    PrivateChat.mark_read(user['uid'], other_uid)
    return render_template('pic_private_chat.html', user=user, other=other,
                           messages=messages)


@app.route('/pic/chat/<other_uid>/send', methods=['POST'])
@login_required
def pic_send_private_message(other_uid):
    user = get_current_user()
    content = request.form.get('content', '')
    if content.strip():
        PrivateChat.send_message(user['uid'], user['username'], other_uid, content)
        other = PicUser.get_by_uid(other_uid)
        other_name = other.get('username', other_uid) if other else other_uid
        preview = content[:30] + '...' if len(content) > 30 else content
        UserActionLog.log(user['uid'], user['username'], '发送私聊消息',
                          f'向 {other_name} ({other_uid}) 发送消息: {preview}')
    return redirect(url_for('pic_private_chat', other_uid=other_uid))


@app.route('/pic/chat/<other_uid>/send_points', methods=['POST'])
@login_required
def pic_send_private_points(other_uid):
    user = get_current_user()
    amount = int(request.form.get('amount', 0))
    remark = request.form.get('remark', '').strip()

    success, msg = PrivateChat.send_points(user['uid'], user['username'],
                                            other_uid, amount, remark)
    if success:
        UserActionLog.log(user['uid'], user['username'], '私信转账',
                          f'向 {other_uid} 转账 {amount} 积分{(" - " + remark) if remark else ""}')
    return redirect(url_for('pic_private_chat', other_uid=other_uid))


# ==================== 群聊 ====================
@app.route('/pic/groups')
@login_required
def pic_groups():
    user = get_current_user()
    groups = GroupChat.get_user_groups(user['uid'])

    all_user_groups = user.get('groups', [])
    invitations = []
    for g in all_user_groups:
        if isinstance(g, dict) and 'inviter_uid' in g:
            invitations.append(g)

    return render_template('pic_groups.html', user=user, groups=groups,
                           invitations=invitations)


@app.route('/pic/group/create', methods=['GET', 'POST'])
@login_required
def pic_create_group():
    user = get_current_user()
    if request.method == 'POST':
        name = request.form.get('name', '')
        if name.strip():
            gid = GroupChat.create(user['uid'], user['username'], name)
            UserActionLog.log(user['uid'], user['username'], '创建群聊',
                              f'创建群聊成功，群ID: {gid}，群名称: {name}')
            return redirect(url_for('pic_group_chat', gid=gid))
    return render_template('pic_create_group.html', user=user)


@app.route('/pic/group/<int:gid>')
@login_required
def pic_group_chat(gid):
    user = get_current_user()
    group = GroupChat.get_by_id(gid)
    if not group:
        return '群不存在', 404
    members = [m.get('uid') for m in group.get('members', [])]
    if user['uid'] not in members:
        return '不是群成员', 403
    return render_template('pic_group_chat.html', user=user, group=group)


@app.route('/pic/group/<int:gid>/send', methods=['POST'])
@login_required
def pic_send_group_message(gid):
    user = get_current_user()
    content = request.form.get('content', '')
    if content.strip():
        GroupChat.send_message(gid, user['uid'], user['username'], content)
        group = GroupChat.get_by_id(gid)
        group_name = group.get('name', str(gid)) if group else str(gid)
        preview = content[:30] + '...' if len(content) > 30 else content
        UserActionLog.log(user['uid'], user['username'], '发送群聊消息',
                          f'在群 {group_name} (ID: {gid}) 发送消息: {preview}')
    return redirect(url_for('pic_group_chat', gid=gid))


@app.route('/pic/group/<int:gid>/red_packet/send', methods=['POST'])
@login_required
def pic_send_group_red_packet(gid):
    user = get_current_user()
    group = pic_models.GroupChat.get_by_id(gid)
    if not group:
        return '群不存在', 404
    members = [m.get('uid') for m in group.get('members', [])]
    if user['uid'] not in members:
        return '不是群成员', 403

    rp_type = request.form.get('rp_type', 'lucky')
    total_amount = int(request.form.get('total_amount', 0))
    total_count = int(request.form.get('total_count', 1))
    remark = request.form.get('remark', '').strip()
    password = request.form.get('password', '').strip()
    target_uid = request.form.get('target_uid', '').strip()

    if total_amount <= 0:
        return '金额必须大于0', 400

    target_name = ''
    if rp_type == 'single':
        target = PicUser.get_by_uid(target_uid)
        if not target:
            return '目标用户不存在', 400
        target_name = target.get('username', '')
        total_count = 1

    if rp_type == 'password' and not password:
        return '口令红包必须设置口令', 400

    rpid, err = pic_models.RedPacket.create(
        gid=gid,
        sender_uid=user['uid'],
        sender_name=user['username'],
        rp_type=rp_type,
        total_amount=total_amount,
        total_count=total_count,
        password=password,
        remark=remark,
        target_uid=target_uid,
        target_name=target_name
    )
    if err:
        return err, 400

    pic_models.GroupChat.send_red_packet_msg(
        gid, user['uid'], user['username'],
        rpid, rp_type, total_amount, total_count, remark, target_name
    )
    group_name = group.get('name', str(gid))
    UserActionLog.log(user['uid'], user['username'], '发群红包',
                      f'在群 {group_name} (ID: {gid}) 发{rp_type}红包，金额: {total_amount}，个数: {total_count}')
    return redirect(url_for('pic_group_chat', gid=gid))


@app.route('/pic/red_packet/<int:rpid>/grab', methods=['POST'])
@login_required
def pic_grab_red_packet(rpid):
    user = get_current_user()
    password = request.form.get('password', '').strip()

    success, msg, amount = pic_models.RedPacket.grab(
        rpid, user['uid'], user['username'], password
    )

    referrer = request.referrer or url_for('pic_groups')
    if success:
        UserActionLog.log(user['uid'], user['username'], '抢红包',
                          f'抢到红包 {rpid}，金额: {amount} 积分')
    return redirect(referrer)


@app.route('/pic/group/<int:gid>/invite', methods=['GET', 'POST'])
@login_required
def pic_group_invite(gid):
    user = get_current_user()
    group = GroupChat.get_by_id(gid)
    if not group or group.get('creator_uid') != user['uid']:
        return '只有群主可以邀请', 403

    if request.method == 'POST':
        target_uid = request.form.get('target_uid', '')
        GroupChat.invite(gid, user['uid'], target_uid)
        target = PicUser.get_by_uid(target_uid)
        target_name = target.get('username', target_uid) if target else target_uid
        UserActionLog.log(user['uid'], user['username'], '群聊邀请',
                          f'邀请 {target_name} ({target_uid}) 加入群 {group.get("name", "")} (ID: {gid})')
        return redirect(url_for('pic_group_chat', gid=gid))

    friends = user.get('friends', [])
    members = [m.get('uid') for m in group.get('members', [])]
    inviteable = [f for f in friends if f.get('uid') not in members]
    return render_template('pic_group_invite.html', user=user, group=group,
                           inviteable=inviteable)


@app.route('/pic/group/<int:gid>/accept', methods=['POST'])
@login_required
def pic_accept_group_invite(gid):
    user = get_current_user()
    GroupChat.accept_invitation(gid, user['uid'])
    group = GroupChat.get_by_id(gid)
    group_name = group.get('name', str(gid)) if group else str(gid)
    UserActionLog.log(user['uid'], user['username'], '加入群聊',
                      f'接受邀请加入群 {group_name} (ID: {gid})')
    return redirect(url_for('pic_groups'))


@app.route('/pic/group/<int:gid>/delete', methods=['POST'])
@login_required
def pic_delete_group(gid):
    user = get_current_user()
    group = GroupChat.get_by_id(gid)
    group_name = group.get('name', str(gid)) if group else str(gid)
    GroupChat.delete_group(gid, user['uid'])
    UserActionLog.log(user['uid'], user['username'], '删除群聊',
                      f'删除群聊 {group_name} (ID: {gid})')
    return redirect(url_for('pic_groups'))


# ==================== 视频转码工具 ====================
@app.route('/pic/convert')
@login_required
def pic_convert():
    user = get_current_user()
    return render_template('pic_convert.html', user=user,
                           ffmpeg_available=video_converter.is_ffmpeg_available())


@app.route('/pic/convert/upload', methods=['POST'])
@login_required
def pic_convert_upload():
    user = get_current_user()

    if not video_converter.is_ffmpeg_available():
        return jsonify({'success': False, 'error': 'FFmpeg 不可用，视频转码功能已禁用'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})

    if not allowed_file(file.filename, ALLOWED_VIDEO_EXT):
        return jsonify({'success': False, 'error': '不支持的文件格式'})

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    task_id = str(uuid.uuid4())
    input_filename = f'{task_id}_input.{ext}'
    input_path = os.path.join(video_converter.CONVERT_DIR, input_filename)
    file.save(input_path)

    output_filename = f'{task_id}_output.mp4'
    output_path = os.path.join(video_converter.CONVERT_DIR, output_filename)

    crf = int(request.form.get('crf', 23))
    preset = request.form.get('preset', 'medium')

    info = video_converter.probe_video(input_path)
    current_codec = info.get('codec_name', 'unknown')

    if current_codec == 'h264':
        already_h264 = True
    else:
        already_h264 = False
        video_converter.start_convert_task(task_id, input_path, output_path, crf, preset)

    return jsonify({
        'success': True,
        'task_id': task_id,
        'already_h264': already_h264,
        'current_codec': current_codec,
        'video_info': {
            'codec': info.get('codec_name', 'unknown'),
            'width': info.get('width', 'unknown'),
            'height': info.get('height', 'unknown'),
            'duration': info.get('duration', 'unknown')
        },
        'download_url': url_for('pic_converted_file', filename=output_filename) if already_h264 else None
    })


@app.route('/pic/convert/status/<task_id>')
@login_required
def pic_convert_status(task_id):
    task = video_converter.get_task_status(task_id)
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'})

    output_filename = f'{task_id}_output.mp4'
    download_url = None
    if task['status'] == 'completed':
        download_url = url_for('pic_converted_file', filename=output_filename)

    return jsonify({
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'error': task.get('error'),
        'download_url': download_url
    })


@app.route('/pic/converted/<filename>')
@login_required
def pic_converted_file(filename):
    return send_from_directory(video_converter.CONVERT_DIR, filename)


# ==================== 初始化 & 启动 ====================
if __name__ == '__main__':
    init_default_admin()
    app.run(debug=True, host='0.0.0.0', port=5001)
