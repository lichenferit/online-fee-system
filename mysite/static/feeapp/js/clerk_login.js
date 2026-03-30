
if (window.history && window.history.replaceState) {
    window.history.replaceState(null, '', window.location.href);
    window.addEventListener('popstate', function(e) {
        window.history.pushState(null, '', window.location.href);
    });
}

let currentEmail = '';

function showPage(pageId) {
    var pages = document.querySelectorAll('.page');
    for (var i = 0; i < pages.length; i++) {
        pages[i].classList.remove('active');
    }
    document.getElementById(pageId).classList.add('active');
    clearAllMessages();

    if (pageId === 'loginPage') {
        const loginEmail = document.getElementById('loginEmail');
        const loginPassword = document.getElementById('loginPassword');
        if (loginEmail) loginEmail.value = '';
        if (loginPassword) loginPassword.value = '';
    }
}

function clearAllMessages() {
    var errorElements = document.querySelectorAll('.error-message');
    for (var i = 0; i < errorElements.length; i++) {
        errorElements[i].textContent = '';
    }
    var messageElements = document.querySelectorAll('[id*="Message"]');
    for (var i = 0; i < messageElements.length; i++) {
        messageElements[i].innerHTML = '';
    }
}


function showSuccessMessage(elementId, message) {
    document.getElementById(elementId).innerHTML =
        '<div class="success-message">' + message + '</div>';
}

function showErrorMessage(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.innerHTML =
            '<div class="error-message">' + message + '</div>';
    }
}

function togglePassword(inputId) {
    var passwordField = document.getElementById(inputId);
    var toggleButton = passwordField.nextElementSibling;

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleButton.textContent = '';
    } else {
        passwordField.type = 'password';
        toggleButton.textContent = '';
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function checkPasswordStrength(password) {
    var strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
}

function updatePasswordStrength() {
    var password = document.getElementById('newPassword').value;
    var strengthBar = document.getElementById('strengthBar');
    var strength = checkPasswordStrength(password);

    strengthBar.classList.remove('strength-weak', 'strength-medium', 'strength-strong');

    if (password.length === 0) {
        strengthBar.style.width = '0%';
    } else if (strength <= 2) {
        strengthBar.classList.add('strength-weak');
        strengthBar.style.width = '33%';
    } else if (strength <= 4) {
        strengthBar.classList.add('strength-medium');
        strengthBar.style.width = '66%';
    } else {
        strengthBar.classList.add('strength-strong');
        strengthBar.style.width = '100%';
    }
}

function showLogin() {
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    clearAllMessages();
    showPage('loginPage');
}

window.onload = function () {
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    if (loginEmail) loginEmail.value = '';
    if (loginPassword) loginPassword.value = '';
};

function showForgotPassword() {
    showPage('forgotStep1');
}

function showDashboard() {
   
   window.location.href = '/clerk/dashboard/'; 
}

function makeAPICall(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    }).then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showSlideNotification(message, isSuccess = true) {
    const toast = document.createElement('div');
    toast.className = 'toast-slide';
    toast.textContent = message;

    if (isSuccess) {
        toast.style.background = 'rgba(40, 167, 69, 0.95)';
    } else {
        toast.style.background = 'rgba(220, 53, 69, 0.95)';
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 50);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function resendOtp() {
    var email = document.getElementById('otpEmail').value;
    var resendBtn = event.target;
    var originalText = resendBtn.textContent;

    resendBtn.textContent = 'Resending...';
    resendBtn.disabled = true;

    makeAPICall('/api/clerk/resend-otp/', { email: email })
        .then((data) => {
            if (data.success) {
                showSlideNotification(data.message, true);
            } else {
                showSlideNotification(data.message, false);
            }
            resendBtn.textContent = originalText;
            resendBtn.disabled = false;
        })
        .catch((error) => {
            showSlideNotification('Error occurred while resending OTP.', false);
            resendBtn.textContent = originalText;
            resendBtn.disabled = false;
        });
}

document.addEventListener('DOMContentLoaded', function () {
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function (e) {
            e.preventDefault();

            var email = document.getElementById('loginEmail').value.trim();
            var password = document.getElementById('loginPassword').value;

            if (!email) {
                showSlideNotification('Email is required.', false);
                return;
            }
            if (!isValidEmail(email)) {
                showSlideNotification('Please enter a valid email.', false);
                return;
            }
            if (!password) {
                showSlideNotification('Password is required.', false);
                return;
            }

            loginBtn.textContent = 'Logging in...';
            loginBtn.disabled = true;

            makeAPICall('/api/clerk/login/', { email: email, password: password })
                .then((data) => {
                    if (data.success) {
                        showSlideNotification('Login successful! Redirecting...', true);
                        setTimeout(function () {
                            showDashboard();
                        }, 2000);
                    } else {
                        showSlideNotification(data.message || 'Invalid email or password.', false);
                    }
                    loginBtn.textContent = 'Login';
                    loginBtn.disabled = false;
                })
                .catch((error) => {
                    console.error('Login error:', error);
                    showSlideNotification('An error occurred during login. Please try again.', false);
                    loginBtn.textContent = 'Login';
                    loginBtn.disabled = false;
                });
        });
    }

    const sendOtpBtn = document.getElementById('sendOtpBtn');
    if (sendOtpBtn) {
        sendOtpBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var email = document.getElementById('resetEmail').value.trim();

            if (!email) {
                showSlideNotification('Email is required.', false);
                return;
            }
            if (!isValidEmail(email)) {
                showSlideNotification('Please enter a valid email.', false);
                return;
            }

            sendOtpBtn.textContent = 'Sending OTP...';
            sendOtpBtn.disabled = true;
            currentEmail = email;

            makeAPICall('/api/clerk/forgot-password/', { email: email })
                .then((data) => {
                    if (data.success) {
                        showSlideNotification(data.message || 'OTP sent successfully!', true);
                        document.getElementById('otpEmail').value = email;
                        setTimeout(function () {
                            showPage('forgotStep2');
                        }, 1500);
                    } else {
                        showSlideNotification(data.message || 'Failed to send OTP.', false);
                    }
                    sendOtpBtn.textContent = 'Send OTP';
                    sendOtpBtn.disabled = false;
                })
                .catch((error) => {
                    console.error('Send OTP error:', error);
                    showSlideNotification('An error occurred. Please try again.', false);
                    sendOtpBtn.textContent = 'Send OTP';
                    sendOtpBtn.disabled = false;
                });
        });
    }

    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var email = document.getElementById('otpEmail').value.trim();
            var otp = document.getElementById('otpCode').value.trim();

            if (!otp) {
                showSlideNotification('OTP is required.', false);
                return;
            }
            if (otp.length !== 6) {
                showSlideNotification('Enter a valid 6-digit OTP.', false);
                return;
            }

            verifyOtpBtn.textContent = 'Verifying...';
            verifyOtpBtn.disabled = true;

            makeAPICall('/api/clerk/verify-otp/', { email: email, otp: otp })
                .then((data) => {
                    if (data.success) {
                        showSlideNotification(data.message || 'OTP verified successfully!', true);
                        setTimeout(function () {
                            showPage('forgotStep3');
                        }, 1500);
                    } else {
                        showSlideNotification(data.message || 'Invalid OTP. Try again.', false);
                    }
                    verifyOtpBtn.textContent = 'Verify OTP';
                    verifyOtpBtn.disabled = false;
                })
                .catch((error) => {
                    console.error('Verify OTP error:', error);
                    showSlideNotification('An error occurred. Please try again.', false);
                    verifyOtpBtn.textContent = 'Verify OTP';
                    verifyOtpBtn.disabled = false;
                });
        });
    }

    const savePasswordBtn = document.getElementById('savePasswordBtn');
    if (savePasswordBtn) {
        savePasswordBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var email = currentEmail || document.getElementById('otpEmail').value.trim();
            var newPassword = document.getElementById('newPassword').value;
            var confirmPassword = document.getElementById('confirmPassword').value;

            if (!newPassword) {
                showSlideNotification('New password is required.', false);
                return;
            }
            if (checkPasswordStrength(newPassword) < 3) {
                showSlideNotification('Password is too weak.', false);
                return;
            }
            if (!confirmPassword) {
                showSlideNotification('Please confirm your password.', false);
                return;
            }
            if (newPassword !== confirmPassword) {
                showSlideNotification('Passwords do not match.', false);
                return;
            }

            savePasswordBtn.textContent = 'Saving...';
            savePasswordBtn.disabled = true;

            makeAPICall('/api/clerk/reset-password/', {
                email: email,
                new_password: newPassword,
            })
                .then((data) => {
                    if (data.success) {
                        showSlideNotification(data.message || 'Password updated successfully!', true);
                        setTimeout(function () {
                            showLogin();
                            currentEmail = '';
                        }, 2000);
                    } else {
                        showSlideNotification(data.message || 'Failed to update password.', false);
                    }
                    savePasswordBtn.textContent = 'Save Password';
                    savePasswordBtn.disabled = false;
                })
                .catch((error) => {
                    console.error('Reset password error:', error);
                    showSlideNotification('An error occurred. Please try again.', false);
                    savePasswordBtn.textContent = 'Save Password';
                    savePasswordBtn.disabled = false;
                });
        });
    }

    const newPasswordField = document.getElementById('newPassword');
    if (newPasswordField) {
        newPasswordField.addEventListener('input', updatePasswordStrength);
    }
});