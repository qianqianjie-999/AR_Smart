from datetime import datetime
from app import db


class Customer(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    region = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    registered_addr = db.Column(db.String(500))
    contact_addr = db.Column(db.String(500))
    billing_info = db.Column(db.Text)
    business_contact = db.Column(db.String(100))
    credit_level = db.Column(db.String(20), default='B')
    remark = db.Column(db.Text)
    is_deleted = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer)
    updated_by = db.Column(db.Integer)

    contacts = db.relationship('CustomerContact', backref='customer', lazy=True, cascade='all, delete-orphan')
    contracts = db.relationship('Contract', backref='customer', lazy=True)


class CustomerContact(db.Model):
    __tablename__ = 'customer_contact'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    contact_type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    position = db.Column(db.String(100))
    is_primary = db.Column(db.Integer, default=0)
    remark = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
