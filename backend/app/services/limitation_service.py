from datetime import datetime, date, timedelta
from decimal import Decimal
from app import db
from app.models.contract import Contract, PaymentNode
from app.models.payment import PaymentRecord
from app.models.collection import CollectionRecord
from app.models.limitation import LimitationRecord
from app.models.notification import NotificationRecord


LIMITATION_YEARS = 3
LIMITATION_DAYS = 1095  # 3年 = 1095天


def _get_latest_payment_date(contract_id):
    """获取合同最后一次回款日期"""
    record = (
        PaymentRecord.query
        .filter_by(contract_id=contract_id, is_deleted=0)
        .order_by(PaymentRecord.payment_date.desc())
        .first()
    )
    return record.payment_date if record else None


def _get_latest_payment_node_date(contract_id):
    """获取合同最后一个付款节点到期日"""
    node = (
        PaymentNode.query
        .filter_by(contract_id=contract_id)
        .order_by(PaymentNode.due_date.desc())
        .first()
    )
    return node.due_date if node else None


def _get_latest_collection_date(contract_id):
    """获取合同最后一次催款日期"""
    record = (
        CollectionRecord.query
        .filter_by(contract_id=contract_id, is_deleted=0)
        .order_by(CollectionRecord.collection_date.desc())
        .first()
    )
    return record.collection_date if record else None


def calc_limitation_end(contract_id):
    """计算诉讼时效到期日

    规则：
      基准日期 = max(最后付款节点到期日, 最后一次回款日期, 最后一次催款日期, 验收日期)
      时效到期日 = 基准日期 + 3年（1095天）
      状态判定：剩余>90天='有效', <=90且>0='即将到期', <=0='已过期'
    """
    contract = Contract.query.get(contract_id)
    if not contract:
        return None

    last_payment_date = _get_latest_payment_date(contract_id)
    last_collection_date = _get_latest_collection_date(contract_id)
    last_payment_node_date = _get_latest_payment_node_date(contract_id)
    acceptance_date = contract.acceptance_date

    candidates = []
    if last_payment_node_date:
        candidates.append(last_payment_node_date)
    if last_payment_date:
        candidates.append(last_payment_date)
    if last_collection_date:
        candidates.append(last_collection_date)
    if acceptance_date:
        candidates.append(acceptance_date)

    if not candidates:
        return None

    base_date = max(candidates)

    if isinstance(base_date, datetime):
        base_date = base_date.date()

    limitation_end = base_date + timedelta(days=LIMITATION_DAYS)
    today = date.today()
    days_remaining = (limitation_end - today).days

    if days_remaining > 90:
        status = '有效'
    elif days_remaining > 0:
        status = '即将到期'
    else:
        status = '已过期'

    return {
        'base_date': base_date,
        'base_type': _determine_base_type(base_date, last_payment_node_date, last_payment_date, last_collection_date, acceptance_date),
        'limitation_end_date': limitation_end,
        'days_remaining': days_remaining,
        'status': status,
    }


def _determine_base_type(base_date, last_payment_node_date, last_payment_date, last_collection_date, acceptance_date):
    """确定基准类型"""
    if last_payment_node_date and base_date == last_payment_node_date:
        return '付款节点'
    if last_payment_date and base_date == last_payment_date:
        return '回款'
    if last_collection_date and base_date == last_collection_date:
        return '催款'
    if acceptance_date and base_date == acceptance_date:
        return '验收'
    return '其他'


def interrupt_limitation(contract_id, interrupt_type, interrupt_date, event_desc):
    """中断时效

    1. 记录当前时效信息（将旧的 LimitationRecord 状态标记）
    2. 创建新的时效记录（基准日期=中断日期，到期日=中断日期+3年）
    """
    # 找到当前有效的时效记录
    current = (
        LimitationRecord.query
        .filter_by(contract_id=contract_id)
        .order_by(LimitationRecord.created_at.desc())
        .first()
    )

    if isinstance(interrupt_date, datetime):
        interrupt_date = interrupt_date.date()

    new_limitation_end = interrupt_date + timedelta(days=LIMITATION_DAYS)
    days_remaining = (new_limitation_end - date.today()).days

    if days_remaining > 90:
        status = '有效'
    elif days_remaining > 0:
        status = '即将到期'
    else:
        status = '已过期'

    new_record = LimitationRecord(
        contract_id=contract_id,
        base_date=interrupt_date,
        base_type=interrupt_type,
        limitation_end_date=new_limitation_end,
        days_remaining=days_remaining,
        status=status,
    )

    if current:
        current.interrupt_event = event_desc
        current.interrupt_date = interrupt_date
        current.interrupt_type = interrupt_type
        current.next_limitation_end = new_limitation_end
        # 将旧记录标记为已过期（被中断）
        if current.status == '有效':
            current.status = '已过期'

    db.session.add(new_record)
    db.session.commit()
    return new_record


def update_all_limitations():
    """定时任务：更新所有时效记录的天数和状态"""
    today = date.today()
    records = LimitationRecord.query.filter(
        LimitationRecord.limitation_end_date.isnot(None),
    ).all()

    for record in records:
        if isinstance(record.limitation_end_date, datetime):
            end_date = record.limitation_end_date.date()
        else:
            end_date = record.limitation_end_date

        days_remaining = (end_date - today).days
        record.days_remaining = days_remaining

        if days_remaining > 90:
            record.status = '有效'
        elif days_remaining > 0:
            record.status = '即将到期'
        else:
            record.status = '已过期'

    db.session.commit()
    return len(records)


def check_warnings():
    """检查需要预警的时效记录（90天/30天/7天）并生成通知"""
    today = date.today()
    notifications = []

    # 查询所有有效或即将到期的时效记录
    records = LimitationRecord.query.filter(
        LimitationRecord.limitation_end_date.isnot(None),
        LimitationRecord.status.in_(['有效', '即将到期']),
    ).all()

    for record in records:
        if isinstance(record.limitation_end_date, datetime):
            end_date = record.limitation_end_date.date()
        else:
            end_date = record.limitation_end_date

        days_remaining = (end_date - today).days
        contract = Contract.query.get(record.contract_id)

        if not contract:
            continue

        # 90天预警
        if days_remaining <= 90 and not record.warning_90_sent:
            notif = _create_warning(record, contract, '90天预警', days_remaining)
            if notif:
                notifications.append(notif)
            record.warning_90_sent = 1

        # 30天预警
        if days_remaining <= 30 and not record.warning_30_sent:
            notif = _create_warning(record, contract, '30天预警', days_remaining)
            if notif:
                notifications.append(notif)
            record.warning_30_sent = 1

        # 7天预警
        if days_remaining <= 7 and not record.warning_7_sent:
            notif = _create_warning(record, contract, '7天预警', days_remaining)
            if notif:
                notifications.append(notif)
            record.warning_7_sent = 1

        # 过期通知
        if days_remaining <= 0 and not record.expired_notice_sent:
            notif = _create_warning(record, contract, '已过期', days_remaining)
            if notif:
                notifications.append(notif)
            record.expired_notice_sent = 1

    db.session.commit()
    return notifications


def _create_warning(record, contract, notify_type, days_remaining):
    """创建预警通知记录"""
    content = (
        f'合同「{contract.project_name}」（编号：{contract.contract_no or "无"}）'
        f'诉讼时效{notify_type}，剩余{days_remaining}天，'
        f'时效到期日：{record.limitation_end_date}。请及时跟进处理。'
    )

    notification = NotificationRecord(
        contract_id=contract.id,
        limitation_id=record.id,
        notify_type=notify_type,
        notify_method='系统通知',
        notify_content=content,
        notify_status='待发送',
    )
    db.session.add(notification)
    return notification
