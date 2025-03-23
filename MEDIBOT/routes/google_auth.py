import json
import os

import requests
from app import db
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "")}/google_login/callback'

# Display setup instructions to the user
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# Check if Google OAuth credentials are available
GOOGLE_OAUTH_CONFIGURED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

# Initialize OAuth client if credentials are available
if GOOGLE_OAUTH_CONFIGURED:
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
else:
    client = None
    print("WARNING: Google OAuth is not configured. Sign-in with Google will not work.")

# Create blueprint
google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    """Handle Google login request"""
    # Check if Google OAuth is properly configured
    if not GOOGLE_OAUTH_CONFIGURED:
        return "Google OAuth is not configured. Please set up GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables.", 500
    
    try:
        # Find out what URL to hit for Google login
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login
        # and provide URL user will be redirected to after successful login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # Replacing http:// with https:// is important as the external
            # protocol must be https to match the URI whitelisted
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        return f"An error occurred during Google login: {str(e)}", 500


@google_auth.route("/google_login/callback")
def callback():
    """Handle Google auth callback"""
    # Check if Google OAuth is properly configured
    if not GOOGLE_OAUTH_CONFIGURED:
        return "Google OAuth is not configured. Please set up GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables.", 500
    
    try:
        # Get authorization code Google sent back
        code = request.args.get("code")
        
        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare and send a request to get tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # Replacing http:// with https:// is important as the external
            # protocol must be https to match the URI whitelisted
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Make sure email is verified with Google
        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo["given_name"]
        else:
            return "User email not available or not verified by Google.", 400
        
        # Check if user exists in our database
        user = User.query.filter_by(email=users_email).first()
        
        # If user doesn't exist, create a new one
        if not user:
            # Create basic user profile with default values
            # Note: In a production app, you'd want to collect additional info
            user = User(
                username=users_name,
                email=users_email,
                password_hash="google-oauth-no-password",
                full_name=users_name,
                age=30,  # Default age
                address="Please update your address",
                role="patient"  # Default role
            )
            
            db.session.add(user)
            db.session.commit()
        
        # Log in the user
        login_user(user)
        
        # Redirect to homepage
        return redirect(url_for("index"))
    except Exception as e:
        return f"An error occurred during Google authentication: {str(e)}", 500


@google_auth.route("/oauth_logout")
@login_required
def logout():
    """Handle OAuth logout"""
    logout_user()
    return redirect(url_for("index"))