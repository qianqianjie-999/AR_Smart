from datetime import datetime
from app import db


class CollectionTemplate(db.Model):
    __tablename__ = 'collection_template'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    template_type = db.Column(db.String(50), default='催款函')
    subject = db.Column(db.String(500))
    content = db.Column(db.Text)
    is_default = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)