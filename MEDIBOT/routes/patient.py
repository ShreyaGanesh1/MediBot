from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from models import (
    User, PatientInfo, EmergencyContact, Location, Hospital, Doctor, 
    Appointment, Chat, ChatMessage, MedicalRecord
)
from app import db
from utils.encryption import encrypt_data, decrypt_data
from utils.location import get_nearby_hospitals, get_location, get_offline_map_data
from datetime import datetime

patient_bp = Blueprint('patient', __name__)

# Check if user is logged in and is a patient
from functools import wraps

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'patient':
            flash('You must be logged in as a patient to access this page', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@patient_required
def dashboard():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    patient_info = PatientInfo.query.filter_by(user_id=user_id).first()
    emergency_contacts = EmergencyContact.query.filter_by(user_id=user_id).all()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=user_id, 
        status='scheduled'
    ).order_by(Appointment.date).limit(5).all()
    
    # Get recent medical records
    recent_records = MedicalRecord.query.filter_by(
        user_id=user_id
    ).order_by(MedicalRecord.date.desc()).limit(5).all()
    
    return render_template(
        'patient/dashboard.html',
        user=user,
        patient_info=patient_info,
        emergency_contacts=emergency_contacts,
        upcoming_appointments=upcoming_appointments,
        recent_records=recent_records
    )

@patient_bp.route('/emergency')
@patient_required
def emergency():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    emergency_contacts = EmergencyContact.query.filter_by(user_id=user_id).all()
    
    # Get current location for map initialization
    current_location = get_location()
    
    # Get nearby hospitals
    nearby_hospitals = get_nearby_hospitals(current_location['latitude'], current_location['longitude'])
    
    return render_template(
        'patient/emergency.html',
        user=user,
        emergency_contacts=emergency_contacts,
        current_location=current_location,
        nearby_hospitals=nearby_hospitals
    )

@patient_bp.route('/health-tracking')
@patient_required
def health_tracking():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    patient_info = PatientInfo.query.filter_by(user_id=user_id).first()
    medical_records = MedicalRecord.query.filter_by(user_id=user_id).order_by(MedicalRecord.date.desc()).all()
    
    return render_template(
        'patient/health_tracking.html',
        user=user,
        patient_info=patient_info,
        medical_records=medical_records
    )

@patient_bp.route('/hospitals')
@patient_required
def hospitals():
    # Get all hospitals
    hospitals = Hospital.query.all()
    
    # Get current location for map initialization
    current_location = get_location()
    
    return render_template(
        'patient/hospitals.html',
        hospitals=hospitals,
        current_location=current_location
    )

@patient_bp.route('/doctors')
@patient_bp.route('/doctors/<int:hospital_id>')
@patient_required
def doctors(hospital_id=None):
    # Get all doctors or filter by hospital
    if hospital_id:
        doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
        hospital = Hospital.query.get_or_404(hospital_id)
    else:
        doctors = Doctor.query.all()
        hospital = None
    
    return render_template(
        'patient/doctors.html',
        doctors=doctors,
        hospital=hospital
    )

@patient_bp.route('/chat/<int:doctor_id>', methods=['GET', 'POST'])
@patient_required
def chat(doctor_id):
    user_id = session.get('user_id')
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get or create chat session
    chat_session = Chat.query.filter_by(
        patient_id=user_id,
        doctor_id=doctor_id,
        end_time=None  # Only active sessions
    ).first()
    
    if not chat_session:
        chat_session = Chat(
            patient_id=user_id,
            doctor_id=doctor_id
        )
        db.session.add(chat_session)
        db.session.commit()
    
    # Get chat messages
    messages = ChatMessage.query.filter_by(chat_id=chat_session.id).order_by(ChatMessage.timestamp).all()
    
    if request.method == 'POST':
        message = request.form.get('message')
        
        if message:
            new_message = ChatMessage(
                chat_id=chat_session.id,
                sender_type='patient',
                message=message
            )
            db.session.add(new_message)
            db.session.commit()
            
            return redirect(url_for('patient.chat', doctor_id=doctor_id))
    
    return render_template(
        'patient/chat.html',
        doctor=doctor,
        chat_session=chat_session,
        messages=messages
    )

@patient_bp.route('/mental-health')
@patient_required
def mental_health():
    return render_template('patient/mental_health.html')

# API endpoints for mobile app
@patient_bp.route('/api/update-location', methods=['POST'])
@jwt_required()
def api_update_location():
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate user is a patient
    user = User.query.get(user_id)
    if not user or user.role != 'patient':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Create new location entry
        new_location = Location(
            user_id=user_id,
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        db.session.add(new_location)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Location updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@patient_bp.route('/api/emergency-alert', methods=['POST'])
@jwt_required()
def api_emergency_alert():
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate user is a patient
    user = User.query.get(user_id)
    if not user or user.role != 'patient':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Get current location
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Get emergency contacts
        emergency_contacts = EmergencyContact.query.filter_by(user_id=user_id).all()
        contact_details = [
            {
                'name': contact.name,
                'phone_number': contact.phone_number,
                'email': contact.email
            }
            for contact in emergency_contacts
        ]
        
        # Get nearby hospitals
        nearby_hospitals = get_nearby_hospitals(latitude, longitude)
        
        # In a real application, you would send SMS/email to emergency contacts
        # and notify nearby hospitals
        
        return jsonify({
            'success': True,
            'message': 'Emergency alert sent successfully',
            'contacts_notified': contact_details,
            'nearby_hospitals': nearby_hospitals
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@patient_bp.route('/api/medical-records', methods=['GET'])
@jwt_required()
def api_get_medical_records():
    user_id = get_jwt_identity()
    
    # Validate user is a patient
    user = User.query.get(user_id)
    if not user or user.role != 'patient':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        medical_records = MedicalRecord.query.filter_by(user_id=user_id).order_by(MedicalRecord.date.desc()).all()
        
        records = []
        for record in medical_records:
            # Decrypt sensitive data
            decrypted_data = decrypt_data(record.encrypted_data) if record.encrypted_data else None
            
            records.append({
                'id': record.id,
                'record_type': record.record_type,
                'title': record.title,
                'description': record.description,
                'hospital_name': record.hospital_name,
                'doctor_name': record.doctor_name,
                'date': record.date.strftime('%Y-%m-%d'),
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sensitive_data': decrypted_data
            })
        
        return jsonify({
            'success': True,
            'medical_records': records
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@patient_bp.route('/api/offline-map-data', methods=['GET'])
@jwt_required()
def api_get_offline_map_data():
    """
    API endpoint to get offline map data that can be cached on the client device.
    Includes hospital data, pre-calculated directions, and simplified routing.
    """
    user_id = get_jwt_identity()
    
    # Validate user is a patient
    user = User.query.get(user_id)
    if not user or user.role != 'patient':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Get location from request parameters or use default
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        radius = request.args.get('radius', default=5000, type=int)
        
        # If no location provided, get from session or default
        if not latitude or not longitude:
            loc = get_location()
            latitude = loc['latitude']
            longitude = loc['longitude']
        
        # Get offline map data
        offline_data = get_offline_map_data(latitude, longitude, radius)
        
        # Store the latest location in session
        session['location'] = {
            'latitude': latitude,
            'longitude': longitude
        }
        
        # Also create a location record in the database
        new_location = Location(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_location)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'offline_map_data': offline_data
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@patient_bp.route('/offline-map-data', methods=['GET'])
@patient_required
def get_offline_map_data_page():
    """
    Route to get offline map data and display it on a page.
    This is useful for downloading the map data manually.
    """
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # Get current location
    current_location = get_location()
    
    # Get offline map data
    offline_data = get_offline_map_data(
        current_location['latitude'], 
        current_location['longitude']
    )
    
    # Convert to JSON string
    offline_data_json = json.dumps(offline_data, indent=2)
    
    return render_template(
        'patient/offline_map_data.html',
        user=user,
        offline_data=offline_data,
        offline_data_json=offline_data_json
    )
