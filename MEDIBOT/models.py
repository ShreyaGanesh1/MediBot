from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient' or 'attender'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient_info = db.relationship('PatientInfo', backref='user', uselist=False, cascade='all, delete-orphan')
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True, cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    attended_patients = db.relationship('AttenderPatientAssociation', backref='attender', foreign_keys='AttenderPatientAssociation.attender_id', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class PatientInfo(db.Model):
    __tablename__ = 'patient_info'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blood_group = db.Column(db.String(10))
    known_allergies = db.Column(db.Text)
    chronic_diseases = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PatientInfo for User {self.user_id}>'

class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    is_primary = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<EmergencyContact {self.name} for User {self.user_id}>'

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # e.g., 'diagnosis', 'lab_result', 'prescription'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    hospital_name = db.Column(db.String(200))
    doctor_name = db.Column(db.String(100))
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    encrypted_data = db.Column(db.Text)  # For AES encrypted sensitive data
    
    def __repr__(self):
        return f'<MedicalRecord {self.title} for User {self.user_id}>'

class AttenderPatientAssociation(db.Model):
    __tablename__ = 'attender_patient_associations'
    
    id = db.Column(db.Integer, primary_key=True)
    attender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    relationship = db.Column(db.String(50))
    can_access_location = db.Column(db.Boolean, default=False)
    can_access_medical_records = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Create a relationship to the patient
    patient = db.relationship('User', foreign_keys=[patient_id])
    
    def __repr__(self):
        return f'<AttenderPatientAssociation Attender={self.attender_id} Patient={self.patient_id}>'

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Location for User {self.user_id} at {self.timestamp}>'

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    emergency_number = db.Column(db.String(20))
    website = db.Column(db.String(200))
    rating = db.Column(db.Float, default=0.0)  # Average rating from 0 to 5
    
    # Relationships
    doctors = db.relationship('Doctor', backref='hospital', lazy=True)
    reviews = db.relationship('HospitalReview', backref='hospital', lazy=True)
    
    def __repr__(self):
        return f'<Hospital {self.name}>'

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer)
    availability = db.Column(db.String(200))  # JSON string with availability slots
    rating = db.Column(db.Float, default=0.0)  # Average rating from 0 to 5
    
    # Relationships
    reviews = db.relationship('DoctorReview', backref='doctor', lazy=True)
    
    def __repr__(self):
        return f'<Doctor {self.name} ({self.specialization})>'

class HospitalReview(db.Model):
    __tablename__ = 'hospital_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<HospitalReview for Hospital {self.hospital_id} by User {self.user_id}>'

class DoctorReview(db.Model):
    __tablename__ = 'doctor_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<DoctorReview for Doctor {self.doctor_id} by User {self.user_id}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)  # Format: HH:MM
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'completed', 'cancelled'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id])
    
    def __repr__(self):
        return f'<Appointment for Patient {self.patient_id} with Doctor {self.doctor_id}>'

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_video = db.Column(db.Boolean, default=False)
    
    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id])
    messages = db.relationship('ChatMessage', backref='chat', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chat between Patient {self.patient_id} and Doctor {self.doctor_id}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'doctor'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatMessage in Chat {self.chat_id} from {self.sender_type}>'

class InsurancePolicy(db.Model):
    __tablename__ = 'insurance_policies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    coverage_amount = db.Column(db.Float, nullable=False)
    premium = db.Column(db.Float, nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    benefits = db.Column(db.Text)  # JSON string with list of benefits
    
    def __repr__(self):
        return f'<InsurancePolicy {self.name} by {self.provider}>'

class UserInsurance(db.Model):
    __tablename__ = 'user_insurance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('insurance_policies.id'), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    premium_amount = db.Column(db.Float, nullable=False)
    payment_frequency = db.Column(db.String(20), nullable=False)  # 'monthly', 'quarterly', 'annually'
    status = db.Column(db.String(20), default='active')  # 'active', 'expired', 'cancelled'
    
    # Relationships
    user = db.relationship('User')
    policy = db.relationship('InsurancePolicy')
    
    def __repr__(self):
        return f'<UserInsurance for User {self.user_id} - Policy {self.policy_id}>'

class MentalHealthSession(db.Model):
    __tablename__ = 'mental_health_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    summary = db.Column(db.Text)
    
    # Relationships
    messages = db.relationship('MentalHealthMessage', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MentalHealthSession for User {self.user_id}>'

class MentalHealthMessage(db.Model):
    __tablename__ = 'mental_health_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('mental_health_sessions.id'), nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        sender = "User" if self.is_from_user else "Bot"
        return f'<MentalHealthMessage in Session {self.session_id} from {sender}>'
