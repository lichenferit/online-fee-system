
function getCSRFToken() {
    let cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        let [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return decodeURIComponent(value);
    }
    return '';
}
let currentChallanStatus = '';
document.addEventListener('DOMContentLoaded', function () {
    loadStudentChallans();
});

function loadStudentChallans() {
    const resultBox = document.getElementById("challanResult");
    const challansListSection = document.getElementById("challansListSection");
    const challansList = document.getElementById("challansList");

    resultBox.innerHTML = "<p style='text-align:center;'>Loading your challans...</p>";
    resultBox.style.display = "block";
    challansListSection.style.display = "none";

    fetch('/api/get-my-challans/', {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'An error occurred');
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            showErrorModal(data.message || 'Could not load challans.');
            return;
        }
        if (!data.challans || data.challans.length === 0) {
            resultBox.innerHTML = `<p style="color:orange; text-align:center;"><strong>Challan not found.</strong></p>`;
            return;
        }

        resultBox.innerHTML = `
            <p><strong>Student Name:</strong> ${data.student_name}</p>
            <p><strong>Roll Number:</strong> ${data.roll_number}</p>
            <p><strong>Program:</strong> ${data.program}</p>
            <p><strong>Total Challans:</strong> ${data.total_challans}</p>
        `;

        const challans = data.challans;

        const unpaid = challans.filter(c => c.status !== 'PAID');
        const paid   = challans.filter(c => c.status === 'PAID');

        function sortNewestFirst(a, b) {
            const parseDate = str => {
                if (!str || str === 'N/A') return new Date(0);
                const [d, m, y] = str.split('/');
                return new Date(`${y}-${m}-${d}`);
            };
            return parseDate(b.generation_date) - parseDate(a.generation_date);
        }

        unpaid.sort(sortNewestFirst);
        paid.sort(sortNewestFirst);

        const sorted = [...unpaid, ...paid];
        let listHTML = '';
        sorted.forEach(challan => {
            const isPaid = challan.status === 'PAID';

            const statusBadge = isPaid
                ? '<span style="background: #22c55e; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">PAID</span>'
                : '<span style="background: #ef4444; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">UNPAID</span>';

            listHTML += `
                <div style="border: 2px solid #1e3a8a; border-radius: 10px; padding: 15px; margin-bottom: 15px; background: #f8fafc;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <p style="margin: 5px 0;"><strong>Challan No:</strong> ${challan.challan_number}</p>
                            <p style="margin: 5px 0;"><strong>Amount:</strong> Rs. ${challan.amount}</p>
                            <p style="margin: 5px 0;"><strong>Due Date:</strong> ${challan.due_date}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> ${statusBadge}</p>
                        </div>
                        <div style="margin-top: 10px;">
                            <button onclick="viewChallanDetails('${challan.challan_number}', '${challan.status}')" 
                                style="background: #1e3a8a; color: white; padding: 10px 25px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                View
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        challansList.innerHTML = listHTML;
        challansListSection.style.display = "block";
    })
    .catch(error => {
        console.error('Error:', error);
        resultBox.innerHTML = `<p style="color:red; text-align:center;"><strong>${error.message}</strong></p>`;
    });
}

function viewChallanDetails(challanNumber, status) {
    currentChallanStatus = status;

    const modal = document.getElementById("challanViewModal");
    const content = document.getElementById("challanViewContent");
    const printContainer = document.getElementById("printButtonContainer");

    content.innerHTML = "<p style='text-align:center;'>Loading challan...</p>";
    printContainer.innerHTML = "";
    modal.style.display = "block";
    document.body.style.overflow = "hidden";

    fetch(`/api/view-challan-html/${challanNumber}/`, {
        method: "GET",
        headers: {
            "X-CSRFToken": getCSRFToken()
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Challan not found');
        return response.text();
    })
    .then(htmlContent => {
        content.innerHTML = `
            <div style="border: 2px solid #1e3a8a; border-radius: 10px; padding: 10px; background: white;">
                <iframe id="challanFrame" srcdoc="${htmlContent.replace(/"/g, '&quot;')}" 
                    style="width: 100%; height: 500px; border: none;"></iframe>
            </div>
        `;

        if (status !== 'PAID') {
            printContainer.innerHTML = `
                <button onclick="printChallan('${challanNumber}')" 
                    style="background: #16a34a; color: white; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; margin-right: 10px;">
                    Print Challan
                </button>
                <button onclick="downloadPDF('${challanNumber}')" 
                    style="background: #2563eb; color: white; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
                    Download PDF
                </button>
            `;
        } else {
            printContainer.innerHTML = `
                <p style="color: #16a34a; font-weight: bold; font-size: 14px;">
                    This challan has been PAID. View only mode.
                </p>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        content.innerHTML = `<p style="color:red; text-align:center;"><strong>Error loading challan: ${error.message}</strong></p>`;
    });
}

function printChallan(challanNumber) {
    const iframe = document.getElementById("challanFrame");
    if (iframe) {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
    }
}

function downloadPDF(challanNumber) {
    window.open(`/api/download-challan-pdf/${challanNumber}/`, '_blank');
}

function closeModal() {
    const modal = document.getElementById("challanViewModal");
    modal.style.display = "none";
    document.body.style.overflow = "auto";
}

function showErrorModal(message) {
    const modal = document.createElement('div');
    modal.id = 'errorModal';
    modal.style.cssText = 'display: block; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 2000; overflow-y: auto;';

    modal.innerHTML = `
        <div style="background: white; max-width: 300px; margin: 100px auto; padding: 30px; border-radius: 15px; position: relative; border: 3px solid #1e3a8a;">
            <p style="text-align: center; font-size: 16px; color: #333; margin: 20px 0;">${message}</p>
            <div style="text-align: center; margin-top: 25px;">
                <button onclick="closeErrorModal()" style="background: #1e3a8a; color: white; border: none; padding: 12px 40px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
                    OK
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    document.body.style.overflow = "hidden";
}

function closeErrorModal() {
    const modal = document.getElementById('errorModal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = "auto";
    }
}

document.addEventListener('click', function (event) {
    const modal = document.getElementById("challanViewModal");
    if (event.target === modal) closeModal();
});

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const errorModal = document.getElementById('errorModal');
        if (errorModal) closeErrorModal();
        else closeModal();
    }
});