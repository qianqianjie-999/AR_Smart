import bcrypt
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app import db
from app.models.system import SysUser, SysRole, SysPermission, SysRolePermission
from app.utils.auth import generate_token, login_required
from app.utils.helpers import success_response, error_response, log_operation

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response('用户名和密码不能为空')

    user = SysUser.query.filter_by(username=username).first()
    if not user:
        return error_response('用户名或密码错误')

    if user.status != 1:
        return error_response('账号已被禁用，请联系管理员')

    # bcrypt 验证密码
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return error_response('用户名或密码错误')
    except (ValueError, AttributeError):
        return error_response('密码验证异常，请联系管理员')

    # 获取角色信息
    role = SysRole.query.get(user.role_id) if user.role_id else None
    role_code = role.role_code if role else 'viewer'
    role_name = role.role_name if role else '普通查看'

    # 获取用户权限列表
    permissions = _get_user_permissions(user.role_id)

    # 生成token
    token = generate_token(user.id, user.username, role_code)

    # 更新登录信息
    user.last_login = datetime.now()
    user.login_ip = request.remote_addr
    db.session.commit()

    log_operation('认证', '登录', f'{username} 登录系统')

    return success_response({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'phone': user.phone,
            'email': user.email,
            'avatar': user.avatar,
            'dept': user.dept,
            'role_id': user.role_id,
            'role_code': role_code,
            'role_name': role_name,
            'status': user.status,
        },
        'permissions': permissions,
    }, message='登录成功')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    log_operation('认证', '登出', f'{g.current_username} 登出系统')
    return success_response(message='登出成功')


@auth_bp.route('/userinfo', methods=['GET'])
@login_required
def userinfo():
    """获取当前用户信息"""
    user = SysUser.query.get(g.current_user_id)
    if not user:
        return error_response('用户不存在', code=404)

    role = SysRole.query.get(user.role_id) if user.role_id else None
    permissions = _get_user_permissions(user.role_id)

    return success_response({
        'user': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'phone': user.phone,
            'email': user.email,
            'avatar': user.avatar,
            'dept': user.dept,
            'role_id': user.role_id,
            'role_code': role.role_code if role else 'viewer',
            'role_name': role.role_name if role else '普通查看',
            'status': user.status,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
        },
        'permissions': permissions,
    })


@auth_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return error_response('旧密码和新密码不能为空')

    if len(new_password) < 6:
        return error_response('新密码长度不能少于6位')

    user = SysUser.query.get(g.current_user_id)
    if not user:
        return error_response('用户不存在', code=404)

    # 验证旧密码
    try:
        if not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
            return error_response('旧密码错误')
    except (ValueError, AttributeError):
        return error_response('密码验证异常，请联系管理员')

    # 更新密码
    user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.commit()

    log_operation('认证', '修改密码', f'{g.current_username} 修改密码')
    return success_response(message='密码修改成功')


def _get_user_permissions(role_id):
    """获取用户权限列表"""
    if not role_id:
        return []

    perms = (
        db.session.query(SysPermission)
        .join(SysRolePermission, SysRolePermission.perm_id == SysPermission.id)
        .filter(SysRolePermission.role_id == role_id)
        .order_by(SysPermission.sort_order)
        .all()
    )

    return [
        {
            'id': p.id,
            'perm_name': p.perm_name,
            'perm_code': p.perm_code,
            'perm_type': p.perm_type,
            'parent_id': p.parent_id,
            'module': p.module,
            'path': p.path,
            'icon': p.icon,
        }
        for p in perms
    ]
