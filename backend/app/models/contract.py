from datetime import datetime
from app import db


class Contract(db.Model):
    __tablename__ = 'contract'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    contract_no = db.Column(db.String(100))
    project_name = db.Column(db.String(500), nullable=False)
    sign_date = db.Column(db.Date)
    acceptance_date = db.Column(db.Date)
    contract_amount = db.Column(db.Numeric(18, 2), default=0)
    audit_amount = db.Column(db.Numeric(18, 2), default=0)
    payment_method = db.Column(db.Text)
    payment_terms = db.Column(db.Text)
    breach_clause = db.Column(db.Text)
    penalty_interest = db.Column(db.String(100), default='日万分之五')
    status = db.Column(db.String(20), default='执行中')
    total_paid = db.Column(db.Numeric(18, 2), default=0)
    outstanding_amount = db.Column(db.Numeric(18, 2), default=0)
    current_due_amount = db.Column(db.Numeric(18, 2), default=0)
    total_invoiced = db.Column(db.Numeric(18, 2), default=0)
    contract_file = db.Column(db.String(500))
    acceptance_file = db.Column(db.String(500))
    settlement_file = db.Column(db.String(500))
    remark = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)
    updated_by = db.Column(db.Integer)

    payment_nodes = db.relationship('PaymentNode', backref='contract', lazy=True, cascade='all, delete-orphan')
    payment_records = db.relationship('PaymentRecord', backref='contract', lazy=True, cascade='all, delete-orphan')
    invoice_records = db.relationship('InvoiceRecord', backref='contract', lazy=True, cascade='all, delete-orphan')
    collection_records = db.relationship('CollectionRecord', backref='contract', lazy=True, cascade='all, delete-orphan')
    limitation_records = db.relationship('LimitationRecord', backref='contract', lazy=True, cascade='all, delete-orphan')


class PaymentNode(db.Model):
    __tablename__ = 'payment_node'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete='CASCADE'), nullable=False)
    node_no = db.Column(db.Integer, nullable=False)
    node_name = db.Column(db.String(200))
    pay_ratio = db.Column(db.Numeric(5, 2))
    pay_amount = db.Column(db.Numeric(18, 2))
    due_date = db.Column(db.Date)
    due_condition = db.Column(db.Text)
    actual_pay_date = db.Column(db.Date)
    actual_pay_amount = db.Column(db.Numeric(18, 2), default=0)
    status = db.Column(db.String(20), default='未到期')
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
