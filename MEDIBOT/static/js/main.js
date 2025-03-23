/**
 * MediBot - Main JavaScript
 * Contains common functionality used across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Setup dropdown dynamic population
    setupPatientDropdown();
    
    // Initialize common event listeners
    setupEventListeners();
    
    // Set up dark mode functionality
    setupDarkMode();
    
    // Handle alert auto-dismissal
    setupAlertDismiss();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Populate the patient dropdown in attender navigation
 */
function setupPatientDropdown() {
    const patientDropdown = document.getElementById('patientDropdown');
    
    if (patientDropdown) {
        // Get dropdown menu
        const dropdownMenu = patientDropdown.nextElementSibling;
        
        // Fetch patients from API (this is simulated in this demo)
        fetch('/attender/api/patients')
            .then(response => {
                // If we can't get patients, don't show error to user
                if (!response.ok) return [];
                return response.json();
            })
            .then(data => {
                if (data && data.patients && data.patients.length > 0) {
                    // Clear existing dropdown items except the "View All" option
                    const viewAllItem = dropdownMenu.querySelector('.dropdown-item');
                    dropdownMenu.innerHTML = '';
                    dropdownMenu.appendChild(viewAllItem);
                    
                    // Add divider
                    const divider = document.createElement('li');
                    divider.innerHTML = '<hr class="dropdown-divider">';
                    dropdownMenu.appendChild(divider);
                    
                    // Add patients to dropdown
                    data.patients.forEach(patient => {
                        const item = document.createElement('li');
                        item.innerHTML = `<a class="dropdown-item" href="/attender/medical-records/${patient.id}">${patient.full_name}</a>`;
                        dropdownMenu.appendChild(item);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching patients:', error);
            });
    }
}

/**
 * Setup common event listeners
 */
function setupEventListeners() {
    // Password confirmation validation
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        if (field.id.includes('confirm')) {
            field.addEventListener('input', validatePasswordMatch);
        }
    });
    
    // Search functionality in tables
    const searchInputs = document.querySelectorAll('.table-search-input');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', handleTableSearch);
    });
}

/**
 * Validate that password and confirm password fields match
 */
function validatePasswordMatch() {
    const passwordId = this.id.replace('confirm_', '');
    const password = document.getElementById(passwordId);
    
    if (password && this.value !== password.value) {
        this.setCustomValidity("Passwords don't match");
    } else {
        this.setCustomValidity('');
    }
}

/**
 * Handle search functionality in tables
 */
function handleTableSearch() {
    const searchValue = this.value.toLowerCase();
    const tableId = this.getAttribute('data-table');
    const table = document.getElementById(tableId);
    
    if (table) {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            let textContent = row.textContent.toLowerCase();
            if (textContent.includes(searchValue)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

/**
 * Set up dark mode functionality
 * Note: The app currently uses dark mode by default
 */
function setupDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const htmlElement = document.documentElement;
            
            if (htmlElement.getAttribute('data-bs-theme') === 'dark') {
                htmlElement.setAttribute('data-bs-theme', 'light');
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            } else {
                htmlElement.setAttribute('data-bs-theme', 'dark');
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            }
            
            // Save preference
            localStorage.setItem('darkMode', htmlElement.getAttribute('data-bs-theme'));
        });
        
        // Check saved preference
        const savedDarkMode = localStorage.getItem('darkMode');
        if (savedDarkMode) {
            document.documentElement.setAttribute('data-bs-theme', savedDarkMode);
            darkModeToggle.innerHTML = savedDarkMode === 'dark' ? 
                '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
    }
}

/**
 * Set up automatic dismissal of alerts after a delay
 */
function setupAlertDismiss() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Format a date string in a user-friendly way
 * @param {string} dateString - The date string to format
 * @returns {string} The formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

/**
 * Format time in a user-friendly way
 * @param {string} timeString - The time string to format
 * @returns {string} The formatted time
 */
function formatTime(timeString) {
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit'
    });
}

/**
 * Show a loading spinner in the specified element
 * @param {HTMLElement} element - The element to show the spinner in
 * @param {string} message - Optional message to show with the spinner
 */
function showSpinner(element, message = 'Loading...') {
    const originalContent = element.innerHTML;
    element.setAttribute('data-original-content', originalContent);
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${message}
    `;
    element.disabled = true;
}

/**
 * Hide the loading spinner and restore the original content
 * @param {HTMLElement} element - The element containing the spinner
 */
function hideSpinner(element) {
    const originalContent = element.getAttribute('data-original-content');
    if (originalContent) {
        element.innerHTML = originalContent;
        element.removeAttribute('data-original-content');
    }
    element.disabled = false;
}

/**
 * Show a toast notification
 * @param {string} title - Title of the notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, danger, warning, info)
 */
function showToast(title, message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast bg-${type} text-white` + (type === 'light' ? ' text-dark' : '');
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toastEl.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}
