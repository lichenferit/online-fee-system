function validateChallanNumber(challan) {
  return /^[^\s]{6,12}$/.test(challan);
}

const modalOverlay = document.getElementById('modalOverlay');
const modal = document.getElementById('modal');
const modalMessage = document.getElementById('modalMessage');
const modalCloseBtn = document.getElementById('modalCloseBtn');

function showModal(message, type = 'info', processing = false) {
  modalMessage.textContent = message;
  modal.className = 'modal';
  if (processing) {
    modal.classList.add('processing');
    modalCloseBtn.style.display = 'none';
  } else {
    modalCloseBtn.style.display = 'inline-block';
    modalCloseBtn.focus();
  }
  if (type === 'success') modal.classList.add('success');
  else if (type === 'error') modal.classList.add('error');
  else modal.classList.add('info');
  modalOverlay.style.display = 'flex';
}

function hideModal() {
  modalOverlay.style.display = 'none';
}

modalCloseBtn.addEventListener('click', () => {
  hideModal();
  if (modal.classList.contains('success')) {
    document.getElementById('challanNumber').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('dueDate').value = '';
    document.getElementById('status').value = '';
  }
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.getElementById('updateBtn').addEventListener('click', () => {
  const challanNumber = document.getElementById('challanNumber').value.trim();
  const amount = document.getElementById('amount').value.trim();
  const dueDate = document.getElementById('dueDate').value.trim();
  const status = document.getElementById('status').value;

  console.log('Form values:', { challanNumber, amount, dueDate, status });

  if (!challanNumber) {
    showModal('Challan Number is required.', 'error');
    return;
  }

  if (!validateChallanNumber(challanNumber)) {
    showModal('Invalid Challan Number format. Must be 6-12 characters, no spaces.', 'error');
    return;
  }

  if (!amount && !dueDate && !status) {
    showModal('Please enter at least one field to update (Amount, Due Date, or Status).', 'error');
    return;
  }

  showModal('Processing update... please wait.', 'info', true);


  fetch(`/api/get-challan-data/${challanNumber}/`)
    .then(response => response.json())
    .then(challanData => {
      if (challanData.error) {
        hideModal();
        showModal(challanData.error, 'error');
        return;
      }
      if (challanData.status && challanData.status.toUpperCase() === 'PAID') {
        hideModal();
        showModal('This challan is already PAID. No updates are allowed on a paid challan.', 'error');
        return;
      }
      
      sendUpdateRequest();
    })
    .catch(() => {
     
      sendUpdateRequest();
    });

  function sendUpdateRequest() {
    const payload = { challanNumber };
    if (amount) payload.amount = amount;
    if (dueDate) payload.dueDate = dueDate;
    if (status) payload.status = status;

    console.log('Sending payload:', JSON.stringify(payload));

    fetch('/api/update-challan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(payload),
    })
    .then(response => {
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers.get('content-type'));

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return response.text().then(html => {
          console.error('Received HTML instead of JSON:', html.substring(0, 200));
          throw new Error('Server returned an error page. Please check if the URL /api/update_challan/ is correct in urls.py');
        });
      }

      return response.json().then(data => {
        if (!response.ok) {
          throw new Error(data.error || `Server error: ${response.status}`);
        }
        return data;
      });
    })
    .then(data => {
      console.log('Success response:', data);
      if (data.message) {
        showModal(data.message, 'success');
      } else {
        showModal('Update completed successfully.', 'success');
      }
    })
    .catch(error => {
      console.error('Update error:', error);
      showModal(error.message || 'Failed to connect to server.', 'error');
    });
  } 
});

document.addEventListener('DOMContentLoaded', function() {
  const urlParams = new URLSearchParams(window.location.search);
  const challanFromUrl = urlParams.get('challan');

  if (challanFromUrl) {
    document.getElementById('challanNumber').value = challanFromUrl;
  }

  const dueDateInput = document.getElementById('dueDate');

  function isWeekend(date) {
    const day = date.getDay();
    return day === 0 || day === 6;
  }

  function getNextValidDate(date) {
    const newDate = new Date(date);
    while (isWeekend(newDate)) {
      newDate.setDate(newDate.getDate() + 1);
    }
    return newDate;
  }

  const today = new Date();
  const nextValid = getNextValidDate(today);
  const minDate = nextValid.toISOString().split('T')[0];
  dueDateInput.setAttribute('min', minDate);

  dueDateInput.addEventListener('input', function() {
    const selectedDate = new Date(this.value);
    if (isWeekend(selectedDate)) {
      showModal('Saturday and Sunday are not allowed. Please select a weekday.', 'error');
      this.value = '';
    }
  });
});