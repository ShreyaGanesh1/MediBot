/**
ock';
        }
    }
}

/**
 * Send emergency alert to backend
 * @param {number} latitude - User's latitude
 * @param {number} longitude - User's longitude
 * @param {string} mode - Emergency mode ('online' or 'offline')
 */
function sendEmergencyAlert(latitude, longitude, mode) {
    // In a real app, this would make an API call to the backend
    
    // Simulate API call with a delay
    setTimeout(() => {
        if (mode === 'online') {
            // Update the emergency modal to show success
            document.getElementById('emergencyModalMessage').textContent = 'Emergency Alert Sent!';
            document.getElementById('emergencyModalDetails').innerHTML = `
                Emergency services and your emergency contacts have been notified.
                ${latitude && longitude ? '<br>Your location has been shared with emergency responders.' : ''}
            `;
            
            // Close modal after a delay
            setTimeout(() => {
                const modalElement = document.getElementById('emergencyModal');
                const emergencyModal = bootstrap.Modal.getInstance(modalElement);
                emergencyModal.hide();
                
                // Show success message on the page
                const emergencyStatus = document.getElementById('emergencyStatus');
                if (emergencyStatus) {
                    emergencyStatus.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>Emergency alert sent!</strong> Help is on the way.
                        </div>
                    `;
                    emergencyStatus.style.display = 'block';
                }
            }, 3000);
        }
    }, 2000);
    
    // In a real app, we would also:
    // 1. Send the alert to the server
    // 2. Notify emergency contacts
    // 3. Contact nearest hospitals/emergency services
    // 4. Start tracking user's location for emergency services
    
    console.log(`Emergency alert sent with mode: ${mode}, location: ${latitude}, ${longitude}`);
}

/**
 * Set up map toggle button
 */
function setupMapToggle() {
    const toggleMapBtn = document.getElementById('toggleMapBtn');
    if (toggleMapBtn) {
        toggleMapBtn.addEventListener('click', toggleMapMode);
    }
}

/**
 * Toggle between online and offline maps
 */
function toggleMapMode() {
    const onlineMap = document.getElementById('map');
    const offlineMap = document.getElementById('offline-map');
    const toggleBtn = document.getElementById('toggleMapBtn');
    
    if (!onlineMap || !offlineMap) return;
    
    if (isOnlineMap) {
        // Switch to offline map
        onlineMap.style.display = 'none';
        offlineMap.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-exchange-alt me-1"></i> Switch to Online Map';
        toggleBtn.classList.remove('btn-outline-info');
        toggleBtn.classList.add('btn-outline-success');
        
        // Update offline map size as it might not have been initialized properly when hidden
        if (offlineMap) {
            offlineMap.invalidateSize();
        }
    } else {
        // Switch to online map
        offlineMap.style.display = 'none';
        onlineMap.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-exchange-alt me-1"></i> Switch to Offline Map';
        toggleBtn.classList.remove('btn-outline-success');
        toggleBtn.classList.add('btn-outline-info');
    }
    
    isOnlineMap = !isOnlineMap;
}

/**
 * Initialize the offline map with OpenStreetMap
 */
function initOfflineMap() {
    // Get current position from the window object (set in the inline script)
    if (!window.currentPosition) {
        console.error('Current position not available for offline map');
        return;
    }
    
    // Initialize the map
    offlineMap = L.map('offline-map').setView(
        [window.currentPosition.lat, window.currentPosition.lng], 
        13
    );
    
    // Add dark theme tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(offlineMap);
    
    // Add user marker
    offlineUserMarker = L.circleMarker(
        [window.currentPosition.lat, window.currentPosition.lng],
        {
            radius: 8,
            fillColor: '#4285F4',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 1
        }
    ).addTo(offlineMap);
    
    // Add hospital markers
    if (window.nearby_hospitals) {
        window.nearby_hospitals.forEach(hospital => {
            const marker = L.marker([hospital.latitude, hospital.longitude])
                .addTo(offlineMap);
            
            marker.bindPopup(`
                <div>
                    <h5>${hospital.name}</h5>
                    <p>${hospital.address || ''}</p>
                    <p>Distance: ${hospital.distance} km</p>
                    <p>Phone: ${hospital.phone_number || 'N/A'}</p>
                    <button class="btn btn-sm btn-primary" 
                        onclick="getOfflineDirections(${hospital.latitude}, ${hospital.longitude}, '${hospital.name}')">
                        Get Directions
                    </button>
                </div>
            `);
            
            offlineHospitalMarkers.push(marker);
        });
    }
}

/**
 * Get directions using the offline map
 * @param {number} lat - Destination latitude
 * @param {number} lng - Destination longitude
 * @param {string} name - Destination name
 */
function getOfflineDirections(lat, lng, name) {
    if (!offlineMap) return;
    
    // Clear any existing route layers
    offlineMap.eachLayer(layer => {
        if (layer instanceof L.Polyline && !(layer instanceof L.CircleMarker)) {
            offlineMap.removeLayer(layer);
        }
    });
    
    // Draw a simple straight line between points for offline use
    const userLatLng = [window.currentPosition.lat, window.currentPosition.lng];
    const destLatLng = [lat, lng];
    
    const routeLine = L.polyline([userLatLng, destLatLng], {
        color: '#dc3545',
        weight: 5,
        opacity: 0.7
    }).addTo(offlineMap);
    
    // Fit map to show the route
    offlineMap.fitBounds(routeLine.getBounds(), {padding: [50, 50]});
    
    // Calculate straight-line distance
    const distance = offlineMap.distance(userLatLng, destLatLng) / 1000; // convert to km
    alert(`Offline directions to ${name}\nDistance: ${distance.toFixed(2)} km (straight line)\nNote: This is simplified offline routing.`);
}

/**
 * Load cached offline map data from localStorage
 * This allows the app to work even when the user is offline
 */
function loadCachedOfflineData() {
    // Check if offline map data is cached in localStorage
    const cachedData = localStorage.getItem('medibot-offline-map-data');
    
    if (cachedData) {
        try {
            // Parse the cached data
            const offlineData = JSON.parse(cachedData);
            
            // Check if data is still valid (not expired)
            const now = new Date().getTime() / 1000; // current time in seconds
            if (offlineData.cache_expiry && offlineData.cache_expiry > now) {
                console.log('Using cached offline map data (valid until ' + new Date(offlineData.cache_expiry * 1000).toLocaleString() + ')');
                
                // Show a notification
                const status = document.getElementById('emergencyStatus');
                if (status) {
                    status.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Offline data available!</strong> You can use the app even when offline.
                            <button class="btn btn-sm btn-outline-dark ms-2" onclick="toggleMapMode()">
                                Switch to Offline Map
                            </button>
                        </div>
                    `;
                    status.style.display = 'block';
                    
                    // Auto-hide the notification after 5 seconds
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 5000);
                }
                
                return true;
            } else {
                console.log('Cached offline map data has expired');
                localStorage.removeItem('medibot-offline-map-data');
            }
        } catch (e) {
            console.error('Error parsing cached offline map data:', e);
            localStorage.removeItem('medibot-offline-map-data');
        }
    }
    
    return false;
}

/**
 * Get directions to a hospital or specific location
 * Note: This function is called from HTML with inline event handlers
 * @param {number} lat - Destination latitude
 * @param {number} lng - Destination longitude
 * @param {string} name - Destination name
 */
function getDirectionsTo(lat, lng, name) {
    if (!isOnlineMap) {
        // Use offline directions
        getOfflineDirections(lat, lng, name);
        return;
    }
    
    // Use online Google Maps
    console.log(`Getting directions to ${name} at ${lat}, ${lng}`);
    
    // This will be executed by the maps-specific code in the page
    if (window.directionsService && window.directionsRenderer) {
        const destination = new google.maps.LatLng(lat, lng);
        const origin = new google.maps.LatLng(window.currentPosition.lat, window.currentPosition.lng);
        
        window.directionsService.route(
            {
                origin: origin,
                destination: destination,
                travelMode: google.maps.TravelMode.DRIVING
            },
            (response, status) => {
                if (status === "OK") {
                    window.directionsRenderer.setDirections(response);
                    
                    // Get route information
                    const route = response.routes[0];
                    const leg = route.legs[0];
                    
                    // Alert with directions info
                    alert(`Directions to ${name}\nDistance: ${leg.distance.text}\nEstimated time: ${leg.duration.text}`);
                } else {
                    alert("Directions request failed due to " + status);
                }
            }
        );
    }
}
