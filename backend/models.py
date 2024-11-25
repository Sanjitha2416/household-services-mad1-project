from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class CustomerDetails(db.Model):
    __tablename__ = "customer_details"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.Integer, default=1, nullable=False)  # 0 = admin, 1 = customer
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    pincode = db.Column(db.Integer, nullable=False)

    # Relationship: Customer can make multiple service requests
    service_requests = db.relationship(
        'ServiceRequest', 
        cascade="all, delete", 
        backref="customer", 
        lazy=True
    )

class ProfessionalDetails(db.Model):
    __tablename__ = "professional_details"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.Integer, default=1, nullable=False)  # 0 = admin, 1 = professional
    name = db.Column(db.String, nullable=False)
    service = db.Column(db.String, nullable=False)
    experience = db.Column(db.Integer, nullable=False)  
    address = db.Column(db.String, nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="Pending") 

    # Relationship: Professional can handle multiple service requests
    service_requests = db.relationship(
        'ServiceRequest', 
        cascade="all, delete", 
        backref="professional", 
        lazy=True
    )

class Service(db.Model):
    __tablename__ = "service"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)  # Active/Inactive

    # Relationship: A service can have multiple subcategories 
    subcategories = db.relationship(
        'Subcategory', 
        cascade="all, delete", 
        backref="service", 
        lazy=True
    )

    # Relationship: A service can have multiple service requests
    service_requests = db.relationship(
        'ServiceRequest', 
        cascade="all, delete", 
        backref="service", 
        lazy=True
    )

class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)


class ServiceRequest(db.Model):
    __tablename__ = "service_request"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    address = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="Pending", nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer_details.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professional_details.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)

    # Relationship: A service request can have one feedback
    feedback = db.relationship(
        'Feedback', 
        cascade="all, delete", 
        backref="service_request", 
        lazy=True
    )

class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rating = db.Column(db.Integer, nullable=False) 
    remark = db.Column(db.String, nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey("service_request.id"), nullable=False)
