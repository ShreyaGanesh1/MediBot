from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
from models import User, PatientInfo, EmergencyContact
from app import db
from MEDIBOT.utils.encryption import encrypt_data, decrypt_data

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == data.get('username')) | 
            (User.email == data.get('email'))
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            age=data.get('age'),
            address=data.get('address'),
            role=data.get('role')  # 'patient' or 'attender'
        )
        new_user.set_password(data.get('password'))
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # If user is a patient, create patient info
            if data.get('role') == 'patient':
                patient_info = PatientInfo(
                    user_id=new_user.id,
                    blood_group=data.get('blood_group'),
                    known_allergies=data.get('known_allergies'),
                    chronic_diseases=data.get('chronic_diseases'),
                    current_medications=data.get('current_medications')
                )
                db.session.add(patient_info)
                
                # Add emergency contacts
                for i in range(1, 5):  # Minimum 4 emergency contacts required
                    contact_name = data.get(f'emergency_name_{i}')
                    if contact_name:
                        emergency_contact = EmergencyContact(
                            user_id=new_user.id,
                            name=contact_name,
                            relationship=data.get(f'emergency_relationship_{i}'),
                            phone_number=data.get(f'emergency_phone_{i}'),
                            email=data.get(f'emergency_email_{i}'),
                            is_primary=(i == 1)  # First contact is primary
                        )
                        db.session.add(emergency_contact)
                
                db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Create JWT token
            access_token = create_access_token(identity=user.id)
            
            # Store user info in session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Redirect based on role
            if user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
            else:
                return redirect(url_for('attender.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

# API endpoints for mobile app
@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == data.get('username')) | 
        (User.email == data.get('email'))
    ).first()
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    
    # Create new user
    new_user = User(
        username=data.get('username'),
        email=data.get('email'),
        full_name=data.get('full_name'),
        age=data.get('age'),
        address=data.get('address'),
        role=data.get('role')  # 'patient' or 'attender'
    )
    new_user.set_password(data.get('password'))
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # If user is a patient, create patient info
        if data.get('role') == 'patient':
            patient_info = PatientInfo(
                user_id=new_user.id,
                blood_group=data.get('blood_group'),
                known_allergies=data.get('known_allergies'),
                chronic_diseases=data.get('chronic_diseases'),
                current_medications=data.get('current_medications')
            )
            db.session.add(patient_info)
            
            # Add emergency contacts
            emergency_contacts = data.get('emergency_contacts', [])
            for i, contact in enumerate(emergency_contacts):
                emergency_contact = EmergencyContact(
                    user_id=new_user.id,
                    name=contact.get('name'),
                    relationship=contact.get('relationship'),
                    phone_number=contact.get('phone_number'),
                    email=contact.get('email'),
                    is_primary=(i == 0)  # First contact is primary
                )
                db.session.add(emergency_contact)
            
            db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'access_token': access_token,
            'user_id': new_user.id,
            'role': new_user.role
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
