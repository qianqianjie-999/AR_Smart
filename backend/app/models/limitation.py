from datetime import datetime
from app import db


class LimitationRecord(db.Model):
    __tablename__ = 'limitation_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete='CASCADE'), nullable=False)
    base_date = db.Column(db.Date)
    base_type = db.Column(db.String(50))
    limitation_end_date = db.Column(db.Date)
    days_remaining = db.Column(db.Integer)
    status = db.Column(db.String(20), default='有效')
    interrupt_event = db.Column(db.String(500))
    interrupt_date = db.Column(db.Date)
    interrupt_type = db.Column(db.String(50))
    next_limitation_end = db.Column(db.Date)
    warning_90_sent = db.Column(db.Integer, default=0)
    warning_30_sent = db.Column(db.Integer, default=0)
    warning_7_sent = db.Column(db.Integer, default=0)
    expired_notice_sent = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
