document.addEventListener('DOMContentLoaded', function() {
    const errorDiv = document.getElementById('errorMessage');
    const pdfDownloader = document.getElementById('pdfDownloader');
    const loadingMsg = document.getElementById('loadingMsg');
    const challanPage = document.getElementById('challanPage');
    const challanPreviewPage = document.getElementById('challanPreviewPage');
    const challanListArea = document.getElementById('challanListArea');
    const challanPreviewArea = document.getElementById('challanPreviewArea');
    const previewPrintBtn = document.getElementById('previewPrintBtn');
    const previewDownloadPdfBtn = document.getElementById('previewDownloadPdfBtn');
    const previewBackBtn = document.getElementById('previewBackBtn');

    window.addEventListener('afterprint', function() {
        document.body.style.display = 'none';
        document.body.offsetHeight;
        document.body.style.display = '';
    });

    previewBackBtn.addEventListener('click', function() {
        challanPreviewPage.style.display = 'none';
        challanPage.style.display = 'block';
    });

    function loadMyChallans() {
        challanListArea.innerHTML = '';
        errorDiv.style.display = 'none';
        if (loadingMsg) loadingMsg.style.display = 'block';

        fetch('/api/get-my-challans/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Server error: ' + response.status);
                });
            }
            return response.json();
        })
        .then(data => {
            if (loadingMsg) loadingMsg.style.display = 'none';

            if (!data.success) {
                showError(data.message || 'Could not load challans.');
                return;
            }

            if (!data.challans || data.challans.length === 0) {
                showError('No challans found for your account.');
                return;
            }

            const unpaid = data.challans.filter(c => c.status !== 'PAID');
            const paid   = data.challans.filter(c => c.status === 'PAID');

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
            const challanList = sorted.map(c => ({
                challan_number:  c.challan_number,
                challan_amount:  c.amount,
                due_date:        c.due_date,
                generation_date: c.generation_date,
                is_paid:         c.status === 'PAID',
                disciplines:     c.disciplines,
                semesters:       c.semesters,
                html_content:    ''
            }));

            renderChallanList(challanList);
        })
        .catch(error => {
            if (loadingMsg) loadingMsg.style.display = 'none';
            showError(error.message);
        });
    }

    
    loadMyChallans();

    function renderChallanList(challanList) {
        challanListArea.innerHTML = '';

        challanList.forEach(function(challan) {
            const row = document.createElement('div');
            row.className = 'challan-list-row';

            if (challan.is_paid) {
                row.classList.add('challan-row-paid');
            } else {
                row.classList.add('challan-row-unpaid');
            }

            const infoDiv = document.createElement('div');
            infoDiv.className = 'challan-row-info';
            infoDiv.innerHTML =
                '<div class="challan-row-number">' + challan.challan_number + '</div>' +
                '<div class="challan-row-details">' +
                    '<span>Amount: Rs. ' + challan.challan_amount + '</span>' +
                    '<span>Due: ' + challan.due_date + '</span>' +
                    '<span>Generated: ' + challan.generation_date + '</span>' +
                '</div>' +
                '<div class="challan-row-disciplines">' + challan.disciplines + ' | ' + challan.semesters + '</div>';

            const statusBadge = document.createElement('div');
            statusBadge.className = 'challan-row-status ' + (challan.is_paid ? 'status-paid' : 'status-unpaid');
            statusBadge.textContent = challan.is_paid ? 'Paid' : 'Unpaid';

            const btnsDiv = document.createElement('div');
            btnsDiv.className = 'challan-row-buttons';

            if (!challan.is_paid) {
                const printBtn = document.createElement('button');
                printBtn.className = 'btn green';
                printBtn.textContent = 'Print';
                printBtn.addEventListener('click', function() {
                    fetchAndPreviewChallan(challan.challan_number, true);
                });

                const downloadPdfBtn = document.createElement('button');
                downloadPdfBtn.className = 'btn pink';
                downloadPdfBtn.textContent = 'Download PDF';
                downloadPdfBtn.addEventListener('click', function() {
                    pdfDownloader.src = '/api/download-challan-pdf/' + challan.challan_number + '/';
                });

                btnsDiv.appendChild(printBtn);
                btnsDiv.appendChild(downloadPdfBtn);
            }

            row.appendChild(infoDiv);
            row.appendChild(statusBadge);
            row.appendChild(btnsDiv);
            challanListArea.appendChild(row);
        });
    }

    function fetchAndPreviewChallan(challanNumber, triggerPrint) {
        fetch('/api/view-challan-html/' + challanNumber + '/', {
            method: 'GET',
            headers: { 'X-CSRFToken': getCsrfToken() }
        })
        .then(response => {
            if (!response.ok) throw new Error('Challan not found');
            return response.text();
        })
        .then(htmlContent => {
            const challanObj = {
                challan_number: challanNumber,
                html_content:   htmlContent,
                is_paid:        false
            };
            openChallanPreview(challanObj, triggerPrint);
        })
        .catch(error => {
            showError('Error loading challan: ' + error.message);
        });
    }

    function openChallanPreview(challan, triggerPrint) {
        challanPreviewArea.innerHTML = challan.html_content;

        if (challan.is_paid) {
            previewPrintBtn.style.display = 'none';
            previewDownloadPdfBtn.style.display = 'none';
        } else {
            previewPrintBtn.style.display = 'inline-block';
            previewDownloadPdfBtn.style.display = 'inline-block';
        }

        previewDownloadPdfBtn.setAttribute('data-challan-number', challan.challan_number);

        challanPage.style.display = 'none';
        challanPreviewPage.style.display = 'block';

        if (triggerPrint) {
            setTimeout(function() {
                printChallan();
            }, 150);
        }
    }

    previewPrintBtn.addEventListener('click', function() {
        printChallan();
    });

    function printChallan() {
        if (!challanPreviewArea || challanPreviewArea.innerHTML.trim() === '') return;

        const printWindow = window.open('', '_blank');
        printWindow.document.write(
            '<!DOCTYPE html><html><head>' +
            '<meta charset="UTF-8">' +
            '<title>Print Challan</title>' +
            '<link rel="stylesheet" href="/static/feeapp/css/download_challan.css">' +
            '</head><body>' +
            challanPreviewArea.innerHTML +
            '</body></html>'
        );
        printWindow.document.close();
        printWindow.focus();

        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };

        setTimeout(function() {
            if (!printWindow.closed) {
                printWindow.print();
                printWindow.close();
            }
        }, 800);
    }

    previewDownloadPdfBtn.addEventListener('click', function() {
        const challanNumber = previewDownloadPdfBtn.getAttribute('data-challan-number');
        if (challanNumber) {
            pdfDownloader.src = '/api/download-challan-pdf/' + challanNumber + '/';
        }
    });

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.color = 'red';
        errorDiv.style.display = 'block';
        errorDiv.style.padding = '10px';
        errorDiv.style.marginTop = '10px';
        errorDiv.style.backgroundColor = '#ffebee';
        errorDiv.style.border = '1px solid #ef5350';
        errorDiv.style.borderRadius = '4px';
        hideNotificationAfterDelay();
    }

    function hideNotificationAfterDelay() {
        if (window.notificationTimeout) {
            clearTimeout(window.notificationTimeout);
        }
        window.notificationTimeout = setTimeout(function() {
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }, 5000);
    }

    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }
        return null;
    }
});