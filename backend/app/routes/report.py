"""报表中心路由"""

from datetime import date, timedelta
from flask import Blueprint, g, request, send_file
from sqlalchemy import func

from app import db
from app.models import Customer, Contract, PaymentNode, PaymentRecord, LimitationRecord
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate

report_bp = Blueprint('report', __name__, url_prefix='/api/report')


@report_bp.route('/summary', methods=['GET'])
@login_required
def summary():
    """首页仪表盘统计"""
    today = date.today()
    seven_days_later = today + timedelta(days=7)

    total_customers = Customer.query.filter_by(is_deleted=0).count()
    total_contracts = Contract.query.filter_by(is_deleted=0).count()

    agg = db.session.query(
        func.coalesce(func.sum(Contract.contract_amount), 0).label('total_contract'),
        func.coalesce(func.sum(Contract.audit_amount), 0).label('total_audit'),
        func.coalesce(func.sum(Contract.total_paid), 0).label('total_paid'),
        func.coalesce(func.sum(Contract.outstanding_amount), 0).label('total_outstanding'),
        func.coalesce(func.sum(Contract.current_due_amount), 0).label('total_due'),
    ).filter(Contract.is_deleted == 0).first()

    # 应收账款总额 = 逾期节点的未付金额合计（从付款节点实时计算）
    total_receivable = db.session.query(
        func.coalesce(func.sum(PaymentNode.pay_amount - PaymentNode.actual_pay_amount), 0)
    ).join(Contract, Contract.id == PaymentNode.contract_id).filter(
        Contract.is_deleted == 0,
        PaymentNode.due_date <= today,
        PaymentNode.status == '逾期',
    ).scalar() or 0

    # 到期应收款 = 逾期节点的未付金额合计（同应收账款总额）
    total_due_amount = total_receivable

    # 实时计算尚欠金额（从付款节点确保与合同详情一致）
    # 优先从 contract 表读取（已通过核销更新），但也保留从节点计算的兜底
    realtime_outstanding = float(agg.total_outstanding) if agg.total_outstanding else 0

    # 即将到期时效数（90天内到期的合同）
    expiring_limitations = 0
    latest_lim_subq = db.session.query(
        LimitationRecord.contract_id,
        func.max(LimitationRecord.created_at).label('max_created')
    ).group_by(LimitationRecord.contract_id).subquery()

    lim_records = db.session.query(LimitationRecord).join(
        latest_lim_subq,
        (LimitationRecord.contract_id == latest_lim_subq.c.contract_id) &
        (LimitationRecord.created_at == latest_lim_subq.c.max_created)
    ).join(Contract, Contract.id == LimitationRecord.contract_id).filter(
        Contract.is_deleted == 0
    ).all()
    for r in lim_records:
        if r.days_remaining is not None and 0 < r.days_remaining <= 90:
            expiring_limitations += 1

    # 近期到期预警（7天内到期的付款节点）
    warnings = []
    warning_nodes = db.session.query(
        PaymentNode,
        Contract.contract_no,
        Contract.project_name,
        Customer.name.label('customer_name'),
    ).join(Contract, Contract.id == PaymentNode.contract_id).outerjoin(
        Customer, Customer.id == Contract.customer_id
    ).filter(
        Contract.is_deleted == 0,
        PaymentNode.due_date.isnot(None),
        PaymentNode.due_date <= seven_days_later,
        PaymentNode.status.in_(['未到期', '逾期']),
    ).order_by(PaymentNode.due_date.asc()).limit(10).all()

    for item in warning_nodes:
        node = item[0]
        remaining = (node.due_date - today).days if node.due_date else 0
        status = '已过期' if remaining < 0 else '即将到期'
        warnings.append({
            'contract_no': item[1],
            'customer_name': item[3],
            'due_date': node.due_date.strftime('%Y-%m-%d') if node.due_date else None,
            'remaining_days': max(remaining, 0),
            'amount': float(node.pay_amount) if node.pay_amount else 0,
            'status': status,
        })

    return success_response({
        # DashboardView 使用（camelCase）
        'customerCount': total_customers,
        'contractCount': total_contracts,
        'totalReceivable': float(total_receivable),
        'outstandingAmount': realtime_outstanding,
        'dueReceivable': float(total_due_amount),
        'expiringLimitations': expiring_limitations,
        # ReportView 使用（snake_case）
        'total_customers': total_customers,
        'total_contracts': total_contracts,
        'total_contract_amount': float(agg.total_contract) if agg.total_contract else 0,
        'total_paid': float(agg.total_paid) if agg.total_paid else 0,
        'total_outstanding': realtime_outstanding,
        'total_due': float(total_due_amount),
        'warnings': warnings,
    })


@report_bp.route('/regional', methods=['GET'])
@login_required
def regional():
    """区域分布统计"""
    results = db.session.query(
        Customer.region,
        func.count(func.distinct(Contract.id)).label('contract_count'),
        func.coalesce(func.sum(Contract.contract_amount), 0).label('total_amount'),
        func.coalesce(func.sum(Contract.outstanding_amount), 0).label('outstanding_amount'),
        func.count(func.distinct(Customer.id)).label('customer_count'),
    ).outerjoin(Contract, (Contract.customer_id == Customer.id) & (Contract.is_deleted == 0)).filter(
        Customer.is_deleted == 0,
        Customer.region.isnot(None),
        Customer.region != '',
    ).group_by(Customer.region).order_by(func.sum(Contract.outstanding_amount).desc()).all()

    data = []
    for r in results:
        data.append({
            'region': r.region,
            'contract_count': r.contract_count,
            'total_amount': float(r.total_amount) if r.total_amount else 0,
            'outstanding_amount': float(r.outstanding_amount) if r.outstanding_amount else 0,
            'customer_count': r.customer_count,
        })

    return success_response(data)


@report_bp.route('/customer-ranking', methods=['GET'])
@login_required
def customer_ranking():
    """客户欠款TOP10"""
    limit = request.args.get('limit', 10, type=int)

    results = db.session.query(
        Customer.name.label('customer_name'),
        Customer.region,
        func.coalesce(func.sum(Contract.outstanding_amount), 0).label('outstanding_amount'),
        func.count(Contract.id).label('contract_count'),
    ).join(Contract, (Contract.customer_id == Customer.id) & (Contract.is_deleted == 0)).filter(
        Customer.is_deleted == 0,
    ).group_by(Customer.id).order_by(func.sum(Contract.outstanding_amount).desc()).limit(limit).all()

    data = []
    for r in results:
        data.append({
            'customer_name': r.customer_name,
            'region': r.region,
            'outstanding_amount': float(r.outstanding_amount) if r.outstanding_amount else 0,
            'contract_count': r.contract_count,
        })

    return success_response(data)


@report_bp.route('/aging', methods=['GET'])
@login_required
def aging():
    """账龄分析"""
    today = date.today()
    cutoff_1y = today - timedelta(days=365)
    cutoff_2y = today - timedelta(days=2 * 365)
    cutoff_3y = today - timedelta(days=3 * 365)

    contracts = Contract.query.filter(Contract.is_deleted == 0, Contract.outstanding_amount > 0).all()

    aging_0_1y = {'count': 0, 'amount': 0.0}
    aging_1_2y = {'count': 0, 'amount': 0.0}
    aging_2_3y = {'count': 0, 'amount': 0.0}
    aging_over_3y = {'count': 0, 'amount': 0.0}
    details = []

    for c in contracts:
        sign_date = c.sign_date
        outstanding = float(c.outstanding_amount) if c.outstanding_amount else 0
        aging_days = (today - sign_date).days if sign_date else 0

        customer = Customer.query.get(c.customer_id)
        detail = {
            'contract_id': c.id,
            'project_name': c.project_name,
            'customer_name': customer.name if customer else '',
            'sign_date': sign_date.strftime('%Y-%m-%d') if sign_date else None,
            'outstanding_amount': outstanding,
            'aging_days': aging_days,
        }
        details.append(detail)

        if sign_date and sign_date > cutoff_1y:
            aging_0_1y['count'] += 1
            aging_0_1y['amount'] += outstanding
        elif sign_date and sign_date > cutoff_2y:
            aging_1_2y['count'] += 1
            aging_1_2y['amount'] += outstanding
        elif sign_date and sign_date > cutoff_3y:
            aging_2_3y['count'] += 1
            aging_2_3y['amount'] += outstanding
        else:
            aging_over_3y['count'] += 1
            aging_over_3y['amount'] += outstanding

    return success_response({
        'aging_0_1y': aging_0_1y,
        'aging_1_2y': aging_1_2y,
        'aging_2_3y': aging_2_3y,
        'aging_over_3y': aging_over_3y,
        'details': details,
    })


@report_bp.route('/due-receivable', methods=['GET'])
@login_required
def due_receivable():
    """到期应收款明细"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    today = date.today()

    query = db.session.query(
        PaymentNode,
        Contract.project_name,
        Customer.name.label('customer_name'),
    ).join(Contract, Contract.id == PaymentNode.contract_id).outerjoin(
        Customer, Customer.id == Contract.customer_id
    ).filter(
        Contract.is_deleted == 0,
        PaymentNode.status == '逾期',
    ).order_by(PaymentNode.due_date.asc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        node = item[0] if isinstance(item, tuple) else item.PaymentNode
        project_name = item[1] if isinstance(item, tuple) else item.project_name
        customer_name = item[2] if isinstance(item, tuple) else item.customer_name

        days_overdue = (today - node.due_date).days if node.due_date else 0
        data.append({
            'contract_id': node.contract_id,
            'project_name': project_name,
            'customer_name': customer_name,
            'node_name': node.node_name,
            'due_date': node.due_date.strftime('%Y-%m-%d') if node.due_date else None,
            'pay_amount': float(node.pay_amount) if node.pay_amount else 0,
            'days_overdue': days_overdue,
        })

    return success_response({
        'list': data,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
    })


@report_bp.route('/payment-trend', methods=['GET'])
@login_required
def payment_trend():
    """回款趋势 - 返回近6个月统计"""
    records = PaymentRecord.query.filter(
        PaymentRecord.is_deleted == 0,
        PaymentRecord.payment_date.isnot(None),
    ).all()

    # 按月份聚合
    from collections import defaultdict
    month_map = defaultdict(float)
    for r in records:
        key = r.payment_date.strftime('%Y-%m')
        month_map[key] += float(r.amount) if r.amount else 0

    # 取最近6个月（含当前月），按日历月计算
    months = []
    amounts = []
    today = date.today()
    for i in range(5, -1, -1):
        # 从5个月前开始，逐月推算
        target_month = today - timedelta(days=30 * i)
        # 更精确地计算月份：每月1号
        year = target_month.year
        month = target_month.month
        key = f'{year:04d}-{month:02d}'
        label = f'{month}月'
        months.append(label)
        amounts.append(round(month_map.get(key, 0), 2))

    # 返回两种格式：数组兼容 DashboardView，对象兼容 ReportView
    trend_list = [{'period': months[i], 'amount': amounts[i]} for i in range(len(months))]

    return success_response({
        'months': months,
        'amounts': amounts,
        'trendList': trend_list,
    })


@report_bp.route('/limitation-stats', methods=['GET'])
@login_required
def limitation_stats():
    """时效状态统计"""
    today = date.today()

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

    active = 0
    expiring_soon = 0
    expired = 0

    for r in records:
        days = r.days_remaining
        if days is not None and days <= 0:
            expired += 1
        elif days is not None and days <= 90:
            expiring_soon += 1
        else:
            active += 1

    # 返回两种格式：数组给 DashboardView pieChart，对象给 ReportView
    array_format = [
        {'name': '有效', 'value': active},
        {'name': '即将到期', 'value': expiring_soon},
        {'name': '已过期', 'value': expired},
    ]
    obj_format = {
        'active': active,
        'expiring_soon': expiring_soon,
        'expired': expired,
    }

    # 返回数组作为 data（兼容 DashboardView），在 info 中返回对象格式
    return success_response({
        'array': array_format,
        'object': obj_format,
    })



@report_bp.route('/export/<report_type>', methods=['GET'])
@login_required
def export_report(report_type):
    """导出报表Excel"""
    try:
        import openpyxl
        from io import BytesIO
    except ImportError:
        return error_response('导出功能需要安装 openpyxl 库', 500)

    def _get_json(resp):
        """Extract JSON data from Flask response tuple."""
        if isinstance(resp, tuple):
            return resp[0].get_json()
        return resp.get_json()

    wb = openpyxl.Workbook()

    if report_type == 'summary':
        ws = wb.active
        ws.title = '应收账款总览'
        summary_data = _get_json(summary())
        if summary_data.get('code') == 200:
            data = summary_data['data']
            ws.append(['指标', '数值'])
            for k, v in data.items():
                ws.append([k, v])

    elif report_type == 'regional':
        ws = wb.active
        ws.title = '区域分布'
        ws.append(['区域', '合同数量', '总金额', '欠款金额', '客户数量'])
        regional_data = _get_json(regional())
        if regional_data.get('code') == 200:
            for item in regional_data['data']:
                ws.append([
                    item.get('region'),
                    item.get('contract_count'),
                    item.get('total_amount'),
                    item.get('outstanding_amount'),
                    item.get('customer_count'),
                ])

    elif report_type == 'aging':
        ws = wb.active
        ws.title = '账龄分析'
        aging_data = _get_json(aging())
        if aging_data.get('code') == 200:
            data = aging_data['data']
            ws.append(['账龄区间', '合同数', '金额'])
            ws.append(['0-1年', data['aging_0_1y']['count'], data['aging_0_1y']['amount']])
            ws.append(['1-2年', data['aging_1_2y']['count'], data['aging_1_2y']['amount']])
            ws.append(['2-3年', data['aging_2_3y']['count'], data['aging_2_3y']['amount']])
            ws.append(['>3年', data['aging_over_3y']['count'], data['aging_over_3y']['amount']])
            # Add details in second sheet
            ws2 = wb.create_sheet('账龄明细')
            ws2.append(['合同ID', '项目名称', '客户名称', '签订日期', '欠款金额', '账龄天数'])
            for d in data.get('details', []):
                ws2.append([
                    d.get('contract_id'),
                    d.get('project_name'),
                    d.get('customer_name'),
                    d.get('sign_date'),
                    d.get('outstanding_amount'),
                    d.get('aging_days'),
                ])

    elif report_type == 'due-receivable':
        ws = wb.active
        ws.title = '到期应收款'
        ws.append(['合同ID', '项目名称', '客户名称', '节点名称', '到期日', '金额', '逾期天数'])
        due_data = _get_json(due_receivable())
        if due_data.get('code') == 200:
            for item in due_data['data'].get('list', []):
                ws.append([
                    item.get('contract_id'),
                    item.get('project_name'),
                    item.get('customer_name'),
                    item.get('node_name'),
                    item.get('due_date'),
                    item.get('pay_amount'),
                    item.get('days_overdue'),
                ])

    else:
        return error_response(f'未知的报表类型: {report_type}', 400)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{report_type}_报表_{date.today().strftime("%Y%m%d")}.xlsx',
    )
