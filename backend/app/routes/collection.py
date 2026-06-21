"""催款管理路由"""

from datetime import date, timedelta
from flask import Blueprint, g, request

from app import db
from app.models import Contract, CollectionRecord, LimitationRecord
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

collection_bp = Blueprint('collection', __name__, url_prefix='/api/collection')


def _parse_date(date_val):
    """Helper to parse a date value (string or date object)."""
    if date_val is None:
        return None
    if isinstance(date_val, date):
        return date_val
    try:
        from datetime import datetime as dt
        return dt.strptime(str(date_val), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _interrupt_limitation(contract_id, interrupt_date, interrupt_type='催款中断'):
    """Trigger limitation interruption from collection action."""
    current_limitation = LimitationRecord.query.filter_by(contract_id=contract_id).order_by(
        LimitationRecord.created_at.desc()
    ).first()

    interrupt_dt = _parse_date(interrupt_date)
    if not interrupt_dt:
        interrupt_dt = date.today()

    if current_limitation:
        current_limitation.interrupt_date = interrupt_dt
        current_limitation.interrupt_type = interrupt_type
        current_limitation.interrupt_event = f'{interrupt_type} - {interrupt_dt}'

    new_end_date = interrupt_dt + timedelta(days=3 * 365)
    days_remaining = (new_end_date - date.today()).days

    new_limitation = LimitationRecord(
        contract_id=contract_id,
        base_date=interrupt_dt,
        base_type='时效中断',
        limitation_end_date=new_end_date,
        days_remaining=days_remaining,
        status='有效' if days_remaining > 90 else ('即将到期' if days_remaining > 0 else '已过期'),
    )
    db.session.add(new_limitation)


@collection_bp.route('/', methods=['GET'])
@login_required
def list_collections():
    """催款列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    contract_id = request.args.get('contract_id', type=int)
    collection_type = request.args.get('collection_type', '')
    date_start = request.args.get('date_start', '')
    date_end = request.args.get('date_end', '')

    query = CollectionRecord.query.filter(CollectionRecord.is_deleted == 0)

    if contract_id:
        query = query.filter(CollectionRecord.contract_id == contract_id)
    if collection_type:
        query = query.filter(CollectionRecord.collection_type == collection_type)
    if date_start:
        query = query.filter(CollectionRecord.collection_date >= date_start)
    if date_end:
        query = query.filter(CollectionRecord.collection_date <= date_end)

    query = query.order_by(CollectionRecord.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        contract = Contract.query.get(item.contract_id)
        data.append({
            'id': item.id,
            'contract_id': item.contract_id,
            'collection_date': item.collection_date.strftime('%Y-%m-%d') if item.collection_date else None,
            'collection_type': item.collection_type,
            'collection_content': item.collection_content,
            'express_no': item.express_no,
            'recipient': item.recipient,
            'sign_status': item.sign_status,
            'is_limitation_interrupt': item.is_limitation_interrupt,
            'collection_file': item.collection_file,
            'remark': item.remark,
            'project_name': contract.project_name if contract else '',
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@collection_bp.route('/', methods=['POST'])
@login_required
def create_collection():
    """登记催款"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    contract_id = json_data.get('contract_id')
    if not contract_id:
        return error_response('合同ID不能为空')

    contract = Contract.query.filter_by(id=contract_id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    collection_date_str = json_data.get('collection_date', date.today().strftime('%Y-%m-%d'))
    collection_date = _parse_date(collection_date_str) or date.today()
    is_limitation_interrupt = json_data.get('is_limitation_interrupt', 1)

    record = CollectionRecord(
        contract_id=contract_id,
        collection_date=collection_date,
        collection_type=json_data.get('collection_type', ''),
        collection_content=json_data.get('collection_content', ''),
        express_no=json_data.get('express_no', ''),
        recipient=json_data.get('recipient', ''),
        sign_status=json_data.get('sign_status', ''),
        is_limitation_interrupt=is_limitation_interrupt,
        collection_file=json_data.get('collection_file', ''),
        remark=json_data.get('remark', ''),
        created_by=g.get('current_user_id'),
    )
    db.session.add(record)

    # 时效中断
    if is_limitation_interrupt == 1:
        _interrupt_limitation(contract_id, collection_date, '催款中断')

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='催款管理',
        action='登记催款',
        content=f'登记催款: 合同 {contract.project_name}',
    )

    return success_response({'id': record.id}, '登记催款成功')


@collection_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_collection(id):
    """编辑催款"""
    record = CollectionRecord.query.filter_by(id=id, is_deleted=0).first()
    if not record:
        return error_response('催款记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    record.collection_date = _parse_date(json_data.get('collection_date')) if json_data.get('collection_date') else record.collection_date
    record.collection_type = json_data.get('collection_type', record.collection_type)
    record.collection_content = json_data.get('collection_content', record.collection_content)
    record.express_no = json_data.get('express_no', record.express_no)
    record.recipient = json_data.get('recipient', record.recipient)
    record.sign_status = json_data.get('sign_status', record.sign_status)
    record.is_limitation_interrupt = json_data.get('is_limitation_interrupt', record.is_limitation_interrupt)
    record.collection_file = json_data.get('collection_file', record.collection_file)
    record.remark = json_data.get('remark', record.remark)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='催款管理',
        action='编辑催款',
        content=f'编辑催款 ID:{id}',
    )

    return success_response(message='编辑催款成功')


@collection_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_collection(id):
    """删除催款（软删除）"""
    record = CollectionRecord.query.filter_by(id=id, is_deleted=0).first()
    if not record:
        return error_response('催款记录不存在', 404)

    record.is_deleted = 1
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='催款管理',
        action='删除催款',
        content=f'删除催款 ID:{id}',
    )

    return success_response(message='删除催款成功')


@collection_bp.route('/<int:id>/upload', methods=['POST'])
@login_required
def upload_collection_file(id):
    """上传催款函附件"""
    record = CollectionRecord.query.filter_by(id=id, is_deleted=0).first()
    if not record:
        return error_response('催款记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    if 'collection_file' in json_data:
        record.collection_file = json_data['collection_file']

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='催款管理',
        action='上传催款函附件',
        content=f'上传催款函附件 ID:{id}',
    )

    return success_response(message='上传催款函附件成功')
