from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os
import json
from models import User, MentalHealthSession, MentalHealthMessage
from app import db
from datetime import datetime

mental_health_bp = Blueprint('mental_health', __name__)

@mental_health_bp.route('/chat')
def chat():
    if 'user_id' not in session:
        flash('You must be logged in to access the mental health chatbot', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    
    # Get or create an active session
    active_session = MentalHealthSession.query.filter_by(
        user_id=user_id,
        end_time=None
    ).first()
    
    if not active_session:
        active_session = MentalHealthSession(user_id=user_id)
        db.session.add(active_session)
        db.session.commit()
    
    # Get previous messages for this session
    messages = MentalHealthMessage.query.filter_by(
        session_id=active_session.id
    ).order_by(MentalHealthMessage.timestamp).all()
    
    return render_template(
        'mental_health/chat.html',
        session=active_session,
        messages=messages
    )

@mental_health_bp.route('/send-message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        flash('You must be logged in to use the mental health chatbot', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    message_text = request.form.get('message')
    session_id = request.form.get('session_id')
    
    if not message_text:
        flash('Please enter a message', 'danger')
        return redirect(url_for('mental_health.chat'))
    
    try:
        # Save user message
        user_message = MentalHealthMessage(
            session_id=session_id,
            is_from_user=True,
            message=message_text
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get AI response
        ai_response = get_ai_response(user_id, message_text)
        
        # Save AI response
        bot_message = MentalHealthMessage(
            session_id=session_id,
            is_from_user=False,
            message=ai_response
        )
        db.session.add(bot_message)
        db.session.commit()
        
        return redirect(url_for('mental_health.chat'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {str(e)}', 'danger')
        return redirect(url_for('mental_health.chat'))

@mental_health_bp.route('/end-session', methods=['POST'])
def end_session():
    if 'user_id' not in session:
        flash('You must be logged in to end a session', 'danger')
        return redirect(url_for('auth.login'))
    
    session_id = request.form.get('session_id')
    
    try:
        # End the session
        mental_health_session = MentalHealthSession.query.get_or_404(session_id)
        mental_health_session.end_time = datetime.utcnow()
        
        # Generate a summary of the session
        messages = MentalHealthMessage.query.filter_by(
            session_id=session_id
        ).order_by(MentalHealthMessage.timestamp).all()
        
        conversation = "\n".join([
            f"{'User' if msg.is_from_user else 'AI'}: {msg.message}"
            for msg in messages
        ])
        
        summary = generate_session_summary(conversation)
        mental_health_session.summary = summary
        
        db.session.commit()
        
        flash('Mental health session ended successfully', 'success')
        return redirect(url_for('mental_health.history'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error ending session: {str(e)}', 'danger')
        return redirect(url_for('mental_health.chat'))

@mental_health_bp.route('/history')
def history():
    if 'user_id' not in session:
        flash('You must be logged in to view your session history', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    
    # Get completed sessions
    completed_sessions = MentalHealthSession.query.filter(
        MentalHealthSession.user_id == user_id,
        MentalHealthSession.end_time != None
    ).order_by(MentalHealthSession.start_time.desc()).all()
    
    return render_template(
        'mental_health/history.html',
        sessions=completed_sessions
    )

@mental_health_bp.route('/view-session/<int:session_id>')
def view_session(session_id):
    if 'user_id' not in session:
        flash('You must be logged in to view session details', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    
    # Get the session
    mental_health_session = MentalHealthSession.query.get_or_404(session_id)
    
    # Ensure user owns this session
    if mental_health_session.user_id != user_id:
        flash('You do not have permission to view this session', 'danger')
        return redirect(url_for('mental_health.history'))
    
    # Get session messages
    messages = MentalHealthMessage.query.filter_by(
        session_id=session_id
    ).order_by(MentalHealthMessage.timestamp).all()
    
    return render_template(
        'mental_health/view_session.html',
        session=mental_health_session,
        messages=messages
    )

@mental_health_bp.route('/meditation')
def meditation():
    # Simple meditation resources
    meditation_resources = [
        {
            'title': 'Deep Breathing Exercise',
            'description': 'A simple breathing exercise to help reduce stress and anxiety.',
            'steps': [
                'Find a comfortable position, sitting or lying down.',
                'Place one hand on your chest and the other on your stomach.',
                'Breathe in slowly through your nose, feeling your stomach expand.',
                'Exhale slowly through your mouth, feeling your stomach contract.',
                'Repeat for 5-10 minutes, focusing on your breath.'
            ]
        },
        {
            'title': 'Body Scan Meditation',
            'description': 'A meditation technique to help you become aware of sensations in your body.',
            'steps': [
                'Lie down in a comfortable position.',
                'Close your eyes and take a few deep breaths.',
                'Starting from your toes, focus your attention on each part of your body.',
                'Notice any sensations without judgment.',
                'Gradually move up through your body, ending at the top of your head.',
                'If your mind wanders, gently bring it back to the body part you were focusing on.'
            ]
        },
        {
            'title': 'Mindful Observation',
            'description': 'A simple mindfulness exercise to help you stay present.',
            'steps': [
                'Choose a natural object within your immediate environment.',
                'Focus on watching it for a minute or two.',
                'Don\'t do anything except notice the thing you are looking at.',
                'Relax and observe its features and characteristics.',
                'Observe the object as if you\'re seeing it for the first time.'
            ]
        }
    ]
    
    # Distress helplines
    helplines = [
        {
            'name': 'National Suicide Prevention Lifeline',
            'phone': '1-800-273-8255',
            'website': 'https://suicidepreventionlifeline.org/'
        },
        {
            'name': 'Crisis Text Line',
            'phone': 'Text HOME to 741741',
            'website': 'https://www.crisistextline.org/'
        },
        {
            'name': 'SAMHSA\'s National Helpline',
            'phone': '1-800-662-4357',
            'website': 'https://www.samhsa.gov/find-help/national-helpline'
        }
    ]
    
    return render_template(
        'mental_health/meditation.html',
        meditation_resources=meditation_resources,
        helplines=helplines
    )

# Helper functions
def get_ai_response(user_id, message):
    # In a production environment, this would use the OpenAI API
    # For now, we'll provide simple responses based on keywords
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['sad', 'depress', 'unhappy', 'miserable']):
        return "I'm sorry you're feeling this way. Depression is a common but serious mood disorder. Would you like to talk more about what's making you feel sad? Remember that seeking help from a professional is important if these feelings persist."
    
    if any(word in message_lower for word in ['anxious', 'anxiety', 'worry', 'stress', 'panic']):
        return "It sounds like you might be experiencing anxiety. Try taking a few deep breaths. Inhale for 4 counts, hold for a moment, and exhale for 6 counts. This can help regulate your nervous system. Would you like to discuss some other anxiety management techniques?"
    
    if any(word in message_lower for word in ['sleep', 'insomnia', 'tired', 'fatigue']):
        return "Sleep issues can significantly impact your mental health. Consider establishing a regular sleep schedule, avoiding screens before bedtime, and creating a calming bedtime routine. Have you tried any of these approaches?"
    
    if any(word in message_lower for word in ['help', 'emergency', 'crisis', 'suicide', 'kill']):
        return "If you're in crisis or having thoughts of self-harm, please reach out to a crisis helpline immediately: National Suicide Prevention Lifeline at 1-800-273-8255 or text HOME to 741741 for the Crisis Text Line. Would you like me to provide more resources?"
    
    if any(word in message_lower for word in ['meditate', 'meditation', 'mindful', 'calm']):
        return "Meditation and mindfulness practices can be very helpful for mental well-being. Have you tried the meditation exercises in the Meditation tab? Even a few minutes of mindful breathing each day can make a difference."
    
    # Default response for messages that don't match specific patterns
    return "Thank you for sharing. I'm here to listen and support you. Would you like to tell me more about what's on your mind, or would you prefer some coping strategies or resources?"

def generate_session_summary(conversation):
    # In a production environment, this would use the OpenAI API
    # For now, we'll provide a simple summary
    
    # Count messages
    lines = conversation.split('\n')
    user_messages = sum(1 for line in lines if line.startswith('User:'))
    ai_messages = sum(1 for line in lines if line.startswith('AI:'))
    
    # Simple keyword detection
    keywords = {
        'depression': conversation.lower().count('depress'),
        'anxiety': conversation.lower().count('anxious') + conversation.lower().count('anxiety'),
        'stress': conversation.lower().count('stress'),
        'sleep': conversation.lower().count('sleep') + conversation.lower().count('insomnia'),
        'meditation': conversation.lower().count('meditate') + conversation.lower().count('meditation')
    }
    
    # Find the most mentioned topic
    main_topic = max(keywords.items(), key=lambda x: x[1])[0] if any(keywords.values()) else 'general mental health'
    
    return f"Session summary: Conversation primarily focused on {main_topic}. {user_messages} messages from user, {ai_messages} responses from AI."

# API endpoints for mobile app
@mental_health_bp.route('/api/chat-sessions', methods=['GET'])
@jwt_required()
def api_get_chat_sessions():
    user_id = get_jwt_identity()
    
    try:
        # Get all sessions for this user
        sessions = MentalHealthSession.query.filter_by(user_id=user_id).order_by(MentalHealthSession.start_time.desc()).all()
        
        sessions_list = []
        for session in sessions:
            sessions_list.append({
                'id': session.id,
                'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else None,
                'summary': session.summary,
                'is_active': session.end_time is None
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@mental_health_bp.route('/api/chat-messages/<int:session_id>', methods=['GET'])
@jwt_required()
def api_get_chat_messages(session_id):
    user_id = get_jwt_identity()
    
    try:
        # Ensure session belongs to this user
        session = MentalHealthSession.query.get_or_404(session_id)
        if session.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get messages for this session
        messages = MentalHealthMessage.query.filter_by(session_id=session_id).order_by(MentalHealthMessage.timestamp).all()
        
        messages_list = []
        for message in messages:
            messages_list.append({
                'id': message.id,
                'is_from_user': message.is_from_user,
                'message': message.message,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': messages_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@mental_health_bp.route('/api/send-message', methods=['POST'])
@jwt_required()
def api_send_message():
    user_id = get_jwt_identity()
    data = request.json
    
    try:
        session_id = data.get('session_id')
        message_text = data.get('message')
        
        if not message_text:
            return jsonify({'success': False, 'message': 'Message text is required'}), 400
        
        # If no session_id provided, get or create an active session
        if not session_id:
            active_session = MentalHealthSession.query.filter_by(
                user_id=user_id,
                end_time=None
            ).first()
            
            if not active_session:
                active_session = MentalHealthSession(user_id=user_id)
                db.session.add(active_session)
                db.session.commit()
            
            session_id = active_session.id
        else:
            # Ensure session belongs to this user
            session = MentalHealthSession.query.get_or_404(session_id)
            if session.user_id != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Save user message
        user_message = MentalHealthMessage(
            session_id=session_id,
            is_from_user=True,
            message=message_text
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get AI response
        ai_response = get_ai_response(user_id, message_text)
        
        # Save AI response
        bot_message = MentalHealthMessage(
            session_id=session_id,
            is_from_user=False,
            message=ai_response
        )
        db.session.add(bot_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'user_message': {
                'id': user_message.id,
                'message': user_message.message,
                'timestamp': user_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            },
            'bot_message': {
                'id': bot_message.id,
                'message': bot_message.message,
                'timestamp': bot_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
