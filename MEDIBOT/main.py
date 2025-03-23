from app import app

# Import all routes to ensure they are registered
from routes import auth, patient, attender, hospital, insurance, mental_health, google_auth

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
