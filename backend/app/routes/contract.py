"""合同管理路由"""

from datetime import date, timedelta
from flask import Blueprint, g, request
from sqlalchemy import func, or_

from app import db
from app.models import Customer, Contract, PaymentNode, PaymentRecord, CollectionRecord, LimitationRecord, InvoiceRecord
from app.services.payment_service import calc_overdue_interest
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

contract_bp = Blueprint('contract', __name__, url_prefix='/api/contract')


def parse_date(date_str):
    """解析日期字符串为date对象"""
    if not date_str:
        return None
    if isinstance(date_str, date):
        return date_str
    try:
        return date.fromisoformat(date_str.replace('/', '-'))
    except (ValueError, AttributeError):
        return None


@contract_bp.route('/', methods=['GET'])
@login_required
def list_contracts():
    """合同列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status', '')
    sign_date_start = request.args.get('sign_date_start', '')
    sign_date_end = request.args.get('sign_date_end', '')
    keyword = request.args.get('keyword', '')
    customer_name = request.args.get('customer_name', '')
    project_name = request.args.get('project_name', '')

    query = db.session.query(
        Contract.id,
        Contract.contract_no,
        Contract.project_name,
        Customer.name.label('customer_name'),
        Contract.contract_amount,
        Contract.audit_amount,
        Contract.total_paid,
        Contract.outstanding_amount,
        Contract.status,
        Contract.sign_date,
    ).outerjoin(Customer, Customer.id == Contract.customer_id)

    query = query.filter(Contract.is_deleted == 0)

    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if status:
        query = query.filter(Contract.status == status)
    if sign_date_start:
        query = query.filter(Contract.sign_date >= sign_date_start)
    if sign_date_end:
        query = query.filter(Contract.sign_date <= sign_date_end)
    if customer_name:
        query = query.filter(Customer.name.contains(customer_name))
    if project_name:
        query = query.filter(Contract.project_name.contains(project_name))
    if keyword:
        query = query.filter(or_(
            Contract.project_name.contains(keyword),
            Contract.contract_no.contains(keyword),
        ))

    query = query.order_by(Contract.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    # 批量计算到期应付金额
    contract_ids = [item.id for item in result['list']]
    today = date.today()
    due_amounts = {}
    if contract_ids:
        due_rows = db.session.query(
            PaymentNode.contract_id,
            func.coalesce(func.sum(PaymentNode.pay_amount - PaymentNode.actual_pay_amount), 0)
        ).filter(
            PaymentNode.contract_id.in_(contract_ids),
            PaymentNode.due_date <= today,
            PaymentNode.status == '逾期',
        ).group_by(PaymentNode.contract_id).all()
        due_amounts = {row[0]: float(row[1]) for row in due_rows}

    data = []
    for item in result['list']:
        data.append({
            'id': item.id,
            'contract_no': item.contract_no,
            'project_name': item.project_name,
            'customer_name': item.customer_name,
            'contract_amount': float(item.contract_amount) if item.contract_amount else 0,
            'audit_amount': float(item.audit_amount) if item.audit_amount else 0,
            'total_paid': float(item.total_paid) if item.total_paid else 0,
            'outstanding_amount': float(item.outstanding_amount) if item.outstanding_amount else 0,
            'due_amount': due_amounts.get(item.id, 0),
            'status': item.status,
            'sign_date': item.sign_date.strftime('%Y-%m-%d') if item.sign_date else None,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@contract_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_contract(id):
    """合同详情"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    customer = Customer.query.get(contract.customer_id)
    customer_data = None
    if customer:
        customer_data = {
            'id': customer.id,
            'region': customer.region,
            'name': customer.name,
            'business_contact': customer.business_contact,
            'credit_level': customer.credit_level,
        }

    today = date.today()
    payment_nodes = PaymentNode.query.filter_by(contract_id=id).order_by(PaymentNode.node_no).all()
    nodes_data = []
    for n in payment_nodes:
        # 实时计算状态
        if n.due_date is None:
            status = '未到期'
        elif (n.actual_pay_amount or 0) >= (n.pay_amount or 0):
            status = '已支付'
        elif n.due_date > today:
            status = '未到期'
        else:
            status = '逾期'

        nodes_data.append({
            'id': n.id,
            'node_no': n.node_no,
            'node_name': n.node_name,
            'pay_ratio': float(n.pay_ratio) if n.pay_ratio else 0,
            'pay_amount': float(n.pay_amount) if n.pay_amount else 0,
            'due_date': n.due_date.strftime('%Y-%m-%d') if n.due_date else None,
            'due_condition': n.due_condition,
            'actual_pay_date': n.actual_pay_date.strftime('%Y-%m-%d') if n.actual_pay_date else None,
            'actual_pay_amount': float(n.actual_pay_amount) if n.actual_pay_amount else 0,
            'status': status,
        })

    # 统计字段：最近一次付款时间
    last_payment = PaymentRecord.query.filter_by(
        contract_id=id, is_deleted=0
    ).order_by(PaymentRecord.payment_date.desc()).first()
    last_payment_date = last_payment.payment_date.strftime('%Y-%m-%d') if last_payment and last_payment.payment_date else None

    # 统计字段：最后一次催款函时间
    last_collection = CollectionRecord.query.filter_by(
        contract_id=id, is_deleted=0
    ).order_by(CollectionRecord.collection_date.desc()).first()
    last_collection_date = last_collection.collection_date.strftime('%Y-%m-%d') if last_collection and last_collection.collection_date else None

    # 统计字段：最后一次付款结点（最后一个有实际付款的节点名称）
    last_paid_node = PaymentNode.query.filter_by(
        contract_id=id
    ).filter(PaymentNode.actual_pay_amount > 0).order_by(PaymentNode.node_no.desc()).first()
    last_payment_node = last_paid_node.node_name if last_paid_node else None

    # 统计字段：当前到期应付金额（从付款节点实时计算）
    today = date.today()
    current_due_nodes = PaymentNode.query.filter_by(contract_id=id).filter(
        PaymentNode.status == '逾期',
        PaymentNode.due_date <= today,
    ).all()
    current_due_amount = sum(
        (float(n.pay_amount) if n.pay_amount else 0) - (float(n.actual_pay_amount) if n.actual_pay_amount else 0)
        for n in current_due_nodes
    ) if current_due_nodes else 0

    data = {
        'id': contract.id,
        'customer_id': contract.customer_id,
        'customer_name': getattr(customer, 'name', None),
        'contract_no': contract.contract_no,
        'project_name': contract.project_name,
        'sign_date': contract.sign_date.strftime('%Y-%m-%d') if contract.sign_date else None,
        'acceptance_date': contract.acceptance_date.strftime('%Y-%m-%d') if contract.acceptance_date else None,
        'contract_amount': float(contract.contract_amount) if contract.contract_amount else 0,
        'audit_amount': float(contract.audit_amount) if contract.audit_amount else 0,
        'payment_method': contract.payment_method,
        'breach_clause': contract.breach_clause or contract.payment_terms,
        'penalty_interest': contract.penalty_interest,
        'remark': contract.remark,
        'status': contract.status,
        'total_paid': float(contract.total_paid) if contract.total_paid else 0,
        'outstanding_amount': float(contract.outstanding_amount) if contract.outstanding_amount else 0,
        'current_due_amount': max(float(current_due_amount), 0),
        'total_invoiced': float(contract.total_invoiced) if contract.total_invoiced else 0,
        'last_payment_date': last_payment_date,
        'last_collection_date': last_collection_date,
        'last_payment_node': last_payment_node,
        'contract_file': contract.contract_file,
        'acceptance_file': contract.acceptance_file,
        'settlement_file': contract.settlement_file,
        'created_at': contract.created_at.strftime('%Y-%m-%d %H:%M:%S') if contract.created_at else None,
        'customer': customer_data,
        'payment_nodes': nodes_data,
    }
    return success_response(data)


@contract_bp.route('/', methods=['POST'])
@login_required
def create_contract():
    """新增合同"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    customer_id = json_data.get('customer_id')
    project_name = json_data.get('project_name', '')
    if not customer_id or not project_name:
        return error_response('客户和项目名称不能为空')

    contract_amount = json_data.get('contract_amount', 0)
    audit_amount = json_data.get('audit_amount', contract_amount)

    sign_date = parse_date(json_data.get('sign_date'))
    acceptance_date = parse_date(json_data.get('acceptance_date'))

    contract = Contract(
        customer_id=customer_id,
        contract_no=json_data.get('contract_no', ''),
        project_name=project_name,
        sign_date=sign_date,
        acceptance_date=acceptance_date,
        contract_amount=contract_amount,
        audit_amount=audit_amount,
        payment_method=json_data.get('payment_method', ''),
        breach_clause=json_data.get('breach_clause', ''),
        penalty_interest=json_data.get('penalty_interest', '日万分之五'),
        contract_file=json_data.get('contract_file', '[]'),
        acceptance_file=json_data.get('acceptance_file', '[]'),
        settlement_file=json_data.get('settlement_file', '[]'),
        status=json_data.get('status', '执行中'),
        outstanding_amount=audit_amount if audit_amount else contract_amount,
        remark=json_data.get('remark', ''),
        created_by=g.get('current_user_id'),
        updated_by=g.get('current_user_id'),
    )
    db.session.add(contract)
    db.session.flush()

    # 创建付款节点
    payment_nodes = json_data.get('payment_nodes', [])
    for node in payment_nodes:
        pn = PaymentNode(
            contract_id=contract.id,
            node_no=node.get('node_no', 0),
            node_name=node.get('node_name', ''),
            pay_ratio=node.get('pay_ratio', 0),
            pay_amount=node.get('pay_amount', 0),
            due_date=parse_date(node.get('due_date')),
            due_condition=node.get('due_condition', ''),
            status='未到期',
        )
        db.session.add(pn)

    # 自动初始化时效记录
    limitation = LimitationRecord(
        contract_id=contract.id,
        base_date=contract.sign_date,
        base_type='合同签订',
        limitation_end_date=contract.sign_date + timedelta(days=3 * 365) if contract.sign_date else None,
        days_remaining=((contract.sign_date + timedelta(days=3 * 365)) - date.today()).days if contract.sign_date else 0,
        status='有效',
    )
    db.session.add(limitation)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='新增合同',
        content=f'新增合同: {project_name}',
    )

    return success_response({'id': contract.id}, '新增合同成功')


@contract_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_contract(id):
    """编辑合同"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    contract.customer_id = json_data.get('customer_id', contract.customer_id)
    contract.contract_no = json_data.get('contract_no', contract.contract_no)
    contract.project_name = json_data.get('project_name', contract.project_name)
    contract.sign_date = parse_date(json_data.get('sign_date')) if json_data.get('sign_date') else contract.sign_date
    contract.acceptance_date = parse_date(json_data.get('acceptance_date')) if json_data.get('acceptance_date') else contract.acceptance_date
    contract.contract_amount = json_data.get('contract_amount', contract.contract_amount)
    contract.audit_amount = json_data.get('audit_amount', contract.audit_amount)
    contract.payment_method = json_data.get('payment_method', contract.payment_method)
    contract.breach_clause = json_data.get('breach_clause', contract.breach_clause)
    contract.penalty_interest = json_data.get('penalty_interest', contract.penalty_interest)
    contract.remark = json_data.get('remark', contract.remark)
    contract.status = json_data.get('status', contract.status)
    contract.updated_by = g.get('current_user_id')

    # 更新附件字段（支持多文件JSON格式）
    if 'contract_file' in json_data:
        contract.contract_file = json_data['contract_file']
    if 'acceptance_file' in json_data:
        contract.acceptance_file = json_data['acceptance_file']
    if 'settlement_file' in json_data:
        contract.settlement_file = json_data['settlement_file']

    # 更新付款节点：先删后增
    payment_nodes = json_data.get('payment_nodes')
    if payment_nodes is not None:
        PaymentNode.query.filter_by(contract_id=id).delete()
        for node in payment_nodes:
            pn = PaymentNode(
                contract_id=id,
                node_no=node.get('node_no', 0),
                node_name=node.get('node_name', ''),
                pay_ratio=node.get('pay_ratio', 0),
                pay_amount=node.get('pay_amount', 0),
                due_date=parse_date(node.get('due_date')),
                due_condition=node.get('due_condition', ''),
                actual_pay_date=parse_date(node.get('actual_pay_date')) if node.get('actual_pay_date') else None,
                actual_pay_amount=node.get('actual_pay_amount', 0),
                status=node.get('status', '未到期'),
            )
            db.session.add(pn)

    # 重新计算尚欠金额：审计金额>0用审计金额，否则用合同金额
    base_amount = float(contract.audit_amount or 0)
    if base_amount == 0:
        base_amount = float(contract.contract_amount or 0)
    total_paid = float(contract.total_paid or 0)
    contract.outstanding_amount = base_amount - total_paid

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='编辑合同',
        content=f'编辑合同: {contract.project_name}',
    )

    return success_response(message='编辑合同成功')


@contract_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_contract(id):
    """删除合同（软删除）"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    # 软删除合同
    contract.is_deleted = 1
    contract.updated_by = g.get('current_user_id')

    # 软删除回款记录
    PaymentRecord.query.filter_by(contract_id=id, is_deleted=0).update(
        {'is_deleted': 1}, synchronize_session=False
    )
    # 软删除开票记录
    InvoiceRecord.query.filter_by(contract_id=id, is_deleted=0).update(
        {'is_deleted': 1}, synchronize_session=False
    )
    # 软删除催款记录
    CollectionRecord.query.filter_by(contract_id=id, is_deleted=0).update(
        {'is_deleted': 1}, synchronize_session=False
    )
    # 硬删除付款节点
    PaymentNode.query.filter_by(contract_id=id).delete(synchronize_session=False)
    # 硬删除时效记录
    LimitationRecord.query.filter_by(contract_id=id).delete(synchronize_session=False)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='删除合同',
        content=f'删除合同: {contract.project_name}',
    )

    return success_response(message='删除合同成功')


@contract_bp.route('/<int:id>/payment-nodes', methods=['GET'])
@login_required
def get_payment_nodes(id):
    """获取付款节点列表"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    nodes = PaymentNode.query.filter_by(contract_id=id).order_by(PaymentNode.node_no).all()
    data = []
    for n in nodes:
        data.append({
            'id': n.id,
            'node_no': n.node_no,
            'node_name': n.node_name,
            'pay_ratio': float(n.pay_ratio) if n.pay_ratio else 0,
            'pay_amount': float(n.pay_amount) if n.pay_amount else 0,
            'due_date': n.due_date.strftime('%Y-%m-%d') if n.due_date else None,
            'due_condition': n.due_condition,
            'actual_pay_date': n.actual_pay_date.strftime('%Y-%m-%d') if n.actual_pay_date else None,
            'actual_pay_amount': float(n.actual_pay_amount) if n.actual_pay_amount else 0,
            'status': n.status,
        })
    return success_response(data)


@contract_bp.route('/<int:id>/payment-nodes', methods=['PUT'])
@login_required
def update_payment_nodes(id):
    """更新付款节点（全量替换）"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    # 兼容两种格式：前端提交 { nodes: [...] } 或直接 [...]
    if isinstance(json_data, dict):
        nodes_list = json_data.get('nodes', json_data.get('payment_nodes', []))
    else:
        nodes_list = json_data or []

    PaymentNode.query.filter_by(contract_id=id).delete()

    for idx, node in enumerate(nodes_list):
        if not isinstance(node, dict):
            continue
        pn = PaymentNode(
            contract_id=id,
            node_no=node.get('node_no', idx + 1),
            node_name=node.get('node_name', ''),
            pay_ratio=node.get('pay_ratio', 0),
            pay_amount=node.get('pay_amount', 0),
            due_date=parse_date(node.get('due_date')),
            due_condition=node.get('due_condition', ''),
            status=node.get('status', '未到期'),
            actual_pay_date=parse_date(node.get('actual_pay_date')),
            actual_pay_amount=node.get('actual_pay_amount', 0),
        )
        db.session.add(pn)

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='更新付款节点',
        content=f'更新合同 {contract.project_name} 付款节点',
    )

    return success_response(message='更新付款节点成功')


@contract_bp.route('/<int:id>/upload', methods=['POST'])
@login_required
def upload_contract_files(id):
    """上传合同/验收/结算附件"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    if 'contract_file' in json_data:
        contract.contract_file = json_data['contract_file']
    if 'acceptance_file' in json_data:
        contract.acceptance_file = json_data['acceptance_file']
    if 'settlement_file' in json_data:
        contract.settlement_file = json_data['settlement_file']

    contract.updated_by = g.get('current_user_id')
    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='上传附件',
        content=f'上传合同 {contract.project_name} 附件',
    )

    return success_response(message='上传附件成功')


@contract_bp.route('/<int:id>/payment-node/<int:node_id>/status', methods=['PUT'])
@login_required
def update_payment_node_status(id, node_id):
    """更新单个付款节点状态
    入参：status, actual_pay_amount, actual_pay_date, create_payment_record
    逻辑：
      - 若 status = 已支付：更新节点状态 + 实际支付金额/日期；若 create_payment_record=true 则创建回款记录 → 重新核销所有节点
      - 若 status = 逾期 / 未到期：仅更新状态
    """
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    status = json_data.get('status')
    if not status:
        return error_response('请选择状态')

    node = PaymentNode.query.filter_by(id=node_id, contract_id=id).first()
    if not node:
        return error_response('付款节点不存在', 404)

    today = date.today()

    if status == '已支付':
        actual_pay_amount = json_data.get('actual_pay_amount', node.pay_amount)
        actual_pay_date = parse_date(json_data.get('actual_pay_date')) or today
        create_payment_record = json_data.get('create_payment_record', True)

        node.status = '已支付'
        node.actual_pay_amount = actual_pay_amount
        node.actual_pay_date = actual_pay_date

        if create_payment_record:
            last_payment = PaymentRecord.query.filter_by(
                contract_id=id, is_deleted=0
            ).order_by(PaymentRecord.payment_no.desc()).first()
            payment_no = (last_payment.payment_no + 1) if last_payment else 1

            new_record = PaymentRecord(
                contract_id=id,
                payment_no=payment_no,
                amount=actual_pay_amount,
                payment_date=actual_pay_date,
                payment_method='',
                bank_account='',
                remark='节点状态更新自动生成',
                interrupt_limitation=1,
                created_by=g.get('current_user_id'),
                updated_by=g.get('current_user_id'),
            )
            db.session.add(new_record)

            # 重新核销所有节点
            all_nodes = PaymentNode.query.filter_by(contract_id=id).order_by(PaymentNode.node_no).all()
            all_payments = PaymentRecord.query.filter_by(contract_id=id, is_deleted=0).order_by(PaymentRecord.payment_date).all()
            total_paid = sum(float(p.amount) if p.amount else 0 for p in all_payments)

            for n in all_nodes:
                if n.id == node_id:
                    continue
                n.actual_pay_amount = 0
                n.actual_pay_date = None
                if n.due_date and n.due_date < today:
                    n.status = '逾期'
                else:
                    n.status = '未到期'

            remaining = total_paid - float(actual_pay_amount)
            for n in all_nodes:
                if n.id == node_id:
                    continue
                n_amount = float(n.pay_amount) if n.pay_amount else 0
                if remaining <= 0:
                    break
                if remaining >= n_amount:
                    n.actual_pay_amount = n_amount
                    n.actual_pay_date = all_payments[-1].payment_date if all_payments else today
                    n.status = '已支付'
                    remaining -= n_amount
                else:
                    n.actual_pay_amount = remaining
                    n.actual_pay_date = all_payments[-1].payment_date if all_payments else today
                    n.status = '逾期'
                    remaining = 0

            # 重新计算合同尚欠金额
            base_amount = float(contract.audit_amount or 0)
            if base_amount == 0:
                base_amount = float(contract.contract_amount or 0)
            contract.total_paid = total_paid
            contract.outstanding_amount = base_amount - total_paid

            # 重新计算 current_due_amount
            current_due = 0
            for n in all_nodes:
                if n.status in ('逾期',) and n.due_date and n.due_date <= today:
                    current_due += float(n.pay_amount or 0) - float(n.actual_pay_amount or 0)
            contract.current_due_amount = max(current_due, 0)
    else:
        # 逾期 / 未到期：只更新状态
        node.status = status

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='合同管理',
        action='更新节点状态',
        content=f'合同 {contract.project_name} 节点[{node.node_name}]状态变更为 {status}',
    )

    return success_response(message='状态更新成功')


@contract_bp.route('/<int:id>/overdue-interest', methods=['GET'])
@login_required
def get_overdue_interest(id):
    """获取合同的逾期利息"""
    contract = Contract.query.filter_by(id=id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    result = calc_overdue_interest(id)
    return success_response(result)
