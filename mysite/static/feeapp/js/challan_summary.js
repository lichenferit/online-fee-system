
function toggleHistoryTable(blockId, btnId) {
    var block = document.getElementById(blockId);
    var btn   = document.getElementById(btnId);
    var isAlreadyActive = block && block.classList.contains('active');

    document.querySelectorAll('.history-table-block').forEach(function (b) {
        b.classList.remove('active');
    });
    document.querySelectorAll('.history-toggle-btn').forEach(function (b) {
        b.classList.remove('active');
    });
    document.querySelectorAll('.history-btn-arrow').forEach(function (a) {
        a.innerHTML = '&#9660;';
    });
    resetLoginHistorySearch();

    if (!isAlreadyActive) {
        if (block) { block.classList.add('active'); }
        if (btn) {
            btn.classList.add('active');
            var arrow = btn.querySelector('.history-btn-arrow');
            if (arrow) { arrow.innerHTML = '&#9650;'; }
        }
    }
}

function resetLoginHistorySearch() {
    var userIdEl   = document.getElementById('searchUserId');
    var dateFromEl = document.getElementById('searchLoginDateFrom');
    var dateToEl   = document.getElementById('searchLoginDateTo');
    var errEl      = document.getElementById('loginSearchError');
    var tableWrap  = document.getElementById('loginHistoryTableWrap');
    var emptyMsg   = document.getElementById('loginSearchEmptyMsg');

    if (userIdEl)   { userIdEl.value   = ''; }
    if (dateFromEl) { dateFromEl.value = ''; }
    if (dateToEl)   { dateToEl.value   = ''; }
    if (errEl)      { errEl.style.display   = 'none'; errEl.textContent = ''; }
    if (tableWrap)  { tableWrap.style.display = 'none'; }
    if (emptyMsg)   { emptyMsg.style.display  = 'none'; }

    document.querySelectorAll('.login-history-row').forEach(function (row) {
        row.style.display = '';
    });
}

function showScreen2() {
    document.getElementById('screen1').style.display = 'none';
    document.getElementById('screen2').style.display = 'block';
    document.getElementById('screen3').style.display = 'none';
    window.scrollTo(0, 0);
}

function showScreen3() {
    document.getElementById('screen1').style.display = 'none';
    document.getElementById('screen2').style.display = 'none';
    document.getElementById('screen3').style.display = 'block';
    window.scrollTo(0, 0);
}

function goBackToScreen1() {
    document.getElementById('screen2').style.display = 'none';
    document.getElementById('screen3').style.display = 'none';
    document.getElementById('screen1').style.display = 'block';

    fundReportData = null;

    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value   = '';
    document.getElementById('filterProgram').value  = '';
    document.getElementById('filterShift').value    = '';
    document.getElementById('filterCourseGroup').innerHTML = '<option value="">Select Program First</option>';
    document.getElementById('filterSemester').innerHTML    = '<option value="">Select Program First</option>';

    hideValidationError();
    window.scrollTo(0, 0);
}


function loadCourseGroups(programId) {
    var cgSelect  = document.getElementById('filterCourseGroup');
    var semSelect = document.getElementById('filterSemester');

    if (!programId) {
        cgSelect.innerHTML  = '<option value="">Select Program First</option>';
        semSelect.innerHTML = '<option value="">Select Program First</option>';
        return;
    }

    cgSelect.innerHTML  = '<option value="">Loading...</option>';
    semSelect.innerHTML = '<option value="">Loading...</option>';

    var apiBase = document.getElementById('programDetailsApiBase').value;
    var apiUrl  = apiBase.replace(/\/0\/$/, '/' + programId + '/');

    fetch(apiUrl, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function (response) {
        if (!response.ok) {
            throw new Error('Server returned ' + response.status);
        }
        return response.json();
    })
    .then(function (data) {

        cgSelect.innerHTML = '<option value="">Select Group</option>';
        if (data.disciplines && data.disciplines.length > 0) {
            data.disciplines.forEach(function (d) {
                var opt = document.createElement('option');
                opt.value       = d.discipline_id;
                opt.textContent = d.discipline_name;
                cgSelect.appendChild(opt);
            });
        } else {
            cgSelect.innerHTML = '<option value="">No groups found</option>';
        }

        semSelect.innerHTML = '<option value="">Select Semester</option>';
        if (data.semesters && data.semesters.length > 0) {
            data.semesters.forEach(function (s) {
                var opt = document.createElement('option');
                opt.value       = s.semester_name;
                opt.textContent = s.semester_name;
                semSelect.appendChild(opt);
            });
        } else {
            semSelect.innerHTML = '<option value="">No semesters found</option>';
        }

    })
    .catch(function (err) {
        console.error('loadCourseGroups error:', err);
        cgSelect.innerHTML  = '<option value="">Error loading — try again</option>';
        semSelect.innerHTML = '<option value="">Error loading — try again</option>';
    });
}

function filterLoginHistory() {
    var userId   = document.getElementById('searchUserId').value.trim().toLowerCase();
    var dateFrom = document.getElementById('searchLoginDateFrom').value;
    var dateTo   = document.getElementById('searchLoginDateTo').value;
    var errEl    = document.getElementById('loginSearchError');
    var tableWrap= document.getElementById('loginHistoryTableWrap');
    var emptyMsg = document.getElementById('loginSearchEmptyMsg');

    if (!userId && !dateFrom && !dateTo) {
        errEl.textContent   = 'Please enter at least a User Email or a date range to search.';
        errEl.style.display = 'block';
        tableWrap.style.display = 'none';
        return;
    }

    errEl.style.display  = 'none';
    errEl.textContent    = '';
    tableWrap.style.display = 'block';
    emptyMsg.style.display  = 'none';

    var rows         = document.querySelectorAll('.login-history-row');
    var visibleCount = 0;

    rows.forEach(function (row) {
        var rowEmail = row.getAttribute('data-email') || '';
        var rowDate  = row.getAttribute('data-date')  || '';   /* format: yyyy-mm-dd */

        var matchUser = !userId   || rowEmail.includes(userId);
        var matchFrom = !dateFrom || rowDate >= dateFrom;
        var matchTo   = !dateTo   || rowDate <= dateTo;

        if (matchUser && matchFrom && matchTo) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    if (visibleCount === 0) {
        emptyMsg.style.display = 'block';
    }
}

var fundReportData = null;

function generateFundReport() {
    var dateFrom  = document.getElementById('filterDateFrom').value;
    var dateTo    = document.getElementById('filterDateTo').value;
    var programId = document.getElementById('filterProgram').value;
    var shift     = document.getElementById('filterShift').value;
    var groupId   = document.getElementById('filterCourseGroup').value;
    var semester  = document.getElementById('filterSemester').value;

    if (!dateFrom) { showValidationError('Please select Date From.'); return; }
    if (!dateTo)   { showValidationError('Please select Date To.');   return; }
    if (dateFrom > dateTo) { showValidationError('Date From cannot be after Date To.'); return; }
    if (!programId) { showValidationError('Please select a Program.'); return; }
    if (!shift)     { showValidationError('Please select a Shift.');   return; }
    if (!groupId)   { showValidationError('Please select a Course Group.'); return; }
    if (!semester)  { showValidationError('Please select a Semester / Year.'); return; }

    hideValidationError();

    var params = new URLSearchParams();
    params.append('date_from',  dateFrom);
    params.append('date_to',    dateTo);
    params.append('program_id', programId);
    params.append('shift',      shift);
    params.append('group_id',   groupId);
    params.append('semester',   semester);

    var btn = document.getElementById('generateBtn');
    btn.innerHTML = 'Generating... &#9654;';
    btn.disabled  = true;

    var apiUrl = document.getElementById('fundReportApiUrl').value;

    fetch(apiUrl + '?' + params.toString(), {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function (response) {
        return response.json().then(function (data) {
            return { status: response.status, data: data };
        });
    })
    .then(function (result) {
        btn.innerHTML = 'Generate Report &#9654;';
        btn.disabled  = false;

        if (result.status !== 200 || result.data.error) {
            var msg = (result.data && result.data.error)
                ? result.data.error
                : 'Server error (status ' + result.status + ')';
            showValidationError('Error: ' + msg);
            return;
        }

        fundReportData = result.data;

        var filterText = 'Filters: ' + escapeHTML(result.data.filter_summary || 'All Records');
        document.getElementById('screen2FilterBar').innerHTML = filterText;
        document.getElementById('screen3FilterBar').innerHTML = filterText;

        document.getElementById('screen2ReportContent').innerHTML =
            buildReportHTML(result.data.paid_groups, result.data.paid_grand_total, result.data.paid_count, 'Paid');

        document.getElementById('screen3ReportContent').innerHTML =
            buildReportHTML(result.data.unpaid_groups, result.data.unpaid_grand_total, result.data.unpaid_count, 'Unpaid');

        showScreen2();
    })
    .catch(function (err) {
        btn.innerHTML = 'Generate Report &#9654;';
        btn.disabled  = false;
        showValidationError('Network error: ' + err.message);
        console.error(err);
    });
}

function switchReportTab(tab) {
    if (!fundReportData) return;

    if (tab === 'paid') {
        document.getElementById('btnPaid').classList.add('active');
        document.getElementById('btnUnpaid').classList.remove('active');
        document.getElementById('btnPaid3').classList.add('active');
        document.getElementById('btnUnpaid3').classList.remove('active');
        showScreen2();
    } else {
        document.getElementById('btnPaid').classList.remove('active');
        document.getElementById('btnUnpaid').classList.add('active');
        document.getElementById('btnPaid3').classList.remove('active');
        document.getElementById('btnUnpaid3').classList.add('active');
        showScreen3();
    }
}

function buildReportHTML(groups, grandTotal, count, label) {
    var html = '';

    if (!groups || groups.length === 0) {
        html += '<div class="report-empty-msg">No ' + label.toLowerCase() +
                ' challans found for the selected filters.</div>';
        return html;
    }

    groups.forEach(function (group) {
        html += '<div class="group-label">';
        html += escapeHTML(group.program) +
                ' &mdash; ' + escapeHTML(group.discipline) +
                ' &mdash; ' + escapeHTML(group.shift) + ' Shift' +
                ' &mdash; ' + escapeHTML(group.semester);
        html += '</div>';

        html += '<div class="table-section report-table-wrap">';
        html += '<table class="main-table"><thead><tr>';
        html += '<th>Fee Head Name</th>';
        html += '<th>No. of Challans</th>';
        html += '<th>Total Amount</th>';
        html += '</tr></thead><tbody>';

        group.fee_heads.forEach(function (fh) {
            html += '<tr>';
            html += '<td>' + escapeHTML(fh.fee_head_name) + '</td>';
            html += '<td class="center-cell">' + fh.challan_count + '</td>';
            html += '<td class="amount-cell">Rs. ' + formatAmount(fh.total_amount) + '</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';
    });

    html += '<div class="table-section report-table-wrap" style="margin-top:10px;margin-bottom:32px;">';
    html += '<table class="main-table"><tbody>';
    html += '<tr class="total-row">';
    html += '<td><strong>Grand Total</strong></td>';
    html += '<td class="center-cell"><strong>' + count + ' Challans</strong></td>';
    html += '<td class="amount-cell"><strong>Rs. ' + formatAmount(grandTotal) + '</strong></td>';
    html += '</tr>';
    html += '</tbody></table></div>';

    return html;
}

function printReport() {
    
    var printBtns = document.querySelectorAll('[onclick="printReport()"]');
    printBtns.forEach(function (btn) {
        btn.style.display = 'none';
    });

    window.print();
    setTimeout(function () {
        printBtns.forEach(function (btn) {
            btn.style.display = '';
        });
    }, 1000);
}

function showValidationError(msg) {
    var el = document.getElementById('filterValidationError');
    if (el) {
        el.textContent   = msg;
        el.style.display = 'block';
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function hideValidationError() {
    var el = document.getElementById('filterValidationError');
    if (el) {
        el.style.display = 'none';
        el.textContent   = '';
    }
}

function formatAmount(val) {
    var num = parseFloat(val) || 0;
    return num.toLocaleString('en-PK', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

window.addEventListener('DOMContentLoaded', function () {
    hideValidationError();
});