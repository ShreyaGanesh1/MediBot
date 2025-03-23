/**
 * MediBot - Chat Functionality
 * Manages patient-doctor chat and video calling features
 */

let chatSocket = null;
let localStream = null;
let remoteStream = null;
let peerConnection = null;
let isMuted = false;
let isVideoOff = false;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat features if we're on the chat page
    if (document.getElementById('chatMessages')) {
        initializeChat();
    }
});

/**
 * Initialize chat functionality
 */
function initializeChat() {
    // Scroll to bottom of chat messages
    scrollToBottom();
    
    // Set up message form submission
    setupMessageForm();
    
    // Set up video call functionality
    setupVideoCallFeatures();
    
    // Set up simulated doctor responses
    setupSimulatedResponses();
}

/**
 * Scroll to the bottom of the chat messages
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Set up message form submission
 */
function setupMessageForm() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    
    if (messageForm && messageInput) {
        messageForm.addEventListener('submit', function(e) {
            // Check if message is empty
            if (!messageInput.value.trim()) {
                e.preventDefault();
                return;
            }
            
            // In a real app with websockets, we would add the message 
            // to the UI immediately and then send it to the server
            
            // For the demo, we'll let the form submit as normal
            // The backend will add the message to the database and 
            // redirect back to the chat page with the new message visible
        });
        
        // Add focus to message input
        messageInput.focus();
        
        // Add Ctrl+Enter keyboard shortcut for sending messages
        messageInput.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                if (messageInput.value.trim()) {
                    messageForm.submit();
                }
            }
        });
    }
}

/**
 * Set up video call features
 */
function setupVideoCallFeatures() {
    const startVideoBtn = document.getElementById('startVideoBtn');
    const endCallBtn = document.getElementById('endCallBtn');
    const toggleMicBtn = document.getElementById('toggleMicBtn');
    const toggleVideoBtn = document.getElementById('toggleVideoBtn');
    const videoCallArea = document.getElementById('videoCallArea');
    
    if (startVideoBtn && videoCallArea) {
        startVideoBtn.addEventListener('click', function() {
            videoCallArea.style.display = 'block';
            startVideoBtn.disabled = true;
            startVideoBtn.innerHTML = '<i class="fas fa-video me-2"></i>Video Call Active';
            
            // Initialize WebRTC
            initializeVideoCall();
        });
    }
    
    if (endCallBtn) {
        endCallBtn.addEventListener('click', function() {
            endVideoCall();
            
            videoCallArea.style.display = 'none';
            if (startVideoBtn) {
                startVideoBtn.disabled = false;
                startVideoBtn.innerHTML = '<i class="fas fa-video me-2"></i>Start Video Call';
            }
        });
    }
    
    if (toggleMicBtn) {
        toggleMicBtn.addEventListener('click', function() {
            toggleMicrophone();
        });
    }
    
    if (toggleVideoBtn) {
        toggleVideoBtn.addEventListener('click', function() {
            toggleVideo();
        });
    }
}

/**
 * Initialize WebRTC video call
 */
function initializeVideoCall() {
    // In a real application, this would use real WebRTC with signaling server
    
    // Request access to webcam and microphone
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            localStream = stream;
            
            // Display local video
            const localVideo = document.getElementById('localVideo');
            if (localVideo) {
                localVideo.srcObject = stream;
            }
            
            // Add a system message to chat
            addSystemMessage('Video call started');
            
            // Simulate connecting to remote peer
            simulateConnectingToDoctor();
        })
        .catch(err => {
            console.error('Error accessing media devices:', err);
            
            // Show error message to user
            alert('Could not access camera or microphone. Please check permissions and try again.');
            
            // Reset UI
            resetVideoUI();
            
            // Add system message about failure
            addSystemMessage('Failed to start video call: ' + err.message);
        });
}

/**
 * Simulate connecting to a doctor
 */
function simulateConnectingToDoctor() {
    // Add a "connecting" message
    addSystemMessage('Connecting to doctor...');
    
    // Simulate connection delay
    setTimeout(() => {
        // In a real app, we would set up WebRTC connection here
        // and handle signaling to connect with the doctor
        
        // For demo, we'll just show the local video feed as the remote video too
        const remoteVideo = document.getElementById('remoteVideo');
        if (remoteVideo && localStream) {
            remoteVideo.srcObject = localStream;
            
            // Add connected message
            addSystemMessage('Doctor connected to video call');
        }
    }, 3000);
}

/**
 * End the video call
 */
function endVideoCall() {
    // Stop all tracks in the local stream
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    // Clear the video elements
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    
    if (localVideo) {
        localVideo.srcObject = null;
    }
    
    if (remoteVideo) {
        remoteVideo.srcObject = null;
    }
    
    // Close any WebRTC peer connection
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    // Add system message about call ending
    addSystemMessage('Video call ended');
    
    // Reset mute/video buttons
    resetVideoControls();
}

/**
 * Toggle microphone mute state
 */
function toggleMicrophone() {
    const toggleMicBtn = document.getElementById('toggleMicBtn');
    
    if (localStream) {
        const audioTracks = localStream.getAudioTracks();
        if (audioTracks.length > 0) {
            const track = audioTracks[0];
            
            // Toggle enabled state
            track.enabled = !track.enabled;
            isMuted = !track.enabled;
            
            // Update button UI
            if (toggleMicBtn) {
                toggleMicBtn.innerHTML = isMuted ? 
                    '<i class="fas fa-microphone-slash"></i>' : 
                    '<i class="fas fa-microphone"></i>';
            }
            
            // Add system message
            addSystemMessage(isMuted ? 'You muted your microphone' : 'You unmuted your microphone');
        }
    }
}

/**
 * Toggle video on/off state
 */
function toggleVideo() {
    const toggleVideoBtn = document.getElementById('toggleVideoBtn');
    const localVideo = document.getElementById('localVideo');
    
    if (localStream) {
        const videoTracks = localStream.getVideoTracks();
        if (videoTracks.length > 0) {
            const track = videoTracks[0];
            
            // Toggle enabled state
            track.enabled = !track.enabled;
            isVideoOff = !track.enabled;
            
            // Update button UI
            if (toggleVideoBtn) {
                toggleVideoBtn.innerHTML = isVideoOff ? 
                    '<i class="fas fa-video-slash"></i>' : 
                    '<i class="fas fa-video"></i>';
            }
            
            // Update video display
            if (localVideo) {
                localVideo.style.display = isVideoOff ? 'none' : 'block';
            }
            
            // Add system message
            addSystemMessage(isVideoOff ? 'You turned off your camera' : 'You turned on your camera');
        }
    }
}

/**
 * Reset video UI elements
 */
function resetVideoUI() {
    const videoCallArea = document.getElementById('videoCallArea');
    const startVideoBtn = document.getElementById('startVideoBtn');
    
    if (videoCallArea) {
        videoCallArea.style.display = 'none';
    }
    
    if (startVideoBtn) {
        startVideoBtn.disabled = false;
        startVideoBtn.innerHTML = '<i class="fas fa-video me-2"></i>Start Video Call';
    }
    
    resetVideoControls();
}

/**
 * Reset video control buttons to default state
 */
function resetVideoControls() {
    const toggleMicBtn = document.getElementById('toggleMicBtn');
    const toggleVideoBtn = document.getElementById('toggleVideoBtn');
    
    if (toggleMicBtn) {
        toggleMicBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
    
    if (toggleVideoBtn) {
        toggleVideoBtn.innerHTML = '<i class="fas fa-video"></i>';
    }
    
    isMuted = false;
    isVideoOff = false;
}

/**
 * Add a system message to the chat
 * @param {string} message - The system message to add
 */
function addSystemMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const systemMessage = document.createElement('div');
    systemMessage.className = 'message text-center w-100 my-3';
    systemMessage.innerHTML = `
        <div class="text-muted small">
            <i class="fas fa-info-circle me-1"></i>
            ${message}
        </div>
    `;
    
    chatMessages.appendChild(systemMessage);
    scrollToBottom();
}

/**
 * Add a normal chat message to the UI
 * @param {string} message - The message text
 * @param {boolean} isFromUser - Whether the message is from the current user
 */
function addChatMessage(message, isFromUser) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isFromUser ? 'message-sent' : 'message-received'}`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${message}
        </div>
        <div class="message-time">
            ${timeString}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Set up simulated doctor responses
 */
function setupSimulatedResponses() {
    // This is only for the demo to simulate doctor responses
    // In a real app, this would use real-time websocket communication
    
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            // Don't actually submit the form in the demo
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message to UI
            addChatMessage(message, true);
            
            // Clear input
            messageInput.value = '';
            
            // Simulate doctor typing
            simulateDoctorTyping();
            
            // Simulate doctor response after a delay
            setTimeout(() => {
                const doctorResponses = [
                    "Thank you for sharing that information. Have you been experiencing these symptoms for long?",
                    "I understand your concern. Let me know if there are any other symptoms you've noticed.",
                    "Based on what you've described, I'd recommend we run some additional tests.",
                    "Have you taken any medication for this condition recently?",
                    "Let's discuss your options for treatment. Do you have any questions about what I've explained so far?",
                    "I'd like to follow up with you in two weeks to see how you're progressing.",
                    "That's a common concern with this condition. Most patients see improvement within a few weeks.",
                    "I'm going to send you some educational materials about managing this condition at home."
                ];
                
                // Choose a random response
                const randomResponse = doctorResponses[Math.floor(Math.random() * doctorResponses.length)];
                
                // Add doctor response to UI
                addChatMessage(randomResponse, false);
            }, 3000);
        });
    }
}

/**
 * Simulate doctor typing indicator
 */
function simulateDoctorTyping() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Create typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message message-received typing-indicator';
    typingIndicator.innerHTML = `
        <div class="message-content">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    `;
    
    // Add to chat
    chatMessages.appendChild(typingIndicator);
    scrollToBottom();
    
    // Remove after doctor "responds"
    setTimeout(() => {
        typingIndicator.remove();
    }, 3000);
}
