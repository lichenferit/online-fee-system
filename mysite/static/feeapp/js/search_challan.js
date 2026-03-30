
function searchChallans() {
    const cnic = document.getElementById("cnic").value.trim();

    if (!cnic) {
        showModal("Please enter CNIC number.");
        return;
    }
    const cleanCnic = cnic.replace(/-/g, '');
    showLoading(true);

    fetch(`/api/search-challans-by-cnic/?cnic=${encodeURIComponent(cleanCnic)}`)
        .then(response => response.json())
        .then(data => {
            showLoading(false);

            if (data.success) {
                displayResults(data);
            } else {
                showModal(data.message || "No challans found for this CNIC.");
            }
        })
        .catch(error => {
            showLoading(false);
            console.error("Error:", error);
            showModal("Error searching challans. Please try again.");
        });
}
function displayResults(data) {
    const studentInfoDiv = document.getElementById("studentInfo");
    studentInfoDiv.innerHTML = `
        <p><strong>Student Name:</strong> ${data.student_name}</p>
        <p><strong>CNIC:</strong> ${data.cnic}</p>
        <p><strong>Roll Number:</strong> ${data.roll_number}</p>
        <p><strong>Program:</strong> ${data.program || 'N/A'}</p>
    `;

    const challansListDiv = document.getElementById("challansList");

    if (data.challans.length === 0) {
        challansListDiv.innerHTML = `
            <div class="no-challans">
                <h3>Challans not Found</h3>
                <p>This student has no challans in the system.</p>
            </div>
        `;
    } else {
        let challansHTML = '';

        data.challans.forEach(challan => {
            const isPaid = challan.status.toUpperCase() === 'PAID';
            const statusClass = isPaid ? 'paid' : 'unpaid';

            challansHTML += `
                <div class="challan-card ${statusClass}">
                    <div class="challan-header">
                        <span class="challan-number">Challan #${challan.challan_number}</span>
                        <span class="challan-status ${statusClass}">${challan.status}</span>
                    </div>
                    <div class="challan-details">
                        <p><strong>Amount:</strong> Rs. ${challan.amount}</p>
                        <p><strong>Due Date:</strong> ${challan.due_date}</p>
                        <p><strong>Generated:</strong> ${challan.generation_date}</p>
                        <p><strong>Discipline:</strong> ${challan.disciplines || 'N/A'}</p>
                        <p><strong>Semester:</strong> ${challan.semesters || 'N/A'}</p>
                        <p><strong>Session:</strong> ${challan.session || 'N/A'}</p>
                    </div>
                    <div class="challan-actions">
                        <button class="btn-print" onclick="printChallan('${challan.challan_number}')">
                             Download
                        </button>
                        <button class="btn-view" onclick="viewChallan('${challan.challan_number}')">
                             View
                        </button>
                        ${!isPaid ? `
                            <button class="btn-edit" onclick="editChallan('${challan.challan_number}')">
                                 Edit
                            </button>
                            <button class="btn-installment" onclick="createInstallment('${challan.challan_number}', '${data.cnic}')">
                                 Installment
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        challansListDiv.innerHTML = challansHTML;
    }
    document.getElementById("searchPage").classList.remove("active");
    document.getElementById("resultPage").classList.add("active");
}

function printChallan(challanNumber) {
    window.open(`/api/download-challan-pdf/${challanNumber}/`, '_blank');
}

function viewChallan(challanNumber) {
    window.open(`/api/view-challan-html/${challanNumber}/`, '_blank');
}

function editChallan(challanNumber) {
    window.location.href = `/update_challan/?challan=${challanNumber}`;
    
}

function createInstallment(challanNumber, cnic) {
   
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/manage-installment/';

    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCookie('csrftoken');
    form.appendChild(csrfInput);

    const cnicInput = document.createElement('input');
    cnicInput.type = 'hidden';
    cnicInput.name = 'cnic';
    cnicInput.value = cnic;
    form.appendChild(cnicInput);

    const challanInput = document.createElement('input');
    challanInput.type = 'hidden';
    challanInput.name = 'challan_num';
    challanInput.value = challanNumber;
    form.appendChild(challanInput);

    document.body.appendChild(form);
    form.submit();
}

function goBack() {
    document.getElementById("resultPage").classList.remove("active");
    document.getElementById("searchPage").classList.add("active");
    document.getElementById("cnic").value = '';
}

function showModal(message) {
    document.getElementById("modalMessage").textContent = message;
    document.getElementById("errorModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("errorModal").style.display = "none";
}
function showLoading(show) {
    document.getElementById("loadingSpinner").style.display = show ? "flex" : "none";
}
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
document.addEventListener('DOMContentLoaded', function() {
    const cnicInput = document.getElementById('cnic');
    if (cnicInput) {
        cnicInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchChallans();
            }
        });
    }
});