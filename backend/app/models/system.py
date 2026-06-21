from datetime import datetime
from app import db


class SysConfig(db.Model):
    __tablename__ = 'sys_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class SysRole(db.Model):
    __tablename__ = 'sys_role'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(50), nullable=False)
    role_code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_system = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    users = db.relationship('SysUser', backref='role', lazy=True)


class SysUser(db.Model):
    __tablename__ = 'sys_user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    avatar = db.Column(db.String(500))
    dept = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey('sys_role.id'))
    status = db.Column(db.Integer, default=1)
    last_login = db.Column(db.DateTime)
    login_ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class SysPermission(db.Model):
    __tablename__ = 'sys_permission'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    perm_name = db.Column(db.String(100), nullable=False)
    perm_code = db.Column(db.String(100), unique=True, nullable=False)
    perm_type = db.Column(db.String(20))
    parent_id = db.Column(db.Integer, default=0)
    module = db.Column(db.String(50))
    path = db.Column(db.String(200))
    icon = db.Column(db.String(100))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)


class SysRolePermission(db.Model):
    __tablename__ = 'sys_role_permission'

    role_id = db.Column(db.Integer, db.ForeignKey('sys_role.id'), primary_key=True, nullable=False)
    perm_id = db.Column(db.Integer, db.ForeignKey('sys_permission.id'), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class OperationLog(db.Model):
    __tablename__ = 'operation_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(100))
    module = db.Column(db.String(50))
    action = db.Column(db.String(50))
    content = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
