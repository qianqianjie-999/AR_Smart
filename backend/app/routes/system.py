"""系统管理路由"""

from flask import Blueprint, g, request, send_file
from sqlalchemy import func

from app import db
from app.models import SysUser, SysRole, SysPermission, SysRolePermission, SysConfig, OperationLog
from app.utils.auth import login_required, require_role
from app.utils.helpers import success_response, error_response, paginate, log_operation
from app.config import Config

system_bp = Blueprint('system', __name__, url_prefix='/api/system')


# ==================== 用户管理 ====================

@system_bp.route('/users', methods=['GET'])
@login_required
@require_role('admin')
def list_users():
    """用户列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = SysUser.query.order_by(SysUser.created_at.desc())
    result = paginate(query, page=page, page_size=page_size)

    data = []
    for u in result['list']:
        role = SysRole.query.get(u.role_id) if u.role_id else None
        data.append({
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name,
            'phone': u.phone,
            'email': u.email,
            'avatar': u.avatar,
            'dept': u.dept,
            'role_id': u.role_id,
            'role_name': role.role_name if role else '',
            'status': u.status,
            'last_login': u.last_login.strftime('%Y-%m-%d %H:%M:%S') if u.last_login else None,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@system_bp.route('/users', methods=['POST'])
@login_required
@require_role('admin')
def create_user():
    """创建用户"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    username = json_data.get('username', '')
    password = json_data.get('password', '')
    if not username or not password:
        return error_response('用户名和密码不能为空')

    existing = SysUser.query.filter_by(username=username).first()
    if existing:
        return error_response('用户名已存在')

    try:
        import bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(password)

    user = SysUser(
        username=username,
        password=hashed,
        real_name=json_data.get('real_name', ''),
        phone=json_data.get('phone', ''),
        email=json_data.get('email', ''),
        avatar=json_data.get('avatar', ''),
        dept=json_data.get('dept', ''),
        role_id=json_data.get('role_id'),
        status=json_data.get('status', 1),
    )
    db.session.add(user)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='创建用户',
        content=f'创建用户: {username}',
    )

    return success_response({'id': user.id}, '创建用户成功')


@system_bp.route('/users/<int:id>', methods=['PUT'])
@login_required
@require_role('admin')
def update_user(id):
    """编辑用户"""
    user = SysUser.query.get(id)
    if not user:
        return error_response('用户不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    user.real_name = json_data.get('real_name', user.real_name)
    user.phone = json_data.get('phone', user.phone)
    user.email = json_data.get('email', user.email)
    user.avatar = json_data.get('avatar', user.avatar)
    user.dept = json_data.get('dept', user.dept)
    user.role_id = json_data.get('role_id', user.role_id)
    user.status = json_data.get('status', user.status)

    new_password = json_data.get('password')
    if new_password:
        try:
            import bcrypt
            user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except ImportError:
            from werkzeug.security import generate_password_hash
            user.password = generate_password_hash(new_password)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='编辑用户',
        content=f'编辑用户: {user.username}',
    )

    return success_response(message='编辑用户成功')


@system_bp.route('/users/<int:id>', methods=['DELETE'])
@login_required
@require_role('admin')
def delete_user(id):
    """删除/禁用用户"""
    user = SysUser.query.get(id)
    if not user:
        return error_response('用户不存在', 404)

    # 软删除：设置 status=0 禁用
    user.status = 0
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='删除用户',
        content=f'禁用用户: {user.username}',
    )

    return success_response(message='删除用户成功')


# ==================== 角色管理 ====================

@system_bp.route('/roles', methods=['GET'])
@login_required
@require_role('admin')
def list_roles():
    """角色列表"""
    roles = SysRole.query.order_by(SysRole.created_at.desc()).all()
    data = []
    for r in roles:
        data.append({
            'id': r.id,
            'role_name': r.role_name,
            'role_code': r.role_code,
            'description': r.description,
            'is_system': r.is_system,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else None,
        })
    return success_response(data)


@system_bp.route('/roles', methods=['POST'])
@login_required
@require_role('admin')
def create_role():
    """创建角色"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    role_name = json_data.get('role_name', '')
    role_code = json_data.get('role_code', '')
    if not role_name or not role_code:
        return error_response('角色名称和编码不能为空')

    existing = SysRole.query.filter_by(role_code=role_code).first()
    if existing:
        return error_response('角色编码已存在')

    role = SysRole(
        role_name=role_name,
        role_code=role_code,
        description=json_data.get('description', ''),
        is_system=json_data.get('is_system', 0),
    )
    db.session.add(role)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='创建角色',
        content=f'创建角色: {role_name}',
    )

    return success_response({'id': role.id}, '创建角色成功')


@system_bp.route('/roles/<int:id>', methods=['PUT'])
@login_required
@require_role('admin')
def update_role(id):
    """编辑角色"""
    role = SysRole.query.get(id)
    if not role:
        return error_response('角色不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    role.role_name = json_data.get('role_name', role.role_name)
    role.role_code = json_data.get('role_code', role.role_code)
    role.description = json_data.get('description', role.description)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='编辑角色',
        content=f'编辑角色: {role.role_name}',
    )

    return success_response(message='编辑角色成功')


@system_bp.route('/roles/<int:id>', methods=['DELETE'])
@login_required
@require_role('admin')
def delete_role(id):
    """删除角色"""
    role = SysRole.query.get(id)
    if not role:
        return error_response('角色不存在', 404)

    # 检查是否有用户使用该角色
    users_with_role = SysUser.query.filter_by(role_id=id).count()
    if users_with_role > 0:
        return error_response(f'该角色已被{users_with_role}个用户使用,无法删除')

    # 检查是否为系统内置角色
    if role.is_system == 1:
        return error_response('系统内置角色无法删除')

    # 删除角色权限关联
    SysRolePermission.query.filter_by(role_id=id).delete()

    db.session.delete(role)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='删除角色',
        content=f'删除角色: {role.role_name}',
    )

    return success_response(message='删除角色成功')


@system_bp.route('/roles/<int:id>/permissions', methods=['PUT'])
@login_required
@require_role('admin')
def assign_permissions(id):
    """分配权限"""
    role = SysRole.query.get(id)
    if not role:
        return error_response('角色不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    perm_ids = json_data.get('perm_ids', [])

    # 清空现有权限
    SysRolePermission.query.filter_by(role_id=id).delete()

    # 分配新权限
    for perm_id in perm_ids:
        rp = SysRolePermission(role_id=id, perm_id=perm_id)
        db.session.add(rp)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='分配权限',
        content=f'为角色 {role.role_name} 分配权限',
    )

    return success_response(message='分配权限成功')


# ==================== 权限管理 ====================

@system_bp.route('/permissions', methods=['GET'])
@login_required
@require_role('admin')
def list_permissions():
    """权限列表（树形结构）"""
    perms = SysPermission.query.order_by(SysPermission.sort_order).all()

    # Build tree
    perm_map = {}
    for p in perms:
        perm_map[p.id] = {
            'id': p.id,
            'perm_name': p.perm_name,
            'perm_code': p.perm_code,
            'perm_type': p.perm_type,
            'parent_id': p.parent_id,
            'module': p.module,
            'path': p.path,
            'icon': p.icon,
            'sort_order': p.sort_order,
            'children': [],
        }

    tree = []
    for p in perms:
        node = perm_map[p.id]
        if p.parent_id and p.parent_id in perm_map:
            perm_map[p.parent_id]['children'].append(node)
        else:
            tree.append(node)

    return success_response(tree)


# ==================== 操作日志 ====================

@system_bp.route('/logs', methods=['GET'])
@login_required
@require_role('admin')
def list_logs():
    """操作日志（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    module = request.args.get('module', '')
    action = request.args.get('action', '')
    date_start = request.args.get('date_start', '')
    date_end = request.args.get('date_end', '')
    user_id = request.args.get('user_id', type=int)

    query = OperationLog.query

    if module:
        query = query.filter(OperationLog.module == module)
    if action:
        query = query.filter(OperationLog.action == action)
    if date_start:
        query = query.filter(func.date(OperationLog.created_at) >= date_start)
    if date_end:
        query = query.filter(func.date(OperationLog.created_at) <= date_end)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)

    query = query.order_by(OperationLog.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for l in result['list']:
        data.append({
            'id': l.id,
            'user_id': l.user_id,
            'username': l.username,
            'module': l.module,
            'action': l.action,
            'content': l.content,
            'ip_address': l.ip_address,
            'duration': l.duration,
            'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


# ==================== 系统配置 ====================

@system_bp.route('/config', methods=['GET'])
@login_required
@require_role('admin')
def list_config():
    """系统配置列表"""
    configs = SysConfig.query.all()
    data = {}
    for c in configs:
        data[c.config_key] = c.config_value
    return success_response(data)


@system_bp.route('/config', methods=['PUT'])
@login_required
@require_role('admin')
def update_config():
    """批量更新配置"""
    json_data = request.get_json(silent=True)
    if not json_data or not isinstance(json_data, dict):
        return error_response('请提供有效的配置数据')

    for key, value in json_data.items():
        config = SysConfig.query.filter_by(config_key=key).first()
        if config:
            config.config_value = str(value)
        else:
            config = SysConfig(config_key=key, config_value=str(value))
            db.session.add(config)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='系统管理',
        action='更新配置',
        content='批量更新系统配置',
    )

    return success_response(message='更新配置成功')


# ==================== 数据库备份 ====================

@system_bp.route('/backup', methods=['GET'])
@login_required
@require_role('admin')
def backup():
    """数据库备份（返回SQL文件）"""
    import subprocess
    import tempfile
    import os
    from datetime import datetime as dt

    db_url = Config.SQLALCHEMY_DATABASE_URI

    # Parse mysql+pymysql://user:password@host:port/dbname
    # Format: mysql+pymysql://root:@127.0.0.1:3306/arms_db
    try:
        url_part = db_url.replace('mysql+pymysql://', '')
        creds_host, db_name = url_part.rsplit('/', 1)
        if ':' in creds_host.rsplit('@', 1)[0] if '@' in creds_host else True:
            # user:password@host:port
            user_pass, host_port = creds_host.split('@')
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
            else:
                user, password = user_pass, ''
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host, port = host_port, '3306'
    except Exception:
        return error_response('无法解析数据库连接字符串', 500)

    tmp_file = tempfile.NamedTemporaryFile(suffix='.sql', delete=False)
    tmp_file.close()

    try:
        cmd = ['mysqldump', '-h', host, '-P', port, '-u', user]
        if password:
            cmd.extend(['-p' + password])
        cmd.append(db_name)

        with open(tmp_file.name, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return error_response(f'备份失败: {result.stderr}', 500)

        log_operation(
            user_id=g.get('current_user_id'),
            username=g.get('current_username', ''),
            module='系统管理',
            action='数据库备份',
            content='数据库备份',
        )

        return send_file(
            tmp_file.name,
            mimetype='application/sql',
            as_attachment=True,
            download_name=f'backup_{dt.now().strftime("%Y%m%d_%H%M%S")}.sql',
        )
    except Exception as e:
        return error_response(f'备份失败: {str(e)}', 500)
    finally:
        try:
            os.unlink(tmp_file.name)
        except OSError:
            pass
