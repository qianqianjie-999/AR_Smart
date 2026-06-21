"""文件上传路由"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, g, request, send_file, current_app
from werkzeug.utils import secure_filename
from functools import wraps
import jwt

from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def token_optional(f):
    """Optional token auth: try to decode token, but don't require it."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = jwt.decode(token, current_app.config.get('SECRET_KEY', 'arms-secret-key'), algorithms=['HS256'])
                g.user_id = payload.get('user_id')
                g.username = payload.get('username')
            except Exception:
                pass
        return f(*args, **kwargs)
    return decorated


@upload_bp.route('/', methods=['POST'])
@login_required
def upload_files():
    """上传文件（支持单文件和多文件）"""
    # Support both single file ('file') and multi-file ('files')
    if 'file' in request.files:
        files = [request.files['file']]
    elif 'files' in request.files:
        files = request.files.getlist('files')
    else:
        return error_response('请选择要上传的文件')

    if not files or len(files) == 0 or files[0].filename == '':
        return error_response('请选择要上传的文件')

    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    uploaded = []
    for file in files:
        if file.filename == '':
            continue

        if not allowed_file(file.filename):
            return error_response(f'不支持的文件类型: {file.filename}')

        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(upload_dir, new_filename)
        file.save(filepath)

        uploaded.append({
            'original_name': file.filename,
            'filename': new_filename,
            'url': f'/api/upload/{new_filename}',
            'size': os.path.getsize(filepath),
        })

    return success_response(uploaded[0] if len(uploaded) == 1 else uploaded, '上传成功')


@upload_bp.route('/<filename>', methods=['GET'])
@token_optional
def download_file(filename):
    """下载/预览文件（支持 token 参数进行认证）"""
    filename = secure_filename(filename)
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    filepath = os.path.join(upload_dir, filename)
    if not os.path.exists(filepath):
        filepath = os.path.join(upload_dir, os.path.basename(filename))
        if not os.path.exists(filepath):
            return error_response('文件不存在', 404)

    return send_file(filepath)


@upload_bp.route('/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """删除文件"""
    filename = secure_filename(filename)
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    filepath = os.path.join(upload_dir, filename)

    if not os.path.exists(filepath):
        filepath = os.path.join(upload_dir, os.path.basename(filename))
        if not os.path.exists(filepath):
            return error_response('文件不存在', 404)

    try:
        os.remove(filepath)
    except OSError as e:
        return error_response(f'删除文件失败: {str(e)}', 500)

    return success_response(message='删除文件成功')
