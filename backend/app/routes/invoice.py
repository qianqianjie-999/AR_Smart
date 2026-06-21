"""开票管理路由"""

from datetime import date, datetime
from flask import Blueprint, g, request

from app import db
from app.models import Contract, InvoiceRecord
from app.utils.auth import login_required
from app.utils.helpers import success_response, error_response, paginate, log_operation

invoice_bp = Blueprint('invoice', __name__, url_prefix='/api/invoice')


def parse_date(date_str):
    """解析日期字符串为date对象"""
    if not date_str:
        return None
    if isinstance(date_str, date):
        return date_str
    try:
        return date.fromisoformat(str(date_str).replace('/', '-'))
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            return None


@invoice_bp.route('/', methods=['GET'])
@login_required
def list_invoices():
    """开票列表（分页）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    contract_id = request.args.get('contract_id', type=int)
    invoice_date_start = request.args.get('invoice_date_start', '')
    invoice_date_end = request.args.get('invoice_date_end', '')

    query = InvoiceRecord.query.filter(InvoiceRecord.is_deleted == 0)

    if contract_id:
        query = query.filter(InvoiceRecord.contract_id == contract_id)
    if invoice_date_start:
        query = query.filter(InvoiceRecord.invoice_date >= invoice_date_start)
    if invoice_date_end:
        query = query.filter(InvoiceRecord.invoice_date <= invoice_date_end)

    query = query.order_by(InvoiceRecord.created_at.desc())

    result = paginate(query, page=page, page_size=page_size)

    data = []
    for item in result['list']:
        contract = Contract.query.get(item.contract_id)
        data.append({
            'id': item.id,
            'contract_id': item.contract_id,
            'invoice_no': item.invoice_no,
            'amount': float(item.amount) if item.amount else 0,
            'tax_rate': float(item.tax_rate) if item.tax_rate else 13,
            'invoice_date': item.invoice_date.strftime('%Y-%m-%d') if item.invoice_date else None,
            'invoice_type': item.invoice_type,
            'invoice_file': item.invoice_file,
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


@invoice_bp.route('/', methods=['POST'])
@login_required
def create_invoice():
    """登记开票"""
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    contract_id = json_data.get('contract_id')
    amount = json_data.get('amount')
    if not contract_id or not amount:
        return error_response('合同ID和开票金额不能为空')

    contract = Contract.query.filter_by(id=contract_id, is_deleted=0).first()
    if not contract:
        return error_response('合同不存在', 404)

    invoice = InvoiceRecord(
        contract_id=contract_id,
        invoice_no=json_data.get('invoice_no', ''),
        amount=amount,
        tax_rate=json_data.get('tax_rate', 13),
        invoice_date=parse_date(json_data.get('invoice_date')),
        invoice_type=json_data.get('invoice_type', ''),
        invoice_file=json_data.get('invoice_file', ''),
        remark=json_data.get('remark', ''),
        created_by=g.get('current_user_id'),
    )
    db.session.add(invoice)

    # 更新合同 total_invoiced
    total_invoiced = db.session.query(
        db.func.coalesce(db.func.sum(InvoiceRecord.amount), 0)
    ).filter(
        InvoiceRecord.contract_id == contract_id,
        InvoiceRecord.is_deleted == 0,
    ).scalar()
    contract.total_invoiced = total_invoiced

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='开票管理',
        action='登记开票',
        content=f'登记开票: 合同 {contract.project_name}, 金额 {amount}',
    )

    return success_response({'id': invoice.id}, '登记开票成功')


@invoice_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_invoice(id):
    """编辑开票"""
    invoice = InvoiceRecord.query.filter_by(id=id, is_deleted=0).first()
    if not invoice:
        return error_response('开票记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    invoice.invoice_no = json_data.get('invoice_no', invoice.invoice_no)
    invoice.amount = json_data.get('amount', invoice.amount)
    invoice.tax_rate = json_data.get('tax_rate', invoice.tax_rate)
    invoice.invoice_date = parse_date(json_data.get('invoice_date')) if json_data.get('invoice_date') else invoice.invoice_date
    invoice.invoice_type = json_data.get('invoice_type', invoice.invoice_type)
    invoice.invoice_file = json_data.get('invoice_file', invoice.invoice_file)
    invoice.remark = json_data.get('remark', invoice.remark)

    # 重新计算合同 total_invoiced
    contract = Contract.query.get(invoice.contract_id)
    if contract:
        total_invoiced = db.session.query(
            db.func.coalesce(db.func.sum(InvoiceRecord.amount), 0)
        ).filter(
            InvoiceRecord.contract_id == invoice.contract_id,
            InvoiceRecord.is_deleted == 0,
        ).scalar()
        contract.total_invoiced = total_invoiced

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='开票管理',
        action='编辑开票',
        content=f'编辑开票 ID:{id}',
    )

    return success_response(message='编辑开票成功')


@invoice_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_invoice(id):
    """删除开票（软删除）"""
    invoice = InvoiceRecord.query.filter_by(id=id, is_deleted=0).first()
    if not invoice:
        return error_response('开票记录不存在', 404)

    contract_id = invoice.contract_id
    invoice.is_deleted = 1

    # 重新计算合同 total_invoiced
    contract = Contract.query.get(contract_id)
    if contract:
        total_invoiced = db.session.query(
            db.func.coalesce(db.func.sum(InvoiceRecord.amount), 0)
        ).filter(
            InvoiceRecord.contract_id == contract_id,
            InvoiceRecord.is_deleted == 0,
        ).scalar()
        contract.total_invoiced = total_invoiced

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='开票管理',
        action='删除开票',
        content=f'删除开票 ID:{id}',
    )

    return success_response(message='删除开票成功')


@invoice_bp.route('/<int:id>/upload', methods=['POST'])
@login_required
def upload_invoice_file(id):
    """上传发票附件"""
    invoice = InvoiceRecord.query.filter_by(id=id, is_deleted=0).first()
    if not invoice:
        return error_response('开票记录不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response('请提供有效的JSON数据')

    if 'invoice_file' in json_data:
        invoice.invoice_file = json_data['invoice_file']

    db.session.commit()

    log_operation(
        user_id=g.get('current_user_id'),
        username=g.get('current_username', ''),
        module='开票管理',
        action='上传发票附件',
        content=f'上传发票附件 ID:{id}',
    )

    return success_response(message='上传发票附件成功')
