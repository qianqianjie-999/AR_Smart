from datetime import datetime
from app import db


class PaymentRecord(db.Model):
    __tablename__ = 'payment_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete='CASCADE'), nullable=False)
    payment_no = db.Column(db.Integer)
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    bank_account = db.Column(db.String(100))
    remark = db.Column(db.Text)
    interrupt_limitation = db.Column(db.Integer, default=1)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)
    updated_by = db.Column(db.Integer)
