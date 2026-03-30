function showNotification(message) {
  const notification = document.getElementById('notification');
  if (window.notificationTimeout) {
    clearTimeout(window.notificationTimeout);
  }
  notification.innerText = message;
  notification.classList.remove('hide');
  notification.classList.add('show');
  window.notificationTimeout = setTimeout(() => {
    hideNotification();
  }, 4000);
}

function hideNotification() {
  const notification = document.getElementById('notification');
  notification.classList.remove('show');
  notification.classList.add('hide');
  if (window.notificationTimeout) {
    clearTimeout(window.notificationTimeout);
    window.notificationTimeout = null;
  }
}

function validateForm() {
  const cnicField = document.getElementById("cnic");
  const dobField = document.getElementById("dob");
  const cnic = cnicField.value.trim();
  const dob = dobField.value.trim();
  const cnicDigitsOnly = cnic.replace(/[-\s]/g, '');
  if (cnicDigitsOnly.length !== 13 || !/^\d{13}$/.test(cnicDigitsOnly)) {
    showNotification("CNIC must be 13 digits (XXXXX-XXXXXXX-X)");
    return false;
  }
  if (!dob) {
    showNotification("Please select Date of Birth");
    return false;
  }
  return true;
}

function clearDjangoMessages() {
  const messagesContainer = document.querySelector('.messages-container');
  if (messagesContainer) {
    messagesContainer.style.display = 'none';
  }
  document.querySelectorAll('.alert').forEach(alert => {
    alert.style.display = 'none';
  });
}

function handleDjangoErrors() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const message = alert.textContent.trim();
    if (message && message.includes('Invalid CNIC')) {
      showNotification("Invalid CNIC or Date of Birth. Please try again.");
      alert.style.display = 'none';
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  clearDjangoMessages();
  setTimeout(() => {
    handleDjangoErrors();
  }, 100);

  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      const isValid = validateForm();
      if (!isValid) {
        event.preventDefault();
        return false;
      }
      return true;
    });
  }
});

document.addEventListener('input', function() {
  hideNotification();
});