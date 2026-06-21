"""JWT认证工具"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app


def generate_token(user_id, username, role_code=None, permissions=None):
    """生成JWT access token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role_code': role_code,
        'permissions': permissions or [],
        'exp': datetime.utcnow() + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=2)),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def generate_refresh_token(user_id, username):
    """生成JWT refresh token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=7)),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def login_required(f):
    """JWT认证装饰器：验证Token并将用户信息存入g对象"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            g.current_user_id = payload.get('user_id')
            g.current_username = payload.get('username')
            g.current_role_code = payload.get('role_code')
            g.current_permissions = payload.get('permissions', [])
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': 'Token已过期，请重新登录'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': '无效的Token'}), 401
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """角色权限检查装饰器（需配合@login_required使用）"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = getattr(g, 'current_role_code', None)
            # 管理员拥有所有权限
            if user_role == 'admin':
                return f(*args, **kwargs)
            if user_role not in roles:
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_permission(perm_code):
    """权限码检查装饰器（需配合@login_required使用）"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = getattr(g, 'current_role_code', None)
            if user_role == 'admin':
                return f(*args, **kwargs)
            permissions = getattr(g, 'current_permissions', [])
            if perm_code not in permissions:
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
