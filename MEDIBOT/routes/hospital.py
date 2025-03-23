from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Hospital, Doctor, HospitalReview, DoctorReview
from app import db

hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.route('/list')
def list_hospitals():
    hospitals = Hospital.query.all()
    return render_template(
        'hospital/list.html',
        hospitals=hospitals
    )

@hospital_bp.route('/view/<int:hospital_id>')
def view_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
    reviews = HospitalReview.query.filter_by(hospital_id=hospital_id).order_by(HospitalReview.created_at.desc()).all()
    
    return render_template(
        'hospital/view.html',
        hospital=hospital,
        doctors=doctors,
        reviews=reviews
    )

@hospital_bp.route('/review/<int:hospital_id>', methods=['POST'])
def review_hospital(hospital_id):
    if 'user_id' not in session:
        flash('You must be logged in to submit a review', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if not rating or not 1 <= int(rating) <= 5:
        flash('Please provide a valid rating (1-5)', 'danger')
        return redirect(url_for('hospital.view_hospital', hospital_id=hospital_id))
    
    try:
        # Check if user has already reviewed this hospital
        existing_review = HospitalReview.query.filter_by(
            hospital_id=hospital_id,
            user_id=user_id
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
        else:
            # Create new review
            new_review = HospitalReview(
                hospital_id=hospital_id,
                user_id=user_id,
                rating=rating,
                comment=comment
            )
            db.session.add(new_review)
        
        db.session.commit()
        
        # Update hospital's average rating
        update_hospital_rating(hospital_id)
        
        flash('Review submitted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting review: {str(e)}', 'danger')
    
    return redirect(url_for('hospital.view_hospital', hospital_id=hospital_id))

@hospital_bp.route('/doctor/<int:doctor_id>')
def view_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    hospital = Hospital.query.get(doctor.hospital_id)
    reviews = DoctorReview.query.filter_by(doctor_id=doctor_id).order_by(DoctorReview.created_at.desc()).all()
    
    return render_template(
        'hospital/doctor.html',
        doctor=doctor,
        hospital=hospital,
        reviews=reviews
    )

@hospital_bp.route('/doctor/review/<int:doctor_id>', methods=['POST'])
def review_doctor(doctor_id):
    if 'user_id' not in session:
        flash('You must be logged in to submit a review', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if not rating or not 1 <= int(rating) <= 5:
        flash('Please provide a valid rating (1-5)', 'danger')
        return redirect(url_for('hospital.view_doctor', doctor_id=doctor_id))
    
    try:
        # Check if user has already reviewed this doctor
        existing_review = DoctorReview.query.filter_by(
            doctor_id=doctor_id,
            user_id=user_id
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
        else:
            # Create new review
            new_review = DoctorReview(
                doctor_id=doctor_id,
                user_id=user_id,
                rating=rating,
                comment=comment
            )
            db.session.add(new_review)
        
        db.session.commit()
        
        # Update doctor's average rating
        update_doctor_rating(doctor_id)
        
        flash('Review submitted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting review: {str(e)}', 'danger')
    
    return redirect(url_for('hospital.view_doctor', doctor_id=doctor_id))

# Helper functions
def update_hospital_rating(hospital_id):
    reviews = HospitalReview.query.filter_by(hospital_id=hospital_id).all()
    
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        avg_rating = total_rating / len(reviews)
        
        hospital = Hospital.query.get(hospital_id)
        hospital.rating = round(avg_rating, 1)
        db.session.commit()

def update_doctor_rating(doctor_id):
    reviews = DoctorReview.query.filter_by(doctor_id=doctor_id).all()
    
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        avg_rating = total_rating / len(reviews)
        
        doctor = Doctor.query.get(doctor_id)
        doctor.rating = round(avg_rating, 1)
        db.session.commit()

# API endpoints for mobile app
@hospital_bp.route('/api/hospitals', methods=['GET'])
def api_get_hospitals():
    try:
        hospitals = Hospital.query.all()
        
        hospitals_list = []
        for hospital in hospitals:
            hospitals_list.append({
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'latitude': hospital.latitude,
                'longitude': hospital.longitude,
                'phone_number': hospital.phone_number,
                'emergency_number': hospital.emergency_number,
                'website': hospital.website,
                'rating': hospital.rating
            })
        
        return jsonify({
            'success': True,
            'hospitals': hospitals_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@hospital_bp.route('/api/hospital/<int:hospital_id>/doctors', methods=['GET'])
def api_get_hospital_doctors(hospital_id):
    try:
        doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
        
        doctors_list = []
        for doctor in doctors:
            doctors_list.append({
                'id': doctor.id,
                'name': doctor.name,
                'specialization': doctor.specialization,
                'experience_years': doctor.experience_years,
                'availability': doctor.availability,
                'rating': doctor.rating
            })
        
        return jsonify({
            'success': True,
            'doctors': doctors_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@hospital_bp.route('/api/hospital/<int:hospital_id>/reviews', methods=['GET'])
def api_get_hospital_reviews(hospital_id):
    try:
        reviews = HospitalReview.query.filter_by(hospital_id=hospital_id).order_by(HospitalReview.created_at.desc()).all()
        
        reviews_list = []
        for review in reviews:
            user = review.user
            reviews_list.append({
                'id': review.id,
                'user_name': user.full_name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'reviews': reviews_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@hospital_bp.route('/api/doctor/<int:doctor_id>/reviews', methods=['GET'])
def api_get_doctor_reviews(doctor_id):
    try:
        reviews = DoctorReview.query.filter_by(doctor_id=doctor_id).order_by(DoctorReview.created_at.desc()).all()
        
        reviews_list = []
        for review in reviews:
            user = review.user
            reviews_list.append({
                'id': review.id,
                'user_name': user.full_name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'reviews': reviews_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
