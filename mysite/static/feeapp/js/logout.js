(function() {
    
    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }
    
    function getUserType() {
        const fromParam = getQueryParam('from');
        if (fromParam) {
            return fromParam;
        }
        if (window.location.pathname.includes('student')) {
            return 'student';
        } else if (window.location.pathname.includes('clerk')) {
            return 'clerk';
        }
        return 'student';
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
    
    function isLogoutPage() {
        return document.getElementById('yesBtn') !== null && 
               document.getElementById('noBtn') !== null;
    }
    
    function isDashboardPage() {
        const path = window.location.pathname.toLowerCase();
        return path.includes('dashboard') || 
               path.includes('challan-summary') || 
               path.includes('manage-installment') ||
               path.includes('search-challan') ||
               path.includes('update-challan') ||
               path.includes('view-challan');
    }
    function isLoginPage() {
        const path = window.location.pathname.toLowerCase();
        return path.includes('student-login') ||
               path.includes('student_login') ||
               path.includes('clerk-login') ||
               path.includes('clerk_login');
    }

    function isRoleSelectPage() {
        const path = window.location.pathname.toLowerCase();
        return path === '/' || path.includes('role-select') || path.includes('role_select');
    }

    function initLogoutConfirmation() {
        const yesBtn = document.getElementById('yesBtn');
        const noBtn = document.getElementById('noBtn');
        const fromPage = getQueryParam('from');
        
        if (yesBtn) {
            yesBtn.addEventListener('click', () => {
                window.location.replace(`/logout_action/?from=${fromPage || 'student'}`);
            });
        }
        
        if (noBtn) {
            noBtn.addEventListener('click', () => {
                if (fromPage === 'student') {
                    window.location.replace('/dashboard/');
                } else if (fromPage === 'clerk') {
                    window.location.replace('/clerk/dashboard/');
                } else {
                    window.history.back();
                }
            });
        }

        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', window.location.href);
        }
    }
    
    function initAutoLogout() {

        const IDLE_TIMEOUT_MS   = 5  * 60 * 1000;
        const ACTIVE_TIMEOUT_MS = 10 * 60 * 1000;
        const WARNING_BEFORE_MS = 30 * 1000;

        let workStarted = false;

        const WORK_EVENTS = ['submit', 'change'];

        const WORK_PATHS = [
            'challan-form',
            'manage-installment',
            'update-challan',
            'search-challan',
            'challan-summary',
        ];

        function checkIfWorkPage() {
            const path = window.location.pathname.toLowerCase();
            return WORK_PATHS.some(p => path.includes(p));
        }

        if (checkIfWorkPage()) {
            workStarted = true;
        }

        function markWorkStarted() {
            if (!workStarted) {
                workStarted = true;
                resetTimer();
            }
        }

        WORK_EVENTS.forEach(evt => {
            document.addEventListener(evt, markWorkStarted, { passive: true });
        });

        const _origFetch = window.fetch;
        window.fetch = function(...args) {
            markWorkStarted();
            return _origFetch.apply(this, args);
        };

        let timeoutId;
        let warningTimeoutId;
        let countdownInterval;
        let warningShown = false;
        
        function saveLogoutTimeAndRedirect(userType, reason) {
            const logoutUrl = `/logout_action/?from=${userType}&reason=${reason}`;

            if (userType !== 'clerk') {
                window.location.replace(logoutUrl);
                return;
            }

            fetch('/api/save-auto-logout-time/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ reason: reason }),
            })
            .catch(function(err) {
                console.error('Auto-logout time save failed:', err);
            })
            .finally(function() {
                window.location.replace(logoutUrl);
            });
        }

        function performLogout() {
            const userType = getUserType();
            saveLogoutTimeAndRedirect(userType, 'timeout');
        }
        
        function showWarning() {
            if (warningShown) return;
            warningShown = true;
            
            const modal = document.createElement('div');
            modal.id = 'timeout-warning-modal';
            modal.innerHTML = `
                <div class="timeout-overlay"></div>
                <div class="timeout-modal">
                    <div class="timeout-icon">!</div>
                    <h3>Session Timeout Warning</h3>
                    <p>You will be logged out in <span id="countdown">30</span> seconds due to inactivity.</p>
                    <button id="stay-logged-in" class="stay-btn">Stay Logged In</button>
                </div>
            `;
            
            const style = document.createElement('style');
            style.id = 'timeout-warning-styles';
            style.textContent = `
                .timeout-overlay {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 9998;
                }
                .timeout-modal {
                    position: fixed;
                    top: 50%; left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 30px 40px;
                    border-radius: 10px;
                    text-align: center;
                    z-index: 9999;
                    box-shadow: 0 0 15px rgba(11, 46, 111, 0.3);
                    border: 4px solid #1e3a8a;
                    max-width: 400px;
                    width: 90%;
                }
                .timeout-icon { font-size: 50px; margin-bottom: 15px; }
                .timeout-modal h3 { color: #1e3a8a; margin-bottom: 15px; font-size: 1.4rem; }
                .timeout-modal p  { color: #333; margin-bottom: 20px; font-size: 1rem; }
                .timeout-modal #countdown { font-weight: bold; color: #dc2626; font-size: 1.2rem; }
                .stay-btn {
                    background: #1e3a8a; color: white;
                    border: none; padding: 10px 25px;
                    font-size: 16px; font-weight: bold;
                    border-radius: 5px; cursor: pointer;
                    transition: all 0.3s;
                }
                .stay-btn:hover { background: #152a66; transform: translateY(-2px); }
            `;
            
            if (!document.getElementById('timeout-warning-styles')) {
                document.head.appendChild(style);
            }
            document.body.appendChild(modal);
            
            let seconds = 30;
            const countdownEl = document.getElementById('countdown');
            
            countdownInterval = setInterval(() => {
                seconds--;
                if (countdownEl) countdownEl.textContent = seconds;
                if (seconds <= 0) {
                    clearInterval(countdownInterval);
                    performLogout();
                }
            }, 1000);
            
            const stayBtn = document.getElementById('stay-logged-in');
            if (stayBtn) {
                stayBtn.addEventListener('click', () => {
                    clearInterval(countdownInterval);
                    modal.remove();
                    warningShown = false;
                    resetTimer();
                });
            }
        }
        
        function resetTimer() {
            if (timeoutId)         clearTimeout(timeoutId);
            if (warningTimeoutId)  clearTimeout(warningTimeoutId);
            if (countdownInterval) clearInterval(countdownInterval);
            
            const existingModal = document.getElementById('timeout-warning-modal');
            if (existingModal) {
                existingModal.remove();
                warningShown = false;
            }

            const currentTimeout = workStarted ? ACTIVE_TIMEOUT_MS : IDLE_TIMEOUT_MS;

            warningTimeoutId = setTimeout(showWarning,  currentTimeout - WARNING_BEFORE_MS);
            timeoutId        = setTimeout(performLogout, currentTimeout);
        }
        
        const activityEvents = [
            'mousedown', 'mousemove', 'keydown',
            'keypress', 'scroll', 'touchstart', 'click', 'wheel'
        ];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, resetTimer, { passive: true });
        });
        
        resetTimer();
    }

    function initBrowserCloseHandler() {
        const userType = getUserType();
        if (userType !== 'clerk') return;

        let beaconSent = false;

        const pageLoadTime = Date.now();

        function sendBeacon() {
            if (beaconSent) return;

            const timeOnPage = Date.now() - pageLoadTime;
            if (timeOnPage < 10000) return;

            beaconSent = true;

            const csrfToken = getCookie('csrftoken');
            const data = JSON.stringify({ reason: 'browser_close' });
            const blob = new Blob([data], { type: 'application/json' });

            if (navigator.sendBeacon) {
                navigator.sendBeacon('/api/save-auto-logout-time/', blob);
            } else {
                try {
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/api/save-auto-logout-time/', false);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.setRequestHeader('X-CSRFToken', csrfToken);
                    xhr.send(data);
                } catch(e) {
                    console.error('Fallback XHR failed:', e);
                }
            }
        }

        window.addEventListener('beforeunload', sendBeacon);
        window.addEventListener('pagehide', sendBeacon);
    }
    function initLoginPageGuard() {
    if (!window.history || !window.history.replaceState) return;
    window.history.replaceState({ loginPage: true }, '', window.location.href);
    window.history.pushState({ loginPage: true }, '', window.location.href);

    window.addEventListener('popstate', function(e) {
        window.history.pushState({ loginPage: true }, '', window.location.href);
    });
}

   

    function init() {
        if (isLogoutPage()) {
            initLogoutConfirmation();
        }
        if (isDashboardPage()) {
            initAutoLogout();
            initBrowserCloseHandler();
        }
        if (isLoginPage()) {
            initLoginPageGuard();
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();