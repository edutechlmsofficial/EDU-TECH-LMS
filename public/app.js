// EDU TECH APP Frontend JavaScript
// Handles AJAX calls, form submissions, and UI interactions

const API_BASE_URL = 'http://localhost:5000/api/auth';

// -------------------- ALERT SYSTEM --------------------
// Stacked alert container
const alertContainer = document.createElement('div');
alertContainer.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2';
document.body.appendChild(alertContainer);

function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ease-out opacity-0 translate-x-10`;
    alertDiv.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
                <p class="text-sm">${message}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600" onclick="removeAlert(this.parentElement.parentElement)">×</button>
        </div>
    `;

    // Type-specific colors
    if (type === 'success') alertDiv.classList.add('bg-green-100', 'text-green-800', 'border', 'border-green-200');
    else if (type === 'error') alertDiv.classList.add('bg-red-100', 'text-red-800', 'border', 'border-red-200');
    else alertDiv.classList.add('bg-blue-100', 'text-blue-800', 'border', 'border-blue-200');

    alertContainer.appendChild(alertDiv);

    // Trigger slide-in animation
    requestAnimationFrame(() => {
        alertDiv.classList.remove('opacity-0', 'translate-x-10');
        alertDiv.classList.add('opacity-100', 'translate-x-0');
    });

    // Auto-remove after duration
    setTimeout(() => removeAlert(alertDiv), duration);
}

function removeAlert(element) {
    element.classList.add('opacity-0', 'translate-x-10');
    setTimeout(() => {
        if (element.parentElement) element.remove();
    }, 300); // match transition duration
}

// -------------------- UTILITY FUNCTIONS --------------------
function setLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner"></span> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || 'Submit';
    }
}

// -------------------- AJAX HELPER --------------------
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            ...options.headers
        },
        ...options
    };

    // Only set Content-Type to application/json if not FormData
    if (!(options.body instanceof FormData)) {
        config.headers['Content-Type'] = 'application/json';
    }

    // Add authorization header if token exists
    const sessionData = localStorage.getItem('edutech_session') || sessionStorage.getItem('edutech_session');
    if (sessionData) {
        try {
            const session = JSON.parse(sessionData);
            if (session.token) {
                config.headers['Authorization'] = `Bearer ${session.token}`;
            }
        } catch (error) {
            console.error('Error parsing session data:', error);
        }
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API request failed:', error);
        showAlert(error.message, 'error'); // Use new alert system here
        throw error;
    }
}

// -------------------- AUTH FUNCTIONS --------------------
async function login(email, password) {
    try {
        const data = await apiRequest('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        // Store session data including token
        const sessionData = {
            user: data.user,
            token: data.token,
            loginTime: new Date().toISOString()
        };

        localStorage.setItem('edutech_session', JSON.stringify(sessionData));

        showAlert('Login successful!', 'success');
        return data;
    } catch (error) {
        throw error;
    }
}

async function register(userData) {
    try {
        const data = await apiRequest('/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        showAlert('Registration successful! Please login.', 'success');
        return data;
    } catch (error) {
        throw error;
    }
}

async function logout() {
    localStorage.removeItem('edutech_session');
    sessionStorage.removeItem('edutech_session');
    window.location.href = '/pages/user_login.html';
}

// -------------------- LESSON & QUIZ FUNCTIONS --------------------
async function getLessons(grade = null) {
    try {
        const params = grade ? `?grade=${encodeURIComponent(grade)}` : '';
        return await apiRequest(`/student/lessons${params}`);
    } catch (error) {
        throw error;
    }
}

async function getLesson(lessonId) {
    try {
        return await apiRequest(`/lessons/${lessonId}`);
    } catch (error) {
        throw error;
    }
}

async function getQuizzes() {
    try {
        return await apiRequest('/quizzes');
    } catch (error) {
        throw error;
    }
}

async function updateProgress(lessonId, progressData) {
    try {
        return await apiRequest('/progress', {
            method: 'POST',
            body: JSON.stringify({ lesson_id: lessonId, ...progressData })
        });
    } catch (error) {
        console.error('Failed to update progress:', error);
        throw error;
    }
}

async function getProgress(userId) {
    try {
        return await apiRequest(`/progress?user_id=${userId}`);
    } catch (error) {
        throw error;
    }
}

// -------------------- AI FUNCTIONS --------------------
async function getAITutorResponse(query) {
    try {
        const data = await apiRequest('/ai/tutor', {
            method: 'POST',
            body: JSON.stringify({ query })
        });
        return data.response;
    } catch (error) {
        throw error;
    }
}

async function generateContent(topic) {
    try {
        const data = await apiRequest('/ai/generate-content', {
            method: 'POST',
            body: JSON.stringify({ topic })
        });
        return data.content;
    } catch (error) {
        throw error;
    }
}

// -------------------- FILE UPLOAD --------------------
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload-file`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        showAlert('File uploaded successfully!', 'success');
        return data;
    } catch (error) {
        throw error;
    }
}

// -------------------- VALIDATION --------------------
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function validateRequired(value) {
    return value && value.trim().length > 0;
}

// -------------------- DOM READY --------------------
function domReady(fn) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fn);
    } else {
        fn();
    }
}

// -------------------- EXPORT --------------------
window.EDUApp = {
    login,
    register,
    logout,
    getLessons,
    getLesson,
    getQuizzes,
    updateProgress,
    getProgress,
    getAITutorResponse,
    generateContent,
    uploadFile,
    showAlert,
    setLoading,
    validateEmail,
    validatePassword,
    validateRequired,
    domReady,
    apiRequest,

    // Fetches the quiz attempts for the logged-in student
    async getQuizAttempts() {
        try {
            return await this.apiRequest('/student/quizzes/attempts');
        } catch (error) {
            console.error('Failed to fetch quiz attempts:', error);
            throw error;
        }
    }
};
