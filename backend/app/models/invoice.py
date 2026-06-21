from datetime import datetime
from app import db


class InvoiceRecord(db.Model):
    __tablename__ = 'invoice_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete='CASCADE'), nullable=False)
    invoice_no = db.Column(db.String(100))
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=13)
    invoice_date = db.Column(db.Date)
    invoice_type = db.Column(db.String(50))
    invoice_file = db.Column(db.String(500))
    remark = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)
