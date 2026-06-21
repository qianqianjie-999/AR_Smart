from datetime import date, datetime
import re
from decimal import Decimal
from app import db
from app.models.contract import Contract, PaymentNode
from app.models.payment import PaymentRecord


def calc_outstanding(contract_id):
    """计算尚欠金额 = audit_amount - sum(payment_records)

    Returns:
        Decimal: 尚欠金额
    """
    contract = Contract.query.get(contract_id)
    if not contract:
        return Decimal('0')

    audit_amount = contract.audit_amount or Decimal('0')
    if audit_amount == 0:
        audit_amount = contract.contract_amount or Decimal('0')

    total_paid = (
        db.session.query(db.func.coalesce(db.func.sum(PaymentRecord.amount), 0))
        .filter(
            PaymentRecord.contract_id == contract_id,
            PaymentRecord.is_deleted == 0,
        )
        .scalar()
    )
    total_paid = Decimal(str(total_paid))

    outstanding = audit_amount - total_paid
    return outstanding


def calc_current_due(contract_id, today=None):
    """计算当前到期应收款 = sum(已到期但未付款的节点金额)

    Args:
        contract_id: 合同ID
        today: 计算日期，默认为今天

    Returns:
        Decimal: 当前到期应收款金额
    """
    if today is None:
        today = date.today()

    nodes = PaymentNode.query.filter(
        PaymentNode.contract_id == contract_id,
        PaymentNode.status == '逾期',
    ).all()

    total_due = Decimal('0')
    for node in nodes:
        pay_amount = node.pay_amount or Decimal('0')
        actual_pay = node.actual_pay_amount or Decimal('0')
        # 节点应付金额 - 实际已付 = 该节点尚欠
        node_unpaid = pay_amount - actual_pay
        if node_unpaid > 0:
            total_due += node_unpaid

    return total_due


def process_payment(contract_id, amount, payment_date):
    """登记回款后处理：

    1. 按顺序自动核销付款节点
    2. 更新合同累计回款、尚欠金额
    3. 返回处理结果（包含是否需要中断时效的提示）
    """
    contract = Contract.query.get(contract_id)
    if not contract:
        return {'success': False, 'message': '合同不存在'}

    if isinstance(payment_date, datetime):
        payment_date = payment_date.date()

    remaining = Decimal(str(amount))

    # 计算回款次数
    max_payment_no = (
        db.session.query(db.func.max(PaymentRecord.payment_no))
        .filter(PaymentRecord.contract_id == contract_id)
        .scalar()
    )
    new_payment_no = (max_payment_no or 0) + 1

    # 按节点序号升序获取未完全付款的节点
    nodes = (
        PaymentNode.query
        .filter(
            PaymentNode.contract_id == contract_id,
            PaymentNode.status != '已支付',
        )
        .order_by(PaymentNode.node_no.asc())
        .all()
    )

    updated_nodes = []
    for node in nodes:
        if remaining <= 0:
            break

        pay_amount = node.pay_amount or Decimal('0')
        actual_pay = node.actual_pay_amount or Decimal('0')
        node_unpaid = pay_amount - actual_pay

        if node_unpaid <= 0:
            continue

        # 本次核销金额 = min(剩余回款, 节点未付金额)
        apply_amount = min(remaining, node_unpaid)
        node.actual_pay_amount = actual_pay + apply_amount
        node.actual_pay_date = payment_date

        # 更新节点状态
        if node.actual_pay_amount >= pay_amount:
            node.status = '已支付'
        elif remaining < node_unpaid:
            # 部分付款，节点仍然是已到期/逾期状态
            pass

        remaining -= apply_amount
        updated_nodes.append({
            'node_id': node.id,
            'node_name': node.node_name,
            'applied_amount': float(apply_amount),
            'new_status': node.status,
        })

    # 创建回款记录
    payment_record = PaymentRecord(
        contract_id=contract_id,
        payment_no=new_payment_no,
        amount=amount,
        payment_date=payment_date,
    )
    db.session.add(payment_record)

    # 更新合同累计金额
    contract.total_paid = (contract.total_paid or Decimal('0')) + Decimal(str(amount))
    contract.outstanding_amount = calc_outstanding(contract_id)
    contract.current_due_amount = calc_current_due(contract_id)

    db.session.commit()

    need_interrupt = True  # 回款默认中断时效

    return {
        'success': True,
        'message': '回款登记成功',
        'payment_id': payment_record.id,
        'payment_no': new_payment_no,
        'remaining_unapplied': float(remaining),
        'updated_nodes': updated_nodes,
        'total_paid': float(contract.total_paid),
        'outstanding_amount': float(contract.outstanding_amount),
        'current_due_amount': float(contract.current_due_amount),
        'need_interrupt_limitation': need_interrupt,
    }


def update_payment_node_status(contract_id):
    """更新付款节点状态（基于当前日期与到期日比较）

    规则：
    - 已付清 -> 已支付
    - 未到期 + 当前日期 >= 到期日 + 未付清 -> 逾期
    """
    today = date.today()
    nodes = PaymentNode.query.filter(
        PaymentNode.contract_id == contract_id,
        PaymentNode.status.in_(['未到期', '逾期']),
    ).all()

    updated_count = 0
    for node in nodes:
        if node.due_date is None:
            continue

        if isinstance(node.due_date, datetime):
            due_date = node.due_date.date()
        else:
            due_date = node.due_date

        pay_amount = node.pay_amount or Decimal('0')
        actual_pay = node.actual_pay_amount or Decimal('0')

        if actual_pay >= pay_amount:
            if node.status != '已支付':
                node.status = '已支付'
                updated_count += 1
        elif due_date <= today:
            if node.status != '逾期':
                node.status = '逾期'
                updated_count += 1
        else:
            if node.status != '未到期':
                node.status = '未到期'
                updated_count += 1

    if updated_count > 0:
        db.session.commit()

    return updated_count


def _ensure_date(d):
    """确保 d 是 date 对象"""
    if isinstance(d, datetime):
        return d.date()
    return d


def _parse_penalty_rate(penalty_str):
    """解析利率字符串

    支持格式：'日万分之五' -> 0.0005, '日千分之一' -> 0.001, '0.0005' -> 0.0005
    """
    if not penalty_str:
        return 0.0005

    # 直接数字格式
    try:
        return float(penalty_str)
    except (ValueError, TypeError):
        pass

    # "日万分之五" 格式
    match = re.match(r'日(万|千|百)分之([一二三四五六七八九\d]+)', penalty_str)
    if match:
        unit = match.group(1)
        num_str = match.group(2)
        num_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
        num = num_map.get(num_str, int(num_str) if num_str.isdigit() else 5)
        if unit == '万':
            return num / 10000
        elif unit == '千':
            return num / 1000
        elif unit == '百':
            return num / 100
    return 0.0005


def calc_overdue_interest(contract_id, today=None):
    """计算合同所有节点的逾期利息

    Args:
        contract_id: 合同ID
        today: 计算日期，默认今天

    Returns:
        dict: {
            'nodes': [{node_id, node_name, pay_amount, actual_pay_amount,
                       due_date, status, overdue_days, interest}, ...],
            'total_interest': float,
            'daily_rate': float,
            'penalty_interest': str
        }
    """
    if today is None:
        today = date.today()

    contract = Contract.query.get(contract_id)
    if not contract:
        return {'nodes': [], 'total_interest': 0, 'daily_rate': 0, 'penalty_interest': ''}

    # 解析利率
    penalty_str = contract.penalty_interest or '日万分之五'
    daily_rate = _parse_penalty_rate(penalty_str)

    nodes = PaymentNode.query.filter_by(contract_id=contract_id).order_by(PaymentNode.node_no).all()

    nodes_data = []
    total_interest = Decimal('0')

    for node in nodes:
        pay_amount = node.pay_amount or Decimal('0')
        actual_pay = node.actual_pay_amount or Decimal('0')

        # 判断状态
        if node.due_date is None:
            status = '未到期'
            overdue_days = 0
            interest = Decimal('0')
        elif actual_pay >= pay_amount:
            status = '已支付'
            overdue_days = 0
            interest = Decimal('0')
        elif node.due_date > today:
            status = '未到期'
            overdue_days = 0
            interest = Decimal('0')
        else:
            status = '逾期'
            overdue_days = (today - node.due_date).days

            # 阶段1：全额逾期期间（到期日 -> 首次回款日或今天）
            first_pay_date = node.actual_pay_date
            if first_pay_date:
                first_pay_date = _ensure_date(first_pay_date)
                days_full = max((first_pay_date - node.due_date).days, 0)
            else:
                days_full = overdue_days

            interest = pay_amount * Decimal(str(daily_rate)) * days_full

            # 阶段2：剩余未付部分继续计息
            unpaid = pay_amount - actual_pay
            if unpaid > 0 and first_pay_date:
                days_remaining = max((today - first_pay_date).days, 0)
                if days_remaining > 0:
                    interest += unpaid * Decimal(str(daily_rate)) * days_remaining

            total_interest += interest

        nodes_data.append({
            'node_id': node.id,
            'node_name': node.node_name,
            'pay_amount': float(pay_amount),
            'actual_pay_amount': float(actual_pay),
            'due_date': node.due_date.strftime('%Y-%m-%d') if node.due_date else None,
            'status': status,
            'overdue_days': overdue_days,
            'interest': float(interest),
        })

    return {
        'nodes': nodes_data,
        'total_interest': float(total_interest),
        'daily_rate': daily_rate,
        'penalty_interest': penalty_str,
    }
