/**
 * MediBot - Mental Health Support
 * Manages mental health chatbot and meditation features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize mental health chat if we're on the chat page
    if (document.getElementById('mentalHealthMessages')) {
        initializeMentalHealthChat();
    }
    
    // Initialize meditation controls if we're on the meditation page
    if (document.getElementById('meditationControls')) {
        initializeMeditationControls();
    }
    
    // Initialize session viewing if we're on the view session page
    if (document.getElementById('sessionDetails')) {
        initializeSessionViewer();
    }
});

/**
 * Initialize mental health chat functionality
 */
function initializeMentalHealthChat() {
    // Scroll to bottom of chat messages
    scrollToBottom();
    
    // Set up message form submission
    setupMessageForm();
    
    // Set up suggested message buttons
    setupSuggestedMessages();
}

/**
 * Scroll to the bottom of the chat messages
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('mentalHealthMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Set up message form submission
 */
function setupMessageForm() {
    const messageForm = document.getElementById('mentalHealthMessageForm');
    const messageInput = document.getElementById('mentalHealthInput');
    
    if (messageForm && messageInput) {
        messageForm.addEventListener('submit', function(e) {
            // Check if message is empty
            if (!messageInput.value.trim()) {
                e.preventDefault();
                return;
            }
            
            // Show sending state
            const sendButton = messageForm.querySelector('button[type="submit"]');
            if (sendButton) {
                const originalText = sendButton.innerHTML;
                sendButton.disabled = true;
                sendButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Sending...';
                
                // Reset button after form submission (useful if there's an error)
                setTimeout(() => {
                    sendButton.disabled = false;
                    sendButton.innerHTML = originalText;
                }, 2000);
            }
            
            // Let the form submit normally - the backend will handle adding the message
        });
        
        // Focus on message input
        messageInput.focus();
    }
}

/**
 * Set up suggested message buttons
 */
function setupSuggestedMessages() {
    const suggestedButtons = document.querySelectorAll('.suggested-message');
    if (suggestedButtons.length > 0) {
        suggestedButtons.forEach(button => {
            button.addEventListener('click', function() {
                const message = this.getAttribute('data-message');
                const messageInput = document.getElementById('mentalHealthInput');
                
                if (messageInput && message) {
                    messageInput.value = message;
                    messageInput.focus();
                }
            });
        });
    }
}

/**
 * Initialize meditation controls for the meditation page
 */
function initializeMeditationControls() {
    const playButtons = document.querySelectorAll('.meditation-play-btn');
    const pauseButtons = document.querySelectorAll('.meditation-pause-btn');
    const stopButtons = document.querySelectorAll('.meditation-stop-btn');
    const timerDisplays = document.querySelectorAll('.meditation-timer');
    
    let activeTimer = null;
    let currentTimerInterval = null;
    let remainingTime = 0;
    
    // Set up play buttons
    playButtons.forEach(button => {
        button.addEventListener('click', function() {
            const meditationCard = this.closest('.meditation-card');
            if (!meditationCard) return;
            
            const duration = parseInt(this.getAttribute('data-duration') || '300');
            const timerDisplay = meditationCard.querySelector('.meditation-timer');
            const pauseButton = meditationCard.querySelector('.meditation-pause-btn');
            const playButton = this;
            
            // Stop any existing meditation
            stopAllMeditations();
            
            // Set this as the active timer
            activeTimer = timerDisplay;
            remainingTime = duration;
            
            // Update UI
            playButton.style.display = 'none';
            if (pauseButton) pauseButton.style.display = 'inline-block';
            
            // Start the timer
            updateTimerDisplay(timerDisplay, remainingTime);
            currentTimerInterval = setInterval(() => {
                remainingTime--;
                updateTimerDisplay(timerDisplay, remainingTime);
                
                if (remainingTime <= 0) {
                    stopAllMeditations();
                    playMeditationCompletionSound();
                    showMeditationCompleteMessage(meditationCard);
                }
            }, 1000);
            
            // Play meditation start sound
            playMeditationStartSound();
            
            // Show active meditation status
            meditationCard.classList.add('active-meditation');
        });
    });
    
    // Set up pause buttons
    pauseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const meditationCard = this.closest('.meditation-card');
            if (!meditationCard) return;
            
            const playButton = meditationCard.querySelector('.meditation-play-btn');
            
            // Clear the interval
            clearInterval(currentTimerInterval);
            currentTimerInterval = null;
            
            // Update UI
            this.style.display = 'none';
            if (playButton) playButton.style.display = 'inline-block';
            
            // Update meditation card status
            meditationCard.classList.remove('active-meditation');
        });
    });
    
    // Set up stop buttons
    stopButtons.forEach(button => {
        button.addEventListener('click', function() {
            stopAllMeditations();
        });
    });
    
    // Helper function to stop all meditations
    function stopAllMeditations() {
        // Clear any existing interval
        if (currentTimerInterval) {
            clearInterval(currentTimerInterval);
            currentTimerInterval = null;
        }
        
        // Reset all UI elements
        document.querySelectorAll('.meditation-card').forEach(card => {
            card.classList.remove('active-meditation');
            
            const playButton = card.querySelector('.meditation-play-btn');
            const pauseButton = card.querySelector('.meditation-pause-btn');
            const timerDisplay = card.querySelector('.meditation-timer');
            
            if (playButton) playButton.style.display = 'inline-block';
            if (pauseButton) pauseButton.style.display = 'none';
            if (timerDisplay) updateTimerDisplay(timerDisplay, 0);
        });
    }
    
    // Helper function to update timer display
    function updateTimerDisplay(element, seconds) {
        if (!element) return;
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        element.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    // Simulate sounds (in a real app, these would use the Web Audio API)
    function playMeditationStartSound() {
        console.log('Meditation start sound played');
    }
    
    function playMeditationCompletionSound() {
        console.log('Meditation completion sound played');
    }
    
    // Show completion message
    function showMeditationCompleteMessage(meditationCard) {
        if (!meditationCard) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'alert alert-success mt-3';
        messageElement.innerHTML = '<i class="fas fa-check-circle me-2"></i>Meditation complete! How do you feel?';
        
        meditationCard.appendChild(messageElement);
        
        // Remove the message after 5 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

/**
 * Initialize session viewer
 */
function initializeSessionViewer() {
    // Set up message filtering
    const filterButtons = document.querySelectorAll('.message-filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const filterType = this.getAttribute('data-filter');
                
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Filter messages
                filterSessionMessages(filterType);
            });
        });
    }
}

/**
 * Filter session messages based on type
 * @param {string} filterType - The type of messages to show ('all', 'user', or 'ai')
 */
function filterSessionMessages(filterType) {
    const messages = document.querySelectorAll('.session-message');
    
    messages.forEach(message => {
        switch (filterType) {
            case 'user':
                message.style.display = message.classList.contains('user-message') ? '' : 'none';
                break;
            case 'ai':
                message.style.display = message.classList.contains('ai-message') ? '' : 'none';
                break;
            case 'all':
            default:
                message.style.display = '';
                break;
        }
    });
}
