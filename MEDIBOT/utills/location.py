import os
import requests
import json
from flask import session
from models import Hospital
from datetime import datetime

# Get Google Maps API key from environment variable
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

def get_location():
    """
    Get current location from session or use a default location.
    In a real application, this would be determined by GPS.
    
    Returns:
        dict: Dictionary containing latitude and longitude
    """
    # Check if location is stored in session
    if 'location' in session:
        return session['location']
    
    # Default location (example: New York City)
    default_location = {
        'latitude': 40.7128,
        'longitude': -74.0060
    }
    
    # Store in session for later use
    session['location'] = default_location
    
    return default_location

def get_nearby_hospitals(latitude, longitude, radius=5000):
    """
    Get nearby hospitals using Google Places API.
    
    Args:
        latitude (float): Current latitude
        longitude (float): Current longitude
        radius (int): Search radius in meters (default: 5000m / 5km)
        
    Returns:
        list: List of nearby hospitals
    """
    # In a production environment, this would use the Google Places API
    # For now, we'll query our database for hospitals
    
    # Get all hospitals from the database
    hospitals = Hospital.query.all()
    
    # Calculate simple distance to filter nearby hospitals
    # This is a simplified approach; in production, use proper geospatial queries
    nearby = []
    for hospital in hospitals:
        # Calculate rough distance using latitude/longitude (not accurate for large distances)
        lat_diff = abs(hospital.latitude - latitude)
        lon_diff = abs(hospital.longitude - longitude)
        
        # Simple approximation: 0.01 degrees is roughly 1km at the equator
        # This is very rough but works for demonstration purposes
        distance_approx = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 100
        
        if distance_approx <= (radius / 1000):  # Convert meters to km
            nearby.append({
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'latitude': hospital.latitude,
                'longitude': hospital.longitude,
                'phone_number': hospital.phone_number,
                'emergency_number': hospital.emergency_number,
                'distance': round(distance_approx, 1)  # Distance in km
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance'])
    
    return nearby

def get_offline_map_data(latitude, longitude, radius=5000):
    """
    Get map data for offline use, including hospitals and basic routing information.
    This data can be cached locally on the device.
    
    Args:
        latitude (float): Current latitude
        longitude (float): Current longitude
        radius (int): Search radius in meters
        
    Returns:
        dict: Dictionary containing map data for offline use
    """
    # Get nearby hospitals
    hospitals = get_nearby_hospitals(latitude, longitude, radius)
    
    # Get pre-calculated routes to each hospital for offline use
    # In a real app, this would include simplified routing instructions
    # For now, just include direct distances
    for hospital in hospitals:
        hospital['offline_route'] = {
            'distance_km': hospital['distance'],
            'estimated_time_min': round(hospital['distance'] * 2),  # Simple estimate: 30 km/h average speed
            'simplified_directions': f"Head {get_cardinal_direction(latitude, longitude, hospital['latitude'], hospital['longitude'])} toward {hospital['name']}"
        }
    
    # Return offline map data package
    return {
        'user_location': {
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': datetime.now().isoformat()
        },
        'hospitals': hospitals,
        'cache_expiry': (datetime.now().timestamp() + 3600 * 24)  # Cache valid for 24 hours
    }

def get_cardinal_direction(lat1, lon1, lat2, lon2):
    """
    Get cardinal direction (N, NE, E, SE, S, SW, W, NW) from point 1 to point 2
    
    Args:
        lat1, lon1: Starting coordinates
        lat2, lon2: Ending coordinates
        
    Returns:
        str: Cardinal direction
    """
    import math
    
    # Calculate angle
    dy = lat2 - lat1
    dx = lon2 - lon1
    angle = math.atan2(dy, dx) * 180 / math.pi
    
    # Convert angle to 0-360 range
    angle = (angle + 360) % 360
    
    # Convert angle to cardinal direction
    directions = ["east", "northeast", "north", "northwest", "west", "southwest", "south", "southeast"]
    index = round(angle / 45) % 8
    return directions[index]

def get_directions(start_lat, start_lng, end_lat, end_lng, mode='driving'):
    """
    Get directions between two points using Google Directions API.
    
    Args:
        start_lat (float): Starting latitude
        start_lng (float): Starting longitude
        end_lat (float): Ending latitude
        end_lng (float): Ending longitude
        mode (str): Travel mode ('driving', 'walking', 'bicycling', 'transit')
        
    Returns:
        dict: Directions data
    """
    # In a production environment, this would use the Google Directions API
    # For now, we'll return a simplified response
    
    # Example response structure
    directions = {
        'distance': {
            'text': '5.2 km',
            'value': 5200  # meters
        },
        'duration': {
            'text': '12 mins',
            'value': 720  # seconds
        },
        'steps': [
            {
                'instruction': 'Head north on Broadway',
                'distance': '0.5 km'
            },
            {
                'instruction': 'Turn right onto Main St',
                'distance': '1.2 km'
            },
            {
                'instruction': 'Turn left onto Hospital Ave',
                'distance': '3.5 km'
            }
        ]
    }
    
    return directions
