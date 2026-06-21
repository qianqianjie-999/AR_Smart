import os
import json
import uuid
from datetime import datetime
from flask import jsonify, request, g, current_app
from app import db


def success_response(data=None, message='操作成功', **kwargs):
    """统一成功响应"""
    resp = {'code': 200, 'message': message, 'data': data}
    resp.update(kwargs)
    return jsonify(resp)


def error_response(message, code=400):
    """统一错误响应"""
    return jsonify({'code': code, 'message': message}), code


def paginate(query, page=1, page_size=20):
    """分页处理 - 使用offset/limit方式

    Returns:
        dict with list, total, page, page_size
    """
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size,
    }


def paginate_query(query, page=None, per_page=None):
    """分页处理（兼容旧版）- 使用Flask-SQLAlchemy paginate

    Returns:
        dict with items, total, page, per_page, pages
    """
    page = page or request.args.get('page', 1, type=int)
    per_page = per_page or request.args.get('pageSize', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'png', 'jpg', 'jpeg', 'gif', 'bmp',
    'zip', 'rar', '7z',
}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, subdir=''):
    """保存上传文件

    Returns:
        str: 相对文件路径，失败返回 None
    """
    if file is None or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subdir)
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return os.path.join(subdir, filename)


def log_operation(*args, **kwargs):
    """记录操作日志

    Supports two call patterns:
    1. Old: log_operation(module, action, content)
    2. New: log_operation(user_id=..., username=..., module=..., action=..., content=...)
    """
    from app.models.system import OperationLog

    if kwargs:
        # New-style: keyword arguments
        user_id = kwargs.get('user_id')
        username = kwargs.get('username', '')
        module = kwargs.get('module', '')
        action = kwargs.get('action', '')
        content = kwargs.get('content', '')
        duration = kwargs.get('duration', 0)
    elif len(args) >= 2:
        # Old-style: log_operation(module, action, content)
        module = args[0] if len(args) > 0 else ''
        action = args[1] if len(args) > 1 else ''
        content = args[2] if len(args) > 2 else ''
        duration = 0
        try:
            user_id = getattr(g, 'current_user_id', None)
            username = getattr(g, 'current_username', None)
        except RuntimeError:
            user_id = None
            username = None
    else:
        return  # Not enough args

    if isinstance(content, (dict, list)):
        content = json.dumps(content, ensure_ascii=False)

    try:
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')[:500]
    except RuntimeError:
        ip_address = None
        user_agent = None

    log = OperationLog(
        user_id=user_id,
        username=username,
        module=module,
        action=action,
        content=str(content) if content else '',
        ip_address=ip_address,
        user_agent=user_agent,
        duration=duration,
    )
    db.session.add(log)
    db.session.commit()


def validate_date(date_str, formats=None):
    """验证并解析日期字符串"""
    if formats is None:
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None
