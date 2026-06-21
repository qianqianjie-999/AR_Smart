"""回款管理路由"""

from datetime import date, timedelta
from flask import Blueprint, g, request

from app import db
from app.models import Contract, PaymentNode, PaymentRecord, LimitationRecord
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')


@payment_bp.route('/', methods=['GET'])
@login_required
def list_payments():
    """回款列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    contract_id = request.args.get('contract_id', type=int)
    payment_date_start = request.args.get('payment_date_start', '')
    payment_date_end = request.args.get('payment_date_end', '')

    query = PaymentRecord.query.filter(PaymentRecord.is_deleted == 0)

    if contract_id:
        query = query.filter(PaymentRecord.contract_id == contract_id)
    if payment_date_start:
        query = query.filter(PaymentRecord.payment_date >= payment_date_start)
    if payment_date_end:
        query = query.filter(PaymentRecord.payment_date <= payment_date_end)

    query = query.order_by(PaymentRecord.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        contract = Contract.query.get(item.contract_id)
        data.append({
            'id': item.id,
            'contract_id': item.contract_id,
            'payment_no': item.payment_no,
            'amount': float(item.amount) if item.amount else 0,
            'payment_date': item.payment_date.strftime('%Y-%m-%d') if item.payment_date else None,
            'payment_method': item.payment_method,
            'bank_account': item.bank_account,
            'remark': item.remark,
            'interrupt_limitation': item.interrupt_limitation,
            'project_name': contract.project_name if contract else '',
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


def _reconcile_payment_nodes(contract_id):
    """按顺序自动核销付款节点：匹配金额，更新节点状态"""
    nodes = PaymentNode.query.filter_by(contract_id=contract_id).order_by(PaymentNode.node_no).all()
    payments = PaymentRecord.query.filter_by(contract_id=contract_id, is_deleted=0).order_by(PaymentRecord.payment_date).all()

    total_paid = sum(float(p.amount) if p.amount else 0 for p in payments)

    # 重置所有节点
    for node in nodes:
        node.actual_pay_amount = 0
        node.actual_pay_date = None
        node.status = '未到期'

    remaining = total_paid
    for node in nodes:
        node_amount = float(node.pay_amount) if node.pay_amount else 0
        if remaining <= 0:
            break
        if remaining >= node_amount:
            # 完全覆盖此节点
            node.actual_pay_amount = node_amount
            node.actual_pay_date = payments[-1].payment_date if payments else date.today()
            node.status = '已支付'
            remaining -= node_amount
        else:
            # 部分覆盖
            node.actual_pay_amount = remaining
            node.actual_pay_date = payments[-1].payment_date if payments else date.today()
            node.status = '逾期'
            remaining = 0

    # 更新到期状态
    today = date.today()
    for node in nodes:
        if node.status in ('已支付',):
            continue
        if node.due_date:
            if node.due_date < today:
                node.status = '逾期'
            else:
                node.status = '未到期'

    contract = Contract.query.get(contract_id)
    if contract:
        contract.total_paid = total_paid
        base_amount = float(contract.audit_amount or 0)
        if base_amount == 0:
            base_amount = float(contract.contract_amount or 0)
        contract.outstanding_amount = base_amount - total_paid
        # 计算当前到期金额
        current_due = 0
        for node in nodes:
            if node.status in ('逾期',) and node.due_date and node.due_date <= today:
                current_due += float(node.pay_amount or 0) - float(node.actual_pay_amount or 0)
        contract.current_due_amount = max(current_due, 0)


def _parse_date_val(date_val):
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


def _interrupt_limitation(contract_id, interrupt_date, interrupt_type='回款中断'):
    """触发时效中断"""
    current_limitation = LimitationRecord.query.filter_by(contract_id=contract_id).order_by(
        LimitationRecord.created_at.desc()
    ).first()

    interrupt_dt = _parse_date_val(interrupt_date)
    if not interrupt_dt:
        interrupt_dt = date.today()

    if current_limitation:
        current_limitation.interrupt_date = interrupt_dt
        current_limitation.interrupt_type = interrupt_type
        current_limitation.interrupt_event = f'{interrupt_type} - {interrupt_dt}'

    # 创建新时效记录
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


@payment_bp.route('/', methods=['POST'])
@login_required
def create_payment():
    """登记回款"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    contract_id = json_data.get('contract_id')
    amount = json_data.get('amount')
    if not contract_id or not amount:
        return error_response('合同ID和回款金额不能为空')

    contract = Contract.query.filter_by(id=contract_id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    payment_date_str = json_data.get('payment_date', date.today().strftime('%Y-%m-%d'))
    payment_date = _parse_date_val(payment_date_str) or date.today()
    interrupt_limitation = json_data.get('interrupt_limitation', 1)

    # 自动计算 payment_no（该合同的第几次回款）
    last_payment = PaymentRecord.query.filter_by(
        contract_id=contract_id, is_deleted=0
    ).order_by(PaymentRecord.payment_no.desc()).first()
    payment_no = (last_payment.payment_no + 1) if last_payment else 1

    payment = PaymentRecord(
        contract_id=contract_id,
        payment_no=payment_no,
        amount=amount,
        payment_date=payment_date,
        payment_method=json_data.get('payment_method', ''),
        bank_account=json_data.get('bank_account', ''),
        remark=json_data.get('remark', ''),
        interrupt_limitation=interrupt_limitation,
        created_by=g.get('current_user_id'),
        updated_by=g.get('current_user_id'),
    )
    db.session.add(payment)

    # 自动核销付款节点
    _reconcile_payment_nodes(contract_id)

    # 触发时效中断
    if interrupt_limitation == 1:
        _interrupt_limitation(contract_id, payment_date, '回款中断')

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='回款管理',
        action='登记回款',
        content=f'登记回款: 合同 {contract.project_name}, 金额 {amount}',
    )

    return success_response({'id': payment.id, 'payment_no': payment_no}, '登记回款成功')


@payment_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_payment(id):
    """编辑回款"""
    payment = PaymentRecord.query.filter_by(id=id, is_deleted=0).first()
    if not payment:
        return error_response('回款记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    payment.amount = json_data.get('amount', payment.amount)
    payment.payment_date = _parse_date_val(json_data.get('payment_date')) if json_data.get('payment_date') else payment.payment_date
    payment.payment_method = json_data.get('payment_method', payment.payment_method)
    payment.bank_account = json_data.get('bank_account', payment.bank_account)
    payment.remark = json_data.get('remark', payment.remark)
    payment.interrupt_limitation = json_data.get('interrupt_limitation', payment.interrupt_limitation)
    payment.updated_by = g.get('current_user_id')

    # 重新核销付款节点
    _reconcile_payment_nodes(payment.contract_id)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='回款管理',
        action='编辑回款',
        content=f'编辑回款 ID:{id}',
    )

    return success_response(message='编辑回款成功')


@payment_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_payment(id):
    """删除回款（软删除）"""
    payment = PaymentRecord.query.filter_by(id=id, is_deleted=0).first()
    if not payment:
        return error_response('回款记录不存在', 404)

    contract_id = payment.contract_id

    payment.is_deleted = 1
    payment.updated_by = g.get('current_user_id')

    # 重新计算合同金额和节点状态
    _reconcile_payment_nodes(contract_id)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='回款管理',
        action='删除回款',
        content=f'删除回款 ID:{id}',
    )

    return success_response(message='删除回款成功')
