from datetime import datetime
from app import db


class CollectionRecord(db.Model):
    __tablename__ = 'collection_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete='CASCADE'), nullable=False)
    collection_date = db.Column(db.Date)
    collection_type = db.Column(db.String(50))
    collection_content = db.Column(db.Text)
    express_no = db.Column(db.String(100))
    recipient = db.Column(db.String(100))
    sign_status = db.Column(db.String(20))
    collection_file = db.Column(db.String(500))
    is_limitation_interrupt = db.Column(db.Integer, default=1)
    remark = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)
