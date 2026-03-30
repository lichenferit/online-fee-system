
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

function initializePage() {
    setupEventListeners();
    const today = new Date().toISOString().split('T')[0];
    const firstDueDateInput = document.getElementById('first_due_date');
    const secondDueDateInput = document.getElementById('second_due_date');
    
    if (firstDueDateInput) {
        firstDueDateInput.min = today;
    }
    if (secondDueDateInput) {
        secondDueDateInput.min = today;
    }
}

function setupEventListeners() {

}
function showScreen(screenId) {
    const screens = document.querySelectorAll('.screen');
    screens.forEach(screen => {
        screen.classList.remove('active');
    });
    
    const selectedScreen = document.getElementById(screenId);
    if (selectedScreen) {
        selectedScreen.classList.add('active');
        
        if (screenId === 'screen1' || screenId === 'screen2') {
            sessionStorage.removeItem('notificationShown');
        }
        
       
    }
}

function handleFormSubmit(event) {
    
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        minimumFractionDigits: 0
    }).format(amount);
}

function updateSecondAmount() {
    const firstAmount = parseFloat(document.getElementById('first_amount').value) || 0;
    const totalAmount = parseFloat(document.getElementById('total_amount_value').value) || 0;
    const secondAmount = totalAmount - firstAmount;
    
    const secondAmountInput = document.getElementById('second_amount');
    if (secondAmountInput) {
        secondAmountInput.value = secondAmount > 0 ? secondAmount.toFixed(2) : '';
    }
}

function validateFirstDate() {
    const firstDate = document.getElementById('first_due_date').value;
    if (!firstDate) return;
    
    const selectedDate = new Date(firstDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (selectedDate < today) {
        showNotification('First installment due date cannot be in the past!');
        document.getElementById('first_due_date').value = '';
        return false;
    }
    
    const dayOfWeek = selectedDate.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
        showNotification('First installment due date cannot be Saturday or Sunday!');
        document.getElementById('first_due_date').value = '';
        return false;
    }
    
    return true;
}

function validateSecondDate() {
    const firstDate = document.getElementById('first_due_date').value;
    const secondDate = document.getElementById('second_due_date').value;
    
    if (!secondDate) return;
    
    const selectedDate = new Date(secondDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (selectedDate < today) {
        showNotification('Second installment due date cannot be in the past!');
        document.getElementById('second_due_date').value = '';
        return false;
    }
    const dayOfWeek = selectedDate.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
        showNotification('Second installment due date cannot be Saturday or Sunday!');
        document.getElementById('second_due_date').value = '';
        return false;
    }
    
    if (firstDate) {
        const firstDateObj = new Date(firstDate);
        if (selectedDate <= firstDateObj) {
            showNotification('Second installment due date must be after first installment due date!');
            document.getElementById('second_due_date').value = '';
            return false;
        }
    }
    
    return true;
}

function validateInstallmentForm() {
    const firstAmount = parseFloat(document.getElementById('first_amount').value);
    const totalAmount = parseFloat(document.getElementById('total_amount_value').value);
    const firstDate = document.getElementById('first_due_date').value;
    const secondDate = document.getElementById('second_due_date').value;
    if (!firstAmount || firstAmount <= 0) {
        showNotification('Please enter a valid first installment amount!');
        return false;
    }
    if (firstAmount >= totalAmount) {
        showNotification('First installment amount must be less than total amount!');
        return false;
    }
    if (!firstDate) {
        showNotification('Please select first installment due date!');
        return false;
    }
    if (!secondDate) {
        showNotification('Please select second installment due date!');
        return false;
    }
    if (!validateFirstDate() || !validateSecondDate()) {
        return false;
    }
    
    return true;
}

let notificationTimeout = null;

function showNotification(message, type = 'info') {
    const modal = document.getElementById("notificationModal");
    const modalMessage = document.getElementById("modalMessage");
    const modalContent = modal?.querySelector('.modal-content');
    
    if (modal && modalMessage && modalContent) {
        modalContent.classList.remove('success', 'error', 'info');
        
        if (message.includes('successfully') || message.includes('saved') || message.includes('created')) {
            modalContent.classList.add('success');
        } else if (message.includes('not found') || message.includes('Error') || message.includes('error') || message.includes('cannot')) {
            modalContent.classList.add('error');
        } else {
            modalContent.classList.add('info');
        }
        
        modalMessage.innerText = message;
        modal.style.display = "flex";
        
        if (notificationTimeout) {
            clearTimeout(notificationTimeout);
        }
        
        notificationTimeout = setTimeout(() => { 
            closeModal(); 
        }, 5000);
    }
}

function closeModal() {
    const modal = document.getElementById("notificationModal");
    if (modal) {
        modal.style.display = "none";
    }
    
    if (notificationTimeout) {
        clearTimeout(notificationTimeout);
        notificationTimeout = null;
    }
}
function validateScreen1() {
    const cnic = document.getElementById('cnic')?.value.trim();
    const challan = document.getElementById('challan')?.value.trim();
    
    if (!cnic || !challan) {
        showNotification('Please enter both CNIC and Challan Number.');
        return false;
    }
    
    sessionStorage.removeItem('notificationShown');
    return true;
}
function clearNotificationState() {
    sessionStorage.removeItem('notificationShown');
}
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('screen1')?.classList.contains('active')) {
        clearNotificationState();
    }
});

document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        if (document.getElementById('screen1')?.classList.contains('active')) {
            clearNotificationState();
        }
    }
});