"""时效管理路由【核心】"""

from datetime import date, timedelta
from flask import Blueprint, g, request
from sqlalchemy import func, or_

from app import db
from app.models import Customer, Contract, LimitationRecord
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

limitation_bp = Blueprint('limitation', __name__, url_prefix='/api/limitation')


def _calc_status(days_remaining):
    """Calculate limitation status based on days remaining."""
    if days_remaining is None:
        return '未知'
    if days_remaining <= 0:
        return '已过期'
    if days_remaining <= 90:
        return '即将到期'
    return '有效'


@limitation_bp.route('/', methods=['GET'])
@login_required
def list_limitations():
    """时效列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    status = request.args.get('status', '')
    contract_id = request.args.get('contract_id', type=int)
    end_date_start = request.args.get('end_date_start', '')
    end_date_end = request.args.get('end_date_end', '')
    keyword = request.args.get('keyword', '')

    query = db.session.query(
        LimitationRecord.id,
        LimitationRecord.contract_id,
        Contract.contract_no,
        Contract.project_name,
        Customer.name.label('customer_name'),
        LimitationRecord.base_date,
        LimitationRecord.limitation_end_date,
        LimitationRecord.days_remaining,
        LimitationRecord.status,
        LimitationRecord.interrupt_date,
        LimitationRecord.interrupt_type,
    ).outerjoin(Contract, Contract.id == LimitationRecord.contract_id).outerjoin(
        Customer, Customer.id == Contract.customer_id
    ).filter(Contract.is_deleted == 0)

    if status:
        query = query.filter(LimitationRecord.status == status)
    if contract_id:
        query = query.filter(LimitationRecord.contract_id == contract_id)
    if end_date_start:
        query = query.filter(LimitationRecord.limitation_end_date >= end_date_start)
    if end_date_end:
        query = query.filter(LimitationRecord.limitation_end_date <= end_date_end)
    if keyword:
        query = query.filter(or_(
            Contract.project_name.contains(keyword),
        ))

    query = query.order_by(LimitationRecord.limitation_end_date.asc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        # 统计中断次数
        interrupt_count = LimitationRecord.query.filter_by(
            contract_id=item.contract_id
        ).filter(LimitationRecord.interrupt_date.isnot(None)).count()

        data.append({
            'id': item.id,
            'contract_id': item.contract_id,
            'contract_no': item.contract_no,
            'project_name': item.project_name,
            'customer_name': item.customer_name,
            'base_date': item.base_date.strftime('%Y-%m-%d') if item.base_date else None,
            'due_date': item.limitation_end_date.strftime('%Y-%m-%d') if item.limitation_end_date else None,
            'remaining_days': item.days_remaining,
            'status': item.status,
            'interrupt_count': interrupt_count,
            'last_interrupt_date': item.interrupt_date.strftime('%Y-%m-%d') if item.interrupt_date else None,
            'interrupt_type': item.interrupt_type,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@limitation_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """时效看板数据"""
    today = date.today()

    # 获取每个合同的最新时效记录
    latest_subquery = db.session.query(
        LimitationRecord.contract_id,
        func.max(LimitationRecord.created_at).label('max_created')
    ).group_by(LimitationRecord.contract_id).subquery()

    records = db.session.query(LimitationRecord).join(
        latest_subquery,
        (LimitationRecord.contract_id == latest_subquery.c.contract_id) &
        (LimitationRecord.created_at == latest_subquery.c.max_created)
    ).join(Contract, Contract.id == LimitationRecord.contract_id).filter(
        Contract.is_deleted == 0
    ).all()

    total = len(records)
    active = 0
    expiring_soon = 0  # <=90 days
    expired = 0
    status_dist = {}
    region_dist = {}
    warning_list = []

    for r in records:
        # Update status
        days = r.days_remaining
        if days is not None and days <= 0:
            s = '已过期'
        elif days is not None and days <= 90:
            s = '即将到期'
        else:
            s = '有效'

        if s == '有效':
            active += 1
        elif s == '即将到期':
            expiring_soon += 1
        else:
            expired += 1

        # Status distribution
        status_dist[s] = status_dist.get(s, 0) + 1

        # Warning list: <=7 days
        if days is not None and 0 < days <= 7:
            contract = Contract.query.get(r.contract_id)
            customer = Customer.query.get(contract.customer_id) if contract else None
            warning_list.append({
                'id': r.id,
                'contract_no': contract.contract_no if contract else '',
                'project_name': contract.project_name if contract else '',
                'customer_name': customer.name if customer else '',
                'remaining_days': days,
                'due_date': r.limitation_end_date.strftime('%Y-%m-%d') if r.limitation_end_date else None,
                'base_date': r.base_date.strftime('%Y-%m-%d') if r.base_date else None,
                'amount': float(contract.outstanding_amount) if contract and contract.outstanding_amount else 0,
            })

        # Region distribution
        contract = Contract.query.get(r.contract_id)
        customer = Customer.query.get(contract.customer_id) if contract else None
        region = customer.region if customer else '未知'
        if region not in region_dist:
            region_dist[region] = {'active': 0, 'expiring_soon': 0, 'expired': 0}
        if s == '有效':
            region_dist[region]['active'] += 1
        elif s == '即将到期':
            region_dist[region]['expiring_soon'] += 1
        else:
            region_dist[region]['expired'] += 1

    status_distribution = [{'name': k, 'value': v} for k, v in status_dist.items()]
    region_distribution = [{'name': k, 'effective': v['active'], 'expiring': v['expiring_soon'], 'expired': v['expired']} for k, v in region_dist.items()]

    return success_response({
        'effectiveCount': active,
        'expiringCount': expiring_soon,
        'expiredCount': expired,
        'totalCount': total,
        'pieData': status_distribution,
        'barData': region_distribution,
        'warnings': warning_list,
    })


@limitation_bp.route('/<int:id>/interrupt', methods=['POST'])
@login_required
def interrupt_limitation(id):
    """时效中断"""
    current = LimitationRecord.query.get(id)
    if not current:
        return error_response('时效记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    interrupt_type = json_data.get('interrupt_type', '手动中断')
    interrupt_date_str = json_data.get('interrupt_date', date.today().strftime('%Y-%m-%d'))
    interrupt_event = json_data.get('interrupt_event', '')

    # Parse interrupt_date
    try:
        from datetime import datetime as dt
        interrupt_date = dt.strptime(str(interrupt_date_str), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        interrupt_date = date.today()

    # 1. Update current record
    current.interrupt_date = interrupt_date
    current.interrupt_type = interrupt_type
    current.interrupt_event = interrupt_event

    # 2. Create new limitation record
    new_end_date = interrupt_date + timedelta(days=3 * 365)
    days_remaining = (new_end_date - date.today()).days
    status = _calc_status(days_remaining)

    new_limitation = LimitationRecord(
        contract_id=current.contract_id,
        base_date=interrupt_date,
        base_type='时效中断',
        limitation_end_date=new_end_date,
        days_remaining=days_remaining,
        status=status,
    )
    db.session.add(new_limitation)
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='时效管理',
        action='时效中断',
        content=f'时效中断: 记录ID {id}, 中断类型 {interrupt_type}',
    )

    return success_response({'id': new_limitation.id}, '时效中断成功')


@limitation_bp.route('/<int:id>/history', methods=['GET'])
@login_required
def limitation_history(id):
    """时效中断历史"""
    current = LimitationRecord.query.get(id)
    if not current:
        return error_response('时效记录不存在', 404)

    records = LimitationRecord.query.filter_by(contract_id=current.contract_id).order_by(
        LimitationRecord.created_at.desc()
    ).all()

    data = []
    for r in records:
        data.append({
            'id': r.id,
            'contract_id': r.contract_id,
            'base_date': r.base_date.strftime('%Y-%m-%d') if r.base_date else None,
            'base_type': r.base_type,
            'limitation_end_date': r.limitation_end_date.strftime('%Y-%m-%d') if r.limitation_end_date else None,
            'days_remaining': r.days_remaining,
            'status': r.status,
            'interrupt_event': r.interrupt_event,
            'interrupt_date': r.interrupt_date.strftime('%Y-%m-%d') if r.interrupt_date else None,
            'interrupt_type': r.interrupt_type,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else None,
        })

    return success_response(data)
