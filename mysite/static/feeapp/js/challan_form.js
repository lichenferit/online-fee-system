
let programs = [];
let currentProgram = null;
const programFormMap = {
    '1': 'bs',
    '2': 'bsr',
    '3': 'inter',
    '4': 'bachelor',
    '5': 'masters',
    '6': 'adp'
};

document.addEventListener('DOMContentLoaded', function() {
    loadPrograms();
    
    document.getElementById('programSelect').addEventListener('change', handleProgramChange);
    
    setMinimumDueDate();
});

function setMinimumDueDate() {
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yyyy = today.getFullYear();
    const minDate = `${yyyy}-${mm}-${dd}`;
    
    window.minDueDate = minDate;
}


function validateDueDate(dateInput) {
    const selectedDate = new Date(dateInput.value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
   
    if (selectedDate < today) {
        alert('Due date cannot be in the past! Please select today or a future date.');
        dateInput.value = '';
        return false;
    }
    
    const dayOfWeek = selectedDate.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
        const dayName = dayOfWeek === 0 ? 'Sunday' : 'Saturday';
        alert(`Due date cannot be ${dayName}! Please select a weekday (Monday-Friday).`);
        dateInput.value = '';
        return false;
    }
    
    return true;
}

function loadPrograms() {
    fetch('/api/get-programs/')
        .then(response => response.json())
        .then(data => {
            programs = data.programs;
            const select = document.getElementById('programSelect');
            
            programs.forEach(program => {
                const option = document.createElement('option');
                option.value = String(program.program_id);
                option.textContent = program.ProgramName;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading programs:', error));
}

function handleProgramChange(e) {
    const programId = e.target.value;
    
    if (!programId) {
        currentProgram = null;
        document.querySelectorAll('.program-form').forEach(div => div.classList.add('hidden'));
        return;
    }
    
    fetch(`/api/get-program-details/${programId}/`)
        .then(response => response.json())
        .then(data => {
            currentProgram = {
                id: programId,
                ...data
            };
            
            const formId = programFormMap[programId];
            if (!formId) {
                throw new Error(`No form mapping found for program ID: ${programId}`);
            }
            
            showProgramForm(formId);
        })
        .catch(error => {
            console.error('Error loading program details:', error);
            alert('Error loading program details. Please try again.');
        });
}

function showProgramForm(formId) {
    document.querySelectorAll('.program-form').forEach(div => div.classList.add('hidden'));
    
    if (!formId || !currentProgram) {
        return;
    }
    
    const formDiv = document.getElementById(formId + 'Form');
    if (!formDiv) {
        return;
    }
    
    formDiv.innerHTML = '';
    
    const template = document.getElementById('formTemplate');
    if (!template) {
        return;
    }
    
    const templateContent = template.content.cloneNode(true);
    
    const shiftOptions = templateContent.querySelector('.shift-options');
    if (shiftOptions) {
        shiftOptions.innerHTML = '';
        const shifts = currentProgram.shifts || ['Morning', 'Evening'];
        shifts.forEach(shift => {
            const label = document.createElement('label');
            label.innerHTML = `<input type="radio" name="shift" value="${shift}" onchange="updateStudentSelectionOnChange()"> ${shift}`;
            shiftOptions.appendChild(label);
        });
    }
    
    const sessionSelect = templateContent.querySelector('.session-select');
    if (sessionSelect) {
        sessionSelect.innerHTML = '<option value=""> Select Session </option>';
        
        if (currentProgram.sessions && currentProgram.sessions.length > 0) {
            currentProgram.sessions.forEach(session => {
                const option = document.createElement('option');
                option.value = session.session_name;
                option.textContent = session.session_name;
                sessionSelect.appendChild(option);
            });
        }
        
        sessionSelect.addEventListener('change', updateStudentSelectionOnChange);
    }
    
    const disciplineList = templateContent.querySelector('.discipline-list');
    if (disciplineList) {
        disciplineList.innerHTML = '';
        
        if (currentProgram.disciplines && currentProgram.disciplines.length > 0) {
            currentProgram.disciplines.forEach(discipline => {
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'discipline-checkbox';
                checkbox.value = discipline.discipline_id;
                checkbox.setAttribute('data-name', discipline.discipline_name);
                checkbox.onchange = updateStudentSelectionOnChange;
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(' ' + discipline.discipline_name));
                disciplineList.appendChild(label);
            });
        } else {
            disciplineList.innerHTML = '<div>No course groups available</div>';
        }
    }
    
    const semesterCheckboxes = templateContent.querySelector('.semester-checkboxes');
    if (semesterCheckboxes) {
        semesterCheckboxes.innerHTML = '';
        
        if (currentProgram.semesters && currentProgram.semesters.length > 0) {
            currentProgram.semesters.forEach(semester => {
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'semester-checkbox';
                checkbox.value = semester.semester_id;
                checkbox.setAttribute('data-name', semester.semester_name);
                checkbox.onchange = updateStudentSelectionOnChange;
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(' ' + semester.semester_name));
                semesterCheckboxes.appendChild(label);
            });
        } else {
            semesterCheckboxes.innerHTML = '<div>No semesters available</div>';
        }
    }

    const generateOptions = templateContent.querySelector('#generateOptions');
    if (generateOptions) {
        generateOptions.style.display = 'block';

        const radios = generateOptions.querySelectorAll('input[name="generate_mode"]');
        radios.forEach(radio => {
            radio.addEventListener('change', handleGenerateModeChange);
        });
    }
    
    let feeHeadSection = templateContent.querySelector('.fee-head-section');
    if (!feeHeadSection) {
        feeHeadSection = document.createElement('div');
        feeHeadSection.className = 'fee-head-section';
        feeHeadSection.innerHTML = `
            <div class="section-title">Available Fee Heads</div>
            <div class="fee-head-container"></div>
            <div class="text-center" style="margin-top: 10px; margin-bottom: 20px;">
                <button class="btn add-fee-head-btn" type="button" onclick="addNewFeeHead()">Add New Fee Head</button>
            </div>
        `;
        
        const tuitionSection = templateContent.querySelector('.grid.grid-2.mb-4');
        if (tuitionSection) {
            tuitionSection.parentNode.insertBefore(feeHeadSection, tuitionSection);
        }
    }
    
    const feeHeadContainer = feeHeadSection.querySelector('.fee-head-container');
    if (feeHeadContainer) {
        feeHeadContainer.innerHTML = '';
        
        if (currentProgram.fee_heads && currentProgram.fee_heads.length > 0) {
            currentProgram.fee_heads.forEach(feeHead => {
                const feeHeadDiv = document.createElement('div');
                feeHeadDiv.className = 'fee-head-item';
                feeHeadDiv.innerHTML = `
                    <label>
                        <input type="checkbox" class="fee-head-checkbox" value="${feeHead.fee_head_account_id}" 
                               data-name="${feeHead.fee_head_name}" data-amount="${feeHead.fee_head_amount}" 
                               onchange="handleFeeHeadChange(this)">
                        ${feeHead.fee_head_name}
                    </label>
                    <input type="number" class="fee-amount-input" value="${feeHead.fee_head_amount}" 
                           placeholder="Amount" data-fee-head-id="${feeHead.fee_head_account_id}"
                           oninput="calculateGrandTotal()">
                `;
                feeHeadContainer.appendChild(feeHeadDiv);
            });
        } else {
            feeHeadContainer.innerHTML = '<div>No fee heads available</div>';
        }
    }
    
    const dueDateInput = templateContent.querySelector('input[type="date"]');
    if (dueDateInput) {
        dueDateInput.min = window.minDueDate;
        dueDateInput.addEventListener('change', function() {
            validateDueDate(this);
        });
    }
    
    formDiv.appendChild(templateContent);
    formDiv.classList.remove('hidden');

    const activeGenOptions = formDiv.querySelector('#generateOptions');
    if (activeGenOptions) {
        const checkedMode = activeGenOptions.querySelector('input[name="generate_mode"]:checked');
        const studentSelection = activeGenOptions.querySelector('#studentSelection');
        if (checkedMode && checkedMode.value === 'single' && studentSelection) {
            studentSelection.style.display = 'block';
            updateStudentSelection();
        }
    }
}

function updateStudentSelectionOnChange() {
    const activeForm = document.querySelector('.program-form:not(.hidden)');
    if (!activeForm) return;
    const checkedMode = activeForm.querySelector('input[name="generate_mode"]:checked');
    if (checkedMode && checkedMode.value === 'single') {
        updateStudentSelection();
    }
}

function handleFeeHeadChange(checkbox) {
    const amountInput = document.querySelector(`.fee-amount-input[data-fee-head-id="${checkbox.value}"]`);
    if (amountInput) {
        amountInput.disabled = !checkbox.checked;
        calculateGrandTotal();
    }
}

function addNewFeeHead() {
    const activeForm = document.querySelector('.program-form:not(.hidden)');
    if (!activeForm) return;
    
    const feeHeadName = prompt("Enter Fee Head Name:");
    if (!feeHeadName || feeHeadName.trim() === '') return;
    
    const feeHeadAmount = prompt("Enter Default Amount:");
    if (!feeHeadAmount || isNaN(feeHeadAmount)) return;
    
    fetch('/api/get-programs/')
        .then(response => response.json())
        .then(data => {
            let programOptions = '';
            data.programs.forEach(program => {
                programOptions += `
                    <label>
                        <input type="checkbox" value="${program.program_id}" ${program.program_id == currentProgram.id ? 'checked' : ''}>
                        ${program.ProgramName}
                    </label><br>`;
            });
            
            const programDiv = document.createElement('div');
            programDiv.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.3); z-index: 1000; max-width: 500px; max-height: 70vh; overflow-y: auto;';
            
            programDiv.innerHTML = `
                <h3>Select Programs for this Fee Head</h3>
                <div id="programSelectionContainer">
                    ${programOptions}
                </div>
                <div style="margin-top: 20px; text-align: center;">
                    <button id="saveFeeHeadBtn" class="btn">Save</button>
                    <button id="cancelFeeHeadBtn" class="btn" style="background: #dc3545;">Cancel</button>
                </div>
            `;
            
            document.body.appendChild(programDiv);
            
            document.getElementById('saveFeeHeadBtn').addEventListener('click', function() {
                const selectedPrograms = [];
                programDiv.querySelectorAll('#programSelectionContainer input:checked').forEach(checkbox => {
                    selectedPrograms.push(parseInt(checkbox.value));
                });
                
                if (selectedPrograms.length === 0) {
                    alert('Please select at least one program');
                    return;
                }
                
                fetch('/api/add-fee-head/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        program_ids: selectedPrograms,
                        fee_head_name: feeHeadName.trim(),
                        fee_head_amount: parseFloat(feeHeadAmount)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        handleProgramChange({target: {value: currentProgram.id}});
                        showSuccessMessage(`Fee head "${data.fee_head_name}" added successfully!`);
                    } else {
                        alert('Error adding fee head: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error adding fee head:', error);
                    alert('Error adding fee head. Please try again.');
                })
                .finally(() => {
                    programDiv.remove();
                });
            });
            
            document.getElementById('cancelFeeHeadBtn').addEventListener('click', function() {
                programDiv.remove();
            });
        })
        .catch(error => {
            console.error('Error loading programs:', error);
            alert('Error loading programs. Please try again.');
        });
}

function saveCustomSession() {
    const activeForm = document.querySelector('.program-form:not(.hidden)');
    if (!activeForm) return;
    
    const customSessionInput = activeForm.querySelector('.custom-session-input');
    const sessionValue = customSessionInput.value.trim();
    
    if (!sessionValue) {
        alert('Please enter a session name');
        return;
    }
    
    fetch('/api/save-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            program_id: currentProgram.id,
            session_name: sessionValue
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            handleProgramChange({target: {value: currentProgram.id}});
            showSuccessMessage(`Session "${data.session_name}" saved successfully!`);
        } else {
            alert('Error saving session: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving session:', error);
        alert('Error saving session. Please try again.');
    });
}

function handleGenerateModeChange(e) {
    const mode = e.target.value;
    const activeForm = document.querySelector('.program-form:not(.hidden)');
    if (!activeForm) return;

    const studentSelection = activeForm.querySelector('#studentSelection');
    if (!studentSelection) return;

    if (mode === 'single') {
        studentSelection.style.display = 'block';
        updateStudentSelection();
    } else {
        studentSelection.style.display = 'none';
    }
}

function updateStudentSelection() {
    if (!currentProgram) {
        return;
    }
    
    const activeForm = document.querySelector('.program-form:not(.hidden)');
    if (!activeForm) {
        return;
    }
    
    const shift = activeForm.querySelector('input[name="shift"]:checked')?.value;
    const session = activeForm.querySelector('.session-select')?.value || 
                  activeForm.querySelector('.custom-session-input')?.value;
    const disciplineCheckbox = activeForm.querySelector('.discipline-checkbox:checked');
    const discipline = disciplineCheckbox?.value;
    const semesterCheckbox = activeForm.querySelector('.semester-checkbox:checked');
    const semester = semesterCheckbox?.value;
    
    const select = activeForm.querySelector('#studentSelect');
    if (!select) return;

    if (!shift || !session || !discipline || !semester) {
        select.innerHTML = '<option value="">-- Complete all fields first --</option>';
        return;
    }
    
    const params = new URLSearchParams({
        program_id: currentProgram.id,
        shift: shift,
        session: session,
        discipline: discipline,
        semester: semester
    });
    
    fetch(`/api/get-students/?${params}`)
        .then(response => response.json())
        .then(data => {
            select.innerHTML = '<option value="">-- Select Student --</option>';
            
            if (data.students && data.students.length > 0) {
                data.students.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.user_id;
                    option.textContent = `${student.student_name} (${student.college_roll_number})`;
                    select.appendChild(option);
                });
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No students found';
                select.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error loading students:', error);
            select.innerHTML = '<option value="">-- Error loading students --</option>';
        });
}

function calculateGrandTotal() {
    const activeForm = document.querySelector('.program-form:not(.hidden) .form-content');
    if (!activeForm) return;
    
    let total = 0;
    
    const checkedFeeHeads = activeForm.querySelectorAll('.fee-head-checkbox:checked');
    checkedFeeHeads.forEach(checkbox => {
        const amountInput = document.querySelector(`.fee-amount-input[data-fee-head-id="${checkbox.value}"]`);
        if (amountInput) {
            const amount = parseFloat(amountInput.value) || 0;
            total += amount;
        }
    });
    
    const tuitionInput = activeForm.querySelector('.tuition-fee');
    if (tuitionInput) {
        total += parseFloat(tuitionInput.value) || 0;
    }
    
    const grandTotalInput = activeForm.querySelector('.grand-total');
    if (grandTotalInput) {
        grandTotalInput.value = total.toFixed(2);
    }
}

function goBack() {
    document.getElementById('form-container').style.display = 'block';
    document.getElementById('headerBox').style.display = 'block';
    document.getElementById('challanDisplay').style.display = 'none';
    document.getElementById('challanDisplay').classList.remove('show');
    document.getElementById('printBackBtn').style.display = 'none';
    window.scrollTo(0, 0);
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('generate-btn')) {
        const form = e.target.closest('.form-content');
        if (!form) {
            alert('Form not found!');
            return;
        }
        
        const tuition = form.querySelector('.tuition-fee')?.value;
        if (!tuition || tuition === "0" || tuition === "") {
            alert('Please enter Tuition Fee amount!');
            return;
        }
        
        const shift = form.querySelector('input[name="shift"]:checked')?.value;
        if (!shift) {
            alert('Please select a shift!');
            return;
        }
        
        const session = form.querySelector('.session-select')?.value || 
                      form.querySelector('.custom-session-input')?.value;
        if (!session) {
            alert('Please select a session!');
            return;
        }
        
        const disciplines = Array.from(form.querySelectorAll('.discipline-checkbox:checked'))
            .map(cb => cb.value);
        
        if (disciplines.length === 0) {
            alert('Please select at least one course group!');
            return;
        }
        
        const semesters = Array.from(form.querySelectorAll('.semester-checkbox:checked'))
            .map(cb => cb.value);
        
        if (semesters.length === 0) {
            alert('Please select at least one semester!');
            return;
        }
        
        const feeHeads = [];
        form.querySelectorAll('.fee-head-checkbox:checked').forEach(checkbox => {
            const amountInput = document.querySelector(`.fee-amount-input[data-fee-head-id="${checkbox.value}"]`);
            if (amountInput) {
                const amount = parseFloat(amountInput.value) || 0;
                if (amount > 0) {
                    feeHeads.push({ 
                        id: checkbox.value, 
                        name: checkbox.getAttribute('data-name'),
                        amount: amount 
                    });
                }
            }
        });
        
        if (feeHeads.length === 0) {
            alert('Please select at least one fee head!');
            return;
        }
        
        const dueDateInput = form.querySelector('input[type="date"]');
        const dueDate = dueDateInput?.value;
        if (!dueDate) {
            alert('Please select a due date!');
            return;
        }
        
        if (!validateDueDate(dueDateInput)) {
            return;
        }

        const isBulkRadio = form.querySelector('input[name="generate_mode"]:checked');
        const isBulk = isBulkRadio ? isBulkRadio.value === 'bulk' : false;
        const studentSelect = form.querySelector('#studentSelect');
        const studentId = isBulk ? null : (studentSelect ? studentSelect.value : null);
        
        if (!isBulk && !studentId) {
            alert('Please select a student!');
            return;
        }
        
        const generateBtn = e.target;
        const originalText = generateBtn.textContent;
        generateBtn.textContent = 'Generating...';
        generateBtn.disabled = true;
        
        fetch('/api/generate-challan/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                program_id: currentProgram.id,
                shift: shift,
                session: session,
                disciplines: disciplines,
                semesters: semesters,
                fee_heads: feeHeads,
                tuition_fee: parseFloat(tuition),
                due_date: dueDate,
                is_bulk: isBulk,
                student_id: studentId
            })
        })
        .then(response => response.json())
        .then(data => {
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
            
            if (data.success) {
                if (isBulk) {
                    showSuccessMessage(`Challans generated for ${data.challans_count} students successfully!`);
                } else {
                    displayChallan(data);
                }
            } else {
                alert('Error generating challan: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error generating challan:', error);
            alert('Error generating challan. Please try again.');
            
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
        });
    }
});

function displayChallan(challanData) {
    if (!challanData || !challanData.challan_number) {
        alert('Invalid challan data received');
        return;
    }
    
    const challanDisplay = document.getElementById('challanDisplay');
    const formContainer = document.getElementById('form-container');
    const headerBox = document.getElementById('headerBox');
    const printBackBtn = document.getElementById('printBackBtn');
    
    if (!challanDisplay) {
        alert('Challan display container not found');
        return;
    }
    
    const dataUpdates = [
        { selector: '.c-name', value: challanData.student_name || 'N/A' },
        { selector: '.c-roll', value: challanData.roll_number || 'N/A' },
        { selector: '.c-shift', value: (challanData.shift || 'N/A').toLowerCase() },
        { selector: '.form-discipline', value: challanData.disciplines || 'N/A' },
        { selector: '.form-semester', value: challanData.semesters || 'N/A' },
        { selector: '.form-session', value: challanData.session || 'N/A' },
        { selector: '.c-amount', value: `Rs. ${challanData.amount || '0'}` },
        { selector: '.c-due', value: formatDate(challanData.due_date) },
        { selector: '.c-one-bill', value: challanData.one_bill_number || 'Pending' },
        { selector: '.challan-number-text', value: challanData.challan_number || 'N/A' }
    ];
    
    dataUpdates.forEach(item => {
        const elements = document.querySelectorAll(item.selector);
        elements.forEach(el => {
            el.textContent = item.value;
        });
    });
    
    if (challanData.fee_heads && Array.isArray(challanData.fee_heads)) {
        const tableBody = document.querySelectorAll('.fee-table-body');
        tableBody.forEach(tbody => {
            tbody.innerHTML = '';
            challanData.fee_heads.forEach(fh => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${fh.name}</td>
                    <td>${fh.amount}</td>
                `;
                tbody.appendChild(row);
            });
        });
    }
    
    if (challanData.logo && challanData.logo.logo_url) {
        document.querySelectorAll('.logo-container img').forEach(img => {
            img.src = challanData.logo.logo_url;
            img.alt = challanData.logo.college_name;
        });
    }
    
    if (formContainer) formContainer.style.display = 'none';
    if (headerBox) headerBox.style.display = 'none';
    
    challanDisplay.style.display = 'block';
    challanDisplay.classList.remove('hidden-on-screen');
    challanDisplay.classList.add('show');
    
    if (printBackBtn) printBackBtn.style.display = 'block';
    
    window.scrollTo({ top: 0, behavior: 'instant' });
    
    if (challanData.challan_number) {
        setTimeout(() => checkChallanSaved(challanData.challan_number), 500);
    }
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

function showSuccessMessage(message) {
    const successMsg = document.createElement('div');
    successMsg.className = 'success-message';
    successMsg.textContent = message;
    successMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        z-index: 100000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-weight: 600;
        font-size: 14px;
    `;
    
    document.body.appendChild(successMsg);
    
    setTimeout(() => {
        successMsg.style.opacity = '0';
        successMsg.style.transition = 'opacity 0.5s';
        setTimeout(() => successMsg.remove(), 500);
    }, 3000);
}

function checkChallanSaved(challanNumber) {
    fetch(`/api/check-challan-saved/${challanNumber}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.pdf_exists && data.pdf_url) {
                addDownloadButton(data.pdf_url);
            }
        })
        .catch(error => console.error('Error checking challan:', error));
}

function addDownloadButton(pdfUrl) {
    if (document.getElementById('downloadPdfBtn')) return;
    
    const downloadBtn = document.createElement('button');
    downloadBtn.id = 'downloadPdfBtn';
    downloadBtn.textContent = 'Download PDF';
    downloadBtn.style.cssText = `
        background: #007bff;
        color: white;
        padding: 12px 30px;
        margin: 0 10px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
    `;
    downloadBtn.onclick = () => {
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = pdfUrl.split('/').pop();
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
    
    const buttonsWrapper = document.getElementById('printBackBtn');
    if (buttonsWrapper) {
        buttonsWrapper.insertBefore(downloadBtn, buttonsWrapper.firstChild);
    }
}