from datetime import datetime
from app import db


class NotificationRecord(db.Model):
    __tablename__ = 'notification_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, nullable=False)
    limitation_id = db.Column(db.Integer)
    notify_type = db.Column(db.String(20))
    notify_method = db.Column(db.String(50))
    notify_content = db.Column(db.Text)
    notify_status = db.Column(db.String(20), default='待发送')
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
