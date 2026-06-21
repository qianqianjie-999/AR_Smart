#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业应收账款管理系统（ARMS）- Excel数据导入工具
从Excel文件导入历史应收账款数据

使用方法：
    python import_excel.py /path/to/应收帐款.xls

Excel格式说明（参考开发文档附录A）：
- header=2（第3行为表头）
- 字段映射见下方 FIELD_MAP
"""

import sys
import os
import json
import re
from datetime import datetime, date, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.customer import Customer, CustomerContact
from app.models.contract import Contract, PaymentNode
from app.models.payment import PaymentRecord
from app.models.invoice import InvoiceRecord
from app.models.collection import CollectionRecord
from app.models.limitation import LimitationRecord
from app.services.limitation_service import calc_limitation_end

app = create_app()

# ============================================
# Excel列名 -> 系统字段映射
# ============================================
FIELD_MAP = {
    '区域': 'region',
    '客户名称': 'name',
    '客户注册地址': 'registered_addr',
    '客户联系地址': 'contact_addr',
    '开票信息': 'billing_info',
    '客户联系人': 'contact_person',
    '合同编号': 'contract_no',
    '项目名称': 'project_name',
    '签订日期': 'sign_date',
    '验收日期': 'acceptance_date',
    '合同金额': 'contract_amount',
    '审计（结算）金额': 'audit_amount',
    '收回货款': 'payments',
    '尚欠金额': 'outstanding_amount',
    '付款方式': 'payment_method',
    '付款节点': 'payment_terms',
    '截止到2025年6月份到期应收款金额': 'due_amount',
    '最后一次付款结点': 'last_payment_node',
    '最近一次付款时间': 'last_payment_date',
    '最后一次催款函时间（EMS）': 'last_collection_date',
    '开票金额': 'invoices',
    '业务联系人': 'business_contact',
    '合同附件': 'contract_file',
    '验收资料附件': 'acceptance_file',
    '结算附件': 'settlement_file',
    '发票附件': 'invoice_file',
    '催款函附件': 'collection_file',
    '中断时效时间': 'interrupt_date',
}


def clean_value(val):
    """清理单元格值"""
    if pd.isna(val) or val in ('', 'nan', 'NaN', 'None', None):
        return None
    if isinstance(val, str):
        val = val.strip()
        if val in ('', '-', '--', '无', '/', 'nan', 'NaN'):
            return None
    return val


def parse_date(val):
    """解析日期"""
    val = clean_value(val)
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    if isinstance(val, (int, float)):
        # Excel日期序列号
        from datetime import date, timedelta
        return date(1899, 12, 30) + timedelta(days=int(val))
    # 字符串解析
    val = str(val).strip()
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
        '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
        '%Y年%m月%d日', '%m/%d/%Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    # 尝试用pandas解析
    try:
        return pd.to_datetime(val).date()
    except Exception:
        pass
    print(f"  [警告] 无法解析日期: {val}")
    return None


def parse_amount(val):
    """解析金额（元）"""
    val = clean_value(val)
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    val = str(val).replace(',', '').replace('，', '').replace('¥', '').replace('元', '').strip()
    try:
        return round(float(val), 2)
    except ValueError:
        return 0.0


def parse_payment_terms(text):
    """解析付款节点文本"""
    nodes = []
    text = clean_value(text)
    if not text:
        return nodes

    # 尝试JSON解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for i, item in enumerate(data):
                nodes.append({
                    'node_no': item.get('node_no', i + 1),
                    'node_name': str(item.get('node_name', f'第{i+1}期')),
                    'pay_ratio': float(item.get('pay_ratio', 0)),
                    'pay_amount': float(item.get('pay_amount', 0)),
                    'due_date': item.get('due_date'),
                    'due_condition': str(item.get('due_condition', '')),
                })
            return nodes
    except (json.JSONDecodeError, ValueError):
        pass

    # 文本解析：使用正则匹配 "节点名称 比例% 金额 日期" 或类似格式
    # 常见的格式：
    # 1. 预付款30%  验收款60%  质保金10%
    # 2. 序号.名称:比例,金额,日期
    # 简单处理：按换行或分号分割
    parts = re.split(r'[\n;；。]', text)
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        # 尝试提取名称和比例
        node_name = part
        pay_ratio = 0
        due_date = None
        # 提取比例
        ratio_match = re.search(r'(\d+(?:\.\d+)?)\s*%', part)
        if ratio_match:
            pay_ratio = float(ratio_match.group(1))
            node_name = re.sub(r'\d+(?:\.\d+)?\s*%', '', part).strip()

        nodes.append({
            'node_no': i + 1,
            'node_name': node_name or f'第{i+1}期',
            'pay_ratio': pay_ratio,
            'pay_amount': 0,
            'due_date': due_date,
            'due_condition': '',
        })

    return nodes


def parse_payments(text):
    """解析回款记录文本"""
    payments = []
    text = clean_value(text)
    if not text:
        return payments

    # 尝试JSON解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except (json.JSONDecodeError, ValueError):
        pass

    # 文本解析：多笔回款通常用换行或分号分隔
    # 格式：日期 金额(元) 方式 或 金额 日期
    parts = re.split(r'[\n;；]', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 提取日期
        date_match = re.search(r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})', part)
        payment_date = parse_date(date_match.group(1)) if date_match else None

        # 提取金额
        amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:元|万)?', part)
        amount = parse_amount(amount_match.group(1)) if amount_match else 0

        # 提取方式
        method = '银行转账'
        if '承兑' in part:
            method = '银行承兑'
        elif '现金' in part:
            method = '现金'

        payments.append({
            'amount': amount,
            'payment_date': payment_date,
            'payment_method': method,
            'interrupt_limitation': 1,
        })

    return payments


def calc_limitation(contract_id):
    """
    计算合同的最新诉讼时效
    基准日期 = max(最后一次回款日期, 最后一次催款日期, 验收日期)
    时效到期日 = 基准日期 + 3年
    """
    contract = Contract.query.get(contract_id)
    if not contract:
        return None

    dates = []

    # 最后一次回款日期
    last_payment = PaymentRecord.query.filter_by(
        contract_id=contract_id, is_deleted=0
    ).order_by(PaymentRecord.payment_date.desc()).first()
    if last_payment and last_payment.payment_date:
        dates.append(last_payment.payment_date)

    # 最后一次催款日期
    last_collection = CollectionRecord.query.filter_by(
        contract_id=contract_id, is_deleted=0
    ).order_by(CollectionRecord.collection_date.desc()).first()
    if last_collection and last_collection.collection_date:
        dates.append(last_collection.collection_date)

    # 验收日期
    if contract.acceptance_date:
        dates.append(contract.acceptance_date)

    # 签订日期（兜底）
    if not dates and contract.sign_date:
        dates.append(contract.sign_date)

    if not dates:
        dates.append(date.today())

    base_date = max(dates)
    limitation_end = base_date + timedelta(days=3 * 365)  # 简化：3年 = 3*365天
    days_remaining = (limitation_end - date.today()).days

    if days_remaining > 90:
        status = '有效'
    elif days_remaining > 0:
        status = '即将到期'
    else:
        status = '已过期'

    return {
        'base_date': base_date,
        'limitation_end_date': limitation_end,
        'days_remaining': days_remaining,
        'status': status,
    }


def import_excel(file_path):
    """主导入函数"""
    import pandas as pd

    print(f"\n{'='*60}")
    print(f"  企业应收账款管理系统 - Excel数据导入工具")
    print(f"{'='*60}")
    print(f"  文件: {file_path}")

    # 读取Excel
    print(f"\n[1/5] 读取Excel文件...")
    df = pd.read_excel(file_path, header=None)

    # 智能识别表头行
    header_row = None
    for i in range(min(5, len(df))):
        row_vals = [str(v) for v in df.iloc[i] if pd.notna(v)]
        if any(kw in ' '.join(row_vals) for kw in ['客户名称', '项目名称', '合同金额', '区域']):
            header_row = i
            break

    if header_row is None:
        header_row = 2  # 默认第3行
        print(f"  未找到表头，使用默认行号: {header_row + 1}")
    else:
        print(f"  识别表头位于第 {header_row + 1} 行")

    # 重新读取，使用正确的表头
    df = pd.read_excel(file_path, header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    print(f"  数据行数: {len(df)}, 列数: {len(df.columns)}")
    print(f"  列名: {list(df.columns)}")

    # 字段映射
    print(f"\n[2/5] 字段映射...")
    col_map = {}
    for col in df.columns:
        for excel_name, sys_name in FIELD_MAP.items():
            if excel_name in col or col in excel_name:
                col_map[sys_name] = col
                break
    print(f"  映射字段: {list(col_map.keys())}")

    # 逐行导入
    print(f"\n[3/5] 逐行导入数据...")
    success_count = 0
    error_count = 0
    errors = []

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                row_num = idx + 2  # Excel行号
                customer_name = clean_value(row.get(col_map.get('name', ''), ''))

                if not customer_name:
                    print(f"  跳过第{row_num}行：无客户名称")
                    continue

                # --- 1. 创建/获取客户 ---
                customer = Customer.query.filter_by(name=customer_name, is_deleted=0).first()
                if not customer:
                    billing_info = str(clean_value(row.get(col_map.get('billing_info', ''), '') or ''))
                    customer = Customer(
                        region=str(clean_value(row.get(col_map.get('region', ''), '') or '未知')),
                        name=customer_name,
                        registered_addr=str(clean_value(row.get(col_map.get('registered_addr', ''), '') or '')),
                        contact_addr=str(clean_value(row.get(col_map.get('contact_addr', ''), '') or '')),
                        billing_info=billing_info if billing_info else None,
                        business_contact=str(clean_value(row.get(col_map.get('business_contact', ''), '') or '')),
                        credit_level='B',
                    )
                    db.session.add(customer)
                    db.session.flush()

                # --- 2. 创建联系人（如果有） ---
                contact_val = clean_value(row.get(col_map.get('contact_person', ''), ''))
                if contact_val:
                    existing_contact = CustomerContact.query.filter_by(customer_id=customer.id).first()
                    if not existing_contact:
                        contact = CustomerContact(
                            customer_id=customer.id,
                            contact_type='第一',
                            name=str(contact_val),
                            is_primary=1,
                        )
                        db.session.add(contact)

                # --- 3. 创建合同 ---
                project_name = clean_value(row.get(col_map.get('project_name', ''), ''))
                if not project_name:
                    print(f"  跳过第{row_num}行：无项目名称")
                    continue

                contract_no = clean_value(row.get(col_map.get('contract_no', ''), ''))
                contract = Contract(
                    customer_id=customer.id,
                    contract_no=str(contract_no) if contract_no else None,
                    project_name=str(project_name),
                    sign_date=parse_date(row.get(col_map.get('sign_date', ''), '')),
                    acceptance_date=parse_date(row.get(col_map.get('acceptance_date', ''), '')),
                    contract_amount=parse_amount(row.get(col_map.get('contract_amount', ''), 0)),
                    audit_amount=parse_amount(row.get(col_map.get('audit_amount', ''), 0)),
                    payment_method=str(clean_value(row.get(col_map.get('payment_method', ''), '') or '')),
                    payment_terms=str(clean_value(row.get(col_map.get('payment_terms', ''), '') or '')),
                    status='执行中',
                )
                db.session.add(contract)
                db.session.flush()

                # --- 4. 创建付款节点 ---
                payment_terms = str(clean_value(row.get(col_map.get('payment_terms', ''), '') or ''))
                nodes = parse_payment_terms(payment_terms)
                if nodes:
                    total_pay_amount = 0
                    for node in nodes:
                        # 根据合同金额和比例计算应付金额
                        base_amount = contract.audit_amount if contract.audit_amount > 0 else contract.contract_amount
                        if node['pay_ratio'] > 0:
                            node['pay_amount'] = round(base_amount * node['pay_ratio'] / 100, 2)
                        pn = PaymentNode(
                            contract_id=contract.id,
                            node_no=node['node_no'],
                            node_name=node['node_name'],
                            pay_ratio=node['pay_ratio'],
                            pay_amount=node['pay_amount'],
                            due_date=node['due_date'],
                            due_condition=node.get('due_condition', ''),
                            status='未到期',
                        )
                        db.session.add(pn)
                        total_pay_amount += node['pay_amount']
                else:
                    # 如果没有解析出节点，创建一个默认节点
                    pn = PaymentNode(
                        contract_id=contract.id,
                        node_no=1,
                        node_name='合同金额',
                        pay_ratio=100,
                        pay_amount=contract.audit_amount or contract.contract_amount,
                        status='未到期',
                    )
                    db.session.add(pn)

                # --- 5. 创建回款记录 ---
                payments_text = str(clean_value(row.get(col_map.get('payments', ''), '') or ''))
                payments = parse_payments(payments_text)
                total_paid = 0
                for i, pmt in enumerate(payments):
                    if pmt['amount'] > 0:
                        pr = PaymentRecord(
                            contract_id=contract.id,
                            payment_no=i + 1,
                            amount=pmt['amount'],
                            payment_date=pmt.get('payment_date'),
                            payment_method=pmt.get('payment_method', '银行转账'),
                            interrupt_limitation=pmt.get('interrupt_limitation', 1),
                        )
                        db.session.add(pr)
                        total_paid += pmt['amount']

                # --- 6. 计算尚欠金额 ---
                contract.total_paid = total_paid
                if contract.audit_amount > 0:
                    contract.outstanding_amount = contract.audit_amount - total_paid
                else:
                    contract.outstanding_amount = contract.contract_amount - total_paid

                # --- 7. 创建催款记录（如果有最后一次催款时间） ---
                last_collection_date = parse_date(row.get(col_map.get('last_collection_date', ''), ''))
                if last_collection_date:
                    cr = CollectionRecord(
                        contract_id=contract.id,
                        collection_date=last_collection_date,
                        collection_type='EMS',
                        collection_content=f'历史催款记录（从Excel导入）',
                        sign_status='已签收',
                        is_limitation_interrupt=1,
                    )
                    db.session.add(cr)

                # --- 8. 初始化时效记录 ---
                limitation_info = calc_limitation(contract.id)
                if limitation_info:
                    lr = LimitationRecord(
                        contract_id=contract.id,
                        base_date=limitation_info['base_date'],
                        base_type='auto',
                        limitation_end_date=limitation_info['limitation_end_date'],
                        days_remaining=limitation_info['days_remaining'],
                        status=limitation_info['status'],
                    )
                    db.session.add(lr)

                success_count += 1
                if success_count % 10 == 0:
                    print(f"  已导入 {success_count} 行...")

            except Exception as e:
                error_count += 1
                error_msg = f"第{idx+2}行导入失败: {str(e)}"
                errors.append(error_msg)
                print(f"  [错误] {error_msg}")
                continue

        # 提交事务
        print(f"\n[4/5] 提交数据到数据库...")
        try:
            db.session.commit()
            print(f"  提交成功！")
        except Exception as e:
            db.session.rollback()
            print(f"  [错误] 提交失败: {e}")
            error_count += 1

    # 统计信息
    print(f"\n[5/5] 导入完成！")
    print(f"\n{'='*60}")
    print(f"  成功导入: {success_count} 条")
    print(f"  失败: {error_count} 条")
    if errors:
        print(f"\n  失败详情:")
        for err in errors[:10]:  # 只显示前10条
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... 还有 {len(errors) - 10} 条错误")
    print(f"{'='*60}\n")

    return success_count, error_count


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python import_excel.py <Excel文件路径>")
        print("示例: python import_excel.py ../应收帐款.xls")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    import_excel(file_path)
