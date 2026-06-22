import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 加载 .env 文件（在导入 config 之前）
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

db = SQLAlchemy()


def create_app(config_name=None):
    """Flask应用工厂"""
    app = Flask(__name__)

    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    from app.config import config
    app.config.from_object(config.get(config_name, config['default']))

    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 配置日志
    _setup_logging(app)

    # 注册蓝图（延迟导入避免循环依赖）
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.contract import contract_bp
    from app.routes.payment import payment_bp
    from app.routes.invoice import invoice_bp
    from app.routes.collection import collection_bp
    from app.routes.limitation import limitation_bp
    from app.routes.report import report_bp
    from app.routes.system import system_bp
    from app.routes.upload import upload_bp
    from app.routes.template import template_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(contract_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(limitation_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(template_bp)

    # 注册错误处理器
    _register_error_handlers(app)

    # 初始化定时任务
    _init_scheduler(app)

    return app


def _setup_logging(app):
    """配置日志"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    if not app.debug:
        handler = logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(handler)


def _register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'code': 400, 'message': '请求参数错误'}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'code': 401, 'message': '未授权访问'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'code': 403, 'message': '权限不足'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'message': '资源不存在'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'code': 405, 'message': '请求方法不允许'}), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'code': 413, 'message': '上传文件过大'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Internal Server Error: {e}')
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Unhandled Exception: {e}', exc_info=True)
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500


def _init_scheduler(app):
    """初始化APScheduler定时任务"""
    scheduler = BackgroundScheduler(daemon=True)

    @scheduler.scheduled_job('cron', hour=2, minute=0, id='daily_limitation_update')
    def daily_task():
        """每天凌晨2点执行定时任务：
        1. 更新所有时效记录的天数和状态
        2. 更新付款节点状态
        3. 检查并生成预警通知
        """
        with app.app_context():
            try:
                from app.services.limitation_service import update_all_limitations, check_warnings
                from app.services.payment_service import update_payment_node_status
                from app.models.contract import Contract

                app.logger.info('[Scheduler] 开始执行每日定时任务...')

                # 1. 更新时效状态
                limitation_count = update_all_limitations()
                app.logger.info(f'[Scheduler] 更新时效记录: {limitation_count} 条')

                # 2. 更新所有合同的付款节点状态
                contracts = Contract.query.filter_by(is_deleted=0).all()
                node_update_count = 0
                for contract in contracts:
                    count = update_payment_node_status(contract.id)
                    node_update_count += count
                app.logger.info(f'[Scheduler] 更新付款节点状态: {node_update_count} 个')

                # 3. 检查预警
                warnings = check_warnings()
                app.logger.info(f'[Scheduler] 生成预警通知: {len(warnings)} 条')

                app.logger.info('[Scheduler] 每日定时任务完成')
            except Exception as e:
                app.logger.error(f'[Scheduler] 定时任务异常: {e}', exc_info=True)

    scheduler.start()
    app.logger.info('[Scheduler] 定时任务已启动 (每天 02:00)')
