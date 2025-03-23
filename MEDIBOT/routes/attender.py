from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from models import (
    User, PatientInfo, EmergencyContact, Location, MedicalRecord,
    AttenderPatientAssociation, InsurancePolicy, UserInsurance
)
from app import db
from utils.encryption import encrypt_data, decrypt_data
from utils.ai_predictions import get_risk_prediction
from datetime import datetime

attender_bp = Blueprint('attender', __name__)

# Check if user is logged in and is an attender
from functools import wraps

def attender_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'attender':
            flash('You must be logged in as an attender to access this page', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@attender_bp.route('/dashboard')
@attender_required
def dashboard():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # Get patients associated with this attender
    associations = AttenderPatientAssociation.query.filter_by(attender_id=user_id).all()
    patients = []
    
    for assoc in associations:
        patient = User.query.get(assoc.patient_id)
        if patient:
            patient_info = PatientInfo.query.filter_by(user_id=patient.id).first()
            patients.append({
                'user': patient,
                'info': patient_info,
                'association': assoc
            })
    
    return render_template(
        'attender/dashboard.html',
        user=user,
        patients=patients
    )

@attender_bp.route('/location/<int:patient_id>')
@attender_required
def location(patient_id):
    user_id = session.get('user_id')
    
    # Check if attender has permission to access this patient's location
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_location=True
    ).first()
    
    if not association:
        flash('You do not have permission to access this patient\'s location', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    patient = User.query.get_or_404(patient_id)
    
    # Get patient's last known location
    last_location = Location.query.filter_by(
        user_id=patient_id
    ).order_by(Location.timestamp.desc()).first()
    
    return render_template(
        'attender/location.html',
        patient=patient,
        location=last_location
    )

@attender_bp.route('/medical-records/<int:patient_id>')
@attender_required
def medical_records(patient_id):
    user_id = session.get('user_id')
    
    # Check if attender has permission to access this patient's medical records
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_medical_records=True
    ).first()
    
    if not association:
        flash('You do not have permission to access this patient\'s medical records', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    patient = User.query.get_or_404(patient_id)
    patient_info = PatientInfo.query.filter_by(user_id=patient_id).first()
    
    # Get all medical records for this patient
    medical_records = MedicalRecord.query.filter_by(
        user_id=patient_id
    ).order_by(MedicalRecord.date.desc()).all()
    
    # Get risk prediction
    risk_prediction = get_risk_prediction(patient_id)
    
    return render_template(
        'attender/medical_records.html',
        patient=patient,
        patient_info=patient_info,
        medical_records=medical_records,
        risk_prediction=risk_prediction
    )

@attender_bp.route('/medical-records/<int:patient_id>/add', methods=['GET', 'POST'])
@attender_required
def add_medical_record(patient_id):
    user_id = session.get('user_id')
    
    # Check if attender has permission to access this patient's medical records
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_medical_records=True
    ).first()
    
    if not association:
        flash('You do not have permission to manage this patient\'s medical records', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    patient = User.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        record_type = request.form.get('record_type')
        title = request.form.get('title')
        description = request.form.get('description')
        hospital_name = request.form.get('hospital_name')
        doctor_name = request.form.get('doctor_name')
        date_str = request.form.get('date')
        sensitive_data = request.form.get('sensitive_data')
        
        try:
            # Parse date
            record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Encrypt sensitive data
            encrypted_data = encrypt_data(sensitive_data) if sensitive_data else None
            
            # Create new medical record
            new_record = MedicalRecord(
                user_id=patient_id,
                record_type=record_type,
                title=title,
                description=description,
                hospital_name=hospital_name,
                doctor_name=doctor_name,
                date=record_date,
                encrypted_data=encrypted_data
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash('Medical record added successfully', 'success')
            return redirect(url_for('attender.medical_records', patient_id=patient_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding medical record: {str(e)}', 'danger')
    
    return render_template(
        'attender/add_medical_record.html',
        patient=patient
    )

@attender_bp.route('/medical-records/<int:patient_id>/edit/<int:record_id>', methods=['GET', 'POST'])
@attender_required
def edit_medical_record(patient_id, record_id):
    user_id = session.get('user_id')
    
    # Check if attender has permission to access this patient's medical records
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_medical_records=True
    ).first()
    
    if not association:
        flash('You do not have permission to manage this patient\'s medical records', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    patient = User.query.get_or_404(patient_id)
    record = MedicalRecord.query.get_or_404(record_id)
    
    # Ensure record belongs to this patient
    if record.user_id != patient_id:
        flash('Record not found for this patient', 'danger')
        return redirect(url_for('attender.medical_records', patient_id=patient_id))
    
    if request.method == 'POST':
        record.record_type = request.form.get('record_type')
        record.title = request.form.get('title')
        record.description = request.form.get('description')
        record.hospital_name = request.form.get('hospital_name')
        record.doctor_name = request.form.get('doctor_name')
        date_str = request.form.get('date')
        sensitive_data = request.form.get('sensitive_data')
        
        try:
            # Parse date
            record.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Encrypt sensitive data if provided
            if sensitive_data:
                record.encrypted_data = encrypt_data(sensitive_data)
            
            db.session.commit()
            
            flash('Medical record updated successfully', 'success')
            return redirect(url_for('attender.medical_records', patient_id=patient_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating medical record: {str(e)}', 'danger')
    
    # Decrypt sensitive data for display
    sensitive_data = decrypt_data(record.encrypted_data) if record.encrypted_data else None
    
    return render_template(
        'attender/edit_medical_record.html',
        patient=patient,
        record=record,
        sensitive_data=sensitive_data
    )

@attender_bp.route('/medical-records/<int:patient_id>/delete/<int:record_id>', methods=['POST'])
@attender_required
def delete_medical_record(patient_id, record_id):
    user_id = session.get('user_id')
    
    # Check if attender has permission to access this patient's medical records
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_medical_records=True
    ).first()
    
    if not association:
        flash('You do not have permission to manage this patient\'s medical records', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    record = MedicalRecord.query.get_or_404(record_id)
    
    # Ensure record belongs to this patient
    if record.user_id != patient_id:
        flash('Record not found for this patient', 'danger')
        return redirect(url_for('attender.medical_records', patient_id=patient_id))
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Medical record deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medical record: {str(e)}', 'danger')
    
    return redirect(url_for('attender.medical_records', patient_id=patient_id))

@attender_bp.route('/insurance/<int:patient_id>')
@attender_required
def insurance(patient_id):
    user_id = session.get('user_id')
    
    # Check if attender is associated with this patient
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id
    ).first()
    
    if not association:
        flash('You are not authorized to view this patient\'s insurance information', 'danger')
        return redirect(url_for('attender.dashboard'))
    
    patient = User.query.get_or_404(patient_id)
    
    # Get patient's insurance policies
    user_insurances = UserInsurance.query.filter_by(user_id=patient_id).all()
    
    # Get all available insurance policies
    all_policies = InsurancePolicy.query.all()
    
    # Get recommended policies based on patient medical records
    recommended_policies = []
    for policy in all_policies:
        if len(recommended_policies) < 3 and policy not in [ui.policy for ui in user_insurances]:
            recommended_policies.append(policy)
    
    return render_template(
        'attender/insurance.html',
        patient=patient,
        user_insurances=user_insurances,
        all_policies=all_policies,
        recommended_policies=recommended_policies
    )

# API endpoints for mobile app
@attender_bp.route('/api/patients', methods=['GET'])
@jwt_required()
def api_get_patients():
    user_id = get_jwt_identity()
    
    # Validate user is an attender
    user = User.query.get(user_id)
    if not user or user.role != 'attender':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Get patients associated with this attender
        associations = AttenderPatientAssociation.query.filter_by(attender_id=user_id).all()
        patients = []
        
        for assoc in associations:
            patient = User.query.get(assoc.patient_id)
            if patient:
                patient_info = PatientInfo.query.filter_by(user_id=patient.id).first()
                patients.append({
                    'id': patient.id,
                    'username': patient.username,
                    'full_name': patient.full_name,
                    'age': patient.age,
                    'address': patient.address,
                    'can_access_location': assoc.can_access_location,
                    'can_access_medical_records': assoc.can_access_medical_records,
                    'blood_group': patient_info.blood_group if patient_info else None,
                    'chronic_diseases': patient_info.chronic_diseases if patient_info else None
                })
        
        return jsonify({
            'success': True,
            'patients': patients
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@attender_bp.route('/api/patient-location/<int:patient_id>', methods=['GET'])
@jwt_required()
def api_patient_location(patient_id):
    user_id = get_jwt_identity()
    
    # Validate user is an attender with permission
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_location=True
    ).first()
    
    if not association:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Get patient's last known location
        last_location = Location.query.filter_by(
            user_id=patient_id
        ).order_by(Location.timestamp.desc()).first()
        
        if not last_location:
            return jsonify({'success': False, 'message': 'No location data available'}), 404
        
        return jsonify({
            'success': True,
            'location': {
                'latitude': last_location.latitude,
                'longitude': last_location.longitude,
                'timestamp': last_location.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@attender_bp.route('/api/medical-records/<int:patient_id>', methods=['GET'])
@jwt_required()
def api_get_patient_medical_records(patient_id):
    user_id = get_jwt_identity()
    
    # Validate user is an attender with permission
    association = AttenderPatientAssociation.query.filter_by(
        attender_id=user_id,
        patient_id=patient_id,
        can_access_medical_records=True
    ).first()
    
    if not association:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        medical_records = MedicalRecord.query.filter_by(
            user_id=patient_id
        ).order_by(MedicalRecord.date.desc()).all()
        
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
        
        # Get risk prediction
        risk_prediction = get_risk_prediction(patient_id)
        
        return jsonify({
            'success': True,
            'medical_records': records,
            'risk_prediction': risk_prediction
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
