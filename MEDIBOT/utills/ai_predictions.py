from models import User, PatientInfo, MedicalRecord
import random

def get_risk_prediction(patient_id):
    """
    Generate AI-based risk predictions for a patient based on their medical records.
    In a production environment, this would use a trained ML model.
    
    Args:
        patient_id (int): ID of the patient
        
    Returns:
        dict: Dictionary containing risk predictions
    """
    # Get patient information
    patient = User.query.get(patient_id)
    patient_info = PatientInfo.query.filter_by(user_id=patient_id).first()
    medical_records = MedicalRecord.query.filter_by(user_id=patient_id).all()
    
    if not patient or not patient_info:
        return {
            'overall_risk': 'Unknown',
            'heart_disease_risk': 'Unknown',
            'diabetes_risk': 'Unknown',
            'cancer_risk': 'Unknown',
            'recommendations': [
                'Insufficient data to generate risk predictions',
                'Please complete your medical profile'
            ]
        }
    
    # In a real AI system, these would be calculated using trained models
    # For now, we'll use a simple rule-based approach for demonstration
    
    # Initialize risk levels
    heart_risk = 'Low'
    diabetes_risk = 'Low'
    cancer_risk = 'Low'
    overall_risk = 'Low'
    
    # Check for age risk factor
    age = patient.age
    if age > 60:
        heart_risk = 'Medium'
        cancer_risk = 'Medium'
    
    # Check for chronic diseases
    chronic_diseases = patient_info.chronic_diseases or ''
    if 'heart' in chronic_diseases.lower() or 'cardiac' in chronic_diseases.lower():
        heart_risk = 'High'
    if 'diabetes' in chronic_diseases.lower():
        diabetes_risk = 'High'
    if 'cancer' in chronic_diseases.lower():
        cancer_risk = 'High'
    
    # Check medical records for risk indicators
    for record in medical_records:
        description = (record.description or '').lower()
        
        # Heart disease indicators
        if any(keyword in description for keyword in ['cholesterol', 'hypertension', 'blood pressure']):
            heart_risk = 'Medium' if heart_risk == 'Low' else 'High'
        
        # Diabetes indicators
        if any(keyword in description for keyword in ['glucose', 'sugar', 'insulin']):
            diabetes_risk = 'Medium' if diabetes_risk == 'Low' else 'High'
        
        # Cancer indicators
        if any(keyword in description for keyword in ['tumor', 'malignant', 'cancer']):
            cancer_risk = 'Medium' if cancer_risk == 'Low' else 'High'
    
    # Calculate overall risk
    risk_values = {'Low': 1, 'Medium': 2, 'High': 3}
    overall_score = (risk_values[heart_risk] + risk_values[diabetes_risk] + risk_values[cancer_risk]) / 3
    
    if overall_score < 1.5:
        overall_risk = 'Low'
    elif overall_score < 2.5:
        overall_risk = 'Medium'
    else:
        overall_risk = 'High'
    
    # Generate recommendations
    recommendations = []
    
    if heart_risk == 'Medium' or heart_risk == 'High':
        recommendations.append('Consider regular cardiovascular check-ups')
        recommendations.append('Monitor blood pressure and cholesterol levels')
    
    if diabetes_risk == 'Medium' or diabetes_risk == 'High':
        recommendations.append('Regular blood glucose monitoring recommended')
        recommendations.append('Consider consulting with an endocrinologist')
    
    if cancer_risk == 'Medium' or cancer_risk == 'High':
        recommendations.append('Follow age-appropriate cancer screenings')
    
    if not recommendations:
        recommendations.append('Maintain a healthy lifestyle with regular exercise')
        recommendations.append('Schedule routine check-ups for preventive care')
    
    return {
        'overall_risk': overall_risk,
        'heart_disease_risk': heart_risk,
        'diabetes_risk': diabetes_risk,
        'cancer_risk': cancer_risk,
        'recommendations': recommendations
    }

def get_insurance_recommendations(patient_id):
    """
    Generate insurance recommendations based on patient medical data.
    In a production environment, this would use a sophisticated recommendation system.
    
    Args:
        patient_id (int): ID of the patient
        
    Returns:
        list: List of recommended insurance types
    """
    # Get risk prediction
    risk_prediction = get_risk_prediction(patient_id)
    
    recommendations = []
    
    # Recommend based on risk levels
    if risk_prediction['heart_disease_risk'] == 'High':
        recommendations.append({
            'type': 'Cardiac Care Insurance',
            'coverage': 'Specialized coverage for heart conditions and treatments',
            'priority': 'High'
        })
    
    if risk_prediction['diabetes_risk'] == 'High':
        recommendations.append({
            'type': 'Diabetes Management Plan',
            'coverage': 'Coverage for diabetes medications, supplies, and specialist visits',
            'priority': 'High'
        })
    
    if risk_prediction['cancer_risk'] == 'High':
        recommendations.append({
            'type': 'Cancer Protection Plan',
            'coverage': 'Comprehensive coverage for cancer treatments and therapies',
            'priority': 'High'
        })
    
    # Always recommend some basic insurance options
    if len(recommendations) < 3:
        recommendations.append({
            'type': 'Comprehensive Health Insurance',
            'coverage': 'All-round coverage for most medical needs',
            'priority': 'Medium'
        })
    
    if len(recommendations) < 3:
        recommendations.append({
            'type': 'Hospital Cash Insurance',
            'coverage': 'Daily cash benefits during hospitalization',
            'priority': 'Medium'
        })
    
    if len(recommendations) < 3:
        recommendations.append({
            'type': 'Critical Illness Cover',
            'coverage': 'Lump sum payment upon diagnosis of critical illnesses',
            'priority': 'Medium'
        })
    
    return recommendations
