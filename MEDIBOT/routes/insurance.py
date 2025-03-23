from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import InsurancePolicy, UserInsurance, User, MedicalRecord
from app import db
from datetime import datetime, timedelta

insurance_bp = Blueprint('insurance', __name__)

@insurance_bp.route('/calculator')
def calculator():
    if 'user_id' not in session:
        flash('You must be logged in to access the insurance calculator', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get all available insurance policies
    policies = InsurancePolicy.query.all()
    
    return render_template(
        'insurance/calculator.html',
        policies=policies
    )

@insurance_bp.route('/calculate', methods=['POST'])
def calculate():
    if 'user_id' not in session:
        flash('You must be logged in to access the insurance calculator', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    policy_id = request.form.get('policy_id')
    age = request.form.get('age')
    has_preexisting_conditions = request.form.get('has_preexisting_conditions') == 'yes'
    family_history = request.form.get('family_history') == 'yes'
    coverage_amount = request.form.get('coverage_amount')
    
    # Get the selected policy
    policy = InsurancePolicy.query.get_or_404(policy_id)
    
    # Calculate premium based on inputs
    base_premium = policy.premium
    
    # Age factor
    age_factor = 1.0
    if int(age) > 60:
        age_factor = 1.5
    elif int(age) > 40:
        age_factor = 1.2
    
    # Health condition factors
    health_factor = 1.0
    if has_preexisting_conditions:
        health_factor += 0.3
    if family_history:
        health_factor += 0.2
    
    # Coverage amount factor
    coverage_factor = float(coverage_amount) / policy.coverage_amount
    
    # Calculate final premium
    calculated_premium = base_premium * age_factor * health_factor * coverage_factor
    
    # Calculate different payment options
    monthly_premium = calculated_premium / 12
    quarterly_premium = calculated_premium / 4
    annual_premium = calculated_premium
    
    return render_template(
        'insurance/calculation_result.html',
        policy=policy,
        age=age,
        has_preexisting_conditions=has_preexisting_conditions,
        family_history=family_history,
        coverage_amount=coverage_amount,
        monthly_premium=monthly_premium,
        quarterly_premium=quarterly_premium,
        annual_premium=annual_premium
    )

@insurance_bp.route('/policies')
def policies():
    if 'user_id' not in session:
        flash('You must be logged in to view insurance policies', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # Get user's insurance policies
    user_insurances = UserInsurance.query.filter_by(user_id=user_id).all()
    
    # Get all available insurance policies
    all_policies = InsurancePolicy.query.all()
    
    # Filter out policies that the user already has
    available_policies = [
        policy for policy in all_policies 
        if policy.id not in [ui.policy_id for ui in user_insurances]
    ]
    
    return render_template(
        'insurance/policies.html',
        user=user,
        user_insurances=user_insurances,
        available_policies=available_policies
    )

@insurance_bp.route('/apply/<int:policy_id>', methods=['GET', 'POST'])
def apply(policy_id):
    if 'user_id' not in session:
        flash('You must be logged in to apply for insurance', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    policy = InsurancePolicy.query.get_or_404(policy_id)
    
    if request.method == 'POST':
        policy_number = f"POL-{user_id}-{policy_id}-{datetime.now().strftime('%Y%m%d')}"
        start_date_str = request.form.get('start_date')
        payment_frequency = request.form.get('payment_frequency')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            # Calculate end date based on policy duration
            end_date = start_date + timedelta(days=30 * policy.duration_months)
            
            # Determine premium amount based on payment frequency
            if payment_frequency == 'monthly':
                premium_amount = policy.premium / 12
            elif payment_frequency == 'quarterly':
                premium_amount = policy.premium / 4
            else:  # annually
                premium_amount = policy.premium
            
            # Create new user insurance
            new_insurance = UserInsurance(
                user_id=user_id,
                policy_id=policy_id,
                policy_number=policy_number,
                start_date=start_date,
                end_date=end_date,
                premium_amount=premium_amount,
                payment_frequency=payment_frequency,
                status='active'
            )
            
            db.session.add(new_insurance)
            db.session.commit()
            
            flash('Insurance policy application successful', 'success')
            return redirect(url_for('insurance.policies'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error applying for insurance: {str(e)}', 'danger')
    
    return render_template(
        'insurance/apply.html',
        user=user,
        policy=policy
    )

@insurance_bp.route('/view/<int:insurance_id>')
def view(insurance_id):
    if 'user_id' not in session:
        flash('You must be logged in to view insurance details', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    user_insurance = UserInsurance.query.get_or_404(insurance_id)
    
    # Ensure user owns this insurance policy
    if user_insurance.user_id != user_id:
        flash('You do not have permission to view this insurance policy', 'danger')
        return redirect(url_for('insurance.policies'))
    
    policy = InsurancePolicy.query.get(user_insurance.policy_id)
    
    # Calculate next payment date
    today = datetime.now().date()
    if user_insurance.payment_frequency == 'monthly':
        next_payment = today.replace(day=user_insurance.start_date.day)
        if next_payment < today:
            next_payment = next_payment.replace(month=next_payment.month+1 if next_payment.month < 12 else 1)
            if next_payment.month == 1:
                next_payment = next_payment.replace(year=next_payment.year+1)
    elif user_insurance.payment_frequency == 'quarterly':
        months_to_add = (((today.month - user_insurance.start_date.month) // 3) + 1) * 3
        next_payment = user_insurance.start_date.replace(month=((user_insurance.start_date.month - 1 + months_to_add) % 12) + 1)
        if next_payment.month < user_insurance.start_date.month:
            next_payment = next_payment.replace(year=next_payment.year+1)
    else:  # annually
        next_payment = user_insurance.start_date.replace(year=today.year)
        if next_payment < today:
            next_payment = next_payment.replace(year=next_payment.year+1)
    
    return render_template(
        'insurance/view.html',
        user_insurance=user_insurance,
        policy=policy,
        next_payment=next_payment
    )

# API endpoints for mobile app
@insurance_bp.route('/api/policies', methods=['GET'])
@jwt_required()
def api_get_policies():
    try:
        policies = InsurancePolicy.query.all()
        
        policies_list = []
        for policy in policies:
            policies_list.append({
                'id': policy.id,
                'name': policy.name,
                'provider': policy.provider,
                'description': policy.description,
                'coverage_amount': policy.coverage_amount,
                'premium': policy.premium,
                'duration_months': policy.duration_months,
                'benefits': policy.benefits
            })
        
        return jsonify({
            'success': True,
            'policies': policies_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@insurance_bp.route('/api/user-insurances', methods=['GET'])
@jwt_required()
def api_get_user_insurances():
    user_id = get_jwt_identity()
    
    try:
        user_insurances = UserInsurance.query.filter_by(user_id=user_id).all()
        
        insurances_list = []
        for insurance in user_insurances:
            policy = InsurancePolicy.query.get(insurance.policy_id)
            
            # Calculate next payment date
            today = datetime.now().date()
            if insurance.payment_frequency == 'monthly':
                next_payment = today.replace(day=insurance.start_date.day)
                if next_payment < today:
                    next_payment = next_payment.replace(month=next_payment.month+1 if next_payment.month < 12 else 1)
                    if next_payment.month == 1:
                        next_payment = next_payment.replace(year=next_payment.year+1)
            elif insurance.payment_frequency == 'quarterly':
                months_to_add = (((today.month - insurance.start_date.month) // 3) + 1) * 3
                next_payment = insurance.start_date.replace(month=((insurance.start_date.month - 1 + months_to_add) % 12) + 1)
                if next_payment.month < insurance.start_date.month:
                    next_payment = next_payment.replace(year=next_payment.year+1)
            else:  # annually
                next_payment = insurance.start_date.replace(year=today.year)
                if next_payment < today:
                    next_payment = next_payment.replace(year=next_payment.year+1)
            
            insurances_list.append({
                'id': insurance.id,
                'policy_number': insurance.policy_number,
                'policy_name': policy.name,
                'provider': policy.provider,
                'start_date': insurance.start_date.strftime('%Y-%m-%d'),
                'end_date': insurance.end_date.strftime('%Y-%m-%d'),
                'premium_amount': insurance.premium_amount,
                'payment_frequency': insurance.payment_frequency,
                'status': insurance.status,
                'next_payment_date': next_payment.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'insurances': insurances_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@insurance_bp.route('/api/recommend-policies', methods=['GET'])
@jwt_required()
def api_recommend_policies():
    user_id = get_jwt_identity()
    
    try:
        # Get user's existing insurance policies
        user_insurances = UserInsurance.query.filter_by(user_id=user_id).all()
        existing_policy_ids = [ui.policy_id for ui in user_insurances]
        
        # Get user's medical records
        medical_records = MedicalRecord.query.filter_by(user_id=user_id).all()
        
        # Simple recommendation logic based on medical records
        has_heart_condition = any('heart' in record.description.lower() for record in medical_records if record.description)
        has_diabetes = any('diabetes' in record.description.lower() for record in medical_records if record.description)
        has_cancer_history = any('cancer' in record.description.lower() for record in medical_records if record.description)
        
        # Query policies that might be relevant
        recommended_policies = []
        
        if has_heart_condition:
            heart_policies = InsurancePolicy.query.filter(
                InsurancePolicy.description.like('%heart%'),
                ~InsurancePolicy.id.in_(existing_policy_ids)
            ).limit(2).all()
            recommended_policies.extend(heart_policies)
        
        if has_diabetes:
            diabetes_policies = InsurancePolicy.query.filter(
                InsurancePolicy.description.like('%diabetes%'),
                ~InsurancePolicy.id.in_(existing_policy_ids)
            ).limit(2).all()
            recommended_policies.extend(diabetes_policies)
        
        if has_cancer_history:
            cancer_policies = InsurancePolicy.query.filter(
                InsurancePolicy.description.like('%cancer%'),
                ~InsurancePolicy.id.in_(existing_policy_ids)
            ).limit(2).all()
            recommended_policies.extend(cancer_policies)
        
        # If no specific policies found or no conditions matched, recommend general policies
        if not recommended_policies:
            general_policies = InsurancePolicy.query.filter(
                ~InsurancePolicy.id.in_(existing_policy_ids)
            ).limit(3).all()
            recommended_policies.extend(general_policies)
        
        # Format the response
        policies_list = []
        for policy in recommended_policies:
            policies_list.append({
                'id': policy.id,
                'name': policy.name,
                'provider': policy.provider,
                'description': policy.description,
                'coverage_amount': policy.coverage_amount,
                'premium': policy.premium,
                'duration_months': policy.duration_months,
                'benefits': policy.benefits
            })
        
        return jsonify({
            'success': True,
            'recommended_policies': policies_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
