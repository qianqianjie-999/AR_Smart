"""催款模板管理路由"""

from flask import Blueprint, g, request

from app import db
from app.models.template import CollectionTemplate
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

template_bp = Blueprint('template', __name__, url_prefix='/api/template')


@template_bp.route('/', methods=['GET'])
@login_required
def list_templates():
    """模板列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    template_type = request.args.get('template_type', '')

    query = CollectionTemplate.query.filter(CollectionTemplate.is_deleted == 0)

    if template_type:
        query = query.filter(CollectionTemplate.template_type == template_type)

    query = query.order_by(CollectionTemplate.is_default.desc(), CollectionTemplate.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        data.append({
            'id': item.id,
            'name': item.name,
            'template_type': item.template_type,
            'subject': item.subject,
            'content': item.content,
            'is_default': item.is_default,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
            'updated_at': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@template_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_template(id):
    """模板详情"""
    template = CollectionTemplate.query.filter_by(id=id, is_deleted=0).first()
    if not template:
        return error_response('模板不存在', 404)

    return success_response({
        'id': template.id,
        'name': template.name,
        'template_type': template.template_type,
        'subject': template.subject,
        'content': template.content,
        'is_default': template.is_default,
        'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S') if template.created_at else None,
        'updated_at': template.updated_at.strftime('%Y-%m-%d %H:%M:%S') if template.updated_at else None,
    })


@template_bp.route('/', methods=['POST'])
@login_required
def create_template():
    """创建模板"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    name = json_data.get('name', '')
    if not name:
        return error_response('模板名称不能为空')

    # 如果设为默认，先取消其他默认
    if json_data.get('is_default', 0):
        CollectionTemplate.query.filter_by(
            template_type=json_data.get('template_type', '催款函'),
            is_default=1
        ).update({'is_default': 0})

    template = CollectionTemplate(
        name=name,
        template_type=json_data.get('template_type', '催款函'),
        subject=json_data.get('subject', ''),
        content=json_data.get('content', ''),
        is_default=json_data.get('is_default', 0),
        created_by=getattr(g, 'current_user_id', None),
    )
    db.session.add(template)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='模板管理',
        action='创建模板',
        content=f'创建模板: {name}',
    )

    return success_response({'id': template.id}, '创建模板成功')


@template_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_template(id):
    """编辑模板"""
    template = CollectionTemplate.query.filter_by(id=id, is_deleted=0).first()
    if not template:
        return error_response('模板不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    # 如果设为默认，先取消其他默认
    if json_data.get('is_default', 0):
        CollectionTemplate.query.filter_by(
            template_type=template.template_type,
            is_default=1
        ).filter(CollectionTemplate.id != id).update({'is_default': 0})

    template.name = json_data.get('name', template.name)
    template.template_type = json_data.get('template_type', template.template_type)
    template.subject = json_data.get('subject', template.subject)
    template.content = json_data.get('content', template.content)
    template.is_default = json_data.get('is_default', template.is_default)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='模板管理',
        action='编辑模板',
        content=f'编辑模板: {template.name}',
    )

    return success_response(message='编辑模板成功')


@template_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_template(id):
    """删除模板（软删除）"""
    template = CollectionTemplate.query.filter_by(id=id, is_deleted=0).first()
    if not template:
        return error_response('模板不存在', 404)

    template.is_deleted = 1
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='模板管理',
        action='删除模板',
        content=f'删除模板: {template.name}',
    )

    return success_response(message='删除模板成功')


@template_bp.route('/types', methods=['GET'])
@login_required
def get_template_types():
    """获取模板类型列表"""
    types = ['催款函', '律师函', '对账单', '提醒函', '其他']
    return success_response(types)


@template_bp.route('/default/<template_type>', methods=['GET'])
@login_required
def get_default_template(template_type):
    """获取默认模板"""
    template = CollectionTemplate.query.filter_by(
        template_type=template_type,
        is_default=1,
        is_deleted=0
    ).first()

    if not template:
        # 返回默认的催款函模板
        return success_response({
            'id': 0,
            'name': '默认催款函',
            'template_type': template_type,
            'subject': f'{template_type} - {{{{合同名称}}}}',
            'content': f'尊敬的{{{{客户名称}}}}：\n\n截至{{{{日期}}}}，贵公司与我方签订的合同「{{{{合同名称}}}}」尚欠款项{{{{欠款金额}}}}元，已逾期{{{{逾期天数}}}}天。\n\n请贵公司于收到本函后7个工作日内安排付款，如有疑问请及时与我方联系。\n\n联系人：{{{{联系人}}}}\n联系电话：{{{{联系电话}}}}\n\n特此函告。',
            'is_default': 1,
        })

    return success_response({
        'id': template.id,
        'name': template.name,
        'template_type': template.template_type,
        'subject': template.subject,
        'content': template.content,
        'is_default': template.is_default,
    })